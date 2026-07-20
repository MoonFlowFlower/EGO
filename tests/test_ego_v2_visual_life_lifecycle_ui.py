from __future__ import annotations

from copy import deepcopy
import ast
import json
from pathlib import Path
import sys
import time
import tkinter as tk
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.controller import DispatchResult, PlaygroundController
from labs.ego_life_playground_v0.engine import (
    DEFAULT_INTERVENTIONS,
    compute_step,
    episode_id_for,
    initial_state,
    make_command,
    make_run_metadata,
)
from labs.ego_life_playground_v0.microworld import reset_world_for_life
from labs.ego_life_playground_v0.store import CommitReceipt, RecoveryFrame, RecoveryResult, SQLiteEventStore
from labs.ego_life_playground_v0.terminal import TerminalPlayground, build_terminal_snapshot
from labs.ego_life_playground_v0.visual_console import (
    PlaygroundWindow,
    build_advanced_details,
    build_chinese_causal_view,
    build_tk_trace_payload,
)
from tests.test_ego_v2_visual_life_four_life import (
    _command_for,
    _death_ready_state,
    _force_action,
    _respawning_state,
    _run_meta,
)


def _controller_and_store(tmp_path: Path, *, run_id: str = "ui-life") -> tuple[PlaygroundController, SQLiteEventStore, Path]:
    db_path = tmp_path / f"{run_id}.sqlite3"
    store = SQLiteEventStore(db_path)
    controller = PlaygroundController(store, run_id=run_id, seed=17, world_seed=30)
    return controller, store, db_path


def _spin(root: tk.Tk, *, timeout: float = 1.2) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        root.update_idletasks()
        root.update()
        time.sleep(0.01)


