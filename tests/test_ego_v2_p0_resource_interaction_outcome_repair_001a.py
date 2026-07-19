from __future__ import annotations

from copy import deepcopy
import hashlib

import pytest

from labs.ego_life_playground_v0 import engine, microworld
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import RecoveryFrame, SQLiteEventStore
from labs.ego_life_playground_v0.visual_console import build_chinese_causal_view


def _resource_instance_id(command_hash: str) -> str:
    return hashlib.sha256(
        f"resource_instance|{command_hash}".encode("utf-8")
    ).hexdigest()


def _stationary_state(*, run_id: str, seed: int, energy: float) -> dict:
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
    state["world"]["agent"]["position"] = "site_a"
    state["world"]["public_observation"]["agent_position"] = "site_a"
    microworld.verify_world_state(state["world"])
    return state


def _command(state: dict, *, cue: str, world_event: str) -> dict:
    return engine.make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        cue=cue,
        world_event=world_event,
        trigger_source="headless_acceptance",
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=state["last_command_hash"],
    )


def _step(state: dict, meta: dict, *, cue: str, world_event: str):
    command = _command(state, cue=cue, world_event=world_event)
    return engine.compute_step(state, command, meta), command


def test_stationary_positive_resource_instance_resolves_and_replenishes_energy():
    run_id = "resource-interaction-stationary-positive"
    state = _stationary_state(run_id=run_id, seed=18, energy=0.0)
    meta = engine.make_run_metadata(run_id, 18)

    result, command = _step(
        state,
        meta,
        cue="resource",
        world_event="resource_appears",
    )

    trace = result.trace
    interaction = trace["world_transition"]["resource_interaction"]
    assert trace["schema_version"] == "ego.life_playground.trace.v6"
    assert trace["selected_action"] == "forage"
    assert trace["world_transition"]["moved"] is False
    assert trace["world_transition"]["visited_site"] == "site_a"
    assert trace["world_transition"]["outcome"] == 1.0
    assert trace["world_transition"]["food_obtained"] is True
    assert interaction == {
        "instance_id": _resource_instance_id(command["command_hash"]),
        "available": True,
        "attempted": True,
        "resolved": True,
        "outcome": 1.0,
        "food_obtained": True,
        "failure_reason": None,
    }
    assert interaction["instance_id"] not in engine.canonical_json(
        trace["policy_projection"]
    )
    assert interaction["instance_id"] not in engine.canonical_json(
        trace["policy_non_memory_projection"]
    )
    assert trace["energy_before"] == 0.0
    assert trace["passive_decay"] == 0.02
    assert trace["action_cost"] == engine.ACTION_COSTS["forage"] == 0.02
    assert trace["food_gain"] == engine.FOOD_ENERGY_GAIN == 0.28
    assert trace["energy_after"] == pytest.approx(0.24)
    assert result.next_state["organism"]["energy"] == pytest.approx(0.24)
    history = result.next_state["world"]["private_dynamics"]["outcome_history"]
    assert len(history) == 1
    assert history[0]["source_command_hash"] == command["command_hash"]


def test_stationary_negative_resource_resolves_without_food_gain():
    run_id = "resource-interaction-stationary-negative"
    state = _stationary_state(run_id=run_id, seed=17, energy=0.4)
    meta = engine.make_run_metadata(run_id, 17)

    result, _ = _step(
        state,
        meta,
        cue="resource",
        world_event="resource_appears",
    )

    trace = result.trace
    interaction = trace["world_transition"]["resource_interaction"]
    assert trace["selected_action"] == "forage"
    assert trace["world_transition"]["moved"] is False
    assert trace["world_transition"]["outcome"] == -1.0
    assert trace["world_transition"]["food_obtained"] is False
    assert interaction["available"] is True
    assert interaction["attempted"] is True
    assert interaction["resolved"] is True
    assert interaction["outcome"] == -1.0
    assert interaction["food_obtained"] is False
    assert interaction["failure_reason"] == "harmful_or_unusable_resource"
    assert trace["food_gain"] == 0.0
    assert trace["energy_after"] == pytest.approx(0.36)


