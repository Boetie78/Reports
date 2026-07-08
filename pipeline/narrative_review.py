#!/usr/bin/env python3
"""Narrative quality lint, run after validate.py and citation_check.py pass.

Those two gates check correctness (does it reconcile, is every number real).
This one checks the MEIP Design Rules -- "never duplicate information," "one
visual per question," "interpret, don't restate," length limits on the
summary/bottom-insight -- which are judgment calls, not arithmetic. So unlike
the other two gates, this one prints WARNINGS and exits 0 by default; pass
--strict to make warnings fail the build once you trust the heuristics for
your report type.

False positives are expected here more than in citation_check.py -- a fact
this script calls "descriptive" might genuinely be fine in context, and two
facts it calls "duplicate" might be a deliberate callback. Read the warnings,
don't just chase the exit code.
"""
import argparse
import itertools
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

DUPLICATE_THRESHOLD = 0.6

INTERPRETIVE_MARKERS = [
    "because", "driven by", "drove", "indicat", "suggest", "point", "signal", "reflect",
    "concentrat", "rather than", "which means", "risk", "pressure", "recover",
    "pattern", "problem", "opportunit", "requir", "consider", "should",
    "recommend", "underperform", "outpac", "divergence", "single largest",
    "accounted for", "responsible for", "reinforc", "attention", "priorit",
    "consistent with", "offsett", "protect", "worth checking", "nearly all",
    "nearly two-thirds", "clearest sign",
]


def sentence_count(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return len([p for p in parts if p.strip()])


def collect_narrative_blocks(doc):
    blocks = []
    for section in doc.get("sections", []):
        if section["type"] in ("executive_summary", "bottom_insight") and section.get("text"):
            blocks.append((f"section '{section['id']}' {section['type']}", section["text"]))
        for i, fact in enumerate(section.get("executive_facts", [])):
            blocks.append((f"section '{section['id']}' executive_fact[{i}]", fact["statement"]))
    return blocks


def check_length_limits(doc, warnings):
    for section in doc.get("sections", []):
        if section["type"] == "executive_summary" and section.get("text"):
            n = sentence_count(section["text"])
            if n > 4:
                warnings.append(f"section '{section['id']}' executive_summary has {n} sentences (MEIP: max 4 lines) -- tighten it.")
        if section["type"] == "bottom_insight" and section.get("text"):
            n = sentence_count(section["text"])
            if n > 1:
                warnings.append(f"section '{section['id']}' bottom_insight has {n} sentences (MEIP: one sentence) -- cut to one.")


def check_duplicates(doc, warnings):
    blocks = collect_narrative_blocks(doc)
    for (where_a, text_a), (where_b, text_b) in itertools.combinations(blocks, 2):
        ratio = SequenceMatcher(None, text_a.lower(), text_b.lower()).ratio()
        if ratio >= DUPLICATE_THRESHOLD:
            warnings.append(
                f"{where_a} and {where_b} look like duplicate insights "
                f"(similarity {ratio:.0%}) -- MEIP: never show the same insight twice."
            )


def check_interpretive(doc, warnings):
    for section in doc.get("sections", []):
        for i, fact in enumerate(section.get("executive_facts", [])):
            stmt = fact["statement"].lower()
            if not any(m in stmt for m in INTERPRETIVE_MARKERS):
                warnings.append(
                    f"section '{section['id']}' executive_fact[{i}] reads as descriptive, not "
                    f"interpretive (no causal/implication language found): "
                    f"\"{fact['statement'][:80]}\" -- MEIP: interpret the business, don't restate numbers."
                )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_brief", type=Path)
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any warning fires, instead of just printing them")
    args = parser.parse_args()

    doc = json.loads(args.report_brief.read_text())
    warnings = []
    check_length_limits(doc, warnings)
    check_duplicates(doc, warnings)
    check_interpretive(doc, warnings)

    if warnings:
        print(f"NARRATIVE REVIEW — {len(warnings)} thing(s) worth a second look in {args.report_brief}:\n")
        for w in warnings:
            print(f"  - {w}")
        if args.strict:
            print("\n--strict was set: treating these as failures.")
            sys.exit(1)
        print("\nThese are heuristic judgment calls, not correctness errors -- review them, fix what's real, ignore false positives.")
        sys.exit(0)

    print(f"NARRATIVE REVIEW — nothing flagged in {args.report_brief}.")
    sys.exit(0)


if __name__ == "__main__":
    main()
