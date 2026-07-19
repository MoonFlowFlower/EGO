#!/usr/bin/env python3
"""Small V2-only session boundary for Ego.

This guard reports repository identity, verifies the pinned ITL product-axis
mirror, scans generated active context, and enforces one exact mutation scope.
Historical route transitions are deliberately not reimplemented here.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCOPE = ROOT / "docs/codex/tasks/ego-itl-v2-only-simplification-001a/MUTATION_SCOPE.json"
CLAIM_CEILING = (
    "local explicit V2 product mainline, repository simplification, mirror "
    "integrity, and bounded execution/replay evidence only"
)

# Compatibility readback for one frozen V2 test.  This is not live route
# authority and must not be used to admit new work.
PHASE_C_V2_IMPLEMENTATION_TARGETS = [
    "labs/ego_life_playground_v0/engine.py",
    "labs/ego_life_playground_v0/claims.py",
    "labs/ego_life_playground_v0/microworld.py",
    "tests/test_ego_life_playground_v2_microworld.py",
    "tests/test_ego_life_playground_v0.py",
    "scripts/codex/verify_ego_v2_action_perseveration_repair_001a.py",
    "scripts/tests/test_verify_ego_v2_action_perseveration_repair_001a.py",
    "artifacts/EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A/result.json",
    "artifacts/EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A/trace.jsonl",
    "artifacts/EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A/baseline_comparison.json",
    "artifacts/EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A/ablation_report.json",
    "artifacts/EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A/replay_report.json",
    "artifacts/EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A/leakage_report.json",
    "artifacts/EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A/failure_manifest.json",
    "artifacts/EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A/diagnostic_readback.json",
    "artifacts/EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A/live_repair_receipt.json",
    "artifacts/EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A/claim_ceiling.txt",
]


def _git(root: Path, *args: str, check: bool = True) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def git_readback(root: str | Path = ROOT) -> dict[str, Any]:
    repo = Path(root).resolve()
    upstream = _git(repo, "rev-parse", "--abbrev-ref", "@{upstream}", check=False)
    ahead = behind = None
    if upstream:
        counts = _git(repo, "rev-list", "--left-right", "--count", f"{upstream}...HEAD", check=False)
        if counts:
            behind, ahead = (int(value) for value in counts.split())
    porcelain = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    return {
        "repo_root": str(repo),
        "branch": _git(repo, "branch", "--show-current"),
        "head": _git(repo, "rev-parse", "HEAD"),
        "upstream": upstream or None,
        "ahead": ahead,
        "behind": behind,
        "clean": not bool(porcelain),
        "status_lines": porcelain.splitlines(),
    }


def _product_checks(root: Path, itl_repo: str | Path | None) -> tuple[dict[str, Any], dict[str, Any]]:
    from codex.product_axis import load_product_axis, load_source_pin, verify_pinned_itl_mirror
    from codex.stale_context import scan_repository

    state = load_product_axis(root)
    pin = load_source_pin(root)
    mirror = verify_pinned_itl_mirror(root, itl_repo).to_dict()
    stale = scan_repository(root, state, pin).to_dict()
    return mirror, stale


def build_bootstrap_snapshot(
    root: str | Path = ROOT,
    *,
    itl_repo: str | Path | None = None,
) -> dict[str, Any]:
    repo = Path(root).resolve()
    errors: list[str] = []
    try:
        mirror, stale = _product_checks(repo, itl_repo)
        if mirror["verdict"] != "pass":
            errors.append("product_axis_mirror_invalid")
        if stale["verdict"] != "pass":
            errors.append("active_context_stale")
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        mirror = {"verdict": "fail", "errors": [type(exc).__name__]}
        stale = {"verdict": "fail", "findings": []}
        errors.append(f"product_context_unavailable:{type(exc).__name__}")
    return {
        "verdict": "pass" if not errors else "fail",
        "producer_function": "build_bootstrap_snapshot",
        "aggregation_rule": "pass iff Git identity, pinned ITL mirror, and generated active context are readable and exact",
        "git": git_readback(repo),
        "product_axis_mirror": mirror,
        "stale_context": stale,
        "errors": errors,
        "claim_ceiling": CLAIM_CEILING,
    }


def _changed_paths(root: Path, *, cached: bool) -> list[str]:
    args = ["diff", "--name-only", "--diff-filter=ACDMRTUXB"]
    if cached:
        args.insert(1, "--cached")
        tracked = _git(root, *args).splitlines()
        untracked: list[str] = []
    else:
        tracked = [
            *_git(root, *args).splitlines(),
            *_git(root, "diff", "--cached", "--name-only", "--diff-filter=ACDMRTUXB").splitlines(),
        ]
        untracked = _git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(path.replace("\\", "/") for path in (*tracked, *untracked) if path))


def _matches(path: str, exact: set[str], rules: Iterable[str]) -> bool:
    if path in exact:
        return True
    return any(fnmatch.fnmatchcase(path, rule) for rule in rules if "old-runtime-only" not in rule)


def build_closeout_check(
    root: str | Path = ROOT,
    *,
    mutation_scope: str | Path = DEFAULT_SCOPE,
    itl_repo: str | Path | None = None,
) -> dict[str, Any]:
    repo = Path(root).resolve()
    bootstrap = build_bootstrap_snapshot(repo, itl_repo=itl_repo)
    scope_path = Path(mutation_scope)
    if not scope_path.is_absolute():
        scope_path = repo / scope_path
    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    exact = set(scope.get("exact_non_deletion_paths", []))
    deletion_rules = list(scope.get("deletion_rules", []))
    manifest_path = repo / "artifacts/archive/pre_v2_runtime_retirement_manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        exact.update(row["path"] for row in manifest.get("removed_paths", []))
    changed = _changed_paths(repo, cached=False)
    staged = _changed_paths(repo, cached=True)
    outside = [path for path in changed if not _matches(path, exact, deletion_rules)]
    errors = list(bootstrap["errors"])
    if outside:
        errors.append("changed_path_outside_scope")
    if set(staged) - set(changed):
        errors.append("staged_path_readback_inconsistent")
    return {
        "verdict": "pass" if not errors else "fail",
        "producer_function": "build_closeout_check",
        "aggregation_rule": "pass iff bootstrap passes and every changed/staged path is admitted by the exact task scope or retirement manifest",
        "bootstrap": bootstrap,
        "mutation_scope": str(scope_path),
        "changed_paths": changed,
        "staged_paths": staged,
        "outside_scope": outside,
        "errors": errors,
        "claim_ceiling": CLAIM_CEILING,
    }


def _markdown(payload: dict[str, Any]) -> str:
    git = payload.get("git") or payload.get("bootstrap", {}).get("git", {})
    lines = [
        f"verdict: {payload['verdict']}",
        f"branch: {git.get('branch')}",
        f"head: {git.get('head')}",
        f"clean: {git.get('clean')}",
        f"errors: {json.dumps(payload.get('errors', []))}",
        f"claim_ceiling: {payload['claim_ceiling']}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("bootstrap", "closeout-check"))
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--itl-repo")
    parser.add_argument("--mutation-scope", default=str(DEFAULT_SCOPE))
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args(argv)
    payload = (
        build_bootstrap_snapshot(args.root, itl_repo=args.itl_repo)
        if args.command == "bootstrap"
        else build_closeout_check(
            args.root,
            mutation_scope=args.mutation_scope,
            itl_repo=args.itl_repo,
        )
    )
    print(json.dumps(payload, indent=2, sort_keys=True) if args.format == "json" else _markdown(payload))
    return 0 if payload["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
