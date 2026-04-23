from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from core.connectors import ConnectorAdapter, normalize_connector_record, validate_connector_record


class LinkedInConnector(ConnectorAdapter):
    def name(self) -> str:
        return "linkedin"

    async def fetch(self, context: Dict[str, Any]) -> list[Dict[str, Any]]:
        query = str(context.get("query") or "website redesign").strip()
        limit = int(context.get("limit") or 20)
        normalized_limit = max(1, min(limit, 50))
        user_agent = str(context.get("user_agent") or "clint-v2-worker/1.0")

        url = "https://www.linkedin.com/jobs/search"
        params = {"keywords": query}
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params, headers={"User-Agent": user_agent})
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("li")

        records: list[Dict[str, Any]] = []
        for card in cards:
            title_node = card.select_one("h3") or card.select_one("a[title]")
            title = title_node.get_text(" ", strip=True) if title_node else ""

            link_node = card.select_one("a[href]")
            href = str(link_node.get("href") or "").strip() if link_node else ""
            source_url = self._absolute_url(href)

            company_node = card.select_one("h4") or card.select_one(".base-search-card__subtitle")
            company_name = company_node.get_text(" ", strip=True) if company_node else None

            if not title and not source_url:
                continue

            seed = source_url or title
            records.append(
                {
                    "name": (title or "linkedin_post")[:120],
                    "company_name": company_name,
                    "person_name": None,
                    "website": None,
                    "phone": None,
                    "email": None,
                    "business_category": "Web Solutions",
                    "category": query,
                    "intent_text": self._compact_text(title),
                    "source_record_id": seed[:255],
                    "source_platform": "linkedin",
                    "source_url": source_url,
                    "discovered_at_utc": None,
                    "raw_source_payload": {
                        "title": title,
                        "company_name": company_name,
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
            "source_platform": "linkedin",
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
            return f"https://www.linkedin.com{href}"
        return f"https://www.linkedin.com/{href}"

    @staticmethod
    def _compact_text(text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip()[:4000]
