from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

if "requests" not in sys.modules:
    sys.modules["requests"] = SimpleNamespace(
        get=lambda *args, **kwargs: None,
        post=lambda *args, **kwargs: None,
        exceptions=SimpleNamespace(
            Timeout=Exception,
            ConnectionError=Exception,
        ),
    )

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.telegram_bot import TelegramBot
from EgoCore.tools.run_mvp12_telegram_proactive_transport import (
    run_proactive_telegram_transport_session,
)


class DummyBotApi:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_message(self, chat_id, text):
        self.sent.append({"chat_id": chat_id, "text": text})
        return SimpleNamespace(
            chat=SimpleNamespace(id=chat_id),
            message_id=500 + len(self.sent),
            date=datetime.now(timezone.utc),
        )


@pytest.mark.asyncio
async def test_run_mvp12_telegram_proactive_transport_session_writes_artifact(tmp_path: Path) -> None:
    telegram_bot = TelegramBot(token="dummy", use_runtime_v2=True)
    telegram_bot.app = SimpleNamespace(bot=DummyBotApi())
    output_json = tmp_path / "telegram_proactive_transport.json"

    payload = await run_proactive_telegram_transport_session(
        messages=[
            "我在想，意识的门槛其实可能比人类自以为的低很多。你怎么看？",
            "有主观能动性。",
            "我觉得是有了OS的操作员的感觉。",
        ],
        session_id="telegram:dm:8420019401",
        chat_id=8420019401,
        simulated_idle_seconds=900.0,
        output_json=output_json,
        telegram_bot=telegram_bot,
    )

    assert payload["telegram_transport_result"]["status"] == "sent"
    assert payload["telegram_transport_result"]["sent_records"][0]["transport_source"] == "telegram"
    assert output_json.exists()
    written = json.loads(output_json.read_text(encoding="utf-8"))
    assert written["telegram_transport_result"]["status"] == "sent"
    assert written["pending_proactive_outbox_events"] == []
