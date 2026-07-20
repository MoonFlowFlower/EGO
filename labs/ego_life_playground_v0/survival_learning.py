"""Deterministic Expected SARSA(lambda) support for the V2 product reducer.

This module contains no world transition, metabolism, controller, persistence,
or rendering logic.  Its callable surface accepts only policy-visible state
commitments, candidate scores, and replay identifiers supplied by
``engine.compute_step``.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any, Mapping

from .microworld import ACTIONS


LEARNER_SCHEMA_VERSION = "ego.life_playground.survival_learner.v1"
SELECTION_RECEIPT_SCHEMA_VERSION = "ego.life_playground.survival_selection.v1"
UPDATE_RECEIPT_SCHEMA_VERSION = "ego.life_playground.survival_update.v1"
ALGORITHM = "expected_sarsa_lambda"
ALPHA = 0.20
GAMMA = 0.99
LAMBDA = 0.80
EPSILON_INITIAL = 0.30
EPSILON_DECAY = 0.85
EPSILON_MINIMUM = 0.05
SELECTION_PRODUCER_FUNCTION = (
    "ego_life_playground_v0.survival_learning.select_action"
)
UPDATE_PRODUCER_FUNCTION = (
    "ego_life_playground_v0.survival_learning.update_expected_sarsa_lambda"
)
STATE_KEY_PRODUCER_FUNCTION = (
    "ego_life_playground_v0.survival_learning.build_state_key"
)
STATE_KEY_AGGREGATION_RULE = (
    "sha256(policy_observation_hash,round(energy*1000))"
)
POLICY_MODES = (ALGORITHM, "off")


class SurvivalLearningInvariantError(ValueError):
    """Raised when learner input or serialized state violates its schema."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    if type(value) is not str or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _round(value: float) -> float:
    return round(float(value), 12)


def hyperparameters() -> dict[str, Any]:
    return {
        "algorithm": ALGORITHM,
        "alpha": ALPHA,
        "gamma": GAMMA,
        "lambda": LAMBDA,
        "q_initialization": 0.0,
        "reward_rule": "1.0_if_energy_after_gt_0_else_0.0",
        "epsilon_initial": EPSILON_INITIAL,
        "epsilon_decay": EPSILON_DECAY,
        "epsilon_minimum": EPSILON_MINIMUM,
        "state_key_producer_function": STATE_KEY_PRODUCER_FUNCTION,
        "state_key_aggregation_rule": STATE_KEY_AGGREGATION_RULE,
    }


def empty_survival_learner() -> dict[str, Any]:
    return {
        "schema_version": LEARNER_SCHEMA_VERSION,
        "algorithm": ALGORITHM,
        "q_values": {},
        "eligibility": {},
        "visit_counts": {},
        "update_count": 0,
    }


