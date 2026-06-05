#!/usr/bin/env python3
"""Run the EgoOperator-first repo validation set."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Check:
    category: str
    name: str
    command: Sequence[str]
    source: str
    run_in_fast: bool
    run_in_full: bool
    env_overrides: dict[str, str] | None = None
    precondition_reason: str | None = None


@dataclass(frozen=True)
class Result:
    category: str
    name: str
    command: str
    source: str
    status: str
    note: str
    returncode: int | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run EgoOperator-first repo validation checks")
    parser.add_argument("--mode", choices=["fast", "full"], required=True, help="Validation depth")
    parser.add_argument("--dry-run", action="store_true", help="Print detected commands without executing them")
    return parser.parse_args()


def python_script(path: str, *args: str) -> list[str]:
    return [sys.executable, path, *args]


def detect_checks() -> list[Check]:
    specs: list[Check] = []

    def add_if_exists(
        *,
        category: str,
        name: str,
        rel_path: str,
        args: tuple[str, ...] = (),
        run_in_fast: bool = True,
        run_in_full: bool = True,
    ) -> None:
        if not (ROOT / rel_path).exists():
            specs.append(
                Check(
                    category=category,
                    name=name,
                    command=(),
                    source=rel_path,
                    run_in_fast=False,
                    run_in_full=False,
                    precondition_reason="missing check script",
                )
            )
            return
        specs.append(
            Check(
                category=category,
                name=name,
                command=python_script(rel_path, *args),
                source=rel_path,
                run_in_fast=run_in_fast,
                run_in_full=run_in_full,
            )
        )

    add_if_exists(category="lint", name="Codex repo lint", rel_path="scripts/codex/lint_repo.py")
    add_if_exists(
        category="governance",
        name="Program-state integrity gate",
        rel_path="scripts/codex/check_program_state_integrity.py",
        args=("--skip-diff-check",),
    )
    add_if_exists(
        category="governance",
        name="Route-convergence drift gate",
        rel_path="scripts/codex/verify_route_convergence.py",
    )
    add_if_exists(
        category="governance",
        name="Mainline clarity and staged-exhaust gate",
        rel_path="scripts/codex/verify_mainline_clarity.py",
    )
    add_if_exists(
        category="governance",
        name="Legacy archival purge anti-regression gate",
        rel_path="scripts/codex/verify_legacy_archival_purge.py",
    )
    add_if_exists(
        category="governance",
        name="Runtime authority boundary gate",
        rel_path="scripts/codex/check_runtime_authority_boundaries.py",
    )
    return specs


def should_run(check: Check, mode: str) -> tuple[bool, str | None]:
    if check.precondition_reason:
        return False, check.precondition_reason
    if mode == "fast" and check.run_in_fast:
        return True, None
    if mode == "full" and check.run_in_full:
        return True, None
    return False, "not selected for this mode"


def run_check(check: Check, *, mode: str, dry_run: bool) -> Result:
    command_str = " ".join(check.command) if check.command else "(none)"
    should_execute, reason = should_run(check, mode)
    if not should_execute:
        return Result(
            category=check.category,
            name=check.name,
            command=command_str,
            source=check.source,
            status="skipped",
            note=reason or "not selected",
        )
    if dry_run:
        return Result(
            category=check.category,
            name=check.name,
            command=command_str,
            source=check.source,
            status="skipped",
            note="dry-run",
        )

    env = os.environ.copy()
    if check.env_overrides:
        env.update(check.env_overrides)
    proc = subprocess.run(list(check.command), cwd=ROOT, env=env, text=True)
    if proc.returncode == 0:
        return Result(
            category=check.category,
            name=check.name,
            command=command_str,
            source=check.source,
            status="success",
            note="ok",
            returncode=0,
        )
    return Result(
        category=check.category,
        name=check.name,
        command=command_str,
        source=check.source,
        status="failed",
        note=f"exit={proc.returncode}",
        returncode=proc.returncode,
    )


def print_summary(results: Iterable[Result], *, mode: str) -> None:
    print(f"Codex verify summary (mode={mode})")
    print("=" * 96)
    print(f"{'category':<12} {'status':<8} {'name':<42} {'source':<32} note")
    print("-" * 96)
    for result in results:
        print(
            f"{result.category:<12} {result.status:<8} {result.name[:42]:<42} "
            f"{result.source[:32]:<32} {result.note}"
        )
        print(f"  command: {result.command}")


def main() -> int:
    args = parse_args()
    checks = detect_checks()
    results = [run_check(check, mode=args.mode, dry_run=args.dry_run) for check in checks]
    print_summary(results, mode=args.mode)
    return 1 if any(result.status == "failed" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
