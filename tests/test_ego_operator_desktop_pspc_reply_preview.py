import pytest

from scripts.ego_operator_desktop_turn import (
    extract_pspc_reply_preview_context,
    render_pspc_reply_preview_system_context,
    validate_pspc_reply_preview_context,
)


VALID_CONTEXT = {
    "schema_version": "ego_desktop.pspc_reply_preview_context.v0",
    "source": "ego_desktop_session_local_pspc_reply_preview",
    "claim_ceiling": "local_reply_preview_semantic_signal_extractor_only",
    "allowed_use": "ego_desktop_local_reply_preview_only",
    "runtime_authority": "none",
    "enabled": False,
    "mainline_connected": False,
    "profile": {
        "style": "warm_approach",
        "confidence": 0.82,
        "basis": "gentle interaction history dominates this session",
        "reason_trace_refs": ["session_turn_001:gentle", "session_turn_002:gentle"],
    },
    "forbidden": {
        "direct_action": True,
        "direct_user_message": True,
        "direct_memory_write": True,
        "runtime_gate_bypass": True,
        "runtime_registration": True,
        "proactive_trigger": True,
        "planner_execution": True,
        "model_execution": True,
        "training": True,
    },
    "no_authority": {
        "direct_action_allowed": False,
        "direct_user_message_allowed": False,
        "direct_memory_write_allowed": False,
        "runtime_gate_bypass_allowed": False,
        "runtime_registration_allowed": False,
        "proactive_trigger_allowed": False,
        "planner_execution_allowed": False,
        "model_execution_allowed": False,
        "training_allowed": False,
    },
    "real_memory_written": False,
    "runtime_gate_invoked": False,
    "proactive_triggered": False,
}


def valid_context(**overrides):
    context = {
        **VALID_CONTEXT,
        "profile": dict(VALID_CONTEXT["profile"]),
        "forbidden": dict(VALID_CONTEXT["forbidden"]),
        "no_authority": dict(VALID_CONTEXT["no_authority"]),
    }
    for key, value in overrides.items():
        context[key] = value
    return context


def test_valid_preview_context_renders_local_style_hint_only():
    context = validate_pspc_reply_preview_context(valid_context())
    rendered = render_pspc_reply_preview_system_context(context)

    assert context["profile"]["style"] == "warm_approach"
    assert "PSPC local reply preview" in rendered
    assert "warm_approach" in rendered
    assert "local style hint only" in rendered
    assert "Do not claim consciousness" in rendered
    assert "Do not write memory" in rendered


@pytest.mark.parametrize(
    "field,value",
    [
        ("enabled", True),
        ("mainline_connected", True),
        ("runtime_authority", "proposal_source"),
        ("claim_ceiling", "runtime_integration_ready"),
    ],
)
def test_preview_context_rejects_authority_escalation(field, value):
    with pytest.raises(ValueError):
        validate_pspc_reply_preview_context(valid_context(**{field: value}))


@pytest.mark.parametrize(
    "field",
    [
        "direct_action",
        "direct_user_message",
        "direct_memory_write",
        "runtime_gate_bypass",
        "runtime_registration",
        "proactive_trigger",
    ],
)
def test_preview_context_rejects_missing_forbidden_flags(field):
    context = valid_context()
    context["forbidden"].pop(field)
    with pytest.raises(ValueError):
        validate_pspc_reply_preview_context(context)


@pytest.mark.parametrize(
    "field",
    ["action", "tool_call", "user_message", "memory_write", "gate_decision", "transport", "send"],
)
def test_preview_context_rejects_executable_fields(field):
    context = valid_context()
    context[field] = "not allowed"
    with pytest.raises(ValueError):
        validate_pspc_reply_preview_context(context)


def test_preview_context_extracted_only_when_mode_is_explicit():
    assert extract_pspc_reply_preview_context({"pspc_reply_preview_context": valid_context()}) is None
    assert extract_pspc_reply_preview_context({"pspc_reply_preview_mode": False, "pspc_reply_preview_context": valid_context()}) is None

    extracted = extract_pspc_reply_preview_context(
        {"pspc_reply_preview_mode": True, "pspc_reply_preview_context": valid_context()}
    )
    assert extracted["profile"]["style"] == "warm_approach"
