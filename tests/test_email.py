import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_db
from outreach.email_operator import EmailOperator
from engine.proposer import Proposer
from core.logger import logger

async def run_test():
    await init_db()
    
    lead_name = "Pixartual Support"
    email = "hello@pixartual.studio"
    service = "AI Branding & Outreach"
    
    # 1. Generate Proposal
    proposer = Proposer()
    logger.info(f"Generating test email for {lead_name}...")
    subject, body = await proposer.generate_proposal(
        lead_name, "Internal email delivery health check.", channel="email",
        service=service
    )
    
    logger.info(f"Subject: {subject}")
    
    # 2. Send via Email
    email_op = EmailOperator()
    try:
        success = await email_op.send(email, subject, body)
        
        if success:
            logger.info("[bold green]✓ Email Test: Message delivered.[/bold green]")
        else:
            logger.error("[bold red]✗ Email Test: Delivery error. Check SMTP settings.[/bold red]")
            
    except Exception as e:
        logger.error(f"Email Test Exception: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
