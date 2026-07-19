from __future__ import annotations

from copy import deepcopy
import json

import pytest

from labs.ego_life_playground_v0 import engine, microworld
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore


def _step(
    state: dict,
    meta: dict,
    *,
    cue: str,
    world_event: str,
    trigger_source: str = "headless_acceptance",
) -> tuple[engine.StepResult, dict]:
    command = engine.make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        cue=cue,
        world_event=world_event,
        trigger_source=trigger_source,
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=state["last_command_hash"],
    )
    return engine.compute_step(state, command, meta), command


def _energy_focused_state(run_id: str, seed: int) -> dict:
    return engine.initial_state(
        {
            "energy": 0.4,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.9,
        },
        run_id=run_id,
        seed=seed,
    )


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
    assert trace["energy_after"] == pytest.approx(expected_after)
    assert trace["actual_delta"]["energy"] == pytest.approx(
        trace["energy_after"] - trace["energy_before"]
    )
    assert trace["metabolism"]["energy_before"] == trace["energy_before"]
    assert trace["metabolism"]["energy_after"] == trace["energy_after"]
    assert trace["metabolism"]["producer_function"].endswith(
        "compute_metabolism_ledger"
    )


def test_every_no_food_tick_pays_passive_decay_and_action_cost():
    run_id = "metabolism-no-food-monotonic"
    state = engine.initial_state(
        {
            "energy": 0.5,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.0,
        },
        run_id=run_id,
        seed=17,
    )
    meta = engine.make_run_metadata(run_id, 17)
    energies = [state["organism"]["energy"]]

    for _ in range(3):
        result, _ = _step(
            state,
            meta,
            cue="quiet",
            world_event="quiet_interval",
        )
        trace = result.trace
        assert trace["food_gain"] == 0.0
        assert trace["passive_decay"] == engine.PASSIVE_ENERGY_DECAY_PER_TICK
        assert trace["action_cost"] == engine.ACTION_COSTS[trace["selected_action"]]
        _assert_ledger_reconciles(trace)
        state = result.next_state
        energies.append(state["organism"]["energy"])

    assert all(after < before for before, after in zip(energies, energies[1:]))


def test_forage_requires_real_positive_moved_food_outcome():
    negative_run = "metabolism-forage-negative"
    negative_state = _energy_focused_state(negative_run, seed=17)
    negative_meta = engine.make_run_metadata(negative_run, 17)
    negative, _ = _step(
        negative_state,
        negative_meta,
        cue="resource",
        world_event="resource_appears",
    )

    assert negative.trace["selected_action"] == "forage"
    assert negative.trace["world_transition"]["moved"] is True
    assert negative.trace["world_outcome"]["value"] == -1.0
    assert negative.trace["world_transition"]["food_obtained"] is False
    assert negative.trace["food_gain"] == 0.0
    assert negative.trace["energy_after"] == pytest.approx(0.36)
    _assert_ledger_reconciles(negative.trace)

    repeated, _ = _step(
        negative.next_state,
        negative_meta,
        cue="resource",
        world_event="resource_appears",
    )
    assert repeated.trace["selected_action"] == "forage"
    assert repeated.trace["world_transition"]["moved"] is False
    assert repeated.trace["world_outcome"]["value"] is None
    assert repeated.trace["world_transition"]["food_obtained"] is False
    assert repeated.trace["food_gain"] == 0.0
    assert repeated.trace["energy_after"] < repeated.trace["energy_before"]


def test_positive_moved_forage_outcome_produces_exact_food_gain():
    run_id = "metabolism-forage-food"
    state = _energy_focused_state(run_id, seed=18)
    meta = engine.make_run_metadata(run_id, 18)
    result, _ = _step(
        state,
        meta,
        cue="resource",
        world_event="resource_appears",
    )

    assert result.trace["selected_action"] == "forage"
    assert result.trace["world_transition"]["moved"] is True
    assert result.trace["world_outcome"]["value"] == 1.0
    assert result.trace["world_transition"]["food_obtained"] is True
    assert result.trace["food_gain"] == engine.FOOD_ENERGY_GAIN == 0.28
    assert result.trace["energy_after"] == pytest.approx(0.64)
    _assert_ledger_reconciles(result.trace)


