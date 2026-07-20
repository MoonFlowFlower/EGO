from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.survival_learning import (
    ACTIONS,
    ALPHA,
    GAMMA,
    LAMBDA,
    SurvivalLearningInvariantError,
    build_state_key,
    empty_survival_learner,
    epsilon_for_life,
    select_action,
    update_expected_sarsa_lambda,
    validate_state_key_payload,
)


def _scores(**overrides: float) -> dict[str, float]:
    scores = {action: 0.0 for action in ACTIONS}
    scores.update(overrides)
    return scores


def test_expected_sarsa_lambda_numeric_update_and_eligibility_decay() -> None:
    learner = empty_survival_learner()
    state_a = build_state_key("a" * 64, 0.450)
    state_b = build_state_key("b" * 64, 0.438)
    state_c = build_state_key("c" * 64, 0.426)

    first, receipt_a = update_expected_sarsa_lambda(
        learner,
        state_key=state_a,
        action="move_forward",
        reward=1.0,
        next_state_key=state_b,
        next_candidate_scores=_scores(rest=1.0),
        next_life_index=1,
        terminal=False,
        updates_enabled=True,
    )

    assert receipt_a["td_target"] == pytest.approx(1.0)
    assert receipt_a["td_error"] == pytest.approx(1.0)
    assert first["q_values"][state_a]["move_forward"] == pytest.approx(ALPHA)
    assert first["eligibility"][state_a]["move_forward"] == pytest.approx(GAMMA * LAMBDA)

    second, receipt_b = update_expected_sarsa_lambda(
        first,
        state_key=state_b,
        action="rest",
        reward=0.0,
        next_state_key=state_c,
        next_candidate_scores=_scores(turn_left=1.0),
        next_life_index=1,
        terminal=False,
        updates_enabled=True,
    )

    assert receipt_b["td_error"] == pytest.approx(0.0)
    assert second["q_values"][state_a]["move_forward"] == pytest.approx(ALPHA)
    assert second["eligibility"][state_a]["move_forward"] == pytest.approx(
        (GAMMA * LAMBDA) ** 2
    )
    assert second["eligibility"][state_b]["rest"] == pytest.approx(GAMMA * LAMBDA)
    assert second["visit_counts"][state_a]["move_forward"] == 1
    assert second["visit_counts"][state_b]["rest"] == 1
    assert second["update_count"] == 2


def test_expected_target_uses_epsilon_policy_distribution() -> None:
    learner = empty_survival_learner()
    state_a = build_state_key("a" * 64, 0.450)
    state_b = build_state_key("b" * 64, 0.438)
    learner["q_values"][state_a] = {action: 0.0 for action in ACTIONS}
    learner["q_values"][state_b] = {action: 0.0 for action in ACTIONS}
    learner["q_values"][state_b]["rest"] = 2.0
    learner["q_values"][state_b]["interact"] = 1.0
    epsilon = epsilon_for_life(1)
    expected_q = (1.0 - epsilon) * 2.0 + epsilon * (3.0 / len(ACTIONS))

    updated, receipt = update_expected_sarsa_lambda(
        learner,
        state_key=state_a,
        action="turn_left",
        reward=1.0,
        next_state_key=state_b,
        next_candidate_scores=_scores(rest=2.0),
        next_life_index=1,
        terminal=False,
        updates_enabled=True,
    )

    assert receipt["expected_next_q"] == pytest.approx(expected_q)
    assert receipt["td_target"] == pytest.approx(1.0 + GAMMA * expected_q)
    assert updated["q_values"][state_a]["turn_left"] == pytest.approx(
        ALPHA * receipt["td_error"]
    )


def test_terminal_update_does_not_bootstrap_and_clears_eligibility() -> None:
    learner = empty_survival_learner()
    state_a = build_state_key("a" * 64, 0.010)
    state_b = build_state_key("b" * 64, 0.000)
    learner["q_values"][state_b] = {action: 9.0 for action in ACTIONS}
    learner["eligibility"][state_b] = {"rest": 0.5}

    updated, receipt = update_expected_sarsa_lambda(
        learner,
        state_key=state_a,
        action="move_forward",
        reward=0.0,
        next_state_key=state_b,
        next_candidate_scores=_scores(rest=1.0),
        next_life_index=1,
        terminal=True,
        updates_enabled=True,
    )

    assert receipt["bootstrap_applied"] is False
    assert receipt["td_target"] == 0.0
    assert updated["eligibility"] == {}


def test_selection_is_seed_command_replayable_and_q_precedes_heuristic() -> None:
    learner = empty_survival_learner()
    state_key = build_state_key("d" * 64, 0.450)
    learner["q_values"][state_key] = {action: 0.0 for action in ACTIONS}
    learner["q_values"][state_key]["turn_left"] = 0.8
    scores = _scores(rest=100.0, turn_left=-100.0)

    selected_a, receipt_a = select_action(
        learner,
        state_key=state_key,
        candidate_scores=scores,
        run_seed=701,
        episode_index=15,
        sequence=111,
        life_index=16,
        mode="expected_sarsa_lambda",
    )
    selected_b, receipt_b = select_action(
        deepcopy(learner),
        state_key=state_key,
        candidate_scores=deepcopy(scores),
        run_seed=701,
        episode_index=15,
        sequence=111,
        life_index=16,
        mode="expected_sarsa_lambda",
    )

    assert selected_a == selected_b == "turn_left"
    assert receipt_a == receipt_b
    assert receipt_a["selection_mode"] == "exploit"


def test_q_tie_uses_existing_heuristic_and_off_mode_preserves_it() -> None:
    learner = empty_survival_learner()
    state_key = build_state_key("e" * 64, 0.450)
    scores = _scores(interact=0.7, rest=0.3)

    selected, receipt = select_action(
        learner,
        state_key=state_key,
        candidate_scores=scores,
        run_seed=701,
        episode_index=0,
        sequence=1,
        life_index=1,
        mode="off",
    )

    assert selected == "interact"
    assert receipt["selection_mode"] == "off"
    assert receipt["epsilon"] == 0.0


def test_update_frozen_returns_byte_equivalent_learner() -> None:
    learner = empty_survival_learner()
    state_key = build_state_key("f" * 64, 0.450)
    before = deepcopy(learner)

    updated, receipt = update_expected_sarsa_lambda(
        learner,
        state_key=state_key,
        action="rest",
        reward=1.0,
        next_state_key=state_key,
        next_candidate_scores=_scores(rest=1.0),
        next_life_index=1,
        terminal=False,
        updates_enabled=False,
    )

    assert updated == before
    assert receipt["applied"] is False
    assert receipt["reason"] == "adaptive_updates_frozen"


def test_state_key_scanner_rejects_hidden_input_with_positive_control() -> None:
    valid = {"policy_observation_hash": "1" * 64, "energy_milli": 450}
    assert validate_state_key_payload(valid) == valid
    assert build_state_key("1" * 64, 0.450) == build_state_key("1" * 64, 0.450)

    for forbidden_key in (
        "position",
        "objects_by_cause",
        "cause",
        "token_mapping",
        "future_observation",
        "life_id",
        "seed_id",
    ):
        with pytest.raises(SurvivalLearningInvariantError, match="schema"):
            validate_state_key_payload({**valid, forbidden_key: "positive-control"})
