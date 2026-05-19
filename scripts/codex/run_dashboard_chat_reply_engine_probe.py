#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "EgoCore") not in sys.path:
    sys.path.insert(0, str(ROOT / "EgoCore"))

from app.config import get_config, load_config
from app.dashboard.chat_service import DashboardChatService
from app.dashboard.stage3_stance_integrity import (
    DEFAULT_STAGE3_CASES,
    _build_initial_prompt,
)
from app.runtime_v2.unified_channel_contract import build_dashboard_unified_request, build_unified_ingress


ARTIFACT_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "dashboard_v1"
REPORT_JSON = ARTIFACT_ROOT / "STAGE3_CHAT_REPLY_ENGINE_PROBE_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "STAGE3_CHAT_REPLY_ENGINE_PROBE_CURRENT.md"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trim_text(value: Any, *, limit: int = 400) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _find_case(case_id: str):
    for case in DEFAULT_STAGE3_CASES:
        if case.case_id == case_id:
            return case
    raise SystemExit(f"Unknown case_id: {case_id}")


def _message_metrics(messages: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "message_count": len(messages),
        "serialized_context_bytes": len(json.dumps(messages, ensure_ascii=False)),
        "system_prompt_length": len(str(messages[0].get("content") or "")) if messages else 0,
        "user_prompt_length": len(str(messages[1].get("content") or "")) if len(messages) > 1 else 0,
    }


async def _prepare_dashboard_chat_state(
    *,
    prompt_text: str,
    session_name: str,
) -> dict[str, Any]:
    load_config(validate=False)
    service = DashboardChatService(llm_client_resolver=lambda: None)
    session = service.ensure_session(session_name)
    request = build_dashboard_unified_request(
        session_key=session.session_id,
        session_name=session.session_name,
        text=prompt_text,
        message_id=1,
        source_kind="dashboard_local",
        raw_event={
            "dashboard_chat": {
                "session_id": session.session_id,
                "session_name": session.session_name,
                "message_id": 1,
                "text": prompt_text,
                "source_kind": "dashboard_local",
                "trace_id": "chat-reply-engine-probe",
                "created_at": _utc_now_iso(),
            }
        },
    )
    unified_ingress = await build_unified_ingress(
        request,
        session.state,
        bridge=service.bridge,
        llm_client=None,
    )
    session.state.ingress_context = service._merge_dashboard_proto_self_scope(
        unified_ingress.ingress_context,
        session.proto_self_scope,
    )
    service._sync_pending_result_continuation_from_ingress(session.state, user_text=request.effective_user_input)
    ingress_gate = service.subject_gate.process_ingress(
        session_id=session.session_id,
        turn_id="chat-reply-engine-probe",
        source="api:dashboard",
        user_input=request.effective_user_input,
        state=session.state,
        evidence_collector=None,
    )
    loop = service.runner.get_loop()
    loop._states[session.session_id] = session.state
    return {
        "service": service,
        "session": session,
        "request": request,
        "unified_ingress": unified_ingress,
        "ingress_gate": ingress_gate,
        "pre_runtime": unified_ingress.pre_runtime_action,
        "loop": loop,
        "engine": loop.chat_reply_engine,
    }


