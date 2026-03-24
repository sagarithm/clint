import aiosmtplib
from email.message import EmailMessage
import asyncio
import random
import os
from core.config import settings
from core.logger import logger
import aiosqlite
from datetime import date

class EmailOperator:
    def __init__(self):
        self.accounts = self._load_accounts()

    def _load_accounts(self):
        # Load from .env (Account 1 and 2)
        accounts = []
        for i in range(1, 3):
            user = os.getenv(f"SMTP_USER_{i}")
            password = os.getenv(f"SMTP_PASS_{i}")
            host = os.getenv(f"SMTP_HOST_{i}")
            port = os.getenv(f"SMTP_PORT_{i}")
            if user and password:
                accounts.append({
                    "user": user, 
                    "password": password, 
                    "host": host, 
                    "port": int(port) if port else 587
                })
        return accounts

    async def can_send(self) -> bool:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            async with db.execute("SELECT emails_sent FROM daily_stats WHERE date = ?", (date.today(),)) as cursor:
                row = await cursor.fetchone()
                if row and row[0] >= settings.DAILY_EMAIL_LIMIT:
                    return False
        return True

    async def send(self, to_email: str, subject: str, content: str):
        if not self.accounts:
            logger.error("No SMTP accounts configured.")
            return False

        if not await self.can_send():
            logger.warning("Daily email limit reached.")
            return False

        account = random.choice(self.accounts) # Rotation
        # Use alias if provided in environment, otherwise use main user email
        from_email = os.getenv("FROM_EMAIL_1") or account["user"]
        
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.set_content(content)

        try:
            # Human-like delay
            delay = random.uniform(settings.MIN_DELAY, settings.MAX_DELAY)
            logger.info(f"Waiting {delay:.1f}s before sending email to {to_email}...")
            await asyncio.sleep(delay)

            await aiosmtplib.send(
                msg,
                hostname=account["host"],
                port=account["port"],
                username=account["user"],
                password=account["password"],
                use_tls=True if account["port"] == 465 else False,
                start_tls=True if account["port"] == 587 else False,
            )
            
            await self._update_stats()
            logger.info(f"Email sent successfully to [green]{to_email}[/green] via {account['user']}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def _update_stats(self):
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute("""
                INSERT INTO daily_stats (date, emails_sent) 
                VALUES (?, 1) 
                ON CONFLICT(date) DO UPDATE SET emails_sent = emails_sent + 1
            """, (date.today(),))
            await db.commit()

if __name__ == "__main__":
    op = EmailOperator()
    # asyncio.run(op.send("test@example.com", "Hello", "Content"))
