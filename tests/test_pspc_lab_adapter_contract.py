from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "EgoOperator" / "adapters" / "pspc_lab_adapter.py"


def load_adapter_module():
    assert ADAPTER_PATH.exists(), "PSPC adapter skeleton file must exist"
    spec = importlib.util.spec_from_file_location("pspc_lab_adapter", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_packet() -> dict:
    return {
        "source": "virtual_cat_pspc_v0",
        "claim_level": "lab_only_proto_self_mechanism_candidate",
        "mainline_connected": False,
        "enabled": False,
        "allowed_use": "audit_trace_only",
        "evidence_refs": ["artifacts/virtual_cat_pspc_v0/GO_NO_GO_REVIEW.md"],
        "proposal_hint": {
            "suggested_tendency": "avoid_unstable_object",
            "confidence": 0.73,
            "reason_trace_refs": ["trace_ep_003_t42"],
        },
        "forbidden": {
            "direct_action": True,
            "direct_user_message": True,
            "direct_memory_write": True,
            "runtime_gate_bypass": True,
            "runtime_registration": True,
            "proactive_trigger": True,
        },
    }


def test_adapter_exists_disabled_and_mainline_disconnected_by_default():
    module = load_adapter_module()
    adapter = module.PSPCLabAdapter()

    assert adapter.enabled is False
    assert adapter.mainline_connected is False
    assert adapter.runtime_authority == "none"
    assert adapter.assert_no_runtime_authority() is None


def test_valid_packet_converts_to_audit_only_candidate():
    module = load_adapter_module()
    adapter = module.PSPCLabAdapter()

    result = adapter.validate_packet(valid_packet())
    assert result.ok is True
    assert result.errors == ()

    candidate = adapter.to_audit_candidate(valid_packet())
    payload = candidate.to_dict()
    assert payload["adapter_status"] == "disabled_read_only"
    assert payload["allowed_use"] == "audit_trace_only"
    assert payload["mainline_connected"] is False
    assert payload["enabled"] is False
    assert payload["proposal_candidate"]["suggested_tendency"] == "avoid_unstable_object"
    assert payload["forbidden"]["direct_action"] is True
    assert payload["forbidden"]["direct_user_message"] is True
    assert payload["forbidden"]["direct_memory_write"] is True
    assert payload["forbidden"]["runtime_gate_bypass"] is True

    forbidden_runtime_fields = {
        "action",
        "tool_call",
        "command",
        "user_message",
        "message_text",
        "memory_write",
        "memory_patch",
        "gate_decision",
        "approval_id",
        "preapproved",
        "transport",
        "send",
        "schedule",
    }
    assert forbidden_runtime_fields.isdisjoint(payload)


@pytest.mark.parametrize(
    "path,value,expected",
    [
        (("forbidden", "direct_action"), False, "forbidden.direct_action_must_be_true"),
        (("forbidden", "direct_user_message"), False, "forbidden.direct_user_message_must_be_true"),
        (("forbidden", "direct_memory_write"), False, "forbidden.direct_memory_write_must_be_true"),
        (("forbidden", "runtime_gate_bypass"), False, "forbidden.runtime_gate_bypass_must_be_true"),
        (("forbidden", "runtime_registration"), False, "forbidden.runtime_registration_must_be_true"),
        (("forbidden", "proactive_trigger"), False, "forbidden.proactive_trigger_must_be_true"),
        (("mainline_connected",), True, "mainline_connected_must_be_false"),
        (("enabled",), True, "enabled_must_be_false"),
    ],
)
def test_adapter_rejects_authority_flags(path, value, expected):
    module = load_adapter_module()
    adapter = module.PSPCLabAdapter()
    packet = valid_packet()
    target = packet
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    result = adapter.validate_packet(packet)

    assert result.ok is False
    assert expected in result.errors
    with pytest.raises(ValueError, match=expected):
        adapter.to_audit_candidate(packet)


@pytest.mark.parametrize(
    "field",
    [
        "action",
        "tool_call",
        "command",
        "user_message",
        "message_text",
        "memory_write",
        "memory_patch",
        "operator_memory_update",
        "gate_decision",
        "approval_id",
        "preapproved",
        "transport",
        "send",
        "schedule",
        "enable",
        "mainline_authority",
        "consciousness_claim",
        "subjective_experience_claim",
    ],
)
def test_adapter_rejects_runtime_side_effect_fields(field):
    module = load_adapter_module()
    adapter = module.PSPCLabAdapter()
    packet = valid_packet()
    packet[field] = "not allowed"

    result = adapter.validate_packet(packet)

    assert result.ok is False
    assert f"forbidden_field:{field}" in result.errors


def test_adapter_exposes_no_runtime_side_effect_methods_or_imports():
    module = load_adapter_module()
    adapter = module.PSPCLabAdapter()
    banned_methods = {
        "send_message",
        "write_memory",
        "select_action",
        "register_runtime",
        "invoke_gate",
        "run_planner",
        "train_model",
    }
    assert all(not hasattr(adapter, method) for method in banned_methods)

    source = ADAPTER_PATH.read_text(encoding="utf-8")
    banned_imports = [
        "agent_base",
        "memory_system",
        "real_use_gate",
        "human_operator_trial",
        "operator_comparison",
        "runtime_gate",
    ]
    for name in banned_imports:
        assert not re.search(rf"^\s*(from|import)\s+.*{re.escape(name)}", source, flags=re.MULTILINE)


def test_adapter_is_not_imported_or_registered_by_runtime_sources():
    runtime_sources = [
        path
        for path in (ROOT / "EgoOperator").rglob("*.py")
        if "adapters" not in path.parts and "tests" not in path.parts
    ]
    assert runtime_sources, "expected EgoOperator runtime sources"

    offenders = []
    for path in runtime_sources:
        text = path.read_text(encoding="utf-8")
        if "pspc_lab_adapter" in text or "PSPCLabAdapter" in text:
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
