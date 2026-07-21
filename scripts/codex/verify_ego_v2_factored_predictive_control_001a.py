#!/usr/bin/env python3
"""Callable Phase-B product adaptation verifier with bounded early stop."""

from __future__ import annotations

import argparse
import ast
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine, predictive_control  # noqa: E402
from labs.ego_life_playground_v0.controller import PlaygroundController  # noqa: E402
from labs.ego_life_playground_v0.store import SQLiteEventStore  # noqa: E402


TASK_ID = "EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-001A"
CLAIM_CEILING = (
    "Replayable product prediction/update and bounded adaptation evidence within "
    "the declared 16-life contexts only."
)
NEW_CONTEXTS = tuple(
    (layout, world_seed, policy_seed)
    for layout, worlds in (
        ("p0_cross_v1", (52, 53)),
        ("p2_vertical_v1", (54, 55)),
        ("p2_offset_v1", (56, 57)),
    )
    for world_seed in worlds
    for policy_seed in (711, 712)
)
OLD_CONTEXTS = tuple(
    (layout, world_seed, policy_seed)
    for layout, worlds in (
        ("p0_cross_v1", (30, 31)),
        ("p2_vertical_v1", (42, 43)),
        ("p2_offset_v1", (44, 45)),
    )
    for world_seed in worlds
    for policy_seed in (701, 702)
)
CONFIGS = {
    "factored_mpc": dict(
        engine.DEFAULT_INTERVENTIONS,
        predictive_control_mode="factored_mpc",
    ),
    "heuristic_off": dict(engine.DEFAULT_INTERVENTIONS),
    "expected_sarsa": dict(
        engine.DEFAULT_INTERVENTIONS,
        survival_learning_mode="expected_sarsa_lambda",
    ),
}


def _canonical_json(value: Any) -> str:
    return engine.canonical_json(value)


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, int(len(ordered) * 0.95) - 1)]


def _context_id(layout: str, world_seed: int, policy_seed: int) -> str:
    return f"{layout}:world={world_seed}:policy={policy_seed}"


def _life_means(rows: list[dict[str, Any]], field: str) -> tuple[float | None, float | None]:
    by_life: dict[int, list[float]] = {}
    for row in rows:
        value = row.get(field)
        if value is None:
            continue
        by_life.setdefault(int(row["life_index"]), []).append(float(value))
    early_values = [value for life in range(1, 5) for value in by_life.get(life, [])]
    late_values = [value for life in range(13, 17) for value in by_life.get(life, [])]
    return (
        None if not early_values else sum(early_values) / len(early_values),
        None if not late_values else sum(late_values) / len(late_values),
    )


def _fresh_replay(db_path: Path, run_id: str) -> dict[str, Any]:
    with SQLiteEventStore(db_path) as store:
        recovered = store.recover_run(run_id)
    return {
        "sequence": recovered.last_committed_sequence,
        "state_hash": engine.canonical_hash(recovered.state),
        "trace_chain_hash": engine.canonical_hash(recovered.traces),
        "verification_mode": recovered.verification_mode,
    }


