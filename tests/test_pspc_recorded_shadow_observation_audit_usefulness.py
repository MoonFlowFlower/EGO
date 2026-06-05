from __future__ import annotations

import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_pspc_recorded_shadow_observation_audit_usefulness.py"


def load_runner_module():
    assert RUNNER_PATH.exists(), "recorded shadow observation audit usefulness runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_recorded_shadow_observation_audit_usefulness", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_case_classification_produces_audit_tendency_and_risk():
    runner = load_runner_module()
    cases = runner.load_recorded_cases(ROOT)

    classifications = [runner.classify_case(case) for case in cases]

    assert len(classifications) == 18
    assert all(item["suggested_tendency"] for item in classifications)
    assert all(item["risk_signal"] for item in classifications)
    assert all(0.0 < item["confidence"] <= 1.0 for item in classifications)


def test_recorded_shadow_observation_audit_usefulness_passes(tmp_path):
    runner = load_runner_module()

    result = runner.run_audit_usefulness(ROOT, tmp_path)

    assert result["status"] == "pass"
    assert result["verdict"] == "audit_usefulness_pass_go_for_disabled_runtime_flag_contract"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / recorded_shadow_audit_usefulness_only"
    assert result["recorded_case_count"] == 18
    assert result["audit_useful_count"] >= 12
    assert result["next_allowed_step"] == "disabled_runtime_flag_contract_only"
    assert all(result["checks"].values())

    for record in result["records"]:
        observation = record["audit_observation"]
        assert record["audit_useful"] is True
        assert observation["suggested_tendency"]
        assert observation["risk_signal"]
        assert observation["reason_trace_refs"]
        assert observation["evidence_refs"]
        assert observation["audit_only"] is True
        assert observation["non_executable"] is True
        assert record["runtime_field_hits"] == []
        assert record["user_output_diff"] is False
        assert record["memory_diff"] is False
        assert record["approval_diff"] is False
        assert record["gate_diff"] is False
        assert record["runtime_output_diff"] is False
        assert all(value is False for value in record["side_effects"].values())

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "RECORDED_SHADOW_OBSERVATION_AUDIT_USEFULNESS_REPORT.md",
        "recorded_shadow_observation_audit_usefulness.json",
    ]
    report = (tmp_path / "RECORDED_SHADOW_OBSERVATION_AUDIT_USEFULNESS_REPORT.md").read_text(encoding="utf-8")
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Rollback" in report


def test_audit_observation_rejects_runtime_fields():
    runner = load_runner_module()

    assert runner.runtime_field_hits({"gate_decision": "allow"}) == ["gate_decision"]
    assert runner.runtime_field_hits({"nested": {"memory_write": "x"}}) == ["nested.memory_write"]


def test_audit_usefulness_runner_has_no_runtime_imports_or_side_effect_calls():
    source = RUNNER_PATH.read_text(encoding="utf-8") if RUNNER_PATH.exists() else ""
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
