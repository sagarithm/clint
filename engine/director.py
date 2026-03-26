import asyncio
import aiosqlite
from typing import List, Dict, Optional

from core.config import settings
from core.logger import logger
from core.database import get_db
from core.scorer import score_lead
from core.utils import sanitize_emails

from scrapers.maps import MapsScraper
from scrapers.web_crawler import WebCrawler
from engine.auditor import AIAuditor
from engine.proposer import Proposer
from outreach.email_operator import EmailOperator

class OutreachDirector:
    """
    The orchestrator for the 'Founder Mode' autonomous outreach workflow.
    
    Manages the lifecycle of a lead from discovery (MapsScraper) to 
    enrichment (WebCrawler), AI Analysis (Auditor), and final conversion 
    (Proposer/EmailOperator).
    """

    def __init__(self) -> None:
        self.maps_scraper = MapsScraper()
        self.web_crawler = WebCrawler()
        self.auditor = AIAuditor()
        self.proposer = Proposer()
        self.email_op = EmailOperator()

    async def execute_autonomous_batch(self, query: str, target_count: int = 50, send_limit: int = 20) -> int:
        """
        Runs a full, end-to-end outreach campaign autonomously with live progress.
        """
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        
        logger.info(f"[[FOUNDER MODE]] Initializing campaign for: [bold cyan]{query}[/bold cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=logger.console
        ) as progress:
            
            # Phase 1: Lead Discovery
            scrape_task = progress.add_task(f"[yellow]Discovering leads for '{query}'...", total=None)
            await self.maps_scraper.scrape(query, max_results=target_count)
            progress.update(scrape_task, description="[bold green]Discovery Complete.", completed=True)
            
            # Phase 2: Processing & Enrichment
            query_id = f"AUTO_{query[:10].replace(' ', '_')}_{random.randint(100, 999)}"
            
            async with get_db() as db:
                async with db.execute("""
                    SELECT * FROM leads 
                    WHERE status = 'new' 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (target_count,)) as cursor:
                    leads = await cursor.fetchall()
            
            if not leads:
                logger.warning("No new leads found to process.")
                return 0
                
            process_task = progress.add_task("[cyan]Enriching & Auditing...", total=len(leads))
            sent_count = 0
            
            for lead in leads:
                lead_data = dict(lead)
                progress.update(process_task, description=f"[cyan]Processing: {lead_data['name']}")
                
                try:
                    # 2.1 Enrichment
                    if lead_data['website'] and "google.com" not in lead_data['website']:
                        enrichment = await self.web_crawler.crawl(lead_data['website'], lead_data['name'], query_id=query_id)
                        
                        emails = enrichment.get('emails', [])
                        email_str = ",".join(emails) if emails else "N/A"
                        about_us = enrichment.get('about_us_info')
                        
                        # Score lead with new intelligence
                        score = score_lead({**lead_data, 'email': email_str, 'about_us_info': about_us})
                        
                        async with get_db() as db:
                            await db.execute("""
                                UPDATE leads SET email = ?, about_us_info = ?, score = ?
                                WHERE id = ?
                            """, (email_str, about_us, score, lead_data['id']))
                            await db.commit()
                        
                        lead_data['email'] = email_str
                        lead_data['about_us_info'] = about_us
                        lead_data['score'] = score

                    # 3. Outreach (Multi-Condition Branching)
                    if sent_count < send_limit and lead_data['email'] and lead_data['email'] != "N/A":
                        # Only send if score is high enough (e.g. > 5) for autonomous mode
                        if lead_data.get('score', 0) >= 5:
                            progress.update(process_task, description=f"[bold magenta]Sending to: {lead_data['name']}")
                            await self._process_outreach(lead_data)
                            sent_count += 1
                        else:
                            logger.info(f"Skipping low-value lead: {lead_data['name']} (Score: {lead_data.get('score')})")
                    
                except Exception as e:
                    logger.error(f"Failed to process lead {lead_data['name']}: {e}")
                
                progress.advance(process_task)
                
        logger.info(f"[[FOUNDER MODE]] Batch Complete. Total Sent: [bold green]{sent_count}[/bold green]")
        return sent_count

    async def _process_outreach(self, lead_data: Dict) -> bool:
        """Generates and sends a personalized proposal for a specific lead."""
        logger.info(f"Generating high-ticket pitch for [bold green]{lead_data['name']}[/bold green]...")
        
        # AI Audit
        audit = await self.auditor.audit_website(lead_data['name'], lead_data)
        
        # Proposal Generation
        subject, body = await self.proposer.generate_proposal(
            lead_data['name'], audit, 'email',
            lead_data.get('rating', 0.0), lead_data.get('reviews_count', 0),
            lead_data.get('business_category'), bool(lead_data['website']),
            lead_data.get('about_us_info'), score=lead_data.get('score', 0.0)
        )
        
        # Delivery
        to_email = lead_data['email'].split(',')[0]
        success = await self.email_op.send(to_email, subject, body)
        
        if success:
            async with get_db() as db:
                await db.execute("""
                    UPDATE leads SET status = 'sent', outreach_step = 1, last_outreach = datetime('now') 
                    WHERE id = ?
                """, (lead_data['id'],))
                await db.commit()
                
            # Log to History
            async with get_db() as db:
                await db.execute("""
                    INSERT INTO outreach_history (lead_id, channel, content, status)
                    VALUES (?, 'email', ?, 'sent')
                """, (lead_data['id'], body[:500]))
                await db.commit()
        
        return success

if __name__ == "__main__":
    director = OutreachDirector()
    # asyncio.run(director.execute_autonomous_batch("Dentists in California", target_count=5, send_limit=1))
