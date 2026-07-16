from __future__ import annotations

from copy import deepcopy
import inspect
import json
from pathlib import Path
import sqlite3

import pytest

from labs.ego_life_playground_v0 import engine
from labs.ego_life_playground_v0.store import RecoveryFrame, RecoveryResult


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


def _p2_control_arm(
    verifier,
    *,
    arm_id,
    control_id,
    layout_id,
    context_id,
    train_world_seed=30,
):
    config = verifier._load_frozen_p2_config()
    context = next(
        item for item in config["heldout_contexts"] if item["context_id"] == context_id
    )
    return {
        "arm_id": arm_id,
        "control_id": control_id,
        "train_world_seed": train_world_seed,
        "context_id": context_id,
        "world_seed": context["world_seed"],
        "layout_id": layout_id,
        "schedule": config["heldout_event_schedules"][context["event_schedule_id"]],
        "train_public_history": [],
        "reference_episodes": [],
    }


def _hostile_leaf_value(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 100
    if isinstance(value, float):
        return value + 0.125
    if isinstance(value, str):
        return value + "__hostile"
    if isinstance(value, list):
        return list(reversed(value)) + [{"hostile": True}]
    if isinstance(value, dict):
        return {**deepcopy(value), "hostile": ["unused"]}
    raise AssertionError(type(value))


@pytest.fixture(scope="module")
def _p2_actual_usage_fixture(tmp_path_factory):
    verifier = _verifier()
    output = tmp_path_factory.mktemp("p2-actual-usage")
    verifier.run_p2_verification(output)
    learning = json.loads((output / "learning_report.json").read_text(encoding="utf-8"))
    return verifier, verifier._load_frozen_p2_config(), learning[
        "frozen_config_binding"
    ]["actual_usage_ledger"]


def test_p2_exact_history_uses_one_public_projection_with_match_and_fallback_provenance():
    verifier = _verifier()
    reference = [
        {
            "sequence": 91,
            "episode_index": 4,
            "observation_hash": "private-noise-a",
            "context_key": "private-noise-b",
            "layout_id": "p2_vertical_v1",
            "event": "resource_appears",
            "cue": "resource",
            "next_cue": "quiet",
            "action_taken": "forage",
            "revealed_outcome": 1.0,
        },
        {
            "sequence": 92,
            "episode_index": 4,
            "layout_id": "p2_vertical_v1",
            "event": "quiet_interval",
            "cue": "quiet",
            "next_cue": None,
            "action_taken": "rest",
            "revealed_outcome": None,
        },
    ]
    query = [
        {
            "layout_id": "p2_offset_v1",
            "event": "threat_nearby",
            "cue": "threat",
            "next_cue": "resource",
            "action_taken": "withdraw",
            "revealed_outcome": -1.0,
        },
        {
            "unrelated_query_noise": {"ignored": True},
            "layout_id": "p2_offset_v1",
            "event": "resource_appears",
            "cue": "resource",
            "next_cue": "quiet",
            "action_taken": "forage",
            "revealed_outcome": 1.0,
        }
    ]
    access = _baseline_access([])
    access.update(
        {
            "query_history_prefix": query,
            "reference_episodes": [reference],
        }
    )
    matched = verifier.baseline_exact_public_history_lookup_with_provenance(access)
    assert matched["action"] == "rest"
    assert matched["match_status"] == "exact_public_prefix_match"
    assert matched["reference_episode_index"] == 0
    assert matched["matched_prefix_length"] == 1
    assert matched["query_suffix_start_index"] == 1
    assert matched["reference_action_index"] == 1
    assert matched["layout_invariant"] is True
    assert matched["projection_schema_fields"] == [
        "event",
        "cue",
        "action_taken",
        "revealed_outcome",
    ]
    assert matched["reference_prefix_projection_hash"] == matched["query_projection_hash"]

    noisy = deepcopy(access)
    noisy["query_history_prefix"][0]["second_ignored_field"] = [1, 2, 3]
    noisy["reference_episodes"][0][0]["third_ignored_field"] = "noise"
    assert verifier.baseline_exact_public_history_lookup_with_provenance(noisy) == matched

    mismatched = deepcopy(access)
    mismatched["query_history_prefix"][1]["event"] = "threat_nearby"
    fallback = verifier.baseline_exact_public_history_lookup_with_provenance(mismatched)
    assert fallback["action"] == "approach"
    assert fallback["match_status"] == "no_exact_public_prefix_match"
    assert fallback["fallback_reason"] == "no_projected_reference_prefix_match"


def test_p2_product_trigger_seed_provenance_binds_recovered_state_and_rejects_mismatch():
    verifier = _verifier()
    config = verifier._load_frozen_p2_config()
    controller_inputs = {
        "run_id": "p2-product-trigger-hostile-control",
        "policy_seed": config["policy_tie_seed"],
        "world_seed": config["train_world_seeds"][0],
        "layout_id": config["heldout_layout_ids"][0],
    }
    initial = engine.initial_state(
        run_id=controller_inputs["run_id"],
        seed=controller_inputs["world_seed"],
        layout_id=controller_inputs["layout_id"],
    )
    recovery = RecoveryResult(
        run_id=controller_inputs["run_id"],
        run_meta=engine.make_run_metadata(
            controller_inputs["run_id"], controller_inputs["policy_seed"]
        ),
        frames=(RecoveryFrame(sequence=0, state=initial, trace=None),),
        recovered=True,
    )

    provenance = verifier._p2_product_trigger_seed_provenance(
        recovery=recovery,
        controller_inputs=controller_inputs,
        config=config,
    )
    assert provenance["valid"] is True
    assert provenance["recovered_policy_seed"] == config["policy_tie_seed"]
    assert provenance["recorded_world_seed"] == config["train_world_seeds"][0]
    assert provenance["world_seed_recomputed_initial_state_match"] is True

    hostile_inputs = deepcopy(controller_inputs)
    hostile_inputs["world_seed"] += 1
    mismatch = verifier._p2_product_trigger_seed_provenance(
        recovery=recovery,
        controller_inputs=hostile_inputs,
        config=config,
    )
    assert mismatch["valid"] is False
    assert mismatch["world_seed_recomputed_initial_state_match"] is False
    assert "recorded_world_seed_not_frozen_train_seed" in mismatch["failures"]
    assert "recorded_world_seed_does_not_recompute_recovered_initial_state" in mismatch[
        "failures"
    ]


@pytest.mark.parametrize(
    "encoded",
    (
        r"C:\t\p2-root-hostile\nested\file.json",
        "C:/t/p2-root-hostile/nested/file.json",
        r"C:\\t\\p2-root-hostile\\nested\\file.json",
    ),
)
def test_p2_physical_root_scan_recurses_over_native_slash_and_json_escaped_strings(encoded):
    verifier = _verifier()
    scan = verifier.scan_physical_output_root(
        {"outer": [{"inner": encoded}]}, Path(r"C:\t\p2-root-hostile")
    )
    assert scan["offender_count"] == 1
    assert scan["physical_output_root_absent"] is False
    assert scan["offenders"][0]["value_sha256"]
    assert "p2-root-hostile" not in json.dumps(scan)


def test_p2_frozen_config_and_actual_usage_ledger_bind_every_executed_input(
    _p2_actual_usage_fixture,
):
    verifier, config, ledger = _p2_actual_usage_fixture
    assert set(ledger["leaf_evidence"]) == set(config)
    assert all(item["evidence_count"] > 0 for item in ledger["leaf_evidence"].values())
    assert verifier.bind_p2_frozen_config(config, ledger)["all_frozen_inputs_used"] is True


def test_p2_binding_fails_closed_for_hostile_checkpoint_and_equivalence_mutations(
    _p2_actual_usage_fixture,
):
    verifier, config, ledger = _p2_actual_usage_fixture

    hostile_checkpoints = deepcopy(config)
    hostile_checkpoints["learning_checkpoints"] = [101, 102, 103, 104]
    checkpoint_bound = verifier.bind_p2_frozen_config(hostile_checkpoints, ledger)
    assert checkpoint_bound["all_frozen_inputs_used"] is False
    assert "unused_or_mismatched_frozen_leaf:learning_checkpoints" in checkpoint_bound["blocking_failures"]

    hostile_rule = deepcopy(config)
    hostile_rule["equivalence_rule"] = "fabricated_rule"
    rule_bound = verifier.bind_p2_frozen_config(hostile_rule, ledger)
    assert rule_bound["all_frozen_inputs_used"] is False
    assert "unused_or_mismatched_frozen_leaf:equivalence_rule" in rule_bound["blocking_failures"]


def test_p2_binding_fails_closed_for_every_hostile_frozen_top_level_leaf(
    _p2_actual_usage_fixture,
):
    verifier, config, ledger = _p2_actual_usage_fixture
    for key in config:
        hostile = deepcopy(config)
        hostile[key] = _hostile_leaf_value(hostile[key])
        bound = verifier.bind_p2_frozen_config(hostile, ledger)
        assert bound["all_frozen_inputs_used"] is False, key
        assert f"unused_or_mismatched_frozen_leaf:{key}" in bound["blocking_failures"], key


def test_p2_independent_controls_survive_candidate_reducer_and_scorer_failure(monkeypatch):
    verifier = _verifier()
    monkeypatch.setattr(
        engine,
        "compute_step",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("candidate reducer called")),
    )
    monkeypatch.setattr(
        engine,
        "_score_candidate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("candidate scorer called")),
    )
    config = verifier._load_frozen_p2_config()
    context = config["heldout_contexts"][0]
    outputs = {
        control_id: verifier.run_p2_independent_control(
            control_id=control_id,
            world_seed=context["world_seed"],
            layout_id=context["layout_id"],
            schedule=config["heldout_event_schedules"][context["event_schedule_id"]],
            train_public_history=[],
            reference_episodes=[],
        )
        for control_id in config["independent_controls"]
    }
    assert set(outputs) == set(config["independent_controls"])
    assert all("candidate_reducer_called" not in item for item in outputs.values())
    assert all("candidate_scorer_called" not in item for item in outputs.values())
    assert all(len(item["action_sequence"]) == 8 for item in outputs.values())


