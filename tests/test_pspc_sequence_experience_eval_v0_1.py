from __future__ import annotations

import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_pspc_sequence_experience_eval_v0_1.py"
HELPER_PATH = ROOT / "scripts" / "pspc_shadow_contracts.py"
BASE_DATASET_PATH = ROOT / "docs" / "codex" / "tasks" / "pspc-sequence-experience-eval-v0" / "sequence_eval_dataset_v0.jsonl"
ROBUSTNESS_DATASET_PATH = (
    ROOT / "docs" / "codex" / "tasks" / "pspc-sequence-experience-eval-v0-1" / "robustness_dataset_v0_1.jsonl"
)


def load_runner_module():
    assert RUNNER_PATH.exists(), "sequence experience eval v0.1 runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_sequence_experience_eval_v0_1", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_eval(tmp_path):
    runner = load_runner_module()
    result = runner.run_sequence_experience_eval_v0_1(
        ROOT,
        tmp_path,
        base_dataset_path=BASE_DATASET_PATH,
        robustness_dataset_path=ROBUSTNESS_DATASET_PATH,
    )
    return runner, result


def test_robustness_dataset_removes_obvious_shortcut_keywords():
    runner = load_runner_module()

    records = runner.load_robustness_dataset(ROBUSTNESS_DATASET_PATH)

    assert sorted(records) == ["frequent_interruption", "gentle_interaction", "late_night_care"]
    assert all(len(history) == 10 for history in records.values())
    for history in records.values():
        for text in history:
            for keyword in runner.OBVIOUS_KEYWORDS:
                assert keyword not in text


def test_v0_1_writes_report_json_and_manual_review_packet(tmp_path):
    _runner, result = run_eval(tmp_path)

    assert result["status"] == "pass"
    assert result["verdict"] == "sequence_experience_eval_v0_1_pass__manual_review_packet_ready"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only"
    assert result["artifact_only"] is True
    assert result["runtime_connected"] is False
    assert result["enabled"] is False
    assert result["mainline_connected"] is False
    assert result["next_allowed_step"] == "manual_shadow_review_go_no_go_remains_human_required"
    assert all(result["checks"].values())
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "MANUAL_REVIEW_PACKET.md",
        "SEQUENCE_EXPERIENCE_EVAL_V0_1_REPORT.md",
        "sequence_experience_eval_v0_1.json",
    ]


def test_paraphrase_triggers_preserve_dominant_tendency(tmp_path):
    runner, result = run_eval(tmp_path)

    assert result["trigger_variants"] == list(runner.TRIGGER_VARIANTS)
    section = result["paraphrase_trigger_robustness"]
    assert section["status"] == "pass"
    for group_id, group_result in section["category_results"].items():
        assert len(group_result["trigger_variants"]) == 4
        assert len(set(group_result["dominant_tendencies"])) == 1, group_id
        assert group_result["max_profile_distance_from_base_trigger"] == 0.0


def test_lexical_shortcut_audit_keeps_direction_without_obvious_keywords(tmp_path):
    result = run_eval(tmp_path)[1]

    section = result["lexical_shortcut_audit"]
    assert section["status"] == "pass"
    assert "category labels remain fixture authority" in section["remaining_shortcut_risk"]
    for group_result in section["category_results"].values():
        assert group_result["obvious_keyword_hits"] == []
        assert group_result["clean_dominant"] == group_result["paraphrased_dominant"]
        assert group_result["profile_distance"] <= 0.20


def test_counterfactual_deletion_high_salience_matters_more_than_low_salience(tmp_path):
    result = run_eval(tmp_path)[1]

    section = result["counterfactual_deletion"]
    assert section["status"] == "pass"
    assert section["average_high_salience_distance"] > section["average_low_salience_distance"]
    for group_result in section["category_results"].values():
        distances = group_result["profile_distances_from_full"]
        assert distances["delete_high_salience_items"] > distances["delete_low_salience_items"]
        assert distances["delete_recent_items"] > 0.12
        assert len(group_result["deleted_positions"]["high_salience"]) == 3
        assert len(group_result["deleted_positions"]["low_salience"]) == 3


def test_mixed_histories_expose_conflict_and_resolution_basis(tmp_path):
    result = run_eval(tmp_path)[1]

    section = result["mixed_history_resolution"]
    assert section["status"] == "pass"
    assert sorted(section["scenarios"]) == [
        "gentle_to_interruption",
        "interruption_to_gentle",
        "late_night_to_gentle",
        "late_night_to_interruption",
    ]
    for scenario in section["scenarios"].values():
        assert scenario["dominant_tendency"] != "neutral"
        assert scenario["conflict_score"] >= 0.5
        assert "recency_salience" in scenario["resolution_basis"]


def test_manual_review_packet_contains_human_go_no_go_checklist(tmp_path):
    run_eval(tmp_path)

    packet = (tmp_path / "MANUAL_REVIEW_PACKET.md").read_text(encoding="utf-8")

    assert "Human Checklist" in packet
    assert "shadow_memory_candidate" in packet
    assert "real memory writes" in packet
    assert "go-no-go" in packet.lower() or "go/no-go" in packet.lower()
    assert "What This Does Not Prove" in packet


def test_runtime_authority_fields_and_side_effects_absent_in_v0_1(tmp_path):
    runner, result = run_eval(tmp_path)

    assert result["runtime_scan"]["ok"] is True
    assert result["runtime_scan"]["offenders"] == []
    assert result["side_effects"] == runner.SIDE_EFFECTS_FALSE
    assert all(value is False for value in result["side_effects"].values())
    assert runner.runtime_field_hits(result) == []


def test_v0_1_runner_and_helper_do_not_import_runtime_or_side_effect_paths():
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
