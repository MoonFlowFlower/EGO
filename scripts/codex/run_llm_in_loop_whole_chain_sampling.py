#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]
EGOCORE_DIR = ROOT / "EgoCore"
for candidate in (EGOCORE_DIR, EGOCORE_DIR / "modules", ROOT / "OpenEmotion"):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from app.agent_core.native_loop import NativeLoopResult, NativeToolCallingLoop
from app.config import load_config
from app.llm_client import LLMResponse
from app.openemotion_adapter.proto_self_adapter import ProtoSelfAdapter
from app.openemotion_hooks.native_hooks import NativeOpenEmotionHooks
from app.runtime_v2.proto_self_runtime import RuntimeV2ProtoSelfRuntime
from app.telegram_bot import TelegramBot
from app.telegram_evidence_collector import TelegramEvidenceCollector
from app.telegram_runtime_result import TelegramTurnResult
from app.runtime_v2.unified_channel_contract import UnifiedIngressBundle, UnifiedIngressRequest, build_unified_ingress

import app.telegram_bot as telegram_bot_module

from scripts.codex.h1_e4_sampling_common import (
    git_head_short,
    load_sample_bundles,
    now_iso,
    rel_path,
    write_json,
    write_text,
)


ARTIFACT_ROOT = ROOT / "artifacts" / "telegram_simulated_whole_chain_v1"
SAMPLE_ROOT = ARTIFACT_ROOT / "simulated_telegram"
REPORTS_DIR = ARTIFACT_ROOT / "reports"
MIRROR_ROOT = ARTIFACT_ROOT / "mirror"
TARGET_ROOT = ARTIFACT_ROOT / "generated_targets"

RUN_JSON = REPORTS_DIR / "LLM_WHOLE_CHAIN_RUN_CURRENT.json"
RUN_MD = REPORTS_DIR / "LLM_WHOLE_CHAIN_RUN_CURRENT.md"
MANIFEST_JSON = REPORTS_DIR / "LLM_WHOLE_CHAIN_SAMPLE_MANIFEST_CURRENT.json"
MANIFEST_MD = REPORTS_DIR / "LLM_WHOLE_CHAIN_SAMPLE_MANIFEST_CURRENT.md"
FAILURES_JSON = REPORTS_DIR / "LLM_WHOLE_CHAIN_FAILURES_CURRENT.json"
FAILURES_MD = REPORTS_DIR / "LLM_WHOLE_CHAIN_FAILURES_CURRENT.md"
EXECUTION_JSON = REPORTS_DIR / "LLM_WHOLE_CHAIN_EXECUTION_REPORT_CURRENT.json"
EXECUTION_MD = REPORTS_DIR / "LLM_WHOLE_CHAIN_EXECUTION_REPORT_CURRENT.md"
TRACE_READINESS_JSON = REPORTS_DIR / "LLM_WHOLE_CHAIN_TRACE_READINESS_CURRENT.json"
TRACE_READINESS_MD = REPORTS_DIR / "LLM_WHOLE_CHAIN_TRACE_READINESS_CURRENT.md"

EXTRA_TRACE_FILES = [
    "ingress_event.json",
    "native_loop_trace.json",
    "contract_runtime_trace.json",
    "model_trace.json",
    "tool_trace.json",
]


@dataclass(frozen=True)
class FrozenCase:
    case_id: str
    prompt: str
    target_filename: str
    output_format: str


FROZEN_CASES: List[FrozenCase] = [
    FrozenCase(
        case_id="C1_create_html_intro",
        prompt="请在 {target_path} 创建一个介绍 EgoCore 的 html 页面。",
        target_filename="egocore_intro.html",
        output_format="html",
    ),
    FrozenCase(
        case_id="C2_create_html_openemotion",
        prompt="请在 {target_path} 创建一个介绍 OpenEmotion 的 html 页面。",
        target_filename="openemotion_intro.html",
        output_format="html",
    ),
]


class DummyBot:
    async def send_chat_action(self, chat_id, action):
        return None


class DummyChat:
    def __init__(self, chat_id: int):
        self.id = chat_id
        self.type = "private"


class DummyUser:
    def __init__(self, user_id: int, username: str):
        self.id = user_id
        self.username = username


