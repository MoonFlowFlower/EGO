"""Tk visual console routed only through PlaygroundController recovery frames."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, Mapping

from .controller import PlaygroundController, public_state_hash
from .engine import DEFAULT_INTERVENTIONS, DEFAULT_PRIVATE_WORLD_SEED, EngineInvariantError, MAX_LIVES
from .microworld import ALLOWED_WORLD_EVENTS, FACING_DELTAS, make_public_frame
from .store import RecoveryFrame, SQLiteEventStore, default_db_path
from .terminal import build_terminal_snapshot


def _lifecycle_payload(state: Mapping[str, Any], trace: Mapping[str, Any] | None) -> dict[str, Any]:
    lifecycle = deepcopy(state.get("lifecycle", {}))
    results = lifecycle.get("life_results", []) if isinstance(lifecycle, dict) else []
    trace_mapping = trace if isinstance(trace, Mapping) else {}
    return {
        "lifecycle": lifecycle,
        "life_survival": [int(item["survival_ticks"]) for item in results],
        "terminal_life_result": None
        if not isinstance(lifecycle, dict)
        else deepcopy(lifecycle.get("terminal_life_result")),
        "transition_kind": trace_mapping.get("transition_kind"),
        "policy_invoked": None
        if trace is None
        else bool(trace_mapping.get("policy_invoked")),
        "life_termination": deepcopy(trace_mapping.get("life_termination")),
        "carry_reset_receipt": deepcopy(trace_mapping.get("carry_reset_receipt")),
    }


def _survival_window_summary(life_survival: list[int]) -> dict[str, float | None]:
    early = life_survival[:4]
    late = life_survival[12:16]
    return {
        "lives_1_4_mean": None if len(early) < 4 else round(sum(early) / 4.0, 3),
        "lives_13_16_mean": None if len(late) < 4 else round(sum(late) / 4.0, 3),
    }


def _resource_success_count(controller: PlaygroundController, *, through_sequence: int) -> int:
    recovery = getattr(controller, "recovery", None)
    frames = getattr(recovery, "frames", ())
    if (
        frames
        and through_sequence == frames[-1].sequence
        and hasattr(controller, "_ui_resource_successes")
    ):
        return int(getattr(controller, "_ui_resource_successes"))
    return sum(
        1
        for recovered_frame in frames
        if recovered_frame.sequence <= through_sequence
        and isinstance(recovered_frame.trace, Mapping)
        and bool(
            (recovered_frame.trace.get("survival_learning") or {}).get(
                "successful_resource_interaction"
            )
        )
    )

_TOKEN_COLORS = {
    "self": "#73d2de",
    "empty": "#1c2533",
    "wall": "#0d1117",
    "occluded": "#202938",
    "v0": "#9cdcfe",
    "v1": "#c586c0",
    "v2": "#dcdcaa",
    "v3": "#ce9178",
    "v4": "#4ec9b0",
}

_WORLD_COLORS = {
    "bg": "#0b0f14",
    "panel": "#111821",
    "grid": "#243242",
    "walkable": "#1a2532",
    "wall": "#06080c",
    "text": "#ecf4ff",
    "muted": "#90a3bb",
    "agent": "#6ee7f2",
    "object": "#ffc857",
}


def _copy_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return {} if value is None else deepcopy(dict(value))


def build_tk_trace_payload(
    state: Mapping[str, Any], trace: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Build a renderer-only payload from recovered state and recovered trace."""

    observer_frame = make_public_frame(state, trace)
    policy_visual = (
        deepcopy(trace["observation"])
        if isinstance(trace, Mapping) and isinstance(trace.get("observation"), Mapping)
        else deepcopy(observer_frame["observation"])
    )
    payload = {
        "clock": deepcopy(state["clock"]),
        "current_goal": deepcopy(state["current_goal"]),
        "observer_frame": observer_frame,
        "policy_visual": policy_visual,
        "public_state_hash": public_state_hash(state),
        "observer_public_world_hash": observer_frame["public_world_hash"],
        "observer_observation_hash": observer_frame["observation_hash"],
        "policy_projection_boundary": {
            "world_visible_to_policy": False,
            "policy_visual_exact_tokens_only": True,
        },
        **_lifecycle_payload(state, trace),
    }
    if trace is None:
        payload["selected_action"] = None
        payload["trigger_source"] = None
        payload["provenance_projection"] = {}
        payload["policy_projection_hash"] = None
        payload["code_path_hash"] = None
        return payload
    payload.update(
        {
            "selected_action": trace.get("selected_action"),
            "trigger_source": trace.get("trigger_source"),
            "provenance_projection": deepcopy(trace.get("provenance_projection")),
            "policy_projection_hash": trace.get("policy_projection_hash"),
            "code_path_hash": trace.get("code_path_hash"),
            "command_hash": trace.get("command_hash"),
            "trace_hash": trace.get("trace_hash"),
            "goal_before": deepcopy(trace.get("goal_before")),
            "goal_progress": deepcopy(trace.get("goal_progress")),
            "goal_transition": deepcopy(trace.get("goal_transition")),
            "goal_after": deepcopy(trace.get("goal_after")),
            "survival_learning": deepcopy(trace.get("survival_learning")),
        }
    )
    return payload


