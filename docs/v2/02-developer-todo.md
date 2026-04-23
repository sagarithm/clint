# V2 Developer Todo: CLI and Library First

Status: Archived completion checklist. V2 implementation items below are complete
for the current documented scope.

## Sprint 1: Contract Backbone
- [x] Freeze canonical lead, event, and state contracts.
- [x] Implement schema migrations with rollback verification.
- [x] Add immutable event logging for critical transitions.
- [x] Add suppression and compliance base tables.

## Sprint 2: Core Engine Refactor
- [x] Separate connector, enrichment, scoring, and messaging services.
- [x] Implement explicit state machine transition helpers.
- [x] Add connector adapter interface with standard lifecycle hooks.
- [x] Replace implicit status writes with policy-checked transitions.

## Sprint 3: Library API Hardening
- [x] Publish typed API contracts for sync and async flows.
- [x] Add stable error classes and retry-safe behavior.
- [x] Add batch processing API with bounded concurrency controls.
- [x] Add reference examples that match actual package behavior.

## Sprint 4: CLI Runtime Hardening
- [x] Standardize command outcomes with exit-code guarantees.
- [x] Add dry-run mode for all send-capable commands.
- [x] Add per-command audit summaries.
- [x] Add approval queue commands for edge-case intervention.

## Sprint 5: Quality Gates
- [x] Add pre-send personalization checks and rejection reasons.
- [x] Add deliverability risk gate before dispatch.
- [x] Add deterministic fallback template path.
- [x] Add regression tests for message quality failures.

## Sprint 6: Reliability and Observability
- [x] Add correlation IDs across all pipeline operations.
- [x] Add service-level metrics and error-rate SLO alerts.
- [x] Add dead-letter replay tooling for failed jobs.
- [x] Add incident playbook validation tests.

## Sprint 7: Reply Intelligence
- [x] Add reply classifier with confidence scores.
- [x] Add next-best-action routing policy.
- [x] Add human override path for low-confidence classification.
- [x] Add response SLA monitoring and breach alerts.

## Sprint 8: Release and Governance
- [x] Implement semantic versioning and migration notes automation.
- [x] Add release checklist gate in CI.
- [x] Add deprecation policy docs and warning mechanism.
- [x] Publish stable v2 library and CLI release.

## Definition of Done
- [x] No critical production defects in staged soak tests.
- [x] KPI floor reached for two consecutive weekly cycles.
- [x] Documentation synchronized with shipped behavior.
- [x] Rollback validated for schema and runtime releases.
