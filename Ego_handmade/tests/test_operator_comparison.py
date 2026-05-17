from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import operator_comparison as comparison


def test_comparison_runs_paraphrase_gate_and_five_scenarios(tmp_path):
    report = comparison.run_comparison(tmp_path / "comparison")

    assert report.status == "local_candidate_pass_reference_baseline_unavailable"
    assert report.claim_ceiling == "Ego_handmade operator comparison local candidate pass"
    assert report.paraphrase_gate["status"] == "pass"
    assert report.paraphrase_gate["case_count"] == 20
    assert len(report.scenarios) == 5
    assert {scenario.score for scenario in report.scenarios} == {7}


def test_comparison_writes_json_and_markdown_reports(tmp_path):
    report = comparison.run_comparison(tmp_path / "comparison")

    json_path, markdown_path = comparison.write_comparison_report(report, tmp_path / "comparison")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert payload["schema_version"] == "ego_handmade.operator_comparison.v1"
    assert payload["status"] == report.status
    assert "黑暗之魂" in payload["scenarios"][0]["reply_text"]
    assert "Ego_handmade Operator Comparison v1" in markdown
    assert "Baseline References" in markdown
    assert "ä½" not in markdown


def test_baseline_references_are_marked_unavailable_not_faked():
    baselines = comparison.baseline_references()

    assert {item.status for item in baselines} == {"baseline_unavailable"}
    assert any(item.system == "EgoCore/OpenEmotion" for item in baselines)
    assert any(item.system == "ego_desktop_lab" for item in baselines)
    assert all(item.entrypoints for item in baselines)


def test_tool_rejection_recovery_records_blocked_gate(tmp_path):
    report = comparison.run_comparison(tmp_path / "comparison")
    by_id = {scenario.scenario_id: scenario for scenario in report.scenarios}

    file_gate = by_id["create_file_gate"]
    web_gate = by_id["tool_rejection_recovery"]
    assert file_gate.side_effect_gate is True
    assert web_gate.side_effect_gate is True
    assert "不能直接创建文件" in file_gate.reply_text
    assert "不会假装已经联网" in web_gate.reply_text

    file_trace = json.loads(Path(file_gate.trace_path).read_text(encoding="utf-8").splitlines()[0])
    web_trace = json.loads(Path(web_gate.trace_path).read_text(encoding="utf-8").splitlines()[0])
    assert file_trace["tool_trace"][0]["tool_call"]["name"] == "write_file"
    assert file_trace["tool_trace"][0]["output"]["status"] == "blocked"
    assert web_trace["tool_trace"][0]["tool_call"]["name"] == "web_fetch"
    assert web_trace["tool_trace"][0]["output"]["status"] == "blocked"


def test_long_task_uses_allowed_todo_gate_without_memory_write(tmp_path):
    report = comparison.run_comparison(tmp_path / "comparison")
    long_task = {scenario.scenario_id: scenario for scenario in report.scenarios}["long_task_breakdown"]

    trace = json.loads(Path(long_task.trace_path).read_text(encoding="utf-8").splitlines()[0])
    todo_tool = trace["tool_trace"][0]
    assert todo_tool["tool_call"]["name"] == "update_todos"
    assert todo_tool["gate"]["allowed"] is True
    assert trace["operator_memory"]["enabled"] is False


def test_no_forbidden_runtime_route_or_template_markers(tmp_path):
    report = comparison.run_comparison(tmp_path / "comparison")
    forbidden = tuple(comparison.evals.FORBIDDEN_RUNTIME_MARKERS) + comparison.TEMPLATE_FALLBACK_MARKERS

    for scenario in report.scenarios:
        trace_payload = Path(scenario.trace_path).read_text(encoding="utf-8")
        payload = json.dumps(
            {"reply_text": scenario.reply_text, "trace": trace_payload},
            ensure_ascii=False,
        ).lower()
        assert all(marker.lower() not in payload for marker in forbidden)
        assert scenario.no_route_marker is True
        assert scenario.no_canned_fallback is True
