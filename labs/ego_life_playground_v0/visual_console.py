"""Tk visual view routed through the single PlaygroundController."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, Callable, Mapping

from .controller import (
    DISCLOSURE,
    PlaygroundController,
    public_state_hash,
)
from .engine import (
    ACTIONS,
    CUES,
    DEFAULT_INTERVENTIONS,
    DEFAULT_PRIVATE_WORLD_SEED,
    EngineInvariantError,
)
from .microworld import (
    ALLOWED_WORLD_EVENTS,
    cue_for_event,
    default_event_for_sequence,
    event_for_cue,
    make_public_frame,
)
from .store import RecoveryFrame, SQLiteEventStore, default_db_path
from .terminal import _timeline_from_recovery, build_terminal_snapshot

def build_tk_trace_payload(
    state: Mapping[str, Any], trace: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Build the normal Tk trace view without full state/world/trace commitments."""

    current_goal = state["current_goal"]
    if trace is None:
        return {
            "clock": deepcopy(state["clock"]),
            "current_goal": deepcopy(current_goal),
            "selected_action": None,
            "public_state_hash": public_state_hash(state),
        }
    return {
        "clock": deepcopy(state["clock"]),
        "current_goal": deepcopy(current_goal),
        "trigger_source": trace["trigger_source"],
        "interventions": deepcopy(trace["interventions"]),
        "command": deepcopy(trace["command"]),
        "selected_action": trace["selected_action"],
        "prediction": deepcopy(trace["prediction"]),
        "actual_delta": deepcopy(trace["actual_delta"]),
        "prediction_error": deepcopy(trace["prediction_error"]),
        "model_update": deepcopy(trace["model_update"]),
        "memory_update": deepcopy(trace["memory_update"]),
        "claim_retrieval": deepcopy(trace.get("claim_retrieval")),
        "claim_update": deepcopy(trace.get("claim_update")),
        "world_outcome": deepcopy(trace.get("world_outcome")),
        "provenance_projection": deepcopy(trace["provenance_projection"]),
        "memory_refs": deepcopy(trace["memory_refs"]),
        "policy_projection_hash": trace.get("policy_projection_hash"),
        "policy_non_memory_projection_hash": trace.get(
            "policy_non_memory_projection_hash"
        ),
        "public_state_hash": public_state_hash(state),
        "code_path_hash": trace["code_path_hash"],
    }


_VISUAL_COLORS = {
    "root": "#080b12",
    "window": "#090d14",
    "title": "#111925",
    "status": "#0f151f",
    "meta": "#0c121b",
    "panel": "#121a26",
    "timeline": "#101722",
    "controls": "#0b1018",
    "tile": "#182335",
    "wall": "#080c12",
    "path": "#1e3949",
    "border": "#29364e",
    "text": "#eef4ff",
    "muted": "#8796ac",
    "muted2": "#6e7f99",
    "cyan": "#59dde2",
    "green": "#78e0a2",
    "amber": "#ffca70",
    "rose": "#ff8098",
    "purple": "#aaa0ff",
}


_VISUAL_FONT = ("Microsoft YaHei UI", 10)


_VISUAL_FONT_SMALL = ("Microsoft YaHei UI", 9)


_VISUAL_FONT_TINY = ("Microsoft YaHei UI", 8)


_VISUAL_FONT_HEAD = ("Microsoft YaHei UI", 12, "bold")


_VISUAL_FONT_TITLE = ("Microsoft YaHei UI", 16, "bold")


_ZH_LABELS: dict[str, dict[str, str]] = {
    "action": {
        "approach": "靠近",
        "explore": "探索",
        "forage": "获取资源",
        "rest": "休整",
        "withdraw": "撤离",
    },
    "event": {
        "resource_appears": "资源出现",
        "social_signal": "社交信号出现",
        "novel_object": "新奇物体出现",
        "threat_nearby": "附近出现威胁",
        "quiet_interval": "环境进入安静时段",
    },
    "cue": {
        "resource": "资源线索",
        "contact": "接触线索",
        "novelty": "新奇线索",
        "threat": "威胁线索",
        "quiet": "安静线索",
    },
    "position": {
        "site_a": "地点 A",
        "site_b": "地点 B",
        "fork": "分岔点",
        "home": "休息区",
    },
    "object": {
        "resource": "资源",
        "signal": "社交信号",
        "novel_object": "新奇物体",
        "threat": "威胁",
        "shelter": "庇护区",
    },
    "state": {
        "energy": "能量",
        "safety": "安全",
        "connection": "连接",
        "stimulation": "刺激",
    },
}


_EVENT_DISPLAY_TO_ID = {
    label: technical_id for technical_id, label in _ZH_LABELS["event"].items()
}


def _zh_label(namespace: str, value: Any) -> str:
    """Translate only predeclared public IDs; unknown IDs fail closed."""

    if value is None:
        return "未记录／未知"
    return _ZH_LABELS.get(namespace, {}).get(str(value), "未记录／未知")


def _format_number(value: Any, *, digits: int = 3, signed: bool = False) -> str:
    if type(value) not in {int, float}:
        return "未记录／未知"
    template = f"{{:{'+' if signed else ''}.{digits}f}}"
    return template.format(float(value))


def _format_delta(values: Any) -> str:
    if not isinstance(values, Mapping):
        return "未记录／未知"
    parts = []
    for key in ("energy", "safety", "connection", "stimulation"):
        if key in values:
            parts.append(f"{_zh_label('state', key)} {_format_number(values[key], signed=True)}")
    return " · ".join(parts) if parts else "未记录／未知"


def _format_internal_state(values: Any) -> str:
    if not isinstance(values, Mapping):
        return "未记录／未知"
    parts = []
    for key in ("energy", "safety", "connection", "stimulation"):
        if key in values:
            parts.append(f"{_zh_label('state', key)} {_format_number(values[key])}")
    return " · ".join(parts) if parts else "未记录／未知"


def _format_goal(goal: Any) -> str:
    if not isinstance(goal, Mapping):
        return "未记录／未知"
    state_label = _zh_label("state", goal.get("state_variable"))
    target = _format_number(goal.get("target"), digits=2)
    return f"提升{state_label}至 {target}"


def _selected_candidate(trace: Mapping[str, Any]) -> Mapping[str, Any] | None:
    selected = trace.get("selected_action")
    candidates = trace.get("candidates")
    if not isinstance(candidates, list):
        return None
    return next(
        (
            candidate
            for candidate in candidates
            if isinstance(candidate, Mapping) and candidate.get("action") == selected
        ),
        None,
    )


