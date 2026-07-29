#!/usr/bin/env python3
"""Frozen old-context engineering gate for replay-kernel repair 001F."""

from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import statistics
import sys
import time
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine, predictive_control  # noqa: E402
from labs.ego_life_playground_v0.controller import PlaygroundController  # noqa: E402
from labs.ego_life_playground_v0.store import SQLiteEventStore  # noqa: E402
from scripts.codex import (  # noqa: E402
    verify_ego_v2_factored_predictive_control_boundary_gate_001c as boundary,
)


TASK_ID = "EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F"
PRODUCER = "verify_ego_v2_predictive_replay_kernel_repair_001f"
CONTEXTS = (
    ("p0_cross_v1", 52, 711),
    ("p2_vertical_v1", 54, 711),
)
ALLOWED_WORLD_SEEDS = frozenset({52, 54})
ALLOWED_POLICY_SEEDS = frozenset({711})
CONTAMINATED_WORLD_SEEDS = frozenset(range(30, 151))
FORBIDDEN_FRESH_POLICY_SEEDS = frozenset({721, 722})
CLAIM_CEILING = (
    "Exact-equivalent old-context replay/performance engineering evidence only; "
    "no prediction-learning success, held-out adaptation, survival effect, neural "
    "emergence, agency, AGI, consciousness, or electronic-life evidence."
)
ARTIFACT_DIR = REPO_ROOT / "artifacts" / TASK_ID
FIXTURE_PATH = (
    REPO_ROOT
    / "artifacts"
    / "EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-BOUNDARY-GATE-001C"
    / "prechange_semantic_fixture.json"
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_file(path: Path) -> str:
    return _hash_bytes(path.read_bytes())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical_json(value) + "\n", encoding="utf-8", newline="\n")


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(_canonical_json(row) + "\n")


def _input_artifact(path: Path, *, relative_to: Path = REPO_ROOT) -> dict[str, str]:
    return {
        "path": path.relative_to(relative_to).as_posix(),
        "sha256": _hash_file(path),
    }


def _code_path_hash() -> str:
    paths = (
        Path(__file__).resolve(),
        Path(engine.__file__).resolve(),
        Path(predictive_control.__file__).resolve(),
        Path(boundary.__file__).resolve(),
    )
    return engine.canonical_hash(
        [{"path": path.name, "sha256": _hash_file(path)} for path in paths]
    )


def _provenance(
    function: str,
    *,
    inputs: list[Any],
    run_id: str,
    aggregation_rule: str,
    context_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "producer_function": f"{PRODUCER}.{function}",
        "input_artifacts": inputs,
        "run_id": run_id,
        "seed": [711],
        "context_ids": context_ids or [],
        "life_ids": [1, 2, 3, 4],
        "action_ids": list(engine.ACTIONS),
        "aggregation_rule": aggregation_rule,
        "code_path_hash": _code_path_hash(),
        "runtime": predictive_control.numeric_runtime_contract(),
        "process_mode": "fresh_process" if function == "private_replay" else "gate_process",
    }


