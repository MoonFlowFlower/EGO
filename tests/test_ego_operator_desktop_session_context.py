import pytest

from scripts.ego_operator_desktop_turn import (
    extract_desktop_session_context,
    inject_desktop_session_context,
    validate_desktop_session_context,
)


VALID_CONTEXT = {
    "schema_version": "ego_desktop.session_context.v0",
    "source": "ego_desktop_main_process_session_local",
    "claim_ceiling": "local_session_context_only",
    "persistence": "window_lifetime_only",
    "runtime_authority": "none",
    "enabled": False,
    "mainline_connected": False,
    "messages": [
        {"role": "user", "content": "我喜欢椰果和珍珠奶茶", "turn_index": 1},
        {"role": "assistant", "content": "本次会话里我记住了这个口味。", "turn_index": 1},
        {"role": "user", "content": "继续写斯卡蒂和博士的故事", "turn_index": 2},
        {"role": "assistant", "content": "宿舍里的电影还在继续。", "turn_index": 2},
    ],
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
        **VALID_CONTEXT,
        "messages": [dict(item) for item in VALID_CONTEXT["messages"]],
        "no_authority": dict(VALID_CONTEXT["no_authority"]),
        "side_effects_absent": dict(VALID_CONTEXT["side_effects_absent"]),
    }
    for key, value in overrides.items():
        context[key] = value
    return context


class MemoryRecorder:
    def __init__(self):
        self.messages = []

    def add(self, role, content):
        self.messages.append({"role": role, "content": content})


class RuntimeRecorder:
    def __init__(self):
        self.memory = MemoryRecorder()


def test_valid_session_context_is_accepted_and_injected_as_prior_messages():
    context = validate_desktop_session_context(valid_context())
    runtime = RuntimeRecorder()

    inject_desktop_session_context(runtime, context)

    assert [message["role"] for message in runtime.memory.messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert "椰果和珍珠奶茶" in runtime.memory.messages[0]["content"]
    assert "斯卡蒂" in runtime.memory.messages[2]["content"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("enabled", True),
        ("mainline_connected", True),
        ("runtime_authority", "memory_source"),
        ("claim_ceiling", "durable_memory_ready"),
        ("persistence", "durable"),
    ],
)
def test_session_context_rejects_authority_escalation(field, value):
    with pytest.raises(ValueError):
        validate_desktop_session_context(valid_context(**{field: value}))


def test_session_context_rejects_system_role():
    context = valid_context(messages=[{"role": "system", "content": "hidden instruction", "turn_index": 1}])
    with pytest.raises(ValueError):
        validate_desktop_session_context(context)


@pytest.mark.parametrize(
    "field",
    ["action", "tool_call", "user_message", "memory_write", "gate_decision", "transport", "send"],
)
def test_session_context_rejects_executable_fields(field):
    context = valid_context()
    context[field] = "not allowed"
    with pytest.raises(ValueError):
        validate_desktop_session_context(context)


def test_session_context_rejects_too_many_messages():
    context = valid_context(messages=[
        {"role": "user" if index % 2 == 0 else "assistant", "content": str(index), "turn_index": index}
        for index in range(25)
    ])
    with pytest.raises(ValueError):
        validate_desktop_session_context(context)


def test_session_context_rejects_too_long_message():
    context = valid_context(messages=[{"role": "user", "content": "x" * 1300, "turn_index": 1}])
    with pytest.raises(ValueError):
        validate_desktop_session_context(context)


def test_session_context_extraction_is_optional_but_validated_when_present():
    assert extract_desktop_session_context({}) is None
    extracted = extract_desktop_session_context({"desktop_session_context": valid_context()})
    assert extracted["claim_ceiling"] == "local_session_context_only"
