from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import httpx

from core.connectors import ConnectorAdapter, normalize_connector_record, validate_connector_record


class UpworkConnector(ConnectorAdapter):
    def name(self) -> str:
        return "upwork"

    async def fetch(self, context: Dict[str, Any]) -> list[Dict[str, Any]]:
        query = str(context.get("query") or "website redesign").strip()
        limit = int(context.get("limit") or 20)
        normalized_limit = max(1, min(limit, 50))
        user_agent = str(context.get("user_agent") or "clint-v2-worker/1.0")

        # Public RSS feed endpoint for job demand signals.
        url = "https://www.upwork.com/ab/feed/jobs/rss"
        params = {"q": query, "sort": "recency"}

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params, headers={"User-Agent": user_agent})
            resp.raise_for_status()
            body = resp.text

        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return []

        records: list[Dict[str, Any]] = []
        items = root.findall("./channel/item")
        for item in items[:normalized_limit]:
            title = self._xml_text(item, "title")
            link = self._xml_text(item, "link")
            description = self._xml_text(item, "description")
            guid = self._xml_text(item, "guid")
            published = self._xml_text(item, "pubDate")

            discovered_at = self._parse_pubdate_to_utc(published)
            intent_text = self._clean_text(description)

            records.append(
                {
                    "name": (title or "upwork_job")[:120],
                    "company_name": None,
                    "person_name": None,
                    "website": None,
                    "phone": None,
                    "email": None,
                    "business_category": "Web Solutions",
                    "category": query,
                    "intent_text": intent_text,
                    "source_record_id": (guid or link or title)[:255],
                    "source_platform": "upwork",
                    "source_url": link or None,
                    "discovered_at_utc": discovered_at,
                    "raw_source_payload": {
                        "title": title,
                        "link": link,
                        "description": description,
                        "guid": guid,
                        "pubDate": published,
                    },
                }
            )

        return records

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            **raw_record,
            "source_platform": "upwork",
            "source_url": raw_record.get("source_url") or raw_record.get("url"),
        }
        return normalize_connector_record(payload)

    def validate(self, record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        return validate_connector_record(record)

    @staticmethod
    def _xml_text(item: ET.Element, tag: str) -> str:
        node = item.find(tag)
        if node is None or node.text is None:
            return ""
        return str(node.text).strip()

    @staticmethod
    def _clean_text(text: str) -> str:
        if not text:
            return ""
        no_tags = re.sub(r"<[^>]+>", " ", html.unescape(text))
        compact = re.sub(r"\s+", " ", no_tags).strip()
        return compact[:4000]

    @staticmethod
    def _parse_pubdate_to_utc(pub_date: str) -> Optional[str]:
        if not pub_date:
            return None
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
            try:
                dt = datetime.strptime(pub_date, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        return None