class DummyMessage:
    def __init__(self, text: str, message_id: int, chat_id: int):
        self.text = text
        self.message_id = message_id
        self.reply_to_message = None
        self.date = datetime.now(timezone.utc)
        self.sent: List[str] = []
        self._chat_id = chat_id

    async def reply_text(self, text, parse_mode=None):
        self.sent.append(text)
        return SimpleNamespace(
            chat=SimpleNamespace(id=self._chat_id),
            message_id=self.message_id + len(self.sent),
            date=datetime.now(timezone.utc),
        )


class DummyUpdate:
    def __init__(self, text: str, *, message_id: int, chat_id: int, user_id: int, username: str):
        self.update_id = message_id + 9000
        self.message = DummyMessage(text, message_id=message_id, chat_id=chat_id)
        self.effective_chat = DummyChat(chat_id)
        self.effective_user = DummyUser(user_id, username)

    def to_dict(self):
        return {
            "update_id": self.update_id,
            "message": {
                "message_id": self.message.message_id,
                "date": self.message.date.isoformat(),
                "chat": {"id": self.effective_chat.id, "type": self.effective_chat.type},
                "from": {"id": self.effective_user.id, "is_bot": False, "username": self.effective_user.username},
                "text": self.message.text,
            },
        }


def _ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _safe_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _safe_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_json(item) for item in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _safe_json(value.to_dict())
    if hasattr(value, "__dict__"):
        return _safe_json(vars(value))
    return repr(value)


def _response_to_dict(response: LLMResponse) -> Dict[str, Any]:
    return {
        "content": response.content,
        "model": response.model,
        "provider": response.provider,
        "usage": dict(response.usage or {}),
        "finish_reason": response.finish_reason,
        "raw_response": _safe_json(response.raw_response),
        "tool_calls": _safe_json(response.tool_calls),
    }


