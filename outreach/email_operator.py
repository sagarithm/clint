import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import asyncio
import random
import os
from core.config import settings
from core.logger import logger
from dotenv import load_dotenv
from datetime import date

class EmailOperator:
    def __init__(self):
        self.accounts = self._load_accounts()
        self.current_idx = 0

    def _load_accounts(self):
        # Load Account 1 from central settings
        accounts = []
        if settings.SMTP_USER_1 and settings.SMTP_PASS_1:
            accounts.append({
                "user": settings.SMTP_USER_1,
                "pass": settings.SMTP_PASS_1,
                "host": settings.SMTP_HOST_1,
                "port": settings.SMTP_PORT_1
            })
        
        # Support for additional accounts via environment (Account 2+)
        i = 2
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
        msg["From"] = f"Pixartual Studio <{settings.FROM_EMAIL}>"
        msg["Reply-To"] = settings.FROM_EMAIL
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
