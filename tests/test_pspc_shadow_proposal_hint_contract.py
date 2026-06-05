from __future__ import annotations

import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_pspc_shadow_proposal_hint_contract.py"
HELPER_PATH = ROOT / "scripts" / "pspc_shadow_contracts.py"
INPUT_ARTIFACT = ROOT / "artifacts" / "pspc_sequence_experience_eval_v0_1" / "sequence_experience_eval_v0_1.json"


def load_runner_module():
    assert RUNNER_PATH.exists(), "proposal hint contract runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_shadow_proposal_hint_contract", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_contract(tmp_path):
    runner = load_runner_module()
    result = runner.run_proposal_hint_contract(ROOT, tmp_path, input_artifact_path=INPUT_ARTIFACT)
    return runner, result


def test_proposal_hint_contract_writes_artifact_only_outputs(tmp_path):
    _runner, result = run_contract(tmp_path)

    assert result["status"] == "pass"
    assert result["verdict"] == "proposal_hint_contract_pass__manual_review_only"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only"
    assert result["artifact_only"] is True
    assert result["runtime_connected"] is False
    assert result["adapter_created"] is False
    assert result["enabled"] is False
    assert result["mainline_connected"] is False
    assert result["packet_count"] >= 3
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "PROPOSAL_HINT_CONTRACT_REPORT.md",
        "proposal_hint_contract.json",
    ]


def test_packet_schema_and_forbidden_flags_are_strict(tmp_path):
    runner, result = run_contract(tmp_path)

    for packet in result["packets"]:
        runner.validate_packet(packet)
        assert packet["source"] == "pspc_sequence_experience_eval_v0_1"
        assert packet["packet_type"] == "shadow_proposal_hint"
        assert packet["enabled"] is False
        assert packet["mainline_connected"] is False
        assert packet["runtime_authority"] == "none"
        assert packet["human_required_status"] == "PSPC-SHADOW-HOOK-007_human_required_preserved"
        assert packet["forbidden"] == runner.FORBIDDEN_AUTHORITY_FLAGS
        assert all(value is False for value in packet["forbidden"].values())
        assert set(packet["proposal_hint"]) == runner.PROPOSAL_HINT_KEYS
        assert packet["proposal_hint"]["audit_use_only"] is True
        assert 0.35 <= packet["proposal_hint"]["confidence"] <= 0.82


def test_packet_is_not_executable_and_cannot_raise_claim_ceiling(tmp_path):
    runner, result = run_contract(tmp_path)

    for packet in result["packets"]:
        assert runner.runtime_field_hits(packet) == []
        assert not runner.REJECTED_PACKET_FIELDS & set(packet)
        assert packet["claim_ceiling"] == runner.CLAIM_CEILING
        assert "suggested_interaction_style" in packet["proposal_hint"]
        assert "action" not in packet["proposal_hint"]
        assert "user_message" not in packet["proposal_hint"]
        assert "memory_write" not in packet["proposal_hint"]
        assert "gate_decision" not in packet["proposal_hint"]


def test_packet_preserves_reason_trace_refs_and_evidence_refs(tmp_path):
    _runner, result = run_contract(tmp_path)

    for packet in result["packets"]:
        assert packet["proposal_hint"]["reason_trace_refs"]
        assert packet["evidence_refs"] == [str(INPUT_ARTIFACT)]
        assert packet["proposal_hint"]["basis"].startswith("recency_salience")


def test_checks_prove_static_runtime_boundary_and_human_required(tmp_path):
    runner, result = run_contract(tmp_path)

    assert all(result["checks"].values())
    assert result["runtime_scan"]["ok"] is True
    assert result["runtime_scan"]["offenders"] == []
    assert result["side_effects"] == runner.SIDE_EFFECTS_FALSE
    assert all(value is False for value in result["side_effects"].values())
    assert result["next_allowed_step"] == "manual_review_may_consider_product_only_local_behavior_prototype_design"


def test_report_states_proves_does_not_prove_and_manual_checklist(tmp_path):
    run_contract(tmp_path)

    report = (tmp_path / "PROPOSAL_HINT_CONTRACT_REPORT.md").read_text(encoding="utf-8")

    assert "Manual Go/No-Go Checklist" in report
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Rollback" in report
    assert "runtime integration safety" in report


def test_runner_does_not_import_runtime_or_side_effect_paths():
    source = RUNNER_PATH.read_text(encoding="utf-8") + "\n" + HELPER_PATH.read_text(encoding="utf-8")
    banned = [
        "EgoOperator.agent_base",
        "agent_base",
        "memory_system",
        "runtime_gate",
        "real_use_gate",
        "human_operator_trial",
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
