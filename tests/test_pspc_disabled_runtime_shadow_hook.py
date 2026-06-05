from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "EgoOperator" / "adapters" / "pspc_disabled_runtime_shadow_hook.py"
RUNNER_PATH = ROOT / "scripts" / "run_pspc_disabled_runtime_shadow_hook.py"


def load_hook_module():
    assert HOOK_PATH.exists(), "default-off runtime shadow hook must exist"
    spec = importlib.util.spec_from_file_location("pspc_disabled_runtime_shadow_hook", HOOK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_runner_module():
    assert RUNNER_PATH.exists(), "default-off runtime shadow hook runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_disabled_runtime_shadow_hook", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_shadow_context() -> dict:
    return {
        "source": "recorded_fixture",
        "runtime_connected": False,
        "hook_registered": False,
        "enabled": False,
        "mainline_connected": False,
        "allowed_use": "shadow_audit_only",
        "claim_ceiling": "lab_only_proto_self_mechanism_candidate / recorded_trace_replay_no_diff_only",
        "operator_trace_refs": ["trace_ep_003_t42"],
        "audit_candidate": {
            "source": "virtual_cat_pspc_v0",
            "claim_level": "lab_only_proto_self_mechanism_candidate",
            "enabled": False,
            "mainline_connected": False,
            "runtime_authority": "none",
            "non_executable": True,
            "suggested_tendency": "avoid_unstable_object",
            "confidence": 0.73,
            "reason_trace_refs": ["trace_ep_003_t42"],
            "evidence_refs": ["artifacts/virtual_cat_pspc_v0/summary.json"],
        },
        "side_effects": {
            "runtime_registered": False,
            "user_response_mutated": False,
            "memory_written": False,
            "gate_invoked": False,
            "approval_mutated": False,
            "transport_called": False,
            "proactive_trigger": False,
            "planner_called": False,
            "training_called": False,
            "model_executed": False,
        },
    }


def test_hook_defaults_and_public_methods_only():
    module = load_hook_module()
    hook = module.PSPCDisabledRuntimeShadowHook()

    assert hook.enabled is False
    assert hook.mainline_connected is False
    assert hook.runtime_authority == "none"
    assert hook.audit_only is True
    assert hook.read_only is True
    assert hook.non_executable is True
    hook.assert_no_runtime_authority()

    public_callables = sorted(
        name
        for name in dir(hook)
        if not name.startswith("_") and callable(getattr(hook, name))
    )
    assert public_callables == [
        "assert_no_runtime_authority",
        "render_shadow_artifact",
        "validate_shadow_context",
    ]


def test_hook_assertion_rejects_enabled_or_mainline_connected():
    module = load_hook_module()

    enabled = module.PSPCDisabledRuntimeShadowHook()
    enabled.enabled = True
    with pytest.raises(RuntimeError, match="enabled_must_be_false"):
        enabled.assert_no_runtime_authority()

    connected = module.PSPCDisabledRuntimeShadowHook()
    connected.mainline_connected = True
    with pytest.raises(RuntimeError, match="mainline_connected_must_be_false"):
        connected.assert_no_runtime_authority()


def test_hook_validates_and_rejects_runtime_authority_fields():
    module = load_hook_module()
    hook = module.PSPCDisabledRuntimeShadowHook()
    context = valid_shadow_context()

    assert hook.validate_shadow_context(context) == {"ok": True, "errors": []}

    bad = dict(context)
    bad["runtime_connected"] = True
    assert "shadow_context.runtime_connected_must_be_false" in hook.validate_shadow_context(bad)["errors"]

    bad = dict(context)
    bad["audit_candidate"] = dict(context["audit_candidate"])
    bad["audit_candidate"]["gate_decision"] = "allow"
    assert any("audit_candidate_has_runtime_authority_fields" in error for error in hook.validate_shadow_context(bad)["errors"])

    bad = dict(context)
    bad["side_effects"] = dict(context["side_effects"])
    bad["side_effects"]["memory_written"] = True
    assert "side_effects_must_all_be_false" in hook.validate_shadow_context(bad)["errors"]


def test_hook_renders_audit_only_artifact():
    module = load_hook_module()
    hook = module.PSPCDisabledRuntimeShadowHook()

    result = hook.render_shadow_artifact(valid_shadow_context())

    assert result["source"] == "pspc_disabled_runtime_shadow_hook_v0"
    assert result["enabled"] is False
    assert result["mainline_connected"] is False
    assert result["runtime_authority"] == "none"
    assert result["audit_only"] is True
    assert result["read_only"] is True
    assert result["non_executable"] is True
    assert result["audit_observation"]["suggested_tendency"] == "avoid_unstable_object"
    assert result["audit_observation"]["can_drive_runtime"] is False
    assert result["audit_observation"]["can_change_user_response"] is False
    assert result["audit_observation"]["can_write_memory"] is False
    assert result["audit_observation"]["can_invoke_gate"] is False
    assert all(value is False for value in result["side_effects"].values())
    assert result["forbidden_mutations"]["runtime_registry"] is True
    assert result["forbidden_mutations"]["memory"] is True
    assert result["forbidden_mutations"]["gate_decision"] is True


def test_runner_writes_default_off_hook_artifacts_only(tmp_path):
    runner = load_runner_module()

    result = runner.run_review(ROOT, tmp_path)

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / default_off_hook_module_only"
    assert result["hook_artifact"]["enabled"] is False
    assert result["hook_artifact"]["mainline_connected"] is False
    assert result["hook_artifact"]["runtime_authority"] == "none"
    assert result["runtime_scan"]["offenders"] == []
    assert result["checks"]["side_effects_absent"] is True
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "DEFAULT_OFF_HOOK_REPORT.md",
        "default_off_hook_result.json",
    ]
    report = (tmp_path / "DEFAULT_OFF_HOOK_REPORT.md").read_text(encoding="utf-8")
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Rollback" in report


def test_hook_and_runner_have_no_runtime_imports_or_side_effect_calls():
    source = "\n".join(path.read_text(encoding="utf-8") for path in [HOOK_PATH, RUNNER_PATH] if path.exists())
    banned = [
        "EgoOperator.agent_base",
        "agent_base",
        "memory_system",
        "real_use_gate",
        "human_operator_trial",
        "operator_comparison",
        "runtime_gate",
        "send_message",
        "write_memory",
        "select_action",
        "register_runtime",
        "invoke_gate",
        "run_planner",
        "train_model",
    ]
    for item in banned:
        assert not re.search(rf"^\s*(from|import)\s+.*{re.escape(item)}", source, flags=re.MULTILINE)
        assert not re.search(rf"\b{re.escape(item)}\s*\(", source)


def test_active_runtime_sources_do_not_import_or_register_hook():
    runtime_sources = [
        path
        for path in (ROOT / "EgoOperator").rglob("*.py")
        if "adapters" not in path.parts and "tests" not in path.parts
    ]
    assert runtime_sources
    offenders = []
    markers = ["pspc_disabled_runtime_shadow_hook", "PSPCDisabledRuntimeShadowHook"]
    for path in runtime_sources:
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in markers):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []
