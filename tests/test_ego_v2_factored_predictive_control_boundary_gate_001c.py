from __future__ import annotations

from copy import deepcopy
import json
import platform
from pathlib import Path

import numpy as np
import pytest

from labs.ego_life_playground_v0 import engine, predictive_control
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.microworld import PUBLIC_OBSERVATION_SCHEMA_VERSION, policy_observation
from labs.ego_life_playground_v0.store import SQLiteEventStore
from labs.ego_life_playground_v0.visual_console import build_tk_trace_payload


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    REPO_ROOT
    / "artifacts"
    / "EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-BOUNDARY-GATE-001C"
    / "prechange_semantic_fixture.json"
)


def _observation(front: str = "empty") -> dict:
    visual = [["occluded" for _ in range(5)] for _ in range(5)]
    visual[2][2] = "self"
    visual[1][2] = front
    visual[2][1] = "empty"
    visual[2][3] = "empty"
    visual[3][2] = "empty"
    return {
        "schema_version": PUBLIC_OBSERVATION_SCHEMA_VERSION,
        "visual": visual,
    }


def _organism(**overrides: float) -> dict[str, float]:
    organism = {
        "energy": 0.45,
        "safety": 0.62,
        "connection": 0.50,
        "stimulation": 0.43,
    }
    organism.update(overrides)
    return organism


def _prepared_state(front: str = "empty") -> tuple[dict, dict]:
    observation = _observation(front)
    state, receipt = predictive_control.observe_belief(
        predictive_control.empty_state(),
        observation=observation,
        episode_index=0,
        mode="relative",
    )
    assert receipt["applied"] is True
    return state, observation


def test_numpy_runtime_contract_and_fixed_array_state_schema() -> None:
    hyperparameters = predictive_control.hyperparameters()
    runtime = hyperparameters["numeric_runtime"]

    assert runtime == {
        "backend": "numpy",
        "backend_version": "2.2.6",
        "dtype": "<f8",
        "python_version": platform.python_version(),
    }
    assert hyperparameters["action_order"] == list(engine.ACTIONS)
    assert hyperparameters["outcome_order"] == list(predictive_control.OUTCOMES)
    assert hyperparameters["state_order"] == list(engine.STATE_KEYS)
    assert hyperparameters["feature_order"] == list(predictive_control.FEATURE_NAMES)
    assert hyperparameters["action_order_hash"]
    assert hyperparameters["outcome_order_hash"]
    assert hyperparameters["state_order_hash"]
    assert hyperparameters["feature_order_hash"]

    state = predictive_control.empty_state()
    model = state["model"]
    assert model["schema_version"] == "ego.life_playground.factored_predictor.v5"
    assert np.asarray(model["outcome_weights"]).shape == (5, 6, 15)
    assert np.asarray(model["delta_base_weights"]).shape == (5, 4, 15)
    assert np.asarray(model["delta_outcome_offsets"]).shape == (5, 6, 4)
    assert np.asarray(model["resource_weights"]).shape == (5, 15)
    assert np.asarray(model["terminal_weights"]).shape == (5, 15)
    predictive_control.validate_state(state)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(np, "__version__", "2.2.5")
        with pytest.raises(
            predictive_control.PredictiveControlInvariantError,
            match="requires numpy 2.2.6",
        ):
            predictive_control.hyperparameters()
        with pytest.raises(
            predictive_control.PredictiveControlInvariantError,
            match="requires numpy 2.2.6",
        ):
            predictive_control.empty_state()
        with pytest.raises(
            predictive_control.PredictiveControlInvariantError,
            match="requires numpy 2.2.6",
        ):
            predictive_control.validate_state(state)


def test_validate_state_rejects_malformed_or_nonfinite_fixed_arrays() -> None:
    state = predictive_control.empty_state()

    malformed = deepcopy(state)
    malformed["model"]["outcome_weights"][0][0] = malformed["model"]["outcome_weights"][0][0][:-1]
    with pytest.raises(predictive_control.PredictiveControlInvariantError, match="shape"):
        predictive_control.validate_state(malformed)

    nonfinite = deepcopy(state)
    nonfinite["model"]["delta_base_weights"][3][1][7] = float("nan")
    with pytest.raises(predictive_control.PredictiveControlInvariantError, match="finite"):
        predictive_control.validate_state(nonfinite)