def build_chinese_causal_view(frame: RecoveryFrame) -> dict[str, Any]:
    """Translate one recovered frame without interpreting unrecorded mental state."""

    state = frame.state
    trace = frame.trace
    if trace is None:
        return {
            "步骤发生前": {
                "当前目标": _format_goal(state.get("current_goal")),
                "正在执行的动作": "未记录／未知",
                "当前预期": "未记录／未知",
                "决策依据": "尚无已提交步骤",
                "关键内部状态": _format_internal_state(state.get("organism")),
                "读取的记忆及来源": "尚无本步读取记录",
            },
            "外部事件": {
                "发生了什么": "尚无已提交事件",
                "可观察线索": "未记录／未知",
                "是否来自用户注入": "否",
            },
            "候选与选择": {
                "候选排行": [],
                "选择的行动": "未记录／未知",
                "胜出依据": "未记录／未知",
            },
            "结果与变化": {
                "当前预期": "未记录／未知",
                "实际结果": "未记录／未知",
                "预测误差": "未记录／未知",
                "更新与巩固": "未记录／未知",
                "内部状态变化": _format_internal_state(state.get("organism")),
                "记忆与来源变化": "未记录／未知",
            },
            "动作连续性": {
                "之前动作": "未记录／未知",
                "之前动作状态": "未记录／未知",
                "中断原因": "未记录／未知",
                "是否重新选择": "否",
                "新动作": "未记录／未知",
                "新目标": _format_goal(state.get("current_goal")),
            },
        }

    policy = trace.get("policy_non_memory_projection")
    policy = policy if isinstance(policy, Mapping) else {}
    observation = trace.get("observation")
    observation = observation if isinstance(observation, Mapping) else {}
    visible_objects = observation.get("visible_object_ids")
    visible_objects = visible_objects if isinstance(visible_objects, list) else []
    visible_labels = [_zh_label("object", item) for item in visible_objects]
    visible_labels = [item for item in visible_labels if item != "未记录／未知"]
    memory_refs = trace.get("memory_refs")
    memory_refs = memory_refs if isinstance(memory_refs, list) else []
    claims = trace.get("claim_retrieval")
    claims = claims if isinstance(claims, Mapping) else {}
    claim_items = claims.get("claims") if isinstance(claims.get("claims"), list) else []
    source_count = len(claims.get("source_episode_ids", [])) if isinstance(
        claims.get("source_episode_ids"), list
    ) else 0
    selected = _selected_candidate(trace)
    candidates = trace.get("candidates")
    candidates = [item for item in candidates if isinstance(item, Mapping)] if isinstance(
        candidates, list
    ) else []
    ranked = sorted(
        candidates,
        key=lambda item: float("-inf")
        if type(item.get("total_score")) not in {int, float}
        else float(item["total_score"]),
        reverse=True,
    )
    candidate_rows = []
    for rank, candidate in enumerate(ranked, start=1):
        candidate_rows.append(
            {
                "排名": rank,
                "行动": _zh_label("action", candidate.get("action")),
                "总分": _format_number(candidate.get("total_score"), signed=True),
                "目标收益": _format_number(
                    candidate.get("current_goal_deficit_reduction"), signed=True
                ),
                "总收益": _format_number(candidate.get("total_deficit_reduction"), signed=True),
                "记忆": _format_number(candidate.get("memory_bias"), signed=True),
                "新奇": _format_number(candidate.get("untried_bonus"), signed=True),
                "代价": _format_number(candidate.get("action_cost"), signed=True),
                "路径格数": candidate.get("path", {}).get("shortest_path_steps")
                if isinstance(candidate.get("path"), Mapping)
                else "未记录／未知",
            }
        )
    if selected is None:
        winning_basis = "未记录／未知"
    else:
        runner_score = ranked[1].get("total_score") if len(ranked) > 1 else None
        winning_basis = (
            f"记录总分 {_format_number(selected.get('total_score'), signed=True)}；"
            f"次高分 {_format_number(runner_score, signed=True)}；"
            "仅依据本步候选评分字段"
        )
    model_update = trace.get("model_update")
    model_update = model_update if isinstance(model_update, Mapping) else {}
    memory_update = trace.get("memory_update")
    memory_update = memory_update if isinstance(memory_update, Mapping) else {}
    claim_update = trace.get("claim_update")
    claim_update = claim_update if isinstance(claim_update, Mapping) else {}
    memory_bytes = trace.get("memory_bytes")
    memory_bytes = memory_bytes if isinstance(memory_bytes, Mapping) else {}
    update_text = (
        f"模型更新：{'已应用' if model_update.get('applied') is True else '未应用'}；"
        f"记忆写入：{'已应用' if memory_update.get('applied') is True else '未应用'}；"
        f"巩固：{'已应用' if memory_update.get('consolidation_applied') is True else '未应用'}"
    )
    memory_change = (
        f"读取 {len(memory_refs)} 条记忆；竞争主张 {len(claim_items)} 条；"
        f"来源回合 {source_count} 个；"
        f"记忆字节：{'已变化' if memory_bytes.get('changed') is True else '未变化'}；"
        f"主张记录：{'已写入' if claim_update.get('applied') is True else '未写入'}"
    )
    before_internal = policy.get("organism")
    after_internal = state.get("organism")
    return {
        "步骤发生前": {
            "当前目标": _format_goal(trace.get("goal_before")),
            "正在执行的动作": "未记录／未知",
            "当前预期": _format_delta(trace.get("prediction")),
            "决策依据": winning_basis,
            "关键内部状态": _format_internal_state(before_internal),
            "读取的记忆及来源": (
                f"读取 {len(memory_refs)} 条记忆；竞争主张 {len(claim_items)} 条；"
                f"来源回合 {source_count} 个"
            ),
        },
        "外部事件": {
            "发生了什么": _zh_label("event", trace.get("world_event")),
            "可观察线索": "、".join(visible_labels) if visible_labels else "无已记录可见物体",
            "观察位置": _zh_label("position", observation.get("agent_position")),
            "是否来自用户注入": "是"
            if trace.get("trigger_source") == "terminal_event"
            else "否",
        },
        "候选与选择": {
            "候选排行": candidate_rows,
            "选择的行动": _zh_label("action", trace.get("selected_action")),
            "胜出依据": winning_basis,
        },
        "结果与变化": {
            "当前预期": _format_delta(trace.get("prediction")),
            "实际结果": _format_delta(trace.get("actual_delta")),
            "预测误差": _format_delta(trace.get("prediction_error")),
            "更新与巩固": update_text,
            "内部状态变化": (
                f"之前：{_format_internal_state(before_internal)}\n"
                f"之后：{_format_internal_state(after_internal)}"
            ),
            "记忆与来源变化": memory_change,
        },
        "动作连续性": {
            "之前动作": "未记录／未知",
            "之前动作状态": "未记录／未知",
            "中断原因": "未记录／未知",
            "是否重新选择": "是（本步记录了候选与选择）",
            "新动作": _zh_label("action", trace.get("selected_action")),
            "新目标": _format_goal(trace.get("goal_after")),
        },
    }


