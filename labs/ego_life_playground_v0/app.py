"""Controller and Tk renderer for the explicit local playground process."""

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
    CUES,
    DEFAULT_TOGGLES,
    StepResult,
    compute_step,
    initial_state,
    make_command,
    make_run_metadata,
)
from .store import CommitReceipt, RecoveryResult, SQLiteEventStore, default_db_path


DISCLOSURE = (
    "Deterministic deficit scorer + tabular EMA; local product-clock surface; "
    "science weight 0."
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
        episode_id: str = "manual-local",
        on_committed: Callable[[dict[str, Any], dict[str, Any]], None] | None = None,
    ) -> None:
        self.store = store
        self.on_committed = on_committed
        selected_run_id = run_id or store.latest_run_id()
        self.recovery_status = "new run"
        if selected_run_id is not None and store.run_exists(selected_run_id):
            recovered = store.recover_run(selected_run_id)
            self.run_id = selected_run_id
            self.run_meta = recovered.run_meta
            self.state = recovered.state
            self.last_trace = recovered.traces[-1] if recovered.traces else None
            self.recovery_status = f"recomputed {recovered.command_count} command(s)"
        else:
            self.run_id = selected_run_id or f"local-{uuid.uuid4().hex[:16]}"
            self.run_meta = make_run_metadata(self.run_id, seed, episode_id)
            self.state = initial_state()
            self.last_trace: dict[str, Any] | None = None
            store.create_run(self.run_meta, self.state)

    def dispatch(self, cue: str, toggles: Mapping[str, bool]) -> DispatchResult:
        command = make_command(
            sequence=int(self.state["step"]) + 1,
            cue=cue,
            toggles=toggles,
            prev_command_hash=self.state.get("last_command_hash"),
        )
        computed = compute_step(self.state, command, self.run_meta)
        receipt = self.store.append_step(command, computed.trace)
        if not receipt.committed:
            # Neither controller state nor renderer callback is changed on a
            # failed transaction.
            return DispatchResult(receipt=receipt, step=None)
        self.state = computed.next_state
        self.last_trace = computed.trace
        self.recovery_status = f"committed step {receipt.sequence}"
        if self.on_committed is not None:
            self.on_committed(deepcopy(self.state), deepcopy(self.last_trace))
        return DispatchResult(receipt=receipt, step=computed)

    def recover(self) -> RecoveryResult:
        recovered = self.store.recover_run(self.run_id)
        self.state = recovered.state
        self.last_trace = recovered.traces[-1] if recovered.traces else None
        self.recovery_status = f"recomputed {recovered.command_count} command(s)"
        return recovered

    def export(self, output_path: str | Path) -> Path:
        output = self.store.export_run(self.run_id, output_path)
        self.recovery_status = f"recomputed + exported {output.name}"
        return output


