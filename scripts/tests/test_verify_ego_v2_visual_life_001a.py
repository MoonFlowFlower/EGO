from __future__ import annotations

import ast
import importlib.util
import inspect
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "codex" / "verify_ego_v2_visual_life_001a.py"


def _load_verifier():
    spec = importlib.util.spec_from_file_location("verify_ego_v2_visual_life_001a", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_full_run_writes_exact_artifacts_and_reports_baseline_status(tmp_path):
    verifier = _load_verifier()
    output = tmp_path / "evidence"

    result = verifier.run_card_a_verification(output)

    assert result["task_id"] == verifier.TASK_ID
    assert {path.name for path in output.iterdir()} == verifier.REQUIRED_ARTIFACTS
    assert result == json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert result["checks"]["schema_versions_match_contract"]["value"] is True
    assert result["checks"]["action_boundary_matches_contract"]["value"] is True
    assert result["checks"]["real_trigger_step_and_run_path"]["value"] is True
    assert result["checks"]["replay_two_fresh_processes_match"]["value"] is True
    assert result["checks"]["tamper_controls_fail_closed"]["value"] is True
    assert result["checks"]["policy_projection_leakage_scan_clean"]["value"] is True
    assert result["checks"]["policy_projection_positive_control_fires"]["value"] is True
    assert result["checks"]["single_path_dispatch_only"]["value"] is True
    assert result["checks"]["recursive_provenance_present"]["value"] is True

    baseline = json.loads((output / "baseline_comparison.json").read_text(encoding="utf-8"))
    assert {item["baseline_id"] for item in baseline["invocation_ledger"]} == {
        "hash_policy",
        "visual_lookup_countq",
    }
    assert baseline["strongest_baseline"] in {"hash_policy", "visual_lookup_countq"}
    assert baseline["disposition"] in {"non_equivalent", "equal_access_equivalent_downgrade"}
    assert baseline["comparisons"]

    ablation = json.loads((output / "ablation_report.json").read_text(encoding="utf-8"))
    assert set(ablation["cases"]) == {
        "canonical",
        "memory_off",
        "update_freeze",
        "no_occlusion",
        "fixed_position",
    }
    assert all(case["invoked"] is True for case in ablation["invocation_ledger"])

    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    assert set(replay["contexts"]) == {"cross_seed_1701", "offset_seed_1709"}
    assert replay["stored_selected_action_comparison_only"] is True
    for context_id, context in replay["contexts"].items():
        assert context["fresh_process_runs_equal"] is True
        assert context["local_vs_fresh_equal"] is True
        assert set(context["tamper_controls"]) == {
            "initial_state",
            "command_payload",
            "trace_selected_action",
            "trace_prev_hash",
        }
        assert all(control["failed_closed"] for control in context["tamper_controls"].values())

    receipt = json.loads((output / "live_ui_receipt.json").read_text(encoding="utf-8"))
    assert receipt["tk_available"] is True
    assert receipt["step_triggered"] is True
    assert receipt["run_triggered"] is True
    assert receipt["paused_at_command_count"] >= 3
    assert receipt["sqlite_command_count"] == receipt["sqlite_trace_count"]
    assert receipt["displayed_sequence"] == receipt["sqlite_command_count"]


def test_recursive_provenance_collector_finds_nested_records(tmp_path):
    verifier = _load_verifier()
    payload = {
        "producer_function": "root",
        "input_artifacts": [{"path": str(tmp_path / "a.txt"), "sha256": "0" * 64, "bytes": 0}],
        "run_id": "run",
        "seed_context_episode_ids": {"seed": 1},
        "aggregation_rule": "rule",
        "code_path_hash": "1" * 64,
        "engine_code_path_hash": "2" * 64,
        "verifier_source_hash": "3" * 64,
        "child": {
            "producer_function": "child",
            "input_artifacts": [],
            "run_id": "run",
            "seed_context_episode_ids": {"seed": 1},
            "aggregation_rule": "rule",
            "code_path_hash": "1" * 64,
            "engine_code_path_hash": "2" * 64,
            "verifier_source_hash": "3" * 64,
        },
    }
    records = verifier.collect_evidence_records(payload)
    assert [record["producer_function"] for record in records] == ["root", "child"]


def test_baselines_are_independent_of_candidate_compute_step_and_scorer(monkeypatch):
    verifier = _load_verifier()
    access = {
        "observation": {"visual": [["self"]]},
        "organism": {"energy": 0.4, "safety": 0.6, "connection": 0.5, "stimulation": 0.4},
        "current_goal": {"state_variable": "energy"},
        "legal_actions": ["turn_left", "turn_right", "move_forward", "interact", "rest"],
    }
    train = [
        {
            "access": access,
            "selected_action": "rest",
            "utility_by_action": {"rest": 0.01},
        }
    ]
    monkeypatch.setattr(
        verifier.engine,
        "compute_step",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("candidate reducer called")),
    )
    monkeypatch.setattr(
        verifier.engine,
        "_score_candidate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("candidate scorer called")),
        raising=False,
    )

    assert verifier.baseline_hash_policy(access)["selected_action"] in access["legal_actions"]
    assert (
        verifier.baseline_visual_lookup_countq(train, access)["selected_action"]
        in access["legal_actions"]
    )


