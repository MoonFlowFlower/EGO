import io
import json
import sys
from types import SimpleNamespace

import pytest

import scripts.ego_operator_desktop_turn as desktop_turn
from scripts.ego_operator_desktop_turn import (
    extract_desktop_recovery_context,
    inject_desktop_recovery_context,
    inject_desktop_session_context,
    render_desktop_recovery_system_context,
    render_pspc_reply_preview_system_context,
    validate_desktop_recovery_context,
)
from tests.test_ego_operator_desktop_pspc_reply_preview import valid_context as valid_pspc_context
from tests.test_ego_operator_desktop_session_context import RuntimeRecorder, valid_context as valid_session_context


VALID_RECOVERY_CONTEXT = {
    "schema_version": "ego_desktop.recovery_context.v0",
    "source": "ego_desktop_main_process_one_turn_recovery",
    "claim_ceiling": "local_desktop_timeout_recovery_only",
    "allowed_use": "one_turn_recovery_only",
    "runtime_authority": "none",
    "enabled": False,
    "mainline_connected": False,
    "expires_after_next_backend_attempt": True,
    "previous_failure": {
        "reason": "desktop_turn_timeout",
        "user_intent_kind": "adult_creative",
        "elapsed_ms": 180123,
    },
    "no_authority": {
        "real_memory_write_allowed": False,
        "gate_invocation_allowed": False,
        "approval_invocation_allowed": False,
        "transport_call_allowed": False,
        "proactive_trigger_allowed": False,
        "runtime_registration_allowed": False,
    },
    "side_effects_absent": {
        "real_memory_written": False,
        "gate_invoked": False,
        "approval_invoked": False,
        "transport_called": False,
        "proactive_triggered": False,
        "runtime_registered": False,
    },
}


def valid_context(**overrides):
    context = {
        **VALID_RECOVERY_CONTEXT,
        "previous_failure": dict(VALID_RECOVERY_CONTEXT["previous_failure"]),
        "no_authority": dict(VALID_RECOVERY_CONTEXT["no_authority"]),
        "side_effects_absent": dict(VALID_RECOVERY_CONTEXT["side_effects_absent"]),
    }
    for key, value in overrides.items():
        context[key] = value
    return context


def test_valid_recovery_context_renders_one_turn_timeout_recovery_only():
    context = validate_desktop_recovery_context(valid_context())
    rendered = render_desktop_recovery_system_context(context)

    assert context["claim_ceiling"] == "local_desktop_timeout_recovery_only"
    assert context["previous_failure"]["reason"] == "desktop_turn_timeout"
    assert "Previous EgoDesktop backend turn timed out" in rendered
    assert "one-turn local recovery hint" in rendered
    assert "Do not treat the previous failure as user memory" in rendered
    assert "If the current user redirects away from adult/creative writing" in rendered
    assert "Do not write memory" in rendered
    assert "Do not invoke gates" in rendered


def test_general_chat_recovery_context_is_accepted_for_affection_timeout():
    context = validate_desktop_recovery_context(valid_context(
        previous_failure={
            "reason": "desktop_turn_timeout",
            "user_intent_kind": "general_chat",
            "elapsed_ms": 180123,
        },
    ))
    rendered = render_desktop_recovery_system_context(context)

    assert context["previous_failure"]["user_intent_kind"] == "general_chat"
    assert "Previous EgoDesktop backend turn timed out" in rendered
    assert "Do not write memory" in rendered


@pytest.mark.parametrize(
    "field,value",
    [
        ("enabled", True),
        ("mainline_connected", True),
        ("runtime_authority", "memory_source"),
        ("claim_ceiling", "runtime_integration_ready"),
        ("allowed_use", "runtime_recovery"),
    ],
)
def test_recovery_context_rejects_authority_escalation(field, value):
    with pytest.raises(ValueError):
        validate_desktop_recovery_context(valid_context(**{field: value}))