def test_p2_stored_action_input_claim_is_computed_from_persisted_commands_recovery_and_tamper(
    tmp_path,
):
    verifier = _verifier()
    db_path = tmp_path / "commands.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE commands (run_id TEXT NOT NULL, sequence INTEGER NOT NULL, command_json TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO commands(run_id, sequence, command_json) VALUES (?,?,?)",
            (
                "test-run",
                1,
                json.dumps({"sequence": 1, "cue": "quiet", "interventions": {}}),
            ),
        )
    passed = verifier._p2_stored_action_input_control(
        {
            "control_id": "stored_action_rehash",
            "control_available": True,
            "failed_closed": True,
        },
        db_path=db_path,
        recovery_recomputed=[True],
    )
    assert passed["computed"] is True
    assert passed["stored_action_used_as_input"] is False
    assert passed["persisted_command_count"] == 1
    assert passed["command_action_input_offender_count"] == 0
    assert passed["all_fresh_recoveries_recomputed"] is True

    unavailable = verifier._p2_stored_action_input_control(
        {
            "control_id": "stored_action_rehash",
            "control_available": False,
            "failed_closed": False,
        },
        db_path=db_path,
        recovery_recomputed=[True],
    )
    assert unavailable["computed"] is False
    assert unavailable["stored_action_used_as_input"] is None


