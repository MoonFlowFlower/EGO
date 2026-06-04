from __future__ import annotations

import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_pspc_recorded_trace_replay_no_diff.py"
REPORT_PATH = ROOT / "EgoOperator" / "artifacts" / "human_operator_trial" / "v2_latest" / "human_operator_trial_report.json"


def load_runner_module():
    assert RUNNER_PATH.exists(), "recorded trace replay no-diff runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_recorded_trace_replay_no_diff", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_recorded_cases_load_from_human_operator_report():
    runner = load_runner_module()

    cases = runner.load_recorded_cases(REPORT_PATH)

    assert len(cases) == 18
    assert cases[0]["source"] == "ego_operator_human_trial_v2_recorded"
    assert cases[0]["recorded_only"] is True
    assert cases[0]["runtime_connected"] is False
    assert cases[0]["scenario_id"]
    assert cases[0]["trace_path"]
    assert "response_hash" in cases[0]["baseline_snapshot"]
    assert set(cases[0]).isdisjoint(runner.RUNTIME_FIELDS)


def test_recorded_replay_preserves_output_and_runtime_snapshots(tmp_path):
    runner = load_runner_module()

    result = runner.run_replay(ROOT, tmp_path)

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / recorded_trace_replay_no_diff_only"
    assert result["recorded_case_count"] == 18
    assert result["observer_enabled"] is False
    assert result["observer_mainline_connected"] is False
    assert result["runtime_registered"] is False
    assert result["next_allowed_step"] == "deterministic_runtime_adjacent_smoke_only"
    assert result["comparison"]["all_user_response_hashes_equal"] is True
    assert result["comparison"]["all_snapshot_hashes_equal"] is True
    assert result["comparison"]["memory_diff"] is False
    assert result["comparison"]["approval_diff"] is False
    assert result["comparison"]["gate_diff"] is False
    assert result["comparison"]["runtime_output_diff"] is False
    assert result["comparison"]["pspc_adds_only_audit_artifacts"] is True
    assert all(value is False for value in result["side_effects"].values())

    for record in result["replay_records"]:
        assert record["baseline_response_hash"] == record["with_shadow_response_hash"]
        assert record["baseline_snapshot_hash"] == record["with_shadow_snapshot_hash"]
        assert record["memory_diff"] is False
        assert record["approval_diff"] is False
        assert record["gate_diff"] is False
        assert record["runtime_output_diff"] is False
        assert record["direct_action"] is False
        assert record["direct_user_message"] is False
        assert record["proactive_trigger"] is False
        assert record["runtime_registered"] is False

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "RECORDED_TRACE_REPLAY_NO_DIFF_REPORT.md",
        "recorded_trace_replay_no_diff.json",
    ]
    report = (tmp_path / "RECORDED_TRACE_REPLAY_NO_DIFF_REPORT.md").read_text(encoding="utf-8")
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Failure Meaning" in report
    assert "Rollback" in report


def test_replay_runner_has_no_runtime_imports_or_side_effect_calls():
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


def test_runtime_sources_still_do_not_import_or_register_replay_observer():
    runtime_sources = [
        path
        for path in (ROOT / "EgoOperator").rglob("*.py")
        if "adapters" not in path.parts and "tests" not in path.parts
    ]
    assert runtime_sources

    offenders = []
    for path in runtime_sources:
        text = path.read_text(encoding="utf-8")
        if "pspc_runtime_adjacent_observer" in text or "PSPCRuntimeAdjacentObserver" in text:
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
