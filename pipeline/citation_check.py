#!/usr/bin/env python3
"""Anti-fabrication scanner. Run after validate.py passes.

validate.py checks that the *structured* data reconciles. This script checks
the *prose* -- every number the narrative claims (executive_summary,
bottom_insight, executive_facts, custom_html text) must trace back to a real
value somewhere in the document. If a number appears in a sentence but not
anywhere in the data, that is exactly the "placeholder / invented number"
failure mode this whole system exists to catch, so it is flagged loudly
rather than silently rendered.

This is a heuristic safety net, not a formal proof: it strips currency/percent
symbols and unit suffixes and compares magnitudes with a small tolerance. It
will not catch a fabricated number that happens to equal a real one used in a
different context. Treat a clean run as a strong signal, not a guarantee --
still read the narrative once before shipping.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from refs import collect_numeric_leaves

NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9])"
    r"-?R?\s?\d[\d,]*(?:\.\d+)?"
    r"\s?(?:m|bn|k|pp)?%?"
    r"(?![A-Za-z0-9])"
)

TOLERANCE = 0.15  # absolute drift allowed, in whatever unit the number is expressed


def extract_numbers(text):
    found = []
    for match in NUMBER_RE.finditer(text):
        raw = match.group()
        cleaned = re.sub(r"[Rrpp%,\s]", "", raw)
        cleaned = re.sub(r"[mbnk]$", "", cleaned, flags=re.IGNORECASE)
        try:
            found.append((raw.strip(), float(cleaned)))
        except ValueError:
            continue
    return found


_TAG_RE = re.compile(r"<[^>]+>")


def narrative_texts(doc):
    for section in doc.get("sections", []):
        text = section.get("text")
        if text:
            if section.get("type") == "custom_html":
                # Strip markup first -- otherwise numbers inside HTML attributes
                # (style="line-height:1.7", widths, etc.) get scanned as if they
                # were prose claims, which they aren't.
                text = _TAG_RE.sub(" ", text)
            yield f"section '{section['id']}' ({section['type']})", text
        for fact in section.get("executive_facts", []):
            yield f"section '{section['id']}' executive_fact", fact["statement"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_brief", type=Path)
    args = parser.parse_args()

    doc = json.loads(args.report_brief.read_text(encoding="utf-8"))
    known_values = collect_numeric_leaves(doc)

    uncited = []
    for where, text in narrative_texts(doc):
        for raw, value in extract_numbers(text):
            magnitude = abs(value)
            # Compare magnitudes on both sides: narrative prose often signals
            # direction with words ("fell", "down", "behind") rather than a
            # literal minus sign, while the source value is stored signed.
            if not any(abs(magnitude - abs(k)) <= TOLERANCE for k in known_values):
                uncited.append((where, raw, text))

    if uncited:
        print(f"CITATION CHECK FAILED — {len(uncited)} number(s) in narrative text have no matching value in the data:\n")
        for where, raw, text in uncited:
            print(f"  - '{raw}' in {where}:")
            print(f"      \"{text.strip()}\"")
        print(
            "\nEither the narrative is quoting a number that isn't in report_brief.json "
            "(fabrication risk -- fix the narrative or add the source data), or it's a "
            "legitimate number this heuristic doesn't recognise (e.g. a year, a page "
            "number) -- add it to the data if it's meaningful, otherwise rephrase."
        )
        sys.exit(1)

    print(f"CITATION CHECK PASSED — every number in the narrative text traces back to {args.report_brief}.")
    sys.exit(0)


if __name__ == "__main__":
    main()
