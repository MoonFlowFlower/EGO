from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.engine import (
    DEFAULT_INTERVENTIONS,
    compute_step,
    initial_state,
    make_command,
    make_run_metadata,
)
from labs.ego_life_playground_v0.microworld import policy_observation, verify_world_state
from labs.ego_life_playground_v0.store import SQLiteEventStore
from labs.ego_life_playground_v0.terminal import build_terminal_snapshot
from labs.ego_life_playground_v0.visual_console import build_tk_trace_payload
from labs.ego_life_playground_v0.visual_console import build_chinese_causal_view


def _observation_hash(observation: dict[str, object]) -> str:
    from labs.ego_life_playground_v0.engine import canonical_hash

    return canonical_hash(observation)


def _step(state, *, run_id="goal-test", interventions=None):
    if int(state["clock"]["global_tick"]) == 0:
        state["component_hashes"]["model"] = _observation_hash(state["model"])
        state["component_hashes"]["memory"] = _observation_hash(state["memory"])
    meta = make_run_metadata(run_id, 17)
    command = make_command(
        sequence=state["clock"]["global_tick"] + 1,
        trigger_source="headless_acceptance",
        interventions=interventions or DEFAULT_INTERVENTIONS,
        prev_command_hash=state["last_command_hash"],
    )
    return compute_step(deepcopy(state), command, meta)


def _state_with_resource_ahead(
    *,
    run_id: str,
    organism: dict[str, float],
) -> dict[str, object]:
    state = initial_state(organism, run_id=run_id)
    world = deepcopy(state["world"])
    world["agent"]["position"] = [4, 2]
    world["agent"]["facing"] = "N"
    world["objects_by_cause"]["resource"]["position"] = [4, 1]
    world["objects_by_cause"]["social"]["position"] = [1, 1]
    world["objects_by_cause"]["novelty"]["position"] = [7, 1]
    world["objects_by_cause"]["threat"]["position"] = [2, 3]
    world["objects_by_cause"]["shelter"]["position"] = [6, 3]
    verify_world_state(world)
    state["world"] = world
    return state


def _state_with_empty_front(
    *,
    run_id: str,
    organism: dict[str, float],
) -> dict[str, object]:
    state = _state_with_resource_ahead(run_id=run_id, organism=organism)
    world = deepcopy(state["world"])
    world["objects_by_cause"]["resource"]["position"] = [1, 3]
    verify_world_state(world)
    state["world"] = world
    return state


def _set_goal_model(
    state: dict[str, object],
    *,
    goal_key: str,
    action: str,
    ema_delta: dict[str, float],
) -> None:
    observation = policy_observation(state["world"])
    observation_hash = _observation_hash(observation)
    state["current_goal"]["state_variable"] = goal_key
    state["current_goal"]["status"] = "active"
    state["current_goal"]["entry_deficit"] = round(0.72 - state["organism"][goal_key], 6)
    state["model"] = {
        f"{observation_hash}|{goal_key}": {
            action: {
                "count": 1,
                "ema_delta": deepcopy(ema_delta),
            }
        }
    }


def test_goal_hysteresis_carries_active_target_until_completion() -> None:
    state = _state_with_empty_front(
        run_id="goal-carry",
        organism={
            "energy": 0.50,
            "safety": 0.30,
            "connection": 0.74,
            "stimulation": 0.74,
        },
    )
    _set_goal_model(
        state,
        goal_key="energy",
        action="rest",
        ema_delta={"energy": 0.0, "safety": 0.20, "connection": 0.0, "stimulation": 0.0},
    )

    result = _step(state, run_id="goal-carry")

    assert result.trace["goal_before"]["state_variable"] == "energy"
    assert result.trace["goal_after"]["state_variable"] == "energy"
    assert result.trace["goal_transition"]["kind"] == "carried_active_goal"
    assert result.trace["goal_transition"]["reason"] == "hysteresis_carry"
    assert result.trace["goal_progress"]["eligible_body_goals"] == ["safety"]
    assert result.trace["goal_after"]["selected_global_tick"] == result.trace["goal_before"][
        "selected_global_tick"
    ]
    assert result.trace["goal_after"]["entry_deficit"] == result.trace["goal_before"][
        "entry_deficit"
    ]
    assert set(result.trace["goal_progress"]["variable_states_before"]) == {
        "energy",
        "safety",
        "connection",
        "stimulation",
    }
    assert result.trace["goal_progress"]["variable_states_after"]["energy"] == {
        "value": result.next_state["organism"]["energy"],
        "deficit": round(max(0.0, 0.72 - result.next_state["organism"]["energy"]), 6),
        "latched": False,
        "eligible": True,
        "severe": False,
    }


