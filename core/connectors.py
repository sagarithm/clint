from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import aiosqlite


class ConnectorAdapter(ABC):
    """Contract for source adapters in the ingestion layer."""

    @abstractmethod
    def name(self) -> str:
        """Returns a stable connector identifier."""

    @abstractmethod
    async def fetch(self, context: Dict[str, Any]) -> list[Dict[str, Any]]:
        """Fetches raw source records."""

    @abstractmethod
    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Maps raw records to canonical connector shape."""

    @abstractmethod
    def validate(self, record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates a normalized record and returns reason code when invalid."""


def build_source_record_id(seed_parts: list[str]) -> str:
    seed = "|".join(str(part or "") for part in seed_parts)
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def normalize_connector_record(data: Dict[str, Any]) -> Dict[str, Any]:
    source_platform = (data.get("source_platform") or "unknown_source").strip().lower()
    source_url = (data.get("source_url") or "").strip() or None
    discovered_at_utc = data.get("discovered_at_utc")
    if not discovered_at_utc:
        discovered_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    source_record_id = (data.get("source_record_id") or "").strip()
    if not source_record_id:
        source_record_id = build_source_record_id(
            [
                source_platform,
                data.get("name", ""),
                data.get("phone", ""),
                data.get("website", ""),
                source_url or "",
            ]
        )

    return {
        "source_platform": source_platform,
        "source_record_id": source_record_id,
        "source_url": source_url,
        "discovered_at_utc": discovered_at_utc,
        "raw_payload_json": json.dumps(data, default=str),
    }


def validate_connector_record(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    if not record.get("source_platform"):
        return False, "missing_source_platform"
    if not record.get("source_record_id"):
        return False, "missing_source_record_id"
    return True, None


async def persist_lead_source(
    db: aiosqlite.Connection,
    *,
    lead_id: int,
    record: Dict[str, Any],
    adapter_version: str,
) -> None:
    await db.execute(
        """
        INSERT INTO lead_sources (
            lead_id,
            source_platform,
            source_record_id,
            source_url,
            discovered_at_utc,
            raw_payload_json,
            adapter_version
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            record.get("source_platform"),
            record.get("source_record_id"),
            record.get("source_url"),
            record.get("discovered_at_utc"),
            record.get("raw_payload_json"),
            adapter_version,
        ),
    )


async def log_connector_rejection(
    db: aiosqlite.Connection,
    *,
    source_platform: str,
    reason_code: str,
    reason_detail: str = "",
    raw_payload: Optional[Dict[str, Any]] = None,
) -> None:
    await db.execute(
        """
        INSERT INTO connector_rejections (
            source_platform,
            reason_code,
            reason_detail,
            raw_payload_json
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            source_platform,
            reason_code,
            reason_detail,
            json.dumps(raw_payload, default=str) if raw_payload is not None else None,
        ),
    )
