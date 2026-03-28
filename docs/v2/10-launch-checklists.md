# V2 Launch Checklists

## Pre-Launch Checklist
- [ ] ICP, offer, and proof assets approved
- [ ] Connector health checks passing
- [ ] Scoring thresholds configured and reviewed
- [ ] Suppression and compliance checks active
- [ ] Sending limits and warmup profiles configured
- [ ] Reply handling workflows tested
- [ ] Dashboards and alerts live

## Technical Readiness Checklist
- [ ] Migrations applied in staging and validated
- [ ] Queue retries and dead-letter handling tested
- [ ] API failure scenarios simulated
- [ ] Rate-limit and backoff logic verified
- [ ] Structured logs and correlation IDs confirmed

## Messaging Readiness Checklist
- [ ] Source-specific templates loaded
- [ ] Proof snippets mapped to niche
- [ ] Quality gate thresholds validated
- [ ] Human review path active for low-quality drafts

## Launch Day Checklist
- [ ] Start with controlled send volume
- [ ] Monitor ingestion, send, and reply pipelines hourly
- [ ] Verify suppression and unsubscribe actions in real time
- [ ] Keep rollback switch ready for each major module

## First 72 Hours Checklist
- [ ] Daily quality review of first-touch messages
- [ ] Source-by-source lead quality validation
- [ ] Deliverability health review and cap adjustment
- [ ] Fast iteration on weak opening lines

## Week 1 Optimization Checklist
- [ ] Remove bottom-performing source and template combinations
- [ ] Increase volume only for healthy inboxes
- [ ] Recalibrate scoring with real reply outcomes
- [ ] Review positive replies for offer-message fit

## Rollback Checklist
- [ ] Disable failing connector
- [ ] Route leads to safe fallback queues
- [ ] Pause affected inboxes
- [ ] Notify owners and document incident
- [ ] Restore after root-cause verification

## Sign-Off Criteria
- [ ] Positive reply rate above baseline
- [ ] No critical deliverability incidents
- [ ] Stable connector uptime
- [ ] Team follows runbook without blockers
