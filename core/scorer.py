from typing import Any, Dict


def _clip(value: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, value))


def score_lead_v2(lead: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates V2 decomposed scoring and explainable reason codes."""
    reason_codes: list[str] = []

    website = str(lead.get("website") or "").strip().lower()
    rating = float(lead.get("rating") or 0.0)
    reviews = int(lead.get("reviews_count") or 0)
    category = str(lead.get("business_category") or lead.get("category") or "").lower()
    metadata = str(lead.get("about_us_info") or "").lower()
    email = str(lead.get("email") or "").strip().lower()

    # Fit score: service alignment and business potential.
    fit_score = 5.0
    high_value_niches = [
        "dentist", "dental", "legal", "lawyer", "attorney", "roofing",
        "hvac", "construction", "medical", "clinic", "spa", "saas",
    ]
    if any(niche in category for niche in high_value_niches):
        fit_score += 2.5
        reason_codes.append("fit_high_value_niche")
    if rating >= 4.3 and reviews >= 30:
        fit_score += 1.5
        reason_codes.append("fit_established_reputation")
    elif rating == 0 and reviews == 0:
        fit_score -= 1.0
        reason_codes.append("fit_low_reputation_signal")
    fit_score = _clip(fit_score)

    # Intent score: urgency and visible problem indicators.
    intent_score = 4.0
    if not website or website == "n/a" or "google.com" in website:
        intent_score += 3.0
        reason_codes.append("intent_missing_website")
    if "failed" in metadata or "not found" in metadata or "error" in metadata:
        intent_score += 2.0
        reason_codes.append("intent_technical_issue")
    if 0 < rating < 4.2:
        intent_score += 1.0
        reason_codes.append("intent_reputation_gap")
    intent_score = _clip(intent_score)

    # Authority score: proxy confidence that we can reach decision power.
    authority_score = 3.0
    if email and email != "n/a":
        authority_score += 3.0
        reason_codes.append("authority_direct_email")
    if lead.get("phone"):
        authority_score += 2.0
        reason_codes.append("authority_phone_available")
    authority_score = _clip(authority_score)

    # Timing score: freshness and near-term action probability proxies.
    timing_score = 5.0
    if reviews < 15:
        timing_score += 1.0
        reason_codes.append("timing_low_social_proof")
    if "new" in str(lead.get("status") or "").lower():
        timing_score += 0.5
    timing_score = _clip(timing_score)

    # Risk score: delivery and quality risk (higher means riskier).
    risk_score = 1.5
    if not email or email == "n/a":
        risk_score += 2.5
        reason_codes.append("risk_no_email")
    if not website or website == "n/a":
        risk_score += 1.0
        reason_codes.append("risk_low_context")
    risk_score = _clip(risk_score)

    priority_score = _clip(
        (0.35 * fit_score)
        + (0.35 * intent_score)
        + (0.20 * authority_score)
        + (0.10 * timing_score)
        - (0.15 * risk_score),
        1.0,
        10.0,
    )

    return {
        "fit_score": round(fit_score, 2),
        "intent_score": round(intent_score, 2),
        "authority_score": round(authority_score, 2),
        "timing_score": round(timing_score, 2),
        "risk_score": round(risk_score, 2),
        "priority_score": round(priority_score, 2),
        "reason_codes": sorted(set(reason_codes)),
    }


def score_lead(lead: Dict[str, Any]) -> int:
    """Backward-compatible score used by existing status ordering logic."""
    return int(round(score_lead_v2(lead)["priority_score"]))
