from __future__ import annotations

from copy import deepcopy
import math

import numpy as np
import pytest

from labs.ego_life_playground_v0 import engine, predictive_control
from labs.ego_life_playground_v0.microworld import PUBLIC_OBSERVATION_SCHEMA_VERSION


def _observation(front: str = "empty") -> dict:
    visual = [["occluded" for _ in range(5)] for _ in range(5)]
    visual[2][2] = "self"
    visual[1][2] = front
    visual[2][1] = "empty"
    visual[2][3] = "empty"
    visual[3][2] = "empty"
    return {"schema_version": PUBLIC_OBSERVATION_SCHEMA_VERSION, "visual": visual}


def _organism() -> dict[str, float]:
    return {
        "energy": 0.45,
        "safety": 0.62,
        "connection": 0.50,
        "stimulation": 0.43,
    }


def _prepared(front: str = "empty") -> tuple[dict, dict]:
    observation = _observation(front)
    state, receipt = predictive_control.observe_belief(
        predictive_control.empty_state(),
        observation=observation,
        episode_index=0,
        mode="relative",
    )
    assert receipt["applied"] is True
    return state, observation


def test_hierarchical_delta_shapes_and_compiled_planner_head_count() -> None:
    state = predictive_control.empty_state()

    assert state["schema_version"] == "ego.life_playground.predictive_control.v5"
    assert state["model"]["schema_version"] == "ego.life_playground.factored_predictor.v5"
    assert np.asarray(state["model"]["delta_base_weights"]).shape == (5, 4, 15)
    assert np.asarray(state["model"]["delta_outcome_offsets"]).shape == (5, 6, 4)
    compiled = predictive_control._compiled_model_arrays(state["model"])  # noqa: SLF001
    packed = predictive_control._compiled_prediction_matrix(compiled)  # noqa: SLF001
    assert packed.shape == (5, 12, 15)
    predictive_control.validate_state(state)

    malformed = deepcopy(state)
    malformed["model"]["delta_outcome_offsets"][0][0].pop()
    with pytest.raises(
        predictive_control.PredictiveControlInvariantError,
        match="delta_outcome_offsets shape mismatch",
    ):
        predictive_control.validate_state(malformed)


def test_expected_delta_is_probability_weighted_base_plus_outcome_offset() -> None:
    state, observation = _prepared("v3")
    model = deepcopy(state["model"])
    action_index = predictive_control.ACTION_INDEX["interact"]
    energy_index = predictive_control.STATE_INDEX["energy"]

    probabilities = {
        "moved": 0.05,
        "blocked": 0.05,
        "interacted": 0.50,
        "no_object": 0.30,
        "rested": 0.05,
        "turned": 0.05,
    }
    offsets = {
        "moved": -0.01,
        "blocked": -0.02,
        "interacted": 0.24,
        "no_object": -0.018,
        "rested": -0.012,
        "turned": -0.18,
    }
    shared_base = 0.02
    model["delta_base_weights"][action_index][energy_index][0] = shared_base
    for outcome, probability in probabilities.items():
        outcome_index = predictive_control.OUTCOME_INDEX[outcome]
        model["outcome_weights"][action_index][outcome_index][0] = math.log(probability)
        model["delta_outcome_offsets"][action_index][outcome_index][energy_index] = offsets[
            outcome
        ]

    prediction = predictive_control.predict_action(
        state | {"model": model},
        observation=observation,
        organism=_organism(),
        action="interact",
        relative_map_mode="relative",
    )

    for outcome in predictive_control.OUTCOMES:
        assert prediction["conditional_delta_by_outcome"][outcome]["energy"] == pytest.approx(
            shared_base + offsets[outcome], abs=1e-12
        )
    expected = sum(
        prediction["outcome_probabilities"][outcome]
        * prediction["conditional_delta_by_outcome"][outcome]["energy"]
        for outcome in predictive_control.OUTCOMES
    )
    assert prediction["predicted_delta"]["energy"] == pytest.approx(expected, abs=1e-12)


