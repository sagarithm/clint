from pathlib import Path
import sys
import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scrapers.connectors.upwork_connector import UpworkConnector


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


class _FakeClient:
    def __init__(self, text: str, capture: dict):
        self._text = text
        self._capture = capture

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def get(self, url, params=None, headers=None):
        self._capture["url"] = url
        self._capture["params"] = params or {}
        self._capture["headers"] = headers or {}
        return _FakeResponse(self._text)


def test_upwork_fetch_parses_rss(monkeypatch):
    rss = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<rss version=\"2.0\">
  <channel>
    <item>
      <title>Need Website Redesign for Dental Clinic</title>
      <link>https://www.upwork.com/jobs/~0123</link>
      <description><![CDATA[<p>Looking for better lead conversion and a faster website.</p>]]></description>
      <guid>upw-0123</guid>
      <pubDate>Mon, 20 Apr 2026 09:30:00 +0000</pubDate>
    </item>
  </channel>
</rss>
"""
    capture = {}

    import scrapers.connectors.upwork_connector as mod

    monkeypatch.setattr(
        mod.httpx,
        "AsyncClient",
        lambda timeout=20.0: _FakeClient(rss, capture),
    )

    connector = UpworkConnector()
    records = asyncio.run(connector.fetch({"query": "dentist web design", "limit": 5}))

    assert len(records) == 1
    first = records[0]
    assert first["source_platform"] == "upwork"
    assert first["source_record_id"] == "upw-0123"
    assert first["source_url"] == "https://www.upwork.com/jobs/~0123"
    assert "lead conversion" in first["intent_text"].lower()
    assert first["discovered_at_utc"] == "2026-04-20 09:30:00"
    assert capture["url"] == "https://www.upwork.com/ab/feed/jobs/rss"
    assert capture["params"]["q"] == "dentist web design"


def test_upwork_fetch_invalid_xml_returns_empty(monkeypatch):
    import scrapers.connectors.upwork_connector as mod

    monkeypatch.setattr(
        mod.httpx,
        "AsyncClient",
        lambda timeout=20.0: _FakeClient("not xml", {}),
    )

    connector = UpworkConnector()
    records = asyncio.run(connector.fetch({"query": "test", "limit": 5}))

    assert records == []


def test_upwork_normalize_validate_roundtrip():
    connector = UpworkConnector()
    normalized = connector.normalize(
        {
            "name": "Website Help",
            "source_record_id": "abc123",
            "source_url": "https://www.upwork.com/jobs/~abc123",
        }
    )
    valid, reason = connector.validate(normalized)
    assert valid is True
    assert reason is None
    assert normalized["source_platform"] == "upwork"
