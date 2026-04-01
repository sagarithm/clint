# Clint: AI-Driven Enterprise Outreach

Clint is a production-ready automation suite for lead generation, audit-based personalization, and multi-step outreach.

Documentation index: [docs/README.md](docs/README.md)

## Quick Start

### CLI users

```bash
pip install sagarithm-clint
playwright install chromium
clint version
clint init
clint config doctor
clint run --query "Dentists in California"
```

### Python library users

```python
from clint import Engine

engine = Engine(api_key="your_openrouter_key")
result = engine.personalize({
    "name": "Jane Doe",
    "company": "TechCorp",
    "title": "CTO"
})

print(result["body"])
```

## Core Capabilities

- End-to-end autonomous campaigns (discover, enrich, personalize, outreach)
- AI-based audit and proposal generation
- Multi-step follow-up workflow
- Email and WhatsApp channels
- Local dashboard and export tools
- Production-safe dry-run mode

## Docs Map

- [COMMANDS.md](COMMANDS.md): beginner and advanced CLI commands
- [LAUNCH.md](LAUNCH.md): how to launch and use the library
- [LIBRARY.md](LIBRARY.md): full programmatic API reference
- [examples/README.md](examples/README.md): working integration examples
- [docs/README.md](docs/README.md): full documentation index
- [docs/RELEASE.md](docs/RELEASE.md): release and publish process

## Common Operations

```bash
clint run --query "Dentists in California"
clint run --query "Dentists in California" --live --target 50 --send-limit 20
clint scrape --query "Hotels in London" --target 20
clint followup --days-since-last 3 --channel email
clint export --table all
clint dashboard --host 127.0.0.1 --port 8000
```

## Safety Defaults

- Dry-run is default for campaign runs
- Recommended daily volume: ~200 emails and ~200 WhatsApp messages
- Randomized send delays help reduce detection risk
- Activity logs are written to `logs/outreach.log`

## Development

```bash
pip install -r requirements.txt
pytest -q
```

Current release line: v1.0.2
