import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import aiosqlite

from core.config import settings
from core.database import init_db
from engine.proposer import Proposer
from outreach.email_operator import EmailOperator
from outreach.whatsapp_operator import WhatsAppOperator

app = FastAPI(title="ColdMailer API", version="1.0.0")

# CORS for browser connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

proposer = Proposer()
email_op = EmailOperator()
whatsapp_op = WhatsAppOperator()

# ── STATIC FILES ──
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def serve_dashboard():
    return FileResponse("dashboard.html")

# ── STATS ──
@app.get("/api/stats")
async def get_stats():
    async with aiosqlite.connect(settings.DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM leads") as c:
            total = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM leads WHERE status = 'sent'") as c:
            sent = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM leads WHERE status NOT IN ('new', 'sent')") as c:
            audited = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM leads WHERE status = 'reminder_sent'") as c:
            reminders = (await c.fetchone())[0]
    return {"total": total, "sent": sent, "audited": audited, "reminders": reminders}

# ── LEADS ──
@app.get("/api/leads")
async def get_leads(limit: int = 50, status: Optional[str] = None, search: Optional[str] = None):
    query = "SELECT * FROM leads"
    params = []
    conditions = []
    if status:
        conditions.append("status = ?")
        params.append(status)
    if search:
        conditions.append("(name LIKE ? OR business_category LIKE ? OR address LIKE ?)")
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += f" ORDER BY created_at DESC LIMIT {limit}"

    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]

# ── OUTREACH HISTORY ──
@app.get("/api/history")
async def get_history(limit: int = 20):
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT h.*, l.name as lead_name
            FROM outreach_history h
            LEFT JOIN leads l ON h.lead_id = l.id
            ORDER BY h.sent_at DESC
            LIMIT ?
        """, (limit,)) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]

# ── GENERATE PROPOSAL ──
class ProposalRequest(BaseModel):
    lead_id: int
    channel: str = "email"
    is_reminder: bool = False

@app.post("/api/generate-proposal")
async def generate_proposal(req: ProposalRequest):
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM leads WHERE id = ?", (req.lead_id,)) as cur:
            lead = await cur.fetchone()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = dict(lead)
    text = await proposer.generate_proposal(
        lead['name'], lead.get('audit_summary', ''), req.channel,
        rating=lead.get('rating') or 0.0,
        reviews_count=lead.get('reviews_count') or 0,
        business_category=lead.get('business_category'),
        has_website=bool(lead.get('website')),
        about_us_info=lead.get('about_us_info'),
        is_reminder=req.is_reminder
    )
    return {"proposal": text, "lead": lead}

# ── SEND PROPOSAL ──
class SendRequest(BaseModel):
    lead_id: int
    channel: str
    content: str

@app.post("/api/send")
async def send_proposal(req: SendRequest):
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM leads WHERE id = ?", (req.lead_id,)) as cur:
            lead = await cur.fetchone()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead = dict(lead)

    success = False
    if req.channel == "email" and lead.get("email"):
        success = await email_op.send(
            lead['email'].split(",")[0],
            f"Quick Idea for {lead['name']}",
            req.content
        )
    elif req.channel == "whatsapp" and lead.get("phone"):
        success = await whatsapp_op.send(lead['phone'], req.content)
    else:
        raise HTTPException(status_code=400, detail="No contact info for selected channel")

    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute("""
            INSERT INTO outreach_history (lead_id, channel, content, status)
            VALUES (?, ?, ?, ?)
        """, (req.lead_id, req.channel, req.content, 'sent' if success else 'failed'))
        if success:
            await db.execute("UPDATE leads SET status = 'sent' WHERE id = ?", (req.lead_id,))
        await db.commit()

    return {"success": success}

# ── PIPELINE ──
class PipelineRequest(BaseModel):
    query: str
    limit: int = 10

pipeline_status = {"running": False, "message": "Idle"}

@app.post("/api/pipeline/start")
async def start_pipeline(req: PipelineRequest, background_tasks: BackgroundTasks):
    if pipeline_status["running"]:
        raise HTTPException(status_code=409, detail="Pipeline already running")
    background_tasks.add_task(run_full_pipeline, req.query, req.limit)
    return {"status": "started", "query": req.query}

@app.get("/api/pipeline/status")
async def get_pipeline_status():
    return pipeline_status

async def run_full_pipeline(query: str, limit: int):
    from scrapers.maps import MapsScraper
    from scrapers.web_crawler import WebCrawler
    from engine.auditor import AIAuditor

    pipeline_status["running"] = True
    pipeline_status["message"] = f"Scraping Google Maps for: {query}"
    try:
        scraper = MapsScraper()
        await scraper.scrape(query, limit)

        pipeline_status["message"] = "Auditing websites..."
        crawler = WebCrawler()
        auditor = AIAuditor()

        async with aiosqlite.connect(settings.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM leads WHERE status = 'new'") as cur:
                leads = await cur.fetchall()

        for lead in leads:
            lead = dict(lead)
            if lead.get("website"):
                res = await crawler.crawl(lead["website"], lead["name"])
                if res:
                    audit = await auditor.audit_website(lead["name"], res)
                    async with aiosqlite.connect(settings.DB_PATH) as db:
                        await db.execute("""
                            UPDATE leads
                            SET email=?, social_links=?, screenshot_path=?, about_us_info=?, audit_summary=?, status='pending_review'
                            WHERE id=?
                        """, (
                            ",".join(res.get("emails", [])),
                            str(res.get("social_links", {})),
                            res.get("screenshot_path"),
                            res.get("about_us_info"),
                            audit,
                            lead["id"]
                        ))
                        await db.commit()
            else:
                async with aiosqlite.connect(settings.DB_PATH) as db:
                    await db.execute("UPDATE leads SET status='pending_review', audit_summary='No website found' WHERE id=?", (lead["id"],))
                    await db.commit()

        pipeline_status["message"] = f"Complete! Processed {len(leads)} leads."
    except Exception as e:
        pipeline_status["message"] = f"Error: {str(e)}"
    finally:
        pipeline_status["running"] = False

# ── STARTUP ──
@app.on_event("startup")
async def on_startup():
    await init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
