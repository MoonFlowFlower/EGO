from __future__ import annotations

from copy import deepcopy

import pytest

from labs.ego_life_playground_v0 import predictive_control
from labs.ego_life_playground_v0 import engine
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.microworld import (
    PUBLIC_OBSERVATION_SCHEMA_VERSION,
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


def _self_state(**overrides: float) -> dict[str, float]:
    value = {
        "energy": 0.45,
        "safety": 0.62,
        "connection": 0.50,
        "stimulation": 0.43,
    }
    value.update(overrides)
    return value


def _prepared(state: dict, observation: dict, *, episode_index: int = 0) -> dict:
    updated, receipt = predictive_control.observe_belief(
        state,
        observation=observation,
        episode_index=episode_index,
        mode="relative",
    )
    assert receipt["applied"] is True
    return updated


def test_softmax_and_linear_predictor_update_numerics() -> None:
    observation = _observation("empty")
    state = _prepared(predictive_control.empty_state(), observation)
    before = predictive_control.predict_action(
        state,
        observation=observation,
        organism=_self_state(),
        action="rest",
        relative_map_mode="relative",
    )

    updated, receipt = predictive_control.update_after_transition(
        state,
        observation=observation,
        organism_before=_self_state(),
        action="rest",
        actual_outcome_type="rested",
        actual_delta={
            "energy": -0.012,
            "safety": 0.02,
            "connection": 0.0,
            "stimulation": 0.0,
        },
        terminal=False,
        resource_interaction=False,
        next_observation=observation,
        episode_index=0,
        relative_map_mode="relative",
        updates_enabled=True,
    )
    after = predictive_control.predict_action(
        updated,
        observation=observation,
        organism=_self_state(),
        action="rest",
        relative_map_mode="relative",
    )

    assert before["outcome_probabilities"]["rested"] == pytest.approx(1 / 6)
    assert after["outcome_probabilities"]["rested"] > before["outcome_probabilities"]["rested"]
    assert after["predicted_delta"]["energy"] < 0.0
    assert after["resource_interaction_probability"] < 0.5
    assert after["terminal_risk"] < 0.5
    assert receipt["applied"] is True
    assert receipt["update_count_after"] == 1
    assert receipt["model_hash_before"] != receipt["model_hash_after"]


def test_goal_counterfactual_changes_values_not_predictions() -> None:
    observation = _observation("v3")
    state = _prepared(predictive_control.empty_state(), observation)
    organism = _self_state(energy=0.20, stimulation=0.20)
    # Train two distinguishable visible consequences without passing a goal to
    # the predictor update path.
    for _ in range(8):
        state, _ = predictive_control.update_after_transition(
            state,
            observation=observation,
            organism_before=organism,
            action="interact",
            actual_outcome_type="interacted",
            actual_delta={
                "energy": 0.25,
                "safety": 0.0,
                "connection": 0.0,
                "stimulation": 0.01,
            },
            terminal=False,
            resource_interaction=True,
            next_observation=observation,
            episode_index=0,
            relative_map_mode="relative",
            updates_enabled=True,
        )
        state, _ = predictive_control.update_after_transition(
            state,
            observation=observation,
            organism_before=organism,
            action="turn_left",
            actual_outcome_type="turned",
            actual_delta={
                "energy": -0.014,
                "safety": 0.0,
                "connection": 0.0,
                "stimulation": 0.16,
            },
            terminal=False,
            resource_interaction=False,
            next_observation=observation,
            episode_index=0,
            relative_map_mode="relative",
            updates_enabled=True,
        )

    common = {
        "state": state,
        "observation": observation,
        "organism": organism,
        "heuristic_scores": {action: 0.0 for action in predictive_control.ACTIONS},
        "horizon": 1,
        "beam_width": 16,
        "discount": 0.97,
        "relative_map_mode": "relative",
        "goal_value_mode": "contextual",
        "action_costs": {
            "turn_left": 0.004,
            "turn_right": 0.004,
            "move_forward": 0.012,
            "interact": 0.008,
            "rest": 0.002,
        },
    }
    energy = predictive_control.plan_action(
        **common, active_goal="energy"
    )
    stimulation = predictive_control.plan_action(
        **common, active_goal="stimulation"
    )

    assert energy["predictions_by_action"] == stimulation["predictions_by_action"]
    assert energy["candidate_values"] != stimulation["candidate_values"]
    assert energy["selected_action"] == "interact"
    assert stimulation["selected_action"] == "turn_left"


def test_predictor_input_leakage_scanner_has_positive_control() -> None:
    valid = {
        "observation": _observation(),
        "organism": _self_state(),
        "belief_summary": {
            "relative_pose": [0, 0],
            "relative_facing": "N",
            "known_cell_count": 4,
            "known_object_count": 0,
            "front_token": "empty",
            "token_counts": {f"v{index}": 0 for index in range(5)},
        },
    }
    predictive_control.validate_predictor_input(valid)
    for forbidden in ("global_position", "cause", "token_mapping", "future_observation"):
        contaminated = deepcopy(valid)
        contaminated[forbidden] = "positive-control"
        with pytest.raises(predictive_control.PredictiveControlInvariantError):
            predictive_control.validate_predictor_input(contaminated)


def test_respawn_resets_relative_map_and_preserves_predictor() -> None:
    state = _prepared(predictive_control.empty_state(), _observation("v1"))
    state, _ = predictive_control.update_after_transition(
        state,
        observation=_observation("v1"),
        organism_before=_self_state(),
        action="interact",
        actual_outcome_type="interacted",
        actual_delta={
            "energy": 0.2,
            "safety": 0.0,
            "connection": 0.0,
            "stimulation": 0.0,
        },
        terminal=False,
        resource_interaction=True,
        next_observation=_observation("empty"),
        episode_index=0,
        relative_map_mode="relative",
        updates_enabled=True,
    )
    model_hash = predictive_control.model_hash(state)
    reset = predictive_control.reset_for_respawn(state, episode_index=1)
    assert reset["belief"]["cells"] == {}
    assert reset["belief"]["relative_pose"] == [0, 0]
    assert reset["model"]["update_count"] == 1
    assert predictive_control.model_hash(reset) == model_hash


def test_engine_factored_mode_updates_through_only_compute_step() -> None:
    state = engine.initial_state(run_id="factored-engine", seed=52)
    meta = engine.make_run_metadata("factored-engine", 711)
    interventions = dict(
        engine.DEFAULT_INTERVENTIONS,
        predictive_control_mode="factored_mpc",
    )
    command = engine.make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=interventions,
        prev_command_hash=None,
    )
    result = engine.compute_step(state, command, meta)

    receipt = result.trace["predictive_control"]
    assert receipt["mode"] == "factored_mpc"
    assert receipt["plan"]["selected_action"] == result.trace["selected_action"]
    assert set(receipt["plan"]["predictions_by_action"]) == set(engine.ACTIONS)
    assert set(receipt["plan"]["candidate_values"]) == set(engine.ACTIONS)
    assert len(receipt["plan"]["planned_actions"]) == 3
    assert receipt["update"]["applied"] is True
    assert result.next_state["predictive_control"]["model"]["update_count"] == 1
    assert result.trace["survival_learning"]["selection"]["selection_mode"] == "delegated_factored_mpc"


