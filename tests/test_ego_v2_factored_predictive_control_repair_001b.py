from __future__ import annotations

from collections import Counter
from copy import deepcopy
import inspect

import pytest

from labs.ego_life_playground_v0 import engine, predictive_control
from labs.ego_life_playground_v0.microworld import (
    PUBLIC_OBSERVATION_SCHEMA_VERSION,
    policy_observation,
)


def _visible_observation(front_token: str = "empty") -> dict:
    visual = [["empty" for _ in range(5)] for _ in range(5)]
    visual[2][2] = "self"
    visual[1][2] = front_token
    return {
        "schema_version": PUBLIC_OBSERVATION_SCHEMA_VERSION,
        "visual": visual,
    }


def _organism(*, energy: float = 0.2) -> dict[str, float]:
    return {
        "energy": energy,
        "safety": 0.7,
        "connection": 0.7,
        "stimulation": 0.7,
    }


def _complete_exploration(state: dict, *, identified_tokens: tuple[str, ...] = ()) -> dict:
    updated = deepcopy(state)
    updated["exploration"]["action_exposure_counts"] = {
        action: 4 for action in engine.ACTIONS
    }
    updated["exploration"]["token_interaction_counts"] = {
        f"v{index}": (2 if f"v{index}" in identified_tokens else 0)
        for index in range(5)
    }
    return updated


def _train_resource_token(token: str) -> tuple[dict, dict]:
    observation = _visible_observation(token)
    state = predictive_control.empty_state()
    for _ in range(16):
        state, _ = predictive_control.update_after_transition(
            state,
            observation=observation,
            organism_before=_organism(),
            action="interact",
            actual_outcome_type="interacted",
            actual_delta={
                "energy": 0.25,
                "safety": 0.0,
                "connection": 0.0,
                "stimulation": 0.0,
            },
            terminal=False,
            resource_interaction=True,
            next_observation=observation,
            episode_index=0,
            relative_map_mode="off",
            updates_enabled=True,
        )
    for _ in range(64):
        state, _ = predictive_control.update_after_transition(
            state,
            observation=_visible_observation("empty"),
            organism_before=_organism(),
            action="interact",
            actual_outcome_type="no_object",
            actual_delta={
                "energy": -0.01,
                "safety": 0.0,
                "connection": 0.0,
                "stimulation": 0.0,
            },
            terminal=False,
            resource_interaction=False,
            next_observation=_visible_observation("empty"),
            episode_index=0,
            relative_map_mode="off",
            updates_enabled=True,
        )
    return _complete_exploration(state, identified_tokens=(token,)), observation


def _factored_interventions(**overrides: str) -> dict[str, str]:
    value = dict(
        engine.DEFAULT_INTERVENTIONS,
        predictive_control_mode="factored_mpc",
    )
    value.update(overrides)
    return value


def _run_actions(*, limit: int = 32, update_mode: str = "canonical"):
    run_id = f"repair-coverage-{update_mode}"
    state = engine.initial_state(run_id=run_id, seed=52, layout_id="p0_cross_v1")
    meta = engine.make_run_metadata(run_id, 711)
    interventions = _factored_interventions(update_mode=update_mode)
    traces = []
    while len([trace for trace in traces if trace.get("selected_action")]) < limit:
        command = engine.make_command(
            sequence=int(state["clock"]["global_tick"]) + 1,
            trigger_source="headless_acceptance",
            interventions=interventions,
            prev_command_hash=state["last_command_hash"],
        )
        result = engine.compute_step(state, command, meta)
        state = result.next_state
        traces.append(result.trace)
    return state, traces


def test_bounded_exploration_covers_all_atomic_actions_before_exploitation() -> None:
    state, traces = _run_actions()
    selected = [trace["selected_action"] for trace in traces if trace.get("selected_action")]
    first_twenty = Counter(selected[:20])

    assert first_twenty == Counter({action: 4 for action in engine.ACTIONS})
    assert set(selected[:32]) == set(engine.ACTIONS)
    assert state["predictive_control"]["exploration"]["coverage_step"] == 32
    assert any(
        trace["predictive_control"]["plan"]["selection_mode"] == "mpc_exploit"
        for trace in traces[20:]
        if trace["predictive_control"]["plan"] is not None
    )


