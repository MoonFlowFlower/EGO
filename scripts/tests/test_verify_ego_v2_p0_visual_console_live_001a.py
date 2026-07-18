from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.codex.verify_ego_v2_p0_visual_console_live_001a import (
    REQUIRED_ARTIFACTS,
    aggregate_visual_result,
    run_visual_verification,
    scan_forbidden_tokens,
)


def test_visual_verifier_runs_real_tk_step_run_and_writes_exact_evidence_set(tmp_path):
    output = tmp_path / "evidence"
    screenshot = tmp_path / "visual-console.png"

    result = run_visual_verification(output, screenshot_path=screenshot)

    assert result["verdict"] == "pass"
    assert set(path.name for path in output.iterdir()) == REQUIRED_ARTIFACTS
    assert screenshot.is_file() and screenshot.stat().st_size > 0
    assert all(check["value"] is True for check in result["checks"].values())
    assert result["checks"]["ui_step_calls_canonical_dispatch"]["producer_function"]
    assert result["checks"]["sqlite_committed_transition"]["value"] is True
    assert result["checks"]["fresh_process_recover"]["value"] is True
    assert result["checks"]["same_recovery_frame_all_panels"]["value"] is True
    assert result["checks"]["scheduled_waypoints_equal_trace"]["value"] is True
    assert result["checks"]["run_commit_recover_animate_lockstep"]["value"] is True
    assert result["checks"]["pause_close_zero_extra_dispatch"]["value"] is True
    assert result["checks"]["export_byte_identity"]["value"] is True
    assert result["checks"]["replay_recomputes_serialized_state_observation"]["value"] is True
    assert result["checks"]["chinese_mapping_causal_bytes_unchanged"]["value"] is True
    assert result["checks"]["private_field_leakage_scan_positive_control"]["value"] is True
    assert result["checks"]["no_second_engine_path"]["value"] is True
    assert result["checks"]["fresh_process_and_tk_non_skip"]["value"] is True
    assert result["checks"]["ux_capture_produced"]["value"] is True

    baseline = json.loads((output / "baseline_comparison.json").read_text(encoding="utf-8"))
    assert baseline["frozen_player_no_dispatch"]["committed_sequence_delta"] == 0
    assert baseline["live_visual_console"]["committed_sequence_delta"] >= 3
    ablation = json.loads((output / "ablation_report.json").read_text(encoding="utf-8"))
    assert ablation["no_op_dispatch"]["failure_observed"] is True
    assert ablation["straight_line_decoy"]["failure_observed"] is True
    assert ablation["animation_latch_held_closed"]["failure_observed"] is True
    assert ablation["id_only_translation"]["failure_observed"] is True
    assert ablation["leakage_positive_control"]["failure_observed"] is True
    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    assert replay["fresh_process"]["returncode"] == 0
    assert replay["fresh_process"]["recovered"] is True
    assert replay["recomputed_trace_equal"] is True


def test_visual_verifier_scanner_fires_on_positive_control_and_clean_source(tmp_path):
    clean = tmp_path / "clean.py"
    positive = tmp_path / "positive.py"
    clean.write_text("visible = True\n", encoding="utf-8")
    positive.write_text("hidden_regime = 'positive-control'\n", encoding="utf-8")

    clean_report = scan_forbidden_tokens(clean)
    positive_report = scan_forbidden_tokens(positive)

    assert clean_report["matches"] == []
    assert positive_report["matches"] == ["hidden_regime"]


def test_visual_verifier_aggregation_fails_closed_on_one_false_check():
    checks = {
        "a": {"value": True},
        "b": {"value": False},
    }
    assert aggregate_visual_result(checks)["verdict"] == "fail"
    assert aggregate_visual_result(checks)["failed_checks"] == ["b"]
    with pytest.raises(ValueError, match="computed check"):
        aggregate_visual_result({"forged": True})
