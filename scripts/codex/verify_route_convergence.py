#!/usr/bin/env python3
"""Verify one pinned product mirror and its generated Ego reader surface."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from typing import Any
import uuid


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR.parent))

from codex.product_axis import load_product_axis, load_source_pin, verify_pinned_itl_mirror
from codex.retired_runtime_inventory import (
    RETIRED_ROOTS,
    scan_current_legacy_callers,
    verify_manifest_recoverable,
    verify_preserved_untracked_inventory,
)
from codex.stale_context import run_positive_controls, scan_repository


ROOT = Path(__file__).resolve().parents[2]
PRODUCERS = (
    "labs/ego_life_playground_v0/engine.py",
    "labs/ego_life_playground_v0/microworld.py",
    "labs/ego_life_playground_v0/claims.py",
    "labs/ego_life_playground_v0/store.py",
)
RETIREMENT_MANIFEST = "artifacts/archive/pre_v2_runtime_retirement_manifest.json"
ACTIVE_EXECUTION_PATHS = (
    "labs/ego_life_playground_v0/app.py",
    "labs/ego_life_playground_v0/controller.py",
    "labs/ego_life_playground_v0/engine.py",
    "labs/ego_life_playground_v0/store.py",
    "labs/ego_life_playground_v0/terminal.py",
    "labs/ego_life_playground_v0/visual_console.py",
    "scripts/run_ego_life_playground_v0.py",
)


def _class_definitions(path: Path, name: str) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return sum(isinstance(node, ast.ClassDef) and node.name == name for node in ast.walk(tree))


def scan_single_execution_path(root: str | Path = ROOT) -> dict[str, Any]:
    """Locate the only controller, reducer, store, dispatch, and replay definitions."""

    repo = Path(root).resolve()
    expected = {
        "class:PlaygroundController": ["labs/ego_life_playground_v0/controller.py"],
        "class:SQLiteEventStore": ["labs/ego_life_playground_v0/store.py"],
        "function:compute_step": ["labs/ego_life_playground_v0/engine.py"],
        "function:dispatch": ["labs/ego_life_playground_v0/controller.py"],
        "function:recover_run": ["labs/ego_life_playground_v0/store.py"],
    }
    found = {name: [] for name in expected}
    for relative in ACTIVE_EXECUTION_PATHS:
        path = repo / relative
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                key = f"class:{node.name}"
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                key = f"function:{node.name}"
            else:
                continue
            if key in found:
                found[key].append(relative)
    errors = [
        f"{name}:{locations!r}"
        for name, locations in found.items()
        if locations != expected[name]
    ]
    return {
        "verdict": "pass" if not errors else "fail",
        "producer_function": "scan_single_execution_path",
        "input_artifacts": list(ACTIVE_EXECUTION_PATHS),
        "run_id": f"single-v2-path-{uuid.uuid4().hex}",
        "aggregation_rule": "pass iff the active source AST contains exactly one canonical controller, reducer, store, dispatch, and replay/recompute definition at the frozen paths",
        "code_path_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "expected": expected,
        "found": found,
        "errors": errors,
    }


def run_visual_smoke(root: str | Path = ROOT) -> dict[str, Any]:
    """Run the existing real-Tk verifier and retain its bounded artifact set."""

    repo = Path(root).resolve()
    verifier = repo / "scripts/codex/verify_ego_v2_p0_visual_console_live_001a.py"
    visual_root = repo / "artifacts/EGO-ITL-V2-ONLY-SIMPLIFICATION-001A/visual_smoke"
    output = visual_root / "evidence"
    screenshot = visual_root / "visual.png"
    command = [
        sys.executable,
        str(verifier),
        "--output-dir",
        str(output),
        "--screenshot",
        str(screenshot),
    ]
    completed = subprocess.run(
        command,
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    payload: dict[str, Any] | None = None
    parse_error: str | None = None
    try:
        payload = json.loads(completed.stdout.strip())
    except (json.JSONDecodeError, TypeError) as exc:
        parse_error = f"{type(exc).__name__}:{exc}"
    retained = [*sorted(output.glob("*")), screenshot]
    artifact_hashes = {
        path.relative_to(repo).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in retained
        if path.is_file()
    }
    errors = []
    if completed.returncode != 0:
        errors.append(f"returncode:{completed.returncode}")
    if parse_error:
        errors.append(parse_error)
    if not payload or payload.get("verdict") != "pass":
        errors.append("visual_verdict")
    return {
        "verdict": "pass" if not errors else "fail",
        "producer_function": "run_visual_smoke",
        "input_artifacts": [
            "scripts/codex/verify_ego_v2_p0_visual_console_live_001a.py",
            "labs/ego_life_playground_v0/controller.py",
            "labs/ego_life_playground_v0/visual_console.py",
        ],
        "run_id": (payload or {}).get("run_id", f"visual-smoke-{uuid.uuid4().hex}"),
        "seed_context": (payload or {}).get("seed_context_episode_ids"),
        "aggregation_rule": "pass iff a fresh process runs the real Tk verifier, all computed UI/SQLite/replay checks pass, and the retained bounded evidence set is hashed",
        "code_path_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "command": command,
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode("utf-8")).hexdigest(),
        "artifact_hashes": artifact_hashes,
        "computed_result": payload,
        "errors": errors,
    }


def build_retirement_evidence(
    root: str | Path = ROOT,
    *,
    full_local_recovery: bool = False,
) -> dict[str, Any]:
    """Verify clone-portable retirement by default and local quarantine on request."""

    repo = Path(root).resolve()
    manifest = json.loads((repo / RETIREMENT_MANIFEST).read_text(encoding="utf-8"))
    tracked_recovery = verify_manifest_recoverable(repo, manifest).to_dict()
    active_retired_roots = [
        root_text.rstrip("/")
        for root_text in RETIRED_ROOTS
        if (repo / root_text.rstrip("/")).exists()
    ]
    untracked_recovery = (
        verify_preserved_untracked_inventory(
            repo, manifest["untracked_preservation"]
        )
        if full_local_recovery
        else None
    )
    errors = []
    if tracked_recovery["verdict"] != "pass":
        errors.append("tracked_recovery")
    if active_retired_roots:
        errors.append("active_retired_roots")
    if untracked_recovery is not None and untracked_recovery["verdict"] != "pass":
        errors.append("untracked_recovery")
    return {
        "verdict": "pass" if not errors else "fail",
        "producer_function": "build_retirement_evidence",
        "input_artifacts": [RETIREMENT_MANIFEST, manifest["rollback_tag"]],
        "run_id": f"retirement-evidence-{uuid.uuid4().hex}",
        "aggregation_rule": "pass iff every tracked retired blob is recoverable from the rollback tag and active retired roots are absent; when full local retirement recovery is requested, every preserved untracked byte must also be recoverable from the external quarantine",
        "code_path_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rollback_tag": manifest["rollback_tag"],
        "rollback_commit": manifest["rollback_commit"],
        "removed_path_count": manifest["removed_path_count"],
        "active_retired_roots": active_retired_roots,
        "full_local_recovery_requested": full_local_recovery,
        "tracked_recovery": tracked_recovery,
        "untracked_recovery": untracked_recovery,
        "errors": errors,
    }


def _run_json_lines(root: Path, arguments: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    command = [sys.executable, str(root / "scripts/run_ego_life_playground_v0.py"), *arguments]
    result = subprocess.run(command, cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    rows = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    return rows, command


def run_runtime_evidence(root: str | Path = ROOT) -> dict[str, Any]:
    """Exercise the explicit launcher, terminal path, SQLite trace, and fresh replay."""

    repo = Path(root).resolve()
    artifact_dir = repo / "artifacts/EGO-ITL-V2-ONLY-SIMPLIFICATION-001A"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    db_path = artifact_dir / "runtime.sqlite3"
    export_path = artifact_dir / "runtime_export.json"
    for path in (db_path, export_path):
        if path.exists():
            path.unlink()
    runtime_run_id = "ego-itl-v2-only-runtime-001a"
    quick, quick_command = _run_json_lines(
        repo,
        ["--quick-check", "--db", str(db_path), "--run-id", runtime_run_id],
    )
    terminal, terminal_command = _run_json_lines(
        repo,
        [
            "--terminal", "--db", str(db_path), "--run-id", runtime_run_id,
            "--command", "step resource_appears",
            "--command", "run 2",
            "--command", f"save {export_path}",
            "--command", "replay",
        ],
    )
    fresh, fresh_command = _run_json_lines(
        repo,
        [
            "--terminal", "--db", str(db_path), "--run-id", runtime_run_id,
            "--command", f"load {runtime_run_id}",
            "--command", "replay",
        ],
    )
    with sqlite3.connect(db_path) as connection:
        counts = {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table} WHERE run_id = ?", (runtime_run_id,)).fetchone()[0])
            for table in ("runs", "commands", "traces")
        }
    status_sequence = [row.get("status") for row in terminal]
    fresh_status_sequence = [row.get("status") for row in fresh]
    checks = {
        "quick_check_transition": bool(quick and quick[-1].get("clock", {}).get("global_tick", 0) >= 1),
        "terminal_step_run_save_replay": status_sequence == ["committed", "committed", "saved", "recomputed"],
        "sqlite_state_and_trace": counts["runs"] == 1 and counts["commands"] == counts["traces"] >= 4,
        "fresh_process_load_replay": fresh_status_sequence == ["loaded", "recomputed"] and fresh[-1].get("frame_count") == counts["traces"] + 1,
        "export_present": export_path.is_file() and export_path.stat().st_size > 0,
    }
    hashes = {
        path.relative_to(repo).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (db_path, export_path)
    }
    return {
        "verdict": "pass" if all(checks.values()) else "fail",
        "producer_function": "run_runtime_evidence",
        "input_artifacts": [
            "scripts/run_ego_life_playground_v0.py",
            "labs/ego_life_playground_v0/controller.py",
            "labs/ego_life_playground_v0/store.py",
            *hashes,
        ],
        "run_id": runtime_run_id,
        "seed_context": {"seed": 17, "world_seed": 271828, "episode_id": runtime_run_id},
        "aggregation_rule": "pass iff explicit quick-check commits, terminal step/run/save/replay succeeds, SQLite command/trace counts agree, and a fresh process loads and recomputes every frame",
        "code_path_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "commands": [quick_command, terminal_command, fresh_command],
        "checks": checks,
        "sqlite_counts": counts,
        "artifact_hashes": hashes,
        "quick_check": quick,
        "terminal_status_sequence": status_sequence,
        "fresh_process_status_sequence": fresh_status_sequence,
        "fresh_process_frame_count": fresh[-1].get("frame_count") if fresh else None,
    }


def build_report(
    root: str | Path = ROOT,
    *,
    itl_repo: str | Path | None = None,
    runtime_check: bool = False,
    visual_check: bool = False,
    retirement_check: bool = False,
) -> dict[str, Any]:
    repo = Path(root).resolve()
    state = load_product_axis(repo)
    pin = load_source_pin(repo)
    mirror = verify_pinned_itl_mirror(repo, itl_repo).to_dict()
    stale = scan_repository(repo, state, pin).to_dict()
    positives = run_positive_controls(state, pin)
    callers = list(scan_current_legacy_callers(repo))
    structure = scan_single_execution_path(repo)
    controller_defs = _class_definitions(repo / "labs/ego_life_playground_v0/controller.py", "PlaygroundController")
    retirement = build_retirement_evidence(
        repo, full_local_recovery=retirement_check
    )
    producer_hashes = {
        path: hashlib.sha256((repo / path).read_bytes()).hexdigest()
        for path in PRODUCERS
    }
    checks = {
        "pinned_mirror": mirror["verdict"],
        "generated_views": stale["verdict"],
        "stale_scanner_positive_controls": positives["verdict"],
        "legacy_callers_zero": "pass" if not callers else "fail",
        "single_execution_path": structure["verdict"],
        "retirement_recovery": retirement["verdict"],
    }
    errors = [name for name, verdict in checks.items() if verdict != "pass"]
    runtime = run_runtime_evidence(repo) if runtime_check else None
    if runtime is not None and runtime["verdict"] != "pass":
        errors.append("runtime_evidence")
    visual = run_visual_smoke(repo) if visual_check else None
    if visual is not None and visual["verdict"] != "pass":
        errors.append("visual_smoke")
    return {
        "task_id": "EGO-ITL-V2-ONLY-SIMPLIFICATION-001A",
        "producer_function": "build_report",
        "input_artifacts": sorted([*PRODUCERS, *stale["input_artifacts"], *mirror["input_artifacts"]]),
        "run_id": f"ego-v2-only-convergence-{uuid.uuid4().hex}",
        "aggregation_rule": "pass iff pinned mirror, generated views, positive controls, caller scan, retirement recovery, and one controller/reducer/store/replay structure pass; requested runtime and visual checks must also pass",
        "code_path_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "checks": checks,
        "mirror": mirror,
        "stale_context": stale,
        "positive_controls": positives,
        "legacy_callers": callers,
        "controller_definition_count": controller_defs,
        "single_execution_path": structure,
        "retirement_evidence": retirement,
        "causal_producer_hashes": producer_hashes,
        "runtime_evidence": runtime,
        "visual_smoke": visual,
        "validation_errors": errors,
        "claim_ceiling": "local V2 product routing and evidence hygiene only",
        "verdict": "pass" if not errors else "fail",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--itl-repo")
    parser.add_argument("--output")
    parser.add_argument("--runtime-check", action="store_true")
    parser.add_argument("--visual-check", action="store_true")
    parser.add_argument("--retirement-check", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(
        args.root,
        itl_repo=args.itl_repo,
        runtime_check=args.runtime_check,
        visual_check=args.visual_check,
        retirement_check=args.retirement_check,
    )
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
