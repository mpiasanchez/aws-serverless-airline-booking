---
name: pr-scope-snapshot
description: 'Use this skill when the user asks for a concise, paste-ready PR summary from branch differences, with optional review notes only when needed.'
license: MIT
compatibility: 'Cross-platform. No scripts required. Uses git branch comparison and file-level analysis.'
metadata:
  version: "1.0"
argument-hint: 'Required for best results: base and target refs (for example base=master target=HEAD).'
---

# PR Scope Snapshot

Creates a short, clear, paste-ready PR description from branch comparison. Include extra reviewer notes only when they add value.

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
4. PR description draft (paste-ready, short, clear, and concise)

Optional sections (include only when applicable):

- Risks and reviewer focus points
- Follow-up questions and open assumptions
- Test evidence
- Documentation impact
- Additional review notes (blockers, unknowns, recommended reviewer checks)

## Workflow

1. Compare base and target refs.
2. Group changed files by feature area.
3. Build the core PR summary first (problem solved, key changes, paste-ready draft).
4. Identify risk hotspots (schema, auth, infra, payment, core flows).
5. Add optional notes only when evidence exists in the diff.

## Rules

- Keep summary short, clear, and reviewer-friendly.
- Keep the PR description draft explicitly copy/paste ready for GitHub (or equivalent tools).
- Keep the PR description separate from review notes so users can paste the PR text without cleanup.
- Default to a simple, classic PR description when no meaningful risks/tests/docs notes are found.
- Do not force optional sections; omit them when not applicable.
- Avoid listing every file when grouping is clearer.
- If branch histories are unrelated, state that clearly and use direct tip-to-tip diff.
- Include unresolved risks as explicit follow-up items when they exist.

## Suggested Activation Prompts

- "Run PR scope snapshot from master to this branch"
- "Create a PR draft summary for base=master target=HEAD"
- "Summarize branch differences for reviewers"
- "Generate a simple, paste-ready PR description"
- "Generate a paste-ready PR description and add risks or follow-up questions only if applicable"
