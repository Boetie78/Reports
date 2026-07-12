"""Executive category classification for MEIP Phase 2."""
from __future__ import annotations

from typing import Any


CATEGORIES = {
    "performance": "Performance",
    "risk": "Risk",
    "opportunity": "Opportunity",
    "customer": "Customer",
    "commercial": "Commercial",
    "financial": "Financial",
    "operations": "Operations",
    "people": "People",
    "compliance": "Compliance",
    "technology": "Technology",
    "external_event": "External Event",
}


def classify(item: dict[str, Any]) -> str:
    """Classify an analysis item into an executive bucket.

    This is deterministic and keyword-based for v1. Report profiles can override
    the category later.
    """

    text = " ".join(
        str(item.get(key, ""))
        for key in ("headline", "interpretation", "business_impact", "id", "type")
    ).lower()

    if any(word in text for word in ("customer", "promise", "complaint", "delivery")):
        return CATEGORIES["customer"]
    if any(word in text for word in ("revenue", "sales", "margin", "cost", "refund", "cancellation")):
        return CATEGORIES["financial"]
    if any(word in text for word in ("strike", "weather", "public holiday", "event")):
        return CATEGORIES["external_event"]
    if any(word in text for word in ("system", "technology", "downtime", "app", "scan")):
        return CATEGORIES["technology"]
    if item.get("type") == "risk":
        return CATEGORIES["risk"]
    if item.get("type") == "opportunity":
        return CATEGORIES["opportunity"]
    if any(word in text for word in ("courier", "store", "driver", "picking", "staging", "dispatch")):
        return CATEGORIES["operations"]
    return CATEGORIES["performance"]
