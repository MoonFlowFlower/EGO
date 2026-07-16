"""Controller plus terminal/Tk views for the explicit local microworld."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Mapping
import uuid

from .engine import (
    ACTIONS,
    CUES,
    DEFAULT_INTERVENTIONS,
    EngineInvariantError,
    StepResult,
    compute_step,
    initial_state,
    make_command,
    make_run_metadata,
)
from .microworld import (
    ALLOWED_WORLD_EVENTS,
    cue_for_event,
    default_event_for_sequence,
    event_for_cue,
    make_public_frame,
)
from .store import (
    CommitReceipt,
    RecoveryFrame,
    RecoveryResult,
    SQLiteEventStore,
    default_db_path,
)


DISCLOSURE = (
    "Deterministic visible microworld + deficit scorer + tabular EMA; "
    "local default-off product surface; science weight 0."
)


@dataclass(frozen=True)
class DispatchResult:
    receipt: CommitReceipt
    step: StepResult | None


class PlaygroundController:
    """The UI's only state-changing entrypoint."""

    def __init__(
        self,
        store: SQLiteEventStore,
        *,
        run_id: str | None = None,
        seed: int = 17,
        on_committed: Callable[[dict[str, Any], dict[str, Any]], None] | None = None,
        on_recovered: Callable[[RecoveryResult], None] | None = None,
    ) -> None:
        self.store = store
        self.on_committed = on_committed
        self.on_recovered = on_recovered
        selected_run_id = run_id if run_id is not None else store.latest_compatible_run_id()

        if selected_run_id is not None and store.run_exists(selected_run_id):
            self.run_id = selected_run_id
            recovered = store.recover_run(selected_run_id)
            self._adopt_recovery(recovered)
            self.recovery_status = f"recomputed {recovered.command_count} command(s)"
            if self.on_recovered is not None:
                self.on_recovered(recovered)
            return

        self.run_id = selected_run_id or f"local-{uuid.uuid4().hex[:16]}"
        self.run_meta = make_run_metadata(self.run_id, seed)
        state = initial_state(run_id=self.run_id)
        store.create_run(self.run_meta, state)
        recovered = store.recover_run(self.run_id)
        self._adopt_recovery(recovered)
        self.recovery_status = "new run"

    def _adopt_recovery(self, recovered: RecoveryResult) -> None:
        self.recovery = recovered
        self.run_meta = recovered.run_meta
        self.state = recovered.state
        self.last_trace = recovered.traces[-1] if recovered.traces else None

    def dispatch(
        self,
        cue: str,
        interventions: Mapping[str, str],
        *,
        trigger_source: str = "ui_step_button",
        world_event: str | None = None,
    ) -> DispatchResult:
        command = make_command(
            sequence=int(self.state["clock"]["global_tick"]) + 1,
            cue=cue,
            trigger_source=trigger_source,
            interventions=interventions,
            prev_command_hash=self.state.get("last_command_hash"),
            world_event=world_event,
        )
        computed = compute_step(self.state, command, self.run_meta)
        receipt = self.store.append_step(command, computed.trace)
        if not receipt.committed:
            # Neither controller state, its derived recovery timeline, nor a
            # renderer callback changes after an atomic transaction failure.
            return DispatchResult(receipt=receipt, step=None)

        # Timeline truth is always rebuilt from serialized initial state plus
        # ordered commands.  Stored traces remain comparison-only inputs.
        recovered = self.store.recover_run(self.run_id)
        self._adopt_recovery(recovered)
        self.recovery_status = f"committed tick {receipt.sequence}"
        if self.on_committed is not None:
            self.on_committed(deepcopy(self.state), deepcopy(self.last_trace))
        return DispatchResult(receipt=receipt, step=computed)

    def recover(self) -> RecoveryResult:
        recovered = self.store.recover_run(self.run_id)
        self._adopt_recovery(recovered)
        self.recovery_status = f"recomputed {recovered.command_count} command(s)"
        if self.on_recovered is not None:
            self.on_recovered(recovered)
        return recovered

    def export(self, output_path: str | Path) -> Path:
        output = self.store.export_run(self.run_id, output_path)
        self.recovery_status = f"recomputed + exported {output.name}"
        return output

    def load_run(self, run_id: str) -> RecoveryResult:
        """Adopt an existing durable run after complete recomputation."""

        if type(run_id) is not str or not run_id:
            raise EngineInvariantError("run_id must be a non-empty string")
        if not self.store.run_exists(run_id):
            raise EngineInvariantError(f"unknown run: {run_id}")
        recovered = self.store.recover_run(run_id)
        self.run_id = run_id
        self._adopt_recovery(recovered)
        self.recovery_status = f"loaded + recomputed {recovered.command_count} command(s)"
        if self.on_recovered is not None:
            self.on_recovered(recovered)
        return recovered

    def reset_run(self, run_id: str | None = None) -> RecoveryResult:
        """Start a new run without deleting any prior episode history."""

        selected = run_id or f"local-{uuid.uuid4().hex[:16]}"
        if type(selected) is not str or not selected:
            raise EngineInvariantError("run_id must be a non-empty string")
        if self.store.run_exists(selected):
            raise EngineInvariantError(f"run already exists: {selected}")
        seed = int(self.run_meta["seed"])
        run_meta = make_run_metadata(selected, seed)
        state = initial_state(run_id=selected)
        self.store.create_run(run_meta, state)
        recovered = self.store.recover_run(selected)
        self.run_id = selected
        self._adopt_recovery(recovered)
        self.recovery_status = "new run after reset"
        if self.on_recovered is not None:
            self.on_recovered(recovered)
        return recovered