def _fresh_replay_subprocess(db_path: Path, run_id: str) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--fresh-replay",
            str(db_path),
            "--run-id",
            run_id,
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _run_context(spec: Mapping[str, Any]) -> dict[str, Any]:
    config_id = str(spec["config_id"])
    layout = str(spec["layout"])
    world_seed = int(spec["world_seed"])
    policy_seed = int(spec["policy_seed"])
    context_id = _context_id(layout, world_seed, policy_seed)
    run_id = f"{TASK_ID}:{config_id}:{context_id}"
    interventions = deepcopy(CONFIGS[config_id])
    with tempfile.TemporaryDirectory(prefix="ego-v2-fpc-") as raw_temp:
        temp = Path(raw_temp)
        database = temp / "run.sqlite3"
        snapshot = temp / "sequence-355.sqlite3"
        durations: list[float] = []
        rows: list[dict[str, Any]] = []
        snapshot_metrics: dict[str, Any] | None = None
        with SQLiteEventStore(database) as store:
            controller = PlaygroundController(
                store,
                run_id=run_id,
                seed=policy_seed,
                world_seed=world_seed,
                layout_id=layout,
            )
            while controller.state["lifecycle"]["trial_status"] != "terminal":
                started = time.perf_counter()
                dispatched = controller.dispatch(
                    interventions,
                    trigger_source="ui_run_button",
                )
                elapsed = time.perf_counter() - started
                if not dispatched.receipt.committed:
                    raise RuntimeError(dispatched.receipt.error)
                trace = controller.last_trace
                if controller.state["lifecycle"]["trial_status"] != "terminal":
                    durations.append(elapsed)
                predictive_trace = trace.get("predictive_control") or {}
                update = predictive_trace.get("update") or {}
                rows.append(
                    {
                        "life_index": int(trace["lifecycle_after"]["life_index"]),
                        "sequence": int(trace["sequence"]),
                        "selected_action": trace.get("selected_action"),
                        "resource_interaction": float(trace.get("food_gain") or 0.0) > 0.0,
                        "outcome_brier": update.get("outcome_brier"),
                        "outcome_nll": update.get("outcome_nll"),
                        "trace_bytes": len(_canonical_json(trace).encode("utf-8")),
                        "row_readback_verified": dispatched.receipt.row_readback_verified,
                    }
                )
                sequence = int(controller.state["clock"]["global_tick"])
                if sequence == 355 and not snapshot.exists():
                    shutil.copy2(database, snapshot)
                    through_355 = [row for row in rows if int(row["sequence"]) <= 355]
                    online_at_355 = {
                        "sequence": controller.recovery.last_committed_sequence,
                        "state_hash": engine.canonical_hash(controller.state),
                        "trace_chain_hash": engine.canonical_hash(
                            controller.recovery.traces
                        ),
                        "verification_mode": "full_replay",
                    }
                    replay_started = time.perf_counter()
                    replay_at_355 = _fresh_replay(snapshot, run_id)
                    recovery_seconds = time.perf_counter() - replay_started
                    fresh = (
                        _fresh_replay_subprocess(snapshot, run_id)
                        if bool(spec.get("fresh_process"))
                        else None
                    )
                    first = statistics.median(durations[:32])
                    last = statistics.median(durations[-32:])
                    snapshot_metrics = {
                        "producer_function": (
                            "verify_ego_v2_factored_predictive_control_001a._run_context"
                        ),
                        "aggregation_rule": "first_355_committed_controller_commands",
                        "command_count": 355,
                        "dispatch_p95_seconds": _p95(durations),
                        "dispatch_max_seconds": max(durations),
                        "first_32_median_seconds": first,
                        "last_32_median_seconds": last,
                        "last_first_ratio": last / first,
                        "recovery_seconds": recovery_seconds,
                        "trace_mean_bytes": sum(row["trace_bytes"] for row in through_355)
                        / len(through_355),
                        "trace_max_bytes": max(row["trace_bytes"] for row in through_355),
                        "sqlite_bytes": snapshot.stat().st_size,
                        "state_replay_exact": replay_at_355 == online_at_355,
                        "fresh_process": fresh,
                        "fresh_process_exact": fresh is None or fresh == replay_at_355,
                        "database_sha256": _hash_file(snapshot),
                    }
            state = deepcopy(controller.state)
            recovery = controller.recovery
            final_db = {
                "logical_id": f"{config_id}:{context_id}:terminal.sqlite3",
                "sha256": _hash_file(database),
                "bytes": database.stat().st_size,
            }
        life_survival = [
            int(item["survival_ticks"])
            for item in state["lifecycle"]["life_results"]
        ]
        early_brier, late_brier = _life_means(rows, "outcome_brier")
        early_nll, late_nll = _life_means(rows, "outcome_nll")
        resource_by_life = {
            life: sum(
                1
                for row in rows
                if int(row["life_index"]) == life and row["resource_interaction"]
            )
            for life in range(1, 17)
        }
        return {
            "producer_function": (
                "verify_ego_v2_factored_predictive_control_001a._run_context -> "
                "PlaygroundController.dispatch -> engine.compute_step"
            ),
            "input_artifacts": [final_db],
            "run_id": run_id,
            "seed": policy_seed,
            "world_seed": world_seed,
            "context_id": context_id,
            "config_id": config_id,
            "aggregation_rule": "complete_16_life_controller_run_no_operator_injection",
            "code_path_hash": engine.compute_code_path_hash(),
            "command_count": recovery.command_count,
            "trial_status": state["lifecycle"]["trial_status"],
            "life_survival": life_survival,
            "early_survival": sum(life_survival[:4]) / (4.0 * 256.0),
            "late_survival": sum(life_survival[12:16]) / (4.0 * 256.0),
            "early_resource_interactions": sum(resource_by_life[life] for life in range(1, 5)),
            "late_resource_interactions": sum(resource_by_life[life] for life in range(13, 17)),
            "early_brier": early_brier,
            "late_brier": late_brier,
            "early_nll": early_nll,
            "late_nll": late_nll,
            "model_update_count": int(state["predictive_control"]["model"]["update_count"]),
            "verification_mode": recovery.verification_mode,
            "last_full_replay_sequence": recovery.last_full_replay_sequence,
            "all_row_readbacks_verified": all(row["row_readback_verified"] for row in rows),
            "snapshot_355": snapshot_metrics,
        }


