#!/usr/bin/env python3
"""Render a validated report_brief.json to PDF + one PNG per page.

Runs pipeline/validate.py's checks in-process before rendering anything -- this
is a real gate, not a convention: an unvalidated or reconciliation-failing
document cannot reach the template/chart code no matter how this script is
invoked. Citation and narrative checks are still separate steps you should run
yourself (pipeline/citation_check.py, pipeline/narrative_review.py); they are
not part of this gate.
All chart geometry (bar heights, line points, axis scales) is computed here in
plain Python, not in the template -- one place where numbers turn into pixels,
so what's drawn always matches what's in the data.
"""
import argparse
import json
import sys
from pathlib import Path

import jinja2
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent.parent
TEMPLATES = ROOT / "templates"
import os
CHROMIUM_PATH = os.environ.get("CHROMIUM_PATH", "/opt/pw-browsers/chromium")

FAVORABLE = "#2e9e6d"
UNFAVORABLE = "#d6455a"
NEUTRAL = "#6b7280"
NAVY = "#0b1f3a"

PAGE_W, PAGE_H = 1600, 900
CHART_W, CHART_H = 720, 260


def direction_of(value):
    if value > 0:
        return "favorable"
    if value < 0:
        return "unfavorable"
    return "neutral"


def format_number(value, signed=False):
    """Jinja filter: comma-thousands numeric formatting for template display.

    Whole numbers render with no decimals (615760 -> "615,760"); non-whole
    numbers keep up to 2 decimals (28.6667 -> "28.67"). Strings and other
    non-numeric values pass through unchanged so labels/units in the same
    field never break this filter.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    sign = "+" if signed else ""
    if float(value).is_integer():
        return f"{value:{sign},.0f}"
    return f"{value:{sign},.2f}"


def build_kpi_strip(section):
    return {**section, "layout_class": "full"}


def build_breakdown_table(section):
    bd = section["breakdown"]
    mode = bd.get("mode", "share")
    parent_value = bd["parent_total"]["value"]
    components = []
    for c in bd["components"]:
        pct = c.get("pct_of_parent")
        # Auto-deriving value/parent_total only makes sense in share mode
        # (parts of one whole). In variance mode, a percentage is vs each
        # component's own base and must be supplied explicitly, not derived
        # against the aggregate total -- see validate.py for why.
        if pct is None and parent_value and mode == "share":
            pct = c["value"] / parent_value * 100
        direction = direction_of(c["value"]) if mode == "variance" else "neutral"
        components.append({**c, "pct_of_parent": pct, "direction": direction})
    return {
        **section,
        "layout_class": section.get("layout_width", "half"),
        "title": bd["title"],
        "unit": bd["unit"],
        "mode": mode,
        "label_header": section.get("label_header", "Item"),
        "components": components,
        "parent_label": bd["parent_total"]["label"],
        "parent_value": parent_value,
    }


def build_waterfall(section):
    bd = section["breakdown"]
    parent_value = bd["parent_total"]["value"]
    components = bd["components"]

    running = 0.0
    steps = []
    for c in components:
        steps.append((running, running + c["value"], c["value"]))
        running += c["value"]

    extents = [0.0, parent_value] + [e for step in steps for e in step[:2]]
    max_abs = max(abs(e) for e in extents) or 1.0

    plot_h = 150
    zero_y = 55
    scale = plot_h / max_abs

    def y_of(v):
        return zero_y - v * scale

    n = len(components) + 1
    col_w = CHART_W / n
    bar_w = col_w * 0.5

    bars = []
    for i, (c, (start, end, delta)) in enumerate(zip(components, steps)):
        top_y = min(y_of(start), y_of(end))
        height = abs(y_of(end) - y_of(start))
        x = i * col_w + (col_w - bar_w) / 2
        color = UNFAVORABLE if delta < 0 else FAVORABLE
        pct = c.get("pct_of_parent")
        label_bits = [f"{delta:+.1f}{bd['unit']}".replace(bd["unit"], "").strip() + bd["unit"]]
        if pct is not None:
            label_bits.append(f"({pct:+.2f}%)")
        bars.append({
            "x": x, "y": top_y, "width": bar_w, "height": max(height, 2),
            "color": color, "label": c["label"],
            "value_label": " ".join(label_bits),
            "value_y": top_y - 8 if delta < 0 else top_y - 8,
        })

    total_top = min(y_of(0), y_of(parent_value))
    total_height = abs(y_of(parent_value) - y_of(0))
    total_x = (n - 1) * col_w + (col_w - bar_w) / 2
    bars.append({
        "x": total_x, "y": total_top, "width": bar_w, "height": max(total_height, 2),
        "color": NAVY, "label": bd["parent_total"]["label"],
        "value_label": f"{parent_value:+.1f}{bd['unit']}",
        "value_y": total_top - 8,
    })

    return {
        **section,
        "layout_class": section.get("layout_width", "half"),
        "title": bd["title"],
        "unit": bd["unit"],
        "zero_y": zero_y,
        "bars": bars,
    }


def build_time_series_chart(section):
    ts = section["time_series"]
    all_values = [v for s in ts["series"] for v in s["values"] if v is not None]
    lo, hi = min(all_values), max(all_values)
    if lo == hi:
        lo, hi = lo - 1, hi + 1
    pad = (hi - lo) * 0.1
    lo, hi = lo - pad, hi + pad

    plot_top, plot_bottom = 20, 220
    plot_left, plot_right = 30, 700
    n_cat = len(ts["categories"])

    def x_of(i):
        return plot_left + (i * (plot_right - plot_left) / max(n_cat - 1, 1))

    def y_of(v):
        return plot_bottom - (v - lo) / (hi - lo) * (plot_bottom - plot_top)

    gridlines = []
    for frac in (0, 0.5, 1):
        val = lo + frac * (hi - lo)
        gridlines.append((y_of(val), f"{val:.0f}{ts.get('unit', '')}"))

    step = max(1, n_cat // 6)
    cat_ticks = [(x_of(i), cat) for i, cat in enumerate(ts["categories"]) if i % step == 0]

    palette = [NAVY, "#c9781f", FAVORABLE, UNFAVORABLE, "#5b7fa6"]
    series_out = []
    for i, s in enumerate(ts["series"]):
        pts = [(x_of(j), y_of(v)) for j, v in enumerate(s["values"]) if v is not None]
        last_x, last_y = pts[-1]
        series_out.append({
            "name": s["name"],
            "color": palette[i % len(palette)],
            "points": " ".join(f"{x:.1f},{y:.1f}" for x, y in pts),
            "dot_points": pts,
            "last_y": last_y,
            "last_label": f"{s['values'][-1]:.2f}{ts.get('unit', '')}",
        })

    return {
        **section,
        "layout_class": section.get("layout_width", "half"),
        "title": ts["title"],
        "unit": ts.get("unit", ""),
        "gridlines": gridlines,
        "cat_ticks": cat_ticks,
        "series": series_out,
    }


def build_bar_chart(section):
    bc = section["bar_chart"]
    values = bc["values"]
    max_abs = max((abs(v) for v in values), default=1.0) or 1.0
    has_negative = any(v < 0 for v in values)

    # Bars can go either direction (variance-style data), not just up from a
    # floor (count-style data) -- baseline sits in the middle when there are
    # negative values so both directions have their own room within the 260
    # viewBox, and scale is driven by the largest magnitude in either
    # direction, not just max(values), or a large negative value would be
    # invisible (see comment history for why this changed).
    if has_negative:
        plot_h = 80          # max bar extent from baseline, either direction
        baseline_y = 120     # leaves room above for +value labels, below for -bars + their labels + category row
        category_label_y = 235
    else:
        plot_h = 160
        baseline_y = 200
        category_label_y = baseline_y + 18
    scale = plot_h / max_abs

    n = len(values)
    col_w = CHART_W / n
    bar_w = col_w * 0.55

    ann_by_cat = {a["category"]: a for a in bc.get("annotations", [])}
    colors = {"peak": "#ff6a00", "recovery": FAVORABLE, "note": NAVY}

    bars = []
    for i, (cat, val) in enumerate(zip(bc["categories"], values)):
        h = abs(val) * scale
        x = i * col_w + (col_w - bar_w) / 2
        y = baseline_y - h if val >= 0 else baseline_y
        value_y = (y - 8) if val >= 0 else (y + h + 16)
        ann = ann_by_cat.get(cat)
        color = colors.get(ann["emphasis"], NAVY) if ann else (UNFAVORABLE if val < 0 else NAVY)
        bars.append({
            "x": x, "y": y, "width": bar_w, "height": max(h, 2),
            "color": color, "label": cat,
            "value_label": f"{format_number(val)}{bc.get('unit', '')}",
            "value_y": value_y,
            "annotation": ann["label"] if ann else None,
        })

    return {
        **section,
        "layout_class": section.get("layout_width", "half"),
        "category_label_y": category_label_y,
        "title": bc["title"],
        "unit": bc.get("unit", ""),
        "baseline_y": baseline_y,
        "bars": bars,
    }


def build_ranking(section):
    rankings = []
    for r in section["rankings"]:
        numeric = [it["value"] for it in r["items"] if isinstance(it.get("value"), (int, float))]
        max_val = max((abs(v) for v in numeric), default=1) or 1
        items = []
        for it in r["items"]:
            pct_width = 100.0
            bar_class = "unfavorable"
            if isinstance(it.get("value"), (int, float)):
                pct_width = max(abs(it["value"]) / max_val * 100, 4)
                # Rankings are usually magnitude-only (top drivers), where red
                # is the right default. But a delta-style ranking (e.g. change
                # vs a prior period) mixes signs, and a negative value there
                # is an improvement, not a problem -- coloring it the same
                # alarm-red as a positive regression would misread as bad news.
                if it["value"] < 0:
                    bar_class = "favorable"
            items.append({**it, "pct_width": pct_width, "bar_class": bar_class})
        # note: template uses r.entries, not r.items -- Jinja's dot-access on a
        # plain dict resolves to dict.items() (the builtin method) before it
        # falls back to key lookup, so a key literally named "items" is unreachable.
        rankings.append({**r, "entries": items})
    return {**section, "layout_class": section.get("layout_width", "half"), "rankings": rankings}


def build_external_events(section):
    return {**section, "layout_class": section.get("layout_width", "half"), "events": section["external_events"]}


def build_executive_facts(section):
    return {**section, "layout_class": section.get("layout_width", "half"), "facts": section["executive_facts"]}


def build_executive_summary(section):
    return {**section, "layout_class": "full"}


def build_bottom_insight(section):
    return {**section, "layout_class": "full"}


def build_custom_html(section):
    return {**section, "layout_class": section.get("layout_width", "half")}


BUILDERS = {
    "kpi_strip": build_kpi_strip,
    "breakdown_table": build_breakdown_table,
    "waterfall": build_waterfall,
    "time_series_chart": build_time_series_chart,
    "bar_chart": build_bar_chart,
    "ranking": build_ranking,
    "external_events": build_external_events,
    "executive_facts": build_executive_facts,
    "executive_summary": build_executive_summary,
    "bottom_insight": build_bottom_insight,
    "custom_html": build_custom_html,
}


def paginate(sections):
    pages = [[]]
    for section in sections:
        if section.get("new_page") and pages[-1]:
            pages.append([])
        pages[-1].append(BUILDERS[section["type"]](section))
    return pages


def render_html(doc):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TEMPLATES)))
    env.filters["num"] = format_number
    template = env.get_template("report.html")
    css = (TEMPLATES / "assets" / "style.css").read_text(encoding="utf-8")
    pages = paginate(doc["sections"])
    return template.render(meta=doc["report_meta"], pages=pages, css=css)


def export(html, out_dir, base_name):
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = (out_dir / f"{base_name}.html").resolve()
    html_path.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        launch_path = CHROMIUM_PATH if os.path.exists(CHROMIUM_PATH) else None
        browser = p.chromium.launch(executable_path=launch_path)
        page = browser.new_page(viewport={"width": PAGE_W, "height": PAGE_H})
        page.goto(html_path.as_uri())
        pdf_path = out_dir / f"{base_name}.pdf"
        page.pdf(path=str(pdf_path), width=f"{PAGE_W}px", height=f"{PAGE_H}px", print_background=True)

        n_pages = page.eval_on_selector_all(".page", "els => els.length")
        png_paths = []
        for i in range(n_pages):
            png_path = out_dir / f"{base_name}_page{i + 1:02d}.png"
            page.locator(".page").nth(i).screenshot(path=str(png_path))
            png_paths.append(png_path)
        browser.close()

    return pdf_path, png_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_brief", type=Path)
    parser.add_argument("--out", type=Path, default=ROOT / "output")
    parser.add_argument(
        "--allow-flags",
        action="store_true",
        help="Don't fail the validation gate on provenance.unresolved_flags (use only when reviewed by hand)",
    )
    args = parser.parse_args()

    doc = json.loads(args.report_brief.read_text(encoding="utf-8"))
    sys.path.insert(0, str(Path(__file__).parent))
    from validate import enforce_gate
    enforce_gate(doc, f"render.py ({args.report_brief})", allow_flags=args.allow_flags)

    html = render_html(doc)
    base_name = args.report_brief.stem
    pdf_path, png_paths = export(html, args.out, base_name)

    print(f"Rendered {pdf_path}")
    for p in png_paths:
        print(f"Rendered {p}")


if __name__ == "__main__":
    main()
