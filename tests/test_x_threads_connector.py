from pathlib import Path
import sys
import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scrapers.connectors.x_threads_connector import XThreadsConnector


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


def test_x_threads_fetch_parses_results(monkeypatch):
    html = """
    <html><body>
      <div class="timeline-item">
        <a class="username">@builder</a>
        <a class="tweet-link" href="/builder/status/1">link</a>
        <div class="tweet-content">Need help redesigning our SaaS landing page</div>
      </div>
    </body></html>
    """
    capture = {}

    import scrapers.connectors.x_threads_connector as mod

    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda timeout=20.0: _FakeClient(html, capture))

    connector = XThreadsConnector()
    records = asyncio.run(connector.fetch({"query": "saas website", "limit": 5}))

    assert len(records) == 1
    assert records[0]["source_platform"] == "x_threads"
    assert records[0]["source_url"] == "https://nitter.net/builder/status/1"
    assert "landing page" in records[0]["intent_text"].lower()
    assert capture["url"] == "https://nitter.net/search"
    assert capture["params"]["q"] == "saas website"


def test_x_threads_normalize_validate_roundtrip():
    connector = XThreadsConnector()
    normalized = connector.normalize(
        {
            "name": "Need redesign",
            "source_record_id": "x-1",
            "source_url": "https://nitter.net/builder/status/1",
        }
    )
    valid, reason = connector.validate(normalized)
    assert valid is True
    assert reason is None
