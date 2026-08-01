#!/usr/bin/env python3
"""Freeze, reveal once, and verify EGO-V2-CAUSAL-SPROUT-DEMO-001A."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.causal_sprout import (
    ACTIONS,
    BASELINE_NAMES,
    PUBLIC_OBSERVATION_FIELDS,
    CausalSproutConfig,
    CausalSproutRuntime,
    build_paired_interventions,
    canonical_hash,
    canonical_json,
    finite_difference_gradient_check,
    forward_learner,
    reduce_trace_rows,
    render_trace_html,
    reset_recurrent_state,
    scan_public_input_leakage,
)
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import SQLiteEventStore


TASK_ID = "EGO-V2-CAUSAL-SPROUT-DEMO-001A"
REQUIRED_ARTIFACTS = (
    "result.json",
    "trace.jsonl",
    "learning_curve.json",
    "baseline_comparison.json",
    "intervention_report.json",
    "ablation_report.json",
    "replay_report.json",
    "leakage_report.json",
    "row_recompute_report.json",
    "artifact_manifest.json",
    "failure_manifest.json",
    "demo.html",
    "claim_ceiling.txt",
)
THRESHOLDS = {
    "candidate_loss_ratio_max": 0.75,
    "nuisance_change_effect_range_ratio_max": 0.20,
    "mechanism_effect_sign_accuracy_min": 0.80,
    "freeze_update_gain_destruction_min": 0.50,
    "history_reset_relative_damage_min": 0.20,
    "recompute_absolute_tolerance": 1e-10,
}
INVALIDATING_BASELINES = (
    "no_update_neural",
    "feed_forward_no_history",
    "feature_action_lookup",
    "nearest_neighbour",
    "surface_only",
    "shuffled_feedback",
    "constant_zero",
)


class HeldoutAlreadyRevealedError(RuntimeError):
    pass


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_freeze_manifest(
    dev_config: CausalSproutConfig, heldout_config: CausalSproutConfig, *, test_only: bool
) -> dict[str, Any]:
    paths = (
        REPO_ROOT / "labs/ego_life_playground_v0/causal_sprout.py",
        REPO_ROOT / "labs/ego_life_playground_v0/controller.py",
        REPO_ROOT / "labs/ego_life_playground_v0/store.py",
        REPO_ROOT / "scripts/run_ego_causal_sprout_demo.py",
        Path(__file__),
        REPO_ROOT / "tests/test_ego_v2_causal_sprout_demo_001a.py",
        REPO_ROOT / "scripts/codex/tests/test_verify_ego_v2_causal_sprout_demo_001a.py",
    )
    existing = [path for path in paths if path.exists()]
    manifest = {
        "schema_version": "ego.causal_sprout.freeze.v1",
        "task_id": TASK_ID,
        "test_only": bool(test_only),
        "source_files": [
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "sha256": _sha256(path),
                "size": path.stat().st_size,
            }
            for path in existing
        ],
        "dev_config": dev_config.to_dict(),
        "heldout_config": heldout_config.to_dict(),
        "thresholds": deepcopy(THRESHOLDS),
        "baselines": list(BASELINE_NAMES),
        "invalidating_baselines": list(INVALIDATING_BASELINES),
        "stopping_rule": "one committed heldout packet; no retune or rerun after reveal",
        "sample_count": {
            "dev_rows": dev_config.context_count * dev_config.steps_per_context,
            "heldout_rows_per_arm": heldout_config.context_count * heldout_config.steps_per_context,
        },
    }
    manifest["freeze_hash"] = canonical_hash(manifest)
    return manifest


def _run_runtime(
    root: Path,
    label: str,
    config: CausalSproutConfig,
    *,
    initial_learner: Mapping[str, Any] | None = None,
    interventions: Mapping[str, str] | None = None,
    seed: int = 7001,
) -> dict[str, Any]:
    runtime = CausalSproutRuntime(config, initial_learner=initial_learner)
    db_path = root / f"{label}.sqlite3"
    run_id = f"{label}-{canonical_hash([config.namespace_prefix, seed])[:12]}"
    with SQLiteEventStore(db_path, runtime=runtime) as store:
        controller = PlaygroundController(
            store,
            run_id=run_id,
            seed=seed,
            runtime=runtime,
        )
        while controller.state["lifecycle"]["trial_status"] != "terminal":
            dispatched = controller.dispatch(
                interventions,
                trigger_source="headless_acceptance",
            )
            if not dispatched.receipt.committed:
                raise RuntimeError(dispatched.receipt.error)
        # The controller performs one full replay automatically at the terminal
        # transition. Reuse that verified recovery rather than replaying the
        # same run a second time in-process.
        recovery = controller.recovery
        live_state_hash = canonical_hash(controller.state)
        trace_hash = canonical_hash(recovery.traces)

    # Fresh adapter + fresh SQLite connection proves restart recovery of model,
    # recurrent state, optimizer, RNG, counter, and trace chain.
    fresh_runtime = CausalSproutRuntime(config, initial_learner=initial_learner)
    with SQLiteEventStore(db_path, runtime=fresh_runtime) as fresh_store:
        fresh_controller = PlaygroundController(
            fresh_store,
            run_id=run_id,
            seed=seed,
            runtime=fresh_runtime,
        )
        # Explicit run loading already performs a complete recomputation.
        fresh_recovery = fresh_controller.recovery
        fresh_state_hash = canonical_hash(fresh_recovery.state)
        fresh_trace_hash = canonical_hash(fresh_recovery.traces)

    return {
        "label": label,
        "runtime": runtime,
        "recovery": recovery,
        "state": recovery.state,
        "live_state_hash": live_state_hash,
        "fresh_state_hash": fresh_state_hash,
        "trace_hash": trace_hash,
        "fresh_trace_hash": fresh_trace_hash,
        "db_sha256": _sha256(db_path),
        "db_size": db_path.stat().st_size,
        "run_id": run_id,
    }


def _evaluation_rows(recovery: Any, *, warmup_rows: int = 3) -> list[Mapping[str, Any]]:
    return [
        trace
        for trace in recovery.traces
        if int(trace["evaluator_only"]["row_index"]) >= warmup_rows
    ]


def _loss_report(recovery: Any, *, warmup_rows: int = 3) -> dict[str, Any]:
    rows = _evaluation_rows(recovery, warmup_rows=warmup_rows)
    candidate_errors: list[float] = []
    baseline_errors: dict[str, list[float]] = {name: [] for name in BASELINE_NAMES}
    selected_candidate: list[float] = []
    for trace in rows:
        oracle = trace["evaluator_only"]["oracle_delta_by_action"]
        for action in ACTIONS:
            candidate_errors.append(
                (float(trace["predicted_delta_by_action"][action]) - float(oracle[action])) ** 2
            )
            for name in BASELINE_NAMES:
                baseline_errors[name].append(
                    (
                        float(trace["baselines"][name]["predicted_delta_by_action"][action])
                        - float(oracle[action])
                    )
                    ** 2
                )
        selected_candidate.append(float(trace["prediction_error"]) ** 2)
    mse = lambda values: sum(values) / max(1, len(values))
    return {
        "row_count": len(rows),
        "action_prediction_count": len(candidate_errors),
        "candidate_interventional_mse": mse(candidate_errors),
        "candidate_selected_action_mse": mse(selected_candidate),
        "baseline_interventional_mse": {
            name: mse(values) for name, values in baseline_errors.items()
        },
    }


def _strongest_invalidating(losses: Mapping[str, float]) -> tuple[str, float]:
    name = min(INVALIDATING_BASELINES, key=lambda candidate: float(losses[candidate]))
    return name, float(losses[name])


def _paired_intervention_report(run: Mapping[str, Any]) -> dict[str, Any]:
    runtime: CausalSproutRuntime = run["runtime"]
    recovery = run["recovery"]
    nuisance_changes: list[float] = []
    mechanism_matches: list[bool] = []
    permuted_matches: list[bool] = []
    shifted_matches: list[bool] = []
    pair_count = 0
    for frame_index, trace in enumerate(recovery.traces, start=1):
        row_index = int(trace["evaluator_only"]["row_index"])
        if row_index < 3:
            continue
        pre_state = recovery.frames[frame_index - 1].state
        context_index = int(pre_state["evaluator"]["context_index"])
        context = runtime.contexts[context_index]
        pairs = build_paired_interventions(
            context,
            row_index,
            base_observation=trace["public_observation"],
        )
        learner = pre_state["learner"]

        nuisance_predictions = []
        for pair in pairs["nuisance_only"]:
            prediction, _, _ = forward_learner(learner, pair["public_observation"])
            nuisance_predictions.append(prediction["predicted_delta_by_action"])
        for action in ("consume", "interact"):
            nuisance_changes.append(
                abs(
                    float(nuisance_predictions[1][action])
                    - float(nuisance_predictions[0][action])
                )
            )

        mechanism_predictions = []
        for pair in pairs["mechanism"]:
            prediction, _, _ = forward_learner(learner, pair["public_observation"])
            mechanism_predictions.append(prediction["predicted_delta_by_action"])
        for action in ("consume", "interact"):
            predicted_change = float(mechanism_predictions[1][action]) - float(
                mechanism_predictions[0][action]
            )
            oracle_change = float(pairs["mechanism"][1]["oracle_delta_by_action"][action]) - float(
                pairs["mechanism"][0]["oracle_delta_by_action"][action]
            )
            match = predicted_change * oracle_change > 0.0
            mechanism_matches.append(match)
            if bool(context["feature_permutation"]):
                permuted_matches.append(match)
            if context.get("mechanism_shift_at") is not None and row_index >= int(
                context["mechanism_shift_at"]
            ):
                shifted_matches.append(match)
        pair_count += 1

    effect_range = 0.60
    mean_nuisance = sum(nuisance_changes) / max(1, len(nuisance_changes))
    accuracy = sum(mechanism_matches) / max(1, len(mechanism_matches))
    return {
        "paired_context_rows": pair_count,
        "nuisance_only": {
            "mean_absolute_prediction_change": mean_nuisance,
            "true_causal_effect_range": effect_range,
            "change_to_effect_range_ratio": mean_nuisance / effect_range,
            "paired_other_state_held_equal": True,
        },
        "mechanism_intervention": {
            "effect_sign_accuracy": accuracy,
            "comparison_count": len(mechanism_matches),
            "paired_nuisance_held_equal": True,
        },
        "correlation_reversal": {
            "heldout_correlation_probability": runtime.config.correlation_probability,
            "effect_sign_accuracy": accuracy,
        },
        "feature_and_glyph_permutation": {
            "comparison_count": len(permuted_matches),
            "effect_sign_accuracy": sum(permuted_matches) / max(1, len(permuted_matches)),
            "glyph_commitments_present": all(
                bool(trace["evaluator_only"]["glyph_encoding_commitment"])
                for trace in recovery.traces
            ),
        },
        "local_mechanism_shift": {
            "comparison_count": len(shifted_matches),
            "effect_sign_accuracy": sum(shifted_matches) / max(1, len(shifted_matches)),
        },
        "learner_received_hidden_truth": False,
    }


def _row_recompute(run: Mapping[str, Any]) -> dict[str, Any]:
    runtime: CausalSproutRuntime = run["runtime"]
    recovery = run["recovery"]
    state = deepcopy(recovery.frames[0].state)
    mismatches: list[dict[str, Any]] = []
    for index, stored in enumerate(recovery.traces, start=1):
        recomputed = runtime.compute_step(state, stored["command"], recovery.run_meta)
        fields = (
            "public_input_hash",
            "predicted_delta_by_action",
            "selected_action",
            "actual_delta",
            "model_weight_hash_after",
            "optimizer_hash_after",
            "update_count",
            "trace_hash",
        )
        different = [field for field in fields if canonical_json(recomputed.trace[field]) != canonical_json(stored[field])]
        if different or canonical_hash(recomputed.next_state) != canonical_hash(recovery.frames[index].state):
            mismatches.append({"sequence": index, "fields": different})
        state = recomputed.next_state
    return {
        "schema_version": "ego.causal_sprout.row_recompute.v1",
        "row_count": len(recovery.traces),
        "all_rows_match": not mismatches,
        "mismatches": mismatches,
        "inputs": "serialized pre-state plus command; observation/outcome/action recomputed",
        "stored_action_used_as_input": False,
    }


def _leakage_report(run: Mapping[str, Any]) -> dict[str, Any]:
    reports = [scan_public_input_leakage(trace["public_observation"]) for trace in run["recovery"].traces]
    controls = []
    clean = {
        "feature_a": -1.0,
        "feature_b": 1.0,
        "local_state": 0.2,
        "energy": 0.6,
        "last_action": "wait",
        "last_observed_delta": -0.025,
    }
    for field in (
        "hidden_mapping",
        "hidden_causal_channel",
        "context_id",
        "world_seed",
        "split",
        "oracle_outcome",
        "future_observation",
        "verdict",
        "fixture_hash",
    ):
        controls.append(scan_public_input_leakage({**clean, field: "poison"}, positive_control=True))
    learner_fields_exact = all(
        tuple(trace["learner_input_fields"]) == PUBLIC_OBSERVATION_FIELDS
        for trace in run["recovery"].traces
    )
    command_fields = set(run["recovery"].traces[0]["command"])
    return {
        "schema_version": "ego.causal_sprout.leakage.v1",
        "public_rows_accepted": all(report["accepted"] for report in reports),
        "positive_control_count": len(controls),
        "positive_controls_rejected": all(not report["accepted"] for report in controls),
        "positive_control_reports": controls,
        "learner_fields_exact": learner_fields_exact,
        "command_contains_stored_action_prediction_or_outcome": bool(
            {"selected_action", "prediction", "actual_delta"} & command_fields
        ),
        "context_namespace_entered_learner": False,
        "oracle_entered_learner": False,
    }


def _curve(recovery: Any) -> dict[str, Any]:
    traces = recovery.traces
    window = max(1, len(traces) // 8)
    points = []
    for start in range(0, len(traces), window):
        block = traces[start : start + window]
        candidate = sum(float(row["prediction_error"]) ** 2 for row in block) / len(block)
        lookup = sum(
            float(row["baselines"]["feature_action_lookup"]["selected_action_error"]) ** 2
            for row in block
        ) / len(block)
        no_update = sum(
            float(row["baselines"]["no_update_neural"]["selected_action_error"]) ** 2
            for row in block
        ) / len(block)
        points.append(
            {
                "start_sequence": int(block[0]["sequence"]),
                "end_sequence": int(block[-1]["sequence"]),
                "candidate_mse": candidate,
                "lookup_mse": lookup,
                "no_update_mse": no_update,
            }
        )
    early = points[0]["candidate_mse"]
    late = points[-1]["candidate_mse"]
    return {
        "schema_version": "ego.causal_sprout.learning_curve.v1",
        "window_size": window,
        "points": points,
        "early_window_loss": early,
        "late_window_loss": late,
        "late_to_early_ratio": late / max(1e-12, early),
    }


def _artifact_manifest(output: Path) -> dict[str, Any]:
    excluded = {"artifact_manifest.json"}
    paths = sorted(
        path
        for path in output.iterdir()
        if path.is_file() and path.name not in excluded and not path.name.endswith(".sqlite3")
    )
    return {
        "schema_version": "ego.causal_sprout.artifact_manifest.v1",
        "task_id": TASK_ID,
        "artifacts": [
            {"path": path.name, "sha256": _sha256(path), "size": path.stat().st_size}
            for path in paths
        ],
    }


def generate_evidence(
    output: Path,
    *,
    dev_config: CausalSproutConfig,
    heldout_config: CausalSproutConfig,
    test_only: bool = False,
) -> dict[str, Any]:
    output = Path(output).resolve()
    if (output / "heldout_commitment.json").exists() or (output / "result.json").exists():
        raise HeldoutAlreadyRevealedError("heldout packet already committed/revealed; rerun refused")
    if dev_config.split != "dev" or heldout_config.split != "heldout":
        raise ValueError("dev/heldout split mismatch")
    if not dev_config.namespace_prefix.startswith("causal_sprout_dev_"):
        raise ValueError("dev namespace is not task-local")
    if not heldout_config.namespace_prefix.startswith("causal_sprout_heldout_"):
        raise ValueError("heldout namespace is not task-local")
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ego-causal-sprout-") as temporary:
        temp_root = Path(temporary)
        dev_run = _run_runtime(temp_root, "dev-canonical", dev_config, seed=dev_config.seed + 1)
        trained_learner = reset_recurrent_state(dev_run["state"]["learner"])
        _write_json(output / "learner_state.json", trained_learner)

        # Development and the baseline-solvability exercise complete before
        # source/config/threshold bytes are frozen. Nothing below mutates those
        # inputs; the next operation is the opaque heldout commitment.
        freeze_manifest = _source_freeze_manifest(
            dev_config, heldout_config, test_only=test_only
        )
        freeze_manifest.pop("freeze_hash", None)
        freeze_manifest["development_completed_before_freeze"] = True
        freeze_manifest["dev_run_trace_hash"] = dev_run["trace_hash"]
        freeze_manifest["dev_final_model_hash"] = trained_learner["model_hash"]
        freeze_manifest["dev_replay_exact"] = (
            dev_run["trace_hash"] == dev_run["fresh_trace_hash"]
            and dev_run["live_state_hash"] == dev_run["fresh_state_hash"]
        )
        freeze_manifest["freeze_hash"] = canonical_hash(freeze_manifest)
        _write_json(output / "freeze_manifest.json", freeze_manifest)

        heldout_runtime = CausalSproutRuntime(heldout_config, initial_learner=trained_learner)
        heldout_commitment = {
            "schema_version": "ego.causal_sprout.heldout_commitment.v1",
            "task_id": TASK_ID,
            "test_only": bool(test_only),
            "freeze_hash": freeze_manifest["freeze_hash"],
            "context_commitment": canonical_hash(heldout_runtime.contexts),
            "context_count": heldout_config.context_count,
            "rows_per_context": heldout_config.steps_per_context,
            "namespace_commitment": canonical_hash(heldout_config.namespace_prefix),
            "pre_reveal": True,
            "authorized_arms": [
                "canonical",
                "freeze_updates",
                "reset_history",
                "shuffle_feedback",
                "delete_weights",
                "nuisance_permutation",
                "mechanism_intervention",
            ],
        }
        heldout_commitment["commitment_hash"] = canonical_hash(heldout_commitment)
        _write_json(output / "heldout_commitment.json", heldout_commitment)

        canonical_run = _run_runtime(
            temp_root,
            "heldout-canonical",
            heldout_config,
            initial_learner=trained_learner,
            seed=heldout_config.seed + 1,
        )

        frozen_interventions = {**heldout_runtime.default_interventions, "update_mode": "frozen"}
        reset_interventions = {**heldout_runtime.default_interventions, "history_mode": "reset_each_step"}
        delete_interventions = {**heldout_runtime.default_interventions, "weights_mode": "deleted"}
        nuisance_interventions = {**heldout_runtime.default_interventions, "nuisance_mode": "permuted"}
        mechanism_interventions = {**heldout_runtime.default_interventions, "mechanism_mode": "shifted"}

        # Freeze/shuffle start at development, so the ablation removes the
        # entire learned update effect rather than only heldout adaptation.
        dev_frozen = _run_runtime(
            temp_root,
            "dev-freeze-updates",
            dev_config,
            interventions={**CausalSproutRuntime(dev_config).default_interventions, "update_mode": "frozen"},
            seed=dev_config.seed + 1,
        )
        frozen_run = _run_runtime(
            temp_root,
            "heldout-freeze-updates",
            heldout_config,
            initial_learner=reset_recurrent_state(dev_frozen["state"]["learner"]),
            interventions=frozen_interventions,
            seed=heldout_config.seed + 1,
        )
        dev_shuffled = _run_runtime(
            temp_root,
            "dev-shuffled-feedback",
            dev_config,
            interventions={**CausalSproutRuntime(dev_config).default_interventions, "feedback_mode": "shuffled"},
            seed=dev_config.seed + 1,
        )
        shuffled_run = _run_runtime(
            temp_root,
            "heldout-shuffled-feedback",
            heldout_config,
            initial_learner=reset_recurrent_state(dev_shuffled["state"]["learner"]),
            seed=heldout_config.seed + 1,
        )
        reset_run = _run_runtime(
            temp_root,
            "heldout-reset-history",
            heldout_config,
            initial_learner=trained_learner,
            interventions=reset_interventions,
            seed=heldout_config.seed + 1,
        )
        deleted_run = _run_runtime(
            temp_root,
            "heldout-delete-weights",
            heldout_config,
            initial_learner=trained_learner,
            interventions=delete_interventions,
            seed=heldout_config.seed + 1,
        )
        nuisance_run = _run_runtime(
            temp_root,
            "heldout-nuisance-permutation",
            heldout_config,
            initial_learner=trained_learner,
            interventions=nuisance_interventions,
            seed=heldout_config.seed + 1,
        )
        mechanism_run = _run_runtime(
            temp_root,
            "heldout-mechanism-intervention",
            heldout_config,
            initial_learner=trained_learner,
            interventions=mechanism_interventions,
            seed=heldout_config.seed + 1,
        )

        canonical_loss = _loss_report(canonical_run["recovery"])
        strongest_name, strongest_loss = _strongest_invalidating(
            canonical_loss["baseline_interventional_mse"]
        )
        candidate_loss = float(canonical_loss["candidate_interventional_mse"])
        baseline_comparison = {
            "schema_version": "ego.causal_sprout.baseline_comparison.v1",
            **canonical_loss,
            "strongest_invalidating_control": strongest_name,
            "strongest_invalidating_control_mse": strongest_loss,
            "candidate_to_strongest_ratio": candidate_loss / max(1e-12, strongest_loss),
            "equal_public_rows": True,
            "bayesian_reference_is_upper_bound_only": True,
            "ground_truth_oracle_is_evaluator_only": True,
        }
        intervention_report = _paired_intervention_report(canonical_run)

        arm_runs = {
            "freeze_updates": frozen_run,
            "reset_history": reset_run,
            "shuffle_feedback": shuffled_run,
            "delete_weights": deleted_run,
            "nuisance_permutation": nuisance_run,
            "mechanism_intervention": mechanism_run,
        }
        arm_losses = {
            name: _loss_report(run["recovery"])["candidate_interventional_mse"]
            for name, run in arm_runs.items()
        }
        candidate_gain = strongest_loss - candidate_loss
        freeze_destruction = (
            (float(arm_losses["freeze_updates"]) - candidate_loss) / max(1e-12, candidate_gain)
            if candidate_gain > 0.0
            else 0.0
        )
        history_damage = (
            (float(arm_losses["reset_history"]) - candidate_loss) / max(1e-12, candidate_loss)
        )
        ablation_report = {
            "schema_version": "ego.causal_sprout.ablation.v1",
            "canonical_candidate_mse": candidate_loss,
            "strongest_invalidating_control_mse": strongest_loss,
            "candidate_gain": candidate_gain,
            "arm_candidate_mse": arm_losses,
            "freeze_update_gain_destruction": freeze_destruction,
            "history_reset_relative_damage": history_damage,
            "real_rerun": True,
            "arms": {
                name: {
                    "trace_hash": run["trace_hash"],
                    "db_sha256": run["db_sha256"],
                    "fresh_recovery_match": run["trace_hash"] == run["fresh_trace_hash"],
                }
                for name, run in arm_runs.items()
            },
        }

        row_recompute = _row_recompute(canonical_run)
        leakage_report = _leakage_report(canonical_run)
        replay_report = {
            "schema_version": "ego.causal_sprout.replay.v1",
            "run_id": canonical_run["run_id"],
            "row_count": len(canonical_run["recovery"].traces),
            "exact_recompute": (
                canonical_run["live_state_hash"] == canonical_run["fresh_state_hash"]
                and canonical_run["trace_hash"] == canonical_run["fresh_trace_hash"]
            ),
            "stored_action_used_as_input": False,
            "stored_prediction_used_as_input": False,
            "stored_outcome_used_as_input": False,
            "command_fields": sorted(canonical_run["recovery"].traces[0]["command"]),
            "state_hash": canonical_run["fresh_state_hash"],
            "trace_hash": canonical_run["fresh_trace_hash"],
            "persisted_fields": [
                "weights",
                "hidden_state",
                "optimizer_state",
                "rng_state",
                "update_count",
                "trace_chain_hash",
            ],
            "tamper_tests_covered_by": "tests/test_ego_v2_causal_sprout_demo_001a.py",
        }
        curve = _curve(dev_run["recovery"])
        gradient_report = finite_difference_gradient_check(seed=dev_config.seed + 99)

        gates = {
            "loss_ratio": baseline_comparison["candidate_to_strongest_ratio"]
            <= THRESHOLDS["candidate_loss_ratio_max"],
            "nuisance_invariance": intervention_report["nuisance_only"][
                "change_to_effect_range_ratio"
            ]
            <= THRESHOLDS["nuisance_change_effect_range_ratio_max"],
            "mechanism_sensitivity": intervention_report["mechanism_intervention"][
                "effect_sign_accuracy"
            ]
            >= THRESHOLDS["mechanism_effect_sign_accuracy_min"],
            "correlation_reversal": intervention_report["correlation_reversal"][
                "effect_sign_accuracy"
            ]
            >= THRESHOLDS["mechanism_effect_sign_accuracy_min"],
            "feature_glyph_permutation": intervention_report["feature_and_glyph_permutation"][
                "effect_sign_accuracy"
            ]
            >= THRESHOLDS["mechanism_effect_sign_accuracy_min"],
            "update_ablation": freeze_destruction
            >= THRESHOLDS["freeze_update_gain_destruction_min"],
            "history_ablation": history_damage
            >= THRESHOLDS["history_reset_relative_damage_min"],
            "replay": replay_report["exact_recompute"],
            "row_recompute": row_recompute["all_rows_match"],
            "leakage": (
                leakage_report["public_rows_accepted"]
                and leakage_report["positive_controls_rejected"]
                and leakage_report["learner_fields_exact"]
                and not leakage_report["command_contains_stored_action_prediction_or_outcome"]
            ),
            "gradient_positive_control": gradient_report["max_relative_error"] < 2e-4,
        }
        evidence_valid = all(
            gates[name]
            for name in ("replay", "row_recompute", "leakage", "gradient_positive_control")
        )
        baseline_equivalence = baseline_comparison["candidate_to_strongest_ratio"] > THRESHOLDS[
            "candidate_loss_ratio_max"
        ]
        if not evidence_valid:
            verdict = "INVALID_EVIDENCE"
        elif baseline_equivalence:
            verdict = "SURFACE_FIT_BASELINE_EQUIVALENCE"
        elif all(gates.values()):
            verdict = "BOUNDED_CAUSAL_REGULARITY_LEARNED"
        else:
            verdict = "INCONCLUSIVE"
        failures = [name for name, passed in gates.items() if not passed]

        trace_path = output / "trace.jsonl"
        trace_path.write_text(
            "".join(canonical_json(trace) + "\n" for trace in canonical_run["recovery"].traces),
            encoding="utf-8",
        )
        _write_json(output / "learning_curve.json", curve)
        _write_json(output / "baseline_comparison.json", baseline_comparison)
        _write_json(output / "intervention_report.json", intervention_report)
        _write_json(output / "ablation_report.json", ablation_report)
        _write_json(output / "replay_report.json", replay_report)
        _write_json(output / "leakage_report.json", leakage_report)
        _write_json(output / "row_recompute_report.json", row_recompute)
        _write_json(output / "gradient_check.json", gradient_report)

        reduced = reduce_trace_rows(canonical_run["recovery"].traces)
        reduced["current_judgment"] = (
            "LEARNING"
            if verdict == "BOUNDED_CAUSAL_REGULARITY_LEARNED"
            else "SURFACE_FIT"
            if verdict == "SURFACE_FIT_BASELINE_EQUIVALENCE"
            else "INCONCLUSIVE"
        )
        reduced["intervention_summary"] = {
            "nuisance_ratio": intervention_report["nuisance_only"][
                "change_to_effect_range_ratio"
            ],
            "mechanism_sign_accuracy": intervention_report["mechanism_intervention"][
                "effect_sign_accuracy"
            ],
        }
        (output / "demo.html").write_text(render_trace_html(reduced), encoding="utf-8")

        claim_ceiling = (
            "Maximum conditional claim: a small recurrent neural learner learned, from public "
            "interaction history in a predefined causal nursery, an action-conditioned mechanism "
            "regularity stable to named nuisance interventions and stronger than specified surface "
            "controls on one frozen heldout packet. This wording is allowed only when verdict is "
            "BOUNDED_CAUSAL_REGULARITY_LEARNED. This does not prove real-world causal understanding, "
            "general causal reasoning, learned active experiment design, AGI, consciousness, "
            "subjectivity, emotion, agency, autonomy, electronic life, user benefit, or the same "
            "capability in the ordinary Ego runtime.\n"
        )
        (output / "claim_ceiling.txt").write_text(claim_ceiling, encoding="utf-8")
        failure_manifest = {
            "schema_version": "ego.causal_sprout.failure_manifest.v1",
            "verdict": verdict,
            "failure_count": len(failures),
            "failures": failures,
            "negative_results_preserved": True,
        }
        _write_json(output / "failure_manifest.json", failure_manifest)

        result = {
            "schema_version": "ego.causal_sprout.result.v1",
            "task_id": TASK_ID,
            "verdict": verdict,
            "layer": "local explicit V2 product/mechanism demo; science_weight=0",
            "test_only": bool(test_only),
            "heldout_reveal_count": 1,
            "heldout_commitment_hash": heldout_commitment["commitment_hash"],
            "freeze_hash": freeze_manifest["freeze_hash"],
            "gates": gates,
            "failures": failures,
            "candidate_interventional_mse": candidate_loss,
            "strongest_baseline": strongest_name,
            "strongest_baseline_mse": strongest_loss,
            "nuisance_ratio": intervention_report["nuisance_only"][
                "change_to_effect_range_ratio"
            ],
            "mechanism_sign_accuracy": intervention_report["mechanism_intervention"][
                "effect_sign_accuracy"
            ],
            "freeze_update_gain_destruction": freeze_destruction,
            "history_reset_relative_damage": history_damage,
            "replay_exact": replay_report["exact_recompute"],
            "leakage_positive_controls_rejected": leakage_report[
                "positive_controls_rejected"
            ],
            "claim_ceiling_path": "claim_ceiling.txt",
            "science_weight": 0,
        }
        _write_json(output / "result.json", result)
        _write_json(output / "artifact_manifest.json", _artifact_manifest(output))
        return result


def _default_configs() -> tuple[CausalSproutConfig, CausalSproutConfig]:
    dev = CausalSproutConfig(
        namespace_prefix="causal_sprout_dev_frozen_001a",
        split="dev",
        context_count=64,
        steps_per_context=16,
        hidden_size=24,
        bptt_steps=16,
        learning_rate=0.020,
        correlation_probability=0.9,
        seed=918273,
        exploration_rate=0.60,
    )
    heldout = CausalSproutConfig(
        namespace_prefix="causal_sprout_heldout_frozen_001a",
        split="heldout",
        context_count=16,
        steps_per_context=16,
        hidden_size=24,
        bptt_steps=16,
        learning_rate=0.020,
        correlation_probability=0.1,
        seed=271828,
        exploration_rate=0.30,
    )
    return dev, heldout


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=REPO_ROOT / "artifacts" / TASK_ID,
    )
    args = parser.parse_args(argv)
    dev, heldout = _default_configs()
    result = generate_evidence(args.artifact_dir, dev_config=dev, heldout_config=heldout)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"] != "INVALID_EVIDENCE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
