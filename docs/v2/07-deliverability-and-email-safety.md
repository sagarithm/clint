# V2 Deliverability and Channel Safety

## Objective
Protect sender reputation while sustaining qualified response quality.

## Core Policy
- Reputation is a hard safety boundary, not a soft optimization target.
- No volume increase without health stability.
- Suppression checks are mandatory before every dispatch.

## Sending Controls
- Daily caps by inbox identity and domain health profile.
- Cooldown windows by lead and channel.
- Timezone-aware send windows with bounded randomness.
- Auto-throttle when engagement drops.

## Health Metrics
- Bounce rate (daily and rolling 7-day).
- Complaint rate and unsubscribe rate.
- Positive reply rate per sender identity.
- Delivery latency and provider error rates.

## Safety Automations
- Auto-pause sender identity on threshold breaches.
- Auto-route drafts to approval queue under risk conditions.
- Auto-suppress records on complaint or unsubscribe events.
- Auto-alert operators on anomalies and breach forecasts.

## Incident Playbook

### Bounce Spike
1. Pause affected sender identities.
2. Inspect recent source-quality cohorts.
3. Verify technical email authentication posture.
4. Resume with reduced caps and tighter quality gates.

### Reply Collapse
1. Audit targeting fit and evidence quality.
2. Audit template relevance and message clarity.
3. Run constrained experiments.
4. Scale only after recovery signal stabilizes.