def test_p2_baseline_independence_control_actually_disables_candidate_paths():
    verifier = _verifier()
    config = verifier._load_frozen_p2_config()
    context = config["heldout_contexts"][0]
    arms = [
        _p2_control_arm(
            verifier,
            arm_id=f"30:{context['context_id']}:{control_id}",
            control_id=control_id,
            layout_id=context["layout_id"],
            context_id=context["context_id"],
        )
        for control_id in config["independent_controls"]
    ]
    control = verifier._p2_baseline_independence_control(
        arms=arms,
    )
    assert control["computed"] is True
    assert control["candidate_reducer_disabled_compatible"] is True
    assert control["candidate_reducer_trap_calls"] == 0
    assert control["candidate_scorer_trap_calls"] == 0
    assert control["arm_count"] == len(config["independent_controls"])
    assert set(control["control_invocations"]) == {
        arm["arm_id"] for arm in arms
    }
    assert all(
        invocation["candidate_reducer_called"] is False
        and invocation["candidate_scorer_called"] is False
        for invocation in control["control_invocations"].values()
    )


def test_p2_baseline_independence_trap_detects_offset_layout_only_dependency(
    monkeypatch,
):
    verifier = _verifier()
    original = verifier._P2_CONTROL_PRODUCERS["graph_lookup"]

    def offset_only_candidate_dependency(access):
        if access["observation"]["layout_id"] == "p2_offset_v1":
            engine.compute_step(None, None, None)
        return original(access)

    monkeypatch.setitem(
        verifier._P2_CONTROL_PRODUCERS,
        "graph_lookup",
        offset_only_candidate_dependency,
    )
    arms = [
        _p2_control_arm(
            verifier,
            arm_id="30:heldout_42_vertical_alpha:graph_lookup",
            control_id="graph_lookup",
            layout_id="p2_vertical_v1",
            context_id="heldout_42_vertical_alpha",
        ),
        _p2_control_arm(
            verifier,
            arm_id="30:heldout_44_offset_beta:graph_lookup",
            control_id="graph_lookup",
            layout_id="p2_offset_v1",
            context_id="heldout_44_offset_beta",
        ),
    ]

    control = verifier._p2_baseline_independence_control(arms=arms)

    assert control["candidate_reducer_disabled_compatible"] is False
    vertical = control["control_invocations"][arms[0]["arm_id"]]
    offset = control["control_invocations"][arms[1]["arm_id"]]
    assert vertical["completed"] is True
    assert vertical["candidate_reducer_called"] is False
    assert offset["completed"] is False
    assert offset["candidate_reducer_called"] is True
    assert offset["candidate_reducer_trap_calls"] == 1


