from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.config import settings


@dataclass
class PromptContext:
    lead_name: str
    channel: str
    outreach_step: int
    service: str
    business_category: Optional[str]
    has_website: bool
    rating: float
    reviews_count: int
    about_us_info: Optional[str]
    audit_summary: str
    score: float


def compile_outreach_prompt(ctx: PromptContext) -> str:
    if ctx.outreach_step == 1:
        if ctx.has_website:
            goal = "Pitch a Website Redesign by highlighting issues found in the audit."
            specific_task = "- Refer specifically to the audit findings and suggest how a redesign will fix them."
        else:
            goal = "Pitch a New Website Development since the lead has no online presence."
            specific_task = "- Focus on the benefits of having a digital platform for trust and visibility."
    elif ctx.outreach_step == 2:
        goal = "Soft Follow-up: Check if they saw the previous email/audit. Keep it helpful, not pushy."
        specific_task = "- Mention you shared some thoughts a few days ago and wanted to ensure they reached the right person."
    else:
        goal = "Final Re-engagement: Offer a quick value-add or a very short 5-min chat. Last attempt."
        specific_task = "- Keep it extremely brief and ask if they are still the right person to talk to."

    if ctx.score >= 8:
        tone_strategy = "RESCUE" if ctx.rating < 3.5 else "SCALE"
    else:
        tone_strategy = "STANDARD"

    return f"""
[ROLE] {settings.SENDER_NAME}, Founder at Pixartual.
[GOAL] {goal}
[SERVICE] {ctx.service}
[STRATEGY] {tone_strategy}
[DNA] {settings.SENDER_TAGLINE}
[TASK] {specific_task}

[CONTEXT]
- Target Business: {ctx.lead_name}
- Industry: {ctx.business_category or 'Local Business'}
- Social Proof: {ctx.rating}/5 Stars ({ctx.reviews_count} Reviews)
- Site Crawl: {ctx.about_us_info[:300] if ctx.about_us_info else 'No crawl data'}
- Audit Findings: {ctx.audit_summary}

[SYSTEM INSTRUCTIONS]
1. SALUTATION: Start with "Dear {ctx.lead_name},".
2. SERVICE MENTION: Explicitly mention "{ctx.service}".
3. PERSUASIVE HOOK: Use one specific observation from context.
4. NO FLUFF: Avoid generic opening lines.
5. CHANNEL ADAPTATION: {'[EMAIL] Subject + body' if ctx.channel == 'email' else '[WHATSAPP] short body'}.

[CONSTRAINTS]
- NO PLACEHOLDERS.
- PLAIN TEXT ONLY.
- EMAIL signature required, WhatsApp signature forbidden.
"""
