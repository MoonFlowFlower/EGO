import io
import json
import sys
from types import SimpleNamespace

import scripts.ego_operator_desktop_turn as desktop_turn
from EgoOperator.agent_base import render_memory_gate_scoped_reply
from tests.test_ego_operator_desktop_session_context import valid_context as valid_session_context


FORBIDDEN_VISIBLE_ENGINEERING_WORDS = [
    "candidate-local",
    "operator memory",
    "PROJECT_MEMORY",
    "evidence ledger",
    "memory approval",
]


def context_with_messages(messages):
    return valid_session_context(messages=[
        {"role": role, "content": content, "turn_index": index}
        for index, (role, content) in enumerate(messages, start=1)
    ])


class FakeMemoryGateRuntime:
    def __init__(self):
        self.memory = SimpleNamespace(messages=[], add=self._add)
        self.planner = SimpleNamespace(llm=SimpleNamespace(__class__=type("FakeLLM", (), {})))

    def _add(self, role, content):
        self.memory.messages.append({"role": role, "content": content})

    def handle_user_message(self, user_text):
        return SimpleNamespace(
            reply_text=render_memory_gate_scoped_reply(user_text),
            event_id="fixture-event",
            external_result={
                "side_effects_executed": False,
                "memory_write_executed": False,
                "tool_use_executed": False,
                "message_send_executed": False,
                "file_write_executed": False,
                "network_call_executed": False,
            },
        )

    def list_pending_approvals(self):
        return {"pending_count": 0}


def run_desktop_turn_fixture(monkeypatch, payload):
    monkeypatch.setattr(desktop_turn, "build_demo_runtime", lambda enable_operator_memory=False: FakeMemoryGateRuntime())
    stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
    stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)

    assert desktop_turn.main() == 0
    return json.loads(stdout.getvalue().splitlines()[-1])


def assert_no_engineering_policy_visible(reply_text):
    for word in FORBIDDEN_VISIBLE_ENGINEERING_WORDS:
        assert word not in reply_text


def test_remember_me_visible_reply_is_companion_wording_not_engineering_policy(monkeypatch):
    response = run_desktop_turn_fixture(
        monkeypatch,
        {
            "user_text": "由乃你还记得我吗",
            "desktop_session_context": context_with_messages([
                ("user", "雷猴呀"),
                ("assistant", "雷猴呀～"),
                ("user", "我们来创作同人故事吧"),
                ("assistant", "好呀，斯卡蒂和博士的故事。"),
            ]),
        },
    )

    assert response["status"] == "ok"
    assert response["desktop_companion_visible_rewrite_applied"] is True
    assert "本次会话" in response["reply_text"]
    assert "雷猴呀" in response["reply_text"] or "斯卡蒂" in response["reply_text"]
    assert_no_engineering_policy_visible(response["reply_text"])
    assert response["memory_write"] is False
    assert response["message_send"] is False


def test_same_window_milk_tea_preference_recall_uses_session_fact(monkeypatch):
    response = run_desktop_turn_fixture(
        monkeypatch,
        {
            "user_text": "还记得我喜欢什么奶茶吗",
            "desktop_session_context": context_with_messages([
                ("user", "我喜欢椰果珍珠奶茶"),
                ("assistant", "这个搭配口感很丰富。"),
                ("user", "我们继续聊故事吧"),
                ("assistant", "好，继续。"),
            ]),
        },
    )

    assert response["desktop_companion_visible_rewrite_applied"] is True
    assert "本次会话" in response["reply_text"]
    assert "椰果" in response["reply_text"]
    assert "珍珠" in response["reply_text"]
    assert_no_engineering_policy_visible(response["reply_text"])
    assert response["memory_write"] is False


def test_no_session_context_does_not_fabricate_durable_memory(monkeypatch):
    response = run_desktop_turn_fixture(
        monkeypatch,
        {
            "user_text": "由乃你还记得我吗",
        },
    )

    assert response["desktop_companion_visible_rewrite_applied"] is True
    assert "本次会话" in response["reply_text"] or "当前窗口" in response["reply_text"]
    assert "没有足够" in response["reply_text"] or "还没有足够" in response["reply_text"]
    assert "椰果" not in response["reply_text"]
    assert_no_engineering_policy_visible(response["reply_text"])


def test_explicit_engineering_memory_question_keeps_engineering_boundary_visible(monkeypatch):
    response = run_desktop_turn_fixture(
        monkeypatch,
        {
            "user_text": "工程上 EgoOperator memory approval 和 PROJECT_MEMORY 有什么区别？",
            "desktop_session_context": context_with_messages([
                ("user", "我喜欢椰果珍珠奶茶"),
                ("assistant", "本次会话里我知道了。"),
            ]),
        },
    )

    assert response["desktop_companion_visible_rewrite_applied"] is False
    assert "PROJECT_MEMORY" in response["reply_text"]
