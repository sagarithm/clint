from pathlib import Path
import sys
import asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scrapers.connectors.linkedin_connector import LinkedInConnector


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


def test_linkedin_fetch_parses_results(monkeypatch):
    html = """
    <html><body>
      <ul>
        <li>
          <a href="/jobs/view/123">Frontend Engineer</a>
          <h3>Frontend Engineer</h3>
          <h4>Acme Inc</h4>
        </li>
      </ul>
    </body></html>
    """
    capture = {}

    import scrapers.connectors.linkedin_connector as mod

    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda timeout=20.0: _FakeClient(html, capture))

    connector = LinkedInConnector()
    records = asyncio.run(connector.fetch({"query": "frontend web", "limit": 5}))

    assert len(records) == 1
    assert records[0]["source_platform"] == "linkedin"
    assert records[0]["source_url"] == "https://www.linkedin.com/jobs/view/123"
    assert capture["url"] == "https://www.linkedin.com/jobs/search"
    assert capture["params"]["keywords"] == "frontend web"


def test_linkedin_normalize_validate_roundtrip():
    connector = LinkedInConnector()
    normalized = connector.normalize(
        {
            "name": "Frontend Engineer",
            "source_record_id": "li-1",
            "source_url": "https://www.linkedin.com/jobs/view/123",
        }
    )
    valid, reason = connector.validate(normalized)
    assert valid is True
    assert reason is None
