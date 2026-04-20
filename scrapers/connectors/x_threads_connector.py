from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from core.connectors import ConnectorAdapter, normalize_connector_record, validate_connector_record


class XThreadsConnector(ConnectorAdapter):
    def name(self) -> str:
        return "x_threads"

    async def fetch(self, context: Dict[str, Any]) -> list[Dict[str, Any]]:
        # Placeholder for X/Threads intent ingestion.
        return []

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            **raw_record,
            "source_platform": "x_threads",
            "source_url": raw_record.get("source_url") or raw_record.get("url"),
        }
        return normalize_connector_record(payload)

    def validate(self, record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        return validate_connector_record(record)
