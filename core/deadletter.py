from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import aiosqlite


def _parse_json(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


async def list_deadletter_events(
    db: aiosqlite.Connection,
    *,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    query = "SELECT * FROM deadletter_events"
    params: list[Any] = []
    if status:
        query += " WHERE replay_status = ?"
        params.append(status)
    query += " ORDER BY created_at_utc DESC LIMIT ?"
    params.append(max(1, min(limit, 500)))

    async with db.execute(query, params) as cursor:
        rows = await cursor.fetchall()

    return [dict(r) for r in rows]


async def replay_deadletter_event(
    db: aiosqlite.Connection,
    *,
    event_id: int,
    replay_handler: Any,
) -> Dict[str, Any]:
    async with db.execute("SELECT * FROM deadletter_events WHERE id = ?", (event_id,)) as cursor:
        row = await cursor.fetchone()
    if row is None:
        raise ValueError(f"Deadletter event not found: {event_id}")

    event = dict(row)
    payload = _parse_json(event.get("payload_json"))
    lead_id = payload.get("lead_id") or event.get("lead_id")
    source = str(payload.get("source") or event.get("channel") or "")
    stage = str(payload.get("stage") or "").strip().lower()

    await db.execute(
        "UPDATE deadletter_events SET replay_attempts = COALESCE(replay_attempts, 0) + 1 WHERE id = ?",
        (event_id,),
    )

    raw_record = payload if payload else None
    if not raw_record or not isinstance(raw_record, dict):
        await db.execute(
            """
            UPDATE deadletter_events
            SET replay_status = 'unsupported',
                replay_note = ?,
                replayed_at_utc = datetime('now')
            WHERE id = ?
            """,
            ("No replayable payload found", event_id),
        )
        return {
            "event_id": event_id,
            "status": "unsupported",
            "reason": "missing_payload",
        }

    try:
        replay_result: Dict[str, Any]
        if stage == "enrich" and lead_id is not None:
            replay_result = await replay_handler.replay_enrich_stage(
                lead_id=int(lead_id),
                source=source,
            )
        elif stage == "draft" and lead_id is not None:
            replay_result = await replay_handler.replay_draft_stage(
                lead_id=int(lead_id),
                source=source,
            )
        elif stage == "dispatch" and lead_id is not None:
            # Safe default: dispatch replay is dry-run unless future operator controls opt in.
            replay_result = await replay_handler.replay_dispatch_stage(
                lead_id=int(lead_id),
                source=source,
                live_send=False,
            )
        else:
            source_platform = str(raw_record.get("source_platform") or "").lower()
            source_url = str(raw_record.get("source_url") or raw_record.get("url") or "").lower()
            if source_platform == "upwork" or "upwork.com" in source_url:
                replay_result = await replay_handler.replay_upwork_raw_record(raw_record)
            elif source_platform == "fiverr" or "fiverr.com" in source_url:
                replay_result = await replay_handler.replay_fiverr_raw_record(raw_record)
            elif source_platform == "linkedin" or "linkedin.com" in source_url:
                replay_result = await replay_handler.replay_linkedin_raw_record(raw_record)
            elif source_platform in {"x_threads", "xthreads"} or "nitter.net" in source_url or "x.com" in source_url:
                replay_result = await replay_handler.replay_x_threads_raw_record(raw_record)
            else:
                replay_result = await replay_handler.replay_reddit_raw_record(raw_record)

        await db.execute(
            """
            UPDATE deadletter_events
            SET replay_status = 'replayed',
                replay_note = ?,
                replayed_at_utc = datetime('now')
            WHERE id = ?
            """,
            ("Replay successful", event_id),
        )
        return {
            "event_id": event_id,
            "status": "replayed",
            "replay_result": replay_result,
        }
    except Exception as exc:
        await db.execute(
            """
            UPDATE deadletter_events
            SET replay_status = 'failed',
                replay_note = ?,
                replayed_at_utc = datetime('now')
            WHERE id = ?
            """,
            (str(exc), event_id),
        )
        return {
            "event_id": event_id,
            "status": "failed",
            "reason": str(exc),
        }
