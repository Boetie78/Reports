#!/usr/bin/env python3
"""Validate executive_analysis.json against schema.

This is a structural check for the MEIP intelligence layer. It confirms the
analysis output has the required evidence, insight, action and presentation-plan
shape before it is used downstream.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "executive_analysis.schema.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executive_analysis", type=Path)
    args = parser.parse_args()

    doc = json.loads(args.executive_analysis.read_text())
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))

    if errors:
        print(f"EXECUTIVE ANALYSIS VALIDATION FAILED — {len(errors)} issue(s):\n")
        for error in errors:
            path = "/".join(str(part) for part in error.path) or "<root>"
            print(f"  - [schema] {path}: {error.message}")
        return 1

    print(f"EXECUTIVE ANALYSIS VALIDATION PASSED — {args.executive_analysis}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
