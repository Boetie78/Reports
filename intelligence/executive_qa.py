#!/usr/bin/env python3
"""MEIP Executive QA.

Challenges each Page 1 / Page 2 decision-plan placement against the rules in
docs/EXECUTIVE_INTELLIGENCE_MODEL.md before a report is allowed to claim those
items are ready for executive use. Monitor/Appendix/Ignore items are not
challenged here -- they are not being shown to executives yet, so the bar for
them is lower and belongs elsewhere.

Consumes:
  - a decision_plan.json (placement + reason)
  - the matching prioritised_analysis.json, found by convention from the
    decision_plan filename -- decision_engine.py deliberately strips
    interpretation/business_impact/recommended_action/supporting_evidence out
    of the decision plan (its job is placement, not QA), so this script goes
    back to the source object for what it actually needs to challenge.

Checks, each mapped to a specific Executive Intelligence Model rule:

  evidence_confidence
    Independently re-verifies confidence clears a floor for its placement
    tier (Page 1: 60, Page 2: 45) instead of trusting decision_engine.py's
    own gate -- that's the point of a separate QA step: it has to hold even
    if the decision plan was hand-edited or the upstream gate has a bug.

  evidence_status
    Where the underlying report_brief.json actually carries a real
    evidence_status (schema/report_brief.schema.json's evidenceStatus,
    propagated through supporting_evidence by analyse.py/insight_rules.py),
    this checks the real thing instead of guessing from wording:
    CONFLICTING/MISSING evidence blocks the item outright (escalates to
    Hold, same severity as failing evidence_confidence); PARTIALLY_VERIFIED/
    USER_CONFIRMED evidence requires hedged wording. Objects with no
    propagated evidence_status fall through to the wording-heuristic checks
    below unchanged -- propagation is not yet retrofitted onto every report.

  causal_overreach (Stage 4: "must distinguish correlation from causation")
    Flags causal language in the interpretation when confidence isn't high
    enough to support asserting causation. A confidence-based proxy for
    when real evidence_status isn't available.

  impact_hedging (Stage 5: "potential impacts must be labelled as potential")
    Flags business_impact text that reads as unqualified certainty when
    confidence is not high. Same proxy role as causal_overreach.

  ownership (Stage 7: "should identify an owner ... where possible")
    Flags the literal decision_engine.py fallback default ("Executive
    Sponsor"), which means no owner was actually assigned -- an accountable
    function/department (e.g. "Commercial") is fine and not flagged.

  action_timing (Stage 7: "should include timing or trigger conditions
    where possible")
    Flags a recommended_action with no timing/trigger signal at all.

Status: Hold if evidence_confidence fails, or if evidence_status is
CONFLICTING/MISSING (nothing else can compensate for either). Revise if any
other check fails. Approved if everything passes.

Risk level: High for Hold, Medium for Revise, Low for Approved.

Like narrative_review.py, this prints a challenge/lint report for human
judgment and exits 0 by default -- it does not block render.py/blueprint.py;
that non-bypassable gate is pipeline/validate.py. Pass --strict to fail the
build on any non-Approved review once you trust these heuristics for your
report type.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Windows' console codepage (cp1252) can't encode every character that might
# show up in transcribed report text (arrows, some punctuation) -- reconfigure
# to UTF-8 with a safe fallback so a stray character in source data can never
# crash the report itself, only degrade that one character's display.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

CAUSAL_MARKERS = [
    "because", "driven by", "drove", "caused", "due to", "resulted in",
    "led to", "responsible for", "as a result", "which caused",
]

HEDGE_MARKERS = [
    "may ", "could ", "potential", "risk of", "likely", "appears",
    "suggests", "indicates", "possible", "if this continues", "may indicate",
]

CERTAINTY_MARKERS = [
    "will certainly", "guarantee", "certainly", "definitely", "without doubt",
    "proves that", "always results in", "100% ", "undeniably",
]

GENERIC_OWNER_FALLBACK = "Executive Sponsor"

TIMING_MARKERS = [
    "today", "this week", "this month", "by ", "within ", "immediately",
    "urgent", "before ", "next week", "ongoing", "daily", "weekly", "monthly",
    "end of day", "eod", "eow", "eom",
    # conditional/trigger-based timing, not just fixed dates -- "escalate if
    # repeated in the next cycle" is a real trigger condition, just phrased
    # as a condition rather than a date
    "if repeated", "if this recurs", "next cycle", "next occurrence",
    "once confirmed", "when confirmed", "unless resolved",
]

CONFIDENCE_FLOOR = {"Page 1": 60, "Page 2": 45}


def _text_has_any(text: str, markers: list[str]) -> bool:
    lowered = text.lower()
    return any(m in lowered for m in markers)


def check_evidence_confidence(decision: dict[str, Any], checks: list[dict[str, Any]]) -> bool:
    floor = CONFIDENCE_FLOOR.get(decision["decision"])
    confidence = decision.get("confidence", 0)
    passed = floor is None or confidence >= floor
    checks.append({
        "name": "evidence_confidence",
        "passed": passed,
        "message": (
            f"confidence {confidence} meets the {floor} floor required for {decision['decision']}."
            if passed else
            f"confidence {confidence} is below the {floor} floor required for {decision['decision']} "
            f"-- this item should not be on this page independent of what decision_engine.py decided."
        ),
    })
    return passed


def check_causal_overreach(obj: dict[str, Any], confidence: int, checks: list[dict[str, Any]]) -> bool:
    interpretation = obj.get("interpretation", "")
    has_causal = _text_has_any(interpretation, CAUSAL_MARKERS)
    passed = not has_causal or confidence >= 70
    checks.append({
        "name": "causal_overreach",
        "passed": passed,
        "message": (
            "interpretation contains no unsupported causal language."
            if not has_causal else
            f"interpretation asserts causation with confidence {confidence} (<70) -- Stage 4 requires "
            f"distinguishing correlation from causation; either raise evidence or soften to correlation "
            f"language: \"{interpretation[:100]}\""
            if not passed else
            "interpretation uses causal language, but confidence is high enough to support it."
        ),
    })
    return passed


def check_impact_hedging(obj: dict[str, Any], confidence: int, checks: list[dict[str, Any]]) -> bool:
    impact = obj.get("business_impact", "")
    has_hedge = _text_has_any(impact, HEDGE_MARKERS)
    has_certainty = _text_has_any(impact, CERTAINTY_MARKERS)
    needs_hedge = confidence < 70
    passed = has_certainty is False and (not needs_hedge or has_hedge or not impact)
    checks.append({
        "name": "impact_hedging",
        "passed": passed,
        "message": (
            f"business_impact uses unqualified certainty language "
            f"({', '.join(m for m in CERTAINTY_MARKERS if m in impact.lower())}) -- Stage 5 requires "
            f"potential impacts to be labelled as potential."
            if has_certainty else
            f"confidence {confidence} (<70) but business_impact has no hedging language -- "
            f"Stage 5: \"potential impacts must be labelled as potential\": \"{impact[:100]}\""
            if not passed else
            "business_impact wording matches its confidence level."
        ),
    })
    return passed


def check_ownership(obj: dict[str, Any], checks: list[dict[str, Any]]) -> bool:
    owner = obj.get("owner", "")
    passed = owner != GENERIC_OWNER_FALLBACK
    checks.append({
        "name": "ownership",
        "passed": passed,
        "message": (
            f"owner is the unassigned fallback default ('{GENERIC_OWNER_FALLBACK}') -- Stage 7 requires "
            f"identifying an owner or accountable function; assign a real function or named owner."
            if not passed else
            f"owner '{owner}' is an assigned accountable function, not the generic fallback."
        ),
    })
    return passed


def check_action_timing(obj: dict[str, Any], checks: list[dict[str, Any]]) -> bool:
    action = obj.get("recommended_action", "")
    passed = bool(action) and _text_has_any(action, TIMING_MARKERS)
    checks.append({
        "name": "action_timing",
        "passed": passed,
        "message": (
            "recommended_action has no timing or trigger signal -- Stage 7: \"actions should include "
            f"timing or trigger conditions where possible\": \"{action[:100]}\""
            if not passed else
            "recommended_action includes a timing/trigger signal."
        ),
    })
    return passed


# Statuses too weak to support a Page 1/2 claim outright -- same severity
# tier as failing evidence_confidence, not a wording nitpick.
BLOCKING_EVIDENCE_STATUSES = {"CONFLICTING", "MISSING"}
# Statuses that are usable but must be reflected in hedged wording.
HEDGE_REQUIRED_EVIDENCE_STATUSES = {"PARTIALLY_VERIFIED", "USER_CONFIRMED"}


def check_evidence_status(obj: dict[str, Any], checks: list[dict[str, Any]]) -> bool:
    """Real evidence-status check, not a text-pattern guess -- supersedes
    causal_overreach/impact_hedging's confidence-based heuristic whenever the
    underlying report_brief.json actually carries an evidence_status, since
    that's ground truth and confidence-as-proxy no longer has to guess.
    """
    statuses = [
        ev["evidence_status"]["status"]
        for ev in obj.get("supporting_evidence", [])
        if "evidence_status" in ev
    ]
    if not statuses:
        checks.append({
            "name": "evidence_status",
            "passed": True,
            "message": "no evidence_status present on supporting_evidence -- not yet propagated for this object, "
            "falling back to confidence-based heuristics for causal_overreach/impact_hedging.",
        })
        return True

    blocking = [s for s in statuses if s in BLOCKING_EVIDENCE_STATUSES]
    if blocking:
        checks.append({
            "name": "evidence_status",
            "passed": False,
            "message": f"supporting_evidence carries {', '.join(sorted(set(blocking)))} evidence_status -- "
            f"per docs/DATA_INTEGRITY_STANDARD.md this must not support a Page 1/2 claim until resolved.",
        })
        return False

    needs_hedge = any(s in HEDGE_REQUIRED_EVIDENCE_STATUSES for s in statuses)
    if needs_hedge:
        impact = obj.get("business_impact", "")
        interpretation = obj.get("interpretation", "")
        hedged = _text_has_any(impact, HEDGE_MARKERS) or _text_has_any(interpretation, HEDGE_MARKERS)
        checks.append({
            "name": "evidence_status",
            "passed": hedged,
            "message": (
                f"supporting_evidence carries {', '.join(sorted(set(statuses)))} evidence but wording is "
                f"unhedged -- Stage 5: \"potential impacts must be labelled as potential\"."
                if not hedged else
                f"supporting_evidence carries {', '.join(sorted(set(statuses)))} evidence and wording is "
                f"appropriately hedged."
            ),
        })
        return hedged

    checks.append({
        "name": "evidence_status",
        "passed": True,
        "message": f"all supporting_evidence is {', '.join(sorted(set(statuses)))} -- no hedging required.",
    })
    return True


def review_object(decision: dict[str, Any], obj: dict[str, Any] | None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    confidence = decision.get("confidence", 0)

    confidence_ok = check_evidence_confidence(decision, checks)
    evidence_status_ok = True
    if obj is not None:
        evidence_status_ok = check_evidence_status(obj, checks)
        check_causal_overreach(obj, confidence, checks)
        check_impact_hedging(obj, confidence, checks)
        check_ownership(obj, checks)
        check_action_timing(obj, checks)
    else:
        checks.append({
            "name": "source_object_found",
            "passed": False,
            "message": "could not find the matching executive object in the prioritised_analysis.json "
            "-- only evidence_confidence could be re-checked from the decision plan alone.",
        })

    all_passed = all(c["passed"] for c in checks)
    evidence_status_blocking = not evidence_status_ok and any(
        "must not support a Page 1/2 claim" in c["message"] for c in checks if c["name"] == "evidence_status"
    )
    if not confidence_ok or evidence_status_blocking:
        status, risk = "Hold", "High"
    elif not all_passed:
        status, risk = "Revise", "Medium"
    else:
        status, risk = "Approved", "Low"

    failing = [c["name"] for c in checks if not c["passed"]]
    recommendation = (
        "Ready for publication as placed."
        if status == "Approved" else
        f"{status}: address {', '.join(failing)} before this reaches executives."
    )

    return {
        "executive_object_id": decision["executive_object_id"],
        "title": decision["title"],
        "status": status,
        "risk_level": risk,
        "checks": checks,
        "recommendation": recommendation,
    }


def build_qa(decision_plan: dict[str, Any], prioritised: dict[str, Any] | None, decision_plan_path: Path) -> dict[str, Any]:
    objects_by_id = {}
    if prioritised is not None:
        objects_by_id = {o["id"]: o for o in prioritised.get("executive_objects", [])}

    reviews = []
    for decision in decision_plan.get("decisions", []):
        if decision["decision"] not in CONFIDENCE_FLOOR:
            continue  # Monitor/Appendix/Ignore are not being shown to executives yet
        obj = objects_by_id.get(decision["executive_object_id"])
        reviews.append(review_object(decision, obj))

    meta = decision_plan.get("decision_meta", {})
    return {
        "qa_meta": {
            "source_decision_plan": str(decision_plan_path),
            "source_report_title": meta.get("source_report_title", "Untitled report"),
            "source_report_type": meta.get("source_report_type", "unknown"),
        },
        "reviews": reviews,
    }


def find_prioritised_analysis(decision_plan_path: Path) -> Path | None:
    candidate = Path(str(decision_plan_path).replace("_decision_plan", "_prioritised_analysis"))
    return candidate if candidate.exists() else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("decision_plan", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any review is not Approved")
    args = parser.parse_args()

    decision_plan = json.loads(args.decision_plan.read_text(encoding="utf-8"))

    prioritised_path = find_prioritised_analysis(args.decision_plan)
    prioritised = json.loads(prioritised_path.read_text(encoding="utf-8")) if prioritised_path else None
    if prioritised is None:
        print(f"WARNING: could not find matching prioritised_analysis.json next to {args.decision_plan} "
              f"-- only evidence_confidence will be checked.\n")

    qa = build_qa(decision_plan, prioritised, args.decision_plan)

    output_path = args.output or args.decision_plan.with_name(
        args.decision_plan.stem.replace("_decision_plan", "") + "_executive_qa.json"
    )
    output_path.write_text(json.dumps(qa, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    counts = {"Approved": 0, "Revise": 0, "Hold": 0}
    for r in qa["reviews"]:
        counts[r["status"]] += 1

    print(f"EXECUTIVE QA — {len(qa['reviews'])} Page 1/2 item(s) reviewed in {args.decision_plan}:")
    print(f"  Approved: {counts['Approved']}   Revise: {counts['Revise']}   Hold: {counts['Hold']}\n")
    for r in qa["reviews"]:
        if r["status"] != "Approved":
            print(f"  [{r['status']}/{r['risk_level']}] {r['title']} ({r['executive_object_id']})")
            for c in r["checks"]:
                if not c["passed"]:
                    print(f"      - {c['name']}: {c['message']}")
    print(f"\nWrote {output_path}")

    if args.strict and (counts["Revise"] or counts["Hold"]):
        print("\n--strict was set: treating non-Approved reviews as failures.")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
