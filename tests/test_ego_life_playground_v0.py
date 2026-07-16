from __future__ import annotations

import ast
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.app import DISCLOSURE, PlaygroundController
from labs.ego_life_playground_v0.engine import (
    CUES,
    DEFAULT_INTERVENTIONS,
    EMA_ALPHA,
    EngineInvariantError,
    canonical_hash,
    canonical_json,
    compute_code_path_hash,
    compute_step,
    compute_trace_hash,
    initial_state,
    make_command,
    make_run_metadata,
    state_hash,
)
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore, default_db_path
import labs.ego_life_playground_v0.engine as engine


def _v1_step(
    state=None,
    *,
    run_id="run-v1",
    seed=17,
    cue="resource",
    interventions=None,
    trigger_source="headless_acceptance",
    meta=None,
):
    state = deepcopy(state or engine.initial_state(run_id=run_id))
    meta = deepcopy(meta or engine.make_run_metadata(run_id, seed))
    command = engine.make_command(
        sequence=state["clock"]["global_tick"] + 1,
        cue=cue,
        trigger_source=trigger_source,
        interventions=interventions or engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=state["last_command_hash"],
    )
    return engine.compute_step(state, command, meta), command, meta


def _v1_episode_memory(
    *,
    memory_id,
    action,
    utility,
    source_command_hash,
    source_sequence,
    source_episode_id,
    cue="resource",
    current_goal="stimulation",
):
    return {
        "memory_id": memory_id,
        "kind": "episodic",
        "cue": cue,
        "current_goal": current_goal,
        "action": action,
        "utility": utility,
        "actual_delta": {key: 0.0 for key in engine.STATE_KEYS},
        "source_episode_id": source_episode_id,
        "source_command_hash": source_command_hash,
        "source_sequence": source_sequence,
    }


def _v1_state_before_third_episode(run_id: str) -> dict[str, Any]:
    """Build a valid tick-16 state with matching records from episodes zero and one."""

    state = engine.initial_state(
        {"energy": 0.0, "safety": 0.9, "connection": 0.9, "stimulation": 0.9},
        run_id=run_id,
    )
    state["clock"] = {
        "global_tick": 16,
        "episode_index": 1,
        "episode_id": engine.episode_id_for(run_id, 1),
        "episode_tick": 8,
    }
    state["last_action"] = "forage"
    state["last_command_hash"] = "f" * 64
    state["last_trace_hash"] = "e" * 64
    state["memory"]["episodic"] = [
        _v1_episode_memory(
            memory_id="opaque-episode-zero",
            action="forage",
            utility=0.2,
            source_command_hash="a" * 64,
            source_sequence=1,
            source_episode_id=engine.episode_id_for(run_id, 0),
            current_goal="energy",
        ),
        _v1_episode_memory(
            memory_id="opaque-episode-one",
            action="forage",
            utility=0.2,
            source_command_hash="b" * 64,
            source_sequence=9,
            source_episode_id=engine.episode_id_for(run_id, 1),
            current_goal="energy",
        ),
    ]
    return state


def test_v1_engine_state_run_and_command_schemas_are_canonical():
    state = engine.initial_state(run_id="schema-v1")
    meta = engine.make_run_metadata("schema-v1", 17)
    command = engine.make_command(
        sequence=1,
        cue="resource",
        trigger_source="headless_acceptance",
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )

    assert state["schema_version"] == "ego.life_playground.state.v2"
    assert set(state) == {
        "schema_version",
        "clock",
        "organism",
        "world",
        "current_goal",
        "model",
        "memory",
        "last_action",
        "last_command_hash",
        "last_trace_hash",
    }
    assert state["clock"] == {
        "global_tick": 0,
        "episode_index": 0,
        "episode_id": engine.episode_id_for("schema-v1", 0),
        "episode_tick": 0,
    }
    assert meta["schema_version"] == "ego.life_playground.run.v2"
    assert meta["episode_span_ticks"] == 8
    assert set(command) == {
        "schema_version",
        "sequence",
        "cue",
        "world_event",
        "trigger_source",
        "interventions",
        "prev_command_hash",
        "command_hash",
    }
    assert command["schema_version"] == "ego.life_playground.command.v2"
    assert command["world_event"] == "resource_appears"
    assert command["command_hash"] == engine.canonical_hash(
        {key: value for key, value in command.items() if key != "command_hash"}
    )


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda command: command.update({"selected_action": "forage"}), "schema mismatch"),
        (lambda command: command.pop("trigger_source"), "schema mismatch"),
        (lambda command: command.update({"cue": "future_label"}), "cue is not canonical"),
        (
            lambda command: command["interventions"].update({"update_mode": "sometimes"}),
            "intervention enum",
        ),
        (
            lambda command: command["interventions"].update(
                {"memory_mode": "off", "provenance_mode": "shuffle_projection"}
            ),
            "invalid intervention combination",
        ),
    ],
)
def test_v1_engine_invalid_command_combinations_fail_closed(mutation, match):
    state = engine.initial_state(run_id="invalid")
    meta = engine.make_run_metadata("invalid", 17)
    command = engine.make_command(
        sequence=1,
        cue="resource",
        trigger_source="headless_acceptance",
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    mutation(command)
    if "command_hash" in command:
        command["command_hash"] = engine.canonical_hash(
            {key: value for key, value in command.items() if key != "command_hash"}
        )
    with pytest.raises(engine.EngineInvariantError, match=match):
        engine.compute_step(state, command, meta)


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda state: state["clock"].update({"episode_index": 0.0}), "episode_index.*integer"),
        (lambda state: state["clock"].update({"episode_tick": 0.0}), "episode_tick.*integer"),
        (
            lambda state: state["current_goal"].update({"selected_global_tick": 0.0}),
            "selected_global_tick.*integer",
        ),
        (
            lambda state: state["current_goal"].update({"entry_deficit": 1}),
            "entry_deficit.*float",
        ),
        (lambda state: state["current_goal"].update({"target": 0.71}), "target.*0.72"),
        (
            lambda state: state["current_goal"].update({"selection_reason": "renderer_choice"}),
            "selection_reason.*canonical",
        ),
        (
            lambda state: state["current_goal"].update({"selection_reason": "no_active_deficit"}),
            "active current_goal selection_reason",
        ),
    ],
)
def test_v1_engine_noncanonical_clock_and_goal_state_fail_closed(mutation, match):
    state = engine.initial_state(run_id="invalid-state")
    mutation(state)
    with pytest.raises(engine.EngineInvariantError, match=match):
        _v1_step(state, run_id="invalid-state")


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("producer_function", "forged.compute_step", "producer_function.*canonical"),
        ("aggregation_rule", "post_hoc_best_of_run", "aggregation_rule.*canonical"),
        ("seed", True, "seed.*integer"),
        ("seed", 17.0, "seed.*integer"),
        ("episode_span_ticks", 8.0, "episode_span_ticks.*integer"),
        ("science_weight", False, "science_weight.*integer"),
        ("run_id", 17, "run_id.*string"),
    ],
)
def test_v1_engine_forged_or_noncanonical_run_metadata_fail_closed(field, value, match):
    meta = engine.make_run_metadata("invalid-meta", 17)
    meta[field] = value
    with pytest.raises(engine.EngineInvariantError, match=match):
        _v1_step(run_id="invalid-meta", meta=meta)


