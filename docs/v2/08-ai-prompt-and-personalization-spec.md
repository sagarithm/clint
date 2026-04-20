# V2 Prompt and Personalization Spec

## Objective
Compile context-aware, proof-backed outreach drafts with measurable quality and
explicit safety checks.

## Prompt Compiler Layers

### Layer 1: System Policy
- Brand voice and response tone constraints.
- Non-fabrication and no-placeholder enforcement.
- Channel-specific structural constraints.

### Layer 2: Campaign Policy
- ICP definition and offer framing.
- Approved proof snippets and claim boundaries.
- Stage-aware CTA policy.

### Layer 3: Lead Evidence
- Source context and intent evidence.
- Enrichment-derived friction hypothesis.
- Risk flags and confidence indicators.

## Draft Composition Blocks
- Observation block.
- Outcome/value block.
- Proof block.
- CTA block.

## Quality Gate Scoring
- relevance_score
- personalization_score
- clarity_score
- claim_safety_score
- channel_fit_score

A draft is eligible for send only if all mandatory thresholds pass.

## Fallback Policy
1. Regenerate with stricter constraints once.
2. If still below threshold, route to approval queue.
3. If context quality is insufficient, request re-enrichment.

## Logging Requirements
For every generated draft, store:
- prompt_version
- template_id
- selected_proof_id
- quality_scores_json
- rejection_reason_if_any
- correlation_id
