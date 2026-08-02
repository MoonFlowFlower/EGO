from __future__ import annotations

import math

import pytest

from labs.ego_life_playground_v0 import public_featured_transfer as subject


def _public_observation() -> dict[str, object]:
    return {
        "organism": {"energy": 0.5, "safety": 0.5, "target": 0.72},
        "slots": [
            {"features": [0, 0, 1, 1, 0]},
            {"features": [0, 1, 0, 1, 0]},
            {"features": [1, 0, 0, 1, 0]},
        ],
        "previous": None,
    }


def test_mechanism_family_is_finite_unique_and_compositional() -> None:
    family = subject.mechanism_family()
    assert len(family) == 40
    assert len({(item.energy_weights, item.safety_weights) for item in family}) == 40
    assert subject.combo_bits(29) == (1, 1, 1, 0, 1)

    mechanism = family[17]
    features = (1, 1, 1, 0, 0)
    energy, safety = subject.latent_effect(mechanism, features, "normal")
    reverse_energy, reverse_safety = subject.latent_effect(
        mechanism, features, "full_reverse"
    )
    assert energy == pytest.approx(-reverse_energy)
    assert safety == pytest.approx(-reverse_safety)
    assert energy != safety


def test_feature_splits_are_disjoint_and_training_covers_each_level() -> None:
    splits = subject.FEATURE_COMBO_SPLITS
    flattened = [value for values in splits.values() for value in values]
    assert len(flattened) == len(set(flattened))
    assert set(flattened) == set(range(32))
    training = [subject.combo_bits(value) for value in splits["training_dev"]]
    for feature_index in range(subject.FEATURE_COUNT):
        assert {row[feature_index] for row in training} == {0, 1}


def test_public_boundary_rejects_evaluator_private_fields_recursively() -> None:
    subject.validate_public_payload(_public_observation())
    for forbidden in subject.FORBIDDEN_CANDIDATE_FIELDS:
        payload = _public_observation()
        payload["nested"] = {forbidden: "secret"}
        with pytest.raises(ValueError, match="private candidate field"):
            subject.validate_public_payload(payload)


def test_exact_reference_state_is_json_safe_and_has_no_evaluator_identity() -> None:
    state = subject.new_reference_state()
    subject.validate_reference_state(state)
    receipt = subject.public_state_receipt(state)
    assert receipt["joint_hypotheses"] == 80
    assert receipt["update_count"] == 0
    encoded = subject.canonical_json(state)
    for forbidden in subject.FORBIDDEN_CANDIDATE_FIELDS:
        assert f'"{forbidden}"' not in encoded


def test_exact_update_uses_public_feedback_and_moves_probability_to_truth() -> None:
    state = subject.new_reference_state()
    observation = _public_observation()
    action = "interact_0"
    organism = observation["organism"]
    features = tuple(observation["slots"][0]["features"])
    true_mechanism = subject.mechanism_family()[17]
    delta_energy, delta_safety = subject.transition_delta(
        true_mechanism,
        features,
        "normal",
        energy_before=float(organism["energy"]),
        safety_before=float(organism["safety"]),
        noise_energy=0.0,
        noise_safety=0.0,
    )
    feedback = {
        "energy_before": organism["energy"],
        "safety_before": organism["safety"],
        "energy_after": organism["energy"] + delta_energy,
        "safety_after": organism["safety"] + delta_safety,
        "died": False,
    }
    before = subject.posterior_probability(state, 17, "normal")
    subject.update_after_transition(state, observation, action, feedback)
    after = subject.posterior_probability(state, 17, "normal")
    assert after > before
    assert state["update_count"] == 1
    assert math.isclose(sum(sum(row) for row in state["joint"]), 1.0)


def test_planner_reads_posterior_and_drive_intervention_changes_ranking() -> None:
    state = subject.private_aligned_reference_state(17, "normal")
    observation = _public_observation()
    energy_low = dict(observation)
    energy_low["organism"] = {"energy": 0.1, "safety": 0.8, "target": 0.72}
    safety_low = dict(observation)
    safety_low["organism"] = {"energy": 0.8, "safety": 0.1, "target": 0.72}
    energy_plan = subject.plan_action(state, energy_low)
    safety_plan = subject.plan_action(state, safety_low)
    assert energy_plan["ranking"] != safety_plan["ranking"]
    assert energy_plan["predictions"] == subject.plan_action(state, energy_low)["predictions"]
    assert energy_plan["reason"]["primary_deficit"] == "energy"
    assert safety_plan["reason"]["primary_deficit"] == "safety"


def test_current_world_feedback_is_needed_even_with_correct_shared_mechanism() -> None:
    normal = subject.private_global_reference_state(17)
    reverse = subject.private_global_reference_state(17)
    observation = _public_observation()
    before_normal = subject.local_mode_probability(normal, "full_reverse")
    before_reverse = subject.local_mode_probability(reverse, "full_reverse")
    assert before_normal == pytest.approx(before_reverse)

    features = tuple(observation["slots"][0]["features"])
    mechanism = subject.mechanism_family()[17]
    for state, mode in ((normal, "normal"), (reverse, "full_reverse")):
        de, ds = subject.transition_delta(
            mechanism, features, mode, 0.5, 0.5, 0.0, 0.0
        )
        subject.update_after_transition(
            state,
            observation,
            "interact_0",
            {
                "energy_before": 0.5,
                "safety_before": 0.5,
                "energy_after": 0.5 + de,
                "safety_after": 0.5 + ds,
                "died": False,
            },
        )
    assert subject.local_mode_probability(normal, "full_reverse") < 0.1
    assert subject.local_mode_probability(reverse, "full_reverse") > 0.9


def test_symbolic_information_is_partial_not_answer_leakage() -> None:
    audit = subject.symbolic_capacity_audit()
    assert 0.0 < audit["public_cue_effect_mutual_information_bits"]
    assert (
        audit["public_cue_effect_mutual_information_bits"]
        < audit["shared_mechanism_entropy_bits"]
    )
    assert audit["current_world_interaction_required"] is True