@pytest.mark.parametrize("seed", [True, 17.0, "17"])
def test_v1_engine_run_metadata_constructor_rejects_non_integer_seed(seed):
    with pytest.raises(engine.EngineInvariantError, match="seed.*integer"):
        engine.make_run_metadata("invalid-seed", seed)


@pytest.mark.parametrize("sequence", [True, False, 0, -1, 1.0, 1.9, "1"])
def test_v1_command_constructor_rejects_non_integer_or_nonpositive_sequence(sequence):
    with pytest.raises(engine.EngineInvariantError, match="sequence.*positive integer"):
        engine.make_command(
            sequence=sequence,
            cue="resource",
            trigger_source="headless_acceptance",
            interventions=engine.DEFAULT_INTERVENTIONS,
            prev_command_hash=None,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("memory_mode", True),
        ("update_mode", False),
        ("provenance_mode", 1),
    ],
)
def test_v1_command_constructor_rejects_non_string_intervention_enums(field, value):
    interventions = dict(engine.DEFAULT_INTERVENTIONS)
    interventions[field] = value
    with pytest.raises(engine.EngineInvariantError, match="intervention.*string"):
        engine.make_command(
            sequence=1,
            cue="resource",
            trigger_source="headless_acceptance",
            interventions=interventions,
            prev_command_hash=None,
        )


