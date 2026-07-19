#!/usr/bin/env python3
"""MEIP Normalisation Engine -- observation.json -> a valid report_brief.json.

Second slice of the "raw files -> report_brief.json" pipeline. Consumes the
structural output of intelligence/observation.py (currently: label_value_table
shapes only) and produces a schema-valid report_brief.json breakdown_table
section, ready for pipeline/validate.py.

Zero-fabrication boundaries, stated explicitly:
  - report_meta (title, subtitle, period_label, organization, report_type)
    is NOT inferable from a spreadsheet and must be supplied by a human via
    CLI args -- this script never guesses it.
  - parent_total is computed as the sum of the observed components when the
    source has no explicit total row. This is a real computation, not a
    guess, but it is still an inference beyond raw transcription -- so it is
    always labelled evidence_status DERIVED with a note saying exactly that,
    never presented as VERIFIED.
  - direction (favorable/unfavorable) is never set. Nothing in a raw
    label/value table encodes whether a value is good or bad; that requires
    a target, budget, or prior-period comparison this script does not have.
    Leaving it unset is correct; guessing it would be a fabrication.
  - No executive_facts, executive_summary, or interpretation text is
    generated here. Narrative interpretation is intelligence/analyse.py's
    job, working from a validated report_brief.json -- this script's output
    is deliberately just structure and numbers.

Output still needs pipeline/validate.py to pass before it's safe to use --
this script does not run the gate itself, since the intended workflow is
observe -> normalise -> [human reviews the draft report_brief.json] ->
validate -> ... -> render.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def normalise_label_value_table(table: dict[str, Any], *, section_id: str, title: str, unit: str) -> dict[str, Any]:
    if table["shape"] != "label_value_table":
        raise ValueError(f"normalise_label_value_table cannot handle shape {table['shape']!r}")

    components = [{"label": r["label"], "value": r["value"]} for r in table["rows"]]
    total = round(sum(c["value"] for c in components), 6)

    return {
        "id": section_id,
        "type": "breakdown_table",
        "label_header": table["label_header"],
        "breakdown": {
            "id": f"{section_id}_breakdown",
            "title": title,
            "unit": unit,
            "mode": "share",
            "parent_total": {"label": "Total", "value": total},
            "components": components,
        },
        "evidence_status": {
            "status": "DERIVED",
            "note": f"parent_total ({total:g}) is computed as the sum of the {len(components)} observed "
            f"components -- the source table had no explicit total row. Component values themselves are "
            f"direct transcriptions, not derived.",
        },
    }


def build_report_brief(
    observation: dict[str, Any],
    *,
    title: str,
    subtitle: str,
    period_label: str,
    organization: str,
    report_type: str,
    generated_date: str,
    section_title: str,
    unit: str,
) -> dict[str, Any]:
    if not observation["tables"]:
        raise ValueError(
            f"{observation['source_file']} produced no detected tables (only unclassified regions) -- "
            f"nothing to normalise. See the unclassified entries for why."
        )
    if len(observation["tables"]) > 1:
        raise ValueError(
            f"{observation['source_file']} produced {len(observation['tables'])} detected tables -- this "
            f"slice of normalise.py handles exactly one table per file. Split the source or extend this "
            f"script to loop over multiple tables into multiple sections."
        )

    table = observation["tables"][0]
    section = normalise_label_value_table(table, section_id="observed_breakdown", title=section_title, unit=unit)

    unresolved_flags = []
    if observation.get("unclassified"):
        unresolved_flags.append(
            f"{len(observation['unclassified'])} unclassified region(s) in {observation['source_file']} "
            f"were not normalised -- see the original observation.json for details."
        )

    return {
        "report_meta": {
            "title": title,
            "subtitle": subtitle,
            "organization": organization,
            "period_label": period_label,
            "report_type": report_type,
            "generated_date": generated_date,
        },
        "sections": [section],
        "provenance": {
            "source_files": [observation["source_file"]],
            "extraction_notes": f"Structurally extracted via intelligence/observation.py + normalise.py from "
            f"{observation['source_file']}. Component values are direct transcriptions; parent_total is "
            f"computed, not sourced (see the section's own evidence_status). No narrative, direction, or "
            f"interpretation was generated -- run intelligence/analyse.py after this passes validate.py.",
            "unresolved_flags": unresolved_flags,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("observation", type=Path, help="Output of intelligence/observation.py")
    parser.add_argument("--title", required=True)
    parser.add_argument("--subtitle", required=True)
    parser.add_argument("--period-label", required=True)
    parser.add_argument("--organization", default="Massmart")
    parser.add_argument("--report-type", required=True)
    parser.add_argument("--generated-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--section-title", required=True, help="Title for the generated breakdown_table section")
    parser.add_argument("--unit", default="", help="Unit for the values, e.g. 'R' or 'lines'")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    observation = json.loads(args.observation.read_text(encoding="utf-8"))

    try:
        brief = build_report_brief(
            observation,
            title=args.title,
            subtitle=args.subtitle,
            period_label=args.period_label,
            organization=args.organization,
            report_type=args.report_type,
            generated_date=args.generated_date,
            section_title=args.section_title,
            unit=args.unit,
        )
    except ValueError as e:
        print(f"NORMALISATION FAILED — {e}")
        return 1

    output_path = args.output or Path("output") / f"{args.observation.stem.replace('_observation', '')}_report_brief.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(brief, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"NORMALISED — {output_path}")
    print(f"  Run pipeline/validate.py on this file next -- it is a draft, not yet validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
