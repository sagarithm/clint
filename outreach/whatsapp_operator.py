import asyncio
import random
import os
from playwright.async_api import async_playwright
from core.config import settings
from core.logger import logger
import aiosqlite
from datetime import date

class WhatsAppOperator:
    def __init__(self):
        self.session_path = os.path.join("data", "whatsapp_session")
        os.makedirs(self.session_path, exist_ok=True)
        self.browser_context = None
        self.playwright = None

    async def start(self):
        """Starts a persistent browser context for batch sending."""
        if self.browser_context:
            return
        
        try:
            self.playwright = await async_playwright().start()
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            
            logger.info("Starting WhatsApp Session...")
            self.browser_context = await self.playwright.chromium.launch_persistent_context(
                self.session_path,
                headless=False,
                user_agent=random.choice(user_agents),
                no_viewport=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
        except Exception as e:
            logger.error(f"Failed to start WhatsApp session: {e}")
            self.playwright = None
            self.browser_context = None

    async def stop(self):
        """Closes the browser session."""
        try:
            if self.browser_context:
                await self.browser_context.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error during WhatsApp session cleanup: {e}")
        finally:
            self.browser_context = None
            self.playwright = None

    async def can_send(self) -> bool:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            async with db.execute("SELECT whatsapp_sent FROM daily_stats WHERE date = ?", (date.today(),)) as cursor:
                row = await cursor.fetchone()
                if row and row[0] >= settings.DAILY_WHATSAPP_LIMIT:
                    return False
        return True

    async def send(self, phone: str, message: str):
        if not await self.can_send():
            logger.warning("Daily WhatsApp limit reached.")
            return False

        if not self.browser_context:
            await self.start()
            if not self.browser_context: return False

        # Format phone
        phone = "".join(filter(str.isdigit, phone))
        if not phone:
            logger.error("Invalid phone number.")
            return False

        try:
            page = await self.browser_context.new_page()
            url = f"https://web.whatsapp.com/send?phone={phone}&text="
            
            logger.info(f"Navigating to WhatsApp for [cyan]{phone}[/cyan]...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Resilient wait for the 'White Screen' to pass (decryption/loading)
            logger.info("Waiting for WhatsApp decryption/sync (this may take a moment)...")
            try:
                # Wait for EITHER the chat input OR the 'Starting' screen to pass
                await page.wait_for_selector('div[contenteditable="true"]', timeout=75000)
            except Exception:
                logger.warning("Decryption is taking longer than expected. Retrying wait...")
                await page.wait_for_selector('div[contenteditable="true"]', timeout=30000)

            # Human-like typing
            logger.info(f"Typing message to {phone}...")
            input_box = await page.query_selector('div[contenteditable="true"]')
            await input_box.click()
            
            # Type in chunks to be faster but still human
            await page.keyboard.type(message, delay=random.randint(10, 50))

            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            
            # Wait a few seconds to ensure message actually sends before closing the tab
            await asyncio.sleep(5)
            await page.close()
            
            await self._update_stats()
            logger.info(f"WhatsApp message sent to [green]{phone}[/green]")
            return True

        except Exception as e:
            logger.error(f"WhatsApp error for {phone}: {e}")
            return False

    async def _update_stats(self):
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute("""
                INSERT INTO daily_stats (date, whatsapp_sent) 
                VALUES (?, 1) 
                ON CONFLICT(date) DO UPDATE SET whatsapp_sent = whatsapp_sent + 1
            """, (date.today(),))
            await db.commit()

    async def _update_stats(self):
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute("""
                INSERT INTO daily_stats (date, whatsapp_sent) 
                VALUES (?, 1) 
                ON CONFLICT(date) DO UPDATE SET whatsapp_sent = whatsapp_sent + 1
            """, (date.today(),))
            await db.commit()

if __name__ == "__main__":
    op = WhatsAppOperator()
    # asyncio.run(op.send("919876543210", "Hello! This is a test."))
