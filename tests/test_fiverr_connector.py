from pathlib import Path
import sys
import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scrapers.connectors.fiverr_connector import FiverrConnector


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


def test_fiverr_fetch_parses_cards(monkeypatch):
    html = """
    <html><body>
      <div data-testid='gig-card'>
        <a href='/gig/foo' title='Build a website'>Build a website</a>
        <h3>Build a website</h3>
        <p>I can redesign your landing page for conversions.</p>
      </div>
    </body></html>
    """
    capture = {}

    import scrapers.connectors.fiverr_connector as mod

    monkeypatch.setattr(
        mod.httpx,
        "AsyncClient",
        lambda timeout=20.0: _FakeClient(html, capture),
    )

    connector = FiverrConnector()
    records = asyncio.run(connector.fetch({"query": "landing page", "limit": 5}))

    assert len(records) == 1
    first = records[0]
    assert first["source_platform"] == "fiverr"
    assert first["source_url"] == "https://www.fiverr.com/gig/foo"
    assert "landing page" in first["intent_text"].lower()
    assert capture["url"] == "https://www.fiverr.com/search/gigs"
    assert capture["params"]["query"] == "landing page"


def test_fiverr_normalize_validate_roundtrip():
    connector = FiverrConnector()
    normalized = connector.normalize(
        {
            "name": "Website Help",
            "source_record_id": "fg-1",
            "source_url": "https://www.fiverr.com/gig/foo",
        }
    )
    valid, reason = connector.validate(normalized)
    assert valid is True
    assert reason is None
    assert normalized["source_platform"] == "fiverr"
