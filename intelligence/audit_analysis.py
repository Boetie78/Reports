#!/usr/bin/env python3
"""Audit executive_analysis.json against its source report_brief.json.

Schema validation proves the analysis has the right shape. This audit proves the
analysis is traceable: every evidence data_ref must resolve inside the original
validated report_brief.json, and every evidence value must match the value at
that reference when the value is explicitly supplied.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow running as `python3 intelligence/audit_analysis.py ...` from repo root.
sys.path.append(str(Path(__file__).parent.parent / "pipeline"))

from refs import resolve_ref


EVIDENCE_GROUPS = (
    ("primary_message.supporting_evidence", lambda doc: doc.get("primary_message", {}).get("supporting_evidence", [])),
    ("findings.supporting_evidence", lambda doc: [ev for item in doc.get("findings", []) for ev in item.get("supporting_evidence", [])]),
    ("risks.supporting_evidence", lambda doc: [ev for item in doc.get("risks", []) for ev in item.get("supporting_evidence", [])]),
    ("opportunities.supporting_evidence", lambda doc: [ev for item in doc.get("opportunities", []) for ev in item.get("supporting_evidence", [])]),
    ("recommended_actions.supporting_evidence", lambda doc: [ev for item in doc.get("recommended_actions", []) for ev in item.get("supporting_evidence", [])]),
    ("source_values_used", lambda doc: doc.get("source_values_used", [])),
)


def _normalise(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    return value


def audit(report_brief: dict[str, Any], executive_analysis: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen_refs: set[str] = set()

    for group_name, getter in EVIDENCE_GROUPS:
        for idx, evidence in enumerate(getter(executive_analysis)):
            data_ref = evidence.get("data_ref")
            if not data_ref:
                errors.append(f"[{group_name}[{idx}]] missing data_ref")
                continue
            try:
                resolved = resolve_ref(report_brief, data_ref)
            except ValueError as exc:
                errors.append(f"[{group_name}[{idx}]] dangling evidence ref: {exc}")
                continue

            supplied_value = evidence.get("value")
            if supplied_value is not None and _normalise(supplied_value) != _normalise(resolved):
                errors.append(
                    f"[{group_name}[{idx}]] evidence value mismatch for {data_ref}: "
                    f"analysis has {supplied_value!r}, source has {resolved!r}"
                )
            seen_refs.add(data_ref)

    if not seen_refs:
        errors.append("[evidence] executive_analysis contains no traceable source references")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_brief", type=Path)
    parser.add_argument("executive_analysis", type=Path)
    args = parser.parse_args()

    report_brief = json.loads(args.report_brief.read_text())
    executive_analysis = json.loads(args.executive_analysis.read_text())
    errors = audit(report_brief, executive_analysis)

    if errors:
        print(f"EXECUTIVE ANALYSIS AUDIT FAILED — {len(errors)} issue(s):\n")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("EXECUTIVE ANALYSIS AUDIT PASSED — all evidence refs resolve to the source report_brief.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
