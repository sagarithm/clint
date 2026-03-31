# Clint CLI Release Plan

Date: 2026-03-31
Status: Pre-implementation planning document

## Objective

Launch Clint as a polished open-source CLI, comparable to modern AI CLIs, with:

- Simple install and command flow
- Clear first-run onboarding
- User-owned credentials (OpenRouter API key and Gmail app password)
- Cross-platform reliability (Windows, macOS, Linux)

---

## Product Definition

### What launch-ready means

1. One install command (`pipx install sagarithm-clint`)
2. One stable executable command (`clint`)
3. Clear setup flow (`clint init`)
4. Safe diagnostics (`clint config doctor`)
5. Discoverable command UX (`clint --help`)
6. Versioned public releases on PyPI and GitHub

### Open-source credential model

Clint does not provide hosted secrets. Each user must supply and manage:

- `OPENROUTER_API_KEY`
- `SMTP_USER_1` (Gmail address)
- `SMTP_PASS_1` (Gmail app password)
- Optional sender identity (`SENDER_NAME`, `SENDER_TITLE`)

---

## Release Roadmap

## Phase 1: CLI Contract and UX

### Current codebase findings (2026-03-31)

1. Runtime entrypoint exists as `main.py`, not a packaged `clint` command yet.
2. Existing CLI is menu-driven (`commander.py`) and does not expose argument-based subcommands.
3. Docs currently reference `python run_outreach.py`, but that file does not exist.
4. Existing capabilities map well to planned commands:
	- autonomous run: `OutreachDirector.execute_autonomous_batch`
	- discovery + review: methods in `ColdMailerCLI`
	- follow-up queue processing: `_handle_follow_up`
	- dashboard server: `server.py`

### Phase 1 target

Deliver a stable, discoverable command contract that works before full packaging.

Interim invocation during development:

- `python -m agent.main ...` or `python main.py ...` (dev)

Final public shape (must remain stable):

- `clint <command> [options]`

### Command contract (v1 public surface)

1. `clint init`
	- Purpose: guided first-run setup for credentials and sender identity.
	- Flags:
	  - `--non-interactive`
	  - `--openrouter-key`
	  - `--smtp-user`
	  - `--smtp-pass`
	  - `--sender-name`
	  - `--sender-title`
	- Behavior:
	  - prompts for missing required values unless `--non-interactive`.
	  - writes config safely and masks secrets in output.

2. `clint config set <key> <value>`
	- Purpose: set one config value.
	- Rules:
	  - validate known keys only.
	  - secret keys never echoed in full.

3. `clint config show`
	- Purpose: display effective config.
	- Flags:
	  - `--json`
	  - `--show-secrets` (blocked unless explicit confirmation in interactive mode).

4. `clint config doctor`
	- Purpose: environment diagnostics.
	- Checks:
	  - OpenRouter auth
	  - SMTP auth
	  - Playwright browser install
	  - database path writable
	  - logs/data directories writable
	- Output:
	  - per-check PASS/FAIL/WARN and a final summary.

5. `clint run`
	- Purpose: autonomous campaign execution (maps to director batch flow).
	- Flags:
	  - `--query TEXT`
	  - `--target INT` (default 50)
	  - `--send-limit INT` (default 20)
	  - `--dry-run / --live`
	- UX:
	  - if `--query` missing, prompt interactively.
	  - show progress and final sent count.

6. `clint scrape`
	- Purpose: discovery + enrichment without mandatory sending.
	- Flags:
	  - `--query TEXT`
	  - `--target INT` (default 10)
	  - `--outreach` (optional immediate outreach handoff)

7. `clint dashboard`
	- Purpose: start FastAPI dashboard.
	- Flags:
	  - `--host` (default 127.0.0.1)
	  - `--port` (default 8000)
	  - `--reload`

8. `clint followup`
	- Purpose: process leads ready for follow-up outreach.
	- Flags:
	  - `--days-since-last INT` (default 3)
	  - `--channel email|whatsapp`

