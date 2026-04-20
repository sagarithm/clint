from __future__ import annotations

import json
from typing import Any, Dict, Optional

import aiosqlite


async def save_enrichment_snapshot(
    db: aiosqlite.Connection,
    *,
    lead_id: int,
    website_summary: str,
    rating: float = 0.0,
    reviews_count: int = 0,
    social_links: Optional[Dict[str, Any]] = None,
    contact_confidence: float = 0.0,
    snapshot_version: str = "v2",
) -> None:
    await db.execute(
        """
        INSERT INTO lead_enrichment_snapshots (
            lead_id,
            snapshot_version,
            website_summary,
            rating,
            reviews_count,
            social_links_json,
            contact_confidence
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            snapshot_version,
            website_summary,
            rating,
            reviews_count,
            json.dumps(social_links or {}, default=str),
            contact_confidence,
        ),
    )


async def save_score_snapshot(
    db: aiosqlite.Connection,
    *,
    lead_id: int,
    priority_score: float,
    fit_score: float = 0.0,
    intent_score: float = 0.0,
    authority_score: float = 0.0,
    timing_score: float = 0.0,
    risk_score: float = 0.0,
    reason_codes: Optional[Dict[str, Any]] = None,
) -> None:
    await db.execute(
        """
        INSERT INTO lead_scores (
            lead_id,
            fit_score,
            intent_score,
            authority_score,
            timing_score,
            risk_score,
            priority_score,
            reason_codes_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            fit_score,
            intent_score,
            authority_score,
            timing_score,
            risk_score,
            priority_score,
            json.dumps(reason_codes or {}, default=str),
        ),
    )


async def save_message_draft(
    db: aiosqlite.Connection,
    *,
    lead_id: int,
    channel: str,
    subject: Optional[str],
    body: str,
    template_id: Optional[str] = None,
    prompt_version: str = "v2-legacy",
    quality_score: float = 0.0,
    rejection_reason: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> None:
    await db.execute(
        """
        INSERT INTO message_drafts (
            lead_id,
            channel,
            template_id,
            prompt_version,
            subject,
            body,
            quality_score,
            rejection_reason,
            correlation_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            channel,
            template_id,
            prompt_version,
            subject,
            body,
            quality_score,
            rejection_reason,
            correlation_id,
        ),
    )


async def log_outreach_event_v2(
    db: aiosqlite.Connection,
    *,
    lead_id: int,
    channel: str,
    event_type: str,
    payload: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> None:
    await db.execute(
        """
        INSERT INTO outreach_events (
            lead_id,
            channel,
            event_type,
            event_payload_json,
            correlation_id
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            channel,
            event_type,
            json.dumps(payload or {}, default=str),
            correlation_id,
        ),
    )


async def save_reply_event(
    db: aiosqlite.Connection,
    *,
    lead_id: int,
    channel: str,
    thread_ref: str,
    reply_text: str,
    classifier_label: str,
    classifier_confidence: float,
    requires_human_review: bool,
) -> None:
    await db.execute(
        """
        INSERT INTO reply_events (
            lead_id,
            channel,
            thread_ref,
            reply_text,
            classifier_label,
            classifier_confidence,
            requires_human_review
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            channel,
            thread_ref,
            reply_text,
            classifier_label,
            classifier_confidence,
            1 if requires_human_review else 0,
        ),
    )