def test_packed_prediction_matrix_matches_frozen_ordered_dot_contract() -> None:
    state, observation = _prepared_state()
    model = deepcopy(state["model"])
    for action_index in range(len(engine.ACTIONS)):
        for outcome_index in range(len(predictive_control.OUTCOMES)):
            for feature_index in range(len(predictive_control.FEATURE_NAMES)):
                model["outcome_weights"][action_index][outcome_index][feature_index] = (
                    (action_index + 1) * (outcome_index + 2) * (feature_index - 5) / 1000.0
                )
        for state_index in range(len(predictive_control.STATE_KEYS)):
            for feature_index in range(len(predictive_control.FEATURE_NAMES)):
                model["delta_base_weights"][action_index][state_index][
                    feature_index
                ] = (
                    (action_index + 3)
                    * (state_index + 1)
                    * (feature_index - 8)
                    / 9000.0
                )
    compiled = predictive_control._compiled_model_arrays(model)  # noqa: SLF001
    packed = predictive_control._compiled_prediction_matrix(compiled)  # noqa: SLF001
    payload = predictive_control.predictor_input_snapshot(
        state | {"model": model},
        observation=observation,
        organism=_organism(),
        relative_map_mode="relative",
    )
    features = predictive_control._feature_vector_from_summary(  # noqa: SLF001
        organism=payload["organism"],
        summary=payload["belief_summary"],
    )
    for action_index in range(len(engine.ACTIONS)):
        observed = predictive_control._prediction_dot_batch(  # noqa: SLF001
            packed[action_index], features
        )
        expected = [
            predictive_control._ordered_dot(row, features)  # noqa: SLF001
            for row in packed[action_index]
        ]
        assert observed.tolist() == pytest.approx(expected, abs=1e-15)


def test_compact_planning_prediction_matches_full_internal_prediction() -> None:
    state, observation = _prepared_state()
    payload = predictive_control.predictor_input_snapshot(
        state,
        observation=observation,
        organism=_organism(),
        relative_map_mode="relative",
    )
    compiled = predictive_control._compiled_model_arrays(state["model"])  # noqa: SLF001
    packed = predictive_control._compiled_prediction_matrix(compiled)  # noqa: SLF001
    features = predictive_control._feature_vector_from_summary(  # noqa: SLF001
        organism=payload["organism"],
        summary=payload["belief_summary"],
    )
    for action in engine.ACTIONS:
        full = predictive_control._predict_from_payload(  # noqa: SLF001
            state,
            payload,
            action,
            include_hashes=False,
            precomputed_features=features,
            compiled_model=compiled,
            compiled_prediction_matrix=packed,
            visit_key_cache={},
        )
        compact = predictive_control._planning_prediction_vector(  # noqa: SLF001
            state,
            payload=payload,
            action=action,
            feature_vector=features,
            compiled_model=compiled,
            compiled_prediction_matrix=packed,
            visit_key_cache={},
        )
        expected = tuple(
            full["outcome_probabilities"][outcome]
            for outcome in predictive_control.OUTCOMES
        ) + tuple(full["predicted_delta"][key] for key in predictive_control.STATE_KEYS) + (
            full["resource_interaction_probability"],
            full["terminal_risk"],
            full["uncertainty"],
        )
        assert compact == pytest.approx(expected, abs=1e-15)


def test_plan_action_preserves_semantics_and_reuses_cached_feature_vectors(monkeypatch) -> None:
    state, observation = _prepared_state()
    feature_calls = 0
    compiled_calls = 0
    pose_prediction_calls = 0
    successor_distribution_calls = 0
    original_feature_vector = predictive_control._feature_vector_from_summary  # noqa: SLF001
    original_compiled = predictive_control._compiled_model_arrays  # noqa: SLF001
    original_prediction_for_pose = predictive_control._prediction_for_pose  # noqa: SLF001
    original_expected_pose_distribution = (  # noqa: SLF001
        predictive_control._expected_pose_distribution
    )

    def counting_feature_vector(*, organism, summary):
        nonlocal feature_calls
        feature_calls += 1
        return original_feature_vector(organism=organism, summary=summary)

    def counting_compiled(model):
        nonlocal compiled_calls
        compiled_calls += 1
        return original_compiled(model)

    def counting_prediction_for_pose(*args, **kwargs):
        nonlocal pose_prediction_calls
        pose_prediction_calls += 1
        return original_prediction_for_pose(*args, **kwargs)

    def counting_expected_pose_distribution(*args, **kwargs):
        nonlocal successor_distribution_calls
        successor_distribution_calls += 1
        return original_expected_pose_distribution(*args, **kwargs)

    monkeypatch.setattr(
        predictive_control,
        "_feature_vector_from_summary",
        counting_feature_vector,
    )
    monkeypatch.setattr(predictive_control, "_compiled_model_arrays", counting_compiled)
    monkeypatch.setattr(
        predictive_control,
        "_prediction_for_pose",
        counting_prediction_for_pose,
    )
    monkeypatch.setattr(
        predictive_control,
        "_expected_pose_distribution",
        counting_expected_pose_distribution,
    )
    monkeypatch.setattr(
        predictive_control,
        "_features",
        lambda _payload: pytest.fail("planner reconstructed dict features"),
    )

    common = dict(
        state=state,
        observation=observation,
        organism=_organism(),
        active_goal="energy",
        heuristic_scores={action: 0.0 for action in engine.ACTIONS},
        horizon=12,
        beam_width=16,
        discount=0.97,
        relative_map_mode="relative",
        goal_value_mode="contextual",
        action_costs=engine.ACTION_COSTS,
        run_seed=711,
        episode_index=0,
        sequence=1,
    )
    first = predictive_control.plan_action(**common)
    second = predictive_control.plan_action(**common)

    assert first == second
    assert first["horizon"] == 12
    assert first["beam_width"] == 16
    assert set(first["predictions_by_action"]) == set(engine.ACTIONS)
    assert all(
        abs(sum(prediction["outcome_probabilities"].values()) - 1.0) <= 1e-9
        for prediction in first["predictions_by_action"].values()
    )
    assert compiled_calls == 2
    assert pose_prediction_calls > feature_calls
    assert pose_prediction_calls < 2_000
    assert successor_distribution_calls <= pose_prediction_calls
    assert feature_calls < 120


