import asyncio
import aiosqlite
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

from core.config import settings
from core.database import init_db
from scrapers.maps import MapsScraper
from scrapers.web_crawler import WebCrawler
from engine.auditor import AIAuditor
from engine.proposer import Proposer
from outreach.email_operator import EmailOperator
from outreach.whatsapp_operator import WhatsAppOperator
from core.logger import logger
from core.scorer import score_lead

console = Console()

async def interactive_outreach():
    await init_db()
    
    # 1. User Input
    mode = Prompt.ask("[bold cyan]Select Outreach Mode[/bold cyan]", choices=["Initial", "Resume", "Follow-up"], default="Initial")
    dry_run = Confirm.ask("[bold yellow]Enable Dry Run?[/bold yellow] (Simulates outreach without sending)", default=False)
    
    auditor = AIAuditor()
    proposer = Proposer()
    email_op = EmailOperator()
    whatsapp_op = WhatsAppOperator()
    web_crawler = WebCrawler()

    query = ""
    leads = []
    target_count = 10

    if mode == "Initial":
        query = Prompt.ask("[bold cyan]Enter Search Query[/bold cyan] (e.g., 'Schools in Kadi 382715')")
        target_count = int(Prompt.ask("[bold cyan]How many leads do you need?[/bold cyan]", default="10"))
        
        # Check if we already have leads for this query that are not sent
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM leads WHERE status = 'new' AND category = ? LIMIT ?", (query, target_count)) as cursor:
                leads = await cursor.fetchall()

        if not leads or len(leads) < target_count:
            console.print(f"\n[bold yellow]Step 1: Scraping NEW Leads for '{query}'...[/bold yellow]")
            maps_scraper = MapsScraper()
            await maps_scraper.scrape(query, max_results=target_count)
            # Re-fetch
            async with aiosqlite.connect(settings.DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM leads WHERE status = 'new' AND category = ? ORDER BY rating DESC LIMIT ?", (query, target_count)) as cursor:
                    leads = await cursor.fetchall()

    elif mode == "Resume":
        console.print("\n[bold yellow]Scanning for NEW leads captured but not yet sent...[/bold yellow]")
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM leads WHERE status = 'new' ORDER BY id DESC") as cursor:
                leads = await cursor.fetchall()
        if not leads:
            console.print("[bold red]No pending leads found to resume.[/bold red]")
            return
        query = "Resume Batch"
        target_count = len(leads)

    if mode in ["Initial", "Resume"]:
        # Session Subfolder Logic
        base_screenshot_dir = "data/screenshots"
        os.makedirs(base_screenshot_dir, exist_ok=True)
        existing_dirs = [d for d in os.listdir(base_screenshot_dir) if os.path.isdir(os.path.join(base_screenshot_dir, d)) and d.startswith("S")]
        session_num = 1
        if existing_dirs:
            try:
                session_num = max([int(d[1:]) for d in existing_dirs if d[1:].isdigit()]) + 1
            except: pass
        session_folder = os.path.join(base_screenshot_dir, f"S{session_num:03d}")
        os.makedirs(session_folder, exist_ok=True)

        processed_leads = []
        console.print("\n[bold yellow]Step 2: Enriching Leads (Finding Emails & Scoring)...[/bold yellow]")
        
        for i, lead in enumerate(leads):
            lead_data = dict(lead)
            if lead_data['website']:
                res = await web_crawler.crawl(lead_data['website'], lead_data['name'], output_folder=session_folder)
                emails = res.get('emails', [])
                lead_data['email'] = ",".join(emails) if emails else "N/A"
                lead_data['social_links'] = str(res.get("social_links", {}))
                lead_data['screenshot_path'] = res.get("screenshot_path")
                lead_data['about_us_info'] = res.get("about_us_info")
            
            lead_data['score'] = score_lead(lead_data)
            processed_leads.append(lead_data)
            
            # Update DB with enriched data
            async with aiosqlite.connect(settings.DB_PATH) as db:
                await db.execute("""
                    UPDATE leads SET email = ?, social_links = ?, screenshot_path = ?, about_us_info = ?, score = ?
                    WHERE id = ?
                """, (lead_data['email'], lead_data['social_links'], lead_data['screenshot_path'], lead_data['about_us_info'], lead_data['score'], lead_data['id']))
                await db.commit()

        show_lead_table(processed_leads, query)
        await start_outreach_phase(processed_leads, auditor, proposer, email_op, whatsapp_op, dry_run=dry_run)

    else:
        # Follow-up Mode Logic
        console.print("\n[bold yellow]Scanning for leads ready for Follow-up (>3 days)...[/bold yellow]")
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            # Simplified: any lead sent more than 3 days ago
            await db.execute("UPDATE leads SET status='follow_up_ready' WHERE status='sent' AND last_outreach < datetime('now', '-3 days')")
            await db.commit()
            
            async with db.execute("SELECT * FROM leads WHERE status = 'follow_up_ready' ORDER BY score DESC") as cursor:
                leads = await cursor.fetchall()
        
        if not leads:
            console.print("[bold red]No leads found ready for follow-up today.[/bold red]")
            return
        
        processed_leads = [dict(l) for l in leads]
        show_lead_table(processed_leads, "Follow-up Queue")
        await start_outreach_phase(processed_leads, auditor, proposer, email_op, whatsapp_op, dry_run=dry_run)

def show_lead_table(leads, title):
    table = Table(title=title)
    table.add_column("No.", justify="right", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Score", justify="center", style="bold green")
    table.add_column("Step", justify="center", style="yellow")
    table.add_column("Website", style="blue")
    table.add_column("Email", style="magenta")
    
    for i, lead in enumerate(leads):
        table.add_row(
            str(i+1),
            lead['name'],
            str(lead.get('score', 0)),
            str(lead.get('outreach_step', 0)),
            lead.get('website', 'N/A') or "N/A",
            lead.get('email', 'N/A') or "N/A"
        )
    console.print(table)

async def start_outreach_phase(leads, auditor, proposer, email_op, whatsapp_op, dry_run=False):
    total = len(leads)
    has_email = len([l for l in leads if l['email'] and l['email'] != "N/A"])
    has_phone = len([l for l in leads if l['phone'] and l['phone'] != "N/A"])
    
    console.print(f"\n[bold green]Overview:[/bold green]")
    console.print(f"Total Leads: {total} | Emails: {has_email} | Phones: {has_phone}")

    choice = Prompt.ask("\n[bold cyan]Choose Primary Outreach Channel[/bold cyan]", choices=["Email", "WhatsApp", "None"], default="Email")

    if choice == "Email":
        if has_email > 0:
            if Confirm.ask(f"[bold cyan]Send emails to {has_email} leads?[/bold cyan]"):
                await send_emails(leads, auditor, proposer, email_op, dry_run=dry_run)
        
        wa_leads = [l for l in leads if l['phone'] and l['phone'] != "N/A" and (not l['email'] or l['email'] == "N/A")]
        if wa_leads:
            console.print(f"\n[bold yellow]Leads with Phone but NO Email: {len(wa_leads)}[/bold yellow]")
            if Confirm.ask("[bold cyan]Send WhatsApp messages to these leads?[/bold cyan]"):
                await send_whatsapp(wa_leads, proposer, whatsapp_op, dry_run=dry_run)

    elif choice == "WhatsApp":
        if has_phone > 0:
            if Confirm.ask(f"[bold cyan]Send WhatsApp messages to {has_phone} leads?[/bold cyan]"):
                await send_whatsapp(leads, proposer, whatsapp_op, dry_run=dry_run)
        
        email_leads = [l for l in leads if l['email'] and l['email'] != "N/A" and (not l['phone'] or l['phone'] == "N/A")]
        if email_leads:
            console.print(f"\n[bold yellow]Leads with Email but NO Phone: {len(email_leads)}[/bold yellow]")
            if Confirm.ask("[bold cyan]Send emails to these leads?[/bold cyan]"):
                await send_emails(email_leads, auditor, proposer, email_op, dry_run=dry_run)

    console.print("\n[bold green]Outreach Session Complete![/bold green]")

async def send_emails(leads, auditor, proposer, email_op, dry_run=False):
    sent_emails = 0
    for lead in [l for l in leads if l['email'] and l['email'] != "N/A"]:
        console.print(f"Processing Email for: {lead['name']}...")
        audit = await auditor.audit_website(lead['name'], lead)
        
        # Increment step for proposal generation
        current_step = lead.get('outreach_step', 0) + 1
        
        subject, body = await proposer.generate_proposal(
            lead['name'], audit, 'email', 
            lead.get('rating', 0.0), lead.get('reviews_count', 0), 
            lead.get('business_category'), bool(lead.get('website')), 
            lead.get('about_us_info'), current_step
        )
        
        if dry_run:
            logger.info(f"[bold yellow][DRY RUN][/bold yellow] Would send email to {lead['name']} ({lead['email']})")
            continue

        email_to = lead['email'].split(',')[0]
        success = await email_op.send(email_to, subject, body)
        
        if success:
            sent_emails += 1
            async with aiosqlite.connect(settings.DB_PATH) as db:
                await db.execute("""
                    UPDATE leads SET status = 'sent', outreach_step = ?, last_outreach = datetime('now') 
                    WHERE id = ?
                """, (current_step, lead['id']))
                await db.execute("INSERT INTO outreach_history (lead_id, channel, content, status) VALUES (?, 'email', ?, 'sent')", (lead['id'], body))
                await db.commit()
    console.print(f"[bold green]Successfully sent {sent_emails} emails.[/bold green]")

async def send_whatsapp(leads, proposer, whatsapp_op, dry_run=False):
    sent_wa = 0
    whatsapp_leads = [l for l in leads if l['phone'] and l['phone'] != "N/A"]
    
    if not whatsapp_leads:
        return

    try:
        if not dry_run:
            await whatsapp_op.start()

        for lead in whatsapp_leads:
            console.print(f"Processing WhatsApp for: {lead['name']}...")
            audit = "Focused on digital presence and local growth."
            
            current_step = lead.get('outreach_step', 0) + 1
            subject, body = await proposer.generate_proposal(
                lead['name'], audit, 'whatsapp', 
                lead.get('rating', 0.0), lead.get('reviews_count', 0), 
                lead.get('business_category'), bool(lead.get('website')), 
                lead.get('about_us_info'), current_step
            )
            
            if dry_run:
                logger.info(f"[bold yellow][DRY RUN][/bold yellow] Would send WhatsApp to {lead['name']} ({lead['phone']})")
                continue

            success = await whatsapp_op.send(lead['phone'], body)
            
            if success:
                sent_wa += 1
                async with aiosqlite.connect(settings.DB_PATH) as db:
                    await db.execute("""
                        UPDATE leads SET status = 'sent', outreach_step = ?, last_outreach = datetime('now') 
                        WHERE id = ?
                    """, (current_step, lead['id']))
                    await db.execute("INSERT INTO outreach_history (lead_id, channel, content, status) VALUES (?, 'whatsapp', ?, 'sent')", (lead['id'], body))
                    await db.commit()
                
                # Random delay between WhatsApp messages for safety
                delay = random.uniform(settings.MIN_DELAY, settings.MAX_DELAY)
                logger.info(f"Waiting {delay:.1f}s before next WhatsApp lead...")
                await asyncio.sleep(delay)

    finally:
        if not dry_run:
            await whatsapp_op.stop()

    console.print(f"[bold green]Successfully sent {sent_wa} WhatsApp messages.[/bold green]")

if __name__ == "__main__":
    asyncio.run(interactive_outreach())