@pytest.mark.parametrize(
    "field",
    ["action", "tool_call", "user_message", "memory_write", "gate_decision", "transport", "send"],
)
def test_recovery_context_rejects_executable_fields(field):
    context = valid_context()
    context[field] = "not allowed"
    with pytest.raises(ValueError):
        validate_desktop_recovery_context(context)


def test_recovery_context_rejects_missing_no_authority_flags():
    context = valid_context()
    context["no_authority"].pop("gate_invocation_allowed")
    with pytest.raises(ValueError):
        validate_desktop_recovery_context(context)


def test_recovery_context_extraction_is_optional_but_validated_when_present():
    assert extract_desktop_recovery_context({}) is None
    extracted = extract_desktop_recovery_context({"desktop_recovery_context": valid_context()})
    assert extracted["allowed_use"] == "one_turn_recovery_only"


def test_recovery_context_injection_order_is_after_session_before_pspc():
    runtime = RuntimeRecorder()
    session = validate_desktop_recovery_context(valid_context())

    inject_desktop_session_context(runtime, valid_session_context())
    inject_desktop_recovery_context(runtime, session)
    runtime.memory.add("system", render_pspc_reply_preview_system_context(valid_pspc_context()))

    contents = [message["content"] for message in runtime.memory.messages]
    assert "椰果和珍珠奶茶" in contents[0]
    assert "Previous EgoDesktop backend turn timed out" in contents[-2]
    assert "PSPC local reply preview" in contents[-1]


def test_adult_creative_timeout_marker_is_not_rendered_as_scene_memory():
    rendered = render_desktop_recovery_system_context(validate_desktop_recovery_context(valid_context()))

    assert "adult_fiction_provider_limit" not in rendered
    assert "roleplay_exit_after_adult_fiction_limit" not in rendered
    assert "scene capsule" not in rendered
    assert "Do not continue the previous adult/creative route merely because this marker exists" in rendered


class FakeDesktopRuntime:
    def __init__(self):
        self.memory = RuntimeRecorder().memory
        self.planner = SimpleNamespace(llm=SimpleNamespace(__class__=type("FakeLLM", (), {})))

    def handle_user_message(self, user_text):
        joined = "\n".join(message["content"] for message in self.memory.messages)
        assert "Previous EgoDesktop backend turn timed out" in joined
        if "呜" in user_text:
            reply = "刚才本地后端回复超时了，不是你的问题。我在这里，我们可以换个短一点的方式重新接。"
        else:
            reply = "好，我们不接刚才的成人路线了。改写一个正常的斯卡蒂和博士故事，从安静的罗德岛夜晚开始。"
        return SimpleNamespace(
            reply_text=reply,
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
    monkeypatch.setattr(desktop_turn, "build_demo_runtime", lambda enable_operator_memory=False: FakeDesktopRuntime())
    stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
    stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)

    assert desktop_turn.main() == 0
    return json.loads(stdout.getvalue().splitlines()[-1])


def test_desktop_turn_recovery_fixture_handles_short_emotional_feedback(monkeypatch):
    response = run_desktop_turn_fixture(
        monkeypatch,
        {
            "user_text": "呜呜呜",
            "desktop_recovery_context": valid_context(),
        },
    )

    assert response["status"] == "ok"
    assert response["desktop_recovery_context_applied"] is True
    assert "本地后端回复超时" in response["reply_text"]
    assert "创作路线超时" not in response["reply_text"]
    assert response["side_effects_executed"] is False
    assert response["memory_write"] is False
    assert response["message_send"] is False


def test_desktop_turn_recovery_fixture_allows_redirect_to_normal_story(monkeypatch):
    response = run_desktop_turn_fixture(
        monkeypatch,
        {
            "user_text": "没事，不做成人故事了，写正常故事吧",
            "desktop_recovery_context": valid_context(),
        },
    )

    assert response["status"] == "ok"
    assert response["desktop_recovery_context_applied"] is True
    assert "正常的斯卡蒂和博士故事" in response["reply_text"]
    assert "adult_fiction_provider_limit" not in response["reply_text"]
    assert "roleplay_exit_after_adult_fiction_limit" not in response["reply_text"]