9. `clint export`
	- Purpose: export reporting tables to CSV.
	- Flags:
	  - `--table leads|outreach_history|all` (default all)
	  - `--out-dir PATH` (default data/exports)

10. `clint version`
	 - Purpose: print CLI and app version, plus Python runtime info with `--verbose`.

### UX contract

1. Command discoverability
	- `clint --help` shows all commands in task order: init -> doctor -> scrape/run -> followup -> export.
	- Every command includes one-line purpose, examples, and defaults.

2. Prompting model
	- Prefer flags for automation.
	- Prompt only for missing required args in TTY mode.
	- In non-interactive mode, missing required args must fail fast with remediation text.

3. Output model
	- Human-readable by default (Rich).
	- `--json` on config and diagnostics commands for automation.
	- Keep one success summary line at end of each command.

4. Error model
	- No traceback by default for expected user errors.
	- Show actionable hint and exact next command to fix.
	- `--verbose` reveals stack traces for debugging.

5. Safety defaults
	- default `run` behavior should be dry-run until user explicitly enables live send.
	- always show intended send counts before execution when live mode is selected.

### Exit code contract

- `0`: success
- `2`: usage/validation error (bad args, missing required value)
- `3`: configuration error (missing/invalid credentials)
- `4`: dependency/runtime readiness error (Playwright/database/path)
- `5`: network/auth transport failure (OpenRouter/SMTP/API)
- `10`: unexpected internal error

### Implementation sequence for Phase 1

1. Introduce argument-based command router (Typer recommended).
2. Keep current interactive menu as a fallback path (`clint` with no command).
3. Add adapters that call existing modules first, avoid deep rewrites:
	- `run` -> `OutreachDirector.execute_autonomous_batch`
	- `scrape/review/followup` -> existing CLI handler logic extracted to reusable services
	- `dashboard` -> existing FastAPI/uvicorn start flow
4. Unify docs/help examples to the same command names.
5. Add command-level smoke tests for `--help`, arg validation, and exit codes.

### Updated acceptance criteria for Phase 1

- A user can run `clint --help` and discover first-run flow without reading source code.
- All 10 commands return deterministic exit codes.
- Missing credentials are reported clearly with a remediation path.
- Existing founder-mode behavior remains available through `clint run`.
- Outdated `run_outreach.py` docs are removed or redirected to the new command contract.

## Phase 2: Packaging and Distribution

### Goal

Ship Clint as a standards-compliant Python package with a stable executable (`clint`), reproducible builds, and clean installation paths for both individual users and CI pipelines.

### Packaging architecture

1. Adopt `pyproject.toml` as the single source of packaging truth.
2. Use a modern backend (`hatchling` or `setuptools>=61`) with PEP 517 build isolation.
3. Keep runtime dependencies minimal and pinned by compatible ranges.
4. Move version to a single authoritative location and expose it to CLI (`clint version`).

### Project structure and metadata requirements

1. Package identity
	- distribution name: `sagarithm-clint`
	- import package: `agent` (or `clint` if renamed during packaging cleanup)
	- command: `clint`

2. Metadata fields (required)
	- `name`, `version`, `description`, `readme`, `license`, `requires-python`
	- `authors`, `keywords`, `classifiers`
	- `project.urls` for docs, source, issues

3. Console entrypoint
	- `[project.scripts] clint = <module>:<callable>`
	- entrypoint must parse args and return standard exit codes from Phase 1.

4. Included artifacts
	- Python modules
	- static assets required by dashboard
	- `.env.example`, docs needed for quickstart

5. Excluded artifacts
	- local db files, logs, screenshots, sessions, caches, secrets

### Build and release outputs

1. Build both:
	- source distribution (`sdist`)
	- wheel (`.whl`)
2. Verify package integrity:
	- clean install in virtual env
	- run `clint --help`
	- run `clint version`
3. Publish targets:
	- TestPyPI for pre-release validation
	- PyPI for tagged stable releases

