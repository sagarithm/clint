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

        # Format phone (clean non-digits)
        phone = "".join(filter(str.isdigit, phone))
        if not phone:
            logger.error("Invalid phone number provided.")
            return False

        async with async_playwright() as p:
            # Load session to avoid repeating QR scan
            browser = await p.chromium.launch_persistent_context(
                self.session_path,
                headless=False, # Must be False for initial QR scan and interaction
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await browser.new_page()
            url = f"https://web.whatsapp.com/send?phone={phone}&text="
            
            logger.info(f"Opening WhatsApp Web for [cyan]{phone}[/cyan]...")
            await page.goto(url)

            try:
                # Wait for the main app to load
                await page.wait_for_selector('div[contenteditable="true"]', timeout=60000)
                
                # Human-like typing
                logger.info(f"Typing message to {phone}...")
                input_box = await page.query_selector('div[contenteditable="true"]')
                
                # We don't use 'fill' for WhatsApp as it doesn't trigger listeners well
                # Instead, we click and then type char by char
                await input_box.click()
                for char in message:
                    await page.keyboard.type(char)
                    await asyncio.sleep(random.uniform(0.01, 0.1)) # Human-like typing speed

                await asyncio.sleep(1)
                await page.keyboard.press("Enter")
                
                await asyncio.sleep(random.uniform(settings.MIN_DELAY, settings.MAX_DELAY))
                
                await self._update_stats()
                logger.info(f"WhatsApp message sent to [green]{phone}[/green]")
                
                await browser.close()
                return True

            except Exception as e:
                logger.error(f"Failed to send WhatsApp to {phone}: {e}")
                await browser.close()
                return False

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
