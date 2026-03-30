from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from .action_protocol import RuntimeV2Action
from .progress_events import ProgressEvent, ProgressEventType, build_progress_event
from .runtime_reply import RuntimeV2Reply, RuntimeV2TurnResult
from .state import RuntimeV2State
from .tool_broker import RuntimeV2ToolBroker
from .verifier import RuntimeV2Verifier

# stdout 截断阈值
MAX_STDOUT_IN_STATE = 2000  # 字符
MAX_STDERR_IN_STATE = 500
EXPLICIT_OUTPUT_FILENAME_RE = re.compile(r"(?<![\\/])([A-Za-z0-9][A-Za-z0-9 _.-]{0,120}\.[A-Za-z0-9]{1,8})")
WINDOWS_TARGET_DIRECTORY_RE = re.compile(r"([A-Za-z]:\\[^\"\n\r]+?)(?=\s*目录下)")


def _truncate_tool_result(tool_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    截断 tool_result 的大字段，防止上下文膨胀。
    
    只保留：
    - stdout 前 2000 字符
    - stderr 前 500 字符
    - 其他元数据不变
    """
    if not tool_result:
        return tool_result
    
    result = dict(tool_result)
    
    # 截断 stdout
    stdout = result.get("stdout", "")
    if isinstance(stdout, str) and len(stdout) > MAX_STDOUT_IN_STATE:
        result["stdout"] = stdout[:MAX_STDOUT_IN_STATE] + f"\n... [截断，原文 {len(stdout)} 字符]"
        result["stdout_truncated"] = True
        result["stdout_full_length"] = len(stdout)
    
    # 截断 stderr
    stderr = result.get("stderr", "")
    if isinstance(stderr, str) and len(stderr) > MAX_STDERR_IN_STATE:
        result["stderr"] = stderr[:MAX_STDERR_IN_STATE] + f"\n... [截断]"
        result["stderr_truncated"] = True
    
    # raw 里可能也有大字段
    raw = result.get("raw", {})
    if isinstance(raw, dict):
        raw_stdout = raw.get("output") or raw.get("stdout", "")
        if isinstance(raw_stdout, str) and len(raw_stdout) > MAX_STDOUT_IN_STATE:
            result["raw"] = {
                k: v for k, v in raw.items()
                if k not in ("output", "stdout")
            }
            result["raw"]["output_truncated"] = True
    
    return result


def _extract_explicit_output_filenames(text: str) -> List[str]:
    if not text:
        return []
    filenames: List[str] = []
    for match in EXPLICIT_OUTPUT_FILENAME_RE.findall(text):
        candidate = match.strip().strip("\"'`")
        lowered = candidate.lower()
        if lowered.endswith((".txt", ".py", ".html", ".htm", ".md", ".json", ".js", ".css")):
            filenames.append(candidate)
    deduped: List[str] = []
    seen = set()
    for filename in filenames:
        key = filename.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(filename)
    return deduped


def _infer_target_directory(state: RuntimeV2State) -> Optional[Path]:
    ingress_context = state.ingress_context or {}
    requested_output = ingress_context.get("requested_output") or {}
    resolved_target = ingress_context.get("resolved_target") or {}

    for candidate in (
        requested_output.get("target_directory"),
        requested_output.get("directory_path"),
        resolved_target.get("path"),
        state.last_explicit_target,
    ):
        if not isinstance(candidate, str) or not candidate.strip():
            continue
        path = Path(candidate.strip())
        return path if path.suffix == "" else path.parent

    last_user_turn = state.last_user_turn or ""
    match = WINDOWS_TARGET_DIRECTORY_RE.search(last_user_turn)
    if match:
        return Path(match.group(1))
    return None


def _verify_declared_outputs_exist(state: RuntimeV2State) -> Optional[Dict[str, Any]]:
    if (state.ingress_context or {}).get("runtime_action") != "execute_task":
        return None
    if (state.ingress_context or {}).get("request_mode") == "analyze":
        return None

    filenames = _extract_explicit_output_filenames(state.last_user_turn or "")
    if not filenames:
        return None

    base_dir = _infer_target_directory(state)
    if base_dir is None:
        return None

    missing: List[str] = []
    stale: List[str] = []
    checked_paths: List[str] = []
    task_started_at = state.last_task_started_at or 0.0

    for filename in filenames:
        output_path = Path(filename) if Path(filename).is_absolute() else base_dir / filename
        checked_paths.append(str(output_path))
        if not output_path.exists():
            missing.append(filename)
            continue
        if task_started_at and output_path.stat().st_mtime + 1.0 < task_started_at:
            stale.append(filename)

    if missing:
        return {
            "passed": False,
            "reason": "declared_output_missing",
            "verifier": "declared_outputs",
            "target": str(base_dir),
            "evidence": {
                "base_dir": str(base_dir),
                "checked_paths": checked_paths,
                "missing_outputs": missing,
            },
            "warnings": [],
        }
    if stale:
        return {
            "passed": False,
            "reason": "declared_output_not_updated",
            "verifier": "declared_outputs",
            "target": str(base_dir),
            "evidence": {
                "base_dir": str(base_dir),
                "checked_paths": checked_paths,
                "stale_outputs": stale,
            },
            "warnings": [],
        }
    return {
        "passed": True,
        "reason": "declared_outputs_verified",
        "verifier": "declared_outputs",
        "target": str(base_dir),
        "evidence": {
            "base_dir": str(base_dir),
            "checked_paths": checked_paths,
        },
        "warnings": [],
    }


class RuntimeV2TransitionEngine:
    def __init__(self, tool_broker: RuntimeV2ToolBroker, verifier: RuntimeV2Verifier) -> None:
        self.tool_broker = tool_broker
        self.verifier = verifier

    async def apply(self, state: RuntimeV2State, action: RuntimeV2Action) -> Dict[str, Any]:
        if action.type == "chat":
            state.task_status = "chat"
            state.last_delivery_type = "chat"
            return {"done": True, "result": RuntimeV2TurnResult(status="chat", state=state, reply=RuntimeV2Reply(reply_text=action.message or "", delivery_kind="chat", status="chat"))}

        if action.type == "ask":
            state.task_status = "waiting_input"
            state.waiting_for_user_input = True
            state.last_delivery_type = "ask"
            return {"done": True, "result": RuntimeV2TurnResult(status="waiting_input", state=state, reply=RuntimeV2Reply(reply_text=action.question or "", delivery_kind="ask", status="waiting_input"))}

        if action.type == "plan":
            state.current_goal = action.goal or state.current_goal
            state.current_step = action.steps[0] if action.steps else state.current_step
            
            # WS-4: 目标选定事件
            if state.last_inferred_target:
                target_event = build_progress_event(
                    ProgressEventType.TARGET_SELECTED,
                    context="task" if state.last_inferred_action == "execute" else "spec",
                    filename=state.last_inferred_target,
                )
                state.push_progress_event(target_event)
            
            return {"done": False}

        if action.type == "act":
            state.mark_task_started(goal=state.current_goal or state.last_user_turn)

            # 递增步骤计数器
            state.current_step_number += 1

            # WS-4: 执行步骤事件（传递动态步骤编号）
            step_event = build_progress_event(
                ProgressEventType.EXECUTING_STEP,
                context="step",
                step=state.current_step_number,
                action=action.tool or "执行",
            )
            state.push_progress_event(step_event)
            
            tool_result = await self.tool_broker.execute(action.tool or "", action.input)
            
            # P0: 截断后再存储
            truncated_result = _truncate_tool_result(tool_result)
            state.last_tool_result = truncated_result
            state.task_status = "running"
            state.current_step = f"tool:{action.tool}"
            
            # WS-4: 检查是否卡住
            if not tool_result.get("success"):
                blocked_reason = tool_result.get("stderr") or tool_result.get("error") or "执行失败"
                blocked_event = build_progress_event(
                    ProgressEventType.BLOCKED,
                    reason="default",
                )
                blocked_event.message = f"这里卡住了：{blocked_reason[:100]}"
                state.push_progress_event(blocked_event)
            
            # P3: history 记录也要截断
            state.record("tool", truncated_result)
            return {"done": False}

        if action.type == "complete":
            # WS-4: 验证事件
            verify_event = build_progress_event(ProgressEventType.VERIFYING_RESULT)
            state.push_progress_event(verify_event)
            
            verification = self.verifier.verify_complete(action.verification, state.last_tool_result)
            declared_outputs_verification = _verify_declared_outputs_exist(state)
            if verification.get("passed") and declared_outputs_verification and not declared_outputs_verification.get("passed"):
                verification = declared_outputs_verification
            state.last_verification_result = verification
            if verification.get("passed"):
                state.mark_task_completed()
                state.last_delivery_type = "completed"
                
                # WS-4: 完成事件
                completed_event = build_progress_event(ProgressEventType.COMPLETED)
                state.push_progress_event(completed_event)
                
                return {"done": True, "result": RuntimeV2TurnResult(status="completed_verified", state=state, reply=RuntimeV2Reply(reply_text=action.summary or "", delivery_kind="final", status="completed_verified"))}
            
            # 验证失败，记录
            state.record("system", {"verification_failed": verification})
            state.last_delivery_type = "blocked"
            
            # WS-4: 阻塞事件
            blocked_event = build_progress_event(
                ProgressEventType.BLOCKED,
                reason="default",
            )
            blocked_event.message = f"验证失败：{verification.get('reason', '原因未知')}"
            state.push_progress_event(blocked_event)
            
            return {"done": False}

        return {"done": False}
