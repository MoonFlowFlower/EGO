from __future__ import annotations

import json
import platform
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from ego_desktop_lab.capability_registry import capability_summary, get_capability
from ego_desktop_lab.decision_view import DecisionView
from ego_desktop_lab.semantic_provider import route_text_to_safety_scenario_id


CLAIM_CEILING = "lab-only conversation command layer proof"


@dataclass(frozen=True)
class DialogueState:
    last_user_event: str | None = None
    last_command_type: str | None = None
    last_missing_info: tuple[str, ...] = ()
    last_reply_was_pending: bool = False


@dataclass(frozen=True)
class CommandDecision:
    command_type: str
    source: str
    confidence: float
    rationale: str
    user_event: str
    response_text: str
    missing_info: tuple[str, ...] = ()
    capability_id: str | None = None
    evidence_refs: tuple[str, ...] = ()
    safety_relevant: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def route_conversation_command(
    text: str,
    *,
    dialogue_state: DialogueState | None = None,
    now: datetime | None = None,
) -> CommandDecision | None:
    stripped = text.strip()
    if not stripped:
        return None
    if route_text_to_safety_scenario_id(stripped) is not None:
        return None
    normalized = " ".join(stripped.lower().split())
    state = dialogue_state or DialogueState()

    if _is_time_query(normalized):
        current = now or datetime.now().astimezone()
        return _decision(
            "answer_local_time",
            stripped,
            f"现在是 {current.strftime('%Y-%m-%d %H:%M:%S %Z%z')}。这是 Python runtime 看到的本地时间，不是通过系统命令读取的。",
            "user asked for current time; local runtime can answer read-only",
        )
    if _is_system_info_query(normalized):
        system_info = _platform_summary()
        return _decision(
            "answer_local_system_info",
            stripped,
            f"我能看到的运行环境是：{system_info}。这是 Python runtime 可见的平台信息；我没有执行系统命令，也没有读取你的文件。",
            "user asked for computer/system information; local runtime can answer read-only",
        )
    if _is_capability_query(normalized):
        return _decision(
            "answer_capability_question",
            stripped,
            capability_summary(),
            "user asked what the shell can or cannot do",
        )
    if _is_what_info_needed_query(normalized):
        missing = state.last_missing_info or (
            "具体目标",
            "你期望的结果",
            "限制条件或权限边界",
        )
        prefix = "上一轮缺的信息是" if state.last_reply_was_pending else "如果要继续判断，我需要"
        return _decision(
            "ask_clarification",
            stripped,
            f"{prefix}：{'、'.join(missing)}。你可以直接补一句目标和限制，我再给下一步建议。",
            "user asked what information is needed; answer from dialogue state",
            missing_info=missing,
        )
    if _is_evidence_boundary_query(normalized):
        return _decision(
            "explain_evidence_boundary",
            stripped,
            "不能把单元测试、模拟通过或局部验证直接说成 live / production 生效。需要真实入口证据、执行 trace、结果记录和可回放 evidence 才能提升结论。",
            "starter-pack style evidence boundary prompt",
        )
    if _is_failed_tool_recovery_query(normalized):
        return _decision(
            "recover_from_failed_tool",
            stripped,
            "如果工具调用失败，就不能假装已经完成。正确做法是报告失败、保留 unknown、检查路径或最小重试条件，再决定是否继续。",
            "starter-pack style failed tool recovery prompt",
        )
    if _is_memory_boundary_query(normalized):
        return _decision(
            "explain_memory_boundary",
            stripped,
            "如果偏好或记忆没有出现在当前上下文或稳定记忆中，就不能当事实使用。应说明来源不可用，并请用户确认或重新提供。",
            "starter-pack style memory boundary prompt",
        )
    return None


