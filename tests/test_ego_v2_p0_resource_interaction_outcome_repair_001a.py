from __future__ import annotations

from copy import deepcopy
import json

import pytest

from labs.ego_life_playground_v0 import engine, microworld
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import (
    RecoveryError,
    RecoveryFrame,
    SQLiteEventStore,
)
from labs.ego_life_playground_v0.terminal import build_terminal_snapshot
from labs.ego_life_playground_v0.visual_console import (
    build_chinese_causal_view,
    build_tk_trace_payload,
)


_AGENT_POSITION = [4, 2]
_FORWARD_POSITION = [4, 1]
_OFF_AXIS_POSITIONS = ([1, 1], [7, 1], [2, 3], [6, 3], [3, 3])


def _state_with_front_object(
    *,
    run_id: str,
    seed: int = 18,
    energy: float = 0.1,
    front_cause: str | None = "resource",
) -> dict:
    state = engine.initial_state(
        {
            "energy": energy,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.9,
        },
        run_id=run_id,
        seed=seed,
    )
    world = deepcopy(state["world"])
    world["agent"]["position"] = list(_AGENT_POSITION)
    world["agent"]["facing"] = "N"

    remaining_positions = iter(deepcopy(list(_OFF_AXIS_POSITIONS)))
    for cause in sorted(world["objects_by_cause"]):
        world["objects_by_cause"][cause]["position"] = (
            list(_FORWARD_POSITION)
            if cause == front_cause
            else next(remaining_positions)
        )

    microworld.verify_world_state(world)
    state["world"] = world
    return state


def _command(
    state: dict,
    *,
    injected_event: str | None = None,
    trigger_source: str = "headless_acceptance",
) -> dict:
    return engine.make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        injected_event=injected_event,
        trigger_source=trigger_source,
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=state["last_command_hash"],
    )


def _step(state: dict, meta: dict, *, injected_event: str | None = None):
    command = _command(state, injected_event=injected_event)
    return engine.compute_step(state, command, meta), command


def _metabolism(
    *,
    selected_action: str,
    world_before: dict,
    world_after: dict,
    world_transition: dict,
    energy_before: float = 0.4,
    run_id: str,
) -> dict:
    meta = engine.make_run_metadata(run_id, 18)
    return engine.compute_metabolism_ledger(
        energy_before=energy_before,
        selected_action=selected_action,
        world_before=world_before,
        world_after=world_after,
        world_transition=world_transition,
        run_meta=meta,
        episode_id=engine.episode_id_for(run_id, 0),
        command_hash=engine.canonical_hash({"test_run_id": run_id}),
        code_path_hash=meta["code_path_hash"],
    )


def test_real_resource_directly_ahead_requires_interact_and_replenishes_energy():
    run_id = "resource-interaction-v4-positive"
    state = _state_with_front_object(run_id=run_id)
    world_before = deepcopy(state["world"])
    meta = engine.make_run_metadata(run_id, 18)

    result, command = _step(state, meta)
    trace = result.trace
    transition = trace["world_transition"]
    resource_before = world_before["objects_by_cause"]["resource"]
    resource_after = result.next_state["world"]["objects_by_cause"]["resource"]

    assert trace["schema_version"] == engine.TRACE_SCHEMA_VERSION
    assert trace["observation"]["schema_version"] == (
        microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION
    )
    assert trace["selected_action"] == "interact"
    assert transition == {
        "outcome_type": "interacted",
        "cause": "resource",
        "token": resource_before["token"],
    }
    assert command["injected_event"] is None
    assert result.next_state["world"]["agent"] == world_before["agent"]
    assert resource_after["cause"] == "resource"
    assert resource_after["token"] == resource_before["token"]
    assert resource_after["spawn_count"] == resource_before["spawn_count"] + 1
    assert resource_after["injection_count"] == resource_before["injection_count"]

    assert trace["energy_before"] == 0.1
    assert trace["passive_decay"] == engine.PASSIVE_ENERGY_DECAY_PER_TICK == 0.01
    assert trace["action_cost"] == engine.ACTION_COSTS["interact"] == 0.008
    assert trace["food_gain"] == engine.CAUSE_DELTAS["resource"]["energy"] == 0.28
    assert trace["metabolism"]["food_obtained"] is True
    assert trace["energy_after"] == pytest.approx(0.362)
    assert result.next_state["organism"]["energy"] == pytest.approx(0.362)

    policy_bytes = engine.canonical_json(trace["policy_projection"])
    assert "objects_by_cause" not in policy_bytes
    assert "token_mapping" not in policy_bytes
    assert '"resource"' not in policy_bytes


