# Clint: AI Era Outreach Operating System

Clint is a Python library and CLI for production-grade lead discovery,
evidence-based personalization, and safe outreach automation.

Primary product scope for V2:
- Python package and CLI runtime first.
- Web-solution offer focus (web design, UX, CRO, automation).
- Safety-first execution with explainable decisions.

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

- Evidence-led discovery and enrichment
- Explainable scoring and decision routing
- AI message generation with quality gates
- Email and WhatsApp execution with safety controls
- CLI operations with deterministic exit codes
- Python API for integration and orchestration

## Docs Map

- [COMMANDS.md](COMMANDS.md): beginner and advanced CLI commands
- [LAUNCH.md](LAUNCH.md): library quickstart and integration launch paths
- [LIBRARY.md](LIBRARY.md): Python API usage reference
- [docs/v2/README.md](docs/v2/README.md): V2 architecture and production specs
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
- Suppression and cooldown checks gate outbound actions
- Bounded retries and randomized delays reduce delivery risk
- Activity logs are written to `logs/outreach.log`

## Development

```bash
pip install -r requirements.txt
pytest -q
```

Current release line: v1.0.3 (transitioning to V2 architecture)