def _pose_from_world(world: Mapping[str, Any]) -> dict[str, Any]:
    agent = world["agent"]
    return {
        "position": deepcopy(agent["position"]),
        "facing": str(agent["facing"]),
    }


def _previous_facing(current: str, action: str) -> str:
    if action == "turn_left":
        cycle = {"N": "E", "E": "S", "S": "W", "W": "N"}
        return cycle[current]
    if action == "turn_right":
        cycle = {"N": "W", "W": "S", "S": "E", "E": "N"}
        return cycle[current]
    return current


def _poses_from_recovered_frame(frame: RecoveryFrame) -> tuple[dict[str, Any], dict[str, Any]]:
    after_pose = _pose_from_world(frame.state["world"])
    trace = frame.trace
    if trace is None:
        return deepcopy(after_pose), deepcopy(after_pose)
    action = trace.get("selected_action")
    outcome = (trace.get("world_transition") or {}).get("outcome_type")
    before_pose = deepcopy(after_pose)
    if action == "move_forward" and outcome == "moved":
        dx, dy = FACING_DELTAS[after_pose["facing"]]
        before_pose["position"] = [
            after_pose["position"][0] - dx,
            after_pose["position"][1] - dy,
        ]
        return before_pose, after_pose
    if action in {"turn_left", "turn_right"} and outcome == "turned":
        before_pose["facing"] = _previous_facing(after_pose["facing"], str(action))
    return before_pose, after_pose


def _format_visual(visual: list[list[str]]) -> str:
    return "\n".join(" ".join(row) for row in visual)


def build_chinese_causal_view(
    frame: RecoveryFrame, *, controller: PlaygroundController | None = None
) -> dict[str, Any]:
    """Summarize one recovered frame without adding a second transition path."""

    payload = build_tk_trace_payload(frame.state, frame.trace)
    observer_world = payload["observer_frame"]["world"]
    policy_visual = payload["policy_visual"]["visual"]
    objects = []
    for cause, item in sorted(observer_world["objects_by_cause"].items()):
        position = item["position"]
        objects.append(f"{cause}:{item['token']}@({position[0]},{position[1]})")
    if frame.trace is None:
        return {
            "观察者全局视图": {
                "位置": str(observer_world["agent"]["position"]),
                "朝向": observer_world["agent"]["facing"],
                "隐藏对象": "；".join(objects),
            },
            "有机体5x5视觉": _format_visual(policy_visual),
            "候选与选择": {"选择动作": "未记录／初始状态", "触发来源": "未记录／初始状态"},
            "生命周期": {
                "当前状态": payload["lifecycle"].get("trial_status"),
                "当前生命": f"{payload['lifecycle'].get('life_index')}/{MAX_LIVES}",
                "生存刻度": deepcopy(payload["life_survival"]),
                "终局生命结果": deepcopy(payload["terminal_life_result"]),
                "早晚生命均值": _survival_window_summary(payload["life_survival"]),
            },
            "结果与变化": {"世界结果": "未记录／初始状态", "状态哈希": payload["public_state_hash"]},
        }
    trace = frame.trace
    world_transition = _copy_mapping(trace.get("world_transition"))
    goal_progress = _copy_mapping(trace.get("goal_progress"))
    goal_transition = _copy_mapping(trace.get("goal_transition"))
    survival_trace = _copy_mapping(trace.get("survival_learning"))
    selection = _copy_mapping(survival_trace.get("selection"))
    update = _copy_mapping(survival_trace.get("update"))
    return {
        "观察者全局视图": {
            "位置": str(observer_world["agent"]["position"]),
            "朝向": observer_world["agent"]["facing"],
            "隐藏对象": "；".join(objects),
        },
        "有机体5x5视觉": _format_visual(policy_visual),
        "候选与选择": {
            "选择动作": trace.get("selected_action"),
            "触发来源": trace.get("trigger_source"),
            "候选数量": len(trace.get("candidates", [])),
        },
        "目标仲裁": {
            "之前": deepcopy(trace.get("goal_before")),
            "之后": deepcopy(trace.get("goal_after")),
            "切换类型": goal_transition.get("kind"),
            "切换原因": goal_transition.get("reason"),
            "已完成": goal_progress.get("completed"),
            "迟滞状态": deepcopy(goal_progress.get("completed_latches_after")),
            "重入变量": deepcopy(goal_progress.get("reentered_variables", [])),
            "严重缺口": deepcopy(goal_progress.get("severe_variables_after", [])),
        },
        "生命周期": {
            "当前状态": payload["lifecycle"].get("trial_status"),
            "当前生命": f"{payload['lifecycle'].get('life_index')}/{MAX_LIVES}",
            "生存刻度": deepcopy(payload["life_survival"]),
            "终局生命结果": deepcopy(payload["terminal_life_result"]),
            "早晚生命均值": _survival_window_summary(payload["life_survival"]),
            "转换类型": payload["transition_kind"],
            "调用策略": payload["policy_invoked"],
            "上一生命终结": deepcopy(payload["life_termination"]),
            "重生回执": deepcopy(payload["carry_reset_receipt"]),
        },
        "生存学习": {
            "模式": selection.get("selection_mode"),
            "epsilon": selection.get("epsilon"),
            "动作Q值": deepcopy(selection.get("q_by_action", {})),
            "reward": update.get("reward"),
            "TD目标": update.get("td_target"),
            "TD误差": update.get("td_error"),
            "Q表大小": survival_trace.get("q_table_size"),
            "更新次数": survival_trace.get("update_count"),
            "成功资源交互次数": None
            if controller is None
            else _resource_success_count(controller, through_sequence=frame.sequence),
        },
        "结果与变化": {
            "世界结果": world_transition.get("outcome_type"),
            "命令注入": trace["command"].get("injected_event"),
            "预测误差": deepcopy(trace.get("prediction_error")),
            "状态哈希": payload["public_state_hash"],
        },
    }


