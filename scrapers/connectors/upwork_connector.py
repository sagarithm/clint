from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from core.connectors import ConnectorAdapter, normalize_connector_record, validate_connector_record


class UpworkConnector(ConnectorAdapter):
    def name(self) -> str:
        return "upwork"

    async def fetch(self, context: Dict[str, Any]) -> list[Dict[str, Any]]:
        # Placeholder for upwork demand ingestion.
        return []

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            **raw_record,
            "source_platform": "upwork",
            "source_url": raw_record.get("source_url") or raw_record.get("url"),
        }
        return normalize_connector_record(payload)

    def validate(self, record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        return validate_connector_record(record)
