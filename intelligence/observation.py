#!/usr/bin/env python3
"""MEIP Observation Engine -- structural extraction from raw CSV/Excel files.

First slice of the "raw files -> report_brief.json" pipeline described in
docs/MEIP_ARCHITECTURE.md's intended pipeline. Scope, stated explicitly:
CSV and single-sheet Excel only. No screenshots/OCR, no Word/PDF, no
multi-sheet handling yet -- those are meaningfully different problems
(vision-based extraction for images, different parsers per format) and
belong in later slices, not bolted onto this one.

This module does ONE thing: read a raw tabular file and describe its
structure -- headers, column types, detected table shape, raw cell values
with row/column provenance. It does NOT interpret, does NOT compute
totals, does NOT decide direction (favorable/unfavorable), does NOT
generate narrative text. Per AGENTS.md's zero-fabrication rule, observation
must stay strictly structural; any inference belongs in normalise.py
(clearly labelled DERIVED) or later, never silently here.

Currently detects one shape: a two-column "label, numeric value" table
(header row + 2+ data rows, first column all non-empty strings, second
column all numeric). Anything else is reported as an unclassified region,
not guessed at.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


def _col_letter(idx: int) -> str:
    """0-based column index -> Excel-style letter (0 -> A, 25 -> Z, 26 -> AA)."""
    letter = ""
    idx += 1
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        letter = chr(65 + rem) + letter
    return letter


def _is_numeric_series(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series) and series.notna().all()


def _is_label_series(series: pd.Series) -> bool:
    return series.notna().all() and series.astype(str).str.strip().ne("").all()


def detect_label_value_table(df: pd.DataFrame, sheet: str | None) -> dict[str, Any] | None:
    """Detect a two-column [label, numeric value] shape. Returns a structural
    observation (no interpretation) or None if the shape doesn't match --
    callers must not force a different-shaped table through this detector."""
    if df.shape[1] != 2 or df.shape[0] < 2:
        return None
    label_col, value_col = df.columns[0], df.columns[1]
    if not _is_label_series(df[label_col]):
        return None
    if not _is_numeric_series(df[value_col]):
        return None

    rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        rows.append({
            "label": str(row[label_col]).strip(),
            "value": float(row[value_col]),
            "cell_ref": f"{_col_letter(0)}{i + 2}:{_col_letter(1)}{i + 2}",  # +2: header row + 1-based
        })

    return {
        "shape": "label_value_table",
        "sheet": sheet,
        "label_header": str(label_col).strip(),
        "value_header": str(value_col).strip(),
        "row_count": len(rows),
        "rows": rows,
    }


def observe_dataframe(df: pd.DataFrame, sheet: str | None) -> dict[str, Any]:
    table = detect_label_value_table(df, sheet)
    if table is not None:
        return {"tables": [table], "unclassified": []}

    return {
        "tables": [],
        "unclassified": [{
            "sheet": sheet,
            "shape": df.shape,
            "columns": [str(c) for c in df.columns],
            "reason": "does not match any currently-detected shape (label_value_table is the only one implemented) "
            "-- not guessed at; add a new detector rather than force a bad fit here.",
        }],
    }


def observe_file(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        result = observe_dataframe(df, sheet=None)
    elif path.suffix.lower() in (".xlsx", ".xls"):
        sheets = pd.read_excel(path, sheet_name=None)
        if len(sheets) > 1:
            raise ValueError(
                f"{path} has {len(sheets)} sheets ({', '.join(sheets)}) -- multi-sheet Excel files are out of "
                f"scope for this slice of the observation engine. Split into single-sheet files or extend "
                f"observe_file() to handle multiple sheets explicitly."
            )
        (sheet_name, df), = sheets.items()
        result = observe_dataframe(df, sheet=sheet_name)
    else:
        raise ValueError(f"{path.suffix} is not supported -- this slice of the observation engine reads .csv, "
                          f".xlsx, .xls only. Screenshots, Word, and PDF are separate, later work.")

    return {
        "source_file": str(path),
        **result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source_file", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        observation = observe_file(args.source_file)
    except ValueError as e:
        print(f"OBSERVATION FAILED — {e}")
        return 1

    output_path = args.output or Path("output") / f"{args.source_file.stem}_observation.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(observation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"OBSERVATION WRITTEN — {output_path}")
    print(f"  {len(observation['tables'])} table(s) detected, {len(observation['unclassified'])} unclassified region(s)")
    for t in observation["tables"]:
        print(f"  - {t['shape']}: {t['row_count']} rows, columns [{t['label_header']}, {t['value_header']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