def build_advanced_details(
    frame: RecoveryFrame, *, controller: PlaygroundController
) -> dict[str, Any]:
    """Return the hidden technical details view."""

    payload = build_tk_trace_payload(frame.state, frame.trace)
    before_pose, after_pose = _poses_from_recovered_frame(frame)
    trace = frame.trace or {}
    return {
        "run_id": controller.run_id,
        "sequence": frame.sequence,
        "clock": deepcopy(frame.state["clock"]),
        "lifecycle": deepcopy(frame.state.get("lifecycle")),
        "life_survival": deepcopy(payload.get("life_survival")),
        "terminal_life_result": deepcopy(payload.get("terminal_life_result")),
        "survival_window_summary": _survival_window_summary(
            deepcopy(payload.get("life_survival") or [])
        ),
        "before_pose": before_pose,
        "after_pose": after_pose,
        "public_state_hash": payload["public_state_hash"],
        "observer_public_world_hash": payload["observer_public_world_hash"],
        "observer_observation_hash": payload["observer_observation_hash"],
        "policy_projection_hash": payload.get("policy_projection_hash"),
        "provenance_projection": deepcopy(payload.get("provenance_projection")),
        "transition_kind": payload.get("transition_kind"),
        "policy_invoked": payload.get("policy_invoked"),
        "life_termination": deepcopy(payload.get("life_termination")),
        "carry_reset_receipt": deepcopy(payload.get("carry_reset_receipt")),
        "survival_learning": deepcopy(trace.get("survival_learning")),
        "successful_resource_interactions": _resource_success_count(
            controller, through_sequence=frame.sequence
        ),
        "command_hash": trace.get("command_hash"),
        "trace_hash": trace.get("trace_hash"),
        "prev_trace_hash": trace.get("prev_trace_hash"),
        "code_path_hash": trace.get("code_path_hash"),
        "producer_function": trace.get("producer_function"),
        "input_artifacts": deepcopy(trace.get("input_artifacts")),
        "aggregation_rule": trace.get("aggregation_rule"),
    }


def recorded_waypoints(frame: RecoveryFrame) -> list[list[int]]:
    """Derive animation points only from recovered before/after coordinates."""

    before_pose, after_pose = _poses_from_recovered_frame(frame)
    before = deepcopy(before_pose["position"])
    after = deepcopy(after_pose["position"])
    expected = [after] if before == after else [before, after]
    return validate_scheduled_waypoints(expected, deepcopy(expected))


def validate_scheduled_waypoints(expected: Any, scheduled: Any) -> list[list[int]]:
    """Fail closed unless the scheduled path exactly matches the recovered path."""

    def normalize(value: Any) -> list[list[int]]:
        if not isinstance(value, list) or not value:
            raise ValueError("waypoints must be a non-empty list")
        normalized: list[list[int]] = []
        for point in value:
            if (
                not isinstance(point, list)
                or len(point) != 2
                or any(type(coordinate) is not int for coordinate in point)
            ):
                raise ValueError("waypoints must be [x, y] integer pairs")
            normalized.append([int(point[0]), int(point[1])])
        return normalized

    expected_points = normalize(expected)
    scheduled_points = normalize(scheduled)
    if len(expected_points) > 2 or len(scheduled_points) > 2:
        raise ValueError("waypoints must encode at most one recovered cell move")
    for start, end in zip(expected_points, expected_points[1:]):
        distance = abs(end[0] - start[0]) + abs(end[1] - start[1])
        if distance != 1:
            raise ValueError("recovered move is not adjacent; teleport rejected")
    if scheduled_points != expected_points:
        raise ValueError("scheduled waypoints differ from the recovered path")
    return scheduled_points


def _read_only_text(parent: tk.Misc, *, height: int) -> tk.Text:
    widget = tk.Text(
        parent,
        height=height,
        wrap=tk.WORD,
        bg="#0b1118",
        fg=_WORLD_COLORS["text"],
        insertbackground=_WORLD_COLORS["text"],
        relief=tk.FLAT,
        padx=6,
        pady=6,
    )
    widget.pack(fill=tk.BOTH, expand=True)
    widget.configure(state=tk.DISABLED)
    return widget


