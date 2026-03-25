import asyncio
import aiosqlite
from core.config import settings
from core.database import init_db
from scrapers.maps import MapsScraper
from scrapers.web_crawler import WebCrawler
from engine.auditor import AIAuditor
from engine.proposer import Proposer
from outreach.email_operator import EmailOperator
from core.logger import logger

async def run_automated_outreach(query: str, limit: int = 10, target_emails: int = 10):
    await init_db()
    
    maps_scraper = MapsScraper()
    web_crawler = WebCrawler()
    auditor = AIAuditor()
    proposer = Proposer()
    email_op = EmailOperator()
    
    logger.info(f"Starting automated outreach for: {query}")
    
    # 1. Scrape leads
    await maps_scraper.scrape(query, max_results=limit * 2) # Scrape more to find 10 with websites/emails
    
    # 2. Get new leads, sorted by quality (rating and reviews)
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM leads WHERE status = 'new' ORDER BY rating DESC, reviews_count DESC") as cursor:
            leads = await cursor.fetchall()
    
    sent_count = 0
    for lead in leads:
        if sent_count >= target_emails:
            break
            
        logger.info(f"Processing lead: {lead['name']} ({lead['website'] or 'No Website'})")
        
        has_website = bool(lead['website'])
        res = {}
        emails = []
        
        if has_website:
            # 3. Crawl & Enrich
            res = await web_crawler.crawl(lead['website'], lead['name'])
            emails = res.get('emails', [])
        
        # 4. Audit / Status Determination
        if has_website and res:
            audit = await auditor.audit_website(lead['name'], res)
        else:
            audit = "No website found - potential for new futuristic site creation."
            
        # 5. Generate Proposal
        proposal = await proposer.generate_proposal(
            lead['name'], audit, 'email',
            rating=lead['rating'] or 0.0,
            reviews_count=lead['reviews_count'] or 0,
            business_category=lead['business_category'],
            has_website=has_website,
            about_us_info=res.get('about_us_info', '')
        )
        
        # 6. Send Email (Only if we found an email, otherwise just update DB)
        email_to_use = emails[0] if emails else None
        success = False
        if email_to_use:
            logger.info(f"Sending email to {email_to_use} for {lead['name']}...")
            success = await email_op.send(
                email_to_use, 
                f"Growth Opportunity for {lead['name']}", 
                proposal
            )
        else:
            logger.warning(f"No direct email found for {lead['name']}, updating database as pending review.")

        # 7. Update DB with all collected data
        async with aiosqlite.connect(settings.DB_PATH) as db:
            await db.execute("""
                UPDATE leads 
                SET email = ?, social_links = ?, screenshot_path = ?, about_us_info = ?, audit_summary = ?, status = ?
                WHERE id = ?
            """, (
                ",".join(emails) if emails else None,
                str(res.get("social_links", {})) if res else None,
                res.get("screenshot_path") if res else None,
                res.get("about_us_info") if res else None,
                audit,
                'sent' if success else 'pending_review',
                lead['id']
            ))
            
            if success:
                await db.execute("""
                    INSERT INTO outreach_history (lead_id, channel, content, status)
                    VALUES (?, ?, ?, ?)
                """, (lead['id'], 'email', proposal, 'sent'))
            await db.commit()
            
        if success:
            sent_count += 1
            logger.info(f"Successfully sent email ({sent_count}/{target_emails})")
        else:
            logger.info(f"Lead {lead['name']} updated in database.")

    logger.info(f"Automated outreach complete. Sent {sent_count} emails.")

if __name__ == "__main__":
    import sys
    query = "schools in new delhi"
    limit = 5
    if len(sys.argv) > 1:
        # If last arg is a number, use it as limit
        if sys.argv[-1].isdigit():
            limit = int(sys.argv[-1])
            query = " ".join(sys.argv[1:-1])
        else:
            query = " ".join(sys.argv[1:])
    
    asyncio.run(run_automated_outreach(query, limit=limit, target_emails=limit))