### Cross-platform distribution contract

1. Windows (PowerShell + CMD)
2. macOS (zsh/bash)
3. Linux (bash)

Command behavior must be consistent for:

- help text
- exit codes
- config file discovery
- path handling for logs/data/exports

### Versioning and release semantics

1. SemVer policy:
	- `MAJOR`: breaking CLI contract
	- `MINOR`: backward-compatible command/features
	- `PATCH`: bug fixes and docs-only support updates
2. Pre-releases:
	- `v1.0.0rc1` style for release candidates
3. CLI reports both:
	- package version
	- commit SHA (when available in build metadata)

### Phase 2 implementation checklist

1. Add `pyproject.toml` with script entrypoint and metadata.
2. Add package data configuration for dashboard/static assets.
3. Add build command docs (`python -m build`).
4. Add install docs for:
	- `pipx install sagarithm-clint`
	- `pip install sagarithm-clint`
5. Add smoke test job that validates a fresh install invocation.

### Acceptance criteria

- Fresh machine install can run `clint --help` and `clint version`.
- `pip install` and `pipx install` both work without manual path hacks.
- Wheel and sdist install produce equivalent CLI behavior.
- Package contains required runtime assets and excludes local/private artifacts.
- Works on Windows, macOS, and Linux.

## Phase 3: Credential Onboarding and Validation

### Goal

Make first-run setup fast, safe, and self-healing so users can configure credentials without manually editing files, while maintaining strict secret hygiene.

### `clint init` onboarding contract

1. Setup modes
	- interactive (default)
	- non-interactive (CI/scripted) with explicit flags

2. Required credentials
	- `OPENROUTER_API_KEY`
	- `SMTP_USER_1`
	- `SMTP_PASS_1` (Gmail app password)

3. Optional identity fields
	- `SENDER_NAME`
	- `SENDER_TITLE`
	- `FROM_EMAIL` (defaults to SMTP user if omitted)

4. UX flow
	- detect existing config and ask: keep/update/overwrite
	- prompt for missing values only
	- hide secret input while typing
	- show masked confirmation summary before save

5. Persistence behavior
	- write to user-local config/env file used by CLI runtime
	- atomic write (temp file + rename) to avoid corruption
	- enforce file permissions where platform allows

### `clint config` behavior contract

1. `clint config set`
	- validate key against allowed registry
	- normalize values (trim whitespace, validate email format)
2. `clint config show`
	- mask secrets by default
	- `--json` for automation
3. `clint config doctor`
	- runs dependency + auth + path checks
	- returns non-zero when blocking checks fail

### Doctor checks matrix

1. Credentials and auth
	- OpenRouter key format sanity
	- lightweight API call to verify key validity
	- SMTP login handshake (no email sent)

2. Runtime dependencies
	- Playwright browser availability
	- Python package dependency sanity (critical imports)

3. Local environment
	- writable DB path
	- writable logs and export directories
	- timezone and clock sanity warning (non-blocking)

4. Network conditions
	- DNS/connectivity warning on failures
	- classify timeout vs auth vs transport errors

### Diagnostic output standard

1. Per-check output:
	- check name
	- status (`PASS`, `WARN`, `FAIL`)
	- short reason
	- remediation command or action
2. End summary:
	- passed count, warnings, failures
	- recommended next command

### Secret handling and security controls

1. Never print raw secrets to terminal/logs.
2. Masking standard:
	- key style: show first 4 + last 4 only
	- password style: fixed `********` mask
3. Redaction in exceptions and debug logs.
4. `.gitignore` must include local secret/config files.
5. `.env.example` contains placeholders only, never real values.

### Failure handling and exit codes

1. Missing required credential -> exit code `3`.
2. Invalid credentials or auth handshake failure -> exit code `5`.
3. Missing dependency/path issue -> exit code `4`.
4. Validation/usage mistakes -> exit code `2`.

### Acceptance criteria

