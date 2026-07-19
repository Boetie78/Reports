#!/usr/bin/env python3
"""Audit executive_analysis.json against its source report_brief.json.

Schema validation proves the analysis has the right shape. This audit proves the
analysis is traceable: every evidence data_ref must resolve inside the original
validated report_brief.json, every evidence value must match the value at that
reference when the value is explicitly supplied, and any evidence_status the
analysis claims must actually match what the source report_brief.json carries
at that location (or be flagged as unverifiable, never invented).
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


def _source_evidence_status(report_brief: dict[str, Any], data_ref: str) -> dict[str, Any] | None:
    """Best-effort lookup of the evidence_status sibling of the value data_ref
    points at. Only resolves refs ending in '.value' (kpi/breakdown-component
    shape) or external_event refs whose own evidence_status lives on the event
    dict itself -- not every dataRef shape has a defined evidence_status home,
    so returning None here means 'not checkable', not 'confirmed absent'."""
    if data_ref.endswith(".value"):
        try:
            parent = resolve_ref(report_brief, data_ref[: -len(".value")])
        except ValueError:
            return None
        return parent.get("evidence_status") if isinstance(parent, dict) else None
    return None


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

            claimed_status = evidence.get("evidence_status")
            if claimed_status is not None:
                source_status = _source_evidence_status(report_brief, data_ref)
                if source_status is None:
                    errors.append(
                        f"[{group_name}[{idx}]] evidence_status '{claimed_status.get('status')}' claimed for "
                        f"{data_ref}, but the source report_brief.json has no evidence_status there -- "
                        f"cannot verify, must not be fabricated by the analysis layer"
                    )
                elif claimed_status.get("status") != source_status.get("status"):
                    errors.append(
                        f"[{group_name}[{idx}]] evidence_status mismatch for {data_ref}: analysis claims "
                        f"'{claimed_status.get('status')}', source report_brief.json has "
                        f"'{source_status.get('status')}'"
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

    report_brief = json.loads(args.report_brief.read_text(encoding="utf-8"))
    executive_analysis = json.loads(args.executive_analysis.read_text(encoding="utf-8"))
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
