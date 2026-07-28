from __future__ import annotations

from copy import deepcopy
import math

import numpy as np
import pytest

from labs.ego_life_playground_v0 import engine, predictive_control
from labs.ego_life_playground_v0.microworld import PUBLIC_OBSERVATION_SCHEMA_VERSION


# R1's dense v4 tensor is an intentionally superseded live schema. Its banked
# artifacts and verifier remain immutable; R2 has its own executable contract
# tests rather than silently making these v4 assertions describe v5.
pytestmark = pytest.mark.skip(reason="superseded dense-v4 implementation contract")


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


def test_delta_tensor_is_action_outcome_state_feature_ordered() -> None:
    state = predictive_control.empty_state()

    assert state["schema_version"] == "ego.life_playground.predictive_control.v4"
    assert state["model"]["schema_version"] == "ego.life_playground.factored_predictor.v4"
    assert np.asarray(state["model"]["delta_weights"]).shape == (5, 6, 4, 15)
    predictive_control.validate_state(state)

    malformed = deepcopy(state)
    malformed["model"]["delta_weights"][0][0][0].pop()
    with pytest.raises(
        predictive_control.PredictiveControlInvariantError,
        match="delta_weights shape mismatch",
    ):
        predictive_control.validate_state(malformed)


def test_expected_delta_is_probability_weighted_conditional_delta() -> None:
    state, observation = _prepared("v3")
    model = deepcopy(state["model"])
    action_index = predictive_control.ACTION_INDEX["interact"]
    energy_index = predictive_control.STATE_INDEX["energy"]

    target_probabilities = {
        "moved": 0.05,
        "blocked": 0.05,
        "interacted": 0.50,
        "no_object": 0.30,
        "rested": 0.05,
        "turned": 0.05,
    }
    conditional_energy = {
        "moved": -0.01,
        "blocked": -0.02,
        "interacted": 0.24,
        "no_object": -0.018,
        "rested": -0.012,
        "turned": -0.014,
    }
    for outcome, probability in target_probabilities.items():
        outcome_index = predictive_control.OUTCOME_INDEX[outcome]
        model["outcome_weights"][action_index][outcome_index][0] = math.log(probability)
        model["delta_weights"][action_index][outcome_index][energy_index][0] = (
            conditional_energy[outcome]
        )

    modeled = state | {"model": model}
    prediction = predictive_control.predict_action(
        modeled,
        observation=observation,
        organism=_organism(),
        action="interact",
        relative_map_mode="relative",
    )

    assert prediction["conditional_delta_by_outcome"] == {
        outcome: {
            "energy": pytest.approx(conditional_energy[outcome], abs=1e-12),
            "safety": pytest.approx(0.0, abs=1e-12),
            "connection": pytest.approx(0.0, abs=1e-12),
            "stimulation": pytest.approx(0.0, abs=1e-12),
        }
        for outcome in predictive_control.OUTCOMES
    }
    expected_energy = sum(
        prediction["outcome_probabilities"][outcome]
        * prediction["conditional_delta_by_outcome"][outcome]["energy"]
        for outcome in predictive_control.OUTCOMES
    )
    assert prediction["predicted_delta"]["energy"] == pytest.approx(
        expected_energy,
        abs=1e-12,
    )


def test_update_changes_only_actual_outcome_delta_row() -> None:
    state, observation = _prepared("v3")
    model = deepcopy(state["model"])
    action_index = predictive_control.ACTION_INDEX["interact"]
    energy_index = predictive_control.STATE_INDEX["energy"]
    interacted_index = predictive_control.OUTCOME_INDEX["interacted"]
    no_object_index = predictive_control.OUTCOME_INDEX["no_object"]
    model["delta_weights"][action_index][interacted_index][energy_index][0] = 0.05
    model["delta_weights"][action_index][no_object_index][energy_index][0] = 0.30
    model["outcome_weights"][action_index][no_object_index][0] = 2.0
    state = state | {"model": model}
    before = deepcopy(state["model"]["delta_weights"])
    prediction_before = predictive_control.predict_action(
        state,
        observation=observation,
        organism=_organism(),
        action="interact",
        relative_map_mode="relative",
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

    after = updated["model"]["delta_weights"]
    assert after[action_index][interacted_index] != before[action_index][interacted_index]
    assert after[action_index][no_object_index] == before[action_index][no_object_index]
    expected_intercept = 0.05 + predictive_control.LEARNING_RATE * (
        0.262
        - prediction_before["conditional_delta_by_outcome"]["interacted"]["energy"]
    )
    assert after[action_index][interacted_index][energy_index][0] == pytest.approx(
        expected_intercept,
        abs=1e-12,
    )
    for other_action_index in range(len(predictive_control.ACTIONS)):
        if other_action_index != action_index:
            assert after[other_action_index] == before[other_action_index]
    assert receipt["delta_outcome_updated"] == "interacted"
    assert receipt["conditional_delta_hash_before"] != receipt[
        "conditional_delta_hash_after"
    ]


def test_frozen_update_preserves_conditional_delta_tensor() -> None:
    state, observation = _prepared("v3")
    before_model_hash = predictive_control.model_hash(state)
    before_delta = deepcopy(state["model"]["delta_weights"])

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

    assert frozen["model"]["delta_weights"] == before_delta
    assert predictive_control.model_hash(frozen) == before_model_hash
    assert receipt["delta_outcome_updated"] is None
    assert receipt["conditional_delta_hash_before"] == receipt[
        "conditional_delta_hash_after"
    ]


def test_engine_metadata_and_trace_bind_conditional_delta_receipt() -> None:
    state = engine.initial_state(run_id="conditioned-delta", seed=52)
    meta = engine.make_run_metadata("conditioned-delta", 711)
    command = engine.make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=dict(
            engine.DEFAULT_INTERVENTIONS,
            predictive_control_mode="factored_mpc",
        ),
        prev_command_hash=None,
    )
    result = engine.compute_step(state, command, meta)

    assert meta["schema_version"] == "ego.life_playground.run.v9"
    assert result.next_state["schema_version"] == "ego.life_playground.state.v9"
    assert result.trace["schema_version"] == "ego.life_playground.trace.v14"
    assert result.trace["code_path_hash"] == engine.compute_code_path_hash()
    for prediction in result.trace["predictive_control"]["plan"][
        "predictions_by_action"
    ].values():
        assert "conditional_delta_hash" in prediction
        assert "conditional_delta_by_outcome" not in prediction
    update = result.trace["predictive_control"]["update"]
    assert update["delta_outcome_updated"] == result.trace["world_transition"][
        "outcome_type"
    ]
    assert update["conditional_delta_hash_before"]
    assert update["conditional_delta_hash_after"]
