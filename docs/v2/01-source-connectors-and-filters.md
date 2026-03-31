# V2 Source Connectors and Qualification Filters

## Purpose
Collect better leads, not more noise. Every source connector must emit structured, comparable lead records with intent evidence.

## Universal Lead Record Contract
Each source module should output:
- source_platform
- source_url
- discovered_at
- company_name or person_name
- role (if available)
- website
- email or contact handle
- location
- category/industry
- intent_text (raw snippet)
- intent_keywords_detected
- fit_signals
- authority_signals
- confidence_score

## Priority Sources (Build Order)

### 1) High Intent Sources (Build first)
- Upwork and Fiverr job demand capture
- Reddit posts where businesses ask for help
- LinkedIn posts signaling hiring or growth pain

### 2) Medium Intent Sources
- X and Threads posts with service-seeking language
- Niche directories and local professional listings

### 3) Lower Intent Sources
- Generic maps scraping and broad web crawl
- Use only after strict filters and enrichment

## Source-Specific Query Blueprints

### LinkedIn
- Founder OR Owner OR Marketing Head + niche keyword + growth problem
- Signals:
  - hiring designers/marketers/developers
  - launch announcements
  - conversion complaints

### Reddit
- Subreddits where operators ask for help
- Query terms:
  - "need website redesign"
  - "marketing agency recommendation"
  - "conversion issue"
  - "bookings dropped"

### X/Threads
- Real-time intent phrases:
  - "looking for agency"
  - "need branding help"
  - "developer recommendation"

### Upwork/Fiverr
- Job title + budget + urgency
- Extract:
  - budget tier
  - deadline urgency
  - service type
  - response window

## Qualification Filters (Global)

### Must-Pass Filters
- Contact confidence >= threshold
- Service match to Pixartual core offerings
- Evidence of ability to pay
- No duplicate in active or suppression list

### Exclusion Filters
- Student/academic/non-commercial requests
- Very low budget signals
- Non-serviceable geo or irrelevant category
- Anonymous/no follow-up path

## Scoring Model V2

### Fit Score (0-10)
- Niche relevance
- Business maturity
- Budget and footprint indicators

### Intent Score (0-10)
- Direct demand language
- Time sensitivity
- Problem clarity

### Authority Score (0-10)
- Decision maker role confidence
- Role seniority
- Ownership signals

### Timing Score (0-10)
- Current campaign/event context
- Active hiring/launch windows
- Freshness of signal

### Priority Score Formula
Priority Score = 0.35 * Fit + 0.35 * Intent + 0.2 * Authority + 0.1 * Timing

Queue rules:
- >= 8.0: Immediate outreach
- 6.0 to 7.9: Enrich then outreach
- < 6.0: Nurture or archive

## Data Hygiene Standards
- Normalize domains and company names
- Deduplicate by domain + company + source fingerprint
- Track every rejection reason for model tuning
- Store original intent snippets for auditability

## Anti-Spam and Brand Protection Rules
- Never send if personalization quality is low
- Never send if contact confidence is weak
- Never exceed per-inbox safe limits
- Always honor unsubscribe and suppression across all campaigns