def test_frozen_predictor_keeps_model_hash_but_shares_exposure_schedule() -> None:
    online_state, online = _run_actions(update_mode="canonical")
    frozen_state, frozen = _run_actions(update_mode="frozen")

    assert online_state["predictive_control"]["exploration"] == frozen_state[
        "predictive_control"
    ]["exploration"]
    assert online_state["predictive_control"]["model"]["update_count"] == 32
    assert frozen_state["predictive_control"]["model"]["update_count"] == 0
    assert predictive_control.model_hash(frozen_state["predictive_control"]) == predictive_control.model_hash(
        predictive_control.empty_state()
    )
    assert [item["selected_action"] for item in online[:20]] == [
        item["selected_action"] for item in frozen[:20]
    ]


def test_real_beam_has_global_width_root_coverage_and_no_fixed_templates() -> None:
    source = inspect.getsource(predictive_control)
    assert "template_bank" not in source
    assert "_most_likely_outcome" not in source

    state = engine.initial_state(run_id="repair-beam", seed=52)
    observation = policy_observation(state["world"])
    prepared, _ = predictive_control.observe_belief(
        state["predictive_control"],
        observation=observation,
        episode_index=0,
        mode="relative",
    )
    plan = predictive_control.plan_action(
        state=prepared,
        observation=observation,
        organism=state["organism"],
        active_goal="energy",
        heuristic_scores={action: 0.0 for action in engine.ACTIONS},
        horizon=3,
        beam_width=16,
        discount=0.97,
        relative_map_mode="relative",
        goal_value_mode="contextual",
        action_costs=engine.ACTION_COSTS,
        run_seed=711,
        episode_index=0,
        sequence=1,
    )

    assert plan["beam_receipt"]["expanded_by_depth"] == [5, 25, 80]
    assert plan["beam_receipt"]["retained_by_depth"] == [5, 16, 16]
    assert all(
        roots == list(engine.ACTIONS)
        for roots in plan["beam_receipt"]["root_actions_by_depth"]
    )
    assert plan["beam_receipt"]["all_probability_mass_normalized"] is True


def test_heuristic_scores_are_only_an_exact_value_tie_break() -> None:
    state = engine.initial_state(run_id="repair-tie", seed=52)
    observation = policy_observation(state["world"])
    prepared, _ = predictive_control.observe_belief(
        state["predictive_control"], observation=observation, episode_index=0, mode="relative"
    )
    common = dict(
        state=prepared,
        observation=observation,
        organism=state["organism"],
        active_goal="energy",
        horizon=3,
        beam_width=16,
        discount=0.97,
        relative_map_mode="relative",
        goal_value_mode="contextual",
        action_costs=engine.ACTION_COSTS,
        run_seed=711,
        episode_index=0,
        sequence=21,
    )
    neutral = {action: 0.0 for action in engine.ACTIONS}
    hostile = dict(neutral, interact=1_000_000.0, turn_left=-1_000_000.0)
    first = predictive_control.plan_action(**common, heuristic_scores=neutral)
    second = predictive_control.plan_action(**common, heuristic_scores=hostile)

    if len({item["total"] for item in first["candidate_values"].values()}) > 1:
        assert first["selected_action"] == second["selected_action"]
        assert first["tie_break_used"] is False


def test_goal_counterfactual_keeps_predictions_equal_after_repair() -> None:
    state = engine.initial_state(run_id="repair-goal", seed=52)
    observation = policy_observation(state["world"])
    prepared, _ = predictive_control.observe_belief(
        state["predictive_control"], observation=observation, episode_index=0, mode="relative"
    )
    common = dict(
        state=prepared,
        observation=observation,
        organism=state["organism"],
        heuristic_scores={action: 0.0 for action in engine.ACTIONS},
        horizon=1,
        beam_width=16,
        discount=0.97,
        relative_map_mode="relative",
        goal_value_mode="contextual",
        action_costs=engine.ACTION_COSTS,
        run_seed=711,
        episode_index=0,
        sequence=21,
    )
    energy = predictive_control.plan_action(**common, active_goal="energy")
    stimulation = predictive_control.plan_action(**common, active_goal="stimulation")

    assert energy["predictions_by_action"] == stimulation["predictions_by_action"]
    assert energy["predictor_input_goal_independent"] is True


def test_expected_pose_value_uses_probability_mass_not_modal_outcome() -> None:
    belief = predictive_control.empty_state()["belief"]
    belief["cells"] = {
        f"{x},{y}": "empty" for y in range(-2, 3) for x in range(-2, 3)
    }
    receipt = predictive_control.expected_pose_receipt(
        belief=belief,
        pose=(0, 0),
        facing="N",
        action="move_forward",
        outcome_probabilities={
            "moved": 0.25,
            "blocked": 0.75,
            "interacted": 0.0,
            "no_object": 0.0,
            "rested": 0.0,
            "turned": 0.0,
        },
    )

    assert receipt["successor_distribution"] == [
        [0, -1, "N", 0.25],
        [0, 0, "N", 0.75],
    ]
    assert receipt["expected_newly_observable_unknown_fraction"] == pytest.approx(0.05)
    assert receipt["map_information_value"] == pytest.approx(0.01)


