# V2 System Architecture

## Design Intent
Ship a modular decision engine that powers both library and CLI surfaces with
shared contracts, strong safety gates, and full observability.

## Runtime Surfaces
- Library surface: deterministic Python APIs for integration workloads.
- CLI surface: operator and automation workflows with explicit command contracts.
- API runtime surface: optional orchestration endpoint for remote triggers.

## Core Modules

### 1) Connector Module
- Executes source adapters.
- Normalizes raw records into canonical lead inputs.
- Emits traceable ingestion events.

### 2) Enrichment Module
- Crawls and enriches business context.
- Produces structured evidence blocks.
- Calculates contact confidence inputs.

### 3) Scoring Module
- Computes fit, intent, authority, timing, and risk.
- Returns score and reason codes.
- Routes lead to next state.

### 4) Message Compiler Module
- Assembles channel-aware prompts using evidence and proof assets.
- Generates drafts and evaluates quality metrics.
- Rejects low-confidence outputs with explicit reasons.

### 5) Dispatch Module
- Applies caps, cooldown, and sender health policies.
- Sends through channel operators.
- Records immutable outreach events.

### 6) Reply Intelligence Module
- Classifies inbound responses.
- Maps intent to next-best-action.
- Routes uncertain replies to human review queue.

### 7) Observability Module
- Collects metrics, traces, and structured logs.
- Emits SLO alerts and anomaly events.
- Supports replay and incident diagnostics.

## Event Topology
- events.connector.raw
- events.connector.normalized
- events.enrichment.completed
- events.scoring.completed
- events.message.generated
- events.dispatch.requested
- events.dispatch.completed
- events.reply.received
- events.reply.classified
- events.deadletter

## State Machine
- discovered
- normalized
- enriched
- scored
- queued_for_review
- queued_for_send
- sent
- replied_positive
- replied_neutral
- replied_negative
- booked
- disqualified
- suppressed

## Reliability and Safety Patterns
- Idempotent writes by deterministic lead fingerprint.
- Retry with exponential backoff for transient failures.
- Dead-letter queue and replay utilities.
- Circuit breakers for degraded providers.
- Mandatory suppression check at pre-send boundary.

## Deployment Notes
- Isolate connector workers from dispatch workers.
- Prioritize reply-intelligence workers for faster response SLA.
- Keep state machine transitions in a single shared module.
