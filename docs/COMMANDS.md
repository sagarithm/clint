# Clint Commands Reference

This guide covers first-time setup and all primary CLI commands.

## First-Time Setup (New User)

Run these in order:

```bash
pip install sagarithm-clint
playwright install chromium
clint version
clint init
clint config doctor
clint run --query "Dentists in California"
```

Notes:

1. The first `run` is dry-run by default.
2. Use `--live` only after reviewing dry-run output.

## Core Commands

## `clint version`

Show installed CLI version.

```bash
clint version
```

## `clint init`

Interactive credential and sender setup.

```bash
clint init
```

Non-interactive mode:

```bash
clint init --non-interactive --openrouter-key <KEY> --smtp-user <EMAIL> --smtp-pass <APP_PASSWORD>
```

## `clint config show`

Show current config (secrets masked by default).

```bash
clint config show
clint config show --json
```

## `clint config set`

Set a single config key.

```bash
clint config set SENDER_NAME "Sagar"
```

## `clint config doctor`

Run environment and connectivity diagnostics.

```bash
clint config doctor
```

Checks include:

1. OpenRouter auth
2. SMTP auth
3. Playwright runtime
4. Writable data and log paths

## `clint run`

Autonomous campaign run.

Dry-run (default):

```bash
clint run --query "Dentists in California"
```

Live run:

```bash
clint run --query "Dentists in California" --target 50 --send-limit 20 --live
```

Useful flags:

- `--dry-run`
- `--live`
- `--target <int>`
- `--send-limit <int>`

## `clint scrape`

Discovery-only scraping and queue fill.

```bash
clint scrape --query "Hotels in London" --target 20
```

## `clint followup`

Process follow-up queue for previously contacted leads.

```bash
clint followup --days-since-last 3
```

With explicit channel:

```bash
clint followup --days-since-last 3 --channel email
```

## `clint export`

Export tables as CSV.

```bash
clint export --table all
clint export --table leads
clint export --table outreach_history
```

## `clint dashboard`

Start local web dashboard.

```bash
clint dashboard --host 127.0.0.1 --port 8000
```

## Exit Codes

- `0`: success
- `2`: usage and validation error
- `3`: config error
- `4`: runtime or dependency readiness error
- `5`: network or auth transport error
- `10`: unexpected internal error

## Troubleshooting Notes

1. If `clint` is not found on Windows, try:

```bash
python -m clint_cli --help
```

2. If live mode fails, run `clint config doctor` first.
