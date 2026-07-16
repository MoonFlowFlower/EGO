from __future__ import annotations

from copy import deepcopy
import importlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
import yaml

from labs.ego_life_playground_v0 import engine, microworld
from labs.ego_life_playground_v0 import app as playground_app
from labs.ego_life_playground_v0.app import PlaygroundController, TerminalPlayground
from labs.ego_life_playground_v0.engine import compute_code_path_hash
from labs.ego_life_playground_v0.microworld import (
    ALLOWED_WORLD_EVENTS,
    make_public_frame,
)
from labs.ego_life_playground_v0.store import (
    RecoveryError,
    RecoveryFrame,
    RecoveryResult,
    SQLiteEventStore,
)
from scripts import codex_session_guard


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "run_ego_life_playground_v0.py"


def test_p2_layout_registry_changes_real_topology_and_public_observation():
    default = microworld.initial_world_state(seed=30, layout_id="p0_cross_v1")
    vertical = microworld.initial_world_state(seed=30, layout_id="p2_vertical_v1")
    offset = microworld.initial_world_state(seed=30, layout_id="p2_offset_v1")
    assert [world["layout"]["layout_id"] for world in (default, vertical, offset)] == [
        "p0_cross_v1", "p2_vertical_v1", "p2_offset_v1"
    ]
    assert len({tuple(world["layout"]["base_rows"]) for world in (default, vertical, offset)}) == 3
    assert len({engine.canonical_json(world["layout"]["positions"]) for world in (default, vertical, offset)}) == 3
    assert vertical["public_observation"]["layout_id"] == "p2_vertical_v1"
    microworld.verify_world_state(vertical)

    topologies = [
        microworld.validate_layout_topology(world["layout"])
        for world in (default, vertical, offset)
    ]
    assert [item["walkable_cell_count"] for item in topologies] == [21, 25, 28]
    assert all(item["uses_cell_labels"] is False for item in topologies)
    public_path = microworld.canonical_public_action_path(
        vertical["layout"], vertical["public_observation"]["agent_position"], "forage"
    )
    assert public_path == microworld.canonical_action_path(vertical, "forage")
    relabeled = deepcopy(vertical["layout"])
    relabeled["base_rows"] = [
        "".join("#" if character == "#" else "." for character in row)
        for row in relabeled["base_rows"]
    ]
    assert (
        microworld.canonical_public_action_path(relabeled, "home", "forage")
        == public_path
    )


def _same_schedule_topology_surface(layout_id: str) -> list[dict]:
    run_id = f"p2-topology-hostile-{layout_id}"
    state = engine.initial_state(run_id=run_id, seed=30, layout_id=layout_id)
    meta = engine.make_run_metadata(run_id, 30)
    surface = []
    events = tuple(ALLOWED_WORLD_EVENTS)
    for sequence in range(1, 25):
        event = events[(sequence - 1) % len(events)]
        command = engine.make_command(
            sequence=sequence,
            cue=microworld.cue_for_event(event),
            world_event=event,
            trigger_source="paired_intervention",
            interventions=engine.DEFAULT_INTERVENTIONS,
            prev_command_hash=state["last_command_hash"],
        )
        step = engine.compute_step(state, command, meta)
        surface.append(
            {
                "selected_action": step.trace["selected_action"],
                "candidate_scores": [
                    {
                        "action": candidate["action"],
                        "total_score": candidate["total_score"],
                        "topology_cost": candidate["topology_cost"],
                        "shortest_path_steps": candidate["path"]["shortest_path_steps"],
                        "walkable_cell_count": candidate["path"]["walkable_cell_count"],
                    }
                    for candidate in step.trace["candidates"]
                ],
                "actual_delta": step.trace["actual_delta"],
                "outcome": step.trace["world_outcome"]["value"],
            }
        )
        state = step.next_state
    return surface


def test_p2_same_seed_schedule_has_layout_causal_path_and_score_differences():
    surfaces = {
        layout_id: _same_schedule_topology_surface(layout_id)
        for layout_id in ("p0_cross_v1", "p2_vertical_v1", "p2_offset_v1")
    }
    score_bytes = {
        engine.canonical_json(
            [frame["candidate_scores"] for frame in surface]
        )
        for surface in surfaces.values()
    }
    assert len(score_bytes) == 3


