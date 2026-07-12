#!/usr/bin/env python3
"""Prioritise executive_analysis.json into Executive Decision Objects.

This is MEIP Intelligence Phase 2 Sprint 1. It turns findings, risks,
opportunities and recommended actions into ranked objects with score, urgency,
ownership, confidence, recommended visual and recommended action.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow running as `python3 intelligence/prioritisation_engine.py ...` from repo root.
sys.path.append(str(Path(__file__).parent))

from executive_object import build_executive_object, merge_action_into_object, reprioritise


SOURCE_GROUPS = ("findings", "risks", "opportunities")


def build_prioritised_objects(executive_analysis: dict[str, Any]) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    objects_by_source_id: dict[str, dict[str, Any]] = {}
    sequence = 1
    for group_name in SOURCE_GROUPS:
        for item in executive_analysis.get(group_name, []):
            obj = build_executive_object(item, sequence)
            objects.append(obj)
            objects_by_source_id[item.get("id")] = obj
            sequence += 1

    # recommended_actions are handled separately: an action derived from a
    # finding/risk (via derived_from_id) describes the same underlying issue,
    # not a new one, so it must not become a second independently-ranked
    # object -- that would let the same issue occupy two leadership-deck
    # slots at once. Fold it into its parent instead. Only an action with no
    # traceable parent (or whose parent didn't produce an object) becomes its
    # own object, so nothing is silently dropped.
    for item in executive_analysis.get("recommended_actions", []):
        parent = objects_by_source_id.get(item.get("derived_from_id"))
        if parent is not None:
            merge_action_into_object(parent, item)
            continue
        obj = build_executive_object(item, sequence)
        objects.append(obj)
        sequence += 1

    return reprioritise(objects)


def build_output(executive_analysis: dict[str, Any], source_path: Path) -> dict[str, Any]:
    objects = build_prioritised_objects(executive_analysis)
    return {
        "prioritisation_meta": {
            "source_analysis": str(source_path),
            "source_report_title": executive_analysis.get("analysis_meta", {}).get("source_report_title", "Untitled report"),
            "source_report_type": executive_analysis.get("analysis_meta", {}).get("source_report_type", "unknown"),
        },
        "top_priority": objects[0] if objects else None,
        "executive_objects": objects,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executive_analysis", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    analysis = json.loads(args.executive_analysis.read_text(encoding="utf-8"))
    output = build_output(analysis, args.executive_analysis)
    output_path = args.output or args.executive_analysis.with_name(args.executive_analysis.stem.replace("_executive_analysis", "") + "_prioritised_analysis.json")
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"PRIORITISED ANALYSIS WRITTEN — {output_path}")
    if output.get("top_priority"):
        top = output["top_priority"]
        print(f"Top priority: {top['title']} (score {top['executive_score']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