def test_projected_nlms_update_changes_shared_base_and_zero_sum_offsets() -> None:
    state, observation = _prepared("v3")
    model = deepcopy(state["model"])
    action_index = predictive_control.ACTION_INDEX["interact"]
    energy_index = predictive_control.STATE_INDEX["energy"]
    interacted_index = predictive_control.OUTCOME_INDEX["interacted"]
    no_object_index = predictive_control.OUTCOME_INDEX["no_object"]
    model["delta_base_weights"][action_index][energy_index][0] = 0.05
    model["delta_outcome_offsets"][action_index][interacted_index][energy_index] = -0.24
    model["delta_outcome_offsets"][action_index][no_object_index][energy_index] = 0.24
    state = state | {"model": model}
    before_base = deepcopy(state["model"]["delta_base_weights"])
    before_offsets = deepcopy(state["model"]["delta_outcome_offsets"])
    payload = predictive_control._predictor_input(  # noqa: SLF001
        state,
        observation=observation,
        organism=_organism(),
        relative_map_mode="relative",
    )
    features = predictive_control._feature_vector_from_summary(  # noqa: SLF001
        organism=payload["organism"], summary=payload["belief_summary"]
    )
    prediction_before = predictive_control.predict_action(
        state,
        observation=observation,
        organism=_organism(),
        action="interact",
        relative_map_mode="relative",
    )
    error = 0.262 - prediction_before["conditional_delta_by_outcome"]["interacted"][
        "energy"
    ]
    expected_step = predictive_control.LEARNING_RATE * error / (
        float(np.dot(features, features)) + 1.0
    )

    updated, receipt = predictive_control.update_after_transition(
        state,
        observation=observation,
        organism_before=_organism(),
        action="interact",
        actual_outcome_type="interacted",
        actual_delta={
            "energy": 0.262,
            "safety": 0.0,
            "connection": 0.0,
            "stimulation": 0.0,
        },
        terminal=False,
        resource_interaction=True,
        next_observation=observation,
        episode_index=0,
        relative_map_mode="relative",
        updates_enabled=True,
    )

    after_base = updated["model"]["delta_base_weights"]
    after_offsets = updated["model"]["delta_outcome_offsets"]
    assert after_base[action_index][energy_index][0] == pytest.approx(
        before_base[action_index][energy_index][0]
        + expected_step
        + expected_step / len(predictive_control.OUTCOMES),
        abs=1e-12,
    )
    assert after_offsets[action_index][interacted_index][energy_index] == pytest.approx(
        before_offsets[action_index][interacted_index][energy_index]
        + expected_step * (1.0 - 1.0 / len(predictive_control.OUTCOMES)),
        abs=1e-12,
    )
    assert after_offsets[action_index][no_object_index][energy_index] == pytest.approx(
        before_offsets[action_index][no_object_index][energy_index]
        - expected_step / len(predictive_control.OUTCOMES),
        abs=1e-12,
    )
    assert sum(
        after_offsets[action_index][outcome_index][energy_index]
        for outcome_index in range(len(predictive_control.OUTCOMES))
    ) == pytest.approx(0.0, abs=1e-12)
    for other_action in range(len(predictive_control.ACTIONS)):
        if other_action != action_index:
            assert after_base[other_action] == before_base[other_action]
            assert after_offsets[other_action] == before_offsets[other_action]
    assert receipt["delta_outcome_updated"] == "interacted"
    assert receipt["delta_base_hash_before"] != receipt["delta_base_hash_after"]
    assert receipt["delta_outcome_offset_hash_before"] != receipt[
        "delta_outcome_offset_hash_after"
    ]


def test_frozen_update_preserves_hierarchical_delta_state() -> None:
    state, observation = _prepared("v3")
    before_hash = predictive_control.model_hash(state)
    before_base = deepcopy(state["model"]["delta_base_weights"])
    before_offsets = deepcopy(state["model"]["delta_outcome_offsets"])

    frozen, receipt = predictive_control.update_after_transition(
        state,
        observation=observation,
        organism_before=_organism(),
        action="interact",
        actual_outcome_type="interacted",
        actual_delta={
            "energy": 0.262,
            "safety": 0.0,
            "connection": 0.0,
            "stimulation": 0.0,
        },
        terminal=False,
        resource_interaction=True,
        next_observation=observation,
        episode_index=0,
        relative_map_mode="relative",
        updates_enabled=False,
    )

    assert frozen["model"]["delta_base_weights"] == before_base
    assert frozen["model"]["delta_outcome_offsets"] == before_offsets
    assert predictive_control.model_hash(frozen) == before_hash
    assert receipt["delta_outcome_updated"] is None
    assert receipt["delta_base_hash_before"] == receipt["delta_base_hash_after"]
    assert receipt["delta_outcome_offset_hash_before"] == receipt[
        "delta_outcome_offset_hash_after"
    ]


def test_engine_trace_binds_hierarchical_delta_receipt() -> None:
    state = engine.initial_state(run_id="hierarchical-delta", seed=52)
    meta = engine.make_run_metadata("hierarchical-delta", 711)
    command = engine.make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=dict(engine.DEFAULT_INTERVENTIONS, predictive_control_mode="factored_mpc"),
        prev_command_hash=None,
    )
    result = engine.compute_step(state, command, meta)

    assert meta["schema_version"] == "ego.life_playground.run.v10"
    assert result.next_state["schema_version"] == "ego.life_playground.state.v10"
    assert result.trace["schema_version"] == "ego.life_playground.trace.v15"
    for prediction in result.trace["predictive_control"]["plan"][
        "predictions_by_action"
    ].values():
        assert "conditional_delta_hash" in prediction
        assert "conditional_delta_by_outcome" not in prediction
    update = result.trace["predictive_control"]["update"]
    assert update["delta_outcome_updated"] == result.trace["world_transition"][
        "outcome_type"
    ]
    assert update["delta_base_hash_before"]
    assert update["delta_base_hash_after"]
    assert update["delta_outcome_offset_hash_before"]
    assert update["delta_outcome_offset_hash_after"]
