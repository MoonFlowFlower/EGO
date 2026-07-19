from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.codex.verify_ego_v2_p0_resource_interaction_outcome_repair_001a import (
    REQUIRED_ARTIFACTS,
    aggregate_checks,
    run_resource_interaction_verification,
    scan_policy_for_resource_leakage,
)


def test_resource_interaction_verifier_emits_computed_replayable_artifacts(tmp_path):
    output = tmp_path / "evidence"

    result = run_resource_interaction_verification(output)
    first_bytes = {
        name: (output / name).read_bytes()
        for name in REQUIRED_ARTIFACTS
    }

    assert result["verdict"] == "pass"
    assert {path.name for path in output.iterdir()} == REQUIRED_ARTIFACTS
    assert {
        "stationary_positive_causal_repair",
        "negative_and_no_gain_controls",
        "resource_instance_identity_and_single_settlement",
        "hostile_baselines_diverge",
        "food_gain_ablation_energy_only",
        "resource_leakage_scan",
        "trace_bound_visual_result",
        "controller_replay_and_tamper_checks",
        "required_artifacts_present",
    } <= set(result["checks"])
    assert all(check["value"] is True for check in result["checks"].values())
    assert all(
        check["producer_function"]
        and check["input_artifacts"]
        and check["run_id"]
        and check["seed_context_episode_ids"]
        and check["aggregation_rule"]
        and check["code_path_hash"]
        for check in result["checks"].values()
    )
    for key in (
        "producer_function",
        "input_artifacts",
        "run_id",
        "seed_context_episode_ids",
        "aggregation_rule",
        "code_path_hash",
    ):
        assert result[key]

    baseline = json.loads(
        (output / "baseline_comparison.json").read_text(encoding="utf-8")
    )
    assert sum(
        isinstance(record, str) and record.startswith("trace:")
        for record in baseline["input_artifacts"]
    ) == 3
    assert len(baseline["seed_context_episode_ids"]["context_ids"]) == 3
    assert baseline["moved_only"]["candidate_food_obtained"] is True
    assert baseline["moved_only"]["baseline_food_obtained"] is False
    assert baseline["cue_only"]["negative_candidate_food_obtained"] is False
    assert baseline["cue_only"]["negative_baseline_food_obtained"] is True
    assert baseline["cue_only"]["non_forage_candidate_food_obtained"] is False
    assert baseline["cue_only"]["non_forage_baseline_food_obtained"] is True

    ablation = json.loads(
        (output / "ablation_report.json").read_text(encoding="utf-8")
    )
    assert ablation["food_gain_disabled"]["same_selected_action"] is True
    assert ablation["food_gain_disabled"]["same_resource_interaction"] is True
    assert ablation["food_gain_disabled"]["canonical_energy_after"] == 0.24
    assert ablation["food_gain_disabled"]["ablation_energy_after"] == 0.0

    leakage = json.loads(
        (output / "leakage_report.json").read_text(encoding="utf-8")
    )
    assert leakage["candidate_scan"]["leak_detected"] is False
    assert leakage["positive_control_scan"]["leak_detected"] is True
    assert leakage["positive_control_scan"]["matches"]

    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    sqlite_inputs = [
        record
        for record in replay["input_artifacts"]
        if isinstance(record, dict)
        and record.get("kind") == "ephemeral_sqlite_runtime_before_cleanup"
    ]
    assert sqlite_inputs == [
        {
            "path": "ephemeral://controller.sqlite3",
            "bytes": sqlite_inputs[0]["bytes"],
            "sha256": sqlite_inputs[0]["sha256"],
            "kind": "ephemeral_sqlite_runtime_before_cleanup",
        }
    ]
    assert replay["fresh_process_x2_matches_local_recovery"] is True
    assert replay["duplicate_command_rejected"] is True
    assert replay["resource_interaction_tamper_fail_closed"] is True
    assert "independent recomputation" in replay["resource_interaction_tamper_error"]
    assert replay["stored_trace_tamper_fail_closed"] is True
    assert replay["initial_state_tamper_fail_closed"] is True
    assert replay["local_recovery"]["trigger_sources"] == [
        "ui_step_button",
        "ui_step_button",
    ]
    assert len(set(replay["local_recovery"]["resource_instance_ids"])) == 2

    traces = [
        json.loads(line)
        for line in (output / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    stationary = next(
        record["trace"]
        for record in traces
        if record["scenario"] == "stationary_positive"
    )
    interaction = stationary["world_transition"]["resource_interaction"]
    assert stationary["schema_version"] == "ego.life_playground.trace.v6"
    assert stationary["world_transition"]["moved"] is False
    assert interaction["resolved"] is True
    assert interaction["food_obtained"] is True
    assert stationary["energy_after"] == 0.24

    no_resource = next(
        record["trace"]
        for record in traces
        if record["scenario"] == "no_resource_control"
    )
    assert no_resource["schema_version"] == "ego.life_playground.trace.v6"
    assert no_resource["selected_action"] == "forage"
    assert no_resource["food_gain"] == 0.0
    assert no_resource["metabolism"]["food_gain"] == 0.0
    assert no_resource["world_transition"]["resource_interaction"] == {
        "instance_id": None,
        "available": False,
        "attempted": True,
        "resolved": False,
        "outcome": None,
        "food_obtained": False,
        "failure_reason": "no_resource_event",
    }

    non_forage = next(
        record["trace"]
        for record in traces
        if record["scenario"] == "non_forage_control"
    )
    assert non_forage["schema_version"] == "ego.life_playground.trace.v6"
    assert non_forage["selected_action"] == "approach"
    assert non_forage["world_transition"]["outcome"] == 1.0
    assert non_forage["food_gain"] == 0.0
    assert non_forage["metabolism"]["food_gain"] == 0.0
    assert non_forage["world_transition"]["resource_interaction"][
        "failure_reason"
    ] == "resource_not_attempted"
    assert set(baseline["seed_context_episode_ids"]["context_ids"]) == {
        stationary["episode_id"],
        next(
            record["trace"]["episode_id"]
            for record in traces
            if record["scenario"] == "stationary_negative"
        ),
        non_forage["episode_id"],
    }

    ledger = [
        json.loads(line)
        for line in (output / "experiment_ledger.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert [entry["focus_iteration"] for entry in ledger] == [1, 2]
    assert [entry["changed_variable"] for entry in ledger] == [
        "resource_interaction_causal_path",
        "trace_bound_visual_result_expression",
    ]
    assert all(entry["discriminative_evidence_increased"] is True for entry in ledger)
    assert all(
        entry["producer_function"]
        and entry["input_artifacts"]
        and entry["run_id"]
        and entry["seed_context_episode_ids"]
        and entry["aggregation_rule"]
        and entry["code_path_hash"]
        for entry in ledger
    )

    source_paths = {
        Path(record["path"]).as_posix()
        for record in result["input_artifacts"]
        if isinstance(record, dict) and "path" in record
    }
    assert any(path.endswith("labs/ego_life_playground_v0/visual_console.py") for path in source_paths)

    for artifact_name in (
        "progress_checkpoint.json",
        "stage_scorecard.json",
        "failure_manifest.json",
    ):
        record = json.loads((output / artifact_name).read_text(encoding="utf-8"))
        assert record["producer_function"]
        assert record["input_artifacts"]
        assert record["run_id"]
        assert record["seed_context_episode_ids"]
        assert record["aggregation_rule"]
        assert record["code_path_hash"]

    rerun = run_resource_interaction_verification(output)
    assert rerun["verdict"] == "pass"
    assert {
        name: (output / name).read_bytes()
        for name in REQUIRED_ARTIFACTS
    } == first_bytes


def test_resource_leakage_scanner_positive_control_and_aggregator_fail_closed():
    instance_id = "d" * 64
    clean = scan_policy_for_resource_leakage(
        {"observation": {"event": "resource_appears"}}, instance_id=instance_id
    )
    positive = scan_policy_for_resource_leakage(
        {"observation": {"instance_id": instance_id}}, instance_id=instance_id
    )
    assert clean == {"leak_detected": False, "matches": []}
    assert positive["leak_detected"] is True
    assert positive["matches"] == [
        {"path": "$.observation.instance_id", "match": "forbidden_key_and_value"}
    ]
    post_outcome = scan_policy_for_resource_leakage(
        {
            "policy": {
                "resource_interaction": {
                    "food_obtained": True,
                    "failure_reason": None,
                }
            }
        },
        instance_id=instance_id,
    )
    assert post_outcome["leak_detected"] is True
    assert {match["path"] for match in post_outcome["matches"]} == {
        "$.policy.resource_interaction",
        "$.policy.resource_interaction.food_obtained",
        "$.policy.resource_interaction.failure_reason",
    }

    assert aggregate_checks({"ok": {"value": True}})["verdict"] == "pass"
    assert aggregate_checks(
        {"ok": {"value": True}, "counterexample": {"value": False}}
    ) == {"verdict": "fail", "failed_checks": ["counterexample"]}
    with pytest.raises(ValueError, match="computed check"):
        aggregate_checks({"forged": True})
