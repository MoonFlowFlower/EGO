#!/usr/bin/env python3
"""Callable Phase-A runtime scaling and replay-boundary verifier."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import shutil
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import controller as controller_module  # noqa: E402
from labs.ego_life_playground_v0 import engine  # noqa: E402
from labs.ego_life_playground_v0 import terminal, visual_console  # noqa: E402
from labs.ego_life_playground_v0.controller import PlaygroundController  # noqa: E402
from labs.ego_life_playground_v0.store import (  # noqa: E402
    RecoveryError,
    SQLiteEventStore,
)
from scripts.codex.capture_ego_v2_runtime_scaling_baseline_001a import (  # noqa: E402
    semantic_projection,
)


TASK_ID = "EGO-V2-P0-RUNTIME-SCALING-001A"
RUN_ID = f"{TASK_ID}:semantic-baseline"
SEED = 17
WORLD_SEED = 23
COMMAND_COUNT = 355
CLAIM_CEILING = (
    "Bounded Ego V2 runtime scaling, atomic online commit readback, and explicit "
    "initial-state-plus-commands replay evidence only."
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, int(len(ordered) * 0.95) - 1)]


def _comparable_semantics(value: Mapping[str, Any]) -> dict[str, Any]:
    copied = deepcopy(dict(value))
    metabolism = copied.get("metabolism")
    if isinstance(metabolism, dict):
        metabolism.pop("code_path_hash", None)
    return copied


def benchmark_incremental_controller(
    db_path: Path, baseline: Mapping[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    durations: list[float] = []
    trace_rows: list[dict[str, Any]] = []
    semantic_mismatches: list[int] = []
    readback_failures: list[int] = []
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(
            store,
            run_id=RUN_ID,
            seed=SEED,
            world_seed=WORLD_SEED,
            layout_id="p0_cross_v1",
        )
        for expected in baseline["records"]:
            started = time.perf_counter()
            result = controller.dispatch(trigger_source="ui_run_button")
            duration = time.perf_counter() - started
            if not result.receipt.committed or result.step is None:
                raise RuntimeError(
                    f"incremental dispatch failed at {expected['command']['sequence']}: "
                    f"{result.receipt.error}"
                )
            sequence = int(result.receipt.sequence)
            durations.append(duration)
            if not result.receipt.row_readback_verified:
                readback_failures.append(sequence)
            actual_semantics = _comparable_semantics(
                semantic_projection(controller.state, controller.last_trace)
            )
            expected_semantics = _comparable_semantics(
                expected["semantic_projection"]
            )
            if actual_semantics != expected_semantics:
                semantic_mismatches.append(sequence)
            trace_size = len(engine.canonical_json(controller.last_trace).encode("utf-8"))
            trace_rows.append(
                {
                    "producer_function": (
                        "verify_ego_v2_runtime_scaling_001a."
                        "benchmark_incremental_controller"
                    ),
                    "input_artifacts": [
                        f"baseline_record:{expected['semantic_hash']}",
                        f"command:{controller.last_trace['command_hash']}",
                    ],
                    "run_id": RUN_ID,
                    "seed": SEED,
                    "context_id": "p0_cross_v1:world=23:policy=17",
                    "sequence": sequence,
                    "aggregation_rule": "one atomic controller dispatch",
                    "code_path_hash": controller.run_meta["code_path_hash"],
                    "dispatch_seconds": duration,
                    "trace_bytes": trace_size,
                    "trace_hash": controller.last_trace["trace_hash"],
                    "semantic_hash": engine.canonical_hash(actual_semantics),
                    "row_readback_verified": result.receipt.row_readback_verified,
                    "verification_mode": controller.recovery.verification_mode,
                    "last_full_replay_sequence": (
                        controller.recovery.last_full_replay_sequence
                    ),
                }
            )
        online_state = deepcopy(controller.state)
        online_traces_hash = engine.canonical_hash(controller.recovery.traces)
        started = time.perf_counter()
        recovered = store.recover_run(RUN_ID)
        recovery_seconds = time.perf_counter() - started
        replay = {
            "producer_function": "SQLiteEventStore.recover_run",
            "input_artifacts": [str(db_path)],
            "run_id": RUN_ID,
            "seed": SEED,
            "context_ids": ["p0_cross_v1:world=23:policy=17"],
            "aggregation_rule": "initial_state_plus_355_ordered_commands",
            "code_path_hash": controller.run_meta["code_path_hash"],
            "recovery_seconds": recovery_seconds,
            "state_exact": engine.canonical_json(recovered.state)
            == engine.canonical_json(online_state),
            "trace_chain_exact": engine.canonical_hash(recovered.traces)
            == online_traces_hash,
            "verification_mode": recovered.verification_mode,
            "last_full_replay_sequence": recovered.last_full_replay_sequence,
        }
    first = statistics.median(durations[:32])
    last = statistics.median(durations[-32:])
    sizes = [int(item["trace_bytes"]) for item in trace_rows]
    metrics = {
        "producer_function": (
            "verify_ego_v2_runtime_scaling_001a."
            "benchmark_incremental_controller"
        ),
        "input_artifacts": [str(db_path)],
        "run_id": RUN_ID,
        "seed": SEED,
        "context_ids": ["p0_cross_v1:world=23:policy=17"],
        "aggregation_rule": (
            "p95,max,median(last32)/median(first32),mean/max trace bytes"
        ),
        "code_path_hash": trace_rows[-1]["code_path_hash"],
        "command_count": len(durations),
        "dispatch_p95_seconds": _percentile_95(durations),
        "dispatch_max_seconds": max(durations),
        "first_32_median_seconds": first,
        "last_32_median_seconds": last,
        "last_first_ratio": last / first,
        "trace_mean_bytes": sum(sizes) / len(sizes),
        "trace_max_bytes": max(sizes),
        "semantic_mismatch_sequences": semantic_mismatches,
        "row_readback_failure_sequences": readback_failures,
    }
    return metrics, trace_rows, replay


def benchmark_forced_recovery_ablation(db_path: Path, command_count: int = 32) -> dict[str, Any]:
    durations: list[float] = []
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(
            store,
            run_id=f"{TASK_ID}:forced-full-replay-ablation",
            seed=SEED,
            world_seed=WORLD_SEED,
            layout_id="p0_cross_v1",
        )
        for _ in range(command_count):
            started = time.perf_counter()
            dispatched = controller.dispatch(trigger_source="ui_run_button")
            if not dispatched.receipt.committed:
                raise RuntimeError(dispatched.receipt.error)
            controller.recover()
            durations.append(time.perf_counter() - started)
    return {
        "producer_function": (
            "verify_ego_v2_runtime_scaling_001a."
            "benchmark_forced_recovery_ablation"
        ),
        "input_artifacts": [str(db_path)],
        "run_id": f"{TASK_ID}:forced-full-replay-ablation",
        "seed": SEED,
        "context_ids": ["p0_cross_v1:world=23:policy=17"],
        "aggregation_rule": "dispatch_then_explicit_full_replay_each_tick",
        "code_path_hash": engine.compute_code_path_hash(),
        "command_count": command_count,
        "median_seconds": statistics.median(durations),
        "max_seconds": max(durations),
        "total_seconds": sum(durations),
    }


def run_full_tk_lifecycle(db_path: Path, *, timeout_seconds: float = 180.0) -> dict[str, Any]:
    """Invoke the real Tk Run button and pump its event loop to terminal."""

    import tkinter as tk

    started = time.perf_counter()
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(
            store,
            run_id=f"{TASK_ID}:full-16-life-tk-run",
            seed=701,
            world_seed=30,
            layout_id="p0_cross_v1",
        )
        root = tk.Tk()
        root.withdraw()
        window = visual_console.PlaygroundWindow(root, controller)
        window.display_interval_ms = 1
        invoked = False
        try:
            window.run_button.invoke()
            invoked = True
            deadline = time.perf_counter() + timeout_seconds
            while time.perf_counter() < deadline:
                root.update_idletasks()
                root.update()
                if (
                    controller.state["lifecycle"]["trial_status"] == "terminal"
                    and not window.running
                    and window._run_after_id is None
                    and window._animation_after_id is None
                ):
                    break
                time.sleep(0.001)
            root.update_idletasks()
            root.update()
            terminal_state = deepcopy(controller.state)
            life_results = deepcopy(
                controller.state["lifecycle"]["life_results"]
            )
            history_rows = len(window.history_tree.get_children())
            running = window.running
            run_after_id = window._run_after_id
            triggers = {
                str(frame.trace.get("trigger_source"))
                for frame in controller.recovery.frames
                if isinstance(frame.trace, Mapping)
            }
            verification_mode = controller.recovery.verification_mode
            last_full = controller.recovery.last_full_replay_sequence
            command_count = controller.recovery.command_count
            integrity_blocked = controller.integrity_blocked
        finally:
            window.close()
    return {
        "producer_function": (
            "verify_ego_v2_runtime_scaling_001a.run_full_tk_lifecycle -> "
            "PlaygroundWindow.run_button.invoke -> PlaygroundController.dispatch"
        ),
        "input_artifacts": [str(db_path)],
        "run_id": f"{TASK_ID}:full-16-life-tk-run",
        "seed": 701,
        "context_ids": ["p0_cross_v1:world=30:policy=701"],
        "aggregation_rule": "real Tk Run button event loop until canonical terminal",
        "code_path_hash": engine.compute_code_path_hash(),
        "run_button_invoked": invoked,
        "command_count": command_count,
        "elapsed_seconds": time.perf_counter() - started,
        "trial_status": terminal_state["lifecycle"]["trial_status"],
        "life_result_count": len(life_results),
        "life_survival": [int(item["survival_ticks"]) for item in life_results],
        "verification_mode": verification_mode,
        "last_full_replay_sequence": last_full,
        "integrity_blocked": integrity_blocked,
        "window_running": running,
        "run_after_id": run_after_id,
        "history_row_count": history_rows,
        "history_matches_frames": history_rows == command_count + 1,
        "trigger_sources": sorted(triggers),
    }


def source_scan() -> dict[str, Any]:
    controller_dispatch = inspect.getsource(controller_module.PlaygroundController.dispatch)
    ui_source = inspect.getsource(visual_console.PlaygroundWindow)
    terminal_source = inspect.getsource(terminal.TerminalPlayground)
    checks = {
        "dispatch_has_no_per_tick_recover_run": ".recover_run(" not in controller_dispatch,
        "ui_calls_controller_dispatch": "self.controller.dispatch(" in ui_source,
        "terminal_calls_controller_dispatch": "self.controller.dispatch(" in terminal_source,
        "ui_has_no_compute_step": "compute_step(" not in ui_source,
        "terminal_has_no_compute_step": "compute_step(" not in terminal_source,
        "ui_appends_history_incrementally": "_append_history_frame" in ui_source
        and "rebuild_history=False" in ui_source,
    }
    return {
        "producer_function": "verify_ego_v2_runtime_scaling_001a.source_scan",
        "input_artifacts": [
            "labs/ego_life_playground_v0/controller.py",
            "labs/ego_life_playground_v0/visual_console.py",
            "labs/ego_life_playground_v0/terminal.py",
        ],
        "run_id": RUN_ID,
        "seed": SEED,
        "context_ids": ["source_scan"],
        "aggregation_rule": "all callable entrypoint ownership checks true",
        "code_path_hash": engine.compute_code_path_hash(),
        "checks": checks,
        "all_passed": all(checks.values()),
    }


def _tamper_copy(source: Path, target: Path, mutator: Any) -> dict[str, Any]:
    shutil.copy2(source, target)
    connection = sqlite3.connect(str(target))
    try:
        mutator(connection)
        connection.commit()
    finally:
        connection.close()
    try:
        with SQLiteEventStore(target) as store:
            store.recover_run(RUN_ID)
    except RecoveryError as exc:
        return {
            "failed_closed": True,
            "exception_type": type(exc).__name__,
            "error": str(exc),
        }
    return {"failed_closed": False, "exception_type": None, "error": None}


def tamper_controls(source_db: Path, work_dir: Path) -> dict[str, Any]:
    def trace_td(connection: sqlite3.Connection) -> None:
        row = connection.execute(
            "SELECT sequence, trace_json FROM traces WHERE run_id=? ORDER BY sequence DESC LIMIT 1",
            (RUN_ID,),
        ).fetchone()
        trace = json.loads(row[1])
        trace["survival_learning"]["update"]["td_error"] = 0.123456
        trace["trace_hash"] = engine.compute_trace_hash(trace)
        connection.execute(
            "UPDATE traces SET trace_json=?,trace_hash=? WHERE run_id=? AND sequence=?",
            (engine.canonical_json(trace), trace["trace_hash"], RUN_ID, row[0]),
        )

    def command(connection: sqlite3.Connection) -> None:
        row = connection.execute(
            "SELECT sequence, command_json FROM commands WHERE run_id=? ORDER BY sequence DESC LIMIT 1",
            (RUN_ID,),
        ).fetchone()
        value = json.loads(row[1])
        value["trigger_source"] = "headless_acceptance"
        value["command_hash"] = engine.canonical_hash(
            {key: item for key, item in value.items() if key != "command_hash"}
        )
        connection.execute(
            "UPDATE commands SET command_json=?,command_hash=? WHERE run_id=? AND sequence=?",
            (engine.canonical_json(value), value["command_hash"], RUN_ID, row[0]),
        )

    def initial_q(connection: sqlite3.Connection) -> None:
        row = connection.execute(
            "SELECT initial_state_json FROM runs WHERE run_id=?", (RUN_ID,)
        ).fetchone()
        state = json.loads(row[0])
        state_key = "a" * 64
        state["survival_learner"]["q_values"] = {state_key: {"rest": 0.5}}
        connection.execute(
            "UPDATE runs SET initial_state_json=?,initial_state_hash=? WHERE run_id=?",
            (engine.canonical_json(state), engine.canonical_hash(state), RUN_ID),
        )

    controls = {
        "td_trace_rehashed": _tamper_copy(
            source_db, work_dir / "tamper-td.sqlite3", trace_td
        ),
        "command_rehashed": _tamper_copy(
            source_db, work_dir / "tamper-command.sqlite3", command
        ),
        "initial_q_rehashed": _tamper_copy(
            source_db, work_dir / "tamper-q.sqlite3", initial_q
        ),
    }
    return {
        "producer_function": "verify_ego_v2_runtime_scaling_001a.tamper_controls",
        "input_artifacts": [str(source_db)],
        "run_id": RUN_ID,
        "seed": SEED,
        "context_ids": sorted(controls),
        "aggregation_rule": "all rehashed tamper controls raise RecoveryError",
        "code_path_hash": engine.compute_code_path_hash(),
        "controls": controls,
        "all_failed_closed": all(item["failed_closed"] for item in controls.values()),
    }


def fresh_process_replay(db_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--fresh-replay", str(db_path)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(engine.canonical_json(value) + "\n", encoding="utf-8")


def _database_artifact(path: Path, logical_id: str) -> dict[str, Any]:
    """Describe an ephemeral verifier database without leaking a dead temp path."""

    return {
        "logical_id": logical_id,
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
    }


def verify(output_dir: Path, *, skip_full_lifecycle: bool = False) -> dict[str, Any]:
    baseline_path = output_dir / "semantic_baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ego-v2-runtime-scaling-") as raw_temp:
        work_dir = Path(raw_temp)
        db_path = work_dir / "runtime-355.sqlite3"
        metrics, trace_rows, replay = benchmark_incremental_controller(
            db_path, baseline
        )
        db_bytes = db_path.stat().st_size
        fresh = fresh_process_replay(db_path)
        # Parent-side exact values are derived by one extra explicit replay so
        # the subprocess is compared to computation, not to literals.
        with SQLiteEventStore(db_path) as store:
            parent_recovery = store.recover_run(RUN_ID)
            parent_fresh = {
                "sequence": parent_recovery.last_committed_sequence,
                "state_hash": engine.canonical_hash(parent_recovery.state),
                "trace_chain_hash": engine.canonical_hash(parent_recovery.traces),
            }
        replay["fresh_process"] = fresh
        replay["fresh_process_exact"] = fresh == parent_fresh
        tamper = tamper_controls(db_path, work_dir)
        ablation = benchmark_forced_recovery_ablation(
            work_dir / "forced-recovery.sqlite3"
        )
        lifecycle = (
            {"skipped": True}
            if skip_full_lifecycle
            else run_full_tk_lifecycle(work_dir / "full-lifecycle.sqlite3")
        )
        runtime_artifact = _database_artifact(db_path, "runtime-355.sqlite3")
        forced_artifact = _database_artifact(
            work_dir / "forced-recovery.sqlite3", "forced-recovery.sqlite3"
        )
        metrics["input_artifacts"] = [runtime_artifact]
        replay["input_artifacts"] = [runtime_artifact]
        tamper["input_artifacts"] = [runtime_artifact]
        ablation["input_artifacts"] = [forced_artifact]
        if not skip_full_lifecycle:
            lifecycle["input_artifacts"] = [
                _database_artifact(
                    work_dir / "full-lifecycle.sqlite3",
                    "full-lifecycle.sqlite3",
                )
            ]

        metric_checks = {
            "semantic_exact": not metrics["semantic_mismatch_sequences"],
            "row_readback_all_verified": not metrics[
                "row_readback_failure_sequences"
            ],
            "dispatch_p95_lte_250ms": metrics["dispatch_p95_seconds"] <= 0.250,
            "dispatch_max_lte_500ms": metrics["dispatch_max_seconds"] <= 0.500,
            "last_first_ratio_lt_2": metrics["last_first_ratio"] < 2.0,
            "full_recovery_lte_10s": replay["recovery_seconds"] <= 10.0,
            "trace_mean_lte_32kib": metrics["trace_mean_bytes"] <= 32 * 1024,
            "trace_max_lte_64kib": metrics["trace_max_bytes"] <= 64 * 1024,
            "sqlite_lte_20mib": db_bytes <= 20 * 1024 * 1024,
            "online_full_state_exact": replay["state_exact"],
            "online_full_trace_exact": replay["trace_chain_exact"],
            "fresh_process_exact": replay["fresh_process_exact"],
            "tamper_controls_fail_closed": tamper["all_failed_closed"],
        }
        if not skip_full_lifecycle:
            metric_checks.update(
                {
                    "full_16_lives_terminal": lifecycle["trial_status"] == "terminal"
                    and lifecycle["life_result_count"] == 16
                    and lifecycle["run_button_invoked"] is True
                    and lifecycle["window_running"] is False
                    and lifecycle["run_after_id"] is None
                    and lifecycle["history_matches_frames"] is True
                    and lifecycle["trigger_sources"] == ["ui_run_button"],
                    "terminal_full_replay": lifecycle["verification_mode"]
                    == "full_replay"
                    and lifecycle["last_full_replay_sequence"]
                    == lifecycle["command_count"],
                }
            )
        scan = source_scan()
        metric_checks["single_entrypoint_source_scan"] = scan["all_passed"]
        blockers = sorted(key for key, passed in metric_checks.items() if not passed)
        verdict = "PHASE_A_VERIFIED" if not blockers else "PHASE_A_BLOCKED"

        baseline_comparison = {
            "producer_function": (
                "verify_ego_v2_runtime_scaling_001a.verify"
            ),
            "input_artifacts": [
                {"path": str(baseline_path), "sha256": _sha256(baseline_path)}
            ],
            "run_id": RUN_ID,
            "seed": SEED,
            "context_ids": ["p0_cross_v1:world=23:policy=17"],
            "aggregation_rule": "pinned_prechange_metrics_vs_current_callable_metrics",
            "code_path_hash": engine.compute_code_path_hash(),
            "pinned_prechange": baseline["baseline_metrics"],
            "current": metrics,
            "sqlite_bytes": db_bytes,
        }
        ablation_report = {
            "producer_function": "verify_ego_v2_runtime_scaling_001a.verify",
            "input_artifacts": [runtime_artifact, forced_artifact],
            "run_id": RUN_ID,
            "seed": SEED,
            "context_ids": ["incremental", "forced_full_replay_each_tick"],
            "aggregation_rule": "independent callable forced-recovery intervention",
            "code_path_hash": engine.compute_code_path_hash(),
            "forced_recovery": ablation,
            "incremental_first_32_median_seconds": metrics[
                "first_32_median_seconds"
            ],
            "forced_over_incremental_ratio": ablation["median_seconds"]
            / metrics["first_32_median_seconds"],
            "trace_compaction": {
                "pinned_mean_bytes": baseline["baseline_metrics"][
                    "trace_mean_bytes"
                ],
                "current_mean_bytes": metrics["trace_mean_bytes"],
                "pinned_max_bytes": baseline["baseline_metrics"]["trace_max_bytes"],
                "current_max_bytes": metrics["trace_max_bytes"],
            },
            "ui_incremental_history": scan["checks"][
                "ui_appends_history_incrementally"
            ],
        }
        replay_report = {
            **replay,
            "tamper_controls": tamper,
            "source_scan": scan,
            "full_lifecycle": lifecycle,
        }
        result = {
            "schema_version": "ego.v2.runtime_scaling.result.v1",
            "task_id": TASK_ID,
            "producer_function": "verify_ego_v2_runtime_scaling_001a.verify",
            "input_artifacts": [
                {"path": str(baseline_path), "sha256": _sha256(baseline_path)}
            ],
            "run_id": RUN_ID,
            "seed": SEED,
            "context_ids": [
                "p0_cross_v1:world=23:policy=17",
                "p0_cross_v1:world=30:policy=701",
            ],
            "aggregation_rule": "all predeclared Phase-A acceptance checks",
            "code_path_hash": engine.compute_code_path_hash(),
            "verdict": verdict,
            "checks": metric_checks,
            "blocking_failures": blockers,
            "metrics": metrics,
            "sqlite_bytes": db_bytes,
            "claim_ceiling": CLAIM_CEILING,
        }

    _write_json(output_dir / "baseline_comparison.json", baseline_comparison)
    _write_json(output_dir / "ablation_report.json", ablation_report)
    _write_json(output_dir / "replay_report.json", replay_report)
    _write_json(
        output_dir / "failure_manifest.json",
        {
            "task_id": TASK_ID,
            "verdict": verdict,
            "blocking_failures": blockers,
            "producer_function": "verify_ego_v2_runtime_scaling_001a.verify",
            "code_path_hash": engine.compute_code_path_hash(),
        },
    )
    with (output_dir / "trace.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in trace_rows:
            handle.write(engine.canonical_json(row) + "\n")
    (output_dir / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n", encoding="utf-8"
    )
    _write_json(output_dir / "result.json", result)
    return result


def _fresh_replay(db_path: Path) -> int:
    with SQLiteEventStore(db_path) as store:
        recovered = store.recover_run(RUN_ID)
    print(
        engine.canonical_json(
            {
                "sequence": recovered.last_committed_sequence,
                "state_hash": engine.canonical_hash(recovered.state),
                "trace_chain_hash": engine.canonical_hash(recovered.traces),
            }
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh-replay", type=Path)
    parser.add_argument("--skip-full-lifecycle", action="store_true")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "artifacts" / TASK_ID,
    )
    args = parser.parse_args(argv)
    if args.fresh_replay is not None:
        return _fresh_replay(args.fresh_replay)
    result = verify(
        args.output_dir.resolve(),
        skip_full_lifecycle=args.skip_full_lifecycle,
    )
    print(
        json.dumps(
            {
                "verdict": result["verdict"],
                "blocking_failures": result["blocking_failures"],
                "result": str((args.output_dir / "result.json").resolve()),
            },
            sort_keys=True,
        )
    )
    return 0 if not result["blocking_failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
