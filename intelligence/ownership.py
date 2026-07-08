"""Suggest likely business ownership for executive decision objects."""
from __future__ import annotations

from typing import Any


OWNERS = {
    "operations": "Regional Operations",
    "digital_ops": "Digital Operations",
    "final_mile": "Final Mile / Courier Management",
    "commercial": "Commercial",
    "finance": "Finance",
    "hr": "People / HR",
    "it": "Technology / IT",
    "executive": "Executive Sponsor",
}


def suggest_owner(item: dict[str, Any], category: str) -> str:
    text = " ".join(
        str(item.get(key, ""))
        for key in ("headline", "interpretation", "business_impact", "id")
    ).lower()

    if any(word in text for word in ("courier", "driver", "delivery", "wumdrop", "dpd", "ram", "tcg", "value")):
        return OWNERS["final_mile"]
    if any(word in text for word in ("system", "downtime", "app", "scanner", "technology")):
        return OWNERS["it"]
    if any(word in text for word in ("sales", "margin", "commercial", "range", "stock")):
        return OWNERS["commercial"]
    if any(word in text for word in ("revenue", "cost", "refund", "finance")):
        return OWNERS["finance"]
    if any(word in text for word in ("people", "staff", "labour", "training", "hr")):
        return OWNERS["hr"]
    if category in {"Operations", "Performance", "Customer", "Risk"}:
        return OWNERS["operations"]
    return OWNERS["executive"]
