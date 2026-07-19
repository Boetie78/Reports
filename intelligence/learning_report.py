#!/usr/bin/env python3
"""MEIP Learning Report -- aggregate learning/decisions.jsonl into patterns.

Reads every record intelligence/learning_log.py has appended (across however
many report cycles) and summarises them by rule_family and category, so a
human can see which insight_rules.py rules are earning trust (high accepted
rate) versus which need retuning or retirement (high challenged rate).
This tool only surfaces patterns -- per MEIP_MASTER_CONTEXT.md's Principle 5
and AGENTS.md's human-review requirement, nothing here modifies
insight_rules.py, executive_qa.py thresholds, or any other file automatically.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
LOG_PATH = ROOT / "learning" / "decisions.jsonl"

# Below this many logged decisions for a rule_family, a challenge rate is
# noise, not signal -- don't recommend retuning off two data points.
MIN_SAMPLE_FOR_FLAG = 3
CHALLENGE_RATE_FLAG_THRESHOLD = 0.4


def load_entries(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    entries = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def summarise_by_rule_family(entries: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for e in entries:
        if e["decision"] == "missing":
            continue  # no rule_family by definition; handled separately
        family = e.get("rule_family") or "unknown_rule"
        counts[family][e["decision"]] += 1
    return counts


def print_rule_family_summary(counts: dict[str, dict[str, int]]) -> None:
    print("=== By rule family (accepted/challenged/effective/failed) ===\n")
    if not counts:
        print("  No non-'missing' decisions logged yet.\n")
        return
    for family in sorted(counts):
        c = counts[family]
        scored = c.get("accepted", 0) + c.get("challenged", 0)
        challenge_rate = c.get("challenged", 0) / scored if scored else None
        total = sum(c.values())
        line = f"  {family}: {total} logged"
        parts = [f"{k}={v}" for k, v in sorted(c.items())]
        line += f" ({', '.join(parts)})"
        if challenge_rate is not None:
            line += f" -- challenge rate {challenge_rate:.0%}"
            if scored >= MIN_SAMPLE_FOR_FLAG and challenge_rate >= CHALLENGE_RATE_FLAG_THRESHOLD:
                line += "  [FLAG: consider reviewing this rule in insight_rules.py]"
        print(line)
    print()


def print_missing_summary(entries: list[dict[str, Any]]) -> None:
    missing = [e for e in entries if e["decision"] == "missing"]
    print(f"=== Missing insights ({len(missing)} logged) ===\n")
    if not missing:
        print("  None logged -- no signal yet that a new insight_rules.py rule is needed.\n")
        return
    print("  Each of these is a human-observed gap: something worth surfacing that no")
    print("  current rule in insight_rules.py generates. Repeated similar entries here")
    print("  are the strongest signal for a genuinely new rule, not a tuning tweak.\n")
    for e in missing:
        print(f"  - [{e['timestamp'][:10]}] {e['title']}")
        print(f"      {e['note']}")
    print()


def print_effectiveness_summary(entries: list[dict[str, Any]]) -> None:
    retrospective = [e for e in entries if e["decision"] in ("effective", "failed")]
    print(f"=== Retrospective outcomes ({len(retrospective)} logged) ===\n")
    if not retrospective:
        print("  None logged yet -- these are typically recorded a cycle or more after")
        print("  an item was accepted, once its recommended action's real outcome is known.\n")
        return
    for e in retrospective:
        print(f"  - [{e['timestamp'][:10]}] {e['decision'].upper()}: {e['title']} ({e.get('rule_family', 'unknown_rule')})")
        print(f"      {e['note']}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--log", type=Path, default=LOG_PATH)
    args = parser.parse_args()

    entries = load_entries(args.log)
    print(f"MEIP LEARNING REPORT — {len(entries)} total decision(s) in {args.log}\n")
    if not entries:
        print("Nothing logged yet. Use intelligence/learning_log.py after reviewing a report's")
        print("executive_qa.json output to start building signal.")
        return 0

    print_rule_family_summary(summarise_by_rule_family(entries))
    print_missing_summary(entries)
    print_effectiveness_summary(entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
