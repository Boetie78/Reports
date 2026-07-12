# MEIP Executive Intelligence Model

This document defines the executive intelligence chain for the Massmart Executive Intelligence Platform.

MEIP must separate facts, calculations, findings, interpretations, business impacts, decisions, and actions so that assumptions or recommendations are never represented as verified facts.

## Executive Intelligence Chain

```text
Fact
→ Variance
→ Finding
→ Interpretation
→ Business Impact
→ Decision
→ Action
```

Each stage has a different evidence burden and must be labelled accordingly.

## Stage Definitions

### 1. Fact

A fact is a source-backed statement about what is present in approved evidence.

Examples include a reported sales value, on-time delivery percentage, number of stores, date, region, banner, category, or source-stated event.

Rules:

- Facts require VERIFIED evidence unless explicitly labelled with another evidence status.
- Facts must not include causal language unless the source itself proves causality and that proof is approved.
- Assumptions, interpretations, opinions, and recommendations must not be written as facts.

### 2. Variance

A variance describes the measured difference between a fact and a comparator.

Comparators may include target, prior period, forecast, budget, baseline, benchmark, commitment, or threshold.

Rules:

- Variances are usually DERIVED from verified inputs.
- The comparator must be named.
- The formula or comparison basis must be reproducible.
- A variance does not automatically explain why the movement happened.

### 3. Finding

A finding identifies what is materially notable in the facts and variances.

A finding answers: “What should an executive notice?”

Rules:

- Findings must be grounded in facts or derived variances.
- Findings may prioritise, group, or summarise evidence, but may not invent new evidence.
- Materiality criteria should be explicit where possible.

### 4. Interpretation

An interpretation explains what the finding may mean.

Interpretation may connect patterns, events, operational context, commercial context, customer context, financial context, human resources context, or training context.

Rules:

- Interpretations must be labelled as interpretations, not facts.
- Interpretations must identify the evidence they rely on.
- Interpretations must distinguish correlation from causation.
- Where evidence is incomplete, interpretations must carry PARTIALLY_VERIFIED, USER_CONFIRMED, CONFLICTING, or MISSING status as appropriate.

### 5. Business Impact

Business impact explains why the finding and interpretation matter to Massmart or the relevant audience.

Impact may relate to revenue, margin, cost, service, customer experience, stock, operations, compliance, people, capacity, reputation, risk, or executive focus.

Rules:

- Quantified impacts require VERIFIED or DERIVED evidence.
- Qualitative impacts require explicit support or user confirmation.
- Potential impacts must be labelled as potential, not actual.

### 6. Decision

A decision states what leadership needs to decide, approve, stop, start, change, escalate, fund, monitor, or accept.

Rules:

- Decisions must follow from the documented finding, interpretation, and business impact.
- Decisions must not be framed as already approved unless approval evidence exists.
- Decision options should identify trade-offs, owners, and timing where known.

### 7. Action

An action is the concrete next step assigned or recommended after a decision.

Rules:

- Actions should identify an owner or accountable function where possible.
- Actions should include timing or trigger conditions where possible.
- Actions must not imply that causality is proven unless the evidence supports it.
- Actions based on incomplete evidence must include the evidence limitation.

## Non-Negotiable Representation Rule

Interpretations, assumptions, recommendations, decisions, and actions must never be represented as VERIFIED facts.

MEIP may recommend action under uncertainty, but it must show the uncertainty. The correct response to incomplete evidence is not to remove the intended intelligence layer; it is to label the evidence status, record the unresolved issue, and prevent unsupported claims from appearing as verified truth.

## Blueprint and Rendering Implication

Every blueprint page or section must show how it moves through the executive intelligence chain:

- what fact or facts are being used;
- what variance or comparison matters;
- what finding is material;
- what interpretation is being offered;
- what business impact is at stake;
- what decision is required;
- what action follows.

If any link in the chain is missing, conflicting, or only partially verified, the blueprint must record that issue before rendering can proceed.
