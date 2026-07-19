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
- intelligence modules for analysis, audit, extraction helpers, confidence, ownership, urgency, prioritisation, decision support, scoring, validation, executive QA, a human-in-the-loop learning log, and a first-slice observation/normalisation pair (CSV/single-sheet-Excel label-value tables only);
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
- Learning loop (`intelligence/learning_log.py` / `intelligence/learning_report.py`, per MEIP_MASTER_CONTEXT.md Principle 5) exists as a human-in-the-loop decision log, not an automatic self-tuning system -- AGENTS.md's human-review requirement means insight_rules.py/executive_qa.py thresholds are never adjusted automatically from accumulated data. A human records accepted/challenged/effective/failed/missing decisions against real executive objects (looked up from prioritised_analysis.json, not typed freely, to keep the log itself evidence-grounded); `learning_report.py` aggregates by rule family and flags high challenge rates (>=40%, at 3+ samples) and repeated "missing" entries for a human to act on manually. Persisted to `learning/decisions.jsonl`, git-tracked (unlike `output/`, which is regenerable and gitignored).
- Blueprint generation exists as Markdown export, and reconciliation/schema/citation-ref/event-incorporation validation is now a non-bypassable gate ahead of both render and blueprint export. Full validation against the approved page/section *evidence* checklist (evidence-status labelling per section) is not yet enforced, since evidence-status fields are not yet part of the schema -- see "Absent Capabilities" below.
- Narrative review exists as heuristic linting, but it is not a complete semantic proof of executive quality or factual correctness.
- Evidence auditing exists for analysis references, but the complete evidence-status model is newly documented and not yet fully embedded across all schemas and runtime checks.
- Evidence-status is now a real, optional field (`schema/report_brief.schema.json`'s `evidenceStatus` definition, attached to kpi/breakdown-component/executive_fact/external_event/section) with real enforcement in `pipeline/validate.py`: USER_CONFIRMED/PARTIALLY_VERIFIED/CONFLICTING/MISSING/NOT_APPLICABLE all require a note, and CONFLICTING/MISSING block rendering (same `--allow-flags` override as `provenance.unresolved_flags`). It propagates through `intelligence/extractors.py`/`insight_rules.py` into `executive_analysis.json` and `prioritised_analysis.json` (schema-accepted in both, independently audited against the source by `intelligence/audit_analysis.py`, and used by `intelligence/executive_qa.py` in preference to its wording heuristics whenever it's present). It is now also visible in both rendered outputs: `pipeline/render.py` shows a hover-tooltip badge (via `templates/_evidence_flag.html`, styled in `templates/assets/style.css`) next to any KPI, breakdown-table row, executive fact, external event, or section title carrying a non-VERIFIED/DERIVED status, and `pipeline/blueprint.py` shows the same information inline as Markdown since a static document has no hover affordance. VERIFIED/DERIVED and untagged objects render with no visual change, so existing clean reports are unaffected. Not yet done: retrofitting evidence_status onto existing example reports beyond the one demonstration case in `examples/makro_online_cancellation_june2026.json`.
- Raw extraction helper code exists, but it does not constitute a complete raw-file ingestion platform.
- A first, narrow slice of the observation/normalisation engine exists: `intelligence/observation.py` reads a single CSV or single-sheet Excel file and structurally detects exactly one table shape (a two-column label/numeric-value table) with per-row cell provenance -- it does not interpret, does not compute totals, and reports anything else as an explicit unclassified region rather than guessing. `intelligence/normalise.py` maps that one shape into a schema-valid `report_brief.json` breakdown_table section, computing `parent_total` transparently and labelling it `evidence_status: DERIVED` (never VERIFIED) since the source has no total row. Neither script sets `direction`, writes narrative text, or infers anything not structurally present -- that stays intelligence/analyse.py's job downstream, run separately after `pipeline/validate.py` passes. Verified end-to-end: a raw CSV run through observation -> normalise -> validate -> the full `run_report.py` pipeline (including render and blueprint) passes and produces a correct, non-fabricated finding (a genuine 49.81% concentration detection) with zero manually-authored JSON. This is far short of the intended pipeline below -- no multi-table sheets, no KPI/time-series shape detection, no Word/PDF/screenshot/image/email support -- but it is a real, working first step, not documentation of an aspiration.

## Planned Capabilities

The following capabilities are approved intended direction or described by architecture documents, but must not be claimed as fully implemented until supported by repository code and tests:

- Observation engine coverage beyond the current CSV/single-sheet-Excel label-value-table slice: multi-table sheets, KPI/wide-row shapes, time-series shapes, and unresolved-extraction-question surfacing for shapes that don't fit any detector.
- Normalisation engine coverage beyond breakdown_table sections: mapping detected shapes into kpi_strip, time_series_chart, ranking, or other section types.
- Dedicated blueprint validation gate enforcing required page/section fields before rendering.

## Absent Capabilities and Current Gaps

The current repository does not implement raw-file ingestion for Word, PowerPoint, PDF, screenshots, images, emails, or meeting notes at all. For Excel/CSV specifically, only the narrow slice described above (single-sheet, one label/numeric-value table shape) is implemented -- multi-sheet files, multi-table sheets, and any other shape are explicitly out of scope and rejected rather than guessed at (see Partially Implemented Capabilities).

Most current examples and commands still assume a structured `report_brief.json` already exists, since the observation/normalisation slice only covers one input shape. The raw-file ingestion gap must still be recorded whenever describing end-to-end MEIP capability for anything other than that one shape:

```text
raw files → observation → normalisation → report_brief.json
```

is intended architecture for all source formats and shapes. The verified current implementation covers a narrow slice of the left-hand side of that pipeline (CSV/single-sheet-Excel label-value tables only) and begins at `report_brief.json` for everything else:

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
