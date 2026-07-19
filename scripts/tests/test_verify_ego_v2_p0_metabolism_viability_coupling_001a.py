from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.codex.verify_ego_v2_p0_metabolism_viability_coupling_001a import (
    REQUIRED_ARTIFACTS,
    aggregate_checks,
    run_metabolism_verification,
)


def test_metabolism_verifier_emits_exact_artifacts_and_passes(tmp_path):
    output = tmp_path / "evidence"

    result = run_metabolism_verification(output)

    assert result["verdict"] == "pass"
    assert {path.name for path in output.iterdir()} == REQUIRED_ARTIFACTS
    assert all(check["value"] is True for check in result["checks"].values())

    baseline = json.loads(
        (output / "baseline_comparison.json").read_text(encoding="utf-8")
    )
    assert baseline["legacy_resource_forage_negative_outcome"]["legacy_energy_after"] > baseline["legacy_resource_forage_negative_outcome"]["task_energy_after"]
    assert baseline["legacy_quiet_rest"]["legacy_energy_after"] > baseline["legacy_quiet_rest"]["task_energy_after"]

    ablation = json.loads(
        (output / "ablation_report.json").read_text(encoding="utf-8")
    )
    assert ablation["food_gain_disabled"]["canonical_food_gain"] > 0.0
    assert ablation["food_gain_disabled"]["ablation_food_gain"] == 0.0
    assert ablation["food_gain_disabled"]["ablation_energy_after"] < ablation["food_gain_disabled"]["canonical_energy_after"]

    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    assert replay["sqlite_recovery_matches_fresh_process"] is True
    assert replay["fresh_process_runs_equal"] is True
    assert replay["tamper_fail_closed"] is True

    scorecard = json.loads(
        (output / "stage_scorecard.json").read_text(encoding="utf-8")
    )
    assert scorecard["verdict"] == "pass"
    assert scorecard["focus_iteration"] == 1


def test_metabolism_verifier_aggregator_fails_closed():
    assert aggregate_checks({"ok": {"value": True}})["verdict"] == "pass"
    failed = aggregate_checks(
        {"ok": {"value": True}, "counterexample": {"value": False}}
    )
    assert failed == {"verdict": "fail", "failed_checks": ["counterexample"]}
    with pytest.raises(ValueError, match="computed check"):
        aggregate_checks({"forged": True})