def test_public_predictions_match_prechange_fixture_within_boundary(tmp_path: Path) -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    expected_step = fixture["steps"][0]
    with SQLiteEventStore(tmp_path / "fixture.sqlite3") as store:
        controller = PlaygroundController(
            store,
            run_id="fixture-check",
            seed=711,
            world_seed=52,
            layout_id="p0_cross_v1",
        )
        dispatched = controller.dispatch(
            dict(engine.DEFAULT_INTERVENTIONS, predictive_control_mode="factored_mpc"),
            trigger_source="ui_run_button",
        )
        assert dispatched.receipt.committed is True
        trace = controller.last_trace

    assert trace is not None
    plan = trace["predictive_control"]["plan"]
    assert trace["selected_action"] == expected_step["selected_action"]
    for action in engine.ACTIONS:
        expected_prediction = expected_step["predictions_by_action"][action]
        observed_prediction = plan["predictions_by_action"][action]
        assert observed_prediction["outcome_probabilities"] == pytest.approx(
            expected_prediction["outcome_probabilities"], abs=1e-12
        )
        assert observed_prediction["predicted_delta"] == pytest.approx(
            expected_prediction["predicted_delta"], abs=1e-12
        )
        assert observed_prediction["resource_interaction_probability"] == pytest.approx(
            expected_prediction["resource_interaction_probability"], abs=1e-12
        )
        assert observed_prediction["terminal_risk"] == pytest.approx(
            expected_prediction["terminal_risk"], abs=1e-12
        )
        expected_value = expected_step["candidate_values"][action]
        observed_value = plan["candidate_values"][action]
        assert observed_value["plan_actions"] == expected_value["plan_actions"]
        assert observed_value["trajectory_hash"] == expected_value["trajectory_hash"]
        for key in expected_value.keys() - {"plan_actions", "trajectory_hash"}:
            assert observed_value[key] == pytest.approx(expected_value[key], abs=1e-12)


def test_update_only_changes_selected_action_and_frozen_updates_keep_model_hash(monkeypatch) -> None:
    state, observation = _prepared_state("v1")
    before = deepcopy(state["model"])
    compiled_calls = 0
    original_compiled = predictive_control._compiled_model_arrays  # noqa: SLF001

    def counting_compiled(model):
        nonlocal compiled_calls
        compiled_calls += 1
        return original_compiled(model)

    monkeypatch.setattr(predictive_control, "_compiled_model_arrays", counting_compiled)
    updated, receipt = predictive_control.update_after_transition(
        state,
        observation=observation,
        organism_before=_organism(),
        action="interact",
        actual_outcome_type="interacted",
        actual_delta={
            "energy": 0.18,
            "safety": 0.0,
            "connection": 0.02,
            "stimulation": 0.02,
        },
        terminal=False,
        resource_interaction=True,
        next_observation=observation,
        episode_index=0,
        relative_map_mode="relative",
        updates_enabled=True,
    )

    assert receipt["applied"] is True
    assert compiled_calls == 1
    for action_index, action in enumerate(engine.ACTIONS):
        changed = (
            updated["model"]["outcome_weights"][action_index] != before["outcome_weights"][action_index]
            or updated["model"]["delta_base_weights"][action_index] != before["delta_base_weights"][action_index]
            or updated["model"]["delta_outcome_offsets"][action_index] != before["delta_outcome_offsets"][action_index]
            or updated["model"]["resource_weights"][action_index] != before["resource_weights"][action_index]
            or updated["model"]["terminal_weights"][action_index] != before["terminal_weights"][action_index]
        )
        assert changed is (action == "interact")

    frozen_state, frozen_receipt = predictive_control.update_after_transition(
        state,
        observation=observation,
        organism_before=_organism(),
        action="interact",
        actual_outcome_type="interacted",
        actual_delta={
            "energy": 0.18,
            "safety": 0.0,
            "connection": 0.02,
            "stimulation": 0.02,
        },
        terminal=False,
        resource_interaction=True,
        next_observation=observation,
        episode_index=0,
        relative_map_mode="relative",
        updates_enabled=False,
    )
    assert predictive_control.model_hash(frozen_state) == predictive_control.model_hash(state)
    assert frozen_receipt["model_hash_before"] == frozen_receipt["model_hash_after"]
    assert frozen_receipt["action_exposure_counts_after"]["interact"] == 1
    assert compiled_calls == 2


