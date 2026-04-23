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
from scrapers.connectors.fiverr_connector import FiverrConnector
from scrapers.connectors.linkedin_connector import LinkedInConnector
from scrapers.connectors.reddit_connector import RedditConnector
from scrapers.connectors.upwork_connector import UpworkConnector
from scrapers.connectors.x_threads_connector import XThreadsConnector
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
        self.fiverr = FiverrConnector()
        self.linkedin = LinkedInConnector()
        self.reddit = RedditConnector()
        self.upwork = UpworkConnector()
        self.x_threads = XThreadsConnector()
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
        return await self._run_pipeline(
            connector=self.reddit,
            source_platform="reddit",
            source_label="Reddit",
            adapter_version="reddit.v2",
            pipeline_key="reddit_pipeline",
            query=query,
            limit=limit,
            live_send=live_send,
        )

    async def run_upwork_pipeline(
        self,
        *,
        query: str,
        limit: int = 20,
        live_send: bool = False,
    ) -> Dict[str, Any]:
        return await self._run_pipeline(
            connector=self.upwork,
            source_platform="upwork",
            source_label="Upwork",
            adapter_version="upwork.v2",
            pipeline_key="upwork_pipeline",
            query=query,
            limit=limit,
            live_send=live_send,
        )

    async def run_fiverr_pipeline(
        self,
        *,
        query: str,
        limit: int = 20,
        live_send: bool = False,
    ) -> Dict[str, Any]:
        return await self._run_pipeline(
            connector=self.fiverr,
            source_platform="fiverr",
            source_label="Fiverr",
            adapter_version="fiverr.v2",
            pipeline_key="fiverr_pipeline",
            query=query,
            limit=limit,
            live_send=live_send,
        )

    async def run_linkedin_pipeline(
        self,
        *,
        query: str,
        limit: int = 20,
        live_send: bool = False,
    ) -> Dict[str, Any]:
        return await self._run_pipeline(
            connector=self.linkedin,
            source_platform="linkedin",
            source_label="LinkedIn",
            adapter_version="linkedin.v2",
            pipeline_key="linkedin_pipeline",
            query=query,
            limit=limit,
            live_send=live_send,
        )

    async def run_x_threads_pipeline(
        self,
        *,
        query: str,
        limit: int = 20,
        live_send: bool = False,
    ) -> Dict[str, Any]:
        return await self._run_pipeline(
            connector=self.x_threads,
            source_platform="x_threads",
            source_label="XThreads",
            adapter_version="x_threads.v2",
            pipeline_key="x_threads_pipeline",
            query=query,
            limit=limit,
            live_send=live_send,
        )

    async def _run_pipeline(
        self,
        *,
        connector: Any,
        source_platform: str,
        source_label: str,
        adapter_version: str,
        pipeline_key: str,
        query: str,
        limit: int,
        live_send: bool,
    ) -> Dict[str, Any]:
        raw_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        enrich_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        score_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        draft_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        dispatch_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

        result = WorkerResult()

        raw_records = await connector.fetch({"query": query, "limit": limit})
        result.discovered = len(raw_records)
        for record in raw_records:
            await raw_queue.put(record)

        await self._ingest_worker(
            raw_queue,
            enrich_queue,
            result,
            connector=connector,
            source_platform=source_platform,
            source_label=source_label,
            adapter_version=adapter_version,
        )
        await self._enrich_worker(enrich_queue, score_queue, result, pipeline_key=pipeline_key)
        await self._score_worker(score_queue, draft_queue, result, pipeline_key=pipeline_key)
        await self._draft_worker(draft_queue, dispatch_queue, result, pipeline_key=pipeline_key)
        await self._dispatch_worker(
            dispatch_queue,
            result,
            live_send=live_send,
            pipeline_key=pipeline_key,
        )

        return {
            "query": query,
            "source": source_platform,
            "live_send": live_send,
            "result": result.__dict__,
        }

    async def replay_reddit_raw_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self.reddit.normalize(raw_record)
        valid, reason = self.reddit.validate(normalized)
        if not valid:
            raise ValueError(reason or "invalid_record")

        lead_id = await self._upsert_lead_from_record(
            raw_record,
            source_label="Reddit",
            default_category="Reddit",
        )
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

    async def replay_upwork_raw_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self.upwork.normalize(raw_record)
        valid, reason = self.upwork.validate(normalized)
        if not valid:
            raise ValueError(reason or "invalid_record")

        lead_id = await self._upsert_lead_from_record(
            raw_record,
            source_label="Upwork",
            default_category="Upwork",
        )
        async with get_db() as db:
            await persist_lead_source(
                db,
                lead_id=lead_id,
                record=normalized,
                adapter_version="upwork.v2.replay",
            )
            await publish_event(
                db,
                topic=TOPIC_CONNECTOR_NORMALIZED,
                lead_id=lead_id,
                payload={"source": "upwork", "replay": True},
            )
            await db.commit()

        return {"lead_id": lead_id, "source_record_id": normalized.get("source_record_id")}

    async def replay_fiverr_raw_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self.fiverr.normalize(raw_record)
        valid, reason = self.fiverr.validate(normalized)
        if not valid:
            raise ValueError(reason or "invalid_record")

        lead_id = await self._upsert_lead_from_record(
            raw_record,
            source_label="Fiverr",
            default_category="Fiverr",
        )
        async with get_db() as db:
            await persist_lead_source(
                db,
                lead_id=lead_id,
                record=normalized,
                adapter_version="fiverr.v2.replay",
            )
            await publish_event(
                db,
                topic=TOPIC_CONNECTOR_NORMALIZED,
                lead_id=lead_id,
                payload={"source": "fiverr", "replay": True},
            )
            await db.commit()

        return {"lead_id": lead_id, "source_record_id": normalized.get("source_record_id")}

    async def replay_linkedin_raw_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self.linkedin.normalize(raw_record)
        valid, reason = self.linkedin.validate(normalized)
        if not valid:
            raise ValueError(reason or "invalid_record")

        lead_id = await self._upsert_lead_from_record(
            raw_record,
            source_label="LinkedIn",
            default_category="LinkedIn",
        )
        async with get_db() as db:
            await persist_lead_source(
                db,
                lead_id=lead_id,
                record=normalized,
                adapter_version="linkedin.v2.replay",
            )
            await publish_event(
                db,
                topic=TOPIC_CONNECTOR_NORMALIZED,
                lead_id=lead_id,
                payload={"source": "linkedin", "replay": True},
            )
            await db.commit()

        return {"lead_id": lead_id, "source_record_id": normalized.get("source_record_id")}

    async def replay_x_threads_raw_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self.x_threads.normalize(raw_record)
        valid, reason = self.x_threads.validate(normalized)
        if not valid:
            raise ValueError(reason or "invalid_record")

        lead_id = await self._upsert_lead_from_record(
            raw_record,
            source_label="XThreads",
            default_category="XThreads",
        )
        async with get_db() as db:
            await persist_lead_source(
                db,
                lead_id=lead_id,
                record=normalized,
                adapter_version="x_threads.v2.replay",
            )
            await publish_event(
                db,
                topic=TOPIC_CONNECTOR_NORMALIZED,
                lead_id=lead_id,
                payload={"source": "x_threads", "replay": True},
            )
            await db.commit()

        return {"lead_id": lead_id, "source_record_id": normalized.get("source_record_id")}

    async def replay_enrich_stage(self, *, lead_id: int, source: str = "") -> Dict[str, Any]:
        lead = await self._get_lead(lead_id)
        if lead is None:
            raise ValueError(f"lead_not_found:{lead_id}")

        pipeline_key = self._pipeline_key_from_source(source)
        result = WorkerResult()
        enrich_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        score_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        draft_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        dispatch_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

        await enrich_queue.put(lead)
        await self._enrich_worker(enrich_queue, score_queue, result, pipeline_key=pipeline_key)
        await self._score_worker(score_queue, draft_queue, result, pipeline_key=pipeline_key)
        await self._draft_worker(draft_queue, dispatch_queue, result, pipeline_key=pipeline_key)
        await self._dispatch_worker(
            dispatch_queue,
            result,
            live_send=False,
            pipeline_key=pipeline_key,
        )
        return {"lead_id": lead_id, "stage": "enrich", "pipeline_key": pipeline_key, "result": result.__dict__}

    async def replay_draft_stage(self, *, lead_id: int, source: str = "") -> Dict[str, Any]:
        lead = await self._get_lead(lead_id)
        if lead is None:
            raise ValueError(f"lead_not_found:{lead_id}")

        pipeline_key = self._pipeline_key_from_source(source)
        result = WorkerResult()
        draft_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        dispatch_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

        await draft_queue.put(lead)
        await self._draft_worker(draft_queue, dispatch_queue, result, pipeline_key=pipeline_key)
        await self._dispatch_worker(
            dispatch_queue,
            result,
            live_send=False,
            pipeline_key=pipeline_key,
        )
        return {"lead_id": lead_id, "stage": "draft", "pipeline_key": pipeline_key, "result": result.__dict__}

    async def replay_dispatch_stage(self, *, lead_id: int, source: str = "", live_send: bool = False) -> Dict[str, Any]:
        lead = await self._get_lead(lead_id)
        if lead is None:
            raise ValueError(f"lead_not_found:{lead_id}")

        latest_draft = await self._get_latest_message_draft(lead_id, channel="email")
        if latest_draft is None:
            raise ValueError(f"no_message_draft:{lead_id}")

        pipeline_key = self._pipeline_key_from_source(source)
        result = WorkerResult()
        dispatch_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        await dispatch_queue.put(
            {
                "lead": lead,
                "subject": str(latest_draft.get("subject") or ""),
                "body": str(latest_draft.get("body") or ""),
            }
        )
        await self._dispatch_worker(
            dispatch_queue,
            result,
            live_send=live_send,
            pipeline_key=pipeline_key,
        )
        return {
            "lead_id": lead_id,
            "stage": "dispatch",
            "pipeline_key": pipeline_key,
            "live_send": live_send,
            "result": result.__dict__,
        }

    async def _ingest_worker(
        self,
        raw_queue: asyncio.Queue[Dict[str, Any]],
        enrich_queue: asyncio.Queue[Dict[str, Any]],
        result: WorkerResult,
        *,
        connector: Any,
        source_platform: str,
        source_label: str,
        adapter_version: str,
    ) -> None:
        while not raw_queue.empty():
            raw = await raw_queue.get()
            try:
                normalized = connector.normalize(raw)
                valid, reason = connector.validate(normalized)
                if not valid:
                    async with get_db() as db:
                        await log_connector_rejection(
                            db,
                            source_platform=source_platform,
                            reason_code=reason or "invalid_record",
                            reason_detail=f"{source_platform} ingestion validation failed",
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

                lead_id = await self._upsert_lead_from_record(
                    raw,
                    source_label=source_label,
                    default_category=source_label,
                )
                async with get_db() as db:
                    await persist_lead_source(
                        db,
                        lead_id=lead_id,
                        record=normalized,
                        adapter_version=adapter_version,
                    )
                    await publish_event(
                        db,
                        topic=TOPIC_CONNECTOR_RAW,
                        lead_id=lead_id,
                        payload={"source": source_platform},
                    )
                    await publish_event(
                        db,
                        topic=TOPIC_CONNECTOR_NORMALIZED,
                        lead_id=lead_id,
                        payload={"source": source_platform, "source_url": normalized.get("source_url")},
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
        *,
        pipeline_key: str,
    ) -> None:
        while not enrich_queue.empty():
            lead = await enrich_queue.get()
            try:
                website = str(lead.get("website") or "").strip()
                crawl_data: Dict[str, Any] = {}
                if website:
                    crawl_data = await self.crawler.crawl(
                        website,
                        lead.get("name", "unknown"),
                        query_id=pipeline_key.upper()[:32],
                    )

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
                        payload={"source": pipeline_key},
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
        *,
        pipeline_key: str,
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
                        reason=f"{pipeline_key}_scored",
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
                    reason_codes={"source": pipeline_key, "codes": score_data["reason_codes"]},
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
        *,
        pipeline_key: str,
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
                        template_id=pipeline_key,
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
                        payload={"stage": "draft", "source": pipeline_key},
                    )
                    await db.commit()

    async def _dispatch_worker(
        self,
        dispatch_queue: asyncio.Queue[Dict[str, Any]],
        result: WorkerResult,
        *,
        live_send: bool,
        pipeline_key: str,
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
                        payload={"reason": reason, "source": pipeline_key},
                    )
                    await db.commit()
                    result.blocked += 1
                    continue

                try:
                    await transition_lead_state(
                        db,
                        lead["id"],
                        "queued_for_send",
                        reason=f"{pipeline_key}_dispatch_ready",
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
                            reason=f"{pipeline_key}_dispatch_success",
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
                        payload={"status": "sent", "source": pipeline_key},
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
                        payload={"status": "failed", "source": pipeline_key},
                    )
                    await publish_deadletter(
                        db,
                        topic=TOPIC_DEADLETTER,
                        lead_id=lead["id"],
                        channel="email",
                        error_message="dispatch_failed",
                        payload={"stage": "dispatch", "source": pipeline_key},
                    )
                    await db.commit()
                result.failed += 1

    async def _upsert_lead_from_record(
        self,
        record: Dict[str, Any],
        *,
        source_label: str,
        default_category: str,
    ) -> int:
        name = str(record.get("name") or "Unnamed Lead")[:255]
        website = record.get("website")
        category = record.get("category") or default_category
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
                    source_label,
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

    async def _get_latest_message_draft(self, lead_id: int, *, channel: str = "email") -> Optional[Dict[str, Any]]:
        async with get_db() as db:
            async with db.execute(
                """
                SELECT *
                FROM message_drafts
                WHERE lead_id = ? AND channel = ?
                ORDER BY created_at_utc DESC, id DESC
                LIMIT 1
                """,
                (lead_id, channel),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return dict(row)

    @staticmethod
    def _pipeline_key_from_source(source: str) -> str:
        source_l = str(source or "").lower()
        if "linkedin" in source_l:
            return "linkedin_pipeline"
        if "x_threads" in source_l or "xthreads" in source_l or "nitter" in source_l:
            return "x_threads_pipeline"
        if "fiverr" in source_l:
            return "fiverr_pipeline"
        if "upwork" in source_l:
            return "upwork_pipeline"
        if "reddit" in source_l:
            return "reddit_pipeline"
        return "reddit_pipeline"