def _timeline_from_recovery(recovery: RecoveryResult) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for frame in recovery.frames:
        trace = frame.trace
        clock = frame.state["clock"]
        timeline.append(
            {
                "sequence": frame.sequence,
                "global_tick": clock["global_tick"],
                "episode_index": clock["episode_index"],
                "episode_tick": clock["episode_tick"],
                "event": "quiet_interval" if trace is None else event_for_cue(trace["cue"]),
                "observation": "quiet" if trace is None else trace["cue"],
                "observation_hash": None if trace is None else trace["observation_hash"],
                "selected_action": None if trace is None else trace["selected_action"],
                "trace_hash": None if trace is None else trace["trace_hash"],
            }
        )
    return timeline


def build_terminal_snapshot(controller: PlaygroundController) -> dict[str, Any]:
    """Expose one understandable view derived only from recovered truth."""

    recovery = controller.recovery
    frame = recovery.frames[-1]
    state = frame.state
    trace = frame.trace
    previous_state = recovery.frames[-2].state if len(recovery.frames) > 1 else state
    selected_candidate = None
    if trace is not None:
        selected_candidate = next(
            item for item in trace["candidates"] if item["action"] == trace["selected_action"]
        )
    world_frame = make_public_frame(state, trace)
    return {
        "run_id": controller.run_id,
        "world": world_frame,
        "observation": deepcopy(world_frame["observation"]),
        "observation_hash": world_frame["observation_hash"],
        "decision_observation": deepcopy(world_frame["observation"])
        if trace is None
        else deepcopy(trace["observation"]),
        "decision_observation_hash": world_frame["observation_hash"]
        if trace is None
        else trace["observation_hash"],
        "internal_state": deepcopy(state["organism"]),
        "current_goal": deepcopy(state["current_goal"]),
        "candidates": [] if trace is None else deepcopy(trace["candidates"]),
        "legal_actions": [] if trace is None else deepcopy(trace["legal_actions"]),
        "gated_actions": [] if trace is None else deepcopy(trace["gated_actions"]),
        "selected_action": None if trace is None else trace["selected_action"],
        "selected_score": None if selected_candidate is None else selected_candidate["total_score"],
        "prediction": None if trace is None else deepcopy(trace["prediction"]),
        "actual_delta": None if trace is None else deepcopy(trace["actual_delta"]),
        "prediction_error": None if trace is None else deepcopy(trace["prediction_error"]),
        "model_update": None if trace is None else deepcopy(trace["model_update"]),
        "memory": {
            "read": None
            if trace is None
            else {
                "refs": deepcopy(trace["memory_refs"]),
                "projection": deepcopy(trace["provenance_projection"]),
            },
            "write": None if trace is None else deepcopy(trace["memory_update"]),
            "persistent_state": deepcopy(state["memory"]),
        },
        "state_transition": {
            "before_hash": None if trace is None else trace["state_before_hash"],
            "decision_hash": None if trace is None else trace["decision_state_hash"],
            "after_hash": None if trace is None else trace["state_after_hash"],
            "organism_before": deepcopy(previous_state["organism"]),
            "organism_after": deepcopy(state["organism"]),
        },
        "timeline": _timeline_from_recovery(recovery),
        "trace_hash": None if trace is None else trace["trace_hash"],
        "recovered": recovery.recovered,
        "science_weight": 0,
    }


