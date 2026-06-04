from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "scripts" / "run_pspc_static_compatibility_review.py"


def load_review_module():
    assert HARNESS_PATH.exists(), "static compatibility review harness must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_static_compatibility_review", HARNESS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_field_classification_is_complete_and_static():
    review = load_review_module()

    classification = review.build_field_classification()

    assert classification["audit_only"] == [
        "source",
        "claim_level",
        "adapter_status",
        "allowed_use",
        "evidence",
        "forbidden",
    ]
    assert classification["proposal_hint"] == [
        "proposal_candidate.suggested_tendency",
        "proposal_candidate.confidence",
        "proposal_candidate.reason_trace_refs",
    ]
    assert classification["required_forbidden"] == [
        "direct_action",
        "direct_user_message",
        "direct_memory_write",
        "runtime_gate_bypass",
        "runtime_registration",
        "proactive_trigger",
    ]
    for field in [
        "action",
        "tool_call",
        "command",
        "user_message",
        "memory_write",
        "gate_decision",
        "approval_id",
        "transport",
        "send",
        "schedule",
        "enable",
        "mainline_authority",
        "consciousness_claim",
        "subjective_experience_claim",
    ]:
        assert field in classification["rejected_fields"]


def test_static_review_passes_for_existing_dry_run_artifact(tmp_path):
    review = load_review_module()

    result = review.run_review(repo_root=ROOT, out_dir=tmp_path)

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / static_compatibility_only"
    checks = result["compatibility_checks"]
    assert checks["audit_candidate_non_executable"] is True
    assert checks["proposal_hint_audit_only"] is True
    assert checks["missing_forbidden_flags_rejected"] is True
    assert checks["enabled_true_rejected"] is True
    assert checks["mainline_connected_true_rejected"] is True
    assert checks["runtime_import_or_registry_absent"] is True

    assert result["runtime_scan"]["offenders"] == []
    assert result["side_effects"] == {
        "runtime_registered": False,
        "gate_invoked": False,
        "memory_written": False,
        "direct_action": False,
        "direct_user_message": False,
        "proactive_trigger": False,
    }
    assert result["proposal_hint_status"] == "audit_hint_only"

    json_path = tmp_path / "static_compatibility_review.json"
    report_path = tmp_path / "STATIC_COMPATIBILITY_REVIEW.md"
    assert json_path.exists()
    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Failure Meaning" in report
    assert "Rollback" in report
    assert "lab_only_proto_self_mechanism_candidate / static_compatibility_only" in report


def test_review_negative_cases_are_rejected():
    review = load_review_module()

    result = review.run_review(repo_root=ROOT, out_dir=ROOT / "artifacts" / "_tmp_pspc_static_review_test")
    negative = result["negative_validation"]

    assert negative["missing_forbidden.direct_action"]["ok"] is False
    assert "forbidden.direct_action_must_be_true" in negative["missing_forbidden.direct_action"]["errors"]
    assert negative["enabled_true"]["ok"] is False
    assert "enabled_must_be_false" in negative["enabled_true"]["errors"]
    assert negative["mainline_connected_true"]["ok"] is False
    assert "mainline_connected_must_be_false" in negative["mainline_connected_true"]["errors"]


def test_audit_candidate_cannot_be_interpreted_as_runtime_action_or_proposal():
    review = load_review_module()

    dry_run = review.load_dry_run_result(ROOT)
    candidate = dry_run["audit_candidate"]
    proposal_candidate = candidate["proposal_candidate"]

    for field in review.RUNTIME_EXECUTABLE_FIELDS:
        assert field not in candidate
    for field in ["proposal_id", "action", "tool_call", "approval_id", "gate_decision"]:
        assert field not in proposal_candidate
    assert set(proposal_candidate) == {"suggested_tendency", "confidence", "reason_trace_refs"}


def test_runtime_sources_do_not_import_or_register_adapter():
    review = load_review_module()

    scan = review.scan_runtime_sources(ROOT)

    assert scan["offenders"] == []
    assert scan["runtime_source_count"] > 0

