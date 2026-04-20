# V2 KPI and Experiment Framework

## Goal
Operate the system through measurable, repeatable decision cycles.

## KPI Layers

### Acquisition KPIs
- leads_discovered
- leads_qualified
- qualification_rate
- source_health_score

### Intelligence KPIs
- enrichment_success_rate
- scoring_confidence_distribution
- draft_quality_pass_rate
- approval_queue_ratio

### Outreach KPIs
- sends_attempted
- sends_successful
- positive_reply_rate
- meeting_booking_rate
- qualified_meeting_rate

### Reliability KPIs
- connector_error_rate
- queue_backlog_size
- dispatch_failure_rate
- SLA_breach_count

## Dashboard Views
- Executive health board.
- Source and connector performance board.
- Template and prompt performance board.
- Sender reputation and deliverability board.

## Experiment Workflow
1. Define hypothesis and primary metric.
2. Set sample floor and stop conditions.
3. Run bounded experiment window.
4. Promote, rollback, or archive based on policy.

## Decision Rules
- Promote only with stable positive uplift and no risk regression.
- Roll back immediately on deliverability or quality degradation.
- Archive learnings with versioned context and action notes.

## Operational Hooks (Implemented)
- CLI: `clint experiments-decide --experiment-id <id>`
- API: `POST /api/experiments/decide`

Default decision thresholds:
- minimum sample per variant: 30
- minimum uplift for promotion: 5 percent
- maximum negative quality impact: -5 percent