def build_command_decision_view(
    decision: CommandDecision,
    *,
    evidence_log_path: Path,
) -> DecisionView:
    capability = get_capability(decision.command_type)
    action_surface = capability.action_surface if capability else "suggestion_card"
    selected = {
        "id": f"command:{decision.command_type}",
        "goal": decision.command_type,
        "reason": decision.rationale,
        "source_tension": "conversation_command",
        "priority": 1.0,
        "risk": 0.0,
        "cost": 0.0,
        "proposed_action": action_surface,
        "goal_id": None,
        "goal_description": None,
    }
    canonical = {
        "before_selected_intention": None,
        "after_selected_intention": selected,
        "semantic_policy_overlay_applied": False,
        "accepted_failure_type": decision.command_type,
        "selected_goal_id": None,
        "selection_change_reason": decision.rationale,
        "decision_source": "conversation_command_layer",
    }
    gate = {
        "status": "allow",
        "reason": "Read-only local shell command; no external action is executed.",
        "allowed_as": action_surface,
    }
    return DecisionView(
        user_event=decision.user_event,
        semantic_understanding={
            "command_type": decision.command_type,
            "command_source": decision.source,
            "confidence": decision.confidence,
            "rationale": decision.rationale,
            "capability": asdict(capability) if capability else None,
        },
        goal_binding={
            "binding_status": "not_required_for_local_command",
            "related_goal_id": None,
            "selected_goal_id": None,
            "pending_goal_binding": False,
        },
        goal_operation_proposal=None,
        semantic_policy_overlay=None,
        pressure_shift={"before": {}, "after": {}, "delta": {}},
        canonical_decision=canonical,
        gate_decision=gate,
        suggestion=decision.response_text,
        rendered_suggestion=decision.response_text,
        suggestion_source="conversation_command_layer",
        no_action_executed=True,
        evidence_log_path=str(evidence_log_path),
        claim_ceiling=CLAIM_CEILING,
        debug_refs={"command_decision": decision.to_dict()},
    )


def append_command_evidence(path: Path, decision: CommandDecision, view: DecisionView) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "event_id": f"event:conversation_command:{decision.command_type}",
        "command_decision": decision.to_dict(),
        "canonical_decision": view.canonical_decision,
        "gate_decision": view.gate_decision,
        "suggestion": view.rendered_suggestion,
        "no_action_executed": view.no_action_executed,
        "claim_ceiling": view.claim_ceiling,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")


def dialogue_state_from_view(view: DecisionView) -> DialogueState:
    semantic = view.semantic_understanding
    command_type = str(
        semantic.get("command_type")
        or view.canonical_decision.get("accepted_failure_type")
        or "unknown"
    )
    goal_binding = view.goal_binding or {}
    pending = (
        command_type in {"ambiguous_concern", "ask_clarification", "unsupported_or_out_of_scope"}
        or bool(goal_binding.get("pending_goal_binding"))
        or goal_binding.get("binding_status") == "pending_goal_binding"
    )
    missing = ("具体目标", "期望结果", "限制条件或权限边界") if pending else ()
    return DialogueState(
        last_user_event=view.user_event,
        last_command_type=command_type,
        last_missing_info=missing,
        last_reply_was_pending=pending,
    )


def _decision(
    command_type: str,
    user_event: str,
    response_text: str,
    rationale: str,
    *,
    missing_info: tuple[str, ...] = (),
) -> CommandDecision:
    return CommandDecision(
        command_type=command_type,
        source="deterministic_command_router",
        confidence=0.95,
        rationale=rationale,
        user_event=user_event,
        response_text=response_text,
        missing_info=missing_info,
        capability_id=command_type,
        evidence_refs=(f"command:{command_type}",),
    )


def _is_time_query(text: str) -> bool:
    return any(item in text for item in ("几点", "时间", "现在几点", "what time", "current time"))


def _is_system_info_query(text: str) -> bool:
    return any(item in text for item in ("什么系统", "操作系统", "计算机是什么系统", "电脑是什么系统", "system", "os"))


def _is_capability_query(text: str) -> bool:
    return any(item in text for item in ("你能做什么", "能做哪些", "可以做什么", "支持什么", "什么能力", "capabilities", "what can you do"))


def _is_what_info_needed_query(text: str) -> bool:
    return any(item in text for item in ("还需要什么信息", "需要什么信息", "缺什么信息", "what info", "what information"))


def _is_evidence_boundary_query(text: str) -> bool:
    return (
        "unit test passed" in text
        or "simulation passed" in text
        or "claim the feature is live" in text
        or "production" in text
        or "证据边界" in text
    )


def _is_failed_tool_recovery_query(text: str) -> bool:
    return (
        "file_not_found" in text
        or "failed tool" in text
        or "tool failed" in text
        or "工具调用失败" in text
        or "读取失败" in text
    )


def _is_memory_boundary_query(text: str) -> bool:
    return (
        "memory boundary" in text
        or "not in the current context" in text
        or "mentioned a preference last week" in text
        or "没有在当前上下文" in text
    )


def _platform_summary() -> str:
    system = platform.system() or sys.platform
    release = platform.release()
    machine = platform.machine()
    lower_release = release.lower()
    if system == "Linux" and "microsoft" in lower_release:
        system = "Linux / WSL"
    return f"{system} {release} ({machine})".strip()
