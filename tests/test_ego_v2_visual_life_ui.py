from __future__ import annotations

from copy import deepcopy
import ast
from pathlib import Path
import sqlite3
import sys
import time
import tkinter as tk

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import RecoveryFrame, SQLiteEventStore
from labs.ego_life_playground_v0.visual_console import (
    PlaygroundWindow,
    build_tk_trace_payload,
    recorded_waypoints,
    validate_scheduled_waypoints,
)


ALLOWED_VISUAL_TOKENS = {
    "self",
    "empty",
    "wall",
    "occluded",
    "v0",
    "v1",
    "v2",
    "v3",
    "v4",
}


def _controller_and_store(tmp_path: Path) -> tuple[PlaygroundController, SQLiteEventStore, Path]:
    db_path = tmp_path / "visual-ui.db"
    store = SQLiteEventStore(db_path)
    controller = PlaygroundController(store, run_id="ui-test", seed=17, world_seed=30)
    return controller, store, db_path


def _step_frame(tmp_path: Path) -> RecoveryFrame:
    controller, store, _db_path = _controller_and_store(tmp_path)
    try:
        controller.dispatch(trigger_source="ui_step_button")
        return controller.recovery.frames[-1]
    finally:
        store.close()


def _spin(root: tk.Tk, *, timeout: float = 1.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        root.update_idletasks()
        root.update()
        time.sleep(0.01)


def test_build_tk_trace_payload_keeps_observer_world_and_policy_visual_separate(tmp_path: Path) -> None:
    frame = _step_frame(tmp_path)

    payload = build_tk_trace_payload(frame.state, frame.trace)

    assert payload["policy_visual"] == frame.trace["observation"]
    assert payload["observer_frame"]["world"] == frame.state["world"]
    assert payload["observer_frame"]["observation_hash"] == payload["observer_observation_hash"]
    assert payload["policy_visual"]["visual"] == frame.trace["observation"]["visual"]
    flat = {token for row in payload["policy_visual"]["visual"] for token in row}
    assert flat <= ALLOWED_VISUAL_TOKENS
    forbidden = {"life", "seed", "resource", "social", "novelty", "threat", "shelter"}
    assert flat.isdisjoint(forbidden)
    assert "objects_by_cause" in payload["observer_frame"]["world"]
    assert "provenance_projection" in payload
    assert "policy_projection_hash" in payload
    assert "policy_non_memory_projection_hash" not in payload


def test_recorded_waypoints_fail_closed_on_teleport(tmp_path: Path) -> None:
    frame = _step_frame(tmp_path)
    assert recorded_waypoints(frame)
    with pytest.raises(ValueError, match="teleport|one cell|adjacent"):
        validate_scheduled_waypoints([[0, 0], [2, 0]], [[0, 0], [2, 0]])


def test_tk_step_run_and_inject_use_controller_dispatch_only(tmp_path: Path) -> None:
    controller, store, db_path = _controller_and_store(tmp_path)
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
            assert window.redraw_count >= 1
            assert window.observer_canvas_data["sequence"] == controller.recovery.frames[-1].sequence
            assert window.visual_grid_data == controller.last_trace["observation"]["visual"]

            before_run = controller.recovery.frames[-1].sequence
            window.run_button.invoke()
            _spin(root, timeout=1.0)
            window.pause_button.invoke()
            _spin(root, timeout=0.2)
            assert controller.recovery.frames[-1].sequence >= before_run + 2

            with sqlite3.connect(db_path) as connection:
                command_count = connection.execute(
                    "SELECT COUNT(*) FROM commands WHERE run_id = ?",
                    (controller.run_id,),
                ).fetchone()[0]
            assert command_count >= 3

            previous_trace = deepcopy(controller.last_trace)
            window.inject_event_var.set("threat_nearby")
            window.inject_button.invoke()
            _spin(root, timeout=0.8)
            assert controller.last_trace["command"]["injected_event"] == "threat_nearby"

            window.inject_event_var.set("")
            window.step_button.invoke()
            _spin(root, timeout=0.8)
            assert controller.last_trace["command"]["injected_event"] is None
            assert previous_trace["command"]["injected_event"] is None
        finally:
            window.close()
            try:
                root.destroy()
            except tk.TclError:
                pass
    finally:
        store.close()


def test_visual_console_source_does_not_bypass_controller_path() -> None:
    source = Path("labs/ego_life_playground_v0/visual_console.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_calls = {"compute_step", "transition_world", "append_step", "create_run"}
    assert "cue" not in source
    assert "world_event" not in source
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = None
        if isinstance(node.func, ast.Name):
            target = node.func.id
        elif isinstance(node.func, ast.Attribute):
            target = node.func.attr
        assert target not in forbidden_calls
