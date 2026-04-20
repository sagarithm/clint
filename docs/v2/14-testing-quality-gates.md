# V2 Testing and Quality Gates

## Objective
Ensure reliability, safety, and consistent product behavior before release.

## Test Matrix
- Unit tests: connectors, scoring, quality gates, policy checks.
- Integration tests: end-to-end lead lifecycle and dispatch flow.
- Contract tests: CLI command contracts and library API stability.
- Reliability tests: retry, backoff, and dead-letter replay behavior.
- Regression tests: message quality and suppression enforcement.

## Non-Functional Verification
- Performance checks for batch and queue workloads.
- Soak tests for long-running operational stability.
- Failure injection for provider outages and timeout spikes.

## Quality Gates
- No critical test failures.
- Contract tests pass for supported versions.
- Deliverability safety checks pass in staging simulation.
- Documentation updates included for behavior-affecting changes.

## Release Blockers
- Any suppression bypass defect.
- Any state machine integrity failure.
- Any unresolved high-severity reliability defect.
