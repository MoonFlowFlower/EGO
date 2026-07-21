from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import claims
from labs.ego_life_playground_v0.engine import (
    DEFAULT_INTERVENTIONS,
    EngineInvariantError,
    canonical_hash,
    compute_code_path_hash,
    compute_code_path_manifest,
    compute_step,
    initial_state,
    make_command,
    make_run_metadata,
)
from labs.ego_life_playground_v0.microworld import (
    ACTIONS,
    policy_observation,
    public_world_projection,
    verify_world_state,
)


FORBIDDEN_POLICY_TOKENS = (
    "resource",
    "social",
    "novelty",
    "threat",
    "shelter",
    "injected_event",
    "world_event",
    "layout",
    "position",
    "path",
    "mask",
    "seed",
    "episode",
    "lineage",
    "command_hash",
    "source_command_hash",
    "source_episode_id",
)


def _step(
    state=None,
    *,
    run_id="visual-life",
    seed=17,
    injected_event=None,
    interventions=None,
):
    state = deepcopy(state or initial_state(run_id=run_id))
    meta = make_run_metadata(run_id, seed)
    command = make_command(
        sequence=state["clock"]["global_tick"] + 1,
        trigger_source="headless_acceptance",
        interventions=interventions or DEFAULT_INTERVENTIONS,
        prev_command_hash=state["last_command_hash"],
        injected_event=injected_event,
    )
    return compute_step(state, command, meta), command, meta


def _state_with_resource_ahead(*, run_id="resource-ahead"):
    state = initial_state(
        {
            "energy": 0.10,
            "safety": 0.70,
            "connection": 0.70,
            "stimulation": 0.70,
        },
        run_id=run_id,
    )
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
    observation = public_world_projection(world)["observation"]
    observation_hash = canonical_hash(observation)
    state["current_goal"]["state_variable"] = "energy"
    state["current_goal"]["status"] = "active"
    state["model"] = {
        f"{observation_hash}|energy": {
            "interact": {
                "count": 1,
                "ema_delta": {
                    "energy": 0.40,
                    "safety": 0.0,
                    "connection": 0.0,
                    "stimulation": 0.0,
                },
            }
        }
    }
    state["component_hashes"]["model"] = canonical_hash(state["model"])
    return state, observation


def _state_with_occluded_rear_token(*, run_id="no-occlusion"):
    state = initial_state(run_id=run_id)
    world = deepcopy(state["world"])
    world["agent"]["position"] = [4, 3]
    world["agent"]["facing"] = "N"
    world["objects_by_cause"]["resource"]["position"] = [4, 2]
    world["objects_by_cause"]["social"]["position"] = [4, 1]
    reserved = [[4, 3], [4, 2], [4, 1]]
    for cause in ("novelty", "threat", "shelter"):
        if world["objects_by_cause"][cause]["position"] in reserved:
            for cell in world["layout"]["base_rows"]:
                pass
    walkable = [
        [x, y]
        for y, row in enumerate(world["layout"]["base_rows"])
        for x, ch in enumerate(row)
        if ch != "#"
    ]
    used = {tuple(cell) for cell in reserved}
    for cause in ("novelty", "threat", "shelter"):
        if tuple(world["objects_by_cause"][cause]["position"]) in used:
            for cell in walkable:
                if tuple(cell) not in used:
                    world["objects_by_cause"][cause]["position"] = cell
                    used.add(tuple(cell))
                    break
        else:
            used.add(tuple(world["objects_by_cause"][cause]["position"]))
    verify_world_state(world)
    state["world"] = world
    return state


def test_card_a_schema_versions_and_command_v5_shape():
    state = initial_state(run_id="schema-v3")
    meta = make_run_metadata("schema-v3", 17)
    command = make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
        injected_event="social_signal",
    )

    assert state["schema_version"] == "ego.life_playground.state.v8"
    assert meta["schema_version"] == "ego.life_playground.run.v8"
    assert command["schema_version"] == "ego.life_playground.command.v7"
    assert set(command) == {
        "schema_version",
        "sequence",
        "injected_event",
        "trigger_source",
        "interventions",
        "prev_command_hash",
        "command_hash",
    }
    assert command["injected_event"] == "social_signal"
    assert "cue" not in command
    assert "world_event" not in command


def test_card_a_step_is_deterministic_and_command_contains_only_replay_inputs():
    result_a, command, meta = _step(run_id="deterministic")
    state = initial_state(run_id="deterministic")
    result_b = compute_step(state, deepcopy(command), deepcopy(meta))

    assert result_a.trace["schema_version"] == "ego.life_playground.trace.v13"
    assert result_a.trace["selected_action"] in ACTIONS
    assert {item["action"] for item in result_a.trace["candidates"]} == set(ACTIONS)
    assert result_a.trace["selected_action"] == next(
        item["action"]
        for item in result_a.trace["candidates"]
        if item["selected"]
    )
    assert result_a.trace["trace_hash"] == result_b.trace["trace_hash"]
    assert result_a.next_state == result_b.next_state
    assert "selected_action" not in command
    assert "world_seed" not in command
    assert "life_id" not in command
    assert "semantic_cue" not in command
    assert "legal_mask" not in command
    assert "path" not in command
    assert result_a.trace["candidate_actions"] == list(ACTIONS)
    assert "action_gate" not in result_a.trace
    assert "legal_actions" not in json.dumps(result_a.trace["policy_projection"], sort_keys=True)


