import asyncio
import csv
import os
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.align import Align

from core.logger import logger
from core.database import init_db, get_db
from core.config import settings
from core.scorer import score_lead
from scrapers.maps import MapsScraper
from scrapers.web_crawler import WebCrawler
from engine.director import OutreachDirector

console = Console()

class FounderDashboard:
    """
    A premium command-line dashboard for the Pixartual Founder.
    
    Provides real-time analytics, lead management, and automated 
    campaign orchestration with a high-end aesthetic.
    """

    def __init__(self) -> None:
        self.director = OutreachDirector()
        self.crawler = WebCrawler()

    async def render_header(self) -> Panel:
        """Renders the dashboard header."""
        return Panel(
            Align.center("[bold gold1]PIXARTUAL STUDIO: FOUNDER DASHBOARD v2.0[/bold gold1]\n[dim]Autonomous Outreach & Lead Conversion Engine[/dim]"),
            border_style="gold1"
        )

    async def get_stats(self) -> Dict[str, int]:
        """Fetches outreach statistics from the database-driven state."""
        async with get_db() as db:
            async with db.execute("SELECT COUNT(*) FROM leads") as c: total = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM leads WHERE status = 'sent'") as c: sent = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM leads WHERE status = 'new'") as c: new = (await c.fetchone())[0]
            async with db.execute("SELECT SUM(whatsapp_sent + emails_sent) FROM daily_stats WHERE date = ?", (os.getenv("CURRENT_DATE", "2026-03-26"),)) as c: 
                daily = (await c.fetchone())[0] or 0
        return {"total": total, "sent": sent, "new": new, "daily": daily}

    async def show_analytics(self) -> None:
        """Displays a clean summary of current business metrics."""
        stats = await self.get_stats()
        table = Table(box=None, expand=True)
        table.add_column("METRIC", style="cyan")
        table.add_column("VALUE", justify="right", style="bold green")
        
        table.add_row("Total Prospects", str(stats['total']))
        table.add_row("Outreach Sent", str(stats['sent']))
        table.add_row("Active Queue", str(stats['new']))
        table.add_row("Daily Throughput", str(stats['daily']))
        
        console.print(Panel(table, title="[bold]Business Intelligence[/bold]", border_style="cyan"))

    async def main_loop(self) -> None:
        """The main interactive loop for the dashboard."""
        await init_db()
        while True:
            console.clear()
            console.print(await self.render_header())
            await self.show_analytics()
            
            console.print("\n[bold]COMMAND CENTER[/bold]")
            console.print("1. [bold green]LAUNCH[/bold green] - Autonomous Founder Mode")
            console.print("2. [bold blue]DISCOVER[/bold blue] - Manual Lead Scrape")
            console.print("3. [bold yellow]REVIEW[/bold yellow] - Process Pending Queue")
            console.print("4. [bold magenta]EXPORT[/bold magenta] - Generate CSV Reports")
            console.print("5. [bold red]EXIT[/bold red] - Shutdown Engine")
            
            choice = Prompt.ask("\n[bold cyan]Select Action[/bold cyan]", choices=["1", "2", "3", "4", "5"], default="1")
            
            if choice == "1":
                await self._run_autonomous()
            elif choice == "2":
                await self._run_discovery()
            elif choice == "3":
                await self._run_review()
            elif choice == "4":
                await self._run_export()
            elif choice == "5":
                console.print("[dim]Shutting down systems... Goodbye, Founder.[/dim]")
                break

    async def _run_autonomous(self) -> None:
        """Triggers the Director's autonomous batch mode."""
        q = Prompt.ask("[bold cyan]Search Niche[/bold cyan]", default="Dentists in California")
        limit = int(Prompt.ask("[bold cyan]Batch Size[/bold cyan]", default="50"))
        await self.director.execute_autonomous_batch(q, target_count=limit)
        Prompt.ask("\n[dim]Press Enter to return to Dashboard...[/dim]")

    async def _run_discovery(self) -> None:
        """Runs a manual scraping and enrichment cycle."""
        q = Prompt.ask("[bold cyan]Enter Query[/bold cyan]")
        await self.director.maps_scraper.scrape(q, max_results=20)
        console.print("[green]Discovery complete. Leads added to queue.[/green]")
        Prompt.ask("\n[dim]Press Enter to return...[/dim]")

    async def _run_review(self) -> None:
        """Allows manual review of leads with AI-generated audits."""
        from run_outreach import ColdMailerCLI
        cli = ColdMailerCLI()
        await cli._handle_resume()
        Prompt.ask("\n[dim]Press Enter to return...[/dim]")

    async def _run_export(self) -> None:
        """Dumps all database tables to CSV files for reporting."""
        os.makedirs("data/exports", exist_ok=True)
        async with get_db() as db:
            for table in ["leads", "outreach_history"]:
                async with db.execute(f"SELECT * FROM {table}") as cursor:
                    rows = [dict(r) for r in await cursor.fetchall()]
                    if rows:
                        path = f"data/exports/{table}.csv"
                        with open(path, "w", newline="", encoding="utf-8") as f:
                            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                            writer.writeheader()
                            writer.writerows(rows)
                        console.print(f"[bold green]✓ Exported {table} to {path}[/bold green]")
        Prompt.ask("\n[dim]Press Enter to return...[/dim]")

if __name__ == "__main__":
    from rich.prompt import Prompt
    app = FounderDashboard()
    asyncio.run(app.main_loop())
