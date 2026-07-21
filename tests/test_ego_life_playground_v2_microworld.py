from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import tkinter as tk

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.controller import PlaygroundController, public_state_projection
from labs.ego_life_playground_v0.microworld import (
    ACTIONS,
    FACING_DELTAS,
    apply_operator_injection,
    initial_world_state,
    make_public_frame,
    policy_observation,
    public_world_projection,
    reset_world_for_life,
    transition_world,
    validate_layout_topology,
    verify_world_state,
)
from labs.ego_life_playground_v0.store import SQLiteEventStore
from labs.ego_life_playground_v0.terminal import TerminalPlayground
from labs.ego_life_playground_v0.visual_console import PlaygroundWindow, build_tk_trace_payload


SCRIPT_PATH = REPO_ROOT / "scripts" / "run_ego_life_playground_v0.py"


def _controller(tmp_path: Path, *, run_id: str = "ui-run") -> tuple[PlaygroundController, SQLiteEventStore]:
    store = SQLiteEventStore(tmp_path / f"{run_id}.sqlite3")
    controller = PlaygroundController(store, run_id=run_id, seed=17, world_seed=30)
    return controller, store


def _spin(root: tk.Tk, *, timeout: float = 1.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        root.update_idletasks()
        root.update()
        time.sleep(0.01)


def _subprocess_terminal(db_path: Path, *commands: str, run_id: str = "subprocess-run") -> list[dict]:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--terminal",
            "--db",
            str(db_path),
            "--run-id",
            run_id,
            "--seed",
            "17",
            "--world-seed",
            "30",
            *sum((["--command", command] for command in commands), []),
        ],
        cwd=str(REPO_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def test_card_a_world_schema_mapping_and_life_reset_are_stable():
    world_l1 = initial_world_state(seed=17, layout_id="p0_cross_v1", life_index=1)
    world_l3 = initial_world_state(seed=17, layout_id="p0_cross_v1", life_index=3)

    verify_world_state(world_l1)
    verify_world_state(world_l3)

    assert world_l1["schema_version"] == "ego.life_playground.microworld.state.v4"
    assert world_l1["trial"]["token_mapping"] == world_l3["trial"]["token_mapping"]
    assert sorted(world_l1["trial"]["token_mapping"]) == ["v0", "v1", "v2", "v3", "v4"]
    assert {item["token"] for item in world_l1["objects_by_cause"].values()} == set(
        world_l1["trial"]["token_mapping"]
    )
    assert reset_world_for_life(world_l1, 3) == world_l3
    assert world_l1["agent"]["position"] != world_l3["agent"]["position"]


def test_card_a_policy_visual_and_observer_frame_stay_split():
    world = initial_world_state(seed=9, layout_id="p2_offset_v1", life_index=1)
    projection = public_world_projection(world)
    frame = make_public_frame(
        {
            "world": world,
            "clock": {"global_tick": 0, "episode_index": 0, "episode_tick": 0, "episode_id": "episode-0"},
            "organism": {"energy": 0.45, "safety": 0.62, "connection": 0.5, "stimulation": 0.43},
            "current_goal": {"status": "explore"},
            "last_action": None,
        }
    )

    flat = {token for row in projection["observation"]["visual"] for token in row}
    assert projection["observation"]["schema_version"] == "ego.life_playground.microworld.observation.v4"
    assert projection["schema_version"] == "ego.life_playground.microworld.public_projection.v2"
    assert projection["world"]["schema_version"] == "ego.life_playground.microworld.state.v4"
    assert projection["observation"]["visual"][2][2] == "self"
    assert flat <= {"self", "empty", "wall", "occluded", "v0", "v1", "v2", "v3", "v4"}
    assert "trial" not in projection["world"]
    assert "objects_by_cause" not in projection["world"]
    assert "objects_by_cause" in frame["world"]
    assert "trial" in frame["world"]


def test_card_a_no_occlusion_ablation_recomputes_visual_without_semantic_inputs():
    world = initial_world_state(seed=3, layout_id="p0_cross_v1", life_index=1)
    world["agent"]["position"] = [4, 3]
    world["agent"]["facing"] = "N"
    world["objects_by_cause"]["resource"]["position"] = [4, 2]
    world["objects_by_cause"]["social"]["position"] = [4, 1]
    used = [[4, 3], [4, 2], [4, 1]]
    walkable = validate_layout_topology(world["layout"])["walkable_cells"]
    for cause in ("novelty", "threat", "shelter"):
        if world["objects_by_cause"][cause]["position"] in used:
            for cell in walkable:
                cell = list(cell)
                if cell not in used:
                    world["objects_by_cause"][cause]["position"] = cell
                    used.append(cell)
                    break
    verify_world_state(world)

    canonical = policy_observation(world, occlusion=True)
    ablated = policy_observation(world, occlusion=False)

    assert canonical["visual"][0][2] == "occluded"
    assert ablated["visual"][0][2] == world["objects_by_cause"]["social"]["token"]
    assert ablated["visual"][2][2] == "self"
    assert "resource" not in json.dumps(ablated, sort_keys=True).lower()


def test_card_a_fixed_metabolism_and_resource_interaction_use_current_world_contract():
    world = initial_world_state(seed=12, layout_id="p2_vertical_v1", life_index=1)
    world["agent"]["position"] = [3, 3]
    world["agent"]["facing"] = "N"
    front = [3 + FACING_DELTAS["N"][0], 3 + FACING_DELTAS["N"][1]]
    world["objects_by_cause"]["resource"]["position"] = front
    reserved = [world["agent"]["position"], front]
    for cause, item in world["objects_by_cause"].items():
        if cause == "resource":
            continue
        if item["position"] in reserved:
            for cell in validate_layout_topology(world["layout"])["walkable_cells"]:
                cell = list(cell)
                if cell not in reserved:
                    item["position"] = cell
                    reserved.append(cell)
                    break
    verify_world_state(world)

    turned_left, left = transition_world(world, "turn_left")
    turned_right, right = transition_world(world, "turn_right")
    rested, rest = transition_world(world, "rest")
    interacted_world, interacted = transition_world(world, "interact")
    blocked_world, blocked = transition_world(world, "move_forward")

    assert left == {"outcome_type": "turned", "direction": "left"}
    assert right == {"outcome_type": "turned", "direction": "right"}
    assert turned_left["agent"]["facing"] == "W"
    assert turned_right["agent"]["facing"] == "E"
    assert rested == world
    assert rest == {"outcome_type": "rested"}
    assert interacted["outcome_type"] == "interacted"
    assert interacted["cause"] == "resource"
    assert interacted_world["objects_by_cause"]["resource"]["spawn_count"] == 1
    assert blocked == {"outcome_type": "blocked", "blocked_by": "object"}
    assert blocked_world["agent"]["position"] == [3, 3]


def test_card_a_terminal_step_run_pause_inspect_inject_save_load_reset_replay(tmp_path: Path):
    controller, store = _controller(tmp_path, run_id="terminal-run")
    export_path = tmp_path / "terminal.trace.jsonl"
    try:
        terminal = TerminalPlayground(controller)

        help_result = terminal.execute("help")
        inspect_result = terminal.execute("inspect")
        step_result = terminal.execute("step")
        run_result = terminal.execute("run 2")
        pause_result = terminal.execute("pause")
        inject_result = terminal.execute("inject threat_nearby")
        save_result = terminal.execute(f"save {export_path}")
        replay_result = terminal.execute("replay")
        reset_result = terminal.execute("reset reset-run")
        load_result = terminal.execute("load terminal-run")

        assert help_result["status"] == "ok"
        assert "run N" in help_result["usage"]
        assert inspect_result["status"] == "ok"
        assert inspect_result["snapshot"]["recovered"] is True
        assert step_result["status"] == "committed"
        assert step_result["snapshot"]["timeline"][-1]["injected_event"] is None
        assert run_result["status"] == "committed"
        assert run_result["ticks_committed"] == 2
        assert pause_result["status"] == "paused"
        assert inject_result["status"] == "committed"
        assert (
            inject_result["snapshot"]["timeline"][-1]["injected_event"]
            == "threat_nearby"
        )
        assert save_result["status"] == "saved"
        assert export_path.exists()
        assert replay_result["status"] == "recomputed"
        assert replay_result["frame_count"] == 5
        assert reset_result["status"] == "reset"
        assert reset_result["run_id"] == "reset-run"
        assert load_result["status"] == "loaded"
        assert load_result["run_id"] == "terminal-run"
    finally:
        store.close()


def test_card_a_terminal_subprocess_restart_and_replay_hashes_match(tmp_path: Path):
    db_path = tmp_path / "terminal-subprocess.sqlite3"
    first = _subprocess_terminal(db_path, "step", "inject resource_appears", "replay", run_id="replay-run")
    second = _subprocess_terminal(db_path, "load replay-run", "replay", run_id="replay-run")

    replay_first = first[-1]
    load_second = second[0]
    replay_second = second[-1]

    assert replay_first["status"] == "recomputed"
    assert load_second["status"] == "loaded"
    assert replay_second["status"] == "recomputed"
    assert replay_first["timeline"] == replay_second["timeline"]
    assert load_second["snapshot"]["timeline"] == replay_first["timeline"]


def test_card_a_headless_launcher_real_controller_store_and_recovery(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--quick-check",
            "--db",
            str(tmp_path / "quick.sqlite3"),
            "--run-id",
            "quick-run",
            "--seed",
            "53",
            "--world-seed",
            "30",
        ],
        cwd=str(REPO_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout.strip())

    assert result.returncode == 0
    assert payload["command_schema_version"] == "ego.life_playground.command.v7"
    assert payload["state_schema_version"] == "ego.life_playground.state.v8"
    assert payload["recovered"] is True
    assert payload["frame_count"] == 2
    assert payload["science_weight"] == 0


def test_card_a_tk_window_step_run_inject_and_visual_split(tmp_path: Path):
    controller, store = _controller(tmp_path, run_id="tk-run")
    try:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            pytest.skip(f"tk unavailable: {exc}")
        root.withdraw()
        window = PlaygroundWindow(root, controller)
        window.display_interval_ms = 5
        try:
            initial_sequence = controller.recovery.frames[-1].sequence
            window.step_button.invoke()
            _spin(root, timeout=0.8)
            assert controller.recovery.frames[-1].sequence == initial_sequence + 1
            assert window.visual_grid_data == controller.last_trace["observation"]["visual"]
            assert window.observer_canvas_data["sequence"] == controller.recovery.frames[-1].sequence

            before_run = controller.recovery.frames[-1].sequence
            window.run_button.invoke()
            _spin(root, timeout=0.8)
            window.pause_button.invoke()
            _spin(root, timeout=0.2)
            assert controller.recovery.frames[-1].sequence >= before_run + 1

            before_inject = deepcopy(controller.last_trace["observation"])
            window.inject_event_var.set("social_signal")
            window.inject_button.invoke()
            _spin(root, timeout=0.8)
            assert controller.last_trace["command"]["injected_event"] == "social_signal"
            assert controller.last_trace["observation"] != before_inject
        finally:
            window.close()
            try:
                root.destroy()
            except tk.TclError:
                pass
    finally:
        store.close()


def test_card_a_build_tk_trace_payload_keeps_injection_semantic_out_of_policy_projection(tmp_path: Path):
    controller, store = _controller(tmp_path, run_id="payload-run")
    try:
        assert controller.dispatch(
            trigger_source="terminal_event", injected_event="resource_appears"
        ).receipt.committed is True
        payload = build_tk_trace_payload(controller.state, controller.last_trace)
        encoded_policy = json.dumps(payload["policy_visual"], sort_keys=True).lower()
        projection = json.dumps(controller.last_trace["policy_projection"], sort_keys=True).lower()

        assert payload["policy_visual"] == controller.last_trace["observation"]
        assert payload["observer_frame"]["world"] == controller.state["world"]
        assert payload["observer_observation_hash"] == payload["observer_frame"]["observation_hash"]
        assert payload["policy_projection_boundary"] == {
            "world_visible_to_policy": False,
            "policy_visual_exact_tokens_only": True,
        }
        assert "resource_appears" not in encoded_policy
        assert "resource_appears" not in projection
        assert "position" not in projection
        assert "layout" not in projection
    finally:
        store.close()


def test_card_a_public_projection_excludes_semantic_path_and_selector_inputs(tmp_path: Path):
    controller, store = _controller(tmp_path, run_id="projection-run")
    try:
        projection = public_state_projection(controller.state)
        encoded_world = json.dumps(projection["world"], sort_keys=True).lower()
        encoded_observation = json.dumps(policy_observation(controller.state["world"]), sort_keys=True).lower()

        assert projection["schema_version"] == "ego.life_playground.public_state_projection.v1"
        assert set(projection) == {"schema_version", "clock", "organism", "current_goal", "world"}
        assert set(projection["world"]) == {"schema_version", "world", "observation"}
        for forbidden in ("resource", "social", "novelty", "threat", "shelter", "path", "mask", "seed"):
            assert forbidden not in encoded_world
            assert forbidden not in encoded_observation
        assert set(controller.last_trace["candidates"] if controller.last_trace else ACTIONS) != set()
    finally:
        store.close()


def test_card_a_operator_injection_relocates_world_only_before_visual_observation():
    world = initial_world_state(seed=5, layout_id="p2_offset_v1", life_index=1)
    before = deepcopy(world["objects_by_cause"]["threat"])
    injected = apply_operator_injection(world, "threat_nearby")
    after = injected["objects_by_cause"]["threat"]
    observation = public_world_projection(injected)["observation"]

    assert after["injection_count"] == before["injection_count"] + 1
    assert after["position"] != before["position"]
    assert "threat" not in json.dumps(observation, sort_keys=True).lower()
    assert observation["schema_version"] == "ego.life_playground.microworld.observation.v4"


def test_card_a_terminal_and_ui_sources_do_not_bypass_controller_or_store():
    terminal_source = (REPO_ROOT / "labs" / "ego_life_playground_v0" / "terminal.py").read_text(
        encoding="utf-8"
    )
    ui_source = (REPO_ROOT / "labs" / "ego_life_playground_v0" / "visual_console.py").read_text(
        encoding="utf-8"
    )
    script_source = SCRIPT_PATH.read_text(encoding="utf-8")

    for source in (terminal_source, ui_source, script_source):
        assert "compute_step(" not in source
        assert "append_step(" not in source
        assert "create_run(" not in source
    assert "controller.dispatch(" in terminal_source
    assert "controller.dispatch(" in ui_source
    assert "PlaygroundController(" in script_source