class PlaygroundWindow:
    def __init__(self, root: tk.Tk, controller: PlaygroundController) -> None:
        self.root = root
        self.controller = controller
        root.title("EGO Visible Life Proxy v0 — Local Playground")
        root.geometry("1320x840")
        root.minsize(1050, 700)

        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Disclosure.TLabel", foreground="#8b1a1a", font=("Segoe UI", 10, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 10, "bold"))

        shell = ttk.Frame(root, padding=10)
        shell.pack(fill=tk.BOTH, expand=True)
        ttk.Label(shell, text=DISCLOSURE, style="Disclosure.TLabel").pack(fill=tk.X, pady=(0, 8))

        toolbar = ttk.Frame(shell)
        toolbar.pack(fill=tk.X, pady=(0, 8))
        self.toggle_vars = {
            "memory_on": tk.BooleanVar(value=True),
            "learning_on": tk.BooleanVar(value=True),
            "consolidation_on": tk.BooleanVar(value=True),
        }
        for key, label in (
            ("memory_on", "Memory"),
            ("learning_on", "Learning"),
            ("consolidation_on", "Consolidation replay"),
        ):
            ttk.Checkbutton(toolbar, text=label, variable=self.toggle_vars[key]).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)
        for cue in CUES:
            ttk.Button(toolbar, text=cue.title(), command=lambda value=cue: self._dispatch(value)).pack(
                side=tk.LEFT, padx=3
            )
        ttk.Button(toolbar, text="Restart / recompute", command=self._recover).pack(side=tk.RIGHT, padx=3)
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

        goals_box = ttk.LabelFrame(left, text="Endogenous goal proposals (deficits)", padding=6)
        goals_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.goals_text = _read_only_text(goals_box, height=8)

        memory_box = ttk.LabelFrame(left, text="Structured memory + provenance", padding=6)
        memory_box.pack(fill=tk.BOTH, expand=True)
        self.memory_text = _read_only_text(memory_box, height=16)

        candidate_box = ttk.LabelFrame(right, text="One-step action candidates / score components", padding=6)
        candidate_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        columns = ("action", "deficit", "memory", "novelty", "cost", "tie", "total")
        self.candidate_tree = ttk.Treeview(candidate_box, columns=columns, show="headings", height=8)
        headings = {
            "action": "Action",
            "deficit": "Deficit Δ",
            "memory": "Memory bias",
            "novelty": "Untried",
            "cost": "Cost",
            "tie": "Seed tie",
            "total": "Total",
        }
        for column in columns:
            self.candidate_tree.heading(column, text=headings[column])
            self.candidate_tree.column(column, width=100, anchor=tk.CENTER)
        self.candidate_tree.pack(fill=tk.BOTH, expand=True)

        lower = ttk.Panedwindow(right, orient=tk.HORIZONTAL)
        lower.pack(fill=tk.BOTH, expand=True)
        model_box = ttk.LabelFrame(lower, text="Tabular outcome model (count / EMA)", padding=6)
        trace_box = ttk.LabelFrame(lower, text="Selection / prediction / trace", padding=6)
        lower.add(model_box, weight=1)
        lower.add(trace_box, weight=1)
        self.model_text = _read_only_text(model_box, height=19)
        self.trace_text = _read_only_text(trace_box, height=19)

        self.status_var = tk.StringVar()
        ttk.Label(shell, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(
            fill=tk.X, pady=(8, 0)
        )
        self.redraw()

    def _toggle_snapshot(self) -> dict[str, bool]:
        return {key: bool(var.get()) for key, var in self.toggle_vars.items()}

    def _dispatch(self, cue: str) -> None:
        result = self.controller.dispatch(cue, self._toggle_snapshot())
        if not result.receipt.committed:
            messagebox.showerror("Atomic commit rejected", result.receipt.error or "unknown error")
            self.status_var.set("No state redraw: SQLite command+trace transaction rolled back")
            return
        self.redraw()

    def _recover(self) -> None:
        try:
            self.controller.recover()
        except Exception as exc:
            messagebox.showerror("Recovery failed closed", str(exc))
            self.status_var.set(f"Recovery failed closed: {exc}")
            return
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

    def redraw(self) -> None:
        state = self.controller.state
        for key, (bar, label) in self.state_widgets.items():
            value = float(state["organism"][key])
            bar["value"] = value * 100
            label["text"] = f"{value:.3f}"

        trace = self.controller.last_trace
        if trace is None:
            goals = _goals_from_state(state)
            candidates: list[dict[str, Any]] = []
        else:
            goals = trace["goals"]
            candidates = trace["candidates"]
        _set_text(
            self.goals_text,
            "\n".join(
                f"{goal['priority']}. {goal['state_variable']}: "
                f"{goal['current']:.3f} → {goal['target']:.2f}  deficit={goal['deficit']:.3f}"
                for goal in goals
            ),
        )
        _set_text(self.memory_text, json.dumps(state["memory"], indent=2, ensure_ascii=False))
        _set_text(self.model_text, json.dumps(state["model"], indent=2, ensure_ascii=False))

        for item in self.candidate_tree.get_children():
            self.candidate_tree.delete(item)
        selected_action = trace["selected_action"] if trace else None
        for candidate in sorted(candidates, key=lambda item: item["total_score"], reverse=True):
            iid = self.candidate_tree.insert(
                "",
                tk.END,
                values=(
                    candidate["action"],
                    f"{candidate['deficit_reduction']:.4f}",
                    f"{candidate['memory_bias']:.4f}",
                    f"{candidate['untried_bonus']:.4f}",
                    f"{candidate['action_cost']:.4f}",
                    f"{candidate['tie_break']:.8f}",
                    f"{candidate['total_score']:.5f}",
                ),
            )
            if candidate["action"] == selected_action:
                self.candidate_tree.selection_set(iid)

        if trace is None:
            trace_view = {
                "selected_action": None,
                "prediction": None,
                "actual_delta": None,
                "prediction_error": None,
                "latest_trace_hash": None,
            }
        else:
            trace_view = {
                "selected_action": trace["selected_action"],
                "prediction": trace["prediction"],
                "actual_delta": trace["actual_delta"],
                "prediction_error": trace["prediction_error"],
                "model_update": trace["model_update"],
                "memory_update": trace["memory_update"],
                "latest_trace_hash": trace["trace_hash"],
                "code_path_hash": trace["code_path_hash"],
            }
        _set_text(self.trace_text, json.dumps(trace_view, indent=2, ensure_ascii=False))
        self.status_var.set(
            f"run={self.controller.run_id} | step={state['step']} | "
            f"{self.controller.recovery_status} | db={self.controller.store.path}"
        )


def run_app(db_path: str | Path | None = None, *, seed: int = 17) -> None:
    store = SQLiteEventStore(db_path or default_db_path())
    try:
        controller = PlaygroundController(store, seed=seed)
        root = tk.Tk()
        window = PlaygroundWindow(root, controller)
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        root.mainloop()
        del window
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


def _goals_from_state(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    from .engine import propose_goals

    return propose_goals(state["organism"])
