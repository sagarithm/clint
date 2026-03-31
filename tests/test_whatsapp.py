import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_db
from outreach.whatsapp_operator import WhatsAppOperator
from engine.proposer import Proposer
from core.logger import logger

async def run_test():
    await init_db()
    
    lead_name = "Pixartual Support"
    phone = "+91 9589570105"
    service = "AI Automation Suite"
    
    # 1. Generate Proposal
    proposer = Proposer()
    logger.info(f"Generating test proposal for {lead_name}...")
    subject, body = await proposer.generate_proposal(
        lead_name, "Internal system health check.", channel="whatsapp",
        service=service
    )
    
    logger.info(f"Generated Message:\n{body}")
    
    # 2. Send via WhatsApp
    whatsapp_op = WhatsAppOperator()
    try:
        await whatsapp_op.start()
        success = await whatsapp_op.send(phone, body)
        
        if success is True:
            logger.info("[bold green]✓ WhatsApp Test: Message delivered.[/bold green]")
        elif success == "not_found":
            logger.warning("[bold yellow]⚠ WhatsApp Test: User correctly identified as 'Not Found'.[/bold yellow]")
        else:
            logger.error("[bold red]✗ WhatsApp Test: Delivery error.[/bold red]")
            
    finally:
        await whatsapp_op.stop()

if __name__ == "__main__":
    asyncio.run(run_test())