def validate_state_key_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the entire permitted learned-state input surface.

    The exact-key check is also the positive-control target used by the product
    leakage scanner.  No ignored extension fields are permitted.
    """

    required = {"policy_observation_hash", "energy_milli"}
    if not isinstance(payload, Mapping) or set(payload) != required:
        raise SurvivalLearningInvariantError("learner state-key input schema mismatch")
    observation_hash = payload["policy_observation_hash"]
    energy_milli = payload["energy_milli"]
    if not _is_sha256(observation_hash):
        raise SurvivalLearningInvariantError(
            "learner state-key policy_observation_hash must be lowercase sha256"
        )
    if type(energy_milli) is not int or not 0 <= energy_milli <= 1000:
        raise SurvivalLearningInvariantError(
            "learner state-key energy_milli must be an integer within 0..1000"
        )
    return {
        "policy_observation_hash": observation_hash,
        "energy_milli": energy_milli,
    }


def build_state_key(policy_observation_hash: str, energy: float) -> str:
    if isinstance(energy, bool) or not isinstance(energy, (int, float)):
        raise SurvivalLearningInvariantError("learner energy must be numeric")
    if not math.isfinite(float(energy)) or not 0.0 <= float(energy) <= 1.0:
        raise SurvivalLearningInvariantError("learner energy must be finite within 0..1")
    payload = validate_state_key_payload(
        {
            "policy_observation_hash": policy_observation_hash,
            "energy_milli": round(float(energy) * 1000),
        }
    )
    return _canonical_hash(payload)


def epsilon_for_life(life_index: int) -> float:
    if type(life_index) is not int or life_index < 1:
        raise SurvivalLearningInvariantError("life_index must be a positive integer")
    return _round(
        max(
            EPSILON_MINIMUM,
            EPSILON_INITIAL * (EPSILON_DECAY ** (life_index - 1)),
        )
    )


def learner_state_hash(learner: Mapping[str, Any]) -> str:
    validate_survival_learner(learner)
    return _canonical_hash(learner)


def eligibility_hash(learner: Mapping[str, Any]) -> str:
    validate_survival_learner(learner)
    return _canonical_hash(learner["eligibility"])


def q_table_hash(learner: Mapping[str, Any]) -> str:
    validate_survival_learner(learner)
    return _canonical_hash(learner["q_values"])


def q_table_size(learner: Mapping[str, Any]) -> int:
    validate_survival_learner(learner)
    return sum(len(row) for row in learner["q_values"].values())


def clear_eligibility_for_respawn(learner: Mapping[str, Any]) -> dict[str, Any]:
    """Reset life-local traces while preserving learned values and counters."""

    validate_survival_learner(learner)
    updated = deepcopy(dict(learner))
    updated["eligibility"] = {}
    validate_survival_learner(updated)
    return updated


def validate_survival_learner(learner: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "algorithm",
        "q_values",
        "eligibility",
        "visit_counts",
        "update_count",
    }
    if not isinstance(learner, Mapping) or set(learner) != required:
        raise SurvivalLearningInvariantError("survival learner state schema mismatch")
    if learner["schema_version"] != LEARNER_SCHEMA_VERSION:
        raise SurvivalLearningInvariantError("survival learner schema_version mismatch")
    if learner["algorithm"] != ALGORITHM:
        raise SurvivalLearningInvariantError("survival learner algorithm mismatch")
    if type(learner["update_count"]) is not int or learner["update_count"] < 0:
        raise SurvivalLearningInvariantError("survival learner update_count is invalid")
    _validate_numeric_table(learner["q_values"], "q_values", lower=None, upper=None)
    _validate_numeric_table(learner["eligibility"], "eligibility", lower=0.0, upper=1.0)
    _validate_count_table(learner["visit_counts"])


def _validate_numeric_table(
    table: Any, label: str, *, lower: float | None, upper: float | None
) -> None:
    if not isinstance(table, Mapping):
        raise SurvivalLearningInvariantError(f"survival learner {label} must be an object")
    for state_key, row in table.items():
        if not _is_sha256(state_key) or not isinstance(row, Mapping) or not row:
            raise SurvivalLearningInvariantError(f"survival learner {label} row is invalid")
        for action, value in row.items():
            if action not in ACTIONS or isinstance(value, bool) or not isinstance(value, (int, float)):
                raise SurvivalLearningInvariantError(f"survival learner {label} entry is invalid")
            number = float(value)
            if not math.isfinite(number):
                raise SurvivalLearningInvariantError(f"survival learner {label} must be finite")
            if lower is not None and number < lower:
                raise SurvivalLearningInvariantError(f"survival learner {label} is below range")
            if upper is not None and number > upper:
                raise SurvivalLearningInvariantError(f"survival learner {label} is above range")


def _validate_count_table(table: Any) -> None:
    if not isinstance(table, Mapping):
        raise SurvivalLearningInvariantError("survival learner visit_counts must be an object")
    for state_key, row in table.items():
        if not _is_sha256(state_key) or not isinstance(row, Mapping) or not row:
            raise SurvivalLearningInvariantError("survival learner visit_counts row is invalid")
        for action, value in row.items():
            if action not in ACTIONS or type(value) is not int or value < 1:
                raise SurvivalLearningInvariantError("survival learner visit_counts entry is invalid")


def _validate_candidate_scores(candidate_scores: Mapping[str, float]) -> dict[str, float]:
    if not isinstance(candidate_scores, Mapping) or set(candidate_scores) != set(ACTIONS):
        raise SurvivalLearningInvariantError("candidate score schema mismatch")
    normalized: dict[str, float] = {}
    for action in ACTIONS:
        value = candidate_scores[action]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SurvivalLearningInvariantError("candidate score must be numeric")
        if not math.isfinite(float(value)):
            raise SurvivalLearningInvariantError("candidate score must be finite")
        normalized[action] = float(value)
    return normalized


def q_values_for_state(learner: Mapping[str, Any], state_key: str) -> dict[str, float]:
    validate_survival_learner(learner)
    if not _is_sha256(state_key):
        raise SurvivalLearningInvariantError("learner state_key must be lowercase sha256")
    row = learner["q_values"].get(state_key, {})
    return {action: _round(float(row.get(action, 0.0))) for action in ACTIONS}


def _heuristic_choice(candidate_scores: Mapping[str, float], eligible: tuple[str, ...]) -> str:
    highest = max(candidate_scores[action] for action in eligible)
    # Candidate rows in the existing reducer are sorted by action before max;
    # preserve its first-on-equal behavior.
    return min(action for action in eligible if candidate_scores[action] == highest)


def _greedy_choice(q_by_action: Mapping[str, float], candidate_scores: Mapping[str, float]) -> str:
    maximum = max(q_by_action.values())
    eligible = tuple(action for action in ACTIONS if q_by_action[action] == maximum)
    return _heuristic_choice(candidate_scores, eligible)


def _exploration_draw(
    *, run_seed: int, episode_index: int, sequence: int, state_key: str
) -> tuple[float, int, str]:
    payload = {
        "producer": SELECTION_PRODUCER_FUNCTION,
        "run_seed": run_seed,
        "episode_index": episode_index,
        "sequence": sequence,
        "state_key": state_key,
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).digest()
    unit = int.from_bytes(digest[:8], "big") / float(2**64)
    action_index = int.from_bytes(digest[8:16], "big") % len(ACTIONS)
    return _round(unit), action_index, hashlib.sha256(digest).hexdigest()


def select_action(
    learner: Mapping[str, Any],
    *,
    state_key: str,
    candidate_scores: Mapping[str, float],
    run_seed: int,
    episode_index: int,
    sequence: int,
    life_index: int,
    mode: str,
) -> tuple[str, dict[str, Any]]:
    validate_survival_learner(learner)
    scores = _validate_candidate_scores(candidate_scores)
    if not _is_sha256(state_key):
        raise SurvivalLearningInvariantError("learner state_key must be lowercase sha256")
    if type(run_seed) is not int:
        raise SurvivalLearningInvariantError("run_seed must be an integer")
    if type(episode_index) is not int or episode_index < 0:
        raise SurvivalLearningInvariantError("episode_index must be non-negative")
    if type(sequence) is not int or sequence < 1:
        raise SurvivalLearningInvariantError("sequence must be positive")
    if type(life_index) is not int or life_index < 1:
        raise SurvivalLearningInvariantError("life_index must be positive")
    if mode not in POLICY_MODES:
        raise SurvivalLearningInvariantError("survival learning mode is invalid")

    q_by_action = q_values_for_state(learner, state_key)
    draw, exploration_index, draw_hash = _exploration_draw(
        run_seed=run_seed,
        episode_index=episode_index,
        sequence=sequence,
        state_key=state_key,
    )
    greedy_action = _greedy_choice(q_by_action, scores)
    if mode == "off":
        epsilon = 0.0
        selected_action = _heuristic_choice(scores, tuple(ACTIONS))
        selection_mode = "off"
        exploration_applied = False
    else:
        epsilon = epsilon_for_life(life_index)
        exploration_applied = draw < epsilon
        if exploration_applied:
            selected_action = str(ACTIONS[exploration_index])
            selection_mode = "explore"
        else:
            selected_action = greedy_action
            selection_mode = "exploit"

    receipt = {
        "schema_version": SELECTION_RECEIPT_SCHEMA_VERSION,
        "producer_function": SELECTION_PRODUCER_FUNCTION,
        "algorithm": ALGORITHM,
        "requested_mode": mode,
        "selection_mode": selection_mode,
        "state_key": state_key,
        "epsilon": epsilon,
        "exploration_draw": draw,
        "exploration_draw_hash": draw_hash,
        "exploration_applied": exploration_applied,
        "greedy_action": greedy_action,
        "selected_action": selected_action,
        "q_by_action": q_by_action,
        "q_table_hash_before": q_table_hash(learner),
        "eligibility_hash_before": eligibility_hash(learner),
        "learner_hash_before": learner_state_hash(learner),
        "q_table_size_before": q_table_size(learner),
        "update_count_before": int(learner["update_count"]),
    }
    return selected_action, receipt


def expected_policy_value(
    learner: Mapping[str, Any],
    *,
    state_key: str,
    candidate_scores: Mapping[str, float],
    life_index: int,
) -> float:
    scores = _validate_candidate_scores(candidate_scores)
    q_by_action = q_values_for_state(learner, state_key)
    greedy_action = _greedy_choice(q_by_action, scores)
    epsilon = epsilon_for_life(life_index)
    uniform_mean = sum(q_by_action.values()) / len(ACTIONS)
    return _round((1.0 - epsilon) * q_by_action[greedy_action] + epsilon * uniform_mean)


def update_expected_sarsa_lambda(
    learner: Mapping[str, Any],
    *,
    state_key: str,
    action: str,
    reward: float,
    next_state_key: str,
    next_candidate_scores: Mapping[str, float],
    next_life_index: int,
    terminal: bool,
    updates_enabled: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_survival_learner(learner)
    _validate_candidate_scores(next_candidate_scores)
    if not _is_sha256(state_key) or not _is_sha256(next_state_key):
        raise SurvivalLearningInvariantError("learner update state_key must be lowercase sha256")
    if action not in ACTIONS:
        raise SurvivalLearningInvariantError("learner update action is invalid")
    if isinstance(reward, bool) or not isinstance(reward, (int, float)):
        raise SurvivalLearningInvariantError("learner reward must be numeric")
    if float(reward) not in {0.0, 1.0}:
        raise SurvivalLearningInvariantError("learner reward must follow the fixed binary rule")
    if type(terminal) is not bool or type(updates_enabled) is not bool:
        raise SurvivalLearningInvariantError("learner update flags must be boolean")

    before = deepcopy(dict(learner))
    q_before = q_values_for_state(before, state_key)[action]
    expected_next_q = 0.0 if terminal else expected_policy_value(
        before,
        state_key=next_state_key,
        candidate_scores=next_candidate_scores,
        life_index=next_life_index,
    )
    td_target = _round(float(reward) + (0.0 if terminal else GAMMA * expected_next_q))
    td_error = _round(td_target - q_before)

    updated = deepcopy(before)
    if updates_enabled:
        eligibility_row = updated["eligibility"].setdefault(state_key, {})
        eligibility_row[action] = 1.0
        for eligible_state, row in list(updated["eligibility"].items()):
            q_row = updated["q_values"].setdefault(eligible_state, {})
            for eligible_action, eligibility_value in list(row.items()):
                current_q = float(q_row.get(eligible_action, 0.0))
                q_row[eligible_action] = _round(
                    current_q + ALPHA * td_error * float(eligibility_value)
                )
        visit_row = updated["visit_counts"].setdefault(state_key, {})
        visit_row[action] = int(visit_row.get(action, 0)) + 1
        updated["update_count"] = int(updated["update_count"]) + 1
        if terminal:
            updated["eligibility"] = {}
        else:
            decay = GAMMA * LAMBDA
            for row in updated["eligibility"].values():
                for eligible_action, eligibility_value in list(row.items()):
                    row[eligible_action] = _round(float(eligibility_value) * decay)
        reason = "expected_sarsa_lambda_update"
    else:
        reason = "adaptive_updates_frozen"

    validate_survival_learner(updated)
    q_after = q_values_for_state(updated, state_key)[action]
    receipt = {
        "schema_version": UPDATE_RECEIPT_SCHEMA_VERSION,
        "producer_function": UPDATE_PRODUCER_FUNCTION,
        "algorithm": ALGORITHM,
        "applied": updates_enabled,
        "reason": reason,
        "state_key": state_key,
        "action": action,
        "reward": float(reward),
        "next_state_key": next_state_key,
        "bootstrap_applied": not terminal,
        "expected_next_q": expected_next_q,
        "td_target": td_target,
        "td_error": td_error,
        "q_selected_before": q_before,
        "q_selected_after": q_after,
        "q_table_hash_before": q_table_hash(before),
        "q_table_hash_after": q_table_hash(updated),
        "eligibility_hash_before": eligibility_hash(before),
        "eligibility_hash_after": eligibility_hash(updated),
        "learner_hash_before": learner_state_hash(before),
        "learner_hash_after": learner_state_hash(updated),
        "q_table_size_after": q_table_size(updated),
        "update_count_after": int(updated["update_count"]),
    }
    return updated, receipt
