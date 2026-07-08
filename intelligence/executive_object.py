"""Executive Decision Object builder.

An Executive Decision Object is the common payload used by the future Decision,
QA, Question, Page Planning and Learning engines. It is derived from an existing
executive_analysis item and never introduces unsupported source values.
"""
from __future__ import annotations

from typing import Any

from categories import classify
from confidence import evidence_confidence
from ownership import suggest_owner
from scoring import recommended_action, recommended_visual, score_item
from urgency import urgency_from_score


def build_executive_object(item: dict[str, Any], sequence: int) -> dict[str, Any]:
    scoring = score_item(item)
    score = scoring["total"]
    category = classify(item)
    owner = suggest_owner(item, category)

    return {
        "id": f"exec_obj_{sequence:03d}",
        "source_id": item.get("id", f"source_{sequence}"),
        "source_type": item.get("type", "finding"),
        "title": item.get("headline", "Untitled executive object"),
        "category": category,
        "executive_score": score,
        "priority": sequence,
        "urgency": urgency_from_score(score),
        "owner": owner,
        "confidence": evidence_confidence(item),
        "recommended_visual": recommended_visual(item, score),
        "recommended_action": recommended_action(item, owner, score),
        "business_impact": item.get("business_impact", ""),
        "interpretation": item.get("interpretation", ""),
        "scoring": scoring,
        "supporting_evidence": item.get("supporting_evidence", []),
    }


def reprioritise(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort objects by executive score and assign final priority numbers."""

    sorted_objects = sorted(objects, key=lambda obj: obj["executive_score"], reverse=True)
    for idx, obj in enumerate(sorted_objects, start=1):
        obj["priority"] = idx
    return sorted_objects