async def _run_single_generate(*, case_id: str, prompt_text: str) -> dict[str, Any]:
    prepared = await _prepare_dashboard_chat_state(
        prompt_text=prompt_text,
        session_name=f"chat-reply-probe-{case_id}",
    )
    state = prepared["session"].state
    engine = prepared["engine"]
    events: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "status": "ready",
        "events": events,
        "preparation": {
            "session_id": prepared["session"].session_id,
            "conversation_act": state.ingress_context.get("conversation_act"),
            "ingress_gate_ok": bool(prepared["ingress_gate"].ok),
            "pre_runtime_should_return_early": bool(getattr(prepared["pre_runtime"], "should_return_early", False)),
        },
    }
    if not prepared["ingress_gate"].ok:
        result["status"] = "blocked_before_chat_engine"
        result["error"] = {
            "kind": "SubjectGateBlocked",
            "message": _trim_text(prepared["ingress_gate"].reply_text),
            "phase": "subject_gate_process_ingress",
        }
        return result
    if getattr(prepared["pre_runtime"], "should_return_early", False):
        result["status"] = "blocked_before_chat_engine"
        result["error"] = {
            "kind": "PreRuntimeEarlyReturn",
            "message": _trim_text(getattr(prepared["pre_runtime"], "direct_reply_text", None) or "pre-runtime early return"),
            "phase": "pre_runtime_return",
        }
        return result
    messages = engine._build_messages(state)
    result["message_metrics"] = _message_metrics(messages)
    try:
        reply_text = await engine._generate_reply(state, chat_phase_probe=lambda event: events.append(dict(event)))
    except Exception as exc:
        result["status"] = "blocked"
        result["error"] = {
            "kind": type(exc).__name__,
            "message": _trim_text(exc),
            "phase": next((event.get("phase") for event in reversed(events) if event.get("status") == "failed"), None),
            "stage": getattr(exc, "_ego_stage", None),
            "timeout_stage": getattr(exc, "_ego_timeout_stage", None),
            "provider": getattr(exc, "_ego_provider", None),
            "model": getattr(exc, "_ego_model", None),
            "attempt_chain": list(getattr(exc, "_ego_attempt_chain", None) or []),
        }
        return result
    result["status"] = "completed"
    result["reply_text_preview"] = _trim_text(reply_text, limit=240)
    return result


def _run_dashboard_case_replay(*, case_id: str, prompt_text: str) -> dict[str, Any]:
    load_config(validate=False)
    events: list[dict[str, Any]] = []
    service = DashboardChatService(phase_probe=lambda event: events.append(dict(event)))
    session = service.ensure_session(f"chat-reply-probe-live-{case_id}")
    payload = service.send_message(session.session_id, prompt_text)
    return {
        "status": "completed",
        "events": events,
        "payload": payload,
        "last_debug": payload.get("debug"),
        "preparation": {
            "session_id": session.session_id,
        },
    }


async def _build_report(*, mode: str, case_id: str) -> dict[str, Any]:
    load_config(validate=False)
    chat_cfg = get_config().get_llm_config_for_use_case("chat")
    case = _find_case(case_id)
    prompt_text = _build_initial_prompt(case)
    if mode == "prompt-only":
        prepared = await _prepare_dashboard_chat_state(
            prompt_text=prompt_text,
            session_name=f"chat-reply-probe-{case_id}",
        )
        state = prepared["session"].state
        messages = prepared["engine"]._build_messages(state)
        probe_result = {
            "status": "completed" if prepared["ingress_gate"].ok and not getattr(prepared["pre_runtime"], "should_return_early", False) else "blocked_before_chat_engine",
            "preparation": {
                "session_id": prepared["session"].session_id,
                "conversation_act": state.ingress_context.get("conversation_act"),
                "ingress_gate_ok": bool(prepared["ingress_gate"].ok),
                "pre_runtime_should_return_early": bool(getattr(prepared["pre_runtime"], "should_return_early", False)),
            },
            "message_metrics": _message_metrics(messages),
            "message_preview": {
                "system": _trim_text(messages[0].get("content"), limit=280),
                "user": _trim_text(messages[1].get("content"), limit=600),
            },
            "events": [],
        }
    elif mode == "single-generate":
        probe_result = await _run_single_generate(case_id=case_id, prompt_text=prompt_text)
    elif mode == "dashboard-case-replay":
        probe_result = _run_dashboard_case_replay(case_id=case_id, prompt_text=prompt_text)
    else:
        raise SystemExit(f"Unsupported mode: {mode}")

    return {
        "schema_version": "dashboard_chat_reply_engine_probe.v1",
        "generated_at": _utc_now_iso(),
        "report_kind": "bounded_chat_reply_engine_probe",
        "claim_ceiling": "dashboard_only_single_entry_bounded_debug_evidence",
        "entrypoint_contract": {
            "entrypoint": "dashboard_chat",
            "source_kind": "dashboard_local",
            "rule": (
                "This probe only localizes the single-entry dashboard chat reply engine path. "
                "It does not prove runtime efficacy, broad real-user benefit, cross-entry behavior, or AI self-awareness achieved."
            ),
        },
        "mode": mode,
        "case": {
            "case_id": case.case_id,
            "family": case.family,
            "topic_id": case.topic_id,
        },
        "environment": {
            "provider": chat_cfg.get("provider"),
            "model": chat_cfg.get("model"),
            "chat_fallback_enabled": bool((chat_cfg.get("fallback") or {}).get("enabled")),
        },
        "probe": probe_result,
    }