class TerminalPlayground:
    """Synchronous, paused-by-default P0 operator surface.

    Every state-changing command calls ``PlaygroundController.dispatch``;
    inspect, pause, save/load and replay do not implement a second reducer.
    """

    HELP = (
        "step [event] | run N | pause | inspect | inject EVENT | "
        "save PATH | load RUN_ID | reset [RUN_ID] | replay | help | quit"
    )

    def __init__(self, controller: PlaygroundController) -> None:
        self.controller = controller
        self.paused = True

    def _dispatch_event(self, event: str, trigger_source: str) -> DispatchResult:
        return self.controller.dispatch(
            cue_for_event(event),
            DEFAULT_INTERVENTIONS,
            trigger_source=trigger_source,
            world_event=event,
        )

    def execute(self, command_line: str) -> dict[str, Any]:
        raw = command_line.strip()
        if not raw:
            return {"command": "", "status": "error", "error": "empty command"}
        parts = raw.split()
        operation = parts[0].lower()
        try:
            if operation in {"help", "?"}:
                return {
                    "command": "help",
                    "status": "ok",
                    "usage": self.HELP,
                    "allowed_world_events": list(ALLOWED_WORLD_EVENTS),
                }
            if operation in {"quit", "exit"}:
                self.paused = True
                return {"command": operation, "status": "quit"}
            if operation == "pause":
                self.paused = True
                return {
                    "command": "pause",
                    "status": "paused",
                    "global_tick": self.controller.state["clock"]["global_tick"],
                }
            if operation == "inspect":
                if len(parts) != 1:
                    raise ValueError("usage: inspect")
                return {"command": "inspect", "status": "ok", "snapshot": build_terminal_snapshot(self.controller)}
            if operation == "step":
                if len(parts) > 2:
                    raise ValueError("usage: step [event]")
                sequence = int(self.controller.state["clock"]["global_tick"]) + 1
                event = parts[1] if len(parts) == 2 else default_event_for_sequence(sequence)
                result = self._dispatch_event(event, "terminal_step")
                if not result.receipt.committed:
                    raise RuntimeError(result.receipt.error or "atomic commit rejected")
                self.paused = True
                return {
                    "command": "step",
                    "event": event,
                    "status": "committed",
                    "snapshot": build_terminal_snapshot(self.controller),
                }
            if operation == "inject":
                if len(parts) != 2:
                    raise ValueError("usage: inject EVENT")
                event = parts[1]
                result = self._dispatch_event(event, "terminal_event")
                if not result.receipt.committed:
                    raise RuntimeError(result.receipt.error or "atomic commit rejected")
                self.paused = True
                return {
                    "command": "inject",
                    "event": event,
                    "status": "committed",
                    "snapshot": build_terminal_snapshot(self.controller),
                }
            if operation == "run":
                if len(parts) != 2:
                    raise ValueError("usage: run N")
                ticks = int(parts[1])
                if ticks <= 0 or ticks > 10000:
                    raise ValueError("run tick count must be between 1 and 10000")
                self.paused = False
                for _ in range(ticks):
                    sequence = int(self.controller.state["clock"]["global_tick"]) + 1
                    event = default_event_for_sequence(sequence)
                    result = self._dispatch_event(event, "terminal_run")
                    if not result.receipt.committed:
                        self.paused = True
                        raise RuntimeError(result.receipt.error or "atomic commit rejected")
                self.paused = True
                return {
                    "command": "run",
                    "status": "committed",
                    "ticks_committed": ticks,
                    "snapshot": build_terminal_snapshot(self.controller),
                }
            if operation == "save":
                path_text = raw[len(parts[0]) :].strip()
                if not path_text:
                    raise ValueError("usage: save PATH")
                output = self.controller.export(path_text)
                return {"command": "save", "status": "saved", "path": str(output)}
            if operation == "load":
                if len(parts) != 2:
                    raise ValueError("usage: load RUN_ID")
                recovery = self.controller.load_run(parts[1])
                self.paused = True
                return {
                    "command": "load",
                    "status": "loaded",
                    "run_id": self.controller.run_id,
                    "frame_count": len(recovery.frames),
                    "snapshot": build_terminal_snapshot(self.controller),
                }
            if operation == "reset":
                if len(parts) > 2:
                    raise ValueError("usage: reset [RUN_ID]")
                recovery = self.controller.reset_run(parts[1] if len(parts) == 2 else None)
                self.paused = True
                return {
                    "command": "reset",
                    "status": "reset",
                    "run_id": self.controller.run_id,
                    "frame_count": len(recovery.frames),
                    "snapshot": build_terminal_snapshot(self.controller),
                }
            if operation == "replay":
                if len(parts) != 1:
                    raise ValueError("usage: replay")
                recovery = self.controller.recover()
                self.paused = True
                return {
                    "command": "replay",
                    "status": "recomputed",
                    "run_id": self.controller.run_id,
                    "frame_count": len(recovery.frames),
                    "timeline": _timeline_from_recovery(recovery),
                }
            raise ValueError(f"unknown command {operation!r}; {self.HELP}")
        except (EngineInvariantError, OSError, RuntimeError, ValueError) as exc:
            self.paused = True
            return {
                "command": operation,
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
            }