def build_advanced_details(
    frame: RecoveryFrame, *, controller: PlaygroundController
) -> dict[str, Any]:
    """Return technical IDs/hashes for the hidden advanced-details panel only."""

    trace = frame.trace or {}
    clock = frame.state.get("clock", {})
    return {
        "run_id": controller.run_id,
        "sequence": frame.sequence,
        "episode_id": clock.get("episode_id"),
        "episode_index": clock.get("episode_index"),
        "episode_tick": clock.get("episode_tick"),
        "run_seed": controller.run_meta.get("seed"),
        "world_seed": controller.world_seed,
        "layout_id": frame.state.get("world", {}).get("layout", {}).get("layout_id"),
        "event_id": trace.get("world_event"),
        "cue_id": trace.get("cue"),
        "action_id": trace.get("selected_action"),
        "trigger_source": trace.get("trigger_source"),
        "interventions": deepcopy(trace.get("interventions")),
        "command_hash": trace.get("command_hash"),
        "trace_hash": trace.get("trace_hash"),
        "prev_trace_hash": trace.get("prev_trace_hash"),
        "state_before_hash": trace.get("state_before_hash"),
        "state_after_hash": trace.get("state_after_hash"),
        "observation_hash": trace.get("observation_hash"),
        "policy_projection_hash": trace.get("policy_projection_hash"),
        "code_path_hash": trace.get("code_path_hash"),
        "producer_function": trace.get("producer_function"),
        "input_artifacts": deepcopy(trace.get("input_artifacts")),
        "aggregation_rule": trace.get("aggregation_rule"),
        "memory_refs": deepcopy(trace.get("memory_refs")),
        "provenance_projection": deepcopy(trace.get("provenance_projection")),
        "claim_retrieval": deepcopy(trace.get("claim_retrieval")),
    }


def recorded_waypoints(frame: RecoveryFrame) -> list[list[int]]:
    """Read animation waypoints only from the recovered frame's recorded path."""

    if frame.trace is None:
        world = make_public_frame(frame.state)
        position = world["agent"]["position"]
        raw = [deepcopy(world["layout"]["positions"][position])]
    else:
        raw = deepcopy(
            frame.trace["world_transition"]["path"]["shortest_path_coordinates"]
        )
    return validate_scheduled_waypoints(raw, deepcopy(raw))


def validate_scheduled_waypoints(
    expected: Any, scheduled: Any
) -> list[list[int]]:
    """Fail closed unless actual scheduled endpoints equal the recorded path."""

    def normalized(value: Any) -> list[list[int]]:
        if (
            not isinstance(value, list)
            or not value
            or any(
                not isinstance(point, list)
                or len(point) != 2
                or any(type(coordinate) is not int for coordinate in point)
                for point in value
            )
        ):
            raise ValueError("recorded path must be a non-empty list of [x,y] integers")
        return deepcopy(value)

    expected_points = normalized(expected)
    scheduled_points = normalized(scheduled)
    if scheduled_points != expected_points:
        raise ValueError("scheduled waypoints differ from the recorded path")
    return scheduled_points


def _configure_visual_styles(root: tk.Misc) -> None:
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure(
        "Visual.TButton",
        font=_VISUAL_FONT,
        foreground=_VISUAL_COLORS["text"],
        background="#182233",
        bordercolor=_VISUAL_COLORS["border"],
        padding=(12, 7),
    )
    style.map(
        "Visual.TButton",
        background=[("active", "#24334a"), ("disabled", "#111722")],
        foreground=[("disabled", _VISUAL_COLORS["muted2"])],
    )
    style.configure(
        "VisualAccent.TButton",
        font=_VISUAL_FONT,
        foreground="#071015",
        background=_VISUAL_COLORS["cyan"],
        bordercolor=_VISUAL_COLORS["cyan"],
        padding=(13, 7),
    )
    style.configure(
        "Visual.Treeview",
        background="#101824",
        fieldbackground="#101824",
        foreground=_VISUAL_COLORS["text"],
        rowheight=25,
        bordercolor=_VISUAL_COLORS["border"],
        font=_VISUAL_FONT_TINY,
    )
    style.configure(
        "Visual.Treeview.Heading",
        background="#182335",
        foreground=_VISUAL_COLORS["text"],
        font=_VISUAL_FONT_TINY,
    )
    style.map(
        "Visual.Treeview",
        background=[("selected", "#183b48")],
        foreground=[("selected", _VISUAL_COLORS["cyan"])],
    )
    style.configure(
        "Visual.TCombobox",
        fieldbackground="#151f2d",
        background="#151f2d",
        foreground=_VISUAL_COLORS["text"],
        arrowcolor=_VISUAL_COLORS["cyan"],
    )
    for name, color in (
        ("Energy", _VISUAL_COLORS["amber"]),
        ("Safety", _VISUAL_COLORS["green"]),
        ("Connection", _VISUAL_COLORS["rose"]),
        ("Stimulation", _VISUAL_COLORS["cyan"]),
    ):
        style.configure(
            f"{name}.Horizontal.TProgressbar",
            troughcolor="#202b3b",
            background=color,
            bordercolor="#202b3b",
            thickness=7,
        )


class _ScrollableFrame(tk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bg=_VISUAL_COLORS["window"])
        self.canvas = tk.Canvas(
            self, bg=_VISUAL_COLORS["window"], highlightthickness=0, bd=0
        )
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=_VISUAL_COLORS["window"])
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.inner.bind(
            "<Configure>",
            lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(self.window_id, width=event.width),
        )