def _run_old_context_regression(context: tuple[str, int, int]) -> dict[str, Any]:
    layout, world_seed, policy_seed = context
    context_id = _context_id(layout, world_seed, policy_seed)
    run_id = f"{TASK_ID}:old-regression:{context_id}"
    with tempfile.TemporaryDirectory(prefix="ego-v2-fpc-regression-") as raw_temp:
        with SQLiteEventStore(Path(raw_temp) / "regression.sqlite3") as store:
            controller = PlaygroundController(
                store,
                run_id=run_id,
                seed=policy_seed,
                world_seed=world_seed,
                layout_id=layout,
            )
            actions = []
            for _ in range(8):
                result = controller.dispatch(
                    deepcopy(engine.DEFAULT_INTERVENTIONS),
                    trigger_source="ui_run_button",
                )
                if not result.receipt.committed:
                    raise RuntimeError(result.receipt.error)
                actions.append(controller.last_trace.get("selected_action"))
            recovered = store.recover_run(run_id)
    return {
        "context_id": context_id,
        "command_count": 8,
        "actions": actions,
        "replay_exact": engine.canonical_hash(recovered.state)
        == engine.canonical_hash(controller.state),
    }


def _aggregate(runs: list[dict[str, Any]], config_id: str) -> dict[str, Any]:
    selected = [run for run in runs if run["config_id"] == config_id]
    return {
        "config_id": config_id,
        "run_count": len(selected),
        "early_survival": sum(run["early_survival"] for run in selected) / len(selected),
        "late_survival": sum(run["late_survival"] for run in selected) / len(selected),
        "positive_direction_count": sum(
            run["late_survival"] > run["early_survival"] for run in selected
        ),
        "early_resource_interactions": sum(
            run["early_resource_interactions"] for run in selected
        ),
        "late_resource_interactions": sum(
            run["late_resource_interactions"] for run in selected
        ),
        "early_brier": (
            None
            if any(run["early_brier"] is None for run in selected)
            else sum(run["early_brier"] for run in selected) / len(selected)
        ),
        "late_brier": (
            None
            if any(run["late_brier"] is None for run in selected)
            else sum(run["late_brier"] for run in selected) / len(selected)
        ),
        "early_nll": (
            None
            if any(run["early_nll"] is None for run in selected)
            else sum(run["early_nll"] for run in selected) / len(selected)
        ),
        "late_nll": (
            None
            if any(run["late_nll"] is None for run in selected)
            else sum(run["late_nll"] for run in selected) / len(selected)
        ),
    }


