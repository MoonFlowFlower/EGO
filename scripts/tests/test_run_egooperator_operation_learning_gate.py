from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "codex" / "run_egooperator_operation_learning_gate.py"


def _load_gate_module():
    if not MODULE_PATH.exists():
        raise AssertionError(f"operation-learning gate runner missing: {MODULE_PATH}")
    spec = importlib.util.spec_from_file_location("run_egooperator_operation_learning_gate", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_unreviewed_human_trial_report_blocks_candidates(tmp_path: Path) -> None:
    gate = _load_gate_module()
    human_report_path = tmp_path / "human_report.json"
    trigger_report_path = tmp_path / "trigger_report.json"
    human_report_path.write_text(json.dumps(_human_report(status="human_trial_needs_review", review_blocker_count=3)), encoding="utf-8")
    trigger_report_path.write_text(json.dumps(_trigger_report()), encoding="utf-8")

    report = gate.build_operation_learning_report(
        human_report_path=human_report_path,
        trigger_report_path=trigger_report_path,
        run_id="test-run-unreviewed",
    )

    assert report["status"] == "operation_learning_blocked"
    assert report["candidate_count"] == 0
    assert report["human_review_admission"]["status"] == "fail"
    assert "human_report_status_not_candidate_pass" in report["human_review_admission"]["reasons"]
    assert "human_review_blockers_present" in report["human_review_admission"]["reasons"]
    assert report["trigger_admission"]["status"] == "pass"
    assert report["enabled"] is False
    assert report["mainline_connected"] is False
    assert report["runtime_authority"] is False
    assert all(report["side_effect_absence"].values())


def test_missing_desktop_trigger_contract_blocks_candidates(tmp_path: Path) -> None:
    gate = _load_gate_module()
    human_report_path = tmp_path / "human_report.json"
    trigger_report_path = tmp_path / "trigger_report.json"
    trigger_report = _trigger_report()
    trigger_report.pop("desktop_trigger_contract_status")
    human_report_path.write_text(json.dumps(_human_report()), encoding="utf-8")
    trigger_report_path.write_text(json.dumps(trigger_report), encoding="utf-8")

    report = gate.build_operation_learning_report(
        human_report_path=human_report_path,
        trigger_report_path=trigger_report_path,
        run_id="test-run-trigger-blocked",
    )

    assert report["status"] == "operation_learning_blocked"
    assert report["candidate_count"] == 0
    assert report["human_review_admission"]["status"] == "pass"
    assert report["trigger_admission"]["status"] == "fail"
    assert "desktop_trigger_contract_status_not_pass" in report["trigger_admission"]["reasons"]


def test_valid_reviewed_inputs_emit_review_only_candidates_without_raw_text(tmp_path: Path) -> None:
    gate = _load_gate_module()
    human_report_path = tmp_path / "human_report.json"
    trigger_report_path = tmp_path / "trigger_report.json"
    human_report_path.write_text(json.dumps(_human_report()), encoding="utf-8")
    trigger_report_path.write_text(json.dumps(_trigger_report()), encoding="utf-8")

    report = gate.build_operation_learning_report(
        human_report_path=human_report_path,
        trigger_report_path=trigger_report_path,
        run_id="test-run-valid",
    )

    serialized = json.dumps(report, ensure_ascii=False, sort_keys=True)
    assert report["status"] == "operation_learning_candidates_ready_for_human_review"
    assert report["candidate_count"] == 3
    assert report["human_review_admission"]["status"] == "pass"
    assert report["trigger_admission"]["status"] == "pass"
    assert report["claim_ceiling"] == "default_off_operation_learning_candidate_runner_only"
    assert {candidate["review_state"] for candidate in report["candidates"]} == {"human_review_required"}
    assert {candidate["runtime_authority"] for candidate in report["candidates"]} == {False}
    assert {candidate["memory_promotion_authorized"] for candidate in report["candidates"]} == {False}
    assert {candidate["proactive_send_authorized"] for candidate in report["candidates"]} == {False}
    assert "reviewed raw reply" not in serialized
    assert "selected raw user text" not in serialized


def test_write_operation_learning_artifacts_records_hashes_without_raw_text(tmp_path: Path) -> None:
    gate = _load_gate_module()
    human_report_path = tmp_path / "human_report.json"
    trigger_report_path = tmp_path / "trigger_report.json"
    human_report_path.write_text(json.dumps(_human_report()), encoding="utf-8")
    trigger_report_path.write_text(json.dumps(_trigger_report()), encoding="utf-8")
    report = gate.build_operation_learning_report(
        human_report_path=human_report_path,
        trigger_report_path=trigger_report_path,
        run_id="test-run-write",
    )

    write_result = gate.write_operation_learning_artifacts(tmp_path / "out", report)
    report_text = (tmp_path / "out" / "operation_learning_gate_report.json").read_text(encoding="utf-8")
    candidates_text = (tmp_path / "out" / "operation_learning_candidates.jsonl").read_text(encoding="utf-8")

    assert write_result["candidate_count"] == 3
    assert write_result["operation_learning_gate_report_sha256"] == _sha_text(report_text)
    assert write_result["operation_learning_candidates_sha256"] == _sha_text(candidates_text)
    assert "reviewed raw reply" not in report_text + candidates_text
    assert "selected raw user text" not in report_text + candidates_text


def _human_report(*, status: str = "human_trial_candidate_pass", review_blocker_count: int = 0) -> dict:
    observations = []
    for idx in range(3):
        observations.append({
            "scenario_id": f"scenario_{idx}",
            "prompt": f"human prompt {idx}",
            "reply_text": f"reviewed raw reply {idx}",
            "operator_score": 5,
            "failure_notes": [],
            "subjective_notes": f"human-reviewed note {idx}",
            "trace_path": f"trace/{idx}.jsonl",
        })
    return {
        "schema_version": "ego_operator.human_operator_trial.v2",
        "status": status,
        "provider_mode": "openrouter",
        "observation_count": len(observations),
        "known_scenario_coverage": len(observations),
        "invalid_observation_count": 0,
        "average_operator_score": 5.0,
        "memory_misuse_count": 0,
        "gate_violation_count": 0,
        "review_blocker_count": review_blocker_count,
        "observations": observations,
    }


def _trigger_report() -> dict:
    return {
        "schema": "egodesktop.joi_real_loop.selected_source_trigger_input.v0",
        "selection_id": "wizard_of_wikipedia_hf:train:0",
        "source_id": "wizard_of_wikipedia_hf",
        "capture_manifest_source_count": 3,
        "capture_manifest_selected_row_count": 15,
        "capture_manifest_source_ids": ["dailydialog_hf", "empathetic_dialogues_hf", "wizard_of_wikipedia_hf"],
        "three_source_manifest_status": "pass",
        "desktop_trigger_contract_status": "pass",
        "future_trace_fields_status": "pass",
        "desktop_trigger_required": "window.egoDesktop.sendChatTurn",
        "writer_required": "EgoDesktop/src/joiRealLoopGAblationTraceRunner.js",
        "raw_text_in_report": False,
        "runtime_authority": "explicit_smoke_only",
        "scoring_authority": False,
        "capture_authority": False,
        "user_text_hash": _sha_text("selected raw user text"),
        "user_text_plain_sha256": _sha_text("selected raw user text"),
    }


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
