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
    query = Prompt.ask("[bold cyan]Enter Search Query[/bold cyan] (e.g., 'Schools in Kadi 382715')")
    target_count = int(Prompt.ask("[bold cyan]How many leads do you need?[/bold cyan]", default="10"))
    
    maps_scraper = MapsScraper()
    web_crawler = WebCrawler()
    auditor = AIAuditor()
    proposer = Proposer()
    email_op = EmailOperator()
    whatsapp_op = WhatsAppOperator()
    
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

    console.print(f"\n[bold yellow]Step 1: Scraping Leads for '{query}'...[/bold yellow]")
    await maps_scraper.scrape(query, max_results=target_count)
    
    # 2. Process & Enrich
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM leads WHERE status = 'new' AND category = ? ORDER BY rating DESC", (query,)) as cursor:
            leads = await cursor.fetchall()

    if not leads:
        console.print("[bold red]No new leads found in database.[/bold red]")
        return

    table = Table(title=f"Leads Found for: {query}")
    table.add_column("No.", justify="right", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Score", justify="center", style="bold green")
    table.add_column("Website", style="blue")
    table.add_column("Email", style="magenta")
    table.add_column("Phone", style="green")

    processed_leads = []
    console.print("\n[bold yellow]Step 2: Enriching Leads (Finding Emails & Scoring)...[/bold yellow]")
    
    leads_to_process = leads[:target_count]
    for i, lead in enumerate(leads_to_process):
        lead_data = dict(lead)
        emails = []
        
        if lead_data['website']:
            res = await web_crawler.crawl(lead_data['website'], lead_data['name'], output_folder=session_folder)
            emails = res.get('emails', [])
            lead_data['email'] = ",".join(emails) if emails else "N/A"
            lead_data['social_links'] = str(res.get("social_links", {}))
            lead_data['screenshot_path'] = res.get("screenshot_path")
            lead_data['about_us_info'] = res.get("about_us_info")
        
        lead_data['score'] = score_lead(lead_data)
        processed_leads.append(lead_data)
        
        table.add_row(
            str(i+1),
            lead_data['name'],
            str(lead_data['score']),
            lead_data['website'] or "N/A",
            lead_data['email'] or "N/A",
            lead_data['phone'] or "N/A"
        )
        # Update DB with enriched data
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute("""
                UPDATE leads SET email = ?, social_links = ?, screenshot_path = ?, about_us_info = ?, score = ?
                WHERE id = ?
            """, (lead_data['email'], lead_data['social_links'], lead_data['screenshot_path'], lead_data['about_us_info'], lead_data['score'], lead_data['id']))
            await db.commit()

    console.print(table)

    # 3. Overview
    total = len(processed_leads)
    has_email = len([l for l in processed_leads if l['email'] and l['email'] != "N/A"])
    has_phone = len([l for l in processed_leads if l['phone'] and l['phone'] != "N/A"])
    has_web = len([l for l in processed_leads if l['website']])

    console.print(f"\n[bold green]Overview:[/bold green]")
    console.print(f"Total Leads: {total}")
    console.print(f"Emails Found: {has_email}")
    console.print(f"Phones Found: {has_phone}")
    console.print(f"Websites Found: {has_web} | Not Found: {total - has_web}")

    # 4. Outreach Logic Selection
    choice = Prompt.ask("\n[bold cyan]Choose Primary Outreach Channel[/bold cyan]", choices=["Email", "WhatsApp", "None"], default="Email")

    if choice == "Email":
        # Email First Flow
        if has_email > 0:
            if Confirm.ask(f"[bold cyan]Send emails to {has_email} leads?[/bold cyan]"):
                await send_emails(processed_leads, auditor, proposer, email_op)
        
        # Follow up with WA for those without email
        wa_leads = [l for l in processed_leads if l['phone'] and l['phone'] != "N/A" and (not l['email'] or l['email'] == "N/A")]
        if wa_leads:
            console.print(f"\n[bold yellow]Leads with Phone but NO Email: {len(wa_leads)}[/bold yellow]")
            if Confirm.ask("[bold cyan]Send WhatsApp messages to these leads?[/bold cyan]"):
                await send_whatsapp(wa_leads, proposer, whatsapp_op)

    elif choice == "WhatsApp":
        # WhatsApp First Flow
        if has_phone > 0:
            if Confirm.ask(f"[bold cyan]Send WhatsApp messages to {has_phone} leads?[/bold cyan]"):
                await send_whatsapp(processed_leads, proposer, whatsapp_op)
        
        # Follow up with Email for those without phone
        email_leads = [l for l in processed_leads if l['email'] and l['email'] != "N/A" and (not l['phone'] or l['phone'] == "N/A")]
        if email_leads:
            console.print(f"\n[bold yellow]Leads with Email but NO Phone: {len(email_leads)}[/bold yellow]")
            if Confirm.ask("[bold cyan]Send emails to these leads?[/bold cyan]"):
                await send_emails(email_leads, auditor, proposer, email_op)

    console.print("\n[bold green]Outreach Session Complete![/bold green]")

async def send_emails(leads, auditor, proposer, email_op):
    sent_emails = 0
    for lead in [l for l in leads if l['email'] and l['email'] != "N/A"]:
        console.print(f"Processing Email for: {lead['name']}...")
        audit = await auditor.audit_website(lead['name'], lead)
        subject, body = await proposer.generate_proposal(lead['name'], audit, 'email', lead['rating'], lead['reviews_count'], lead['business_category'], bool(lead['website']), lead['about_us_info'])
        
        email_to = lead['email'].split(',')[0]
        success = await email_op.send(email_to, subject, body)
        
        if success:
            sent_emails += 1
            async with aiosqlite.connect(settings.DB_PATH) as db:
                await db.execute("UPDATE leads SET status = 'sent' WHERE id = ?", (lead['id'],))
                await db.execute("INSERT INTO outreach_history (lead_id, channel, content, status) VALUES (?, 'email', ?, 'sent')", (lead['id'], body))
                await db.commit()
    console.print(f"[bold green]Successfully sent {sent_emails} emails.[/bold green]")

async def send_whatsapp(leads, proposer, whatsapp_op):
    sent_wa = 0
    for lead in [l for l in leads if l['phone'] and l['phone'] != "N/A"]:
        console.print(f"Processing WhatsApp for: {lead['name']}...")
        audit = "Focused on digital presence and local growth."
        subject, body = await proposer.generate_proposal(lead['name'], audit, 'whatsapp', lead['rating'], lead['reviews_count'], lead['business_category'], bool(lead['website']), lead['about_us_info'])
        
        success = await whatsapp_op.send(lead['phone'], body)
        if success:
            sent_wa += 1
            async with aiosqlite.connect(settings.DB_PATH) as db:
                await db.execute("UPDATE leads SET status = 'sent' WHERE id = ?", (lead['id'],))
                await db.execute("INSERT INTO outreach_history (lead_id, channel, content, status) VALUES (?, 'whatsapp', ?, 'sent')", (lead['id'], body))
                await db.commit()
    console.print(f"[bold green]Successfully sent {sent_wa} WhatsApp messages.[/bold green]")

if __name__ == "__main__":
    asyncio.run(interactive_outreach())
