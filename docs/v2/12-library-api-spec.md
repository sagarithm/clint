# V2 Library API Specification

## Purpose
Define the stable Python package interface that powers integrations and CLI
runtime workflows.

## API Design Principles
- Typed input and output contracts.
- Sync and async parity where practical.
- Deterministic behavior with explicit failure semantics.
- Backward-compatible evolution through semantic versioning.

## Core API Domains
- Lead ingestion and normalization.
- Enrichment and evidence extraction.
- Scoring and decision reasoning.
- Message drafting and quality validation.
- Dispatch orchestration and event publication.
- Reply classification and next-action recommendation.

## Contract Requirements
- Public methods return structured result objects.
- Results include reason codes for key decisions.
- Exceptions are stable, documented, and domain-specific.
- Batch APIs expose bounded-concurrency controls.

## Reliability Requirements
- Idempotent operations where side effects can repeat.
- Retry-safe integration calls with clear max-attempt behavior.
- Correlation ID support in all eventful operations.

## Versioning Policy
- Major: breaking API changes.
- Minor: additive functionality.
- Patch: bug fixes and non-breaking behavior improvements.

## Documentation Requirements
- Public API examples for each domain.
- Migration notes for any behavioral changes.
- Changelog entries tied to API versions.
