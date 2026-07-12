# Repository Agent Instructions

These instructions apply repository-wide.

## Core MEIP Rules

- MEIP means Massmart Executive Intelligence Platform.
- The repository is authoritative for claims about what is currently implemented.
- The approved MEIP master context is authoritative for intended product direction.
- Differences between intended architecture and current implementation must be explicitly recorded.

## Zero-Fabrication and Evidence

- Do not invent metrics, source values, citations, business events, owners, explanations, or recommendations.
- Every numeric claim, material statement, chart input, and executive conclusion must trace to approved evidence or be labelled with the correct evidence status.
- Preserve source lineage when transforming data through briefs, analysis, blueprints, and rendered outputs.
- Interpretations and recommendations must not be represented as verified facts.

## Validation Gates

- Validate data, citations, narrative, intelligence outputs, and blueprints before rendering.
- No report page, section, or visual may progress to rendering until its blueprint has been validated against approved evidence.
- If validation fails, fix the source, extraction, schema, or blueprint issue rather than rendering around it.

## Tests and Documentation

- Run relevant repository checks for changed code, schemas, examples, prompts, or documentation.
- For documentation-only changes, run at least formatting/diff checks where applicable.
- Update documentation when behaviour, contracts, workflow, validation gates, or architecture change.
- Report commands run, tests run, risks, and unresolved issues in final handoffs.

## Branch and Collaboration Rules

- Inspect the repository before implementation and reuse existing components before creating duplicates.
- Do not push directly to `main` or `meip/executive-intelligence-engine`.
- All implementation and documentation changes must use a dedicated task branch.
- Codex branches must use `codex/<task-name>`.
- Claude branches must use `claude/<task-name>`.
- Keep Claude and Codex work on separate branches unless a human explicitly coordinates a shared branch.
- Do not let multiple agents edit the same task area simultaneously without an explicit handoff.
- Before merging, use pull-request review to confirm scope, evidence, tests, and unresolved risks.
- Do not merge a pull request without human approval.
- Do not delete, rewrite, rebase, or force-push another agent's branch.
- Never commit credentials, tokens, API keys, passwords, confidential source files, or generated secrets.
- After another agent's changes merge, update from the target branch and re-check affected files before continuing.
