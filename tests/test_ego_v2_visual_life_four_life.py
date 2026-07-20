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
    EPISODE_SPAN_TICKS,
    MAX_LIVES,
    EngineInvariantError,
    canonical_hash,
    compute_step,
    episode_id_for,
    initial_state,
    make_command,
    make_run_metadata,
)
from labs.ego_life_playground_v0.microworld import reset_world_for_life
from labs.ego_life_playground_v0.store import SQLiteEventStore


def _run_meta(run_id: str, seed: int = 17) -> dict[str, object]:
    return make_run_metadata(run_id, seed)


def _command_for(state: dict[str, object], *, injected_event: str | None = None) -> dict[str, object]:
    return make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        trigger_source="headless_acceptance",
        interventions=DEFAULT_INTERVENTIONS,
        prev_command_hash=state["last_command_hash"],
        injected_event=injected_event,
    )


def _force_action(monkeypatch: pytest.MonkeyPatch, action: str) -> None:
    from labs.ego_life_playground_v0 import engine as engine_module

    def forced_score_candidate(*, action: str, **kwargs):
        return {
            "action": action,
            "total_score": 1.0 if action == forced_action_name else 0.0,
            "deterministic_tie": 0.0,
            "predicted_delta": {
                "energy": 0.0,
                "safety": 0.0,
                "connection": 0.0,
                "stimulation": 0.0,
            },
            "legacy_memory_bias": 0.0,
            "claim_bias": 0.0,
            "goal_alignment": 0.0,
            "novelty_score": 0.0,
            "predicted_total_deficit_reduction": 0.0,
            "predicted_current_goal_reduction": 0.0,
            "model_ref": None,
        }

    forced_action_name = action
    monkeypatch.setattr(engine_module, "_score_candidate", forced_score_candidate)


def _death_ready_state(*, run_id: str, life_index: int = 1, global_tick: int = 0) -> dict[str, object]:
    state = initial_state(
        {
            "energy": 0.014,
            "safety": 0.62,
            "connection": 0.50,
            "stimulation": 0.43,
        },
        run_id=run_id,
    )
    if global_tick:
        prior_results = [
            {
                "life_index": index,
                "survival_ticks": EPISODE_SPAN_TICKS,
                "censored": True,
                "termination": "censored",
            }
            for index in range(1, life_index)
        ]
        state["clock"] = {
            "global_tick": global_tick,
            "episode_index": life_index - 1,
            "episode_id": episode_id_for(run_id, life_index - 1),
            "episode_tick": global_tick
            - sum(item["survival_ticks"] for item in prior_results)
            - (life_index - 1),
        }
        state["world"] = reset_world_for_life(state["world"], life_index)
        state["lifecycle"] = {
            "trial_status": "active",
            "life_index": life_index,
            "awaiting_respawn": False,
            "life_results": prior_results,
            "terminal_life_result": None,
        }
        state["last_action"] = "rest"
        state["last_command_hash"] = "a" * 64
        state["last_trace_hash"] = "b" * 64
    return state


def _valid_fast_forward_state(
    *,
    run_id: str,
    life_index: int,
    episode_tick: int,
    energy: float,
) -> dict[str, object]:
    state = initial_state(
        {
            "energy": energy,
            "safety": 0.62,
            "connection": 0.50,
            "stimulation": 0.43,
        },
        run_id=run_id,
    )
    prior_results = [
        {
            "life_index": index,
            "survival_ticks": EPISODE_SPAN_TICKS,
            "censored": True,
            "termination": "censored",
        }
        for index in range(1, life_index)
    ]
    global_tick = sum(item["survival_ticks"] for item in prior_results) + (life_index - 1) + episode_tick
    state["clock"] = {
        "global_tick": global_tick,
        "episode_index": life_index - 1,
        "episode_id": episode_id_for(run_id, life_index - 1),
        "episode_tick": episode_tick,
    }
    state["lifecycle"] = {
        "trial_status": "active",
        "life_index": life_index,
        "awaiting_respawn": False,
        "life_results": prior_results,
        "terminal_life_result": None,
    }
    state["last_action"] = "rest"
    state["last_command_hash"] = "a" * 64
    state["last_trace_hash"] = "b" * 64
    state["world"] = reset_world_for_life(state["world"], life_index)
    return state