def _valid_life_state(
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
    completed_tick_sum = 256 * (life_index - 1)
    completed_respawns = life_index - 1
    state["clock"] = {
        "global_tick": completed_tick_sum + completed_respawns + episode_tick,
        "episode_index": life_index - 1,
        "episode_id": episode_id_for(run_id, life_index - 1),
        "episode_tick": episode_tick,
    }
    state["lifecycle"] = {
        "trial_status": "active",
        "life_index": life_index,
        "awaiting_respawn": False,
        "life_results": [
            {
                "life_index": index,
                "survival_ticks": 256,
                "censored": True,
                "termination": "censored",
            }
            for index in range(1, life_index)
        ],
        "fourth_life_result": None,
    }
    state["last_action"] = "rest"
    state["last_command_hash"] = "a" * 64
    state["last_trace_hash"] = "b" * 64
    state["world"] = reset_world_for_life(state["world"], life_index)
    return state


class _MemoryController:
    def __init__(self, state: dict[str, object], *, run_id: str) -> None:
        self.run_id = run_id
        self.run_meta = _run_meta(run_id)
        self.state = deepcopy(state)
        self.last_trace = None
        self._committed = 0
        self.recovery = RecoveryResult(
            run_id=run_id,
            run_meta=self.run_meta,
            frames=(RecoveryFrame(sequence=0, state=deepcopy(state), trace=None),),
            recovered=True,
        )
        self.on_committed = None
        self.on_recovered = None

    @property
    def committed_count(self) -> int:
        return self._committed

    def dispatch(self, interventions=None, *, trigger_source="ui_step_button", injected_event=None):
        if self.state["lifecycle"]["trial_status"] == "terminal":
            raise RuntimeError("trial is terminal")
        command = make_command(
            sequence=int(self.state["clock"]["global_tick"]) + 1,
            trigger_source=trigger_source,
            interventions=DEFAULT_INTERVENTIONS if interventions is None else interventions,
            prev_command_hash=self.state["last_command_hash"],
            injected_event=injected_event,
        )
        computed = compute_step(self.state, command, self.run_meta)
        self._committed += 1
        self.state = computed.next_state
        self.last_trace = computed.trace
        self.recovery = RecoveryResult(
            run_id=self.run_id,
            run_meta=self.run_meta,
            frames=(
                *self.recovery.frames,
                RecoveryFrame(
                    sequence=command["sequence"],
                    state=deepcopy(self.state),
                    trace=deepcopy(self.last_trace),
                ),
            ),
            recovered=True,
        )
        if self.on_committed is not None:
            self.on_committed(deepcopy(self.state), deepcopy(self.last_trace))
        return DispatchResult(
            receipt=CommitReceipt(
                committed=True,
                run_id=self.run_id,
                sequence=command["sequence"],
                trace_hash=self.last_trace["trace_hash"],
                error=None,
            ),
            step=computed,
        )


def _respawn_recovery(monkeypatch: pytest.MonkeyPatch) -> tuple[RecoveryResult, RecoveryFrame]:
    _force_action(monkeypatch, "turn_left")
    run_id = "respawn-ui"
    awaiting = _respawning_state(monkeypatch, run_id=run_id)
    respawn = compute_step(awaiting, _command_for(awaiting), _run_meta(run_id))
    recovery = RecoveryResult(
        run_id=run_id,
        run_meta=_run_meta(run_id),
        frames=(
            RecoveryFrame(sequence=1, state=awaiting, trace=None),
            RecoveryFrame(sequence=2, state=respawn.next_state, trace=respawn.trace),
        ),
        recovered=True,
    )
    return recovery, recovery.frames[-1]


def _terminal_life_four_recovery(monkeypatch: pytest.MonkeyPatch) -> tuple[RecoveryResult, RecoveryFrame]:
    _force_action(monkeypatch, "rest")
    run_id = "terminal-ui"
    before = _valid_life_state(run_id=run_id, life_index=4, episode_tick=255, energy=0.90)
    terminal = compute_step(before, _command_for(before), _run_meta(run_id))
    recovery = RecoveryResult(
        run_id=run_id,
        run_meta=_run_meta(run_id),
        frames=(
            RecoveryFrame(sequence=1026, state=before, trace=None),
            RecoveryFrame(sequence=terminal.trace["sequence"], state=terminal.next_state, trace=terminal.trace),
        ),
        recovered=True,
    )
    return recovery, recovery.frames[-1]


def test_snapshot_and_timeline_accept_pure_respawn_and_terminal_frames(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    respawn_recovery, respawn_frame = _respawn_recovery(monkeypatch)
    respawn_controller = SimpleNamespace(run_id=respawn_recovery.run_id, recovery=respawn_recovery)

    snapshot = build_terminal_snapshot(respawn_controller)

    assert snapshot["selected_action"] is None
    assert snapshot["decision_observation"] is None
    assert snapshot["candidates"] == []
    assert snapshot["lifecycle"]["life_index"] == 2
    assert snapshot["life_survival"] == [1]
    assert snapshot["transition_kind"] == "respawn"
    assert snapshot["policy_invoked"] is False
    assert snapshot["life_termination"] == {
        "life_index": 1,
        "survival_ticks": 1,
        "censored": False,
        "termination": "death",
    }
    assert snapshot["carry_reset_receipt"] == respawn_frame.trace["carry_reset_receipt"]
    assert snapshot["timeline"][-1]["transition_kind"] == "respawn"
    assert snapshot["timeline"][-1]["policy_invoked"] is False
    assert snapshot["timeline"][-1]["observation"] is None
    assert snapshot["timeline"][-1]["carry_reset_receipt"] == respawn_frame.trace["carry_reset_receipt"]

    terminal_recovery, terminal_frame = _terminal_life_four_recovery(monkeypatch)
    terminal_controller = SimpleNamespace(run_id=terminal_recovery.run_id, recovery=terminal_recovery)
    terminal_snapshot = build_terminal_snapshot(terminal_controller)

    assert terminal_snapshot["lifecycle"]["trial_status"] == "terminal"
    assert terminal_snapshot["life_survival"] == [256, 256, 256, 256]
    assert terminal_snapshot["fourth_life_result"] == {"survival_ticks": 256, "censored": True}
    assert terminal_snapshot["transition_kind"] == "action"
    assert terminal_snapshot["policy_invoked"] is True
    assert terminal_snapshot["life_termination"] == terminal_frame.trace["life_termination"]


def test_terminal_run_counts_committed_steps_and_stops_when_trial_turns_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    del tmp_path
    _force_action(monkeypatch, "rest")
    controller = _MemoryController(
        _valid_life_state(
            run_id="terminal-run-stop",
            life_index=4,
            episode_tick=255,
            energy=0.90,
        ),
        run_id="terminal-run-stop",
    )

    terminal = TerminalPlayground(controller)
    result = terminal.execute("run 5")

    assert result["status"] == "committed"
    assert result["requested_ticks"] == 5
    assert result["ticks_committed"] == 1
    assert result["snapshot"]["lifecycle"]["trial_status"] == "terminal"
    assert result["survival_summary"] == {
        "life_survival": [256, 256, 256, 256],
        "fourth_life_result": {"survival_ticks": 256, "censored": True},
        "trial_status": "terminal",
    }
    assert controller.committed_count == 1


def test_terminal_run_continues_across_respawn_without_resetting_ui_local_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    del tmp_path
    _force_action(monkeypatch, "turn_left")
    controller = _MemoryController(
        _respawning_state(monkeypatch, run_id="terminal-run-respawn"),
        run_id="terminal-run-respawn",
    )

    terminal = TerminalPlayground(controller)
    result = terminal.execute("run 2")

    assert result["status"] == "committed"
    assert result["requested_ticks"] == 2
    assert result["ticks_committed"] == 2
    assert result["snapshot"]["timeline"][-2]["transition_kind"] == "respawn"
    assert result["snapshot"]["timeline"][-2]["policy_invoked"] is False
    assert result["snapshot"]["timeline"][-1]["transition_kind"] == "action"
    assert result["snapshot"]["lifecycle"]["trial_status"] == "active"
    assert result["snapshot"]["lifecycle"]["life_index"] == 2
    assert controller.committed_count == 2


def test_real_controller_sqlite_death_to_respawn_run_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "controller-respawn.sqlite3"
    run_id = "controller-respawn"
    _force_action(monkeypatch, "turn_left")
    with SQLiteEventStore(db_path) as store:
        store.create_run(make_run_metadata(run_id, 17), _death_ready_state(run_id=run_id))
        controller = PlaygroundController(store, run_id=run_id, seed=17, world_seed=30)
        terminal = TerminalPlayground(controller)

        result = terminal.execute("run 2")
        inspect_result = terminal.execute("inspect")

        assert result["status"] == "committed"
        assert result["requested_ticks"] == 2
        assert result["ticks_committed"] == 2
        assert result["snapshot"]["timeline"][-2]["transition_kind"] == "action"
        assert result["snapshot"]["timeline"][-1]["transition_kind"] == "respawn"
        assert inspect_result["snapshot"]["lifecycle"]["life_index"] == 2
        assert inspect_result["snapshot"]["life_survival"] == [1]
        assert inspect_result["snapshot"]["carry_reset_receipt"] is not None
        assert store.connection.execute(
            "SELECT COUNT(*) FROM commands WHERE run_id = ?",
            (run_id,),
        ).fetchone()[0] == 2


def test_payload_and_views_surface_lifecycle_and_receipts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _respawn_recovery_data, frame = _respawn_recovery(monkeypatch)
    payload = build_tk_trace_payload(frame.state, frame.trace)
    chinese = build_chinese_causal_view(frame)
    advanced = build_advanced_details(frame, controller=SimpleNamespace(run_id="respawn-ui"))

    assert payload["lifecycle"]["trial_status"] == "active"
    assert payload["lifecycle"]["life_index"] == 2
    assert payload["transition_kind"] == "respawn"
    assert payload["policy_invoked"] is False
    assert payload["life_termination"] == frame.trace["life_termination"]
    assert payload["carry_reset_receipt"] == frame.trace["carry_reset_receipt"]
    assert "生命周期" in chinese
    assert chinese["生命周期"]["当前状态"] == "active"
    assert chinese["生命周期"]["上一生命终结"] == frame.trace["life_termination"]
    assert chinese["生命周期"]["重生回执"] == frame.trace["carry_reset_receipt"]
    assert advanced["lifecycle"] == frame.state["lifecycle"]
    assert advanced["transition_kind"] == "respawn"
    assert advanced["policy_invoked"] is False
    assert advanced["carry_reset_receipt"] == frame.trace["carry_reset_receipt"]


def test_tk_run_crosses_respawn_then_pauses_and_disables_controls_at_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    del tmp_path
    _force_action(monkeypatch, "rest")
    controller = _MemoryController(
        _valid_life_state(
            run_id="window-terminal-stop",
            life_index=4,
            episode_tick=255,
            energy=0.90,
        ),
        run_id="window-terminal-stop",
    )
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"tk unavailable: {exc}")
    root.withdraw()
    window = PlaygroundWindow(root, controller)
    window.display_interval_ms = 5
    try:
        window.run_button.invoke()
        _spin(root, timeout=1.2)

        assert controller.state["lifecycle"]["trial_status"] == "terminal"
        assert window.running is False
        assert window._run_after_id is None
        assert "disabled" in window.step_button.state()
        assert "disabled" in window.run_button.state()
        assert "disabled" in window.inject_button.state()
        assert "disabled" in window.pause_button.state()
        assert "terminal" in window.status_var.get()
        advanced_text = window.advanced_text.get("1.0", "end-1c")
        assert "life_survival" in advanced_text
        assert "fourth_life_result" in advanced_text
        after_terminal = controller.recovery.frames[-1].sequence
        window.step_button.invoke()
        window.run_button.invoke()
        window.inject_event_var.set("resource_appears")
        window.inject_button.invoke()
        _spin(root, timeout=0.2)
        assert controller.recovery.frames[-1].sequence == after_terminal
    finally:
        window.close()
        try:
            root.destroy()
        except tk.TclError:
            pass


def test_terminal_and_visual_console_source_guard_lifecycle_stays_in_controller_dispatch_path() -> None:
    forbidden_calls = {"compute_step", "transition_world", "append_step", "create_run", "initial_state", "reset_world_for_life"}
    dispatch_calls = 0
    for relative in (
        "labs/ego_life_playground_v0/terminal.py",
        "labs/ego_life_playground_v0/visual_console.py",
    ):
        source = Path(relative).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = None
            if isinstance(node.func, ast.Name):
                target = node.func.id
            elif isinstance(node.func, ast.Attribute):
                target = node.func.attr
            assert target not in forbidden_calls
            if target == "dispatch":
                dispatch_calls += 1
    assert dispatch_calls >= 3