def test_p2_same_seed_schedule_topology_contrast_executes_three_layout_score_surfaces():
    verifier = _verifier()
    config = verifier._load_frozen_p2_config()
    contrast = verifier._p2_same_schedule_topology_contrast(config)
    assert contrast["layout_ids"] == [
        config["train_layout_id"],
        *config["heldout_layout_ids"],
    ]
    assert set(contrast["layout_runs"]) == set(contrast["layout_ids"])
    assert all(
        len(run["ticks"]) == len(config["heldout_event_schedules"]["alpha"])
        for run in contrast["layout_runs"].values()
    )
    assert contrast["score_surfaces_all_identical"] is False
    assert contrast["path_metric_surfaces_all_identical"] is False
    assert type(contrast["selected_action_sequences_all_equal"]) is bool
    assert type(contrast["outcome_sequences_all_equal"]) is bool
    assert all(
        tick["selected_action_path"]["producer_function"]
        == "ego_life_playground_v0.microworld.canonical_public_action_path"
        for run in contrast["layout_runs"].values()
        for tick in run["ticks"]
    )


def test_p2_root_leak_is_blocker_first_and_all_computed_failure_views_are_coherent(
    tmp_path, monkeypatch
):
    verifier = _verifier()
    output = tmp_path / "windows-root-leak"
    original = verifier._p2_input_artifacts

    def leaking_inputs(root):
        items = original(root)
        items[0]["hostile_native_root"] = str(Path(root).resolve())
        return items

    monkeypatch.setattr(verifier, "_p2_input_artifacts", leaking_inputs)
    result = verifier.run_p2_verification(output)
    stored_result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    learning = json.loads((output / "learning_report.json").read_text(encoding="utf-8"))
    failure = json.loads((output / "failure_manifest.json").read_text(encoding="utf-8"))

    assert result == stored_result
    assert result["verdict"] == "implementation_control_failure"
    assert result["implementation_controls_passed"] is False
    assert result["summary_metric"]["value"]["implementation_controls_passed"] is False
    assert "physical_output_root_leaked_into_artifact" in result["blocking_failures"]
    assert (
        "physical_output_root_leaked_into_artifact"
        in learning["metric"]["value"]["blocking_failures"]
    )
    assert (
        "physical_output_root_leaked_into_artifact"
        in failure["metric"]["value"]["implementation_failures"]
    )
    assert failure["implementation_failures"] == result["blocking_failures"]
    normalized_root = str(output.resolve()).replace("\\", "/").casefold()
    for path in output.glob("*.json"):
        normalized_text = path.read_text(encoding="utf-8").replace("\\\\", "/").replace(
            "\\", "/"
        ).casefold()
        assert normalized_root not in normalized_text