class PlaygroundWindow:
    """Paused-by-default Tk product clock and frame-derived timeline."""

    def __init__(
        self,
        root: tk.Tk,
        controller: PlaygroundController,
        *,
        display_interval_ms: int = 500,
        animation_segment_ms: int = 150,
    ) -> None:
        if type(display_interval_ms) is not int or display_interval_ms <= 0:
            raise ValueError("display_interval_ms must be a positive integer")
        if type(animation_segment_ms) is not int or animation_segment_ms < 0:
            raise ValueError("animation_segment_ms must be a non-negative integer")
        self.root = root
        self.controller = controller
        self.display_interval_ms = display_interval_ms
        self.running = False
        self._after_id: str | None = None
        self._closed = False
        self._timeline_refreshing = False
        self._display_sequence = controller.recovery.frames[-1].sequence
        self._run_after_id: str | None = None
        self._animation_after_id: str | None = None
        self._animation_generation = 0
        self._animation_segment_ms = animation_segment_ms
        self._animation_subframes = 5
        self._animation_subframe = 0
        self._animation_index = 0
        self._animating = False
        self._animation_paused = False
        self._animation_frame: RecoveryFrame | None = None
        self._expected_waypoints: list[list[int]] = []
        self._scheduled_waypoints: list[list[int]] = []
        self._animation_completed_sequence: int | None = None
        self._cell_centers: dict[tuple[int, int], tuple[float, float]] = {}
        self._agent_items: tuple[int, int, int] | None = None
        self._panel_frame_ids: dict[str, int] = {}
        self._timeline_scale_refreshing = False
        self._advanced_visible = False

        root.title("EGO 本地小世界 · 真实运行视觉控制台")
        root.configure(bg=_VISUAL_COLORS["root"])
        root.geometry("1480x940")
        root.minsize(1100, 720)

        _configure_visual_styles(root)
        style = ttk.Style(root)
        style.configure(
            "Disclosure.TLabel",
            foreground=_VISUAL_COLORS["muted"],
            background=_VISUAL_COLORS["window"],
            font=_VISUAL_FONT_TINY,
        )

        shell = tk.Frame(root, bg=_VISUAL_COLORS["window"], padx=10, pady=10)
        shell.pack(fill=tk.BOTH, expand=True)
        title_bar = tk.Frame(shell, bg=_VISUAL_COLORS["title"], height=46)
        title_bar.pack(fill=tk.X, pady=(0, 7))
        title_bar.pack_propagate(False)
        tk.Label(
            title_bar,
            text="EGO 本地小世界",
            bg=_VISUAL_COLORS["title"],
            fg=_VISUAL_COLORS["text"],
            font=_VISUAL_FONT_TITLE,
        ).pack(side=tk.LEFT, padx=(15, 12))
        tk.Label(
            title_bar,
            text="真实运行 · 默认关闭",
            bg="#18343b",
            fg=_VISUAL_COLORS["cyan"],
            font=_VISUAL_FONT_SMALL,
            padx=9,
            pady=3,
        ).pack(side=tk.LEFT)
        self.sequence_var = tk.StringVar()
        tk.Label(
            title_bar,
            textvariable=self.sequence_var,
            bg=_VISUAL_COLORS["title"],
            fg=_VISUAL_COLORS["muted"],
            font=_VISUAL_FONT,
        ).pack(side=tk.LEFT, padx=14)
        ttk.Label(
            shell,
            text="本地确定性小世界；显式启动才启用；无网络、无后台主动动作；科学权重为零。",
            style="Disclosure.TLabel",
        ).pack(fill=tk.X, pady=(0, 6))

        toolbar = tk.Frame(shell, bg=_VISUAL_COLORS["controls"], padx=8, pady=7)
        toolbar.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            toolbar,
            text="注入事件",
            bg=_VISUAL_COLORS["controls"],
            fg=_VISUAL_COLORS["muted"],
            font=_VISUAL_FONT_SMALL,
        ).pack(side=tk.LEFT)
        self.cue_var = tk.StringVar(value="resource")
        self.event_display_var = tk.StringVar(value=_ZH_LABELS["event"]["resource_appears"])
        self.cue_box = ttk.Combobox(
            toolbar,
            textvariable=self.event_display_var,
            values=tuple(_EVENT_DISPLAY_TO_ID),
            state="readonly",
            width=16,
            style="Visual.TCombobox",
        )
        self.cue_box.pack(side=tk.LEFT, padx=(4, 10))

        self.memory_mode_var = tk.StringVar(value="标准记忆")
        tk.Label(
            toolbar,
            text="记忆",
            bg=_VISUAL_COLORS["controls"],
            fg=_VISUAL_COLORS["muted"],
            font=_VISUAL_FONT_SMALL,
        ).pack(side=tk.LEFT)
        self.memory_mode_box = ttk.Combobox(
            toolbar,
            textvariable=self.memory_mode_var,
            values=("标准记忆", "关闭记忆读取"),
            state="readonly",
            width=14,
            style="Visual.TCombobox",
        )
        self.memory_mode_box.pack(side=tk.LEFT, padx=(4, 10))
        self.memory_mode_box.bind("<<ComboboxSelected>>", self._on_memory_mode_selected)

        self.freeze_updates_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            toolbar,
            text="冻结模型与记忆更新",
            variable=self.freeze_updates_var,
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.provenance_mode_var = tk.StringVar(value="标准来源")
        tk.Label(
            toolbar,
            text="来源",
            bg=_VISUAL_COLORS["controls"],
            fg=_VISUAL_COLORS["muted"],
            font=_VISUAL_FONT_SMALL,
        ).pack(side=tk.LEFT)
        self.provenance_mode_box = ttk.Combobox(
            toolbar,
            textvariable=self.provenance_mode_var,
            values=("标准来源", "打乱来源投影"),
            state="readonly",
            width=14,
            style="Visual.TCombobox",
        )
        self.provenance_mode_box.pack(side=tk.LEFT, padx=(4, 10))
        self.provenance_mode_box.bind(
            "<<ComboboxSelected>>", self._on_provenance_mode_selected
        )

        self.step_button = ttk.Button(
            toolbar, text="执行一步", command=self._step_once, style="VisualAccent.TButton"
        )
        self.step_button.pack(side=tk.LEFT, padx=3)
        self.run_button = ttk.Button(
            toolbar, text="连续运行", command=self._start_run, style="Visual.TButton"
        )
        self.run_button.pack(side=tk.LEFT, padx=3)
        self.pause_button = ttk.Button(
            toolbar, text="暂停", command=self._pause, style="Visual.TButton"
        )
        self.pause_button.pack(side=tk.LEFT, padx=3)
        self.inject_button = ttk.Button(
            toolbar, text="注入", command=self._inject_event, style="Visual.TButton"
        )
        self.inject_button.pack(side=tk.LEFT, padx=3)
        utility_bar = tk.Frame(shell, bg=_VISUAL_COLORS["controls"], padx=8, pady=5)
        utility_bar.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(
            utility_bar, text="重新计算", command=self._recover, style="Visual.TButton"
        ).pack(side=tk.RIGHT, padx=3)
        ttk.Button(utility_bar, text="导出", command=self._export, style="Visual.TButton").pack(
            side=tk.RIGHT, padx=3
        )
        ttk.Button(utility_bar, text="加载", command=self._load_run, style="Visual.TButton").pack(
            side=tk.RIGHT, padx=3
        )
        ttk.Button(utility_bar, text="新建运行", command=self._reset_run, style="Visual.TButton").pack(
            side=tk.RIGHT, padx=3
        )
        self.advanced_toolbar_button = ttk.Button(
            utility_bar,
            text="高级详情",
            command=self._toggle_advanced,
            style="Visual.TButton",
        )
        self.advanced_toolbar_button.pack(side=tk.RIGHT, padx=3)
        tk.Label(
            utility_bar,
            text="保存／加载／重算均委托 canonical controller；运行标识与路径仅在高级详情显示。",
            bg=_VISUAL_COLORS["controls"],
            fg=_VISUAL_COLORS["muted2"],
            font=_VISUAL_FONT_TINY,
        ).pack(side=tk.LEFT)

        body = ttk.Panedwindow(shell, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(body, padding=(0, 0, 6, 0))
        right = ttk.Frame(body, padding=(6, 0, 0, 0))
        body.add(left, weight=7)
        body.add(right, weight=4)

        state_box = ttk.LabelFrame(left, text="当前状态", padding=8)
        state_box.pack(fill=tk.X, pady=(0, 8))
        self.state_widgets: dict[str, tuple[ttk.Progressbar, ttk.Label]] = {}
        for row, key in enumerate(("energy", "safety", "connection", "stimulation")):
            ttk.Label(state_box, text=_zh_label("state", key), width=8).grid(
                row=row, column=0, sticky=tk.W, pady=3
            )
            style_name = {
                "energy": "Energy.Horizontal.TProgressbar",
                "safety": "Safety.Horizontal.TProgressbar",
                "connection": "Connection.Horizontal.TProgressbar",
                "stimulation": "Stimulation.Horizontal.TProgressbar",
            }[key]
            bar = ttk.Progressbar(state_box, maximum=100, length=260, style=style_name)
            bar.grid(row=row, column=1, sticky=tk.EW, padx=5)
            value = ttk.Label(state_box, width=7)
            value.grid(row=row, column=2, sticky=tk.E)
            self.state_widgets[key] = (bar, value)
        state_box.columnconfigure(1, weight=1)

        map_box = tk.Frame(
            left,
            bg="#0a1018",
            highlightthickness=1,
            highlightbackground=_VISUAL_COLORS["border"],
            padx=8,
            pady=8,
        )
        map_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        map_header = tk.Frame(map_box, bg="#0a1018")
        map_header.pack(fill=tk.X, pady=(0, 6))
        tk.Label(
            map_header,
            text="公开世界地图",
            bg="#0a1018",
            fg=_VISUAL_COLORS["text"],
            font=_VISUAL_FONT_HEAD,
        ).pack(side=tk.LEFT)
        tk.Label(
            map_header,
            text="路径逐点来自已恢复 trace",
            bg="#0a1018",
            fg=_VISUAL_COLORS["cyan"],
            font=_VISUAL_FONT_TINY,
        ).pack(side=tk.RIGHT)
        self.map_canvas = tk.Canvas(
            map_box,
            bg="#070b11",
            height=350,
            highlightthickness=1,
            highlightbackground=_VISUAL_COLORS["border"],
            bd=0,
        )
        self.map_canvas.pack(fill=tk.BOTH, expand=True)
        self.map_canvas.bind(
            "<Configure>",
            lambda _event: self.redraw(
                self._frame_for_sequence(self._display_sequence), rebuild_timeline=False
            )
            if not self._closed and not self._animating
            else None,
        )
        legend = tk.Frame(map_box, bg="#0a1018", pady=5)
        legend.pack(fill=tk.X)
        for text, color in (
            ("● 主体位置", _VISUAL_COLORS["cyan"]),
            ("■ 已记录路径", "#4a8398"),
            ("◇ 可见物体", _VISUAL_COLORS["amber"]),
            ("墙体 / 可行走格", _VISUAL_COLORS["muted"]),
        ):
            tk.Label(
                legend,
                text=text,
                bg="#0a1018",
                fg=color,
                font=_VISUAL_FONT_TINY,
            ).pack(side=tk.LEFT, padx=(0, 16))

        goals_box = ttk.LabelFrame(left, text="当前目标", padding=6)
        goals_box.pack(fill=tk.X, pady=(0, 8))
        self.goals_text = _read_only_text(goals_box, height=4)

        memory_box = ttk.LabelFrame(left, text="记忆与来源", padding=6)
        memory_box.pack(fill=tk.X)
        self.memory_text = _read_only_text(memory_box, height=6)

        timeline_box = ttk.LabelFrame(right, text="已恢复时间线／历史只读", padding=6)
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
            ("sequence", "序列", 55),
            ("global_tick", "总步", 55),
            ("episode", "回合", 55),
            ("episode_tick", "回合步", 60),
            ("cue", "事件", 100),
            ("action", "选择行动", 100),
        ):
            self.timeline_tree.heading(column, text=heading)
            self.timeline_tree.column(column, width=width, anchor=tk.CENTER)
        self.timeline_tree.pack(fill=tk.X)
        self.timeline_tree.bind("<<TreeviewSelect>>", self._on_timeline_select)
        self.timeline_scale_var = tk.IntVar(value=self._display_sequence)
        self.timeline_scale = tk.Scale(
            timeline_box,
            from_=0,
            to=self._latest_sequence(),
            orient=tk.HORIZONTAL,
            variable=self.timeline_scale_var,
            command=self._on_timeline_scale,
            showvalue=False,
            resolution=1,
            bg=_VISUAL_COLORS["timeline"],
            troughcolor="#273449",
            activebackground=_VISUAL_COLORS["cyan"],
            highlightthickness=0,
            bd=0,
        )
        self.timeline_scale.pack(fill=tk.X, pady=(5, 0))

        candidate_box = ttk.LabelFrame(
            right, text="候选行动排行与分数拆解", padding=6
        )
        candidate_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        columns = (
            "action",
            "goal",
            "total",
            "memory",
            "novelty",
            "cost",
            "topology",
            "steps",
            "tie",
            "score",
        )
        self.candidate_tree = ttk.Treeview(candidate_box, columns=columns, show="headings", height=7)
        headings = {
            "action": "行动",
            "goal": "目标",
            "total": "总收益",
            "memory": "记忆",
            "novelty": "新奇",
            "cost": "代价",
            "topology": "路径代价",
            "steps": "路径格",
            "tie": "确定项",
            "score": "总分",
        }
        for column in columns:
            self.candidate_tree.heading(column, text=headings[column])
            self.candidate_tree.column(column, width=75, anchor=tk.CENTER)
        self.candidate_tree.configure(style="Visual.Treeview")
        self.candidate_tree.pack(fill=tk.BOTH, expand=True)

        lower = ttk.Panedwindow(right, orient=tk.HORIZONTAL)
        lower.pack(fill=tk.BOTH, expand=True)
        model_box = ttk.LabelFrame(lower, text="步骤发生前／外部事件／动作连续性", padding=6)
        trace_box = ttk.LabelFrame(lower, text="结果与变化", padding=6)
        lower.add(model_box, weight=1)
        lower.add(trace_box, weight=1)
        self.model_text = _read_only_text(model_box, height=17)
        self.trace_text = _read_only_text(trace_box, height=17)
        self.before_text = self.model_text
        self.event_text = self.model_text

        self.advanced_box = ttk.LabelFrame(right, text="高级详情 · 只读技术字段", padding=6)
        self.advanced_text = _read_only_text(self.advanced_box, height=12)
        self.advanced_button = self.advanced_toolbar_button

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
        memory_mode = {
            "标准记忆": "canonical",
            "关闭记忆读取": "off",
        }.get(self.memory_mode_var.get())
        provenance_mode = {
            "标准来源": "canonical",
            "打乱来源投影": "shuffle_projection",
        }.get(self.provenance_mode_var.get())
        if memory_mode is None or provenance_mode is None:
            raise EngineInvariantError("界面干预选项未记录／未知")
        snapshot = {
            "memory_mode": memory_mode,
            "update_mode": "frozen" if self.freeze_updates_var.get() else "enabled",
            "provenance_mode": provenance_mode,
            "provenance_shuffle_seed": DEFAULT_INTERVENTIONS[
                "provenance_shuffle_seed"
            ],
            "consolidation_mode": "canonical",
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
        if self.memory_mode_var.get() == "关闭记忆读取":
            self.provenance_mode_var.set("标准来源")

    def _on_provenance_mode_selected(self, _event: tk.Event[tk.Misc]) -> None:
        if self.provenance_mode_var.get() == "打乱来源投影":
            self.memory_mode_var.set("标准记忆")

    def _latest_sequence(self) -> int:
        return self.controller.recovery.frames[-1].sequence

    def _is_historical(self) -> bool:
        return self._display_sequence != self._latest_sequence()

    def _step_once(self) -> None:
        if self.running or self._animating or self._is_historical():
            return
        world_event = _EVENT_DISPLAY_TO_ID.get(self.event_display_var.get())
        if world_event is None:
            self.status_var.set("执行一步被拒绝：事件未记录／未知")
            return
        self._dispatch("ui_step_button", world_event=world_event)

    def _start_run(self) -> None:
        if self._closed or self.running or self._is_historical():
            return
        self.running = True
        if self._animating:
            self._animation_paused = False
            self._schedule_animation_subframe()
            self._update_progress_controls()
            return
        self._update_progress_controls()
        self._run_after_id = self.root.after(0, self._run_tick)
        self._after_id = self._run_after_id

    def _run_tick(self) -> None:
        self._run_after_id = None
        self._after_id = None
        if self._closed or not self.running or self._animating:
            return
        self._dispatch("ui_run_button")

    def _arm_run_timer(self) -> None:
        self._run_after_id = None
        self._after_id = None
        if not self._closed and self.running and not self._animating:
            interval = max(self.display_interval_ms, 50)
            self._run_after_id = self.root.after(interval, self._run_tick)
            self._after_id = self._run_after_id

    def _pause(self) -> None:
        self.running = False
        for attribute in ("_run_after_id", "_after_id", "_animation_after_id"):
            after_id = getattr(self, attribute)
            if after_id is None:
                continue
            try:
                self.root.after_cancel(after_id)
            except tk.TclError:
                pass
            setattr(self, attribute, None)
        if self._animating:
            self._animation_paused = True
        if not self._closed:
            self._update_progress_controls()

    def _on_committed(
        self,
        _state: dict[str, Any],
        _trace: dict[str, Any],
    ) -> None:
        """Latch one recovered frame, then animate only its recorded path."""

        if self._closed:
            return
        self._display_sequence = self._latest_sequence()
        frame = self._frame_for_sequence(self._display_sequence)
        waypoints = recorded_waypoints(frame)
        self._animation_generation += 1
        self._animation_frame = frame
        self._expected_waypoints = deepcopy(waypoints)
        self._scheduled_waypoints = [deepcopy(waypoints[0])]
        self._animation_index = 0
        self._animation_subframe = 0
        self._animation_paused = False
        self._animating = len(waypoints) > 1
        self.redraw(
            frame,
            agent_override=deepcopy(waypoints[0]),
            path_override=deepcopy(waypoints),
        )
        if self._animating:
            self._schedule_animation_subframe()
        else:
            self._animation_complete()

    def _dispatch(self, trigger_source: str, *, world_event: str | None = None) -> bool:
        if self._closed or self._animating or self._is_historical():
            return False
        if world_event is None:
            world_event = default_event_for_sequence(self._latest_sequence() + 1)
        cue = cue_for_event(world_event)
        try:
            result = self.controller.dispatch(
                cue,
                self._intervention_snapshot(),
                trigger_source=trigger_source,
                world_event=world_event,
            )
        except EngineInvariantError as exc:
            self._pause()
            messagebox.showerror("命令被拒绝", str(exc))
            self.status_var.set(f"已暂停且未提交：{exc}")
            return False
        if not result.receipt.committed:
            self._pause()
            messagebox.showerror("原子提交被拒绝", result.receipt.error or "未记录／未知")
            self.status_var.set("未重绘：SQLite 命令与 trace 事务已回滚")
            return False
        return True

    def _inject_event(self) -> None:
        if self.running or self._animating or self._is_historical():
            return
        world_event = _EVENT_DISPLAY_TO_ID.get(self.event_display_var.get())
        if world_event is None:
            self.status_var.set("注入被拒绝：事件未记录／未知")
            return
        self._dispatch("terminal_event", world_event=world_event)

    def _recover(self) -> None:
        self._pause()
        self._cancel_animation(clear=True)
        try:
            self.controller.recover()
        except Exception as exc:
            messagebox.showerror("重新计算失败并关闭", str(exc))
            self.status_var.set(f"重新计算失败并关闭：{exc}")
            return
        self._display_sequence = self._latest_sequence()
        self.redraw()

    def _export(self) -> None:
        default_name = f"{self.controller.run_id}.trace.jsonl"
        selected = filedialog.asksaveasfilename(
            title="导出重新计算的 trace",
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
            messagebox.showerror("导出被拒绝", str(exc))
            self.status_var.set(f"重新计算失败后导出被拒绝：{exc}")
            return
        self.status_var.set("已验证导出；技术路径见高级详情")

    def _load_run(self) -> None:
        if self._closed:
            return
        self._pause()
        selected = simpledialog.askstring("加载运行", "请输入运行 ID：", parent=self.root)
        if not selected:
            return
        try:
            self.controller.load_run(selected.strip())
        except Exception as exc:
            messagebox.showerror("加载被拒绝", str(exc))
            self.status_var.set(f"加载被拒绝：{exc}")
            return
        self._cancel_animation(clear=True)
        self._display_sequence = self._latest_sequence()
        self.redraw()

    def _reset_run(self) -> None:
        if self._closed:
            return
        self._pause()
        try:
            self.controller.reset_run()
        except Exception as exc:
            messagebox.showerror("新建运行被拒绝", str(exc))
            self.status_var.set(f"新建运行被拒绝：{exc}")
            return
        self._cancel_animation(clear=True)
        self._display_sequence = self._latest_sequence()
        self.redraw()

    def _toggle_advanced(self) -> None:
        self._advanced_visible = not self._advanced_visible
        if self._advanced_visible:
            self.advanced_box.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
            self.advanced_button.configure(text="收起详情")
        else:
            self.advanced_box.pack_forget()
            self.advanced_button.configure(text="高级详情")

    def _cancel_animation(self, *, clear: bool) -> None:
        self._animation_generation += 1
        if self._animation_after_id is not None:
            try:
                self.root.after_cancel(self._animation_after_id)
            except tk.TclError:
                pass
            self._animation_after_id = None
        self._animating = False
        self._animation_paused = False
        if clear:
            self._animation_frame = None
            self._expected_waypoints = []
            self._scheduled_waypoints = []
            self._animation_index = 0
            self._animation_subframe = 0

    def _schedule_animation_subframe(self) -> None:
        if self._closed or not self._animating or self._animation_paused:
            return
        if self._animation_segment_ms == 0:
            self._scheduled_waypoints = deepcopy(self._expected_waypoints)
            self._position_agent(self._expected_waypoints[-1])
            self._animation_complete()
            return
        if self._animation_index >= len(self._expected_waypoints) - 1:
            self._animation_complete()
            return
        start = self._expected_waypoints[self._animation_index]
        target = self._expected_waypoints[self._animation_index + 1]
        start_center = self._cell_centers.get(tuple(start))
        target_center = self._cell_centers.get(tuple(target))
        if start_center is None or target_center is None:
            self._pause()
            self.status_var.set("动画失败：记录路径坐标不在公开地图中")
            return
        self._animation_subframe += 1
        fraction = min(1.0, self._animation_subframe / self._animation_subframes)
        center = (
            start_center[0] + (target_center[0] - start_center[0]) * fraction,
            start_center[1] + (target_center[1] - start_center[1]) * fraction,
        )
        self._position_agent_pixels(center)
        if self._animation_subframe >= self._animation_subframes:
            self._scheduled_waypoints.append(deepcopy(target))
            self._animation_index += 1
            self._animation_subframe = 0
            if self._animation_index >= len(self._expected_waypoints) - 1:
                self._animation_complete()
                return
        delay = max(1, self._animation_segment_ms // self._animation_subframes)
        generation = self._animation_generation
        self._animation_after_id = self.root.after(
            delay,
            lambda: self._schedule_animation_subframe()
            if generation == self._animation_generation
            else None,
        )

    def _animation_complete(self) -> None:
        self._animation_after_id = None
        try:
            validate_scheduled_waypoints(
                self._expected_waypoints, self._scheduled_waypoints
            )
        except ValueError as exc:
            self.running = False
            self._animating = False
            self.status_var.set(f"动画调度与记录路径不一致：{exc}")
            self._update_progress_controls()
            return
        self._animating = False
        self._animation_paused = False
        if self._expected_waypoints:
            self._position_agent(self._expected_waypoints[-1])
        if self._animation_frame is not None:
            self._animation_completed_sequence = self._animation_frame.sequence
        self._update_progress_controls()
        if self.running and not self._closed:
            self._arm_run_timer()
        else:
            self.status_var.set(
                f"序列 {self._display_sequence}：已提交、已恢复、路径动画完成；当前已暂停"
            )

    def _draw_map(
        self,
        frame: RecoveryFrame,
        *,
        path: list[list[int]],
        agent_coordinate: list[int],
    ) -> None:
        public_frame = make_public_frame(frame.state)
        layout = public_frame["layout"]
        rows = layout["base_rows"]
        positions = layout["positions"]
        self.map_canvas.delete("all")
        self._cell_centers.clear()
        width = int(layout["width"])
        height = int(layout["height"])
        canvas_width = max(700, self.map_canvas.winfo_width())
        canvas_height = max(410, self.map_canvas.winfo_height())
        gap = 5
        tile = min(
            62,
            max(28, int((canvas_width - 120) / width) - gap),
            max(28, int((canvas_height - 70) / height) - gap),
        )
        total_width = width * tile + (width - 1) * gap
        total_height = height * tile + (height - 1) * gap
        origin_x = (canvas_width - total_width) / 2
        origin_y = (canvas_height - total_height) / 2
        path_set = {tuple(point) for point in path}
        place_labels = {"A": "地点 A", "B": "地点 B", "F": "分岔点", "H": "休息区"}
        for y, row in enumerate(rows):
            for x, glyph in enumerate(row):
                x0 = origin_x + x * (tile + gap)
                y0 = origin_y + y * (tile + gap)
                x1, y1 = x0 + tile, y0 + tile
                center = ((x0 + x1) / 2, (y0 + y1) / 2)
                self._cell_centers[(x, y)] = center
                wall = glyph == "#"
                fill = _VISUAL_COLORS["wall"] if wall else (
                    _VISUAL_COLORS["path"] if (x, y) in path_set else _VISUAL_COLORS["tile"]
                )
                outline = "#101722" if wall else (
                    "#37657a" if (x, y) in path_set else "#26364c"
                )
                self.map_canvas.create_rectangle(
                    x0, y0, x1, y1, fill=fill, outline=outline, width=1
                )
                if glyph in place_labels:
                    self.map_canvas.create_text(
                        center[0],
                        center[1] - 6,
                        text=glyph,
                        fill=_VISUAL_COLORS["text"],
                        font=("Segoe UI", 13, "bold"),
                    )
                    self.map_canvas.create_text(
                        center[0],
                        center[1] + 13,
                        text=place_labels[glyph],
                        fill=_VISUAL_COLORS["muted"],
                        font=_VISUAL_FONT_TINY,
                    )
        for item in public_frame.get("objects", []):
            if not item.get("visible", True):
                continue
            coordinate = positions.get(item.get("position"))
            center = self._cell_centers.get(tuple(coordinate)) if isinstance(
                coordinate, list
            ) else None
            if center is None:
                continue
            self.map_canvas.create_oval(
                center[0] - 11,
                center[1] - 11,
                center[0] + 11,
                center[1] + 11,
                fill="#3e321c",
                outline=_VISUAL_COLORS["amber"],
                width=2,
            )
            self.map_canvas.create_text(
                center[0],
                center[1],
                text="◇",
                fill=_VISUAL_COLORS["amber"],
                font=("Segoe UI Symbol", 12, "bold"),
            )
        for start, target in zip(path, path[1:]):
            p0 = self._cell_centers[tuple(start)]
            p1 = self._cell_centers[tuple(target)]
            self.map_canvas.create_line(
                *p0, *p1, fill="#4a8398", width=3, dash=(6, 5)
            )
        center = self._cell_centers[tuple(agent_coordinate)]
        outer = self.map_canvas.create_oval(
            center[0] - 18,
            center[1] - 18,
            center[0] + 18,
            center[1] + 18,
            fill="#173b48",
            outline=_VISUAL_COLORS["cyan"],
            width=3,
        )
        core = self.map_canvas.create_oval(
            center[0] - 7,
            center[1] - 7,
            center[0] + 7,
            center[1] + 7,
            fill=_VISUAL_COLORS["cyan"],
            outline="",
        )
        direction = self.map_canvas.create_line(
            center[0],
            center[1],
            center[0] + 12,
            center[1],
            fill=_VISUAL_COLORS["text"],
            width=2,
            arrow=tk.LAST,
        )
        self._agent_items = (outer, core, direction)

    def _position_agent(self, coordinate: list[int]) -> None:
        center = self._cell_centers.get(tuple(coordinate))
        if center is not None:
            self._position_agent_pixels(center)

    def _position_agent_pixels(self, center: tuple[float, float]) -> None:
        if self._agent_items is None:
            return
        outer, core, direction = self._agent_items
        self.map_canvas.coords(
            outer, center[0] - 18, center[1] - 18, center[0] + 18, center[1] + 18
        )
        self.map_canvas.coords(
            core, center[0] - 7, center[1] - 7, center[0] + 7, center[1] + 7
        )
        self.map_canvas.coords(
            direction, center[0], center[1], center[0] + 12, center[1]
        )

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
        self._cancel_animation(clear=True)
        self.redraw(self._frame_for_sequence(sequence), rebuild_timeline=False)

    def _on_timeline_scale(self, value: str) -> None:
        if self._timeline_scale_refreshing or self._closed:
            return
        sequence = int(round(float(value)))
        if sequence == self._display_sequence:
            return
        self._pause()
        self._cancel_animation(clear=True)
        self._display_sequence = sequence
        self.redraw(self._frame_for_sequence(sequence), rebuild_timeline=True)

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
                        "初始状态" if trace is None else _zh_label("event", trace["world_event"]),
                        "—" if trace is None else _zh_label("action", trace["selected_action"]),
                    ),
                )
                if frame.sequence == self._display_sequence:
                    selected_iid = iid
            if selected_iid:
                self.timeline_tree.selection_set(selected_iid)
                self.timeline_tree.see(selected_iid)
        finally:
            self._timeline_refreshing = False
        self.timeline_scale.configure(to=self._latest_sequence())
        self._timeline_scale_refreshing = True
        self.timeline_scale_var.set(self._display_sequence)
        self._timeline_scale_refreshing = False

    def _update_progress_controls(self) -> None:
        blocked = self._is_historical()
        if blocked or self.running or self._animating:
            self.step_button.state(["disabled"])
        else:
            self.step_button.state(["!disabled"])
        if blocked or self.running:
            self.run_button.state(["disabled"])
        else:
            self.run_button.state(["!disabled"])
        if self.running or self._animating:
            self.pause_button.state(["!disabled"])
        else:
            self.pause_button.state(["disabled"])
        if blocked or self.running or self._animating:
            self.inject_button.state(["disabled"])
        else:
            self.inject_button.state(["!disabled"])

    def redraw(
        self,
        frame: RecoveryFrame | None = None,
        *,
        rebuild_timeline: bool = True,
        agent_override: list[int] | None = None,
        path_override: list[list[int]] | None = None,
    ) -> None:
        if frame is None:
            frame = self._frame_for_sequence(self._display_sequence)
        if rebuild_timeline:
            self._rebuild_timeline()
        frame_identity = id(frame)
        self._panel_frame_ids = {
            name: frame_identity
            for name in (
                "status",
                "map",
                "goal",
                "memory",
                "candidates",
                "before",
                "event",
                "result",
                "continuity",
                "advanced",
            )
        }
        state = frame.state
        trace = frame.trace
        view = build_chinese_causal_view(frame)
        for key, (bar, value_label) in self.state_widgets.items():
            value = float(state["organism"][key])
            bar["value"] = value * 100
            value_label["text"] = f"{value:.3f}"

        goal = state["current_goal"]
        goal_age = int(state["clock"]["global_tick"]) - int(goal["selected_global_tick"])
        _set_text(
            self.goals_text,
            f"当前目标：{_format_goal(goal)}\n"
            f"目标状态：{'进行中' if goal.get('status') == 'active' else '已完成'}\n"
            f"保持步数：{goal_age}",
        )
        memory_lines = view["步骤发生前"]["读取的记忆及来源"]
        memory_change = view["结果与变化"]["记忆与来源变化"]
        _set_text(
            self.memory_text,
            f"本步读取：{memory_lines}\n本步变化：{memory_change}\n"
            "技术来源 ID 与哈希仅在高级详情中显示。",
        )

        for item in self.candidate_tree.get_children():
            self.candidate_tree.delete(item)
        candidates: list[dict[str, Any]] = [] if trace is None else trace["candidates"]
        selected_action = None if trace is None else trace["selected_action"]
        for candidate in sorted(
            candidates,
            key=lambda item: float("-inf")
            if item["total_score"] is None
            else item["total_score"],
            reverse=True,
        ):
            topology_cost = candidate["topology_cost"]
            shortest_path_steps = candidate["path"]["shortest_path_steps"]
            iid = self.candidate_tree.insert(
                "",
                tk.END,
                values=(
                    _zh_label("action", candidate["action"]),
                    f"{candidate['current_goal_deficit_reduction']:+.4f}",
                    f"{candidate['total_deficit_reduction']:+.4f}",
                    f"{candidate['memory_bias']:+.4f}",
                    f"{candidate['untried_bonus']:+.4f}",
                    f"{candidate['action_cost']:+.4f}",
                    "—" if topology_cost is None else f"{topology_cost:.4f}",
                    "—" if shortest_path_steps is None else str(shortest_path_steps),
                    f"{candidate['deterministic_tie']:.8f}",
                    "—" if candidate["total_score"] is None else f"{candidate['total_score']:+.5f}",
                ),
            )
            if candidate["action"] == selected_action:
                self.candidate_tree.selection_set(iid)

        before = view["步骤发生前"]
        event = view["外部事件"]
        continuity = view["动作连续性"]
        before_text = (
            "【步骤发生前】\n"
            + "\n".join(f"{key}：{value}" for key, value in before.items())
            + "\n\n【外部事件】\n"
            + "\n".join(f"{key}：{value}" for key, value in event.items())
            + "\n\n【动作连续性】\n"
            + "\n".join(f"{key}：{value}" for key, value in continuity.items())
        )
        result = view["结果与变化"]
        choice = view["候选与选择"]
        result_text = (
            "【候选与选择】\n"
            f"选择的行动：{choice['选择的行动']}\n"
            f"胜出依据：{choice['胜出依据']}\n\n"
            "【结果与变化】\n"
            + "\n".join(f"{key}：{value}" for key, value in result.items())
        )
        _set_text(self.model_text, before_text)
        _set_text(self.trace_text, result_text)
        _set_text(
            self.advanced_text,
            json.dumps(
                build_advanced_details(frame, controller=self.controller),
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            ),
        )

        path = deepcopy(path_override) if path_override is not None else recorded_waypoints(frame)
        public_frame = make_public_frame(state)
        if agent_override is None:
            position = public_frame["agent"]["position"]
            agent_coordinate = deepcopy(public_frame["layout"]["positions"][position])
        else:
            agent_coordinate = deepcopy(agent_override)
        self._draw_map(frame, path=path, agent_coordinate=agent_coordinate)

        clock = state["clock"]
        self.sequence_var.set(
            f"序列 {frame.sequence:02d} / {self._latest_sequence():02d} · "
            f"第 {int(clock['episode_index']) + 1} 回合 · 回合内第 {clock['episode_tick']} 步"
        )
        self._update_progress_controls()
        if self._is_historical():
            mode = "历史只读；返回最新序列后才能继续"
        elif self._animating and self._animation_paused:
            mode = "已在记录路径前缀暂停"
        elif self._animating:
            mode = "已提交并恢复；正在播放记录路径"
        elif self.running:
            mode = "连续运行；等待下一次已提交步骤"
        else:
            mode = "已暂停"
        event_label = "初始状态" if trace is None else _zh_label("event", trace.get("world_event"))
        self.status_var.set(
            f"序列 {frame.sequence} · 事件：{event_label} · {mode} · "
            "SQLite 与运行标识见高级详情"
        )

    def close(self) -> None:
        if self._closed:
            return
        self._pause()
        self._cancel_animation(clear=True)
        self._closed = True
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            # An external window-manager teardown may have destroyed Tcl first.
            pass


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


def _read_only_text(parent: ttk.LabelFrame, *, height: int) -> tk.Text:
    widget = tk.Text(
        parent,
        height=height,
        wrap=tk.WORD,
        font=_VISUAL_FONT_SMALL,
        bg="#0a0f17",
        fg="#c7d3e6",
        insertbackground=_VISUAL_COLORS["cyan"],
        selectbackground="#244358",
        relief=tk.FLAT,
        padx=7,
        pady=7,
    )
    widget.pack(fill=tk.BOTH, expand=True)
    widget.configure(state=tk.DISABLED)
    return widget


def _set_text(widget: tk.Text, value: str) -> None:
    widget.configure(state=tk.NORMAL)
    widget.delete("1.0", tk.END)
    widget.insert("1.0", value)
    widget.configure(state=tk.DISABLED)
