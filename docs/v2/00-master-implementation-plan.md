# ColdMailer V2: Master Implementation Plan for High-Paying Clients

## Objective
Transform the current outreach automation into a multi-source, intent-driven, ROI-focused growth engine that consistently books meetings with high-paying clients.

## North Star Metrics
- Positive reply rate: >= 3%
- Meeting booking rate: >= 1%
- Opportunity rate (qualified meeting): >= 60% of booked meetings
- Cost per qualified meeting: tracked weekly and reduced month over month
- Source contribution: at least 2 sources generating consistent positive replies

## ICP and Offer Strategy

### Primary ICP (Start with one niche for 30 days)
- Preferred verticals: Dental, Legal, Med Spa, B2B SaaS, High-ticket local services
- Minimum buying signals:
  - Established online reputation
  - Visible revenue indicators (reviews, locations, team size, ad activity)
  - Decision-maker reachable

### Offer Positioning
- Do not lead with generic "website redesign" messaging.
- Lead with business outcomes:
  - More booked consultations
  - Better lead conversion rate
  - Lower CAC with better digital funnel
  - Reduced operational waste through automation

### Proof Positioning
Use Pixartual proof assets in every sequence:
- Relevant project snapshot (same or adjacent niche)
- Measurable outcome statement
- One concise credibility anchor (experience, process, result)

## V2 System Architecture

### Layer 1: Lead Discovery
- Multi-source ingestion modules:
  - Google Maps/Directories
  - LinkedIn (compliant workflows)
  - Reddit intent capture
  - X/Threads intent capture
  - Upwork/Fiverr demand capture
- Unified ingestion format for all sources.

### Layer 2: Enrichment
- Website crawl and metadata extraction
- Contact enrichment (role, email confidence)
- Business maturity checks (reviews, activity, footprint)
- Service-fit extraction from source context

### Layer 3: Qualification
- Multi-factor scoring model:
  - Fit Score (ability to pay + service match)
  - Intent Score (buying urgency)
  - Authority Score (decision power)
  - Timing Score (probability of action now)
- Outreach threshold and queue priority routing.

### Layer 4: Message Intelligence
- Source-specific templates and prompts
- Dynamic proof insertion from Pixartual assets
- CTA selector by lead stage and source
- Quality gate (reject low-relevance drafts)

### Layer 5: Sending and Deliverability
- Multi-inbox rotation with ramp policy
- Timezone-aware scheduling
- Bounce and complaint guardrails
- Suppression and unsubscribe enforcement

### Layer 6: Reply and Conversion Ops
- Reply classification (positive, objection, later, wrong person, unsubscribe)
- Auto-next-step actions
- Calendar handoff for positive intent
- CRM stage updates and reporting

## 90-Day Execution Roadmap

### Days 1-14: Foundation
- Finalize niche, offer, and proof stack
- Upgrade lead schema and event logging
- Build source connectors for 2 channels first
- Launch scoring V2 baseline

### Days 15-30: Controlled Launch
- Launch 1 niche campaign with strict quality filtering
- Start with low volume and high personalization
- Measure source-level conversion and kill low performers fast

### Days 31-60: Scale and Optimize
- Add 2-3 additional sources
- Add sequence optimization and A/B testing
- Introduce reply classification automation
- Increase volume only when health metrics are stable

### Days 61-90: Predictable Pipeline
- Standardize weekly GTM operating rhythm
- Build campaign playbooks by source + niche
- Track closed-won attribution by source and template
- Double down on top 20% source-template combinations

## Daily and Weekly Operating Rhythm

### Daily
- Verify source ingestion health
- Review top leads in qualified queue
- Monitor sending and deliverability health
- Process positive replies and handoff quickly

### Weekly
- Review funnel metrics by source
- Remove bottom 30% campaigns/sources
- Adjust scoring weights from outcome data
- Update templates with best-performing proof hooks

## Risk Controls
- Policy-aware source handling and legal compliance
- Hard suppression controls for unsubscribed/bounced leads
- Quality checks to avoid spam-like personalization
- Monitoring and alerting for API failures and queue backlog

## Team Ownership
- Founder/BDM: ICP, offer, proof narrative, deal strategy
- Automation engineer: ingestion, queue, orchestration, integrations
- Lead ops: enrichment quality, data hygiene, suppression
- Growth marketer: messaging tests, conversion optimization

## Exit Criteria for V2 Readiness
- End-to-end flow stable for at least 2 weeks
- Reply and booking metrics above baseline targets
- Clear source-level winner channels identified
- Team runbook documented and repeatable