def test_goal_completion_latches_and_reenters_below_reentry_threshold() -> None:
    state = _state_with_resource_ahead(
        run_id="goal-latch",
        organism={
            "energy": 0.71,
            "safety": 0.74,
            "connection": 0.74,
            "stimulation": 0.74,
        },
    )
    _set_goal_model(
        state,
        goal_key="energy",
        action="interact",
        ema_delta={"energy": 0.40, "safety": 0.0, "connection": 0.0, "stimulation": 0.0},
    )

    completed = _step(state, run_id="goal-latch")

    assert completed.trace["goal_progress"]["completed"] is True
    assert completed.trace["goal_progress"]["completed_latches_after"]["energy"] is True
    assert completed.trace["goal_after"]["status"] == "explore"
    assert completed.trace["goal_transition"]["kind"] == "completed_goal_to_explore"

    reentry_state = deepcopy(completed.next_state)
    reentry_state["organism"]["energy"] = 0.59

    reentered = _step(reentry_state, run_id="goal-latch")

    assert reentered.trace["goal_after"]["state_variable"] == "energy"
    assert reentered.trace["goal_transition"]["kind"] == "reentry"
    assert reentered.trace["goal_transition"]["reason"] == "reentry_below_threshold"
    assert reentered.trace["goal_progress"]["reentered_variables"] == ["energy"]


def test_energy_severe_override_has_priority_over_other_severe_variables() -> None:
    state = _state_with_empty_front(
        run_id="goal-override",
        organism={
            "energy": 0.14,
            "safety": 0.05,
            "connection": 0.20,
            "stimulation": 0.74,
        },
    )
    _set_goal_model(
        state,
        goal_key="connection",
        action="rest",
        ema_delta={"energy": 0.0, "safety": 0.10, "connection": 0.0, "stimulation": 0.0},
    )

    result = _step(state, run_id="goal-override")

    assert result.trace["goal_after"]["state_variable"] == "energy"
    assert result.trace["goal_transition"]["kind"] == "critical_override"
    assert result.trace["goal_transition"]["reason"] == "critical_override_energy"
    assert result.trace["goal_progress"]["severe_variables_after"] == ["energy", "safety"]


def test_explore_uses_visual_transition_counts_and_no_novelty_ablation_is_load_bearing() -> None:
    state = _state_with_resource_ahead(
        run_id="goal-explore",
        organism={
            "energy": 0.74,
            "safety": 0.74,
            "connection": 0.74,
            "stimulation": 0.74,
        },
    )
    observation = policy_observation(state["world"])
    observation_hash = _observation_hash(observation)
    state["current_goal"]["state_variable"] = None
    state["current_goal"]["status"] = "explore"
    state["current_goal"]["entry_deficit"] = 0.0
    state["model"] = {
        "__visual_transition_counts__": {
            observation_hash: {
                "turn_left": {"total": 8, "next_counts": {"a" * 64: 8}},
                "turn_right": {"total": 8, "next_counts": {"b" * 64: 8}},
                "move_forward": {"total": 8, "next_counts": {"c" * 64: 8}},
                "rest": {"total": 8, "next_counts": {"d" * 64: 8}},
                "interact": {"total": 0, "next_counts": {}},
            }
        }
    }

    canonical = _step(state, run_id="goal-explore")
    ablated = _step(
        state,
        run_id="goal-explore",
        interventions=dict(DEFAULT_INTERVENTIONS, novelty_mode="no_novelty"),
    )

    assert canonical.trace["goal_before"]["status"] == "explore"
    assert canonical.trace["selected_action"] == "interact"
    assert canonical.trace["goal_transition"]["kind"] == "explore_carried"
    assert canonical.trace["goal_transition"]["changed"] is False
    assert (
        canonical.trace["goal_after"]["selected_global_tick"]
        == canonical.trace["goal_before"]["selected_global_tick"]
    )
    interact_candidate = next(
        item for item in canonical.trace["candidates"] if item["action"] == "interact"
    )
    assert interact_candidate["explore_score"] > 0.0
    assert interact_candidate["novelty_total_count"] == 0
    assert canonical.trace["goal_progress"]["novelty_counter_hash_before"]

    assert ablated.trace["selected_action"] != canonical.trace["selected_action"]
    assert all(item["explore_score"] == 0.0 for item in ablated.trace["candidates"])