def test_policy_projection_scanner_positive_control_and_clean_case():
    verifier = _load_verifier()
    clean = {
        "observation": {"visual": [["self", "empty"]]},
        "organism": {"energy": 0.4},
        "current_goal": {"state_variable": "energy"},
        "memory_summary": {"episodic_count": 0},
    }

    clean_report = verifier.scan_policy_projection(clean)
    positive = verifier.scan_policy_projection(clean, inject_positive_control=True)

    assert clean_report["offenders"] == []
    assert clean_report["positive_control_detected"] is False
    assert positive["offenders"]
    assert positive["positive_control_detected"] is True
    assert {item["category"] for item in positive["offenders"]} >= {
        "semantic_event",
        "absolute_position",
        "seed_or_life_id",
        "trace_lineage",
    }


def test_policy_projection_scanner_detects_forbidden_scalar_and_list_value_payloads():
    verifier = _load_verifier()
    leaky = {
        "observation": {
            "visual": [["self", "empty"]],
            "note": "resource_appears at [3,1]",
            "encoded": ["episode-000001-aa", "cmd: " + ("1" * 64)],
        },
        "current_goal": {"state_variable": "energy"},
    }

    report = verifier.scan_policy_projection(leaky)

    assert {item["reason"] for item in report["offenders"]} >= {
        "forbidden_scalar_value_pattern",
        "forbidden_list_value_pattern",
    }
    assert {item["category"] for item in report["offenders"]} >= {
        "semantic_event",
        "absolute_position",
        "seed_or_life_id",
        "trace_lineage",
    }


def test_ablation_suite_invokes_real_compute_step(monkeypatch, tmp_path):
    verifier = _load_verifier()
    dataset = verifier.collect_real_run_dataset(tmp_path / "dataset")
    calls: list[str] = []
    original = verifier.engine.compute_step

    def wrapped(*args, **kwargs):
        calls.append("compute_step")
        return original(*args, **kwargs)

    monkeypatch.setattr(verifier.engine, "compute_step", wrapped)
    report = verifier.build_ablation_report(dataset["contexts"])

    assert calls
    assert set(report["cases"]) == {
        "canonical",
        "memory_off",
        "update_freeze",
        "no_occlusion",
        "fixed_position",
    }


def test_replay_report_executes_tamper_controls(tmp_path):
    verifier = _load_verifier()
    dataset = verifier.collect_real_run_dataset(tmp_path / "dataset")
    replay = verifier.build_replay_report(dataset["contexts"])

    assert set(replay["contexts"]) == {"cross_seed_1701", "offset_seed_1709"}
    assert replay["stored_selected_action_comparison_only"] is True
    assert all(
        context["fresh_process_runs_equal"] is True
        and context["local_vs_fresh_equal"] is True
        and all(control["failed_closed"] for control in context["tamper_controls"].values())
        for context in replay["contexts"].values()
    )


def test_single_path_scan_covers_terminal_and_runner_files():
    verifier = _load_verifier()

    report = verifier._single_path_report()

    assert set(report["scanned_files"]) >= {
        "controller.py",
        "visual_console.py",
        "terminal.py",
        "run_ego_life_playground_v0.py",
    }
    assert report["pass"] is True
    assert report["controller_dispatch_compute_step_calls"] == 1
    assert report["controller_dispatch_append_step_calls"] == 1


def test_direct_forbidden_calls_detects_name_and_attribute_invocations():
    verifier = _load_verifier()
    tree = ast.parse(
        "compute_step(state, cmd, meta)\n"
        "engine.compute_step(state, cmd, meta)\n"
        "store.append_step(command, trace)\n"
        "helper.safe_call()\n"
    )

    calls = verifier._direct_forbidden_calls(tree)

    assert calls == ["compute_step", "engine.compute_step", "store.append_step"]


def test_aggregate_result_rejects_noncomputed_records():
    verifier = _load_verifier()
    assert verifier.aggregate_result({"ok": {"value": True}}, acceptance_gate_ids=["ok"])["verdict"] == "pass"
    failed = verifier.aggregate_result(
        {"ok": {"value": True}, "bad": {"value": False}},
        acceptance_gate_ids=["ok", "bad"],
    )
    assert failed["verdict"] == "fail"
    assert failed["failed_checks"] == ["bad"]
    with pytest.raises(ValueError, match="computed check record required"):
        verifier.aggregate_result({"forged": True}, acceptance_gate_ids=["forged"])


def test_source_does_not_use_static_verdict_dictionary():
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    aggregate_source = inspect.getsource(_load_verifier().aggregate_result)
    assert "failed_checks" in aggregate_source
    assert "\"pass\"" in aggregate_source and "\"fail\"" in aggregate_source
    assert "STATIC_VERDICT" not in source
    assert not any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and "verdict" in target.id.lower() for target in node.targets)
        and isinstance(node.value, ast.Dict)
        for node in ast.walk(tree)
    )
