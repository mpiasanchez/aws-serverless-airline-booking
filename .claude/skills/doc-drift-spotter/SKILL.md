---
name: doc-drift-spotter
description: 'Use this skill when the user asks to find documentation that no longer matches the source code, routes, commands, or file structure.'
license: MIT
compatibility: 'Cross-platform. No scripts required. Uses repository documentation and source inspection.'
metadata:
  version: "1.0"
argument-hint: 'Optional: docs area (for example README only, or src/frontend docs).' 
---

# Doc Drift Spotter

Finds mismatches between documentation and current code.

## When To Use

Use this skill for prompts like:

- "Find docs that are out of date"
- "Check README against current source"
- "Spot documentation drift before PR"

Do not use this skill for full repository onboarding documentation generation.

## Output Contract (Required)

Return these sections in order:

1. Scope analyzed
2. Confirmed aligned docs
3. Drift findings (critical, normal, minor)
4. Suggested documentation updates
5. Quick next actions

## Workflow

1. Select doc scope (top-level docs, service docs, frontend docs).
2. Extract concrete claims from docs (paths, commands, modules, workflows).
3. Verify claims against current files and configuration.
4. Mark each claim as aligned, partial, or drifted.
5. Propose minimal edits to remove drift.

## Rules

- Every drift finding must include evidence paths.
- Prefer high-signal issues first (broken paths, wrong commands, missing modules).
- If docs are aligned, explicitly say "No high-impact drift found".
- Do not rewrite whole docs when small targeted updates are enough.

## Suggested Activation Prompts

- "Run doc drift spotter for the root README"
- "Check frontend docs for drift"
- "Find documentation mismatches in this branch"
