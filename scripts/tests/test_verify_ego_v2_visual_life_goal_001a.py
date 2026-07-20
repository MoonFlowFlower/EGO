from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "codex" / "verify_ego_v2_visual_life_goal_001a.py"


def _load_verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_ego_v2_visual_life_goal_001a", SCRIPT
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_card_b_verifier_runs_and_writes_exact_artifacts(tmp_path: Path) -> None:
    verifier = _load_verifier()
    output = tmp_path / "evidence"

    result = verifier.run_card_b_verification(output)

    assert result["task_id"] == verifier.TASK_ID
    assert result["verdict"] == "pass"
    assert {path.name for path in output.iterdir()} == verifier.REQUIRED_ARTIFACTS
    assert result == json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert result["checks"]["declared_goal_scenarios_observed"]["value"] is True
    assert result["checks"]["live_controller_sqlite_terminal_tk_payload_path"]["value"] is True
    assert result["checks"]["goal_hysteresis_completion_reentry_override_explore"]["value"] is True
    assert result["checks"]["equal_access_baseline_reported"]["value"] is True
    assert result["checks"]["real_ablations_invoked_and_load_bearing"]["value"] is True
    assert result["checks"]["goal_payload_leakage_scan_clean_positive_control_fires"]["value"] is True
    assert result["checks"]["replay_two_fresh_processes_match"]["value"] is True
    assert result["checks"]["replay_tamper_controls_fail_closed"]["value"] is True
    assert result["checks"]["recursive_provenance_present"]["value"] is True

    baseline = json.loads((output / "baseline_comparison.json").read_text(encoding="utf-8"))
    assert baseline["baseline_id"] == "equal_access_fixed_priority_fsm"
    assert baseline["disposition"] in {
        "non_equivalent",
        "equal_access_equivalent_downgrade",
    }
    assert baseline["comparisons"]

    ablation = json.loads((output / "ablation_report.json").read_text(encoding="utf-8"))
    assert set(ablation["cases"]) == {
        "canonical",
        "no_hysteresis",
        "no_novelty",
        "no_override",
    }
    assert all(case["record_type"] == verifier.EVIDENCE_RECORD_TYPE for case in ablation["cases"].values())
    assert all(case["invoked"] is True for case in ablation["invocation_ledger"])
    assert all(item["value"] is True for item in ablation["load_bearing"].values())

    leakage = json.loads((output / "leakage_report.json").read_text(encoding="utf-8"))
    assert leakage["clean_scan"]["offenders"] == []
    assert leakage["positive_control_scan"]["positive_control_detected"] is True

    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    assert set(replay["scenarios"]) >= {
        "completion",
        "carry",
        "reentry",
        "severe_initial",
        "severe_post_action",
        "explore",
        "live_controller_step",
    }
    assert all(item["fresh_process_match"]["value"] is True for item in replay["scenarios"].values())
    assert all(item["tamper_controls"]["stored_trace"]["value"] is True for item in replay["scenarios"].values())
    assert result["provenance_scan"]["offenders"] == []


def test_card_b_baseline_is_independent_of_candidate_reducer(monkeypatch) -> None:
    verifier = _load_verifier()
    access = {
        "observation": {"visual": [["self", "empty"]]},
        "organism": {
            "energy": 0.4,
            "safety": 0.6,
            "connection": 0.5,
            "stimulation": 0.4,
        },
        "current_goal": {"state_variable": "energy", "status": "active"},
    }
    monkeypatch.setattr(
        verifier.engine,
        "compute_step",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("candidate reducer called")
        ),
    )
    monkeypatch.setattr(
        verifier.engine,
        "_score_candidate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("candidate scorer called")
        ),
        raising=False,
    )

    assert verifier.equal_access_fixed_priority_fsm(access) in verifier.engine.ACTIONS


def test_card_b_goal_payload_scanner_fires_on_positive_control() -> None:
    verifier = _load_verifier()
    clean = {
        "goal_before": {"state_variable": "energy", "status": "active"},
        "goal_transition": {"reason": "hysteresis_carry"},
        "policy_projection": {"observation": {"visual": [["self", "empty"]]}},
    }

    clean_report = verifier.scan_goal_payloads(clean)
    positive = verifier.scan_goal_payloads(clean, inject_positive_control=True)

    assert clean_report["offenders"] == []
    assert clean_report["positive_control_detected"] is False
    assert positive["offenders"]
    assert positive["positive_control_detected"] is True


def test_card_b_recursive_provenance_validator_fails_closed_on_nested_missing_provenance() -> None:
    verifier = _load_verifier()
    payload = {
        "baseline": {
            "comparison": {
                "value": True,
                "note": "missing evidence provenance must fail closed",
            },
        },
    }

    report = verifier.validate_recursive_provenance(payload)

    assert report["offenders"] == [
        {
            "path": "/baseline/comparison",
            "reason": "missing_provenance_fields",
            "missing_fields": list(verifier.PROVENANCE_FIELDS),
        }
    ]


def test_card_b_recursive_provenance_validator_rejects_raw_data_signal_key() -> None:
    verifier = _load_verifier()
    payload = {
        "comparison": {
            "record_type": verifier.RAW_DATA_RECORD_TYPE,
            "failed_closed": True,
        }
    }

    report = verifier.validate_recursive_provenance(payload)

    assert report["offenders"] == [
        {
            "path": "/comparison",
            "reason": "raw_data_contains_evidence_signal",
            "signal_keys": ["failed_closed"],
        }
    ]


def test_card_b_artifacts_are_byte_stable_across_output_directories(tmp_path: Path) -> None:
    verifier = _load_verifier()
    output_a = tmp_path / "evidence-a"
    output_b = tmp_path / "nested" / "evidence-b"

    verifier.run_card_b_verification(output_a)
    verifier.run_card_b_verification(output_b)

    hashes_a = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output_a.iterdir())
    }
    hashes_b = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output_b.iterdir())
    }

    assert hashes_a == hashes_b
    for name in verifier.REQUIRED_ARTIFACTS:
        assert (output_a / name).read_bytes() == (output_b / name).read_bytes()
    result = json.loads((output_a / "result.json").read_text(encoding="utf-8"))
    trace_ref = next(
        item for item in result["input_artifacts"] if item["path"].endswith("trace.jsonl")
    )
    assert trace_ref["path"] == "artifacts/EGO-V2-P0-VISUAL-LIFE-CARD-B-001A/trace.jsonl"


def test_card_b_aggregate_result_fails_closed() -> None:
    verifier = _load_verifier()
    assert verifier.aggregate_result({"ok": {"value": True}})["verdict"] == "pass"
    failed = verifier.aggregate_result(
        {"ok": {"value": True}, "bad": {"value": False}}
    )
    assert failed == {"verdict": "fail", "failed_checks": ["bad"]}
    with pytest.raises(ValueError, match="computed check record required"):
        verifier.aggregate_result({"forged": True})
