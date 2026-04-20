import re
from typing import Any, Dict, List


_PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]+\}|\[SERVICE\]|\[GOAL\]|\[CONTEXT\]", re.IGNORECASE)
_GENERIC_OPENERS = (
    "i hope this email finds you well",
    "just checking in",
    "dear sir or madam",
)


def evaluate_message_quality(
    *,
    lead_name: str,
    subject: str | None,
    body: str,
    channel: str,
) -> Dict[str, Any]:
    reasons: List[str] = []
    score = 100.0

    content = (body or "").strip()
    content_l = content.lower()

    if not content:
        reasons.append("empty_body")
        score = 0.0
    else:
        if _PLACEHOLDER_PATTERN.search(content):
            reasons.append("placeholder_tokens_found")
            score -= 50

        if any(opener in content_l for opener in _GENERIC_OPENERS):
            reasons.append("generic_opener")
            score -= 10

        if lead_name and lead_name.lower() not in content_l:
            reasons.append("missing_lead_reference")
            score -= 15

        word_count = len(content.split())
        if channel == "whatsapp":
            if word_count > 80:
                reasons.append("whatsapp_too_long")
                score -= 20
            if "warm regards" in content_l:
                reasons.append("whatsapp_signature_present")
                score -= 20
        else:
            if word_count < 40:
                reasons.append("email_too_short")
                score -= 10
            if subject is None or len(subject.strip()) < 4:
                reasons.append("weak_subject")
                score -= 15

    score = max(0.0, min(100.0, score))
    passed = score >= 65 and not any(
        r in reasons for r in ("empty_body", "placeholder_tokens_found")
    )

    return {
        "passed": passed,
        "quality_score": round(score, 2),
        "reasons": reasons,
    }