def test_predictor_input_leakage_scanner_has_positive_control() -> None:
    observation = _visible_observation("v3")
    state = predictive_control.empty_state()
    prepared, _ = predictive_control.observe_belief(
        state, observation=observation, episode_index=0, mode="relative"
    )
    clean_payload = {
        "observation": observation,
        "organism": _organism(),
        "belief_summary": predictive_control.predictor_input_snapshot(
            prepared,
            observation=observation,
            organism=_organism(),
            relative_map_mode="relative",
        )["belief_summary"],
    }
    clean = predictive_control.scan_predictor_input_leakage(clean_payload)
    assert clean["clean"] is True
    assert clean["findings"] == []

    contaminated = deepcopy(clean_payload)
    contaminated["global_position"] = [4, 3]
    contaminated["cause"] = "resource"
    contaminated["token_mapping"] = {"v3": "resource"}
    contaminated["seed"] = 52
    contaminated["future_observation"] = observation
    positive = predictive_control.scan_predictor_input_leakage(contaminated)
    assert positive["clean"] is False
    assert {item["field"] for item in positive["findings"]} == {
        "cause",
        "future_observation",
        "global_position",
        "seed",
        "token_mapping",
    }
    with pytest.raises(predictive_control.PredictiveControlInvariantError):
        predictive_control.validate_predictor_input(contaminated)


@pytest.mark.parametrize("resource_token", ["v1", "v3"])
def test_learned_resource_receipts_select_interact_without_token_name_rule(
    resource_token: str,
) -> None:
    state, observation = _train_resource_token(resource_token)
    prepared, _ = predictive_control.observe_belief(
        state, observation=observation, episode_index=0, mode="relative"
    )
    plan = predictive_control.plan_action(
        state=prepared,
        observation=observation,
        organism=_organism(energy=0.2),
        active_goal="energy",
        heuristic_scores={action: 0.0 for action in engine.ACTIONS},
        horizon=1,
        beam_width=16,
        discount=0.97,
        relative_map_mode="relative",
        goal_value_mode="contextual",
        action_costs=engine.ACTION_COSTS,
        run_seed=721,
        episode_index=0,
        sequence=40,
    )

    assert plan["selection_mode"] == "mpc_exploit"
    assert plan["selected_action"] == "interact"
    assert plan["candidate_values"]["interact"]["homeostatic_value"] > 0.0


def test_relative_resource_position_changes_the_planned_path() -> None:
    state, observation = _train_resource_token("v3")
    for action, outcome in (
        ("move_forward", "moved"),
        ("turn_left", "turned"),
        ("turn_right", "turned"),
        ("rest", "rested"),
    ):
        for _ in range(64):
            state, _ = predictive_control.update_after_transition(
                state,
                observation=_visible_observation("empty"),
                organism_before=_organism(),
                action=action,
                actual_outcome_type=outcome,
                actual_delta={
                    "energy": -0.01,
                    "safety": 0.0,
                    "connection": 0.0,
                    "stimulation": 0.0,
                },
                terminal=False,
                resource_interaction=False,
                next_observation=_visible_observation("empty"),
                episode_index=0,
                relative_map_mode="off",
                updates_enabled=True,
            )
    state = _complete_exploration(state, identified_tokens=("v3",))
    common = dict(
        observation=_visible_observation("empty"),
        organism=_organism(energy=0.2),
        active_goal="energy",
        heuristic_scores={action: 0.0 for action in engine.ACTIONS},
        horizon=4,
        beam_width=16,
        discount=0.97,
        relative_map_mode="relative",
        goal_value_mode="contextual",
        action_costs=engine.ACTION_COSTS,
        run_seed=721,
        episode_index=0,
        sequence=80,
    )
    north = deepcopy(state)
    north["belief"]["cells"] = {"0,-2": "v3"}
    east = deepcopy(state)
    east["belief"]["cells"] = {"2,0": "v3"}

    north_plan = predictive_control.plan_action(state=north, **common)
    east_plan = predictive_control.plan_action(state=east, **common)

    assert north_plan["planned_actions"] != east_plan["planned_actions"]
    assert north_plan["planned_actions"][0] == "move_forward"
    assert east_plan["planned_actions"][0] == "turn_right"