- User can complete setup without manually editing files.
- `clint init` can be re-run idempotently to update only selected fields.
- `clint config doctor` reports actionable PASS/WARN/FAIL diagnostics.
- No secrets leak in terminal output, logs, or exception traces.

## Phase 4: Reliability and Safety Defaults

### Goal

Provide safe-by-default campaign execution that minimizes account risk and delivery failure while preserving operator control.

### Safety policy (updated per product requirement)

1. First-run default is dry-run.
2. No hard daily enforcement limits in CLI runtime.
3. Clear recommendation in UX and docs:
	- up to 200 emails/day and 200 WhatsApp/day is recommended for better deliverability and lower bot-detection risk.
4. Users retain explicit control for stricter self-imposed caps via command options/config.

### Reliability controls

1. Dry-run guardrails
	- dry-run preview shows recipients, channel, and estimated send volume.
	- switching to live requires explicit confirmation (or `--yes` in automation).

2. Sending cadence randomization
	- randomized delay between messages using configured min/max bounds.
	- optional jitter buckets by channel to avoid repetitive timing signatures.

3. Retry and backoff strategy
	- classify retryable errors (timeouts, temporary network, transient SMTP/API)
	- exponential backoff with cap and retry budget
	- do not retry hard auth failures or invalid recipient errors

4. Idempotency and duplicate suppression
	- prevent duplicate sends to same lead/channel within cooldown window
	- support de-dup by normalized email, phone, and domain
	- log suppression reason when a send is skipped

5. Campaign continuation and crash safety
	- persist progress checkpoints in DB
	- recover and resume after interruption without replaying completed sends
	- keep outreach history append-only for auditability

### Operational UX safeguards

1. Preflight summary before live sends:
	- lead count
	- channel mix
	- projected run time range
2. Warnings for high-volume runs beyond recommendation thresholds.
3. Progress UI that clearly separates sent, skipped, retrying, failed.
4. End-of-run reconciliation summary with next-step guidance.

### Failure classification contract

1. Authentication failures
2. Rate-limit or anti-abuse responses
3. Network/transport failures
4. Input/config validation failures
5. Remote service unavailability/degraded performance

Each failure class must produce:

- short explanation
- whether auto-retry happened
- exact remediation action

### Logging and observability requirements

1. Structured logs include run_id, lead_id, channel, event type, outcome.
2. Sensitive fields are redacted.
3. Error logs preserve enough context for support triage.
4. Optional `--verbose` mode expands diagnostics without exposing secrets.

### Acceptance criteria

- Long campaigns recover from temporary API/SMTP/network issues.
- Restarting a stopped run does not resend already completed outreach.
- Users receive recommendation warnings (200 email / 200 WhatsApp per day) without forced caps.
- Logs are useful for issue reports without exposing secrets.

## Phase 5: Open-Source Docs and Community Readiness

### Goal

Make the repository self-service for both end users and contributors, with documentation quality high enough to reduce support burden and accelerate community contributions.

### Documentation architecture

1. Quickstart docs (task-oriented)
	- 10-minute path: install -> init -> doctor -> dry-run -> live run
	- copy-paste commands for Windows/macOS/Linux

2. Reference docs (command-oriented)
	- full CLI reference generated from help output
	- all flags, defaults, examples, exit codes

3. Operations docs (incident-oriented)
	- troubleshooting matrix by symptom
	- recovery playbooks for common failures

### Required files and expected content quality

1. `README.md`
	- product overview, install matrix, quickstart, safety disclaimer
	- clear separation: dry-run vs live-run

2. Platform install guides
	- Windows, macOS, Linux sections with prerequisite checks
	- Playwright install and verification steps

3. Credential setup guide
	- OpenRouter key generation and validation
	- Gmail 2FA + app password creation
	- secret storage and masking behavior

4. Troubleshooting guide
	- auth errors, SMTP errors, Playwright missing, network timeouts
	- each issue includes probable cause and fix steps