def _leakage_report() -> dict[str, Any]:
    observation = {
        "schema_version": "ego.life_playground.microworld.observation.v4",
        "visual": [["occluded"] * 5 for _ in range(5)],
    }
    observation["visual"][2][2] = "self"
    payload = {
        "observation": observation,
        "organism": {
            "energy": 0.45,
            "safety": 0.62,
            "connection": 0.5,
            "stimulation": 0.43,
        },
        "belief_summary": {
            "relative_pose": [0, 0],
            "relative_facing": "N",
            "known_cell_count": 0,
            "known_object_count": 0,
            "front_token": "occluded",
            "token_counts": {f"v{index}": 0 for index in range(5)},
        },
    }
    predictive_control.validate_predictor_input(payload)
    controls = {}
    for field in ("global_position", "objects_by_cause", "cause", "token_mapping", "future_observation", "life_id", "seed_id"):
        contaminated = deepcopy(payload)
        contaminated[field] = "positive-control"
        try:
            predictive_control.validate_predictor_input(contaminated)
        except predictive_control.PredictiveControlInvariantError as exc:
            controls[field] = {"rejected": True, "exception_type": type(exc).__name__}
        else:
            controls[field] = {"rejected": False, "exception_type": None}
    return {
        "producer_function": (
            "ego_life_playground_v0.predictive_control.validate_predictor_input"
        ),
        "input_artifacts": ["constructed_policy_visible_input", "positive_controls"],
        "run_id": f"{TASK_ID}:leakage-scan",
        "seed": 0,
        "context_ids": sorted(controls),
        "aggregation_rule": "valid_input_passes_and_every_forbidden_field_positive_control_rejects",
        "code_path_hash": engine.compute_code_path_hash(),
        "valid_input_accepted": True,
        "positive_controls": controls,
        "all_positive_controls_rejected": all(item["rejected"] for item in controls.values()),
    }


def _goal_counterfactual_report() -> dict[str, Any]:
    observation = {
        "schema_version": "ego.life_playground.microworld.observation.v4",
        "visual": [["occluded"] * 5 for _ in range(5)],
    }
    observation["visual"][2][2] = "self"
    observation["visual"][1][2] = "v3"
    organism = {
        "energy": 0.2,
        "safety": 0.62,
        "connection": 0.5,
        "stimulation": 0.2,
    }
    state, _ = predictive_control.observe_belief(
        predictive_control.empty_state(),
        observation=observation,
        episode_index=0,
        mode="relative",
    )
    for _ in range(8):
        for action, outcome, delta, resource in (
            (
                "interact",
                "interacted",
                {"energy": 0.25, "safety": 0.0, "connection": 0.0, "stimulation": 0.01},
                True,
            ),
            (
                "turn_left",
                "turned",
                {"energy": -0.014, "safety": 0.0, "connection": 0.0, "stimulation": 0.16},
                False,
            ),
        ):
            state, _ = predictive_control.update_after_transition(
                state,
                observation=observation,
                organism_before=organism,
                action=action,
                actual_outcome_type=outcome,
                actual_delta=delta,
                terminal=False,
                resource_interaction=resource,
                next_observation=observation,
                episode_index=0,
                relative_map_mode="relative",
                updates_enabled=True,
            )
    common = {
        "state": state,
        "observation": observation,
        "organism": organism,
        "heuristic_scores": {action: 0.0 for action in engine.ACTIONS},
        "horizon": 1,
        "beam_width": predictive_control.BEAM_WIDTH,
        "discount": predictive_control.DISCOUNT,
        "relative_map_mode": "relative",
        "goal_value_mode": "contextual",
        "action_costs": engine.ACTION_COSTS,
    }
    energy = predictive_control.plan_action(**common, active_goal="energy")
    stimulation = predictive_control.plan_action(**common, active_goal="stimulation")
    return {
        "producer_function": "ego_life_playground_v0.predictive_control.plan_action",
        "input_artifacts": ["constructed_visible_training_history"],
        "run_id": f"{TASK_ID}:goal-counterfactual",
        "seed": 0,
        "context_ids": ["goal=energy", "goal=stimulation"],
        "aggregation_rule": "same_predictor_state_and_action_predictions_under_goal_intervention",
        "code_path_hash": engine.compute_code_path_hash(),
        "prediction_bytes_equal": _canonical_json(energy["predictions_by_action"])
        == _canonical_json(stimulation["predictions_by_action"]),
        "candidate_values_differ": energy["candidate_values"]
        != stimulation["candidate_values"],
        "ranking_changes": energy["selected_action"] != stimulation["selected_action"],
        "energy_selected_action": energy["selected_action"],
        "stimulation_selected_action": stimulation["selected_action"],
    }


