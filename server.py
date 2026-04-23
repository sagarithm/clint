import asyncio
from typing import List, Optional, Dict
from pathlib import Path
from importlib import resources
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from contextlib import asynccontextmanager

from core.config import settings
from core.database import init_db, get_db
from core.deadletter import list_deadletter_events, replay_deadletter_event
from core.experiments import (
    complete_experiment,
    create_experiment,
    decide_experiment,
    list_experiments,
    record_observation,
    start_experiment,
)
from core.kpi import get_kpi_summary
from core.policy import enforce_pre_send_policy
from core.quality_gate import evaluate_message_quality
from core.reply_intelligence import classify_reply
from core.state_machine import transition_lead_state
from core.v2_store import log_outreach_event_v2, save_message_draft, save_reply_event
from engine.director import OutreachDirector
from engine.proposer import Proposer
from engine.worker_orchestrator import QueueWorkerOrchestrator
from outreach.email_operator import EmailOperator
from outreach.whatsapp_operator import WhatsAppOperator
from core.sla_monitor import sla_monitor_loop

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database
    await init_db()
    # Startup: SLA Monitor background loop
    monitor_task = asyncio.create_task(sla_monitor_loop())
    yield
    # Shutdown logic
    monitor_task.cancel()

app = FastAPI(
    title="# Clint | Enterprise Intelligence Dashboard",
    description="Enterprise-grade backend for the Pixartual Outreach Suite.",
    version="1.0.3",
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
worker_orchestrator = QueueWorkerOrchestrator()
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


class ReplyClassifyRequest(BaseModel):
    lead_id: int
    channel: str = "email"
    thread_ref: str = "manual"
    reply_text: str


class ExperimentCreateRequest(BaseModel):
    name: str
    hypothesis: str
    segment: str
    metric_key: str
    variant_a: str
    variant_b: str


class ExperimentObservationRequest(BaseModel):
    experiment_id: int
    variant: str
    sample_size: int
    metric_value: float
    quality_impact: float = 0.0


class ExperimentCompleteRequest(BaseModel):
    experiment_id: int
    winner_variant: str
    decision_note: str


class ExperimentDecideRequest(BaseModel):
    experiment_id: int
    min_sample_per_variant: int = 30
    min_uplift_pct: float = 5.0
    max_negative_quality_impact: float = -5.0


class WorkerRunRequest(BaseModel):
    query: str
    limit: int = 20
    live_send: bool = False


class DeadletterReplayRequest(BaseModel):
    event_id: int

# Global state for pipeline tracking (Simple for now)
pipeline_status = {"running": False, "message": "Idle"}
worker_status = {"running": False, "message": "Idle", "last_result": None}
upwork_worker_status = {"running": False, "message": "Idle", "last_result": None}
fiverr_worker_status = {"running": False, "message": "Idle", "last_result": None}
linkedin_worker_status = {"running": False, "message": "Idle", "last_result": None}
x_threads_worker_status = {"running": False, "message": "Idle", "last_result": None}

BASE_DIR = Path(__file__).resolve().parent
CORE_DIR = BASE_DIR / "core"


# 4. API Endpoints
@app.get("/api/stats")
async def get_stats() -> Dict[str, int]:
    """Provides high-level outreach metrics."""
    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) FROM leads") as c: total = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM leads WHERE status='sent'") as c: sent = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM leads WHERE status='new'") as c: new = (await c.fetchone())[0]
    return {"total": total, "sent": sent, "pending": new}


@app.get("/api/kpi/summary")
async def get_kpi_summary_api() -> Dict:
    async with get_db() as db:
        return await get_kpi_summary(db)
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

    quality = evaluate_message_quality(
        lead_name=lead_data['name'],
        subject=subject if req.channel == 'email' else None,
        body=body,
        channel=req.channel,
    )

    async with get_db() as db:
        await save_message_draft(
            db,
            lead_id=req.lead_id,
            channel=req.channel,
            subject=subject if req.channel == 'email' else None,
            body=body,
            template_id='legacy_proposer',
            prompt_version='v2-legacy',
            quality_score=quality['quality_score'],
            rejection_reason=",".join(quality['reasons']) if not quality['passed'] else None,
        )
        await db.commit()

    return {
        "subject": subject,
        "body": body,
        "quality_gate_passed": quality['passed'],
        "quality_score": quality['quality_score'],
        "quality_reasons": quality['reasons'],
    }

