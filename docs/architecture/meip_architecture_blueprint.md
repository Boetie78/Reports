# MEIP Architecture Blueprint

MEIP is not only a report renderer. It is an Executive Intelligence Platform.

The platform's purpose is to convert messy operational/business source material into trusted executive decision support while preserving three non-negotiables:

1. **No fabricated numbers** — every number must exist in validated source data.
2. **Traceable reasoning** — every finding, risk and action must point back to evidence.
3. **Executive usefulness** — the system must decide what matters, not merely describe what exists.

## Operating Model

MEIP follows this lifecycle:

```text
Observe
↓
Normalise
↓
Validate
↓
Understand
↓
Decide
↓
Challenge
↓
Plan
↓
Render
↓
Review
↓
Learn
```

Each layer has a clear contract and must not blur into another layer.

## 1. Observation Engine

**Purpose:** Identify what source material contains without interpreting it.

Inputs:

- Excel files
- Word documents
- PowerPoint decks
- PDFs
- screenshots/images
- meeting notes
- manual context

Outputs:

- observed entities
- candidate KPIs
- candidate tables
- candidate trends
- candidate events
- unresolved extraction questions

Future contract:

```text
observation.json
```

Rules:

- Do not analyse yet.
- Do not decide what matters yet.
- Do not invent missing fields.
- Mark ambiguity explicitly.

## 2. Normalisation Engine

**Purpose:** Convert observations into the current source-of-truth schema.

Current contract:

```text
report_brief.json
schema/report_brief.schema.json
```

Responsibilities:

- Map KPIs to structured objects.
- Map tables to breakdowns, rankings or charts.
- Map events to `external_events`.
- Map narrative facts to `executive_facts`.
- Preserve provenance and unresolved flags.

Rules:

- If a value cannot be sourced, it must not enter the brief.
- If a total/component mismatch exists, do not repair silently.
- If a field is unknown, leave it out or flag it.

## 3. Validation Engine

**Purpose:** Stop bad data before intelligence or rendering.

Current modules:

```text
pipeline/validate.py
pipeline/citation_check.py
pipeline/narrative_review.py
```

Responsibilities:

- Check schema compliance.
- Check totals equal components.
- Check stated percentages match computed percentages.
- Check all data refs resolve.
- Check external events are actually incorporated.
- Check narrative numbers exist in the validated brief.

Rule:

```text
If validation fails, stop. Never render around the issue.
```

## 4. Executive Intelligence Engine

**Purpose:** Turn validated data into executive meaning.

Current modules:

```text
intelligence/analyse.py
intelligence/insight_rules.py
intelligence/extractors.py
```

Current contract:

```text
executive_analysis.json
schema/executive_analysis.schema.json
```

Responsibilities:

- Identify material findings.
- Identify risks.
- Identify opportunities.
- Recommend actions.
- Produce a primary executive message.
- Attach evidence to every conclusion.

Rule:

```text
The intelligence layer may interpret validated data, but may never create new numbers.
```

## 5. Decision Engine

**Purpose:** Decide what deserves executive attention.

This is the next major build layer.

Decision questions:

- Is this above or below an executive threshold?
- Is the movement material?
- Is the issue concentrated enough to act on?
- Is this a one-off event or a systemic signal?
- Would a VP/COO ask about this?
- Does this require a decision, escalation or action owner?

Future contract:

```text
decision_plan.json
```

Initial decision examples:

```text
If OTD < target: show on Page 1.
If one driver contributes >40% of impact: show as concentration risk.
If a metric moves but remains within tolerance: deprioritise.
If an event explains performance but recovery is unproven: show as risk, not excuse.
```

## 6. Executive QA Engine

**Purpose:** Challenge MEIP's own conclusions before they reach leadership.

QA questions:

- What evidence supports this statement?
- Could there be an alternative explanation?
- Does any other data contradict it?
- Is the wording stronger than the evidence allows?
- Is the issue operational, external, commercial, system-driven or unknown?
- Is the action specific enough for ownership?

Future contract:

```text
executive_qa.json
```

Rules:

- Downgrade confidence where evidence is incomplete.
- Flag unsupported causality.
- Separate "linked to" from "caused by".
- Never turn an external event into an excuse unless recovery evidence exists.

## 7. Blueprint and Design Engine

**Purpose:** Decide how to communicate the intelligence.

Current modules:

```text
intelligence/blueprint_planner.py
pipeline/blueprint.py
pipeline/render.py
templates/
```

Responsibilities:

- Select the right components.
- Prioritise sections.
- Create a presentation plan.
- Render data-bound charts/cards/tables.

Design questions:

- Should this be a KPI card, trend, ranking, waterfall, heatmap or risk box?
- What belongs on Page 1?
- What should move to appendix?
- What is the single leadership takeaway?

Rules:

- Design must be driven by validated data and executive priority.
- Visuals are rendered by code, not imagined by image generation.
- The house style must remain consistent.

## 8. Review and Learning Engine

**Purpose:** Capture human feedback and improve future reports.

Future inputs:

- user feedback
- executive feedback
- preferred chart choices
- rejected language
- preferred thresholds
- recurring business rules

Future contract:

```text
learning_profile.json
```

Examples:

```text
Always compare OTD to 95% target.
Do not show revenue unless supplied by the source data.
Separate event-driven issues from controllable operational failures.
Use Gqeberha, not Port Elizabeth, unless source uses the old name.
```

## Current Implemented State

Implemented:

- `report_brief.json` schema
- validation gate
- citation check
- narrative review
- deterministic executive analysis
- executive analysis schema
- executive analysis traceability audit
- executive analysis Markdown export
- pipeline runner
- HTML/CSS renderer
- Markdown blueprint export

Not yet implemented:

- observation extraction schema
- decision engine
- executive QA engine
- learning profile
- report-type plugin registry
- automated tests/CI

## Next Build Priorities

1. Build the Decision Engine.
2. Build Executive QA.
3. Add tests using the demo report.
4. Add report-type plugin profiles for OTD / Final Mile first.
5. Add learning-profile rules.

## Non-Negotiable MEIP Principle

```text
MEIP may analyse, prioritise, challenge and explain.
MEIP may not invent, estimate, smooth, repair or beautify unsupported data.
```