def _respawning_state(monkeypatch: pytest.MonkeyPatch, *, run_id: str, life_index: int = 1) -> dict[str, object]:
    _force_action(monkeypatch, "turn_left")
    state = _death_ready_state(run_id=run_id, life_index=life_index)
    result = compute_step(state, _command_for(state), _run_meta(run_id))
    return result.next_state


def test_card_c_initial_lifecycle_and_episode_contract():
    state = initial_state(run_id="card-c-initial")

    assert state["schema_version"] == "ego.life_playground.state.v4"
    assert state["clock"] == {
        "global_tick": 0,
        "episode_index": 0,
        "episode_id": state["clock"]["episode_id"],
        "episode_tick": 0,
    }
    assert state["world"]["trial"]["life_index"] == 1
    assert state["lifecycle"] == {
        "trial_status": "active",
        "life_index": 1,
        "awaiting_respawn": False,
        "life_results": [],
        "terminal_life_result": None,
    }


def test_card_c_terminal_death_keeps_updates_and_sets_awaiting_respawn(monkeypatch: pytest.MonkeyPatch):
    run_id = "card-c-death"
    _force_action(monkeypatch, "turn_left")
    before = _death_ready_state(run_id=run_id)

    result = compute_step(before, _command_for(before), _run_meta(run_id))

    assert result.trace["transition_kind"] == "action"
    assert result.trace["policy_invoked"] is True
    assert result.trace["selected_action"] == "turn_left"
    assert result.trace["energy_after"] == pytest.approx(0.0)
    assert result.next_state["organism"]["energy"] == pytest.approx(0.0)
    assert result.trace["model_bytes"]["changed"] is True
    assert result.trace["memory_bytes"]["changed"] is True
    assert result.next_state["lifecycle"]["trial_status"] == "awaiting_respawn"
    assert result.next_state["lifecycle"]["awaiting_respawn"] is True
    assert result.next_state["lifecycle"]["life_results"] == [
        {
            "life_index": 1,
            "survival_ticks": 1,
            "censored": False,
            "termination": "death",
        }
    ]


