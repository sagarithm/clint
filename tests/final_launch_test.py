import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_db
from outreach.email_operator import EmailOperator
from outreach.whatsapp_operator import WhatsAppOperator
from engine.proposer import Proposer
from core.logger import logger

async def run_final_test():
    await init_db()
    proposer = Proposer()
    
    # --- TEST 1: EMAIL ---
    email_target = "sagarithm@gmail.com"
    client_name = "Anchal Kewat"
    email_service = "Website Development & AI Agent Integration"
    
    logger.info(f"Generating Email for {client_name} at {email_target}...")
    subject, email_body = await proposer.generate_proposal(
        client_name, "Needs a modern website with integrated AI agents to automate project workflows.", 
        channel="email", service=email_service
    )
    
    email_op = EmailOperator()
    try:
        email_success = await email_op.send(email_target, subject, email_body)
        if email_success:
            logger.info(f"[bold green]✓ Email delivered to {email_target}[/bold green]")
        else:
            logger.error("[bold red]✗ Email failed. Check SMTP settings.[/bold red]")
    except Exception as e:
        logger.error(f"Email Exception: {e}")

    # --- TEST 2: WHATSAPP ---
    wa_phone = "+91 9589570105" # Using the verified test number
    wa_service = "Digital Brand Scaling & Performance Marketing"
    
    logger.info(f"Generating WhatsApp for {client_name} at {wa_phone}...")
    _, wa_body = await proposer.generate_proposal(
        client_name, "Wants to explore other high-impact services for brand expansion.", 
        channel="whatsapp", service=wa_service
    )
    
    whatsapp_op = WhatsAppOperator()
    try:
        await whatsapp_op.start()
        wa_success = await whatsapp_op.send(wa_phone, wa_body)
        if wa_success is True:
            logger.info(f"[bold green]✓ WhatsApp delivered to {wa_phone}[/bold green]")
        elif wa_success == "not_found":
            logger.warning(f"[bold yellow]⚠ WhatsApp: User {wa_phone} not found on WA.[/bold yellow]")
        else:
            logger.error("[bold red]✗ WhatsApp failed.[/bold red]")
    except Exception as e:
        logger.error(f"WhatsApp Exception: {e}")
    finally:
        await whatsapp_op.stop()

if __name__ == "__main__":
    asyncio.run(run_final_test())