def source_path_scan() -> dict[str, Any]:
    paths = {
        "engine": REPO_ROOT / "labs/ego_life_playground_v0/engine.py",
        "predictive_control": REPO_ROOT
        / "labs/ego_life_playground_v0/predictive_control.py",
        "controller": REPO_ROOT / "labs/ego_life_playground_v0/controller.py",
        "store": REPO_ROOT / "labs/ego_life_playground_v0/store.py",
        "visual_console": REPO_ROOT / "labs/ego_life_playground_v0/visual_console.py",
        "terminal": REPO_ROOT / "labs/ego_life_playground_v0/terminal.py",
    }
    trees = {
        name: ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for name, path in paths.items()
    }

    def definitions(tree: ast.AST, name: str) -> int:
        return sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == name
            for node in ast.walk(tree)
        )

    def calls(tree: ast.AST, name: str) -> int:
        return sum(
            isinstance(node, ast.Call)
            and (
                isinstance(node.func, ast.Name)
                and node.func.id == name
                or isinstance(node.func, ast.Attribute)
                and node.func.attr == name
            )
            for node in ast.walk(tree)
        )

    manifest_paths = [item["path"] for item in engine.compute_code_path_manifest()["files"]]
    forbidden = sorted(
        {
            node.name
            for tree in trees.values()
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and ("checkpoint" in node.name.lower() or "stored_plan" in node.name.lower())
        }
    )
    checks = {
        "one_compute_step_definition": definitions(trees["engine"], "compute_step") == 1,
        "one_controller_definition": definitions(
            trees["controller"], "PlaygroundController"
        )
        == 1,
        "one_store_definition": definitions(trees["store"], "SQLiteEventStore") == 1,
        "controller_calls_compute_step_once": calls(trees["controller"], "compute_step")
        == 1,
        "store_calls_compute_step_once": calls(trees["store"], "compute_step") == 1,
        "visual_console_dispatches": calls(trees["visual_console"], "dispatch") >= 1,
        "terminal_dispatches": calls(trees["terminal"], "dispatch") >= 1,
        "predictive_control_bound_once": manifest_paths.count("predictive_control.py") == 1,
        "no_checkpoint_or_stored_plan_reducer": not forbidden,
    }
    return _provenance(
        "source_path_scan",
        inputs=[_input_artifact(path) for path in paths.values()],
        run_id=f"{TASK_ID}:source-path-scan",
        aggregation_rule="python_ast_single_product_path_and_predictor_manifest_binding",
    ) | {
        "input_artifacts": [_input_artifact(path) for path in paths.values()],
        "checks": checks,
        "forbidden_definitions": forbidden,
        "passed": all(checks.values()),
    }


def boundary_checks(report: Mapping[str, Any]) -> dict[str, bool]:
    recoveries = report["fresh_recoveries"]
    return {
        "three_fresh_recoveries_at_most_10s_and_exact": len(recoveries) == 3
        and all(
            float(item.get("seconds", item.get("recover_run_seconds"))) <= 10.0
            and bool(item["exact"])
            for item in recoveries
        ),
        "trace_mean_at_most_32768_bytes": float(report["trace_mean_bytes"])
        <= 32768.0,
        "trace_max_at_most_65536_bytes": int(report["trace_max_bytes"]) <= 65536,
        "dispatch_p95_at_most_250ms": float(report["dispatch_p95_seconds"])
        <= 0.250,
        "dispatch_max_at_most_500ms": float(report["dispatch_max_seconds"])
        <= 0.500,
        "row_readbacks_verified": bool(report["row_readbacks_verified"]),
        "tamper_controls_passed": bool(report["tamper_controls_passed"]),
        "source_path_scan_passed": bool(report["source_path_scan_passed"]),
        "scalar_trace_rows_exact": bool(report["scalar_trace_rows_exact"]),
        "scalar_final_state_exact": bool(report["scalar_final_state_exact"]),
        "recovery_surfaces_exact": bool(report.get("recovery_surfaces_exact", True)),
        "tail_ratio_below_2": float(report.get("duration_tail_ratio", 0.0)) < 2.0,
        "sqlite_at_most_20mib": int(report.get("sqlite_and_sidecar_bytes", 0))
        <= 20 * 1024 * 1024,
    }


def compare_sqlite_rows(left: Path, right: Path) -> dict[str, Any]:
    def rows(path: Path, table: str, payload: str) -> list[tuple[int, str]]:
        connection = sqlite3.connect(path)
        try:
            return [
                (int(sequence), str(raw))
                for sequence, raw in connection.execute(
                    f"SELECT sequence, {payload} FROM {table} ORDER BY sequence"
                ).fetchall()
            ]
        finally:
            connection.close()

    left_commands = rows(left, "commands", "command_json")
    right_commands = rows(right, "commands", "command_json")
    left_traces = rows(left, "traces", "trace_json")
    right_traces = rows(right, "traces", "trace_json")
    return {
        "producer_function": f"{PRODUCER}.compare_sqlite_rows",
        "left_sha256": _hash_file(left),
        "right_sha256": _hash_file(right),
        "command_row_count": len(left_commands),
        "trace_row_count": len(left_traces),
        "command_rows_exact": left_commands == right_commands,
        "trace_rows_exact": left_traces == right_traces,
        "left_command_rows_hash": engine.canonical_hash(left_commands),
        "right_command_rows_hash": engine.canonical_hash(right_commands),
        "left_trace_rows_hash": engine.canonical_hash(left_traces),
        "right_trace_rows_hash": engine.canonical_hash(right_traces),
        "aggregation_rule": "ordered_sqlite_command_and_trace_payload_byte_equality",
        "code_path_hash": _code_path_hash(),
    }


