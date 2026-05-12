---
name: release-readiness
description: 'Use this skill when the user asks for release readiness checks, go/no-go validation, version validation, release notes generation, or branch-to-branch release risk analysis. Trigger for prompts like "prepare release", "validate release", "generate release notes", "is this branch ready to ship".'
license: MIT
compatibility: 'Cross-platform. Requires Python 3.8+ and git. Run scripts/release_scan.py from the target repository root.'
metadata:
   version: "1.1"
argument-hint: 'Optional: base branch, target ref, current version, next version (e.g. "base=origin/main next=1.4.0")'
---

# Release Readiness

Performs a structured release audit and generates a release notes draft from verifiable git history and repository signals.

## Source of Truth

- `scripts/release_scan.py` is the canonical producer for release outputs.
- `assets/templates/*` are fallback scaffolds only when scanner output is missing or incomplete.
- Prefer rerunning the scanner over manually reshaping generated sections.

## Output Contract (Required)

Before finishing, all of the following must be true:

1. `docs/releases/RELEASE_READINESS.md` exists and includes an explicit recommendation: `GO`, `GO with Risks`, or `NO-GO`.
2. `docs/releases/RELEASE_NOTES_DRAFT.md` exists and includes categorized change highlights.
3. `docs/releases/.release-scan.json` exists as machine-readable audit output.
4. Every blocker/risk item has evidence references (file paths, command output, or commit IDs).
5. Unknowns are marked `[TODO]` and intent-dependent choices are marked `[ASK USER]`.
6. Generated outputs come from scanner execution unless a documented fallback is required.

## Workflow

Track this checklist:

```
- [ ] Phase 1: Collect release context and run automated scan
- [ ] Phase 2: Evaluate release gates and identify risks
- [ ] Phase 3: Produce readiness report and notes draft
- [ ] Phase 4: Validate outputs and finalize recommendations
```

### Phase 1: Collect Context and Run Scan

1. Gather intended release inputs from the user if available:
   - Base ref (default: `origin/main`)
   - Target ref (default: `HEAD`)
   - Current version (optional)
   - Next version (optional)

2. Run the scanner from repository root:

```bash
python3 "$SKILL_ROOT/scripts/release_scan.py" \
  --base-ref origin/main \
  --target-ref HEAD \
  --current-version 1.2.3 \
  --next-version 1.3.0 \
  --output-json docs/releases/.release-scan.json \
  --output-readiness-md docs/releases/RELEASE_READINESS.md \
  --output-notes-md docs/releases/RELEASE_NOTES_DRAFT.md
```

If versions are unknown, omit those flags and mark missing validation as `[TODO]`.

### Phase 2: Evaluate Release Gates

Use `references/release-gates.md` to evaluate:

1. Versioning and tag safety.
2. Change scope and breaking changes.
3. Test and CI readiness.
4. Documentation and changelog readiness.
5. Dependency and operational risk indicators.

Anything failing a `Required` gate should appear as a blocker in the report.

### Phase 3: Produce Outputs

1. Confirm scanner wrote all 3 outputs successfully.
2. Review generated sections for clarity, evidence quality, and missing rollout/rollback notes.
3. If scanner output is missing or malformed, repair using templates and keep unresolved items as `[TODO]` or `[ASK USER]`.
4. If repo conventions require a changelog update, map the notes draft into `CHANGELOG.md` format and mark unresolved items as `[ASK USER]`.

### Phase 4: Validate and Finalize

1. Verify all three output files exist and are non-empty.
2. Re-check every `FAIL` gate has explicit evidence and action.
3. Re-check every recommendation is tied to observed data.
4. Return a concise decision summary with:
   - `GO`/`GO with Risks`/`NO-GO`
   - Blockers (if any)
   - Residual risk notes
   - Numbered `[ASK USER]` items

## Gotchas

- Release notes can be misleading if merge strategy squashes commit context. If commit detail is low quality, mark `[ASK USER]` for manual curation.
- SemVer checks require both current and next versions. If either is missing, do not guess.
- A branch can have passing tests but still fail readiness due to missing docs, migration steps, or untracked breaking changes.
- Tag collisions (`v1.2.3` already exists) should always be treated as a hard blocker.
- The scanner is currently the format authority. Avoid parallel manual formatting standards that drift from script output.

## Anti-Patterns

| Do Not | Do Instead |
|---|---|
| Assume readiness because CI exists | Validate gates with evidence from actual repo state |
| Publish notes directly from raw commit subjects | Group, normalize, and flag unclear entries for manual review |
| Infer semantic version intent from branch name | Validate explicit version inputs and tag state |
| Ignore missing rollback notes for risky changes | Add rollback/migration `[TODO]` or `[ASK USER]` items |

## Bundled Assets

| Asset | When to load |
|---|---|
| `scripts/release_scan.py` | Phase 1 automation pass |
| `references/release-gates.md` | Phase 2 gate checks |
| `assets/templates/RELEASE_READINESS.md` | If report needs manual completion/repair |
| `assets/templates/RELEASE_NOTES_DRAFT.md` | If notes need manual curation |
