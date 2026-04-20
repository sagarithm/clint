# V2 Developer Todo: CLI and Library First

## Sprint 1: Contract Backbone
- [ ] Freeze canonical lead, event, and state contracts.
- [ ] Implement schema migrations with rollback verification.
- [ ] Add immutable event logging for critical transitions.
- [ ] Add suppression and compliance base tables.

## Sprint 2: Core Engine Refactor
- [ ] Separate connector, enrichment, scoring, and messaging services.
- [ ] Implement explicit state machine transition helpers.
- [ ] Add connector adapter interface with standard lifecycle hooks.
- [ ] Replace implicit status writes with policy-checked transitions.

## Sprint 3: Library API Hardening
- [ ] Publish typed API contracts for sync and async flows.
- [ ] Add stable error classes and retry-safe behavior.
- [ ] Add batch processing API with bounded concurrency controls.
- [ ] Add reference examples that match actual package behavior.

## Sprint 4: CLI Runtime Hardening
- [ ] Standardize command outcomes with exit-code guarantees.
- [ ] Add dry-run mode for all send-capable commands.
- [ ] Add per-command audit summaries.
- [ ] Add approval queue commands for edge-case intervention.

## Sprint 5: Quality Gates
- [ ] Add pre-send personalization checks and rejection reasons.
- [ ] Add deliverability risk gate before dispatch.
- [ ] Add deterministic fallback template path.
- [ ] Add regression tests for message quality failures.

## Sprint 6: Reliability and Observability
- [ ] Add correlation IDs across all pipeline operations.
- [ ] Add service-level metrics and error-rate SLO alerts.
- [ ] Add dead-letter replay tooling for failed jobs.
- [ ] Add incident playbook validation tests.

## Sprint 7: Reply Intelligence
- [ ] Add reply classifier with confidence scores.
- [ ] Add next-best-action routing policy.
- [ ] Add human override path for low-confidence classification.
- [ ] Add response SLA monitoring and breach alerts.

## Sprint 8: Release and Governance
- [ ] Implement semantic versioning and migration notes automation.
- [ ] Add release checklist gate in CI.
- [ ] Add deprecation policy docs and warning mechanism.
- [ ] Publish stable v2 library and CLI release.

## Definition of Done
- [ ] No critical production defects in staged soak tests.
- [ ] KPI floor reached for two consecutive weekly cycles.
- [ ] Documentation synchronized with shipped behavior.
- [ ] Rollback validated for schema and runtime releases.
