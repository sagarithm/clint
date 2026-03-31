# V2 AI Prompt and Personalization Specification

## Objective
Generate high-relevance outreach messages that feel human, source-aware, and outcome-focused.

## Prompt Architecture

### System Layer
- Persona: Founder-level advisor with domain authority
- Tone: direct, professional, helpful, non-generic
- Constraint: no placeholders, no fabricated claims

### Campaign Layer
- Niche context
- Offer and desired business outcome
- Proof snippet set from Pixartual assets
- Channel constraints (email, DM, platform response)

### Lead Layer
- Source platform and intent snippet
- Business context (industry, size hints, maturity)
- Current friction point from enrichment and audit
- CTA style based on stage and signal strength

## Personalization Blocks
- Block A: specific observation from source signal
- Block B: relevant proof statement
- Block C: one clear value proposition
- Block D: friction-light CTA

## Quality Gate Rules
A generated message must pass:
- Relevance score threshold
- No placeholder tokens
- No repetition or generic openers
- Correct channel length and style
- Claim verification against proof library

## Fallback Strategy
- If score below threshold, regenerate once with stricter constraints
- If still low quality, route to human review queue
- If missing lead context, request enrichment before generation

## Template Families
- Intro outreach (high intent)
- Intro outreach (medium intent)
- Follow-up reminder
- Objection response
- Wrong-person referral ask
- Final close-loop note

## A/B Testing Variables
- Opening line style
- Proof placement
- CTA wording
- Subject format
- Length profile

## Logging and Explainability
Store for each generated message:
- prompt version
- template id
- personalization score
- selected proof id
- generation timestamp

## Risk Controls
- Do not use manipulative or deceptive claims
- Avoid irrelevant urgency framing
- Never mention data that is not in lead context
- Keep tone respectful and non-invasive
