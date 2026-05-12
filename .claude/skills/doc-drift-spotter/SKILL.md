---
name: doc-drift-spotter
description: 'Use this skill when the user asks to find documentation that no longer matches the source code, routes, commands, or file structure.'
license: MIT
compatibility: 'Cross-platform. No scripts required. Uses repository documentation and source inspection.'
metadata:
  version: "1.1"
argument-hint: 'Optional: docs area (for example README only, or src/frontend docs). If omitted, default to full-repository drift review.' 
---

# Doc Drift Spotter

Finds mismatches between documentation and current code.

## When To Use

Use this skill for prompts like:

- "Find docs that are out of date"
- "Check README against current source"
- "Spot documentation drift before PR"
- "Is there any documentation update needed in this branch?"

Do not use this skill for full repository onboarding documentation generation.

## Scope Policy (Required)

- If the user provides an explicit scope (for example, only root README, only frontend docs, or only one service), limit analysis to that scope.
- If the user asks a generic or branch-wide question without scope constraints (for example, "Is there any documentation update needed in this branch?"), perform full-repository coverage.
- Full-repository coverage means reviewing both:
  - Source and configuration across all relevant modules/services in the branch.
  - Existing documentation surfaces (root docs, `docs/`, service READMEs, frontend docs, runbooks, and command references).

## Output Contract (Required)

Return these sections in order:

1. Scope analyzed
2. Confirmed aligned docs
3. Drift findings (critical, normal, minor)
4. Suggested documentation updates
5. Quick next actions

## Workflow

1. Determine scope from user prompt.
2. If scope is generic/branch-wide, perform a source inventory first (services, routes, commands, file structure, config entrypoints) across the repository.
3. Extract concrete claims from docs in scope (paths, commands, modules, workflows).
4. Verify claims against current files and configuration.
5. Mark each claim as aligned, partial, or drifted.
6. Propose minimal edits to remove drift.

## Rules

- Every drift finding must include evidence paths.
- Prefer high-signal issues first (broken paths, wrong commands, missing modules).
- If docs are aligned, explicitly say "No high-impact drift found".
- Do not rewrite whole docs when small targeted updates are enough.
- For generic branch-wide prompts, do not stop after checking one document; ensure repository-wide source and documentation coverage.

## Suggested Activation Prompts

- "Run doc drift spotter for the root README"
- "Check frontend docs for drift"
- "Find documentation mismatches in this branch"
- "Is there any documentation update needed in this branch?"
