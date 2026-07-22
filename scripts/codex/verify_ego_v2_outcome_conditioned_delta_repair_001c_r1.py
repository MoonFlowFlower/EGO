#!/usr/bin/env python3
"""Callable development-context gate for outcome-conditioned delta repair.

The verifier deliberately exposes only the already-consumed worlds 52/54 and
policy seed 711.  It reuses the 001C recovery/tamper machinery, but it does not
require semantic equality with the pre-repair predictor because this task
intentionally changes predictor estimates and may therefore change actions.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Any, Iterable, Mapping

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine, predictive_control  # noqa: E402
from labs.ego_life_playground_v0.microworld import policy_observation  # noqa: E402
from labs.ego_life_playground_v0.store import SQLiteEventStore  # noqa: E402
from scripts.codex import (  # noqa: E402
    verify_ego_v2_factored_predictive_control_boundary_gate_001c as boundary,
)


TASK_ID = "EGO-V2-P1-OUTCOME-CONDITIONED-DELTA-REPAIR-001C-R1"
ARCHIVED_TASK_ID = "EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-BOUNDARY-GATE-001C"
CONTEXTS = (
    ("p0_cross_v1", 52, 711),
    ("p2_vertical_v1", 54, 711),
)
ALLOWED_WORLD_SEEDS = frozenset({52, 54})
ALLOWED_POLICY_SEEDS = frozenset({711})
FORBIDDEN_WORLD_SEEDS = frozenset(range(60, 66))
FORBIDDEN_POLICY_SEEDS = frozenset({721, 722})
CLAIM_CEILING = (
    "Replayable outcome-conditioned delta-head implementation and measured "
    "improvement or failure on already-consumed worlds 52/54 with policy seed "
    "711 only."
)
PRODUCER = "verify_ego_v2_outcome_conditioned_delta_repair_001c_r1"


# The reused helpers resolve these globals at call time.  This makes their run
# IDs and per-row producer records name this task while keeping their original
# callable implementation independently inspectable.
boundary.TASK_ID = TASK_ID
boundary.PRODUCER = PRODUCER
boundary.CONTEXTS = CONTEXTS
boundary.CLAIM_CEILING = CLAIM_CEILING


def _canonical_json(value: Any) -> str:
    return engine.canonical_json(value)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(_canonical_json(value) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(_canonical_json(row) + "\n")
    os.replace(temporary, path)


def _code_path_hash() -> str:
    return _canonical_hash(
        {
            "engine_code_path_hash": engine.compute_code_path_hash(),
            "repair_verifier_sha256": _hash_file(Path(__file__).resolve()),
            "boundary_helper_sha256": _hash_file(Path(boundary.__file__).resolve()),
        }
    )


def _provenance(
    producer_function: str,
    *,
    inputs: list[Any],
    run_id: str,
    aggregation_rule: str,
    context_ids: list[str] | None = None,
    life_ids: list[int] | None = None,
    action_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "producer_function": f"{PRODUCER}.{producer_function}",
        "input_artifacts": inputs,
        "run_id": run_id,
        "seed": [711],
        "context_ids": context_ids or [],
        "life_ids": life_ids or [],
        "action_ids": action_ids or [],
        "aggregation_rule": aggregation_rule,
        "code_path_hash": _code_path_hash(),
    }


def _context_id(layout: str, world_seed: int, policy_seed: int) -> str:
    return f"{layout}:world={world_seed}:policy={policy_seed}"


def _artifact_ref(path: Path, *, relative_to: Path | None = None) -> dict[str, str]:
    display = path.name if relative_to is None else path.relative_to(relative_to).as_posix()
    return {"path": display, "sha256": _hash_file(path)}


def _boundary_checks(runs: list[Mapping[str, Any]]) -> dict[str, bool]:
    return {
        "dispatch_p95_at_most_250ms": all(
            float(run["dispatch_p95_seconds"]) <= 0.250 for run in runs
        ),
        "dispatch_max_at_most_500ms": all(
            float(run["dispatch_max_seconds"]) <= 0.500 for run in runs
        ),
        "last32_first32_ratio_below_2": all(
            float(run["duration_tail_ratio"]) < 2.0 for run in runs
        ),
        "three_fresh_recoveries_each_at_most_10s_and_exact": all(
            len(run["recovery_attempts"]) == 3
            and all(
                float(item["recover_run_seconds"]) <= 10.0 and bool(item["exact"])
                for item in run["recovery_attempts"]
            )
            for run in runs
        ),
        "trace_mean_at_most_32768_bytes": all(
            float(run["trace_mean_bytes"]) <= 32768 for run in runs
        ),
        "trace_max_at_most_65536_bytes": all(
            int(run["trace_max_bytes"]) <= 65536 for run in runs
        ),
        "sqlite_plus_sidecars_at_most_20mib": all(
            int(run["sqlite_and_sidecar_bytes"]) <= 20 * 1024 * 1024 for run in runs
        ),
        "all_row_readbacks_verified": all(
            bool(run["row_readbacks_verified"]) for run in runs
        ),
        "all_recovery_surfaces_exact": all(
            bool(run["all_recovery_surfaces_exact"]) for run in runs
        ),
        "all_four_rehash_tamper_controls_rejected": all(
            bool(run["all_tamper_controls_rejected"]) for run in runs
        ),
        "single_product_path_ast_scan_passed": all(
            bool(run["single_path_scan_passed"]) for run in runs
        ),
    }


def run_boundary(output_dir: Path) -> dict[str, Any]:
    archived_fixture = (
        REPO_ROOT / "artifacts" / ARCHIVED_TASK_ID / "prechange_semantic_fixture.json"
    )
    fixture = json.loads(archived_fixture.read_text(encoding="utf-8"))
    source_scan = boundary._source_path_scan()  # noqa: SLF001
    runs: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    for context in CONTEXTS:
        run, rows, _semantic_steps = boundary._run_smoke_context(  # noqa: SLF001
            output_dir,
            fixture,
            *context,
        )
        run["single_path_scan_passed"] = source_scan["passed"]
        runs.append(run)
        trace_rows.extend(rows)

    checks = _boundary_checks(runs)
    failed = sorted(name for name, passed in checks.items() if not passed)
    context_ids = [_context_id(*context) for context in CONTEXTS]
    trace_path = output_dir / "trace.jsonl"
    _write_jsonl(trace_path, trace_rows)
    (output_dir / "smoke_trace.jsonl").write_bytes(trace_path.read_bytes())

    performance = _provenance(
        "run_boundary",
        inputs=[
            _artifact_ref(output_dir / run["database_path"]) for run in runs
        ],
        run_id=f"{TASK_ID}:performance",
        aggregation_rule="all_thresholds_over_two_old_context_controller_runs",
        context_ids=context_ids,
        life_ids=[1, 2, 3, 4],
        action_ids=list(engine.ACTIONS),
    ) | {"runs": runs, "checks": checks, "failed_checks": failed}
    replay = _provenance(
        "run_boundary",
        inputs=[
            _artifact_ref(output_dir / run["database_path"]) for run in runs
        ],
        run_id=f"{TASK_ID}:replay",
        aggregation_rule="same_process_surfaces_plus_three_fresh_processes_and_rehash_tamper_controls",
        context_ids=context_ids,
        life_ids=[1, 2, 3, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "runs": [
            {
                "context_id": run["context_ids"][0],
                "recovery_surfaces": run["recovery_surfaces"],
                "recovery_attempts": run["recovery_attempts"],
                "tamper_controls": run["tamper_controls"],
            }
            for run in runs
        ],
        "source_path_scan": source_scan,
        "balanced_replay": "pending_boundary_decision",
    }
    smoke = _provenance(
        "run_boundary",
        inputs=[_artifact_ref(trace_path)],
        run_id=f"{TASK_ID}:smoke",
        aggregation_rule="all_runtime_replay_trace_and_single_path_checks",
        context_ids=context_ids,
        life_ids=[1, 2, 3, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "schema_version": "ego.v2.outcome_conditioned_delta_repair.smoke.v1",
        "runs": runs,
        "checks": checks,
        "failed_checks": failed,
        "boundary_passed": not failed,
        "fresh_effect_seeds_consumed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_json(output_dir / "smoke_result.json", smoke)
    _write_json(output_dir / "performance_report.json", performance)
    _write_json(output_dir / "replay_report.json", replay)
    return smoke


def _collect_snapshots(output_dir: Path, smoke: Mapping[str, Any]) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    for run, (layout, world_seed, policy_seed) in zip(smoke["runs"], CONTEXTS):
        context_id = _context_id(layout, world_seed, policy_seed)
        snapshots.extend(
            boundary._collect_balanced_snapshots(  # noqa: SLF001
                output_dir / run["database_path"],
                run["run_id"],
                context_id,
                world_seed,
                policy_seed,
            )
        )
    return snapshots


def _legacy_unconditional_rows(
    output_dir: Path,
    smoke: Mapping[str, Any],
    learned_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Train the pre-repair delta head independently on visible pre-action input."""

    learned_by_key = {
        (str(row["context_id"]), int(row["sequence"]), str(row["action"])): row
        for row in learned_rows
    }
    rows: list[dict[str, Any]] = []
    for run, (layout, world_seed, policy_seed) in zip(smoke["runs"], CONTEXTS):
        context_id = _context_id(layout, world_seed, policy_seed)
        target_sequences = {
            int(row["sequence"])
            for row in learned_rows
            if row["context_id"] == context_id
        }
        weights = np.zeros(
            (len(engine.ACTIONS), len(engine.STATE_KEYS), len(predictive_control.FEATURE_NAMES)),
            dtype=predictive_control.NUMERIC_DTYPE,
        )
        db_path = output_dir / run["database_path"]
        with SQLiteEventStore(db_path) as store:
            recovered = store.recover_run(run["run_id"])
        for previous_frame, frame in zip(recovered.frames, recovered.frames[1:]):
            trace = frame.trace
            if trace is None or trace.get("selected_action") is None:
                continue
            sequence = int(trace["sequence"])
            action = str(trace["selected_action"])
            decision_state, _ = engine._decision_state_for_tick(  # noqa: SLF001
                previous_frame.state,
                run_id=run["run_id"],
                sequence=sequence,
            )
            observation = policy_observation(decision_state["world"], occlusion=True)
            prepared, _ = predictive_control.observe_belief(
                decision_state["predictive_control"],
                observation=observation,
                episode_index=int(decision_state["clock"]["episode_index"]),
                mode="relative",
            )
            payload = predictive_control.predictor_input_snapshot(
                prepared,
                observation=observation,
                organism=decision_state["organism"],
                relative_map_mode="relative",
            )
            features = predictive_control._feature_vector_from_summary(  # noqa: SLF001
                organism=payload["organism"],
                summary=payload["belief_summary"],
            )
            if sequence in target_sequences:
                for candidate in engine.ACTIONS:
                    action_index = predictive_control.ACTION_INDEX[candidate]
                    predicted_delta = {
                        key: max(
                            -0.35,
                            min(
                                0.35,
                                predictive_control._ordered_dot(  # noqa: SLF001
                                    weights[action_index, predictive_control.STATE_INDEX[key]],
                                    features,
                                ),
                            ),
                        )
                        for key in engine.STATE_KEYS
                    }
                    learned = learned_by_key[(context_id, sequence, candidate)]
                    truth = learned["truth"]
                    mae = statistics.fmean(
                        abs(float(predicted_delta[key]) - float(truth["actual_delta"][key]))
                        for key in engine.STATE_KEYS
                    )
                    rows.append(
                        _provenance(
                            "_legacy_unconditional_rows",
                            inputs=[
                                f"snapshot:{learned['snapshot_hash']}",
                                f"legacy_weights:{_canonical_hash(weights.tolist())}",
                                f"truth:{_canonical_hash(truth)}",
                            ],
                            run_id=run["run_id"],
                            aggregation_rule="independent_unconditional_action_state_linear_delta_prediction",
                            context_ids=[context_id],
                            life_ids=[1 if learned["phase"] == "early" else 4],
                            action_ids=[candidate],
                        )
                        | {
                            "context_id": context_id,
                            "phase": learned["phase"],
                            "sequence": sequence,
                            "action": candidate,
                            "predicted_delta": predicted_delta,
                            "delta_mae": mae,
                        }
                    )
            actual_delta = engine.compute_actual_delta(
                trace["world_transition"], selected_action=action
            )
            actual_delta["energy"] = trace["metabolism"]["energy_delta"]
            action_index = predictive_control.ACTION_INDEX[action]
            for key in engine.STATE_KEYS:
                state_index = predictive_control.STATE_INDEX[key]
                prediction = predictive_control._ordered_dot(  # noqa: SLF001
                    weights[action_index, state_index], features
                )
                error = float(actual_delta[key]) - max(-0.35, min(0.35, prediction))
                weights[action_index, state_index] = predictive_control._updated_vector(  # noqa: SLF001
                    weights[action_index, state_index], features, error
                )
    return rows


