---
name: test-gap-radar
description: 'Use this skill when the user asks to find missing tests for implemented code, check test gaps, or prepare test updates before opening a PR.'
license: MIT
compatibility: 'Cross-platform. No scripts required. Uses git diff and repository file inspection.'
metadata:
  version: "1.0"
argument-hint: 'Optional: scope path (for example src/backend/booking), or base and target refs for PR mode.'
---

# Test Gap Radar

Finds code changes that do not have matching test updates.

## When To Use

Use this skill for prompts like:

- "Check what code has no tests yet"
- "Find test gaps in my branch"
- "What tests should I add before PR"

Do not use this skill to run a full release validation or write release notes.

## Modes

1. Branch mode (default): analyze current branch changes and existing test footprint.
2. PR mode (optional): compare `base...target` and report test gaps for that diff.

## Output Contract (Required)

Return these sections in order:

1. Scope analyzed
2. Changed code areas
3. Existing tests found
4. Test gaps (high, medium, low)
5. Suggested tests to add
6. Quick next actions

## Workflow

1. Determine mode and scope.
2. List changed production files in scope.
3. Locate matching test files by folder and naming patterns.
4. Flag gaps where behavior changed but no tests were added or updated.
5. Propose minimal tests needed (unit, integration, acceptance when applicable).

## Rules

- Prefer concise and actionable findings.
- Cite concrete file paths for each finding.
- If no gaps are found, explicitly say "No significant test gaps found".
- Do not invent tests that require unavailable infrastructure.
- Keep recommendations focused on the changed behavior.

## Suggested Activation Prompts

- "Run test gap radar for this branch"
- "Check test gaps under src/backend/booking"
- "Compare test gaps between master and this branch"
