# Executive Report Generation System

This repo turns raw source data (Excel, Word, PDF, PowerPoint, images,
screenshots — in any combination) into executive reports in a consistent
navy/white/orange design, without the two failure modes that motivated it:
data that doesn't reconcile, and numbers that get invented to fill a
placeholder.

It does this by splitting the job into stages that never blur back together:

```
raw files ─▶ report_brief.json ─▶ validated & cited ─▶ executive_analysis.json ─▶ rendered output
(anything)   extraction by AI      validate.py +       intelligence/analyse.py     render.py → PDF/PNG,
             following prompt      citation_check.py   decides what matters        or blueprint.py → .md
```

## Why it's structured this way

The two example decks that motivated this (Makro Week 26, Q1 2026 prep) were
both, on inspection, a single flat AI-generated image per slide with no data
binding at all — that's structurally why numbers drifted and placeholders
showed up. An image model can't enforce "the parts add up to the total"; it
paints something that looks right. This system fixes that by making the
data layer, the narrative, the intelligence layer, and the drawing separate
steps, each checkable on its own:

1. **Extraction** turns messy source files into one structured document
   (`schema/report_brief.schema.json`). This is the only step that needs
   judgment, and it's governed by `prompts/master_system_prompt.md`.
2. **Validation** (`pipeline/validate.py`) is pure code: it checks every
   total equals the sum of its parts, every stated percentage matches its
   computed value, and every citation actually points at something real.
   It fails loudly and specifically rather than rendering around a problem.
3. **Citation check** (`pipeline/citation_check.py`) scans the narrative text
   itself and flags any number that doesn't trace back to the validated
   data — the direct fix for "the report says a number that isn't real."
3b. **Narrative review** (`pipeline/narrative_review.py`) is a heuristic lint,
   not a correctness gate: it checks the MEIP Design Rules that are judgment
   calls rather than arithmetic — no duplicate insights, length limits on the
   summary/bottom-insight, facts that read as interpretation rather than a
   restated number. It warns by default; pass `--strict` to make it fail the
   build.
4. **Executive Intelligence** (`intelligence/analyse.py`) reads only the
   validated brief and produces `executive_analysis.json`: prioritized
   findings, risks, recommended actions and a presentation plan. It does not
   invent numbers; every insight carries supporting evidence back to the
   originating `report_brief.json` data refs.
5. **Intelligence audit** (`intelligence/audit_analysis.py`) verifies that
   every evidence reference in `executive_analysis.json` resolves back to the
   source `report_brief.json` and that explicit evidence values match.
6. **Executive analysis export** (`intelligence/export_analysis.py`) writes a
   human-readable Markdown review pack so you can inspect the AI/business logic
   before rendering.
7. **Output** is either `pipeline/render.py` (renders the validated data into
   your house style as PDF + PNG, deterministically — no chart is ever
   "imagined") or `pipeline/blueprint.py` (exports the same validated data as
   a plain-language Markdown spec you can hand to ChatGPT image generation,
   Canva, or a designer, so that handoff doesn't reopen the fabrication
   problem).

## Why it's adaptable

Every week's report can look and cover different things — different KPIs,
different breakdowns, a report type you haven't run before, or a source
that's itself someone else's PowerPoint. The schema doesn't hard-code a
single report's shape: a report is just an ordered list of `sections`, each
one of a fixed set of general-purpose types (`kpi_strip`, `breakdown_table`,
`waterfall`, `bar_chart`, `time_series_chart`, `ranking`, `external_events`,
`executive_facts`, `executive_summary`, `bottom_insight`, `custom_html`).
A new report type is a new combination/order of these, not a new system.
If you hit a genuinely new visual need, that's a real, occasional extension
to the schema + a new Jinja template in `templates/components/` — not
something that should happen per-report.

## Running it

```bash
pip install -r requirements.txt

# Full quality-gated run: validate → cite → review → analyse → audit → Markdown review pack
python3 pipeline/run_report.py examples/otd_daily_impact_demo.json

# Full run plus rendered PDF/PNG and Markdown blueprint
python3 pipeline/run_report.py examples/otd_daily_impact_demo.json --render --blueprint

# Individual gates remain available when debugging a specific stage
python3 pipeline/validate.py examples/otd_daily_impact_demo.json
python3 pipeline/citation_check.py examples/otd_daily_impact_demo.json
python3 pipeline/narrative_review.py examples/otd_daily_impact_demo.json
python3 intelligence/analyse.py examples/otd_daily_impact_demo.json
python3 intelligence/validate_analysis.py output/otd_daily_impact_demo_executive_analysis.json
python3 intelligence/audit_analysis.py examples/otd_daily_impact_demo.json output/otd_daily_impact_demo_executive_analysis.json
python3 intelligence/export_analysis.py output/otd_daily_impact_demo_executive_analysis.json
python3 pipeline/render.py examples/otd_daily_impact_demo.json
python3 pipeline/blueprint.py examples/otd_daily_impact_demo.json
```

`examples/otd_daily_impact_demo.json` is hand-authored illustrative data
(clearly labeled as such in the document itself) that exercises every
section type — use it as a reference for the shape of a real brief, not as
real numbers.

## The weekly workflow

1. Hand Claude the week's source files and the business context (events,
   strikes, promotions, etc. — anything in `external_events`), with
   `prompts/master_system_prompt.md` as the operating instructions.
2. Claude extracts into a new `report_brief.json` — nothing rendered yet.
3. Run `pipeline/run_report.py <report_brief.json>`. Any failure means going
   back to the extraction/source data, not adjusting numbers to force a pass.
4. Review the generated `output/*_executive_analysis.md` to confirm the story,
   risks, actions and presentation plan make business sense.
5. When all gates pass, render or export a blueprint.

## Repo layout

```
schema/report_brief.schema.json        the data contract — read this to see every field a report can use
schema/executive_analysis.schema.json  the intelligence-layer contract for findings, risks, actions and presentation plan
pipeline/refs.py                       resolves "sections[2].breakdown.components[0].value" style citations
pipeline/validate.py                   reconciliation gate — run first, always
pipeline/citation_check.py             anti-fabrication scanner for narrative text
pipeline/narrative_review.py           heuristic lint for MEIP Design Rules (duplication, length, interpretation)
pipeline/run_report.py                 full quality-gated run coordinator
pipeline/render.py                     report_brief.json → PDF + PNG (Playwright + Chromium)
pipeline/blueprint.py                  report_brief.json → Markdown spec for handoff to another tool
intelligence/analyse.py                report_brief.json → executive_analysis.json
intelligence/export_analysis.py        executive_analysis.json → Markdown review pack
intelligence/insight_rules.py          deterministic executive rules for target misses, concentration, peaks and events
intelligence/blueprint_planner.py      decides which sections deserve executive attention and why
intelligence/validate_analysis.py      validates executive_analysis.json against schema
intelligence/audit_analysis.py         proves executive_analysis evidence refs resolve back to report_brief.json
templates/                             the navy/white/orange design system (Jinja2 + CSS + inline SVG charts)
prompts/master_system_prompt.md        the instructions that govern extraction + narrative
examples/                              sample report_brief.json (illustrative demo data only)
output/                                generated PDFs/PNGs/blueprints/analysis land here
```
