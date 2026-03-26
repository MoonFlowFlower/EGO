from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from app.telegram_bot import TelegramBot
from app.telegram_runtime_result import TelegramTurnReply, TelegramTurnResult


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "telegram_failure_cases"


class DummyChat:
    id = 8420019401
    type = "private"


class DummyUser:
    id = 8420019401
    username = "moonlight"


class DummyMessage:
    def __init__(self, text: str, message_id: int):
        self.text = text
        self.message_id = message_id
        self.reply_to_message = None
        self.sent: List[str] = []

    async def reply_text(self, text, parse_mode=None):
        self.sent.append(text)
        return None


class DummyUpdate:
    def __init__(self, text: str, message_id: int):
        self.message = DummyMessage(text, message_id)
        self.effective_chat = DummyChat()
        self.effective_user = DummyUser()


def _load_cases() -> List[Dict[str, Any]]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(FIXTURE_DIR.glob("*.json"))
    ]


@pytest.mark.parametrize("case", _load_cases(), ids=lambda case: case["case_id"])
@pytest.mark.asyncio
async def test_telegram_failure_case_replay(case, monkeypatch):
    bot = TelegramBot(token="dummy", use_runtime_v2=True)
    bot.native_loop = object()
    events: List[Dict[str, Any]] = []

    async def fake_publish_phase1_event(**kwargs):
        events.append(kwargs)

    async def fail_runtime(*args, **kwargs):
        raise AssertionError(f"{case['case_id']} should not fall back to runtime_v2")

    async def fake_native(*args, **kwargs):
        state = kwargs["state"]
        state.mark_task_completed()
        return TelegramTurnResult(
            status="completed_verified",
            state=state,
            reply=TelegramTurnReply(
                reply_text=case["expected"]["reply_text"],
                delivery_kind="final",
                status="completed_verified",
            ),
        )

    monkeypatch.setattr(bot, "_publish_phase1_event", fake_publish_phase1_event)
    monkeypatch.setattr(bot, "_run_runtime_v2_turn", fail_runtime)
    monkeypatch.setattr(bot, "_run_native_loop_turn", fake_native)

    state = bot._get_runtime_state(case["initial_state"]["session_key"])
    state.task_status = case["initial_state"].get("task_status", state.task_status)
    state.waiting_for_user_input = case["initial_state"].get("waiting_for_user_input", state.waiting_for_user_input)
    state.last_inferred_action = case["initial_state"].get("last_inferred_action")
    for artifact in case["initial_state"].get("pending_artifacts", []):
        state.add_pending_artifact(
            artifact_id=artifact["artifact_id"],
            filename=artifact.get("filename"),
            artifact_ref=artifact.get("artifact_ref"),
        )

    update = DummyUpdate(case["turn"]["text"], case["turn"]["message_id"])
    await bot._handle_with_runtime_v2(
        update=update,
        text=update.message.text,
        chat_id=DummyChat.id,
        user_id=DummyUser.id,
        username=DummyUser.username,
        trace_id=f"replay-{case['case_id']}",
    )

    assert update.message.sent == [case["expected"]["reply_text"]]
    assert state.ingress_context["runtime_action"] == case["expected"]["runtime_action"]
    assert state.ingress_context["resolved_target"]["artifact_id"] == case["expected"]["resolved_target_artifact_id"]
    assert any(
        event["kind"] == "primary_path_selected"
        and event["payload"]["path"] == case["expected"]["primary_path"]
        for event in events
    )
