# V2 Source Connectors and Qualification Filters

## Objective
Collect high-value opportunities with verifiable demand signals for web-solution
offers. Connector output must be normalized, scored, and auditable.

## Connector Contract (Required Fields)
- source_platform
- source_record_id
- source_url
- discovered_at_utc
- actor_name
- company_name
- role_title
- website
- contact_points (email, phone, profile)
- geo
- industry_hint
- intent_evidence_text
- intent_evidence_type
- budget_or_maturity_hints
- authority_hints
- confidence

## Build Priority (CLI and Library First)
1. Maps + directory sources (already operational, improve quality).
2. LinkedIn compliant capture via explicit policy-safe flows.
3. Additional intent sources behind feature flags after baseline stability.

## Current Implementation Status
- Production fetch connectors: Reddit, Upwork (RSS demand ingestion).
- SDK-normalized stubs pending production fetch paths: LinkedIn, X/Threads, Fiverr.
- All connector outputs are normalized through shared adapter contracts and
	can be persisted with rejection reason tracking.

## Normalization Rules
- Canonical domain normalization and duplicate fingerprinting.
- Timestamp all source records in UTC.
- Preserve raw evidence payload for every connector output.
- Reject records that cannot be traced to a source URL or evidence block.

## Qualification Filters

### Must-Pass Rules
- Contact confidence at or above threshold.
- Offer fit is web-solution compatible.
- Suppression checks pass at global and campaign level.
- Lead is not recently contacted within cooldown policy.

### Auto-Reject Rules
- Non-commercial requests or low-intent noise.
- Obvious mismatch with serviceable ICP.
- Unknown or unverified contact surface.
- Duplicate entity with active outreach state.

## Queue Routing Policy
- score >= 8.0: ready_for_message_generation
- 6.0 <= score < 8.0: enrich_and_recheck
- score < 6.0: archive_or_nurture

## Compliance and Source Safety
- Respect source terms and platform interaction limits.
- Keep source adapter policy flags explicit and testable.
- Log all rejects with machine and human-readable reasons.
