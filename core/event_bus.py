from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List

import aiosqlite

from core.v2_store import log_outreach_event_v2


TOPIC_CONNECTOR_RAW = "events.connector.raw"
TOPIC_CONNECTOR_NORMALIZED = "events.connector.normalized"
TOPIC_ENRICHMENT_COMPLETED = "events.enrichment.completed"
TOPIC_SCORING_COMPLETED = "events.scoring.completed"
TOPIC_MESSAGE_GENERATED = "events.message.generated"
TOPIC_DISPATCH_REQUESTED = "events.dispatch.requested"
TOPIC_DISPATCH_COMPLETED = "events.dispatch.completed"
TOPIC_REPLY_RECEIVED = "events.reply.received"
TOPIC_REPLY_CLASSIFIED = "events.reply.classified"
TOPIC_DEADLETTER = "events.deadletter"


@dataclass
class EventMessage:
    topic: str
    lead_id: int
    channel: str
    payload: Dict[str, Any]


class InMemoryEventBus:
    """Lightweight event bus for internal pipeline fanout and local worker orchestration."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[EventMessage], Awaitable[None]]]] = {}

    def subscribe(self, topic: str, handler: Callable[[EventMessage], Awaitable[None]]) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    async def publish(self, message: EventMessage) -> None:
        for handler in self._subscribers.get(message.topic, []):
            await handler(message)


async def publish_event(
    db: aiosqlite.Connection,
    *,
    topic: str,
    lead_id: int,
    channel: str = "system",
    payload: Dict[str, Any] | None = None,
) -> None:
    await log_outreach_event_v2(
        db,
        lead_id=lead_id,
        channel=channel,
        event_type=topic,
        payload=payload or {},
    )


async def publish_deadletter(
    db: aiosqlite.Connection,
    *,
    topic: str,
    error_message: str,
    payload: Dict[str, Any] | None = None,
    lead_id: int | None = None,
    channel: str = "system",
) -> None:
    await db.execute(
        """
        INSERT INTO deadletter_events (
            lead_id,
            channel,
            topic,
            error_message,
            payload_json
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            channel,
            topic,
            error_message,
            json.dumps(payload or {}, default=str),
        ),
    )