def test_no_hysteresis_and_no_override_ablations_change_real_goal_selection() -> None:
    hysteresis_state = _state_with_empty_front(
        run_id="goal-ablate-hyst",
        organism={
            "energy": 0.50,
            "safety": 0.30,
            "connection": 0.74,
            "stimulation": 0.74,
        },
    )
    _set_goal_model(
        hysteresis_state,
        goal_key="energy",
        action="rest",
        ema_delta={"energy": 0.0, "safety": 0.20, "connection": 0.0, "stimulation": 0.0},
    )
    canonical = _step(hysteresis_state, run_id="goal-ablate-hyst")
    no_hysteresis = _step(
        hysteresis_state,
        run_id="goal-ablate-hyst",
        interventions=dict(DEFAULT_INTERVENTIONS, hysteresis_mode="no_hysteresis"),
    )
    assert canonical.trace["goal_after"]["state_variable"] == "energy"
    assert no_hysteresis.trace["goal_after"]["state_variable"] == "safety"
    assert no_hysteresis.trace["goal_transition"]["reason"] == "ablation_max_deficit_retarget"

    override_state = _state_with_empty_front(
        run_id="goal-ablate-override",
        organism={
            "energy": 0.14,
            "safety": 0.05,
            "connection": 0.20,
            "stimulation": 0.74,
        },
    )
    _set_goal_model(
        override_state,
        goal_key="connection",
        action="rest",
        ema_delta={"energy": 0.0, "safety": 0.10, "connection": 0.0, "stimulation": 0.0},
    )
    no_override = _step(
        override_state,
        run_id="goal-ablate-override",
        interventions=dict(DEFAULT_INTERVENTIONS, override_mode="no_override"),
    )
    assert no_override.trace["goal_after"]["state_variable"] == "connection"
    assert no_override.trace["goal_transition"]["reason"] != "critical_override_energy"


def test_goal_reasons_are_rendered_from_recovered_trace_only(tmp_path: Path) -> None:
    db_path = tmp_path / "goal-ui.db"
    store = SQLiteEventStore(db_path)
    controller = PlaygroundController(store, run_id="goal-ui", seed=17, world_seed=17)
    try:
        controller.dispatch(trigger_source="ui_step_button")
        frame = controller.recovery.frames[-1]
        terminal_snapshot = build_terminal_snapshot(controller)
        payload = build_tk_trace_payload(frame.state, frame.trace)

        assert terminal_snapshot["goal_trace"]["goal_transition"] == frame.trace["goal_transition"]
        assert terminal_snapshot["goal_trace"]["goal_progress"] == frame.trace["goal_progress"]
        assert payload["goal_transition"] == frame.trace["goal_transition"]
        assert payload["goal_progress"] == frame.trace["goal_progress"]
        assert payload["goal_before"] == frame.trace["goal_before"]
        assert payload["goal_after"] == frame.trace["goal_after"]
        chinese = build_chinese_causal_view(frame)
        assert chinese["目标仲裁"]["切换原因"] == frame.trace["goal_transition"]["reason"]
        assert chinese["目标仲裁"]["迟滞状态"] == frame.trace["goal_progress"][
            "completed_latches_after"
        ]
    finally:
        store.close()


def test_initial_severe_energy_is_selected_before_first_policy_decision() -> None:
    state = initial_state(
        {
            "energy": 0.14,
            "safety": 0.05,
            "connection": 0.40,
            "stimulation": 0.40,
        },
        run_id="goal-initial-severe",
    )

    assert state["current_goal"]["state_variable"] == "energy"
    assert state["current_goal"]["selection_reason"] == "critical_override_energy"
    result = _step(state, run_id="goal-initial-severe")
    assert result.trace["goal_before"]["state_variable"] == "energy"


def test_critical_override_threshold_is_inclusive_without_masking_actions() -> None:
    exact = initial_state(
        {
            "energy": 0.15,
            "safety": 0.05,
            "connection": 0.40,
            "stimulation": 0.40,
        },
        run_id="goal-critical-exact",
    )
    above = initial_state(
        {
            "energy": 0.150001,
            "safety": 0.80,
            "connection": 0.80,
            "stimulation": 0.80,
        },
        run_id="goal-critical-above",
    )

    assert exact["current_goal"]["state_variable"] == "energy"
    assert exact["current_goal"]["selection_reason"] == "critical_override_energy"
    assert above["current_goal"]["selection_reason"] == "initial_deficit_priority"

    result = _step(exact, run_id="goal-critical-exact")
    assert {item["action"] for item in result.trace["candidates"]} == {
        "turn_left",
        "turn_right",
        "move_forward",
        "interact",
        "rest",
    }


