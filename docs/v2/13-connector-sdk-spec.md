# V2 Connector SDK Specification

## Purpose
Provide a plugin contract for adding and maintaining source connectors safely.

## Connector Lifecycle
1. Fetch raw source records.
2. Normalize to canonical connector output.
3. Validate required fields and policy constraints.
4. Emit accepted records and rejection reasons.

## Required Interface
- name(): returns source name.
- fetch(context): returns iterable of raw records.
- normalize(raw_record): returns canonical connector record.
- validate(record): returns pass/fail with reason codes.

## Canonical Output Requirements
- source_platform
- source_record_id
- source_url
- discovered_at_utc
- actor_or_company fields
- intent_evidence block
- confidence

## Validation Rules
- Missing source URL or record ID must fail validation.
- Empty evidence block must fail validation.
- Unsupported geography or policy-violating records must be rejected.

## Reliability Rules
- Connectors must be idempotent over repeated fetch windows.
- Connector errors must be categorized as transient or terminal.
- Connector retries follow global backoff policy.

## Observability Requirements
- Emit connector metrics: fetched, accepted, rejected, failed.
- Include adapter version in all normalized outputs.
- Attach correlation IDs for traceability.
