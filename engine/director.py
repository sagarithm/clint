import asyncio
import aiosqlite
import random
import os
from typing import List, Dict, Optional

from core.config import settings
from core.logger import logger
from core.database import get_db
from core.event_bus import (
    TOPIC_DISPATCH_COMPLETED,
    TOPIC_DISPATCH_REQUESTED,
    TOPIC_DEADLETTER,
    TOPIC_ENRICHMENT_COMPLETED,
    TOPIC_MESSAGE_GENERATED,
    TOPIC_SCORING_COMPLETED,
    publish_deadletter,
    publish_event,
)
from core.policy import enforce_pre_send_policy
from core.quality_gate import evaluate_message_quality
from core.scorer import score_lead, score_lead_v2
from core.reliability import log_outreach_event, recently_contacted, send_with_retry
from core.state_machine import transition_lead_state
from core.v2_store import (
    log_outreach_event_v2,
    save_enrichment_snapshot,
    save_message_draft,
    save_score_snapshot,
)
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
        from rich.console import Console
        
        logger.info(f"[[FOUNDER MODE]] Initializing campaign for: [bold cyan]{query}[/bold cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=Console()
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
                        score_result = score_lead_v2({**lead_data, 'email': email_str, 'about_us_info': about_us})
                        score = int(round(score_result['priority_score']))
                        
                        async with get_db() as db:
                            await db.execute("""
                                UPDATE leads SET email = ?, about_us_info = ?, score = ?
                                WHERE id = ?
                            """, (email_str, about_us, score, lead_data['id']))
                            await save_enrichment_snapshot(
                                db,
                                lead_id=lead_data['id'],
                                website_summary=about_us or "",
                                rating=float(lead_data.get('rating') or 0.0),
                                reviews_count=int(lead_data.get('reviews_count') or 0),
                                social_links=enrichment.get('social_links') or {},
                            )
                            await publish_event(
                                db,
                                topic=TOPIC_ENRICHMENT_COMPLETED,
                                lead_id=lead_data['id'],
                                payload={"source": "director.autonomous_batch"},
                            )
                            await save_score_snapshot(
                                db,
                                lead_id=lead_data['id'],
                                fit_score=score_result['fit_score'],
                                intent_score=score_result['intent_score'],
                                authority_score=score_result['authority_score'],
                                timing_score=score_result['timing_score'],
                                risk_score=score_result['risk_score'],
                                priority_score=score_result['priority_score'],
                                reason_codes={"source": "director.autonomous_batch", "scorer": "v2", "codes": score_result['reason_codes']},
                            )
                            await publish_event(
                                db,
                                topic=TOPIC_SCORING_COMPLETED,
                                lead_id=lead_data['id'],
                                payload={"priority_score": score_result['priority_score']},
                            )
                            await db.commit()
                        
                        lead_data['email'] = email_str
                        lead_data['about_us_info'] = about_us
                        lead_data['score'] = score

                    # 3. Outreach (Multi-Condition Branching)
                    if sent_count < send_limit and lead_data['email'] and lead_data['email'] != "N/A":
                        # Only send if score is high enough for autonomous mode
                        if lead_data.get('score', 0) >= settings.MIN_SCORE_THRESHOLD:
                            if await recently_contacted(lead_data['id'], 'email'):
                                logger.info(f"Skipping duplicate outreach for {lead_data['name']} (recently contacted).")
                                await log_outreach_event(lead_data['id'], 'email', 'skipped_duplicate')
                                continue
                            progress.update(process_task, description=f"[bold magenta]Sending to: {lead_data['name']}")
                            await self._process_outreach(lead_data)
                            sent_count += 1
                        else:
                            logger.info(f"Skipping low-value lead: {lead_data['name']} (Score: {lead_data.get('score')})")
                    
                except Exception as e:
                    logger.error(f"Failed to process lead {lead_data['name']}: {e}")
                    async with get_db() as db:
                        await publish_deadletter(
                            db,
                            topic=TOPIC_DEADLETTER,
                            lead_id=lead_data.get('id'),
                            channel='system',
                            error_message=str(e),
                            payload={"source": "director.autonomous_batch", "lead_name": lead_data.get('name')},
                        )
                        await db.commit()
                
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
            lead_data.get('about_us_info'), score=lead_data.get('score', 0.0),
            service=lead_data.get('category')
        )

        quality = evaluate_message_quality(
            lead_name=lead_data['name'],
            subject=subject,
            body=body,
            channel='email',
        )

        async with get_db() as db:
            await save_message_draft(
                db,
                lead_id=lead_data['id'],
                channel='email',
                subject=subject,
                body=body,
                template_id="legacy_proposer",
                prompt_version="v2-legacy",
                quality_score=quality['quality_score'],
                rejection_reason=",".join(quality['reasons']) if not quality['passed'] else None,
            )
            await publish_event(
                db,
                topic=TOPIC_MESSAGE_GENERATED,
                lead_id=lead_data['id'],
                channel='email',
                payload={"quality_score": quality['quality_score'], "quality_passed": quality['passed']},
            )

            if not quality['passed']:
                await log_outreach_event_v2(
                    db,
                    lead_id=lead_data['id'],
                    channel='email',
                    event_type='quality_gate_rejected',
                    payload={"reasons": quality['reasons'], "quality_score": quality['quality_score'], "mode": "autonomous"},
                )
                await db.commit()
                return False

            allowed, reason = await enforce_pre_send_policy(db, lead=lead_data, channel='email')
            if not allowed:
                await transition_lead_state(
                    db,
                    lead_data['id'],
                    'suppressed',
                    reason=reason,
                    actor='director.pre_send_policy',
                )
                await log_outreach_event_v2(
                    db,
                    lead_id=lead_data['id'],
                    channel='email',
                    event_type='policy_blocked',
                    payload={"reason": reason, "mode": "autonomous"},
                )
                await db.commit()
                return False

            await publish_event(
                db,
                topic=TOPIC_DISPATCH_REQUESTED,
                lead_id=lead_data['id'],
                channel='email',
                payload={"source": "director.autonomous_batch"},
            )
            await db.commit()
        
        # Delivery
        to_email = lead_data['email'].split(',')[0]
        success = await send_with_retry(
            lambda: self.email_op.send(to_email, subject, body),
            retries=3,
        )
        
        if success:
            async with get_db() as db:
                await transition_lead_state(
                    db,
                    lead_data['id'],
                    "sent",
                    reason="autonomous_email_delivery_success",
                    actor="director.autonomous_batch",
                )
                await db.execute(
                    """
                    UPDATE leads SET outreach_step = 1, last_outreach = datetime('now')
                    WHERE id = ?
                    """,
                    (lead_data['id'],),
                )
                await log_outreach_event_v2(
                    db,
                    lead_id=lead_data['id'],
                    channel='email',
                    event_type='dispatch_success',
                    payload={"status": "sent", "mode": "autonomous"},
                )
                await publish_event(
                    db,
                    topic=TOPIC_DISPATCH_COMPLETED,
                    lead_id=lead_data['id'],
                    channel='email',
                    payload={"status": "sent", "mode": "autonomous"},
                )
                await db.commit()
            await log_outreach_event(lead_data['id'], 'email', 'sent', body)
        else:
            async with get_db() as db:
                await log_outreach_event_v2(
                    db,
                    lead_id=lead_data['id'],
                    channel='email',
                    event_type='dispatch_failed',
                    payload={"status": "failed", "error": "delivery_failed", "mode": "autonomous"},
                )
                await db.commit()
            await log_outreach_event(lead_data['id'], 'email', 'failed', body, 'delivery_failed')
        
        return success

if __name__ == "__main__":
    director = OutreachDirector()
    # asyncio.run(director.execute_autonomous_batch("Dentists in California", target_count=5, send_limit=1))