def _set_text(widget: tk.Text, value: str) -> None:
    widget.configure(state=tk.NORMAL)
    widget.delete("1.0", tk.END)
    widget.insert("1.0", value)
    widget.configure(state=tk.DISABLED)


class PlaygroundWindow:
    """Minimal Tk visual console bound to the single controller path."""

    def __init__(self, root: tk.Tk, controller: PlaygroundController) -> None:
        self.root = root
        self.controller = controller
        self.controller.on_committed = self._on_committed
        self.controller.on_recovered = self._on_recovered
        self.running = False
        self.display_interval_ms = 120
        self.redraw_count = 0
        self.observer_canvas_data: dict[str, Any] = {}
        self.visual_grid_data: list[list[str]] = []
        self._display_sequence = controller.recovery.frames[-1].sequence
        self._closed = False
        self._run_after_id: str | None = None
        self._animation_after_id: str | None = None
        self._animating = False
        self._timeline_refreshing = False
        self.controller._ui_resource_successes = _resource_success_count(
            controller, through_sequence=self._display_sequence
        )
        self.inject_event_var = tk.StringVar(value="")
        self.survival_learning_mode_var = tk.StringVar(value="off")
        self.sequence_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="")

        self.root.title("EGO V2 Visual Life Playground")
        self.root.configure(bg=_WORLD_COLORS["bg"])
        self.root.minsize(1180, 760)
        self._build_layout()
        self.redraw()

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(outer)
        header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(header, textvariable=self.sequence_var).pack(side=tk.LEFT)
        ttk.Label(header, textvariable=self.status_var).pack(side=tk.RIGHT)

        controls = ttk.Frame(outer)
        controls.pack(fill=tk.X, pady=(0, 8))
        self.step_button = ttk.Button(controls, text="Step", command=self._step_once)
        self.step_button.pack(side=tk.LEFT, padx=(0, 6))
        self.run_button = ttk.Button(controls, text="Run", command=self._start_run)
        self.run_button.pack(side=tk.LEFT, padx=(0, 6))
        self.pause_button = ttk.Button(controls, text="Pause", command=self._pause)
        self.pause_button.pack(side=tk.LEFT, padx=(0, 6))
        self.inject_button = ttk.Button(
            controls, text="Inject", command=self._inject_selected_event
        )
        self.inject_button.pack(side=tk.LEFT, padx=(0, 6))
        ttk.Combobox(
            controls,
            textvariable=self.inject_event_var,
            values=["", *ALLOWED_WORLD_EVENTS],
            width=18,
            state="readonly",
        ).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(controls, text="Survival learning").pack(side=tk.LEFT, padx=(0, 4))
        self.survival_learning_mode_box = ttk.Combobox(
            controls,
            textvariable=self.survival_learning_mode_var,
            values=("off", "expected_sarsa_lambda"),
            width=22,
            state="readonly",
        )
        self.survival_learning_mode_box.pack(side=tk.LEFT, padx=(0, 12))
        ttk.Button(controls, text="Inspect", command=self._inspect_latest).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(controls, text="Recover", command=self._recover).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(controls, text="Save", command=self._save).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(controls, text="Load", command=self._load).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(controls, text="Reset", command=self._reset).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(controls, text="Export", command=self._export).pack(side=tk.LEFT)

        body = ttk.Panedwindow(outer, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=3)
        body.add(right, weight=2)

        observer_box = ttk.LabelFrame(left, text="Observer world")
        observer_box.pack(fill=tk.BOTH, expand=True)
        self.observer_canvas = tk.Canvas(
            observer_box,
            bg=_WORLD_COLORS["bg"],
            highlightthickness=0,
            relief=tk.FLAT,
        )
        self.observer_canvas.pack(fill=tk.BOTH, expand=True)

        right_top = ttk.Frame(right)
        right_top.pack(fill=tk.X)
        visual_box = ttk.LabelFrame(right_top, text="Decision-time policy 5x5 visual array")
        visual_box.pack(fill=tk.X, pady=(0, 8))
        self.visual_cell_vars: list[list[tk.StringVar]] = []
        self.visual_cells: list[list[ttk.Label]] = []
        for row_index in range(5):
            vars_row: list[tk.StringVar] = []
            labels_row: list[ttk.Label] = []
            for column_index in range(5):
                var = tk.StringVar(value="")
                label = ttk.Label(
                    visual_box,
                    textvariable=var,
                    width=10,
                    anchor=tk.CENTER,
                    relief=tk.SOLID,
                    padding=(4, 4),
                )
                label.grid(row=row_index, column=column_index, padx=2, pady=2, sticky="nsew")
                vars_row.append(var)
                labels_row.append(label)
            self.visual_cell_vars.append(vars_row)
            self.visual_cells.append(labels_row)
            visual_box.grid_rowconfigure(row_index, weight=1)
        for column_index in range(5):
            visual_box.grid_columnconfigure(column_index, weight=1)

        history_box = ttk.LabelFrame(right, text="History")
        history_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.history_tree = ttk.Treeview(
            history_box,
            columns=("sequence", "tick", "action", "trigger"),
            show="headings",
            height=8,
        )
        for column, heading, width in (
            ("sequence", "Seq", 52),
            ("tick", "Tick", 52),
            ("action", "Action", 110),
            ("trigger", "Trigger", 120),
        ):
            self.history_tree.heading(column, text=heading)
            self.history_tree.column(column, width=width, stretch=True, anchor=tk.CENTER)
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        self.history_tree.bind("<<TreeviewSelect>>", self._on_history_select)

        candidate_box = ttk.LabelFrame(right, text="Candidates")
        candidate_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.candidate_tree = ttk.Treeview(
            candidate_box,
            columns=("action", "q", "score", "goal", "memory"),
            show="headings",
            height=6,
        )
        for column, heading, width in (
            ("action", "Action", 90),
            ("q", "Q", 75),
            ("score", "Score", 90),
            ("goal", "Goal", 90),
            ("memory", "Memory", 90),
        ):
            self.candidate_tree.heading(column, text=heading)
            self.candidate_tree.column(column, width=width, stretch=True, anchor=tk.CENTER)
        self.candidate_tree.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(right)
        notebook.pack(fill=tk.BOTH, expand=True)
        explain_frame = ttk.Frame(notebook)
        inspect_frame = ttk.Frame(notebook)
        advanced_frame = ttk.Frame(notebook)
        notebook.add(explain_frame, text="Chinese explanation")
        notebook.add(inspect_frame, text="Inspect")
        notebook.add(advanced_frame, text="Advanced")
        self.explanation_text = _read_only_text(explain_frame, height=14)
        self.inspect_text = _read_only_text(inspect_frame, height=14)
        self.advanced_text = _read_only_text(advanced_frame, height=14)

    def _latest_sequence(self) -> int:
        return self.controller.recovery.frames[-1].sequence

    def _frame_for_sequence(self, sequence: int) -> RecoveryFrame:
        for frame in self.controller.recovery.frames:
            if frame.sequence == sequence:
                return frame
        raise RuntimeError(f"unknown recovered sequence {sequence}")

    def _is_historical(self) -> bool:
        return self._display_sequence != self._latest_sequence()

    def _is_terminal(self) -> bool:
        lifecycle = self.controller.state.get("lifecycle", {})
        return isinstance(lifecycle, Mapping) and lifecycle.get("trial_status") == "terminal"

    def _interventions(self) -> dict[str, str]:
        return dict(
            DEFAULT_INTERVENTIONS,
            survival_learning_mode=self.survival_learning_mode_var.get(),
        )

    def _dispatch(self, *, trigger_source: str, injected_event: str | None = None) -> bool:
        if self._closed or self._animating or self._is_historical() or self._is_terminal():
            return False
        try:
            result = self.controller.dispatch(
                interventions=self._interventions(),
                trigger_source=trigger_source,
                injected_event=injected_event,
            )
        except EngineInvariantError as exc:
            self._pause()
            messagebox.showerror("Dispatch rejected", str(exc))
            if bool(getattr(self.controller, "integrity_blocked", False)):
                self.status_var.set(f"Paused integrity_blocked after commit: {exc}")
            else:
                self.status_var.set(f"Paused without commit: {exc}")
            return False
        if not result.receipt.committed:
            self._pause()
            messagebox.showerror(
                "Atomic commit rejected", result.receipt.error or "unknown"
            )
            self.status_var.set("Paused: SQLite transaction rolled back")
            return False
        return True

    def _step_once(self) -> None:
        if self.running or self._animating or self._is_historical() or self._is_terminal():
            return
        self._dispatch(trigger_source="ui_step_button")

    def _start_run(self) -> None:
        if self._closed or self.running or self._is_historical() or self._is_terminal():
            return
        self.running = True
        self._update_controls()
        self._run_after_id = self.root.after(0, self._run_tick)

    def _run_tick(self) -> None:
        self._run_after_id = None
        if self._closed or not self.running or self._animating or self._is_historical() or self._is_terminal():
            return
        self._dispatch(trigger_source="ui_run_button")

    def _queue_next_run_tick(self) -> None:
        if self._closed or not self.running or self._animating or self._is_terminal():
            return
        self._run_after_id = self.root.after(
            max(1, int(self.display_interval_ms)), self._run_tick
        )

    def _pause(self) -> None:
        self.running = False
        for attribute in ("_run_after_id", "_animation_after_id"):
            after_id = getattr(self, attribute)
            if after_id is None:
                continue
            try:
                self.root.after_cancel(after_id)
            except tk.TclError:
                pass
            setattr(self, attribute, None)
        self._animating = False
        if not self._closed:
            self._update_controls()

    def _inject_selected_event(self) -> None:
        if self.running or self._animating or self._is_historical() or self._is_terminal():
            return
        event = self.inject_event_var.get().strip()
        if not event:
            self.status_var.set("Inject rejected: choose one optional event")
            return
        self._dispatch(trigger_source="terminal_event", injected_event=event)

    def _on_committed(self, _state: dict[str, Any], _trace: dict[str, Any]) -> None:
        if self._closed:
            return
        self._display_sequence = self._latest_sequence()
        frame = self._frame_for_sequence(self._display_sequence)
        if bool(
            ((frame.trace or {}).get("survival_learning") or {}).get(
                "successful_resource_interaction"
            )
        ):
            self.controller._ui_resource_successes = int(
                getattr(self.controller, "_ui_resource_successes", 0)
            ) + 1
        self._append_history_frame(frame)
        expected = recorded_waypoints(frame)
        before_pose, after_pose = _poses_from_recovered_frame(frame)
        self._animating = len(expected) == 2
        self.redraw(
            frame=frame,
            observer_pose=before_pose if self._animating else after_pose,
            rebuild_history=False,
        )
        if not self._animating:
            if self._is_terminal():
                self._pause()
            elif self.running:
                self._queue_next_run_tick()
            self._update_controls()
            return

        def finish() -> None:
            self._animation_after_id = None
            try:
                validate_scheduled_waypoints(expected, deepcopy(expected))
            except ValueError as exc:
                self._pause()
                self.status_var.set(f"Animation rejected: {exc}")
                return
            self._animating = False
            self.redraw(
                frame=frame,
                observer_pose=after_pose,
                rebuild_history=False,
            )
            if self._is_terminal():
                self._pause()
            elif self.running:
                self._queue_next_run_tick()
            self._update_controls()

        self._animation_after_id = self.root.after(80, finish)
        self._update_controls()

    def _on_recovered(self, _recovery: Any) -> None:
        if self._closed:
            return
        self._display_sequence = self._latest_sequence()
        self.controller._ui_resource_successes = sum(
            1
            for frame in self.controller.recovery.frames
            if isinstance(frame.trace, Mapping)
            and bool(
                (frame.trace.get("survival_learning") or {}).get(
                    "successful_resource_interaction"
                )
            )
        )
        self.redraw()

    def _recover(self) -> None:
        self._pause()
        try:
            self.controller.recover()
        except Exception as exc:  # pragma: no cover - defensive UI surface
            messagebox.showerror("Recover failed", str(exc))
            self.status_var.set(f"Recover failed: {exc}")

    def _save(self) -> None:
        self._export(default_suffix=".trace.jsonl")

    def _load(self) -> None:
        self._pause()
        selected = simpledialog.askstring("Load run", "Existing run_id:")
        if not selected:
            return
        try:
            self.controller.load_run(selected.strip())
        except Exception as exc:  # pragma: no cover - UI dialog branch
            messagebox.showerror("Load failed", str(exc))
            self.status_var.set(f"Load failed: {exc}")

    def _reset(self) -> None:
        self._pause()
        selected = simpledialog.askstring("Reset run", "New run_id (blank = auto):")
        try:
            self.controller.reset_run(selected.strip() if selected and selected.strip() else None)
        except Exception as exc:  # pragma: no cover - UI dialog branch
            messagebox.showerror("Reset failed", str(exc))
            self.status_var.set(f"Reset failed: {exc}")

    def _export(self, default_suffix: str = ".jsonl") -> None:
        default_name = f"{self.controller.run_id}{default_suffix}"
        selected = filedialog.asksaveasfilename(
            title="Export recovered trace",
            initialfile=default_name,
            defaultextension=default_suffix,
        )
        if not selected:
            return
        try:
            output = self.controller.export(selected)
        except Exception as exc:  # pragma: no cover - UI dialog branch
            messagebox.showerror("Export failed", str(exc))
            self.status_var.set(f"Export failed: {exc}")
            return
        self.status_var.set(f"Exported recovered trace to {output}")

    def _inspect_latest(self) -> None:
        snapshot = build_terminal_snapshot(self.controller)
        _set_text(
            self.inspect_text,
            json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True),
        )

    def _draw_live_inspect(self, frame: RecoveryFrame) -> None:
        """Render only the recovered latest receipt on the per-tick hot path."""

        trace = frame.trace or {}
        payload = {
            "run_id": self.controller.run_id,
            "verification_mode": getattr(
                self.controller.recovery, "verification_mode", "unknown"
            ),
            "last_committed_sequence": getattr(
                self.controller.recovery, "last_committed_sequence", None
            ),
            "last_full_replay_sequence": getattr(
                self.controller.recovery, "last_full_replay_sequence", None
            ),
            "row_readback_verified": bool(
                getattr(
                    getattr(self.controller, "last_commit_receipt", None),
                    "row_readback_verified",
                    False,
                )
            ),
            "state_component_hashes": deepcopy(
                frame.state.get("component_hashes", {})
            ),
            "command_hash": trace.get("command_hash"),
            "trace_hash": trace.get("trace_hash"),
            "model_update": deepcopy(trace.get("model_update")),
            "memory_update": deepcopy(trace.get("memory_update")),
            "claim_update": deepcopy(trace.get("claim_update")),
        }
        _set_text(
            self.inspect_text,
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
        )

    def _on_history_select(self, _event: tk.Event[tk.Misc]) -> None:
        if self._timeline_refreshing:
            return
        selection = self.history_tree.selection()
        if not selection:
            return
        sequence = int(self.history_tree.item(selection[0], "values")[0])
        if sequence == self._display_sequence:
            return
        self._display_sequence = sequence
        if self._is_historical():
            self._pause()
        self.redraw(
            frame=self._frame_for_sequence(sequence), rebuild_history=False
        )

    def _append_history_frame(self, frame: RecoveryFrame) -> None:
        self._timeline_refreshing = True
        try:
            trace = frame.trace
            iid = self.history_tree.insert(
                "",
                tk.END,
                values=(
                    frame.sequence,
                    frame.state["clock"]["global_tick"],
                    "" if trace is None else trace.get("selected_action"),
                    "" if trace is None else trace.get("trigger_source"),
                ),
            )
            self.history_tree.selection_set(iid)
            self.history_tree.see(iid)
        finally:
            self._timeline_refreshing = False

    def _rebuild_history(self) -> None:
        self._timeline_refreshing = True
        try:
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            selected_iid = None
            for frame in self.controller.recovery.frames:
                trace = frame.trace
                iid = self.history_tree.insert(
                    "",
                    tk.END,
                    values=(
                        frame.sequence,
                        frame.state["clock"]["global_tick"],
                        "" if trace is None else trace.get("selected_action"),
                        "" if trace is None else trace.get("trigger_source"),
                    ),
                )
                if frame.sequence == self._display_sequence:
                    selected_iid = iid
            if selected_iid is not None:
                self.history_tree.selection_set(selected_iid)
                self.history_tree.see(selected_iid)
        finally:
            self._timeline_refreshing = False

    def _draw_candidates(self, trace: Mapping[str, Any] | None) -> None:
        for item in self.candidate_tree.get_children():
            self.candidate_tree.delete(item)
        if not isinstance(trace, Mapping):
            return
        candidates = [item for item in trace.get("candidates", []) if isinstance(item, Mapping)]
        for candidate in sorted(
            candidates,
            key=lambda item: float("-inf")
            if item.get("total_score") is None
            else float(item["total_score"]),
            reverse=True,
        ):
            iid = self.candidate_tree.insert(
                "",
                tk.END,
                values=(
                    candidate.get("action"),
                    _format_float(candidate.get("survival_q")),
                    _format_float(candidate.get("total_score")),
                    _format_float(candidate.get("current_goal_deficit_reduction")),
                    _format_float(candidate.get("memory_bias")),
                ),
            )
            if candidate.get("selected") is True:
                self.candidate_tree.selection_set(iid)

    def _draw_policy_visual(self, visual: list[list[str]]) -> None:
        self.visual_grid_data = deepcopy(visual)
        for row_index, row in enumerate(visual):
            for column_index, token in enumerate(row):
                self.visual_cell_vars[row_index][column_index].set(token)
                label = self.visual_cells[row_index][column_index]
                label.configure(background=_TOKEN_COLORS.get(token, "#2a3342"), foreground="#ecf4ff")

    def _draw_observer_world(
        self, frame: RecoveryFrame, *, observer_pose: Mapping[str, Any] | None
    ) -> None:
        observer_frame = make_public_frame(frame.state, frame.trace)
        world = observer_frame["world"]
        layout = world["layout"]
        rows = layout["base_rows"]
        width = int(layout["width"])
        height = int(layout["height"])
        canvas = self.observer_canvas
        canvas.delete("all")
        canvas.update_idletasks()
        canvas_width = max(640, canvas.winfo_width() or 640)
        canvas_height = max(420, canvas.winfo_height() or 420)
        tile = min((canvas_width - 40) / width, (canvas_height - 40) / height)
        origin_x = 20
        origin_y = 20
        for y, row in enumerate(rows):
            for x, glyph in enumerate(row):
                x0 = origin_x + x * tile
                y0 = origin_y + y * tile
                x1 = x0 + tile
                y1 = y0 + tile
                fill = _WORLD_COLORS["wall"] if glyph == "#" else _WORLD_COLORS["walkable"]
                canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline=_WORLD_COLORS["grid"])
                canvas.create_text(
                    x0 + 6,
                    y0 + 8,
                    text=f"{x},{y}",
                    anchor="nw",
                    fill=_WORLD_COLORS["muted"],
                    font=("Segoe UI", 7),
                )
        for cause, item in sorted(world["objects_by_cause"].items()):
            x, y = item["position"]
            x0 = origin_x + x * tile
            y0 = origin_y + y * tile
            x1 = x0 + tile
            y1 = y0 + tile
            canvas.create_oval(
                x0 + tile * 0.18,
                y0 + tile * 0.18,
                x1 - tile * 0.18,
                y1 - tile * 0.18,
                fill="#2c2115",
                outline=_WORLD_COLORS["object"],
                width=2,
            )
            canvas.create_text(
                (x0 + x1) / 2,
                y0 + tile * 0.34,
                text=item["token"],
                fill=_WORLD_COLORS["object"],
                font=("Segoe UI", 9, "bold"),
            )
            canvas.create_text(
                (x0 + x1) / 2,
                y0 + tile * 0.68,
                text=cause,
                fill=_WORLD_COLORS["text"],
                font=("Segoe UI", 8),
            )
        pose = observer_pose or _pose_from_world(world)
        x, y = pose["position"]
        center_x = origin_x + x * tile + tile / 2
        center_y = origin_y + y * tile + tile / 2
        canvas.create_oval(
            center_x - tile * 0.24,
            center_y - tile * 0.24,
            center_x + tile * 0.24,
            center_y + tile * 0.24,
            fill="#123744",
            outline=_WORLD_COLORS["agent"],
            width=3,
        )
        dx, dy = FACING_DELTAS[pose["facing"]]
        canvas.create_line(
            center_x,
            center_y,
            center_x + dx * tile * 0.28,
            center_y + dy * tile * 0.28,
            fill=_WORLD_COLORS["agent"],
            width=3,
            arrow=tk.LAST,
        )
        self.observer_canvas_data = {
            "sequence": frame.sequence,
            "observer_pose": deepcopy(pose),
            "world_hash": observer_frame["public_world_hash"],
            "observation_hash": observer_frame["observation_hash"],
        }

    def _update_controls(self) -> None:
        blocked = self._is_historical()
        terminal = self._is_terminal()
        self.step_button.state(
            ["disabled"] if blocked or terminal or self.running or self._animating else ["!disabled"]
        )
        self.run_button.state(
            ["disabled"] if blocked or terminal or self.running else ["!disabled"]
        )
        self.pause_button.state(["!disabled"] if self.running or self._animating else ["disabled"])
        self.inject_button.state(
            ["disabled"] if blocked or terminal or self.running or self._animating else ["!disabled"]
        )
        self.survival_learning_mode_box.configure(
            state="disabled" if blocked or terminal or self.running or self._animating else "readonly"
        )

    def redraw(
        self,
        *,
        frame: RecoveryFrame | None = None,
        observer_pose: Mapping[str, Any] | None = None,
        rebuild_history: bool = True,
    ) -> None:
        if frame is None:
            frame = self._frame_for_sequence(self._display_sequence)
        self.redraw_count += 1
        if rebuild_history:
            self._rebuild_history()
        payload = build_tk_trace_payload(frame.state, frame.trace)
        self._draw_observer_world(frame, observer_pose=observer_pose)
        self._draw_policy_visual(payload["policy_visual"]["visual"])
        self._draw_candidates(frame.trace)
        causal_view = build_chinese_causal_view(frame, controller=self.controller)
        _set_text(
            self.explanation_text,
            json.dumps(causal_view, indent=2, ensure_ascii=False, sort_keys=True),
        )
        _set_text(
            self.advanced_text,
            json.dumps(
                build_advanced_details(frame, controller=self.controller),
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            ),
        )
        self._draw_live_inspect(frame)
        clock = frame.state["clock"]
        self.sequence_var.set(
            f"Sequence {frame.sequence} / {self._latest_sequence()} · "
            f"life {int(clock['episode_index']) + 1}/{MAX_LIVES} · tick {clock['episode_tick']}"
        )
        trigger = None if frame.trace is None else frame.trace.get("trigger_source")
        lifecycle = payload["lifecycle"]
        status_bits = [
            f"observer={payload['observer_public_world_hash'][:8]}",
            f"policy={payload['observer_observation_hash'][:8]}",
            f"trigger={trigger or 'initial'}",
            f"trial={lifecycle.get('trial_status')}",
            f"survival={payload['life_survival']}",
            f"verify={getattr(self.controller.recovery, 'verification_mode', 'unknown')}",
            f"audit={getattr(self.controller.recovery, 'last_full_replay_sequence', None)}",
            f"row_readback={bool(getattr(getattr(self.controller, 'last_commit_receipt', None), 'row_readback_verified', False))}",
        ]
        dispatch_duration = getattr(
            self.controller, "last_dispatch_duration_seconds", None
        )
        if dispatch_duration is not None:
            status_bits.append(
                f"step_ms={float(dispatch_duration) * 1000.0:.1f}"
            )
        if bool(getattr(self.controller, "integrity_blocked", False)):
            status_bits.append("integrity_blocked=true")
        if payload["terminal_life_result"] is not None:
            status_bits.append(f"terminal_life={payload['terminal_life_result']}")
        self.status_var.set(
            " ".join(status_bits)
        )
        self._update_controls()

    def close(self) -> None:
        if self._closed:
            return
        self._pause()
        self._closed = True
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass


def _format_float(value: Any) -> str:
    if type(value) not in {int, float}:
        return "—"
    return f"{float(value):+.4f}"


def run_app(
    db_path: str | Path | None = None,
    *,
    seed: int = 17,
    world_seed: int = DEFAULT_PRIVATE_WORLD_SEED,
    layout_id: str | None = None,
    run_id: str | None = None,
) -> None:
    store = SQLiteEventStore(db_path or default_db_path())
    try:
        controller = PlaygroundController(
            store,
            run_id=run_id,
            seed=seed,
            world_seed=world_seed,
            layout_id=layout_id,
        )
        root = tk.Tk()
        window = PlaygroundWindow(root, controller)
        root.protocol("WM_DELETE_WINDOW", window.close)
        root.mainloop()
    finally:
        store.close()