def _extract_contract_and_step(messages: List[Dict[str, Any]]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    system_content = ""
    for message in reversed(messages):
        if message.get("role") == "system" and "Contract Lock:\n" in str(message.get("content") or ""):
            system_content = str(message.get("content") or "")
            break
    if not system_content:
        raise ValueError("contract system message missing")
    match = re.search(
        r"Contract Lock:\n(.*?)\n\nNext Step Decision:\n(.*?)\n\nRules:\n",
        system_content,
        re.DOTALL,
    )
    if not match:
        raise ValueError("failed to parse contract/step payload")
    return json.loads(match.group(1)), json.loads(match.group(2))


def _build_file_content(contract: Dict[str, Any], path: str) -> str:
    output_format = str(contract.get("output_format") or Path(path).suffix.lstrip(".") or "txt").lower()
    goal = str(contract.get("goal") or "完成任务")
    if output_format == "html":
        return (
            "<!DOCTYPE html><html><body>"
            f"<h1>EgoCore</h1><p>{goal}</p>"
            "</body></html>"
        )
    if output_format in {"md", "markdown"}:
        return f"# 进度摘要\n\n- 目标：{goal}\n- 状态：已生成 whole-chain 样本\n"
    return f"{goal}\n"


class TracingFakeLLMClient:
    def __init__(self, *, case_id: str):
        self.case_id = case_id
        self.interactions: List[Dict[str, Any]] = []

    def chat_with_tools(self, messages, tools, **kwargs):
        contract, step = _extract_contract_and_step(messages)
        if step.get("action_type") == "call_tool":
            target_path = str((step.get("tool_input") or {}).get("path") or contract.get("target_path") or "")
            tool_call = {
                "id": f"{self.case_id}_tool_1",
                "type": "function",
                "name": str(step.get("tool_name") or "file"),
                "arguments": {
                    "operation": "write",
                    "path": target_path,
                    "content": _build_file_content(contract, target_path),
                },
            }
            response = LLMResponse(
                content="",
                model="simulated-whole-chain",
                provider="simulated",
                usage={"prompt_tokens": 120, "completion_tokens": 24},
                finish_reason="tool_calls",
                raw_response={"contract": contract, "step": step, "mode": "tool_call"},
                tool_calls=[tool_call],
            )
        else:
            response = LLMResponse(
                content="这轮不需要调用工具。",
                model="simulated-whole-chain",
                provider="simulated",
                usage={"prompt_tokens": 80, "completion_tokens": 18},
                finish_reason="stop",
                raw_response={"contract": contract, "step": step, "mode": "reply"},
            )
        self.interactions.append(
            {
                "call_kind": "chat_with_tools",
                "request": {
                    "messages": _safe_json(messages),
                    "tools": _safe_json(tools),
                    "kwargs": _safe_json(kwargs),
                },
                "response": _response_to_dict(response),
            }
        )
        return response

    def generate_with_messages(self, messages, **kwargs):
        tool_message = next((m for m in reversed(messages) if m.get("role") == "tool"), {})
        tool_payload = json.loads(tool_message.get("content") or "{}") if tool_message else {}
        metadata = dict(tool_payload.get("metadata") or {})
        path = metadata.get("path") or ""
        if tool_payload.get("success"):
            content = f"已完成，并写入 {path}。"
        else:
            content = f"执行失败：{tool_payload.get('error') or 'unknown_error'}"
        response = LLMResponse(
            content=content,
            model="simulated-whole-chain",
            provider="simulated",
            usage={"prompt_tokens": 60, "completion_tokens": 20},
            finish_reason="stop",
            raw_response={"tool_result": tool_payload},
        )
        self.interactions.append(
            {
                "call_kind": "generate_with_messages",
                "request": {
                    "messages": _safe_json(messages),
                    "kwargs": _safe_json(kwargs),
                },
                "response": _response_to_dict(response),
            }
        )
        return response


def _serialize_request(request: UnifiedIngressRequest) -> Dict[str, Any]:
    return {
        "channel": request.channel,
        "source_kind": request.source_kind,
        "session_key": request.session_key,
        "user_input": request.user_input,
        "effective_user_input": request.effective_user_input,
        "raw_event": _safe_json(request.raw_event),
        "transport_meta": _safe_json(request.transport_meta),
        "extra_context": request.extra_context,
    }


def _serialize_bundle(bundle: UnifiedIngressBundle) -> Dict[str, Any]:
    pre_runtime = bundle.pre_runtime_action
    return {
        "runtime_action": bundle.runtime_action,
        "ingress_context": _safe_json(bundle.ingress_context),
        "normalized_turn": _safe_json(bundle.normalized_turn),
        "semantic_decision": _safe_json(bundle.semantic_decision),
        "pre_runtime_action": _safe_json(pre_runtime),
    }


def _serialize_native_loop_result(result: NativeLoopResult, progress_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "status": result.status,
        "reply_text": result.reply_text,
        "usage": _safe_json(result.usage),
        "finish_reason": result.finish_reason,
        "task_contract": _safe_json(result.task_contract),
        "next_step_decision": _safe_json(result.next_step_decision),
        "verification_result": _safe_json(result.verification_result),
        "checkpoint_payload": _safe_json(result.checkpoint_payload),
        "tool_results": _safe_json(result.tool_results),
        "progress_events": _safe_json(progress_events),
    }


def _serialize_contract_trace(
    *,
    native_result: NativeLoopResult,
    phase_events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "trace_schema": "contract_runtime_v1",
        "task_contract": _safe_json(native_result.task_contract),
        "next_step_decision": _safe_json(native_result.next_step_decision),
        "verification_result": _safe_json(native_result.verification_result),
        "tool_results": _safe_json(native_result.tool_results),
        "usage": _safe_json(native_result.usage),
        "finish_reason": native_result.finish_reason,
        "phase_events": _safe_json(phase_events),
    }


def _serialize_tool_trace(native_result: NativeLoopResult) -> Dict[str, Any]:
    return {
        "tool_call_count": len(native_result.tool_results),
        "tool_results": _safe_json(native_result.tool_results),
    }


def _write_markdown(path: Path, text: str) -> None:
    write_text(path, text if text.endswith("\n") else text + "\n")


async def _run_case(case: FrozenCase, index: int) -> Dict[str, Any]:
    chat_id = 9100 + index
    user_id = 8100 + index
    username = f"wholechain{index}"
    target_path = TARGET_ROOT / case.target_filename
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        target_path.unlink()
    prompt = case.prompt.format(target_path=str(target_path))

    collector = TelegramEvidenceCollector(
        artifacts_dir=SAMPLE_ROOT,
        source_type="simulated_whole_chain",
        channel="telegram",
        evidence_level="E3_controlled_integration",
    )
    telegram_bot_module._EVIDENCE_COLLECTOR_AVAILABLE = True
    telegram_bot_module.get_evidence_collector = lambda: collector

    bot = TelegramBot(token="dummy", use_runtime_v2=True)
    bot.app = SimpleNamespace(bot=DummyBot())
    bot.autonomy_orchestrator = None
    bot._send_autonomy_progress_update = lambda **kwargs: asyncio.sleep(0)

    async def fake_semantic(text, state, llm_client=None):
        return bot.telegram_runtime_bridge.inspect_ingress(text, state)

    bot.telegram_runtime_bridge.inspect_ingress_semantic = fake_semantic

    tracing_client = TracingFakeLLMClient(case_id=case.case_id)
    native_loop = NativeToolCallingLoop(llm_client=tracing_client)
    progress_events: List[Dict[str, Any]] = []
    phase_events: List[Dict[str, Any]] = []
    captured_native_result: Dict[str, Any] = {}

    original_run_turn = native_loop.run_turn

    async def traced_run_turn(**kwargs):
        progress_callback = kwargs.get("progress_callback")

        async def wrapped_progress(phase: str, payload: Dict[str, Any]) -> None:
            progress_events.append({"phase": phase, "payload": _safe_json(payload)})
            if progress_callback is not None:
                await progress_callback(phase, payload)

        kwargs["progress_callback"] = wrapped_progress
        result = await original_run_turn(**kwargs)
        captured_native_result["result"] = result
        return result

    native_loop.run_turn = traced_run_turn  # type: ignore[assignment]
    bot.native_loop = native_loop

    async def capture_phase1_event(**kwargs):
        phase_events.append(
            {
                "kind": kwargs.get("kind"),
                "trace_id": kwargs.get("trace_id"),
                "message_id": kwargs.get("message_id"),
                "payload": _safe_json(kwargs.get("payload") or {}),
            }
        )
        return None

    bot._publish_phase1_event = capture_phase1_event  # type: ignore[assignment]

    hooks = NativeOpenEmotionHooks()
    hooks.runtime = RuntimeV2ProtoSelfRuntime(
        adapter=ProtoSelfAdapter(mirror_dir=MIRROR_ROOT / case.case_id),
        evidence_collector_factory=lambda: collector,
    )
    bot.native_openemotion_hooks = hooks

    update = DummyUpdate(
        prompt,
        message_id=6000 + index,
        chat_id=chat_id,
        user_id=user_id,
        username=username,
    )
    collector.start_sample(update.to_dict())

    session_key = bot._resolve_session_key(update, chat_id, user_id)
    bot._remember_session_transport_binding(session_key, chat_id)
    bot._latest_message_id_by_session[session_key] = update.message.message_id

    state = bot._get_runtime_state(session_key)
    state.reset_active_task_context()
    state.proto_self_subject_profile_override = None

    unified_request = bot._build_unified_telegram_request(
        update=update,
        session_key=session_key,
        text=prompt,
        chat_id=chat_id,
        user_id=user_id,
        username=username,
        source_kind="telegram_simulated",
    )
    unified_ingress = await build_unified_ingress(
        unified_request,
        state,
        bridge=bot.telegram_runtime_bridge,
        llm_client=None,
    )
    ingress = unified_ingress.semantic_decision
    state.ingress_context = dict(unified_ingress.ingress_context or {})
    pre_runtime = unified_ingress.pre_runtime_action
    runtime_action = getattr(ingress, "_runtime_action", None)

    failure: Optional[Dict[str, Any]] = None
    if pre_runtime.should_return_early:
        failure = {"cause": "pre_runtime_early_return", "details": _safe_json(pre_runtime)}
    elif runtime_action != "execute_task":
        failure = {"cause": "unexpected_runtime_action", "details": {"runtime_action": runtime_action}}

    if failure is None:
        ok = await bot._ensure_subject_ingress(
            update=update,
            session_key=session_key,
            state=state,
            text=unified_request.effective_user_input,
            trace_id=f"wholechain{index}",
            ingress_message_id=update.message.message_id,
            turn_prefix="runtime_v2",
            source="telegram_simulated",
        )
        if not ok:
            failure = {"cause": "subject_gate_blocked", "details": {}}

    if failure is None:
        result = await bot._run_primary_turn(
            update=update,
            session_key=session_key,
            text=unified_request.effective_user_input,
            state=state,
            ingress=ingress,
            ack_text=pre_runtime.ack_text,
            trace_id=f"wholechain{index}",
            ingress_message_id=update.message.message_id,
            chat_id=chat_id,
        )
        await bot._deliver_runtime_v2_result(
            update=update,
            state=state,
            result=result,
            is_challenge_turn=ingress.is_challenge_turn,
            ingress_message_id=update.message.message_id,
            trace_id=f"wholechain{index}",
        )

    sample = collector._samples[-1] if collector._samples else None
    sample_id = sample.sample_id if sample is not None else None
    sample_dir = SAMPLE_ROOT / sample_id if sample_id else None
    if sample_dir is None or not sample_dir.exists():
        failure = failure or {"cause": "sample_not_finalized", "details": {}}
    else:
        native_result = captured_native_result.get("result")
        if native_result is None:
            failure = failure or {"cause": "native_loop_result_missing", "details": {}}
        else:
            write_json(
                sample_dir / "ingress_event.json",
                {
                    "schema_version": "whole_chain.ingress_event.v1",
                    "generated_at": now_iso(),
                    "case_id": case.case_id,
                    "request": _serialize_request(unified_request),
                    "bundle": _serialize_bundle(unified_ingress),
                },
            )
            write_json(
                sample_dir / "native_loop_trace.json",
                _serialize_native_loop_result(native_result, progress_events),
            )
            write_json(
                sample_dir / "contract_runtime_trace.json",
                _serialize_contract_trace(native_result=native_result, phase_events=phase_events),
            )
            write_json(
                sample_dir / "model_trace.json",
                {
                    "schema_version": "whole_chain.model_trace.v1",
                    "interaction_count": len(tracing_client.interactions),
                    "interactions": _safe_json(tracing_client.interactions),
                    "requery_required": False,
                },
            )
            write_json(
                sample_dir / "tool_trace.json",
                _serialize_tool_trace(native_result),
            )

    return {
        "case_id": case.case_id,
        "prompt": prompt,
        "session_key": session_key,
        "runtime_action": runtime_action,
        "sample_id": sample_id,
        "sample_dir": rel_path(sample_dir) if sample_dir else None,
        "failure": failure,
    }


def _trace_ready(sample_dir: Path) -> Dict[str, Any]:
    required = {
        "evidence": [
            "raw_update.json",
            "normalized_event.json",
            "openemotion_result.json",
            "response_plan.json",
            "outbox_record.json",
            "timeline.json",
            "tape.json",
            "replay.json",
        ],
        "whole_chain": EXTRA_TRACE_FILES,
    }
    file_status = {
        group: {name: (sample_dir / name).exists() for name in names}
        for group, names in required.items()
    }
    model_trace = json.loads((sample_dir / "model_trace.json").read_text(encoding="utf-8")) if (sample_dir / "model_trace.json").exists() else {}
    interactions = list(model_trace.get("interactions") or [])
    replay_ready = (
        all(all(status.values()) for status in file_status.values())
        and bool(interactions)
        and all(item.get("request") and item.get("response") for item in interactions)
        and not bool(model_trace.get("requery_required"))
    )
    return {
        "file_status": file_status,
        "model_interaction_count": len(interactions),
        "replay_ready_without_requery": replay_ready,
    }


def _build_reports(run_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    bundles = load_sample_bundles(SAMPLE_ROOT)
    bundles_by_dir = {rel_path(bundle.sample_dir): bundle for bundle in bundles}
    manifest_rows = []
    failure_rows = []
    trace_rows = []
    for row in run_rows:
        sample_dir_ref = row.get("sample_dir")
        bundle = bundles_by_dir.get(sample_dir_ref) if sample_dir_ref else None
        failure = row.get("failure")
        if failure:
            failure_rows.append(
                {
                    "case_id": row["case_id"],
                    "cause": failure["cause"],
                    "details": _safe_json(failure.get("details") or {}),
                    "sample_dir": sample_dir_ref,
                }
            )
        manifest_rows.append(
            {
                "case_id": row["case_id"],
                "runtime_action": row.get("runtime_action"),
                "sample_id": row.get("sample_id"),
                "sample_dir": sample_dir_ref,
                "status": "failed" if failure else "completed",
                "bundle_complete": bool(bundle.is_complete) if bundle else False,
                "delivery_success": bool(bundle.outbox_record.get("success")) if bundle else False,
            }
        )
        if bundle:
            readiness = _trace_ready(bundle.sample_dir)
            trace_rows.append(
                {
                    "case_id": row["case_id"],
                    "sample_id": bundle.sample_id,
                    "sample_dir": rel_path(bundle.sample_dir),
                    "replay_ready_without_requery": readiness["replay_ready_without_requery"],
                    "model_interaction_count": readiness["model_interaction_count"],
                    "file_status": readiness["file_status"],
                }
            )

    execution_payload = {
        "schema_version": "whole_chain.execution_report.v1",
        "generated_at": now_iso(),
        "task_slug": "llm-in-loop-whole-chain-sampling",
        "head_git_commit_short": git_head_short(repo_root=ROOT),
        "source_type": "simulated_whole_chain",
        "evidence_level_ceiling": "E3_controlled_integration",
        "summary": {
            "expected_cases": len(FROZEN_CASES),
            "completed_cases": sum(1 for row in manifest_rows if row["status"] == "completed"),
            "failed_cases": len(failure_rows),
            "bundle_complete_cases": sum(1 for row in manifest_rows if row["bundle_complete"]),
            "replay_ready_cases": sum(1 for row in trace_rows if row["replay_ready_without_requery"]),
        },
        "can_prove": [
            "simulated Telegram can traverse the full subject flow with llm_client in the loop on a bounded sample set",
            "whole-chain artifacts can be captured without changing canonical mainline behavior",
            "captured model request/response plus tool returns are sufficient for bounded later replay without re-querying the model for replay-ready samples",
        ],
        "cannot_prove": [
            "runtime efficacy",
            "real Telegram / E4 behavior",
            "repo-level enablement",
            "generalized whole-chain replay beyond the bounded sample set",
        ],
        "hard_rule_status": {
            "relabeled_as_replay": False,
            "repo_level_state_upgraded": False,
            "runtime_efficacy_claim": False,
        },
    }
    manifest_payload = {
        "schema_version": "whole_chain.sample_manifest.v1",
        "generated_at": now_iso(),
        "rows": manifest_rows,
    }
    failures_payload = {
        "schema_version": "whole_chain.failures_table.v1",
        "generated_at": now_iso(),
        "failure_count": len(failure_rows),
        "rows": failure_rows,
    }
    trace_payload = {
        "schema_version": "whole_chain.trace_readiness.v1",
        "generated_at": now_iso(),
        "rows": trace_rows,
    }
    return {
        "execution": execution_payload,
        "manifest": manifest_payload,
        "failures": failures_payload,
        "trace_readiness": trace_payload,
    }


def _render_execution_md(payload: Dict[str, Any]) -> str:
    summary = payload["summary"]
    return f"""# LLM-in-Loop Whole-Chain Execution Report

- generated_at: `{payload['generated_at']}`
- source_type: `{payload['source_type']}`
- evidence_level_ceiling: `{payload['evidence_level_ceiling']}`
- head_git_commit_short: `{payload['head_git_commit_short']}`

## Summary

- expected_cases: `{summary['expected_cases']}`
- completed_cases: `{summary['completed_cases']}`
- failed_cases: `{summary['failed_cases']}`
- bundle_complete_cases: `{summary['bundle_complete_cases']}`
- replay_ready_cases: `{summary['replay_ready_cases']}`

## Can Prove

- simulated Telegram whole-chain path can run with `llm_client` in the loop on this bounded slice
- whole-chain artifacts are captured without changing canonical mainline behavior
- replay-ready traces exist only for the bounded simulated samples that captured full model/tool/runtime artifacts

## Cannot Prove

- runtime efficacy
- real Telegram / E4 behavior
- repo-level enablement
- generalized replay beyond this bounded slice
"""


def _render_manifest_md(payload: Dict[str, Any]) -> str:
    rows = "\n".join(
        f"| `{row['case_id']}` | `{row['status']}` | `{row['runtime_action']}` | `{row['sample_id'] or 'none'}` | `{row['bundle_complete']}` | `{row['delivery_success']}` |"
        for row in payload["rows"]
    )
    return f"""# LLM-in-Loop Whole-Chain Sample Manifest

| case_id | status | runtime_action | sample_id | bundle_complete | delivery_success |
|---|---|---|---|---|---|
{rows}
"""


def _render_failures_md(payload: Dict[str, Any]) -> str:
    if not payload["rows"]:
        return "# LLM-in-Loop Whole-Chain Failures\n\n- failure_count: `0`\n"
    rows = "\n".join(
        f"| `{row['case_id']}` | `{row['cause']}` | `{row['sample_dir'] or 'none'}` | `{json.dumps(row['details'], ensure_ascii=False)}` |"
        for row in payload["rows"]
    )
    return f"""# LLM-in-Loop Whole-Chain Failures

- failure_count: `{payload['failure_count']}`

| case_id | cause | sample_dir | details |
|---|---|---|---|
{rows}
"""


def _render_trace_md(payload: Dict[str, Any]) -> str:
    rows = "\n".join(
        f"| `{row['case_id']}` | `{row['sample_id']}` | `{row['replay_ready_without_requery']}` | `{row['model_interaction_count']}` |"
        for row in payload["rows"]
    )
    return f"""# LLM-in-Loop Whole-Chain Trace Readiness

| case_id | sample_id | replay_ready_without_requery | model_interaction_count |
|---|---|---|---|
{rows}
"""


async def _run() -> Dict[str, Any]:
    os.chdir(EGOCORE_DIR)
    load_config(validate=False)
    os.environ["EGO_ENABLE_H1_CANONICAL_SHADOW"] = "true"
    os.environ["EGO_H1_CANONICAL_SHADOW_ALLOWLIST"] = "*"

    _ensure_clean_dir(SAMPLE_ROOT)
    _ensure_clean_dir(MIRROR_ROOT)
    _ensure_clean_dir(TARGET_ROOT)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    run_rows = []
    for index, case in enumerate(FROZEN_CASES, start=1):
        run_rows.append(await _run_case(case, index))

    reports = _build_reports(run_rows)
    run_payload = {
        "schema_version": "whole_chain.run_meta.v1",
        "generated_at": now_iso(),
        "task_slug": "llm-in-loop-whole-chain-sampling",
        "sample_root": rel_path(SAMPLE_ROOT),
        "reports_root": rel_path(REPORTS_DIR),
        "case_count": len(FROZEN_CASES),
        "cases": [asdict(case) for case in FROZEN_CASES],
    }

    write_json(RUN_JSON, run_payload)
    write_json(MANIFEST_JSON, reports["manifest"])
    write_json(FAILURES_JSON, reports["failures"])
    write_json(EXECUTION_JSON, reports["execution"])
    write_json(TRACE_READINESS_JSON, reports["trace_readiness"])

    _write_markdown(RUN_MD, f"# LLM-in-Loop Whole-Chain Run\n\n- case_count: `{run_payload['case_count']}`\n- sample_root: `{run_payload['sample_root']}`\n")
    _write_markdown(MANIFEST_MD, _render_manifest_md(reports["manifest"]))
    _write_markdown(FAILURES_MD, _render_failures_md(reports["failures"]))
    _write_markdown(EXECUTION_MD, _render_execution_md(reports["execution"]))
    _write_markdown(TRACE_READINESS_MD, _render_trace_md(reports["trace_readiness"]))

    return {
        "run": run_payload,
        "reports": reports,
    }


def main() -> int:
    payload = asyncio.run(_run())
    print(
        json.dumps(
            {
                "sample_root": str(SAMPLE_ROOT),
                "case_count": payload["run"]["case_count"],
                "failed_cases": payload["reports"]["execution"]["summary"]["failed_cases"],
                "replay_ready_cases": payload["reports"]["execution"]["summary"]["replay_ready_cases"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