def test_no_resource_event_and_non_forage_action_cannot_obtain_food():
    quiet_world = microworld.observe_world_event(
        microworld.initial_world_state(seed=18), "quiet_interval"
    )
    quiet_after, quiet_transition = microworld.transition_world(
        quiet_world,
        "forage",
        source_sequence=1,
        source_episode_id="episode-control-quiet",
        source_command_hash="a" * 64,
    )
    assert quiet_transition["outcome"] == 1.0
    assert quiet_transition["food_obtained"] is False
    assert quiet_transition["resource_interaction"] == {
        "instance_id": None,
        "available": False,
        "attempted": True,
        "resolved": False,
        "outcome": None,
        "food_obtained": False,
        "failure_reason": "no_resource_event",
    }
    assert quiet_after["public_observation"]["event"] == "quiet_interval"

    resource_world = microworld.observe_world_event(
        microworld.initial_world_state(seed=17), "resource_appears"
    )
    resource_after, non_forage_transition = microworld.transition_world(
        resource_world,
        "approach",
        source_sequence=1,
        source_episode_id="episode-control-non-forage",
        source_command_hash="b" * 64,
    )
    assert non_forage_transition["outcome"] == 1.0
    assert non_forage_transition["food_obtained"] is False
    assert non_forage_transition["resource_interaction"] == {
        "instance_id": _resource_instance_id("b" * 64),
        "available": True,
        "attempted": False,
        "resolved": False,
        "outcome": None,
        "food_obtained": False,
        "failure_reason": "resource_not_attempted",
    }
    assert resource_after["public_observation"]["event"] == "resource_appears"


def test_resource_instance_is_command_derived_and_each_new_command_settles_once():
    run_id = "resource-interaction-command-identity"
    state = _stationary_state(run_id=run_id, seed=18, energy=0.0)
    meta = engine.make_run_metadata(run_id, 18)

    first, first_command = _step(
        state,
        meta,
        cue="resource",
        world_event="resource_appears",
    )
    second, second_command = _step(
        first.next_state,
        meta,
        cue="resource",
        world_event="resource_appears",
    )

    first_interaction = first.trace["world_transition"]["resource_interaction"]
    second_interaction = second.trace["world_transition"]["resource_interaction"]
    assert first_command["command_hash"] != second_command["command_hash"]
    assert first_interaction["instance_id"] == _resource_instance_id(
        first_command["command_hash"]
    )
    assert second_interaction["instance_id"] == _resource_instance_id(
        second_command["command_hash"]
    )
    assert first_interaction["instance_id"] != second_interaction["instance_id"]
    history = second.next_state["world"]["private_dynamics"]["outcome_history"]
    assert [record["source_command_hash"] for record in history] == [
        first_command["command_hash"],
        second_command["command_hash"],
    ]

    observed = microworld.observe_world_event(state["world"], "resource_appears")
    rerun_a = microworld.transition_world(
        observed,
        "forage",
        source_sequence=1,
        source_episode_id=state["clock"]["episode_id"],
        source_command_hash=first_command["command_hash"],
    )
    rerun_b = microworld.transition_world(
        observed,
        "forage",
        source_sequence=1,
        source_episode_id=state["clock"]["episode_id"],
        source_command_hash=first_command["command_hash"],
    )
    assert rerun_a == rerun_b
    assert len(rerun_a[0]["private_dynamics"]["outcome_history"]) == 1


def test_metabolism_rejects_forged_resource_food_flag():
    world = microworld.observe_world_event(
        microworld.initial_world_state(seed=17), "resource_appears"
    )
    _, transition = microworld.transition_world(
        world,
        "forage",
        source_sequence=1,
        source_episode_id="episode-forged-food",
        source_command_hash="c" * 64,
    )
    assert transition["outcome"] == -1.0
    forged = deepcopy(transition)
    forged["food_obtained"] = True
    forged["resource_interaction"]["food_obtained"] = True

    meta = engine.make_run_metadata("resource-interaction-forged-food", 17)
    with pytest.raises(engine.EngineInvariantError, match="resource interaction"):
        engine.compute_metabolism_ledger(
            energy_before=0.4,
            selected_action="forage",
            world_transition=forged,
            run_meta=meta,
            episode_id="episode-forged-food",
            command_hash="c" * 64,
            code_path_hash=meta["code_path_hash"],
        )