def test_card_c_respawn_is_pure_transition_and_recomputes_carry_reset_hashes(
    monkeypatch: pytest.MonkeyPatch,
):
    run_id = "card-c-respawn"
    awaiting = _respawning_state(monkeypatch, run_id=run_id)
    model_before = canonical_hash(awaiting["model"])
    memory_before = canonical_hash(awaiting["memory"])
    world_before = canonical_hash(awaiting["world"])
    expected_world = canonical_hash(reset_world_for_life(awaiting["world"], 2))

    from labs.ego_life_playground_v0 import engine as engine_module

    def raising_score_candidate(**kwargs):
        raise AssertionError("respawn must not invoke policy scoring")

    monkeypatch.setattr(engine_module, "_score_candidate", raising_score_candidate)
    result = compute_step(awaiting, _command_for(awaiting), _run_meta(run_id))

    assert result.trace["transition_kind"] == "respawn"
    assert result.trace["policy_invoked"] is False
    assert result.trace["selected_action"] is None
    assert result.trace["candidates"] == []
    assert result.next_state["clock"]["global_tick"] == 2
    assert result.next_state["clock"]["episode_index"] == 1
    assert result.next_state["clock"]["episode_tick"] == 0
    assert result.next_state["world"]["trial"]["life_index"] == 2
    assert result.next_state["last_action"] is None
    assert result.next_state["model"] == awaiting["model"]
    assert result.next_state["memory"] == awaiting["memory"]
    assert result.next_state["lifecycle"]["trial_status"] == "active"
    assert result.next_state["lifecycle"]["awaiting_respawn"] is False
    assert result.next_state["lifecycle"]["life_index"] == 2
    receipt = result.trace["carry_reset_receipt"]
    assert canonical_hash(awaiting["model"]) == model_before
    assert canonical_hash(result.next_state["model"]) == receipt["model"]["after_hash"] == model_before
    assert receipt["model"]["expected_hash"] == model_before
    assert receipt["model"]["matches_expected"] is True
    assert receipt["model"]["changed"] is False
    assert canonical_hash(awaiting["memory"]) == memory_before
    assert canonical_hash(result.next_state["memory"]["episodic"]) == receipt["memory_episodic"]["after_hash"]
    assert canonical_hash(result.next_state["memory"]["consolidated"]) == receipt["memory_consolidated"]["after_hash"]
    assert canonical_hash(result.next_state["memory"]["claim_events"]) == receipt["memory_claim_events"]["after_hash"]
    assert canonical_hash(result.next_state["memory"]["competing_claims"]) == receipt["memory_competing_claims"]["after_hash"]
    assert receipt["memory_schema_version"]["after_hash"] == canonical_hash(result.next_state["memory"]["schema_version"])
    assert receipt["memory_schema_version"]["matches_expected"] is True
    assert receipt["memory_episodic"]["matches_expected"] is True
    assert receipt["memory_consolidated"]["matches_expected"] is True
    assert receipt["memory_claim_events"]["matches_expected"] is True
    assert receipt["memory_competing_claims"]["matches_expected"] is True
    assert canonical_hash(awaiting["world"]) == world_before
    assert canonical_hash(result.next_state["world"]) == receipt["world"]["after_hash"] == expected_world
    assert receipt["world"]["expected_hash"] == expected_world
    assert receipt["world"]["matches_expected"] is True
    assert receipt["world"]["changed"] is True
    expected_world_state = reset_world_for_life(awaiting["world"], 2)
    assert receipt["agent_position"]["after_hash"] == canonical_hash(
        result.next_state["world"]["agent"]["position"]
    )
    assert receipt["agent_position"]["expected_hash"] == canonical_hash(
        expected_world_state["agent"]["position"]
    )
    assert receipt["agent_position"]["matches_expected"] is True
    assert receipt["agent_facing"]["after_hash"] == canonical_hash(
        result.next_state["world"]["agent"]["facing"]
    )
    assert receipt["agent_facing"]["expected_hash"] == canonical_hash(
        expected_world_state["agent"]["facing"]
    )
    assert receipt["agent_facing"]["matches_expected"] is True
    for component, field in (
        ("object_positions", "position"),
        ("object_spawn_counts", "spawn_count"),
        ("object_injection_counts", "injection_count"),
    ):
        actual = {
            cause: item[field]
            for cause, item in result.next_state["world"]["objects_by_cause"].items()
        }
        expected = {
            cause: item[field]
            for cause, item in expected_world_state["objects_by_cause"].items()
        }
        assert receipt[component]["after_hash"] == canonical_hash(actual)
        assert receipt[component]["expected_hash"] == canonical_hash(expected)
        assert receipt[component]["matches_expected"] is True
    assert receipt["organism"]["after_hash"] == canonical_hash(result.next_state["organism"])
    assert receipt["organism"]["expected_hash"] == canonical_hash(
        {"energy": 0.45, "safety": 0.62, "connection": 0.5, "stimulation": 0.43}
    )
    assert receipt["organism"]["matches_expected"] is True
    assert receipt["current_goal"]["after_hash"] == canonical_hash(result.next_state["current_goal"])
    assert receipt["current_goal"]["matches_expected"] is True
    assert receipt["goal_completed_latches"]["after_hash"] == canonical_hash(
        result.next_state["current_goal"]["completed_latches"]
    )
    assert receipt["goal_completed_latches"]["matches_expected"] is True
    assert receipt["last_action"]["before_hash"] == canonical_hash(awaiting["last_action"])
    assert receipt["last_action"]["after_hash"] == canonical_hash(result.next_state["last_action"])
    assert receipt["last_action"]["expected_hash"] == canonical_hash(None)
    assert receipt["last_action"]["matches_expected"] is True
    assert receipt["last_action"]["absent_before"] is False
    assert receipt["last_action"]["absent_after"] is False
    assert result.trace["episode_transition"]["carry_checks"]["command_chain_continued"] is True
    assert result.trace["episode_transition"]["carry_checks"]["trace_chain_continued"] is True
    assert result.trace["command_chain"]["before_last_command_hash"] == awaiting["last_command_hash"]
    assert result.trace["command_chain"]["command_prev_matches_before"] is True
    assert result.trace["command_chain"]["after_last_command_hash"] == result.trace["command_hash"]
    assert result.trace["command_chain"]["after_matches_command_hash"] is True
    assert result.trace["trace_chain"]["before_last_trace_hash"] == awaiting["last_trace_hash"]
    assert result.trace["trace_chain"]["trace_prev_matches_before"] is True
    assert result.trace["prev_trace_hash"] == awaiting["last_trace_hash"]
    assert result.trace["vision_ablation"] == {"requested_mode": "canonical", "applied": False}
    assert result.trace["action_episode"] is None
    assert result.trace["decision_state_hash"] is None
    assert result.trace["world_decision_hash"] is None
    assert result.trace["carry_reset_receipt"]["working_spatial_state"]["absent_before"] is True
    assert result.trace["carry_reset_receipt"]["working_spatial_state"]["absent_after"] is True
    assert result.trace["carry_reset_receipt"]["working_spatial_state"]["before_hash"] is None
    assert result.trace["carry_reset_receipt"]["working_spatial_state"]["after_hash"] is None