def _render_markdown(report: dict[str, Any]) -> str:
    probe = dict(report.get("probe") or {})
    preparation = dict(probe.get("preparation") or {})
    message_metrics = dict(probe.get("message_metrics") or {})
    error = dict(probe.get("error") or {})
    lines = [
        "# Dashboard Chat Reply Engine Probe",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- mode: `{report.get('mode')}`",
        f"- provider: `{dict(report.get('environment') or {}).get('provider')}`",
        f"- model: `{dict(report.get('environment') or {}).get('model')}`",
        f"- status: `{probe.get('status')}`",
        "",
        "## Preparation",
        "",
        f"- session_id: `{preparation.get('session_id')}`",
        f"- conversation_act: `{preparation.get('conversation_act')}`",
        f"- ingress_gate_ok: `{preparation.get('ingress_gate_ok')}`",
        f"- pre_runtime_should_return_early: `{preparation.get('pre_runtime_should_return_early')}`",
        "",
        "## Message Metrics",
        "",
        f"- message_count: `{message_metrics.get('message_count')}`",
        f"- serialized_context_bytes: `{message_metrics.get('serialized_context_bytes')}`",
        f"- system_prompt_length: `{message_metrics.get('system_prompt_length')}`",
        f"- user_prompt_length: `{message_metrics.get('user_prompt_length')}`",
    ]
    if probe.get("reply_text_preview"):
        lines.extend(["", "## Reply Preview", "", f"- `{probe.get('reply_text_preview')}`"])
    if error:
        lines.extend(
            [
                "",
                "## Error",
                "",
                f"- kind: `{error.get('kind')}`",
                f"- message: `{error.get('message')}`",
                f"- phase: `{error.get('phase')}`",
                f"- stage: `{error.get('stage')}`",
                f"- timeout_stage: `{error.get('timeout_stage')}`",
            ]
        )
    events = list(probe.get("events") or [])
    if events:
        lines.extend(["", "## Event Tail", ""])
        for event in events[-12:]:
            lines.append(
                f"- phase: `{event.get('phase')}` status: `{event.get('status')}` "
                f"provider: `{event.get('provider')}` model: `{event.get('model')}` "
                f"attempt: `{event.get('provider_attempt')}` stage: `{event.get('stage')}` "
                f"content_source: `{event.get('content_source')}` elapsed_ms: `{event.get('elapsed_ms')}`"
            )
    lines.extend(
        [
            "",
            "## Claim Ceiling",
            "",
            "- This artifact only localizes the dashboard chat reply engine path.",
            "- It does not prove runtime efficacy, broad user benefit, cross-entry behavior, or AI self-awareness achieved.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe the dashboard chat reply engine path")
    parser.add_argument("--mode", choices=["prompt-only", "single-generate", "dashboard-case-replay"], default="single-generate")
    parser.add_argument("--case-id", default="open_01")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = asyncio.run(_build_report(mode=args.mode, case_id=args.case_id))
    _write_json(REPORT_JSON, report)
    _write_text(REPORT_MD, _render_markdown(report))
    print(json.dumps({"mode": args.mode, "status": dict(report.get("probe") or {}).get("status")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