def test_p2_callable_verifier_is_deterministic_and_preserves_negative_result(tmp_path):
    verifier = _verifier()
    first = tmp_path / "p2-a"
    second = tmp_path / "p2-b"
    result_a = verifier.run_p2_verification(first)
    result_b = verifier.run_p2_verification(second)
    assert result_a == result_b
    assert result_a["implementation_controls_passed"] is True
    assert result_a["blocking_failures"] == []
    assert "equal_access_control_equivalence" in result_a["claim_blockers"]
    expected = {
        "continuity.sqlite3", "trace.jsonl", "product_trigger_receipt.json",
        "headroom_report.json", "collision_record.json", "baseline_comparison.json",
        "ablation_report.json", "learning_report.json", "replay_report.json",
        "leakage_report.json", "failure_manifest.json", "claim_ceiling.txt", "result.json",
    }
    assert {path.name for path in first.iterdir()} == expected
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
    learning = json.loads((first / "learning_report.json").read_text(encoding="utf-8"))
    assert learning["frozen_config_binding"]["all_frozen_inputs_used"] is True
    assert len(learning["heldout_full_cross_product"]) == 8
    assert len(learning["counterfactuals"]) == 56
    assert learning["bounded_update_controls"] == {
        "update_equations_valid": True,
        "freeze_adaptive_bytes_preserved": True,
        "consolidation_rebuilt_from_lineage": True,
        "consolidation_idempotent": True,
    }
    replay = json.loads((first / "replay_report.json").read_text(encoding="utf-8"))
    assert replay["stored_action_used_as_input"] is False
    assert replay["stored_action_input_control"]["computed"] is True
    assert (
        replay["stored_action_used_as_input"]
        is replay["stored_action_input_control"]["stored_action_used_as_input"]
    )
    assert replay["all_terminal_states_match"] is True
    assert replay["tamper_controls_passed"] is True
    leakage = json.loads((first / "leakage_report.json").read_text(encoding="utf-8"))
    assert leakage["live_offender_count"] == 0
    assert leakage["positive_controls_fired"] is True
    assert leakage["direct_forbidden_key_or_alias_scan_clean"] is True
    assert leakage["scan_scope"] == (
        "direct_forbidden_key_or_alias_scan_only__not_distributional_leakage_resistance"
    )
    assert set(leakage["live_scan_count_by_family"]) == {
        "train",
        "candidate",
        "from_scratch",
        "counterfactual",
    }
    assert all(leakage["live_scan_count_by_family"].values())
    assert "policy_excludes_private_oracle_future_reward_and_world_seed" not in leakage
    baseline = json.loads((first / "baseline_comparison.json").read_text(encoding="utf-8"))
    assert baseline["candidate_reducer_disabled_compatible"] is True
    assert baseline["independence_control"]["computed"] is True
    assert baseline["independence_control"]["candidate_reducer_disabled_compatible"] is True
    assert baseline["independence_control"]["arm_count"] == 48
    assert baseline["independence_control"]["expected_arm_count"] == 48
    assert len(baseline["independence_control"]["control_invocations"]) == 48
    assert all(
        invocation["candidate_reducer_called"] is False
        and invocation["candidate_scorer_called"] is False
        for invocation in baseline["independence_control"]["control_invocations"].values()
    )
    assert all(
        row["candidate_reducer_called"] is False
        and row["candidate_scorer_called"] is False
        for row in baseline["rows"]
    )
    exact_rows = [
        row for row in baseline["rows"] if row["control_id"] == "exact_public_history_lookup"
    ]
    assert exact_rows
    assert all(len(row["lookup_provenance"]) == 8 for row in exact_rows)
    assert {
        item["match_status"]
        for row in exact_rows
        for item in row["lookup_provenance"]
    } <= {"exact_public_prefix_match", "no_exact_public_prefix_match"}
    assert baseline["exact_public_history_nonempty_match_count"] > 0
    assert any(
        item["matched_prefix_length"] > 0
        for row in exact_rows
        for item in row["lookup_provenance"]
    )
    receipt = json.loads(
        (first / "product_trigger_receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["seed_provenance"]["valid"] is True
    assert receipt["policy_seed"] == 701
    assert receipt["world_seed"] == 30
    assert receipt["metric"]["seed_context_episode_ids"] == {
        "layout_id": receipt["layout_id"],
        "policy_seed": receipt["policy_seed"],
        "run_id": receipt["run_id"],
        "world_seed": receipt["world_seed"],
    }
    evidence_records = []
    for path in first.glob("*.json"):
        evidence_records.extend(verifier.collect_evidence_records(json.loads(path.read_text(encoding="utf-8"))))
    assert len(evidence_records) >= 150
    assert all(
        verifier.REQUIRED_PROVENANCE_FIELDS <= set(record)
        and record["producer_function"]
        and record["input_artifacts"]
        and record["run_id"]
        and record["seed_context_episode_ids"]
        and record["aggregation_rule"]
        and record["code_path_hash"]
        for record in evidence_records
    )
    blob = b"\n".join(path.read_bytes() for path in first.iterdir() if path.suffix != ".sqlite3")
    assert str(first).encode() not in blob
    assert str(second).encode() not in blob


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
        "schema_version": "ego.life_playground.policy_projection.v2",
        "non_memory": {
            "schema_version": "ego.life_playground.policy_non_memory_projection.v2",
            "sequence": 1,
            "policy_tie_seed": 701,
            "context_key": "quiet|energy",
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
            "action_paths": {
                "forage": {"reachable": True},
                "approach": {"reachable": True},
            },
            "model": {},
        },
        "claim_retrieval": {"claims": [], "support_by_action": {}},
        "resolved_memory_view": {
            "episodic": [],
            "consolidated": [],
            "claim_events": [],
            "competing_claims": [],
        },
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
    assert stored_result["verdict"] == "memory_conditioned_effect_not_observed_in_frozen_pair"
    assert stored_result["claim_status"] == "bounded_negative_for_memory_conditioned_effect"
    assert stored_result["blocking_failures"] == []
    assert "control_baseline_equivalent" in stored_result["claim_blockers"]
    assert "freeze_downstream_contrast_inert_side_a" in stored_result["claim_blockers"]
    assert "freeze_downstream_contrast_inert_side_b" in stored_result["claim_blockers"]
    assert "memory_conditioned_effect_not_observed" in stored_result["claim_blockers"]
    assert "source_deletion_target_unavailable" in stored_result["claim_blockers"]
    assert "shuffle_provenance_effect_not_observed" in stored_result["claim_blockers"]
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
        "runtime_mainline_connected": False,
        "runtime_authority": "none",
        "science_weight": 0,
        "remote_anchor": False,
        "proactive_action_enabled": False,
        "initiative_executor_authorized": False,
        "background_dispatch": False,
        "external_side_effects": False,
        "llm": "forbidden",
        "network": "forbidden",
    }

    baseline = json.loads((output / "baseline_comparison.json").read_text(encoding="utf-8"))
    assert baseline["strongest_matching_control"] in {
        "last_success",
        "count_table",
        "transition_table",
        "exact_public_history_lookup",
        "from_scratch",
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
        "b": False,
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
        "b": False,
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
        assert downstream["total_score_contrast"] is False
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
    assert ablation["shuffle_provenance"]["support_effect_changed"] is False
    assert ablation["source_deletion"]["intervention_executed"] is True
    assert ablation["source_deletion"]["target_available"] is False
    assert ablation["source_deletion"]["target_selection"]["status"] == (
        "unavailable_no_supporting_event"
    )
    assert ablation["source_deletion"]["relevant_changed_action"] is False
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


def test_p1_missing_supporting_source_is_a_structured_negative_result(tmp_path):
    verifier = _verifier()
    output = tmp_path / "p1-no-supporting-source"

    result = verifier.run_p1_verification(output)
    ablation = json.loads(
        (output / "ablation_report.json").read_text(encoding="utf-8")
    )

    assert result["blocking_failures"] == []
    assert result["verdict"] == "memory_conditioned_effect_not_observed_in_frozen_pair"
    assert result["claim_status"] == "bounded_negative_for_memory_conditioned_effect"
    assert "memory_conditioned_effect_not_observed" in result["claim_blockers"]
    assert "source_deletion_target_unavailable" in result["claim_blockers"]
    assert "shuffle_provenance_effect_not_observed" in result["claim_blockers"]
    assert result["frozen_config_usage"]["source_deletion_target"]["used"] is True
    source = ablation["source_deletion"]
    assert source["intervention_executed"] is True
    assert source["target_available"] is False
    assert source["relevant_changed_action"] is False
    assert source["target_selection"]["status"] == "unavailable_no_supporting_event"
    assert source["deleted_event_ids"] == []


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
    assert first_files == second_files
    # The repository artifact root advances from P1 to P2. P1 compatibility is
    # therefore proved by two fresh roots, not by requiring the historical P1
    # bytes to remain the repository's current milestone artifact set.

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
            if root != canonical:
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
