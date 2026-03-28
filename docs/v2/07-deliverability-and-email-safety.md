# V2 Deliverability and Email Safety

## Goal
Scale outreach while preserving inbox reputation and reply quality.

## Sending Ramp Policy
- New inbox week 1: 15 to 25 emails/day
- Week 2: 30 to 45/day if bounce and complaint rates remain healthy
- Week 3+: 50+/day only after sustained health
- Prefer multiple inboxes over overloading one inbox

## Core Health Metrics
- Bounce rate (daily and 7-day)
- Complaint rate
- Unsubscribe rate
- Domain-level deliverability trend
- Positive reply rate by inbox

## Safety Guardrails
- Auto-pause inbox on bounce spikes
- Auto-throttle domains with poor engagement
- Per-domain contact frequency caps
- Mandatory suppression checks before every send

## Content Safety Rules
- Avoid spam trigger phrasing and over-promising
- Limit links and formatting complexity
- Keep language natural and personalized
- Ensure subject lines are relevant and specific

## Infrastructure Controls
- SPF, DKIM, and DMARC configured and validated
- Distinct sending domains/subdomains where needed
- Gradual warmup sequence for new inboxes
- Monitor provider feedback and placement indicators

## Scheduling Standards
- Local-time delivery for target region
- Avoid unnatural burst patterns
- Respect business-hour windows by niche
- Use randomized but bounded intervals

## Suppression and Compliance
- Global suppression list across all campaigns
- Immediate suppression on unsubscribe or complaint
- Record suppression reason and timestamp
- Enforce no-contact in all channels

## Incident Response

### If Bounce Rate Spikes
1. Pause affected inboxes
2. Audit recent list quality
3. Verify DNS and authentication health
4. Resume with lower volume after correction

### If Reply Rate Collapses
1. Check inbox placement and spam risk
2. Review targeting and template relevance
3. Run controlled A/B diagnostics
4. Re-enable scale only after recovery

## Weekly Deliverability Review
- Inbox health leaderboard
- Domain risk summary
- Template risk summary
- Corrective actions and owners