def test_p2_unreachable_grid_targets_are_gated_and_transition_fails_closed(monkeypatch):
    disconnected = {
        "layout_id": "p2_disconnected_hostile_v1",
        "width": 7,
        "height": 5,
        "base_rows": ["#######", "#H.F#A#", "#...#.#", "#...#B#", "#######"],
        "positions": {
            "site_a": [5, 1],
            "fork": [3, 1],
            "site_b": [5, 3],
            "home": [1, 1],
        },
    }
    monkeypatch.setitem(
        microworld.LAYOUTS, disconnected["layout_id"], disconnected
    )
    world = microworld.initial_world_state(
        seed=30, layout_id=disconnected["layout_id"]
    )
    gate = microworld.legal_action_gate(world, engine.ACTIONS)

    assert gate["rule"] == "label_free_grid_topology_reachability_v1"
    assert gate["gated_actions"] == ["approach", "forage"]
    assert gate["legal_actions"] == ["explore", "rest", "withdraw"]
    assert gate["action_paths"]["approach"]["reachable"] is False
    assert gate["action_paths"]["approach"]["shortest_path_steps"] is None
    assert gate["action_paths"]["explore"]["reachable"] is True
    with pytest.raises(ValueError, match="unreachable"):
        microworld.transition_world(
            world,
            "forage",
            source_sequence=1,
            source_episode_id="episode-hostile",
            source_command_hash="a" * 64,
        )

    run_id = "p2-disconnected-hostile"
    state = engine.initial_state(
        run_id=run_id, seed=30, layout_id=disconnected["layout_id"]
    )
    command = engine.make_command(
        sequence=1,
        cue="resource",
        world_event="resource_appears",
        trigger_source="paired_intervention",
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    step = engine.compute_step(state, command, engine.make_run_metadata(run_id, 30))
    assert step.trace["selected_action"] in gate["legal_actions"]
    assert step.trace["gated_actions"] == gate["gated_actions"]
    by_action = {item["action"]: item for item in step.trace["candidates"]}
    assert by_action["forage"]["legal"] is False
    assert by_action["forage"]["gate_reasons"] == ["unreachable_target"]


def test_p2_layout_topology_validation_rejects_non_rectangular_or_blocked_positions():
    malformed = deepcopy(microworld.LAYOUTS["p0_cross_v1"])
    malformed["base_rows"][1] = malformed["base_rows"][1][:-1]
    with pytest.raises(ValueError, match="rectangular"):
        microworld.validate_layout_topology(malformed)

    blocked = deepcopy(microworld.LAYOUTS["p0_cross_v1"])
    blocked["positions"]["site_a"] = [0, 0]
    with pytest.raises(ValueError, match="walkable"):
        microworld.validate_layout_topology(blocked)


def test_p2_first_prediction_error_update_is_bounded_from_decision_prediction():
    state = engine.initial_state(run_id="p2-update", seed=30)
    command = engine.make_command(
        sequence=1,
        cue="resource",
        world_event="resource_appears",
        trigger_source="paired_intervention",
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    step = engine.compute_step(state, command, engine.make_run_metadata("p2-update", 30))
    receipt = step.trace["model_update"]
    assert receipt["prediction_before"] == step.trace["prediction"]
    assert receipt["prediction_error"] == step.trace["prediction_error"]
    assert receipt["model_before_hash"] == step.trace["model_bytes"]["before_hash"]
    assert receipt["model_after_hash"] == step.trace["model_bytes"]["after_hash"]
    for key in engine.STATE_KEYS:
        assert receipt["applied_delta"][key] == pytest.approx(
            engine.EMA_ALPHA * step.trace["prediction_error"][key], abs=1e-6
        )
        assert receipt["prediction_after"][key] == pytest.approx(
            receipt["prediction_before"][key] + receipt["applied_delta"][key], abs=1e-6
        )


def test_p2_consolidation_rebuild_is_deterministic_idempotent_and_source_linked():
    episodic = [
        {
            "memory_id": f"m-{index}", "kind": "episodic", "cue": "resource",
            "current_goal": "energy", "action": "forage", "utility": float(index) / 10,
            "actual_delta": {key: 0.1 for key in engine.STATE_KEYS},
            "source_episode_id": f"episode-{index}", "source_command_hash": f"{index + 1:064x}",
            "source_sequence": index + 1,
        }
        for index in range(3)
    ]
    first = engine.rebuild_consolidated_memory(episodic)
    second = engine.rebuild_consolidated_memory(deepcopy(episodic))
    assert first == second
    assert first[0]["source_episode_ids"] == ["episode-0", "episode-1", "episode-2"]
    assert first[0]["source_command_hashes"] == [f"{index + 1:064x}" for index in range(3)]
    state = engine.initial_state(run_id="p2-lineage-tamper", seed=30)
    state["memory"]["episodic"] = episodic
    state["memory"]["consolidated"] = deepcopy(first)
    state["memory"]["consolidated"][0]["source_command_hashes"][0] = "f" * 64
    command = engine.make_command(
        sequence=1, cue="quiet", world_event="quiet_interval",
        trigger_source="paired_intervention", interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    with pytest.raises(engine.EngineInvariantError, match="canonical rebuild"):
        engine.compute_step(
            state, command, engine.make_run_metadata("p2-lineage-tamper", 30)
        )


def test_p2_freeze_preserves_adaptive_bytes_but_world_and_clock_advance():
    run_id = "p2-freeze"
    meta = engine.make_run_metadata(run_id, 701)
    state = engine.initial_state(run_id=run_id, seed=30, layout_id="p2_offset_v1")
    first_command = engine.make_command(
        sequence=1, cue="resource", world_event="resource_appears",
        trigger_source="paired_intervention", interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    first = engine.compute_step(state, first_command, meta)
    frozen = dict(engine.DEFAULT_INTERVENTIONS, update_mode="frozen")
    second_command = engine.make_command(
        sequence=2, cue="contact", world_event="social_signal",
        trigger_source="paired_intervention", interventions=frozen,
        prev_command_hash=first.next_state["last_command_hash"],
    )
    second = engine.compute_step(first.next_state, second_command, meta)
    assert second.trace["model_bytes"]["changed"] is False
    assert second.trace["memory_bytes"]["changed"] is False
    assert second.next_state["clock"]["global_tick"] == 2
    assert second.next_state["world"]["public_observation"] != first.next_state["world"]["public_observation"]
    assert second.trace["world_event"] == "social_signal"


def test_p2_consolidation_off_is_a_typed_read_projection_not_invalid_persisted_state():
    run_id = "p2-consolidation-off"
    state = engine.initial_state(run_id=run_id, seed=30)
    state["memory"]["episodic"] = [
        {
            "memory_id": f"p2-con-{index}", "kind": "episodic", "cue": "resource",
            "current_goal": "stimulation", "action": "approach", "utility": 0.5,
            "actual_delta": {key: 0.0 for key in engine.STATE_KEYS},
            "source_episode_id": f"episode-{index}", "source_command_hash": f"{index + 11:064x}",
            "source_sequence": index + 1,
        }
        for index in range(3)
    ]
    state["memory"]["consolidated"] = engine.rebuild_consolidated_memory(
        state["memory"]["episodic"]
    )
    meta = engine.make_run_metadata(run_id, 701)
    canonical_command = engine.make_command(
        sequence=1, cue="resource", world_event="resource_appears",
        trigger_source="paired_intervention",
        interventions=dict(engine.DEFAULT_INTERVENTIONS, update_mode="frozen"),
        prev_command_hash=None,
    )
    off_command = engine.make_command(
        sequence=1, cue="resource", world_event="resource_appears",
        trigger_source="paired_intervention",
        interventions=dict(
            engine.DEFAULT_INTERVENTIONS,
            update_mode="frozen",
            consolidation_mode="off_projection",
        ),
        prev_command_hash=None,
    )
    canonical = engine.compute_step(state, canonical_command, meta)
    off = engine.compute_step(state, off_command, meta)
    canonical_approach = next(item for item in canonical.trace["candidates"] if item["action"] == "approach")
    off_approach = next(item for item in off.trace["candidates"] if item["action"] == "approach")
    assert canonical_approach["legacy_memory_bias"] > off_approach["legacy_memory_bias"]
    assert off.trace["provenance_projection"]["status"] == "consolidation_off_projection"
    assert off.trace["memory_bytes"]["changed"] is False
    assert off.next_state["memory"] == state["memory"]


def test_p2_terminal_layout_selection_is_persisted_and_explicit_mismatch_fails(tmp_path):
    database = tmp_path / "layout.sqlite3"
    with SQLiteEventStore(database) as store:
        controller = PlaygroundController(
            store, run_id="p2-layout-run", seed=42, layout_id="p2_vertical_v1"
        )
        assert controller.state["world"]["layout"]["layout_id"] == "p2_vertical_v1"
        committed = TerminalPlayground(controller).execute("step novel_object")
        assert committed["status"] == "committed"
        timeline = committed["snapshot"]["timeline"][-1]
        assert timeline["layout_id"] == "p2_vertical_v1"
        assert set(timeline) >= {
            "prediction_error_l1", "model_count_before", "model_count_after",
            "bounded_update_applied", "consolidation_applied",
            "consolidation_lineage_count", "consolidation_lineage_hashes",
        }
    with SQLiteEventStore(database) as reopened:
        with pytest.raises(engine.EngineInvariantError, match="does not match requested"):
            PlaygroundController(
                reopened, run_id="p2-layout-run", seed=42, layout_id="p2_offset_v1"
            )


def test_p2_cli_stored_layout_mismatch_is_structured_and_fail_closed(tmp_path):
    database = tmp_path / "layout-cli.sqlite3"
    with SQLiteEventStore(database) as store:
        PlaygroundController(
            store,
            run_id="p2-layout-cli-run",
            seed=42,
            layout_id="p2_vertical_v1",
        )

    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--terminal",
            "--db",
            str(database),
            "--run-id",
            "p2-layout-cli-run",
            "--layout",
            "p2_offset_v1",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout.strip())
    assert completed.returncode == 2
    assert completed.stderr == ""
    assert payload == {
        "error": (
            "stored run layout 'p2_vertical_v1' does not match requested "
            "'p2_offset_v1'"
        ),
        "error_code": "controller_construction_failed",
        "layout_id": "p2_offset_v1",
        "run_id": "p2-layout-cli-run",
        "status": "error",
    }


def test_product_policy_tie_seed_is_decoupled_from_private_world_seed(tmp_path):
    run_id = "policy-world-seed-decoupling"
    with SQLiteEventStore(tmp_path / "policy-a.sqlite3") as first_store:
        first = PlaygroundController(first_store, run_id=run_id, seed=101)
        first_private = deepcopy(first.state["world"]["private_dynamics"])
        assert first.run_meta["seed"] == 101
    with SQLiteEventStore(tmp_path / "policy-b.sqlite3") as second_store:
        second = PlaygroundController(second_store, run_id=run_id, seed=202)
        second_private = deepcopy(second.state["world"]["private_dynamics"])
        assert second.run_meta["seed"] == 202

    assert first_private == second_private
    expected = engine.initial_state(
        run_id=run_id, seed=engine.DEFAULT_PRIVATE_WORLD_SEED
    )
    assert first_private == expected["world"]["private_dynamics"]
    with SQLiteEventStore(tmp_path / "world-explicit.sqlite3") as third_store:
        third = PlaygroundController(
            third_store, run_id=run_id, seed=101, world_seed=303
        )
        assert third.run_meta["seed"] == 101
        assert third.state["world"]["private_dynamics"] != first_private


def test_policy_projection_commits_all_dynamic_scorer_inputs_and_excludes_private_world():
    run_id = "complete-policy-projection"
    state_a = engine.initial_state(run_id=run_id, seed=18)
    state_b = deepcopy(state_a)
    private_b = state_b["world"]["private_dynamics"]
    private_b["hidden_regime"] = "site_b_high"
    private_b["rng_state"] = int(private_b["rng_state"]) + 991
    microworld.verify_world_state(state_b["world"])
    command = engine.make_command(
        sequence=1,
        cue="quiet",
        world_event="quiet_interval",
        trigger_source="paired_intervention",
        interventions=dict(engine.DEFAULT_INTERVENTIONS, update_mode="frozen"),
        prev_command_hash=None,
    )
    meta = engine.make_run_metadata(run_id, 701)
    result_a = engine.compute_step(state_a, command, meta)
    result_b = engine.compute_step(state_b, command, meta)

    projection = result_a.trace["policy_projection"]
    non_memory = projection["non_memory"]
    assert projection["resolved_memory_view"] == state_a["memory"]
    assert non_memory["sequence"] == 1
    assert non_memory["policy_tie_seed"] == 701
    assert non_memory["context_key"] == result_a.trace["context_key"]
    assert non_memory["action_paths"] == result_a.trace["action_gate"]["action_paths"]
    assert result_a.trace["policy_projection_hash"] == result_b.trace["policy_projection_hash"]
    assert engine.canonical_json(
        [result_a.trace["candidates"], result_a.trace["selected_action"]]
    ) == engine.canonical_json(
        [result_b.trace["candidates"], result_b.trace["selected_action"]]
    )
    assert microworld.world_hash(state_a["world"]) != microworld.world_hash(
        state_b["world"]
    )


def test_policy_projection_changes_for_resolved_memory_or_policy_tie_seed():
    run_id = "policy-projection-hostile"
    baseline = engine.initial_state(run_id=run_id, seed=18)
    with_memory = deepcopy(baseline)
    with_memory["memory"]["episodic"] = [
        {
            "memory_id": f"policy-memory-{index}",
            "kind": "episodic",
            "cue": "quiet",
            "current_goal": "stimulation",
            "action": "approach",
            "utility": 0.5,
            "actual_delta": {key: 0.0 for key in engine.STATE_KEYS},
            "source_episode_id": f"policy-episode-{index}",
            "source_command_hash": f"{index + 1:064x}",
            "source_sequence": index + 1,
        }
        for index in range(3)
    ]
    with_memory["memory"]["consolidated"] = engine.rebuild_consolidated_memory(
        with_memory["memory"]["episodic"]
    )
    command = engine.make_command(
        sequence=1,
        cue="quiet",
        world_event="quiet_interval",
        trigger_source="paired_intervention",
        interventions=dict(engine.DEFAULT_INTERVENTIONS, update_mode="frozen"),
        prev_command_hash=None,
    )
    baseline_result = engine.compute_step(
        baseline, command, engine.make_run_metadata(run_id, 701)
    )
    memory_result = engine.compute_step(
        with_memory, command, engine.make_run_metadata(run_id, 701)
    )
    other_seed_result = engine.compute_step(
        baseline, command, engine.make_run_metadata(run_id, 702)
    )

    assert (
        baseline_result.trace["policy_projection_hash"]
        != memory_result.trace["policy_projection_hash"]
    )
    assert (
        baseline_result.trace["policy_projection_hash"]
        != other_seed_result.trace["policy_projection_hash"]
    )
    assert (
        baseline_result.trace["policy_non_memory_projection_hash"]
        == memory_result.trace["policy_non_memory_projection_hash"]
    )
    assert (
        baseline_result.trace["policy_non_memory_projection_hash"]
        != other_seed_result.trace["policy_non_memory_projection_hash"]
    )


def test_p0_public_microworld_frame_is_readable_and_contains_no_hidden_or_oracle_fields(tmp_path):
    with SQLiteEventStore(tmp_path / "p0.sqlite3") as store:
        controller = PlaygroundController(store, run_id="p0-public", seed=17)
        terminal = TerminalPlayground(controller)
        stepped = terminal.execute("inject resource_appears")

        assert stepped["status"] == "committed"
        snapshot = stepped["snapshot"]
        world = snapshot["world"]
        assert world["product_clock"]["global_tick"] == 1
        assert world["observation"]["event"] == "resource_appears"
        assert world["agent"]["position"] in {"home", "fork", "site_a", "site_b"}
        assert len(world["map_rows"]) == 5
        assert "@" in world["ascii_map"]
        assert world["objects"]
        assert snapshot["internal_state"] == controller.state["organism"]
        assert snapshot["current_goal"] == controller.state["current_goal"]
        assert len(snapshot["candidates"]) >= 2
        assert snapshot["selected_action"] == controller.last_trace["selected_action"]
        assert snapshot["prediction"] == controller.last_trace["prediction"]
        assert snapshot["prediction_error"] == controller.last_trace["prediction_error"]
        assert snapshot["memory"]["write"] == controller.last_trace["memory_update"]
        assert len(snapshot["state_transition"]["public_after_hash"]) == 64
        assert snapshot["state_transition"]["organism_after"] == controller.state["organism"]
        encoded = json.dumps(world, sort_keys=True).lower()
        assert "hidden_regime" not in encoded
        assert "oracle" not in encoded
        assert "correct_action" not in encoded


def test_p0_terminal_commands_cover_step_run_pause_inspect_inject_save_load_reset_and_replay(tmp_path):
    db_path = tmp_path / "commands.sqlite3"
    export_path = tmp_path / "saved.trace.jsonl"
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(store, run_id="p0-command-run", seed=23)
        terminal = TerminalPlayground(controller)

        assert terminal.execute("pause") == {
            "command": "pause",
            "status": "paused",
            "global_tick": 0,
        }
        assert terminal.execute("step")["snapshot"]["world"]["product_clock"]["global_tick"] == 1
        assert terminal.execute("inject threat_nearby")["snapshot"]["world"]["observation"]["event"] == "threat_nearby"
        ran = terminal.execute("run 7")
        assert ran["status"] == "committed"
        assert ran["ticks_committed"] == 7
        assert ran["snapshot"]["world"]["product_clock"]["global_tick"] == 9
        assert ran["snapshot"]["world"]["product_clock"]["episode_index"] == 1
        inspected = terminal.execute("inspect")
        assert inspected["status"] == "ok"
        assert inspected["snapshot"]["timeline"][-1]["sequence"] == 9
        saved = terminal.execute(f"save {export_path}")
        assert saved["status"] == "saved"
        assert export_path.exists()

        reset = terminal.execute("reset p0-second-run")
        assert reset["status"] == "reset"
        assert controller.run_id == "p0-second-run"
        assert controller.state["clock"]["global_tick"] == 0
        loaded = terminal.execute("load p0-command-run")
        assert loaded["status"] == "loaded"
        assert controller.state["clock"]["global_tick"] == 9
        replayed = terminal.execute("replay")
        assert replayed["status"] == "recomputed"
        assert replayed["frame_count"] == 10
        assert replayed["timeline"][-1]["sequence"] == 9


def test_p0_fresh_process_terminal_load_recomputes_same_durable_timeline(tmp_path):
    db_path = tmp_path / "fresh.sqlite3"
    first = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--db",
            str(db_path),
            "--terminal",
            "--run-id",
            "fresh-process-run",
            "--command",
            "run 10",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    second = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--db",
            str(db_path),
            "--terminal",
            "--run-id",
            "fresh-process-run",
            "--command",
            "replay",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    first_payload = json.loads(first.stdout.strip().splitlines()[-1])
    second_payload = json.loads(second.stdout.strip().splitlines()[-1])
    assert first_payload["snapshot"]["world"]["product_clock"]["global_tick"] == 10
    assert second_payload["status"] == "recomputed"
    assert second_payload["frame_count"] == 11
    assert second_payload["timeline"] == first_payload["snapshot"]["timeline"]


def test_p0_event_set_and_causal_code_hash_are_explicit():
    assert ALLOWED_WORLD_EVENTS == (
        "resource_appears",
        "social_signal",
        "novel_object",
        "threat_nearby",
        "quiet_interval",
    )
    assert make_public_frame.__module__.endswith("microworld")
    assert len(compute_code_path_hash()) == 64


def test_p0_scope_passes_real_committed_phase_c_mutation_admission():
    scope_path = (
        REPO_ROOT
        / "docs/codex/tasks/EGO-LIFE-KERNEL-V2-MICROWORLD-MEMORY-CAUSALITY-001A-MUTATION_SCOPE.yaml"
    )
    scope = yaml.safe_load(scope_path.read_text(encoding="utf-8"))
    assert scope["task_kind"] == "bounded_v2_microworld_implementation"
    assert scope["authority_commit"] == "a34ff6630a6456b9e333199b10ee866d30e1c0cd"
    assert (
        scope["authorized_implementation_targets"]
        == codex_session_guard.PHASE_C_V2_IMPLEMENTATION_TARGETS
    )
    admission = codex_session_guard.validate_phase_c_v2_mutation_admission(
        scope,
        repo=REPO_ROOT,
        itl_repo=Path(r"D:\Project\AIProject\MyProject\intelligence-theory-lab"),
    )
    assert admission["status"] == "pass", admission
    assert admission["errors"] == []


def test_p0_world_event_observation_legality_and_transition_are_canonical_reducer_state(tmp_path):
    with SQLiteEventStore(tmp_path / "causal-world.sqlite3") as store:
        controller = PlaygroundController(store, run_id="causal-world", seed=31)
        initial_world = controller.state["world"]
        assert initial_world["agent"]["position"] == "home"
        assert initial_world["public_observation"]["event"] == "quiet_interval"

        terminal = TerminalPlayground(controller)
        result = terminal.execute("inject resource_appears")
        assert result["status"] == "committed"
        trace = controller.last_trace
        assert trace["command"]["world_event"] == "resource_appears"
        assert trace["world_event"] == "resource_appears"
        assert trace["observation"] == trace["world_observation"]
        assert trace["observation_hash"] == engine.canonical_hash(trace["observation"])
        assert trace["legal_actions"] == list(engine.ACTIONS)
        assert trace["gated_actions"] == []
        assert all(candidate["legal"] is True for candidate in trace["candidates"])
        assert all(candidate["gate_reasons"] == [] for candidate in trace["candidates"])
        assert trace["world_before_hash"] == microworld.world_hash(initial_world)
        assert trace["world_after_hash"] == microworld.world_hash(controller.state["world"])
        assert controller.state["world"]["public_observation"]["event"] == "resource_appears"
        assert result["snapshot"]["decision_observation"] == trace["observation"]
        assert result["snapshot"]["decision_observation_hash"] == trace["observation_hash"]
        assert result["snapshot"]["observation_hash"] == microworld.observation_hash(
            controller.state["world"]["public_observation"]
        )

        reopened = store.recover_run("causal-world")
        assert reopened.state["world"] == controller.state["world"]
        assert reopened.traces[-1]["world_after_hash"] == trace["world_after_hash"]


def test_p0_renderer_uses_recovered_world_state_not_selected_action_posthoc(tmp_path):
    with SQLiteEventStore(tmp_path / "renderer-state.sqlite3") as store:
        controller = PlaygroundController(store, run_id="renderer-state", seed=17)
        TerminalPlayground(controller).execute("inject social_signal")
        recovered_state = controller.recovery.state
        forged_trace = dict(controller.last_trace)
        forged_trace["selected_action"] = "withdraw"
        canonical_frame = make_public_frame(recovered_state, controller.last_trace)
        forged_frame = make_public_frame(recovered_state, forged_trace)
        assert forged_frame == canonical_frame
        assert forged_frame["agent"] == recovered_state["world"]["agent"]
        assert forged_frame["objects"] == recovered_state["world"]["objects"]
        assert forged_frame["observation"] == recovered_state["world"]["public_observation"]


def test_p0_typed_world_event_rehash_tamper_fails_recomputing_replay(tmp_path):
    with SQLiteEventStore(tmp_path / "event-tamper.sqlite3") as store:
        controller = PlaygroundController(store, run_id="event-tamper", seed=17)
        TerminalPlayground(controller).execute("inject resource_appears")
        row = store.connection.execute(
            "SELECT command_json FROM commands WHERE run_id = ? AND sequence = 1",
            (controller.run_id,),
        ).fetchone()
        command = json.loads(row["command_json"])
        command["world_event"] = "threat_nearby"
        command["command_hash"] = engine.canonical_hash(
            {key: value for key, value in command.items() if key != "command_hash"}
        )
        store.connection.execute(
            "UPDATE commands SET command_json = ?, command_hash = ? WHERE run_id = ? AND sequence = 1",
            (
                engine.canonical_json(command),
                command["command_hash"],
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="command recomputation failed"):
            store.recover_run(controller.run_id)


def test_p0_rehashed_persisted_world_state_tamper_fails_recomputing_replay(tmp_path):
    with SQLiteEventStore(tmp_path / "world-tamper.sqlite3") as store:
        controller = PlaygroundController(store, run_id="world-tamper", seed=17)
        TerminalPlayground(controller).execute("step")
        row = store.connection.execute(
            "SELECT initial_state_json FROM runs WHERE run_id = ?", (controller.run_id,)
        ).fetchone()
        initial = json.loads(row["initial_state_json"])
        initial["world"]["agent"]["position"] = "site_b"
        store.connection.execute(
            "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
            (
                engine.canonical_json(initial),
                engine.canonical_hash(initial),
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="command recomputation failed"):
            store.recover_run(controller.run_id)


def test_p0_default_launch_skips_incompatible_latest_but_explicit_load_fails_closed(tmp_path):
    db_path = tmp_path / "compatibility.sqlite3"
    with SQLiteEventStore(db_path) as store:
        compatible = PlaygroundController(store, run_id="compatible", seed=17)
        TerminalPlayground(compatible).execute("step")
        incompatible_meta = engine.make_run_metadata("incompatible-latest", 17)
        incompatible_meta["code_path_hash"] = "0" * 64
        incompatible_state = engine.initial_state(run_id="incompatible-latest")
        store.connection.execute(
            "INSERT INTO runs(run_id, run_meta_json, initial_state_json, initial_state_hash, code_path_hash) "
            "VALUES(?, ?, ?, ?, ?)",
            (
                "incompatible-latest",
                engine.canonical_json(incompatible_meta),
                engine.canonical_json(incompatible_state),
                engine.canonical_hash(incompatible_state),
                "0" * 64,
            ),
        )
        assert store.latest_run_id() == "incompatible-latest"

        default = PlaygroundController(store, seed=999)
        assert default.run_id == "compatible"
        before_hash = engine.state_hash(default.state)
        before_frames = len(default.recovery.frames)
        explicit = TerminalPlayground(default).execute("load incompatible-latest")
        assert explicit["status"] == "error"
        assert "code-path drift" in explicit["error"]
        assert default.run_id == "compatible"
        assert engine.state_hash(default.state) == before_hash
        assert len(default.recovery.frames) == before_frames


def test_p0_default_launch_creates_new_run_when_no_compatible_run_exists(tmp_path):
    db_path = tmp_path / "no-compatible.sqlite3"
    with SQLiteEventStore(db_path) as store:
        meta = engine.make_run_metadata("old-only", 17)
        meta["code_path_hash"] = "f" * 64
        state = engine.initial_state(run_id="old-only")
        store.connection.execute(
            "INSERT INTO runs(run_id, run_meta_json, initial_state_json, initial_state_hash, code_path_hash) "
            "VALUES(?, ?, ?, ?, ?)",
            (
                "old-only",
                engine.canonical_json(meta),
                engine.canonical_json(state),
                engine.canonical_hash(state),
                "f" * 64,
            ),
        )
        controller = PlaygroundController(store, seed=41)
        assert controller.run_id != "old-only"
        assert controller.recovery_status == "new run"
        assert controller.run_meta["code_path_hash"] == compute_code_path_hash()


def test_p0_save_oserror_is_structured_and_preserves_state_and_history(tmp_path):
    with SQLiteEventStore(tmp_path / "save-error.sqlite3") as store:
        controller = PlaygroundController(store, run_id="save-error", seed=17)
        terminal = TerminalPlayground(controller)
        terminal.execute("step")
        state_before = engine.canonical_json(controller.state)
        traces_before = engine.canonical_json(controller.recovery.traces)
        counts_before = store.row_counts(controller.run_id)

        result = terminal.execute(f"save {tmp_path}")
        assert result["status"] == "error"
        assert "OSError" in result["error"] or "PermissionError" in result["error"]
        assert engine.canonical_json(controller.state) == state_before
        assert engine.canonical_json(controller.recovery.traces) == traces_before
        assert store.row_counts(controller.run_id) == counts_before


def test_p0_code_path_manifest_is_exact_and_each_causal_file_is_hash_sensitive(monkeypatch):
    manifest = engine.compute_code_path_manifest()
    assert manifest["schema_version"] == "ego.life_playground.code_path.v3"
    assert [item["path"] for item in manifest["files"]] == [
        "engine.py",
        "microworld.py",
        "claims.py",
        "store.py",
    ]
    assert all(len(item["sha256"]) == 64 for item in manifest["files"])
    baseline = compute_code_path_hash()
    original_read_bytes = Path.read_bytes
    for target in ("engine.py", "microworld.py", "claims.py", "store.py"):
        with monkeypatch.context() as scoped:
            def read_with_drift(path: Path, *, _target: str = target) -> bytes:
                payload = original_read_bytes(path)
                return payload + b"\n# causal positive control\n" if path.name == _target else payload

            scoped.setattr(Path, "read_bytes", read_with_drift)
            assert compute_code_path_hash() != baseline


def _p1_claims_module():
    return importlib.import_module("labs.ego_life_playground_v0.claims")


def _p1_record(
    memory,
    *,
    action: str,
    outcome: float,
    event_id: str,
    episode_id: str,
    tick: int,
):
    claims = _p1_claims_module()
    return claims.record_outcome_evidence(
        memory,
        subject="microworld:opaque_fork",
        predicate="preferred_site_action",
        value=action,
        evidence_strength=outcome,
        event_id=event_id,
        source_episode_id=episode_id,
        source_command_hash=(f"{tick:x}"[-1] * 64),
        source_sequence=tick,
        observed_public_features={
            "agent_position": "fork",
            "visible_object_kinds": ["shelter"],
        },
    )


def test_p1_claims_module_is_a_bound_causal_producer():
    claims_path = REPO_ROOT / "labs/ego_life_playground_v0/claims.py"
    assert claims_path.is_file(), "P1 claims producer does not exist"
    manifest = engine.compute_code_path_manifest()
    assert manifest["schema_version"] == "ego.life_playground.code_path.v3"
    assert [entry["path"] for entry in manifest["files"]] == [
        "engine.py",
        "microworld.py",
        "claims.py",
        "store.py",
    ]


def test_p1_competing_claims_coexist_with_support_and_exact_provenance():
    claims = _p1_claims_module()
    memory = claims.empty_claim_memory()
    memory, first = _p1_record(
        memory,
        action="forage",
        outcome=1.0,
        event_id="event-forage-positive",
        episode_id="episode-a",
        tick=1,
    )
    memory, second = _p1_record(
        memory,
        action="approach",
        outcome=-1.0,
        event_id="event-approach-negative",
        episode_id="episode-b",
        tick=9,
    )

    claims.verify_claim_memory(memory)
    assert first["applied"] is True
    assert second["applied"] is True
    assert len(memory["claim_events"]) == 2
    competing = memory["competing_claims"]
    assert {item["value"] for item in competing} == {"forage", "approach"}
    assert len({item["conflict_set_id"] for item in competing}) == 1
    required = {
        "claim_id",
        "conflict_set_id",
        "subject",
        "predicate",
        "value",
        "support",
        "provenance_event_ids",
        "source_episode_ids",
        "first_seen_tick",
        "last_supported_tick",
    }
    assert all(set(item) == required for item in competing)
    by_value = {item["value"]: item for item in competing}
    assert by_value["forage"]["support"] == 1.0
    assert by_value["forage"]["provenance_event_ids"] == ["event-forage-positive"]
    assert by_value["approach"]["support"] == -1.0
    assert by_value["approach"]["source_episode_ids"] == ["episode-b"]

    retrieval = claims.retrieve_competing_claims(
        memory,
        observation={
            "agent_position": "fork",
            "visible_object_ids": ["shelter"],
            "cue": "quiet",
        },
        current_goal="stimulation",
    )
    assert retrieval["status"] == "retrieved"
    assert {item["value"] for item in retrieval["claims"]} == {
        "forage",
        "approach",
    }
    assert retrieval["support_margin"] == 2.0
    assert retrieval["provenance_event_ids"] == [
        "event-approach-negative",
        "event-forage-positive",
    ]


def test_p1_shuffle_provenance_moves_only_lineage_and_recomputes_support():
    claims = _p1_claims_module()
    memory = claims.empty_claim_memory()
    memory, _ = _p1_record(
        memory,
        action="forage",
        outcome=1.0,
        event_id="event-forage-positive",
        episode_id="episode-a",
        tick=1,
    )
    memory, _ = _p1_record(
        memory,
        action="approach",
        outcome=-1.0,
        event_id="event-approach-negative",
        episode_id="episode-b",
        tick=9,
    )
    projected, report = claims.shuffle_provenance(memory, seed=17)

    claims.verify_claim_memory(projected)
    assert report["status"] == "applied"
    assert projected["claim_events"] == memory["claim_events"]
    assert report["event_value_multiset_preserved"] is True
    assert report["non_provenance_claim_fields_preserved"] is True
    assert report["unaffected_fields_hash_before"] == report["unaffected_fields_hash_after"]
    assert report["unaffected_field_count"] > 0
    assert report["changed_json_pointers"]
    assert all(
        any(
            field in pointer
            for field in (
                "/provenance_event_ids",
                "/source_episode_ids",
                "/support",
                "/first_seen_tick",
                "/last_supported_tick",
            )
        )
        for pointer in report["changed_json_pointers"]
    )
    before_support = {item["value"]: item["support"] for item in memory["competing_claims"]}
    after_support = {item["value"]: item["support"] for item in projected["competing_claims"]}
    assert after_support != before_support


def test_p1_relevant_source_deletion_recomputes_claims_but_irrelevant_deletion_is_inert():
    claims = _p1_claims_module()
    memory = claims.empty_claim_memory()
    memory, _ = _p1_record(
        memory,
        action="forage",
        outcome=1.0,
        event_id="event-relevant",
        episode_id="episode-relevant",
        tick=1,
    )
    memory, _ = _p1_record(
        memory,
        action="approach",
        outcome=-1.0,
        event_id="event-other",
        episode_id="episode-other",
        tick=9,
    )

    deleted, relevant_report = claims.delete_sources(
        memory, event_ids=["event-relevant"]
    )
    irrelevant, irrelevant_report = claims.delete_sources(
        memory, source_episode_ids=["episode-not-present"]
    )
    claims.verify_claim_memory(deleted)
    assert relevant_report["deleted_event_ids"] == ["event-relevant"]
    assert {item["value"] for item in deleted["competing_claims"]} == {"approach"}
    assert irrelevant == memory
    assert irrelevant_report["deleted_event_ids"] == []


def _p1_step_state(
    state,
    *,
    run_id: str,
    seed: int,
    event: str,
    interventions=None,
):
    meta = engine.make_run_metadata(run_id, seed)
    cue = microworld.cue_for_event(event)
    command = engine.make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        cue=cue,
        world_event=event,
        trigger_source="paired_intervention",
        interventions=interventions or engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=state["last_command_hash"],
    )
    return engine.compute_step(state, command, meta)


def _p1_history(*, run_id: str, seed: int):
    state = engine.initial_state(
        {
            "energy": 0.4,
            "safety": 0.2,
            "connection": 0.0,
            "stimulation": 0.0,
        },
        run_id=run_id,
        seed=seed,
    )
    state["world"]["agent"]["position"] = "site_a"
    state["world"]["public_observation"]["agent_position"] = "site_a"
    microworld.verify_world_state(state["world"])
    traces = []
    for event in ("resource_appears", "social_signal"):
        step = _p1_step_state(
            state,
            run_id=run_id,
            seed=seed,
            event=event,
        )
        state = step.next_state
        traces.append(step.trace)
    return state, traces


def _p1_paired_checkpoint_states():
    history_a, traces_a = _p1_history(run_id="history-a", seed=18)
    history_b, traces_b = _p1_history(run_id="history-b", seed=19)
    base_a = engine.initial_state(run_id="paired-a", seed=18)
    base_b = engine.initial_state(run_id="paired-b", seed=19)
    base_a["memory"] = deepcopy(history_a["memory"])
    base_b["memory"] = deepcopy(history_b["memory"])
    return base_a, base_b, traces_a, traces_b


def test_p1_hidden_regime_is_persisted_but_excluded_from_policy_and_renderer():
    state = engine.initial_state(
        {
            "energy": 0.0,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.9,
        },
        run_id="p1-hidden",
        seed=18,
    )
    oracle = microworld.oracle_evidence_record(state["world"])
    assert state["world"]["private_dynamics"]["hidden_regime"] in {
        "site_a_high",
        "site_b_high",
    }
    assert type(state["world"]["private_dynamics"]["rng_state"]) is int
    assert state["world"]["private_dynamics"]["outcome_history"] == []
    assert oracle["namespace"] == "evidence_oracle_only"
    assert oracle["correct_action"] in {"forage", "approach"}

    step = _p1_step_state(
        state,
        run_id="p1-hidden",
        seed=18,
        event="resource_appears",
    )
    encoded_policy = engine.canonical_json(step.trace["policy_projection"]).lower()
    encoded_non_memory = engine.canonical_json(
        step.trace["policy_non_memory_projection"]
    ).lower()
    encoded_frame = json.dumps(
        make_public_frame(step.next_state, step.trace), sort_keys=True
    ).lower()
    for forbidden in (
        "hidden_regime",
        "rng_state",
        "correct_action",
        "future_outcome",
        "reward_label",
        "oracle",
    ):
        assert forbidden not in encoded_policy
        assert forbidden not in encoded_non_memory
        assert forbidden not in encoded_frame
    assert step.trace["world_outcome"]["revealed_after_selection"] is True
    assert step.trace["world_outcome"]["value"] in {-1.0, 1.0}
    assert step.trace["claim_update"]["applied"] is True


def test_p1_public_renderer_bytes_are_invariant_to_private_world_only_changes():
    state_a = engine.initial_state(run_id="p1-public-frame-private-a", seed=18)
    state_b = deepcopy(state_a)
    private = state_b["world"]["private_dynamics"]
    private["hidden_regime"] = "site_b_high"
    private["rng_state"] = int(private["rng_state"]) + 991
    private["visit_count"] = 1
    private["outcome_history"] = [
        {
            "selected_action": "approach",
            "visited_site": "site_b",
            "outcome": 1.0,
            "source_sequence": 1,
            "source_episode_id": state_b["clock"]["episode_id"],
            "source_command_hash": "a" * 64,
        }
    ]
    microworld.verify_world_state(state_b["world"])
    assert microworld.world_hash(state_a["world"]) != microworld.world_hash(
        state_b["world"]
    )
    assert engine.canonical_json(make_public_frame(state_a)) == engine.canonical_json(
        make_public_frame(state_b)
    )


def test_p1_normal_terminal_and_tk_payloads_are_invariant_to_private_only_changes():
    before_a = engine.initial_state(run_id="p1-public-payload", seed=18)
    result = _p1_step_state(
        before_a,
        run_id="p1-public-payload",
        seed=18,
        event="quiet_interval",
    )
    after_a = result.next_state
    trace_a = result.trace
    before_b = deepcopy(before_a)
    after_b = deepcopy(after_a)

    def replace_private_history(state, *, salt: int) -> None:
        private = state["world"]["private_dynamics"]
        private["hidden_regime"] = (
            "site_b_high"
            if private["hidden_regime"] == "site_a_high"
            else "site_a_high"
        )
        private["rng_state"] = int(private["rng_state"]) + salt
        private["visit_count"] = 1
        private["outcome_history"] = [
            {
                "selected_action": "forage",
                "visited_site": "site_a",
                "outcome": -1.0,
                "source_sequence": 1,
                "source_episode_id": state["clock"]["episode_id"],
                "source_command_hash": f"{salt:064x}",
            }
        ]
        microworld.verify_world_state(state["world"])

    replace_private_history(before_b, salt=991)
    replace_private_history(after_b, salt=992)
    trace_b = deepcopy(trace_a)
    for field, marker in (
        ("state_before_hash", "1"),
        ("decision_state_hash", "2"),
        ("state_after_hash", "3"),
        ("world_before_hash", "4"),
        ("world_decision_hash", "5"),
        ("world_after_hash", "6"),
        ("trace_hash", "7"),
    ):
        trace_b[field] = marker * 64

    def controller(before, after, trace):
        recovery = RecoveryResult(
            run_id="p1-public-payload",
            run_meta={},
            frames=(
                RecoveryFrame(sequence=0, state=before, trace=None),
                RecoveryFrame(sequence=1, state=after, trace=trace),
            ),
            recovered=True,
        )
        return SimpleNamespace(run_id="p1-public-payload", recovery=recovery)

    terminal_a = playground_app.build_terminal_snapshot(
        controller(before_a, after_a, trace_a)
    )
    terminal_b = playground_app.build_terminal_snapshot(
        controller(before_b, after_b, trace_b)
    )
    tk_a = playground_app.build_tk_trace_payload(after_a, trace_a)
    tk_b = playground_app.build_tk_trace_payload(after_b, trace_b)

    assert engine.canonical_json(terminal_a) == engine.canonical_json(terminal_b)
    assert engine.canonical_json(tk_a) == engine.canonical_json(tk_b)
    forbidden_commitments = {
        "trace_hash",
        "state_before_hash",
        "decision_state_hash",
        "state_after_hash",
        "world_before_hash",
        "world_decision_hash",
        "world_after_hash",
    }

    def keys(value):
        if isinstance(value, dict):
            return set(value) | {
                nested
                for item in value.values()
                for nested in keys(item)
            }
        if isinstance(value, list):
            return {nested for item in value for nested in keys(item)}
        return set()

    assert forbidden_commitments.isdisjoint(keys(terminal_a))
    assert forbidden_commitments.isdisjoint(keys(tk_a))


def test_p1_paired_observation_real_histories_change_scores_and_actions_only_through_memory():
    state_a, state_b, traces_a, traces_b = _p1_paired_checkpoint_states()
    assert [trace["selected_action"] for trace in traces_a] == ["forage", "approach"]
    assert [trace["selected_action"] for trace in traces_b] == ["forage", "approach"]
    assert {trace["world_outcome"]["value"] for trace in traces_a} == {-1.0, 1.0}
    assert {trace["world_outcome"]["value"] for trace in traces_b} == {-1.0, 1.0}
    assert engine.canonical_json(state_a["memory"]) != engine.canonical_json(state_b["memory"])
    assert (
        microworld.oracle_evidence_record(state_a["world"])["correct_action"]
        != microworld.oracle_evidence_record(state_b["world"])["correct_action"]
    )

    result_a = _p1_step_state(
        state_a,
        run_id="paired-a",
        seed=101,
        event="quiet_interval",
    )
    result_b = _p1_step_state(
        state_b,
        run_id="paired-b",
        seed=101,
        event="quiet_interval",
    )
    assert result_a.trace["observation_hash"] == result_b.trace["observation_hash"]
    assert (
        result_a.trace["policy_non_memory_projection_hash"]
        == result_b.trace["policy_non_memory_projection_hash"]
    )
    assert result_a.trace["policy_projection_hash"] != result_b.trace["policy_projection_hash"]
    scores_a = {item["action"]: item["total_score"] for item in result_a.trace["candidates"]}
    scores_b = {item["action"]: item["total_score"] for item in result_b.trace["candidates"]}
    assert scores_a != scores_b
    assert result_a.trace["selected_action"] == "forage"
    assert result_b.trace["selected_action"] == "approach"
    assert result_a.trace["claim_retrieval"]["provenance_event_ids"]
    assert result_b.trace["claim_retrieval"]["provenance_event_ids"]


def test_p1_memory_off_removes_paired_history_score_and_action_difference():
    state_a, state_b, _, _ = _p1_paired_checkpoint_states()
    off = dict(engine.DEFAULT_INTERVENTIONS, memory_mode="off")
    result_a = _p1_step_state(
        state_a,
        run_id="paired-a",
        seed=101,
        event="quiet_interval",
        interventions=off,
    )
    result_b = _p1_step_state(
        state_b,
        run_id="paired-b",
        seed=101,
        event="quiet_interval",
        interventions=off,
    )
    assert result_a.trace["policy_projection_hash"] == result_b.trace["policy_projection_hash"]
    assert result_a.trace["candidates"] == result_b.trace["candidates"]
    assert result_a.trace["selected_action"] == result_b.trace["selected_action"]
    assert all(item["memory_bias"] == 0.0 for item in result_a.trace["candidates"])
    assert result_a.trace["claim_retrieval"]["status"] == "memory_disabled"


def test_p1_freeze_updates_preserves_model_claim_and_event_bytes_while_world_transitions():
    state, _, _, _ = _p1_paired_checkpoint_states()
    before_model = engine.canonical_json(state["model"])
    before_memory = engine.canonical_json(state["memory"])
    before_world = engine.canonical_json(state["world"])
    frozen = dict(engine.DEFAULT_INTERVENTIONS, update_mode="frozen")
    result = _p1_step_state(
        state,
        run_id="paired-a",
        seed=101,
        event="quiet_interval",
        interventions=frozen,
    )
    assert engine.canonical_json(result.next_state["model"]) == before_model
    assert engine.canonical_json(result.next_state["memory"]) == before_memory
    assert engine.canonical_json(result.next_state["world"]) != before_world
    assert result.trace["model_bytes"]["before_hash"] == result.trace["model_bytes"]["after_hash"]
    assert result.trace["memory_bytes"]["before_hash"] == result.trace["memory_bytes"]["after_hash"]
    assert result.trace["claim_update"]["reason"] == "adaptive_updates_frozen"
    assert result.trace["world_transition"]["selected_action"] == result.trace["selected_action"]


def test_p1_shuffle_provenance_and_source_deletion_rerun_the_same_checkpoint():
    claims = _p1_claims_module()
    state, _, _, _ = _p1_paired_checkpoint_states()
    canonical = _p1_step_state(
        state,
        run_id="paired-a",
        seed=101,
        event="quiet_interval",
    )
    shuffled = _p1_step_state(
        state,
        run_id="paired-a",
        seed=101,
        event="quiet_interval",
        interventions=dict(
            engine.DEFAULT_INTERVENTIONS, provenance_mode="shuffle_projection"
        ),
    )
    assert shuffled.trace["provenance_projection"]["status"] == "applied"
    assert shuffled.trace["interventions"]["provenance_shuffle_seed"] == "17"
    assert shuffled.trace["provenance_projection"]["seed"] == 17
    assert shuffled.trace["provenance_projection"]["event_value_multiset_preserved"] is True
    assert (
        shuffled.trace["provenance_projection"]["unaffected_fields_hash_before"]
        == shuffled.trace["provenance_projection"]["unaffected_fields_hash_after"]
    )
    assert shuffled.trace["provenance_projection"]["unaffected_field_count"] > 0
    current_event_id = shuffled.trace["claim_update"]["event_id"]
    without_current_event, deletion_after_step = claims.delete_sources(
        shuffled.next_state["memory"], event_ids=[current_event_id]
    )
    assert deletion_after_step["deleted_event_ids"] == [current_event_id]
    assert engine.canonical_json(
        {
            "claim_events": without_current_event["claim_events"],
            "competing_claims": without_current_event["competing_claims"],
        }
    ) == engine.canonical_json(
        {
            "claim_events": state["memory"]["claim_events"],
            "competing_claims": state["memory"]["competing_claims"],
        }
    )
    assert shuffled.trace["claim_retrieval"]["support_by_action"] != canonical.trace[
        "claim_retrieval"
    ]["support_by_action"]

    relevant = next(
        event
        for event in state["memory"]["claim_events"]
        if event["value"] == canonical.trace["selected_action"]
        and event["evidence_strength"] > 0
    )
    deleted_memory, deletion = claims.delete_sources(
        state["memory"], event_ids=[relevant["event_id"]]
    )
    deleted_state = deepcopy(state)
    deleted_state["memory"] = deleted_memory
    deleted = _p1_step_state(
        deleted_state,
        run_id="paired-a",
        seed=101,
        event="quiet_interval",
    )
    assert deletion["deleted_event_ids"] == [relevant["event_id"]]
    assert deleted.trace["policy_non_memory_projection_hash"] == canonical.trace[
        "policy_non_memory_projection_hash"
    ]
    assert deleted.trace["selected_action"] != canonical.trace["selected_action"]


def test_p1_private_world_and_claim_tamper_fail_recomputing_replay(tmp_path):
    with SQLiteEventStore(tmp_path / "p1-tamper.sqlite3") as store:
        controller = PlaygroundController(store, run_id="p1-tamper", seed=18)
        TerminalPlayground(controller).execute("inject resource_appears")
        row = store.connection.execute(
            "SELECT initial_state_json FROM runs WHERE run_id = ?", (controller.run_id,)
        ).fetchone()
        initial = json.loads(row["initial_state_json"])
        private = initial["world"]["private_dynamics"]
        private["hidden_regime"] = (
            "site_b_high"
            if private["hidden_regime"] == "site_a_high"
            else "site_a_high"
        )
        store.connection.execute(
            "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
            (
                engine.canonical_json(initial),
                engine.canonical_hash(initial),
                controller.run_id,
            ),
        )
        with pytest.raises(RecoveryError, match="stored trace differs|command recomputation failed"):
            store.recover_run(controller.run_id)
