#!/usr/bin/env python3
"""Reconciliation gate. Run this before render.py, always.

Checks, in order:
  1. report_brief.json conforms to schema/report_brief.schema.json
  2. every breakdown/waterfall section: sum(components.value) == parent_total.value
  3. every component.pct_of_parent (if given) matches value/parent_total*100
  4. every dataRef (executive_facts, external_events, section.supporting_data_refs)
     resolves to a real value in the document -- no dangling citations
  5. every external_event is actually incorporated into the narrative, not just
     tagged to data and left silent (MEIP rule: "these must be linked directly
     to the data" -- linked to data AND surfaced in the story, not one or the other)
  6. provenance.unresolved_flags is empty, unless --allow-flags is passed

Exits 0 only if every check passes. Exits 1 and prints every failure found
(not just the first) otherwise -- nothing downstream should ever run against
a document that failed this gate.
"""
import argparse
import json
import sys
from pathlib import Path

import jsonschema

from refs import resolve_ref

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "report_brief.schema.json"


def check_schema(doc, errors):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)
    for e in validator.iter_errors(doc):
        errors.append(f"[schema] {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}")


def check_reconciliation(doc, errors):
    for section in doc.get("sections", []):
        bd = section.get("breakdown")
        if not bd:
            continue
        tolerance = bd.get("tolerance", 0.05)
        parent_value = bd["parent_total"]["value"]
        component_sum = sum(c["value"] for c in bd["components"])
        drift = abs(component_sum - parent_value)
        if drift > tolerance:
            errors.append(
                f"[reconcile] section '{section['id']}' breakdown '{bd['id']}': "
                f"components sum to {component_sum:g} but parent_total "
                f"'{bd['parent_total']['label']}' is {parent_value:g} "
                f"(drift {drift:g} > tolerance {tolerance:g})"
            )
        mode = bd.get("mode", "share")
        for c in bd["components"]:
            # pct_of_parent only means "share of the total" in share mode. In
            # variance mode a stated percentage is variance-vs-that-component's-
            # own-base (e.g. vs its own plan), which has nothing to do with the
            # parent_total denominator -- dividing by a small/near-zero total
            # variance produces meaningless blown-up percentages, so don't
            # cross-check it there.
            if "pct_of_parent" in c and parent_value and mode == "share":
                expected_pct = c["value"] / parent_value * 100
                if abs(expected_pct - c["pct_of_parent"]) > 0.1:
                    errors.append(
                        f"[reconcile] section '{section['id']}' breakdown '{bd['id']}' "
                        f"component '{c['label']}': stated pct_of_parent "
                        f"{c['pct_of_parent']:g}% does not match computed "
                        f"{expected_pct:.2f}% from value/parent_total"
                    )


def check_refs(doc, errors):
    def check_ref_list(refs, where):
        for ref in refs:
            try:
                resolve_ref(doc, ref)
            except ValueError as e:
                errors.append(f"[dangling-ref] {where}: {e}")

    for section in doc.get("sections", []):
        check_ref_list(section.get("supporting_data_refs", []), f"section '{section['id']}'")
        for fact in section.get("executive_facts", []):
            check_ref_list(
                fact.get("supporting_data_refs", []),
                f"section '{section['id']}' executive_fact '{fact['statement'][:40]}...'",
            )
        for ev in section.get("external_events", []):
            check_ref_list(
                ev.get("linked_data_refs", []),
                f"section '{section['id']}' external_event '{ev['name']}'",
            )


def check_events_incorporated(doc, errors):
    """A supplied external_event isn't 'incorporated into the executive
    narrative' just because it has linked_data_refs -- that only proves it's
    tied to data. It also has to actually surface in the story: at least one
    of its linked refs must also be cited by the executive_summary, an
    executive_fact, or the bottom_insight. Otherwise it's data-tagged but the
    narrative never actually talks about it, which is silent, not incorporated.
    """
    narrative_refs = set()
    for section in doc.get("sections", []):
        if section["type"] in ("executive_summary", "bottom_insight"):
            narrative_refs.update(section.get("supporting_data_refs", []))
        for fact in section.get("executive_facts", []):
            narrative_refs.update(fact.get("supporting_data_refs", []))

    for section in doc.get("sections", []):
        for ev in section.get("external_events", []):
            event_refs = set(ev.get("linked_data_refs", []))
            if event_refs and not (event_refs & narrative_refs):
                errors.append(
                    f"[event-not-incorporated] section '{section['id']}' external_event "
                    f"'{ev['name']}': linked to data ({', '.join(sorted(event_refs))}) but "
                    f"none of those refs are cited by executive_summary, an executive_fact, "
                    f"or bottom_insight -- the event is tagged but never actually shows up "
                    f"in the story. Either write it into the narrative or remove it."
                )


def check_flags(doc, errors, allow_flags):
    flags = doc.get("provenance", {}).get("unresolved_flags", [])
    if flags and not allow_flags:
        for f in flags:
            errors.append(f"[unresolved] {f}")


def validate_document(doc, allow_flags=False):
    """Run every check and return the list of error strings (empty = passed).

    This is the single source of truth for "is this document safe to render or
    export." main() below uses it for the standalone `validate.py` CLI, and
    render.py / blueprint.py import it directly to enforce the same gate
    in-process -- so the gate can't be skipped by calling those tools without
    having run validate.py first.
    """
    errors = []
    check_schema(doc, errors)
    if not errors:
        # reconciliation/ref checks assume schema-valid shape; skip if schema failed
        check_reconciliation(doc, errors)
        check_refs(doc, errors)
        check_events_incorporated(doc, errors)
    check_flags(doc, errors, allow_flags)
    return errors


def enforce_gate(doc, source_label, allow_flags=False):
    """Validate `doc` and exit(1) with a printed report if it fails.

    Call this at the top of any tool (render, blueprint, or future export
    formats) that must never run against an unvalidated document. There is
    intentionally no bypass flag here beyond allow_flags, which only relaxes
    the unresolved-flags check and still requires every other check to pass.
    """
    errors = validate_document(doc, allow_flags=allow_flags)
    if errors:
        print(f"VALIDATION GATE FAILED — {source_label} cannot proceed. {len(errors)} issue(s) in the source document:\n")
        for e in errors:
            print(f"  - {e}")
        print("\nRun pipeline/validate.py on this report_brief.json directly for the same report, then fix the source data or extraction before retrying.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_brief", type=Path)
    parser.add_argument(
        "--allow-flags",
        action="store_true",
        help="Don't fail on provenance.unresolved_flags (use only when you've reviewed them by hand)",
    )
    args = parser.parse_args()

    doc = json.loads(args.report_brief.read_text(encoding="utf-8"))
    errors = validate_document(doc, allow_flags=args.allow_flags)

    if errors:
        print(f"VALIDATION FAILED — {len(errors)} issue(s) in {args.report_brief}:\n")
        for e in errors:
            print(f"  - {e}")
        print("\nFix the source data or the extraction, then re-run. Nothing renders until this passes.")
        sys.exit(1)

    print(f"VALIDATION PASSED — {args.report_brief} reconciles and is safe to render.")
    sys.exit(0)


if __name__ == "__main__":
    main()