def test_positive_non_forage_outcome_cannot_replenish_energy():
    run_id = "metabolism-positive-non-food"
    state = engine.initial_state(
        {
            "energy": 0.5,
            "safety": 0.9,
            "connection": 0.0,
            "stimulation": 0.9,
        },
        run_id=run_id,
        seed=17,
    )
    meta = engine.make_run_metadata(run_id, 17)
    result, _ = _step(
        state,
        meta,
        cue="contact",
        world_event="social_signal",
    )

    assert result.trace["selected_action"] == "approach"
    assert result.trace["world_transition"]["moved"] is True
    assert result.trace["world_outcome"]["value"] == 1.0
    assert result.trace["world_transition"]["food_obtained"] is False
    assert result.trace["food_gain"] == 0.0
    assert result.trace["energy_after"] == pytest.approx(0.462)


def test_crossing_critical_energy_restricts_next_real_selector_call():
    run_id = "metabolism-critical-gate"
    state = engine.initial_state(
        {
            "energy": 0.16,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.0,
        },
        run_id=run_id,
        seed=17,
    )
    meta = engine.make_run_metadata(run_id, 17)
    crossing, _ = _step(
        state,
        meta,
        cue="quiet",
        world_event="quiet_interval",
    )
    assert crossing.trace["energy_before"] > engine.CRITICAL_ENERGY_THRESHOLD
    assert crossing.trace["energy_after"] <= engine.CRITICAL_ENERGY_THRESHOLD
    assert crossing.trace["downstream_effect"]["entered_critical"] is True
    assert crossing.trace["downstream_effect"][
        "next_tick_capability_restriction"
    ] is True

    restricted, _ = _step(
        crossing.next_state,
        meta,
        cue="quiet",
        world_event="quiet_interval",
    )
    gate = restricted.trace["viability_gate"]
    assert gate["active"] is True
    assert gate["energy_before"] <= engine.CRITICAL_ENERGY_THRESHOLD
    assert gate["allowed_actions_when_critical"] == list(
        engine.CRITICAL_ENERGY_ALLOWED_ACTIONS
    )
    assert set(restricted.trace["legal_actions"]) <= set(
        engine.CRITICAL_ENERGY_ALLOWED_ACTIONS
    )
    assert restricted.trace["selected_action"] in engine.CRITICAL_ENERGY_ALLOWED_ACTIONS
    by_action = {item["action"]: item for item in restricted.trace["candidates"]}
    for action in ("approach", "explore"):
        assert by_action[action]["selection_eligible"] is False
        assert "critical_energy_capability_restriction" in by_action[action][
            "gate_reasons"
        ]
    assert restricted.trace["downstream_effect"][
        "capability_restriction_active"
    ] is True


def test_sqlite_recovery_recomputes_metabolism_and_tamper_fails_closed(tmp_path):
    db_path = tmp_path / "metabolism-replay.sqlite3"
    run_id = "metabolism-sqlite-replay"
    meta = engine.make_run_metadata(run_id, 18)
    state = _energy_focused_state(run_id, seed=18)

    with SQLiteEventStore(db_path) as store:
        store.create_run(meta, state)
        expected_traces = []
        for cue, event in (
            ("resource", "resource_appears"),
            ("quiet", "quiet_interval"),
        ):
            result, command = _step(state, meta, cue=cue, world_event=event)
            assert store.append_step(command, result.trace).committed is True
            expected_traces.append(result.trace)
            state = result.next_state

        recovered = store.recover_run(run_id)
        assert recovered.state == state
        assert recovered.traces == expected_traces
        assert all("metabolism" in trace for trace in recovered.traces)

        tampered = deepcopy(expected_traces[0])
        tampered["food_gain"] = 0.99
        tampered["metabolism"]["food_gain"] = 0.99
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


def test_real_controller_dispatch_commits_and_recovers_metabolism_trace(tmp_path):
    with SQLiteEventStore(tmp_path / "metabolism-controller.sqlite3") as store:
        controller = PlaygroundController(
            store,
            run_id="metabolism-controller-trigger",
            seed=17,
            world_seed=17,
        )
        dispatched = controller.dispatch(
            "quiet",
            engine.DEFAULT_INTERVENTIONS,
            trigger_source="ui_step_button",
            world_event="quiet_interval",
        )
        assert dispatched.receipt.committed is True
        assert dispatched.step is not None
        recovered = controller.recover()
        assert recovered.command_count == 1
        assert recovered.traces[0] == dispatched.step.trace
        _assert_ledger_reconciles(recovered.traces[0])