def test_card_c_mapping_and_command_trace_chain_persist_across_respawn(
    monkeypatch: pytest.MonkeyPatch,
):
    run_id = "card-c-chain"
    awaiting = _respawning_state(monkeypatch, run_id=run_id)
    mapping_before = deepcopy(awaiting["world"]["trial"]["token_mapping"])
    command_before = awaiting["last_command_hash"]
    trace_before = awaiting["last_trace_hash"]

    respawned = compute_step(awaiting, _command_for(awaiting), _run_meta(run_id))

    assert respawned.next_state["world"]["trial"]["token_mapping"] == mapping_before
    assert respawned.trace["prev_command_hash"] == command_before
    assert respawned.trace["prev_trace_hash"] == trace_before
    assert respawned.next_state["last_command_hash"] == respawned.trace["command_hash"]
    assert respawned.next_state["last_trace_hash"] == respawned.trace["trace_hash"]
    assert respawned.next_state["memory"]["schema_version"] == awaiting["memory"]["schema_version"]
    assert respawned.next_state["world"]["agent"]["position"] != awaiting["world"]["agent"]["position"]


def test_card_c_episode_does_not_roll_at_eight_and_censors_at_256(monkeypatch: pytest.MonkeyPatch):
    run_id = "card-c-censor"
    _force_action(monkeypatch, "rest")
    state = _valid_fast_forward_state(
        run_id=run_id,
        life_index=1,
        episode_tick=255,
        energy=0.90,
    )

    result = compute_step(state, _command_for(state), _run_meta(run_id))

    assert result.trace["transition_kind"] == "action"
    assert result.next_state["clock"]["episode_index"] == 0
    assert result.next_state["clock"]["episode_tick"] == 256
    assert result.next_state["lifecycle"]["trial_status"] == "awaiting_respawn"
    assert result.next_state["lifecycle"]["life_results"][-1] == {
        "life_index": 1,
        "survival_ticks": 256,
        "censored": True,
        "termination": "censored",
    }


def test_card_c_death_wins_over_censor_at_tick_256(monkeypatch: pytest.MonkeyPatch):
    run_id = "card-c-death-256"
    _force_action(monkeypatch, "turn_left")
    state = _valid_fast_forward_state(
        run_id=run_id,
        life_index=1,
        episode_tick=255,
        energy=0.014,
    )

    result = compute_step(state, _command_for(state), _run_meta(run_id))

    assert result.trace["energy_after"] == pytest.approx(0.0)
    assert result.next_state["lifecycle"]["life_results"][-1] == {
        "life_index": 1,
        "survival_ticks": 256,
        "censored": False,
        "termination": "death",
    }


