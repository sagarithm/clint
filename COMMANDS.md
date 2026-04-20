# Clint CLI Commands

This guide is the command reference for first-time users and production operators.

For V2 command contracts, policy behavior, and exit-code guarantees, see
[docs/v2/11-cli-product-spec.md](docs/v2/11-cli-product-spec.md).

## First-Time Setup

Install and verify:

```bash
pip install sagarithm-clint
playwright install chromium
clint version
```

Configure and validate:

```bash
clint init
clint config doctor
```

Safe first run (dry-run default):

```bash
clint run --query "Dentists in California"
```

Go live only after reviewing output:

```bash
clint run --query "Dentists in California" --live --target 50 --send-limit 20
```

## Core Commands

### clint

Interactive command center.

```bash
clint
```

### clint version

Show installed CLI version.

```bash
clint version
```

### clint init

Interactive credential and sender setup.

```bash
clint init
```

Non-interactive:

```bash
clint init --non-interactive --openrouter-key <KEY> --smtp-user <EMAIL> --smtp-pass <APP_PASSWORD> --sender-name "Your Name" --sender-title "Founder"
```

### clint config show

View current configuration.

```bash
clint config show
clint config show --json
```

### clint config set

Set a single key.

```bash
clint config set SENDER_NAME "Your Name"
clint config set SENDER_TITLE "Founder"
```

### clint config doctor

Run readiness checks for API, SMTP, Playwright, and file paths.

```bash
clint config doctor
```

### clint run

Autonomous campaign run.

```bash
clint run --query "Dentists in California"
clint run --query "Dentists in California" --live
```

Operational guidance:
- Use dry-run before every live launch.
- Validate readiness with `clint config doctor` before `--live`.
- Keep small send limits for first production ramp.

### clint scrape

Discovery-only scraping.

```bash
clint scrape --query "Hotels in London" --target 20
```

### clint followup

Process follow-up queue.

```bash
clint followup --days-since-last 3
clint followup --days-since-last 3 --channel email
clint followup --days-since-last 3 --channel whatsapp
```

### clint export

Export data to CSV.

```bash
clint export --table all
clint export --table leads
clint export --table outreach_history
```

### clint dashboard

Start dashboard server.

```bash
clint dashboard --host 127.0.0.1 --port 8000
```

## Reliability and Control Commands

### clint worker-reddit

Run the V2 queue-style Reddit worker pipeline (discover -> enrich -> score -> draft -> send).

```bash
clint worker-reddit --query "dentist website redesign" --limit 20
clint worker-reddit --query "roofing lead generation" --limit 10 --live
```

Notes:
- Defaults to dry-run. Use `--live` only after `clint config doctor` passes.
- Useful for controlled source-specific runs and debugging worker behavior.

### clint experiments-decide

Apply experiment auto-decision policy to a completed experiment.

```bash
clint experiments-decide --experiment-id 3
clint experiments-decide --experiment-id 3 --min-sample 50 --min-uplift-pct 8
```

Notes:
- Returns one of: `promote`, `hold`, `rollback`, or `no_winner`.
- Quality-guard threshold is controlled by `--max-negative-quality-impact`.

### clint deadletter-list

List deadletter events for operational triage and replay planning.

```bash
clint deadletter-list
clint deadletter-list --status pending --limit 100
```

### clint deadletter-replay

Replay a deadletter event through supported recovery handlers.

```bash
clint deadletter-replay --event-id 42
```

Notes:
- Replay updates event replay metadata (`replay_status`, attempts, replay timestamp).
- Unsupported payload types are marked as unsupported rather than silently dropped.

## API Reliability Endpoints

These are available when running `clint dashboard`:

- `POST /api/workers/reddit/run`
- `GET /api/workers/reddit/status`
- `GET /api/deadletter?status=<status>&limit=<n>`
- `POST /api/deadletter/replay`

Example replay request:

```json
{
	"event_id": 42
}
```

## Release Workflow

Pre-release checks:

```bash
pytest -q
clint config doctor
```

Release steps:

1. Update version in `pyproject.toml`.
2. Update release notes in `docs/RELEASE.md`.
3. Commit: `git add .` and `git commit -m "release: vX.Y.Z"`.
4. Tag: `git tag vX.Y.Z`.
5. Push: `git push origin main --tags`.

If publishing manually:

```bash
python -m build
python -m twine upload dist/*
```

## Exit Codes

- 0: success
- 2: usage or validation error
- 3: configuration error
- 4: runtime or dependency readiness error
- 5: network or auth transport error
- 10: unexpected internal error

These codes are contractual and should be used by CI/CD and automation jobs.

## Troubleshooting

If `clint` is not found on Windows:

```bash
python -m clint_cli --help
```

If live mode fails:

```bash
clint config doctor
```
