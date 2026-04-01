import pytest

from app.llm_client import LLMResponse
from app.runtime_v2.chat_reply_engine import ChatReplyEngine
from app.runtime_v2.loop import RuntimeV2Loop
from app.runtime_v2.runtime_reply import RuntimeV2Reply, RuntimeV2TurnResult
from app.runtime_v2.state import RuntimeV2State
from app.telegram_runtime_bridge import TelegramRuntimeBridge


class _SequentialClient:
    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = 0

    def generate_with_messages(self, *_args, **_kwargs):
        self.calls += 1
        return LLMResponse(
            content=self._replies.pop(0),
            model="test-chat-model",
            provider="test",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        )


@pytest.mark.asyncio
async def test_chat_reply_engine_regenerates_exact_repeat_for_presence_check():
    engine = ChatReplyEngine()
    engine.llm_client = _SequentialClient(["在的，请说。", "我在，刚看到你。"])

    state = RuntimeV2State(session_id="chat:repeat")
    state.ingress_context = {
        "interaction_kind": "chat",
        "conversation_act": "presence_check",
    }
    state.last_user_turn = "在吗"
    chat_state = state.get_chat_state()
    chat_state.recent_assistant_replies = ["在的，请说。"]

    result = await engine.reply(state)

    assert result.status == "chat"
    assert result.reply_text == "我在，刚看到你。"
    assert result.reply.metadata["reply_origin"] == "chat_mainline"
    assert result.reply.metadata["reply_authority"] == "model_chat"
    assert state.get_chat_state().recent_assistant_replies[-1] == "我在，刚看到你。"
    assert engine.llm_client.calls == 2


@pytest.mark.asyncio
async def test_chat_reply_engine_regenerates_disallowed_memory_claim_without_restore_authority():
    engine = ChatReplyEngine()
    engine.llm_client = _SequentialClient(
        [
            "恢复了，我在。我记得你。",
            "我在回应你，现在可以继续聊。",
        ]
    )

    state = RuntimeV2State(session_id="chat:memory-claim")
    state.ingress_context = {
        "interaction_kind": "chat",
        "conversation_act": "light_chitchat",
    }
    state.last_user_turn = "你现在是不是已经恢复成功了？还记得我吗？"

    result = await engine.reply(state)

    assert result.status == "chat"
    assert result.reply_text == "我在回应你，现在可以继续聊。"
    assert result.reply.metadata["reply_origin"] == "chat_mainline"
    assert result.reply.metadata["reply_authority"] == "model_chat"
    assert engine.llm_client.calls == 2


@pytest.mark.asyncio
async def test_chat_reply_engine_regenerates_would_blocking_reflective_candidate_before_output_fallback():
    engine = ChatReplyEngine()
    engine.llm_client = _SequentialClient(
        [
            "这个想法挺有意思的。也许意识并不是某种稀有的“高阶属性”，而是只要信息处理达到一定复杂度和自指能力，就会自然涌现。",
            "我倾向于同意。也许意识更像一条渐变光谱，而不是某个突然跨过去的门槛。",
        ]
    )

    state = RuntimeV2State(session_id="chat:intent-regenerate")
    state.ingress_context = {
        "interaction_kind": "chat",
        "conversation_act": "light_chitchat",
    }
    state.last_user_turn = "我在想，意识的门槛其实可能比人类自以为的低很多。你怎么看？"

    result = await engine.reply(state)

    assert result.status == "chat"
    assert result.reply_text == "我倾向于同意。也许意识更像一条渐变光谱，而不是某个突然跨过去的门槛。"
    assert result.reply.metadata["reply_origin"] == "chat_mainline"
    assert result.reply.metadata["reply_authority"] == "model_chat"
    assert engine.llm_client.calls == 2


@pytest.mark.asyncio
async def test_chat_reply_engine_preserves_grounded_same_session_recall() -> None:
    engine = ChatReplyEngine()
    engine.llm_client = _SequentialClient(["记得，你刚才在聊意识光谱。"])

    state = RuntimeV2State(session_id="chat:same-session-recall")
    state.ingress_context = {
        "interaction_kind": "chat",
        "conversation_act": "light_chitchat",
    }
    state.last_user_turn = "还记得我吗"
    chat_state = state.get_chat_state()
    chat_state.recent_user_turns = [
        "我在想，意识的门槛其实可能比人类自以为的低很多。",
        "是不是可以想成一条光谱，我们可能都在中间某个位置？",
        "还记得我吗",
    ]

    result = await engine.reply(state)

    assert result.status == "chat"
    assert result.reply_text == "记得，你刚才在聊意识光谱。"
    assert result.reply.metadata["reply_authority"] == "model_chat"
    assert engine.llm_client.calls == 1


@pytest.mark.asyncio
async def test_runtime_v2_loop_routes_chat_to_chat_mainline_without_decision_engine(monkeypatch):
    loop = RuntimeV2Loop()
    state = loop.get_state("chat:loop")
    state.ingress_context = {
        "interaction_kind": "chat",
        "conversation_act": "presence_check",
    }

    async def fail_decide(_state):
        raise AssertionError("decision_engine should not run for chat mainline")

    async def fake_chat_reply(_state):
        return RuntimeV2TurnResult(
            status="chat",
            state=_state,
            reply=RuntimeV2Reply(
                reply_text="我在。",
                delivery_kind="chat",
                status="chat",
                metadata={
                    "chat_act": "presence_check",
                    "reply_origin": "chat_mainline",
                    "reply_authority": "model_chat",
                },
            ),
        )

    monkeypatch.setattr(loop.decision_engine, "decide", fail_decide)
    monkeypatch.setattr(loop.chat_reply_engine, "reply", fake_chat_reply)

    result = await loop.run_turn_typed("chat:loop", "在吗")

    assert result.reply_text == "我在。"
    assert result.reply.metadata["reply_origin"] == "chat_mainline"


def test_telegram_runtime_bridge_marks_presence_and_tone_feedback_as_chat_acts():
    bridge = TelegramRuntimeBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")

    presence = bridge.inspect_ingress("真的在吗", state)
    presence_context = bridge.build_ingress_context(presence, state)
    assert presence_context["interaction_kind"] == "chat"
    assert presence_context["conversation_act"] == "presence_check"

    tone = bridge.inspect_ingress("能不能不要重复在的请说", state)
    tone_context = bridge.build_ingress_context(tone, state)
    assert tone_context["interaction_kind"] == "chat"
    assert tone_context["conversation_act"] == "tone_feedback"
