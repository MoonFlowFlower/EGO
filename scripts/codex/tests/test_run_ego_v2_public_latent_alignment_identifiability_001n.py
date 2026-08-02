from __future__ import annotations

import math

import pytest

from labs.ego_life_playground_v0 import engine, microworld
from scripts.codex import (
    run_ego_v2_public_latent_alignment_identifiability_001n as campaign,
)


def public_payload(front: str = "v0") -> dict:
    visual = [["empty"] * 5 for _ in range(5)]
    visual[2][2] = "self"
    visual[1][2] = front
    return {
        "observation": {
            "schema_version": microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION,
            "visual": visual,
        },
        "organism": {"energy": 0.45, "safety": 0.62},
        "last_action": None,
        "last_delta": {"energy": 0.0, "safety": 0.0},
    }


def test_exact_mapping_space_and_distinct_public_effects() -> None:
    mappings = campaign.all_legal_mappings()
    assert len(mappings) == math.factorial(5)
    assert len({campaign.canonical_hash(row) for row in mappings}) == 120
    assert all(set(row) == set(microworld.TOKENS) for row in mappings)
    assert all(set(row.values()) == set(microworld.CAUSES) for row in mappings)
    deltas = {cause: campaign.expected_interaction_delta(cause) for cause in microworld.CAUSES}
    assert len({tuple(row.values()) for row in deltas.values()}) == 5
    assert deltas["resource"]["energy"] == pytest.approx(
        engine.CAUSE_DELTAS["resource"]["energy"]
        - engine.PASSIVE_ENERGY_DECAY_PER_TICK
        - engine.ACTION_COSTS["interact"]
    )


def test_exact_posterior_filters_and_marginalizes_all_consistent_mappings() -> None:
    state = campaign.empty_exact_state()
    initial = campaign.posterior_metrics(state)
    assert initial["equivalent_mapping_count"] == 120
    assert initial["posterior_entropy_bits"] == pytest.approx(math.log2(120))
    assert initial["exact_alignment_bayes_error"] == pytest.approx(119 / 120)
    assert initial["behavioral_alignment_bayes_error"] == pytest.approx(0.8)

    state, receipt = campaign.update_exact_posterior(
        state,
        public_input=public_payload("v0"),
        selected_action="interact",
        outcome_type="interacted",
        actual_delta=campaign.expected_interaction_delta("resource"),
        terminal=False,
        updates_enabled=True,
        feedback_mode="canonical",
    )
    assert receipt["applied"] is True
    assert campaign.posterior_metrics(state)["equivalent_mapping_count"] == 24
    assert all(row["v0"] == "resource" for row in state["mapping_hypotheses"])

    for token, cause in zip(("v1", "v2", "v3"), ("social", "novelty", "threat")):
        state, _ = campaign.update_exact_posterior(
            state,
            public_input=public_payload(token),
            selected_action="interact",
            outcome_type="interacted",
            actual_delta=campaign.expected_interaction_delta(cause),
            terminal=False,
            updates_enabled=True,
            feedback_mode="canonical",
        )
    metrics = campaign.posterior_metrics(state)
    assert metrics["equivalent_mapping_count"] == 1
    assert metrics["posterior_entropy_bits"] == 0.0
    assert metrics["exact_alignment_bayes_error"] == 0.0
    assert metrics["behavioral_alignment_bayes_error"] == 0.0


def test_passive_history_has_zero_mapping_information_and_intervention_is_required() -> None:
    audit = campaign.run_symbolic_identifiability_audit()
    assert audit["legal_mapping_count"] == 120
    assert audit["passive_observation_information_gain_bits"] == 0.0
    assert audit["minimum_distinct_direct_interactions"] == 4
    assert audit["worst_case_distinct_direct_interactions"] == 4
    assert audit["classification"] == "DIRECT_INTERVENTION_IDENTIFIABLE"
    assert audit["permanent_public_equivalence_classes"] == []
    assert audit["max_passive_equivalence_class_size"] == 120