class PlaygroundWindow:
    """Paused-by-default Tk product clock and frame-derived timeline."""

    def __init__(
        self,
        root: tk.Tk,
        controller: PlaygroundController,
        *,
        display_interval_ms: int = 500,
    ) -> None:
        if type(display_interval_ms) is not int or display_interval_ms <= 0:
            raise ValueError("display_interval_ms must be a positive integer")
        self.root = root
        self.controller = controller
        self.display_interval_ms = display_interval_ms
        self.running = False
        self._after_id: str | None = None
        self._closed = False
        self._timeline_refreshing = False
        self._display_sequence = controller.recovery.frames[-1].sequence

        root.title("EGO Life Kernel V1 - Local Continuity Playground")
        root.geometry("1420x900")
        root.minsize(1100, 720)

        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Disclosure.TLabel", foreground="#8b1a1a", font=("Segoe UI", 10, "bold"))

        shell = ttk.Frame(root, padding=10)
        shell.pack(fill=tk.BOTH, expand=True)
        ttk.Label(shell, text=DISCLOSURE, style="Disclosure.TLabel").pack(fill=tk.X, pady=(0, 8))

        toolbar = ttk.Frame(shell)
        toolbar.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(toolbar, text="Cue").pack(side=tk.LEFT)
        self.cue_var = tk.StringVar(value="resource")
        self.cue_box = ttk.Combobox(
            toolbar,
            textvariable=self.cue_var,
            values=CUES,
            state="readonly",
            width=11,
        )
        self.cue_box.pack(side=tk.LEFT, padx=(4, 10))

        self.memory_mode_var = tk.StringVar(value="canonical")
        ttk.Label(toolbar, text="Memory").pack(side=tk.LEFT)
        self.memory_mode_box = ttk.Combobox(
            toolbar,
            textvariable=self.memory_mode_var,
            values=("canonical", "off"),
            state="readonly",
            width=10,
        )
        self.memory_mode_box.pack(side=tk.LEFT, padx=(4, 10))
        self.memory_mode_box.bind("<<ComboboxSelected>>", self._on_memory_mode_selected)

        self.freeze_updates_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            toolbar,
            text="Freeze model + memory updates",
            variable=self.freeze_updates_var,
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.provenance_mode_var = tk.StringVar(value="canonical")
        ttk.Label(toolbar, text="Provenance").pack(side=tk.LEFT)
        self.provenance_mode_box = ttk.Combobox(
            toolbar,
            textvariable=self.provenance_mode_var,
            values=("canonical", "shuffle_projection"),
            state="readonly",
            width=18,
        )
        self.provenance_mode_box.pack(side=tk.LEFT, padx=(4, 10))
        self.provenance_mode_box.bind(
            "<<ComboboxSelected>>", self._on_provenance_mode_selected
        )

        self.step_button = ttk.Button(toolbar, text="Step", command=self._step_once)
        self.step_button.pack(side=tk.LEFT, padx=3)
        self.run_button = ttk.Button(toolbar, text="Run", command=self._start_run)
        self.run_button.pack(side=tk.LEFT, padx=3)
        self.pause_button = ttk.Button(toolbar, text="Pause", command=self._pause)
        self.pause_button.pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Restart / recompute", command=self._recover).pack(
            side=tk.RIGHT, padx=3
        )
        ttk.Button(toolbar, text="Export trace", command=self._export).pack(side=tk.RIGHT, padx=3)

        body = ttk.Panedwindow(shell, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(body, padding=(0, 0, 6, 0))
        right = ttk.Frame(body, padding=(6, 0, 0, 0))
        body.add(left, weight=2)
        body.add(right, weight=3)

        state_box = ttk.LabelFrame(left, text="Organism state", padding=8)
        state_box.pack(fill=tk.X, pady=(0, 8))
        self.state_widgets: dict[str, tuple[ttk.Progressbar, ttk.Label]] = {}
        for row, key in enumerate(("energy", "safety", "connection", "stimulation")):
            ttk.Label(state_box, text=key.title(), width=12).grid(row=row, column=0, sticky=tk.W, pady=3)
            bar = ttk.Progressbar(state_box, maximum=100, length=260)
            bar.grid(row=row, column=1, sticky=tk.EW, padx=5)
            value = ttk.Label(state_box, width=7)
            value.grid(row=row, column=2, sticky=tk.E)
            self.state_widgets[key] = (bar, value)
        state_box.columnconfigure(1, weight=1)

        goals_box = ttk.LabelFrame(left, text="Current goal + deficit proposals", padding=6)
        goals_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.goals_text = _read_only_text(goals_box, height=10)

        memory_box = ttk.LabelFrame(left, text="Structured memory + provenance", padding=6)
        memory_box.pack(fill=tk.BOTH, expand=True)
        self.memory_text = _read_only_text(memory_box, height=14)

        timeline_box = ttk.LabelFrame(right, text="Recomputed continuity timeline", padding=6)
        timeline_box.pack(fill=tk.X, pady=(0, 8))
        timeline_columns = ("sequence", "global_tick", "episode", "episode_tick", "cue", "action")
        self.timeline_tree = ttk.Treeview(
            timeline_box,
            columns=timeline_columns,
            show="headings",
            height=5,
            selectmode="browse",
        )
        for column, heading, width in (
            ("sequence", "Seq", 55),
            ("global_tick", "Global", 65),
            ("episode", "Episode", 70),
            ("episode_tick", "Ep tick", 65),
            ("cue", "Cue", 90),
            ("action", "Selected action", 115),
        ):
            self.timeline_tree.heading(column, text=heading)
            self.timeline_tree.column(column, width=width, anchor=tk.CENTER)
        self.timeline_tree.pack(fill=tk.X)
        self.timeline_tree.bind("<<TreeviewSelect>>", self._on_timeline_select)

        candidate_box = ttk.LabelFrame(
            right, text="One-step action candidates / score components", padding=6
        )
        candidate_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        columns = ("action", "goal", "total", "memory", "novelty", "cost", "tie", "score")
        self.candidate_tree = ttk.Treeview(candidate_box, columns=columns, show="headings", height=7)
        headings = {
            "action": "Action",
            "goal": "Goal gain",
            "total": "Total gain",
            "memory": "Memory",
            "novelty": "Untried",
            "cost": "Cost",
            "tie": "Tie",
            "score": "Score",
        }
        for column in columns:
            self.candidate_tree.heading(column, text=headings[column])
            self.candidate_tree.column(column, width=92, anchor=tk.CENTER)
        self.candidate_tree.pack(fill=tk.BOTH, expand=True)

        lower = ttk.Panedwindow(right, orient=tk.HORIZONTAL)
        lower.pack(fill=tk.BOTH, expand=True)
        model_box = ttk.LabelFrame(lower, text="Tabular outcome model (count / EMA)", padding=6)
        trace_box = ttk.LabelFrame(lower, text="Prediction / error / update / trace", padding=6)
        lower.add(model_box, weight=1)
        lower.add(trace_box, weight=1)
        self.model_text = _read_only_text(model_box, height=17)
        self.trace_text = _read_only_text(trace_box, height=17)

        self.status_var = tk.StringVar()
        ttk.Label(shell, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(
            fill=tk.X, pady=(8, 0)
        )
        # The renderer owns the one commit-success callback used by the live
        # widget path.  Controller-only callers may supply their own callback,
        # but attaching a window makes commit -> callback -> redraw canonical.
        self.controller.on_committed = self._on_committed
        self.redraw()

    def _intervention_snapshot(self) -> dict[str, str]:
        snapshot = {
            "memory_mode": self.memory_mode_var.get(),
            "update_mode": "frozen" if self.freeze_updates_var.get() else "enabled",
            "provenance_mode": self.provenance_mode_var.get(),
        }
        if (
            snapshot["memory_mode"] == "off"
            and snapshot["provenance_mode"] == "shuffle_projection"
        ):
            raise EngineInvariantError(
                "invalid intervention combination: Memory OFF and Shuffle Provenance are mutually exclusive"
            )
        return snapshot

    def _on_memory_mode_selected(self, _event: tk.Event[tk.Misc]) -> None:
        if self.memory_mode_var.get() == "off":
            self.provenance_mode_var.set("canonical")

    def _on_provenance_mode_selected(self, _event: tk.Event[tk.Misc]) -> None:
        if self.provenance_mode_var.get() == "shuffle_projection":
            self.memory_mode_var.set("canonical")

    def _latest_sequence(self) -> int:
        return self.controller.recovery.frames[-1].sequence

    def _is_historical(self) -> bool:
        return self._display_sequence != self._latest_sequence()

    def _step_once(self) -> None:
        if self.running or self._is_historical():
            return
        self._dispatch("ui_step_button")

    def _start_run(self) -> None:
        if self._closed or self.running or self._is_historical():
            return
        self.running = True
        self._update_progress_controls()
        # The widget handler never changes causal state directly.  Even the
        # first tick is deferred through Tk's scheduler.
        self._after_id = self.root.after(0, self._run_tick)

    def _run_tick(self) -> None:
        self._after_id = None
        if self._closed or not self.running:
            return
        committed = self._dispatch("ui_run_button")
        if self.running and committed:
            # Arm the display interval only after Tk has drained redraw work
            # from this committed frame.  A single ``root.update()`` therefore
            # observes one tick rather than recursively consuming timers whose
            # delay elapsed while widgets were being laid out.
            self._after_id = self.root.after_idle(self._arm_run_timer)

    def _arm_run_timer(self) -> None:
        self._after_id = None
        if not self._closed and self.running:
            # Very small Tk timers can expire while ``update()`` is still
            # draining geometry work and collapse several logical ticks into
            # one widget-event observation.  Keep a small UI-only floor; it is
            # deliberately absent from causal state, commands, and hashes.
            interval = max(self.display_interval_ms, 50)
            self._after_id = self.root.after(interval, self._run_tick)

    def _pause(self) -> None:
        self.running = False
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
        if not self._closed:
            self._update_progress_controls()

    def _on_committed(
        self,
        _state: dict[str, Any],
        _trace: dict[str, Any],
    ) -> None:
        """Advance visible truth only from the post-commit controller callback."""

        if self._closed:
            return
        self._display_sequence = self._latest_sequence()
        self.redraw()

    def _dispatch(self, trigger_source: str) -> bool:
        if self._closed or self._is_historical():
            return False
        try:
            result = self.controller.dispatch(
                self.cue_var.get(),
                self._intervention_snapshot(),
                trigger_source=trigger_source,
            )
        except EngineInvariantError as exc:
            self._pause()
            messagebox.showerror("Command rejected", str(exc))
            self.status_var.set(f"Paused without commit: {exc}")
            return False
        if not result.receipt.committed:
            self._pause()
            messagebox.showerror("Atomic commit rejected", result.receipt.error or "unknown error")
            self.status_var.set("No redraw: SQLite command+trace transaction rolled back")
            return False
        return True

    def _recover(self) -> None:
        self._pause()
        try:
            self.controller.recover()
        except Exception as exc:
            messagebox.showerror("Recovery failed closed", str(exc))
            self.status_var.set(f"Recovery failed closed: {exc}")
            return
        self._display_sequence = self._latest_sequence()
        self.redraw()

    def _export(self) -> None:
        default_name = f"{self.controller.run_id}.trace.jsonl"
        selected = filedialog.asksaveasfilename(
            title="Export recomputed trace",
            initialdir=str(self.controller.store.path.parent),
            initialfile=default_name,
            defaultextension=".jsonl",
            filetypes=[("JSON Lines", "*.jsonl"), ("All files", "*.*")],
        )
        if not selected:
            return
        try:
            output = self.controller.export(selected)
        except Exception as exc:
            messagebox.showerror("Export rejected", str(exc))
            self.status_var.set(f"Export rejected after recovery failure: {exc}")
            return
        self.status_var.set(f"Verified export: {output}")

    def _frame_for_sequence(self, sequence: int) -> RecoveryFrame:
        for frame in self.controller.recovery.frames:
            if frame.sequence == sequence:
                return frame
        raise RuntimeError(f"unknown recomputed frame sequence: {sequence}")

    def _on_timeline_select(self, _event: tk.Event[tk.Misc]) -> None:
        if self._timeline_refreshing:
            return
        selection = self.timeline_tree.selection()
        if not selection:
            return
        sequence = int(self.timeline_tree.item(selection[0], "values")[0])
        if sequence == self._display_sequence:
            # Programmatic selection_set calls during timeline rebuild can
            # queue this virtual event until after the guard is released.
            # They must not create a second redraw outside the commit callback.
            return
        self._display_sequence = sequence
        if self._is_historical():
            self._pause()
        self.redraw(self._frame_for_sequence(sequence), rebuild_timeline=False)

    def _rebuild_timeline(self) -> None:
        self._timeline_refreshing = True
        try:
            for item in self.timeline_tree.get_children():
                self.timeline_tree.delete(item)
            selected_iid = ""
            for frame in self.controller.recovery.frames:
                clock = frame.state["clock"]
                trace = frame.trace
                iid = self.timeline_tree.insert(
                    "",
                    tk.END,
                    values=(
                        frame.sequence,
                        clock["global_tick"],
                        clock["episode_index"],
                        clock["episode_tick"],
                        "initial" if trace is None else trace["cue"],
                        "-" if trace is None else trace["selected_action"],
                    ),
                )
                if frame.sequence == self._display_sequence:
                    selected_iid = iid
            if selected_iid:
                self.timeline_tree.selection_set(selected_iid)
                self.timeline_tree.see(selected_iid)
        finally:
            self._timeline_refreshing = False

    def _update_progress_controls(self) -> None:
        blocked = self._is_historical()
        if blocked or self.running:
            self.step_button.state(["disabled"])
        else:
            self.step_button.state(["!disabled"])
        if blocked or self.running:
            self.run_button.state(["disabled"])
        else:
            self.run_button.state(["!disabled"])
        if self.running:
            self.pause_button.state(["!disabled"])
        else:
            self.pause_button.state(["disabled"])

    def redraw(
        self,
        frame: RecoveryFrame | None = None,
        *,
        rebuild_timeline: bool = True,
    ) -> None:
        if frame is None:
            frame = self._frame_for_sequence(self._display_sequence)
        if rebuild_timeline:
            self._rebuild_timeline()

        state = frame.state
        trace = frame.trace
        for key, (bar, label) in self.state_widgets.items():
            value = float(state["organism"][key])
            bar["value"] = value * 100
            label["text"] = f"{value:.3f}"

        from .engine import propose_goals

        goals = propose_goals(state["organism"]) if trace is None else trace["goals"]
        current_goal = state["current_goal"]
        goal_age_ticks = int(state["clock"]["global_tick"]) - int(
            current_goal["selected_global_tick"]
        )
        goal_lines = [
            "current_goal=" + json.dumps(current_goal, sort_keys=True, ensure_ascii=False),
            f"goal_age_ticks={goal_age_ticks}",
            "",
        ]
        goal_lines.extend(
            f"{goal['priority']}. {goal['state_variable']}: "
            f"{goal['current']:.3f} -> {goal['target']:.2f} deficit={goal['deficit']:.3f}"
            for goal in goals
        )
        _set_text(self.goals_text, "\n".join(goal_lines))
        _set_text(self.memory_text, json.dumps(state["memory"], indent=2, ensure_ascii=False))
        _set_text(self.model_text, json.dumps(state["model"], indent=2, ensure_ascii=False))

        for item in self.candidate_tree.get_children():
            self.candidate_tree.delete(item)
        candidates: list[dict[str, Any]] = [] if trace is None else trace["candidates"]
        selected_action = None if trace is None else trace["selected_action"]
        for candidate in sorted(candidates, key=lambda item: item["total_score"], reverse=True):
            iid = self.candidate_tree.insert(
                "",
                tk.END,
                values=(
                    candidate["action"],
                    f"{candidate['current_goal_deficit_reduction']:.4f}",
                    f"{candidate['total_deficit_reduction']:.4f}",
                    f"{candidate['memory_bias']:.4f}",
                    f"{candidate['untried_bonus']:.4f}",
                    f"{candidate['action_cost']:.4f}",
                    f"{candidate['deterministic_tie']:.8f}",
                    f"{candidate['total_score']:.5f}",
                ),
            )
            if candidate["action"] == selected_action:
                self.candidate_tree.selection_set(iid)

        if trace is None:
            trace_view: dict[str, Any] = {
                "clock": state["clock"],
                "current_goal": current_goal,
                "selected_action": None,
                "trace_hash": None,
            }
        else:
            trace_view = {
                "clock": state["clock"],
                "current_goal": current_goal,
                "trigger_source": trace["trigger_source"],
                "interventions": trace["interventions"],
                "command": trace["command"],
                "selected_action": trace["selected_action"],
                "prediction": trace["prediction"],
                "actual_delta": trace["actual_delta"],
                "prediction_error": trace["prediction_error"],
                "model_update": trace["model_update"],
                "memory_update": trace["memory_update"],
                "provenance_projection": trace["provenance_projection"],
                "memory_refs": trace["memory_refs"],
                "trace_hash": trace["trace_hash"],
                "code_path_hash": trace["code_path_hash"],
            }
        _set_text(self.trace_text, json.dumps(trace_view, indent=2, ensure_ascii=False))

        self._update_progress_controls()
        clock = state["clock"]
        if self._is_historical():
            mode = "read-only historical frame; return to latest frame to continue"
        else:
            mode = "running" if self.running else "paused"
        self.status_var.set(
            f"run={self.controller.run_id} | global_tick={clock['global_tick']} | "
            f"episode={clock['episode_index']}:{clock['episode_tick']} | {mode} | "
            f"{self.controller.recovery_status} | db={self.controller.store.path}"
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._pause()
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            # An external window-manager teardown may have destroyed Tcl first.
            pass


def run_app(db_path: str | Path | None = None, *, seed: int = 17) -> None:
    store = SQLiteEventStore(db_path or default_db_path())
    try:
        controller = PlaygroundController(store, seed=seed)
        root = tk.Tk()
        window = PlaygroundWindow(root, controller)
        root.protocol("WM_DELETE_WINDOW", window.close)
        root.mainloop()
    finally:
        store.close()


def _read_only_text(parent: ttk.LabelFrame, *, height: int) -> tk.Text:
    widget = tk.Text(parent, height=height, wrap=tk.NONE, font=("Consolas", 9))
    widget.pack(fill=tk.BOTH, expand=True)
    widget.configure(state=tk.DISABLED)
    return widget


def _set_text(widget: tk.Text, value: str) -> None:
    widget.configure(state=tk.NORMAL)
    widget.delete("1.0", tk.END)
    widget.insert("1.0", value)
    widget.configure(state=tk.DISABLED)
