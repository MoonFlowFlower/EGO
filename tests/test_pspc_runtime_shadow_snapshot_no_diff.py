from __future__ import annotations

import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_pspc_runtime_shadow_snapshot_no_diff.py"


def load_runner_module():
    assert RUNNER_PATH.exists(), "runtime shadow snapshot no-diff runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_runtime_shadow_snapshot_no_diff", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_recorded_cases_load_for_snapshot_no_diff():
    runner = load_runner_module()

    cases = runner.load_recorded_cases(ROOT)

    assert len(cases) == 18
    assert cases[0]["scenario_id"]
    assert cases[0]["trace_path"]
    assert "user_output_hash" in cases[0]["baseline_runtime_snapshot"]


def test_snapshot_no_diff_runner_preserves_runtime_snapshots(tmp_path):
    runner = load_runner_module()

    result = runner.run_snapshot_no_diff(ROOT, tmp_path)

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / runtime_snapshot_no_diff_only"
    assert result["recorded_case_count"] == 18
    assert result["next_allowed_step"] == "recorded_shadow_observation_audit_usefulness_only"
    assert result["checks"] == {
        "recorded_case_count": True,
        "user_output_hashes_equal": True,
        "snapshot_hashes_equal": True,
        "memory_diff_absent": True,
        "approval_diff_absent": True,
        "gate_diff_absent": True,
        "runtime_output_diff_absent": True,
        "pspc_adds_only_shadow_artifacts": True,
        "shadow_artifacts_non_executable": True,
        "side_effects_absent": True,
        "runtime_import_or_registry_absent": True,
    }
    assert result["runtime_scan"]["offenders"] == []
    for record in result["records"]:
        assert record["baseline_user_output_hash"] == record["hook_present_user_output_hash"]
        assert record["baseline_snapshot_hash"] == record["hook_present_snapshot_hash"]
        assert record["memory_diff"] is False
        assert record["approval_diff"] is False
        assert record["gate_diff"] is False
        assert record["runtime_output_diff"] is False
        assert record["shadow_runtime_field_hits"] == []
        assert all(value is False for value in record["side_effects"].values())

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "RUNTIME_SHADOW_SNAPSHOT_NO_DIFF_REPORT.md",
        "runtime_shadow_snapshot_no_diff.json",
    ]
    report = (tmp_path / "RUNTIME_SHADOW_SNAPSHOT_NO_DIFF_REPORT.md").read_text(encoding="utf-8")
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Rollback" in report


def test_snapshot_runner_has_no_runtime_imports_or_side_effect_calls():
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


def test_active_runtime_sources_still_do_not_import_or_register_hook():
    runner = load_runner_module()

    scan = runner.scan_runtime_sources(ROOT)

    assert scan["runtime_source_count"] > 0
    assert scan["offenders"] == []