def test_no_gain_from_non_resource_no_object_or_blocked_attempts():
    social_world = _state_with_front_object(
        run_id="resource-control-social", front_cause="social"
    )["world"]
    social_after, social_transition = microworld.transition_world(social_world, "interact")
    assert social_transition["outcome_type"] == "interacted"
    assert social_transition["cause"] == "social"

    empty_world = _state_with_front_object(
        run_id="resource-control-empty", front_cause=None
    )["world"]
    empty_after, no_object_transition = microworld.transition_world(
        empty_world, "interact"
    )
    assert no_object_transition == {"outcome_type": "no_object"}
    assert empty_after == empty_world

    resource_world = _state_with_front_object(
        run_id="resource-control-blocked"
    )["world"]
    blocked_after, blocked_transition = microworld.transition_world(
        resource_world, "move_forward"
    )
    assert blocked_transition == {"outcome_type": "blocked", "blocked_by": "object"}
    assert blocked_after["agent"]["position"] == resource_world["agent"]["position"]

    controls = (
        (
            "interact",
            social_world,
            social_after,
            social_transition,
            "resource-control-social-ledger",
        ),
        (
            "interact",
            empty_world,
            empty_after,
            no_object_transition,
            "resource-control-empty-ledger",
        ),
        (
            "move_forward",
            resource_world,
            blocked_after,
            blocked_transition,
            "resource-control-blocked-ledger",
        ),
    )
    for action, world_before, world_after, transition, run_id in controls:
        ledger = _metabolism(
            selected_action=action,
            world_before=world_before,
            world_after=world_after,
            world_transition=transition,
            run_id=run_id,
        )
        assert ledger["food_obtained"] is False
        assert ledger["food_gain"] == 0.0
        assert ledger["energy_after"] == pytest.approx(
            0.4 - engine.PASSIVE_ENERGY_DECAY_PER_TICK - engine.ACTION_COSTS[action]
        )


def test_resource_settlement_object_respawn_and_life_reset_are_deterministic():
    world = _state_with_front_object(run_id="resource-deterministic-respawn")[
        "world"
    ]
    before = deepcopy(world)
    before_item = deepcopy(world["objects_by_cause"]["resource"])

    first_world, first_transition = microworld.transition_world(
        deepcopy(world),
        "interact",
        source_sequence=1,
        source_episode_id="episode-resource-a",
        source_command_hash="a" * 64,
    )
    second_world, second_transition = microworld.transition_world(
        deepcopy(world),
        "interact",
        source_sequence=999,
        source_episode_id="episode-resource-b",
        source_command_hash="b" * 64,
    )

    assert world == before
    assert first_transition == second_transition == {
        "outcome_type": "interacted",
        "cause": "resource",
        "token": before_item["token"],
    }
    assert first_world == second_world
    first_item = first_world["objects_by_cause"]["resource"]
    assert first_item["cause"] == before_item["cause"]
    assert first_item["token"] == before_item["token"]
    assert first_item["spawn_count"] == before_item["spawn_count"] + 1
    assert first_item["injection_count"] == before_item["injection_count"]
    assert first_item["position"] in microworld.validate_layout_topology(
        first_world["layout"]
    )["walkable_cells"]

    life_two_a = microworld.reset_world_for_life(first_world, 2)
    life_two_b = microworld.reset_world_for_life(second_world, 2)
    assert life_two_a == life_two_b
    assert life_two_a["trial"]["token_mapping"] == world["trial"]["token_mapping"]
    assert life_two_a["objects_by_cause"]["resource"]["token"] == before_item["token"]
    assert all(
        item["spawn_count"] == 0 and item["injection_count"] == 0
        for item in life_two_a["objects_by_cause"].values()
    )


