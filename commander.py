import asyncio
import random
import os
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Prompt, Confirm
from rich.align import Align

from core.config import settings
from core.database import init_db, get_db
from core.logger import logger
from core.reliability import log_outreach_event, recently_contacted, send_with_retry
from core.scorer import score_lead
from scrapers.web_crawler import WebCrawler
from engine.director import OutreachDirector
from engine.auditor import AIAuditor
from engine.proposer import Proposer
from outreach.email_operator import EmailOperator
from outreach.whatsapp_operator import WhatsAppOperator

console = Console()

class ColdMailerCLI:
    """
    The main interactive CLI for ColdMailer Pro.
    Provides a premium 'Founder' experience for managing outreach campaigns.
    """

    def __init__(self) -> None:
        self.director = OutreachDirector()
        self.crawler = WebCrawler()
        self.auditor = AIAuditor()
        self.proposer = Proposer()
        self.email_op = EmailOperator()
        self.whatsapp_op = WhatsAppOperator()

    async def run(self) -> None:
        """Main entry point for the interactive CLI loop."""
        await init_db()
        os.system('cls' if os.name == 'nt' else 'clear')
        
        console.print(Panel(
        "[bold cyan]CLINT[/bold cyan] [white]v1.0.2[/white]\n"
        "[dim]Enterprise Intelligence & Outreach Suite[/dim]",
        border_style="bright_blue",
        expand=False
    ))
    
        while True:
            console.print("\n[bold cyan]COMMAND CENTER[/bold cyan]")
            console.print("1. [bold green]LAUNCH[/bold green] - Founder Mode (Full Auto)")
            console.print("2. [bold blue]DISCOVER[/bold blue] - Initial Lead Scrape")
            console.print("3. [bold yellow]REVIEW[/bold yellow] - Pending Leads & Proposals")
            console.print("4. [bold magenta]FOLLOW UP[/bold magenta] - Nudge Passive Leads")
            console.print("5. [bold red]EXIT[/bold red] - Shutdown Systems")
            
            choice = Prompt.ask("\n[bold cyan]Select Action[/bold cyan]", choices=["1", "2", "3", "4", "5"], default="1")
            
            if choice == "1":
                await self._handle_founder_mode()
            elif choice == "2":
                await self._handle_initial_scrape()
            elif choice == "3":
                await self._handle_resume()
            elif choice == "4":
                await self._handle_follow_up()
            elif choice == "5":
                console.print("[dim]Shutting down... Goodbye, Founder.[/dim]")
                break

    async def _handle_founder_mode(self) -> None:
        """Executes the fully autonomous 'Founder' workflow.
        [ROLE] {settings.SENDER_NAME}, Founder at Pixartual.
        """
        query = Prompt.ask("[bold cyan]Target Niche (e.g. Dentists Dallas)[/bold cyan]", default="Dentists in California")
        target = int(Prompt.ask("[bold cyan]Collection Target[/bold cyan]", default="50"))
        limit = int(Prompt.ask("[bold cyan]Send Limit[/bold cyan]", default="20"))
        
        console.print(f"\n[bold green]➜ Initiating High-Intelligence Batch for '{query}'...[/bold green]")
        await self.director.execute_autonomous_batch(query, target_count=target, send_limit=limit)
        Prompt.ask("\n[dim]Press Enter to return to Command Center...[/dim]")

    async def _handle_initial_scrape(self) -> None:
        """Manages manual lead discovery and enrichment."""
        query = Prompt.ask("[bold cyan]Enter Search Query[/bold cyan]")
        target = int(Prompt.ask("[bold cyan]Leads to Collect[/bold cyan]", default="10"))
        
        # Scrape
        await self.director.maps_scraper.scrape(query, max_results=target)
        
        # Unique Query ID for this scrape
        query_id = f"Q{random.randint(100, 999)}"
        
        # Enrichment & Scoring
        async with get_db() as db:
            async with db.execute("SELECT * FROM leads WHERE status = 'new'") as cursor:
                leads = [dict(l) for l in await cursor.fetchall()]
        
        if not leads: return
        
        console.print(f"\n[bold yellow]Analyzing {len(leads)} Prospects (Query ID: {query_id})...[/bold yellow]")
        for lead in leads:
            if lead['website']:
                res = await self.crawler.crawl(lead['website'], lead['name'], query_id=query_id)
                emails = ",".join(res.get('emails', []))
                score = score_lead({**lead, 'email': emails, 'about_us_info': res.get('about_us_info')})
                
                async with get_db() as db:
                    await db.execute(
                        "UPDATE leads SET email = ?, about_us_info = ?, score = ? WHERE id = ?",
                        (emails, res.get('about_us_info'), score, lead['id'])
                    )
                    await db.commit()
        
        await self._display_and_outreach(f"Discovery: {query}")

    async def _handle_resume(self) -> None:
        """Resumes outreach for leads that were scraped but reached."""
        await self._display_and_outreach("Pending Prospects")

    async def _handle_follow_up(self) -> None:
        """Processes leads ready for the next step in the sequence."""
        async with get_db() as db:
            # Mark leads for follow up after 3 days
            await db.execute("""
                UPDATE leads SET status = 'follow_up_ready' 
                WHERE status = 'sent' AND last_outreach < datetime('now', '-3 days')
            """)
            await db.commit()
        await self._display_and_outreach("Follow-up Queue", status_filter='follow_up_ready')

    async def _display_and_outreach(self, title: str, status_filter: str = 'new') -> None:
        """Displays leads in a table and initiates the outreach phase."""
        async with get_db() as db:
            async with db.execute(f"SELECT * FROM leads WHERE status = '{status_filter}' ORDER BY score DESC") as cursor:
                leads = [dict(l) for l in await cursor.fetchall()]

        if not leads:
            console.print("[bold red]No records found in this queue.[/bold red]")
            return

        # Display Table
        table = Table(title=f"INTELLIGENCE REPORT: {title}", header_style="bold gold1")
        table.add_column("Sr. No.", justify="right", style="dim")
        table.add_column("Score", justify="center", style="bold green")
        table.add_column("Business Name", style="white")
        table.add_column("Number", style="cyan")
        table.add_column("Email Status", justify="center", style="magenta")
        table.add_column("Web Status", style="blue")
        table.add_column("Category", style="dim")
        
        from urllib.parse import urlparse
        
        for i, l in enumerate(leads, 1):
            email_status = "[bold green]VALID[/bold green]" if l['email'] and l['email'] != "N/A" else "[dim]N/A[/dim]"
            phone = l['phone'] if l['phone'] else "[dim]N/A[/dim]"
            
            # Extract clean domain
            if l['website'] and l['website'] != "N/A":
                domain = urlparse(l['website']).netloc.replace('www.', '')
                web_status = f"[bold blue]{domain}[/bold blue]"
            else:
                web_status = "[dim]N/A[/dim]"
                
            table.add_row(str(i), str(l['score']), l['name'], phone, email_status, web_status, l['business_category'] or "Local")
        
        console.print(table)

        if Confirm.ask("\n[bold cyan]Proceed to Outreach Stage?[/bold cyan]"):
            channel = Prompt.ask("Choose Delivery Channel", choices=["Email", "WhatsApp", "Exit"], default="Email")
            if channel == "Email":
                await self._bulk_delivery(leads, 'email')
            elif channel == "WhatsApp":
                await self._bulk_delivery(leads, 'whatsapp')
        
        Prompt.ask("\n[dim]Press Enter to return...[/dim]")

    async def _bulk_delivery(self, leads: List[Dict], channel: str) -> None:
        """Orchestrates bulk delivery with live-updating status."""
        if channel == 'whatsapp':
            await self.whatsapp_op.start()

        console.print(f"\n[bold yellow]➜ Executing '{channel.upper()}' Campaign...[/bold yellow]")
        
        for lead in leads:
            if (channel == 'email' and lead['email'] and lead['email'] != "N/A") or \
               (channel == 'whatsapp' and lead['phone']):
                if await recently_contacted(lead['id'], channel):
                    console.print(f"[bold yellow]↺ Skipped duplicate: {lead['name']} already contacted recently on {channel}.[/bold yellow]")
                    await log_outreach_event(lead['id'], channel, "skipped_duplicate")
                    continue
                
                # Live Status Message
                console.print(f"[dim]Generating personalized pitch for {lead['name']}...[/dim]")
                
                audit = await self.auditor.audit_website(lead['name'], lead)
                subject, body = await self.proposer.generate_proposal(
                    lead['name'], audit, channel,
                    rating=lead.get('rating', 0.0), reviews_count=lead.get('reviews_count', 0),
                    business_category=lead.get('business_category'), has_website=bool(lead['website']),
                    about_us_info=lead.get('about_us_info'), score=lead.get('score', 0.0),
                    service=lead.get('business_category')
                )
                
                success = False
                if channel == 'email':
                    success = await send_with_retry(
                        lambda: self.email_op.send(lead['email'].split(',')[0], subject, body),
                        retries=3,
                    )
                else:
                    success = await send_with_retry(
                        lambda: self.whatsapp_op.send(lead['phone'], body),
                        retries=2,
                    )
                
                if success == True:
                    console.print(f"[bold green]✓ Sent to {lead['name']}[/bold green]")
                    async with get_db() as db:
                        await db.execute("UPDATE leads SET status='sent', last_outreach=datetime('now') WHERE id=?", (lead['id'],))
                        await db.commit()
                    await log_outreach_event(lead['id'], channel, "sent", body)
                elif success == "not_found":
                    console.print(f"[bold yellow]⚠ User mapping failed: {lead['name']} not on WhatsApp. Added to Call List.[/bold yellow]")
                    self._add_to_call_list(lead)
                    await log_outreach_event(lead['id'], channel, "not_found")
                else:
                    console.print(f"[bold red]✗ Failed reaching {lead['name']}[/bold red]")
                    await log_outreach_event(lead['id'], channel, "failed", body, "delivery_failed")
        
        if channel == 'whatsapp':
            await self.whatsapp_op.stop()

    def _add_to_call_list(self, lead: Dict) -> None:
        """Saves non-WhatsApp leads to a dedicated call list for manual follow-up."""
        os.makedirs("data", exist_ok=True)
        file_path = "data/direct_call_list.csv"
        file_exists = os.path.isfile(file_path)
        
        import csv
        with open(file_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Phone", "Website", "Category"])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "Name": lead['name'],
                "Phone": lead['phone'],
                "Website": lead['website'],
                "Category": lead['business_category']
            })

if __name__ == "__main__":
    cli = ColdMailerCLI()
    asyncio.run(cli.run())
