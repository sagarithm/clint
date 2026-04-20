# Clint Launch Guide (CLI + Library First)

## Purpose
Launch Clint in production-safe mode with Python package and CLI as the primary
surfaces.

## Launch Modes
- CLI mode: operator-driven campaigns and runbooks.
- Library mode: embedded personalization and orchestration in your applications.

## Production Launch Sequence
1. Install and verify runtime.
2. Configure credentials and sender identity.
3. Run readiness checks.
4. Execute dry-run campaign.
5. Move to controlled live run.
6. Monitor health and reply behavior.

## CLI Launch Path

```bash
pip install sagarithm-clint
playwright install chromium
clint version
clint init
clint config doctor
clint run --query "Dentists in California"
clint run --query "Dentists in California" --live --target 50 --send-limit 20
```

## Library Launch Path

```python
from clint import Engine

engine = Engine(api_key="your_openrouter_key")
result = engine.personalize(
    {
        "name": "Jane Doe",
        "company": "TechCorp",
        "title": "CTO",
        "category": "Technology",
        "score": 8,
    },
    channel="email",
    outreach_step=1,
    service="Website Redesign",
)

print(result["subject"])
print(result["body"])
```

## Safety Requirements Before Live Runs
- `clint config doctor` passes.
- Suppression and cooldown checks are active.
- Small send limits are used for first launch window.
- Delivery and reply events are monitored.

## V2 Specifications
- CLI spec: [docs/v2/11-cli-product-spec.md](docs/v2/11-cli-product-spec.md)
- Library spec: [docs/v2/12-library-api-spec.md](docs/v2/12-library-api-spec.md)
- Launch checklist: [docs/v2/10-launch-checklists.md](docs/v2/10-launch-checklists.md)
