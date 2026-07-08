"""Executive scoring model for MEIP Phase 2.

Scoring is deterministic and produces a 0-100 executive importance score. It is
not a financial calculation; it is a prioritisation model that helps MEIP decide
what deserves leadership attention first.
"""
from __future__ import annotations

from typing import Any

from confidence import evidence_confidence, evidence_score_component


EXECUTIVE_KPI_TERMS = ("otd", "on time", "sla", "target", "cancellation", "revenue", "sales", "margin")
CUSTOMER_TERMS = ("customer", "promise", "delivery", "late", "complaint", "refund")
FINANCIAL_TERMS = ("revenue", "sales", "margin", "cost", "refund", "cancellation")
CONCENTRATION_TERMS = ("drives", "contributes", "largest", "% of", "peak", "concentration")
EXTERNAL_EVENT_TERMS = ("strike", "weather", "public holiday", "external", "event")
TARGET_TERMS = ("below target", "unfavorable", "failure", "miss", "below", "late")


def _text(item: dict[str, Any]) -> str:
    return " ".join(
        str(item.get(key, ""))
        for key in ("headline", "interpretation", "business_impact", "id", "type")
    ).lower()


def score_item(item: dict[str, Any]) -> dict[str, int]:
    text = _text(item)
    confidence = evidence_confidence(item)

    kpi_threshold = 30 if any(term in text for term in TARGET_TERMS) else 0
    customer_impact = 20 if any(term in text for term in CUSTOMER_TERMS) else 0
    financial_impact = 15 if any(term in text for term in FINANCIAL_TERMS) else 0
    executive_interest = 10 if any(term in text for term in EXECUTIVE_KPI_TERMS) else 3
    trend_or_concentration = 10 if any(term in text for term in CONCENTRATION_TERMS) else 0
    external_event = 5 if any(term in text for term in EXTERNAL_EVENT_TERMS) else 0
    evidence_component = evidence_score_component(confidence)

    total = min(
        100,
        kpi_threshold
        + customer_impact
        + financial_impact
        + executive_interest
        + trend_or_concentration
        + external_event
        + evidence_component,
    )

    return {
        "kpi_threshold": kpi_threshold,
        "customer_impact": customer_impact,
        "financial_impact": financial_impact,
        "executive_interest": executive_interest,
        "trend_or_concentration": trend_or_concentration,
        "external_event": external_event,
        "evidence_confidence": evidence_component,
        "total": total,
    }


def recommended_visual(item: dict[str, Any], score: int) -> str:
    text = _text(item)
    if score >= 85 and any(term in text for term in ("target", "otd", "sla")):
        return "Hero KPI"
    if any(term in text for term in ("drives", "%", "contributes", "largest")):
        return "Driver Breakdown"
    if any(term in text for term in ("peak", "trend", "day", "week")):
        return "Trend / Bar Chart"
    if item.get("type") == "risk":
        return "Risk Callout"
    return "Executive Fact Card"


def recommended_action(item: dict[str, Any], owner: str, score: int) -> str:
    if score >= 85:
        return f"Assign {owner} owner immediately, confirm root cause, and track recovery in the next reporting cycle."
    if score >= 70:
        return f"Assign {owner} owner this week and confirm whether the issue is recurring or isolated."
    if score >= 50:
        return f"Monitor with {owner} and escalate only if repeated in the next cycle."
    return "Keep as supporting context unless leadership requests detail."
