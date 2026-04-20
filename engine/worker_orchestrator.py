from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional

from core.connectors import (
    log_connector_rejection,
    persist_lead_source,
)
from core.database import get_db
from core.event_bus import (
    TOPIC_CONNECTOR_NORMALIZED,
    TOPIC_CONNECTOR_RAW,
    TOPIC_DEADLETTER,
    TOPIC_DISPATCH_COMPLETED,
    TOPIC_DISPATCH_REQUESTED,
    TOPIC_ENRICHMENT_COMPLETED,
    TOPIC_MESSAGE_GENERATED,
    TOPIC_SCORING_COMPLETED,
    publish_deadletter,
    publish_event,
)
from core.policy import enforce_pre_send_policy
from core.quality_gate import evaluate_message_quality
from core.reliability import send_with_retry
from core.scorer import score_lead_v2
from core.state_machine import transition_lead_state
from core.v2_store import (
    log_outreach_event_v2,
    save_enrichment_snapshot,
    save_message_draft,
    save_score_snapshot,
)
from engine.proposer import Proposer
from outreach.email_operator import EmailOperator
from scrapers.connectors.reddit_connector import RedditConnector
from scrapers.web_crawler import WebCrawler


@dataclass
class WorkerResult:
    discovered: int = 0
    normalized: int = 0
    enriched: int = 0
    scored: int = 0
    drafted: int = 0
    dispatch_attempted: int = 0
    sent: int = 0
    failed: int = 0
    blocked: int = 0


