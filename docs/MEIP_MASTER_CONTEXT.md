# MEIP Master Context

MEIP means **Massmart Executive Intelligence Platform**.

The platform is the product. Every report, report brief, intelligence artefact, blueprint, rendered page, validation rule, and review cycle must improve the Massmart Executive Intelligence Platform rather than existing as a once-off isolated deliverable.

## Project Identity

MEIP is the **Massmart Executive Intelligence Platform**. Do not shorten the identity to only “Executive Intelligence Platform” when describing the current project.

The platform may later support external organisations, but the current project identity remains Massmart-specific unless and until a formally approved product identity changes that scope.

## Intended Platform Scope

MEIP is intended to support the following Massmart banners, functions, review cadences, and future audiences:

- Makro
- Game
- Builders
- Omni and Ecommerce
- Operations
- Commercial
- Finance
- Customer
- Human Resources
- Regional Reviews
- Training and Development
- Future Massmart business units
- Potential external organisations in future

This scope describes intended product direction. A capability must not be removed from the intended MEIP vision merely because that capability is not yet implemented in the repository.

## Authority and Conflict Rule

The repository is authoritative for claims about what is currently implemented. The approved MEIP master context is authoritative for intended product direction. Differences between intended architecture and current implementation must be explicitly recorded and must not be silently resolved.

This means:

- current-state documentation must accurately describe the code, schemas, templates, examples, and checks that exist now;
- intended-state documentation may define future platform capabilities, operating principles, and governance requirements;
- any gap between current implementation and intended architecture must be labelled as a gap, roadmap item, unresolved issue, or exclusion;
- no report, blueprint, or presentation may imply that an intended capability already exists unless the repository implementation supports that claim.

## Product Principle

MEIP must convert messy operational, commercial, financial, customer, human resources, and training source material into trusted executive decision support.

The platform must preserve these product principles:

1. **Evidence before presentation** — no visual or narrative claim may outrun the evidence.
2. **Intelligence before decoration** — page design follows executive questions, findings, decisions, and actions.
3. **Traceability before confidence** — every verified metric and material claim must trace to approved evidence.
4. **Explicit uncertainty** — missing, partial, conflicting, or not-applicable evidence must be labelled rather than hidden.
5. **Reusable platform learning** — each report should improve future MEIP rules, templates, validation gates, or intelligence patterns.

## Blueprint Validation Gate

No report page, section, or visual may progress to rendering until its blueprint has been validated against approved evidence.

Every blueprint page or section must include:

- purpose;
- executive question answered;
- headline;
- verified metrics;
- evidence references;
- intended visual;
- key insight;
- decision or action;
- validation status;
- unresolved issues or exclusions.

Blueprint validation must happen before rendering, image generation, design handoff, or executive distribution. If a blueprint is incomplete, unsupported, internally inconsistent, or based on unresolved evidence, it must be held back until the issue is corrected or explicitly excluded.

## Required Treatment of Gaps

When intended MEIP architecture differs from current implementation, documentation and review packs must identify the difference using one of these labels:

- **Current implementation** — implemented and available in the repository now.
- **Approved intended direction** — approved as part of MEIP direction but not necessarily implemented yet.
- **Gap** — intended direction is not yet implemented or only partially implemented.
- **Exclusion** — intentionally out of scope for the current report, release, or review cycle.
- **Unresolved issue** — cannot be validated from the available evidence or current repository state.

Gaps must not be silently resolved by weakening the intended MEIP vision. They must also not be represented as implemented functionality until the repository supports that claim.
