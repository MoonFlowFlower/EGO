from __future__ import annotations

import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "scripts" / "run_pspc_adapter_dry_run.py"


def load_harness_module():
    assert HARNESS_PATH.exists(), "dry-run harness script must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_adapter_dry_run", HARNESS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_packet_uses_existing_pspc_artifact_refs():
    harness = load_harness_module()

    packet = harness.build_canonical_packet(ROOT)

    assert packet["source"] == "virtual_cat_pspc_v0"
    assert packet["claim_level"] == "lab_only_proto_self_mechanism_candidate"
    assert packet["mainline_connected"] is False
    assert packet["enabled"] is False
    assert packet["allowed_use"] == "audit_trace_only"
    assert packet["evidence_refs"]
    for ref in packet["evidence_refs"]:
        assert (ROOT / ref).exists()
    assert packet["forbidden"]["direct_action"] is True
    assert packet["forbidden"]["direct_user_message"] is True
    assert packet["forbidden"]["direct_memory_write"] is True
    assert packet["forbidden"]["runtime_gate_bypass"] is True
    assert packet["forbidden"]["runtime_registration"] is True
    assert packet["forbidden"]["proactive_trigger"] is True


def test_dry_run_writes_only_audit_artifacts(tmp_path):
    harness = load_harness_module()

    result = harness.run_dry_run(repo_root=ROOT, out_dir=tmp_path)

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / adapter_dry_run_only"
    assert result["adapter"]["enabled"] is False
    assert result["adapter"]["mainline_connected"] is False
    assert result["adapter"]["runtime_authority"] == "none"
    assert result["validation"]["ok"] is True

    candidate = result["audit_candidate"]
    assert candidate["adapter_status"] == "disabled_read_only"
    assert candidate["allowed_use"] == "audit_trace_only"
    assert candidate["mainline_connected"] is False
    assert candidate["enabled"] is False
    assert candidate["proposal_candidate"]["suggested_tendency"] == "avoid_unstable_object"
    assert candidate["forbidden"]["direct_action"] is True
    assert candidate["forbidden"]["direct_user_message"] is True
    assert candidate["forbidden"]["direct_memory_write"] is True
    assert candidate["forbidden"]["runtime_gate_bypass"] is True

    forbidden_runtime_fields = {
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
    }
    assert forbidden_runtime_fields.isdisjoint(candidate)

    report_path = tmp_path / "DRY_RUN_REPORT.md"
    json_path = tmp_path / "dry_run_result.json"
    assert report_path.exists()
    assert json_path.exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["DRY_RUN_REPORT.md", "dry_run_result.json"]

    report = report_path.read_text(encoding="utf-8")
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Rollback" in report
    assert "Failure Meaning" in report
    assert "lab_only_proto_self_mechanism_candidate / adapter_dry_run_only" in report


def test_dry_run_harness_has_no_runtime_imports_or_side_effect_calls():
    source = HARNESS_PATH.read_text(encoding="utf-8") if HARNESS_PATH.exists() else ""
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


def test_runtime_sources_do_not_import_or_register_pspc_adapter():
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
