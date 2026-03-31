import asyncio
import random
from typing import Any, Awaitable, Callable

from core.database import get_db


async def recently_contacted(lead_id: int, channel: str, cooldown_hours: int = 72) -> bool:
    async with get_db() as db:
        async with db.execute(
            """
            SELECT 1
            FROM outreach_history
            WHERE lead_id = ?
              AND channel = ?
              AND status = 'sent'
              AND sent_at >= datetime('now', ?)
            LIMIT 1
            """,
            (lead_id, channel, f"-{cooldown_hours} hours"),
        ) as cursor:
            return await cursor.fetchone() is not None


async def log_outreach_event(
    lead_id: int,
    channel: str,
    status: str,
    content: str = "",
    error_message: str | None = None,
) -> None:
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO outreach_history (lead_id, channel, content, status, error_message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (lead_id, channel, content[:500], status, error_message),
        )
        await db.commit()


async def send_with_retry(
    send_fn: Callable[[], Awaitable[Any]],
    retries: int = 3,
    base_delay: float = 1.5,
    max_delay: float = 8.0,
) -> Any:
    attempt = 0
    while True:
        attempt += 1
        result = await send_fn()
        if result is True or result == "not_found":
            return result

        if attempt >= retries:
            return result

        delay = min(max_delay, base_delay * (2 ** (attempt - 1))) + random.uniform(0.0, 0.5)
        await asyncio.sleep(delay)
