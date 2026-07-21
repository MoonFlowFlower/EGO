from __future__ import annotations

from copy import deepcopy

import pytest

from labs.ego_life_playground_v0 import engine, microworld
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore


def _step(
    state: dict,
    meta: dict,
    *,
    injected_event: str | None = None,
    trigger_source: str = "headless_acceptance",
) -> tuple[engine.StepResult, dict]:
    command = engine.make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        injected_event=injected_event,
        trigger_source=trigger_source,
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=state["last_command_hash"],
    )
    return engine.compute_step(state, command, meta), command


def _state_with_front(
    run_id: str,
    seed: int,
    *,
    front_cause: str | None,
    organism: dict[str, float] | None = None,
) -> dict:
    state = engine.initial_state(
        organism
        or {
            "energy": 0.4,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.9,
        },
        run_id=run_id,
        seed=seed,
    )
    world = deepcopy(state["world"])
    world["agent"]["position"] = [4, 2]
    world["agent"]["facing"] = "N"
    positions = {
        "resource": [1, 1],
        "social": [2, 1],
        "novelty": [6, 1],
        "threat": [1, 3],
        "shelter": [7, 3],
    }
    if front_cause is not None:
        if front_cause not in microworld.CAUSES:
            raise AssertionError(f"non-canonical fixture cause: {front_cause}")
        displaced = positions[front_cause]
        positions[front_cause] = [4, 1]
        for cause in microworld.CAUSES:
            if cause != front_cause and positions[cause] == [4, 1]:
                positions[cause] = displaced
                break
    for cause, position in positions.items():
        world["objects_by_cause"][cause]["position"] = position
    microworld.verify_world_state(world)
    state["world"] = world
    return state


def _force_action(state: dict, action: str) -> None:
    assert action in microworld.ACTIONS
    observation = microworld.policy_observation(state["world"])
    observation_key = microworld.observation_hash(observation)
    goal_key = (
        str(state["current_goal"]["state_variable"])
        if state["current_goal"]["status"] == "active"
        else "explore"
    )
    rewarded_variable = goal_key if goal_key in engine.STATE_KEYS else "energy"
    predicted_delta = {key: 0.0 for key in engine.STATE_KEYS}
    predicted_delta[rewarded_variable] = 1.0
    state["model"] = {
        f"{observation_key}|{goal_key}": {
            action: {"count": 1, "ema_delta": predicted_delta}
        }
    }
    state["component_hashes"]["model"] = engine.canonical_hash(state["model"])


def _assert_ledger_reconciles(trace: dict) -> None:
    expected_after = round(
        max(
            0.0,
            min(
                1.0,
                trace["energy_before"]
                - trace["passive_decay"]
                - trace["action_cost"]
                + trace["food_gain"],
            ),
        ),
        6,
    )
    metabolism = trace["metabolism"]
    assert trace["energy_after"] == pytest.approx(expected_after)
    assert trace["actual_delta"]["energy"] == pytest.approx(
        trace["energy_after"] - trace["energy_before"]
    )
    assert metabolism["energy_before"] == trace["energy_before"]
    assert metabolism["energy_after"] == trace["energy_after"]
    assert metabolism["selected_action"] == trace["selected_action"]
    assert metabolism["food_obtained"] is (trace["food_gain"] > 0.0)
    assert metabolism["producer_function"] == engine.METABOLISM_PRODUCER_FUNCTION
    assert metabolism["aggregation_rule"] == engine.METABOLISM_AGGREGATION_RULE
    assert metabolism["code_path_hash"] == trace["code_path_hash"]
    assert metabolism["input_artifacts"][0] == f"run:{trace['run_id']}"
    assert metabolism["input_artifacts"][1] == f"command:{trace['command_hash']}"


