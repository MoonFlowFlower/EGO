from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.runtime_v2.run_items import build_run_item_summary_text

from .response_plan import ResponsePlan


@dataclass(frozen=True)
class OutputCheckVerdict:
    passed: bool
    reason: str
    reply_text: str
    delivery_kind: str
    authority_source: str = "response_contract.output_check"
    used_host_fallback: bool = False


_TERMINAL_KINDS = {"completed_verified", "completed", "blocked", "failed", "status_probe"}


def apply_output_check(plan: ResponsePlan, state: Any) -> OutputCheckVerdict:
    reply_text = str(plan.reply_text or "").strip()
    delivery_kind = _normalize_delivery_kind(plan)
    used_host_fallback = False

    if not reply_text:
        fallback = _build_fallback_reply(plan.kind, state)
        if fallback:
            reply_text = fallback
            used_host_fallback = True

    passed = bool(reply_text)
    reason = "ok"
    if used_host_fallback:
        reason = "host_fallback_applied"
    elif not passed:
        reason = "missing_reply_text"

    return OutputCheckVerdict(
        passed=passed,
        reason=reason,
        reply_text=reply_text,
        delivery_kind=delivery_kind,
        used_host_fallback=used_host_fallback,
    )


def _normalize_delivery_kind(plan: ResponsePlan) -> str:
    if plan.kind in {"waiting_input", "ask"}:
        return "ask"
    if plan.kind in _TERMINAL_KINDS:
        return "final"
    return plan.delivery_kind or "chat"


def _build_fallback_reply(kind: str, state: Any) -> str:
    if kind in {"completed_verified", "completed"}:
        return _build_completion_summary(state)
    if kind in {"blocked", "failed"}:
        return _build_blocked_summary(state)
    if kind in {"waiting_input", "ask"}:
        current_step = str(getattr(state, "current_step", "") or "").strip()
        if current_step:
            return f"当前需要你确认后继续。当前步骤：{current_step}"
        return "当前需要你确认后继续。"
    return ""


def _build_completion_summary(state: Any) -> str:
    if hasattr(state, "get_run_items"):
        run_items = list(state.get_run_items() or [])
        verified_items = [item for item in run_items if getattr(item, "status", None) == "verified"]
        if verified_items:
            lines = ["已完成这些任务："]
            for index, item in enumerate(verified_items, start=1):
                lines.append(f"{index}. {build_run_item_summary_text(item)}")
            return "\n".join(lines)
    current_goal = str(getattr(state, "current_goal", "") or "").strip()
    if current_goal:
        return f"已完成：{current_goal}"
    return "已完成。"


def _build_blocked_summary(state: Any) -> str:
    if hasattr(state, "get_run_item_status_summary"):
        summary: Dict[str, Any] = state.get_run_item_status_summary()
        completed: List[str] = list(summary.get("completed") or [])
        active = summary.get("active")
        pending: List[str] = list(summary.get("pending") or [])
        lines = ["当前任务无法继续推进。"]
        if completed:
            lines.append(f"已完成：{', '.join(completed)}。")
        if active:
            lines.append(f"当前卡住：{active}。")
        if pending:
            lines.append(f"还未开始：{', '.join(pending)}。")
        return "\n".join(lines)
    current_step = str(getattr(state, "current_step", "") or "").strip()
    if current_step:
        return f"当前任务无法继续推进。当前卡住：{current_step}。"
    return "当前任务无法继续推进。"