def result_verdict(context_reports: list[Mapping[str, Any]]) -> str:
    if context_reports and all(
        all(bool(value) for value in report["checks"].values())
        for report in context_reports
    ):
        return "PREDICTIVE_REPLAY_KERNEL_BOUNDARY_REPAIRED"
    return "BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION"


def _context_id(layout: str, world_seed: int, policy_seed: int) -> str:
    return f"{layout}:world={world_seed}:policy={policy_seed}"


def _run_scalar_ablation(
    output_dir: Path,
    *,
    layout: str,
    world_seed: int,
    policy_seed: int,
    run_id: str,
) -> dict[str, Any]:
    if world_seed not in ALLOWED_WORLD_SEEDS or policy_seed not in ALLOWED_POLICY_SEEDS:
        raise RuntimeError("scalar ablation is outside the consumed-context allowlist")
    path = output_dir / f"scalar_{layout}.sqlite3"
    for candidate in (path, Path(str(path) + "-wal"), Path(str(path) + "-shm")):
        if candidate.exists():
            candidate.unlink()
    interventions = dict(
        engine.DEFAULT_INTERVENTIONS,
        predictive_control_mode="factored_mpc",
        update_mode="canonical",
    )
    original_plan = predictive_control.plan_action

    def scalar_plan(**kwargs: Any) -> dict[str, Any]:
        return original_plan(**kwargs, _prewarm_predictions=False)

    durations: list[float] = []
    predictive_control.plan_action = scalar_plan
    try:
        with SQLiteEventStore(path) as store:
            controller = PlaygroundController(
                store,
                run_id=run_id,
                seed=policy_seed,
                world_seed=world_seed,
                layout_id=layout,
            )
            while len(controller.state["lifecycle"]["life_results"]) < 4:
                started = time.perf_counter()
                dispatched = controller.dispatch(
                    interventions, trigger_source="ui_run_button"
                )
                durations.append(time.perf_counter() - started)
                if not dispatched.receipt.committed:
                    raise RuntimeError(dispatched.receipt.error)
            final_state_hash = engine.state_hash(controller.state)
            final_model_hash = predictive_control.model_hash(
                controller.state["predictive_control"]
            )
            command_count = controller.recovery.command_count
    finally:
        predictive_control.plan_action = original_plan
    return _provenance(
        "_run_scalar_ablation",
        inputs=[{"path": path.name, "sha256": _hash_file(path)}],
        run_id=f"{TASK_ID}:scalar:{_context_id(layout, world_seed, policy_seed)}",
        aggregation_rule="same_controller_path_with_exact_scalar_prediction_kernel_ablation",
        context_ids=[_context_id(layout, world_seed, policy_seed)],
    ) | {
        "database_path": path.name,
        "world_seed": world_seed,
        "policy_seed": policy_seed,
        "command_count": command_count,
        "dispatch_total_seconds": sum(durations),
        "dispatch_p95_seconds": sorted(durations)[
            max(0, math.ceil(len(durations) * 0.95) - 1)
        ],
        "dispatch_max_seconds": max(durations),
        "final_state_hash": final_state_hash,
        "final_model_hash": final_model_hash,
        "ablation_instrument": (
            "checker-owned callable wrapper invokes live plan_action with "
            "_prewarm_predictions=False; no product command exposes this selector"
        ),
    }


def _configure_boundary_helper() -> None:
    boundary.TASK_ID = TASK_ID
    boundary.PRODUCER = PRODUCER
    boundary.CONTEXTS = CONTEXTS
    boundary.ALLOWED_WORLD_SEEDS = ALLOWED_WORLD_SEEDS
    boundary.ALLOWED_POLICY_SEEDS = ALLOWED_POLICY_SEEDS
    boundary.FORBIDDEN_WORLD_SEEDS = CONTAMINATED_WORLD_SEEDS - ALLOWED_WORLD_SEEDS
    boundary.FORBIDDEN_POLICY_SEEDS = FORBIDDEN_FRESH_POLICY_SEEDS
    boundary.CLAIM_CEILING = CLAIM_CEILING


