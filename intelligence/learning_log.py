#!/usr/bin/env python3
"""MEIP Learning Log -- record a human decision about a generated report element.

Implements MEIP_MASTER_CONTEXT.md Product Principle 5: "each report should
improve future MEIP rules, templates, validation gates, or intelligence
patterns." This is deliberately a human-in-the-loop log, not an automatic
self-tuning system -- AGENTS.md requires human review before any change, so
nothing in this repo should silently adjust its own thresholds based on
accumulated data. This tool only records what a human observed; a human
still decides what to do about it (see intelligence/learning_report.py,
which aggregates these records into a pattern summary for a human to act on).

Five decision types:
  accepted   -- the generated element was correct and used as-is
  challenged -- the generated element was materially wrong, misleading, or
                had to be substantially rewritten before use
  effective  -- (retrospective, usually logged in a later cycle) a prior
                accepted element's recommended action measurably helped
  failed     -- (retrospective) a prior accepted element's interpretation or
                recommended action turned out to be wrong once more evidence
                arrived
  missing    -- a human added an insight the rules never generated at all --
                the strongest signal that a new insight_rules.py rule is
                needed

For accepted/challenged/effective/failed, this looks up the real object in
the given prioritised_analysis.json so rule_family/category/title are pulled
from the actual record, not typed freely -- avoids the log itself becoming a
source of unverified claims. For missing, there is no source object by
definition, so title/note are the human's own account of what was missed.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
LOG_PATH = ROOT / "learning" / "decisions.jsonl"

DECISIONS = {"accepted", "challenged", "effective", "failed", "missing"}

# Known insight_rules.py id prefixes -> rule family. Kept in sync by hand
# with insight_rules.py's _insight() callers; if a new rule is added there
# with a new id prefix, add it here too so aggregation doesn't lump it into
# "unknown_rule".
RULE_FAMILIES = [
    ("kpi_unfavorable_", "kpi_unfavorable"),
    ("concentration_", "concentration"),
    ("peak_", "peak"),
    ("external_event_", "external_event"),
    ("action_", "action"),
]


def _rule_family(source_id: str | None) -> str:
    if not source_id:
        return "unknown_rule"
    for prefix, family in RULE_FAMILIES:
        if source_id.startswith(prefix):
            return family
    return "unknown_rule"


def _find_object(prioritised: dict[str, Any], executive_object_id: str) -> dict[str, Any] | None:
    for obj in prioritised.get("executive_objects", []):
        if obj.get("id") == executive_object_id:
            return obj
    return None


def record_decision(
    *,
    decision: str,
    note: str,
    prioritised_path: Path | None,
    executive_object_id: str | None,
    missing_title: str | None,
) -> dict[str, Any]:
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of {sorted(DECISIONS)}, got {decision!r}")
    if not note.strip():
        raise ValueError("note is required -- record why, not just what, so the aggregate report means something")

    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "note": note.strip(),
    }

    if decision == "missing":
        if not missing_title or not missing_title.strip():
            raise ValueError("--missing-title is required when --decision missing (no source object exists to name it)")
        entry.update({
            "source_analysis": str(prioritised_path) if prioritised_path else None,
            "executive_object_id": None,
            "source_id": None,
            "rule_family": None,
            "category": None,
            "title": missing_title.strip(),
        })
        return entry

    if prioritised_path is None or executive_object_id is None:
        raise ValueError(f"--prioritised-analysis and --object-id are required for decision={decision!r}")

    prioritised = json.loads(prioritised_path.read_text(encoding="utf-8"))
    obj = _find_object(prioritised, executive_object_id)
    if obj is None:
        raise ValueError(f"executive_object_id {executive_object_id!r} not found in {prioritised_path}")

    entry.update({
        "source_analysis": str(prioritised_path),
        "source_report_title": prioritised.get("prioritisation_meta", {}).get("source_report_title"),
        "executive_object_id": executive_object_id,
        "source_id": obj.get("source_id"),
        "rule_family": _rule_family(obj.get("source_id")),
        "category": obj.get("category"),
        "title": obj.get("title"),
    })
    return entry


def append_entry(entry: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--decision", required=True, choices=sorted(DECISIONS))
    parser.add_argument("--note", required=True, help="Why -- this is what makes the aggregate report useful.")
    parser.add_argument("--prioritised-analysis", type=Path, default=None,
                         help="Path to the prioritised_analysis.json this object came from. Required unless --decision missing.")
    parser.add_argument("--object-id", default=None,
                         help="executive_object_id from that file. Required unless --decision missing.")
    parser.add_argument("--missing-title", default=None,
                         help="Short description of the insight the rules never generated. Required when --decision missing.")
    args = parser.parse_args()

    try:
        entry = record_decision(
            decision=args.decision,
            note=args.note,
            prioritised_path=args.prioritised_analysis,
            executive_object_id=args.object_id,
            missing_title=args.missing_title,
        )
    except ValueError as e:
        print(f"LEARNING LOG REJECTED — {e}")
        return 1

    append_entry(entry)
    print(f"LOGGED — {entry['decision']}: {entry.get('title', entry.get('missing_title'))}")
    print(f"  -> {LOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
