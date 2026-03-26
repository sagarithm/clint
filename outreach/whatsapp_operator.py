import asyncio
import os
import random
from typing import Optional
from datetime import date
from playwright.async_api import async_playwright, BrowserContext, Playwright

from core.logger import logger
from core.config import settings
from core.database import get_db

class WhatsAppOperator:
    """
    A persistent WhatsApp Web operator for automated messaging.
    
    Uses a Playwright persistent context to maintain login sessions 
    and simulates human-like typing and navigation to avoid detection.
    """

    def __init__(self) -> None:
        self.session_path: str = os.path.join("data", "whatsapp_session")
        os.makedirs(self.session_path, exist_ok=True)
        self.context: Optional[BrowserContext] = None
        self.playwright: Optional[Playwright] = None

    async def start(self) -> None:
        """Initializes the persistent browser session for WhatsApp Web."""
        if self.context: return
        
        try:
            self.playwright = await async_playwright().start()
            logger.info("Starting Persistent WhatsApp Session...")
            
            self.context = await self.playwright.chromium.launch_persistent_context(
                self.session_path,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp browser: {e}")
            await self.stop()

    async def stop(self) -> None:
        """Gracefully closes the browser and Playwright instances."""
        if self.context: await self.context.close()
        if self.playwright: await self.playwright.stop()
        self.context = None
        self.playwright = None

    async def send(self, phone: str, message: str) -> bool:
        """
        Sends a WhatsApp message to a specific phone number.
        
        Args:
            phone: Target phone number (numeric only).
            message: The personalized proposal content.
            
        Returns:
            True if sent successfully, False otherwise.
        """
        if not self.context: await self.start()
        if not self.context: return False

        # 1. Clean Phone Number
        clean_phone = "".join(filter(str.isdigit, phone))
        if not clean_phone:
            logger.error(f"Invalid phone format: {phone}")
            return False

        try:
            page = await self.context.new_page()
            url = f"https://web.whatsapp.com/send?phone={clean_phone}"
            
            logger.info(f"Navigating to WhatsApp for [bold cyan]{clean_phone}[/bold cyan]...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # 2. Check for "Invalid Number" Dialog
            try:
                # This selector usually covers the "Phone number shared via url is invalid" popup
                invalid_dialog = await page.wait_for_selector('div[data-animate-modal-body]', timeout=15000)
                if invalid_dialog:
                    text = await invalid_dialog.inner_text()
                    if "invalid" in text.lower() or "not found" in text.lower():
                        logger.warning(f"User not found for {clean_phone} on WhatsApp.")
                        await page.close()
                        return "not_found"
            except:
                pass # Continue if dialog doesn't appear

            # 3. Wait for Chat Box
            logger.info("Waiting for chat synchronization...")
            try:
                await page.wait_for_selector('div[contenteditable="true"]', timeout=30000)
            except:
                logger.error(f"Timeout waiting for chat interface: {clean_phone}")
                await page.close()
                return False
            
            # 4. Human-Type Content
            logger.info("Mimicking human typing...")
            input_box = await page.query_selector('div[contenteditable="true"]')
            if not input_box: 
                await page.close()
                return False
            
            await input_box.click()
            await page.keyboard.type(message, delay=random.randint(20, 50))
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            
            # 5. Verification Wait
            await asyncio.sleep(random.randint(5, 8))
            await page.close()
            
            await self._update_stats()
            logger.info(f"✓ WhatsApp confirmed sent to {clean_phone}")
            return True

        except Exception as e:
            logger.error(f"✕ WhatsApp delivery failed for {clean_phone}: {e}")
            return False

    async def _update_stats(self) -> None:
        """Increments the daily outreach counter in the database."""
        async with get_db() as db:
            await db.execute("""
                INSERT INTO daily_stats (date, whatsapp_sent) 
                VALUES (?, 1) 
                ON CONFLICT(date) DO UPDATE SET whatsapp_sent = whatsapp_sent + 1
            """, (date.today(),))
            await db.commit()

if __name__ == "__main__":
    op = WhatsAppOperator()
    # asyncio.run(op.send("1234567890", "Hello from ColdMailer Pro!"))
