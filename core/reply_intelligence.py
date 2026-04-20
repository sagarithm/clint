from __future__ import annotations

from typing import Any, Dict


def classify_reply(reply_text: str) -> Dict[str, Any]:
    text = (reply_text or "").strip().lower()
    if not text:
        return {
            "label": "unknown",
            "confidence": 0.2,
            "requires_human_review": True,
            "next_action": "human_review",
        }

    positive_markers = ["yes", "interested", "let's talk", "book", "call", "meeting"]
    negative_markers = ["not interested", "stop", "remove", "unsubscribe", "no thanks"]
    neutral_markers = ["later", "busy", "next month", "follow up", "maybe"]

    if any(marker in text for marker in negative_markers):
        label = "replied_negative"
        confidence = 0.9
        next_action = "suppress_or_close"
    elif any(marker in text for marker in positive_markers):
        label = "replied_positive"
        confidence = 0.85
        next_action = "book_or_handoff"
    elif any(marker in text for marker in neutral_markers):
        label = "replied_neutral"
        confidence = 0.75
        next_action = "schedule_follow_up"
    else:
        label = "unknown"
        confidence = 0.45
        next_action = "human_review"

    requires_human_review = confidence < 0.7
    return {
        "label": label,
        "confidence": confidence,
        "requires_human_review": requires_human_review,
        "next_action": next_action,
    }
