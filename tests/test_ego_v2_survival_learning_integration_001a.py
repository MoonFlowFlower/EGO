from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.engine import (
    DEFAULT_INTERVENTIONS,
    MAX_LIVES,
    canonical_hash,
    canonical_json,
    compute_code_path_manifest,
    compute_step,
    compute_trace_hash,
    episode_id_for,
    initial_state,
    make_command,
    make_run_metadata,
)
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore
from labs.ego_life_playground_v0.survival_learning import ALGORITHM
from labs.ego_life_playground_v0.microworld import reset_world_for_life


def _command(state: dict, *, mode: str, update_mode: str = "canonical") -> dict:
    return make_command(
        sequence=state["clock"]["global_tick"] + 1,
        trigger_source="headless_acceptance",
        interventions=dict(
            DEFAULT_INTERVENTIONS,
            survival_learning_mode=mode,
            update_mode=update_mode,
        ),
        prev_command_hash=state["last_command_hash"],
    )


def test_initial_state_run_metadata_and_code_manifest_bind_survival_learner() -> None:
    state = initial_state(run_id="learner-schema")
    meta = make_run_metadata("learner-schema", 701)
    manifest = compute_code_path_manifest()

    assert state["schema_version"] == "ego.life_playground.state.v6"
    assert state["survival_learner"]["algorithm"] == ALGORITHM
    assert state["survival_learner"]["q_values"] == {}
    assert meta["schema_version"] == "ego.life_playground.run.v6"
    assert meta["max_lives"] == 16 == MAX_LIVES
    assert meta["survival_learning"]["algorithm"] == ALGORITHM
    assert manifest["schema_version"] == "ego.life_playground.code_path.v7"
    assert "survival_learning.py" in {item["path"] for item in manifest["files"]}


def test_compute_step_uses_learner_selection_and_updates_compact_receipt() -> None:
    run_id = "learner-step"
    state = initial_state(run_id=run_id)
    result = compute_step(
        state,
        _command(state, mode=ALGORITHM),
        make_run_metadata(run_id, 701),
    )
    receipt = result.trace["survival_learning"]

    assert result.trace["selected_action"] == receipt["selection"]["selected_action"]
    assert receipt["selection"]["state_key"] == receipt["update"]["state_key"]
    assert receipt["selection"]["q_by_action"].keys() == set(result.trace["candidate_actions"])
    assert receipt["update"]["reward"] == (1.0 if result.trace["energy_after"] > 0 else 0.0)
    assert receipt["update"]["applied"] is True
    assert result.next_state["survival_learner"]["update_count"] == 1
    assert receipt["update"]["learner_hash_after"] != receipt["update"]["learner_hash_before"]
    assert "q_values" not in receipt


def test_off_and_update_frozen_do_not_modify_q() -> None:
    run_id = "learner-off-frozen"
    state = initial_state(run_id=run_id)
    meta = make_run_metadata(run_id, 701)

    off = compute_step(state, _command(state, mode="off"), meta)
    assert off.next_state["survival_learner"]["q_values"] == {}
    assert off.trace["survival_learning"]["selection"]["selection_mode"] == "off"
    assert off.trace["survival_learning"]["update"]["applied"] is False

    frozen = compute_step(
        state,
        _command(state, mode=ALGORITHM, update_mode="frozen"),
        meta,
    )
    assert frozen.next_state["survival_learner"] == state["survival_learner"]
    assert frozen.trace["survival_learning"]["update"]["reason"] == "adaptive_updates_frozen"


def test_controller_sqlite_recomputes_q_and_rejects_td_trace_tamper(tmp_path: Path) -> None:
    db_path = tmp_path / "survival-learning.sqlite3"
    run_id = "learner-sqlite"
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(store, run_id=run_id, seed=701)
        result = controller.dispatch(
            interventions=dict(
                DEFAULT_INTERVENTIONS,
                survival_learning_mode=ALGORITHM,
            ),
            trigger_source="ui_run_button",
        )
        assert result.receipt.committed is True
        recovered = store.recover_run(run_id)
        assert recovered.state["survival_learner"]["update_count"] == 1
        assert recovered.traces[-1]["trigger_source"] == "ui_run_button"

        row = store.connection.execute(
            "SELECT trace_json FROM traces WHERE run_id = ? AND sequence = 1", (run_id,)
        ).fetchone()
        trace = json.loads(row["trace_json"])
        trace["survival_learning"]["update"]["td_error"] += 0.5
        trace["trace_hash"] = compute_trace_hash(trace)
        store.connection.execute(
            "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = 1",
            (canonical_json(trace), trace["trace_hash"], run_id),
        )

        with pytest.raises(RecoveryError, match="independent recomputation"):
            store.recover_run(run_id)