def _aggregate_delta(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    cells: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        cells[(str(row["context_id"]), str(row["action"]))].append(
            float(row["delta_mae"])
        )
    return {
        "cell_count": len(cells),
        "delta_mae": statistics.fmean(
            statistics.fmean(values) for values in cells.values()
        ),
        "aggregation_rule": "mean_within_context_action_then_equal_macro_mean_across_cells",
    }


def _outcome_agnostic_rows(learned_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for learned in learned_rows:
        conditional = learned["prediction"]["conditional_delta_by_outcome"]
        predicted_delta = {
            key: statistics.fmean(float(conditional[outcome][key]) for outcome in predictive_control.OUTCOMES)
            for key in engine.STATE_KEYS
        }
        truth = learned["truth"]
        rows.append(
            _provenance(
                "_outcome_agnostic_rows",
                inputs=[
                    f"prediction:{_canonical_hash(learned['prediction'])}",
                    f"truth:{_canonical_hash(truth)}",
                ],
                run_id=str(learned["run_id"]),
                aggregation_rule="uniform_mean_of_six_conditional_rows_removing_predicted_outcome_weighting",
                context_ids=[str(learned["context_id"])],
                life_ids=[1 if learned["phase"] == "early" else 4],
                action_ids=[str(learned["action"])],
            )
            | {
                "context_id": learned["context_id"],
                "phase": learned["phase"],
                "sequence": learned["sequence"],
                "action": learned["action"],
                "predicted_delta": predicted_delta,
                "delta_mae": statistics.fmean(
                    abs(float(predicted_delta[key]) - float(truth["actual_delta"][key]))
                    for key in engine.STATE_KEYS
                ),
            }
        )
    return rows


def _balanced_digest(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "base": boundary._balanced_digest(payload),  # noqa: SLF001
        "code_path_hash": _code_path_hash(),
    }


def _compute_balanced(output_dir: Path) -> dict[str, Any]:
    return boundary._compute_balanced_payload(output_dir)  # noqa: SLF001


def run_balanced(output_dir: Path, smoke: Mapping[str, Any]) -> dict[str, Any]:
    payload = _compute_balanced(output_dir)
    rows = payload["rows"]
    learned_rows = [row for row in rows if row["model"] == "learned"]
    aggregate = payload["aggregate_metrics"]
    snapshots = _collect_snapshots(output_dir, smoke)
    action_counts = Counter(row["action"] for row in learned_rows)
    context_phase_counts = Counter(
        (row["context_id"], row["phase"], row["action"]) for row in learned_rows
    )

    legacy_rows = _legacy_unconditional_rows(output_dir, smoke, learned_rows)
    ablation_rows = _outcome_agnostic_rows(learned_rows)
    legacy = {
        phase: _aggregate_delta([row for row in legacy_rows if row["phase"] == phase])
        for phase in ("early", "late")
    }
    ablation = {
        phase: _aggregate_delta([row for row in ablation_rows if row["phase"] == phase])
        for phase in ("early", "late")
    }

    first = snapshots[0]
    clean_payload = predictive_control.predictor_input_snapshot(
        first["predictive_state"],
        observation=first["observation"],
        organism=first["organism"],
        relative_map_mode="relative",
    )
    leakage = boundary.run_leakage_controls(clean_payload)
    frozen = [boundary._run_frozen_control(output_dir, *context) for context in CONTEXTS]  # noqa: SLF001

    expected_digest = _balanced_digest(payload)
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--private-evaluate", str(output_dir)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    fresh_digest = json.loads(completed.stdout)
    replay_exact = fresh_digest == expected_digest
    learned_late = aggregate["learned"]["late"]
    learned_early = aggregate["learned"]["early"]
    no_update_late = aggregate["no_update"]["late"]
    checks = {
        "all_five_action_counts_exactly_equal": len(set(action_counts.values())) == 1
        and set(action_counts) == set(engine.ACTIONS),
        "no_snapshot_action_context_unused": len(learned_rows)
        == len(snapshots) * len(engine.ACTIONS)
        and len(context_phase_counts) == len(CONTEXTS) * 2 * len(engine.ACTIONS)
        and all(count > 0 for count in context_phase_counts.values()),
        "learned_late_brier_improves_by_at_least_0_02": learned_late["outcome_brier"]
        <= learned_early["outcome_brier"] - 0.02,
        "learned_late_nll_improves_by_at_least_0_05": learned_late["outcome_nll"]
        <= learned_early["outcome_nll"] - 0.05,
        "learned_late_brier_below_no_update_late": learned_late["outcome_brier"]
        < no_update_late["outcome_brier"],
        "learned_late_nll_below_no_update_late": learned_late["outcome_nll"]
        < no_update_late["outcome_nll"],
        "learned_late_delta_mae_below_early": learned_late["delta_mae"]
        < learned_early["delta_mae"],
        "learned_late_delta_mae_below_no_update_late": learned_late["delta_mae"]
        < no_update_late["delta_mae"],
        "learned_late_delta_mae_below_legacy_unconditional": learned_late["delta_mae"]
        < legacy["late"]["delta_mae"],
        "outcome_agnostic_ablation_changes_late_delta_metric": not math.isclose(
            learned_late["delta_mae"], ablation["late"]["delta_mae"], abs_tol=1e-15
        ),
        "leakage_clean_and_all_positive_controls_detected": leakage["clean_scan"]["clean"]
        and leakage["all_positive_controls_detected"],
        "fresh_subprocess_balanced_recompute_exact": replay_exact,
        "two_frozen_update_controls_pass": all(
            item["model_hash_unchanged"]
            and item["update_count"] == 0
            and item["first_20_cover_each_action_at_least_four"]
            for item in frozen
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    report = _provenance(
        "run_balanced",
        inputs=[_artifact_ref(output_dir / "smoke_result.json")],
        run_id=f"{TASK_ID}:balanced",
        aggregation_rule="equal_macro_mean_within_context_phase_action_for_all_five_actions",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        life_ids=[1, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "schema_version": "ego.v2.outcome_conditioned_delta_repair.balanced.v1",
        "snapshot_count": len(snapshots),
        "sample_counts_by_action": {action: action_counts[action] for action in engine.ACTIONS},
        "aggregate_metrics": aggregate,
        "legacy_unconditional_metrics": legacy,
        "outcome_agnostic_ablation_metrics": ablation,
        "rows": rows,
        "legacy_rows": legacy_rows,
        "outcome_agnostic_rows": ablation_rows,
        "frozen_update_controls": frozen,
        "checks": checks,
        "failed_checks": failed,
        "passed": not failed,
        "fresh_subprocess_digest_expected": expected_digest,
        "fresh_subprocess_digest_actual": fresh_digest,
        "fresh_effect_seeds_consumed": False,
    }
    _write_json(
        output_dir / "leakage_report.json",
        leakage
        | _provenance(
            "run_balanced",
            inputs=[f"clean:{leakage['clean_scan']['input_hash']}"],
            run_id=f"{TASK_ID}:leakage",
            aggregation_rule="clean_plus_five_independent_forbidden_field_positive_controls",
            context_ids=[_context_id(*context) for context in CONTEXTS],
            life_ids=[1, 4],
            action_ids=list(engine.ACTIONS),
        ),
    )
    return report


def _not_run(name: str, smoke: Mapping[str, Any]) -> dict[str, Any]:
    return _provenance(
        "run_gate",
        inputs=[],
        run_id=f"{TASK_ID}:{name}:not-run",
        aggregation_rule="not_run_boundary_failed",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        action_ids=list(engine.ACTIONS),
    ) | {"status": "not_run_boundary_failed", "failed_boundary_checks": smoke["failed_checks"]}


def run_gate(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if ALLOWED_WORLD_SEEDS & FORBIDDEN_WORLD_SEEDS or ALLOWED_POLICY_SEEDS & FORBIDDEN_POLICY_SEEDS:
        raise RuntimeError("development and forbidden fresh seed manifests overlap")
    smoke = run_boundary(output_dir)
    if smoke["boundary_passed"]:
        balanced = run_balanced(output_dir, smoke)
        verdict = (
            "OUTCOME_CONDITIONING_REPAIRED_ON_DEVELOPMENT_CONTEXTS"
            if balanced["passed"]
            else "OUTCOME_CONDITIONING_REPAIRED_NO_DELTA_IMPROVEMENT"
        )
    else:
        balanced = _not_run("balanced", smoke)
        verdict = "BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION"

    _write_json(output_dir / "balanced_prediction_report.json", balanced)
    baseline = _provenance(
        "run_gate",
        inputs=[_artifact_ref(output_dir / "balanced_prediction_report.json")],
        run_id=f"{TASK_ID}:baseline",
        aggregation_rule="independent_legacy_unconditional_and_zero_initialized_no_update_comparison",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        life_ids=[1, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "legacy_unconditional": balanced.get("legacy_unconditional_metrics"),
        "no_update": (balanced.get("aggregate_metrics") or {}).get("no_update"),
        "status": "completed" if smoke["boundary_passed"] else "not_run_boundary_failed",
    }
    ablation = _provenance(
        "run_gate",
        inputs=[_artifact_ref(output_dir / "balanced_prediction_report.json")],
        run_id=f"{TASK_ID}:ablation",
        aggregation_rule="uniform_outcome_row_collapse_on_same_balanced_snapshots",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        life_ids=[1, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "outcome_agnostic": balanced.get("outcome_agnostic_ablation_metrics"),
        "status": "completed" if smoke["boundary_passed"] else "not_run_boundary_failed",
    }
    _write_json(output_dir / "baseline_comparison.json", baseline)
    _write_json(output_dir / "ablation_report.json", ablation)

    replay_path = output_dir / "replay_report.json"
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    replay["balanced_replay"] = {
        "status": "completed" if smoke["boundary_passed"] else "not_run_boundary_failed",
        "exact": (balanced.get("checks") or {}).get(
            "fresh_subprocess_balanced_recompute_exact", False
        ),
        "expected": balanced.get("fresh_subprocess_digest_expected"),
        "actual": balanced.get("fresh_subprocess_digest_actual"),
    }
    _write_json(replay_path, replay)

    failed_checks = list(smoke["failed_checks"])
    failed_checks.extend(balanced.get("failed_checks", []))
    failure = _provenance(
        "run_gate",
        inputs=[
            _artifact_ref(output_dir / "smoke_result.json"),
            _artifact_ref(output_dir / "balanced_prediction_report.json"),
        ],
        run_id=f"{TASK_ID}:failure-manifest",
        aggregation_rule="all_failed_checks_preserved_without_threshold_or_parameter_tuning",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        life_ids=[1, 4],
        action_ids=list(engine.ACTIONS),
    ) | {"failed_checks": failed_checks, "verdict": verdict}
    eligibility = _provenance(
        "run_gate",
        inputs=[_artifact_ref(output_dir / "balanced_prediction_report.json")],
        run_id=f"{TASK_ID}:eligibility",
        aggregation_rule="repair_card_never_authorizes_fresh_effect_seed_consumption",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        action_ids=list(engine.ACTIONS),
    ) | {
        "fresh_effect_seeds_consumed": False,
        "eligible_for_separate_effect_card": False,
        "verdict": verdict,
    }
    result = _provenance(
        "run_gate",
        inputs=[
            _artifact_ref(output_dir / "performance_report.json"),
            _artifact_ref(output_dir / "balanced_prediction_report.json"),
            _artifact_ref(output_dir / "baseline_comparison.json"),
            _artifact_ref(output_dir / "ablation_report.json"),
            _artifact_ref(replay_path),
        ],
        run_id=f"{TASK_ID}:result",
        aggregation_rule="boundary_must_pass_then_all_frozen_prediction_checks_for_positive_development_verdict",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        life_ids=[1, 2, 3, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "task_id": TASK_ID,
        "verdict": verdict,
        "boundary_passed": smoke["boundary_passed"],
        "balanced_prediction_passed": bool(balanced.get("passed", False)),
        "failed_checks": failed_checks,
        "fresh_effect_seeds_consumed": False,
        "eligible_for_separate_effect_card": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_json(output_dir / "failure_manifest.json", failure)
    _write_json(output_dir / "effect_gate_eligibility.json", eligibility)
    _write_json(output_dir / "result.json", result)
    (output_dir / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
    )
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gate", type=Path)
    group.add_argument("--private-evaluate", type=Path, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.private_evaluate is not None:
        print(_canonical_json(_balanced_digest(_compute_balanced(args.private_evaluate.resolve()))))
        return 0
    result = run_gate(args.gate.resolve())
    print(
        _canonical_json(
            {
                "task_id": TASK_ID,
                "verdict": result["verdict"],
                "fresh_effect_seeds_consumed": False,
                "eligible_for_separate_effect_card": False,
            }
        )
    )
    return (
        0
        if result["verdict"]
        == "OUTCOME_CONDITIONING_REPAIRED_ON_DEVELOPMENT_CONTEXTS"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
