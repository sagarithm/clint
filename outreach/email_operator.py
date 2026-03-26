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
        i = 1
        while True:
            user = os.getenv(f"SMTP_USER_{i}")
            pwd = os.getenv(f"SMTP_PASS_{i}")
            if not user or not pwd: break
            
            accounts.append({
                "user": user,
                "pass": pwd,
                "host": os.getenv(f"SMTP_HOST_{i}", "smtp.gmail.com"),
                "port": int(os.getenv(f"SMTP_PORT_{i}", "587"))
            })
            i += 1
        return accounts

    async def send(self, to_email: str, subject: str, body: str) -> bool:
        """
        Sends a personalized email using the next available account in rotation.
        
        Args:
            to_email: Recipient address.
            subject: Email subject.
            body: Email content (HTML supported).
            
        Returns:
            True if sent successfully, False otherwise.
        """
        if not self.accounts:
            logger.error("No SMTP accounts configured. Set SMTP_USER_1/SMTP_PASS_1 in .env.")
            return False

        account = self.accounts[self.current_idx]
        self.current_idx = (self.current_idx + 1) % len(self.accounts)

        msg = MIMEMultipart()
        msg["From"] = f"{settings.SENDER_NAME} <{account['user']}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html" if "<br" in body or "<p" in body else "plain"))

        try:
            logger.info(f"Sending email to [bold magenta]{to_email}[/bold magenta] via {account['user']}...")
            
            # Randomized delay to mimic human behavior
            await asyncio.sleep(random.uniform(settings.MIN_DELAY_SECONDS, settings.MAX_DELAY_SECONDS))
            
            async with aiosmtplib.SMTP(
                hostname=account['host'], 
                port=account['port'], 
                use_tls=False, 
                start_tls=True
            ) as smtp:
                await smtp.login(account['user'], account['pass'])
                await smtp.send_message(msg)
                
            logger.info(f"✓ Email delivered successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"✕ SMTP delivery failed for {to_email}: {e}")
            return False

if __name__ == "__main__":
    op = EmailOperator()
    # asyncio.run(op.send("test@example.com", "Hello", "Content"))