def test_q_persists_across_respawn_while_eligibility_is_cleared() -> None:
    run_id = "learner-respawn"
    state = initial_state(run_id=run_id)
    prior_results = [
        {
            "life_index": index,
            "survival_ticks": 256,
            "censored": True,
            "termination": "censored",
        }
        for index in range(1, 15)
    ]
    state["clock"] = {
        "global_tick": 14 * 256 + 14 + 255,
        "episode_index": 14,
        "episode_id": episode_id_for(run_id, 14),
        "episode_tick": 255,
    }
    state["world"] = reset_world_for_life(state["world"], 15)
    state["lifecycle"] = {
        "trial_status": "active",
        "life_index": 15,
        "awaiting_respawn": False,
        "life_results": prior_results,
        "terminal_life_result": None,
    }
    state["last_action"] = "rest"
    state["last_command_hash"] = "a" * 64
    state["last_trace_hash"] = "b" * 64
    meta = make_run_metadata(run_id, 701)

    awaiting = compute_step(state, _command(state, mode=ALGORITHM), meta)
    q_after_life = deepcopy(awaiting.next_state["survival_learner"]["q_values"])
    visits_after_life = deepcopy(awaiting.next_state["survival_learner"]["visit_counts"])
    assert awaiting.next_state["lifecycle"]["trial_status"] == "awaiting_respawn"
    assert q_after_life
    assert awaiting.next_state["survival_learner"]["eligibility"] == {}

    respawned = compute_step(
        awaiting.next_state,
        _command(awaiting.next_state, mode=ALGORITHM),
        meta,
    )
    assert respawned.next_state["lifecycle"]["life_index"] == 16
    assert respawned.next_state["survival_learner"]["q_values"] == q_after_life
    assert respawned.next_state["survival_learner"]["visit_counts"] == visits_after_life
    assert respawned.next_state["survival_learner"]["eligibility"] == {}


def test_recovery_rejects_tampered_initial_q_even_with_recomputed_state_hash(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "initial-q-tamper.sqlite3"
    run_id = "initial-q-tamper"
    with SQLiteEventStore(db_path) as store:
        PlaygroundController(store, run_id=run_id, seed=701)
        row = store.connection.execute(
            "SELECT initial_state_json FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        state = json.loads(row["initial_state_json"])
        state_key = "f" * 64
        state["survival_learner"]["q_values"] = {state_key: {"rest": 99.0}}
        store.connection.execute(
            "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
            (canonical_json(state), canonical_hash(state), run_id),
        )

        with pytest.raises(RecoveryError, match="initial survival learner must be empty"):
            store.recover_run(run_id)


def test_off_mode_terminal_clears_prior_eligibility_without_changing_q() -> None:
    run_id = "learner-off-terminal-reset"
    state = initial_state(run_id=run_id)
    state["clock"] = {
        "global_tick": 255,
        "episode_index": 0,
        "episode_id": episode_id_for(run_id, 0),
        "episode_tick": 255,
    }
    state["last_action"] = "rest"
    state["last_command_hash"] = "a" * 64
    state["last_trace_hash"] = "b" * 64
    state_key = "e" * 64
    state["survival_learner"]["q_values"] = {state_key: {"rest": 0.4}}
    state["survival_learner"]["eligibility"] = {state_key: {"rest": 0.5}}
    state["survival_learner"]["visit_counts"] = {state_key: {"rest": 1}}
    state["survival_learner"]["update_count"] = 1
    q_before = deepcopy(state["survival_learner"]["q_values"])

    terminal = compute_step(
        state,
        _command(state, mode="off"),
        make_run_metadata(run_id, 701),
    )

    assert terminal.next_state["survival_learner"]["q_values"] == q_before
    assert terminal.next_state["survival_learner"]["eligibility"] == {}
    assert terminal.trace["survival_learning"]["update"]["applied"] is False
    assert terminal.trace["survival_learning"]["update"]["eligibility_reset_applied"] is True