@app.post("/api/outreach/send")
async def send_outreach(req: SendRequest):
    """Triggers the delivery of a proposal via Email or WhatsApp."""
    async with get_db() as db:
        async with db.execute("SELECT * FROM leads WHERE id = ?", (req.lead_id,)) as c:
            lead = await c.fetchone()
    
    if not lead: raise HTTPException(status_code=404, detail="Lead not found")
    lead_data = dict(lead)

    async with get_db() as db:
        allowed, reason = await enforce_pre_send_policy(db, lead=lead_data, channel=req.channel)
        if not allowed:
            await transition_lead_state(
                db,
                req.lead_id,
                "suppressed",
                reason=reason,
                actor="api.pre_send_policy",
            )
            await log_outreach_event_v2(
                db,
                lead_id=req.lead_id,
                channel=req.channel,
                event_type="policy_blocked",
                payload={"reason": reason, "source": "api"},
            )
            await db.commit()
            return {"success": False, "blocked": True, "reason": reason}
    
    success = False
    if req.channel == 'email':
        to_email = lead_data['email'].split(',')[0]
        success = await email_op.send(to_email, req.subject, req.body)
    elif req.channel == 'whatsapp':
        success = await whatsapp_op.send(lead_data['phone'], req.body)
        
    if success:
        async with get_db() as db:
            await transition_lead_state(
                db,
                req.lead_id,
                "sent",
                reason=f"api_{req.channel}_delivery_success",
                actor="api.outreach.send",
            )
            await db.execute("UPDATE leads SET last_outreach=datetime('now') WHERE id=?", (req.lead_id,))
            await log_outreach_event_v2(
                db,
                lead_id=req.lead_id,
                channel=req.channel,
                event_type="dispatch_success",
                payload={"status": "sent", "source": "api"},
            )
            await db.commit()
    else:
        async with get_db() as db:
            await log_outreach_event_v2(
                db,
                lead_id=req.lead_id,
                channel=req.channel,
                event_type="dispatch_failed",
                payload={"status": "failed", "source": "api"},
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


@app.post("/api/reply/classify")
async def classify_reply_api(req: ReplyClassifyRequest):
    async with get_db() as db:
        async with db.execute("SELECT * FROM leads WHERE id = ?", (req.lead_id,)) as c:
            lead = await c.fetchone()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    result = classify_reply(req.reply_text)

    async with get_db() as db:
        await save_reply_event(
            db,
            lead_id=req.lead_id,
            channel=req.channel,
            thread_ref=req.thread_ref,
            reply_text=req.reply_text,
            classifier_label=result["label"],
            classifier_confidence=float(result["confidence"]),
            requires_human_review=bool(result["requires_human_review"]),
        )

        if result["label"] in {"replied_positive", "replied_neutral", "replied_negative"}:
            await transition_lead_state(
                db,
                req.lead_id,
                result["label"],
                reason="reply_classified",
                actor="api.reply.classify",
            )

        await log_outreach_event_v2(
            db,
            lead_id=req.lead_id,
            channel=req.channel,
            event_type="reply_classified",
            payload=result,
        )
        await db.commit()

    return result


@app.get("/api/experiments")
async def experiments_list(status: Optional[str] = None):
    async with get_db() as db:
        return await list_experiments(db, status=status)


@app.post("/api/experiments/create")
async def experiments_create(req: ExperimentCreateRequest):
    async with get_db() as db:
        experiment_id = await create_experiment(
            db,
            name=req.name,
            hypothesis=req.hypothesis,
            segment=req.segment,
            metric_key=req.metric_key,
            variant_a=req.variant_a,
            variant_b=req.variant_b,
        )
        await db.commit()
    return {"experiment_id": experiment_id, "status": "planned"}


@app.post("/api/experiments/start")
async def experiments_start(experiment_id: int):
    async with get_db() as db:
        await start_experiment(db, experiment_id=experiment_id)
        await db.commit()
    return {"experiment_id": experiment_id, "status": "running"}


@app.post("/api/experiments/observe")
async def experiments_observe(req: ExperimentObservationRequest):
    async with get_db() as db:
        await record_observation(
            db,
            experiment_id=req.experiment_id,
            variant=req.variant,
            sample_size=req.sample_size,
            metric_value=req.metric_value,
            quality_impact=req.quality_impact,
        )
        await db.commit()
    return {"experiment_id": req.experiment_id, "status": "observation_recorded"}


@app.post("/api/experiments/complete")
async def experiments_complete(req: ExperimentCompleteRequest):
    async with get_db() as db:
        await complete_experiment(
            db,
            experiment_id=req.experiment_id,
            winner_variant=req.winner_variant,
            decision_note=req.decision_note,
        )
        await db.commit()
    return {"experiment_id": req.experiment_id, "status": "completed", "winner": req.winner_variant}


@app.post("/api/experiments/decide")
async def experiments_decide(req: ExperimentDecideRequest):
    async with get_db() as db:
        result = await decide_experiment(
            db,
            experiment_id=req.experiment_id,
            min_sample_per_variant=req.min_sample_per_variant,
            min_uplift_pct=req.min_uplift_pct,
            max_negative_quality_impact=req.max_negative_quality_impact,
        )
        await db.commit()
    return result

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


@app.post("/api/workers/reddit/run")
async def run_reddit_worker(req: WorkerRunRequest, background_tasks: BackgroundTasks):
    if worker_status["running"]:
        raise HTTPException(status_code=400, detail="Worker pipeline already running")

    background_tasks.add_task(_run_reddit_worker_task, req.query, req.limit, req.live_send)
    return {"status": "started", "query": req.query, "limit": req.limit, "live_send": req.live_send}


@app.get("/api/workers/reddit/status")
async def get_reddit_worker_status():
    return worker_status


@app.post("/api/workers/upwork/run")
async def run_upwork_worker(req: WorkerRunRequest, background_tasks: BackgroundTasks):
    if upwork_worker_status["running"]:
        raise HTTPException(status_code=400, detail="Upwork worker pipeline already running")

    background_tasks.add_task(_run_upwork_worker_task, req.query, req.limit, req.live_send)
    return {"status": "started", "query": req.query, "limit": req.limit, "live_send": req.live_send}


@app.get("/api/workers/upwork/status")
async def get_upwork_worker_status():
    return upwork_worker_status


@app.post("/api/workers/fiverr/run")
async def run_fiverr_worker(req: WorkerRunRequest, background_tasks: BackgroundTasks):
    if fiverr_worker_status["running"]:
        raise HTTPException(status_code=400, detail="Fiverr worker pipeline already running")

    background_tasks.add_task(_run_fiverr_worker_task, req.query, req.limit, req.live_send)
    return {"status": "started", "query": req.query, "limit": req.limit, "live_send": req.live_send}


@app.get("/api/workers/fiverr/status")
async def get_fiverr_worker_status():
    return fiverr_worker_status


@app.post("/api/workers/linkedin/run")
async def run_linkedin_worker(req: WorkerRunRequest, background_tasks: BackgroundTasks):
    if linkedin_worker_status["running"]:
        raise HTTPException(status_code=400, detail="LinkedIn worker pipeline already running")

    background_tasks.add_task(_run_linkedin_worker_task, req.query, req.limit, req.live_send)
    return {"status": "started", "query": req.query, "limit": req.limit, "live_send": req.live_send}


@app.get("/api/workers/linkedin/status")
async def get_linkedin_worker_status():
    return linkedin_worker_status


@app.post("/api/workers/x-threads/run")
async def run_x_threads_worker(req: WorkerRunRequest, background_tasks: BackgroundTasks):
    if x_threads_worker_status["running"]:
        raise HTTPException(status_code=400, detail="X/Threads worker pipeline already running")

    background_tasks.add_task(_run_x_threads_worker_task, req.query, req.limit, req.live_send)
    return {"status": "started", "query": req.query, "limit": req.limit, "live_send": req.live_send}


@app.get("/api/workers/x-threads/status")
async def get_x_threads_worker_status():
    return x_threads_worker_status


@app.get("/api/deadletter")
async def deadletter_list(status: Optional[str] = None, limit: int = 50):
    async with get_db() as db:
        return await list_deadletter_events(db, status=status, limit=limit)


@app.post("/api/deadletter/replay")
async def deadletter_replay(req: DeadletterReplayRequest):
    async with get_db() as db:
        result = await replay_deadletter_event(
            db,
            event_id=req.event_id,
            replay_handler=worker_orchestrator,
        )
        await db.commit()
    return result


async def _run_reddit_worker_task(query: str, limit: int, live_send: bool):
    worker_status["running"] = True
    worker_status["message"] = f"Running reddit queue worker for '{query}'"
    worker_status["last_result"] = None
    try:
        result = await worker_orchestrator.run_reddit_pipeline(
            query=query,
            limit=limit,
            live_send=live_send,
        )
        worker_status["last_result"] = result
        worker_status["message"] = "Worker run completed"
    except Exception as e:
        worker_status["message"] = f"Worker run failed: {str(e)}"
    finally:
        worker_status["running"] = False


async def _run_upwork_worker_task(query: str, limit: int, live_send: bool):
    upwork_worker_status["running"] = True
    upwork_worker_status["message"] = f"Running upwork queue worker for '{query}'"
    upwork_worker_status["last_result"] = None
    try:
        result = await worker_orchestrator.run_upwork_pipeline(
            query=query,
            limit=limit,
            live_send=live_send,
        )
        upwork_worker_status["last_result"] = result
        upwork_worker_status["message"] = "Worker run completed"
    except Exception as e:
        upwork_worker_status["message"] = f"Worker run failed: {str(e)}"
    finally:
        upwork_worker_status["running"] = False


async def _run_fiverr_worker_task(query: str, limit: int, live_send: bool):
    fiverr_worker_status["running"] = True
    fiverr_worker_status["message"] = f"Running fiverr queue worker for '{query}'"
    fiverr_worker_status["last_result"] = None
    try:
        result = await worker_orchestrator.run_fiverr_pipeline(
            query=query,
            limit=limit,
            live_send=live_send,
        )
        fiverr_worker_status["last_result"] = result
        fiverr_worker_status["message"] = "Worker run completed"
    except Exception as e:
        fiverr_worker_status["message"] = f"Worker run failed: {str(e)}"
    finally:
        fiverr_worker_status["running"] = False


async def _run_linkedin_worker_task(query: str, limit: int, live_send: bool):
    linkedin_worker_status["running"] = True
    linkedin_worker_status["message"] = f"Running linkedin queue worker for '{query}'"
    linkedin_worker_status["last_result"] = None
    try:
        result = await worker_orchestrator.run_linkedin_pipeline(
            query=query,
            limit=limit,
            live_send=live_send,
        )
        linkedin_worker_status["last_result"] = result
        linkedin_worker_status["message"] = "Worker run completed"
    except Exception as e:
        linkedin_worker_status["message"] = f"Worker run failed: {str(e)}"
    finally:
        linkedin_worker_status["running"] = False


async def _run_x_threads_worker_task(query: str, limit: int, live_send: bool):
    x_threads_worker_status["running"] = True
    x_threads_worker_status["message"] = f"Running x_threads queue worker for '{query}'"
    x_threads_worker_status["last_result"] = None
    try:
        result = await worker_orchestrator.run_x_threads_pipeline(
            query=query,
            limit=limit,
            live_send=live_send,
        )
        x_threads_worker_status["last_result"] = result
        x_threads_worker_status["message"] = "Worker run completed"
    except Exception as e:
        x_threads_worker_status["message"] = f"Worker run failed: {str(e)}"
    finally:
        x_threads_worker_status["running"] = False

# 5. Static Assets & Frontend
app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")

@app.get("/")
async def serve_dashboard():
    # Prefer package resource resolution for installed environments.
    candidates = [
        CORE_DIR / "dashboard.html",
        BASE_DIR / "dashboard.html",
    ]

    try:
        resource_path = resources.files("core").joinpath("dashboard.html")
        if resource_path.is_file():
            candidates.insert(0, Path(str(resource_path)))
    except Exception:
        pass

    for path in candidates:
        if path.exists() and path.is_file():
            return FileResponse(str(path))

    return JSONResponse(
        status_code=500,
        content={
            "error": "dashboard_missing",
            "detail": "dashboard.html is not bundled in this installation.",
        },
    )

if __name__ == "__main__":
    import uvicorn
    import os
    # Security: Bind to localhost by default for local development. 
    # Use environment variables if external exposure is needed.
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run("server:app", host=host, port=8000, reload=True)
