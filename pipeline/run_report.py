#!/usr/bin/env python3
"""Run the MEIP report pipeline in the correct order.

This script is intentionally a coordinator, not a new source of truth. Each step
still lives in its own module so failures stay specific and auditable.

Default flow:
  1. pipeline/validate.py
  2. pipeline/citation_check.py
  3. pipeline/narrative_review.py
  4. intelligence/analyse.py
  5. intelligence/validate_analysis.py
  6. intelligence/audit_analysis.py
  7. intelligence/export_analysis.py
  8. intelligence/prioritisation_engine.py

Optional flags can also render and/or export a Markdown blueprint after all gates
pass.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run_step(label: str, command: list[str]) -> None:
    print(f"\n=== {label} ===")
    print("$ " + " ".join(command))
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        raise SystemExit(f"\nSTOPPED — {label} failed with exit code {completed.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_brief", type=Path, help="Path to report_brief.json")
    parser.add_argument("--render", action="store_true", help="Render PDF/PNG after all validation and intelligence gates pass")
    parser.add_argument("--blueprint", action="store_true", help="Export Markdown blueprint after all gates pass")
    parser.add_argument("--no-analysis-md", action="store_true", help="Skip human-readable executive analysis Markdown export")
    parser.add_argument("--no-prioritisation", action="store_true", help="Skip executive object prioritisation")
    parser.add_argument("--strict-narrative", action="store_true", help="Make narrative_review.py warnings fail the run")
    args = parser.parse_args()

    report_brief = args.report_brief
    if not report_brief.is_absolute():
        report_brief = Path.cwd() / report_brief

    analysis_path = ROOT / "output" / f"{report_brief.stem}_executive_analysis.json"
    prioritised_path = ROOT / "output" / f"{report_brief.stem}_prioritised_analysis.json"

    py = sys.executable
    run_step("Validate report brief", [py, "pipeline/validate.py", str(report_brief)])
    run_step("Check narrative citations", [py, "pipeline/citation_check.py", str(report_brief)])

    narrative_cmd = [py, "pipeline/narrative_review.py", str(report_brief)]
    if args.strict_narrative:
        narrative_cmd.append("--strict")
    run_step("Review narrative quality", narrative_cmd)

    run_step("Generate executive analysis", [py, "intelligence/analyse.py", str(report_brief), "--output", str(analysis_path)])
    run_step("Validate executive analysis schema", [py, "intelligence/validate_analysis.py", str(analysis_path)])
    run_step("Audit executive analysis traceability", [py, "intelligence/audit_analysis.py", str(report_brief), str(analysis_path)])

    if not args.no_analysis_md:
        run_step("Export executive analysis review pack", [py, "intelligence/export_analysis.py", str(analysis_path)])
    if not args.no_prioritisation:
        run_step("Prioritise executive decision objects", [py, "intelligence/prioritisation_engine.py", str(analysis_path), "--output", str(prioritised_path)])
    if args.render:
        run_step("Render report", [py, "pipeline/render.py", str(report_brief)])
    if args.blueprint:
        run_step("Export blueprint", [py, "pipeline/blueprint.py", str(report_brief)])

    print("\nMEIP PIPELINE PASSED — report is validated, cited, analysed, prioritised and ready for executive use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
