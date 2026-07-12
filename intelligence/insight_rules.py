"""Deterministic MEIP insight rules.

These rules are intentionally conservative. They only use values already present
in a validated report_brief.json and every generated statement carries evidence
refs back to the originating brief.
"""
from __future__ import annotations

from typing import Any

from extractors import Evidence, iter_bar_charts, iter_breakdowns, iter_kpis, numeric, pct


def _insight(
    *,
    insight_id: str,
    insight_type: str,
    priority: int,
    headline: str,
    interpretation: str,
    business_impact: str,
    evidence: list[Evidence],
    confidence: str = "high",
    magnitude_pct: float | None = None,
    derived_from_id: str | None = None,
) -> dict[str, Any]:
    insight = {
        "id": insight_id,
        "type": insight_type,
        "priority": priority,
        "headline": headline,
        "interpretation": interpretation,
        "business_impact": business_impact,
        "confidence": confidence,
        "supporting_evidence": [e.as_dict() for e in evidence],
    }
    # magnitude_pct is only set when a rule has a real computed severity signal
    # (a target deviation, a concentration share, a peak share) -- it is never
    # guessed, so scoring.py must treat a missing value as "no signal", not zero.
    if magnitude_pct is not None:
        insight["magnitude_pct"] = round(magnitude_pct, 2)
    if derived_from_id is not None:
        insight["derived_from_id"] = derived_from_id
    return insight


def _scope_from_title(title: str, max_len: int = 20) -> str | None:
    """Extract a short entity/scope prefix from a section title that follows
    the 'Scope — Descriptor' convention (e.g. 'Western Cape — Region
    Overview' -> 'Western Cape'). Returns None when the title doesn't follow
    that convention or the segment is too long to be a clean scope label --
    callers must not use this speculatively, only to disambiguate a real,
    already-detected headline collision (see detect_target_misses)."""

    if " — " not in title:
        return None
    scope = title.split(" — ", 1)[0].strip()
    if not scope or len(scope) > max_len:
        return None
    return scope


