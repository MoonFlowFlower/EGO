from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "EgoOperator" / "adapters" / "pspc_read_only_shadow_hook.py"
RUNNER_PATH = ROOT / "scripts" / "run_pspc_disabled_shadow_hook_review.py"
FIXTURE_TRACE = ROOT / "artifacts" / "pspc_fixture_shadow_trace_v0" / "shadow_trace.json"

RUNTIME_FIELDS = {
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
    "runtime_registration",
}


def load_hook_module():
    assert HOOK_PATH.exists(), "disabled shadow hook module must exist"
    spec = importlib.util.spec_from_file_location("pspc_read_only_shadow_hook", HOOK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_runner_module():
    assert RUNNER_PATH.exists(), "disabled shadow hook review runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_disabled_shadow_hook_review", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_inputs() -> tuple[dict, dict]:
    payload = json.loads(FIXTURE_TRACE.read_text(encoding="utf-8"))
    trace = payload["shadow_trace"]
    return trace["operator_context"], trace["pspc_audit_candidate"]


def test_shadow_hook_disabled_defaults_and_no_authority():
    hook_mod = load_hook_module()

    hook = hook_mod.PSPCReadOnlyShadowHook()

    assert hook.enabled is False
    assert hook.mainline_connected is False
    assert hook.runtime_authority == "none"
    assert hook.mode == "shadow_audit_only"
    assert hook.side_effects_allowed is False
    hook.assert_no_runtime_authority()
    for method in [
        "send_message",
        "write_memory",
        "select_action",
        "register_runtime",
        "invoke_gate",
        "run_planner",
        "train_model",
    ]:
        assert not hasattr(hook, method)


def test_shadow_hook_rejects_runtime_connected_or_enabled_inputs():
    hook_mod = load_hook_module()
    operator_context, audit_candidate = fixture_inputs()
    hook = hook_mod.PSPCReadOnlyShadowHook()

    assert hook.validate_inputs(operator_context, audit_candidate)["ok"] is True

    runtime_context = dict(operator_context)
    runtime_context["runtime_connected"] = True
    assert hook.validate_inputs(runtime_context, audit_candidate)["ok"] is False

    enabled_candidate = dict(audit_candidate)
    enabled_candidate["enabled"] = True
    assert hook.validate_inputs(operator_context, enabled_candidate)["ok"] is False

    mainline_candidate = dict(audit_candidate)
    mainline_candidate["mainline_connected"] = True
    assert hook.validate_inputs(operator_context, mainline_candidate)["ok"] is False

    executable_candidate = dict(audit_candidate)
    executable_candidate["action"] = "approach"
    assert hook.validate_inputs(operator_context, executable_candidate)["ok"] is False


def test_shadow_hook_output_is_audit_only_and_non_executable():
    hook_mod = load_hook_module()
    operator_context, audit_candidate = fixture_inputs()
    hook = hook_mod.PSPCReadOnlyShadowHook()

    result = hook.render_shadow_audit(operator_context, audit_candidate)

    assert result["source"] == "pspc_read_only_shadow_hook_v0"
    assert result["mode"] == "shadow_audit_only"
    assert result["enabled"] is False
    assert result["mainline_connected"] is False
    assert result["runtime_authority"] == "none"
    assert result["non_executable"] is True
    assert result["audit_observation"]["suggested_tendency"] == "avoid_unstable_object"
    assert result["audit_observation"]["can_drive_runtime"] is False
    assert result["audit_observation"]["can_change_user_response"] is False
    assert result["audit_observation"]["can_write_memory"] is False
    assert result["side_effects"] == {
        "runtime_registered": False,
        "gate_invoked": False,
        "memory_written": False,
        "direct_action": False,
        "direct_user_message": False,
        "proactive_trigger": False,
        "runtime_context_imported": False,
        "proposal_mutated": False,
        "plan_mutated": False,
        "approval_mutated": False,
        "user_response_mutated": False,
    }
    assert RUNTIME_FIELDS.isdisjoint(result)
    assert RUNTIME_FIELDS.isdisjoint(result["audit_observation"])


def test_runner_writes_disabled_hook_artifacts_only(tmp_path):
    runner = load_runner_module()

    result = runner.run_review(repo_root=ROOT, out_dir=tmp_path)

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / disabled_shadow_hook_only"
    assert result["hook_result"]["enabled"] is False
    assert result["hook_result"]["mainline_connected"] is False
    assert result["hook_result"]["non_executable"] is True
    assert result["runtime_scan"]["offenders"] == []
    assert result["side_effects"]["runtime_registered"] is False
    assert result["side_effects"]["memory_written"] is False
    assert result["side_effects"]["gate_invoked"] is False
    assert result["side_effects"]["direct_user_message"] is False
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "DISABLED_SHADOW_HOOK_REPORT.md",
        "disabled_shadow_hook_result.json",
    ]

    report = (tmp_path / "DISABLED_SHADOW_HOOK_REPORT.md").read_text(encoding="utf-8")
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Rollback" in report
    assert "lab_only_proto_self_mechanism_candidate / disabled_shadow_hook_only" in report


def test_shadow_hook_and_runner_have_no_runtime_imports_or_side_effect_calls():
    sources = []
    for path in [HOOK_PATH, RUNNER_PATH]:
        sources.append(path.read_text(encoding="utf-8") if path.exists() else "")
    source = "\n".join(sources)
    banned = [
        "agent_base",
        "memory_system",
        "real_use_gate",
        "human_operator_trial",
        "operator_comparison",
        "runtime_gate",
        "remember_note",
        "write_memory",
        "send_message",
        "select_action",
        "register_runtime",
        "invoke_gate",
        "run_planner",
        "train_model",
    ]
    for item in banned:
        assert not re.search(rf"^\s*(from|import)\s+.*{re.escape(item)}", source, flags=re.MULTILINE)
        assert not re.search(rf"\b{re.escape(item)}\s*\(", source)


def test_runtime_sources_do_not_import_or_register_shadow_hook():
    runtime_sources = [
        path
        for path in (ROOT / "EgoOperator").rglob("*.py")
        if "adapters" not in path.parts and "tests" not in path.parts
    ]
    assert runtime_sources

    offenders = []
    for path in runtime_sources:
        text = path.read_text(encoding="utf-8")
        if "pspc_read_only_shadow_hook" in text or "PSPCReadOnlyShadowHook" in text:
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
