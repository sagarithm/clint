from __future__ import annotations

from typing import Any, Dict

import aiosqlite


def _safe_rate(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


async def get_kpi_summary(db: aiosqlite.Connection) -> Dict[str, Any]:
    async with db.execute("SELECT COUNT(*) FROM leads") as c:
        total_leads = int((await c.fetchone())[0])

    async with db.execute("SELECT COUNT(*) FROM leads WHERE status = 'new'") as c:
        pending_leads = int((await c.fetchone())[0])

    async with db.execute("SELECT COUNT(*) FROM leads WHERE status = 'sent'") as c:
        sent_leads = int((await c.fetchone())[0])

    async with db.execute("SELECT COUNT(*) FROM reply_events") as c:
        total_replies = int((await c.fetchone())[0])

    async with db.execute("SELECT COUNT(*) FROM reply_events WHERE classifier_label = 'replied_positive'") as c:
        positive_replies = int((await c.fetchone())[0])

    async with db.execute("SELECT COUNT(*) FROM reply_events WHERE classifier_label = 'replied_negative'") as c:
        negative_replies = int((await c.fetchone())[0])

    async with db.execute("SELECT COUNT(*) FROM leads WHERE status = 'booked'") as c:
        booked = int((await c.fetchone())[0])

    async with db.execute("SELECT COUNT(*) FROM message_drafts") as c:
        drafts = int((await c.fetchone())[0])

    async with db.execute("SELECT COUNT(*) FROM message_drafts WHERE rejection_reason IS NOT NULL AND rejection_reason != ''") as c:
        rejected_drafts = int((await c.fetchone())[0])

    async with db.execute("SELECT COUNT(*) FROM compliance_checks WHERE decision = 'blocked'") as c:
        policy_blocks = int((await c.fetchone())[0])

    return {
        "top_funnel": {
            "leads_discovered": total_leads,
            "leads_pending": pending_leads,
        },
        "mid_funnel": {
            "messages_generated": drafts,
            "messages_sent": sent_leads,
            "reply_total": total_replies,
            "positive_reply_rate": _safe_rate(positive_replies, sent_leads),
            "negative_reply_rate": _safe_rate(negative_replies, sent_leads),
        },
        "bottom_funnel": {
            "meetings_booked": booked,
            "booking_rate": _safe_rate(booked, sent_leads),
        },
        "quality_and_safety": {
            "draft_rejection_rate": _safe_rate(rejected_drafts, drafts),
            "policy_blocks": policy_blocks,
        },
    }