def _single_path_source_scan() -> dict[str, Any]:
    package = REPO_ROOT / "labs" / "ego_life_playground_v0"
    trees = {
        path.name: ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for path in package.glob("*.py")
    }
    compute_definitions = sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "compute_step"
        for tree in trees.values()
        for node in ast.walk(tree)
    )
    plan_callers = []
    transition_callers = []
    for filename, tree in trees.items():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and node.func.attr == "plan_action":
                plan_callers.append(filename)
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "transition_world"
            ):
                transition_callers.append(filename)
    value = (
        compute_definitions == 1
        and plan_callers == ["engine.py"]
        and set(transition_callers) == {"engine.py"}
    )
    return {
        "producer_function": (
            "verify_ego_v2_factored_predictive_control_001a._single_path_source_scan"
        ),
        "input_artifacts": [str(package)],
        "run_id": f"{TASK_ID}:single-path-scan",
        "seed": 0,
        "context_ids": sorted(trees),
        "aggregation_rule": "one_compute_step_and_predictive_plan_only_called_from_engine",
        "code_path_hash": engine.compute_code_path_hash(),
        "compute_step_definitions": compute_definitions,
        "plan_callers": plan_callers,
        "transition_world_callers": transition_callers,
        "value": value,
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(_canonical_json(value) + "\n", encoding="utf-8")


def refresh_isolated_performance(output_dir: Path) -> dict[str, Any]:
    """Replace contention-biased timing with one isolated callable rerun."""

    layout, world_seed, policy_seed = NEW_CONTEXTS[0]
    isolated_run = _run_context(
        {
            "config_id": "factored_mpc",
            "layout": layout,
            "world_seed": world_seed,
            "policy_seed": policy_seed,
            "fresh_process": True,
        }
    )
    performance = isolated_run["snapshot_355"]
    if performance is None:
        raise RuntimeError("isolated run did not reach sequence 355")
    result_path = output_dir / "result.json"
    replay_path = output_dir / "replay_report.json"
    failure_path = output_dir / "failure_manifest.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    replacements = {
        "fresh_process_replay_exact": bool(performance["fresh_process_exact"]),
        "dispatch_p95_lte_250ms": performance["dispatch_p95_seconds"] <= 0.250,
        "dispatch_max_lte_500ms": performance["dispatch_max_seconds"] <= 0.500,
        "last_first_ratio_lt_2": performance["last_first_ratio"] < 2.0,
        "recovery_lte_10s": performance["recovery_seconds"] <= 10.0,
        "trace_mean_lte_32kib": performance["trace_mean_bytes"] <= 32 * 1024,
        "trace_max_lte_64kib": performance["trace_max_bytes"] <= 64 * 1024,
        "sqlite_lte_20mib": performance["sqlite_bytes"] <= 20 * 1024 * 1024,
    }
    result["checks"].update(replacements)
    result["performance"] = performance
    result["failed_checks"] = sorted(
        name for name, passed in result["checks"].items() if not passed
    )
    replay["performance_and_replay"] = performance
    replay["isolated_timing_rerun"] = {
        "producer_function": (
            "verify_ego_v2_factored_predictive_control_001a."
            "refresh_isolated_performance"
        ),
        "run_id": isolated_run["run_id"],
        "context_id": isolated_run["context_id"],
        "aggregation_rule": "single_process_no_parallel_contention",
        "input_artifacts": isolated_run["input_artifacts"],
        "code_path_hash": engine.compute_code_path_hash(),
    }
    failure["failed_checks"] = result["failed_checks"]
    failure["isolated_performance_refresh"] = True
    _write_json(result_path, result)
    _write_json(replay_path, replay)
    _write_json(failure_path, failure)
    return result


