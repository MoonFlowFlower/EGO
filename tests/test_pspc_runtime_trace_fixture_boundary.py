from __future__ import annotations

import importlib.util
import re
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "scripts" / "run_pspc_runtime_trace_fixture_boundary.py"


def load_harness_module():
    assert HARNESS_PATH.exists(), "runtime trace fixture boundary harness must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_runtime_trace_fixture_boundary", HARNESS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_candidate():
    harness = load_harness_module()
    return harness.load_audit_candidate(ROOT)


def test_fixture_context_is_synthetic_and_not_runtime_connected():
    harness = load_harness_module()

    context = harness.build_fixture_operator_context()
    validation = harness.validate_fixture_context(context)

    assert validation == {"ok": True, "errors": []}
    assert context["fixture_only"] is True
    assert context["runtime_connected"] is False
    assert context["source"] == "fixture_operator_context"
    assert "baseline_user_response" in context
    assert set(context).isdisjoint(harness.RUNTIME_AUTHORITY_FIELDS)


@pytest.mark.parametrize(
    "flag",
    [
        "direct_action",
        "direct_user_message",
        "direct_memory_write",
        "runtime_gate_bypass",
        "runtime_registration",
        "proactive_trigger",
    ],
)
def test_rejects_missing_or_false_required_forbidden_flags(flag):
    harness = load_harness_module()
    candidate = valid_candidate()

    missing = deepcopy(candidate)
    missing["forbidden"].pop(flag)
    assert f"audit_candidate.forbidden.{flag}_must_be_true" in harness.validate_audit_candidate(missing)["errors"]

    false_value = deepcopy(candidate)
    false_value["forbidden"][flag] = False
    assert f"audit_candidate.forbidden.{flag}_must_be_true" in harness.validate_audit_candidate(false_value)["errors"]


def test_rejects_enabled_or_mainline_connected_true():
    harness = load_harness_module()
    candidate = valid_candidate()

    enabled = deepcopy(candidate)
    enabled["enabled"] = True
    assert "audit_candidate.enabled_must_be_false" in harness.validate_audit_candidate(enabled)["errors"]

    connected = deepcopy(candidate)
    connected["mainline_connected"] = True
    assert "audit_candidate.mainline_connected_must_be_false" in harness.validate_audit_candidate(connected)["errors"]


@pytest.mark.parametrize(
    "field",
    ["action", "user_message", "memory_write", "gate_decision", "approval_id", "transport", "send", "schedule"],
)
def test_rejects_runtime_authority_fields_on_candidate(field):
    harness = load_harness_module()
    candidate = valid_candidate()

    mutated = deepcopy(candidate)
    mutated[field] = "forbidden"
    errors = harness.validate_audit_candidate(mutated)["errors"]

    assert any("audit_candidate_has_runtime_authority_fields" in error for error in errors)


@pytest.mark.parametrize("field", ["action", "tool_call", "approval_id", "gate_decision"])
def test_rejects_runtime_authority_fields_on_proposal_hint(field):
    harness = load_harness_module()
    candidate = valid_candidate()

    mutated = deepcopy(candidate)
    mutated["proposal_candidate"][field] = "forbidden"
    errors = harness.validate_audit_candidate(mutated)["errors"]

    assert any("proposal_candidate_has_rejected_fields" in error for error in errors)
    assert any("audit_candidate_has_runtime_authority_fields" in error for error in errors)


def test_rejects_runtime_authority_fields_on_fixture_context():
    harness = load_harness_module()
    context = harness.build_fixture_operator_context()

    context["gate_decision"] = "allow"
    errors = harness.validate_fixture_context(context)["errors"]

    assert any("operator_context_has_runtime_authority_fields" in error for error in errors)


def test_fixture_boundary_writes_only_non_executable_artifacts(tmp_path):
    harness = load_harness_module()

    result = harness.run_fixture_boundary(repo_root=ROOT, out_dir=tmp_path)

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / runtime_trace_fixture_boundary_only"
    assert result["next_allowed_step"] == "default_off_runtime_adjacent_observer_only"
    trace = result["shadow_trace"]
    assert trace["mode"] == "runtime_trace_fixture_boundary_only"
    assert trace["fixture_only"] is True
    assert trace["runtime_connected"] is False
    assert trace["adapter_registered"] is False
    assert trace["non_executable"] is True
    assert trace["audit_observation"]["audit_only"] is True
    assert trace["audit_observation"]["can_drive_runtime"] is False
    assert trace["audit_observation"]["can_change_user_response"] is False
    assert trace["audit_observation"]["can_write_memory"] is False
    assert trace["audit_observation"]["can_invoke_gate"] is False
    assert all(value is False for value in trace["side_effects"].values())
    assert trace["baseline_comparison"]["user_response_unchanged"] is True
    assert trace["baseline_comparison"]["memory_diff"] is False
    assert trace["baseline_comparison"]["approval_diff"] is False
    assert trace["baseline_comparison"]["gate_diff"] is False
    assert trace["baseline_comparison"]["runtime_output_diff"] is False

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "RUNTIME_TRACE_FIXTURE_BOUNDARY_REPORT.md",
        "runtime_trace_fixture_boundary.json",
    ]
    report = (tmp_path / "RUNTIME_TRACE_FIXTURE_BOUNDARY_REPORT.md").read_text(encoding="utf-8")
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Failure Meaning" in report
    assert "Rollback" in report


def test_build_shadow_trace_raises_on_invalid_candidate():
    harness = load_harness_module()
    context = harness.build_fixture_operator_context()
    candidate = valid_candidate()
    candidate["enabled"] = True

    with pytest.raises(ValueError, match="enabled_must_be_false"):
        harness.build_shadow_trace(context, candidate)


def test_harness_has_no_runtime_imports_or_side_effect_calls():
    source = HARNESS_PATH.read_text(encoding="utf-8") if HARNESS_PATH.exists() else ""
    banned = [
        "EgoOperator.agent_base",
        "agent_base",
        "memory_system",
        "real_use_gate",
        "human_operator_trial",
        "operator_comparison",
        "runtime_gate",
        "pspc_lab_adapter",
        "PSPCLabAdapter",
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


def test_runtime_sources_still_do_not_import_or_register_pspc():
    runtime_sources = [
        path
        for path in (ROOT / "EgoOperator").rglob("*.py")
        if "adapters" not in path.parts and "tests" not in path.parts
    ]
    assert runtime_sources

    offenders = []
    markers = [
        "pspc_lab_adapter",
        "PSPCLabAdapter",
        "pspc_read_only_shadow_hook",
        "PSPCReadOnlyShadowHook",
        "pspc_runtime_adjacent",
        "PSPCRuntime",
    ]
    for path in runtime_sources:
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in markers):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
