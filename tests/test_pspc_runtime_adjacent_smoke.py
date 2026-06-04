from __future__ import annotations

import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_pspc_runtime_adjacent_smoke.py"


def load_runner_module():
    assert RUNNER_PATH.exists(), "runtime-adjacent smoke runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_runtime_adjacent_smoke", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_smoke_cases_use_only_deterministic_or_recorded_artifacts():
    runner = load_runner_module()
    observer = runner.load_json(ROOT, runner.OBSERVER_RESULT)
    replay = runner.load_json(ROOT, runner.REPLAY_RESULT)

    cases = runner.build_smoke_cases(observer, replay)

    assert len(cases) == 3
    assert all(case["live_user_channel"] is False for case in cases)
    assert {case["input_source"] for case in cases} == {
        str(runner.OBSERVER_RESULT),
        str(runner.REPLAY_RESULT),
    }


def test_runtime_adjacent_smoke_preserves_snapshots_and_writes_artifacts(tmp_path):
    runner = load_runner_module()

    result = runner.run_smoke(ROOT, tmp_path)

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / deterministic_runtime_adjacent_smoke_only"
    assert result["case_count"] == 3
    assert result["next_allowed_step"] == "runtime_hook_go_no_go_only"
    assert result["checks"] == {
        "uses_no_live_user_channel": True,
        "runtime_behavior_unchanged": True,
        "pspc_output_audit_only": True,
        "pspc_output_non_executable": True,
        "pspc_disabled": True,
        "pspc_mainline_disconnected": True,
        "runtime_import_or_registry_absent": True,
        "side_effects_absent": True,
    }
    assert result["runtime_scan"]["runtime_source_count"] > 0
    assert result["runtime_scan"]["offenders"] == []
    for case in result["smoke_cases"]:
        assert case["baseline_runtime_behavior_hash"] == case["with_shadow_runtime_behavior_hash"]
        assert case["runtime_behavior_unchanged"] is True
        assert case["pspc_audit_only"] is True
        assert case["pspc_non_executable"] is True
        assert case["pspc_enabled"] is False
        assert case["pspc_mainline_connected"] is False
        assert all(value is False for value in case["side_effects"].values())

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "RUNTIME_ADJACENT_SMOKE_REPORT.md",
        "runtime_adjacent_smoke.json",
    ]
    report = (tmp_path / "RUNTIME_ADJACENT_SMOKE_REPORT.md").read_text(encoding="utf-8")
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Failure Meaning" in report
    assert "Rollback" in report


def test_smoke_runner_has_no_runtime_imports_or_side_effect_calls():
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


def test_runtime_sources_still_do_not_import_or_register_observer():
    runner = load_runner_module()

    runtime_scan = runner.scan_runtime_sources(ROOT)

    assert runtime_scan["runtime_source_count"] > 0
    assert runtime_scan["offenders"] == []
