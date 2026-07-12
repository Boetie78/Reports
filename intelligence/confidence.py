"""Confidence scoring for MEIP executive decision objects."""
from __future__ import annotations

from typing import Any


def evidence_confidence(item: dict[str, Any]) -> int:
    """Return 0-100 confidence from evidence structure.

    This is deliberately conservative. Stronger future versions can incorporate
    source quality, contradictions and multi-source agreement.
    """

    evidence = item.get("supporting_evidence", [])
    if not evidence:
        return 20

    score = 45
    score += min(len(evidence) * 12, 36)

    refs = [ev.get("data_ref") for ev in evidence if ev.get("data_ref")]
    if refs:
        score += 10
    if len(set(refs)) == len(refs):
        score += 5
    if all(ev.get("value") is not None for ev in evidence):
        score += 4

    confidence_label = item.get("confidence")
    if confidence_label == "high":
        score += 5
    elif confidence_label == "low":
        score -= 15

    return max(0, min(100, score))


def evidence_score_component(confidence: int) -> int:
    """Map 0-100 confidence to the scoring model's 0-10 evidence component."""

    return round(confidence / 10)