def test_engine_public_actual_delta_and_compact_trace_fail_closed(monkeypatch) -> None:
    meta = engine.make_run_metadata("trace-boundary", 711)
    assert meta["schema_version"] == "ego.life_playground.run.v10"
    assert meta["default_predictive_control_mode"] == "off"
    assert meta["predictive_control"]["numeric_runtime"]["backend_version"] == "2.2.6"

    state = engine.initial_state(run_id="trace-boundary", seed=52)
    command = engine.make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=dict(engine.DEFAULT_INTERVENTIONS, predictive_control_mode="factored_mpc"),
        prev_command_hash=None,
    )
    actual_delta_calls = 0
    original_compute_actual_delta = engine.compute_actual_delta

    def counting_compute_actual_delta(world_transition, *, selected_action):
        nonlocal actual_delta_calls
        actual_delta_calls += 1
        return original_compute_actual_delta(
            world_transition,
            selected_action=selected_action,
        )

    monkeypatch.setattr(engine, "compute_actual_delta", counting_compute_actual_delta)
    result = engine.compute_step(state, command, meta)
    trace = result.trace

    assert actual_delta_calls == 1
    assert trace["schema_version"] == "ego.life_playground.trace.v15"
    plan = trace["predictive_control"]["plan"]
    assert "producer_function" not in plan
    assert "algorithm" not in plan
    assert "predictor_context_hash" in plan
    assert "candidate_value_hashes" not in plan
    assert set(plan["predictions_by_action"]) == set(engine.ACTIONS)
    for prediction in plan["predictions_by_action"].values():
        assert "input_hash" not in prediction
        assert "feature_hash" not in prediction
        assert "uncertainty" not in prediction
        assert "visit_count" not in prediction
        assert "conditional_delta_hash" in prediction
        assert "conditional_delta_by_outcome" not in prediction
        assert "prediction_hash" in prediction
    assert plan["beam_receipt"]["root_action_counts_by_depth"] == [5] * 12
    assert "update" in trace["predictive_control"]
    assert "selected_action_update" not in trace["predictive_control"]
    assert "world_observation" not in trace
    assert trace["command"] == command
    repeated_fields = {
        "global_tick": trace["sequence"],
        "episode_index": trace["action_episode"]["episode_index"],
        "episode_tick": trace["action_episode"]["episode_tick"],
        "episode_before": trace["action_episode"],
        "policy_decision_input_hash": trace["policy_projection"]["decision_input_hash"],
        "world_observation": trace["observation"],
    }
    assert not (set(repeated_fields) & set(trace))
    legacy_repeated = deepcopy(trace)
    legacy_repeated.update(repeated_fields)
    legacy_repeated["predictive_control"]["plan"]["candidate_value_hashes"] = {
        action: engine.canonical_hash(value)
        for action, value in plan["candidate_values"].items()
    }
    assert len(engine.canonical_json(legacy_repeated).encode("utf-8")) - len(
        engine.canonical_json(trace).encode("utf-8")
    ) >= 900
    ui_payload = build_tk_trace_payload(result.next_state, trace)
    assert ui_payload["predictive_control"]["update"]["outcome_brier"] == trace[
        "predictive_control"
    ]["update"]["outcome_brier"]

    assert engine.compute_actual_delta(
        {"outcome_type": "interacted", "cause": "resource"},
        selected_action="interact",
    ) == engine._actual_delta(  # noqa: SLF001
        {"outcome_type": "interacted", "cause": "resource"},
        selected_action="interact",
    )

    drifted = deepcopy(meta)
    drifted["predictive_control"]["numeric_runtime"]["backend_version"] = "2.2.5"
    with pytest.raises(engine.EngineInvariantError, match="predictive control metadata mismatch"):
        engine.compute_step(state, command, drifted)

    old_state = deepcopy(state)
    old_state["schema_version"] = "ego.life_playground.state.v7"
    with pytest.raises(engine.EngineInvariantError, match="causal state schema mismatch"):
        engine.compute_step(old_state, command, meta)

    old_meta = deepcopy(meta)
    old_meta["schema_version"] = "ego.life_playground.run.v7"
    with pytest.raises(
        engine.EngineInvariantError,
        match="run metadata schema_version is not canonical",
    ):
        engine.compute_step(state, command, old_meta)
