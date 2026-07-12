#!/usr/bin/env python3
"""Generate MEIP executive_analysis.json from a validated report_brief.json.

This is the first version of the Executive Intelligence Engine. It does not
extract raw files and it does not render. It sits after pipeline/validate.py and
before blueprint/render, turning validated report facts into prioritized
findings, risks, actions and a presentation plan.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow running as `python3 intelligence/analyse.py ...` from repo root.
sys.path.append(str(Path(__file__).parent))

from blueprint_planner import build_presentation_plan
from extractors import Evidence, with_section_indexes
from insight_rules import run_rules


def _collect_source_values(analysis_parts: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    seen = set()
    values: list[dict[str, Any]] = []
    for group in analysis_parts.values():
        for item in group:
            for ev in item.get("supporting_evidence", []):
                key = ev.get("data_ref")
                if key in seen:
                    continue
                seen.add(key)
                values.append(ev)
    return values


def _primary_message(doc: dict[str, Any], findings: list[dict[str, Any]], risks: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = sorted(findings + risks, key=lambda item: item["priority"])
    if candidates:
        top = candidates[0]
        return {
            "headline": top["headline"],
            "summary": top["interpretation"],
            "confidence": top.get("confidence", "medium"),
            "supporting_evidence": top.get("supporting_evidence", []),
        }

    # Conservative fallback: use the first KPI value as the anchor if no rule fired.
    for idx, section in enumerate(doc.get("sections", [])):
        if section.get("type") == "kpi_strip" and section.get("kpis"):
            kpi = section["kpis"][0]
            ev = Evidence(
                data_ref=f"sections[{idx}].kpis[0].value",
                label=kpi.get("label", "Primary KPI"),
                value=kpi.get("value"),
                unit=kpi.get("unit", ""),
            ).as_dict()
            return {
                "headline": f"{ev['label']} is the primary executive anchor",
                "summary": "No deterministic exception rule fired. Use the validated KPI set as the leadership anchor and review source context before adding interpretation.",
                "confidence": "low",
                "supporting_evidence": [ev],
            }

    return {
        "headline": "No executive message generated",
        "summary": "The validated brief does not contain enough structured KPI or driver data for the current deterministic rules.",
        "confidence": "low",
        "supporting_evidence": [
            {
                "data_ref": "report_meta.title",
                "label": "Report title",
                "value": doc.get("report_meta", {}).get("title", "Unknown report"),
            }
        ],
    }


def build_executive_analysis(doc: dict[str, Any], source_path: Path) -> dict[str, Any]:
    doc = with_section_indexes(doc)
    parts = run_rules(doc)
    primary = _primary_message(doc, parts["findings"], parts["risks"])
    source_values = _collect_source_values(parts)
    for ev in primary.get("supporting_evidence", []):
        if ev.get("data_ref") not in {item.get("data_ref") for item in source_values}:
            source_values.append(ev)

    analysis = {
        "analysis_meta": {
            "source_report_title": doc.get("report_meta", {}).get("title", "Untitled report"),
            "source_report_type": doc.get("report_meta", {}).get("report_type", "unknown"),
            "generated_from": str(source_path),
        },
        "primary_message": primary,
        "findings": parts["findings"],
        "risks": parts["risks"],
        "opportunities": parts["opportunities"],
        "recommended_actions": parts["recommended_actions"],
        "presentation_plan": [],
        "source_values_used": source_values,
    }
    analysis["presentation_plan"] = build_presentation_plan(doc, analysis)
    return analysis


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_brief", type=Path, help="Validated report_brief.json")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Where to write executive_analysis.json. Defaults to output/<brief-stem>_executive_analysis.json",
    )
    args = parser.parse_args()

    doc = json.loads(args.report_brief.read_text(encoding="utf-8"))
    analysis = build_executive_analysis(doc, args.report_brief)

    output_path = args.output or Path("output") / f"{args.report_brief.stem}_executive_analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"EXECUTIVE ANALYSIS WRITTEN — {output_path}")
    print(f"Primary message: {analysis['primary_message']['headline']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
