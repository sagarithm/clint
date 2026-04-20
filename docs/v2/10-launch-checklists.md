# V2 Launch Checklists

## Pre-Launch Readiness
- [ ] ICP and offer locked for launch cycle.
- [ ] Library and CLI version targets finalized.
- [ ] Connector policy checks passing.
- [ ] Scoring and quality-gate thresholds approved.
- [ ] Suppression and compliance controls active.

## Engineering Readiness
- [ ] Schema migrations validated with rollback tests.
- [ ] State machine transitions validated by integration tests.
- [ ] Retry and dead-letter workflows tested.
- [ ] Correlation IDs and structured logs verified.
- [ ] Critical runbooks tested in simulation.

## Messaging Readiness
- [ ] Prompt compiler version pinned.
- [ ] Proof asset mapping approved.
- [ ] Draft quality pass-rate above minimum threshold.
- [ ] Approval queue path active for low-confidence drafts.

## Launch Day Operations
- [ ] Start with constrained send caps.
- [ ] Monitor connector, scoring, dispatch, and reply health hourly.
- [ ] Validate suppression actions in real time.
- [ ] Keep rollback commands and owners on active duty.

## First 7 Days
- [ ] Daily source quality review.
- [ ] Daily deliverability and sender-risk review.
- [ ] Daily prompt and template review against outcomes.
- [ ] Controlled tuning only, no major architecture changes.

## Rollback Protocol
- [ ] Disable failing module via feature flag.
- [ ] Route in-flight jobs to safe queue states.
- [ ] Pause impacted sender identities.
- [ ] Log incident timeline and remediation actions.
- [ ] Re-enable only after root-cause closure.

## Sign-Off Criteria
- [ ] KPI floor met for two consecutive weeks.
- [ ] No critical safety incidents.
- [ ] No unresolved high-severity defects.
- [ ] Documentation reflects exact shipped behavior.