def test_card_a_optional_injection_changes_visual_state_but_not_policy_semantics():
    baseline, _, _ = _step(run_id="inject-baseline")
    injected, command, _ = _step(
        run_id="inject-baseline",
        injected_event="threat_nearby",
    )

    assert command["injected_event"] == "threat_nearby"
    assert injected.trace["observation"] != baseline.trace["observation"]
    encoded = json.dumps(injected.trace["policy_projection"], sort_keys=True).lower()
    assert (
        injected.trace["policy_projection"]["observation"]
        != injected.trace["observation"]
    )
    assert injected.trace["observation"] == policy_observation(
        injected.next_state["world"], occlusion=True
    )
    for token in FORBIDDEN_POLICY_TOKENS:
        assert token not in encoded


def test_card_a_interact_applies_fixed_costs_and_cause_delta():
    state, observation = _state_with_resource_ahead()
    result, _, _ = _step(state, run_id="resource-ahead")

    assert result.trace["policy_projection"]["observation"] == observation
    assert result.trace["observation"] == policy_observation(
        result.next_state["world"], occlusion=True
    )
    assert result.trace["selected_action"] == "interact"
    assert result.trace["world_transition"]["outcome_type"] == "interacted"
    assert result.trace["world_transition"]["cause"] == "resource"
    assert result.trace["passive_decay"] == pytest.approx(0.010)
    assert result.trace["action_cost"] == pytest.approx(0.008)
    assert result.trace["actual_delta"] == {
        "energy": pytest.approx(0.262),
        "safety": pytest.approx(0.0),
        "connection": pytest.approx(0.0),
        "stimulation": pytest.approx(0.0),
    }
    assert result.next_state["organism"]["energy"] == pytest.approx(0.362)


def test_card_a_visual_context_model_update_and_claim_v2_policy_summary():
    memory = claims.empty_claim_memory()
    observation = {
        "schema_version": "ego.life_playground.microworld.observation.v4",
        "visual": [
            ["wall", "wall", "wall", "wall", "wall"],
            ["wall", "empty", "v0", "empty", "wall"],
            ["wall", "empty", "self", "empty", "wall"],
            ["wall", "empty", "empty", "empty", "wall"],
            ["wall", "wall", "wall", "wall", "wall"],
        ],
    }
    observed_public_features = {
        "observation_hash": canonical_hash(observation),
        "current_goal": "energy",
        "visual": observation["visual"],
        "interoception_delta": {
            "energy": 0.262,
            "safety": 0.0,
            "connection": 0.0,
            "stimulation": 0.0,
        },
    }
    memory, _ = claims.record_outcome_evidence(
        memory,
        subject="visual_context",
        predicate="preferred_action",
        value="interact",
        evidence_strength=0.8,
        event_id="claim-event-a",
        source_episode_id="episode-000001",
        source_command_hash="a" * 64,
        source_sequence=1,
        observed_public_features=observed_public_features,
    )
    memory, _ = claims.record_outcome_evidence(
        memory,
        subject="visual_context",
        predicate="preferred_action",
        value="rest",
        evidence_strength=0.2,
        event_id="claim-event-b",
        source_episode_id="episode-000001",
        source_command_hash="b" * 64,
        source_sequence=2,
        observed_public_features=observed_public_features,
    )

    retrieval = claims.retrieve_competing_claims(
        memory,
        observation=observation,
        current_goal="energy",
    )

    assert claims.CLAIM_MEMORY_SCHEMA_VERSION == "ego.life_playground.claim_memory.v2"
    assert claims.CLAIM_EVENT_SCHEMA_VERSION == "ego.life_playground.claim_event.v2"
    assert claims.CLAIM_RETRIEVAL_SCHEMA_VERSION == "ego.life_playground.claim_retrieval.v2"
    assert retrieval["schema_version"] == "ego.life_playground.claim_retrieval.v2"
    assert retrieval["support_by_action"]["interact"] > retrieval["support_by_action"]["rest"]
    assert claims.memory_bias_for_action(retrieval, "interact") > claims.memory_bias_for_action(
        retrieval, "rest"
    )
    summary_json = json.dumps(retrieval["policy_summary"], sort_keys=True).lower()
    assert "provenance" not in summary_json
    assert "source_episode_id" not in summary_json
    assert "command_hash" not in summary_json


