# V2 Database Schema Specification

## Goals
- Support multi-source ingestion
- Preserve explainable lead scoring
- Track full outreach and reply lifecycle
- Enforce suppression and compliance controls

## Recommended Tables

### leads
Core deduplicated entity.
- id
- company_name
- person_name
- role_title
- primary_domain
- website
- primary_email
- primary_phone
- location_city
- location_region
- industry
- niche
- status
- created_at
- updated_at

### lead_sources
Per-source discovery records.
- id
- lead_id
- source_platform
- source_url
- external_id
- discovered_at
- raw_payload_json
- connector_version

### lead_signals
Extracted signals and confidence evidence.
- id
- lead_id
- signal_type
- signal_text
- signal_value
- confidence_score
- captured_at

### lead_enrichment
Snapshot enrichment outputs.
- id
- lead_id
- crawl_summary
- review_count
- rating
- social_profiles_json
- team_size_hint
- budget_hint
- enrichment_version
- enriched_at

### lead_scores
Explainable score history.
- id
- lead_id
- fit_score
- intent_score
- authority_score
- timing_score
- priority_score
- score_reason_json
- scored_at

### outreach_sequences
Campaign sequence metadata.
- id
- campaign_id
- lead_id
- current_step
- next_action_at
- sequence_status
- owner
- updated_at

### outreach_messages
Stored generated messages and metadata.
- id
- sequence_id
- channel
- subject
- body
- template_id
- personalization_score
- generated_at

### outreach_events
Delivery and engagement tracking.
- id
- message_id
- event_type
- event_at
- provider_message_id
- event_metadata_json

### inbox_accounts
Sender infrastructure and health.
- id
- email_address
- domain
- warmup_stage
- daily_cap
- health_status
- bounce_rate_7d
- complaint_rate_7d
- last_used_at

### reply_threads
Inbound thread state.
- id
- lead_id
- channel
- thread_ref
- latest_reply_text
- reply_class
- sentiment
- requires_human
- updated_at

### suppression_list
Global no-contact controls.
- id
- contact_key
- suppression_type
- reason
- source
- created_at

### compliance_audit
Compliance decision history.
- id
- lead_id
- check_name
- decision
- reason
- checked_at

## Key Indexes
- leads(primary_domain)
- leads(status)
- lead_sources(source_platform, discovered_at)
- lead_scores(priority_score)
- outreach_sequences(next_action_at, sequence_status)
- outreach_events(event_type, event_at)
- suppression_list(contact_key)

## Data Constraints
- Unique dedupe key on (primary_domain, company_name normalized)
- Foreign key integrity across lead_id and sequence_id chains
- Immutable event rows for auditability
- Soft delete for lead records, hard delete for sensitive PII by policy

## Migration Strategy
1. Add new tables in non-breaking mode.
2. Backfill source and score history from existing records.
3. Switch writers to new tables behind feature flags.
4. Run dual-write validation window.
5. Cut over readers and retire legacy reads.