def detect_target_misses(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag KPIs where the reported direction is explicitly unfavorable.

    The existing report schema already carries direction. This rule does not
    infer target logic unless the source brief has encoded it.
    """

    built: list[dict[str, Any]] = []
    fingerprints: dict[tuple, dict[str, Any]] = {}

    for section, kpi, idx in iter_kpis(doc):
        if kpi.get("direction") != "unfavorable":
            continue
        ev = Evidence(
            data_ref=f"sections[{section['_index']}].kpis[{idx}].value",
            label=kpi.get("label", kpi.get("id", "KPI")),
            value=kpi.get("value"),
            unit=kpi.get("unit", ""),
        )
        comparison = ""
        magnitude_pct = None
        if "comparison_value" in kpi:
            comparison = f" compared with {kpi.get('comparison_label', 'comparison')} {kpi['comparison_value']}{kpi.get('comparison_unit', '')}"
            comparison_raw = kpi.get("comparison_value")
            if isinstance(comparison_raw, str) and "%" in comparison_raw:
                # comparison_value is already expressed as a delta percentage
                # (e.g. "+8.5%" vs a prior period) -- that percentage *is* the
                # magnitude. Diffing it against `value` would compare mismatched
                # units (e.g. an order count against a percentage) and produce a
                # number that looks precise but means nothing.
                delta_pct = numeric(comparison_raw)
                if delta_pct is not None:
                    magnitude_pct = min(abs(delta_pct), 100)
            else:
                actual = numeric(kpi.get("value"))
                baseline = numeric(comparison_raw)
                if actual is not None and baseline not in (None, 0):
                    magnitude_pct = min(abs(actual - baseline) / abs(baseline) * 100, 100)

        # Two sections sometimes restate the exact same KPI -- e.g. a headline
        # number repeated on both a dashboard page and a deep-dive page for a
        # different audience. That's the same fact, not a new one, so fold
        # this section's evidence into the finding already recorded for it
        # instead of creating a second object that competes with it for
        # placement.
        fingerprint = (
            kpi.get("label"), kpi.get("value"), kpi.get("unit"),
            kpi.get("comparison_label"), kpi.get("comparison_value"), kpi.get("comparison_unit"),
        )
        if fingerprint in fingerprints:
            fingerprints[fingerprint]["insight"]["supporting_evidence"].append(ev.as_dict())
            continue

        insight = _insight(
            insight_id=f"kpi_unfavorable_{kpi.get('id', idx)}",
            insight_type="finding",
            priority=1,
            headline=f"{ev.label} is unfavorable",
            interpretation=f"{ev.label} reported {ev.value}{ev.unit}{comparison}, and is marked unfavorable in the validated brief.",
            business_impact="Leadership should treat this as a performance exception requiring explanation, ownership and recovery tracking.",
            evidence=[ev],
            magnitude_pct=magnitude_pct,
        )
        entry = {"insight": insight, "kpi": kpi, "section": section}
        fingerprints[fingerprint] = entry
        built.append(entry)

    # A KPI's own label is often only unambiguous in the context of the page
    # it's rendered on (e.g. "Region Margin" under a "Western Cape" page
    # header) -- flattened into one global executive list, identical
    # headlines from genuinely different findings become impossible to tell
    # apart. Only disambiguate when a real collision exists in the output,
    # and only with information that actually differs across the colliding
    # group -- never a scope guessed and applied to every finding regardless
    # of whether it was ever actually ambiguous.
    by_headline: dict[str, list[dict[str, Any]]] = {}
    for entry in built:
        by_headline.setdefault(entry["insight"]["headline"], []).append(entry)

    for headline, group in by_headline.items():
        if len(group) < 2:
            continue
        comparison_labels = [e["kpi"].get("comparison_label") for e in group]
        if all(comparison_labels) and len(set(comparison_labels)) == len(group):
            for e, cl in zip(group, comparison_labels):
                e["insight"]["headline"] = f"{headline} ({cl})"
            continue
        scopes = [_scope_from_title(e["section"].get("title", "")) for e in group]
        if all(scopes) and len(set(scopes)) == len(group):
            for e, scope in zip(group, scopes):
                e["insight"]["headline"] = f"{scope} {headline}"

    return [e["insight"] for e in built]


def detect_concentration(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify where one component carries a disproportionate share of a total."""

    insights: list[dict[str, Any]] = []
    for section in iter_breakdowns(doc):
        bd = section["breakdown"]
        if bd.get("mode", "share") != "share":
            continue
        total = numeric(bd["parent_total"]["value"])
        if total is None or total <= 0:
            continue
        components = bd.get("components", [])
        if not components:
            continue
        top_idx, top_component = max(enumerate(components), key=lambda item: item[1].get("value", 0))
        top_value = numeric(top_component.get("value"))
        if top_value is None:
            continue
        share = pct(top_value, total)
        if share is None or share < 35:
            continue
        ev_top = Evidence(
            data_ref=f"sections[{section['_index']}].breakdown.components[{top_idx}].value",
            label=top_component.get("label", "Top component"),
            value=top_component.get("value"),
            unit=bd.get("unit", ""),
        )
        ev_total = Evidence(
            data_ref=f"sections[{section['_index']}].breakdown.parent_total.value",
            label=bd["parent_total"].get("label", "Total"),
            value=bd["parent_total"].get("value"),
            unit=bd.get("unit", ""),
        )
        priority = 1 if share >= 50 else 2
        insights.append(
            _insight(
                insight_id=f"concentration_{bd.get('id', section['id'])}_{top_idx}",
                insight_type="finding",
                priority=priority,
                headline=f"{ev_top.label} drives {share:.2f}% of {bd.get('title', 'the total')}",
                interpretation=f"{ev_top.label} contributes {top_value:g} of {total:g} {bd.get('unit', '').strip()}, making it the largest driver in this breakdown.",
                business_impact="A concentrated driver is easier to target, but it also creates risk if recovery actions do not directly address that area.",
                evidence=[ev_top, ev_total],
                magnitude_pct=share,
            )
        )
    return insights


def detect_peak_bars(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify the highest bar in bar-chart sections."""

    insights: list[dict[str, Any]] = []
    for section in iter_bar_charts(doc):
        chart = section["bar_chart"]
        values = chart.get("values", [])
        categories = chart.get("categories", [])
        if not values or len(values) != len(categories):
            continue
        max_idx = max(range(len(values)), key=lambda i: values[i])
        # "Share of total" only means something when every bar is a magnitude
        # (e.g. daily order counts). For a mixed-sign chart (e.g. variance vs
        # plan), the total can be near zero or negative, which turns "share"
        # into a meaningless, sometimes wildly out-of-range number (a real
        # instance produced -412%) -- so it's only computed for non-negative
        # charts, and treated as no signal (not fabricated) otherwise.
        has_negative = any(isinstance(v, (int, float)) and v < 0 for v in values)
        total = sum(v for v in values if isinstance(v, (int, float)))
        if not has_negative and not total:
            continue
        share = pct(values[max_idx], total) if not has_negative and total else None
        ev = Evidence(
            data_ref=f"sections[{section['_index']}].bar_chart.values[{max_idx}]",
            label=categories[max_idx],
            value=values[max_idx],
            unit=chart.get("unit", ""),
        )
        detail = f", representing {share:.2f}% of the chart total" if share is not None else ""
        insights.append(
            _insight(
                insight_id=f"peak_{chart.get('id', section['id'])}_{max_idx}",
                insight_type="finding",
                priority=2 if (share or 0) >= 35 else 3,
                headline=f"{categories[max_idx]} is the peak point in {chart.get('title', 'the chart')}",
                interpretation=f"{categories[max_idx]} is the highest point at {values[max_idx]:g}{chart.get('unit', '')}{detail}.",
                business_impact="Leadership should test whether the peak is event-driven, operationally driven, or an early signal of a repeatable trend.",
                evidence=[ev],
                magnitude_pct=share,
            )
        )
    return insights


def detect_external_event_risks(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert validated external events into executive risk statements."""

    insights: list[dict[str, Any]] = []
    for section in doc.get("sections", []):
        for event_idx, event in enumerate(section.get("external_events", [])):
            evidence = []
            for ref_idx, ref in enumerate(event.get("linked_data_refs", [])):
                evidence.append(
                    Evidence(
                        data_ref=ref,
                        label=f"{event.get('name', 'External event')} linked value {ref_idx + 1}",
                        value=None,
                    )
                )
            if not evidence:
                continue
            insights.append(
                _insight(
                    insight_id=f"external_event_{section.get('id', 'section')}_{event_idx}",
                    insight_type="risk",
                    priority=2,
                    headline=f"{event.get('name')} is linked to report performance",
                    interpretation=event.get("description", "The event is linked to validated report data."),
                    business_impact="External events can explain performance movement, but leadership still needs recovery tracking to confirm the issue has normalised.",
                    evidence=evidence,
                    confidence="medium",
                )
            )
    return insights


def build_action_recommendations(findings: list[dict[str, Any]], risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create action prompts grounded in existing finding/risk evidence."""

    actions: list[dict[str, Any]] = []
    source_items = sorted(findings + risks, key=lambda item: item["priority"])[:3]
    for idx, item in enumerate(source_items, start=1):
        action = {
            "id": f"action_{idx}_{item['id']}",
            "type": "action",
            "priority": min(item["priority"], 3),
            "headline": f"Assign owner and recovery check for: {item['headline']}",
            "interpretation": "The issue is material enough to be surfaced in the executive pack and should not remain a passive observation.",
            "business_impact": "A named owner, date-bound recovery check and next-cycle measurement prevents the same issue from repeating without accountability.",
            "confidence": item.get("confidence", "medium"),
            "supporting_evidence": item.get("supporting_evidence", []),
            # Explicit lineage: this action is about the finding/risk it was built
            # from, not a new independent fact -- prioritisation_engine.py uses
            # this to fold the action into its parent's decision object instead
            # of letting the same underlying issue compete twice for placement.
            "derived_from_id": item["id"],
        }
        if item.get("magnitude_pct") is not None:
            action["magnitude_pct"] = item["magnitude_pct"]
        actions.append(action)
    return actions


def run_rules(doc: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    findings = []
    findings.extend(detect_target_misses(doc))
    findings.extend(detect_concentration(doc))
    findings.extend(detect_peak_bars(doc))

    risks = detect_external_event_risks(doc)
    opportunities: list[dict[str, Any]] = []
    actions = build_action_recommendations(findings, risks)

    return {
        "findings": sorted(findings, key=lambda item: item["priority"]),
        "risks": sorted(risks, key=lambda item: item["priority"]),
        "opportunities": opportunities,
        "recommended_actions": sorted(actions, key=lambda item: item["priority"]),
    }
