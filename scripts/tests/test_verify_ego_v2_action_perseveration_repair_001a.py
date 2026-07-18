from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.codex.verify_ego_v2_action_perseveration_repair_001a import (
    REQUIRED_ARTIFACTS,
    aggregate_checks,
    run_action_repair_verification,
    scan_forbidden_values,
)


def test_action_repair_verifier_replays_frozen_stream_and_runs_real_visual_path(tmp_path):
    output = tmp_path / "evidence"
    screenshot = tmp_path / "action-repair.png"

    result = run_action_repair_verification(output, screenshot_path=screenshot)

    assert result["verdict"] == "pass"
    assert {path.name for path in output.iterdir()} == REQUIRED_ARTIFACTS
    assert screenshot.is_file() and screenshot.stat().st_size > 0
    assert all(check["value"] is True for check in result["checks"].values())

    baseline = json.loads(
        (output / "baseline_comparison.json").read_text(encoding="utf-8")
    )
    assert baseline["frozen_old_trace"]["trailing_forage_suffix"] == 62
    assert baseline["repaired_replay"]["trailing_forage_suffix"] == 0
    assert len(baseline["repaired_replay"]["action_counts"]) >= 4
    assert baseline["always_forage_baseline"]["trailing_forage_suffix"] == 71

    ablation = json.loads(
        (output / "ablation_report.json").read_text(encoding="utf-8")
    )
    assert ablation["unfiltered_claims_with_progress_gate"]["selected_action"] == "approach"
    assert ablation["unfiltered_claims_without_progress_gate"]["selected_action"] == "forage"
    assert ablation["zero_distance_repeat"]["second_outcome"] is None
    assert ablation["zero_distance_repeat"]["second_claim_update_applied"] is False
    matched = ablation["matched_context_scoring_probe"]
    assert matched["support_by_action"] == {"approach": 0.65, "forage": -0.65}
    assert matched["context_memory_eligible"] is True
    assert matched["approach_claim_memory_bias"] != 0.0
    assert matched["approach_total_score"] != matched["memory_off_approach_total_score"]

    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    assert replay["command_count"] == 71
    assert replay["second_recompute_trace_hashes_equal"] is True
    assert replay["unused_frozen_commands"] == []

    receipt = json.loads(
        (output / "live_repair_receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["visual_verifier_verdict"] == "pass"
    assert receipt["real_tk_trigger"] is True
    assert receipt["screenshot"]["bytes"] > 0


def test_action_repair_leakage_scanner_has_real_positive_control():
    clean = {"observation": {"cue": "contact"}, "selected_action": "approach"}
    positive = {"observation": {"cue": "contact"}, "hidden_regime": "positive"}

    assert scan_forbidden_values(clean)["matches"] == []
    assert scan_forbidden_values(positive)["matches"] == ["hidden_regime"]


def test_action_repair_aggregator_fails_closed():
    assert aggregate_checks({"ok": {"value": True}})["verdict"] == "pass"
    failed = aggregate_checks(
        {"ok": {"value": True}, "counterexample": {"value": False}}
    )
    assert failed == {"verdict": "fail", "failed_checks": ["counterexample"]}
    with pytest.raises(ValueError, match="computed check"):
        aggregate_checks({"forged": True})
