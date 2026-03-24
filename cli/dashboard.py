import asyncio
import csv
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from core.logger import logger
from core.database import init_db
from scrapers.maps import MapsScraper
from scrapers.web_crawler import WebCrawler
from engine.auditor import AIAuditor
from engine.proposer import Proposer
from outreach.email_operator import EmailOperator
from outreach.whatsapp_operator import WhatsAppOperator
import aiosqlite
from core.config import settings

console = Console()

class ColdMailerApp:
    def __init__(self):
        self.maps_scraper = MapsScraper()
        self.web_crawler = WebCrawler()
        self.auditor = AIAuditor()
        self.proposer = Proposer()
        self.email_op = EmailOperator()
        self.whatsapp_op = WhatsAppOperator()

    async def show_stats(self):
        async with aiosqlite.connect(settings.DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM leads") as c: total = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM leads WHERE status = 'sent'") as c: sent = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM leads WHERE status = 'pending_review'") as c: pending = (await c.fetchone())[0]

        table = Table(title="ColdMailer Stats")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="green")
        table.add_row("Total Leads", str(total))
        table.add_row("Sent Proposals", str(sent))
        table.add_row("Pending Review", str(pending))
        
        console.print(Panel(table, title="Dashboard", border_style="bold magenta"))

    async def run_pipeline(self, query: str, limit: int = 10):
        console.print(f"[bold yellow]Starting High-Tech Pipeline for: [/bold yellow][cyan]{query}[/cyan]")
        
        # 1. Scraping
        await self.maps_scraper.scrape(query, limit)

        # 2. Enrich & Audit
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM leads WHERE status = 'new'") as cursor:
                leads = await cursor.fetchall()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            enroll_task = progress.add_task("[cyan]Enriching & Auditing Leads...", total=len(leads))
            
            for lead in leads:
                # Crawl
                res = await self.web_crawler.crawl(lead['website'], lead['name'])
                if not res:
                    continue
                
                # Update Database with new crawl data
                async with aiosqlite.connect(settings.DB_PATH) as db:
                    await db.execute("""
                        UPDATE leads 
                        SET email = ?, social_links = ?, screenshot_path = ?, about_us_info = ?
                        WHERE id = ?
                    """, (",".join(res.get('emails', [])), str(res.get('social_links', {})), 
                          res.get('screenshot_path'), res.get('about_us_info'), lead['id']))
                    await db.commit()

                # Audit
                audit = await self.auditor.audit_website(lead['name'], res)
                
                # Update DB
                async with aiosqlite.connect(settings.DB_PATH) as db:
                    await db.execute("""
                        UPDATE leads 
                        SET email = ?, social_links = ?, audit_summary = ?, status = 'pending_review'
                        WHERE id = ?
                    """, (emails, social, audit, lead['id']))
                    await db.commit()
                
                progress.advance(enroll_task)
        
        console.print(Panel(f"[bold green]Pipeline Complete![/bold green]\nFound and Audited {len(leads)} new leads.", border_style="bold green"))
        
        # Auto-Export
        await self.export_to_csv()
        
        # Ask for immediate outreach
        choice = await asyncio.to_thread(input, "\nWould you like to start outreach for these leads now? (y/n): ")
        if choice.lower() == 'y':
            await self.review_and_send()

    async def main_menu(self):
        console.print(Panel("COLDMAILER AUTOMATION ENGINE v1.0", style="bold blue"))
        while True:
            await self.show_stats()
            console.print("\n[bold cyan]Options:[/bold cyan]")
            console.print("1. [green]Search & Audit Leads[/green]")
            console.print("2. [yellow]Review & Send Initial Proposals[/yellow]")
            console.print("3. [cyan]Send Reminders / Follow-ups[/cyan]")
            console.print("4. [blue]Export Data to CSV[/blue]")
            console.print("5. [red]Exit[/red]")
            
            choice = await asyncio.to_thread(input, "\nSelect an option: ")
            
            if choice == "1":
                q = await asyncio.to_thread(input, "Enter search query (e.g. 'Coffee shops NYC'): ")
                limit = await asyncio.to_thread(input, "Enter limit (default 10): ")
                await self.run_pipeline(q, int(limit) if limit else 10)
            elif choice == "2":
                await self.review_and_send()
            elif choice == "3":
                await self.send_reminders()
            elif choice == "4":
                await self.export_to_csv()
            elif choice == "5":
                break

    async def review_and_send(self):
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM leads WHERE status = 'pending_review'") as cursor:
                leads = await cursor.fetchall()

        if not leads:
            console.print("[yellow]No leads pending review.[/yellow]")
            return

        for lead in leads:
            console.print(f"\n[bold green]Lead: {lead['name']}[/bold green]")
            console.print(f"Website: {lead['website']}")
            if lead['business_category']: console.print(f"Category: {lead['business_category']}")
            if lead['rating']: console.print(f"Rating: {lead['rating']} ({lead['reviews_count']} reviews)")
            if lead['screenshot_path']: console.print(f"Screenshot: [dim]{lead['screenshot_path']}[/dim]")
            console.print(f"Audit: {lead['audit_summary']}")
            
            choice = await asyncio.to_thread(input, "Generate Proposals for Review? (y/n/skip): ")
            if choice.lower() == 'y':
                channels = []
                if lead['email']: channels.append('email')
                if lead['phone']: channels.append('whatsapp')
                
                for channel in channels:
                    console.print(f"\n[bold yellow]Generating {channel.upper()} Proposal...[/bold yellow]")
                    proposal = await self.proposer.generate_proposal(
                        lead['name'], lead['audit_summary'], channel,
                        rating=lead['rating'] or 0.0,
                        reviews_count=lead['reviews_count'] or 0,
                        business_category=lead['business_category'],
                        has_website=bool(lead['website']),
                        about_us_info=lead.get('about_us_info')
                    )
                    
                    console.print(Panel(proposal, title=f"{channel.upper()} PREVIEW for {lead['name']}", border_style="cyan"))
                    
                    confirm = await asyncio.to_thread(input, f"Send this {channel}? (y/n): ")
                    if confirm.lower() == 'y':
                        if channel == 'email':
                            success = await self.email_op.send(lead['email'].split(",")[0], f"Important: Performance Audit for {lead['name']}", proposal)
                        else:
                            success = await self.whatsapp_op.send(lead['phone'], proposal)
                        
                        async with aiosqlite.connect(settings.DB_PATH) as db:
                            await db.execute("""
                                INSERT INTO outreach_history (lead_id, channel, content, status)
                                VALUES (?, ?, ?, ?)
                            """, (lead['id'], channel, proposal, 'sent' if success else 'failed'))
                            await db.commit()
                        
                        console.print(f"[bold green]{channel.capitalize()} Sent![/bold green]" if success else f"[bold red]{channel.capitalize()} Failed.[/bold red]")
                
                async with aiosqlite.connect(settings.DB_PATH) as db:
                    await db.execute("UPDATE leads SET status = 'sent' WHERE id = ?", (lead['id'],))
                    await db.commit()
            elif choice.lower() == 'skip':
                continue

    async def send_reminders(self):
        console.print(Panel("[bold yellow]Reminder / Follow-up Manager[/bold yellow]", border_style="yellow"))
        
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            # Find leads sent at least 1 message but status is still 'sent' (no reply tracked yet)
            async with db.execute("SELECT * FROM leads WHERE status = 'sent' LIMIT 10") as cursor:
                leads = await cursor.fetchall()
        
        if not leads:
            console.print("[yellow]No leads currently pending for reminders.[/yellow]")
            return

        for lead in leads:
            console.print(f"\n[bold cyan]Nudging Lead: {lead['name']}[/bold cyan] ({lead['website'] or 'No Website'})")
            
            choice = await asyncio.to_thread(input, "Generate Reminder? (y/n/skip): ")
            if choice.lower() == 'y':
                channels = []
                if lead['email']: channels.append('email')
                if lead['phone']: channels.append('whatsapp')
                
                for channel in channels:
                    console.print(f"\n[bold yellow]Generating {channel.upper()} Reminder...[/bold yellow]")
                    # Custom logic for reminder in proposer
                    proposal = await self.proposer.generate_proposal(
                        lead['name'], lead['audit_summary'], channel,
                        rating=lead['rating'] or 0.0,
                        has_website=bool(lead['website']),
                        about_us_info=lead.get('about_us_info'),
                        is_reminder=True
                    )
                    
                    console.print(Panel(proposal, title=f"REMINDER PREVIEW ({channel.upper()})", border_style="yellow"))
                    
                    confirm = await asyncio.to_thread(input, f"Send this reminder? (y/n): ")
                    if confirm.lower() == 'y':
                        if channel == 'email':
                            success = await self.email_op.send(lead['email'].split(",")[0], f"Following up: Audit for {lead['name']}", proposal)
                        else:
                            success = await self.whatsapp_op.send(lead['phone'], proposal)
                        
                        async with aiosqlite.connect(settings.DB_PATH) as db:
                            await db.execute("""
                                INSERT INTO outreach_history (lead_id, channel, content, status)
                                VALUES (?, ?, ?, ?)
                            """, (lead['id'], channel, proposal, 'reminder_sent' if success else 'failed'))
                            await db.commit()
                        
                        console.print(f"[bold green]Reminder Sent![/bold green]" if success else f"[bold red]Failed.[/bold red]")
                
                async with aiosqlite.connect(settings.DB_PATH) as db:
                    await db.execute("UPDATE leads SET status = 'reminder_sent' WHERE id = ?", (lead['id'],))
                    await db.commit()
            elif choice.lower() == 'skip':
                continue
        os.makedirs("data", exist_ok=True)
        
        # Expert Leads
        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM leads") as cursor:
                leads = await cursor.fetchall()
            
            if leads:
                keys = leads[0].keys()
                with open("data/leads_export.csv", "w", newline="", encoding="utf-8") as f:
                    dict_writer = csv.DictWriter(f, fieldnames=keys)
                    dict_writer.writeheader()
                    dict_writer.writerows([dict(row) for row in leads])
                console.print("[bold green]Leads exported to data/leads_export.csv[/bold green]")

            # Export Outreach History
            async with db.execute("SELECT * FROM outreach_history") as cursor:
                history = await cursor.fetchall()
            
            if history:
                keys = history[0].keys()
                with open("data/outreach_history_export.csv", "w", newline="", encoding="utf-8") as f:
                    dict_writer = csv.DictWriter(f, fieldnames=keys)
                    dict_writer.writeheader()
                    dict_writer.writerows([dict(row) for row in history])
                console.print("[bold green]Outreach history exported to data/outreach_history_export.csv[/bold green]")
            else:
                console.print("[yellow]No outreach history found to export.[/yellow]")

if __name__ == "__main__":
    app = ColdMailerApp()
    asyncio.run(init_db())
    asyncio.run(app.main_menu())