class QueueWorkerOrchestrator:
    """Queue-driven staged pipeline for connector ingestion and outreach processing."""

    def __init__(self) -> None:
        self.reddit = RedditConnector()
        self.crawler = WebCrawler()
        self.proposer = Proposer()
        self.email = EmailOperator()

    async def run_reddit_pipeline(
        self,
        *,
        query: str,
        limit: int = 20,
        live_send: bool = False,
    ) -> Dict[str, Any]:
        raw_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        enrich_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        score_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        draft_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        dispatch_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

        result = WorkerResult()

        raw_records = await self.reddit.fetch({"query": query, "limit": limit})
        result.discovered = len(raw_records)
        for record in raw_records:
            await raw_queue.put(record)

        await self._ingest_worker(raw_queue, enrich_queue, result)
        await self._enrich_worker(enrich_queue, score_queue, result)
        await self._score_worker(score_queue, draft_queue, result)
        await self._draft_worker(draft_queue, dispatch_queue, result)
        await self._dispatch_worker(dispatch_queue, result, live_send=live_send)

        return {
            "query": query,
            "live_send": live_send,
            "result": result.__dict__,
        }

    async def replay_reddit_raw_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self.reddit.normalize(raw_record)
        valid, reason = self.reddit.validate(normalized)
        if not valid:
            raise ValueError(reason or "invalid_record")

        lead_id = await self._upsert_lead_from_record(raw_record)
        async with get_db() as db:
            await persist_lead_source(
                db,
                lead_id=lead_id,
                record=normalized,
                adapter_version="reddit.v2.replay",
            )
            await publish_event(
                db,
                topic=TOPIC_CONNECTOR_NORMALIZED,
                lead_id=lead_id,
                payload={"source": "reddit", "replay": True},
            )
            await db.commit()

        return {"lead_id": lead_id, "source_record_id": normalized.get("source_record_id")}

    async def _ingest_worker(
        self,
        raw_queue: asyncio.Queue[Dict[str, Any]],
        enrich_queue: asyncio.Queue[Dict[str, Any]],
        result: WorkerResult,
    ) -> None:
        while not raw_queue.empty():
            raw = await raw_queue.get()
            try:
                normalized = self.reddit.normalize(raw)
                valid, reason = self.reddit.validate(normalized)
                if not valid:
                    async with get_db() as db:
                        await log_connector_rejection(
                            db,
                            source_platform="reddit",
                            reason_code=reason or "invalid_record",
                            reason_detail="reddit ingestion validation failed",
                            raw_payload=raw,
                        )
                        await publish_deadletter(
                            db,
                            topic=TOPIC_DEADLETTER,
                            error_message=reason or "invalid_record",
                            payload=raw,
                            channel="system",
                        )
                        await db.commit()
                    continue

                lead_id = await self._upsert_lead_from_record(raw)
                async with get_db() as db:
                    await persist_lead_source(
                        db,
                        lead_id=lead_id,
                        record=normalized,
                        adapter_version="reddit.v2",
                    )
                    await publish_event(
                        db,
                        topic=TOPIC_CONNECTOR_RAW,
                        lead_id=lead_id,
                        payload={"source": "reddit"},
                    )
                    await publish_event(
                        db,
                        topic=TOPIC_CONNECTOR_NORMALIZED,
                        lead_id=lead_id,
                        payload={"source": "reddit", "source_url": normalized.get("source_url")},
                    )
                    await db.commit()

                lead = await self._get_lead(lead_id)
                if lead is not None:
                    await enrich_queue.put(lead)
                    result.normalized += 1
            except Exception as e:
                async with get_db() as db:
                    await publish_deadletter(
                        db,
                        topic=TOPIC_DEADLETTER,
                        error_message=str(e),
                        payload=raw,
                        channel="system",
                    )
                    await db.commit()

    async def _enrich_worker(
        self,
        enrich_queue: asyncio.Queue[Dict[str, Any]],
        score_queue: asyncio.Queue[Dict[str, Any]],
        result: WorkerResult,
    ) -> None:
        while not enrich_queue.empty():
            lead = await enrich_queue.get()
            try:
                website = str(lead.get("website") or "").strip()
                crawl_data: Dict[str, Any] = {}
                if website:
                    crawl_data = await self.crawler.crawl(website, lead.get("name", "unknown"), query_id="REDDIT_PIPE")

                emails = ",".join(crawl_data.get("emails", [])) or (lead.get("email") or "N/A")
                about = crawl_data.get("about_us_info") or lead.get("about_us_info") or ""

                async with get_db() as db:
                    await db.execute(
                        "UPDATE leads SET email = ?, about_us_info = ? WHERE id = ?",
                        (emails, about, lead["id"]),
                    )
                    await save_enrichment_snapshot(
                        db,
                        lead_id=lead["id"],
                        website_summary=about,
                        rating=float(lead.get("rating") or 0.0),
                        reviews_count=int(lead.get("reviews_count") or 0),
                        social_links=crawl_data.get("social_links") or {},
                    )
                    await publish_event(
                        db,
                        topic=TOPIC_ENRICHMENT_COMPLETED,
                        lead_id=lead["id"],
                        payload={"source": "reddit_pipeline"},
                    )
                    await db.commit()

                updated = await self._get_lead(lead["id"])
                if updated is not None:
                    await score_queue.put(updated)
                    result.enriched += 1
            except Exception as e:
                async with get_db() as db:
                    await publish_deadletter(
                        db,
                        topic=TOPIC_DEADLETTER,
                        lead_id=lead.get("id"),
                        error_message=str(e),
                        payload={"stage": "enrich"},
                    )
                    await db.commit()

    async def _score_worker(
        self,
        score_queue: asyncio.Queue[Dict[str, Any]],
        draft_queue: asyncio.Queue[Dict[str, Any]],
        result: WorkerResult,
    ) -> None:
        while not score_queue.empty():
            lead = await score_queue.get()
            score_data = score_lead_v2(lead)
            score_value = int(round(score_data["priority_score"]))

            async with get_db() as db:
                await db.execute("UPDATE leads SET score = ? WHERE id = ?", (score_value, lead["id"]))
                try:
                    await transition_lead_state(
                        db,
                        lead["id"],
                        "scored",
                        reason="reddit_pipeline_scored",
                        actor="worker.score",
                    )
                except ValueError:
                    pass
                await save_score_snapshot(
                    db,
                    lead_id=lead["id"],
                    fit_score=score_data["fit_score"],
                    intent_score=score_data["intent_score"],
                    authority_score=score_data["authority_score"],
                    timing_score=score_data["timing_score"],
                    risk_score=score_data["risk_score"],
                    priority_score=score_data["priority_score"],
                    reason_codes={"source": "reddit_pipeline", "codes": score_data["reason_codes"]},
                )
                await publish_event(
                    db,
                    topic=TOPIC_SCORING_COMPLETED,
                    lead_id=lead["id"],
                    payload={"priority_score": score_data["priority_score"]},
                )
                await db.commit()

            updated = await self._get_lead(lead["id"])
            if updated is not None:
                await draft_queue.put(updated)
                result.scored += 1

    async def _draft_worker(
        self,
        draft_queue: asyncio.Queue[Dict[str, Any]],
        dispatch_queue: asyncio.Queue[Dict[str, Any]],
        result: WorkerResult,
    ) -> None:
        while not draft_queue.empty():
            lead = await draft_queue.get()
            try:
                subject, body = await self.proposer.generate_proposal(
                    lead_name=lead["name"],
                    audit_summary=lead.get("about_us_info") or "Potential website and conversion improvements.",
                    channel="email",
                    rating=lead.get("rating", 0.0),
                    reviews_count=lead.get("reviews_count", 0),
                    business_category=lead.get("business_category"),
                    has_website=bool(lead.get("website")),
                    about_us_info=lead.get("about_us_info"),
                    score=float(lead.get("score") or 0),
                    service="Website Redesign",
                )

                quality = evaluate_message_quality(
                    lead_name=lead["name"],
                    subject=subject,
                    body=body,
                    channel="email",
                )

                async with get_db() as db:
                    await save_message_draft(
                        db,
                        lead_id=lead["id"],
                        channel="email",
                        subject=subject,
                        body=body,
                        template_id="reddit_pipeline",
                        prompt_version="v2-worker",
                        quality_score=quality["quality_score"],
                        rejection_reason=",".join(quality["reasons"]) if not quality["passed"] else None,
                    )
                    await publish_event(
                        db,
                        topic=TOPIC_MESSAGE_GENERATED,
                        lead_id=lead["id"],
                        channel="email",
                        payload={"quality_score": quality["quality_score"], "quality_passed": quality["passed"]},
                    )
                    await db.commit()

                if not quality["passed"]:
                    result.blocked += 1
                    continue

                await dispatch_queue.put({"lead": lead, "subject": subject, "body": body})
                result.drafted += 1
            except Exception as e:
                async with get_db() as db:
                    await publish_deadletter(
                        db,
                        topic=TOPIC_DEADLETTER,
                        lead_id=lead.get("id"),
                        error_message=str(e),
                        payload={"stage": "draft"},
                    )
                    await db.commit()

    async def _dispatch_worker(
        self,
        dispatch_queue: asyncio.Queue[Dict[str, Any]],
        result: WorkerResult,
        *,
        live_send: bool,
    ) -> None:
        while not dispatch_queue.empty():
            item = await dispatch_queue.get()
            lead = item["lead"]
            subject = item["subject"]
            body = item["body"]

            async with get_db() as db:
                allowed, reason = await enforce_pre_send_policy(db, lead=lead, channel="email")
                if not allowed:
                    try:
                        await transition_lead_state(
                            db,
                            lead["id"],
                            "suppressed",
                            reason=reason,
                            actor="worker.dispatch.policy",
                        )
                    except ValueError:
                        pass
                    await log_outreach_event_v2(
                        db,
                        lead_id=lead["id"],
                        channel="email",
                        event_type="policy_blocked",
                        payload={"reason": reason, "source": "reddit_pipeline"},
                    )
                    await db.commit()
                    result.blocked += 1
                    continue

                try:
                    await transition_lead_state(
                        db,
                        lead["id"],
                        "queued_for_send",
                        reason="reddit_pipeline_dispatch_ready",
                        actor="worker.dispatch",
                    )
                except ValueError:
                    pass

                await publish_event(
                    db,
                    topic=TOPIC_DISPATCH_REQUESTED,
                    lead_id=lead["id"],
                    channel="email",
                    payload={"live_send": live_send},
                )
                await db.commit()

            result.dispatch_attempted += 1
            if not live_send:
                async with get_db() as db:
                    await log_outreach_event_v2(
                        db,
                        lead_id=lead["id"],
                        channel="email",
                        event_type="dispatch_dry_run",
                        payload={"status": "simulated"},
                    )
                    await publish_event(
                        db,
                        topic=TOPIC_DISPATCH_COMPLETED,
                        lead_id=lead["id"],
                        channel="email",
                        payload={"status": "simulated"},
                    )
                    await db.commit()
                continue

            to_email = str(lead.get("email") or "").split(",")[0].strip()
            success = await send_with_retry(lambda: self.email.send(to_email, subject, body), retries=3)
            if success is True:
                async with get_db() as db:
                    try:
                        await transition_lead_state(
                            db,
                            lead["id"],
                            "sent",
                            reason="reddit_pipeline_dispatch_success",
                            actor="worker.dispatch",
                        )
                    except ValueError:
                        pass
                    await db.execute("UPDATE leads SET last_outreach = datetime('now') WHERE id = ?", (lead["id"],))
                    await log_outreach_event_v2(
                        db,
                        lead_id=lead["id"],
                        channel="email",
                        event_type="dispatch_success",
                        payload={"status": "sent", "source": "reddit_pipeline"},
                    )
                    await publish_event(
                        db,
                        topic=TOPIC_DISPATCH_COMPLETED,
                        lead_id=lead["id"],
                        channel="email",
                        payload={"status": "sent"},
                    )
                    await db.commit()
                result.sent += 1
            else:
                async with get_db() as db:
                    await log_outreach_event_v2(
                        db,
                        lead_id=lead["id"],
                        channel="email",
                        event_type="dispatch_failed",
                        payload={"status": "failed", "source": "reddit_pipeline"},
                    )
                    await publish_deadletter(
                        db,
                        topic=TOPIC_DEADLETTER,
                        lead_id=lead["id"],
                        channel="email",
                        error_message="dispatch_failed",
                        payload={"stage": "dispatch", "source": "reddit_pipeline"},
                    )
                    await db.commit()
                result.failed += 1

    async def _upsert_lead_from_record(self, record: Dict[str, Any]) -> int:
        name = str(record.get("name") or "Unnamed Lead")[:255]
        website = record.get("website")
        category = record.get("category") or "Reddit"
        business_category = record.get("business_category") or "Web Solutions"

        async with get_db() as db:
            async with db.execute("SELECT id FROM leads WHERE name = ?", (name,)) as cursor:
                existing = await cursor.fetchone()
            if existing:
                return int(existing[0])

            cur = await db.execute(
                """
                INSERT INTO leads (name, website, phone, business_category, source, category, status, lifecycle_state)
                VALUES (?, ?, ?, ?, ?, ?, 'new', 'new')
                """,
                (
                    name,
                    website,
                    record.get("phone"),
                    business_category,
                    "Reddit",
                    category,
                ),
            )
            await db.commit()
            return int(cur.lastrowid)

    async def _get_lead(self, lead_id: int) -> Optional[Dict[str, Any]]:
        async with get_db() as db:
            async with db.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return dict(row)
