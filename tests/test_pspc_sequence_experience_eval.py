from __future__ import annotations

import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_pspc_sequence_experience_eval.py"
HELPER_PATH = ROOT / "scripts" / "pspc_shadow_contracts.py"
DATASET_PATH = ROOT / "docs" / "codex" / "tasks" / "pspc-sequence-experience-eval-v0" / "sequence_eval_dataset_v0.jsonl"


def load_runner_module():
    assert RUNNER_PATH.exists(), "sequence experience eval runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_sequence_experience_eval", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dataset_has_required_groups_and_trigger():
    runner = load_runner_module()

    records = runner.load_dataset(DATASET_PATH)

    assert sorted(record["group_id"] for record in records) == [
        "frequent_interruption",
        "gentle_interaction",
        "late_night_care",
    ]
    assert all(len(record["history_inputs"]) == 10 for record in records)
    assert all(record["trigger"] == "我回来了。" for record in records)


def test_sequence_eval_writes_artifact_only_report(tmp_path):
    runner = load_runner_module()

    result = runner.run_sequence_experience_eval(ROOT, tmp_path, dataset_path=DATASET_PATH)

    assert result["status"] == "pass"
    assert result["verdict"] == "sequence_experience_eval_pass__manual_review_still_required"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only"
    assert result["sequence_count"] == 3
    assert result["control_count"] == 2
    assert result["enabled"] is False
    assert result["mainline_connected"] is False
    assert result["runtime_connected"] is False
    assert result["artifact_only"] is True
    assert result["next_allowed_step"] == "manual_shadow_review_go_no_go_remains_human_required"
    assert all(result["checks"].values())
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "SEQUENCE_EXPERIENCE_EVAL_REPORT.md",
        "sequence_experience_eval.json",
    ]


def test_history_records_include_state_delta_and_shadow_memory_event(tmp_path):
    runner = load_runner_module()

    result = runner.run_sequence_experience_eval(ROOT, tmp_path, dataset_path=DATASET_PATH)

    for sequence in result["sequences"]:
        assert len(sequence["history_turns"]) == 10
        for turn in sequence["history_turns"]:
            assert set(turn["state_before"]) == set(runner.STATE_KEYS)
            assert set(turn["state_delta"]) == set(runner.STATE_KEYS)
            assert set(turn["state_after"]) == set(runner.STATE_KEYS)
            assert "shadow_memory_event" in turn
            assert "memory_write" not in turn
            assert turn["shadow_memory_event"]["audit_only"] is True
            assert turn["shadow_memory_event"]["non_executable"] is True
            assert isinstance(turn["salience"], float)
            assert turn["expected_future_behavior"]
            assert turn["runtime_field_hits"] == []


def test_trigger_profiles_diverge_in_expected_directions(tmp_path):
    runner = load_runner_module()

    result = runner.run_sequence_experience_eval(ROOT, tmp_path, dataset_path=DATASET_PATH)
    by_category = {sequence["category"]: sequence for sequence in result["sequences"] + result["controls"]}
    gentle_profile = by_category["gentle_interaction"]["shadow_observation"]["trigger_behavior_profile"]
    interruption_profile = by_category["frequent_interruption"]["shadow_observation"]["trigger_behavior_profile"]
    late_profile = by_category["late_night_care"]["shadow_observation"]["trigger_behavior_profile"]
    no_history_profile = by_category["no_history"]["shadow_observation"]["trigger_behavior_profile"]
    shuffled_profile = by_category["shuffled_history"]["shadow_observation"]["trigger_behavior_profile"]

    assert gentle_profile["approach_tendency"] > gentle_profile["avoidance_tendency"]
    assert gentle_profile["dominant_tendency"] == "approach"
    assert interruption_profile["avoidance_tendency"] > gentle_profile["avoidance_tendency"] + 0.55
    assert interruption_profile["boundary_expression"] > gentle_profile["boundary_expression"] + 0.45
    assert late_profile["care_tendency"] > gentle_profile["care_tendency"] + 0.55
    assert late_profile["low_interrupt"] > interruption_profile["low_interrupt"] + 0.50
    assert no_history_profile["dominant_tendency"] == "neutral"
    assert max(
        shuffled_profile["approach_tendency"],
        shuffled_profile["avoidance_tendency"],
        shuffled_profile["care_tendency"],
    ) > 0.20
    assert shuffled_profile != gentle_profile
    assert shuffled_profile != interruption_profile
    assert shuffled_profile != late_profile


def test_runtime_authority_fields_and_side_effects_absent(tmp_path):
    runner = load_runner_module()

    result = runner.run_sequence_experience_eval(ROOT, tmp_path, dataset_path=DATASET_PATH)

    assert result["runtime_scan"]["ok"] is True
    assert result["runtime_scan"]["offenders"] == []
    assert result["side_effects"] == runner.SIDE_EFFECTS_FALSE
    assert all(value is False for value in result["side_effects"].values())
    assert runner.runtime_field_hits(result) == []


def test_sequence_runner_and_helper_do_not_import_runtime_or_side_effect_paths():
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
