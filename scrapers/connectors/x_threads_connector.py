from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from core.connectors import ConnectorAdapter, normalize_connector_record, validate_connector_record


class XThreadsConnector(ConnectorAdapter):
    def name(self) -> str:
        return "x_threads"

    async def fetch(self, context: Dict[str, Any]) -> list[Dict[str, Any]]:
        query = str(context.get("query") or "website redesign").strip()
        limit = int(context.get("limit") or 20)
        normalized_limit = max(1, min(limit, 50))
        user_agent = str(context.get("user_agent") or "clint-v2-worker/1.0")

        # Use Nitter public search page to gather intent signals without auth.
        url = "https://nitter.net/search"
        params = {"f": "tweets", "q": query}
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params, headers={"User-Agent": user_agent})
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div.timeline-item")

        records: list[Dict[str, Any]] = []
        for card in cards:
            text_node = card.select_one("div.tweet-content")
            content = text_node.get_text(" ", strip=True) if text_node else ""

            author_node = card.select_one("a.username")
            person_name = author_node.get_text(" ", strip=True) if author_node else None

            link_node = card.select_one("a.tweet-link")
            href = str(link_node.get("href") or "").strip() if link_node else ""
            source_url = self._absolute_url(href)

            if not content and not source_url:
                continue

            title = content[:120] if content else (person_name or "x_thread")
            seed = source_url or title
            records.append(
                {
                    "name": title,
                    "company_name": None,
                    "person_name": person_name,
                    "website": None,
                    "phone": None,
                    "email": None,
                    "business_category": "Web Solutions",
                    "category": query,
                    "intent_text": self._compact_text(content),
                    "source_record_id": seed[:255],
                    "source_platform": "x_threads",
                    "source_url": source_url,
                    "discovered_at_utc": None,
                    "raw_source_payload": {
                        "content": content,
                        "person_name": person_name,
                        "href": href,
                    },
                }
            )

            if len(records) >= normalized_limit:
                break

        return records

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            **raw_record,
            "source_platform": "x_threads",
            "source_url": raw_record.get("source_url") or raw_record.get("url"),
        }
        return normalize_connector_record(payload)

    def validate(self, record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        return validate_connector_record(record)

    @staticmethod
    def _absolute_url(href: str) -> Optional[str]:
        if not href:
            return None
        if href.startswith("http://") or href.startswith("https://"):
            return href
        if href.startswith("/"):
            return f"https://nitter.net{href}"
        return f"https://nitter.net/{href}"

    @staticmethod
    def _compact_text(text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip()[:4000]