def test_visual_result_separates_resource_attempt_from_positive_outcome():
    run_id = "resource-interaction-ui-positive"
    state = _stationary_state(run_id=run_id, seed=18, energy=0.0)
    result, _ = _step(
        state,
        engine.make_run_metadata(run_id, 18),
        cue="resource",
        world_event="resource_appears",
    )

    view = build_chinese_causal_view(
        RecoveryFrame(sequence=1, state=result.next_state, trace=result.trace)
    )

    assert view["外部事件"]["发生了什么"] == "资源线索出现"
    assert view["候选与选择"]["选择的行动"] == "尝试获取资源"
    shown = view["结果与变化"]
    interaction = result.trace["world_transition"]["resource_interaction"]
    assert shown["资源实例"] == interaction["instance_id"]
    assert shown["资源结果"] == "成功：已获得食物"
    assert shown["失败原因"] == "无"
    assert shown["食物补能"] == "+0.280"
    assert shown["基础消耗"] == "-0.020"
    assert shown["动作成本"] == "-0.020"
    assert shown["能量净变化"] == "+0.240"


def test_controller_sqlite_stationary_resource_ui_is_trace_bound(tmp_path):
    run_id = "resource-interaction-ui-recovered"
    state = _stationary_state(run_id=run_id, seed=18, energy=0.0)
    meta = engine.make_run_metadata(run_id, 18)
    with SQLiteEventStore(tmp_path / "resource-ui.sqlite3") as store:
        store.create_run(meta, state)
        controller = PlaygroundController(store, run_id=run_id)
        dispatched = controller.dispatch(
            "resource",
            engine.DEFAULT_INTERVENTIONS,
            trigger_source="ui_step_button",
            world_event="resource_appears",
        )
        assert dispatched.receipt.committed is True
        recovered = controller.recover()

    frame = recovered.frames[-1]
    trace = frame.trace
    assert trace is not None
    assert trace["world_transition"]["moved"] is False
    assert trace["world_transition"]["resource_interaction"]["resolved"] is True
    assert trace["food_gain"] == 0.28
    real_view = build_chinese_causal_view(frame)
    assert real_view["外部事件"]["发生了什么"] == "资源线索出现"
    assert real_view["候选与选择"]["选择的行动"] == "尝试获取资源"
    assert real_view["结果与变化"]["资源结果"] == "成功：已获得食物"
    assert real_view["结果与变化"]["食物补能"] == "+0.280"

    trace_variant = deepcopy(trace)
    trace_variant["world_transition"]["outcome"] = -1.0
    trace_variant["world_transition"]["food_obtained"] = False
    trace_variant["world_transition"]["resource_interaction"].update(
        {
            "outcome": -1.0,
            "food_obtained": False,
            "failure_reason": "harmful_or_unusable_resource",
        }
    )
    trace_variant["world_outcome"]["value"] = -1.0
    trace_variant["world_outcome"]["food_obtained"] = False
    trace_variant["food_gain"] = 0.0
    trace_variant["metabolism"]["food_gain"] = 0.0
    trace_variant["metabolism"]["energy_after"] = 0.0
    trace_variant["metabolism"]["energy_delta"] = 0.0
    variant_frame = RecoveryFrame(
        sequence=frame.sequence,
        state=deepcopy(frame.state),
        trace=trace_variant,
    )
    variant_view = build_chinese_causal_view(variant_frame)

    assert trace_variant["seed"] == trace["seed"]
    assert trace_variant["run_id"] == trace["run_id"]
    assert trace_variant["world_event"] == trace["world_event"]
    assert trace_variant["selected_action"] == trace["selected_action"]
    assert variant_view["外部事件"] == real_view["外部事件"]
    assert variant_view["候选与选择"]["选择的行动"] == "尝试获取资源"
    assert variant_view["结果与变化"]["资源结果"] == "失败：未获得食物"
    assert variant_view["结果与变化"]["失败原因"] == "资源有害或不可用"
    assert variant_view["结果与变化"]["食物补能"] == "+0.000"
