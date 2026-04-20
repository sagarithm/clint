from __future__ import annotations

from typing import Any, Dict, Tuple

import aiosqlite


def _contact_key_from_lead(lead: Dict[str, Any], channel: str) -> str | None:
    if channel == "email":
        email = str(lead.get("email") or "").split(",")[0].strip().lower()
        return email or None
    phone = "".join(ch for ch in str(lead.get("phone") or "") if ch.isdigit())
    return phone or None


async def is_suppressed(
    db: aiosqlite.Connection,
    *,
    lead: Dict[str, Any],
    channel: str,
) -> Tuple[bool, str | None, str | None]:
    contact_key = _contact_key_from_lead(lead, channel)
    if not contact_key:
        return False, None, None

    async with db.execute(
        """
        SELECT suppression_type, reason
        FROM suppression_entries
        WHERE contact_key = ?
        ORDER BY created_at_utc DESC
        LIMIT 1
        """,
        (contact_key,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        return False, None, contact_key
    return True, str(row[0]), contact_key


async def write_compliance_check(
    db: aiosqlite.Connection,
    *,
    lead_id: int,
    check_name: str,
    decision: str,
    reason: str,
) -> None:
    await db.execute(
        """
        INSERT INTO compliance_checks (lead_id, check_name, decision, reason)
        VALUES (?, ?, ?, ?)
        """,
        (lead_id, check_name, decision, reason),
    )


async def enforce_pre_send_policy(
    db: aiosqlite.Connection,
    *,
    lead: Dict[str, Any],
    channel: str,
) -> Tuple[bool, str]:
    lead_id = int(lead["id"])
    suppressed, suppression_type, contact_key = await is_suppressed(
        db,
        lead=lead,
        channel=channel,
    )

    if suppressed:
        reason = f"suppressed:{suppression_type or 'unknown'}"
        await write_compliance_check(
            db,
            lead_id=lead_id,
            check_name="suppression_check",
            decision="blocked",
            reason=reason,
        )
        return False, reason

    if channel == "email":
        email = str(lead.get("email") or "").strip().lower()
        if not email or email == "n/a":
            reason = "missing_email_contact"
            await write_compliance_check(
                db,
                lead_id=lead_id,
                check_name="contact_presence_check",
                decision="blocked",
                reason=reason,
            )
            return False, reason

    if channel == "whatsapp":
        phone = str(lead.get("phone") or "").strip()
        if not phone:
            reason = "missing_phone_contact"
            await write_compliance_check(
                db,
                lead_id=lead_id,
                check_name="contact_presence_check",
                decision="blocked",
                reason=reason,
            )
            return False, reason

    await write_compliance_check(
        db,
        lead_id=lead_id,
        check_name="pre_send_policy",
        decision="passed",
        reason=f"contact_key:{contact_key or 'na'}",
    )
    return True, "passed"
