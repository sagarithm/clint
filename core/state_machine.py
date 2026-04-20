from __future__ import annotations

from typing import Optional

import aiosqlite


LEAD_STATES = {
    "new",
    "normalized",
    "enriched",
    "scored",
    "queued_for_review",
    "queued_for_send",
    "follow_up_ready",
    "sent",
    "replied_positive",
    "replied_neutral",
    "replied_negative",
    "booked",
    "disqualified",
    "suppressed",
}


ALLOWED_TRANSITIONS = {
    "new": {"normalized", "enriched", "scored", "queued_for_send", "disqualified", "suppressed", "sent"},
    "normalized": {"enriched", "scored", "queued_for_send", "disqualified", "suppressed", "sent"},
    "enriched": {"scored", "queued_for_review", "queued_for_send", "disqualified", "suppressed", "sent"},
    "scored": {"queued_for_review", "queued_for_send", "disqualified", "suppressed", "sent"},
    "queued_for_review": {"queued_for_send", "disqualified", "suppressed"},
    "queued_for_send": {"sent", "suppressed", "disqualified"},
    "sent": {"follow_up_ready", "replied_positive", "replied_neutral", "replied_negative", "suppressed"},
    "follow_up_ready": {"sent", "replied_positive", "replied_neutral", "replied_negative", "suppressed"},
    "replied_positive": {"booked", "disqualified", "suppressed"},
    "replied_neutral": {"queued_for_send", "disqualified", "suppressed"},
    "replied_negative": {"disqualified", "suppressed"},
    "booked": set(),
    "disqualified": set(),
    "suppressed": set(),
}


def _normalize_state(value: Optional[str]) -> str:
    if not value:
        return "new"
    return str(value).strip().lower()


def can_transition(from_state: Optional[str], to_state: str) -> bool:
    source = _normalize_state(from_state)
    target = _normalize_state(to_state)
    if target not in LEAD_STATES:
        return False
    if source == target:
        return True
    allowed_targets = ALLOWED_TRANSITIONS.get(source, set())
    return target in allowed_targets


async def transition_lead_state(
    db: aiosqlite.Connection,
    lead_id: int,
    to_state: str,
    *,
    reason: Optional[str] = None,
    actor: str = "system",
    sync_status: bool = True,
) -> None:
    target = _normalize_state(to_state)
    if target not in LEAD_STATES:
        raise ValueError(f"Unsupported lead state: {to_state}")

    async with db.execute(
        "SELECT lifecycle_state, status FROM leads WHERE id = ?",
        (lead_id,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise ValueError(f"Lead not found: {lead_id}")

    current_state = _normalize_state(row[0] or row[1])
    if not can_transition(current_state, target):
        raise ValueError(f"Invalid lead state transition: {current_state} -> {target}")

    if sync_status:
        await db.execute(
            """
            UPDATE leads
            SET lifecycle_state = ?, status = ?, state_updated_at = datetime('now')
            WHERE id = ?
            """,
            (target, target, lead_id),
        )
    else:
        await db.execute(
            """
            UPDATE leads
            SET lifecycle_state = ?, state_updated_at = datetime('now')
            WHERE id = ?
            """,
            (target, lead_id),
        )

    await db.execute(
        """
        INSERT INTO lead_state_transitions (lead_id, from_state, to_state, reason, actor)
        VALUES (?, ?, ?, ?, ?)
        """,
        (lead_id, current_state, target, reason, actor),
    )