@pytest.mark.parametrize(
    "sequence,prev_command_hash",
    [
        (1, "a" * 64),
        (2, None),
        (2, "not-a-sha256"),
    ],
)
def test_v1_command_constructor_enforces_prev_hash_null_conditions(
    sequence, prev_command_hash
):
    with pytest.raises(engine.EngineInvariantError, match="prev_command_hash"):
        engine.make_command(
            sequence=sequence,
            cue="resource",
            trigger_source="headless_acceptance",
            interventions=engine.DEFAULT_INTERVENTIONS,
            prev_command_hash=prev_command_hash,
        )


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda state: state["organism"].update({"energy": "0.45"}), "organism.*float"),
        (lambda state: state["organism"].update({"energy": math.nan}), "organism.*finite"),
        (lambda state: state["organism"].update({"energy": 1.01}), "organism.*range"),
        (lambda state: state.update({"model": []}), "model.*object"),
        (
            lambda state: state["model"].update(
                {
                    "resource|stimulation": {
                        "forage": {
                            "count": True,
                            "ema_delta": {key: 0.0 for key in engine.STATE_KEYS},
                        }
                    }
                }
            ),
            "model count.*positive integer",
        ),
        (lambda state: state["memory"].update({"episodic": {}}), "episodic.*list"),
        (
            lambda state: state["memory"]["episodic"].append(
                _v1_episode_memory(
                    memory_id="invalid-action",
                    action="renderer_action",
                    utility=0.0,
                    source_command_hash="a" * 64,
                    source_sequence=1,
                    source_episode_id="episode-invalid",
                )
            ),
            "episodic memory action.*canonical",
        ),
        (lambda state: state.update({"last_action": "renderer_action"}), "last_action"),
        (lambda state: state.update({"last_command_hash": "not-a-sha256"}), "last_command_hash"),
        (lambda state: state.update({"last_trace_hash": "not-a-sha256"}), "last_trace_hash"),
    ],
)
def test_v1_engine_full_causal_state_types_fail_closed(mutation, match):
    state = engine.initial_state(run_id="strict-state")
    mutation(state)
    command = engine.make_command(
        sequence=1,
        cue="resource",
        trigger_source="headless_acceptance",
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    with pytest.raises(engine.EngineInvariantError, match=match):
        engine.compute_step(state, command, engine.make_run_metadata("strict-state", 17))


def test_v1_engine_noninitial_state_requires_canonical_action_and_hash_chain():
    first, _, meta = _v1_step(run_id="strict-chain")
    for field, invalid, match in (
        ("last_action", None, "last_action.*non-null"),
        ("last_command_hash", None, "last_command_hash.*non-null"),
        ("last_trace_hash", None, "last_trace_hash.*non-null"),
    ):
        state = deepcopy(first.next_state)
        state[field] = invalid
        command = engine.make_command(
            sequence=2,
            cue="resource",
            trigger_source="headless_acceptance",
            interventions=engine.DEFAULT_INTERVENTIONS,
            prev_command_hash=first.next_state["last_command_hash"],
        )
        with pytest.raises(engine.EngineInvariantError, match=match):
            engine.compute_step(state, command, meta)


def test_v1_engine_rollover_occurs_before_ticks_9_and_17_and_carries_goal():
    state = engine.initial_state(run_id="rollover")
    meta = engine.make_run_metadata("rollover", 17)
    transitions = []
    episode_indices = []
    for _ in range(17):
        result, _, _ = _v1_step(state, run_id="rollover", cue="quiet", meta=meta)
        transitions.append(result.trace["episode_transition"])
        episode_indices.append(result.trace["action_episode"]["episode_index"])
        state = result.next_state

    assert [index for index, transition in enumerate(transitions, 1) if transition["applied"]] == [9, 17]
    assert episode_indices[:8] == [0] * 8
    assert episode_indices[8:16] == [1] * 8
    assert episode_indices[16] == 2
    for tick in (9, 17):
        transition = transitions[tick - 1]
        assert transition["carry_checks"] == {
            "organism_unchanged": True,
            "model_unchanged": True,
            "memory_unchanged": True,
            "current_goal_unchanged": True,
            "command_chain_unchanged": True,
            "trace_chain_unchanged": True,
        }


def test_v1_engine_goal_carries_until_completion_then_enters_homeostasis():
    state = engine.initial_state(
        {"energy": 0.70, "safety": 1.0, "connection": 1.0, "stimulation": 1.0},
        run_id="goal-complete",
    )
    goal_before = deepcopy(state["current_goal"])
    result, _, _ = _v1_step(state, run_id="goal-complete", cue="resource")

    assert goal_before["state_variable"] == "energy"
    assert result.trace["goal_before"] == goal_before
    assert result.trace["goal_progress"]["completed"] is True
    assert result.trace["goal_transition"]["kind"] == "completed_to_homeostasis"
    assert result.next_state["current_goal"]["state_variable"] is None
    assert result.next_state["current_goal"]["status"] == "homeostasis"


def test_v1_engine_homeostasis_reappearing_deficit_becomes_active_goal():
    state = engine.initial_state(
        {key: engine.TARGET_LEVEL for key in engine.STATE_KEYS}, run_id="homeostasis"
    )
    assert state["current_goal"]["status"] == "homeostasis"
    result, _, _ = _v1_step(state, run_id="homeostasis", cue="resource")
    assert result.trace["goal_transition"]["kind"] == "deficit_reappeared"
    assert result.next_state["current_goal"]["status"] == "active"
    assert result.next_state["current_goal"]["selection_reason"] == "deficit_reappeared"


def test_v1_engine_candidate_score_has_frozen_goal_total_memory_cost_components():
    result, _, _ = _v1_step()
    required = {
        "current_goal_deficit_reduction",
        "total_deficit_reduction",
        "memory_bias",
        "untried_bonus",
        "action_cost",
        "deterministic_tie",
        "total_score",
    }
    for candidate in result.trace["candidates"]:
        assert required <= set(candidate)
        expected = (
            candidate["current_goal_deficit_reduction"]
            + candidate["total_deficit_reduction"]
            + candidate["memory_bias"]
            + candidate["untried_bonus"]
            - candidate["action_cost"]
            + candidate["deterministic_tie"]
        )
        assert candidate["total_score"] == pytest.approx(expected, abs=1e-9)
    assert result.trace["context_key"] == "resource|stimulation"


def test_v1_engine_hash_order_is_noncyclic_and_memory_uses_command_provenance():
    result, command, _ = _v1_step()
    trace = result.trace
    assert trace["state_after_hash"] == engine.state_hash(result.next_state)
    assert trace["trace_hash"] == engine.compute_trace_hash(trace)
    assert result.next_state["last_trace_hash"] == trace["trace_hash"]
    assert result.next_state["last_command_hash"] == command["command_hash"]
    written = result.next_state["memory"]["episodic"][-1]
    assert written["source_command_hash"] == command["command_hash"]
    assert "source_trace_hash" not in engine.canonical_json(result.next_state["memory"])


def test_v1_engine_memory_off_zeroes_reads_and_preserves_memory_bytes():
    state = engine.initial_state(run_id="memory-off")
    state["memory"]["episodic"].append(
        _v1_episode_memory(
            memory_id="opaque-a",
            action="approach",
            utility=0.6,
            source_command_hash="a" * 64,
            source_sequence=1,
            source_episode_id="episode-source-a",
        )
    )
    before = engine.canonical_json(state["memory"])
    interventions = dict(engine.DEFAULT_INTERVENTIONS, memory_mode="off")
    result, _, _ = _v1_step(state, run_id="memory-off", interventions=interventions)
    assert engine.canonical_json(result.next_state["memory"]) == before
    assert all(item["memory_bias"] == 0.0 for item in result.trace["candidates"])
    assert all(item["memory_refs"] == [] for item in result.trace["candidates"])
    assert result.trace["memory_update"] == {
        "applied": False,
        "episodic_write": None,
        "consolidation_applied": False,
        "consolidation_refs": [],
        "reason": "memory_disabled",
    }
    assert result.trace["provenance_projection"]["status"] == "memory_disabled"


def test_v1_engine_freeze_updates_preserves_model_and_memory_but_not_clock_or_organism():
    first, _, meta = _v1_step(run_id="freeze")
    before_model = engine.canonical_json(first.next_state["model"])
    before_memory = engine.canonical_json(first.next_state["memory"])
    interventions = dict(engine.DEFAULT_INTERVENTIONS, update_mode="frozen")
    second, _, _ = _v1_step(
        first.next_state, run_id="freeze", cue="contact", interventions=interventions, meta=meta
    )
    assert engine.canonical_json(second.next_state["model"]) == before_model
    assert engine.canonical_json(second.next_state["memory"]) == before_memory
    assert second.next_state["clock"]["global_tick"] == 2
    assert second.next_state["organism"] != first.next_state["organism"]
    assert second.trace["model_update"] == {
        "applied": False,
        "reason": "adaptive_updates_frozen",
        "context_key": second.trace["context_key"],
        "action": second.trace["selected_action"],
    }
    assert second.trace["memory_update"]["reason"] == "adaptive_updates_frozen"


def test_v1_engine_structured_memory_changes_real_score_path_and_selection():
    state = engine.initial_state(run_id="memory-shape")
    without, _, _ = _v1_step(state, run_id="memory-shape")
    state["memory"]["consolidated"].append(
        {
            "memory_id": "opaque-consolidated",
            "kind": "consolidated",
            "key": "resource|stimulation|approach",
            "cue": "resource",
            "current_goal": "stimulation",
            "action": "approach",
            "strength": 0.5,
            "source_command_hashes": ["b" * 64, "c" * 64, "d" * 64],
            "source_episode_ids": ["episode-a", "episode-b", "episode-c"],
            "source_sequences": [1, 9, 17],
            "episode_count": 3,
        }
    )
    with_memory, _, _ = _v1_step(state, run_id="memory-shape")
    approach = next(item for item in with_memory.trace["candidates"] if item["action"] == "approach")
    assert without.trace["selected_action"] == "forage"
    assert approach["memory_bias"] > 0
    assert approach["memory_refs"] == ["b" * 64, "c" * 64, "d" * 64]
    assert with_memory.trace["selected_action"] == "approach"


def test_v1_engine_shuffle_projection_is_causal_read_only_and_opaque_id_invariant():
    state = engine.initial_state(run_id="shuffle")
    state["memory"]["episodic"] = [
        _v1_episode_memory(
            memory_id="opaque-a",
            action="approach",
            utility=0.6,
            source_command_hash="a" * 64,
            source_sequence=1,
            source_episode_id="episode-a",
        ),
        _v1_episode_memory(
            memory_id="opaque-b",
            action="forage",
            utility=-0.4,
            source_command_hash="b" * 64,
            source_sequence=9,
            source_episode_id="episode-b",
        ),
    ]
    renamed = deepcopy(state)
    renamed["memory"]["episodic"][0]["memory_id"] = "unrelated-name-1"
    renamed["memory"]["episodic"][1]["memory_id"] = "unrelated-name-2"
    before = engine.canonical_json(state["memory"])
    renamed_before = engine.canonical_json(renamed["memory"])
    interventions = dict(engine.DEFAULT_INTERVENTIONS, provenance_mode="shuffle_projection")

    shuffled, _, _ = _v1_step(state, run_id="shuffle", interventions=interventions)
    renamed_shuffled, _, _ = _v1_step(renamed, run_id="shuffle", interventions=interventions)

    projection = shuffled.trace["provenance_projection"]
    assert projection["status"] == "applied"
    assert projection["eligibility_count"] == 2
    assert projection["cross_slot_moves"] >= 1
    marginals = projection["marginal_preservation"]
    assert marginals["slot_counts_preserved"] is True
    assert marginals["bundle_multiset_preserved"] is True
    assert marginals["eligible_records_before"] == 2
    assert marginals["eligible_records_after"] == 2
    assert marginals["slot_counts_before"] == marginals["slot_counts_after"]
    assert marginals["bundle_hash_counts_before"] == marginals["bundle_hash_counts_after"]
    assert shuffled.trace["candidates"] == renamed_shuffled.trace["candidates"]
    assert shuffled.trace["selected_action"] == renamed_shuffled.trace["selected_action"]
    assert shuffled.trace["provenance_projection"] == renamed_shuffled.trace["provenance_projection"]
    # The projection is read-only: the only persisted change is the current canonical write.
    assert engine.canonical_json(shuffled.next_state["memory"])[0 : len(before)] != ""
    assert shuffled.next_state["memory"]["episodic"][:2] == state["memory"]["episodic"]
    assert renamed_shuffled.next_state["memory"]["episodic"][:2] == renamed["memory"]["episodic"]
    assert before != renamed_before  # positive control truly changed only opaque IDs


def test_v1_engine_shuffle_marginal_helper_detects_slot_and_bundle_tampering():
    source = {
        "episodic": [
            _v1_episode_memory(
                memory_id="opaque-a",
                action="approach",
                utility=0.6,
                source_command_hash="a" * 64,
                source_sequence=1,
                source_episode_id="episode-a",
            ),
            _v1_episode_memory(
                memory_id="opaque-b",
                action="forage",
                utility=-0.4,
                source_command_hash="b" * 64,
                source_sequence=9,
                source_episode_id="episode-b",
            ),
        ],
        "consolidated": [],
    }
    slot_tampered = deepcopy(source)
    slot_tampered["episodic"][0]["cue"] = "contact"
    slot_report = engine._compute_projection_marginals(source, slot_tampered)
    assert slot_report["slot_counts_preserved"] is False
    assert slot_report["bundle_multiset_preserved"] is True
    assert slot_report["slot_counts_before"] != slot_report["slot_counts_after"]

    bundle_tampered = deepcopy(source)
    bundle_tampered["episodic"][0]["utility"] = 0.123456
    bundle_report = engine._compute_projection_marginals(source, bundle_tampered)
    assert bundle_report["slot_counts_preserved"] is True
    assert bundle_report["bundle_multiset_preserved"] is False
    assert bundle_report["bundle_hash_counts_before"] != bundle_report["bundle_hash_counts_after"]


def test_v1_recovery_frames_drive_derived_state_traces_and_fresh_recovery_callback(tmp_path):
    from labs.ego_life_playground_v0.app import PlaygroundController

    db_path = tmp_path / "continuity.sqlite3"
    store = SQLiteEventStore(db_path)
    controller = PlaygroundController(store, run_id="recovery-frames", seed=17)
    for cue, trigger_source, interventions in (
        ("resource", "ui_step_button", engine.DEFAULT_INTERVENTIONS),
        (
            "novelty",
            "ui_run_button",
            dict(engine.DEFAULT_INTERVENTIONS, update_mode="frozen"),
        ),
    ):
        dispatched = controller.dispatch(
            cue,
            interventions,
            trigger_source=trigger_source,
        )
        assert dispatched.receipt.committed, dispatched.receipt.error
    expected_state = engine.canonical_json(controller.state)
    expected_traces = store.recover_run(controller.run_id).traces
    store.close()

    callbacks = []
    reopened_store = SQLiteEventStore(db_path)
    try:
        reopened = PlaygroundController(
            reopened_store,
            run_id="recovery-frames",
            seed=999,
            on_recovered=callbacks.append,
        )
        assert len(callbacks) == 1
        recovery = callbacks[0]
        assert [type(frame).__name__ for frame in recovery.frames] == [
            "RecoveryFrame",
            "RecoveryFrame",
            "RecoveryFrame",
        ]
        assert [frame.sequence for frame in recovery.frames] == [0, 1, 2]
        assert recovery.frames[0].trace is None
        assert recovery.frames[0].state["clock"]["global_tick"] == 0
        assert [frame.trace for frame in recovery.frames[1:]] == recovery.traces
        assert engine.canonical_json(recovery.frames[-1].state) == engine.canonical_json(
            recovery.state
        )
        assert engine.canonical_json(recovery.state) == expected_state
        assert recovery.traces == expected_traces
        assert engine.canonical_json(reopened.state) == expected_state

        command = recovery.frames[-1].trace["command"]
        assert set(command) == {
            "schema_version",
            "sequence",
            "cue",
            "world_event",
            "trigger_source",
            "interventions",
            "prev_command_hash",
            "command_hash",
        }
        assert command["schema_version"] == "ego.life_playground.command.v2"
        assert command["sequence"] == 2
        assert command["cue"] == "novelty"
        assert command["trigger_source"] == "ui_run_button"
        assert command["interventions"] == {
            "memory_mode": "canonical",
            "update_mode": "frozen",
            "provenance_mode": "canonical",
        }
    finally:
        reopened_store.close()


def test_v1_second_insert_failure_changes_no_state_callback_or_recovery_timeline(
    tmp_path, monkeypatch
):
    from labs.ego_life_playground_v0.app import PlaygroundController

    callbacks = []
    store = SQLiteEventStore(tmp_path / "atomic.sqlite3")
    controller = PlaygroundController(
        store,
        run_id="atomic-v1",
        seed=17,
        on_committed=lambda state, trace: callbacks.append((state, trace)),
    )
    try:
        before_state = engine.canonical_json(controller.state)
        before_frames = store.recover_run(controller.run_id).frames
        store.connection.execute(
            "CREATE TRIGGER force_v1_trace_failure BEFORE INSERT ON traces "
            "BEGIN SELECT RAISE(ABORT, 'forced v1 trace failure'); END"
        )

        failed = controller.dispatch(
            "resource",
            engine.DEFAULT_INTERVENTIONS,
            trigger_source="ui_step_button",
        )

        assert failed.receipt.committed is False
        assert failed.step is None
        assert "forced v1 trace failure" in failed.receipt.error
        assert engine.canonical_json(controller.state) == before_state
        assert controller.last_trace is None
        assert callbacks == []
        assert store.row_counts(controller.run_id) == (0, 0)
        after_recovery = store.recover_run(controller.run_id)
        assert len(before_frames) == len(after_recovery.frames) == 1
        assert after_recovery.frames[0].sequence == 0
        assert after_recovery.frames[0].trace is None
    finally:
        store.close()

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local-app-data"))
    assert default_db_path() == (
        tmp_path / "local-app-data" / "EgoLifePlaygroundV2" / "continuity.sqlite3"
    )


def test_v1_real_tk_run_button_uses_after_then_committed_callback_redraws_once(
    tmp_path, monkeypatch
):
    import tkinter as tk

    from labs.ego_life_playground_v0.app import PlaygroundController, PlaygroundWindow

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk unavailable: {exc}")

    store = SQLiteEventStore(tmp_path / "tk-run.sqlite3")
    try:
        root.withdraw()
        controller = PlaygroundController(store, run_id="tk-run", seed=17)
        initial = deepcopy(controller.state)
        # Keep the second display tick outside this single Tk ``update`` call;
        # the behavior under test is that the first tick is scheduled through
        # ``after(0)`` rather than executed by ``Button.invoke`` itself.
        window = PlaygroundWindow(root, controller, display_interval_ms=1000)
        installed_callback = controller.on_committed
        assert installed_callback is not None
        assert getattr(installed_callback, "__self__", None) is window

        callback_calls = []
        redraw_calls = []
        original_redraw = window.redraw

        def observe_callback(state, trace):
            callback_calls.append((state, trace))
            installed_callback(state, trace)

        def observe_redraw(*args, **kwargs):
            redraw_calls.append((args, kwargs))
            return original_redraw(*args, **kwargs)

        controller.on_committed = observe_callback
        monkeypatch.setattr(window, "redraw", observe_redraw)
        assert window.running is False
        assert store.row_counts(controller.run_id) == (0, 0)

        window.run_button.invoke()
        assert store.row_counts(controller.run_id) == (0, 0)
        root.update()
        assert store.row_counts(controller.run_id) == (1, 1)
        assert len(callback_calls) == 1
        assert len(redraw_calls) == 1
        assert controller.last_trace["trigger_source"] == "ui_run_button"
        assert controller.last_trace["command"]["trigger_source"] == "ui_run_button"

        expected_command = engine.make_command(
            sequence=1,
            cue=window.cue_var.get(),
            trigger_source="ui_run_button",
            interventions=engine.DEFAULT_INTERVENTIONS,
            prev_command_hash=None,
        )
        expected = engine.compute_step(initial, expected_command, controller.run_meta)
        assert engine.canonical_json(controller.state) == engine.canonical_json(expected.next_state)
        assert engine.canonical_json(controller.last_trace) == engine.canonical_json(expected.trace)
        causal_bytes = engine.canonical_json(
            {
                "run_meta": controller.run_meta,
                "state": controller.state,
                "trace": controller.last_trace,
            }
        )
        assert "display_interval" not in causal_bytes
        assert len(window.timeline_tree.get_children()) == 2
        assert len(window.candidate_tree.get_children()) == len(engine.ACTIONS)
        assert '"ui_run_button"' in window.trace_text.get("1.0", tk.END)
        assert "global_tick=1" in window.status_var.get()
        goal = controller.state["current_goal"]
        expected_goal_age = controller.state["clock"]["global_tick"] - goal["selected_global_tick"]
        assert f"goal_age_ticks={expected_goal_age}" in window.goals_text.get("1.0", tk.END)

        store.connection.execute(
            "CREATE TRIGGER force_tk_trace_failure BEFORE INSERT ON traces "
            "BEGIN SELECT RAISE(ABORT, 'forced Tk trace failure'); END"
        )
        monkeypatch.setattr(
            "labs.ego_life_playground_v0.app.messagebox.showerror",
            lambda *_args, **_kwargs: None,
        )

        window.pause_button.invoke()
        assert window.running is False
        window.step_button.invoke()
        assert len(callback_calls) == 1
        assert len(redraw_calls) == 1
        assert store.row_counts(controller.run_id) == (1, 1)
        root.after(35, root.quit)
        root.mainloop()
        assert store.row_counts(controller.run_id) == (1, 1)
    finally:
        try:
            root.destroy()
        finally:
            store.close()


def test_v1_invalid_memory_off_shuffle_ui_combination_fails_paused_without_tk_callback_error(
    tmp_path, monkeypatch
):
    import tkinter as tk

    from labs.ego_life_playground_v0.app import PlaygroundController, PlaygroundWindow

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk unavailable: {exc}")

    store = SQLiteEventStore(tmp_path / "tk-invalid-intervention.sqlite3")
    callback_errors = []
    try:
        root.withdraw()
        root.report_callback_exception = lambda *error: callback_errors.append(error)
        monkeypatch.setattr(
            "labs.ego_life_playground_v0.app.messagebox.showerror",
            lambda *_args, **_kwargs: None,
        )
        controller = PlaygroundController(store, run_id="tk-invalid-intervention", seed=17)
        window = PlaygroundWindow(root, controller, display_interval_ms=1000)

        window.memory_mode_var.set("off")
        window.provenance_mode_var.set("shuffle_projection")
        window.run_button.invoke()
        root.update()

        assert callback_errors == []
        assert window.running is False
        assert window._after_id is None
        assert not window.step_button.instate(["disabled"])
        assert not window.run_button.instate(["disabled"])
        assert window.pause_button.instate(["disabled"])
        assert store.row_counts(controller.run_id) == (0, 0)

        # The real combobox events also keep the two forbidden modes mutually
        # exclusive before dispatch is attempted.
        window.provenance_mode_var.set("canonical")
        window.memory_mode_var.set("off")
        window.memory_mode_box.event_generate("<<ComboboxSelected>>")
        root.update()
        window.provenance_mode_var.set("shuffle_projection")
        window.provenance_mode_box.event_generate("<<ComboboxSelected>>")
        root.update()
        assert window.provenance_mode_var.get() == "shuffle_projection"
        assert window.memory_mode_var.get() == "canonical"
    finally:
        try:
            root.destroy()
        finally:
            store.close()


def test_v1_window_close_cancels_scheduled_run_and_leaves_no_background_command(tmp_path):
    import tkinter as tk

    from labs.ego_life_playground_v0.app import PlaygroundController, PlaygroundWindow

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk unavailable: {exc}")

    store = SQLiteEventStore(tmp_path / "tk-close.sqlite3")
    try:
        root.withdraw()
        controller = PlaygroundController(store, run_id="tk-close", seed=17)
        window = PlaygroundWindow(root, controller, display_interval_ms=10)

        window.run_button.invoke()
        assert window.running is True
        assert window._after_id is not None
        assert store.row_counts(controller.run_id) == (0, 0)

        window.close()

        assert window.running is False
        assert window._after_id is None
        try:
            root_exists = bool(root.winfo_exists())
        except tk.TclError:
            root_exists = False
        assert root_exists is False

        # Exercise the former event source after close where Tcl permits it;
        # the canceled callback must never append a command or trace.
        try:
            root.update_idletasks()
            root.update()
        except tk.TclError:
            pass
        assert window._after_id is None
        assert store.row_counts(controller.run_id) == (0, 0)
    finally:
        try:
            if root.winfo_exists():
                root.destroy()
        except tk.TclError:
            pass
        store.close()


def test_v1_historical_timeline_frame_is_read_only_and_disables_progress_controls(tmp_path):
    import tkinter as tk

    from labs.ego_life_playground_v0.app import PlaygroundController, PlaygroundWindow

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk unavailable: {exc}")

    store = SQLiteEventStore(tmp_path / "tk-history.sqlite3")
    try:
        root.withdraw()
        controller = PlaygroundController(store, run_id="tk-history", seed=17)
        for cue in ("resource", "contact"):
            result = controller.dispatch(
                cue,
                engine.DEFAULT_INTERVENTIONS,
                trigger_source="ui_step_button",
            )
            assert result.receipt.committed, result.receipt.error
        latest_bytes = engine.canonical_json(controller.state)
        recovery = store.recover_run(controller.run_id)
        window = PlaygroundWindow(root, controller, display_interval_ms=10)
        rows = window.timeline_tree.get_children()
        assert len(rows) == 3

        window.timeline_tree.selection_set(rows[0])
        window.timeline_tree.event_generate("<<TreeviewSelect>>")
        root.update()
        assert engine.canonical_json(controller.state) == latest_bytes
        assert window.step_button.instate(["disabled"])
        assert window.run_button.instate(["disabled"])
        assert "read-only" in window.status_var.get().lower()
        initial_energy = recovery.frames[0].state["organism"]["energy"]
        assert window.state_widgets["energy"][1].cget("text") == f"{initial_energy:.3f}"

        window.timeline_tree.selection_set(rows[-1])
        window.timeline_tree.event_generate("<<TreeviewSelect>>")
        root.update()
        assert not window.step_button.instate(["disabled"])
        assert not window.run_button.instate(["disabled"])
    finally:
        try:
            root.destroy()
        finally:
            store.close()


def test_v1_launcher_headless_smoke_reports_continuity_shape(tmp_path, capsys):
    launcher = REPO_ROOT / "scripts/run_ego_life_playground_v0.py"
    spec = importlib.util.spec_from_file_location("run_ego_life_playground_v1_test", launcher)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    result = module.main(
        ["--headless-smoke", "--db", str(tmp_path / "headless-v1.sqlite3"), "--seed", "53"]
    )
    payload = json.loads(capsys.readouterr().out.strip())

    assert result == 0
    assert set(payload) == {
        "run_id",
        "clock",
        "current_goal",
        "selected_action",
        "trace_hash",
        "recovered",
        "frame_count",
        "trigger_source",
        "interventions",
        "science_weight",
    }
    assert payload["clock"] == {
        "global_tick": 1,
        "episode_index": 0,
        "episode_id": engine.episode_id_for(payload["run_id"], 0),
        "episode_tick": 1,
    }
    assert payload["frame_count"] == 2
    assert payload["trigger_source"] == "headless_acceptance"
    assert payload["interventions"] == engine.DEFAULT_INTERVENTIONS
    assert payload["recovered"] is True
    assert payload["science_weight"] == 0
    assert len(payload["trace_hash"]) == 64


def _controller(tmp_path, *, run_id="run-a", seed=17, callback=None):
    store = SQLiteEventStore(tmp_path / "playground.sqlite3")
    controller = PlaygroundController(store, run_id=run_id, seed=seed, on_committed=callback)
    return store, controller


def _commit_one(store, controller, cue="resource", interventions=None):
    result = controller.dispatch(
        cue,
        interventions or DEFAULT_INTERVENTIONS,
        trigger_source="ui_step_button",
    )
    assert result.receipt.committed, result.receipt.error
    assert result.step is not None
    return result


def test_compute_step_is_fully_deterministic():
    state = initial_state(run_id="deterministic")
    meta = make_run_metadata("deterministic", 41)
    command = make_command(
        sequence=1,
        cue="contact",
        trigger_source="headless_acceptance",
        interventions=DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    first = compute_step(deepcopy(state), deepcopy(command), deepcopy(meta))
    second = compute_step(deepcopy(state), deepcopy(command), deepcopy(meta))
    assert canonical_json(first.next_state) == canonical_json(second.next_state)
    assert canonical_json(first.trace) == canonical_json(second.trace)


def test_seed_is_used_by_deterministic_tie_component():
    first, _, _ = _v1_step(seed=1)
    second, _, _ = _v1_step(seed=2)
    first_ties = {
        item["action"]: item["deterministic_tie"] for item in first.trace["candidates"]
    }
    second_ties = {
        item["action"]: item["deterministic_tie"] for item in second.trace["candidates"]
    }
    assert first_ties != second_ties
    assert first.trace["seed"] == 1
    assert second.trace["seed"] == 2


def test_command_contains_only_replay_inputs_and_hash():
    command = make_command(
        sequence=1,
        cue="resource",
        trigger_source="headless_acceptance",
        interventions=DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    assert set(command) == {
        "schema_version",
        "sequence",
        "cue",
        "world_event",
        "trigger_source",
        "interventions",
        "prev_command_hash",
        "command_hash",
    }
    forbidden = {"selected_action", "actual_delta", "state", "candidate", "prediction"}
    assert not (set(command) & forbidden)


def test_prediction_error_updates_tabular_ema():
    result, _, _ = _v1_step(cue="resource")
    update = result.trace["model_update"]
    assert update["applied"] is True
    assert update["alpha"] == EMA_ALPHA
    assert update["new_count"] == 1
    assert any(abs(value) > 0 for value in result.trace["prediction_error"].values())
    entry = result.next_state["model"][result.trace["context_key"]][result.trace["selected_action"]]
    assert entry["count"] == 1
    assert entry["ema_delta"] == result.trace["actual_delta"]


def test_learning_off_reads_but_does_not_change_model_bytes():
    first, _, meta = _v1_step(run_id="freeze-model-read")
    before = canonical_json(first.next_state["model"])
    interventions = dict(DEFAULT_INTERVENTIONS, update_mode="frozen")
    second, _, _ = _v1_step(
        first.next_state,
        run_id="freeze-model-read",
        interventions=interventions,
        meta=meta,
    )
    assert canonical_json(second.next_state["model"]) == before
    assert second.trace["model_update"]["applied"] is False
    selected = next(
        item for item in second.trace["candidates"] if item["action"] == second.trace["selected_action"]
    )
    # Existing estimates remain legal read inputs even when writes are frozen.
    assert selected["model_ref"]["source"] in {"tabular_ema", "hardcoded_prior"}


def test_memory_off_zeroes_bias_refs_and_preserves_memory_bytes():
    state = initial_state(run_id="memory-disabled-v1")
    state["memory"]["consolidated"].append(
        {
            "memory_id": "con-force",
            "kind": "consolidated",
            "key": "resource|stimulation|approach",
            "cue": "resource",
            "current_goal": "stimulation",
            "action": "approach",
            "strength": 0.5,
            "source_command_hashes": ["a" * 64, "b" * 64, "c" * 64],
            "source_episode_ids": ["ep-a", "ep-b", "ep-c"],
            "source_sequences": [1, 9, 17],
            "episode_count": 3,
        }
    )
    before = canonical_json(state["memory"])
    interventions = dict(DEFAULT_INTERVENTIONS, memory_mode="off")
    result, _, _ = _v1_step(
        state,
        run_id="memory-disabled-v1",
        interventions=interventions,
    )
    assert canonical_json(result.next_state["memory"]) == before
    assert all(item["memory_bias"] == 0.0 for item in result.trace["candidates"])
    assert all(item["memory_refs"] == [] for item in result.trace["candidates"])
    assert result.trace["memory_update"]["reason"] == "memory_disabled"


def test_structured_memory_directly_changes_action_score_and_selection():
    state = initial_state(run_id="memory-causal-v1")
    without, _, _ = _v1_step(state, run_id="memory-causal-v1")
    state["memory"]["consolidated"].append(
        {
            "memory_id": "con-force",
            "kind": "consolidated",
            "key": "resource|stimulation|approach",
            "cue": "resource",
            "current_goal": "stimulation",
            "action": "approach",
            "strength": 0.5,
            "source_command_hashes": ["a" * 64, "b" * 64, "c" * 64],
            "source_episode_ids": ["ep-a", "ep-b", "ep-c"],
            "source_sequences": [1, 9, 17],
            "episode_count": 3,
        }
    )
    with_memory, _, _ = _v1_step(state, run_id="memory-causal-v1")
    approach = next(item for item in with_memory.trace["candidates"] if item["action"] == "approach")
    assert without.trace["selected_action"] == "forage"
    assert approach["memory_bias"] > 0
    assert approach["memory_refs"] == ["a" * 64, "b" * 64, "c" * 64]
    assert with_memory.trace["selected_action"] == "approach"


def test_consolidation_requires_three_matching_episodes_and_records_provenance():
    run_id = "consolidate-v1"
    state = _v1_state_before_third_episode(run_id)
    result, command, _ = _v1_step(state, run_id=run_id, cue="resource")
    update = result.trace["memory_update"]
    expected_hashes = ["a" * 64, "b" * 64, command["command_hash"]]
    expected_episode_ids = [engine.episode_id_for(run_id, index) for index in range(3)]
    assert result.trace["episode_transition"]["applied"] is True
    assert result.trace["action_episode"]["episode_index"] == 2
    assert result.trace["selected_action"] == "forage"
    assert update["consolidation_applied"] is True
    assert update["consolidation_refs"] == expected_hashes
    consolidated = result.next_state["memory"]["consolidated"]
    assert len(consolidated) == 1
    assert consolidated[0]["source_command_hashes"] == expected_hashes
    assert consolidated[0]["source_episode_ids"] == expected_episode_ids
    assert consolidated[0]["source_sequences"] == [1, 9, 17]
    assert consolidated[0]["episode_count"] == 3


def test_freeze_updates_blocks_episode_write_and_consolidation_at_threshold():
    run_id = "freeze-before-consolidation-v1"
    state = _v1_state_before_third_episode(run_id)
    before_memory = canonical_json(state["memory"])
    interventions = dict(DEFAULT_INTERVENTIONS, update_mode="frozen")
    result, _, _ = _v1_step(
        state,
        run_id=run_id,
        cue="resource",
        interventions=interventions,
    )
    assert canonical_json(result.next_state["memory"]) == before_memory
    assert result.trace["memory_update"] == {
        "applied": False,
        "episodic_write": None,
        "consolidation_applied": False,
        "consolidation_refs": [],
        "reason": "adaptive_updates_frozen",
    }


def test_trace_has_computed_evidence_provenance_fields():
    result, command, meta = _v1_step(run_id="trace-provenance-v1")
    trace = result.trace
    assert trace["producer_function"].endswith("engine.compute_step")
    assert trace["run_id"] == meta["run_id"]
    assert trace["episode_id"] == trace["action_episode"]["episode_id"]
    assert trace["episode_id"] == result.next_state["clock"]["episode_id"]
    assert trace["global_tick"] == result.next_state["clock"]["global_tick"]
    assert trace["trigger_source"] == command["trigger_source"]
    assert trace["interventions"] == DEFAULT_INTERVENTIONS
    assert trace["input_artifacts"][-1] == f"command:{command['command_hash']}"
    assert trace["aggregation_rule"] == "single_step_deterministic_one_step_argmax"
    assert trace["code_path_hash"] == compute_code_path_hash()
    assert trace["trace_hash"] == compute_trace_hash(trace)
    assert trace["state_after_hash"] == state_hash(result.next_state)


def test_atomic_command_and_trace_commit(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        result = _commit_one(store, controller)
        assert store.row_counts(controller.run_id) == (1, 1)
        assert result.receipt.trace_hash == controller.last_trace["trace_hash"]
    finally:
        store.close()


def test_second_insert_failure_rolls_back_both_rows_and_returns_typed_receipt(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        store.connection.execute(
            "CREATE TRIGGER force_trace_failure BEFORE INSERT ON traces "
            "BEGIN SELECT RAISE(ABORT, 'forced trace failure'); END"
        )
        result = controller.dispatch(
            "resource",
            DEFAULT_INTERVENTIONS,
            trigger_source="ui_step_button",
        )
        assert result.receipt.committed is False
        assert result.receipt.run_id == controller.run_id
        assert result.receipt.sequence == 1
        assert result.receipt.trace_hash is None
        assert "forced trace failure" in result.receipt.error
        assert store.row_counts(controller.run_id) == (0, 0)
    finally:
        store.close()


def test_controller_changes_state_and_callback_only_after_commit(tmp_path):
    callbacks = []
    store, controller = _controller(
        tmp_path,
        callback=lambda state, trace: callbacks.append((state, trace)),
    )
    try:
        before = canonical_json(controller.state)
        store.connection.execute(
            "CREATE TRIGGER force_trace_failure BEFORE INSERT ON traces "
            "BEGIN SELECT RAISE(ABORT, 'forced'); END"
        )
        failed = controller.dispatch(
            "resource",
            DEFAULT_INTERVENTIONS,
            trigger_source="ui_step_button",
        )
        assert failed.receipt.committed is False
        assert canonical_json(controller.state) == before
        assert controller.last_trace is None
        assert callbacks == []
        store.connection.execute("DROP TRIGGER force_trace_failure")
        succeeded = controller.dispatch(
            "resource",
            DEFAULT_INTERVENTIONS,
            trigger_source="ui_step_button",
        )
        assert succeeded.receipt.committed is True
        assert controller.state["clock"]["global_tick"] == 1
        assert controller.last_trace["trigger_source"] == "ui_step_button"
        assert len(callbacks) == 1
    finally:
        store.close()


def test_fresh_store_restart_recomputes_same_state_model_memory_and_trace(tmp_path):
    db_path = tmp_path / "restart.sqlite3"
    store = SQLiteEventStore(db_path)
    controller = PlaygroundController(store, run_id="restart", seed=29)
    _commit_one(store, controller, "resource")
    _commit_one(store, controller, "contact")
    expected_state = canonical_json(controller.state)
    expected_trace = canonical_json(controller.last_trace)
    store.close()

    restarted_store = SQLiteEventStore(db_path)
    try:
        restarted = PlaygroundController(restarted_store, run_id="restart", seed=999)
        assert canonical_json(restarted.state) == expected_state
        assert canonical_json(restarted.last_trace) == expected_trace
        assert restarted.recovery_status == "recomputed 2 command(s)"
    finally:
        restarted_store.close()


def test_stored_action_tamper_even_after_rehash_fails_recovery(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        _commit_one(store, controller)
        row = store.connection.execute(
            "SELECT trace_json FROM traces WHERE run_id = ? AND sequence = 1", (controller.run_id,)
        ).fetchone()
        trace = json.loads(row["trace_json"])
        trace["selected_action"] = "withdraw" if trace["selected_action"] != "withdraw" else "approach"
        trace["trace_hash"] = compute_trace_hash(trace)
        store.connection.execute(
            "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = 1",
            (canonical_json(trace), trace["trace_hash"], controller.run_id),
        )
        with pytest.raises(RecoveryError, match="independent recomputation"):
            store.recover_run(controller.run_id)
    finally:
        store.close()


def test_command_tamper_fails_before_stored_trace_is_accepted(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        _commit_one(store, controller)
        row = store.connection.execute(
            "SELECT command_json FROM commands WHERE run_id = ? AND sequence = 1", (controller.run_id,)
        ).fetchone()
        command = json.loads(row["command_json"])
        command["cue"] = "threat"
        store.connection.execute(
            "UPDATE commands SET command_json = ? WHERE run_id = ? AND sequence = 1",
            (canonical_json(command), controller.run_id),
        )
        with pytest.raises(RecoveryError, match="recomputation failed"):
            store.recover_run(controller.run_id)
    finally:
        store.close()


def test_missing_trace_fails_row_parity(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        _commit_one(store, controller)
        store.connection.execute(
            "DELETE FROM traces WHERE run_id = ? AND sequence = 1", (controller.run_id,)
        )
        with pytest.raises(RecoveryError, match="row parity"):
            store.recover_run(controller.run_id)
    finally:
        store.close()


def test_run_code_path_drift_fails_closed(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        _commit_one(store, controller)
        store.connection.execute(
            "UPDATE runs SET code_path_hash = 'drifted' WHERE run_id = ?", (controller.run_id,)
        )
        with pytest.raises(RecoveryError, match="code-path drift"):
            store.recover_run(controller.run_id)
    finally:
        store.close()


def test_store_source_bytes_participate_in_code_path_hash_and_recovery(tmp_path, monkeypatch):
    store, controller = _controller(tmp_path)
    try:
        _commit_one(store, controller)
        original_hash = compute_code_path_hash()
        original_read_bytes = Path.read_bytes

        def read_with_store_drift(path: Path) -> bytes:
            payload = original_read_bytes(path)
            if path.name == "store.py" and path.parent.name == "ego_life_playground_v0":
                return payload + b"\n# bounded store drift positive control\n"
            return payload

        monkeypatch.setattr(Path, "read_bytes", read_with_store_drift)
        assert compute_code_path_hash() != original_hash
        with pytest.raises(RecoveryError, match="code-path drift"):
            store.recover_run(controller.run_id)
    finally:
        store.close()


def test_export_requires_recovery_and_emits_provenance_jsonl(tmp_path):
    store, controller = _controller(tmp_path)
    try:
        _commit_one(store, controller)
        output = store.export_run(controller.run_id, tmp_path / "trace.jsonl")
        records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
        assert records[0]["record_type"] == "run"
        assert records[0]["producer_function"].endswith("SQLiteEventStore.export_run")
        assert records[0]["code_path_hash"] == compute_code_path_hash()
        assert records[1]["record_type"] == "trace"
        assert records[1]["trace"]["trace_hash"] == controller.last_trace["trace_hash"]
    finally:
        store.close()


def test_export_after_tamper_fails_without_creating_output(tmp_path):
    store, controller = _controller(tmp_path)
    output = tmp_path / "must-not-exist.jsonl"
    try:
        _commit_one(store, controller)
        store.connection.execute(
            "UPDATE commands SET command_hash = 'tampered' WHERE run_id = ? AND sequence = 1",
            (controller.run_id,),
        )
        with pytest.raises(RecoveryError):
            store.export_run(controller.run_id, output)
        assert not output.exists()
    finally:
        store.close()


def test_app_import_is_safe_and_discloses_baseline():
    import tkinter as tk
    import labs.ego_life_playground_v0.app as app

    assert tk._default_root is None
    assert app.PlaygroundController is PlaygroundController
    assert DISCLOSURE == (
        "Deterministic visible microworld + deficit scorer + tabular EMA; "
        "local default-off product surface; science weight 0."
    )


def test_default_database_path_is_outside_repository():
    path = default_db_path().resolve()
    assert REPO_ROOT.resolve() not in path.parents


def test_forbidden_import_and_runtime_surface_ast_scan():
    implementation_paths = [
        REPO_ROOT / "labs/ego_life_playground_v0/__init__.py",
        REPO_ROOT / "labs/ego_life_playground_v0/engine.py",
        REPO_ROOT / "labs/ego_life_playground_v0/store.py",
        REPO_ROOT / "labs/ego_life_playground_v0/app.py",
        REPO_ROOT / "scripts/run_ego_life_playground_v0.py",
    ]
    forbidden_import_roots = {
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http",
        "openai",
        "anthropic",
        "EgoDesktop",
        "EgoOperator",
    }
    for path in implementation_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        assert not (imported & forbidden_import_roots), (path, imported & forbidden_import_roots)


def test_launcher_headless_smoke_uses_real_controller_store_and_recovery(tmp_path, capsys):
    launcher = REPO_ROOT / "scripts/run_ego_life_playground_v0.py"
    spec = importlib.util.spec_from_file_location("run_ego_life_playground_v0_test", launcher)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.main(["--headless-smoke", "--db", str(tmp_path / "smoke.sqlite3"), "--seed", "53"])
    payload = json.loads(capsys.readouterr().out.strip())
    assert result == 0
    assert payload["recovered"] is True
    assert payload["clock"]["global_tick"] == 1
    assert payload["clock"]["episode_tick"] == 1
    assert payload["trigger_source"] == "headless_acceptance"
    assert payload["interventions"] == DEFAULT_INTERVENTIONS
    assert payload["frame_count"] == 2
    assert payload["science_weight"] == 0
    assert len(payload["trace_hash"]) == 64


def test_all_cues_are_callable_through_one_compute_path():
    for cue in CUES:
        result, command, _ = _v1_step(cue=cue)
        assert result.trace["command"] == command
        assert result.trace["producer_function"].endswith("engine.compute_step")
        assert result.trace["cue"] == cue
        assert result.trace["trigger_source"] == "headless_acceptance"
        assert result.next_state["clock"]["global_tick"] == 1


def test_invalid_command_schema_and_hidden_selected_action_are_rejected():
    state = initial_state(run_id="schema")
    meta = make_run_metadata("schema", 1)
    command = make_command(
        sequence=1,
        cue="resource",
        trigger_source="headless_acceptance",
        interventions=DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    command["selected_action"] = "forage"
    with pytest.raises(EngineInvariantError, match="schema mismatch"):
        compute_step(state, command, meta)
