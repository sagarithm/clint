# Clint CLI Commands (Beginner + Full Reference)

This is a top-level quick reference for new users and teams preparing for production runs.

## 1) First-Time Newbie Setup

Use this exact flow:

```bash
pip install -r requirements.txt
playwright install chromium
clint version
clint init
clint config doctor
clint run --query "Dentists in California"
```

What this does:

1. Installs dependencies.
2. Installs browser runtime for scraping.
3. Confirms CLI install.
4. Saves credentials and sender profile.
5. Validates environment and access.
6. Executes safe dry-run campaign.

Go live only after checking dry-run output:

```bash
clint run --query "Dentists in California" --live --target 50 --send-limit 20
```

## 2) Command Center

### `clint`

Open interactive menu mode.

```bash
clint
```

### `clint version`

Print CLI version.

```bash
clint version
```

### `clint init`

Guided setup.

```bash
clint init
```

Non-interactive setup:

```bash
clint init --non-interactive --openrouter-key <KEY> --smtp-user <EMAIL> --smtp-pass <APP_PASSWORD> --sender-name "Sagar" --sender-title "Founder"
```

### `clint config show`

View configuration.

```bash
clint config show
clint config show --json
```

### `clint config set`

Set one key.

```bash
clint config set SENDER_NAME "Sagar"
clint config set SENDER_TITLE "Founder"
```

### `clint config doctor`

Readiness and connectivity checks.

```bash
clint config doctor
```

### `clint run`

End-to-end autonomous campaign.

```bash
clint run --query "Dentists in California"
clint run --query "Dentists in California" --live
```

### `clint scrape`

Only scrape and queue leads.

```bash
clint scrape --query "Hotels in London" --target 20
```

### `clint followup`

Process follow-up queue.

```bash
clint followup --days-since-last 3
clint followup --days-since-last 3 --channel email
clint followup --days-since-last 3 --channel whatsapp
```

### `clint export`

Export records.

```bash
clint export --table all
clint export --table leads
clint export --table outreach_history
```

### `clint dashboard`

Run local dashboard API/server.

```bash
clint dashboard --host 127.0.0.1 --port 8000
```

## 3) Release Workflow (What To Do)

Run this before release:

```bash
pytest -q
clint config doctor
```

Then release in this order:

1. Update version in `pyproject.toml`.
2. Update release notes in `docs/RELEASE.md`.
3. Re-run tests: `pytest -q`.
4. Commit: `git add . && git commit -m "release: vX.Y.Z"`.
5. Tag: `git tag vX.Y.Z`.
6. Push: `git push && git push --tags`.
7. If publishing package: `python -m build` then `twine upload dist/*`.

## 4) Common Issues

### `clint` command not found (Windows)

Use:

```bash
python -m clint_cli --help
```

### Live run fails

Run:

```bash
clint config doctor
```

### Exit code meaning

- `0`: success
- `2`: argument or validation error
- `3`: config error
- `4`: runtime or dependency issue
- `5`: auth or network transport issue
- `10`: unexpected internal error
