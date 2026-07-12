#!/usr/bin/env python3
"""Export a validated report_brief.json as a plain-language Markdown blueprint.

Use this when you want to hand the exact, reconciled numbers to a different
tool -- ChatGPT image generation, Canva, a human designer -- instead of (or
in addition to) rendering with pipeline/render.py. The point of the
blueprint is that whoever draws the final page is working from an exact
spec, not a vague prompt, so they have nothing left to invent.

Only run this after validate.py has passed.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def render_kpi_strip(section, out):
    out.append(f"### KPI Strip — {section.get('title', '')}".rstrip())
    for k in section["kpis"]:
        line = f"- **{k['label']}**: {k['value']}{k.get('unit', '')}"
        if k.get("comparison_label"):
            line += f"  ({k['comparison_label']}: {k.get('comparison_value', '')})"
        out.append(line)
    out.append("")


def render_breakdown_table(section, out):
    bd = section["breakdown"]
    mode = bd.get("mode", "share")
    out.append(f"### Table — {bd['title']} ({bd['unit']})")
    header = f"| {section.get('label_header', 'Item')} | Value |"
    sep = "|---|---|"
    if mode == "variance":
        header += " Variance |"
        sep += "---|"
    header += " % |"
    sep += "---|"
    out.append(header)
    out.append(sep)
    parent_value = bd["parent_total"]["value"]
    for c in bd["components"]:
        pct = c.get("pct_of_parent")
        # Only derive value/parent_total in share mode -- see validate.py's
        # check_reconciliation for why that ratio is meaningless in variance mode.
        if pct is None and parent_value and mode == "share":
            pct = c["value"] / parent_value * 100
        row = f"| {c['label']} | {c['value']:g} {bd['unit']} |"
        if mode == "variance":
            row += f" {c['value']:+g} {bd['unit']} |"
        row += f" {pct:.2f}% |" if pct is not None else " — |"
        out.append(row)
    total_row = f"| **{bd['parent_total']['label']}** | **{parent_value:g} {bd['unit']}** |"
    if mode == "variance":
        total_row += f" **{parent_value:+g} {bd['unit']}** |"
    total_row += " **100.00%** |" if mode == "share" else " — |"
    out.append(total_row)
    out.append("")


def render_bar_chart(section, out):
    bc = section["bar_chart"]
    out.append(f"### Chart — {bc['title']} ({bc.get('unit', '')})".rstrip())
    ann = {a["category"]: a for a in bc.get("annotations", [])}
    for cat, val in zip(bc["categories"], bc["values"]):
        line = f"- {cat}: {val:g}{bc.get('unit', '')}"
        if cat in ann:
            line += f"  [{ann[cat]['emphasis'].upper()}: {ann[cat]['label']}]"
        out.append(line)
    out.append("")


def render_waterfall(section, out):
    bd = section["breakdown"]
    out.append(f"### Waterfall — {bd['title']} ({bd['unit']})")
    for c in bd["components"]:
        pct = c.get("pct_of_parent")
        pct_str = f" ({pct:+.2f}%)" if pct is not None else ""
        out.append(f"- {c['label']}: {c['value']:+g} {bd['unit']}{pct_str}")
    out.append(f"- **Total — {bd['parent_total']['label']}: {bd['parent_total']['value']:+g} {bd['unit']}**")
    out.append("")


def render_time_series_chart(section, out):
    ts = section["time_series"]
    out.append(f"### Trend — {ts['title']} ({ts.get('unit', '')})".rstrip())
    out.append(f"Categories: {', '.join(ts['categories'])}")
    for s in ts["series"]:
        vals = ", ".join(f"{v:g}{ts.get('unit', '')}" if v is not None else "n/a" for v in s["values"])
        out.append(f"- **{s['name']}**: {vals}")
    for a in ts.get("annotations", []):
        out.append(f"  [{a.get('emphasis', 'note').upper()} at {a['category']}: {a['label']}]")
    out.append("")


def render_ranking(section, out):
    out.append(f"### Ranking — {section.get('title', '')}".rstrip())
    for r in section["rankings"]:
        out.append(f"**{r['scope_label']}**")
        for item in r["items"]:
            val = f" — {item['value']}{item.get('unit', '')}" if item.get("value") is not None else ""
            out.append(f"{item['rank']}. {item['label']}{val}")
    out.append("")


def render_external_events(section, out):
    out.append(f"### External Events — {section.get('title', '')}".rstrip())
    for e in section["external_events"]:
        out.append(f"- **{e['name']}** ({e['type']}{', ' + e['date_or_period'] if e.get('date_or_period') else ''}): {e['description']}")
    out.append("")


def render_executive_facts(section, out):
    out.append(f"### Executive Facts — {section.get('title', '')}".rstrip())
    for f in section["executive_facts"]:
        out.append(f"- {f['statement']}")
    out.append("")


def render_text_block(label):
    def render(section, out):
        out.append(f"### {label} — {section.get('title', '')}".rstrip())
        out.append(section["text"])
        out.append("")
    return render


RENDERERS = {
    "kpi_strip": render_kpi_strip,
    "breakdown_table": render_breakdown_table,
    "bar_chart": render_bar_chart,
    "waterfall": render_waterfall,
    "time_series_chart": render_time_series_chart,
    "ranking": render_ranking,
    "external_events": render_external_events,
    "executive_facts": render_executive_facts,
    "executive_summary": render_text_block("Executive Summary"),
    "bottom_insight": render_text_block("Bottom Insight"),
}


def build_blueprint(doc):
    meta = doc["report_meta"]
    out = [
        f"# {meta['title']}",
        f"*{meta['subtitle']}*",
        "",
        f"**Organization:** {meta.get('organization', '')}  ",
        f"**Period:** {meta['period_label']}  ",
        f"**Report type:** {meta['report_type']}  ",
        f"**Generated:** {meta['generated_date']}",
        "",
        "> Every number below is validated and reconciled against source data "
        "(see `pipeline/validate.py`). Render this exactly as specified — do "
        "not round differently, do not add data points not listed here, and "
        "do not invent a chart shape not described below.",
        "",
        "---",
        "",
    ]
    page = 1
    for i, section in enumerate(doc["sections"]):
        if section.get("new_page") and i > 0:
            page += 1
            out.append(f"## Page {page}")
            out.append("")
        renderer = RENDERERS.get(section["type"])
        if renderer:
            renderer(section, out)
        else:
            out.append(f"### {section['type']} — {section.get('title', '')}".rstrip())
            if section.get("text"):
                out.append(section["text"])
            out.append("")

    notes = doc.get("provenance", {}).get("extraction_notes")
    if notes:
        out += ["---", "", f"**Extraction notes:** {notes}", ""]

    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_brief", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    doc = json.loads(args.report_brief.read_text(encoding="utf-8"))
    blueprint = build_blueprint(doc)

    out_path = args.out or (ROOT / "output" / f"{args.report_brief.stem}_blueprint.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(blueprint, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
