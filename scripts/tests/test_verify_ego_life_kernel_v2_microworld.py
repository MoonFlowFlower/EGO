from __future__ import annotations

import inspect
import json
from pathlib import Path
import sqlite3

import pytest

from labs.ego_life_playground_v0 import engine


def _verifier():
    from scripts.codex import verify_ego_life_kernel_v2_microworld as verifier

    return verifier


def _baseline_access(history):
    return {
        "schema_version": "ego.v2.p1.baseline_access.v1",
        "observation": {
            "cue": "quiet",
            "agent_position": "fork",
            "visible_object_ids": ["shelter"],
            "revealed_outcome": None,
        },
        "legal_actions": ["approach", "explore", "forage", "rest", "withdraw"],
        "organism": {
            "energy": 0.45,
            "safety": 0.62,
            "connection": 0.50,
            "stimulation": 0.43,
        },
        "current_goal": "stimulation",
        "public_history": history,
    }


def test_p1_independent_baselines_run_when_candidate_reducer_is_unavailable(monkeypatch):
    verifier = _verifier()
    history = [
        {"cue": "resource", "action_taken": "forage", "revealed_outcome": 1.0},
        {"cue": "contact", "action_taken": "approach", "revealed_outcome": -1.0},
    ]
    access = _baseline_access(history)
    monkeypatch.setattr(
        engine,
        "compute_step",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("candidate called")),
    )
    producers = verifier.BASELINE_PRODUCERS
    required = {
        "observation_only",
        "q_only",
        "cue_clock_fsm",
        "last_success",
        "recency_window_1",
        "recency_window_2",
        "recency_window_4",
        "exact_public_history_lookup",
        "nearest_history",
        "graph_lookup",
        "successor_map",
        "fsm_planner",
        "episodic_traversal",
        "no_update",
        "from_scratch",
        "count_table",
        "transition_table",
    }
    assert required <= set(producers)
    results = {name: producer(access) for name, producer in producers.items()}
    assert all(result in access["legal_actions"] for result in results.values())
    for producer in producers.values():
        source = inspect.getsource(producer)
        assert "compute_step" not in source
        assert "selected_action" not in source
        assert "hidden_regime" not in source
        assert "correct_action" not in source
        assert "oracle" not in source.lower()


def test_p1_leakage_scanner_rejects_live_alias_and_nested_positive_controls():
    verifier = _verifier()
    clean = {
        "schema_version": "ego.life_playground.policy_projection.v1",
        "non_memory": {
            "schema_version": "ego.life_playground.policy_non_memory_projection.v1",
            "observation": {
                "schema_version": "ego.life_playground.microworld.observation.v2",
                "event": "quiet_interval",
                "cue": "quiet",
                "summary": "quiet",
                "agent_position": "fork",
                "visible_object_ids": ["shelter"],
                "revealed_outcome": None,
            },
            "organism": {"energy": 0.5},
            "current_goal": {"state_variable": "energy"},
            "legal_actions": ["forage", "approach"],
            "model": {},
        },
        "claim_retrieval": {"claims": [], "support_by_action": {}},
    }
    assert verifier.scan_policy_projection(clean)["offenders"] == []
    controls = {
        "hidden_regime": ({"hidden_regime": "site_a_high"}, "hidden_regime", "/hidden_regime"),
        "renamed_hidden_regime": ({"latent_mode": "site_a_high"}, "hidden_regime", "/latent_mode"),
        "nested_correct_action": (
            {"nested": {"target_action": "forage"}},
            "correct_action",
            "/nested/target_action",
        ),
        "future_outcome": ({"next_outcome": 1.0}, "future_outcome", "/next_outcome"),
        "reward_label": (
            {"labels": {"utility_label": "positive"}},
            "reward_label",
            "/labels/utility_label",
        ),
        "oracle": ({"answer_key": "site_a"}, "oracle", "/answer_key"),
    }
    for control_id, (injected, expected_category, expected_suffix) in controls.items():
        candidate = json.loads(json.dumps(clean))
        candidate["non_memory"]["observation"]["positive_control"] = injected
        scan = verifier.scan_policy_projection(candidate)
        assert scan["offenders"], control_id
        assert any(
            offender["category"] == expected_category
            and offender["path"].endswith(expected_suffix)
            and offender["reason"] == "forbidden_key_or_alias"
            for offender in scan["offenders"]
        ), control_id
        assert scan["positive_control_detected"] is True


