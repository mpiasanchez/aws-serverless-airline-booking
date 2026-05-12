# Release Gates

Use this matrix for final go/no-go evaluation.

## Required Gates

1. Version Validity
- Current and next versions are valid SemVer or explicitly marked `[TODO]`.
- If both versions are provided, next version is greater than current.

2. Tag Safety
- Intended release tag does not already exist.
- Previous release tag used for comparison is identified.

3. Breaking Change Visibility
- Breaking changes are explicitly listed.
- Any migration/rollback implications are documented.

4. Test Signal
- Test strategy is present in repo or changes are low-risk and justified.
- If test files are absent for high-risk changes, mark `FAIL`.

5. CI/Build Readiness
- CI pipeline config exists and no known red flags are reported.

6. Documentation Readiness
- Changelog and/or release notes are prepared.
- User-visible changes are described.

## Advisory Gates

1. Dependency Risk
- Notable dependency changes are highlighted.

2. Operational Risk
- Infra/config changes are highlighted.
- Rollback steps are present or marked `[TODO]`.

3. Scope Risk
- Large change sets include staged rollout guidance.

## Decision Policy

- `GO`: No `FAIL` in Required gates.
- `NO-GO`: One or more `FAIL` in Required gates.
- `GO with Risks`: No Required `FAIL`, but Advisory gates include medium/high concerns.