5. Responsible-use and legal note
	- anti-spam, consent, and platform terms reminders
	- operator responsibility statement

6. Privacy/data handling statement
	- what is stored locally (db/logs/screenshots)
	- retention and deletion guidance

7. `CONTRIBUTING.md`
	- local dev setup, test commands, linting, commit conventions
	- PR checklist and review expectations

8. `CODE_OF_CONDUCT.md`
	- community behavior standards and escalation path

9. `SECURITY.md`
	- responsible disclosure process
	- supported versions and security patch policy

10. Issue and PR templates
	 - bug report, feature request, docs issue, regression template
	 - required environment and reproduction details

### Documentation quality gates

1. Every command in docs must exist and pass `--help`.
2. No references to removed/legacy commands.
3. All quickstart commands validated in clean environment.
4. Docs include realistic expected output snippets.
5. Links and command examples pass CI lint/check.

### Community readiness process

1. Add maintainer response SLA guidance for issues/PRs.
2. Define label taxonomy (`bug`, `onboarding`, `docs`, `good-first-issue`, `security`).
3. Curate starter issues with clear acceptance criteria.
4. Add discussion guidance for roadmap and support requests.

### Acceptance criteria

- A new user can complete first outreach flow using docs only.
- A contributor can set up dev env, run tests, and open a valid PR without maintainer intervention.
- Documentation has no stale command references and matches shipped CLI behavior.
- Community governance/security files are present, clear, and actionable.

## Phase 6: CI/CD and Release Engineering

Add GitHub Actions workflows:

1. Lint + tests on push and PR
2. Build package artifacts
3. Publish to TestPyPI on prerelease tags
4. Publish to PyPI on release tags

Release process:

1. Tag version
2. Auto-generate release notes/changelog
3. Attach artifacts
4. Verify install and smoke tests post-release

Acceptance criteria:

- Tag-to-PyPI path is automated and repeatable
- Rollback and hotfix process documented

## Phase 7: Public Launch

Launch assets:

1. GitHub release notes
2. Install commands (`pipx`, `pip`)
3. Quick demo GIF/video
4. Safety and usage disclaimers

Post-launch operations:

1. Daily issue triage for first 14 days
2. Fast patch releases for onboarding or install breakages
3. Track key metrics (installs, setup success, first-run completion)

---

## Security and Compliance Baseline

1. Never commit user credentials
2. Redact sensitive values in logs and traces
3. Keep dependency vulnerability scanning active
4. Publish responsible-use guidance:
	 - Respect anti-spam and communication laws
	 - Respect third-party platform terms
	 - User is responsible for recipient consent and message compliance

---

## Milestones

### Milestone A (Week 1)

- Finalize command contract
- Local installable build with `clint` command

### Milestone B (Week 2)

- `init` + `doctor` complete
- Credential flow secure and documented
- Dry-run safety defaults live

### Milestone C (Week 3)

- CI/CD release pipeline complete
- Core docs and community files complete

### Milestone D (Week 4)

- Public `v1.0.0` launch on PyPI and GitHub
- First-week support and patch cycle active

---

## Definition of Done for v1.0.0

1. `pipx install sagarithm-clint` works and exposes `clint`
2. `clint init` captures OpenRouter and Gmail app password flow
3. `clint config doctor` validates full runtime dependencies
4. `clint run` supports dry-run and live-run modes
5. Documentation and OSS governance files are complete
6. CI can publish signed artifacts to PyPI from version tags
7. Smoke tests pass on Windows, macOS, and Linux

---

## Notes for Gmail Auth

- Users should use Gmail with 2FA enabled and create an app password.
- Regular Gmail account password should not be used for SMTP automation.
- If app-password auth fails, doctor output should explicitly suggest checking:
	- 2FA status
	- app password creation
	- sender address matching configured SMTP user

## Notes for OpenRouter Auth

- Key validity should be tested via a lightweight API call during doctor checks.
- If key is invalid or rate-limited, return actionable remediation steps.