@pytest.mark.parametrize(
    ("action", "outcome_type"),
    [
        ("turn_left", "turned"),
        ("turn_right", "turned"),
        ("move_forward", "moved"),
        ("interact", "no_object"),
        ("rest", "rested"),
    ],
)
def test_every_local_action_pays_passive_decay_and_its_exact_cost(
    action: str, outcome_type: str
) -> None:
    run_id = f"metabolism-five-actions-{action}"
    state = _state_with_front(run_id, 17, front_cause=None)
    meta = engine.make_run_metadata(run_id, 17)
    world_before = deepcopy(state["world"])
    _force_action(state, action)

    result, command = _step(state, meta)
    trace = result.trace

    assert command["injected_event"] is None
    assert trace["selected_action"] == action
    assert trace["candidate_actions"] == list(microworld.ACTIONS)
    assert {item["action"] for item in trace["candidates"]} == set(
        microworld.ACTIONS
    )
    assert all("selection_eligible" not in item for item in trace["candidates"])
    assert trace["world_transition"]["outcome_type"] == outcome_type
    assert trace["food_gain"] == 0.0
    assert trace["passive_decay"] == engine.PASSIVE_ENERGY_DECAY_PER_TICK
    assert trace["action_cost"] == engine.ACTION_COSTS[action]
    assert trace["energy_after"] == pytest.approx(
        trace["energy_before"]
        - engine.PASSIVE_ENERGY_DECAY_PER_TICK
        - engine.ACTION_COSTS[action]
    )
    assert result.next_state["lifecycle"]["trial_status"] == "active"
    assert result.next_state["organism"]["energy"] > 0.0
    _assert_ledger_reconciles(trace)

    if action == "turn_left":
        assert result.next_state["world"]["agent"]["facing"] == "W"
        assert result.next_state["world"]["agent"]["position"] == [4, 2]
    elif action == "turn_right":
        assert result.next_state["world"]["agent"]["facing"] == "E"
        assert result.next_state["world"]["agent"]["position"] == [4, 2]
    elif action == "move_forward":
        assert result.next_state["world"]["agent"]["position"] == [4, 1]
    else:
        assert result.next_state["world"] == world_before


def test_interact_requires_an_immediately_forward_object_for_resource_gain() -> None:
    run_id = "metabolism-front-cell-negative"
    state = _state_with_front(run_id, 17, front_cause=None)
    meta = engine.make_run_metadata(run_id, 17)
    resource_before = deepcopy(state["world"]["objects_by_cause"]["resource"])
    _force_action(state, "interact")

    result, _ = _step(state, meta)

    assert result.trace["observation"]["visual"][1][2] == "empty"
    assert result.trace["selected_action"] == "interact"
    assert result.trace["world_transition"] == {"outcome_type": "no_object"}
    assert result.next_state["world"]["objects_by_cause"]["resource"] == resource_before
    assert result.trace["food_gain"] == 0.0
    assert result.trace["energy_after"] == pytest.approx(0.382)
    _assert_ledger_reconciles(result.trace)


def test_forward_resource_interaction_produces_exact_food_gain() -> None:
    run_id = "metabolism-front-resource"
    state = _state_with_front(run_id, 18, front_cause="resource")
    meta = engine.make_run_metadata(run_id, 18)
    resource_token = state["world"]["objects_by_cause"]["resource"]["token"]
    resource_spawn_before = state["world"]["objects_by_cause"]["resource"][
        "spawn_count"
    ]
    _force_action(state, "interact")

    result, _ = _step(state, meta)

    assert result.trace["observation"]["visual"][1][2] == resource_token
    assert result.trace["selected_action"] == "interact"
    assert result.trace["world_transition"] == {
        "outcome_type": "interacted",
        "cause": "resource",
        "token": resource_token,
    }
    assert (
        result.next_state["world"]["objects_by_cause"]["resource"]["spawn_count"]
        == resource_spawn_before + 1
    )
    assert result.trace["food_gain"] == engine.CAUSE_DELTAS["resource"]["energy"]
    assert result.trace["food_gain"] == 0.28
    assert result.trace["energy_after"] == pytest.approx(0.662)
    assert result.next_state["organism"]["energy"] == pytest.approx(0.662)
    _assert_ledger_reconciles(result.trace)


def test_forward_non_resource_interaction_changes_body_but_not_energy_gain() -> None:
    run_id = "metabolism-front-social"
    state = _state_with_front(
        run_id,
        17,
        front_cause="social",
        organism={
            "energy": 0.4,
            "safety": 0.9,
            "connection": 0.4,
            "stimulation": 0.9,
        },
    )
    meta = engine.make_run_metadata(run_id, 17)
    social_token = state["world"]["objects_by_cause"]["social"]["token"]
    _force_action(state, "interact")

    result, _ = _step(state, meta)

    assert result.trace["observation"]["visual"][1][2] == social_token
    assert result.trace["world_transition"] == {
        "outcome_type": "interacted",
        "cause": "social",
        "token": social_token,
    }
    assert result.trace["food_gain"] == 0.0
    assert result.trace["actual_delta"] == {
        "energy": pytest.approx(-0.018),
        "safety": pytest.approx(0.0),
        "connection": pytest.approx(0.16),
        "stimulation": pytest.approx(0.02),
    }
    assert result.trace["energy_after"] == pytest.approx(0.382)
    _assert_ledger_reconciles(result.trace)


