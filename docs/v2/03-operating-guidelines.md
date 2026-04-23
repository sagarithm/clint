# V2 Operating Guidelines

## Operating Doctrine
This system is an evidence-led automation engine. Quality, trust, and
measurable outcomes are prioritized over volume.

## Scope Policy
- Primary offer: web solutions.
- Primary surfaces: Python library and CLI.
- Autonomy mode: mostly automated with approvals for risky or low-confidence
  actions.

## Campaign Readiness Standard
Before activation, all checks must pass:
- ICP and offer are explicitly selected.
- Proof assets mapped to niche and stage.
- Source adapters healthy and policy-compliant.
- Suppression and cooldown policies active.
- Deliverability guardrails configured.

## Decision Pipeline
1. Discover and normalize source evidence.
2. Enrich and validate contact confidence.
3. Score fit, intent, authority, timing, and risk.
4. Generate message variants and run quality gates.
5. Route to auto-send or approval queue.
6. Send with safety checks and event logging.
7. Classify replies and execute next-best action.

## Quality Gates (Mandatory)
- Relevance and personalization thresholds pass.
- No unsupported claims or fabricated context.
- No placeholder tokens.
- Channel-specific style and length constraints pass.
- Suppression and legal policy checks pass.

## Sending Governance
- Start at low controlled volume per sender identity.
- Increase only after stable health over defined windows.
- Auto-pause on bounce, complaint, or anomaly spikes.
- Enforce contact frequency limits and cooldown windows.

## Reply SLA
- Positive intent: first response within 1 business hour.
- Clarification: response within 4 business hours.
- Objection handling: same business day with proof-backed response.
- Unsubscribe or complaint: immediate suppression and logged reason.

## Weekly Control Review
- Source ranking by qualified reply and meeting rate.
- Template ranking by conversion and risk profile.
- Deliverability health and sender-level risk board.
- Actions: pause, promote, retrain, or rollback.

## Deadletter Incident Loop
Use deadletter controls as the standard recovery procedure for failed async
events:
1. Triage with `clint deadletter-list --status pending`.
2. Validate payload class and root cause from event metadata.
3. Replay with `clint deadletter-replay --event-id <id>` for supported types.
4. Confirm outcome using replay status and replay attempt counters.
5. Escalate unsupported payload classes into connector/worker backlog.

Current supported replay classes:
- Raw source payload replay for Reddit and Upwork ingestion paths.
- Stage-level replay for `enrich`, `draft`, and `dispatch` deadletter events.
- Dispatch replay runs in dry-run mode by default for safety.

Operational API equivalents:
- `GET /api/deadletter`
- `POST /api/deadletter/replay`

## Change Control Rules
- No production change without objective and rollback plan.
- No scaling without two-week KPI stability.
- No source expansion before baseline quality targets are met.
- All significant experiments must be logged and versioned.