def test_no_hysteresis_rearms_a_completed_variable_before_point_six() -> None:
    state = _state_with_empty_front(
        run_id="goal-no-hyst-rearm",
        organism={
            "energy": 0.69,
            "safety": 0.74,
            "connection": 0.74,
            "stimulation": 0.74,
        },
    )
    state["current_goal"].update(
        {
            "state_variable": None,
            "status": "explore",
            "entry_deficit": 0.0,
            "selection_reason": "explore_no_eligible_body_goal",
            "completed_latches": {
                "energy": True,
                "safety": True,
                "connection": True,
                "stimulation": True,
            },
        }
    )

    canonical = _step(state, run_id="goal-no-hyst-rearm")
    ablated = _step(
        state,
        run_id="goal-no-hyst-rearm",
        interventions=dict(DEFAULT_INTERVENTIONS, hysteresis_mode="no_hysteresis"),
    )

    assert canonical.trace["goal_after"]["status"] == "explore"
    assert ablated.trace["goal_after"]["state_variable"] == "energy"
    assert ablated.trace["goal_after"]["completed_latches"]["energy"] is False


def test_reentry_threshold_is_strictly_below_point_six() -> None:
    def completed_explore_state(connection: float, run_id: str):
        state = _state_with_empty_front(
            run_id=run_id,
            organism={
                "energy": 0.80,
                "safety": 0.80,
                "connection": connection,
                "stimulation": 0.80,
            },
        )
        state["current_goal"].update(
            {
                "state_variable": None,
                "status": "explore",
                "entry_deficit": 0.0,
                "selection_reason": "explore_no_eligible_body_goal",
                "completed_latches": {
                    "energy": True,
                    "safety": True,
                    "connection": True,
                    "stimulation": True,
                },
            }
        )
        return state

    exact = _step(
        completed_explore_state(0.60, "goal-reentry-exact"),
        run_id="goal-reentry-exact",
    )
    below = _step(
        completed_explore_state(0.599999, "goal-reentry-below"),
        run_id="goal-reentry-below",
    )

    assert exact.trace["goal_after"]["status"] == "explore"
    assert exact.trace["goal_progress"]["reentered_variables"] == []
    assert below.trace["goal_after"]["state_variable"] == "connection"
    assert below.trace["goal_transition"]["reason"] == "reentry_below_threshold"


def test_completion_switch_to_another_body_goal_has_completion_reason() -> None:
    state = _state_with_resource_ahead(
        run_id="goal-complete-switch",
        organism={
            "energy": 0.50,
            "safety": 0.50,
            "connection": 0.74,
            "stimulation": 0.74,
        },
    )
    _set_goal_model(
        state,
        goal_key="energy",
        action="interact",
        ema_delta={"energy": 0.40, "safety": 0.0, "connection": 0.0, "stimulation": 0.0},
    )

    result = _step(state, run_id="goal-complete-switch")

    assert result.trace["goal_progress"]["completed"] is True
    assert result.trace["goal_after"]["state_variable"] == "safety"
    assert result.trace["goal_transition"] == {
        "changed": True,
        "kind": "completed_goal_to_body_goal",
        "reason": "previous_goal_completed",
    }


def test_explore_context_is_explicit_and_uncertainty_increases_score() -> None:
    state = _state_with_empty_front(
        run_id="goal-explore-context",
        organism={
            "energy": 0.74,
            "safety": 0.74,
            "connection": 0.74,
            "stimulation": 0.74,
        },
    )
    observation_hash = _observation_hash(policy_observation(state["world"]))
    state["current_goal"].update(
        {
            "state_variable": None,
            "status": "explore",
            "entry_deficit": 0.0,
            "selection_reason": "explore_no_eligible_body_goal",
        }
    )
    state["model"] = {
        "__visual_transition_counts__": {
            observation_hash: {
                "turn_left": {"total": 4, "next_counts": {"a" * 64: 4}},
                "turn_right": {
                    "total": 4,
                    "next_counts": {"b" * 64: 2, "c" * 64: 2},
                },
            }
        }
    }

    result = _step(state, run_id="goal-explore-context")
    by_action = {item["action"]: item for item in result.trace["candidates"]}

    assert result.trace["context_key"].endswith("|explore")
    assert by_action["turn_right"]["explore_uncertainty"] > by_action["turn_left"][
        "explore_uncertainty"
    ]
    assert by_action["turn_right"]["explore_score"] > by_action["turn_left"][
        "explore_score"
    ]
    assert (
        result.trace["goal_progress"]["novelty_counter_hash_after"]
        != result.trace["goal_progress"]["novelty_counter_hash_before"]
    )
