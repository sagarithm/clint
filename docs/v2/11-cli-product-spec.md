# V2 CLI Product Specification

## Purpose
Define a stable, production-grade CLI surface for operating the outreach system
with deterministic behavior and clear safety guarantees.

## Design Goals
- Fast operational workflows.
- Predictable exit codes and machine-readable outcomes.
- Safe defaults for commands with outbound side effects.
- Full traceability for each command execution.

## Command Families
- Discovery commands: source acquisition and normalization tasks.
- Intelligence commands: enrichment, scoring, and audit tasks.
- Messaging commands: draft generation and quality checks.
- Dispatch commands: send orchestration and controlled rollout.
- Reply commands: inbound classification and next-step routing.
- Ops commands: health, metrics, and incident diagnostics.

## Implemented V2 Command Surface (Current)
- Core operations: `run`, `scrape`, `followup`, `export`, `dashboard`.
- Worker controls: `worker-reddit`.
- Experiment controls: `experiments-decide`.
- Incident recovery controls: `deadletter-list`, `deadletter-replay`.

## Reliability Ops Contract (Current)
- `worker-reddit`:
	- Inputs: `--query`, `--limit`, `--dry-run/--live`.
	- Behavior: executes staged Reddit worker pipeline with bounded batch size.
- `experiments-decide`:
	- Inputs: `--experiment-id`, thresholds for sample/uplift/quality impact.
	- Behavior: returns deterministic decision (`promote|hold|rollback|no_winner`).
- `deadletter-list`:
	- Inputs: optional replay status filter and limit.
	- Behavior: returns replay triage view with status and attempt metadata.
- `deadletter-replay`:
	- Inputs: deadletter event ID.
	- Behavior: reprocesses supported payloads and records replay metadata.

## Behavioral Contracts
- Every command returns a structured summary object.
- Side-effecting commands support dry-run mode.
- All commands attach a correlation ID to resulting events.
- Commands fail with explicit reason codes.

## Exit Codes (Baseline)
- 0: success
- 2: usage/validation error
- 3: configuration error
- 4: runtime dependency failure
- 5: network/provider failure
- 10: internal unexpected failure

## Safety Defaults
- Dispatch commands default to bounded volume.
- Suppression checks are mandatory and cannot be bypassed in standard mode.
- Commands interacting with providers use retry and backoff policy.

## Operator Experience Standards
- Clear command help with examples.
- Progress and status visibility for long-running operations.
- Final summary includes counts, decisions, and unresolved actions.

## API Parity for Ops Workflows
Reliability commands are mirrored by API endpoints for dashboard or external
automation surfaces:
- `POST /api/workers/reddit/run`
- `GET /api/workers/reddit/status`
- `GET /api/deadletter`
- `POST /api/deadletter/replay`

## Backward Compatibility
- Breaking command behavior requires major version increment.
- Deprecated flags require warning period and migration guidance.
