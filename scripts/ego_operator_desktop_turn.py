"""Run one EgoOperator desktop chat turn and return JSON for EgoDesktop."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OPENROUTER_KEY_FILE = Path(r"D:\Project\AIProject\MyProject\Test\openrouterKey.txt")


def _read_key_file(path: Path) -> str:
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    for line in raw.splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if text.startswith("OPENROUTER_API_KEY="):
            text = text.split("=", 1)[1].strip()
        return text.strip().strip('"').strip("'")
    return ""


def _load_openrouter_key_before_agent_import() -> None:
    if os.getenv("OPENROUTER_API_KEY"):
        return
    configured = os.getenv("OPENROUTER_API_KEY_FILE", "").strip()
    candidates = [Path(configured)] if configured else []
    candidates.append(DEFAULT_OPENROUTER_KEY_FILE)
    for candidate in candidates:
        key = _read_key_file(candidate)
        if key:
            os.environ["OPENROUTER_API_KEY"] = key
            os.environ.setdefault("OPENROUTER_API_KEY_FILE", str(candidate))
            return


_load_openrouter_key_before_agent_import()

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from EgoOperator.agent_base import build_demo_runtime  # noqa: E402


PSPC_REPLY_PREVIEW_SCHEMA_VERSION = "ego_desktop.pspc_reply_preview_context.v0"
PSPC_REPLY_PREVIEW_CLAIM_CEILING = "local_reply_preview_only"
PSPC_REPLY_PREVIEW_ALLOWED_USE = "ego_desktop_local_reply_preview_only"
PSPC_REPLY_PREVIEW_EXECUTABLE_FIELDS = {
    "action",
    "tool_call",
    "command",
    "user_message",
    "memory_write",
    "gate_decision",
    "approval_id",
    "transport",
    "send",
    "schedule",
    "enable",
    "mainline_authority",
    "proposal_id",
}
PSPC_REPLY_PREVIEW_REQUIRED_FORBIDDEN = {
    "direct_action",
    "direct_user_message",
    "direct_memory_write",
    "runtime_gate_bypass",
    "runtime_registration",
    "proactive_trigger",
    "planner_execution",
    "model_execution",
    "training",
}
PSPC_REPLY_PREVIEW_REQUIRED_NO_AUTHORITY_FALSE = {
    "direct_action_allowed",
    "direct_user_message_allowed",
    "direct_memory_write_allowed",
    "runtime_gate_bypass_allowed",
    "runtime_registration_allowed",
    "proactive_trigger_allowed",
    "planner_execution_allowed",
    "model_execution_allowed",
    "training_allowed",
}
DESKTOP_SESSION_CONTEXT_SCHEMA_VERSION = "ego_desktop.session_context.v0"
DESKTOP_SESSION_CONTEXT_CLAIM_CEILING = "local_session_context_only"
DESKTOP_SESSION_CONTEXT_MAX_MESSAGES = 24
DESKTOP_SESSION_CONTEXT_MAX_CHARS_PER_MESSAGE = 1200
DESKTOP_SESSION_CONTEXT_MAX_TOTAL_CHARS = 12000
DESKTOP_SESSION_REQUIRED_NO_AUTHORITY_FALSE = {
    "real_memory_write_allowed",
    "gate_invocation_allowed",
    "approval_invocation_allowed",
    "transport_call_allowed",
    "proactive_trigger_allowed",
    "runtime_registration_allowed",
}
DESKTOP_SESSION_REQUIRED_SIDE_EFFECTS_FALSE = {
    "real_memory_written",
    "gate_invoked",
    "approval_invoked",
    "transport_called",
    "proactive_triggered",
    "runtime_registered",
}


def _llm_unavailable(runtime: object, reply_text: str) -> bool:
    planner = getattr(runtime, "planner", None)
    llm = getattr(planner, "llm", None)
    if llm is not None and llm.__class__.__name__ == "NoLLM":
        return True
    return str(reply_text or "").lstrip().startswith("LLM 不可用")


def _side_effects_from_result(result: object) -> dict:
    external_result = getattr(result, "external_result", None)
    if not isinstance(external_result, dict):
        return {
            "side_effects_executed": False,
            "memory_write": False,
            "tool_use": False,
            "message_send": False,
            "file_write": False,
            "network_call": False,
        }
    return {
        "side_effects_executed": bool(external_result.get("side_effects_executed")),
        "memory_write": bool(external_result.get("memory_write_executed")),
        "tool_use": bool(external_result.get("tool_use_executed")),
        "message_send": bool(external_result.get("message_send_executed")),
        "file_write": bool(external_result.get("file_write_executed")),
        "network_call": bool(external_result.get("network_call_executed")),
    }


def _contains_executable_field(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in PSPC_REPLY_PREVIEW_EXECUTABLE_FIELDS:
                return True
            if _contains_executable_field(child):
                return True
    elif isinstance(value, list):
        return any(_contains_executable_field(item) for item in value)
    return False


def _object_at(value: Any, field_name: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def validate_pspc_reply_preview_context(context: Any) -> dict:
    safe_context = _object_at(context, "pspc_reply_preview_context")
    if _contains_executable_field(safe_context):
        raise ValueError("pspc_reply_preview_context contains executable field")
    if safe_context.get("schema_version") != PSPC_REPLY_PREVIEW_SCHEMA_VERSION:
        raise ValueError("invalid pspc_reply_preview_context.schema_version")
    if safe_context.get("claim_ceiling") != PSPC_REPLY_PREVIEW_CLAIM_CEILING:
        raise ValueError("invalid pspc_reply_preview_context.claim_ceiling")
    if safe_context.get("allowed_use") != PSPC_REPLY_PREVIEW_ALLOWED_USE:
        raise ValueError("invalid pspc_reply_preview_context.allowed_use")
    if safe_context.get("runtime_authority") != "none":
        raise ValueError("pspc_reply_preview_context.runtime_authority must be none")
    if safe_context.get("enabled") is not False:
        raise ValueError("pspc_reply_preview_context.enabled=false is required")
    if safe_context.get("mainline_connected") is not False:
        raise ValueError("pspc_reply_preview_context.mainline_connected=false is required")
    profile = _object_at(safe_context.get("profile"), "pspc_reply_preview_context.profile")
    if str(profile.get("style") or "") not in {
        "warm_approach",
        "cautious_boundary",
        "low_interrupt_care",
        "mixed_low_confidence",
    }:
        raise ValueError("invalid pspc_reply_preview_context.profile.style")
    confidence = float(profile.get("confidence", 0))
    if confidence < 0 or confidence > 1:
        raise ValueError("pspc_reply_preview_context.profile.confidence must be between 0 and 1")
    forbidden = _object_at(safe_context.get("forbidden"), "pspc_reply_preview_context.forbidden")
    for flag in sorted(PSPC_REPLY_PREVIEW_REQUIRED_FORBIDDEN):
        if forbidden.get(flag) is not True:
            raise ValueError(f"pspc_reply_preview_context.forbidden.{flag}=true is required")
    no_authority = _object_at(safe_context.get("no_authority"), "pspc_reply_preview_context.no_authority")
    for flag in sorted(PSPC_REPLY_PREVIEW_REQUIRED_NO_AUTHORITY_FALSE):
        if no_authority.get(flag) is not False:
            raise ValueError(f"pspc_reply_preview_context.no_authority.{flag}=false is required")
    for field in ("real_memory_written", "runtime_gate_invoked", "proactive_triggered"):
        if safe_context.get(field) is not False:
            raise ValueError(f"pspc_reply_preview_context.{field}=false is required")
    return safe_context


def extract_pspc_reply_preview_context(payload: dict) -> dict | None:
    if not isinstance(payload, dict) or payload.get("pspc_reply_preview_mode") is not True:
        return None
    return validate_pspc_reply_preview_context(payload.get("pspc_reply_preview_context"))


def render_pspc_reply_preview_system_context(context: dict) -> str:
    profile = _object_at(context.get("profile"), "pspc_reply_preview_context.profile")
    style = str(profile.get("style") or "mixed_low_confidence")
    confidence = float(profile.get("confidence", 0))
    basis = str(profile.get("basis") or "")
    refs = profile.get("reason_trace_refs")
    refs_text = ", ".join(str(item) for item in refs) if isinstance(refs, list) else ""
    style_guidance = {
        "warm_approach": "Use a warmer, slightly closer, softer reply style.",
        "cautious_boundary": "Use a slower, boundary-respecting, less pushy reply style.",
        "low_interrupt_care": "Use a quiet, low-interrupt care style with gentle practical concern.",
        "mixed_low_confidence": "Use a hesitant, preference-checking style and avoid strong assumptions.",
    }.get(style, "Use a cautious low-confidence style and avoid strong assumptions.")
    return "\n".join([
        "PSPC local reply preview context.",
        "This is a local style hint only for this EgoDesktop turn.",
        f"style: {style}",
        f"confidence: {confidence:.4f}",
        f"basis: {basis}",
        f"reason_trace_refs: {refs_text}",
        f"style_guidance: {style_guidance}",
        "Do not claim consciousness, subjective experience, real emotion, durable memory, or live autonomy.",
        "Do not write memory, execute tools, invoke gates, request approval, use transport, or trigger proactive behavior.",
        "Do not mention PSPC or this debug context unless the user explicitly asks.",
    ])


def validate_desktop_session_context(context: Any) -> dict:
    safe_context = _object_at(context, "desktop_session_context")
    if _contains_executable_field(safe_context):
        raise ValueError("desktop_session_context contains executable field")
    if safe_context.get("schema_version") != DESKTOP_SESSION_CONTEXT_SCHEMA_VERSION:
        raise ValueError("invalid desktop_session_context.schema_version")
    if safe_context.get("source") != "ego_desktop_main_process_session_local":
        raise ValueError("invalid desktop_session_context.source")
    if safe_context.get("claim_ceiling") != DESKTOP_SESSION_CONTEXT_CLAIM_CEILING:
        raise ValueError("invalid desktop_session_context.claim_ceiling")
    if safe_context.get("persistence") != "window_lifetime_only":
        raise ValueError("desktop_session_context.persistence must be window_lifetime_only")
    if safe_context.get("runtime_authority") != "none":
        raise ValueError("desktop_session_context.runtime_authority must be none")
    if safe_context.get("enabled") is not False:
        raise ValueError("desktop_session_context.enabled=false is required")
    if safe_context.get("mainline_connected") is not False:
        raise ValueError("desktop_session_context.mainline_connected=false is required")

    messages = safe_context.get("messages")
    if not isinstance(messages, list):
        raise ValueError("desktop_session_context.messages must be a list")
    if len(messages) > DESKTOP_SESSION_CONTEXT_MAX_MESSAGES:
        raise ValueError("desktop_session_context.messages exceeds max count")
    total_chars = 0
    safe_messages = []
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError(f"desktop_session_context.messages[{index}] must be an object")
        role = str(message.get("role") or "")
        if role not in {"user", "assistant"}:
            raise ValueError("desktop_session_context messages only allow user/assistant roles")
        content = str(message.get("content") or "").strip()
        if len(content) > DESKTOP_SESSION_CONTEXT_MAX_CHARS_PER_MESSAGE:
            raise ValueError("desktop_session_context message exceeds max chars")
        total_chars += len(content)
        if total_chars > DESKTOP_SESSION_CONTEXT_MAX_TOTAL_CHARS:
            raise ValueError("desktop_session_context total chars exceeds max")
        turn_index = int(message.get("turn_index") or 0)
        if turn_index < 0:
            raise ValueError("desktop_session_context.turn_index must be non-negative")
        safe_messages.append({
            "role": role,
            "content": content,
            "turn_index": turn_index,
        })

    no_authority = _object_at(safe_context.get("no_authority"), "desktop_session_context.no_authority")
    for flag in sorted(DESKTOP_SESSION_REQUIRED_NO_AUTHORITY_FALSE):
        if no_authority.get(flag) is not False:
            raise ValueError(f"desktop_session_context.no_authority.{flag}=false is required")
    side_effects = _object_at(safe_context.get("side_effects_absent"), "desktop_session_context.side_effects_absent")
    for flag in sorted(DESKTOP_SESSION_REQUIRED_SIDE_EFFECTS_FALSE):
        if side_effects.get(flag) is not False:
            raise ValueError(f"desktop_session_context.side_effects_absent.{flag}=false is required")

    return {
        **safe_context,
        "messages": safe_messages,
    }


def extract_desktop_session_context(payload: dict) -> dict | None:
    if not isinstance(payload, dict) or "desktop_session_context" not in payload:
        return None
    return validate_desktop_session_context(payload.get("desktop_session_context"))


def inject_desktop_session_context(runtime: object, context: dict | None) -> None:
    if context is None:
        return
    memory = getattr(runtime, "memory", None)
    if memory is None or not hasattr(memory, "add"):
        raise ValueError("runtime.memory.add is required for desktop_session_context")
    for message in context.get("messages", []):
        memory.add(str(message["role"]), str(message["content"]))


def main() -> int:
    try:
        payload = json.loads((sys.stdin.read() or "{}").lstrip("\ufeff"))
        user_text = str(payload.get("user_text") or "").strip()
        if not user_text:
            print(json.dumps({"status": "input_error", "reason": "empty_user_text"}, ensure_ascii=False))
            return 2
        try:
            desktop_session_context = extract_desktop_session_context(payload)
            pspc_reply_preview_context = extract_pspc_reply_preview_context(payload)
        except ValueError as exc:
            print(json.dumps({
                "status": "input_error",
                "reason": "invalid_desktop_turn_context",
                "error": str(exc),
                "side_effects_executed": False,
                "memory_write": False,
                "tool_use": False,
                "message_send": False,
                "file_write": False,
                "network_call": False,
                "desktop_session_context_applied": False,
                "pspc_reply_preview_applied": False,
            }, ensure_ascii=False))
            return 2

        runtime = build_demo_runtime(enable_operator_memory=False)
        inject_desktop_session_context(runtime, desktop_session_context)
        if pspc_reply_preview_context is not None:
            runtime.memory.add("system", render_pspc_reply_preview_system_context(pspc_reply_preview_context))
        result = runtime.handle_user_message(user_text)
        pending = runtime.list_pending_approvals()
        reply_text = str(getattr(result, "reply_text", "") or "")
        unavailable = _llm_unavailable(runtime, reply_text)
        response = {
            "status": "llm_expression_unavailable" if unavailable else "ok",
            "reason": "provider_not_configured" if unavailable else "",
            "reply_text": reply_text,
            "event_id": str(getattr(result, "event_id", "") or ""),
            "pending_approvals": int(pending.get("pending_count") or 0) if isinstance(pending, dict) else 0,
            "operator_memory_enabled": False,
            "desktop_session_context_applied": desktop_session_context is not None,
            "desktop_session_context_message_count": (
                len(desktop_session_context.get("messages", []))
                if desktop_session_context is not None
                else 0
            ),
            "desktop_session_context_claim_ceiling": (
                str(desktop_session_context.get("claim_ceiling") or "")
                if desktop_session_context is not None
                else ""
            ),
            "pspc_reply_preview_applied": pspc_reply_preview_context is not None,
            "pspc_reply_preview_style": (
                str(pspc_reply_preview_context.get("profile", {}).get("style") or "")
                if pspc_reply_preview_context is not None
                else ""
            ),
            "pspc_reply_preview_claim_ceiling": (
                str(pspc_reply_preview_context.get("claim_ceiling") or "")
                if pspc_reply_preview_context is not None
                else ""
            ),
            **_side_effects_from_result(result),
        }
        print(json.dumps(response, ensure_ascii=False))
        return 0
    except Exception as exc:  # pragma: no cover - exercised by Electron smoke/error paths.
        print(json.dumps({
            "status": "llm_expression_unavailable",
            "reason": exc.__class__.__name__,
            "error": str(exc),
            "side_effects_executed": False,
            "memory_write": False,
            "tool_use": False,
            "message_send": False,
        }, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
