#!/usr/bin/env python3
"""Callable staged verifier for the 001B factored-control repair.

The smoke gate consumes only the already-used development contexts.  Fresh
effect contexts are deliberately absent from this stage and are not reachable
through ``--smoke``.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
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


TASK_ID = "EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-REPAIR-001B"
SMOKE_CONTEXTS = (
    ("p0_cross_v1", 52, 711),
    ("p2_vertical_v1", 54, 711),
)
CLAIM_CEILING = (
    "Replayable engineering evidence for the repaired factored-control path in "
    "the declared bounded contexts only."
)


def _canonical_json(value: Any) -> str:
    return engine.canonical_json(value)


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, int(len(ordered) * 0.95) - 1)]


def _context_id(layout: str, world_seed: int, policy_seed: int) -> str:
    return f"{layout}:world={world_seed}:policy={policy_seed}"


def _policy_observation_from_trace(trace: Mapping[str, Any]) -> Mapping[str, Any]:
    return (trace.get("policy_projection") or {}).get("observation") or {}


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


def _tamper_rejected(db_path: Path, run_id: str) -> dict[str, Any]:
    tampered_path = db_path.with_name("tampered.sqlite3")
    shutil.copy2(db_path, tampered_path)
    with sqlite3.connect(tampered_path) as connection:
        row = connection.execute(
            "SELECT trace_json FROM traces WHERE run_id = ? AND sequence = 4",
            (run_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("smoke tamper positive control lacks sequence 4")
        trace = json.loads(row[0])
        update = trace["predictive_control"]["update"]
        update["outcome_brier"] = 999.0
        trace["trace_hash"] = engine.compute_trace_hash(trace)
        connection.execute(
            "UPDATE traces SET trace_json = ?, trace_hash = ? "
            "WHERE run_id = ? AND sequence = 4",
            (_canonical_json(trace), trace["trace_hash"], run_id),
        )
        connection.commit()
    error_type = None
    error_message = None
    rejected = False
    try:
        _fresh_replay(tampered_path, run_id)
    except Exception as exc:  # exact engine/store exception is recorded below
        rejected = True
        error_type = type(exc).__name__
        error_message = str(exc)
    return {
        "producer_function": (
            "verify_ego_v2_factored_predictive_control_repair_001b._tamper_rejected"
        ),
        "input_artifacts": [_hash_file(tampered_path)],
        "aggregation_rule": "rehash_tampered_predictive_update_then_recover",
        "rejected": rejected,
        "exception_type": error_type,
        "exception_message": error_message,
    }


def _run_smoke_context(
    layout: str, world_seed: int, policy_seed: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    context_id = _context_id(layout, world_seed, policy_seed)
    run_id = f"{TASK_ID}:smoke:{context_id}"
    interventions = dict(
        engine.DEFAULT_INTERVENTIONS,
        predictive_control_mode="factored_mpc",
    )
    with tempfile.TemporaryDirectory(
        prefix="ego-v2-fpc-repair-smoke-", ignore_cleanup_errors=True
    ) as raw_temp:
        db_path = Path(raw_temp) / "smoke.sqlite3"
        durations: list[float] = []
        rows: list[dict[str, Any]] = []
        action_counts: Counter[str] = Counter()
        successful_resource_interactions = 0
        learned_resource_front_events = 0
        learned_resource_front_turns = 0
        consecutive_learned_front_turns = 0
        maximum_consecutive_learned_front_turns = 0
        with SQLiteEventStore(db_path) as store:
            controller = PlaygroundController(
                store,
                run_id=run_id,
                seed=policy_seed,
                world_seed=world_seed,
                layout_id=layout,
            )
            resource_token = str(
                controller.state["world"]["objects_by_cause"]["resource"]["token"]
            )
            while len(controller.state["lifecycle"]["life_results"]) < 4:
                started = time.perf_counter()
                dispatched = controller.dispatch(
                    interventions,
                    trigger_source="ui_run_button",
                )
                duration = time.perf_counter() - started
                if not dispatched.receipt.committed:
                    raise RuntimeError(dispatched.receipt.error)
                trace = controller.last_trace
                durations.append(duration)
                action = trace.get("selected_action")
                plan = ((trace.get("predictive_control") or {}).get("plan") or {})
                update = ((trace.get("predictive_control") or {}).get("update") or {})
                observation = _policy_observation_from_trace(trace)
                visual = observation.get("visual") or []
                front_token = visual[1][2] if len(visual) == 5 else None
                token_count = int(
                    (plan.get("token_interaction_counts") or {}).get(resource_token, 0)
                )
                learned_resource_front = (
                    action is not None
                    and front_token == resource_token
                    and token_count >= predictive_control.TOKEN_INTERACTION_TARGET
                )
                if action is not None:
                    action_counts[str(action)] += 1
                    if float(trace.get("food_gain") or 0.0) > 0.0:
                        successful_resource_interactions += 1
                    if learned_resource_front:
                        learned_resource_front_events += 1
                        if action in {"turn_left", "turn_right"}:
                            learned_resource_front_turns += 1
                            consecutive_learned_front_turns += 1
                        else:
                            consecutive_learned_front_turns = 0
                    else:
                        consecutive_learned_front_turns = 0
                    maximum_consecutive_learned_front_turns = max(
                        maximum_consecutive_learned_front_turns,
                        consecutive_learned_front_turns,
                    )
                rows.append(
                    {
                        "producer_function": (
                            "PlaygroundController.dispatch->engine.compute_step"
                        ),
                        "input_artifacts": [
                            f"command:{trace.get('command_hash')}",
                            f"trace:{trace.get('trace_hash')}",
                        ],
                        "run_id": run_id,
                        "seed": policy_seed,
                        "context_id": context_id,
                        "episode_id": trace.get("episode_id"),
                        "sequence": trace.get("sequence"),
                        "aggregation_rule": "one_committed_smoke_command",
                        "code_path_hash": trace.get("code_path_hash"),
                        "selected_action": action,
                        "selection_mode": plan.get("selection_mode"),
                        "exploration_reason": plan.get("exploration_reason"),
                        "front_token": front_token,
                        "resource_front_evaluator_only": front_token == resource_token,
                        "resource_token_learned": token_count >= 2,
                        "successful_resource_interaction": (
                            float(trace.get("food_gain") or 0.0) > 0.0
                        ),
                        "outcome_brier": update.get("outcome_brier"),
                        "outcome_nll": update.get("outcome_nll"),
                        "dispatch_seconds": duration,
                        "trace_bytes": len(_canonical_json(trace).encode("utf-8")),
                        "row_readback_verified": (
                            dispatched.receipt.row_readback_verified
                        ),
                    }
                )
            online = {
                "sequence": controller.recovery.last_committed_sequence,
                "state_hash": engine.canonical_hash(controller.state),
                "trace_chain_hash": engine.canonical_hash(controller.recovery.traces),
                "verification_mode": "full_replay",
            }
            life_survival = [
                int(item["survival_ticks"])
                for item in controller.state["lifecycle"]["life_results"]
            ]
            row_readbacks = all(row["row_readback_verified"] for row in rows)
            db_hash = _hash_file(db_path)
            db_bytes = db_path.stat().st_size
            replay_started = time.perf_counter()
            replay = _fresh_replay(db_path, run_id)
            recovery_seconds = time.perf_counter() - replay_started
            fresh = _fresh_replay_subprocess(db_path, run_id)
        tamper = _tamper_rejected(db_path, run_id)
        action_total = sum(action_counts.values())
        result = {
            "producer_function": (
                "verify_ego_v2_factored_predictive_control_repair_001b._run_smoke_context"
            ),
            "input_artifacts": [f"sqlite:{db_hash}"],
            "run_id": run_id,
            "seed": policy_seed,
            "world_seed": world_seed,
            "context_id": context_id,
            "aggregation_rule": "first_four_completed_lives_no_operator_injection",
            "code_path_hash": engine.compute_code_path_hash(),
            "life_survival_ticks": life_survival,
            "action_counts": dict(sorted(action_counts.items())),
            "action_total": action_total,
            "max_action_share": max(action_counts.values()) / action_total,
            "all_five_actions_covered": set(action_counts) == set(engine.ACTIONS),
            "successful_resource_interactions": successful_resource_interactions,
            "learned_resource_front_events": learned_resource_front_events,
            "learned_resource_front_turns": learned_resource_front_turns,
            "maximum_consecutive_learned_resource_front_turns": (
                maximum_consecutive_learned_front_turns
            ),
            "dispatch_p95_seconds": _p95(durations),
            "dispatch_max_seconds": max(durations),
            "trace_mean_bytes": sum(row["trace_bytes"] for row in rows) / len(rows),
            "trace_max_bytes": max(row["trace_bytes"] for row in rows),
            "sqlite_bytes": db_bytes,
            "recovery_seconds": recovery_seconds,
            "row_readbacks_verified": row_readbacks,
            "same_process_replay_exact": replay == online,
            "fresh_process_replay_exact": fresh == replay,
            "tamper_positive_control": tamper,
        }
        return result, rows


def _write_json(path: Path, value: Any) -> None:
    path.write_text(_canonical_json(value) + "\n", encoding="utf-8", newline="\n")


def verify_smoke(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for context in SMOKE_CONTEXTS:
        result, rows = _run_smoke_context(*context)
        results.append(result)
        traces.extend(rows)
    checks = {
        "no_single_action_share_over_0_85": all(
            run["max_action_share"] <= 0.85 for run in results
        ),
        "both_contexts_cover_all_five_actions": all(
            run["all_five_actions_covered"] for run in results
        ),
        "at_least_one_successful_resource_interaction": sum(
            run["successful_resource_interactions"] for run in results
        )
        >= 1,
        "learned_resource_front_does_not_sustain_turning": all(
            run["maximum_consecutive_learned_resource_front_turns"] <= 1
            for run in results
        ),
        "all_row_readbacks_verified": all(
            run["row_readbacks_verified"] for run in results
        ),
        "same_and_fresh_process_replay_exact": all(
            run["same_process_replay_exact"]
            and run["fresh_process_replay_exact"]
            for run in results
        ),
        "rehash_tamper_rejected": all(
            run["tamper_positive_control"]["rejected"] for run in results
        ),
        "dispatch_p95_at_most_250ms": all(
            run["dispatch_p95_seconds"] <= 0.250 for run in results
        ),
        "dispatch_max_at_most_500ms": all(
            run["dispatch_max_seconds"] <= 0.500 for run in results
        ),
        "recovery_at_most_10s": all(
            run["recovery_seconds"] <= 10.0 for run in results
        ),
        "trace_mean_at_most_32kb": all(
            run["trace_mean_bytes"] <= 32 * 1024 for run in results
        ),
        "trace_max_at_most_64kb": all(
            run["trace_max_bytes"] <= 64 * 1024 for run in results
        ),
    }
    failures = sorted(name for name, passed in checks.items() if not passed)
    verdict = "SMOKE_PASSED" if not failures else "REPAIR_FAILED_POLICY_COLLAPSE"
    result = {
        "schema_version": "ego.v2.factored_predictive_control_repair.smoke_result.v1",
        "task_id": TASK_ID,
        "producer_function": (
            "verify_ego_v2_factored_predictive_control_repair_001b.verify_smoke"
        ),
        "input_artifacts": [
            {
                "path": "labs/ego_life_playground_v0/predictive_control.py",
                "sha256": _hash_file(
                    REPO_ROOT / "labs/ego_life_playground_v0/predictive_control.py"
                ),
            }
        ],
        "run_id": f"{TASK_ID}:smoke",
        "seed": [711],
        "context_ids": [_context_id(*context) for context in SMOKE_CONTEXTS],
        "aggregation_rule": "all_predeclared_smoke_checks_over_two_four_life_runs",
        "code_path_hash": engine.compute_code_path_hash(),
        "verdict": verdict,
        "checks": checks,
        "failed_checks": failures,
        "runs": results,
        "fresh_effect_contexts_consumed": False,
        "claim_ceiling": CLAIM_CEILING,
        "default_predictive_control_mode": engine.DEFAULT_INTERVENTIONS[
            "predictive_control_mode"
        ],
    }
    replay = {
        "producer_function": "SQLiteEventStore.recover_run",
        "input_artifacts": [
            item for run in results for item in run["input_artifacts"]
        ],
        "run_id": f"{TASK_ID}:smoke-replay",
        "seed": [711],
        "context_ids": [_context_id(*context) for context in SMOKE_CONTEXTS],
        "aggregation_rule": "same_process_fresh_process_and_rehash_tamper_checks",
        "code_path_hash": engine.compute_code_path_hash(),
        "runs": [
            {
                "context_id": run["context_id"],
                "same_process_replay_exact": run["same_process_replay_exact"],
                "fresh_process_replay_exact": run["fresh_process_replay_exact"],
                "tamper_positive_control": run["tamper_positive_control"],
            }
            for run in results
        ],
    }
    failure_manifest = {
        "producer_function": (
            "verify_ego_v2_factored_predictive_control_repair_001b.verify_smoke"
        ),
        "input_artifacts": ["smoke_result.json", "smoke_replay_report.json"],
        "run_id": f"{TASK_ID}:smoke-failure-manifest",
        "seed": [711],
        "context_ids": [_context_id(*context) for context in SMOKE_CONTEXTS],
        "aggregation_rule": "record_every_failed_smoke_gate",
        "code_path_hash": engine.compute_code_path_hash(),
        "failed_checks": failures,
        "fresh_effect_contexts_blocked": bool(failures),
    }
    _write_json(output_dir / "smoke_result.json", result)
    _write_json(output_dir / "smoke_replay_report.json", replay)
    _write_json(output_dir / "smoke_failure_manifest.json", failure_manifest)
    with (output_dir / "smoke_trace.jsonl").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        for row in traces:
            handle.write(_canonical_json(row) + "\n")
    return result


def finalize_smoke_failure(output_dir: Path) -> dict[str, Any]:
    """Freeze the required negative artifact set without consuming fresh seeds."""

    smoke_result_path = output_dir / "smoke_result.json"
    smoke_trace_path = output_dir / "smoke_trace.jsonl"
    smoke_replay_path = output_dir / "smoke_replay_report.json"
    if not all(path.is_file() for path in (smoke_result_path, smoke_trace_path, smoke_replay_path)):
        raise RuntimeError("smoke artifacts are incomplete")
    smoke = json.loads(smoke_result_path.read_text(encoding="utf-8"))
    if smoke.get("verdict") != "REPAIR_FAILED_POLICY_COLLAPSE":
        raise RuntimeError("smoke failure finalizer requires the frozen failure verdict")
    if smoke.get("fresh_effect_contexts_consumed") is not False:
        raise RuntimeError("fresh effect contexts were unexpectedly consumed")
    code_path_hash = str(smoke["code_path_hash"])
    context_ids = list(smoke["context_ids"])
    input_artifact = {
        "path": "smoke_result.json",
        "sha256": _hash_file(smoke_result_path),
    }
    observation = {
        "schema_version": "ego.life_playground.microworld.observation.v4",
        "visual": [["empty" for _ in range(5)] for _ in range(5)],
    }
    observation["visual"][2][2] = "self"
    organism = {
        "energy": 0.45,
        "safety": 0.62,
        "connection": 0.50,
        "stimulation": 0.43,
    }
    predictor_state = predictive_control.empty_state()
    prepared, _ = predictive_control.observe_belief(
        predictor_state,
        observation=observation,
        episode_index=0,
        mode="relative",
    )
    clean_payload = predictive_control.predictor_input_snapshot(
        prepared,
        observation=observation,
        organism=organism,
        relative_map_mode="relative",
    )
    contaminated = deepcopy(clean_payload)
    positive_fields = {
        "global_position": [4, 3],
        "cause": "resource",
        "token_mapping": {"v3": "resource"},
        "seed": 52,
        "future_observation": observation,
    }
    contaminated.update(positive_fields)
    clean_scan = predictive_control.scan_predictor_input_leakage(clean_payload)
    positive_scan = predictive_control.scan_predictor_input_leakage(contaminated)
    leakage_report = {
        "producer_function": (
            "predictive_control.scan_predictor_input_leakage"
        ),
        "input_artifacts": [
            f"clean:{clean_scan['input_hash']}",
            f"positive_control:{positive_scan['input_hash']}",
        ],
        "run_id": f"{TASK_ID}:leakage-positive-control",
        "seed": [711],
        "context_ids": context_ids,
        "aggregation_rule": "clean_boundary_plus_five_forbidden_field_positive_controls",
        "code_path_hash": code_path_hash,
        "clean_scan": clean_scan,
        "positive_control_scan": positive_scan,
        "positive_control_detected_all_fields": {
            item["field"] for item in positive_scan["findings"]
        }
        == set(positive_fields),
    }
    skipped_controls = [
        "heuristic_off",
        "predictor_no_update",
        "empirical_lookup",
        "shield_only",
        "frozen_expected_sarsa",
        "horizon_1",
        "no_relative_map",
        "equal_goal_context",
        "rest_only",
        "uniform_random",
    ]
    baseline_comparison = {
        "producer_function": (
            "verify_ego_v2_factored_predictive_control_repair_001b.finalize_smoke_failure"
        ),
        "input_artifacts": [input_artifact],
        "run_id": f"{TASK_ID}:baseline-early-stop",
        "seed": [711],
        "context_ids": context_ids,
        "aggregation_rule": "no_baseline_execution_after_predeclared_smoke_stop",
        "code_path_hash": code_path_hash,
        "status": "not_run_smoke_failed",
        "skipped_controls": skipped_controls,
    }
    ablation_report = {
        "producer_function": (
            "verify_ego_v2_factored_predictive_control_repair_001b.finalize_smoke_failure"
        ),
        "input_artifacts": [input_artifact],
        "run_id": f"{TASK_ID}:ablation-early-stop",
        "seed": [711],
        "context_ids": context_ids,
        "aggregation_rule": "no_ablation_execution_after_predeclared_smoke_stop",
        "code_path_hash": code_path_hash,
        "status": "not_run_smoke_failed",
        "skipped_ablations": [
            "predictor_no_update",
            "horizon_1",
            "no_relative_map",
            "equal_goal_context",
        ],
    }
    replay_report = json.loads(smoke_replay_path.read_text(encoding="utf-8"))
    replay_report["source_smoke_report_sha256"] = _hash_file(smoke_replay_path)
    failure_manifest = {
        "producer_function": (
            "verify_ego_v2_factored_predictive_control_repair_001b.finalize_smoke_failure"
        ),
        "input_artifacts": [input_artifact, "smoke_replay_report.json"],
        "run_id": f"{TASK_ID}:failure-manifest",
        "seed": [711],
        "context_ids": context_ids,
        "aggregation_rule": "preserve_failed_smoke_gates_and_unexecuted_fresh_contract",
        "code_path_hash": code_path_hash,
        "verdict": "REPAIR_FAILED_POLICY_COLLAPSE",
        "failed_checks": list(smoke["failed_checks"]),
        "unexecuted_controls": skipped_controls,
        "unexecuted_fresh_contexts": [
            "p0_cross_v1:world=60,61:policy=721,722",
            "p2_vertical_v1:world=62,63:policy=721,722",
            "p2_offset_v1:world=64,65:policy=721,722",
        ],
        "fresh_effect_contexts_consumed": False,
        "default_predictive_control_mode": "off",
    }
    result = {
        **smoke,
        "schema_version": "ego.v2.factored_predictive_control_repair.result.v1",
        "producer_function": (
            "verify_ego_v2_factored_predictive_control_repair_001b.finalize_smoke_failure"
        ),
        "input_artifacts": [input_artifact],
        "run_id": f"{TASK_ID}:bounded-early-stop",
        "aggregation_rule": "freeze_smoke_failure_without_fresh_seed_consumption",
        "stage": "stopped_after_consumed_context_smoke",
        "balanced_prediction_evaluation": "not_run_smoke_failed",
        "baseline_comparison": "not_run_smoke_failed",
        "ablation_report": "not_run_smoke_failed",
    }
    _write_json(output_dir / "result.json", result)
    _write_json(output_dir / "baseline_comparison.json", baseline_comparison)
    _write_json(output_dir / "ablation_report.json", ablation_report)
    _write_json(output_dir / "leakage_report.json", leakage_report)
    _write_json(output_dir / "replay_report.json", replay_report)
    _write_json(output_dir / "failure_manifest.json", failure_manifest)
    (output_dir / "trace.jsonl").write_bytes(smoke_trace_path.read_bytes())
    (output_dir / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "artifacts" / TASK_ID,
    )
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--finalize-smoke-failure", action="store_true")
    parser.add_argument("--fresh-replay", type=Path)
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    if args.fresh_replay is not None:
        if not args.run_id:
            raise SystemExit("--run-id is required with --fresh-replay")
        print(_canonical_json(_fresh_replay(args.fresh_replay, args.run_id)))
        return 0
    if args.finalize_smoke_failure:
        result = finalize_smoke_failure(args.output_dir.resolve())
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
    if not args.smoke:
        raise SystemExit(
            "this staged producer requires --smoke or --finalize-smoke-failure"
        )
    result = verify_smoke(args.output_dir.resolve())
    if result["verdict"] != "SMOKE_PASSED":
        finalize_smoke_failure(args.output_dir.resolve())
    print(
        json.dumps(
            {
                "verdict": result["verdict"],
                "failed_checks": result["failed_checks"],
                "result": str((args.output_dir / "smoke_result.json").resolve()),
            },
            sort_keys=True,
        )
    )
    return 0 if result["verdict"] == "SMOKE_PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