def test_metabolism_rejects_forged_resource_cause_on_no_object_outcome():
    state = _state_with_front_object(
        run_id="resource-forged-outcome", front_cause=None
    )
    no_object_after, no_object_transition = microworld.transition_world(
        state["world"], "interact"
    )
    assert no_object_transition == {"outcome_type": "no_object"}
    assert (
        _metabolism(
            selected_action="interact",
            world_before=state["world"],
            world_after=no_object_after,
            world_transition=no_object_transition,
            run_id="resource-unforged-no-object",
        )["food_gain"]
        == 0.0
    )

    forged_transition = deepcopy(no_object_transition)
    forged_transition.update(
        {
            "cause": "resource",
            "token": state["world"]["objects_by_cause"]["resource"]["token"],
        }
    )
    with pytest.raises(engine.EngineInvariantError):
        _metabolism(
            selected_action="interact",
            world_before=state["world"],
            world_after=no_object_after,
            world_transition=forged_transition,
            run_id="resource-forged-no-object",
        )


def test_metabolism_rejects_valid_shape_cause_token_relabeling() -> None:
    state = _state_with_front_object(
        run_id="resource-forged-cause-token", front_cause="social"
    )
    social_after, genuine = microworld.transition_world(state["world"], "interact")
    assert genuine["outcome_type"] == "interacted"
    assert genuine["cause"] == "social"

    forged = deepcopy(genuine)
    forged["cause"] = "resource"
    with pytest.raises(engine.EngineInvariantError):
        _metabolism(
            selected_action="interact",
            world_before=state["world"],
            world_after=social_after,
            world_transition=forged,
            run_id="resource-forged-cause-token-ledger",
        )


def test_observer_and_chinese_ui_results_are_recovered_trace_bound():
    run_id = "resource-ui-trace-bound"
    state = _state_with_front_object(run_id=run_id)
    result, _ = _step(state, engine.make_run_metadata(run_id, 18))
    frame = RecoveryFrame(sequence=1, state=result.next_state, trace=result.trace)

    payload = build_tk_trace_payload(frame.state, frame.trace)
    view = build_chinese_causal_view(frame)
    assert payload["observer_frame"]["world"] == result.next_state["world"]
    assert payload["policy_visual"] == result.trace["observation"]
    assert payload["selected_action"] == result.trace["selected_action"] == "interact"
    assert "resource" not in engine.canonical_json(payload["policy_visual"])
    assert view["候选与选择"]["选择动作"] == "interact"
    assert view["结果与变化"]["世界结果"] == "interacted"
    assert view["结果与变化"]["命令注入"] is None

    trace_variant = deepcopy(result.trace)
    trace_variant["world_transition"] = {"outcome_type": "no_object"}
    variant_frame = RecoveryFrame(
        sequence=frame.sequence,
        state=deepcopy(frame.state),
        trace=trace_variant,
    )
    variant_payload = build_tk_trace_payload(variant_frame.state, variant_frame.trace)
    variant_view = build_chinese_causal_view(variant_frame)

    assert variant_payload["observer_frame"] == payload["observer_frame"]
    assert variant_payload["policy_visual"] == payload["policy_visual"]
    assert variant_view["观察者全局视图"] == view["观察者全局视图"]
    assert variant_view["候选与选择"] == view["候选与选择"]
    assert variant_view["结果与变化"]["世界结果"] == "no_object"


