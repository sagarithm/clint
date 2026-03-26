import asyncio
from typing import List, Optional, Dict
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from contextlib import asynccontextmanager

from core.config import settings
from core.database import init_db, get_db
from engine.director import OutreachDirector
from engine.proposer import Proposer
from outreach.email_operator import EmailOperator
from outreach.whatsapp_operator import WhatsAppOperator

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database
    await init_db()
    yield
    # Shutdown logic (if any) can go here

app = FastAPI(
    title="# Clint | Enterprise Intelligence Dashboard",
    description="Enterprise-grade backend for the Pixartual Outreach Suite.",
    version="1.0.0",
    lifespan=lifespan
)

# 1. Security & Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Shared Operators
director = OutreachDirector()
proposer = Proposer()
email_op = EmailOperator()
whatsapp_op = WhatsAppOperator()

# 3. Request Models
class ProposalRequest(BaseModel):
    lead_id: int
    channel: str = "email"

class SendRequest(BaseModel):
    lead_id: int
    channel: str
    subject: str
    body: str

class PipelineRequest(BaseModel):
    query: str
    limit: int = 10

# Global state for pipeline tracking (Simple for now)
pipeline_status = {"running": False, "message": "Idle"}

# 4. API Endpoints
@app.get("/api/stats")
async def get_stats() -> Dict[str, int]:
    """Provides high-level outreach metrics."""
    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) FROM leads") as c: total = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM leads WHERE status='sent'") as c: sent = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM leads WHERE status='new'") as c: new = (await c.fetchone())[0]
    return {"total": total, "sent": sent, "pending": new}
@app.get("/api/leads")
async def get_leads(limit: int = 50, status: Optional[str] = None) -> List[Dict]:
    """Retrieves lead list with optional filtering."""
    query = "SELECT * FROM leads"
    params = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY score DESC LIMIT ?"
    params.append(limit)
    
    async with get_db() as db:
        async with db.execute(query, params) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

@app.post("/api/outreach/generate")
async def generate_outreach(req: ProposalRequest):
    """Generates a personalized AI proposal for a specific lead."""
    async with get_db() as db:
        async with db.execute("SELECT * FROM leads WHERE id = ?", (req.lead_id,)) as c:
            lead = await c.fetchone()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead_data = dict(lead)
    body_summary = lead_data.get('audit_summary', 'Digital growth audit.')
    subject, body = await proposer.generate_proposal(
        lead_data['name'], body_summary, req.channel,
        lead_data.get('rating', 0.0), lead_data.get('reviews_count', 0),
        lead_data.get('business_category'), bool(lead_data['website']),
        lead_data.get('about_us_info'), score=lead_data.get('score', 0.0),
        service=lead_data.get('business_category')
    )
    return {"subject": subject, "body": body}

@app.post("/api/outreach/send")
async def send_outreach(req: SendRequest):
    """Triggers the delivery of a proposal via Email or WhatsApp."""
    async with get_db() as db:
        async with db.execute("SELECT * FROM leads WHERE id = ?", (req.lead_id,)) as c:
            lead = await c.fetchone()
    
    if not lead: raise HTTPException(status_code=404, detail="Lead not found")
    lead_data = dict(lead)
    
    success = False
    if req.channel == 'email':
        to_email = lead_data['email'].split(',')[0]
        success = await email_op.send(to_email, req.subject, req.body)
    elif req.channel == 'whatsapp':
        success = await whatsapp_op.send(lead_data['phone'], req.body)
        
    if success:
        async with get_db() as db:
            await db.execute(
                "UPDATE leads SET status='sent', last_outreach=datetime('now') WHERE id=?", 
                (req.lead_id,)
            )
            await db.commit()
            
    return {"success": success}

@app.get("/api/history")
async def get_history(limit: int = 20):
    """Retrieves the latest outreach history."""
    async with get_db() as db:
        async with db.execute("""
            SELECT h.*, l.name as lead_name 
            FROM outreach_history h
            JOIN leads l ON h.lead_id = l.id
            ORDER BY h.sent_at DESC 
            LIMIT ?
        """, (limit,)) as cursor:
            return [dict(r) for r in await cursor.fetchall()]

@app.post("/api/pipeline/start")
async def start_pipeline(req: PipelineRequest, background_tasks: BackgroundTasks):
    """Starts an autonomous discovery pipeline in the background."""
    if pipeline_status["running"]:
        raise HTTPException(status_code=400, detail="Pipeline already running")
    
    background_tasks.add_task(run_pipeline_task, req.query, req.limit)
    return {"status": "started"}

@app.get("/api/pipeline/status")
async def get_pipeline_status():
    """Returns the current status of the background pipeline."""
    return pipeline_status

async def run_pipeline_task(query: str, limit: int):
    """Background task to execute the director's autonomous batch."""
    pipeline_status["running"] = True
    pipeline_status["message"] = f"Discovering leads for '{query}'..."
    try:
        await director.execute_autonomous_batch(query, target_count=limit)
        pipeline_status["message"] = "Pipeline complete"
    except Exception as e:
        pipeline_status["message"] = f"Pipeline failed: {str(e)}"
    finally:
        pipeline_status["running"] = False

# 5. Static Assets & Frontend
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def serve_dashboard():
    return FileResponse("dashboard.html")

if __name__ == "__main__":
    import uvicorn
    import os
    # Security: Bind to localhost by default for local development. 
    # Use environment variables if external exposure is needed.
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run("server:app", host=host, port=8000, reload=True)