def test_plan_uses_only_public_state_and_reports_all_action_diagnostics() -> None:
    state = campaign.empty_exact_state()
    payload = public_payload("v0")
    plan = campaign.plan_exact_action(
        state,
        public_input=payload,
        sequence=1,
        information_gain_enabled=True,
    )
    assert plan["public_input_clean"] is True
    assert plan["state_hash_before"] == campaign.exact_state_hash(state)
    assert set(plan["action_diagnostics"]) == set(microworld.ACTIONS)
    assert plan["action_diagnostics"]["interact"]["information_gain_bits"] > 0
    assert all(
        plan["action_diagnostics"][action]["information_gain_bits"] == 0.0
        for action in microworld.ACTIONS
        if action != "interact"
    )
    assert plan["selected_action"] in microworld.ACTIONS
    assert "mapping" not in campaign.canonical_json(plan).lower()


def test_private_input_is_rejected_fail_closed() -> None:
    state = campaign.empty_exact_state()
    leaked = public_payload()
    leaked["seed"] = 470003
    with pytest.raises(ValueError, match="public input rejected"):
        campaign.plan_exact_action(
            state,
            public_input=leaked,
            sequence=1,
            information_gain_enabled=True,
        )


def test_feedback_shuffle_changes_pairing_without_private_truth() -> None:
    state = campaign.empty_exact_state()
    state, receipt = campaign.update_exact_posterior(
        state,
        public_input=public_payload("v0"),
        selected_action="interact",
        outcome_type="interacted",
        actual_delta=campaign.expected_interaction_delta("resource"),
        terminal=False,
        updates_enabled=True,
        feedback_mode="shuffle",
    )
    assert receipt["observed_token"] == "v0"
    assert receipt["updated_token"] == "v1"
    assert all(row["v1"] == "resource" for row in state["mapping_hypotheses"])


def test_candidate_state_cannot_contain_evaluator_identifiers() -> None:
    state = campaign.empty_exact_state()
    serialized = campaign.canonical_json(state).lower()
    for forbidden in ("world_seed", "layout_id", "opaque_context", "oracle_action", "true_mapping"):
        assert forbidden not in serialized


def test_real_trajectory_preserves_public_call_chain_and_candidate_boundary() -> None:
    world = microworld.initial_world_state(seed=470003, layout_id="p0_cross_v1")
    spec = {
        "opaque_context_id": "test-001n-public",
        "world_seed": 470003,
        "layout_id": "p0_cross_v1",
        "mapping_commitment": dict(world["trial"]["token_mapping"]),
        "dev_only": True,
    }
    trajectory = campaign.run_trajectory(spec, arm="EXACT_BAYES_ADAPTIVE", budget=12)
    assert len(trajectory["rows"]) == 12
    assert all(row["candidate_wrapper_called"] is True for row in trajectory["rows"])
    assert all(row["public_input_clean"] is True for row in trajectory["rows"])
    assert all(row["call_chain"][2:6] == [
        "microworld.transition_world",
        "engine.compute_actual_delta",
        "engine.compute_metabolism_ledger",
        "terminal_energy_check",
    ] for row in trajectory["rows"])
    assert all("world_seed" not in campaign.canonical_json(row["public_input_receipt"]) for row in trajectory["rows"])


def test_equal_access_existing_public_bayes_repeats_scratch() -> None:
    world = microworld.initial_world_state(seed=470176, layout_id="p2_vertical_v1")
    spec = {
        "opaque_context_id": "test-001n-repeat",
        "world_seed": 470176,
        "layout_id": "p2_vertical_v1",
        "mapping_commitment": dict(world["trial"]["token_mapping"]),
        "dev_only": True,
    }
    scratch = campaign.run_trajectory(spec, arm="SCRATCH", budget=12)
    repeated = campaign.run_trajectory(spec, arm="EXISTING_PUBLIC_BAYES", budget=12)
    assert [row["selected_action"] for row in scratch["rows"]] == [
        row["selected_action"] for row in repeated["rows"]
    ]
    assert scratch["total_deficit_auc"] == repeated["total_deficit_auc"]


def test_private_aligned_reference_never_calls_candidate_wrapper() -> None:
    world = microworld.initial_world_state(seed=470349, layout_id="p2_offset_v1")
    spec = {
        "opaque_context_id": "test-001n-private-upper",
        "world_seed": 470349,
        "layout_id": "p2_offset_v1",
        "mapping_commitment": dict(world["trial"]["token_mapping"]),
        "dev_only": True,
    }
    trajectory = campaign.run_trajectory(spec, arm="PRIVATE_ALIGNED_REFERENCE", budget=8)
    assert all(row["evaluator_private"] is True for row in trajectory["rows"])
    assert all(row["candidate_wrapper_called"] is False for row in trajectory["rows"])
