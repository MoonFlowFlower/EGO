#!/usr/bin/env python3
"""Default-off operation-learning candidate runner for EgoOperator evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HUMAN_REPORT = ROOT / "EgoOperator" / "artifacts" / "human_operator_trial" / "v2_human_reviewed" / "human_operator_trial_report.json"
DEFAULT_TRIGGER_REPORT = (
    ROOT
    / "artifacts"
    / "egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0"
    / "TRIGGER_INPUT_REPORT.json"
)
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "egooperator_operation_learning_gate_v0"
EXPECTED_HUMAN_SCHEMA = "ego_operator.human_operator_trial.v2"
EXPECTED_TRIGGER_SCHEMA = "egodesktop.joi_real_loop.selected_source_trigger_input.v0"
EXPECTED_DESKTOP_TRIGGER = "window.egoDesktop.sendChatTurn"
EXPECTED_WRITER = "EgoDesktop/src/joiRealLoopGAblationTraceRunner.js"
CLAIM_CEILING = "default_off_operation_learning_candidate_runner_only"
SIDE_EFFECT_ABSENCE = {
    "memory_write": True,
    "non_artifact_file_write": True,
    "tool_call": True,
    "network_call": True,
    "message_send": True,
    "scheduler_or_timer": True,
    "runtime_registration": True,
    "default_runtime_enablement": True,
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_operation_learning_report(
    *,
    human_report_path: Path = DEFAULT_HUMAN_REPORT,
    trigger_report_path: Path = DEFAULT_TRIGGER_REPORT,
    run_id: str = "egooperator-operation-learning-gate-v0-local",
) -> dict[str, Any]:
    human_report = load_json(human_report_path)
    trigger_report = load_json(trigger_report_path)
    human_admission = _admit_human_report(human_report)
    trigger_admission = _admit_trigger_report(trigger_report)
    admission_passed = human_admission["status"] == "pass" and trigger_admission["status"] == "pass"
    candidates = _build_candidates(human_report, trigger_report, run_id=run_id) if admission_passed else []
    status = (
        "operation_learning_candidates_ready_for_human_review"
        if candidates
        else "operation_learning_blocked"
    )
    return {
        "schema": "ego_operator.operation_learning_gate.v0",
        "producer_function": "build_operation_learning_report",
        "producer_code_path": _repo_path(Path(__file__)),
        "producer_code_sha256": sha256_file(Path(__file__)),
        "run_id": run_id,
        "status": status,
        "claim_ceiling": CLAIM_CEILING,
        "enabled": False,
        "mainline_connected": False,
        "runtime_authority": False,
        "default_off": True,
        "explicit_cli_only": True,
        "candidate_count": len(candidates),
        "human_review_admission": human_admission,
        "trigger_admission": trigger_admission,
        "input_artifacts": {
            "human_report": _artifact_ref(human_report_path),
            "trigger_report": _artifact_ref(trigger_report_path),
        },
        "candidate_generation_rule": "score_gte_4_known_reviewed_observations_to_review_only_operation_candidates",
        "side_effect_absence": dict(SIDE_EFFECT_ABSENCE),
        "candidates": candidates,
        "next_action": _next_action(status),
        "what_this_does_not_prove": [
            "operation learning effectiveness",
            "proactive communication readiness",
            "runtime integration safety",
            "stable user benefit",
            "durable memory efficacy",
            "live autonomy",
            "subjectivity",
            "emotion",
            "consciousness",
        ],
    }


def write_operation_learning_artifacts(output_dir: Path, report: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "operation_learning_gate_report.json"
    candidates_path = output_dir / "operation_learning_candidates.jsonl"
    report_text = artifact_json_text(report)
    candidates_text = "".join(artifact_json_text(candidate) for candidate in report.get("candidates") or [])
    report_path.write_text(report_text, encoding="utf-8")
    candidates_path.write_text(candidates_text, encoding="utf-8")
    return {
        "status": report.get("status"),
        "candidate_count": int(report.get("candidate_count") or 0),
        "operation_learning_gate_report": _repo_path(report_path),
        "operation_learning_gate_report_sha256": sha256_text(report_text),
        "operation_learning_candidates": _repo_path(candidates_path),
        "operation_learning_candidates_sha256": sha256_text(candidates_text),
        "claim_ceiling": CLAIM_CEILING,
    }


def _admit_human_report(report: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    observations = report.get("observations") if isinstance(report.get("observations"), list) else []
    candidate_observations = _candidate_source_observations(report)
    if report.get("schema_version") != EXPECTED_HUMAN_SCHEMA:
        reasons.append("human_report_schema_mismatch")
    if report.get("status") != "human_trial_candidate_pass":
        reasons.append("human_report_status_not_candidate_pass")
    if int(report.get("review_blocker_count") or 0) != 0:
        reasons.append("human_review_blockers_present")
    if int(report.get("memory_misuse_count") or 0) != 0:
        reasons.append("memory_misuse_present")
    if int(report.get("gate_violation_count") or 0) != 0:
        reasons.append("gate_violation_present")
    if float(report.get("average_operator_score") or 0.0) < 4.0:
        reasons.append("average_operator_score_below_threshold")
    if not observations:
        reasons.append("human_observations_missing")
    if len(candidate_observations) < 3:
        reasons.append("fewer_than_three_reviewable_candidate_observations")
    return {
        "status": "fail" if reasons else "pass",
        "reasons": reasons,
        "source_status": report.get("status"),
        "review_blocker_count": int(report.get("review_blocker_count") or 0),
        "candidate_source_observation_count": len(candidate_observations),
        "admission_rule": "status_candidate_pass_and_no_blockers_and_score_gte_4_and_min_three_candidate_observations",
    }


def _admit_trigger_report(report: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if report.get("schema") != EXPECTED_TRIGGER_SCHEMA:
        reasons.append("trigger_report_schema_mismatch")
    if report.get("three_source_manifest_status") != "pass":
        reasons.append("three_source_manifest_status_not_pass")
    if int(report.get("capture_manifest_source_count") or 0) < 3:
        reasons.append("capture_manifest_source_count_below_three")
    if int(report.get("capture_manifest_selected_row_count") or 0) < 1:
        reasons.append("capture_manifest_selected_row_count_missing")
    if report.get("desktop_trigger_contract_status") != "pass":
        reasons.append("desktop_trigger_contract_status_not_pass")
    if report.get("future_trace_fields_status") != "pass":
        reasons.append("future_trace_fields_status_not_pass")
    if report.get("desktop_trigger_required") != EXPECTED_DESKTOP_TRIGGER:
        reasons.append("desktop_trigger_required_mismatch")
    if report.get("writer_required") != EXPECTED_WRITER:
        reasons.append("writer_required_mismatch")
    if report.get("raw_text_in_report") is not False:
        reasons.append("raw_text_in_trigger_report_not_false")
    return {
        "status": "fail" if reasons else "pass",
        "reasons": reasons,
        "selection_id": report.get("selection_id"),
        "source_id": report.get("source_id"),
        "admission_rule": "three_source_manifest_and_desktop_trigger_contract_and_no_raw_text",
    }


def _candidate_source_observations(report: dict[str, Any]) -> list[dict[str, Any]]:
    observations = report.get("observations") if isinstance(report.get("observations"), list) else []
    selected: list[dict[str, Any]] = []
    for observation in observations:
        if not isinstance(observation, dict):
            continue
        if int(observation.get("operator_score") or 0) < 4:
            continue
        if observation.get("failure_notes"):
            continue
        if not observation.get("scenario_id"):
            continue
        selected.append(observation)
    return selected


def _build_candidates(human_report: dict[str, Any], trigger_report: dict[str, Any], *, run_id: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    selection_id = str(trigger_report.get("selection_id") or "")
    for observation in _candidate_source_observations(human_report):
        scenario_id = str(observation.get("scenario_id") or "")
        source_digest = _observation_digest(observation)
        candidate_id = sha256_text(f"{run_id}|{scenario_id}|{selection_id}|{source_digest}")[:24]
        candidates.append({
            "schema": "ego_operator.operation_learning_candidate.v0",
            "candidate_id": f"olc_{candidate_id}",
            "candidate_kind": "operation_learning_candidate",
            "candidate_scope": "review_only",
            "review_state": "human_review_required",
            "source_scenario_id": scenario_id,
            "source_observation_sha256": source_digest,
            "source_trace_path": str(observation.get("trace_path") or ""),
            "trigger_selection_id": selection_id,
            "trigger_source_id": trigger_report.get("source_id"),
            "trigger_user_text_hash": trigger_report.get("user_text_hash"),
            "learning_signal": "human_reviewed_operator_score_gte_4_with_valid_desktop_trigger_contract",
            "proposed_operation": "preserve_llm_first_gate_owned_traceable_response_pattern",
            "runtime_authority": False,
            "memory_promotion_authorized": False,
            "proactive_send_authorized": False,
            "file_write_authorized": False,
            "tool_call_authorized": False,
            "network_call_authorized": False,
            "claim_ceiling": CLAIM_CEILING,
        })
    return candidates


def _observation_digest(observation: dict[str, Any]) -> str:
    digest_payload = {
        "scenario_id": observation.get("scenario_id"),
        "reply_text": observation.get("reply_text"),
        "operator_score": observation.get("operator_score"),
        "trace_path": observation.get("trace_path"),
        "subjective_notes": observation.get("subjective_notes"),
    }
    return sha256_text(json.dumps(digest_payload, ensure_ascii=False, sort_keys=True))


def _artifact_ref(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    return {
        "path": _repo_path(resolved),
        "sha256": sha256_file(resolved),
    }


def _repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _next_action(status: str) -> str:
    if status == "operation_learning_candidates_ready_for_human_review":
        return "Human operator must review operation_learning_candidates.jsonl before any runtime integration task."
    return "Clear human-review and selected-source trigger admission blockers before generating operation-learning candidates."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build default-off EgoOperator operation-learning candidate artifacts.")
    parser.add_argument("--human-report", type=Path, default=DEFAULT_HUMAN_REPORT)
    parser.add_argument("--trigger-report", type=Path, default=DEFAULT_TRIGGER_REPORT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-id", default="egooperator-operation-learning-gate-v0-local")
    args = parser.parse_args(argv)

    report = build_operation_learning_report(
        human_report_path=args.human_report,
        trigger_report_path=args.trigger_report,
        run_id=args.run_id,
    )
    write_result = write_operation_learning_artifacts(args.out, report)
    print(artifact_json_text(write_result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
