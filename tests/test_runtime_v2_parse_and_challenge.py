import pytest

from app.runtime_v2.action_protocol import RuntimeV2Action
from app.runtime_v2.loop import RuntimeV2Loop
from app.telegram_bot import TelegramBot


def test_action_protocol_invalid_json_returns_internal_ask_without_user_text():
    action = RuntimeV2Action.from_model_output('not json at all')
    assert action.type == 'ask'
    assert action.question is None
    assert action.raw['kind'] == 'invalid_json'


@pytest.mark.asyncio
async def test_runtime_v2_loop_retries_invalid_json_once(monkeypatch):
    loop = RuntimeV2Loop()
    actions = iter([
        RuntimeV2Action.from_model_output('not json at all'),
        RuntimeV2Action.from_model_output('{"type":"chat","message":"你好，我在。"}'),
    ])

    async def fake_decide(_state):
        return next(actions)

    monkeypatch.setattr(loop, '_decide', fake_decide)
    result = await loop.run_turn_typed('session:test', '你好')
    assert result.status == 'chat'
    assert result.reply_text == '你好，我在。'


@pytest.mark.asyncio
async def test_challenge_turn_does_not_get_absorbed_as_busy_placeholder(monkeypatch):
    bot = TelegramBot(token='test-token', use_runtime_v2=True)

    class DummyBot:
        async def send_chat_action(self, chat_id, action):
            return None

    class DummyMessage:
        text = '你没改啊'
        message_id = 9
        reply_to_message = None
        last_text = None
        async def reply_text(self, text, parse_mode=None):
            self.last_text = text

    class DummyChat:
        id = 123
        type = 'private'

    class DummyUser:
        id = 456
        username = 'moonlight'

    class DummyUpdate:
        message = DummyMessage()
        effective_chat = DummyChat()
        effective_user = DummyUser()

    bot.app = type('A', (), {'bot': DummyBot()})()
    state = bot.runtime_v2_loop.get_state('telegram:dm:456')
    state.task_status = 'running'
    state.current_goal = '修改 test.html 配色'

    async def fake_run_turn_typed(session_id, user_input):
        from app.runtime_v2.runtime_reply import RuntimeV2Reply, RuntimeV2TurnResult
        return RuntimeV2TurnResult(
            status='waiting_input',
            state=state,
            reply=RuntimeV2Reply(reply_text='我继续检查刚才那个文件。', delivery_kind='progress', status='waiting_input'),
        )

    monkeypatch.setattr(bot.runtime_v2_loop, 'run_turn_typed', fake_run_turn_typed)
    await bot.handle_message(DummyUpdate(), None)
    assert DummyUpdate.message.last_text == '我继续检查刚才那个文件。'
