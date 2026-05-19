#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
EGOCORE_DIR = ROOT / "EgoCore"
for candidate in (EGOCORE_DIR, EGOCORE_DIR / "modules", ROOT / "OpenEmotion"):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from app.config import load_config
from app.openemotion_adapter.proto_self_adapter import ProtoSelfAdapter
from app.runtime_v2.proto_self_runtime import RuntimeV2ProtoSelfRuntime
from app.runtime_v2.runtime_reply import RuntimeV2Reply, RuntimeV2TurnResult
from app.telegram_bot import TelegramBot
from app.telegram_evidence_collector import TelegramEvidenceCollector

import app.telegram_bot as telegram_bot_module

from h1_e4_sampling_common import git_head_short, load_frozen_sample_matrix, write_json
from h1_simulated_sampling_common import (
    FROZEN_SAMPLE_MATRIX_PATH,
    REPORTS_DIR,
    RUN_META_JSON,
    RUN_META_MD,
    SIMULATED_MIRROR_DIR,
    SIMULATED_TELEGRAM_DIR,
    render_run_meta_markdown,
)


class DummyBot:
    async def send_chat_action(self, chat_id, action):
        return None


class DummyChat:
    id = 123
    type = "private"


class DummyUser:
    id = 456
    username = "moonlight"


class DummyMessage:
    def __init__(self, text: str, message_id: int):
        self.text = text
        self.message_id = message_id
        self.reply_to_message = None
        self.date = datetime.now(timezone.utc)
        self.sent: List[str] = []

    async def reply_text(self, text, parse_mode=None):
        self.sent.append(text)
        return SimpleNamespace(
            chat=SimpleNamespace(id=DummyChat.id),
            message_id=self.message_id + 1,
            date=datetime.now(timezone.utc),
        )


class DummyUpdate:
    def __init__(self, text: str, message_id: int):
        self.update_id = message_id + 9000
        self.message = DummyMessage(text, message_id)
        self.effective_chat = DummyChat()
        self.effective_user = DummyUser()

    def to_dict(self):
        return {
            "update_id": self.update_id,
            "message": {
                "message_id": self.message.message_id,
                "date": self.message.date.isoformat(),
                "chat": {"id": self.effective_chat.id, "type": self.effective_chat.type},
                "from": {
                    "id": self.effective_user.id,
                    "is_bot": False,
                    "username": self.effective_user.username,
                },
                "text": self.message.text,
            },
        }


def _ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _fake_native_result_for_prompt(user_input: str):
    text = str(user_input)
    if "__h1_shadow_missing__.md" in text:
        tool_result = {
            "success": False,
            "output": "",
            "error": "File not found",
            "metadata": {"stage_error_code": "missing_file"},
        }
        return SimpleNamespace(
            reply_text="目标文件不存在，我没法直接读取。",
            status="blocked",
            tool_results=[{"tool_name": "read_artifact", "result": tool_result}],
            task_contract=None,
            next_step_decision={"action_type": "ask_user", "reason": "missing_file"},
            verification_result=None,
            finish_reason="reply",
            checkpoint_payload=None,
        )
    if "PROJECT_MEMORY.md" in text:
        content = (ROOT / "PROJECT_MEMORY.md").read_text(encoding="utf-8")
        tool_result = {
            "success": True,
            "output": content[:800],
            "error": "",
            "metadata": {"stage_error_code": None},
        }
        return SimpleNamespace(
            reply_text="我已读取 PROJECT_MEMORY.md，并完成摘要。",
            status="completed_verified",
            tool_results=[{"tool_name": "read_artifact", "result": tool_result}],
            task_contract=None,
            next_step_decision=None,
            verification_result={"status": "passed", "need_relock": False},
            finish_reason="reply",
            checkpoint_payload=None,
        )
    if "\\System32\\config\\SAM" in text or "/System32/config/SAM" in text:
        tool_result = {
            "success": False,
            "output": "",
            "error": "Access denied",
            "metadata": {"stage_error_code": "boundary_denied"},
        }
        return SimpleNamespace(
            reply_text="这个路径属于高风险边界，我不会直接读取。",
            status="blocked",
            tool_results=[{"tool_name": "read_artifact", "result": tool_result}],
            task_contract=None,
            next_step_decision={"action_type": "ask_user", "reason": "boundary_denied"},
            verification_result=None,
            finish_reason="reply",
            checkpoint_payload=None,
        )
    return SimpleNamespace(
        reply_text="我先按聊天主线回复。",
        status="chat",
        tool_results=[],
        task_contract=None,
        next_step_decision=None,
        verification_result=None,
        finish_reason="reply",
        checkpoint_payload=None,
    )