def test_card_a_hash_and_code_path_v4_fail_closed():
    manifest = compute_code_path_manifest()
    assert manifest["schema_version"] == "ego.life_playground.code_path.v9"
    assert {entry["path"] for entry in manifest["files"]} == {
        "engine.py",
        "microworld.py",
        "claims.py",
        "predictive_control.py",
        "survival_learning.py",
        "store.py",
    }

    state = initial_state(run_id="tamper")
    meta = make_run_metadata("tamper", 17)
    command = make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    command["selected_action"] = "interact"
    with pytest.raises(EngineInvariantError, match="schema mismatch"):
        compute_step(state, command, meta)

    drifted = deepcopy(meta)
    drifted["code_path_hash"] = "0" * 64
    with pytest.raises(EngineInvariantError, match="code-path hash"):
        compute_step(state, make_command(
            sequence=1,
            trigger_source="headless_acceptance",
            interventions=DEFAULT_INTERVENTIONS,
            prev_command_hash=None,
        ), drifted)


def test_card_a_claim_feature_schema_and_observation_shape_fail_closed():
    memory = claims.empty_claim_memory()
    observation = {
        "schema_version": "ego.life_playground.microworld.observation.v4",
        "visual": [["wall"] * 5 for _ in range(5)],
    }
    bad_features = {
        "observation_hash": canonical_hash(observation),
        "visual": observation["visual"],
        "current_goal": "energy",
        "interoception_delta": {"energy": 0.0, "safety": 0.0, "connection": 0.0, "stimulation": 0.0},
        "position": [0, 0],
    }
    with pytest.raises(ValueError, match="schema mismatch"):
        claims.record_outcome_evidence(
            memory,
            subject="visual_context",
            predicate="preferred_action",
            value="rest",
            evidence_strength=0.1,
            event_id="claim-bad",
            source_episode_id="episode-1",
            source_command_hash="a" * 64,
            source_sequence=1,
            observed_public_features=bad_features,
        )
    with pytest.raises(ValueError, match="schema mismatch"):
        claims.retrieve_competing_claims(
            memory,
            observation={**observation, "extra": True},
            current_goal="energy",
        )


def test_card_a_memory_off_and_update_frozen_are_load_bearing_and_state_preserving():
    state, _ = _state_with_resource_ahead(run_id="ablations")
    baseline, _, _ = _step(state, run_id="ablations")
    frozen_interventions = dict(DEFAULT_INTERVENTIONS, update_mode="frozen")
    frozen, _, _ = _step(state, run_id="ablations", interventions=frozen_interventions)
    off_interventions = dict(DEFAULT_INTERVENTIONS, memory_mode="off")
    off, _, _ = _step(state, run_id="ablations", interventions=off_interventions)

    assert baseline.trace["model_update"]["applied"] is True
    assert baseline.trace["memory_update"]["applied"] is True
    assert baseline.trace["claim_update"]["applied"] is True

    assert frozen.trace["model_update"]["applied"] is False
    assert frozen.trace["memory_update"]["reason"] == "adaptive_updates_frozen"
    assert frozen.trace["claim_update"]["reason"] == "adaptive_updates_frozen"
    assert frozen.next_state["model"] == state["model"]
    assert frozen.next_state["memory"] == state["memory"]

    assert off.trace["memory_update"]["reason"] == "memory_disabled"
    assert off.trace["claim_update"]["reason"] == "memory_disabled"
    assert off.next_state["memory"] == state["memory"]

    for candidate in baseline.trace["candidates"]:
        action = candidate["action"]
        summary = baseline.trace["policy_projection"]["memory_summary"]
        assert candidate["legacy_memory_bias"] == summary["legacy_bias_by_action"][action]
    encoded = json.dumps(
        baseline.trace["policy_projection"]["memory_summary"], sort_keys=True
    ).lower()
    assert "command_hash" not in encoded
    assert "episode_id" not in encoded
    assert "memory_id" not in encoded


def test_card_a_no_occlusion_ablation_recomputes_actual_behind_cell():
    state = _state_with_occluded_rear_token()
    baseline, _, _ = _step(state, run_id="no-occlusion")
    no_occ, _, _ = _step(
        state,
        run_id="no-occlusion",
        interventions=dict(DEFAULT_INTERVENTIONS, vision_mode="no_occlusion"),
    )

    canonical_observation = policy_observation(state["world"], occlusion=True)
    ablated_observation = policy_observation(state["world"], occlusion=False)
    assert baseline.trace["policy_projection"]["observation"] == canonical_observation
    assert no_occ.trace["policy_projection"]["observation"] == ablated_observation
    assert baseline.trace["policy_projection"]["observation"]["visual"][0][2] == "occluded"
    assert (
        no_occ.trace["policy_projection"]["observation"]["visual"][0][2]
        == state["world"]["objects_by_cause"]["social"]["token"]
    )
    assert baseline.trace["observation"] == policy_observation(
        baseline.next_state["world"], occlusion=True
    )
    assert no_occ.trace["observation"] == policy_observation(
        no_occ.next_state["world"], occlusion=False
    )
    assert baseline.trace["world_before_hash"] == no_occ.trace["world_before_hash"]
    assert baseline.trace["world_decision_hash"] == no_occ.trace["world_decision_hash"]
    assert no_occ.trace["vision_ablation"] == {"mode": "no_occlusion", "applied": True}
