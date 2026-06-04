from __future__ import annotations

import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_pspc_recorded_shadow_observation.py"
REPORT_PATH = ROOT / "EgoOperator" / "artifacts" / "human_operator_trial" / "v2_latest" / "human_operator_trial_report.json"

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


def load_runner_module():
    assert RUNNER_PATH.exists(), "recorded shadow observation runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_recorded_shadow_observation", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_recorded_cases_are_loaded_from_human_operator_report():
    runner = load_runner_module()

    cases = runner.load_recorded_cases(REPORT_PATH)

    assert len(cases) == 18
    assert cases[0]["source"] == "ego_operator_human_trial_v2_recorded"
    assert cases[0]["scenario_id"]
    assert cases[0]["prompt"]
    assert cases[0]["reply_text"]
    assert cases[0]["trace_path"]
    assert cases[0]["runtime_connected"] is False
    assert cases[0]["recorded_only"] is True
    assert RUNTIME_FIELDS.isdisjoint(cases[0])


def test_recorded_shadow_observation_preserves_outputs_and_writes_artifacts(tmp_path):
    runner = load_runner_module()

    result = runner.run_observation(repo_root=ROOT, out_dir=tmp_path)

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / recorded_shadow_observation_only"
    assert result["input_source"].endswith(
        "EgoOperator\\artifacts\\human_operator_trial\\v2_latest\\human_operator_trial_report.json"
    )
    assert result["recorded_case_count"] == 18
    assert result["hook_enabled"] is False
    assert result["mainline_connected"] is False
    assert result["runtime_registered"] is False
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

    comparison = result["comparison"]
    assert comparison["all_user_responses_unchanged"] is True
    assert comparison["memory_diff"] is False
    assert comparison["approval_gate_diff"] is False
    assert comparison["runtime_output_diff"] is False
    assert comparison["pspc_shadow_artifact_only"] is True

    assert len(result["shadow_records"]) == 18
    for record in result["shadow_records"]:
        assert record["baseline_response_hash"] == record["with_shadow_response_hash"]
        assert record["user_response_unchanged"] is True
        assert record["memory_diff"] is False
        assert record["approval_gate_diff"] is False
        assert record["runtime_output_diff"] is False
        assert record["pspc_shadow_added"] is True
        assert RUNTIME_FIELDS.isdisjoint(record)
        assert RUNTIME_FIELDS.isdisjoint(record["pspc_shadow_observation"])

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "RECORDED_SHADOW_OBSERVATION_REPORT.md",
        "recorded_shadow_observation.json",
    ]
    report = (tmp_path / "RECORDED_SHADOW_OBSERVATION_REPORT.md").read_text(encoding="utf-8")
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Rollback" in report
    assert "lab_only_proto_self_mechanism_candidate / recorded_shadow_observation_only" in report


def test_recorded_shadow_runner_has_no_runtime_imports_or_side_effect_calls():
    source = RUNNER_PATH.read_text(encoding="utf-8") if RUNNER_PATH.exists() else ""
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


def test_runtime_sources_do_not_import_or_register_recorded_shadow_hook():
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
