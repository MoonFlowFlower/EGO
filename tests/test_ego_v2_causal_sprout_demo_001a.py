from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from labs.ego_life_playground_v0 import causal_sprout as causal_sprout_module
from labs.ego_life_playground_v0.causal_sprout import (
    ACTIONS,
    PUBLIC_OBSERVATION_FIELDS,
    CausalSproutConfig,
    CausalSproutRuntime,
    build_paired_interventions,
    canonical_hash,
    create_learner,
    finite_difference_gradient_check,
    forward_learner,
    generate_contexts,
    reduce_trace_rows,
    render_trace_html,
    scan_public_input_leakage,
    update_learner,
)
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.engine import EngineInvariantError
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore


def _config(**overrides: object) -> CausalSproutConfig:
    values: dict[str, object] = {
        "namespace_prefix": "causal_sprout_dev_unit",
        "split": "dev",
        "context_count": 4,
        "steps_per_context": 10,
        "hidden_size": 24,
        "bptt_steps": 4,
        "learning_rate": 0.015,
        "correlation_probability": 0.9,
        "seed": 918273,
    }
    values.update(overrides)
    return CausalSproutConfig(**values)


def test_runtime_enforces_repo_pinned_numpy_version(monkeypatch):
    monkeypatch.setattr(causal_sprout_module.np, "__version__", "99.0.0")
    with pytest.raises(EngineInvariantError, match="requires numpy 2.2.6"):
        CausalSproutRuntime(_config())


def test_nursery_exposes_only_public_fields_and_builds_true_paired_interventions():
    contexts = generate_contexts(_config())
    assert len(contexts) == 4
    assert all(context["context_name"].startswith("causal_sprout_dev_") for context in contexts)
    assert all(type(context["context_name"]) is str for context in contexts)

    pairs = build_paired_interventions(contexts[0], row_index=3)
    nuisance_left, nuisance_right = pairs["nuisance_only"]
    mechanism_left, mechanism_right = pairs["mechanism"]
    for row in (nuisance_left, nuisance_right, mechanism_left, mechanism_right):
        assert set(row["public_observation"]) == set(PUBLIC_OBSERVATION_FIELDS)
        assert scan_public_input_leakage(row["public_observation"])["accepted"] is True

    hidden_channel = contexts[0]["hidden_mechanism_channel"]
    nuisance_channel = "feature_b" if hidden_channel == "feature_a" else "feature_a"
    assert nuisance_left["public_observation"][hidden_channel] == nuisance_right["public_observation"][hidden_channel]
    assert nuisance_left["public_observation"][nuisance_channel] != nuisance_right["public_observation"][nuisance_channel]
    assert nuisance_left["oracle_delta_by_action"] == nuisance_right["oracle_delta_by_action"]
    assert mechanism_left["public_observation"][nuisance_channel] == mechanism_right["public_observation"][nuisance_channel]
    assert mechanism_left["public_observation"][hidden_channel] != mechanism_right["public_observation"][hidden_channel]
    assert mechanism_left["oracle_delta_by_action"] != mechanism_right["oracle_delta_by_action"]


def test_leakage_scanner_has_positive_controls_and_rejects_forbidden_identity_fields():
    clean = {
        "feature_a": -1.0,
        "feature_b": 1.0,
        "local_state": 0.25,
        "energy": 0.7,
        "last_action": "consume",
        "last_observed_delta": 0.2,
    }
    assert scan_public_input_leakage(clean) == {
        "accepted": True,
        "forbidden_paths": [],
        "positive_control": False,
    }
    for forbidden in (
        "hidden_causal_channel",
        "hidden_mapping",
        "context_id",
        "world_seed",
        "split",
        "oracle_outcome",
        "future_observation",
        "verdict",
        "fixture_hash",
    ):
        poisoned = {**clean, forbidden: "positive-control"}
        report = scan_public_input_leakage(poisoned, positive_control=True)
        assert report["accepted"] is False
        assert report["positive_control"] is True
        assert forbidden in report["forbidden_paths"]


def test_tiny_rnn_optimizer_really_changes_weights_and_finite_difference_control_passes():
    learner = create_learner(hidden_size=24, seed=123, learning_rate=0.01, bptt_steps=4)
    observation = {
        "feature_a": -1.0,
        "feature_b": 1.0,
        "local_state": 0.2,
        "energy": 0.6,
        "last_action": "interact",
        "last_observed_delta": -0.2,
    }
    before_model_hash = learner["model_hash"]
    before_optimizer_hash = learner["optimizer_hash"]
    prediction, cache, advanced = forward_learner(learner, observation)
    updated, receipt = update_learner(
        advanced,
        cache,
        selected_action="consume",
        actual_delta=0.3,
        update_mode="canonical",
    )
    assert set(prediction["predicted_delta_by_action"]) == set(ACTIONS)
    assert set(prediction["terminal_risk_by_action"]) == set(ACTIONS)
    assert set(prediction["policy_logits_by_action"]) == set(ACTIONS)
    assert receipt["applied"] is True
    assert receipt["gradient_norm"] > 0.0
    assert updated["update_count"] == learner["update_count"] + 1
    assert updated["model_hash"] != before_model_hash
    assert updated["optimizer_hash"] != before_optimizer_hash

    frozen, frozen_receipt = update_learner(
        advanced,
        cache,
        selected_action="consume",
        actual_delta=0.3,
        update_mode="frozen",
    )
    assert frozen_receipt["applied"] is False
    assert frozen["model_hash"] == advanced["model_hash"]
    assert finite_difference_gradient_check(seed=321)["max_relative_error"] < 2e-4


