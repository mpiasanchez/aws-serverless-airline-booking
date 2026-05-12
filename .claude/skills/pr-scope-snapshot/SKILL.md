---
name: pr-scope-snapshot
description: 'Use this skill when the user asks for a concise PR summary from branch differences, including what changed, risk hotspots, and review notes.'
license: MIT
compatibility: 'Cross-platform. No scripts required. Uses git branch comparison and file-level analysis.'
metadata:
  version: "1.0"
argument-hint: 'Required for best results: base and target refs (for example base=master target=HEAD).'
---

# PR Scope Snapshot

Creates a short, clear PR-ready summary from branch comparison.

## When To Use

Use this skill for prompts like:

- "Summarize this PR"
- "Generate PR description from my branch"
- "What changed between master and my branch"

Do not use this skill for release go or no-go decisions.

## Input

Use explicit refs whenever possible:

- base: comparison branch (for example master)
- target: current work branch (for example HEAD)

## Output Contract (Required)

Return these sections in order:

1. Scope and refs
2. Problem solved (1 to 3 bullets)
3. Key changes by area
4. Risks and reviewer focus points
5. Test and documentation evidence
6. PR description draft (paste-ready)

## Workflow

1. Compare base and target refs.
2. Group changed files by feature area.
3. Identify risk hotspots (schema, auth, infra, payment, core flows).
4. Pull test and docs signals from changed files.
5. Produce a concise PR draft with reviewer guidance.

## Rules

- Keep summary short and reviewer-friendly.
- Avoid listing every file when grouping is clearer.
- If branch histories are unrelated, state that clearly and use direct tip-to-tip diff.
- Include unresolved risks as explicit follow-up items.

## Suggested Activation Prompts

- "Run PR scope snapshot from master to this branch"
- "Create a PR draft summary for base=master target=HEAD"
- "Summarize branch differences for reviewers"