def test_crossing_critical_energy_overrides_goal_without_masking_local_actions() -> None:
    run_id = "metabolism-critical-goal-override"
    state = _state_with_front(
        run_id,
        17,
        front_cause=None,
        organism={
            "energy": 0.16,
            "safety": 0.14,
            "connection": 0.9,
            "stimulation": 0.9,
        },
    )
    meta = engine.make_run_metadata(run_id, 17)
    assert state["current_goal"]["state_variable"] == "safety"
    _force_action(state, "move_forward")

    crossing, _ = _step(state, meta)

    assert crossing.trace["selected_action"] == "move_forward"
    assert crossing.trace["energy_before"] > engine.CRITICAL_OVERRIDE_THRESHOLD
    assert crossing.trace["energy_after"] <= engine.CRITICAL_OVERRIDE_THRESHOLD
    assert crossing.trace["energy_after"] > 0.0
    assert crossing.trace["goal_before"]["state_variable"] == "safety"
    assert crossing.trace["goal_after"]["state_variable"] == "energy"
    assert crossing.trace["goal_transition"] == {
        "changed": True,
        "kind": "critical_override",
        "reason": "critical_override_energy",
    }
    assert crossing.trace["candidate_actions"] == list(microworld.ACTIONS)
    assert {item["action"] for item in crossing.trace["candidates"]} == set(
        microworld.ACTIONS
    )

    severe_state = crossing.next_state
    _force_action(severe_state, "turn_right")
    severe, _ = _step(severe_state, meta)

    assert severe.trace["goal_before"]["state_variable"] == "energy"
    assert severe.trace["selected_action"] == "turn_right"
    assert severe.trace["candidate_actions"] == list(microworld.ACTIONS)
    assert {item["action"] for item in severe.trace["candidates"]} == set(
        microworld.ACTIONS
    )
    assert all("gate_reasons" not in item for item in severe.trace["candidates"])
    assert severe.next_state["world"]["agent"]["facing"] == "E"
    assert severe.next_state["organism"]["energy"] > 0.0


def test_sqlite_recovery_recomputes_metabolism_and_tamper_fails_closed(
    tmp_path,
) -> None:
    db_path = tmp_path / "metabolism-replay.sqlite3"
    run_id = "metabolism-sqlite-replay"
    meta = engine.make_run_metadata(run_id, 18)
    state = _state_with_front(run_id, 18, front_cause=None)

    with SQLiteEventStore(db_path) as store:
        store.create_run(meta, state)
        expected_traces = []
        for injected_event in (None, "quiet_interval"):
            result, command = _step(
                state,
                meta,
                injected_event=injected_event,
            )
            assert command["injected_event"] == injected_event
            assert store.append_step(command, result.trace).committed is True
            expected_traces.append(result.trace)
            state = result.next_state

        recovered = store.recover_run(run_id)
        assert recovered.state == state
        assert recovered.traces == expected_traces
        assert all(trace["transition_kind"] == "action" for trace in recovered.traces)
        for trace in recovered.traces:
            _assert_ledger_reconciles(trace)

        tampered = deepcopy(expected_traces[0])
        tampered["passive_decay"] = 0.99
        tampered["metabolism"]["passive_decay"] = 0.99
        tampered["trace_hash"] = engine.compute_trace_hash(tampered)
        store.connection.execute(
            "UPDATE traces SET trace_json = ?, trace_hash = ? "
            "WHERE run_id = ? AND sequence = 1",
            (
                engine.canonical_json(tampered),
                tampered["trace_hash"],
                run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="independent recomputation"):
            store.recover_run(run_id)


def test_real_controller_dispatch_commits_and_recovers_metabolism_trace(
    tmp_path,
) -> None:
    with SQLiteEventStore(tmp_path / "metabolism-controller.sqlite3") as store:
        controller = PlaygroundController(
            store,
            run_id="metabolism-controller-trigger",
            seed=17,
            world_seed=17,
        )
        dispatched = controller.dispatch(
            interventions=engine.DEFAULT_INTERVENTIONS,
            trigger_source="ui_step_button",
            injected_event="quiet_interval",
        )

        assert dispatched.receipt.committed is True
        assert dispatched.step is not None
        assert dispatched.step.trace["command"]["injected_event"] == "quiet_interval"
        assert dispatched.step.trace["trigger_source"] == "ui_step_button"
        assert dispatched.step.trace["candidate_actions"] == list(microworld.ACTIONS)
        assert dispatched.step.trace["observation"]["schema_version"] == (
            microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION
        )
        assert dispatched.step.next_state["lifecycle"]["trial_status"] == "active"
        assert dispatched.step.next_state["organism"]["energy"] > 0.0

        recovered = controller.recover()
        assert recovered.command_count == 1
        assert recovered.state == dispatched.step.next_state
        assert recovered.traces[0] == dispatched.step.trace
        _assert_ledger_reconciles(recovered.traces[0])
