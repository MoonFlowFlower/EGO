from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "codex"
    / "verify_ego_v2_visual_life_lifecycle_001a.py"
)


def _load_verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_ego_v2_visual_life_lifecycle_001a", SCRIPT
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_card_c_verifier_runs_and_writes_exact_artifacts(tmp_path: Path) -> None:
    verifier = _load_verifier()
    output = tmp_path / "evidence"

    result = verifier.run_card_c_verification(output)

    assert result["task_id"] == verifier.TASK_ID
    assert {path.name for path in output.iterdir()} == verifier.REQUIRED_ARTIFACTS
    assert result == json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert result["checks"]["declared_lifecycle_scenarios_observed"]["value"] is True
    assert result["checks"]["death_respawn_next_action_chain"]["value"] is True
    assert result["checks"]["censor_respawn_chain"]["value"] is True
    assert result["checks"]["life_four_terminal_reject"]["value"] is True
    assert result["checks"]["real_terminal_controller_sqlite_path"]["value"] is True
    assert result["checks"]["pure_respawn_carry_reset_exact"]["value"] is True
    assert result["checks"]["independent_scripted_respawn_baseline_reported"]["value"] is True
    assert result["checks"]["no_carry_ablation_executed"]["value"] is True
    assert result["checks"]["policy_projection_leakage_scan_clean_positive_control_fires"]["value"] is True
    assert result["checks"]["replay_two_fresh_processes_match"]["value"] is True
    assert result["checks"]["replay_tamper_controls_fail_closed"]["value"] is True
    assert result["checks"]["single_controller_reducer_store_path"]["value"] is True
    assert result["checks"]["recursive_provenance_present"]["value"] is True
    assert result["source_scan"]["versions"] == {
        "state": "ego.life_playground.state.v3",
        "run": "ego.life_playground.run.v3",
        "command": "ego.life_playground.command.v5",
        "trace": "ego.life_playground.trace.v7",
        "world": "ego.life_playground.microworld.state.v4",
        "policy_observation": "ego.life_playground.microworld.observation.v4",
        "observer_frame": "ego.life_playground.microworld.public_frame.v5",
        "claim_memory": "ego.life_playground.claim_memory.v2",
        "code_path_manifest": "ego.life_playground.code_path.v4",
    }

    tk_check = result["checks"]["real_tk_run_controller_sqlite_path"]
    failure = json.loads((output / "failure_manifest.json").read_text(encoding="utf-8"))
    if tk_check["value"]:
        assert result["verdict"] == "pass"
        assert failure["environment_blockers"] == []
    else:
        assert result["verdict"] == "fail"
        assert "tk_runtime_unavailable" in failure["environment_blockers"]

    baseline = json.loads((output / "baseline_comparison.json").read_text(encoding="utf-8"))
    assert baseline["baseline_id"] == "independent_scripted_respawn_baseline"
    assert baseline["disposition"] in {
        "observable_equivalence_claim_blocker",
        "non_equivalent",
    }
    assert baseline["comparisons"]
    assert baseline["independence_probe"]["value"] is True
    assert baseline["independence_probe"]["forbidden_call_findings"] == []
    assert baseline["independence_probe"]["forbidden_call_attempts"] == {
        "compute_step": 0,
        "_score_candidate": 0,
    }
    assert len(baseline["independence_probe"]["callable_source_hash"]) == 64
    if baseline["disposition"] == "observable_equivalence_claim_blocker":
        assert "scripted_respawn_observable_equivalence" in result["claim_blockers"]
        assert failure["engineering_failures"] == ([] if result["verdict"] == "pass" else ["real_tk_run_controller_sqlite_path"])

    ablation = json.loads((output / "ablation_report.json").read_text(encoding="utf-8"))
    assert set(ablation["cases"]) == {"canonical_carry", "no_carry"}
    assert all(case["invoked"] is True for case in ablation["invocation_ledger"])
    assert ablation["science_adjudication_authorized"] is False
    assert ablation["comparison"]["behavior_equivalent"] in {True, False}
    assert ablation["comparison"]["retained_memory_equivalent"] in {True, False}
    assert ablation["comparison"]["model_matches_empty_constructor"] is True
    assert ablation["comparison"]["memory_matches_empty_constructor"] is True
    assert ablation["comparison"]["model_differs_from_canonical_post_respawn"] is True
    assert ablation["comparison"]["memory_differs_from_canonical_post_respawn"] is True

    assert set(baseline["comparisons"]) == {
        "death_respawn",
        "censor_respawn",
        "life_four_terminal",
    }
    assert all(
        comparison["observable_equivalent"] is True
        for comparison in baseline["comparisons"].values()
    )
    assert all(
        component["value"] is True
        for comparison_id, comparison in baseline["comparisons"].items()
        if comparison_id != "life_four_terminal"
        for component in comparison["component_matches"].values()
    )

    leakage = json.loads((output / "leakage_report.json").read_text(encoding="utf-8"))
    assert leakage["scan_scope"] == "policy_projection_only"
    assert leakage["clean_scan"]["offenders"] == []
    assert leakage["positive_control_scan"]["positive_control_detected"] is True
    assert {item["category"] for item in leakage["positive_control_scan"]["offenders"]} == {
        "life_index",
        "seed",
        "token_mapping",
    }

    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    assert set(replay["scenarios"]) == {
        "death_respawn_next_action",
        "censor_respawn",
        "life_four_terminal",
        "terminal_controller_sqlite",
    }
    assert replay["stored_selected_actions_used_as_input"] is False
    assert all(
        scenario["fresh_process_match"]["value"] is True
        for scenario in replay["scenarios"].values()
    )
    observed_tampers = {
        tamper_id
        for scenario in replay["scenarios"].values()
        for tamper_id in scenario["tamper_controls"]
    }
    assert observed_tampers == {
        "initial_state",
        "command",
        "stored_trace",
        "carry_receipt",
        "policy_flag",
        "fourth_life_result",
    }
    assert all(
        control["value"] is True
        for scenario in replay["scenarios"].values()
        for control in scenario["tamper_controls"].values()
    )
    assert result["provenance_scan"]["offenders"] == []
    for name in {
        "result.json",
        "baseline_comparison.json",
        "ablation_report.json",
        "leakage_report.json",
        "replay_report.json",
        "failure_manifest.json",
    }:
        payload = json.loads((output / name).read_text(encoding="utf-8"))
        assert verifier.validate_recursive_provenance(payload)["offenders"] == [], name
    trace_payload = [
        json.loads(line)
        for line in (output / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert verifier.validate_recursive_provenance(trace_payload)["offenders"] == []


def test_card_c_scripted_respawn_baseline_is_independent_of_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = _load_verifier()
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
    pre_respawn = verifier._active_life_state(
        run_id="baseline-independent",
        life_index=1,
        episode_tick=1,
        energy=0.0,
    )
    pre_respawn["model"] = {"retained": {"count": 1}}
    pre_respawn["memory"]["episodic"] = [{"retained": "episode"}]
    pre_respawn["lifecycle"] = {
        "trial_status": "awaiting_respawn",
        "life_index": 1,
        "awaiting_respawn": True,
        "life_results": [
            {
                "life_index": 1,
                "survival_ticks": 1,
                "censored": False,
                "termination": "death",
            }
        ],
        "fourth_life_result": None,
    }
    terminal = verifier._active_life_state(
        run_id="baseline-terminal",
        life_index=4,
        episode_tick=255,
        energy=0.9,
    )
    terminal["lifecycle"] = {
        "trial_status": "terminal",
        "life_index": 4,
        "awaiting_respawn": False,
        "life_results": [
            {
                "life_index": index,
                "survival_ticks": 256,
                "censored": True,
                "termination": "censored",
            }
            for index in range(1, 5)
        ],
        "fourth_life_result": {"survival_ticks": 256, "censored": True},
    }

    baseline = verifier.independent_scripted_respawn_baseline(
        [pre_respawn], terminal_states=[terminal]
    )

    respawn = baseline["respawns"][0]
    expected_world = verifier.reset_world_for_life(pre_respawn["world"], 2)
    assert respawn["transition_kind"] == "respawn"
    assert respawn["policy_called"] is False
    assert respawn["life_index_after"] == 2
    assert respawn["carry_hashes"]["model"] == verifier.engine.canonical_hash(
        pre_respawn["model"]
    )
    assert respawn["carry_hashes"]["memory_episodic"] == verifier.engine.canonical_hash(
        pre_respawn["memory"]["episodic"]
    )
    assert respawn["reset_hashes"]["world"] == verifier.engine.canonical_hash(
        expected_world
    )
    assert respawn["reset_hashes"]["organism"] == verifier.engine.canonical_hash(
        verifier.BASELINE_INITIAL_ORGANISM
    )
    assert respawn["life_result"] == pre_respawn["lifecycle"]["life_results"][-1]
    assert baseline["terminal_outputs"][0]["fourth_life_result"] == {
        "survival_ticks": 256,
        "censored": True,
    }
    assert baseline["terminal_outputs"][0]["further_dispatch"] == "rejected"


def test_card_c_policy_projection_scanner_only_uses_declared_positive_controls() -> None:
    verifier = _load_verifier()
    clean_projection = {
        "schema_version": "ego.life_playground.policy_projection.v1",
        "observation": {"visual": [["self", "empty"]]},
        "current_goal": {"state_variable": "energy", "status": "active"},
    }

    clean = verifier.scan_policy_projection(clean_projection)
    positive = verifier.scan_policy_projection(
        clean_projection,
        inject_positive_control=True,
    )

    assert clean["scan_scope"] == "policy_projection_only"
    assert clean["offenders"] == []
    assert clean["positive_control_detected"] is False
    assert positive["positive_control_detected"] is True
    assert {item["category"] for item in positive["offenders"]} == {
        "life_index",
        "seed",
        "token_mapping",
    }


def test_card_c_recursive_provenance_fails_on_nested_missing_record() -> None:
    verifier = _load_verifier()
    report = verifier.validate_recursive_provenance(
        {"replay": {"comparison": {"value": True}}}
    )

    assert report["offenders"] == [
        {
            "path": "/replay/comparison",
            "reason": "missing_provenance_fields",
            "missing_fields": list(verifier.PROVENANCE_FIELDS),
        }
    ]


def test_card_c_recursive_provenance_rejects_raw_data_signal_bypass() -> None:
    verifier = _load_verifier()
    report = verifier.validate_recursive_provenance(
        {
            "comparison": {
                "record_type": verifier.RAW_DATA_RECORD_TYPE,
                "behavior_equivalent": True,
            }
        }
    )

    assert report["offenders"] == [
        {
            "path": "/comparison",
            "reason": "raw_data_contains_evidence_signal",
            "signal_keys": ["behavior_equivalent"],
        }
    ]


def test_card_c_tk_unavailable_is_explicit_blocker(tmp_path: Path) -> None:
    verifier = _load_verifier()

    def unavailable_root():
        raise verifier.tk.TclError("test display unavailable")

    report = verifier.exercise_real_tk_run(tmp_path, root_factory=unavailable_root)

    assert report["tk_available"] is False
    assert report["value"] is False
    assert report["blocker"]["blocker_id"] == "tk_runtime_unavailable"
    assert report["blocker"]["error_class"] == "TclError"


def test_card_c_artifacts_are_byte_stable_across_output_directories(tmp_path: Path) -> None:
    verifier = _load_verifier()
    output_a = tmp_path / "evidence-a"
    output_b = tmp_path / "nested" / "evidence-b"

    verifier.run_card_c_verification(output_a)
    verifier.run_card_c_verification(output_b)

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
    assert trace_ref["path"] == (
        "artifacts/EGO-V2-P0-VISUAL-LIFE-CARD-C-001A/trace.jsonl"
    )


def test_card_c_verifier_does_not_invent_carry_mode_product_api() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "carry_mode" not in source


def test_card_c_aggregate_result_fails_closed() -> None:
    verifier = _load_verifier()
    assert verifier.aggregate_result({"ok": {"value": True}})["verdict"] == "pass"
    assert verifier.aggregate_result(
        {"ok": {"value": True}, "bad": {"value": False}}
    ) == {"verdict": "fail", "failed_checks": ["bad"]}
    with pytest.raises(ValueError, match="computed check record required"):
        verifier.aggregate_result({"forged": True})