def refresh_static_checks(output_dir: Path) -> dict[str, Any]:
    """Add callable separation and single-path checks without rerunning episodes."""

    result_path = output_dir / "result.json"
    leakage_path = output_dir / "leakage_report.json"
    failure_path = output_dir / "failure_manifest.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    leakage = json.loads(leakage_path.read_text(encoding="utf-8"))
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    counterfactual = _goal_counterfactual_report()
    source_scan = _single_path_source_scan()
    result["checks"].update(
        {
            "goal_counterfactual_prediction_equal": counterfactual[
                "prediction_bytes_equal"
            ],
            "goal_counterfactual_value_and_ranking_change": counterfactual[
                "candidate_values_differ"
            ]
            and counterfactual["ranking_changes"],
            "single_reducer_source_scan": source_scan["value"],
        }
    )
    result["failed_checks"] = sorted(
        name for name, passed in result["checks"].items() if not passed
    )
    leakage["goal_counterfactual"] = counterfactual
    leakage["single_path_source_scan"] = source_scan
    failure["failed_checks"] = result["failed_checks"]
    failure["static_checks_refreshed"] = True
    _write_json(result_path, result)
    _write_json(leakage_path, leakage)
    _write_json(failure_path, failure)
    return result


def verify(output_dir: Path, *, max_workers: int | None = None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    specs = []
    for config_id in CONFIGS:
        for layout, world_seed, policy_seed in NEW_CONTEXTS:
            specs.append(
                {
                    "config_id": config_id,
                    "layout": layout,
                    "world_seed": world_seed,
                    "policy_seed": policy_seed,
                    "fresh_process": False,
                }
            )
    workers = max_workers or min(12, max(1, os.cpu_count() or 1))
    runs: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_run_context, spec) for spec in specs]
        for future in as_completed(futures):
            runs.append(future.result())
    runs.sort(key=lambda item: (item["config_id"], item["context_id"]))
    isolated_performance_run = _run_context(
        {
            "config_id": "factored_mpc",
            "layout": NEW_CONTEXTS[0][0],
            "world_seed": NEW_CONTEXTS[0][1],
            "policy_seed": NEW_CONTEXTS[0][2],
            "fresh_process": True,
        }
    )
    old_regression = [_run_old_context_regression(context) for context in OLD_CONTEXTS]
    aggregate = {config_id: _aggregate(runs, config_id) for config_id in CONFIGS}
    candidate = aggregate["factored_mpc"]
    heuristic = aggregate["heuristic_off"]
    sarsa = aggregate["expected_sarsa"]
    performance = isolated_performance_run["snapshot_355"]
    if performance is None:
        raise RuntimeError("isolated performance run did not reach sequence 355")
    checks = {
        "late_minus_early_gt_005": candidate["late_survival"] - candidate["early_survival"] > 0.05,
        "positive_direction_at_least_9_of_12": candidate["positive_direction_count"] >= 9,
        "late_beats_heuristic_by_005": candidate["late_survival"] - heuristic["late_survival"] > 0.05,
        "late_beats_sarsa_by_005": candidate["late_survival"] - sarsa["late_survival"] > 0.05,
        "late_above_38_tick_bound": candidate["late_survival"] > 38.0 / 256.0,
        "late_resources_exceed_early": candidate["late_resource_interactions"] > candidate["early_resource_interactions"],
        "brier_improves": candidate["late_brier"] is not None and candidate["late_brier"] < candidate["early_brier"],
        "nll_improves": candidate["late_nll"] is not None and candidate["late_nll"] < candidate["early_nll"],
        "all_new_contexts_consumed": {run["context_id"] for run in runs if run["config_id"] == "factored_mpc"}
        == {_context_id(*context) for context in NEW_CONTEXTS},
        "all_old_contexts_regressed": len(old_regression) == 12 and all(item["replay_exact"] for item in old_regression),
        "all_terminal_full_replay": all(
            run["trial_status"] == "terminal"
            and len(run["life_survival"]) == 16
            and run["verification_mode"] == "full_replay"
            and run["last_full_replay_sequence"] == run["command_count"]
            for run in runs
        ),
        "all_row_readbacks_verified": all(run["all_row_readbacks_verified"] for run in runs),
        "fresh_process_replay_exact": bool(performance["fresh_process_exact"]),
        "dispatch_p95_lte_250ms": performance["dispatch_p95_seconds"] <= 0.250,
        "dispatch_max_lte_500ms": performance["dispatch_max_seconds"] <= 0.500,
        "last_first_ratio_lt_2": performance["last_first_ratio"] < 2.0,
        "recovery_lte_10s": performance["recovery_seconds"] <= 10.0,
        "trace_mean_lte_32kib": performance["trace_mean_bytes"] <= 32 * 1024,
        "trace_max_lte_64kib": performance["trace_max_bytes"] <= 64 * 1024,
        "sqlite_lte_20mib": performance["sqlite_bytes"] <= 20 * 1024 * 1024,
    }
    leakage = _leakage_report()
    checks["leakage_positive_controls"] = leakage["all_positive_controls_rejected"]
    primary_failures = [
        name
        for name in (
            "late_minus_early_gt_005",
            "positive_direction_at_least_9_of_12",
            "late_above_38_tick_bound",
            "late_resources_exceed_early",
        )
        if not checks[name]
    ]
    verdict = (
        "PRODUCT_PREDICTIVE_CONTROL_NOT_OBSERVED"
        if primary_failures
        else "BLOCKED_INCOMPLETE_EFFECT_CONTROLS"
    )
    skipped_controls = [
        "predictor_no_update",
        "horizon_1",
        "no_relative_map",
        "goal_context_equal",
        "empirical_lookup",
        "rest_only",
        "uniform_random",
        "shield_only",
    ]
    baseline_comparison = {
        "producer_function": "verify_ego_v2_factored_predictive_control_001a._aggregate",
        "input_artifacts": [item for run in runs for item in run["input_artifacts"]],
        "run_id": f"{TASK_ID}:new-context-baselines",
        "seed": [711, 712],
        "context_ids": sorted({_context_id(*context) for context in NEW_CONTEXTS}),
        "aggregation_rule": "mean_lives_1_4_and_13_16_over_12_contexts_divided_by_256",
        "code_path_hash": engine.compute_code_path_hash(),
        "configs": aggregate,
    }
    ablation_report = {
        "producer_function": "verify_ego_v2_factored_predictive_control_001a.verify",
        "input_artifacts": ["primary_candidate_and_baseline_results"],
        "run_id": f"{TASK_ID}:bounded-early-stop",
        "seed": [711, 712],
        "context_ids": sorted({_context_id(*context) for context in NEW_CONTEXTS}),
        "aggregation_rule": "stop_remaining_effect_controls_after_predeclared_primary_candidate_failure",
        "code_path_hash": engine.compute_code_path_hash(),
        "status": "not_run_primary_candidate_failed",
        "primary_failures": primary_failures,
        "skipped_controls": skipped_controls,
        "callable_modes_present": {
            "predictor_no_update": "update_mode=frozen",
            "horizon_1": "predictive_horizon_mode=h1",
            "no_relative_map": "relative_map_mode=off",
            "goal_context_equal": "goal_value_mode=equal",
        },
    }
    replay_report = {
        "producer_function": "SQLiteEventStore.recover_run",
        "input_artifacts": [performance["database_sha256"]],
        "run_id": f"{TASK_ID}:factored_mpc:first-context:sequence-355",
        "seed": 711,
        "context_ids": [_context_id(*NEW_CONTEXTS[0])],
        "aggregation_rule": "initial_state_plus_355_commands_parent_and_fresh_process_exact",
        "code_path_hash": engine.compute_code_path_hash(),
        "performance_and_replay": performance,
        "isolated_timing_rerun": {
            "producer_function": (
                "verify_ego_v2_factored_predictive_control_001a._run_context"
            ),
            "run_id": isolated_performance_run["run_id"],
            "context_id": isolated_performance_run["context_id"],
            "aggregation_rule": "single_process_no_parallel_contention",
            "input_artifacts": isolated_performance_run["input_artifacts"],
            "code_path_hash": engine.compute_code_path_hash(),
        },
        "all_terminal_runs_full_replay": checks["all_terminal_full_replay"],
        "old_context_regression": old_regression,
    }
    failures = sorted(name for name, passed in checks.items() if not passed)
    failure_manifest = {
        "producer_function": "verify_ego_v2_factored_predictive_control_001a.verify",
        "input_artifacts": ["result.json", "baseline_comparison.json", "replay_report.json"],
        "run_id": f"{TASK_ID}:failure-manifest",
        "seed": [711, 712],
        "context_ids": sorted({_context_id(*context) for context in NEW_CONTEXTS}),
        "aggregation_rule": "preserve_every_failed_or_unexecuted_declared_gate",
        "code_path_hash": engine.compute_code_path_hash(),
        "verdict": verdict,
        "failed_checks": failures,
        "primary_failures": primary_failures,
        "unexecuted_controls": skipped_controls,
        "default_mode_remains_off": True,
    }
    result = {
        "schema_version": "ego.v2.factored_predictive_control.result.v1",
        "task_id": TASK_ID,
        "producer_function": "verify_ego_v2_factored_predictive_control_001a.verify",
        "input_artifacts": [
            {
                "path": "labs/ego_life_playground_v0/predictive_control.py",
                "sha256": _hash_file(REPO_ROOT / "labs/ego_life_playground_v0/predictive_control.py"),
            }
        ],
        "run_id": f"{TASK_ID}:acceptance",
        "seed": [711, 712],
        "context_ids": sorted({_context_id(*context) for context in NEW_CONTEXTS}),
        "aggregation_rule": "declared_effect_checks_with_primary_failure_early_stop",
        "code_path_hash": engine.compute_code_path_hash(),
        "verdict": verdict,
        "checks": checks,
        "failed_checks": failures,
        "primary_failures": primary_failures,
        "performance": performance,
        "claim_ceiling": CLAIM_CEILING,
        "default_predictive_control_mode": engine.DEFAULT_INTERVENTIONS["predictive_control_mode"],
    }
    _write_json(output_dir / "result.json", result)
    _write_json(output_dir / "baseline_comparison.json", baseline_comparison)
    _write_json(output_dir / "ablation_report.json", ablation_report)
    _write_json(output_dir / "leakage_report.json", leakage)
    _write_json(output_dir / "replay_report.json", replay_report)
    _write_json(output_dir / "failure_manifest.json", failure_manifest)
    with (output_dir / "trace.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for run in runs:
            handle.write(_canonical_json(run) + "\n")
    (output_dir / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "artifacts" / TASK_ID)
    parser.add_argument("--max-workers", type=int)
    parser.add_argument("--fresh-replay", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--refresh-isolated-performance", action="store_true")
    parser.add_argument("--refresh-static-checks", action="store_true")
    args = parser.parse_args(argv)
    if args.fresh_replay is not None:
        if not args.run_id:
            raise SystemExit("--run-id is required with --fresh-replay")
        print(_canonical_json(_fresh_replay(args.fresh_replay, args.run_id)))
        return 0
    if args.refresh_isolated_performance:
        result = refresh_isolated_performance(args.output_dir.resolve())
        print(
            json.dumps(
                {
                    "verdict": result["verdict"],
                    "failed_checks": result["failed_checks"],
                    "result": str((args.output_dir / "result.json").resolve()),
                },
                sort_keys=True,
            )
        )
        return 0
    if args.refresh_static_checks:
        result = refresh_static_checks(args.output_dir.resolve())
        print(
            json.dumps(
                {
                    "verdict": result["verdict"],
                    "failed_checks": result["failed_checks"],
                    "result": str((args.output_dir / "result.json").resolve()),
                },
                sort_keys=True,
            )
        )
        return 0
    result = verify(args.output_dir.resolve(), max_workers=args.max_workers)
    print(
        json.dumps(
            {
                "verdict": result["verdict"],
                "failed_checks": result["failed_checks"],
                "result": str((args.output_dir / "result.json").resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
