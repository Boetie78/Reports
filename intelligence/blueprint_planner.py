"""Plan what should appear in the executive report.

The planner does not draw anything. It ranks existing sections from the validated
brief and explains why they belong in the presentation. Rendering remains the
responsibility of pipeline/render.py.
"""
from __future__ import annotations

from typing import Any


EXECUTIVE_PRIORITY = {
    "executive_summary": 1,
    "kpi_strip": 1,
    "executive_facts": 2,
    "breakdown_table": 2,
    "bar_chart": 2,
    "time_series_chart": 2,
    "ranking": 3,
    "external_events": 3,
    "bottom_insight": 1,
    "custom_html": 4,
    "waterfall": 3,
}


def _reason_for_section(section: dict[str, Any]) -> str:
    section_type = section.get("type", "section")
    title = section.get("title") or section.get("id", section_type)
    if section_type == "executive_summary":
        return "Sets the leadership message and frames the report before detail."
    if section_type == "kpi_strip":
        return "Shows the core performance indicators leadership will anchor on."
    if section_type == "executive_facts":
        return "Surfaces interpreted facts that should drive discussion and decisions."
    if section_type == "breakdown_table":
        return f"Explains the composition of {title} and helps identify the largest drivers."
    if section_type == "bar_chart":
        return f"Provides a fast visual view of where {title} peaks or concentrates."
    if section_type == "time_series_chart":
        return f"Shows movement over time and whether the issue is isolated or recurring."
    if section_type == "ranking":
        return "Ranks the highest-impact contributors so actions can be targeted."
    if section_type == "external_events":
        return "Documents external context that may explain performance movement."
    if section_type == "bottom_insight":
        return "Closes the page with the most important executive takeaway."
    return "Included because it is present in the validated report brief."


def _preferred_width(section: dict[str, Any]) -> str:
    section_type = section.get("type")
    if section_type in {"executive_summary", "kpi_strip", "bottom_insight"}:
        return "full"
    return section.get("layout_width", "half")


def build_presentation_plan(doc: dict[str, Any], analysis: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a prioritized render plan for existing report sections."""

    plan = []
    referenced_section_ids = set()
    high_priority_terms = set()

    for item in analysis.get("findings", [])[:3] + analysis.get("risks", [])[:2]:
        for ev in item.get("supporting_evidence", []):
            ref = ev.get("data_ref", "")
            if ref.startswith("sections["):
                high_priority_terms.add(ref.split("]", 1)[0] + "]")

    for idx, section in enumerate(doc.get("sections", [])):
        section_id = section.get("id", f"section_{idx}")
        section_ref = f"sections[{idx}]"
        section_priority = EXECUTIVE_PRIORITY.get(section.get("type"), 4)
        if section_ref in high_priority_terms:
            section_priority = min(section_priority, 1)
        if section_id in referenced_section_ids:
            continue
        referenced_section_ids.add(section_id)
        plan.append(
            {
                "section_id": section_id,
                "reason": _reason_for_section(section),
                "priority": section_priority,
                "preferred_width": _preferred_width(section),
            }
        )

    return sorted(plan, key=lambda item: item["priority"])
