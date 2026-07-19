# MEIP Architecture

This document summarises the verified current architecture of the Massmart Executive Intelligence Platform and separates implemented, partial, planned, and absent capabilities.

It references, rather than replaces, the existing architecture documents:

- `docs/architecture/meip_architecture_blueprint.md`
- `docs/architecture/report_lifecycle.md`
- `docs/MEIP_MASTER_CONTEXT.md`
- `docs/DATA_INTEGRITY_STANDARD.md`
- `docs/EXECUTIVE_INTELLIGENCE_MODEL.md`

## Authority Rule

The repository is authoritative for current implementation claims. The approved MEIP master context is authoritative for intended product direction. Any difference between intended architecture and current implementation must be recorded as implemented, partial, planned, absent, gap, exclusion, or unresolved issue.

## Verified Current Architecture

The repository currently implements a structured report-generation pipeline centred on `report_brief.json` inputs. The current path is:

```text
report_brief.json
→ schema validation
→ citation and narrative review
→ executive analysis
→ intelligence validation and audit
→ Markdown review export
→ optional render and/or blueprint export
```

The repository includes:

- schemas for report briefs, executive analysis, executive objects, executive QA, decision plans, and report metadata;
- pipeline modules for validation, citation checks, narrative review, rendering, blueprint export, references, and run orchestration;
- intelligence modules for analysis, audit, extraction helpers, confidence, ownership, urgency, prioritisation, decision support, scoring, and validation;
- Jinja templates and CSS for deterministic report rendering;
- example report briefs for exercising the pipeline.

## Implemented Capabilities

The following capabilities are implemented in the repository now:

- JSON report brief validation against the current schema.
- Reconciliation and citation checks for report brief content.
- Narrative review heuristics for MEIP design-rule issues.
- Executive analysis generation from validated report briefs.
- Executive analysis schema validation and evidence audit.
- Markdown export of executive analysis for human review.
- Deterministic report rendering from validated report briefs.
- Markdown blueprint export from validated report briefs.
- Non-bypassable validation gate: `pipeline/render.py` and `pipeline/blueprint.py` both run the full `pipeline/validate.py` check set in-process before producing any output, regardless of how they are invoked (standalone or via `pipeline/run_report.py`).
- Executive QA challenge of Page 1/Page 2 decision-plan placements (`intelligence/executive_qa.py`): independently re-verifies evidence confidence per placement tier, and checks causal-language overreach, business-impact hedging, ownership assignment, and action timing against the rules in `docs/EXECUTIVE_INTELLIGENCE_MODEL.md`. Monitor/Appendix/Ignore items are out of scope, since they are not shown to executives. Like narrative review, this is a challenge/lint layer (prints findings, exits 0 by default, `--strict-qa` available) -- it does not gate rendering the way `pipeline/validate.py` does.
- Example report briefs demonstrating supported section types.

## Partially Implemented Capabilities

The following capabilities are present in some form but should not be treated as complete platform capability without qualification:

- Executive decision support exists through current intelligence modules and schemas, but full decision governance remains broader than the implemented code.
- Executive QA (`intelligence/executive_qa.py`) checks evidence confidence, causal overreach, impact hedging, ownership, and action timing, but does not yet check whether an interpretation considered and ruled out alternative explanations -- that specific challenge from the original planned scope is still open.
- Blueprint generation exists as Markdown export, and reconciliation/schema/citation-ref/event-incorporation validation is now a non-bypassable gate ahead of both render and blueprint export. Full validation against the approved page/section *evidence* checklist (evidence-status labelling per section) is not yet enforced, since evidence-status fields are not yet part of the schema -- see "Absent Capabilities" below.
- Narrative review exists as heuristic linting, but it is not a complete semantic proof of executive quality or factual correctness.
- Evidence auditing exists for analysis references, but the complete evidence-status model is newly documented and not yet fully embedded across all schemas and runtime checks.
- Evidence-status is now a real, optional field (`schema/report_brief.schema.json`'s `evidenceStatus` definition, attached to kpi/breakdown-component/executive_fact/external_event/section) with real enforcement in `pipeline/validate.py`: USER_CONFIRMED/PARTIALLY_VERIFIED/CONFLICTING/MISSING/NOT_APPLICABLE all require a note, and CONFLICTING/MISSING block rendering (same `--allow-flags` override as `provenance.unresolved_flags`). It also now propagates one tier further: `intelligence/extractors.py` and `intelligence/insight_rules.py` carry it from report_brief kpis/breakdown-components/external_events into `executive_analysis.json` findings' `supporting_evidence` (schema-accepted in both `schema/executive_analysis.schema.json` and `schema/executive_object.schema.json`, and passed through unchanged into `prioritised_analysis.json` by the existing `executive_object.py` copy). `intelligence/audit_analysis.py` independently verifies any evidence_status claimed in the analysis actually matches the source report_brief.json (catches fabrication and drift, not just absence). `intelligence/executive_qa.py` uses the real status when present (CONFLICTING/MISSING escalate straight to Hold; PARTIALLY_VERIFIED/USER_CONFIRMED require hedged wording) and falls back to its confidence-based wording heuristics only when nothing has been propagated for that object yet. Not yet done: retrofitting evidence_status onto existing example reports beyond the one demonstration case, and no rendered output (HTML/PDF) visually surfaces it yet.
- Raw extraction helper code exists, but it does not constitute a complete raw-file ingestion platform.

## Planned Capabilities

The following capabilities are approved intended direction or described by architecture documents, but must not be claimed as fully implemented until supported by repository code and tests:

- Observation engine for identifying tables, KPIs, entities, trends, and unresolved extraction questions from raw material.
- Normalisation engine that converts observations into governed report briefs with explicit provenance.
- Dedicated blueprint validation gate enforcing required page/section fields before rendering.
- Evidence-status visibility in rendered output (HTML/PDF) and Markdown blueprint export -- the status now flows correctly through report_brief -> executive_analysis -> prioritised_analysis (see Implemented Capabilities), but pipeline/render.py and pipeline/blueprint.py do not yet display it anywhere on the page.
- Learning loop that records accepted, challenged, missing, effective, and failed report elements for future profile updates.

## Absent Capabilities and Current Gaps

The current repository does not yet implement a complete raw-file ingestion layer for Excel, Word, PowerPoint, PDF, screenshots, images, emails, or meeting notes.

Current examples and commands assume a structured `report_brief.json` already exists. Therefore, the raw-file ingestion gap must be recorded whenever describing end-to-end MEIP capability:

```text
raw files → observation → normalisation → report_brief.json
```

is intended architecture, while the verified current implementation begins at:

```text
report_brief.json
```

Do not claim that MEIP currently performs complete raw-file extraction, observation, or normalisation unless future code implements and validates those capabilities.

## Intended Pipeline

The intended MEIP pipeline is:

```text
Raw source material
→ Observation
→ Normalisation
→ Validation
→ Executive Intelligence
→ Decision and QA
→ Blueprint and Design
→ Blueprint Validation
→ Rendering
→ Human Review
→ Learning
```

The current repository implements meaningful parts from validation through rendering and blueprint export once a structured report brief is supplied. Earlier raw-file ingestion and later learning-loop capabilities remain planned or partial as described above.

## Relationship to Existing Architecture Documents

Use `docs/architecture/meip_architecture_blueprint.md` for the broader lifecycle and layer descriptions. Use `docs/architecture/report_lifecycle.md` for the report workflow. Use this document to distinguish current repository implementation from intended MEIP architecture.