def test_controller_sqlite_non_resource_interact_never_produces_food(tmp_path):
    run_id = "resource-controller-social-control"
    state = _state_with_front_object(run_id=run_id, front_cause="social")
    meta = engine.make_run_metadata(run_id, 18)

    with SQLiteEventStore(tmp_path / "resource-social-control.sqlite3") as store:
        store.create_run(meta, state)
        controller = PlaygroundController(store, run_id=run_id)
        dispatched = controller.dispatch(
            engine.DEFAULT_INTERVENTIONS,
            trigger_source="ui_step_button",
        )
        assert dispatched.receipt.committed is True
        assert dispatched.step is not None

        recovered = controller.recover()
        trace = recovered.traces[0]
        assert trace["selected_action"] == "interact"
        assert trace["world_transition"]["outcome_type"] == "interacted"
        assert trace["world_transition"]["cause"] == "social"
        assert trace["metabolism"]["food_obtained"] is False
        assert trace["food_gain"] == 0.0
        assert trace["energy_after"] == pytest.approx(0.082)

        snapshot = build_terminal_snapshot(controller)
        assert snapshot["selected_action"] == trace["selected_action"]
        assert snapshot["world_transition"] == trace["world_transition"]
        assert snapshot["actual_delta"] == trace["actual_delta"]


def test_controller_sqlite_recomputes_resource_interaction_and_rejects_trace_tamper(
    tmp_path,
):
    run_id = "resource-controller-replay"
    state = _state_with_front_object(run_id=run_id)
    meta = engine.make_run_metadata(run_id, 18)

    with SQLiteEventStore(tmp_path / "resource-replay.sqlite3") as store:
        store.create_run(meta, state)
        controller = PlaygroundController(store, run_id=run_id)
        dispatched = controller.dispatch(
            engine.DEFAULT_INTERVENTIONS,
            trigger_source="ui_step_button",
        )
        assert dispatched.receipt.committed is True
        assert dispatched.step is not None

        recovered_a = controller.recover()
        recovered_b = store.recover_run(run_id)
        assert store.row_counts(run_id) == (1, 1)
        assert recovered_a.state == recovered_b.state == dispatched.step.next_state
        assert recovered_a.traces == recovered_b.traces == [dispatched.step.trace]
        assert recovered_a.traces[0]["selected_action"] == "interact"
        assert recovered_a.traces[0]["world_transition"]["cause"] == "resource"
        assert recovered_a.traces[0]["food_gain"] == 0.28
        terminal_snapshot = build_terminal_snapshot(controller)
        assert terminal_snapshot["selected_action"] == "interact"
        assert terminal_snapshot["world_transition"] == recovered_a.traces[0][
            "world_transition"
        ]
        recovered_view = build_chinese_causal_view(recovered_a.frames[-1])
        assert recovered_view["候选与选择"]["选择动作"] == "interact"
        assert recovered_view["结果与变化"]["世界结果"] == "interacted"

        tampered = deepcopy(recovered_a.traces[0])
        tampered["world_transition"] = {"outcome_type": "no_object"}
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


def test_controller_sqlite_rejects_valid_schema_initial_world_tamper(tmp_path):
    run_id = "resource-controller-initial-state-tamper"
    state = _state_with_front_object(run_id=run_id)
    meta = engine.make_run_metadata(run_id, 18)

    with SQLiteEventStore(tmp_path / "resource-initial-tamper.sqlite3") as store:
        store.create_run(meta, state)
        controller = PlaygroundController(store, run_id=run_id)
        dispatched = controller.dispatch(
            engine.DEFAULT_INTERVENTIONS,
            trigger_source="ui_step_button",
        )
        assert dispatched.receipt.committed is True

        row = store.connection.execute(
            "SELECT initial_state_json FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        tampered_state = json.loads(row["initial_state_json"])
        tampered_state["world"]["objects_by_cause"]["resource"]["position"] = [3, 3]
        microworld.verify_world_state(tampered_state["world"])
        store.connection.execute(
            "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? "
            "WHERE run_id = ?",
            (
                engine.canonical_json(tampered_state),
                engine.canonical_hash(tampered_state),
                run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="independent recomputation"):
            store.recover_run(run_id)
