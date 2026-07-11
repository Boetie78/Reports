# Claude and Codex Working Protocol

This protocol defines how Claude and Codex collaborate on the Massmart Executive Intelligence Platform without overwriting each other or duplicating work.

## Branch Separation

- The default shared integration branch for the current MEIP programme is `meip/executive-intelligence-engine` unless a human explicitly selects another target.
- Claude and Codex should work on separate branches unless a human explicitly approves a shared branch.
- Branch names should identify the agent and task area, for example `claude/<task>` or `codex/<task>`.
- Pull requests from Claude and Codex must target the approved shared integration branch, not `main`, unless explicitly approved.
- Do not start implementation until the current branch, status, and relevant files have been inspected.

## No Simultaneous Edits to the Same Area

- Claude and Codex must not edit the same task area at the same time without an explicit handoff.
- A task area may be a file, schema, pipeline stage, template group, prompt, documentation set, or example data set.
- If overlap is discovered, stop and agree which agent owns the area before continuing.

## Inspect and Reuse First

Before implementation, each agent must:

1. inspect the repository structure and relevant files;
2. identify existing schemas, modules, templates, prompts, examples, and docs that already solve part of the task;
3. reuse or extend existing components before creating duplicates;
4. record any current implementation versus intended architecture gaps.

## Pull-Request Review Before Merge

- Every branch should be reviewed through a pull request before merge.
- The PR must explain scope, files changed, evidence basis, tests run, risks, and unresolved issues.
- Planned capability must be labelled as planned unless implemented and tested in the repository.

## Updating After Another Agent Merges

After another agent's PR merges, the next agent must:

1. update from the target branch;
2. inspect the changed files relevant to their task;
3. re-run affected checks;
4. adjust their branch to reuse merged work instead of recreating it;
5. record any conflicts, changed assumptions, or follow-up gaps.

If one agent's pull request changes shared schemas, contracts, architecture, or pipeline interfaces, the other agent must update from the merged target before continuing.

## Conflict Resolution

When conflicts occur:

- preserve validated evidence, source lineage, and zero-fabrication rules;
- prefer the implementation that matches current repository contracts unless an approved architecture change requires a new contract;
- do not silently delete another agent's valid work;
- document why each conflict was resolved the chosen way;
- re-run validation and tests after resolution.

## Handoff Requirements

Every handoff between Claude, Codex, or a human reviewer must include:

- files changed;
- commands run;
- tests run and results;
- evidence sources used;
- risks;
- unresolved issues;
- current branch and commit;
- whether any files remain uncommitted;
- any areas the next agent must avoid or inspect first.

## Merge and Continuation Rule

No agent should continue from stale assumptions after another branch merges. Update, inspect, validate, and then proceed.