def run_gate(output_dir: Path) -> dict[str, Any]:
    _configure_boundary_helper()
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    scan = source_path_scan()
    context_reports: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []
    for layout, world_seed, policy_seed in CONTEXTS:
        context_id = _context_id(layout, world_seed, policy_seed)
        optimized, rows, _steps = boundary._run_smoke_context(  # noqa: SLF001
            output_dir,
            fixture,
            layout,
            world_seed,
            policy_seed,
        )
        trace_rows.extend(rows)
        run_id = str(optimized["run_id"])
        scalar = _run_scalar_ablation(
            output_dir,
            layout=layout,
            world_seed=world_seed,
            policy_seed=policy_seed,
            run_id=run_id,
        )
        comparison = compare_sqlite_rows(
            output_dir / optimized["database_path"],
            output_dir / scalar["database_path"],
        )
        online = optimized["recovery_surfaces"]["online"]
        scalar_state_exact = scalar["final_state_hash"] == online["state_hash"]
        check_input = {
            "fresh_recoveries": optimized["recovery_attempts"],
            "trace_mean_bytes": optimized["trace_mean_bytes"],
            "trace_max_bytes": optimized["trace_max_bytes"],
            "dispatch_p95_seconds": optimized["dispatch_p95_seconds"],
            "dispatch_max_seconds": optimized["dispatch_max_seconds"],
            "row_readbacks_verified": optimized["row_readbacks_verified"],
            "tamper_controls_passed": optimized["all_tamper_controls_rejected"],
            "source_path_scan_passed": scan["passed"],
            "scalar_trace_rows_exact": comparison["trace_rows_exact"],
            "scalar_final_state_exact": scalar_state_exact,
            "recovery_surfaces_exact": optimized["all_recovery_surfaces_exact"],
            "duration_tail_ratio": optimized["duration_tail_ratio"],
            "sqlite_and_sidecar_bytes": optimized["sqlite_and_sidecar_bytes"],
        }
        checks = boundary_checks(check_input)
        context_reports.append(
            _provenance(
                "run_gate",
                inputs=[
                    {"path": optimized["database_path"], "sha256": _hash_file(output_dir / optimized["database_path"])},
                    {"path": scalar["database_path"], "sha256": _hash_file(output_dir / scalar["database_path"])},
                ],
                run_id=f"{TASK_ID}:context:{context_id}",
                aggregation_rule="all_exactness_performance_trace_tamper_and_single_path_checks",
                context_ids=[context_id],
            )
            | {
                "context_id": context_id,
                "optimized": optimized,
                "scalar_ablation": scalar,
                "row_comparison": comparison,
                "scalar_final_state_exact": scalar_state_exact,
                "checks": checks,
                "failed_checks": sorted(key for key, value in checks.items() if not value),
            }
        )
        baseline_rows.append(
            {
                "context_id": context_id,
                "optimized_dispatch_total_seconds": sum(
                    float(row["dispatch_seconds"])
                    for row in rows
                    if row["context_ids"] == [context_id]
                ),
                "scalar_dispatch_total_seconds": scalar["dispatch_total_seconds"],
                "command_rows_exact": comparison["command_rows_exact"],
                "trace_rows_exact": comparison["trace_rows_exact"],
                "final_state_exact": scalar_state_exact,
            }
        )

    verdict = result_verdict(context_reports)
    context_ids = [_context_id(*context) for context in CONTEXTS]
    performance = _provenance(
        "run_gate",
        inputs=[_input_artifact(FIXTURE_PATH)],
        run_id=f"{TASK_ID}:performance",
        aggregation_rule="all_frozen_thresholds_over_two_consumed_contexts",
        context_ids=context_ids,
    ) | {"contexts": context_reports}
    baseline = _provenance(
        "run_gate",
        inputs=[{"context_id": row["context_id"]} for row in baseline_rows],
        run_id=f"{TASK_ID}:baseline",
        aggregation_rule="optimized_kernel_vs_callable_scalar_ablation_same_rows",
        context_ids=context_ids,
    ) | {"comparison": baseline_rows}
    ablation = _provenance(
        "run_gate",
        inputs=[{"context_id": row["context_id"]} for row in baseline_rows],
        run_id=f"{TASK_ID}:ablation",
        aggregation_rule="disable_prewarm_and_require_byte_exact_behavior_with_slower_or_equal_runtime",
        context_ids=context_ids,
    ) | {
        "prewarm_disabled": True,
        "all_trace_rows_exact": all(row["trace_rows_exact"] for row in baseline_rows),
        "all_final_states_exact": all(row["final_state_exact"] for row in baseline_rows),
        "runtime_comparison": baseline_rows,
    }
    replay = _provenance(
        "run_gate",
        inputs=[
            {
                "path": report["optimized"]["database_path"],
                "sha256": _hash_file(output_dir / report["optimized"]["database_path"]),
            }
            for report in context_reports
        ],
        run_id=f"{TASK_ID}:replay",
        aggregation_rule="fresh_process_full_recompute_plus_four_rehash_tamper_controls",
        context_ids=context_ids,
    ) | {
        "source_path_scan": scan,
        "contexts": [
            {
                "context_id": report["context_id"],
                "fresh_recoveries": report["optimized"]["recovery_attempts"],
                "recovery_surfaces": report["optimized"]["recovery_surfaces"],
                "tamper_controls": report["optimized"]["tamper_controls"],
                "row_comparison": report["row_comparison"],
            }
            for report in context_reports
        ],
    }
    result = _provenance(
        "run_gate",
        inputs=[_input_artifact(FIXTURE_PATH)],
        run_id=f"{TASK_ID}:result",
        aggregation_rule="all_context_checks_must_pass",
        context_ids=context_ids,
    ) | {
        "task_id": TASK_ID,
        "verdict": verdict,
        "layer": "engineering_implementation_and_old_context_performance_verification",
        "current_additive_framing": "CURRENT_OUTCOME_CONDITIONED_ADDITIVE_FRAMING_EXHAUSTED",
        "mechanism_family": "MECHANISM_FAMILY_NOT_FALSIFIED",
        "contexts": [
            {
                "context_id": report["context_id"],
                "checks": report["checks"],
                "failed_checks": report["failed_checks"],
            }
            for report in context_reports
        ],
        "fresh_effect_seeds_consumed": False,
        "heldout_worlds_executed": [],
        "ineligible_contaminated_worlds": list(range(30, 151)),
        "future_heldout_requirement": (
            "externally selected commitment-hashed opaque world ids wholly >150 "
            "after implementation, priors, thresholds, and development verdict freeze"
        ),
        "eligible_for_old_context_learning_successor_card": verdict
        == "PREDICTIVE_REPLAY_KERNEL_BOUNDARY_REPAIRED",
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_jsonl(output_dir / "trace.jsonl", trace_rows)
    _write_json(output_dir / "performance_report.json", performance)
    _write_json(output_dir / "baseline_comparison.json", baseline)
    _write_json(output_dir / "ablation_report.json", ablation)
    _write_json(output_dir / "replay_report.json", replay)
    _write_json(output_dir / "result.json", result)
    (output_dir / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
    )
    if verdict != "PREDICTIVE_REPLAY_KERNEL_BOUNDARY_REPAIRED":
        _write_json(
            output_dir / "failure_manifest.json",
            _provenance(
                "run_gate",
                inputs=[{"context_id": report["context_id"]} for report in context_reports],
                run_id=f"{TASK_ID}:failure",
                aggregation_rule="all_failed_context_checks",
                context_ids=context_ids,
            )
            | {
                "verdict": verdict,
                "failures": [
                    {
                        "context_id": report["context_id"],
                        "failed_checks": report["failed_checks"],
                    }
                    for report in context_reports
                    if report["failed_checks"]
                ],
            },
        )
    return result


def _run_formal_gate() -> dict[str, Any]:
    if ARTIFACT_DIR.exists():
        raise RuntimeError("001F formal artifact already exists; rerun is frozen")
    staging = ARTIFACT_DIR.with_name(f".{TASK_ID}.{os.getpid()}.tmp")
    if staging.exists():
        raise RuntimeError("001F staging directory already exists")
    staging.mkdir(parents=True)
    try:
        result = run_gate(staging)
        os.replace(staging, ARTIFACT_DIR)
        return result
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true")
    parser.add_argument("--private-replay", type=Path)
    parser.add_argument("--private-run-id")
    args = parser.parse_args(argv)
    if args.private_replay is not None:
        if args.gate or not args.private_run_id:
            parser.error("private replay requires only --private-run-id")
        _configure_boundary_helper()
        payload = boundary._private_replay(  # noqa: SLF001
            args.private_replay.resolve(), args.private_run_id
        )
        print(_canonical_json(payload))
        return 0
    if not args.gate or args.private_run_id is not None:
        parser.error("the public surface is exactly --gate")
    print(_canonical_json(_run_formal_gate()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

