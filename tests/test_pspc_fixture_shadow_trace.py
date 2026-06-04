from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "scripts" / "run_pspc_fixture_shadow_trace.py"

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


def load_shadow_module():
    assert HARNESS_PATH.exists(), "fixture shadow trace harness must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_fixture_shadow_trace", HARNESS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixture_operator_context_is_not_runtime_context():
    harness = load_shadow_module()

    fixture = harness.build_fixture_operator_context()

    assert fixture["fixture_only"] is True
    assert fixture["runtime_connected"] is False
    assert fixture["source"] == "fixture_operator_context"
    assert fixture["operator_trace_refs"] == ["fixture_operator_turn_001"]
    assert fixture["baseline_user_response"] == "fixture_response_unchanged"
    assert fixture["baseline_memory_digest"] == "fixture_no_memory_write"
    assert RUNTIME_FIELDS.isdisjoint(fixture)


def test_fixture_shadow_trace_writes_only_shadow_artifacts(tmp_path):
    harness = load_shadow_module()

    result = harness.run_shadow_trace(repo_root=ROOT, out_dir=tmp_path)

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / fixture_shadow_trace_only"
    assert result["input_sources"]["audit_candidate_source"].endswith(
        "artifacts\\pspc_adapter_dry_run_v0\\dry_run_result.json"
    )
    assert result["input_sources"]["static_review_source"].endswith(
        "artifacts\\pspc_static_compatibility_review_v0\\static_compatibility_review.json"
    )

    trace = result["shadow_trace"]
    assert trace["mode"] == "fixture_only_shadow_audit"
    assert trace["runtime_connected"] is False
    assert trace["adapter_registered"] is False
    assert trace["non_executable"] is True
    assert trace["operator_context"]["fixture_only"] is True
    assert trace["pspc_audit_candidate"]["allowed_use"] == "audit_trace_only"
    assert trace["audit_observation"]["suggested_tendency"] == "avoid_unstable_object"
    assert trace["audit_observation"]["audit_only"] is True
    assert trace["audit_observation"]["can_drive_runtime"] is False
    assert trace["rejected_runtime_fields_present"] == []

    assert result["side_effects"] == {
        "runtime_registered": False,
        "gate_invoked": False,
        "memory_written": False,
        "direct_action": False,
        "direct_user_message": False,
        "proactive_trigger": False,
        "runtime_context_imported": False,
    }
    assert result["baseline_comparison"]["user_response_unchanged"] is True
    assert result["baseline_comparison"]["memory_diff"] is False
    assert result["baseline_comparison"]["gate_diff"] is False
    assert result["baseline_comparison"]["runtime_output_diff"] is False

    report_path = tmp_path / "FIXTURE_SHADOW_TRACE_REPORT.md"
    json_path = tmp_path / "shadow_trace.json"
    assert report_path.exists()
    assert json_path.exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "FIXTURE_SHADOW_TRACE_REPORT.md",
        "shadow_trace.json",
    ]

    report = report_path.read_text(encoding="utf-8")
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Failure Meaning" in report
    assert "Rollback" in report
    assert "lab_only_proto_self_mechanism_candidate / fixture_shadow_trace_only" in report


def test_shadow_trace_cannot_be_interpreted_as_action_memory_gate_or_user_message(tmp_path):
    harness = load_shadow_module()

    result = harness.run_shadow_trace(repo_root=ROOT, out_dir=tmp_path)
    trace = result["shadow_trace"]
    candidate = trace["pspc_audit_candidate"]
    observation = trace["audit_observation"]

    assert RUNTIME_FIELDS.isdisjoint(trace)
    assert RUNTIME_FIELDS.isdisjoint(candidate)
    assert RUNTIME_FIELDS.isdisjoint(observation)
    assert set(candidate["proposal_candidate"]) == {"suggested_tendency", "confidence", "reason_trace_refs"}
    assert {"proposal_id", "action", "tool_call", "approval_id", "gate_decision"}.isdisjoint(
        candidate["proposal_candidate"]
    )


def test_shadow_trace_requires_previous_static_compatibility_pass(tmp_path):
    harness = load_shadow_module()

    result = harness.run_shadow_trace(repo_root=ROOT, out_dir=tmp_path)

    static_review = json.loads((ROOT / "artifacts" / "pspc_static_compatibility_review_v0" / "static_compatibility_review.json").read_text(encoding="utf-8"))
    assert static_review["status"] == "pass"
    assert result["preconditions"]["static_compatibility_status"] == "pass"
    assert result["preconditions"]["audit_candidate_non_executable"] is True
    assert result["preconditions"]["runtime_import_or_registry_absent"] is True


def test_shadow_trace_harness_has_no_runtime_imports_or_side_effect_calls():
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


def test_runtime_sources_still_do_not_import_or_register_pspc_adapter():
    runtime_sources = [
        path
        for path in (ROOT / "EgoOperator").rglob("*.py")
        if "adapters" not in path.parts and "tests" not in path.parts
    ]
    assert runtime_sources

    offenders = []
    for path in runtime_sources:
        text = path.read_text(encoding="utf-8")
        if "pspc_lab_adapter" in text or "PSPCLabAdapter" in text:
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
