#!/usr/bin/env python3
"""Release readiness scanner.

Generates:
- Machine-readable scan output (JSON)
- Markdown readiness report with gate outcomes
- Markdown draft release notes grouped by change type
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

CONVENTIONAL_RE = re.compile(r"^(?P<type>[a-z]+)(\([^)]+\))?(?P<breaking>!)?:\s*(?P<desc>.+)$", re.IGNORECASE)

TEST_PATH_RE = re.compile(
    r"(^|/)(tests?/|__tests__/|cypress/)"
    r"|\.test\.(js|ts|py)$"
    r"|\.spec\.(js|ts|py)$"
    r"|(^|/)test_.*\.py$"
    r"|(^|/).*_test\.py$"
)


@dataclass
class Gate:
    name: str
    required: bool
    status: str
    evidence: str
    action: str


def run_git(args: List[str], check: bool = True) -> str:
    process = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if check and process.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {process.stderr.strip()}")
    return process.stdout.strip()


def ref_exists(ref: str) -> bool:
    process = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return process.returncode == 0


def resolve_base_ref(requested: str) -> str:
    candidates = [requested, "origin/main", "main", "origin/master", "master"]
    for candidate in candidates:
        if candidate and ref_exists(candidate):
            return candidate
    raise RuntimeError("Could not resolve a valid base ref (tried main/master variants).")


def parse_semver(version: Optional[str]) -> Optional[Tuple[int, int, int, Optional[str]]]:
    if not version:
        return None
    match = SEMVER_RE.match(version)
    if not match:
        return None
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    prerelease = match.group(4)
    return major, minor, patch, prerelease


def compare_semver(current: str, nxt: str) -> Optional[int]:
    a = parse_semver(current)
    b = parse_semver(nxt)
    if not a or not b:
        return None

    if a[:3] < b[:3]:
        return 1
    if a[:3] > b[:3]:
        return -1

    # Same major.minor.patch. Stable release is greater than prerelease.
    a_pre = a[3]
    b_pre = b[3]
    if a_pre is None and b_pre is None:
        return 0
    if a_pre is None and b_pre is not None:
        return -1
    if a_pre is not None and b_pre is None:
        return 1

    if a_pre < b_pre:
        return 1
    if a_pre > b_pre:
        return -1
    return 0


def detect_current_version() -> Optional[str]:
    package_json_path = "package.json"
    if not os.path.exists(package_json_path):
        return None
    try:
        with open(package_json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        version = payload.get("version")
        return version if isinstance(version, str) else None
    except Exception:
        return None


def get_tags_for_version(next_version: Optional[str]) -> List[str]:
    if not next_version:
        return []
    candidates = [next_version, f"v{next_version}"]
    existing: List[str] = []
    for tag in candidates:
        if ref_exists(f"refs/tags/{tag}"):
            existing.append(tag)
    return existing


def parse_commits(commit_range: str) -> List[Dict[str, str]]:
    raw = run_git(
        [
            "log",
            "--date=short",
            "--pretty=format:%H%x1f%ad%x1f%an%x1f%s%x1f%b%x1e",
            commit_range,
        ]
    )
    commits: List[Dict[str, str]] = []
    if not raw:
        return commits

    for block in raw.split("\x1e"):
        block = block.strip()
        if not block:
            continue
        parts = block.split("\x1f")
        if len(parts) < 5:
            continue
        commits.append(
            {
                "sha": parts[0],
                "date": parts[1],
                "author": parts[2],
                "subject": parts[3].strip(),
                "body": parts[4].strip(),
            }
        )
    return commits


def classify_commit(subject: str, body: str) -> Tuple[str, bool]:
    body_upper = body.upper()
    breaking = "BREAKING CHANGE" in body_upper

    match = CONVENTIONAL_RE.match(subject)
    if not match:
        return "other", breaking

    commit_type = (match.group("type") or "").lower()
    breaking = breaking or bool(match.group("breaking"))

    mapping = {
        "feat": "features",
        "fix": "fixes",
        "perf": "performance",
        "refactor": "maintenance",
        "docs": "documentation",
        "test": "tests",
        "ci": "maintenance",
        "build": "maintenance",
        "chore": "maintenance",
        "style": "maintenance",
        "revert": "maintenance",
    }
    return mapping.get(commit_type, "other"), breaking


def gather_changed_files(base_sha: str, target_ref: str) -> List[str]:
    raw = run_git(["diff", "--name-only", f"{base_sha}..{target_ref}"])
    if not raw:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def has_test_files_in_repo() -> bool:
    raw = run_git(["ls-files"], check=False)
    for line in raw.splitlines():
        if TEST_PATH_RE.search(line):
            return True
    return False


def build_release_notes(
    next_version: Optional[str],
    base_ref: str,
    target_ref: str,
    merge_base: str,
    grouped: Dict[str, List[Dict[str, str]]],
    breaking_items: List[Dict[str, str]],
) -> str:
    version_label = next_version or "[TODO-version]"
    lines: List[str] = []
    lines.append(f"# Release Notes Draft - {version_label}")
    lines.append("")
    lines.append("## Release Metadata")
    lines.append("")
    lines.append(f"- Base ref: {base_ref}")
    lines.append(f"- Target ref: {target_ref}")
    lines.append(f"- Comparison range: {merge_base}..{target_ref}")
    lines.append("")

    def add_section(title: str, key: str) -> None:
        entries = grouped.get(key, [])
        lines.append(f"## {title}")
        lines.append("")
        if not entries:
            lines.append("- None")
            lines.append("")
            return
        for entry in entries:
            lines.append(f"- {entry['subject']} ({entry['sha'][:7]})")
        lines.append("")

    lines.append("## Breaking Changes")
    lines.append("")
    if breaking_items:
        for entry in breaking_items:
            lines.append(f"- {entry['subject']} ({entry['sha'][:7]})")
    else:
        lines.append("- None")
    lines.append("")

    add_section("Features", "features")
    add_section("Fixes", "fixes")
    add_section("Maintenance and Infrastructure", "maintenance")
    add_section("Test and Quality", "tests")

    lines.append("## Known Issues")
    lines.append("")
    lines.append("- [TODO]")
    lines.append("")
    lines.append("## Upgrade and Rollback Notes")
    lines.append("")
    lines.append("- [TODO]")
    lines.append("")
    return "\n".join(lines)


def build_readiness_markdown(
    base_ref: str,
    target_ref: str,
    merge_base: str,
    current_version: Optional[str],
    next_version: Optional[str],
    latest_tag_base: Optional[str],
    tag_collisions: List[str],
    commit_count: int,
    gates: List[Gate],
    blockers: List[str],
    risks: List[str],
    decision: str,
) -> str:
    lines: List[str] = []
    lines.append("# Release Readiness Report")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(f"- Base ref: {base_ref}")
    lines.append(f"- Target ref: {target_ref}")
    lines.append(f"- Merge base: {merge_base}")
    lines.append(f"- Commit count: {commit_count}")
    lines.append(f"- Generated at: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## Version and Tag Validation")
    lines.append("")
    lines.append(f"- Current version: {current_version or '[TODO]'}")
    lines.append(f"- Next version: {next_version or '[TODO]'}")
    lines.append(f"- Existing tag collision: {', '.join(tag_collisions) if tag_collisions else 'None'}")
    lines.append(f"- Previous release tag: {latest_tag_base or '[TODO]'}")
    lines.append("")

    lines.append("## Gate Matrix")
    lines.append("")
    lines.append("| Gate | Status | Evidence | Action |")
    lines.append("|---|---|---|---|")
    for gate in gates:
        lines.append(f"| {gate.name} | {gate.status} | {gate.evidence} | {gate.action} |")
    lines.append("")

    lines.append("## Top Risks")
    lines.append("")
    if risks:
        for item in risks:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Blockers")
    lines.append("")
    if blockers:
        for item in blockers:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Final Decision")
    lines.append("")
    lines.append(f"- Recommendation: {decision}")
    lines.append("- Decision rationale: Derived from required gate outcomes.")
    lines.append("")
    return "\n".join(lines)


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate release readiness report and release notes draft")
    parser.add_argument("--base-ref", default="origin/main", help="Base ref for comparison")
    parser.add_argument("--target-ref", default="HEAD", help="Target ref for release candidate")
    parser.add_argument("--current-version", default=None, help="Current released version")
    parser.add_argument("--next-version", default=None, help="Planned next release version")
    parser.add_argument("--output-json", default="docs/releases/.release-scan.json")
    parser.add_argument("--output-readiness-md", default="docs/releases/RELEASE_READINESS.md")
    parser.add_argument("--output-notes-md", default="docs/releases/RELEASE_NOTES_DRAFT.md")

    args = parser.parse_args()

    try:
        base_ref = resolve_base_ref(args.base_ref)
        if not ref_exists(args.target_ref):
            raise RuntimeError(f"Target ref does not exist: {args.target_ref}")

        merge_base = run_git(["merge-base", base_ref, args.target_ref])
        commit_range = f"{merge_base}..{args.target_ref}"

        current_version = args.current_version or detect_current_version()
        next_version = args.next_version

        current_semver_ok = parse_semver(current_version) is not None if current_version else False
        next_semver_ok = parse_semver(next_version) is not None if next_version else False
        bump_cmp = compare_semver(current_version, next_version) if current_version and next_version else None

        commits = parse_commits(commit_range)
        changed_files = gather_changed_files(merge_base, args.target_ref)

        grouped: Dict[str, List[Dict[str, str]]] = {
            "features": [],
            "fixes": [],
            "performance": [],
            "maintenance": [],
            "documentation": [],
            "tests": [],
            "other": [],
        }
        breaking_items: List[Dict[str, str]] = []

        for commit in commits:
            category, is_breaking = classify_commit(commit["subject"], commit["body"])
            grouped.setdefault(category, []).append(commit)
            if is_breaking:
                breaking_items.append(commit)

        changelog_changed = any(path.lower().endswith("changelog.md") for path in changed_files)
        docs_changed = any(path.startswith("docs/") or path.endswith("README.md") for path in changed_files)
        tests_changed = any(TEST_PATH_RE.search(path) for path in changed_files)
        ci_changed = any(
            path.startswith(".github/workflows/")
            or path in {"amplify.yml", ".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile"}
            for path in changed_files
        )
        version_files_changed = any(
            path in {"package.json", "pyproject.toml", "setup.py", "VERSION", "pom.xml", "build.gradle"}
            or path.endswith("/package.json")
            or path.endswith("/pyproject.toml")
            for path in changed_files
        )
        dependency_files_changed = any(
            path in {"package-lock.json", "yarn.lock", "Pipfile.lock", "poetry.lock", "requirements.txt"}
            or path.endswith("/package-lock.json")
            or path.endswith("/yarn.lock")
            or path.endswith("/Pipfile.lock")
            for path in changed_files
        )
        infra_changed = any(
            path.startswith("amplify/")
            or path.endswith("template.yaml")
            or path.endswith("template.yml")
            or path.endswith("cloudformation.yml")
            or path.endswith("cloudformation.yaml")
            or path.endswith("docker-compose.yaml")
            for path in changed_files
        )
        code_changed = any(
            path.startswith("src/")
            or path.endswith(".py")
            or path.endswith(".ts")
            or path.endswith(".js")
            or path.endswith(".vue")
            for path in changed_files
        )
        has_repo_tests = has_test_files_in_repo()

        tag_collisions = get_tags_for_version(next_version)
        latest_tag_base = run_git(["describe", "--tags", "--abbrev=0", base_ref], check=False) or None

        gates: List[Gate] = []

        if current_version and next_version:
            if current_semver_ok and next_semver_ok and bump_cmp == 1:
                gates.append(Gate("Version validity", True, "PASS", "SemVer valid and bump is increasing", "None"))
            elif not (current_semver_ok and next_semver_ok):
                gates.append(
                    Gate("Version validity", True, "FAIL", "Current and/or next version is not SemVer", "Use SemVer values")
                )
            else:
                gates.append(
                    Gate(
                        "Version validity",
                        True,
                        "FAIL",
                        "Next version is not greater than current",
                        "Choose a higher next version",
                    )
                )
        else:
            gates.append(
                Gate(
                    "Version validity",
                    True,
                    "WARN",
                    "Current and/or next version not provided",
                    "Provide --current-version and --next-version",
                )
            )

        if tag_collisions:
            gates.append(
                Gate(
                    "Tag safety",
                    True,
                    "FAIL",
                    f"Tag already exists: {', '.join(tag_collisions)}",
                    "Choose a new version/tag",
                )
            )
        else:
            gates.append(Gate("Tag safety", True, "PASS", "No tag collision detected", "None"))

        if breaking_items:
            gates.append(
                Gate(
                    "Breaking change visibility",
                    True,
                    "WARN",
                    f"Breaking changes detected: {len(breaking_items)}",
                    "Document migration and rollback steps",
                )
            )
        else:
            gates.append(Gate("Breaking change visibility", True, "PASS", "No breaking changes detected", "None"))

        if code_changed and not tests_changed and not has_repo_tests:
            gates.append(
                Gate(
                    "Test signal",
                    True,
                    "FAIL",
                    "Code changed but repository has no test assets",
                    "Add or reference test evidence before release",
                )
            )
        elif code_changed and not tests_changed:
            gates.append(
                Gate(
                    "Test signal",
                    True,
                    "WARN",
                    "Code changed but no test files changed",
                    "Confirm existing suite coverage or add tests",
                )
            )
        else:
            gates.append(Gate("Test signal", True, "PASS", "Test files changed or no code changes", "None"))

        if ci_changed or os.path.exists("amplify.yml") or os.path.exists(".github/workflows"):
            gates.append(Gate("CI/build readiness", True, "PASS", "CI/build config detected", "None"))
        else:
            gates.append(
                Gate(
                    "CI/build readiness",
                    True,
                    "WARN",
                    "No CI config observed in repository root",
                    "Confirm CI status externally",
                )
            )

        user_visible_changes = bool(grouped["features"] or grouped["fixes"] or breaking_items)
        if user_visible_changes and not (docs_changed or changelog_changed):
            gates.append(
                Gate(
                    "Documentation readiness",
                    True,
                    "WARN",
                    "User-visible changes without docs/changelog updates",
                    "Update release docs/changelog",
                )
            )
        else:
            gates.append(Gate("Documentation readiness", True, "PASS", "Documentation signal present", "None"))

        gates.append(
            Gate(
                "Dependency risk",
                False,
                "WARN" if dependency_files_changed else "PASS",
                "Dependency files changed" if dependency_files_changed else "No dependency file changes",
                "Review dependency impact" if dependency_files_changed else "None",
            )
        )

        gates.append(
            Gate(
                "Operational risk",
                False,
                "WARN" if infra_changed else "PASS",
                "Infrastructure/config files changed" if infra_changed else "No major infra file changes",
                "Confirm rollback and migration notes" if infra_changed else "None",
            )
        )

        if len(commits) > 80 or len(changed_files) > 200:
            scope_status = "WARN"
            scope_evidence = f"Large scope: commits={len(commits)}, files={len(changed_files)}"
            scope_action = "Consider phased rollout"
        else:
            scope_status = "PASS"
            scope_evidence = f"Scope: commits={len(commits)}, files={len(changed_files)}"
            scope_action = "None"
        gates.append(Gate("Scope risk", False, scope_status, scope_evidence, scope_action))

        blockers = [f"{g.name}: {g.evidence}" for g in gates if g.required and g.status == "FAIL"]
        risks = [f"{g.name}: {g.evidence}" for g in gates if g.status == "WARN"]

        required_warn = any(g.required and g.status == "WARN" for g in gates)
        required_fail = any(g.required and g.status == "FAIL" for g in gates)
        if required_fail:
            decision = "NO-GO"
        elif required_warn:
            decision = "GO with Risks"
        else:
            decision = "GO"

        report = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "base_ref": base_ref,
            "target_ref": args.target_ref,
            "merge_base": merge_base,
            "commit_range": commit_range,
            "versions": {
                "current": current_version,
                "next": next_version,
                "current_semver_valid": current_semver_ok,
                "next_semver_valid": next_semver_ok,
                "next_gt_current": bump_cmp == 1 if bump_cmp is not None else None,
            },
            "tags": {
                "latest_tag_on_base": latest_tag_base,
                "existing_next_version_tags": tag_collisions,
            },
            "summary": {
                "commit_count": len(commits),
                "changed_files_count": len(changed_files),
                "breaking_changes_count": len(breaking_items),
                "tests_changed": tests_changed,
                "docs_changed": docs_changed,
                "changelog_changed": changelog_changed,
                "ci_changed": ci_changed,
                "version_files_changed": version_files_changed,
                "dependency_files_changed": dependency_files_changed,
                "infra_changed": infra_changed,
            },
            "gates": [
                {
                    "name": gate.name,
                    "required": gate.required,
                    "status": gate.status,
                    "evidence": gate.evidence,
                    "action": gate.action,
                }
                for gate in gates
            ],
            "decision": decision,
            "blockers": blockers,
            "risks": risks,
            "changed_files": changed_files,
            "commits": commits,
            "release_notes_groups": {
                key: [{"sha": c["sha"], "subject": c["subject"]} for c in value] for key, value in grouped.items()
            },
            "breaking_changes": [{"sha": c["sha"], "subject": c["subject"]} for c in breaking_items],
        }

        readiness_md = build_readiness_markdown(
            base_ref=base_ref,
            target_ref=args.target_ref,
            merge_base=merge_base,
            current_version=current_version,
            next_version=next_version,
            latest_tag_base=latest_tag_base,
            tag_collisions=tag_collisions,
            commit_count=len(commits),
            gates=gates,
            blockers=blockers,
            risks=risks,
            decision=decision,
        )
        notes_md = build_release_notes(
            next_version=next_version,
            base_ref=base_ref,
            target_ref=args.target_ref,
            merge_base=merge_base,
            grouped=grouped,
            breaking_items=breaking_items,
        )

        ensure_parent_dir(args.output_json)
        ensure_parent_dir(args.output_readiness_md)
        ensure_parent_dir(args.output_notes_md)

        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
            f.write("\n")

        with open(args.output_readiness_md, "w", encoding="utf-8") as f:
            f.write(readiness_md)
            f.write("\n")

        with open(args.output_notes_md, "w", encoding="utf-8") as f:
            f.write(notes_md)
            f.write("\n")

        print(f"Wrote {args.output_json}")
        print(f"Wrote {args.output_readiness_md}")
        print(f"Wrote {args.output_notes_md}")
        print(f"Decision: {decision}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
