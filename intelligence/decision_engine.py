#!/usr/bin/env python3
"""MEIP Decision Engine.

Consumes prioritised_analysis.json and classifies each Executive Decision Object
into a report placement tier: Page 1, Page 2, Appendix, Monitor, or Ignore.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def decide_object(obj: dict[str, Any]) -> dict[str, Any]:
    score = obj.get("executive_score", 0)
    confidence = obj.get("confidence", 0)

    if score >= 85 and confidence >= 65:
        placement = "Page 1"
        page = 1
        reason = "High score with enough evidence confidence for the main executive message."
    elif score >= 70 and confidence >= 55:
        placement = "Page 1"
        page = 1
        reason = "Material leadership item suitable for the front page."
    elif score >= 50:
        placement = "Page 2"
        page = 2
        reason = "Relevant management item, but below the front-page threshold."
    elif score >= 25:
        placement = "Monitor"
        page = None
        reason = "Track this item, but do not place it in the main report yet."
    elif score >= 10:
        placement = "Appendix"
        page = None
        reason = "Keep as supporting context."
    else:
        placement = "Ignore"
        page = None
        reason = "Below executive materiality threshold."

    if confidence < 45 and placement in {"Page 1", "Page 2"}:
        placement = "Monitor"
        page = None
        reason = "Evidence confidence is too low for report placement."

    return {
        "executive_object_id": obj.get("id", "unknown"),
        "title": obj.get("title", "Untitled"),
        "decision": placement,
        "page": page,
        "reason": reason,
        "executive_score": score,
        "confidence": confidence,
        "owner": obj.get("owner", "Executive Sponsor"),
        "urgency": obj.get("urgency", "Monitor"),
        "recommended_visual": obj.get("recommended_visual", "Executive Fact Card"),
    }


def build_decision_plan(prioritised: dict[str, Any], source_path: Path) -> dict[str, Any]:
    return {
        "decision_meta": {
            "source_prioritised_analysis": str(source_path),
            "source_report_title": prioritised.get("prioritisation_meta", {}).get("source_report_title", "Untitled report"),
            "source_report_type": prioritised.get("prioritisation_meta", {}).get("source_report_type", "unknown"),
        },
        "decisions": [decide_object(obj) for obj in prioritised.get("executive_objects", [])],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prioritised_analysis", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    prioritised = json.loads(args.prioritised_analysis.read_text(encoding="utf-8"))
    output = build_decision_plan(prioritised, args.prioritised_analysis)
    output_path = args.output or args.prioritised_analysis.with_name(
        args.prioritised_analysis.stem.replace("_prioritised_analysis", "") + "_decision_plan.json"
    )
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"DECISION PLAN WRITTEN — {output_path}")
    print(f"Decision count: {len(output['decisions'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