def test_p1_callable_verifier_generates_recomputed_reports_without_learning_report(tmp_path):
    verifier = _verifier()
    output = tmp_path / "p1-evidence"
    result = verifier.run_p1_verification(output)

    required = {
        "continuity.sqlite3",
        "trace.jsonl",
        "product_trigger_receipt.json",
        "headroom_report.json",
        "collision_record.json",
        "baseline_comparison.json",
        "ablation_report.json",
        "replay_report.json",
        "leakage_report.json",
        "failure_manifest.json",
        "claim_ceiling.txt",
        "result.json",
    }
    assert required <= {path.name for path in output.iterdir()}
    assert not (output / "learning_report.json").exists()
    stored_result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert stored_result == result
    assert stored_result["verdict"] == "memory_conditioned_effect_observed_but_control_equivalent"
    assert stored_result["claim_status"] == "bounded_negative_for_mechanism_non_equivalence"
    assert stored_result["blocking_failures"] == []
    assert "control_baseline_equivalent" in stored_result["claim_blockers"]
    assert "freeze_downstream_contrast_inert_side_a" in stored_result["claim_blockers"]
    assert stored_result["frozen_config"]["provenance_shuffle_seed"] == 17
    assert stored_result["frozen_config"]["pair_policy_seed"] == 101
    assert set(stored_result["frozen_config_usage"]) == set(
        stored_result["frozen_config"]
    )
    assert all(
        item["used"] is True
        for item in stored_result["frozen_config_usage"].values()
    )
    assert all(
        record["trace_hash"] and record["state_after_hash"]
        for record in stored_result["intervention_output_registry"].values()
    )
    assert stored_result["switches"] == {
        "enabled": False,
        "default_enabled": False,
        "mainline_connected": False,
        "runtime_authority": "none",
        "science_weight": 0,
        "remote_anchor": False,
        "proactive_action_enabled": False,
        "background_dispatch": False,
        "llm": "forbidden",
        "network": "forbidden",
    }

    baseline = json.loads((output / "baseline_comparison.json").read_text(encoding="utf-8"))
    assert baseline["strongest_matching_control"] in {
        "last_success",
        "count_table",
        "transition_table",
        "exact_public_history_lookup",
    }
    assert baseline["strongest_match_rate"] == 1.0
    assert all(record["invoked"] is True for record in baseline["invocation_ledger"])
    assert all(record["input_access_hash"] for record in baseline["invocation_ledger"])
    no_update = next(
        item for item in baseline["comparisons"] if item["baseline_id"] == "no_update"
    )
    assert no_update["access_contract"] == {
        "algorithm": "fixed_untrained_prior_total_deficit_reduction_minus_cost",
        "public_inputs": ["organism", "legal_actions"],
        "updates": "none",
    }

    ablation = json.loads((output / "ablation_report.json").read_text(encoding="utf-8"))
    assert ablation["memory_off"]["paired_difference_removed"] is True
    for ablation_id in ("q_only", "from_scratch"):
        arm = ablation[ablation_id]
        assert set(arm["sides"]) == {"a", "b"}
        assert all(arm["sides"][side]["trace_hash"] for side in ("a", "b"))
        assert all(arm["sides"][side]["state_after_hash"] for side in ("a", "b"))
    assert ablation["freeze_updates"]["model_bytes_preserved"] is True
    assert ablation["freeze_updates"]["claim_and_event_bytes_preserved"] is True
    assert ablation["freeze_updates"]["world_transition_active"] is True
    assert ablation["freeze_updates"]["matched_streams_present"] is True
    assert all(ablation["freeze_updates"]["step1_matched_by_side"].values())
    assert all(
        ablation["freeze_updates"]["enabled_step1_update_applied_by_side"].values()
    )
    assert all(ablation["freeze_updates"]["step2_observation_equal_by_side"].values())
    assert ablation["freeze_updates"]["later_total_score_contrast_by_side"] == {
        "a": False,
        "b": True,
    }
    assert ablation["freeze_updates"]["later_prediction_contrast_by_side"] == {
        "a": False,
        "b": False,
    }
    assert ablation["freeze_updates"]["later_action_contrast_by_side"] == {
        "a": False,
        "b": False,
    }
    assert ablation["freeze_updates"]["later_prediction_or_total_score_contrast_by_side"] == {
        "a": False,
        "b": True,
    }
    for side in ("a", "b"):
        downstream = ablation["freeze_updates"]["later_downstream_by_side"][side]
        assert set(downstream) == {
            "enabled_total_score_vector",
            "frozen_total_score_vector",
            "total_score_contrast",
            "enabled_prediction_vector",
            "frozen_prediction_vector",
            "prediction_contrast",
            "enabled_selected_action",
            "frozen_selected_action",
            "selected_action_contrast",
        }
        assert downstream["total_score_contrast"] is (side == "b")
        assert downstream["prediction_contrast"] is False
        assert downstream["selected_action_contrast"] is False
    assert set(ablation["freeze_updates"]["streams"]) == {"a", "b"}
    assert all(
        len(ablation["freeze_updates"]["streams"][side][mode]["outputs"]) == 3
        for side in ("a", "b")
        for mode in ("enabled", "frozen")
    )
    assert all(
        ablation["freeze_updates"]["streams"][side]["frozen"][
            "terminal_model_matches_initial"
        ]
        and ablation["freeze_updates"]["streams"][side]["frozen"][
            "terminal_memory_matches_initial"
        ]
        for side in ("a", "b")
    )
    assert ablation["shuffle_provenance"]["event_value_multiset_preserved"] is True
    assert ablation["shuffle_provenance"]["seed"] == 17
    assert ablation["shuffle_provenance"]["persisted_memory_unchanged_before_current_write"] is True
    assert (
        ablation["shuffle_provenance"]["unaffected_fields_hash_before"]
        == ablation["shuffle_provenance"]["unaffected_fields_hash_after"]
    )
    assert ablation["shuffle_provenance"]["support_effect_changed"] is True
    assert ablation["source_deletion"]["relevant_changed_action"] is True
    assert ablation["source_deletion"]["irrelevant_inert"] is True

    replay = json.loads((output / "replay_report.json").read_text(encoding="utf-8"))
    assert replay["recomputed_from_serialized_state_and_commands"] is True
    assert replay["stored_action_used_as_input"] is False
    assert len(replay["tamper_controls"]) >= 4
    assert all(control["failed_closed"] for control in replay["tamper_controls"])

    headroom = json.loads((output / "headroom_report.json").read_text(encoding="utf-8"))
    assert headroom["contrast_type"] == "counterfactual_memory_lineage_transplant"
    assert headroom["reachable_state_claim"] is False
    assert all(
        pointer == "/memory" or pointer.startswith("/memory/")
        for transplant in headroom["transplants"].values()
        for pointer in transplant["changed_json_pointers"]
    )
    assert set(headroom["source_history_runs"]) == {"a", "b"}

    with sqlite3.connect(output / "continuity.sqlite3") as connection:
        run_ids = {
            row[0]
            for row in connection.execute("SELECT run_id FROM runs").fetchall()
        }
        assert {"p1-history-a", "p1-history-b", "p1-pair-a", "p1-pair-b"} <= run_ids
        assert connection.execute(
            "SELECT COUNT(*) FROM commands WHERE run_id IN ('p1-history-a','p1-history-b')"
        ).fetchone()[0] == 4

    trace_records = [
        json.loads(line)
        for line in (output / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert {record.get("run_id") for record in trace_records} >= {
        "p1-history-a",
        "p1-history-b",
        "p1-pair-a",
        "p1-pair-b",
    }
    assert any(
        record.get("record_type") == "command"
        and record.get("run_id") == "p1-history-a"
        for record in trace_records
    )


def test_p1_result_aggregation_blocks_unused_frozen_inputs():
    verifier = _verifier()
    reports = verifier.make_minimal_aggregation_fixture()
    result = verifier.aggregate_p1_result(reports)
    assert result["verdict"] == "evidence_invalid__unused_frozen_input"
    assert "missing_frozen_config" in result["blocking_failures"]
    assert any(
        item.startswith("missing_intervention_output:")
        for item in result["blocking_failures"]
    )


def test_p1_result_aggregation_rejects_declared_booleans_without_step_outputs():
    verifier = _verifier()
    reports = verifier.make_minimal_aggregation_fixture()
    reports.update(
        {
            "memory_effect_observed": True,
            "memory_off_removed": True,
            "source_deletion_effect": True,
            "shuffle_effect": True,
            "replay_valid": True,
            "leakage_valid": True,
            "strongest_control_match_rate": 1.0,
        }
    )
    result = verifier.aggregate_p1_result(reports)
    assert result["claim_status"] == "invalid"
    assert any(
        item.startswith("missing_intervention_output:")
        for item in result["blocking_failures"]
    )


def test_p1_real_aggregation_rejects_one_removed_actual_step_result():
    verifier = _verifier()
    pair = verifier._paired_runs()
    baseline = verifier._baseline_report(pair, [])
    ablation = verifier._ablation_report(pair, [])
    actual = verifier._collect_actual_step_results(pair)
    removed = actual.pop("Q_only:b")
    assert isinstance(removed, engine.StepResult)
    result = verifier.aggregate_p1_result(
        {
            "frozen_config": verifier._load_frozen_config(),
            "pair": pair,
            "actual_step_results": actual,
            "headroom": {},
            "baseline": baseline,
            "ablation": ablation,
            "replay": {},
            "leakage": {},
        }
    )
    assert "missing_intervention_output:Q_only:b" in result["blocking_failures"]


def test_p1_aggregation_recomputes_freeze_contrast_from_explicit_vectors():
    verifier = _verifier()
    pair = verifier._paired_runs()
    ablation = verifier._ablation_report(pair, [])
    ablation["freeze_updates"][
        "later_prediction_or_total_score_contrast_by_side"
    ] = {"a": True, "b": True}
    result = verifier.aggregate_p1_result(
        {
            "frozen_config": verifier._load_frozen_config(),
            "pair": pair,
            "actual_step_results": verifier._collect_actual_step_results(pair),
            "headroom": {},
            "baseline": verifier._baseline_report(pair, []),
            "ablation": ablation,
            "replay": {},
            "leakage": {},
        }
    )
    assert "freeze_downstream_contrast_inert_side_a" in result["claim_blockers"]
    assert (
        "freeze_downstream_contrast_report_mismatch:a"
        in result["blocking_failures"]
    )


def test_p1_leakage_artifact_cannot_pass_on_schema_rejection_alone(monkeypatch):
    verifier = _verifier()
    pair = verifier._paired_runs()
    aliases = {key: set(values) for key, values in verifier._FORBIDDEN_ALIASES.items()}
    aliases["hidden_regime"].remove("latent_mode")
    monkeypatch.setattr(verifier, "_FORBIDDEN_ALIASES", aliases)
    report = verifier._leakage_report(pair, [])
    renamed = report["positive_controls"]["renamed_hidden_regime"]
    assert any(item["category"] == "schema" for item in renamed["offenders"])
    assert renamed["expected_alias_detected"] is False
    assert report["positive_controls_fired"] is False


def test_p1_baseline_algorithms_are_distinct_on_hostile_public_history():
    verifier = _verifier()
    access = _baseline_access(
        [
            {
                "cue": "resource",
                "next_cue": "quiet",
                "action_taken": "forage",
                "revealed_outcome": 1.0,
            },
            {
                "cue": "contact",
                "next_cue": "quiet",
                "action_taken": "approach",
                "revealed_outcome": -1.0,
            },
        ]
    )
    exact = verifier.baseline_exact_public_history_lookup(access)
    count = verifier.baseline_count_table(access)
    nearest = verifier.baseline_nearest_history(access)
    graph = verifier.baseline_graph_lookup(access)
    episodic = verifier.baseline_episodic_traversal(access)
    assert exact == "approach"
    assert count == "forage"
    assert len({exact, count, nearest, graph, episodic}) >= 2


def test_p1_no_update_is_an_independent_untrained_prior_scorer_not_q_goal_lookup(
    monkeypatch,
):
    verifier = _verifier()
    access = _baseline_access([])
    access["current_goal"] = "stimulation"
    access["organism"] = {
        "energy": 0.05,
        "safety": 0.71,
        "connection": 0.71,
        "stimulation": 0.40,
    }
    q_action = verifier.baseline_q_only(access)
    no_update_scores = verifier.baseline_no_update_scores(access)
    no_update_action = verifier.baseline_no_update(access)

    assert q_action == "explore"
    assert no_update_action == max(
        sorted(no_update_scores), key=lambda action: no_update_scores[action]
    )
    assert no_update_action == "forage"
    assert no_update_action != q_action
    assert set(no_update_scores) == set(access["legal_actions"])
    changed_history = json.loads(json.dumps(access))
    changed_history["public_history"] = [
        {
            "cue": "quiet",
            "action_taken": "withdraw",
            "revealed_outcome": 1.0,
        }
    ]
    changed_history["current_goal"] = "connection"
    monkeypatch.setattr(
        verifier,
        "baseline_q_only",
        lambda _access: (_ for _ in ()).throw(AssertionError("q-only called")),
    )
    assert verifier.baseline_no_update(changed_history) == no_update_action


def test_p1_verifier_artifacts_are_byte_deterministic_across_output_roots(tmp_path):
    verifier = _verifier()
    first = tmp_path / "root-a"
    second = tmp_path / "root-b"
    verifier.run_p1_verification(first)
    verifier.run_p1_verification(second)
    canonical = (
        verifier.REPO_ROOT
        / "artifacts/EGO-LIFE-KERNEL-V2-MICROWORLD-MEMORY-CAUSALITY-001A"
    )
    assert canonical.is_dir()
    first_files = {path.name: path.read_bytes() for path in first.iterdir()}
    second_files = {path.name: path.read_bytes() for path in second.iterdir()}
    canonical_files = {
        path.name: path.read_bytes()
        for path in canonical.iterdir()
        if path.name in first_files
    }
    assert first_files == second_files
    assert first_files == canonical_files

    logical_ids = {
        "generated://p1/continuity.sqlite3",
        "generated://p1/trace.jsonl",
        "authority://p1/mutation-scope",
    }
    observed_logical_ids = set()

    def collect_artifact_labels(value):
        if isinstance(value, dict):
            artifacts = value.get("input_artifacts")
            if isinstance(artifacts, list):
                for artifact in artifacts:
                    if isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
                        observed_logical_ids.add(artifact["path"])
            for item in value.values():
                collect_artifact_labels(item)
        elif isinstance(value, list):
            for item in value:
                collect_artifact_labels(item)

    for root in (canonical, first, second):
        for path in root.iterdir():
            if path.suffix not in {".json", ".jsonl"}:
                continue
            text = path.read_text(encoding="utf-8")
            for forbidden_root in (
                str(root),
                root.as_posix(),
                json.dumps(str(root))[1:-1],
            ):
                assert forbidden_root not in text
            if path.suffix == ".json":
                collect_artifact_labels(json.loads(text))
            else:
                for line in text.splitlines():
                    collect_artifact_labels(json.loads(line))
    assert observed_logical_ids == logical_ids


def test_p1_every_score_and_contrast_has_computed_provenance(tmp_path):
    verifier = _verifier()
    output = tmp_path / "provenance"
    verifier.run_p1_verification(output)
    required_fields = {
        "producer_function",
        "input_artifacts",
        "run_id",
        "seed_context_episode_ids",
        "aggregation_rule",
        "code_path_hash",
    }
    for name in ("baseline_comparison.json", "ablation_report.json", "result.json"):
        payload = json.loads((output / name).read_text(encoding="utf-8"))
        records = verifier.collect_evidence_records(payload)
        assert records, name
        assert all(required_fields <= set(record) for record in records), name