def test_card_c_life_sixteen_terminal_rejects_further_compute_and_controller_dispatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    run_id = "card-c-life-sixteen"
    _force_action(monkeypatch, "rest")
    before_terminal = _valid_fast_forward_state(
        run_id=run_id,
        life_index=MAX_LIVES,
        episode_tick=255,
        energy=0.90,
    )
    terminal_result = compute_step(before_terminal, _command_for(before_terminal), _run_meta(run_id))
    terminal = terminal_result.next_state

    assert terminal_result.trace["life_termination"] == {
        "life_index": MAX_LIVES,
        "survival_ticks": 256,
        "censored": True,
        "termination": "censored",
    }
    assert terminal["lifecycle"]["trial_status"] == "terminal"
    assert terminal["lifecycle"]["awaiting_respawn"] is False
    assert len(terminal["lifecycle"]["life_results"]) == MAX_LIVES
    assert terminal["lifecycle"]["terminal_life_result"] == {"survival_ticks": 256, "censored": True}
    with pytest.raises(EngineInvariantError, match="terminal"):
        compute_step(terminal, _command_for(terminal), _run_meta(run_id))

    db_path = tmp_path / "card-c-life-sixteen.sqlite3"
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(store, run_id=run_id, seed=17)
        controller.state = deepcopy(terminal)
        with pytest.raises(EngineInvariantError, match="terminal"):
            controller.dispatch(trigger_source="ui_step_button")


def test_card_c_life_sixteen_death_precedence_generates_terminal_without_life_seventeen(
    monkeypatch: pytest.MonkeyPatch,
):
    run_id = "card-c-life-sixteen-death"
    _force_action(monkeypatch, "turn_left")
    before_terminal = _valid_fast_forward_state(
        run_id=run_id,
        life_index=MAX_LIVES,
        episode_tick=255,
        energy=0.014,
    )

    result = compute_step(before_terminal, _command_for(before_terminal), _run_meta(run_id))

    assert result.trace["energy_after"] == pytest.approx(0.0)
    assert result.trace["life_termination"] == {
        "life_index": MAX_LIVES,
        "survival_ticks": 256,
        "censored": False,
        "termination": "death",
    }
    assert result.next_state["lifecycle"]["trial_status"] == "terminal"
    assert len(result.next_state["lifecycle"]["life_results"]) == MAX_LIVES
    assert result.next_state["lifecycle"]["terminal_life_result"] == {
        "survival_ticks": 256,
        "censored": False,
    }
    with pytest.raises(EngineInvariantError, match="terminal"):
        compute_step(result.next_state, _command_for(result.next_state), _run_meta(run_id))


def test_card_c_life_fifteen_can_respawn_into_life_sixteen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_id = "card-c-life-fifteen-respawn"
    _force_action(monkeypatch, "rest")
    before = _valid_fast_forward_state(
        run_id=run_id,
        life_index=MAX_LIVES - 1,
        episode_tick=255,
        energy=0.90,
    )

    awaiting = compute_step(before, _command_for(before), _run_meta(run_id))
    assert awaiting.next_state["lifecycle"]["trial_status"] == "awaiting_respawn"
    assert awaiting.next_state["lifecycle"]["life_index"] == MAX_LIVES - 1

    respawned = compute_step(
        awaiting.next_state,
        _command_for(awaiting.next_state),
        _run_meta(run_id),
    )
    assert respawned.next_state["lifecycle"]["trial_status"] == "active"
    assert respawned.next_state["lifecycle"]["life_index"] == MAX_LIVES
    assert respawned.next_state["clock"]["episode_index"] == MAX_LIVES - 1


def test_card_c_respawn_rejects_injected_event(monkeypatch: pytest.MonkeyPatch):
    run_id = "card-c-respawn-injected"
    awaiting = _respawning_state(monkeypatch, run_id=run_id)

    with pytest.raises(EngineInvariantError, match="respawn"):
        compute_step(awaiting, _command_for(awaiting, injected_event="resource_appears"), _run_meta(run_id))
