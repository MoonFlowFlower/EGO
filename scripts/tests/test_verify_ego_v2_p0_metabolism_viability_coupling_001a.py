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
    assert (
        baseline["legacy_resource_forage_negative_outcome"]["legacy_energy_after"]
        > baseline["legacy_resource_forage_negative_outcome"]["task_energy_after"]
    )
    assert (
        baseline["legacy_quiet_rest"]["legacy_energy_after"]
        > baseline["legacy_quiet_rest"]["task_energy_after"]
    )

    ablation = json.loads(
        (output / "ablation_report.json").read_text(encoding="utf-8")
    )
    assert ablation["food_gain_disabled"]["canonical_food_gain"] > 0.0
    assert ablation["food_gain_disabled"]["ablation_food_gain"] == 0.0
    assert (
        ablation["food_gain_disabled"]["ablation_energy_after"]
        < ablation["food_gain_disabled"]["canonical_energy_after"]
    )

    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    assert replay["sqlite_recovery_matches_fresh_process"] is True
    assert replay["fresh_process_runs_equal"] is True
    assert replay["tamper_fail_closed"] is True
    sqlite_probe = replay["sqlite_probe"]
    assert sqlite_probe["fresh_process_x2_matches_local_recovery"] is True
    assert sqlite_probe["fresh_process_summaries"] == [
        sqlite_probe["local_recovery_summary"],
        sqlite_probe["local_recovery_summary"],
    ]
    assert sqlite_probe["stored_trace_tamper_fail_closed"] is True
    assert sqlite_probe["initial_state_tamper_fail_closed"] is True

    trace_records = [
        json.loads(line)
        for line in (output / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    zero_distance = next(
        record["trace"]
        for record in trace_records
        if record["scenario"] == "zero_distance_resource"
    )
    assert zero_distance["world_transition"]["moved"] is False
    assert zero_distance["food_gain"] == 0.0

    input_paths = {
        Path(item["path"]).as_posix()
        for item in result["input_artifacts"]
        if isinstance(item, dict) and "path" in item
    }
    assert any(path.endswith("labs/ego_life_playground_v0/engine.py") for path in input_paths)
    assert any(path.endswith("labs/ego_life_playground_v0/microworld.py") for path in input_paths)
    assert any(path.endswith("labs/ego_life_playground_v0/store.py") for path in input_paths)
    assert any(
        path.endswith(
            "docs/codex/tasks/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A.md"
        )
        for path in input_paths
    )

    ledger = [
        json.loads(line)
        for line in (output / "experiment_ledger.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert [entry["focus_iteration"] for entry in ledger] == [1, 2]
    assert [entry["changed_variable"] for entry in ledger] == [
        "metabolism_viability_coupling",
        "fresh_process_replay_and_tamper_provenance",
    ]

    scorecard = json.loads(
        (output / "stage_scorecard.json").read_text(encoding="utf-8")
    )
    assert scorecard["verdict"] == "pass"
    assert scorecard["focus_iteration"] == 2


def test_metabolism_verifier_aggregator_fails_closed():
    assert aggregate_checks({"ok": {"value": True}})["verdict"] == "pass"
    failed = aggregate_checks(
        {"ok": {"value": True}, "counterexample": {"value": False}}
    )
    assert failed == {"verdict": "fail", "failed_checks": ["counterexample"]}
    with pytest.raises(ValueError, match="computed check"):
        aggregate_checks({"forged": True})
