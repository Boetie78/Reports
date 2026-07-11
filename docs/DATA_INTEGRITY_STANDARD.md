# MEIP Data Integrity Standard

This standard defines the evidence-status language used by the Massmart Executive Intelligence Platform.

The purpose is to prevent unsupported numbers, assumptions, interpretations, or recommendations from being presented as verified facts.

## Core Rule

Every metric, claim, finding, chart input, blueprint section, and executive recommendation must carry evidence that is appropriate to its status.

If evidence is missing, incomplete, contradictory, user-confirmed, derived, or not applicable, MEIP must say so explicitly.

## Evidence Statuses

### VERIFIED

**Meaning:** The value or claim is directly supported by approved source evidence and has passed the applicable repository validation checks.

**Allowed use:** Use for source-backed facts, source-backed metrics, reconciled totals, validated chart values, and narrative statements that exactly reflect approved evidence.

**Not allowed:** Do not use for assumptions, inferred causes, recommendations, unexplained movements, or values calculated outside an approved derivation rule.

### DERIVED

**Meaning:** The value was calculated from verified or approved source inputs using a documented formula, transformation, or rule.

**Allowed use:** Use for percentages, variances, rates, indexed values, contribution calculations, rankings, or aggregations that can be reproduced from cited inputs.

**Required evidence:** Cite the source inputs and document or reference the calculation method.

**Not allowed:** Do not use when the inputs are missing, contradictory, or not traceable.

### USER_CONFIRMED

**Meaning:** A business user or approved human reviewer has confirmed the value, context, interpretation, exception, or exclusion.

**Allowed use:** Use for business context that may not exist in machine-readable files, such as confirmed event timing, ownership, operational constraints, or known one-off exclusions.

**Required evidence:** Record who or what role confirmed it, when it was confirmed, and what exactly was confirmed.

**Not allowed:** Do not treat user confirmation as a substitute for source data when the claim is a numeric fact that should be present in an approved system extract.

### PARTIALLY_VERIFIED

**Meaning:** Some evidence supports the value or claim, but the evidence is incomplete, limited in scope, awaiting confirmation, or unable to validate the full statement.

**Allowed use:** Use when part of a metric is source-backed, only a subset of regions or banners is validated, an event is confirmed but its quantified impact is not, or a trend is visible but not fully reconciled.

**Required evidence:** State which part is verified, which part is not verified, and what evidence is still needed.

**Not allowed:** Do not present a partially verified item as a complete verified fact.

### CONFLICTING

**Meaning:** Two or more approved or candidate evidence sources disagree, or a value conflicts with another validated value, calculation, or narrative statement.

**Allowed use:** Use for mismatched totals, contradictory source extracts, inconsistent time periods, conflicting ownership, or narrative claims that disagree with validated data.

**Required action:** Stop the affected claim, visual, or blueprint section from rendering until the conflict is resolved, excluded, or explicitly approved with a documented caveat.

**Not allowed:** Do not average, overwrite, or silently choose one source unless an approved precedence rule exists.

### MISSING

**Meaning:** Required evidence is absent.

**Allowed use:** Use when a metric, source file, data reference, owner, time period, calculation input, or validation support is required but unavailable.

**Required action:** Block verified claims and rendering for affected content unless the missing item is explicitly excluded or the section is redesigned around available evidence.

**Not allowed:** Do not fill missing values with placeholders, guesses, example numbers, or visually convenient figures.

### NOT_APPLICABLE

**Meaning:** The evidence requirement does not apply to this specific item because the item is outside the scope of the report, section, metric, audience, or decision.

**Allowed use:** Use for intentionally omitted metrics, non-relevant business units, unavailable comparisons that are not required for the current decision, or governance checks that do not apply to a content type.

**Required evidence:** State why the item is not applicable.

**Not allowed:** Do not use NOT_APPLICABLE to hide missing evidence that is required for the report or decision.

## Rendering Rule

A page, section, visual, or headline may progress only when its evidence statuses are compatible with its purpose:

- VERIFIED and DERIVED items may support final numeric claims when references and calculations are documented.
- USER_CONFIRMED items may support context and approved business explanations when the confirmation is recorded.
- PARTIALLY_VERIFIED items require visible caveats or exclusion from final executive claims.
- CONFLICTING and MISSING items block affected claims or visuals until resolved or explicitly excluded.
- NOT_APPLICABLE items require a reason and must not be used to bypass required evidence.

## Status Integrity

Evidence status describes the level of support for a claim. It does not describe how important the claim is.

A high-impact claim with weak evidence remains weakly evidenced. MEIP must escalate that evidence weakness rather than upgrading the status to make the story cleaner.
