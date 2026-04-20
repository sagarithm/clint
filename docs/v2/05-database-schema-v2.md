# V2 Database Schema Specification

## Design Objectives
- Preserve complete decision evidence per lead lifecycle.
- Support deterministic state transitions and replay workflows.
- Enable high-confidence analytics and attribution.
- Enforce suppression and compliance at query-time and write-time.

## Core Tables

### leads
Canonical entity profile and lifecycle state.
- id
- canonical_name
- canonical_domain
- primary_contact_email
- primary_contact_phone
- industry
- geo
- lifecycle_state
- confidence_level
- created_at
- updated_at

### lead_sources
Source-specific ingest records with provenance.
- id
- lead_id
- source_platform
- source_record_id
- source_url
- discovered_at_utc
- raw_payload_json
- adapter_version

### lead_evidence
Structured evidence blocks used for reasoning.
- id
- lead_id
- evidence_type
- evidence_text
- evidence_value
- evidence_confidence
- captured_at_utc

### lead_enrichment_snapshots
Versioned enrichment snapshots for replayability.
- id
- lead_id
- snapshot_version
- website_summary
- rating
- reviews_count
- social_links_json
- contact_confidence
- enriched_at_utc

### lead_scores
Explainable scoring history.
- id
- lead_id
- fit_score
- intent_score
- authority_score
- timing_score
- risk_score
- priority_score
- reason_codes_json
- scored_at_utc

### message_drafts
Drafts and quality-evaluation outputs.
- id
- lead_id
- channel
- template_id
- prompt_version
- subject
- body
- quality_score
- rejection_reason
- created_at_utc

### outreach_events
Immutable event stream of send lifecycle.
- id
- lead_id
- channel
- event_type
- event_payload_json
- correlation_id
- occurred_at_utc

### reply_events
Inbound reply capture and classification.
- id
- lead_id
- channel
- thread_ref
- reply_text
- classifier_label
- classifier_confidence
- requires_human_review
- occurred_at_utc

### suppression_entries
Global suppression and policy controls.
- id
- contact_key
- suppression_type
- reason
- source
- created_at_utc

### compliance_checks
Decision records for policy evaluation.
- id
- lead_id
- check_name
- decision
- reason
- checked_at_utc

## Required Indexes
- leads(canonical_domain)
- leads(lifecycle_state)
- lead_sources(source_platform, discovered_at_utc)
- lead_scores(priority_score)
- outreach_events(event_type, occurred_at_utc)
- reply_events(classifier_label, occurred_at_utc)
- suppression_entries(contact_key)

## Constraints and Integrity
- Unique dedupe key on canonical_domain plus canonical_name.
- Immutable outreach_events and reply_events rows.
- Foreign key integrity across all lead-linked records.
- Soft-delete for profile records and policy-driven PII purge workflow.

## Migration Strategy
1. Introduce v2 tables in additive mode.
2. Backfill leads, history, and score data with mapping logs.
3. Dual-write from runtime to v1 and v2 tables.
4. Validate read parity and anomaly budgets.
5. Switch readers to v2 and deprecate v1 access paths.