def test_existing_controller_and_store_recompute_causal_sprout_without_stored_action_input(tmp_path: Path):
    runtime = CausalSproutRuntime(_config(context_count=3, steps_per_context=8))
    db_path = tmp_path / "causal-sprout.sqlite3"
    with SQLiteEventStore(db_path, runtime=runtime) as store:
        controller = PlaygroundController(
            store,
            run_id="causal-sprout-unit",
            seed=444,
            runtime=runtime,
        )
        for _ in range(12):
            dispatched = controller.dispatch(trigger_source="headless_acceptance")
            assert dispatched.receipt.committed is True
        live_state = deepcopy(controller.state)
        assert live_state["learner"]["update_count"] > 0
        assert live_state["learner"]["model_hash"] != runtime.initial_model_hash
        recovered = controller.recover()
        assert recovered.recovered is True
        assert canonical_hash(recovered.state) == canonical_hash(live_state)
        assert recovered.state["learner"]["optimizer_state"]
        assert recovered.state["learner"]["rng_state"]
        assert recovered.state["trace_chain_hash"] == recovered.traces[-1]["trace_hash"]
        assert all("selected_action" not in frame.trace["command"] for frame in recovered.frames[1:])

        row = store.connection.execute(
            "SELECT trace_json FROM traces WHERE run_id=? AND sequence=1",
            (controller.run_id,),
        ).fetchone()
        tampered = json.loads(row["trace_json"])
        tampered["selected_action"] = next(action for action in ACTIONS if action != tampered["selected_action"])
        tampered["trace_hash"] = runtime.compute_trace_hash(tampered)
        store.connection.execute(
            "UPDATE traces SET trace_json=?, trace_hash=? WHERE run_id=? AND sequence=1",
            (
                json.dumps(tampered, sort_keys=True, separators=(",", ":")),
                tampered["trace_hash"],
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="stored trace differs"):
            controller.recover()


def test_weight_and_context_assignment_tampering_fail_closed_even_if_outer_row_hash_is_rewritten(tmp_path: Path):
    runtime = CausalSproutRuntime(_config(context_count=2, steps_per_context=6))
    db_path = tmp_path / "tamper.sqlite3"
    with SQLiteEventStore(db_path, runtime=runtime) as store:
        controller = PlaygroundController(store, run_id="tamper-unit", seed=12, runtime=runtime)
        row = store.connection.execute(
            "SELECT initial_state_json FROM runs WHERE run_id=?", (controller.run_id,)
        ).fetchone()
        original = json.loads(row["initial_state_json"])

        weights_tamper = deepcopy(original)
        weights_tamper["learner"]["weights"]["w_xh"][0][0] += 0.125
        store.connection.execute(
            "UPDATE runs SET initial_state_json=?, initial_state_hash=? WHERE run_id=?",
            (
                json.dumps(weights_tamper, sort_keys=True, separators=(",", ":")),
                canonical_hash(weights_tamper),
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="initial replay boundary invalid"):
            controller.recover()

        store.connection.execute(
            "UPDATE runs SET initial_state_json=?, initial_state_hash=? WHERE run_id=?",
            (
                json.dumps(original, sort_keys=True, separators=(",", ":")),
                canonical_hash(original),
                controller.run_id,
            ),
        )
        context_tamper = deepcopy(original)
        context_tamper["evaluator"]["contexts"][0]["hidden_mapping_sign"] *= -1
        store.connection.execute(
            "UPDATE runs SET initial_state_json=?, initial_state_hash=? WHERE run_id=?",
            (
                json.dumps(context_tamper, sort_keys=True, separators=(",", ":")),
                canonical_hash(context_tamper),
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="initial replay boundary invalid"):
            controller.recover()


def test_every_equal_access_baseline_is_called_on_the_same_public_input_rows(tmp_path: Path):
    runtime = CausalSproutRuntime(_config(context_count=2, steps_per_context=7))
    with SQLiteEventStore(tmp_path / "baseline.sqlite3", runtime=runtime) as store:
        controller = PlaygroundController(store, run_id="baseline-unit", seed=88, runtime=runtime)
        for _ in range(9):
            controller.dispatch(trigger_source="headless_acceptance")
        traces = controller.recover().traces

    required = {
        "no_update_neural",
        "feed_forward_no_history",
        "feature_action_lookup",
        "nearest_neighbour",
        "surface_only",
        "shuffled_feedback",
        "random_policy",
        "bayesian_causal_reference",
        "constant_zero",
    }
    for trace in traces:
        assert set(trace["baselines"]) == required
        for receipt in trace["baselines"].values():
            assert receipt["called"] is True
            assert receipt["public_input_hash"] == trace["public_input_hash"]
            assert set(receipt["predicted_delta_by_action"]) == set(ACTIONS)


def test_context_bootstrap_is_generic_factorial_exploration_not_hidden_feature_policy(tmp_path: Path):
    runtime = CausalSproutRuntime(_config(context_count=1, steps_per_context=8))
    with SQLiteEventStore(tmp_path / "bootstrap.sqlite3", runtime=runtime) as store:
        controller = PlaygroundController(store, run_id="bootstrap-unit", seed=991, runtime=runtime)
        for _ in range(4):
            controller.dispatch(trigger_source="headless_acceptance")
        traces = controller.recover().traces
    assert [trace["selected_action"] for trace in traces] == [
        "consume",
        "consume",
        "interact",
        "interact",
    ]
    assert all(trace["selection_reason"] == "generic_factorial_bootstrap" for trace in traces)
    assert [
        (trace["public_observation"]["feature_a"], trace["public_observation"]["feature_b"])
        for trace in traces
    ] == [(-1.0, -1.0), (-1.0, 1.0), (1.0, -1.0), (1.0, 1.0)]


def test_runtime_uses_true_truncated_bptt_chunks_before_mutating_weights(tmp_path: Path):
    runtime = CausalSproutRuntime(_config(context_count=1, steps_per_context=8, bptt_steps=4))
    with SQLiteEventStore(tmp_path / "bptt.sqlite3", runtime=runtime) as store:
        controller = PlaygroundController(store, run_id="bptt-unit", seed=812, runtime=runtime)
        initial_hash = controller.state["learner"]["model_hash"]
        receipts = []
        for _ in range(4):
            result = controller.dispatch(trigger_source="headless_acceptance")
            receipts.append(result.step.trace["update_receipt"])
        assert controller.state["learner"]["update_count"] == 1
        assert controller.state["learner"]["model_hash"] != initial_hash
    assert [receipt["applied"] for receipt in receipts] == [False, False, False, True]
    assert all(receipt["reason"] == "accumulating_truncated_bptt" for receipt in receipts[:3])
    assert receipts[-1]["bptt_record_count"] == 4


def test_html_is_a_trace_reducer_and_contains_no_behavior_transition_path(tmp_path: Path):
    runtime = CausalSproutRuntime(_config(context_count=1, steps_per_context=6))
    with SQLiteEventStore(tmp_path / "html.sqlite3", runtime=runtime) as store:
        controller = PlaygroundController(store, run_id="html-unit", seed=34, runtime=runtime)
        for _ in range(6):
            controller.dispatch(trigger_source="headless_acceptance")
        traces = controller.recover().traces

    report = reduce_trace_rows(traces)
    report["current_judgment"] = "INCONCLUSIVE"
    report["intervention_summary"] = {
        "nuisance_ratio": 0.1,
        "mechanism_sign_accuracy": 0.75,
    }
    html = render_trace_html(report)
    assert report["source_trace_hash"] == canonical_hash(traces)
    assert report["row_count"] == 6
    assert report["rows"][-1]["selected_action"] == traces[-1]["selected_action"]
    assert report["rows"][-1]["model_weight_hash"] == traces[-1]["model_weight_hash_after"]
    assert report["reducer_hash"] in html
    assert "trace-only renderer" in html
    assert "current judgment: INCONCLUSIVE" in html
    assert "nuisance intervention ratio: 0.1" in html
    assert "mechanism intervention sign accuracy: 0.75" in html
    assert "compute_step(" not in html
    assert "select_action(" not in html


def test_demo_entrypoint_runs_through_shared_controller_store_and_writes_trace_html(tmp_path: Path):
    html_path = tmp_path / "demo.html"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_ego_causal_sprout_demo.py",
            "--steps",
            "6",
            "--db",
            str(tmp_path / "demo.sqlite3"),
            "--html",
            str(html_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "tick energy feature_a feature_b" in completed.stdout
    assert "current_judgment=" in completed.stdout
    assert "predicted_delta_by_action=" in completed.stdout
    assert html_path.exists()
    html_text = html_path.read_text(encoding="utf-8")
    assert "trace-only renderer" in html_text
    assert "row_count" in html_text
