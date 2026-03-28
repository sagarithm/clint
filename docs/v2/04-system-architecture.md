# V2 System Architecture

## Design Goal
Build a modular, failure-tolerant pipeline that can ingest multi-source leads, qualify them with high precision, and convert them through compliant, deliverability-safe outreach.

## Core Services

### 1) Ingestion Service
- Pulls records from each source connector
- Normalizes records into unified lead schema
- Emits ingestion events to queue

### 2) Enrichment Service
- Performs website and profile enrichment
- Adds contact confidence and business maturity signals
- Stores enrichment snapshots with timestamps

### 3) Scoring Service
- Calculates fit, intent, authority, and timing scores
- Computes priority score and route decision
- Writes score history for explainability

### 4) Message Intelligence Service
- Selects template by source, niche, and stage
- Injects relevant proof snippets from Pixartual assets
- Validates output quality before queueing for send

### 5) Outreach Scheduler
- Applies per-inbox limits and sending windows
- Handles timezone-aware and domain-aware pacing
- Writes send audit events and state transitions

### 6) Reply Processor
- Ingests inbound replies
- Classifies intent
- Triggers next action (book, follow-up, disqualify, suppress)

### 7) Analytics Service
- Aggregates source and campaign KPIs
- Tracks funnel health and trend lines
- Feeds weekly optimization reports

## Queue Topology
- queue.ingestion.raw
- queue.enrichment.pending
- queue.scoring.pending
- queue.messaging.pending
- queue.sending.pending
- queue.reply.pending
- queue.deadletter

## State Machine (Lead Lifecycle)
- discovered
- normalized
- enriched
- scored
- queued_for_outreach
- sent_step_1
- sent_step_2
- sent_step_3
- replied_positive
- replied_neutral
- replied_negative
- booked
- disqualified
- suppressed

## Reliability Patterns
- Idempotent processors by lead fingerprint
- Exponential backoff retries for external sources
- Dead-letter queue with operator replay tools
- Circuit breakers for failing external APIs
- Health probes per service and per source connector

## Deployment Guidance
- Keep connectors isolated by source to reduce blast radius
- Separate scheduler and sender workers for precise throttling
- Run reply processing as high-priority workers
- Use structured logs with campaign and lead correlation IDs

## Security and Access
- Secrets from secure environment store only
- Principle of least privilege for source credentials
- PII access control and audit trails
- Data retention and deletion tasks by policy

## Operational Alerts
- Connector outage alerts
- Queue backlog alerts
- Bounce spike alerts
- Reply processing delay alerts
- API budget consumption alerts
