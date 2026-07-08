# Report Lifecycle

This document defines the intended lifecycle of a MEIP report from raw files to executive output.

## Stage 0 — Inputs Arrive

Typical inputs:

- operational Excel files
- Power BI exports
- screenshots
- PowerPoint decks
- Word reports
- PDFs
- emails or meeting notes
- manual business context

Required user context:

- reporting period
- audience
- business unit/banner
- target metrics
- known external events
- deadline

## Stage 1 — Observation

MEIP identifies what is present.

Outputs should answer:

- What data tables exist?
- What KPIs exist?
- What time periods exist?
- What entities exist? Stores, couriers, regions, banners, categories.
- What possible events or explanations exist?
- What is missing or ambiguous?

No executive story is written here.

## Stage 2 — Normalisation

MEIP maps observed data into `report_brief.json`.

Rules:

- Use source values only.
- Preserve labels from source where possible.
- Use standard names only when verified.
- Flag ambiguity in provenance.
- Do not create placeholders.

## Stage 3 — Validation

Run:

```bash
python3 pipeline/validate.py <report_brief.json>
python3 pipeline/citation_check.py <report_brief.json>
python3 pipeline/narrative_review.py <report_brief.json>
```

Validation must pass before intelligence runs.

## Stage 4 — Executive Intelligence

Run:

```bash
python3 intelligence/analyse.py <report_brief.json>
```

MEIP generates:

- primary message
- findings
- risks
- opportunities
- recommended actions
- presentation plan
- source values used

## Stage 5 — Intelligence Validation and Audit

Run:

```bash
python3 intelligence/validate_analysis.py output/<name>_executive_analysis.json
python3 intelligence/audit_analysis.py <report_brief.json> output/<name>_executive_analysis.json
```

This checks both structure and traceability.

## Stage 6 — Human Review

Run:

```bash
python3 intelligence/export_analysis.py output/<name>_executive_analysis.json
```

Review the Markdown pack before rendering.

Human reviewer should ask:

- Is the primary message correct?
- Are the findings material?
- Are risks overstated?
- Are actions specific enough?
- Is anything important missing?
- Does wording match the evidence?

## Stage 7 — Render or Blueprint

Render:

```bash
python3 pipeline/render.py <report_brief.json>
```

Blueprint:

```bash
python3 pipeline/blueprint.py <report_brief.json>
```

Use render for automated PDF/PNG output. Use blueprint when handing the spec to ChatGPT image generation, Canva, Figma or a designer.

## Stage 8 — Feedback and Learning

After presentation or review, record:

- what the executive accepted
- what was challenged
- what was missing
- what visuals worked
- what visuals failed
- what rules should change next time

This becomes future `learning_profile.json` input.

## Current One-Command Flow

```bash
python3 pipeline/run_report.py <report_brief.json> --render --blueprint
```

This runs the quality gates, executive intelligence layer, analysis audit, Markdown review export and optional output generation.
