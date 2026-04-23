from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from core.connectors import ConnectorAdapter, normalize_connector_record, validate_connector_record


class FiverrConnector(ConnectorAdapter):
    def name(self) -> str:
        return "fiverr"

    async def fetch(self, context: Dict[str, Any]) -> list[Dict[str, Any]]:
        query = str(context.get("query") or "website design").strip()
        limit = int(context.get("limit") or 20)
        normalized_limit = max(1, min(limit, 50))
        user_agent = str(context.get("user_agent") or "clint-v2-worker/1.0")

        url = "https://www.fiverr.com/search/gigs"
        params = {"query": query}
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params, headers={"User-Agent": user_agent})
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")

        cards = soup.select("div[data-testid='gig-card']")
        if not cards:
            cards = soup.select("article")

        records: list[Dict[str, Any]] = []
        for card in cards:
            title_node = (
                card.select_one("h3")
                or card.select_one("a[title]")
                or card.select_one("a")
            )
            title = title_node.get_text(" ", strip=True) if title_node else ""

            link_node = card.select_one("a[href]")
            href = link_node.get("href") if link_node else ""
            source_url = self._absolute_url(str(href or "").strip())

            desc_node = card.select_one("p")
            description = desc_node.get_text(" ", strip=True) if desc_node else ""

            seller_node = card.select_one("[data-testid='seller-name'], .seller-name")
            person_name = seller_node.get_text(" ", strip=True) if seller_node else None

            if not title and not source_url:
                continue

            seed = source_url or title
            records.append(
                {
                    "name": (title or "fiverr_gig")[:120],
                    "company_name": None,
                    "person_name": person_name,
                    "website": None,
                    "phone": None,
                    "email": None,
                    "business_category": "Web Solutions",
                    "category": query,
                    "intent_text": self._compact_text(description or title),
                    "source_record_id": seed[:255],
                    "source_platform": "fiverr",
                    "source_url": source_url,
                    "discovered_at_utc": None,
                    "raw_source_payload": {
                        "title": title,
                        "description": description,
                        "href": href,
                        "person_name": person_name,
                    },
                }
            )

            if len(records) >= normalized_limit:
                break

        return records

    def normalize(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            **raw_record,
            "source_platform": "fiverr",
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
            return f"https://www.fiverr.com{href}"
        return f"https://www.fiverr.com/{href}"

    @staticmethod
    def _compact_text(text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip()[:4000]
