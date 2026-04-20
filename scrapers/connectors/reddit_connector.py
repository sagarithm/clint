from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import httpx

from core.connectors import ConnectorAdapter, normalize_connector_record, validate_connector_record


class RedditConnector(ConnectorAdapter):
    def name(self) -> str:
        return "reddit"

    async def fetch(self, context: Dict[str, Any]) -> list[Dict[str, Any]]:
        query = str(context.get("query") or "web design help").strip()
        limit = int(context.get("limit") or 20)
        user_agent = str(context.get("user_agent") or "clint-v2-worker/1.0")

        params = {
            "q": query,
            "sort": "new",
            "limit": max(1, min(limit, 100)),
        }
        url = "https://www.reddit.com/search.json"

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params, headers={"User-Agent": user_agent})
            resp.raise_for_status()
            payload = resp.json()

        records: list[Dict[str, Any]] = []
        children = (((payload.get("data") or {}).get("children") or []))

        for item in children:
            data = item.get("data") or {}
            title = str(data.get("title") or "").strip()
            selftext = str(data.get("selftext") or "").strip()
            permalink = str(data.get("permalink") or "").strip()
            source_url = f"https://www.reddit.com{permalink}" if permalink else None

            website = None
            m = re.search(r"https?://[^\s)]+", selftext)
            if m:
                website = m.group(0)

            created_utc = data.get("created_utc")
            discovered_at = None
            if created_utc:
                try:
                    discovered_at = datetime.fromtimestamp(float(created_utc), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    discovered_at = None

            records.append(
                {
                    "name": title[:120] if title else f"reddit_post_{data.get('id', '')}",
                    "company_name": None,
                    "person_name": data.get("author"),
                    "website": website,
                    "phone": None,
                    "email": None,
                    "business_category": "Web Solutions",
                    "category": query,
                    "intent_text": f"{title}\n{selftext}".strip(),
                    "source_record_id": str(data.get("id") or ""),
                    "source_platform": "reddit",
                    "source_url": source_url,
                    "discovered_at_utc": discovered_at,
                    "raw_source_payload": data,
                }
            )

        return records

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            **raw_record,
            "source_platform": "reddit",
            "source_url": raw_record.get("source_url") or raw_record.get("url"),
        }
        return normalize_connector_record(payload)

    def validate(self, record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        return validate_connector_record(record)
