# V2 Developer To-Do Checklist

## Sprint 1: Data and Schema Foundations
- [ ] Add lead_source table for multi-source metadata
- [ ] Add lead_signals table for intent/fit evidence
- [ ] Add suppression table (unsubscribed, bounced, complained)
- [ ] Add outreach_events table (sent, delivered, opened, replied, booked)
- [ ] Add indexes for source_platform, priority_score, status, discovered_at
- [ ] Add migration scripts and rollback safety

## Sprint 2: Connector Framework
- [ ] Create base connector interface (fetch, normalize, validate)
- [ ] Implement connector modules:
  - [ ] linkedin_connector
  - [ ] reddit_connector
  - [ ] x_threads_connector
  - [ ] upwork_connector
  - [ ] fiverr_connector
- [ ] Add retry logic, backoff, and structured failure logging
- [ ] Add source health dashboard metrics

## Sprint 3: Enrichment and Scoring
- [ ] Build enrichment pipeline with staged jobs
- [ ] Add contact confidence scoring
- [ ] Implement scoring_v2 service (fit, intent, authority, timing)
- [ ] Add queue prioritization and status transitions
- [ ] Add tests for score stability and threshold behavior

## Sprint 4: Message and Prompt Intelligence
- [ ] Build template registry by source + niche + outreach_step
- [ ] Add proof snippet injector from Pixartual assets
- [ ] Add personalization validator (reject weak drafts)
- [ ] Add subject/body quality checks and fallback templates
- [ ] Add tone and CTA variants for A/B testing

## Sprint 5: Sending Infrastructure
- [ ] Add per-inbox routing and daily cap logic
- [ ] Add timezone-aware scheduler
- [ ] Add bounce/complaint guardrails and auto-pause rules
- [ ] Add sending warm-up profiles for new inboxes
- [ ] Add send simulation mode with full audit output

## Sprint 6: Reply Automation
- [ ] Integrate inbox polling/webhook intake
- [ ] Add reply classifier service
- [ ] Add action orchestrator (book call, follow-up, disqualify)
- [ ] Add meeting handoff integration
- [ ] Add human override console for edge cases

## Sprint 7: Observability and Reliability
- [ ] Add structured logging across services
- [ ] Add metrics counters per stage
- [ ] Add alerting for connector/sender failures
- [ ] Add dead-letter queue for failed lead jobs
- [ ] Add runbook for incident response

## Sprint 8: Security and Compliance
- [ ] Add secrets management hardening
- [ ] Add data retention and deletion jobs
- [ ] Add opt-out propagation across all campaigns
- [ ] Add platform policy compliance checks per connector

## Testing Requirements
- [ ] Unit tests for connectors and normalizers
- [ ] Unit tests for scoring and threshold routing
- [ ] Integration tests for end-to-end outreach flow
- [ ] Load tests for queue throughput and sender stability
- [ ] Regression tests before each release

## Release Gates
- [ ] No critical errors in staging for 7 days
- [ ] Deliverability health above threshold
- [ ] Positive reply rate meets target baseline
- [ ] Runbook and documentation complete