def test_engine_rejects_two_simultaneous_primary_learners() -> None:
    state = engine.initial_state(run_id="dual-primary")
    meta = engine.make_run_metadata("dual-primary", 711)
    interventions = dict(
        engine.DEFAULT_INTERVENTIONS,
        predictive_control_mode="factored_mpc",
        survival_learning_mode="expected_sarsa_lambda",
    )
    with pytest.raises(engine.EngineInvariantError, match="cannot both select"):
        engine.make_command(
            sequence=1,
            trigger_source="headless_acceptance",
            interventions=interventions,
            prev_command_hash=None,
        )


def test_frozen_predictor_updates_belief_but_not_model() -> None:
    state = engine.initial_state(run_id="frozen-predictor", seed=53)
    meta = engine.make_run_metadata("frozen-predictor", 712)
    interventions = dict(
        engine.DEFAULT_INTERVENTIONS,
        predictive_control_mode="factored_mpc",
        update_mode="frozen",
    )
    command = engine.make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=interventions,
        prev_command_hash=None,
    )
    result = engine.compute_step(state, command, meta)
    update = result.trace["predictive_control"]["update"]
    assert update["applied"] is False
    assert update["reason"] == "predictor_updates_frozen"
    assert update["model_hash_before"] == update["model_hash_after"]
    assert result.next_state["predictive_control"]["model"]["update_count"] == 0
    assert result.next_state["predictive_control"]["belief"]["observation_count"] >= 2


def test_sqlite_recovery_recomputes_predictive_state_and_rejects_trace_tamper(tmp_path) -> None:
    database = tmp_path / "factored.sqlite3"
    from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore

    with SQLiteEventStore(database) as store:
        controller = PlaygroundController(
            store,
            run_id="factored-replay",
            seed=711,
            world_seed=52,
            layout_id="p0_cross_v1",
        )
        interventions = dict(
            engine.DEFAULT_INTERVENTIONS,
            predictive_control_mode="factored_mpc",
            predictive_horizon_mode="h1",
        )
        for _ in range(4):
            dispatched = controller.dispatch(
                interventions,
                trigger_source="ui_run_button",
            )
            assert dispatched.receipt.committed
        online_hash = engine.canonical_hash(controller.state["predictive_control"])
        recovered = store.recover_run(controller.run_id)
        assert engine.canonical_hash(recovered.state["predictive_control"]) == online_hash
        row = store.connection.execute(
            "SELECT trace_json FROM traces WHERE run_id = ? AND sequence = 4",
            (controller.run_id,),
        ).fetchone()
        import json

        trace = json.loads(row["trace_json"])
        trace["predictive_control"]["update"]["outcome_brier"] = 0.0
        trace["trace_hash"] = engine.compute_trace_hash(trace)
        store.connection.execute(
            "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = 4",
            (
                engine.canonical_json(trace),
                trace["trace_hash"],
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="stored trace differs"):
            store.recover_run(controller.run_id)


def test_terminal_explicit_predictive_mode_reaches_controller_trace(tmp_path) -> None:
    from labs.ego_life_playground_v0.store import SQLiteEventStore
    from labs.ego_life_playground_v0.terminal import TerminalPlayground

    with SQLiteEventStore(tmp_path / "terminal-predictive.sqlite3") as store:
        controller = PlaygroundController(
            store,
            run_id="terminal-predictive",
            seed=711,
            world_seed=52,
        )
        terminal = TerminalPlayground(controller)
        enabled = terminal.execute("predictive on")
        assert enabled["predictive_control_mode"] == "factored_mpc"
        committed = terminal.execute("step")
        assert committed["status"] == "committed"
        assert controller.last_trace["trigger_source"] == "terminal_step"
        assert controller.last_trace["interventions"]["predictive_control_mode"] == "factored_mpc"
        assert controller.last_trace["predictive_control"]["plan"]["selected_action"] == controller.last_trace["selected_action"]