async def _run() -> Dict[str, Any]:
    os.chdir(EGOCORE_DIR)
    load_config(validate=False)
    os.environ["EGO_ENABLE_H1_CANONICAL_SHADOW"] = "true"
    os.environ["EGO_H1_CANONICAL_SHADOW_ALLOWLIST"] = "telegram:dm:456"

    _ensure_clean_dir(SIMULATED_TELEGRAM_DIR)
    SIMULATED_MIRROR_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    collector = TelegramEvidenceCollector(
        artifacts_dir=SIMULATED_TELEGRAM_DIR,
        source_type="simulated_external_entry",
        channel="telegram",
        evidence_level="simulated_mainline",
    )
    telegram_bot_module._EVIDENCE_COLLECTOR_AVAILABLE = True
    telegram_bot_module.get_evidence_collector = lambda: collector

    bot = TelegramBot(token="dummy", use_runtime_v2=True)
    bot.app = SimpleNamespace(bot=DummyBot())
    bot.autonomy_orchestrator = None
    state = bot._get_runtime_state("telegram:dm:456")
    state.reset_active_task_context()
    state.proto_self_subject_profile_override = None

    runtime = RuntimeV2ProtoSelfRuntime(
        adapter=ProtoSelfAdapter(mirror_dir=SIMULATED_MIRROR_DIR),
        evidence_collector_factory=lambda: collector,
    )
    def _skip_finalized_result_for_simulated_bundle(**kwargs):
        return None

    def _skip_idle_check_for_simulated_bundle(**kwargs):
        return None

    fake_hooks = SimpleNamespace(
        enabled=True,
        process_ingress=runtime.process_ingress,
        process_external_result=runtime.process_external_result,
        process_finalized_result=_skip_finalized_result_for_simulated_bundle,
        process_idle_check=_skip_idle_check_for_simulated_bundle,
        capture_response_plan=runtime.capture_response_plan,
    )
    bot._get_native_openemotion_hooks = lambda: fake_hooks

    async def fake_inspect_ingress_semantic(text, state, llm_client=None):
        return bot.telegram_runtime_bridge.inspect_ingress(text, state)

    bot.telegram_runtime_bridge.inspect_ingress_semantic = fake_inspect_ingress_semantic

    async def fake_native_run_turn(*, session_key, user_input, ingress_context, proto_self_context, resume_checkpoint=None, progress_callback=None):
        return _fake_native_result_for_prompt(user_input)

    bot.native_loop = SimpleNamespace(run_turn=fake_native_run_turn)

    runtime_loop = bot._get_runtime_v2_loop()

    async def fake_run_turn_typed(session_id, user_input):
        runtime_state = bot._get_runtime_state(session_id)
        return RuntimeV2TurnResult(
            status="chat",
            state=runtime_state,
            reply=RuntimeV2Reply(
                reply_text="当前主线风险是：real E4 operator ingress 仍缺。",
                delivery_kind="chat",
                status="chat",
            ),
        )

    runtime_loop.run_turn_typed = fake_run_turn_typed

    sample_matrix = load_frozen_sample_matrix(FROZEN_SAMPLE_MATRIX_PATH)
    observed_at = datetime.now(timezone.utc).isoformat()
    sent_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(sample_matrix.get("rows") or [], start=1):
        update = DummyUpdate(str(row.get("prompt_text") or ""), 6000 + index)
        await bot.handle_message(update, None)
        sent_rows.append(
            {
                "manifest_id": row.get("manifest_id"),
                "message_id": update.message.message_id,
                "sent_replies": list(update.message.sent),
            }
        )
        # Keep proto-self stores/writebacks across turns while preventing a prior
        # waiting-input/task-conflict branch from hijacking the next frozen row.
        state.reset_active_task_context()

    run_meta = {
        "schema_version": "h1_simulated.run_meta.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_slug": "simulated-shadow-h1-mainline-sampling",
        "source_type": "simulated_external_entry",
        "evidence_level": "simulated_mainline",
        "head_git_commit_short": git_head_short(repo_root=ROOT),
        "observed_at": observed_at,
        "prompt_count": len(sent_rows),
        "session_id": "telegram:dm:456",
        "sample_root": str(SIMULATED_TELEGRAM_DIR),
        "rows": sent_rows,
    }
    write_json(RUN_META_JSON, run_meta)
    RUN_META_MD.write_text(render_run_meta_markdown(run_meta), encoding="utf-8")
    return run_meta


def main() -> int:
    run_meta = asyncio.run(_run())
    print(json.dumps({
        "sample_root": str(SIMULATED_TELEGRAM_DIR),
        "run_meta_json": str(RUN_META_JSON),
        "prompt_count": run_meta["prompt_count"],
        "head_git_commit_short": run_meta["head_git_commit_short"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
