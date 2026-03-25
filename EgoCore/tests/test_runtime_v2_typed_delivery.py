import pytest

from app.runtime_v2.runtime_reply import RuntimeV2Reply, RuntimeV2TurnResult
from app.telegram_bot import TelegramBot


@pytest.mark.asyncio
async def test_telegram_runtime_v2_delivery_accepts_typed_result():
    bot = TelegramBot(token="test-token", use_runtime_v2=True)

    class DummyMessage:
        last_text = None
        async def reply_text(self, text, parse_mode=None):
            self.last_text = text

    class DummyUpdate:
        message = DummyMessage()

    state = bot.runtime_v2_loop.get_state("telegram:dm:456")
    result = RuntimeV2TurnResult(
        status="completed_verified",
        state=state,
        reply=RuntimeV2Reply(
            reply_text="已经改好了。",
            delivery_kind="final",
            status="completed_verified",
        ),
    )

    await bot._deliver_runtime_v2_result(DummyUpdate(), state, result, is_challenge_turn=False)
    assert DummyUpdate.message.last_text == "已经改好了。"
