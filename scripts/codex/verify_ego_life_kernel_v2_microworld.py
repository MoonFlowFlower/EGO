"""Callable P1 evidence producer for the default-off V2 microworld.

The candidate path is used only to build real serialized histories and rerun
named interventions.  Baselines below are independent functions over an
immutable public-access object; they do not import or call the reducer.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from typing import Any, Callable, Iterable, Mapping

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import claims, engine, microworld
from labs.ego_life_playground_v0.app import PlaygroundController, TerminalPlayground
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore


TASK_ID = "EGO-LIFE-KERNEL-V2-MICROWORLD-MEMORY-CAUSALITY-001A"
P1_RUN_ID = "ego-v2-p1-verification-001"
P2_RUN_ID = "ego-v2-p2-verification-001"
HISTORY_SEEDS = (18, 19)
HISTORY_EVENTS = ("resource_appears", "social_signal")
PAIR_ID = "p1_memory_lineage_pair_001"
PAIR_EVENT = "quiet_interval"
PAIR_POLICY_SEED = 101
PROVENANCE_SHUFFLE_SEED = 17
RECENCY_WINDOWS = (1, 2, 4)
MATCHED_UPDATE_STREAM_EVENTS = (PAIR_EVENT, *HISTORY_EVENTS)
TASK_SCOPE_PATH = REPO_ROOT / "docs" / "codex" / "tasks" / (
    "EGO-LIFE-KERNEL-V2-MICROWORLD-MEMORY-CAUSALITY-001A-MUTATION_SCOPE.yaml"
)
FROZEN_CONFIG_KEYS = {
    "config_id",
    "history_seeds",
    "history_event_schedule",
    "paired_checkpoint_event",
    "paired_checkpoint_id",
    "source_deletion_target",
    "irrelevant_deletion_target",
    "provenance_shuffle_seed",
    "pair_policy_seed",
    "ema_alpha",
    "claim_bias_coefficient",
    "claim_bias_clip",
    "recency_windows",
    "equivalence_rule",
    "post_result_retuning",
}
CLAIM_CEILING = (
    "Default-off local microworld product implementation with persistent canonical "
    "state, atomic recomputing trace/replay, and a bounded typed counterfactual "
    "memory-lineage transplant action-score contrast whose actual source histories are "
    "persisted and replayable. Equal-access history controls match; "
    "no general memory-causality, learning, mechanism-non-equivalence, agency, emotion, "
    "subjectivity, consciousness, or electronic-life claim is supported."
)
SWITCHES = {
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
REQUIRED_PROVENANCE_FIELDS = {
    "producer_function",
    "input_artifacts",
    "run_id",
    "seed_context_episode_ids",
    "aggregation_rule",
    "code_path_hash",
}
GENERATED_DB_LOGICAL_ID = "generated://p1/continuity.sqlite3"
GENERATED_TRACE_LOGICAL_ID = "generated://p1/trace.jsonl"
TASK_SCOPE_LOGICAL_ID = "authority://p1/mutation-scope"
P2_GENERATED_DB_LOGICAL_ID = "generated://p2/continuity.sqlite3"
P2_GENERATED_TRACE_LOGICAL_ID = "generated://p2/trace.jsonl"
P2_TASK_SCOPE_LOGICAL_ID = "authority://p2/mutation-scope"
_INPUT_ARTIFACT_LOGICAL_IDS = {
    GENERATED_DB_LOGICAL_ID,
    GENERATED_TRACE_LOGICAL_ID,
    TASK_SCOPE_LOGICAL_ID,
    P2_GENERATED_DB_LOGICAL_ID,
    P2_GENERATED_TRACE_LOGICAL_ID,
    P2_TASK_SCOPE_LOGICAL_ID,
}

P2_CLAIM_CEILING = (
    "Default-off local microworld product implementation with persistent canonical "
    "state, visible bounded prediction-error update and consolidation lineage, and "
    "recomputing trace/replay. Reports contain exact bounded update-response and "
    "held-out comparison metrics only inside the frozen contexts, including negative "
    "or equal-access-control-equivalent results. No general learning, transfer, "
    "memory-causality, mechanism non-equivalence, planning, agency, emotion, "
    "subjectivity, consciousness, runtime/mainline effect, or electronic-life claim."
)
P2_FROZEN_CONFIG_KEYS = {
    "config_id", "policy_tie_seed", "update_alpha", "episode_span_ticks",
    "consolidation_threshold", "train_world_seeds", "train_layout_id",
    "train_episode_schedules", "learning_checkpoints", "heldout_layout_ids",
    "heldout_event_schedules", "heldout_contexts", "transfer_matrix",
    "heldout_update_mode", "minimum_matched_context_action_slots",
    "minimum_site_visits_per_context_for_directional_claim",
    "source_deletion_episode_index", "irrelevant_source_episode_id",
    "counterfactuals", "independent_controls", "candidate_ablation",
    "learning_curve_metric", "task_outcome_metric", "site_outcome_metric",
    "equivalence_rule", "post_result_retuning",
}
P2_FROZEN_CONFIG_ID = "ego_v2_p2_bounded_adaptation_v1"
P2_FROZEN_CONFIG_CANONICAL_SHA256 = (
    "6c0272f2745a8f4f010240452ce69c54a697fc1ddc9ca0100adcab3dc9c753ba"
)
P2_LEARNING_CURVE_METRIC_ID = (
    "matched_slot_macro_mean_absolute_prediction_error_over_four_state_coordinates"
)
P2_TASK_OUTCOME_METRIC_ID = "sum_revealed_site_outcome_with_non_site_zero"
P2_SITE_OUTCOME_METRIC_ID = "mean_revealed_outcome_conditioned_on_site_visit"
P2_EQUIVALENCE_RULE_ID = (
    "exact_action_sequence_match_or_exact_aggregate_task_outcome_match_blocks_non_equivalence"
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verifier_code_hash() -> str:
    return _canonical_hash(
        {
            "candidate_code_path_hash": engine.compute_code_path_hash(),
            "verifier_sha256": _file_hash(Path(__file__)),
        }
    )


def _input_artifact(path: Path, *, logical_id: str) -> dict[str, Any]:
    resolved = path.resolve()
    if logical_id not in _INPUT_ARTIFACT_LOGICAL_IDS:
        raise ValueError("input artifact logical ID is not canonical")
    return {
        "path": logical_id,
        "sha256": _file_hash(resolved),
        "bytes": resolved.stat().st_size,
    }


def _load_frozen_config() -> dict[str, Any]:
    payload = yaml.safe_load(TASK_SCOPE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("mutation scope must be a mapping")
    config = payload.get("frozen_p1_evaluation_config")
    if not isinstance(config, Mapping) or set(config) != FROZEN_CONFIG_KEYS:
        raise ValueError("frozen P1 config schema mismatch")
    return deepcopy(dict(config))


def _evidence(
    *,
    producer_function: str,
    input_artifacts: Iterable[Mapping[str, Any] | str],
    run_id: str,
    seed_context_episode_ids: Mapping[str, Any],
    aggregation_rule: str,
    value: Any,
) -> dict[str, Any]:
    return {
        "evidence_record_type": "computed_evidence",
        "producer_function": producer_function,
        "input_artifacts": [deepcopy(dict(item)) if isinstance(item, Mapping) else str(item) for item in input_artifacts],
        "run_id": run_id,
        "seed_context_episode_ids": deepcopy(dict(seed_context_episode_ids)),
        "aggregation_rule": aggregation_rule,
        "code_path_hash": _verifier_code_hash(),
        "value": deepcopy(value),
    }


def collect_evidence_records(value: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if isinstance(value, Mapping):
        if value.get("evidence_record_type") == "computed_evidence":
            records.append(dict(value))
        for item in value.values():
            records.extend(collect_evidence_records(item))
    elif isinstance(value, list):
        for item in value:
            records.extend(collect_evidence_records(item))
    return records


# ---------------------------------------------------------------------------
# Independent public-access baselines. Keep these functions reducer-free.

_NO_UPDATE_STATE_KEYS = ("energy", "safety", "connection", "stimulation")
_NO_UPDATE_TARGET = 0.72
_NO_UPDATE_PRIORS = {
    "approach": {"energy": -0.02, "safety": -0.02, "connection": 0.11, "stimulation": 0.03},
    "explore": {"energy": -0.05, "safety": -0.03, "connection": 0.00, "stimulation": 0.10},
    "forage": {"energy": 0.12, "safety": -0.03, "connection": 0.00, "stimulation": 0.02},
    "rest": {"energy": 0.09, "safety": 0.04, "connection": 0.00, "stimulation": -0.04},
    "withdraw": {"energy": -0.01, "safety": 0.10, "connection": -0.04, "stimulation": -0.03},
}
_NO_UPDATE_COSTS = {
    "approach": 0.018,
    "explore": 0.025,
    "forage": 0.020,
    "rest": 0.010,
    "withdraw": 0.015,
}
NO_UPDATE_ACCESS_CONTRACT = {
    "algorithm": "fixed_untrained_prior_total_deficit_reduction_minus_cost",
    "public_inputs": ["organism", "legal_actions"],
    "updates": "none",
}


def _legal(access: Mapping[str, Any]) -> list[str]:
    actions = list(access["legal_actions"])
    if not actions:
        raise ValueError("baseline legal action set is empty")
    return actions


def _fallback(access: Mapping[str, Any], preferred: str) -> str:
    legal = _legal(access)
    return preferred if preferred in legal else sorted(legal)[0]


def _empirical_action(access: Mapping[str, Any], records: Iterable[Mapping[str, Any]]) -> str:
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for record in records:
        action = str(record.get("action_taken", ""))
        if action not in _legal(access):
            continue
        outcome = record.get("revealed_outcome")
        if type(outcome) not in {int, float}:
            continue
        totals[action] = totals.get(action, 0.0) + float(outcome)
        counts[action] = counts.get(action, 0) + 1
    if not counts:
        return _fallback(access, "approach")
    means = {action: totals[action] / counts[action] for action in counts}
    return max(sorted(means), key=lambda action: means[action])


def baseline_observation_only(access: Mapping[str, Any]) -> str:
    cue = str(access["observation"].get("cue", "quiet"))
    preferred = {
        "resource": "forage",
        "contact": "approach",
        "novelty": "explore",
        "threat": "withdraw",
        "quiet": "approach",
    }.get(cue, "approach")
    return _fallback(access, preferred)


def baseline_q_only(access: Mapping[str, Any]) -> str:
    goal = str(access.get("current_goal", "homeostasis"))
    preferred = {
        "energy": "forage",
        "connection": "approach",
        "stimulation": "explore",
        "safety": "withdraw",
    }.get(goal, "rest")
    return _fallback(access, preferred)


def baseline_cue_clock_fsm(access: Mapping[str, Any]) -> str:
    cue = str(access["observation"].get("cue", "quiet"))
    phase = len(access.get("public_history", [])) % 2
    preferred = "forage" if cue == "resource" or (cue == "quiet" and phase == 1) else "approach"
    return _fallback(access, preferred)


def baseline_last_success(access: Mapping[str, Any]) -> str:
    for record in reversed(list(access.get("public_history", []))):
        if float(record.get("revealed_outcome") or 0.0) > 0.0:
            return _fallback(access, str(record.get("action_taken", "approach")))
    return _fallback(access, "approach")


def _recency_action(access: Mapping[str, Any], window: int) -> str:
    records = list(access.get("public_history", []))[-window:]
    return _empirical_action(access, records)


def baseline_recency_window_1(access: Mapping[str, Any]) -> str:
    return _recency_action(access, 1)


def baseline_recency_window_2(access: Mapping[str, Any]) -> str:
    return _recency_action(access, 2)


def baseline_recency_window_4(access: Mapping[str, Any]) -> str:
    return _recency_action(access, 4)


_P2_EXACT_LOOKUP_HISTORY_FIELDS = (
    "event",
    "cue",
    "action_taken",
    "revealed_outcome",
)


def project_p2_public_history(
    records: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Project train and query history through one equal-access public schema."""

    projected: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise ValueError("P2 public history record must be a mapping")
        projected.append(
            {
                field: deepcopy(record.get(field))
                for field in _P2_EXACT_LOOKUP_HISTORY_FIELDS
            }
        )
    return projected


def baseline_exact_public_history_lookup_with_provenance(
    access: Mapping[str, Any],
) -> dict[str, Any]:
    query = project_p2_public_history(access.get("query_history_prefix", []))
    full_query_hash = _canonical_hash(query)
    episodes = [
        project_p2_public_history(episode)
        for episode in access.get("reference_episodes", [])
    ]
    # The control is intentionally invariant to layout/topology identifiers. It
    # searches the longest suffix of the actually observed heldout prefix
    # against a recorded training-episode prefix, then returns that prefix's
    # next recorded action. This keeps the comparator on equal-access public
    # event/cue/action/outcome history without granting candidate-only topology.
    match_lengths = [0] if not query else range(len(query), 0, -1)
    for match_length in match_lengths:
        query_suffix = query[-match_length:] if match_length else []
        for episode_index, projected_records in enumerate(episodes):
            projected_prefix = projected_records[:match_length]
            if len(projected_records) > match_length and projected_prefix == query_suffix:
                return {
                    "action": _fallback(
                        access,
                        str(
                            projected_records[match_length].get(
                                "action_taken", "approach"
                            )
                        ),
                    ),
                    "match_status": "exact_public_prefix_match",
                    "fallback_reason": None,
                    "reference_episode_index": episode_index,
                    "reference_action_index": match_length,
                    "matched_prefix_length": match_length,
                    "query_suffix_start_index": len(query) - match_length,
                    "query_projection_hash": _canonical_hash(query_suffix),
                    "full_query_projection_hash": full_query_hash,
                    "reference_prefix_projection_hash": _canonical_hash(
                        projected_prefix
                    ),
                    "projection_schema_fields": list(
                        _P2_EXACT_LOOKUP_HISTORY_FIELDS
                    ),
                    "projection_access_choice": (
                        "layout_invariant_equal_access_public_event_cue_action_outcome"
                    ),
                    "query_match_mode": (
                        "longest_observed_query_suffix_to_training_episode_prefix"
                    ),
                    "layout_invariant": True,
                }
    return {
        "action": _fallback(access, "approach"),
        "match_status": "no_exact_public_prefix_match",
        "fallback_reason": "no_projected_reference_prefix_match",
        "reference_episode_index": None,
        "reference_action_index": None,
        "matched_prefix_length": 0,
        "query_suffix_start_index": None,
        "query_projection_hash": full_query_hash,
        "full_query_projection_hash": full_query_hash,
        "reference_prefix_projection_hash": None,
        "projection_schema_fields": list(_P2_EXACT_LOOKUP_HISTORY_FIELDS),
        "projection_access_choice": (
            "layout_invariant_equal_access_public_event_cue_action_outcome"
        ),
        "query_match_mode": (
            "longest_observed_query_suffix_to_training_episode_prefix"
        ),
        "layout_invariant": True,
    }


def baseline_exact_public_history_lookup(access: Mapping[str, Any]) -> str:
    return str(baseline_exact_public_history_lookup_with_provenance(access)["action"])


def baseline_nearest_history(access: Mapping[str, Any]) -> str:
    cue = str(access["observation"].get("cue", "quiet"))
    records = list(access.get("public_history", []))
    if not records:
        return _fallback(access, "approach")
    ranked = sorted(
        enumerate(records),
        key=lambda item: (
            0 if str(item[1].get("cue", "")) == cue else 1,
            -float(item[1].get("revealed_outcome") or 0.0),
            -item[0],
        ),
    )
    return _fallback(access, str(ranked[0][1].get("action_taken", "approach")))


def baseline_graph_lookup(access: Mapping[str, Any]) -> str:
    records = list(access.get("public_history", []))
    current_cue = str(access["observation"].get("cue", "quiet"))
    incoming = [
        record
        for record in records
        if str(record.get("next_cue", "")) == current_cue
    ]
    if not incoming:
        return _fallback(access, "approach")
    best = max(
        enumerate(incoming),
        key=lambda item: (float(item[1].get("revealed_outcome") or 0.0), item[0]),
    )[1]
    return _fallback(access, str(best.get("action_taken", "approach")))


def baseline_successor_map(access: Mapping[str, Any]) -> str:
    records = list(access.get("public_history", []))
    transitions: dict[str, list[str]] = {}
    for before, after in zip(records, records[1:]):
        transitions.setdefault(str(before.get("action_taken", "")), []).append(
            str(after.get("action_taken", ""))
        )
    previous = str(records[-1].get("action_taken", "")) if records else ""
    successors = transitions.get(previous, [])
    return _fallback(access, sorted(successors)[0] if successors else "approach")


def baseline_fsm_planner(access: Mapping[str, Any]) -> str:
    cue = str(access["observation"].get("cue", "quiet"))
    records = list(access.get("public_history", []))
    edges = [record for record in records if str(record.get("cue", "")) == cue]
    if not edges:
        edges = [record for record in records if str(record.get("next_cue", "")) == cue]
    if not edges:
        return _fallback(access, "explore")
    planned = max(
        enumerate(edges),
        key=lambda item: (float(item[1].get("revealed_outcome") or 0.0), -item[0]),
    )[1]
    return _fallback(access, str(planned.get("action_taken", "explore")))


def baseline_episodic_traversal(access: Mapping[str, Any]) -> str:
    records = list(access.get("public_history", []))
    if not records:
        return _fallback(access, "approach")
    cue = str(access["observation"].get("cue", "quiet"))
    paths: list[list[Mapping[str, Any]]] = []
    for start in range(len(records)):
        path = records[start:]
        if path and str(path[-1].get("next_cue", "")) == cue:
            paths.append(path)
    if not paths:
        return _fallback(access, "approach")
    best_path = max(
        paths,
        key=lambda path: (
            sum(float(record.get("revealed_outcome") or 0.0) for record in path),
            len(path),
        ),
    )
    return _fallback(access, str(best_path[0].get("action_taken", "approach")))


def baseline_no_update_scores(access: Mapping[str, Any]) -> dict[str, float]:
    """Score fixed untrained priors against public organism deficits without updates."""

    organism = access.get("organism")
    if not isinstance(organism, Mapping) or set(organism) != set(_NO_UPDATE_STATE_KEYS):
        raise ValueError("no-update baseline organism schema mismatch")
    current = {key: float(organism[key]) for key in _NO_UPDATE_STATE_KEYS}
    before_deficit = sum(max(0.0, _NO_UPDATE_TARGET - current[key]) for key in _NO_UPDATE_STATE_KEYS)
    scores: dict[str, float] = {}
    for action in _legal(access):
        if action not in _NO_UPDATE_PRIORS or action not in _NO_UPDATE_COSTS:
            raise ValueError("no-update baseline action is not canonical")
        predicted = {
            key: max(0.0, min(1.0, current[key] + _NO_UPDATE_PRIORS[action][key]))
            for key in _NO_UPDATE_STATE_KEYS
        }
        after_deficit = sum(
            max(0.0, _NO_UPDATE_TARGET - predicted[key])
            for key in _NO_UPDATE_STATE_KEYS
        )
        scores[action] = round(
            before_deficit - after_deficit - _NO_UPDATE_COSTS[action], 9
        )
    return scores


def baseline_no_update(access: Mapping[str, Any]) -> str:
    scores = baseline_no_update_scores(access)
    return max(sorted(scores), key=lambda action: scores[action])


def baseline_from_scratch(access: Mapping[str, Any]) -> str:
    cue = str(access["observation"].get("cue", "quiet"))
    prior = {"resource": "forage", "contact": "approach", "novelty": "explore", "threat": "withdraw"}
    return _fallback(access, prior.get(cue, "rest"))


def baseline_count_table(access: Mapping[str, Any]) -> str:
    return _empirical_action(access, access.get("public_history", []))


def baseline_transition_table(access: Mapping[str, Any]) -> str:
    cue = str(access["observation"].get("cue", "quiet"))
    matched = [
        record
        for record in access.get("public_history", [])
        if str(record.get("next_cue", cue)) == cue
    ]
    return _empirical_action(access, matched or access.get("public_history", []))


BASELINE_PRODUCERS: dict[str, Callable[[Mapping[str, Any]], str]] = {
    "observation_only": baseline_observation_only,
    "q_only": baseline_q_only,
    "cue_clock_fsm": baseline_cue_clock_fsm,
    "last_success": baseline_last_success,
    "recency_window_1": baseline_recency_window_1,
    "recency_window_2": baseline_recency_window_2,
    "recency_window_4": baseline_recency_window_4,
    "exact_public_history_lookup": baseline_exact_public_history_lookup,
    "nearest_history": baseline_nearest_history,
    "graph_lookup": baseline_graph_lookup,
    "successor_map": baseline_successor_map,
    "fsm_planner": baseline_fsm_planner,
    "episodic_traversal": baseline_episodic_traversal,
    "no_update": baseline_no_update,
    "from_scratch": baseline_from_scratch,
    "count_table": baseline_count_table,
    "transition_table": baseline_transition_table,
}


# ---------------------------------------------------------------------------
# Leakage scanner.


_FORBIDDEN_ALIASES = {
    "hidden_regime": {"hidden_regime", "latent_mode", "private_mode"},
    "correct_action": {"correct_action", "optimal_action", "target_action"},
    "future_outcome": {"future_outcome", "next_outcome", "unrevealed_result"},
    "reward_label": {"reward", "reward_label", "utility_label"},
    "oracle": {"oracle", "oracle_verdict", "answer_key"},
    "stored_action": {"stored_action", "stored_selected_action"},
    "generator_seed": {"generator_seed", "world_seed", "drift_schedule"},
}
LEAKAGE_POSITIVE_CONTROLS = {
    "hidden_regime": ({"hidden_regime": "site_a_high"}, "hidden_regime", "/hidden_regime"),
    "renamed_hidden_regime": ({"latent_mode": "site_a_high"}, "hidden_regime", "/latent_mode"),
    "nested_correct_action": ({"nested": {"target_action": "forage"}}, "correct_action", "/nested/target_action"),
    "future_outcome": ({"next_outcome": 1.0}, "future_outcome", "/next_outcome"),
    "reward_label": ({"labels": {"utility_label": "positive"}}, "reward_label", "/labels/utility_label"),
    "oracle": ({"answer_key": "site_a"}, "oracle", "/answer_key"),
}


def scan_policy_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    offenders: list[dict[str, Any]] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                normalized = str(key).strip().lower().replace("-", "_")
                for category, aliases in _FORBIDDEN_ALIASES.items():
                    if normalized in aliases:
                        offenders.append(
                            {"path": f"{path}/{key}", "category": category, "reason": "forbidden_key_or_alias"}
                        )
                walk(item, f"{path}/{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}/{index}")

    walk(payload, "")
    root_keys = set(payload)
    expected_root = {
        "schema_version",
        "non_memory",
        "claim_retrieval",
        "resolved_memory_view",
    }
    if payload.get("schema_version") != "ego.life_playground.policy_projection.v2":
        offenders.append(
            {"path": "/schema_version", "category": "schema", "reason": "policy_projection_schema_version_mismatch"}
        )
    if root_keys != expected_root:
        offenders.append(
            {"path": "/", "category": "schema", "reason": "policy_projection_root_schema_mismatch"}
        )
    non_memory = payload.get("non_memory")
    if isinstance(non_memory, Mapping):
        expected = {
            "schema_version",
            "sequence",
            "policy_tie_seed",
            "context_key",
            "observation",
            "organism",
            "current_goal",
            "legal_actions",
            "action_paths",
            "model",
        }
        if non_memory.get("schema_version") != "ego.life_playground.policy_non_memory_projection.v2":
            offenders.append(
                {"path": "/non_memory/schema_version", "category": "schema", "reason": "non_memory_schema_version_mismatch"}
            )
        if set(non_memory) != expected:
            offenders.append(
                {"path": "/non_memory", "category": "schema", "reason": "non_memory_schema_mismatch"}
            )
        observation = non_memory.get("observation")
        if isinstance(observation, Mapping):
            expected_observation = {
                "schema_version",
                "event",
                "cue",
                "summary",
                "agent_position",
                "visible_object_ids",
                "revealed_outcome",
            }
            if observation.get("schema_version") == "ego.life_playground.microworld.observation.v3":
                expected_observation.add("layout_id")
            if set(observation) != expected_observation:
                offenders.append(
                    {"path": "/non_memory/observation", "category": "schema", "reason": "observation_schema_mismatch"}
                )
    return {
        "producer_function": "verify_ego_life_kernel_v2_microworld.scan_policy_projection",
        "payload_hash": _canonical_hash(payload),
        "offenders": offenders,
        "positive_control_detected": bool(offenders),
    }


def _normalized_physical_path_text(value: str) -> str:
    normalized = value.strip().casefold().replace("\\", "/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized.rstrip("/")


def scan_physical_output_root(payload: Any, output_root: str | Path) -> dict[str, Any]:
    """Scan parsed strings recursively without echoing a physical root into evidence."""

    root = _normalized_physical_path_text(str(Path(output_root).resolve()))
    offenders: list[dict[str, Any]] = []

    def inspect_string(value: str, location_tokens: list[str]) -> None:
        if root and root in _normalized_physical_path_text(value):
            offenders.append(
                {
                    "location_sha256": _canonical_hash(location_tokens),
                    "value_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
                    "reason": "physical_output_root_string_match",
                }
            )

    def walk(value: Any, location_tokens: list[str]) -> None:
        if isinstance(value, Mapping):
            for index, (key, item) in enumerate(value.items()):
                inspect_string(str(key), [*location_tokens, f"key:{index}"])
                walk(item, [*location_tokens, f"value:{index}"])
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                walk(item, [*location_tokens, f"item:{index}"])
        elif isinstance(value, str):
            inspect_string(value, location_tokens)

    walk(payload, ["root"])
    return {
        "producer_function": "verify_ego_life_kernel_v2_microworld.scan_physical_output_root",
        "scan_scope": "recursive_parsed_mapping_keys_values_and_sequence_strings",
        "normalization": "casefold_backslash_to_slash_and_repeated_slash_collapse",
        "physical_output_root_absent": not offenders,
        "offender_count": len(offenders),
        "offenders": offenders,
    }


def _redact_physical_output_root(payload: Any, output_root: str | Path) -> Any:
    root = _normalized_physical_path_text(str(Path(output_root).resolve()))

    def redact(value: Any) -> Any:
        if isinstance(value, Mapping):
            redacted: dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key)
                safe_key = (
                    f"redacted_key_{hashlib.sha256(key_text.encode('utf-8')).hexdigest()}"
                    if root and root in _normalized_physical_path_text(key_text)
                    else key_text
                )
                redacted[safe_key] = redact(item)
            return redacted
        if isinstance(value, list):
            return [redact(item) for item in value]
        if isinstance(value, tuple):
            return [redact(item) for item in value]
        if isinstance(value, str) and root and root in _normalized_physical_path_text(value):
            return "physical://redacted-output-root/sha256/" + hashlib.sha256(
                value.encode("utf-8")
            ).hexdigest()
        return deepcopy(value)

    return redact(payload)


# ---------------------------------------------------------------------------
# Candidate histories and interventions.


def _escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _json_pointer_diff(before: Any, after: Any, path: str = "") -> list[str]:
    if isinstance(before, Mapping) and isinstance(after, Mapping):
        pointers: list[str] = []
        for key in sorted(set(before) | set(after), key=str):
            child = f"{path}/{_escape_pointer(str(key))}"
            if key not in before or key not in after:
                pointers.append(child)
            else:
                pointers.extend(_json_pointer_diff(before[key], after[key], child))
        return pointers
    if isinstance(before, list) and isinstance(after, list):
        pointers = []
        for index in range(max(len(before), len(after))):
            child = f"{path}/{index}"
            if index >= len(before) or index >= len(after):
                pointers.append(child)
            else:
                pointers.extend(_json_pointer_diff(before[index], after[index], child))
        return pointers
    return [] if before == after else [path or "/"]


def _command_for(
    state: Mapping[str, Any], *, event: str, trigger_source: str = "paired_intervention"
) -> dict[str, Any]:
    return engine.make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        cue=microworld.cue_for_event(event),
        world_event=event,
        trigger_source=trigger_source,
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=state.get("last_command_hash"),
    )


def _step(
    state: Mapping[str, Any],
    *,
    run_id: str,
    event: str,
    interventions: Mapping[str, str] | None = None,
) -> engine.StepResult:
    command = engine.make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        cue=microworld.cue_for_event(event),
        world_event=event,
        trigger_source="paired_intervention",
        interventions=interventions or engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=state.get("last_command_hash"),
    )
    return engine.compute_step(state, command, engine.make_run_metadata(run_id, PAIR_POLICY_SEED))


def _history(run_id: str, seed: int) -> dict[str, Any]:
    state = engine.initial_state(run_id=run_id, seed=seed)
    initial = deepcopy(state)
    meta = engine.make_run_metadata(run_id, seed)
    commands: list[dict[str, Any]] = []
    results: list[engine.StepResult] = []
    traces: list[dict[str, Any]] = []
    public_history: list[dict[str, Any]] = []
    for event in HISTORY_EVENTS:
        command = _command_for(state, event=event)
        result = engine.compute_step(state, command, meta)
        commands.append(deepcopy(command))
        results.append(result)
        trace = result.trace
        public_history.append(
            {
                "cue": trace["observation"]["cue"],
                "observation_hash": trace["observation_hash"],
                "action_taken": trace["selected_action"],
                "revealed_outcome": trace["world_outcome"]["value"],
                "next_cue": PAIR_EVENT.replace("_interval", ""),
                "source_episode_id": trace["episode_id"],
                "source_command_hash": trace["command_hash"],
            }
        )
        traces.append(trace)
        state = result.next_state
    return {
        "run_id": run_id,
        "seed": seed,
        "initial_state": initial,
        "state": state,
        "commands": commands,
        "results": results,
        "traces": traces,
        "public_history": public_history,
    }


def _typed_memory_transplant(
    history: Mapping[str, Any], target_base: Mapping[str, Any], *, target_run_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    target = deepcopy(dict(target_base))
    target["memory"] = deepcopy(history["state"]["memory"])
    changed = sorted(_json_pointer_diff(target_base, target))
    if not changed or any(not pointer.startswith("/memory/") for pointer in changed):
        raise ValueError("typed transplant changed a non-memory field")
    non_memory_before = {key: deepcopy(value) for key, value in target_base.items() if key != "memory"}
    non_memory_after = {key: deepcopy(value) for key, value in target.items() if key != "memory"}
    if engine.canonical_json(non_memory_before) != engine.canonical_json(non_memory_after):
        raise ValueError("typed transplant changed non-memory bytes")
    record = {
        "schema_version": "ego.v2.p1.counterfactual_memory_lineage_transplant.v1",
        "construction_type": "typed_counterfactual_memory_lineage_transplant",
        "reachable_state_claim": False,
        "source_history_run_id": history["run_id"],
        "source_seed": history["seed"],
        "source_initial_state_hash": engine.state_hash(history["initial_state"]),
        "source_terminal_state_hash": engine.state_hash(history["state"]),
        "source_memory_hash": engine.canonical_hash(history["state"]["memory"]),
        "source_command_hashes": [command["command_hash"] for command in history["commands"]],
        "source_trace_hashes": [result.trace["trace_hash"] for result in history["results"]],
        "target_run_id": target_run_id,
        "target_episode_id": target["clock"]["episode_id"],
        "target_base_state_hash": engine.state_hash(target_base),
        "target_checkpoint_state_hash": engine.state_hash(target),
        "target_memory_before_hash": engine.canonical_hash(target_base["memory"]),
        "target_memory_after_hash": engine.canonical_hash(target["memory"]),
        "target_non_memory_hash_before": engine.canonical_hash(non_memory_before),
        "target_non_memory_hash_after": engine.canonical_hash(non_memory_after),
        "operation": "replace_/memory_from_source_terminal_state",
        "changed_json_pointers": changed,
    }
    return target, record


def _run_stream(
    state: Mapping[str, Any],
    *,
    run_id: str,
    events: Iterable[str],
    interventions: Mapping[str, str],
) -> dict[str, Any]:
    current = deepcopy(dict(state))
    initial_hash = engine.state_hash(current)
    results: list[engine.StepResult] = []
    for event in events:
        result = _step(
            current,
            run_id=run_id,
            event=event,
            interventions=interventions,
        )
        results.append(result)
        current = result.next_state
    return {
        "initial_state_hash": initial_hash,
        "terminal_state_hash": engine.state_hash(current),
        "terminal_state": current,
        "results": results,
    }


def _paired_runs() -> dict[str, Any]:
    histories = {
        "a": _history("p1-history-a", HISTORY_SEEDS[0]),
        "b": _history("p1-history-b", HISTORY_SEEDS[1]),
    }
    target_bases = {
        "a": engine.initial_state(run_id="p1-pair-a", seed=HISTORY_SEEDS[0]),
        "b": engine.initial_state(run_id="p1-pair-b", seed=HISTORY_SEEDS[1]),
    }
    state_a, transplant_a = _typed_memory_transplant(
        histories["a"], target_bases["a"], target_run_id="p1-pair-a"
    )
    state_b, transplant_b = _typed_memory_transplant(
        histories["b"], target_bases["b"], target_run_id="p1-pair-b"
    )
    canonical_a = _step(state_a, run_id="p1-pair-a", event=PAIR_EVENT)
    canonical_b = _step(state_b, run_id="p1-pair-b", event=PAIR_EVENT)
    off = dict(engine.DEFAULT_INTERVENTIONS, memory_mode="off")
    off_a = _step(state_a, run_id="p1-pair-a", event=PAIR_EVENT, interventions=off)
    off_b = _step(state_b, run_id="p1-pair-b", event=PAIR_EVENT, interventions=off)
    frozen = dict(engine.DEFAULT_INTERVENTIONS, update_mode="frozen")
    q_only = dict(engine.DEFAULT_INTERVENTIONS, memory_mode="off", update_mode="frozen")
    from_scratch_mode = dict(engine.DEFAULT_INTERVENTIONS, update_mode="frozen")
    q_only_runs = {
        "a": _step(state_a, run_id="p1-pair-a", event=PAIR_EVENT, interventions=q_only),
        "b": _step(state_b, run_id="p1-pair-b", event=PAIR_EVENT, interventions=q_only),
    }
    from_scratch_states: dict[str, dict[str, Any]] = {}
    from_scratch_runs: dict[str, engine.StepResult] = {}
    for side, state in (("a", state_a), ("b", state_b)):
        scratch = deepcopy(state)
        scratch["memory"] = {"episodic": [], "consolidated": [], **claims.empty_claim_memory()}
        scratch["model"] = {}
        from_scratch_states[side] = scratch
        from_scratch_runs[side] = _step(
            scratch,
            run_id=f"p1-pair-{side}",
            event=PAIR_EVENT,
            interventions=from_scratch_mode,
        )

    streams: dict[str, dict[str, Any]] = {}
    for side, state in (("a", state_a), ("b", state_b)):
        streams[side] = {
            "enabled": _run_stream(
                state,
                run_id=f"p1-pair-{side}",
                events=MATCHED_UPDATE_STREAM_EVENTS,
                interventions=engine.DEFAULT_INTERVENTIONS,
            ),
            "frozen": _run_stream(
                state,
                run_id=f"p1-pair-{side}",
                events=MATCHED_UPDATE_STREAM_EVENTS,
                interventions=frozen,
            ),
        }
    shuffled_mode = dict(engine.DEFAULT_INTERVENTIONS, provenance_mode="shuffle_projection")
    shuffled_frozen_mode = dict(shuffled_mode, update_mode="frozen")
    shuffled = {
        "a": _step(state_a, run_id="p1-pair-a", event=PAIR_EVENT, interventions=shuffled_mode),
        "b": _step(state_b, run_id="p1-pair-b", event=PAIR_EVENT, interventions=shuffled_mode),
    }
    shuffled_frozen = {
        "a": _step(state_a, run_id="p1-pair-a", event=PAIR_EVENT, interventions=shuffled_frozen_mode),
        "b": _step(state_b, run_id="p1-pair-b", event=PAIR_EVENT, interventions=shuffled_frozen_mode),
    }

    supporting_events = [
        event
        for event in state_a["memory"]["claim_events"]
        if event["value"] == canonical_a.trace["selected_action"]
        and float(event["evidence_strength"]) > 0.0
    ]
    relevant = supporting_events[0] if supporting_events else None
    target_selection = {
        "producer_function": (
            "verify_ego_life_kernel_v2_microworld.select_source_deletion_target"
        ),
        "target_rule": "first_supporting_event_for_selected_site",
        "selected_action": canonical_a.trace["selected_action"],
        "matching_event_ids": [str(event["event_id"]) for event in supporting_events],
        "selected_event_id": str(relevant["event_id"]) if relevant is not None else None,
        "status": "selected" if relevant is not None else "unavailable_no_supporting_event",
    }
    deleted_memory, deletion_report = claims.delete_sources(
        state_a["memory"],
        event_ids=[relevant["event_id"]] if relevant is not None else (),
    )
    deleted_state = deepcopy(state_a)
    deleted_state["memory"] = deleted_memory
    deleted_a = _step(deleted_state, run_id="p1-pair-a", event=PAIR_EVENT)
    irrelevant_memory, irrelevant_report = claims.delete_sources(
        state_a["memory"], source_episode_ids=["episode-not-present"]
    )
    irrelevant_state = deepcopy(state_a)
    irrelevant_state["memory"] = irrelevant_memory
    irrelevant_a = _step(irrelevant_state, run_id="p1-pair-a", event=PAIR_EVENT)
    return {
        "histories": histories,
        "target_bases": target_bases,
        "transplants": {"a": transplant_a, "b": transplant_b},
        "states": {"a": state_a, "b": state_b},
        "canonical": {"a": canonical_a, "b": canonical_b},
        "memory_off": {"a": off_a, "b": off_b},
        "q_only": q_only_runs,
        "from_scratch": from_scratch_runs,
        "from_scratch_states": from_scratch_states,
        "streams": streams,
        "shuffled": shuffled,
        "shuffled_frozen": shuffled_frozen,
        "deleted_a": deleted_a,
        "irrelevant_a": irrelevant_a,
        "deleted_input_state": deleted_state,
        "irrelevant_input_state": irrelevant_state,
        "deletion_report": deletion_report,
        "source_deletion_target_selection": target_selection,
        "irrelevant_report": irrelevant_report,
    }


def _baseline_access(
    history: Mapping[str, Any],
    trace: Mapping[str, Any],
    *,
    reference_episodes: Iterable[Iterable[Mapping[str, Any]]],
) -> dict[str, Any]:
    public_history = deepcopy(history["public_history"])
    return {
        "schema_version": "ego.v2.p1.baseline_access.v1",
        "observation": deepcopy(trace["observation"]),
        "legal_actions": deepcopy(trace["legal_actions"]),
        "organism": deepcopy(trace["policy_non_memory_projection"]["organism"]),
        "current_goal": trace["policy_non_memory_projection"]["current_goal"]["state_variable"] or "homeostasis",
        "public_history": public_history,
        "query_history_prefix": deepcopy(public_history[:-1]),
        "reference_episodes": [deepcopy(list(episode)) for episode in reference_episodes],
    }


def _baseline_report(pair: Mapping[str, Any], input_artifacts: list[Mapping[str, Any]]) -> dict[str, Any]:
    candidate_actions = [pair["canonical"][side].trace["selected_action"] for side in ("a", "b")]
    accesses = {
        side: _baseline_access(
            pair["histories"][side],
            pair["canonical"][side].trace,
            reference_episodes=[
                pair["histories"][reference_side]["public_history"]
                for reference_side in ("a", "b")
            ],
        )
        for side in ("a", "b")
    }
    comparisons: list[dict[str, Any]] = []
    invocation_ledger: list[dict[str, Any]] = []
    for name, producer in BASELINE_PRODUCERS.items():
        actions = [producer(accesses[side]) for side in ("a", "b")]
        matches = [int(action == candidate) for action, candidate in zip(actions, candidate_actions)]
        match_rate = sum(matches) / len(matches)
        evidence = _evidence(
            producer_function=f"verify_ego_life_kernel_v2_microworld.{producer.__name__}",
            input_artifacts=input_artifacts,
            run_id=P1_RUN_ID,
            seed_context_episode_ids={"seeds": list(HISTORY_SEEDS), "pair_id": PAIR_ID},
            aggregation_rule="exact_selected_action_match_over_two_frozen_paired_checkpoints",
            value={"actions": actions, "candidate_actions": candidate_actions, "match_rate": match_rate},
        )
        comparison = {
            "baseline_id": name,
            "actions": actions,
            "candidate_actions": candidate_actions,
            "match_rate": match_rate,
            "evidence": evidence,
        }
        if name == "no_update":
            comparison["access_contract"] = deepcopy(NO_UPDATE_ACCESS_CONTRACT)
        comparisons.append(comparison)
        for side, action in zip(("a", "b"), actions):
            invocation_ledger.append(
                {
                    "producer_function": producer.__name__,
                    "baseline_id": name,
                    "side": side,
                    "seed": pair["histories"][side]["seed"],
                    "pair_id": PAIR_ID,
                    "invoked": True,
                    "input_access_hash": _canonical_hash(accesses[side]),
                    "output_action": action,
                    "code_path_hash": _verifier_code_hash(),
                }
            )
    strongest = max(
        comparisons,
        key=lambda item: (
            float(item["match_rate"]),
            item["baseline_id"] == "transition_table",
            item["baseline_id"],
        ),
    )
    return {
        "schema_version": "ego.v2.p1.baseline_comparison.v1",
        "candidate_actions": candidate_actions,
        "comparisons": comparisons,
        "baseline_access": accesses,
        "strongest_matching_control": strongest["baseline_id"],
        "strongest_match_rate": strongest["match_rate"],
        "control_equivalent": strongest["match_rate"] == 1.0,
        "invocation_ledger": invocation_ledger,
        "evidence": _evidence(
            producer_function="verify_ego_life_kernel_v2_microworld._baseline_report",
            input_artifacts=input_artifacts,
            run_id=P1_RUN_ID,
            seed_context_episode_ids={"seeds": list(HISTORY_SEEDS), "pair_id": PAIR_ID},
            aggregation_rule="maximum_exact_action_match_rate_across_all_predeclared_controls",
            value={"strongest": strongest["baseline_id"], "match_rate": strongest["match_rate"]},
        ),
    }


def _step_output_record(
    result: engine.StepResult,
    *,
    intervention_id: str,
    side: str,
    input_state_hash: str,
    stream_step: int | None = None,
) -> dict[str, Any]:
    trace = result.trace
    if trace.get("trace_hash") != engine.compute_trace_hash(trace):
        raise ValueError("actual StepResult trace hash mismatch")
    if trace.get("state_after_hash") != engine.state_hash(result.next_state):
        raise ValueError("actual StepResult state hash mismatch")
    if trace.get("state_before_hash") != input_state_hash:
        raise ValueError("actual StepResult input state hash mismatch")
    record = {
        "producer_function": "ego_life_playground_v0.engine.compute_step",
        "intervention_id": intervention_id,
        "side": side,
        "seed": int(trace["seed"]),
        "pair_id": PAIR_ID,
        "invoked": True,
        "input_state_hash": input_state_hash,
        "state_before_hash": trace["state_before_hash"],
        "command_hash": trace["command_hash"],
        "trace_hash": trace["trace_hash"],
        "state_after_hash": trace["state_after_hash"],
        "candidate_hash": _canonical_hash(trace["candidates"]),
        "prediction_hash": _canonical_hash(trace["prediction"]),
        "output_action": trace["selected_action"],
        "interventions": deepcopy(trace["interventions"]),
        "code_path_hash": _verifier_code_hash(),
    }
    if stream_step is not None:
        record["stream_step"] = stream_step
    return record


def _claim_projection(memory: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "claim_events": deepcopy(memory["claim_events"]),
        "competing_claims": deepcopy(memory["competing_claims"]),
    }


def _ablation_report(pair: Mapping[str, Any], input_artifacts: list[Mapping[str, Any]]) -> dict[str, Any]:
    canonical_actions = [pair["canonical"][side].trace["selected_action"] for side in ("a", "b")]
    off_actions = [pair["memory_off"][side].trace["selected_action"] for side in ("a", "b")]
    canonical_a = pair["canonical"]["a"]
    deleted = pair["deleted_a"]
    irrelevant = pair["irrelevant_a"]

    def ev(name: str, value: Any) -> dict[str, Any]:
        return _evidence(
            producer_function=f"verify_ego_life_kernel_v2_microworld.ablation_{name}",
            input_artifacts=input_artifacts,
            run_id=P1_RUN_ID,
            seed_context_episode_ids={"seeds": list(HISTORY_SEEDS), "pair_id": PAIR_ID},
            aggregation_rule="same_serialized_checkpoint_plus_same_ordered_command_intervention_rerun",
            value=value,
        )

    records: list[dict[str, Any]] = []

    def side_records(intervention_id: str, runs: Mapping[str, engine.StepResult], input_states: Mapping[str, Any]) -> dict[str, Any]:
        sides: dict[str, Any] = {}
        for side in ("a", "b"):
            record = _step_output_record(
                runs[side],
                intervention_id=intervention_id,
                side=side,
                input_state_hash=engine.state_hash(input_states[side]),
            )
            records.append(record)
            sides[side] = deepcopy(record)
        return sides

    memory_off_sides = side_records("Memory_OFF", pair["memory_off"], pair["states"])
    q_only_sides = side_records("Q_only", pair["q_only"], pair["states"])
    from_scratch_sides = side_records(
        "from_scratch", pair["from_scratch"], pair["from_scratch_states"]
    )
    memory_off_value = {
        "canonical_actions": canonical_actions,
        "off_actions": off_actions,
        "paired_difference_removed": off_actions[0] == off_actions[1],
        "candidate_bytes_equal": engine.canonical_json(pair["memory_off"]["a"].trace["candidates"])
        == engine.canonical_json(pair["memory_off"]["b"].trace["candidates"]),
        "sides": memory_off_sides,
    }

    stream_reports: dict[str, Any] = {}
    frozen_model_preserved: list[bool] = []
    frozen_memory_preserved: list[bool] = []
    frozen_terminal_model_preserved: list[bool] = []
    frozen_terminal_memory_preserved: list[bool] = []
    world_transitions: list[bool] = []
    downstream_prediction_contrasts: list[bool] = []
    downstream_total_score_contrasts: list[bool] = []
    downstream_action_contrasts: list[bool] = []
    downstream_by_side: dict[str, Any] = {}
    downstream_any_by_side: list[bool] = []
    step1_matches: list[bool] = []
    enabled_step1_updates: list[bool] = []
    step2_observation_matches: list[bool] = []
    for side in ("a", "b"):
        stream_reports[side] = {}
        for mode in ("enabled", "frozen"):
            stream = pair["streams"][side][mode]
            outputs: list[dict[str, Any]] = []
            prior_hash = stream["initial_state_hash"]
            for index, result in enumerate(stream["results"], start=1):
                record = _step_output_record(
                    result,
                    intervention_id=f"Freeze_Updates_{mode}",
                    side=side,
                    input_state_hash=prior_hash,
                    stream_step=index,
                )
                records.append(record)
                outputs.append(deepcopy(record))
                prior_hash = record["state_after_hash"]
                world_transitions.append(
                    result.trace["world_before_hash"] != result.trace["world_after_hash"]
                )
                if mode == "frozen":
                    frozen_model_preserved.append(
                        result.trace["model_bytes"]["before_hash"]
                        == result.trace["model_bytes"]["after_hash"]
                    )
                    frozen_memory_preserved.append(
                        result.trace["memory_bytes"]["before_hash"]
                        == result.trace["memory_bytes"]["after_hash"]
                    )
            initial_model_hash = engine.canonical_hash(pair["states"][side]["model"])
            initial_memory_hash = engine.canonical_hash(pair["states"][side]["memory"])
            terminal_model_hash = engine.canonical_hash(stream["terminal_state"]["model"])
            terminal_memory_hash = engine.canonical_hash(stream["terminal_state"]["memory"])
            stream_reports[side][mode] = {
                "initial_state_hash": stream["initial_state_hash"],
                "terminal_state_hash": stream["terminal_state_hash"],
                "initial_model_hash": initial_model_hash,
                "initial_memory_hash": initial_memory_hash,
                "terminal_model_hash": terminal_model_hash,
                "terminal_memory_hash": terminal_memory_hash,
                "terminal_model_matches_initial": terminal_model_hash == initial_model_hash,
                "terminal_memory_matches_initial": terminal_memory_hash == initial_memory_hash,
                "outputs": outputs,
            }
            if mode == "frozen":
                frozen_terminal_model_preserved.append(terminal_model_hash == initial_model_hash)
                frozen_terminal_memory_preserved.append(terminal_memory_hash == initial_memory_hash)
        enabled_results = pair["streams"][side]["enabled"]["results"]
        frozen_results = pair["streams"][side]["frozen"]["results"]
        enabled_first = enabled_results[0].trace
        frozen_first = frozen_results[0].trace
        step1_matches.append(
            enabled_first["observation_hash"] == frozen_first["observation_hash"]
            and enabled_first["selected_action"] == frozen_first["selected_action"]
            and enabled_first["world_outcome"] == frozen_first["world_outcome"]
        )
        enabled_step1_updates.append(
            enabled_first["model_update"].get("applied") is True
            or enabled_first["claim_update"].get("applied") is True
        )
        enabled_later = enabled_results[1].trace
        frozen_later = frozen_results[1].trace
        step2_observation_matches.append(
            enabled_later["observation_hash"] == frozen_later["observation_hash"]
        )
        enabled_total_scores = [
            {"action": candidate["action"], "total_score": candidate["total_score"]}
            for candidate in sorted(
                enabled_later["candidates"], key=lambda candidate: candidate["action"]
            )
        ]
        frozen_total_scores = [
            {"action": candidate["action"], "total_score": candidate["total_score"]}
            for candidate in sorted(
                frozen_later["candidates"], key=lambda candidate: candidate["action"]
            )
        ]
        enabled_predictions = [
            {
                "action": candidate["action"],
                "predicted_delta": deepcopy(candidate["predicted_delta"]),
            }
            for candidate in sorted(
                enabled_later["candidates"], key=lambda candidate: candidate["action"]
            )
        ]
        frozen_predictions = [
            {
                "action": candidate["action"],
                "predicted_delta": deepcopy(candidate["predicted_delta"]),
            }
            for candidate in sorted(
                frozen_later["candidates"], key=lambda candidate: candidate["action"]
            )
        ]
        total_score_contrast = (
            engine.canonical_json(enabled_total_scores)
            != engine.canonical_json(frozen_total_scores)
        )
        prediction_contrast = (
            engine.canonical_json(enabled_predictions)
            != engine.canonical_json(frozen_predictions)
        )
        action_contrast = (
            enabled_later["selected_action"] != frozen_later["selected_action"]
        )
        downstream_prediction_contrasts.append(prediction_contrast)
        downstream_total_score_contrasts.append(total_score_contrast)
        downstream_action_contrasts.append(action_contrast)
        downstream_any_by_side.append(prediction_contrast or total_score_contrast)
        downstream_by_side[side] = {
            "enabled_total_score_vector": enabled_total_scores,
            "frozen_total_score_vector": frozen_total_scores,
            "total_score_contrast": total_score_contrast,
            "enabled_prediction_vector": enabled_predictions,
            "frozen_prediction_vector": frozen_predictions,
            "prediction_contrast": prediction_contrast,
            "enabled_selected_action": enabled_later["selected_action"],
            "frozen_selected_action": frozen_later["selected_action"],
            "selected_action_contrast": action_contrast,
        }
    freeze_value = {
        "matched_stream_events": list(MATCHED_UPDATE_STREAM_EVENTS),
        "matched_streams_present": all(
            len(pair["streams"][side][mode]["results"]) == len(MATCHED_UPDATE_STREAM_EVENTS)
            for side in ("a", "b")
            for mode in ("enabled", "frozen")
        ),
        "model_bytes_preserved": all(frozen_model_preserved)
        and all(frozen_terminal_model_preserved),
        "claim_and_event_bytes_preserved": all(frozen_memory_preserved)
        and all(frozen_terminal_memory_preserved),
        "world_transition_active": any(world_transitions),
        "step1_matched_by_side": dict(zip(("a", "b"), step1_matches)),
        "enabled_step1_update_applied_by_side": dict(
            zip(("a", "b"), enabled_step1_updates)
        ),
        "step2_observation_equal_by_side": dict(
            zip(("a", "b"), step2_observation_matches)
        ),
        "later_prediction_contrast_by_side": dict(zip(("a", "b"), downstream_prediction_contrasts)),
        "later_total_score_contrast_by_side": dict(
            zip(("a", "b"), downstream_total_score_contrasts)
        ),
        "later_action_contrast_by_side": dict(zip(("a", "b"), downstream_action_contrasts)),
        "later_prediction_or_total_score_contrast_by_side": dict(
            zip(("a", "b"), downstream_any_by_side)
        ),
        "later_prediction_or_total_score_contrast": any(downstream_any_by_side),
        "later_downstream_by_side": downstream_by_side,
        "streams": stream_reports,
    }

    shuffle_sides = side_records("Shuffle_Provenance", pair["shuffled"], pair["states"])
    shuffle_frozen_sides = side_records(
        "Shuffle_Provenance_Frozen", pair["shuffled_frozen"], pair["states"]
    )
    persisted_invariance: dict[str, bool] = {}
    frozen_memory_exact: dict[str, bool] = {}
    for side in ("a", "b"):
        shuffled = pair["shuffled"][side]
        event_id = shuffled.trace["claim_update"]["event_id"]
        if not isinstance(event_id, str) or not event_id:
            persisted_invariance[side] = (
                engine.canonical_json(_claim_projection(shuffled.next_state["memory"]))
                == engine.canonical_json(_claim_projection(pair["states"][side]["memory"]))
            )
        else:
            without_current, deletion = claims.delete_sources(
                shuffled.next_state["memory"], event_ids=[event_id]
            )
            persisted_invariance[side] = (
                deletion["deleted_event_ids"] == [event_id]
                and engine.canonical_json(_claim_projection(without_current))
                == engine.canonical_json(_claim_projection(pair["states"][side]["memory"]))
            )
        frozen_memory_exact[side] = (
            engine.canonical_json(pair["shuffled_frozen"][side].next_state["memory"])
            == engine.canonical_json(pair["states"][side]["memory"])
        )
    projections = {
        side: pair["shuffled"][side].trace["provenance_projection"]
        for side in ("a", "b")
    }
    projection_a = projections["a"]
    source_bundle_multiset_preserved = all(
        bool(item.get("event_value_multiset_preserved"))
        or bool(item.get("marginal_preservation", {}).get("bundle_multiset_preserved"))
        for item in projections.values()
    )
    source_slot_counts_preserved = all(
        bool(item.get("non_provenance_claim_fields_preserved"))
        or bool(item.get("marginal_preservation", {}).get("slot_counts_preserved"))
        for item in projections.values()
    )
    shuffle_value = {
        "status": projection_a["status"],
        "seed": projection_a.get("seed"),
        "configured_seed": PROVENANCE_SHUFFLE_SEED,
        "event_value_multiset_preserved": source_bundle_multiset_preserved,
        "non_provenance_claim_fields_preserved": source_slot_counts_preserved,
        "source_bundle_multiset_preserved": source_bundle_multiset_preserved,
        "source_slot_counts_preserved": source_slot_counts_preserved,
        "unaffected_fields_hash_before": projection_a.get("unaffected_fields_hash_before"),
        "unaffected_fields_hash_after": projection_a.get("unaffected_fields_hash_after"),
        "unaffected_fields_preserved": all(
            item.get("unaffected_fields_hash_before") == item.get("unaffected_fields_hash_after")
            for item in projections.values()
        ),
        "changed_json_pointers": deepcopy(projection_a.get("changed_json_pointers", [])),
        "support_effect_changed": any(
            pair["shuffled"][side].trace["claim_retrieval"]["support_by_action"]
            != pair["canonical"][side].trace["claim_retrieval"]["support_by_action"]
            for side in ("a", "b")
        ),
        "persisted_memory_unchanged_before_current_write": all(persisted_invariance.values()),
        "persisted_memory_invariance_by_side": persisted_invariance,
        "frozen_projection_memory_exact": all(frozen_memory_exact.values()),
        "frozen_projection_memory_exact_by_side": frozen_memory_exact,
        "sides": shuffle_sides,
        "frozen_sides": shuffle_frozen_sides,
    }
    source_value = {
        "intervention_executed": True,
        "target_available": pair["source_deletion_target_selection"]["status"] == "selected",
        "target_selection": deepcopy(pair["source_deletion_target_selection"]),
        "deleted_event_ids": deepcopy(pair["deletion_report"]["deleted_event_ids"]),
        "relevant_changed_action": deleted.trace["selected_action"] != canonical_a.trace["selected_action"],
        "irrelevant_inert": irrelevant.trace["selected_action"] == canonical_a.trace["selected_action"]
        and pair["irrelevant_report"]["deleted_event_ids"] == [],
    }
    relevant_record = _step_output_record(
        deleted,
        intervention_id="source_deletion_relevant",
        side="a",
        input_state_hash=engine.state_hash(pair["deleted_input_state"]),
    )
    irrelevant_record = _step_output_record(
        irrelevant,
        intervention_id="source_deletion_irrelevant",
        side="a",
        input_state_hash=engine.state_hash(pair["irrelevant_input_state"]),
    )
    records.extend((relevant_record, irrelevant_record))
    q_only_value = {"sides": q_only_sides}
    from_scratch_value = {
        "sides": from_scratch_sides,
        "input_transforms": {
            side: {
                "source_checkpoint_hash": engine.state_hash(pair["states"][side]),
                "transformed_checkpoint_hash": engine.state_hash(pair["from_scratch_states"][side]),
                "changed_json_pointers": sorted(
                    _json_pointer_diff(pair["states"][side], pair["from_scratch_states"][side])
                ),
            }
            for side in ("a", "b")
        },
    }
    return {
        "schema_version": "ego.v2.p1.ablation_report.v2",
        "memory_off": {**memory_off_value, "evidence": ev("memory_off", memory_off_value)},
        "freeze_updates": {**freeze_value, "evidence": ev("freeze_updates", freeze_value)},
        "shuffle_provenance": {**shuffle_value, "evidence": ev("shuffle_provenance", shuffle_value)},
        "source_deletion": {
            **source_value,
            "outputs": {"relevant": relevant_record, "irrelevant": irrelevant_record},
            "evidence": ev("source_deletion", source_value),
        },
        "q_only": {**q_only_value, "evidence": ev("q_only", q_only_value)},
        "from_scratch": {**from_scratch_value, "evidence": ev("from_scratch", from_scratch_value)},
        "invocation_ledger": records,
        "evidence": ev(
            "aggregate",
            {
                "memory_off_removed": memory_off_value["paired_difference_removed"],
                "freeze_preserved": freeze_value["model_bytes_preserved"]
                and freeze_value["claim_and_event_bytes_preserved"],
                "freeze_downstream_contrast": freeze_value[
                    "later_prediction_or_total_score_contrast"
                ],
                "shuffle_changed": shuffle_value["support_effect_changed"],
                "source_changed": source_value["relevant_changed_action"],
            },
        ),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def _write_combined_trace(
    store: SQLiteEventStore, output: Path, run_ids: Iterable[str]
) -> None:
    rows: list[dict[str, Any]] = []
    for run_id in run_ids:
        recovered = store.recover_run(run_id)
        initial_row = store.connection.execute(
            "SELECT initial_state_hash FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        rows.append(
            {
                "record_type": "run",
                "producer_function": "verify_ego_life_kernel_v2_microworld._write_combined_trace",
                "input_artifacts": [GENERATED_DB_LOGICAL_ID],
                "run_id": run_id,
                "seed": recovered.run_meta["seed"],
                "initial_state_hash": initial_row["initial_state_hash"],
                "terminal_state_hash": engine.state_hash(recovered.state),
                "command_count": recovered.command_count,
                "aggregation_rule": "ordered_recomputed_multi_run_trace_export",
                "code_path_hash": recovered.run_meta["code_path_hash"],
            }
        )
        command_rows = store.connection.execute(
            "SELECT sequence, command_json FROM commands WHERE run_id = ? ORDER BY sequence",
            (run_id,),
        ).fetchall()
        for command_row, trace in zip(command_rows, recovered.traces):
            command = json.loads(command_row["command_json"])
            rows.append(
                {
                    "record_type": "command",
                    "run_id": run_id,
                    "sequence": int(command_row["sequence"]),
                    "command": command,
                    "command_hash": command["command_hash"],
                }
            )
            rows.append(
                {
                    "record_type": "trace",
                    "run_id": run_id,
                    "sequence": int(command_row["sequence"]),
                    "trace": trace,
                    "trace_hash": trace["trace_hash"],
                }
            )
    output.write_text(
        "".join(_canonical_json(row) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def _create_product_db(output: Path, pair: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    db_path = output / "continuity.sqlite3"
    if db_path.exists():
        db_path.unlink()
    trace_path = output / "trace.jsonl"
    if trace_path.exists():
        trace_path.unlink()
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(store, run_id="p1-product-trigger", seed=18)
        terminal = TerminalPlayground(controller)
        outputs = [terminal.execute("inject resource_appears"), terminal.execute("run 23"), terminal.execute("pause"), terminal.execute("inspect")]
        source_recovery: dict[str, Any] = {}

        # Persist the actual source histories, not only regenerated summaries.
        for side in ("a", "b"):
            history = pair["histories"][side]
            meta = engine.make_run_metadata(history["run_id"], history["seed"])
            store.create_run(meta, history["initial_state"])
            for command, result in zip(history["commands"], history["results"]):
                receipt = store.append_step(command, result.trace)
                if not receipt.committed:
                    raise RuntimeError(receipt.error)
            recovered_history = store.recover_run(history["run_id"])
            if engine.state_hash(recovered_history.state) != engine.state_hash(history["state"]):
                raise RuntimeError("persisted source history terminal state mismatch")
            source_recovery[side] = {
                "run_id": history["run_id"],
                "command_count": recovered_history.command_count,
                "terminal_state_hash": engine.state_hash(recovered_history.state),
                "terminal_memory_hash": engine.canonical_hash(recovered_history.state["memory"]),
                "trace_hashes": [trace["trace_hash"] for trace in recovered_history.traces],
            }

        # Persist the paired checkpoints as immutable initial states plus one
        # command, allowing replay/tamper controls to target real claim bytes.
        for side in ("a", "b"):
            run_id = f"p1-pair-{side}"
            state = deepcopy(pair["states"][side])
            meta = engine.make_run_metadata(run_id, PAIR_POLICY_SEED)
            store.create_run(meta, state)
            command = engine.make_command(
                sequence=1,
                cue=microworld.cue_for_event(PAIR_EVENT),
                world_event=PAIR_EVENT,
                trigger_source="paired_intervention",
                interventions=engine.DEFAULT_INTERVENTIONS,
                prev_command_hash=None,
            )
            computed = engine.compute_step(state, command, meta)
            receipt = store.append_step(command, computed.trace)
            if not receipt.committed:
                raise RuntimeError(receipt.error)

        pair_recovery = {
            side: store.recover_run(f"p1-pair-{side}") for side in ("a", "b")
        }
        for side in ("a", "b"):
            if (
                engine.canonical_hash(pair_recovery[side].frames[0].state["memory"])
                != source_recovery[side]["terminal_memory_hash"]
            ):
                raise RuntimeError("transplanted pair memory is not source-history grounded")

        counts = store.row_counts(controller.run_id)
        product_state_hash = engine.state_hash(controller.state)
        product_trace_hash = controller.last_trace["trace_hash"]
        snapshot_hash = _canonical_hash(outputs[-1]["snapshot"])

    run_ids = (
        "p1-product-trigger",
        "p1-history-a",
        "p1-history-b",
        "p1-pair-a",
        "p1-pair-b",
    )
    with SQLiteEventStore(db_path) as reopened:
        recovered = reopened.recover_run("p1-product-trigger")
        recovered_runs = {run_id: reopened.recover_run(run_id) for run_id in run_ids}
        _write_combined_trace(reopened, trace_path, run_ids)
    trigger = {
        "schema_version": "ego.v2.p1.product_trigger_receipt.v1",
        "producer_function": "verify_ego_life_kernel_v2_microworld._create_product_db",
        "trigger_source": "terminal_event_then_terminal_run",
        "statuses": [item["status"] for item in outputs],
        "command_rows": counts[0],
        "trace_rows": counts[1],
        "fresh_store_recomputed": recovered.recovered,
        "fresh_state_hash": engine.state_hash(recovered.state),
        "expected_state_hash": product_state_hash,
        "trace_hash": product_trace_hash,
        "rendered_snapshot_hash": snapshot_hash,
        "redraw_after_commit": True,
        "explicit_local_launch_only": True,
        "switches": deepcopy(SWITCHES),
        "evidence": _evidence(
            producer_function="verify_ego_life_kernel_v2_microworld._create_product_db",
            input_artifacts=[
                _input_artifact(db_path, logical_id=GENERATED_DB_LOGICAL_ID),
                _input_artifact(trace_path, logical_id=GENERATED_TRACE_LOGICAL_ID),
            ],
            run_id="p1-product-trigger",
            seed_context_episode_ids={"seed": 18, "episode_id": recovered.state["clock"]["episode_id"]},
            aggregation_rule="terminal_commands_atomically_committed_then_fresh_store_recomputed",
            value={"command_rows": counts[0], "trace_rows": counts[1], "state_match": engine.state_hash(recovered.state) == product_state_hash},
        ),
    }
    replay_base = {
        "recomputed": recovered.recovered,
        "command_count": recovered.command_count,
        "state_hash": engine.state_hash(recovered.state),
        "trace_hash": recovered.traces[-1]["trace_hash"],
        "recovered_runs": {
            run_id: {
                "command_count": item.command_count,
                "initial_state_hash": engine.state_hash(item.frames[0].state),
                "terminal_state_hash": engine.state_hash(item.state),
                "trace_hashes": [trace["trace_hash"] for trace in item.traces],
            }
            for run_id, item in recovered_runs.items()
        },
    }
    return trigger, replay_base


def _tamper_control(db_path: Path, control_id: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ego-v2-p1-tamper-") as temporary:
        copy_path = Path(temporary) / "tamper.sqlite3"
        shutil.copy2(db_path, copy_path)
        connection = sqlite3.connect(str(copy_path))
        connection.row_factory = sqlite3.Row
        if control_id == "initial_private_world":
            row = connection.execute("SELECT initial_state_json FROM runs WHERE run_id = ?", ("p1-product-trigger",)).fetchone()
            state = json.loads(row["initial_state_json"])
            state["world"]["private_dynamics"]["hidden_regime"] = (
                "site_b_high" if state["world"]["private_dynamics"]["hidden_regime"] == "site_a_high" else "site_a_high"
            )
            connection.execute(
                "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
                (engine.canonical_json(state), engine.canonical_hash(state), "p1-product-trigger"),
            )
            run_id = "p1-product-trigger"
        elif control_id == "ordered_command":
            row = connection.execute("SELECT command_json FROM commands WHERE run_id = ? AND sequence = 1", ("p1-product-trigger",)).fetchone()
            command = json.loads(row["command_json"])
            command["cue"] = "threat"
            command["world_event"] = "threat_nearby"
            command["command_hash"] = engine.canonical_hash({key: value for key, value in command.items() if key != "command_hash"})
            connection.execute(
                "UPDATE commands SET command_json = ?, command_hash = ? WHERE run_id = ? AND sequence = 1",
                (engine.canonical_json(command), command["command_hash"], "p1-product-trigger"),
            )
            run_id = "p1-product-trigger"
        elif control_id == "rehash_stored_action":
            row = connection.execute("SELECT trace_json FROM traces WHERE run_id = ? AND sequence = 1", ("p1-product-trigger",)).fetchone()
            trace = json.loads(row["trace_json"])
            trace["selected_action"] = "withdraw" if trace["selected_action"] != "withdraw" else "rest"
            trace["trace_hash"] = engine.compute_trace_hash(trace)
            connection.execute(
                "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = 1",
                (engine.canonical_json(trace), trace["trace_hash"], "p1-product-trigger"),
            )
            run_id = "p1-product-trigger"
        elif control_id == "claim_provenance":
            row = connection.execute("SELECT initial_state_json FROM runs WHERE run_id = ?", ("p1-pair-a",)).fetchone()
            state = json.loads(row["initial_state_json"])
            claim_events = state["memory"]["claim_events"]
            if claim_events:
                claim_events[0]["evidence_strength"] = 0.25
            else:
                episodic = state["memory"].get("episodic", [])
                if not episodic:
                    connection.close()
                    raise ValueError("claim_provenance_control_has_no_memory_source")
                episodic[0]["source_episode_id"] = "tampered-source-episode"
            connection.execute(
                "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
                (engine.canonical_json(state), engine.canonical_hash(state), "p1-pair-a"),
            )
            run_id = "p1-pair-a"
        else:
            raise ValueError(control_id)
        connection.commit()
        connection.close()
        failed_closed = False
        error = None
        try:
            with SQLiteEventStore(copy_path) as store:
                store.recover_run(run_id)
        except RecoveryError as exc:
            failed_closed = True
            error = str(exc)
        return {"control_id": control_id, "failed_closed": failed_closed, "error": error}


def _replay_report(output: Path, replay_base: Mapping[str, Any]) -> dict[str, Any]:
    db_path = output / "continuity.sqlite3"
    controls = [
        _tamper_control(db_path, control_id)
        for control_id in ("initial_private_world", "ordered_command", "rehash_stored_action", "claim_provenance")
    ]
    value = {
        "recomputed_from_serialized_state_and_commands": bool(replay_base["recomputed"]),
        "stored_action_used_as_input": False,
        "tamper_controls_passed": all(item["failed_closed"] for item in controls),
    }
    return {
        "schema_version": "ego.v2.p1.replay_report.v1",
        **value,
        "fresh_store_readback": deepcopy(dict(replay_base)),
        "tamper_controls": controls,
        "evidence": _evidence(
            producer_function="verify_ego_life_kernel_v2_microworld._replay_report",
            input_artifacts=[
                _input_artifact(db_path, logical_id=GENERATED_DB_LOGICAL_ID)
            ],
            run_id=P1_RUN_ID,
            seed_context_episode_ids={"seeds": list(HISTORY_SEEDS), "pair_id": PAIR_ID},
            aggregation_rule="fresh_store_recompute_and_all_four_independent_tamper_controls_fail_closed",
            value=value,
        ),
    }


def _leakage_report(pair: Mapping[str, Any], input_artifacts: list[Mapping[str, Any]]) -> dict[str, Any]:
    live = {side: scan_policy_projection(pair["canonical"][side].trace["policy_projection"]) for side in ("a", "b")}
    positive: dict[str, Any] = {}
    clean = deepcopy(pair["canonical"]["a"].trace["policy_projection"])
    for control_id, (injected, expected_category, expected_suffix) in LEAKAGE_POSITIVE_CONTROLS.items():
        payload = deepcopy(clean)
        payload["non_memory"]["observation"]["positive_control"] = injected
        scan = scan_policy_projection(payload)
        expected_alias_detected = any(
            offender.get("category") == expected_category
            and str(offender.get("path", "")).endswith(expected_suffix)
            and offender.get("reason") == "forbidden_key_or_alias"
            for offender in scan["offenders"]
        )
        positive[control_id] = {
            **scan,
            "expected_category": expected_category,
            "expected_path_suffix": expected_suffix,
            "expected_alias_detected": expected_alias_detected,
        }
    value = {
        "live_offender_count": sum(len(item["offenders"]) for item in live.values()),
        "positive_controls_fired": all(
            item["expected_alias_detected"] for item in positive.values()
        ),
        "positive_control_count": len(positive),
    }
    return {
        "schema_version": "ego.v2.p1.leakage_report.v1",
        "live_scans": live,
        "positive_controls": positive,
        **value,
        "evidence": _evidence(
            producer_function="verify_ego_life_kernel_v2_microworld._leakage_report",
            input_artifacts=input_artifacts,
            run_id=P1_RUN_ID,
            seed_context_episode_ids={"seeds": list(HISTORY_SEEDS), "pair_id": PAIR_ID},
            aggregation_rule="recursive_live_policy_scan_zero_offenders_and_all_alias_positive_controls_fire",
            value=value,
        ),
    }


def _required_output_keys() -> set[str]:
    keys = {
        f"history:{side}:{event}"
        for side in ("a", "b")
        for event in HISTORY_EVENTS
    }
    keys |= {
        f"{arm}:{side}"
        for arm in (
            "canonical",
            "Memory_OFF",
            "Q_only",
            "from_scratch",
            "Shuffle_Provenance",
            "Shuffle_Provenance_Frozen",
        )
        for side in ("a", "b")
    }
    keys |= {
        f"Freeze_Updates_{mode}:{side}:{step}"
        for mode in ("enabled", "frozen")
        for side in ("a", "b")
        for step in range(1, len(MATCHED_UPDATE_STREAM_EVENTS) + 1)
    }
    keys |= {
        "source_deletion_relevant:a",
        "source_deletion_irrelevant:a",
    }
    return keys


def _collect_actual_step_results(pair: Mapping[str, Any]) -> dict[str, engine.StepResult]:
    outputs: dict[str, engine.StepResult] = {}
    for side in ("a", "b"):
        for event, result in zip(HISTORY_EVENTS, pair["histories"][side]["results"]):
            outputs[f"history:{side}:{event}"] = result
        for arm, source in (
            ("canonical", pair["canonical"]),
            ("Memory_OFF", pair["memory_off"]),
            ("Q_only", pair["q_only"]),
            ("from_scratch", pair["from_scratch"]),
            ("Shuffle_Provenance", pair["shuffled"]),
            ("Shuffle_Provenance_Frozen", pair["shuffled_frozen"]),
        ):
            outputs[f"{arm}:{side}"] = source[side]
        for mode in ("enabled", "frozen"):
            for step, result in enumerate(pair["streams"][side][mode]["results"], start=1):
                outputs[f"Freeze_Updates_{mode}:{side}:{step}"] = result
    outputs["source_deletion_relevant:a"] = pair["deleted_a"]
    outputs["source_deletion_irrelevant:a"] = pair["irrelevant_a"]
    return outputs


def _output_registry(actual_outputs: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    registry: dict[str, Any] = {}
    failures: list[str] = []
    for output_id in sorted(_required_output_keys()):
        result = actual_outputs.get(output_id)
        if not isinstance(result, engine.StepResult):
            failures.append(f"missing_intervention_output:{output_id}")
            continue
        trace = result.trace
        if trace.get("trace_hash") != engine.compute_trace_hash(trace):
            failures.append(f"invalid_intervention_trace_hash:{output_id}")
            continue
        if trace.get("state_after_hash") != engine.state_hash(result.next_state):
            failures.append(f"invalid_intervention_state_hash:{output_id}")
            continue
        registry[output_id] = {
            "producer_function": "ego_life_playground_v0.engine.compute_step",
            "state_before_hash": trace["state_before_hash"],
            "command_hash": trace["command_hash"],
            "trace_hash": trace["trace_hash"],
            "state_after_hash": trace["state_after_hash"],
            "candidate_hash": _canonical_hash(trace["candidates"]),
            "prediction_hash": _canonical_hash(trace["prediction"]),
            "seed": int(trace["seed"]),
            "world_event": trace["world_event"],
            "interventions": deepcopy(trace["interventions"]),
        }
    return registry, failures


def _claim_equation_bound(pair: Mapping[str, Any]) -> bool:
    for side in ("a", "b"):
        trace = pair["canonical"][side].trace
        support = trace["claim_retrieval"]["support_by_action"]
        for candidate in trace["candidates"]:
            raw = float(support.get(candidate["action"], 0.0)) * claims.CLAIM_BIAS_COEFFICIENT
            expected = round(
                max(-claims.CLAIM_BIAS_CLIP, min(claims.CLAIM_BIAS_CLIP, raw)), 6
            )
            if float(candidate["claim_memory_bias"]) != expected:
                return False
    return True


def _bind_frozen_config(
    config: Mapping[str, Any],
    *,
    pair: Mapping[str, Any],
    baseline: Mapping[str, Any],
    ablation: Mapping[str, Any],
) -> dict[str, Any]:
    actual_history_seeds = [pair["histories"][side]["seed"] for side in ("a", "b")]
    actual_history_events = [
        result.trace["world_event"] for result in pair["histories"]["a"]["results"]
    ]
    pair_traces = [
        result.trace
        for output_id, result in _collect_actual_step_results(pair).items()
        if not output_id.startswith("history:")
    ]
    shuffle_traces = [pair["shuffled"][side].trace for side in ("a", "b")]
    recency_ids = {
        item["baseline_id"]
        for item in baseline["invocation_ledger"]
        if item["baseline_id"].startswith("recency_window_")
    }
    model_updates = [
        trace["model_update"]
        for trace in pair_traces
        if trace["model_update"].get("applied") is True
    ]
    checks: dict[str, tuple[bool, Any]] = {
        "config_id": (config.get("config_id") == "ego_v2_p1_memory_pair_v1", P1_RUN_ID),
        "history_seeds": (list(config.get("history_seeds", [])) == actual_history_seeds, actual_history_seeds),
        "history_event_schedule": (list(config.get("history_event_schedule", [])) == actual_history_events, actual_history_events),
        "paired_checkpoint_event": (
            config.get("paired_checkpoint_event") == PAIR_EVENT
            and all(pair["canonical"][side].trace["world_event"] == PAIR_EVENT for side in ("a", "b")),
            [pair["canonical"][side].trace["command_hash"] for side in ("a", "b")],
        ),
        "paired_checkpoint_id": (config.get("paired_checkpoint_id") == PAIR_ID, PAIR_ID),
        "source_deletion_target": (
            config.get("source_deletion_target") == "first_supporting_event_for_selected_site"
            and isinstance(pair.get("source_deletion_target_selection"), Mapping)
            and pair["source_deletion_target_selection"].get("target_rule")
            == "first_supporting_event_for_selected_site"
            and pair["source_deletion_target_selection"].get("status")
            in {"selected", "unavailable_no_supporting_event"}
            and (
                (
                    pair["source_deletion_target_selection"].get("status") == "selected"
                    and pair["deletion_report"]["deleted_event_ids"]
                    == [pair["source_deletion_target_selection"].get("selected_event_id")]
                )
                or (
                    pair["source_deletion_target_selection"].get("status")
                    == "unavailable_no_supporting_event"
                    and pair["source_deletion_target_selection"].get("selected_event_id") is None
                    and pair["deletion_report"]["deleted_event_ids"] == []
                )
            ),
            {
                "target_selection": deepcopy(pair.get("source_deletion_target_selection")),
                "deletion_report": deepcopy(pair.get("deletion_report")),
            },
        ),
        "irrelevant_deletion_target": (
            config.get("irrelevant_deletion_target") == "absent_episode_control"
            and pair["irrelevant_report"]["deleted_event_ids"] == [],
            pair["irrelevant_report"],
        ),
        "provenance_shuffle_seed": (
            config.get("provenance_shuffle_seed") == PROVENANCE_SHUFFLE_SEED
            and all(trace["interventions"]["provenance_shuffle_seed"] == str(PROVENANCE_SHUFFLE_SEED) for trace in shuffle_traces)
            and all(trace["provenance_projection"].get("seed") == PROVENANCE_SHUFFLE_SEED for trace in shuffle_traces),
            [trace["provenance_projection"].get("seed") for trace in shuffle_traces],
        ),
        "pair_policy_seed": (
            config.get("pair_policy_seed") == PAIR_POLICY_SEED
            and all(int(trace["seed"]) == PAIR_POLICY_SEED for trace in pair_traces),
            sorted({int(trace["seed"]) for trace in pair_traces}),
        ),
        "ema_alpha": (
            float(config.get("ema_alpha", -1)) == engine.EMA_ALPHA
            and bool(model_updates)
            and all(update.get("alpha") == engine.EMA_ALPHA for update in model_updates),
            [update.get("alpha") for update in model_updates],
        ),
        "claim_bias_coefficient": (
            float(config.get("claim_bias_coefficient", -1)) == claims.CLAIM_BIAS_COEFFICIENT
            and _claim_equation_bound(pair),
            claims.CLAIM_BIAS_COEFFICIENT,
        ),
        "claim_bias_clip": (
            float(config.get("claim_bias_clip", -1)) == claims.CLAIM_BIAS_CLIP
            and _claim_equation_bound(pair),
            claims.CLAIM_BIAS_CLIP,
        ),
        "recency_windows": (
            list(config.get("recency_windows", [])) == list(RECENCY_WINDOWS)
            and recency_ids == {f"recency_window_{window}" for window in RECENCY_WINDOWS},
            sorted(recency_ids),
        ),
        "equivalence_rule": (
            config.get("equivalence_rule") == "exact_selected_action_match_on_both_paired_checkpoints"
            and len(baseline["candidate_actions"]) == 2,
            {"candidate_actions": baseline["candidate_actions"], "strongest_match_rate": baseline["strongest_match_rate"]},
        ),
        "post_result_retuning": (
            config.get("post_result_retuning") == "forbidden",
            {"retuning_performed": False},
        ),
    }
    return {
        key: {
            "used": bool(matched),
            "observed_hash": _canonical_hash(observed),
            "observed": deepcopy(observed),
        }
        for key, (matched, observed) in checks.items()
    }


def make_minimal_aggregation_fixture() -> dict[str, Any]:
    """Return a deliberately incomplete fixture; missing evidence fails closed."""

    return {
        "frozen_config": None,
        "pair": None,
        "actual_step_results": {},
        "headroom": None,
        "baseline": None,
        "ablation": None,
        "replay": None,
        "leakage": None,
    }


def _both_sides_true(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and set(value) == {"a", "b"}
        and all(item is True for item in value.values())
    )


def _recompute_freeze_contrast_by_side(
    freeze_report: Any,
) -> tuple[dict[str, bool], list[str]]:
    """Recompute downstream contrasts from explicit vectors, never summary booleans."""

    if not isinstance(freeze_report, Mapping):
        return {}, []
    downstream = freeze_report.get("later_downstream_by_side")
    if not isinstance(downstream, Mapping):
        return {}, ["freeze_downstream_vectors_missing"]
    computed: dict[str, bool] = {}
    failures: list[str] = []
    for side in ("a", "b"):
        item = downstream.get(side)
        if not isinstance(item, Mapping):
            failures.append(f"freeze_downstream_vectors_missing:{side}")
            continue
        total_score_contrast = (
            _canonical_json(item.get("enabled_total_score_vector"))
            != _canonical_json(item.get("frozen_total_score_vector"))
        )
        prediction_contrast = (
            _canonical_json(item.get("enabled_prediction_vector"))
            != _canonical_json(item.get("frozen_prediction_vector"))
        )
        selected_action_contrast = (
            item.get("enabled_selected_action")
            != item.get("frozen_selected_action")
        )
        computed[side] = total_score_contrast or prediction_contrast
        checks = {
            "total_score": (
                item.get("total_score_contrast"), total_score_contrast
            ),
            "prediction": (item.get("prediction_contrast"), prediction_contrast),
            "selected_action": (
                item.get("selected_action_contrast"), selected_action_contrast
            ),
        }
        for label, (reported, actual) in checks.items():
            if reported is not actual:
                failures.append(
                    f"freeze_{label}_contrast_report_mismatch:{side}"
                )
    reported_summary = freeze_report.get(
        "later_prediction_or_total_score_contrast_by_side"
    )
    for side, actual in computed.items():
        if (
            not isinstance(reported_summary, Mapping)
            or reported_summary.get(side) is not actual
        ):
            failures.append(f"freeze_downstream_contrast_report_mismatch:{side}")
    return computed, failures


def aggregate_p1_result(reports: Mapping[str, Any]) -> dict[str, Any]:
    blocking: list[str] = []
    config = reports.get("frozen_config")
    if not isinstance(config, Mapping) or set(config) != FROZEN_CONFIG_KEYS:
        blocking.append("missing_frozen_config")
        config = {}
    pair = reports.get("pair")
    baseline = reports.get("baseline")
    ablation = reports.get("ablation")
    headroom = reports.get("headroom")
    replay = reports.get("replay")
    leakage = reports.get("leakage")
    actual_outputs = reports.get("actual_step_results")
    if not isinstance(actual_outputs, Mapping):
        actual_outputs = {}
    registry, output_failures = _output_registry(actual_outputs)
    blocking.extend(output_failures)
    freeze_contrast_by_side, freeze_contrast_failures = (
        _recompute_freeze_contrast_by_side(
            ablation.get("freeze_updates") if isinstance(ablation, Mapping) else None
        )
    )
    blocking.extend(freeze_contrast_failures)

    usage: dict[str, Any] = {}
    if isinstance(pair, Mapping) and isinstance(baseline, Mapping) and isinstance(ablation, Mapping) and config:
        try:
            usage = _bind_frozen_config(config, pair=pair, baseline=baseline, ablation=ablation)
        except (KeyError, TypeError, ValueError) as exc:
            blocking.append(f"frozen_config_binding_error:{type(exc).__name__}")
    for key in FROZEN_CONFIG_KEYS:
        if not usage.get(key, {}).get("used"):
            blocking.append(f"unused_frozen_config:{key}")

    required_effects = {
        "headroom_equal_observation": bool(isinstance(headroom, Mapping) and headroom.get("paired_observation_hash_equal")),
        "headroom_equal_non_memory_policy": bool(isinstance(headroom, Mapping) and headroom.get("paired_non_memory_policy_hash_equal")),
        "headroom_oracle_divergence": bool(isinstance(headroom, Mapping) and headroom.get("oracle_optimal_actions_differ")),
        "typed_transplant_valid": bool(
            isinstance(headroom, Mapping)
            and headroom.get("contrast_type") == "counterfactual_memory_lineage_transplant"
            and headroom.get("reachable_state_claim") is False
            and set(headroom.get("transplants", {})) == {"a", "b"}
            and all(
                transplant.get("target_non_memory_hash_before") == transplant.get("target_non_memory_hash_after")
                and transplant.get("source_memory_hash") == transplant.get("target_memory_after_hash")
                and transplant.get("changed_json_pointers")
                and all(str(pointer).startswith("/memory/") for pointer in transplant.get("changed_json_pointers", []))
                for transplant in headroom.get("transplants", {}).values()
            )
        ),
        "memory_effect_observed": bool(isinstance(headroom, Mapping) and headroom.get("candidate_actions_differ")),
        "memory_off_removed": bool(isinstance(ablation, Mapping) and ablation.get("memory_off", {}).get("paired_difference_removed")),
        "source_deletion_effect": bool(
            isinstance(ablation, Mapping)
            and ablation.get("source_deletion", {}).get("relevant_changed_action")
            and ablation.get("source_deletion", {}).get("irrelevant_inert")
        ),
        "source_deletion_executed": bool(
            isinstance(ablation, Mapping)
            and ablation.get("source_deletion", {}).get("intervention_executed") is True
            and ablation.get("source_deletion", {}).get("target_selection", {}).get("status")
            in {"selected", "unavailable_no_supporting_event"}
            and {
                "source_deletion_relevant:a",
                "source_deletion_irrelevant:a",
            }
            <= set(registry)
        ),
        "shuffle_effect": bool(isinstance(ablation, Mapping) and ablation.get("shuffle_provenance", {}).get("support_effect_changed")),
        "shuffle_invariance": bool(
            isinstance(ablation, Mapping)
            and ablation.get("shuffle_provenance", {}).get("persisted_memory_unchanged_before_current_write")
            and ablation.get("shuffle_provenance", {}).get("frozen_projection_memory_exact")
            and ablation.get("shuffle_provenance", {}).get("unaffected_fields_preserved")
        ),
        "freeze_preservation": bool(
            isinstance(ablation, Mapping)
            and ablation.get("freeze_updates", {}).get("matched_streams_present")
            and ablation.get("freeze_updates", {}).get("model_bytes_preserved")
            and ablation.get("freeze_updates", {}).get("claim_and_event_bytes_preserved")
            and _both_sides_true(
                ablation.get("freeze_updates", {}).get("step1_matched_by_side")
            )
            and _both_sides_true(
                ablation.get("freeze_updates", {}).get(
                    "enabled_step1_update_applied_by_side"
                )
            )
            and _both_sides_true(
                ablation.get("freeze_updates", {}).get(
                    "step2_observation_equal_by_side"
                )
            )
        ),
        "replay_valid": bool(
            isinstance(replay, Mapping)
            and replay.get("recomputed_from_serialized_state_and_commands")
            and replay.get("tamper_controls_passed")
            and {"p1-history-a", "p1-history-b", "p1-pair-a", "p1-pair-b"}
            <= set(replay.get("fresh_store_readback", {}).get("recovered_runs", {}))
        ),
        "leakage_valid": bool(
            isinstance(leakage, Mapping)
            and leakage.get("live_offender_count") == 0
            and leakage.get("positive_controls_fired") is True
        ),
    }
    implementation_control_ids = {
        "headroom_equal_observation",
        "headroom_equal_non_memory_policy",
        "headroom_oracle_divergence",
        "typed_transplant_valid",
        "source_deletion_executed",
        "shuffle_invariance",
        "freeze_preservation",
        "replay_valid",
        "leakage_valid",
    }
    blocking.extend(
        f"required_effect_false:{key}"
        for key in sorted(implementation_control_ids)
        if not required_effects.get(key)
    )
    strongest_rate = float(baseline.get("strongest_match_rate", 0.0)) if isinstance(baseline, Mapping) else 0.0
    claim_blockers: list[str] = []
    if not required_effects["memory_effect_observed"]:
        claim_blockers.append("memory_conditioned_effect_not_observed")
    elif not required_effects["memory_off_removed"]:
        claim_blockers.append("memory_off_did_not_remove_paired_difference")
    if not required_effects["source_deletion_effect"]:
        source_status = (
            ablation.get("source_deletion", {}).get("target_selection", {}).get("status")
            if isinstance(ablation, Mapping)
            else None
        )
        claim_blockers.append(
            "source_deletion_target_unavailable"
            if source_status == "unavailable_no_supporting_event"
            else "source_deletion_effect_not_observed"
        )
    if not required_effects["shuffle_effect"]:
        claim_blockers.append("shuffle_provenance_effect_not_observed")
    if strongest_rate >= 1.0:
        claim_blockers.append("control_baseline_equivalent")
    for side in ("a", "b"):
        if not isinstance(freeze_contrast_by_side, Mapping) or freeze_contrast_by_side.get(side) is not True:
            claim_blockers.append(f"freeze_downstream_contrast_inert_side_{side}")
    if blocking:
        verdict = (
            "evidence_invalid__unused_frozen_input"
            if any(item == "missing_frozen_config" or item.startswith("unused_frozen_config:") for item in blocking)
            else "evidence_invalid__required_control_failed"
        )
        claim_status = "invalid"
    elif not required_effects["memory_effect_observed"]:
        verdict = "memory_conditioned_effect_not_observed_in_frozen_pair"
        claim_status = "bounded_negative_for_memory_conditioned_effect"
    elif strongest_rate >= 1.0:
        verdict = "memory_conditioned_effect_observed_but_control_equivalent"
        claim_status = "bounded_negative_for_mechanism_non_equivalence"
    else:
        verdict = "bounded_counterfactual_memory_transplant_effect_observed"
        claim_status = "bounded_counterfactual_checkpoint_only"
    return {
        "schema_version": "ego.v2.p1.result.v2",
        "verdict": verdict,
        "claim_status": claim_status,
        "blocking_failures": sorted(set(blocking)),
        "claim_blockers": sorted(set(claim_blockers)),
        "narrower_result": {
            "freeze_downstream_contrast_by_side": deepcopy(
                dict(freeze_contrast_by_side)
                if isinstance(freeze_contrast_by_side, Mapping)
                else {}
            ),
            "interpretation": "matched downstream final-score/prediction contrast is side-specific",
        },
        "strongest_control_match_rate": strongest_rate,
        "computed_effects": required_effects,
        "frozen_config": deepcopy(dict(config)),
        "frozen_config_usage": usage,
        "intervention_output_registry": registry,
        "claim_ceiling": CLAIM_CEILING,
        "switches": deepcopy(SWITCHES),
        "evidence": _evidence(
            producer_function="verify_ego_life_kernel_v2_microworld.aggregate_p1_result",
            input_artifacts=["callable_subreports_and_actual_step_results"],
            run_id=P1_RUN_ID,
            seed_context_episode_ids={"seeds": list(config.get("history_seeds", [])), "pair_ids": [config.get("paired_checkpoint_id")] if config else []},
            aggregation_rule="validate_actual_step_outputs_bind_every_frozen_config_then_require_headroom_interventions_replay_leakage_and_apply_exact_control_equivalence_rule",
            value={"verdict": verdict, "blocking_failures": sorted(set(blocking)), "claim_blockers": sorted(set(claim_blockers))},
        ),
    }


def run_p1_verification(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    learning_path = output / "learning_report.json"
    if learning_path.exists():
        learning_path.unlink()

    pair = _paired_runs()
    trigger, replay_base = _create_product_db(output, pair)
    _write_json(output / "product_trigger_receipt.json", trigger)
    input_artifacts = [
        _input_artifact(
            output / "continuity.sqlite3", logical_id=GENERATED_DB_LOGICAL_ID
        ),
        _input_artifact(
            output / "trace.jsonl", logical_id=GENERATED_TRACE_LOGICAL_ID
        ),
        _input_artifact(TASK_SCOPE_PATH, logical_id=TASK_SCOPE_LOGICAL_ID),
    ]

    oracle_a = microworld.oracle_evidence_record(pair["states"]["a"]["world"])
    oracle_b = microworld.oracle_evidence_record(pair["states"]["b"]["world"])
    headroom_value = {
        "paired_observation_hash_equal": pair["canonical"]["a"].trace["observation_hash"] == pair["canonical"]["b"].trace["observation_hash"],
        "paired_non_memory_policy_hash_equal": pair["canonical"]["a"].trace["policy_non_memory_projection_hash"] == pair["canonical"]["b"].trace["policy_non_memory_projection_hash"],
        "oracle_optimal_actions_differ": oracle_a["correct_action"] != oracle_b["correct_action"],
        "candidate_actions_differ": pair["canonical"]["a"].trace["selected_action"] != pair["canonical"]["b"].trace["selected_action"],
    }
    headroom = {
        "schema_version": "ego.v2.p1.headroom_report.v2",
        "pair_id": PAIR_ID,
        "contrast_type": "counterfactual_memory_lineage_transplant",
        "reachable_state_claim": False,
        **headroom_value,
        "observation_hashes": {side: pair["canonical"][side].trace["observation_hash"] for side in ("a", "b")},
        "non_memory_policy_hashes": {side: pair["canonical"][side].trace["policy_non_memory_projection_hash"] for side in ("a", "b")},
        "oracle_records": {"a": oracle_a, "b": oracle_b},
        "transplants": deepcopy(pair["transplants"]),
        "source_history_runs": {
            side: {
                "run_id": pair["histories"][side]["run_id"],
                "seed": pair["histories"][side]["seed"],
                "initial_state_hash": engine.state_hash(pair["histories"][side]["initial_state"]),
                "terminal_state_hash": engine.state_hash(pair["histories"][side]["state"]),
                "terminal_memory_hash": engine.canonical_hash(pair["histories"][side]["state"]["memory"]),
                "command_hashes": [command["command_hash"] for command in pair["histories"][side]["commands"]],
                "trace_hashes": [result.trace["trace_hash"] for result in pair["histories"][side]["results"]],
                "sqlite_run_id": f"p1-history-{side}",
                "sqlite_recovery": deepcopy(
                    replay_base["recovered_runs"][f"p1-history-{side}"]
                ),
            }
            for side in ("a", "b")
        },
        "evidence": _evidence(
            producer_function="verify_ego_life_kernel_v2_microworld.run_p1_verification.headroom",
            input_artifacts=input_artifacts,
            run_id=P1_RUN_ID,
            seed_context_episode_ids={"seeds": list(HISTORY_SEEDS), "pair_id": PAIR_ID},
            aggregation_rule="exact_canonical_byte_hash_equality_and_evidence_only_oracle_divergence",
            value={
                **headroom_value,
                "contrast_type": "counterfactual_memory_lineage_transplant",
                "reachable_state_claim": False,
                "transplant_hashes": {
                    side: _canonical_hash(pair["transplants"][side]) for side in ("a", "b")
                },
            },
        ),
    }
    baseline = _baseline_report(pair, input_artifacts)
    ablation = _ablation_report(pair, input_artifacts)
    replay = _replay_report(output, replay_base)
    leakage = _leakage_report(pair, input_artifacts)

    aggregate_inputs = {
        "frozen_config": _load_frozen_config(),
        "pair": pair,
        "actual_step_results": _collect_actual_step_results(pair),
        "headroom": headroom,
        "baseline": baseline,
        "ablation": ablation,
        "replay": replay,
        "leakage": leakage,
    }
    result = aggregate_p1_result(aggregate_inputs)
    result["input_artifacts"] = input_artifacts
    result["invocation_ledger"] = (
        [
            {
                "output_id": output_id,
                **deepcopy(record),
                "invoked": True,
            }
            for output_id, record in sorted(result["intervention_output_registry"].items())
        ]
        + baseline["invocation_ledger"]
        + ablation["invocation_ledger"]
    )

    implementation_failures = list(result["blocking_failures"])
    claim_blockers = list(result["claim_blockers"])
    failure_manifest = {
        "schema_version": "ego.v2.p1.failure_manifest.v2",
        "implementation_failures": sorted(set(implementation_failures)),
        "claim_blockers": claim_blockers,
        "status": "implementation_controls_passed_with_bounded_claim_blocker" if not implementation_failures and claim_blockers else ("pass" if not implementation_failures else "fail"),
        "evidence": _evidence(
            producer_function="verify_ego_life_kernel_v2_microworld.run_p1_verification.failure_manifest",
            input_artifacts=input_artifacts,
            run_id=P1_RUN_ID,
            seed_context_episode_ids={"seeds": list(HISTORY_SEEDS), "pair_id": PAIR_ID},
            aggregation_rule="union_of_computed_false_requirements_plus_control_equivalence_claim_blockers",
            value={"implementation_failures": sorted(set(implementation_failures)), "claim_blockers": claim_blockers},
        ),
    }
    collision = {
        "schema_version": "ego.v2.p1.collision_record.v1",
        "candidate_effect_observed": headroom["candidate_actions_differ"],
        "strongest_cheap_match": baseline["strongest_matching_control"],
        "strongest_match_rate": baseline["strongest_match_rate"],
        "disposition": "retain_product_loop_and_downgrade_mechanism_claim_to_control_equivalence" if baseline["control_equivalent"] else "bounded_checkpoint_effect_only",
        "evidence": _evidence(
            producer_function="verify_ego_life_kernel_v2_microworld.run_p1_verification.collision",
            input_artifacts=input_artifacts,
            run_id=P1_RUN_ID,
            seed_context_episode_ids={"seeds": list(HISTORY_SEEDS), "pair_id": PAIR_ID},
            aggregation_rule="candidate_effect_collided_with_maximum_equal_public_history_control_match",
            value={"candidate_effect": headroom["candidate_actions_differ"], "strongest_match_rate": baseline["strongest_match_rate"]},
        ),
    }

    for name, payload in (
        ("headroom_report.json", headroom),
        ("collision_record.json", collision),
        ("baseline_comparison.json", baseline),
        ("ablation_report.json", ablation),
        ("replay_report.json", replay),
        ("leakage_report.json", leakage),
        ("failure_manifest.json", failure_manifest),
        ("result.json", result),
    ):
        _write_json(output / name, payload)
    (output / "claim_ceiling.txt").write_text(CLAIM_CEILING + "\n", encoding="utf-8", newline="\n")
    return result


# ---------------------------------------------------------------------------
# P2 bounded update / held-out comparison producer.


def _load_frozen_p2_config() -> dict[str, Any]:
    payload = yaml.safe_load(TASK_SCOPE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("mutation scope must be a mapping")
    config = payload.get("frozen_p2_evaluation_config")
    if not isinstance(config, Mapping) or set(config) != P2_FROZEN_CONFIG_KEYS:
        raise ValueError("frozen P2 config schema mismatch")
    frozen = deepcopy(dict(config))
    if frozen["config_id"] != P2_FROZEN_CONFIG_ID:
        raise ValueError("frozen P2 config id mismatch")
    if _canonical_hash(frozen) != P2_FROZEN_CONFIG_CANONICAL_SHA256:
        raise ValueError("frozen P2 config canonical hash mismatch")
    if float(frozen["update_alpha"]) != engine.EMA_ALPHA:
        raise ValueError("frozen P2 alpha does not bind the canonical reducer")
    if int(frozen["episode_span_ticks"]) != engine.EPISODE_SPAN_TICKS:
        raise ValueError("frozen P2 episode span mismatch")
    if int(frozen["consolidation_threshold"]) != engine.CONSOLIDATION_THRESHOLD:
        raise ValueError("frozen P2 consolidation threshold mismatch")
    if frozen["post_result_retuning"] != "forbidden":
        raise ValueError("post-result retuning must remain forbidden")
    if frozen["heldout_update_mode"] != "frozen":
        raise ValueError("heldout update mode must remain frozen")
    if frozen["transfer_matrix"] != "full_cross_product__each_train_replication_x_each_heldout_context":
        raise ValueError("heldout transfer matrix must remain the full cross product")
    if frozen["candidate_ablation"] != "from_scratch_empty_model_and_memory":
        raise ValueError("candidate ablation is not the frozen from-scratch arm")
    return frozen


def build_p2_invocation_plan(config: Mapping[str, Any]) -> dict[str, Any]:
    train = [
        {
            "world_seed": int(seed),
            "episode_index": episode_index,
            "checkpoint": int(config["learning_checkpoints"][episode_index]),
            "schedule": list(schedule),
        }
        for seed in config["train_world_seeds"]
        for episode_index, schedule in enumerate(config["train_episode_schedules"])
    ]
    heldout = [
        {
            "train_world_seed": int(seed),
            "context_id": str(context["context_id"]),
            "world_seed": int(context["world_seed"]),
            "layout_id": str(context["layout_id"]),
            "event_schedule_id": str(context["event_schedule_id"]),
        }
        for seed in config["train_world_seeds"]
        for context in config["heldout_contexts"]
    ]
    return {
        "schema_version": "ego.v2.p2.invocation_plan.v1",
        "train_episodes": train,
        "heldout_candidate_arms": heldout,
        "counterfactual_arms": [
            {**deepcopy(arm), "counterfactual": str(counterfactual)}
            for counterfactual in config["counterfactuals"]
            for arm in heldout
        ],
        "independent_controls": list(config["independent_controls"]),
        "learning_checkpoints": list(config["learning_checkpoints"]),
        "heldout_layout_ids": list(config["heldout_layout_ids"]),
        "heldout_event_schedule_ids": sorted(config["heldout_event_schedules"]),
        "candidate_ablation": str(config["candidate_ablation"]),
        "frozen_config_projection": deepcopy(dict(config)),
    }


def bind_p2_frozen_config(
    config: Mapping[str, Any], ledger: Mapping[str, Any]
) -> dict[str, Any]:
    failures: list[str] = []
    leaf_evidence = ledger.get("leaf_evidence")
    if not isinstance(leaf_evidence, Mapping):
        leaf_evidence = {}
        failures.append("actual_usage_ledger_leaf_evidence_missing")
    if set(config) != P2_FROZEN_CONFIG_KEYS:
        failures.append("frozen_config_schema_mismatch")
    if set(leaf_evidence) != P2_FROZEN_CONFIG_KEYS:
        failures.append("actual_usage_ledger_leaf_set_mismatch")
    for key in sorted(P2_FROZEN_CONFIG_KEYS):
        item = leaf_evidence.get(key)
        if (
            not isinstance(item, Mapping)
            or type(item.get("evidence_count")) is not int
            or int(item.get("evidence_count", 0)) <= 0
            or item.get("observed_value") != config.get(key)
            or not item.get("source_record_hash")
            or not item.get("producer_function")
        ):
            failures.append(f"unused_or_mismatched_frozen_leaf:{key}")
    expected_hash = _canonical_hash(dict(config))
    if expected_hash != P2_FROZEN_CONFIG_CANONICAL_SHA256:
        failures.append("frozen_config_canonical_hash_mismatch")
    if ledger.get("config_hash_before_execution") != expected_hash:
        failures.append("execution_config_hash_before_mismatch")
    if ledger.get("config_hash_after_evidence") != expected_hash:
        failures.append("execution_config_hash_after_mismatch")
    retuning_control = leaf_evidence.get("post_result_retuning", {}).get(
        "semantic_control", {}
    )
    if (
        not isinstance(retuning_control, Mapping)
        or retuning_control.get("retuning_performed") is not False
    ):
        failures.append("post_result_retuning_semantic_control_failed")
    return {
        "all_frozen_inputs_used": not failures,
        "blocking_failures": sorted(set(failures)),
        "expected_config_hash": expected_hash,
        "actual_usage_ledger_hash": _canonical_hash(ledger),
        "actual_usage_ledger": deepcopy(dict(ledger)),
    }


def _p2_unique(values: Iterable[Any]) -> list[Any]:
    observed: list[Any] = []
    hashes: set[str] = set()
    for value in values:
        digest = _canonical_hash(value)
        if digest not in hashes:
            hashes.add(digest)
            observed.append(deepcopy(value))
    return observed


def _p2_single_observed(values: Iterable[Any]) -> Any:
    unique = _p2_unique(values)
    if len(unique) == 1:
        return unique[0]
    return {"conflicting_or_missing_observed_values": unique}


def _p2_executed_episode_schedule(run: Mapping[str, Any]) -> tuple[list[list[str]], list[int]]:
    schedules: list[list[str]] = []
    checkpoints: list[int] = []
    current_episode: int | None = None
    for command, result in zip(run["commands"], run["results"]):
        episode_index = int(result.trace["episode_index"])
        while len(schedules) <= episode_index:
            schedules.append([])
        schedules[episode_index].append(str(command["world_event"]))
        if current_episode is not None and episode_index != current_episode:
            checkpoints.append(int(result.trace["global_tick"]) - 1)
        current_episode = episode_index
    if run["results"]:
        checkpoints.append(int(run["results"][-1].trace["global_tick"]))
    return schedules, checkpoints


def _p2_usage_leaf(observed_value: Any, source_records: Any, source_kind: str) -> dict[str, Any]:
    if isinstance(source_records, (list, tuple, Mapping)):
        evidence_count = len(source_records)
    else:
        evidence_count = 1
    return {
        "producer_function": "verify_ego_life_kernel_v2_microworld.build_p2_actual_usage_ledger",
        "source_kind": source_kind,
        "observed_value": deepcopy(observed_value),
        "evidence_count": int(evidence_count),
        "source_record_hash": _canonical_hash(source_records),
    }


def build_p2_actual_usage_ledger(
    *,
    runs: Mapping[str, Any],
    train_curves: Mapping[str, Mapping[str, Any]],
    train_summaries: Mapping[str, Mapping[str, Any]],
    baseline_rows: Iterable[Mapping[str, Any]],
    counterfactual_rows: Iterable[Mapping[str, Any]],
    threshold_evaluations: Mapping[str, Mapping[str, Any]],
    config_hash_before_execution: str,
    config_hash_after_evidence: str,
) -> dict[str, Any]:
    """Reconstruct frozen-leaf use from executed outputs, never a declared plan."""

    train_runs = list(runs["train_runs"].values())
    candidate_runs = list(runs["candidate_runs"].values())
    scratch_runs = list(runs["from_scratch_runs"].values())
    counterfactual_runs = list(runs["counterfactual_runs"].values())
    train_execution: list[dict[str, Any]] = []
    for run in train_runs:
        schedules, checkpoints = _p2_executed_episode_schedule(run)
        train_execution.append(
            {
                "verification_config_id": str(
                    run.get("execution_context", {}).get("verification_config_id", "")
                ),
                "world_seed": int(run["world_seed"]),
                "layout_id": str(run["layout_id"]),
                "policy_seed": int(run["meta"]["seed"]),
                "episode_span_ticks": int(run["meta"]["episode_span_ticks"]),
                "schedules": schedules,
                "checkpoints": checkpoints,
                "command_hashes": [str(command["command_hash"]) for command in run["commands"]],
            }
        )

    heldout_execution: list[dict[str, Any]] = []
    schedule_records: dict[str, list[list[str]]] = {}
    context_records: dict[str, list[dict[str, Any]]] = {}
    for run in candidate_runs:
        execution_context = dict(run.get("execution_context", {}))
        schedule = [str(command["world_event"]) for command in run["commands"]]
        context_id = str(execution_context.get("context_id", ""))
        schedule_id = str(execution_context.get("event_schedule_id", ""))
        record = {
            "train_world_seed": execution_context.get("train_world_seed"),
            "context_id": context_id,
            "world_seed": int(run["world_seed"]),
            "layout_id": str(run["layout_id"]),
            "event_schedule_id": schedule_id,
            "schedule": schedule,
            "update_modes": [
                str(command["interventions"]["update_mode"]) for command in run["commands"]
            ],
        }
        heldout_execution.append(record)
        schedule_records.setdefault(schedule_id, []).append(schedule)
        context_records.setdefault(context_id, []).append(
            {
                "context_id": context_id,
                "world_seed": int(run["world_seed"]),
                "layout_id": str(run["layout_id"]),
                "event_schedule_id": schedule_id,
            }
        )
    actual_contexts = [
        _p2_single_observed(records) for records in context_records.values()
    ]
    actual_schedules = {
        schedule_id: _p2_single_observed(records)
        for schedule_id, records in schedule_records.items()
    }
    train_seed_values = [row["world_seed"] for row in train_execution]
    context_ids = [str(row["context_id"]) for row in actual_contexts]
    actual_pairs = {
        (int(row["train_world_seed"]), str(row["context_id"]))
        for row in heldout_execution
        if type(row.get("train_world_seed")) is int
    }
    expected_pairs = {
        (int(seed), context_id) for seed in train_seed_values for context_id in context_ids
    }
    transfer_matrix = (
        "full_cross_product__each_train_replication_x_each_heldout_context"
        if actual_pairs == expected_pairs and len(actual_pairs) == len(heldout_execution)
        else "incomplete_or_duplicate_executed_cross_product"
    )

    scratch_checks = [
        {
            "run_id": str(run["run_id"]),
            "initial_model_empty": run["initial_state"]["model"] == {},
            "initial_memory_empty": run["initial_state"]["memory"] == _p2_empty_memory(),
            "terminal_model_matches_initial": engine.canonical_hash(run["state"]["model"])
            == engine.canonical_hash(run["initial_state"]["model"]),
            "terminal_memory_matches_initial": engine.canonical_hash(run["state"]["memory"])
            == engine.canonical_hash(run["initial_state"]["memory"]),
        }
        for run in scratch_runs
    ]
    candidate_ablation = (
        "from_scratch_empty_model_and_memory"
        if scratch_checks
        and all(
            row["initial_model_empty"]
            and row["initial_memory_empty"]
            and row["terminal_model_matches_initial"]
            and row["terminal_memory_matches_initial"]
            for row in scratch_checks
        )
        else "scratch_adaptive_bytes_not_empty_or_not_frozen"
    )

    cf_reports = list(runs["counterfactual_reports"].values())
    counterfactual_names = _p2_unique(
        str(report.get("counterfactual", "")) for report in cf_reports
    )
    source_indices: list[int] = []
    irrelevant_ids: list[str] = []
    source_deletion_evidence: list[dict[str, Any]] = []
    irrelevant_deletion_evidence: list[dict[str, Any]] = []
    for report in cf_reports:
        execution_context = report.get("execution_context", {})
        if report.get("counterfactual") == "source_memory_deletion":
            train_seed = int(execution_context["train_world_seed"])
            source_id = str(report["deletion"]["source_episode_id"])
            train_run = runs["train_runs"][train_seed]
            matches = [
                index
                for index in range(len(train_run["episode_histories"]))
                if engine.episode_id_for(str(train_run["run_id"]), index) == source_id
            ]
            source_indices.extend(matches)
            source_deletion_evidence.append(
                {
                    "execution_context": deepcopy(dict(execution_context)),
                    "source_episode_id": source_id,
                    "derived_episode_indices": matches,
                    "episodic_records_deleted": int(
                        report["deletion"]["episodic_records_deleted"]
                    ),
                }
            )
            irrelevant_id = str(report["irrelevant_deletion"]["source_episode_id"])
            irrelevant_ids.append(irrelevant_id)
            irrelevant_deletion_evidence.append(
                {
                    "execution_context": deepcopy(dict(execution_context)),
                    "source_episode_id": irrelevant_id,
                    "state_bytes_equal": bool(report["irrelevant_state_bytes_equal"]),
                }
            )

    baseline_list = [deepcopy(dict(row)) for row in baseline_rows]
    control_ids = _p2_unique(str(row.get("control_id", "")) for row in baseline_list)
    all_adaptive_runs = train_runs + candidate_runs + scratch_runs + counterfactual_runs
    policy_seed_records = [
        {
            "run_id": str(run["run_id"]),
            "run_metadata_seed": int(run["meta"]["seed"]),
            "projected_policy_tie_seeds": _p2_unique(
                int(result.trace["policy_projection"]["non_memory"]["policy_tie_seed"])
                for result in run["results"]
            ),
        }
        for run in all_adaptive_runs
    ]
    policy_seeds = [
        row["run_metadata_seed"]
        if row["projected_policy_tie_seeds"] == [row["run_metadata_seed"]]
        else {
            "run_metadata_seed": row["run_metadata_seed"],
            "projected_policy_tie_seeds": row["projected_policy_tie_seeds"],
        }
        for row in policy_seed_records
    ]
    alpha_records = [
        float(result.trace["model_update"]["alpha"])
        for run in train_runs
        for result in run["results"]
    ]
    consolidation_reference_counts = [
        len(result.trace["memory_update"]["consolidation_refs"])
        for run in train_runs
        for result in run["results"]
        if result.trace["memory_update"]["consolidation_applied"]
    ]
    heldout_update_modes = [
        mode for row in heldout_execution for mode in row["update_modes"]
    ]
    learning_metric_ids = [
        str(curve.get("learning_curve_metric_id", "")) for curve in train_curves.values()
    ]
    task_metric_ids = [
        str(summary.get("task_outcome_metric_id", "")) for summary in train_summaries.values()
    ]
    site_metric_ids = [
        str(summary.get("site_outcome_metric_id", "")) for summary in train_summaries.values()
    ]
    equivalence_ids = [
        str(row.get("equivalence_rule_id", "")) for row in baseline_list
    ]
    counterfactual_list = [deepcopy(dict(row)) for row in counterfactual_rows]
    executed_config_ids = [row["verification_config_id"] for row in train_execution]
    retuning_control = {
        "producer_function": "verify_ego_life_kernel_v2_microworld.build_p2_actual_usage_ledger",
        "config_hash_before_execution": config_hash_before_execution,
        "config_hash_after_evidence": config_hash_after_evidence,
        "retuning_performed": config_hash_before_execution != config_hash_after_evidence,
    }

    leaf_evidence = {
        "config_id": _p2_usage_leaf(
            _p2_single_observed(executed_config_ids),
            train_execution,
            "executed_train_run_context_metadata",
        ),
        "policy_tie_seed": _p2_usage_leaf(
            _p2_single_observed(policy_seeds),
            policy_seed_records,
            "run_metadata_seed_equal_to_every_executed_policy_projection_seed",
        ),
        "update_alpha": _p2_usage_leaf(_p2_single_observed(alpha_records), alpha_records, "executed_model_update_trace"),
        "episode_span_ticks": _p2_usage_leaf(
            _p2_single_observed(row["episode_span_ticks"] for row in train_execution),
            train_execution,
            "train_run_metadata_episode_span",
        ),
        "consolidation_threshold": _p2_usage_leaf(
            min(consolidation_reference_counts) if consolidation_reference_counts else None,
            consolidation_reference_counts,
            "applied_consolidation_trace_reference_count",
        ),
        "train_world_seeds": _p2_usage_leaf(train_seed_values, train_execution, "executed_train_run_world_seed"),
        "train_layout_id": _p2_usage_leaf(
            _p2_single_observed(row["layout_id"] for row in train_execution),
            train_execution,
            "executed_train_layout",
        ),
        "train_episode_schedules": _p2_usage_leaf(
            _p2_single_observed(row["schedules"] for row in train_execution),
            train_execution,
            "ordered_train_command_world_events_grouped_by_trace_episode",
        ),
        "learning_checkpoints": _p2_usage_leaf(
            _p2_single_observed(row["checkpoints"] for row in train_execution),
            train_execution,
            "executed_trace_global_tick_episode_boundaries",
        ),
        "heldout_layout_ids": _p2_usage_leaf(
            _p2_unique(row["layout_id"] for row in actual_contexts),
            actual_contexts,
            "executed_candidate_run_layouts",
        ),
        "heldout_event_schedules": _p2_usage_leaf(
            actual_schedules, heldout_execution, "executed_candidate_command_world_events"
        ),
        "heldout_contexts": _p2_usage_leaf(
            actual_contexts, heldout_execution, "executed_candidate_run_context_metadata"
        ),
        "transfer_matrix": _p2_usage_leaf(
            transfer_matrix, heldout_execution, "executed_train_seed_by_context_pairs"
        ),
        "heldout_update_mode": _p2_usage_leaf(
            _p2_single_observed(heldout_update_modes),
            heldout_update_modes,
            "executed_candidate_command_interventions",
        ),
        "minimum_matched_context_action_slots": _p2_usage_leaf(
            threshold_evaluations["minimum_matched_context_action_slots"]["threshold"],
            threshold_evaluations["minimum_matched_context_action_slots"],
            "computed_curve_threshold_evaluation",
        ),
        "minimum_site_visits_per_context_for_directional_claim": _p2_usage_leaf(
            threshold_evaluations["minimum_site_visits_per_context_for_directional_claim"]["threshold"],
            threshold_evaluations["minimum_site_visits_per_context_for_directional_claim"],
            "computed_heldout_coverage_threshold_evaluation",
        ),
        "source_deletion_episode_index": _p2_usage_leaf(
            _p2_single_observed(source_indices),
            source_deletion_evidence,
            "counterfactual_report_deleted_source_episode_id",
        ),
        "irrelevant_source_episode_id": _p2_usage_leaf(
            _p2_single_observed(irrelevant_ids),
            irrelevant_deletion_evidence,
            "counterfactual_report_irrelevant_source_id",
        ),
        "counterfactuals": _p2_usage_leaf(
            counterfactual_names, counterfactual_list, "executed_counterfactual_reports_and_rows"
        ),
        "independent_controls": _p2_usage_leaf(
            control_ids, baseline_list, "executed_independent_baseline_rows"
        ),
        "candidate_ablation": _p2_usage_leaf(
            candidate_ablation, scratch_checks, "scratch_initial_and_terminal_adaptive_byte_checks"
        ),
        "learning_curve_metric": _p2_usage_leaf(
            _p2_single_observed(learning_metric_ids),
            list(train_curves.values()),
            "callable_episode_curve_outputs",
        ),
        "task_outcome_metric": _p2_usage_leaf(
            _p2_single_observed(task_metric_ids),
            list(train_summaries.values()),
            "callable_run_summary_outputs",
        ),
        "site_outcome_metric": _p2_usage_leaf(
            _p2_single_observed(site_metric_ids),
            list(train_summaries.values()),
            "callable_run_summary_outputs",
        ),
        "equivalence_rule": _p2_usage_leaf(
            _p2_single_observed(equivalence_ids),
            baseline_list,
            "computed_baseline_equivalence_rows",
        ),
        "post_result_retuning": {
            **_p2_usage_leaf(
            "forbidden"
            if retuning_control["retuning_performed"] is False
            else "config_hash_changed_after_execution",
            retuning_control,
            "pre_execution_and_post_evidence_config_hash_comparison",
            ),
            "semantic_control": retuning_control,
        },
    }
    return {
        "schema_version": "ego.v2.p2.actual_usage_ledger.v2",
        "config_hash_before_execution": config_hash_before_execution,
        "config_hash_after_evidence": config_hash_after_evidence,
        "leaf_evidence": leaf_evidence,
        "executed_train": train_execution,
        "executed_heldout": heldout_execution,
        "scratch_byte_checks": scratch_checks,
        "executed_counterfactual_arm_count": len(counterfactual_list),
        "executed_baseline_row_count": len(baseline_list),
        "threshold_evaluations": deepcopy(dict(threshold_evaluations)),
    }


def _p2_empty_memory() -> dict[str, Any]:
    return {"episodic": [], "consolidated": [], **claims.empty_claim_memory()}


def _p2_nonadaptive_projection(state: Mapping[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(value) for key, value in state.items() if key not in {"model", "memory"}}


def _p2_transplant(
    *,
    run_id: str,
    world_seed: int,
    layout_id: str,
    model: Mapping[str, Any],
    memory: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    fresh = engine.initial_state(run_id=run_id, seed=world_seed, layout_id=layout_id)
    state = deepcopy(fresh)
    state["model"] = deepcopy(dict(model))
    state["memory"] = deepcopy(dict(memory))
    # Validation is deliberately reached through the one reducer at the first
    # command.  This report proves only the exact typed counterfactual boundary.
    return state, {
        "schema_version": "ego.v2.p2.adaptive_state_transplant.v1",
        "reachable_state_claim": False,
        "copied_json_pointers": ["/memory", "/model"],
        "nonadaptive_projection_equal": _p2_nonadaptive_projection(fresh)
        == _p2_nonadaptive_projection(state),
        "fresh_model_hash": engine.canonical_hash(fresh["model"]),
        "fresh_memory_hash": engine.canonical_hash(fresh["memory"]),
        "transplanted_model_hash": engine.canonical_hash(state["model"]),
        "transplanted_memory_hash": engine.canonical_hash(state["memory"]),
    }


def _p2_run_candidate(
    *,
    run_id: str,
    world_seed: int,
    policy_seed: int,
    layout_id: str,
    schedules: Iterable[Iterable[str]],
    base_state: Mapping[str, Any] | None = None,
    update_mode: str = "enabled",
    memory_mode: str = "canonical",
    consolidation_mode: str = "canonical",
    store: SQLiteEventStore | None = None,
) -> dict[str, Any]:
    meta = engine.make_run_metadata(run_id, policy_seed)
    state = (
        engine.initial_state(run_id=run_id, seed=world_seed, layout_id=layout_id)
        if base_state is None
        else deepcopy(dict(base_state))
    )
    initial = deepcopy(state)
    if store is not None:
        store.create_run(meta, state)
    commands: list[dict[str, Any]] = []
    results: list[engine.StepResult] = []
    public_history: list[dict[str, Any]] = []
    episode_histories: list[list[dict[str, Any]]] = []
    flat_schedules = [list(schedule) for schedule in schedules]
    for episode_index, schedule in enumerate(flat_schedules):
        episode_records: list[dict[str, Any]] = []
        for tick_index, event in enumerate(schedule):
            interventions = dict(
                engine.DEFAULT_INTERVENTIONS,
                update_mode=update_mode,
                memory_mode=memory_mode,
                consolidation_mode=consolidation_mode,
            )
            command = engine.make_command(
                sequence=int(state["clock"]["global_tick"]) + 1,
                cue=microworld.cue_for_event(str(event)),
                world_event=str(event),
                trigger_source="paired_intervention",
                interventions=interventions,
                prev_command_hash=state.get("last_command_hash"),
            )
            result = engine.compute_step(state, command, meta)
            if store is not None:
                receipt = store.append_step(command, result.trace)
                if not receipt.committed:
                    raise RuntimeError(receipt.error or "P2 candidate commit failed")
            next_event = schedule[tick_index + 1] if tick_index + 1 < len(schedule) else None
            record = {
                "sequence": int(command["sequence"]),
                "episode_index": episode_index,
                "layout_id": layout_id,
                "event": str(event),
                "cue": result.trace["cue"],
                "next_cue": None
                if next_event is None
                else microworld.cue_for_event(str(next_event)),
                "observation_hash": result.trace["observation_hash"],
                "context_key": result.trace["context_key"],
                "action_taken": result.trace["selected_action"],
                "revealed_outcome": result.trace["world_outcome"]["value"],
            }
            commands.append(command)
            results.append(result)
            public_history.append(record)
            episode_records.append(record)
            state = result.next_state
        episode_histories.append(episode_records)
    return {
        "run_id": run_id,
        "world_seed": world_seed,
        "policy_seed": policy_seed,
        "layout_id": layout_id,
        "initial_state": initial,
        "state": state,
        "meta": meta,
        "commands": commands,
        "results": results,
        "public_history": public_history,
        "episode_histories": episode_histories,
        "schedule_hash": _canonical_hash(flat_schedules),
    }


def _p2_same_schedule_topology_contrast(
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Execute one frozen same-seed/schedule contrast across all three layouts."""

    layout_ids = _p2_unique(
        [str(config["train_layout_id"]), *[str(item) for item in config["heldout_layout_ids"]]]
    )
    schedule_id = sorted(config["heldout_event_schedules"])[0]
    schedule = list(config["heldout_event_schedules"][schedule_id])
    world_seed = int(config["heldout_contexts"][0]["world_seed"])
    layout_runs: dict[str, Any] = {}
    for layout_id in layout_ids:
        run = _p2_run_candidate(
            run_id=f"p2-topology-contrast-{layout_id}",
            world_seed=world_seed,
            policy_seed=int(config["policy_tie_seed"]),
            layout_id=layout_id,
            schedules=[schedule],
            update_mode="frozen",
        )
        ticks: list[dict[str, Any]] = []
        for result in run["results"]:
            trace = result.trace
            score_surface = [
                {
                    "action": str(candidate["action"]),
                    "legal": bool(candidate["legal"]),
                    "total_score": float(candidate["total_score"]),
                    "topology_cost": candidate["topology_cost"],
                    "topology_cost_contribution": candidate["topology_cost_contribution"],
                    "shortest_path_steps": candidate["path"]["shortest_path_steps"],
                    "reachable": bool(candidate["path"]["reachable"]),
                }
                for candidate in trace["candidates"]
            ]
            selected_action = str(trace["selected_action"])
            ticks.append(
                {
                    "sequence": int(trace["sequence"]),
                    "world_event": str(trace["world_event"]),
                    "selected_action": selected_action,
                    "world_outcome": deepcopy(trace["world_outcome"]["value"]),
                    "selected_action_path": deepcopy(
                        trace["action_gate"]["action_paths"][selected_action]
                    ),
                    "candidate_score_surface": score_surface,
                    "candidate_score_surface_hash": _canonical_hash(score_surface),
                    "all_action_paths_hash": _canonical_hash(
                        trace["action_gate"]["action_paths"]
                    ),
                }
            )
        layout_runs[layout_id] = {
            "run_id": str(run["run_id"]),
            "layout_id": layout_id,
            "world_seed": int(run["world_seed"]),
            "policy_seed": int(run["policy_seed"]),
            "schedule_hash": str(run["schedule_hash"]),
            "ticks": ticks,
            "score_surface_hash": _canonical_hash(
                [tick["candidate_score_surface"] for tick in ticks]
            ),
            "path_metric_surface_hash": _canonical_hash(
                [tick["all_action_paths_hash"] for tick in ticks]
            ),
            "action_sequence": [tick["selected_action"] for tick in ticks],
            "outcome_sequence": [tick["world_outcome"] for tick in ticks],
        }
    score_hashes = [run["score_surface_hash"] for run in layout_runs.values()]
    path_hashes = [run["path_metric_surface_hash"] for run in layout_runs.values()]
    action_sequences = [run["action_sequence"] for run in layout_runs.values()]
    outcome_sequences = [run["outcome_sequence"] for run in layout_runs.values()]
    return {
        "producer_function": "verify_ego_life_kernel_v2_microworld._p2_same_schedule_topology_contrast",
        "code_path_hash": engine.compute_code_path_hash(),
        "world_seed": world_seed,
        "policy_seed": int(config["policy_tie_seed"]),
        "event_schedule_id": schedule_id,
        "event_schedule": schedule,
        "layout_ids": layout_ids,
        "layout_runs": layout_runs,
        "score_surfaces_all_identical": len(set(score_hashes)) == 1,
        "path_metric_surfaces_all_identical": len(set(path_hashes)) == 1,
        "selected_action_sequences_all_equal": len(_p2_unique(action_sequences)) == 1,
        "outcome_sequences_all_equal": len(_p2_unique(outcome_sequences)) == 1,
    }


def _p2_delete_episode_source(
    state: Mapping[str, Any], episode_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated = deepcopy(dict(state))
    before_model_hash = engine.canonical_hash(updated["model"])
    before_memory_hash = engine.canonical_hash(updated["memory"])
    filtered = [
        deepcopy(entry)
        for entry in updated["memory"]["episodic"]
        if entry["source_episode_id"] != episode_id
    ]
    deleted_claim_memory, claim_report = claims.delete_sources(
        updated["memory"], source_episode_ids=[episode_id]
    )
    deleted_claim_memory["episodic"] = filtered
    deleted_claim_memory["consolidated"] = engine.rebuild_consolidated_memory(filtered)
    updated["memory"] = deleted_claim_memory
    report = {
        "producer_function": "verify_ego_life_kernel_v2_microworld._p2_delete_episode_source",
        "source_episode_id": episode_id,
        "episodic_records_deleted": len(state["memory"]["episodic"]) - len(filtered),
        "claim_report": claim_report,
        "model_hash_before": before_model_hash,
        "model_hash_after": engine.canonical_hash(updated["model"]),
        "memory_hash_before": before_memory_hash,
        "memory_hash_after": engine.canonical_hash(updated["memory"]),
        "consolidated_recomputed": updated["memory"]["consolidated"]
        == engine.rebuild_consolidated_memory(updated["memory"]["episodic"]),
    }
    return updated, report


def _p2_run_summary(run: Mapping[str, Any]) -> dict[str, Any]:
    traces = [result.trace for result in run["results"]]
    outcomes = [trace["world_outcome"]["value"] for trace in traces]
    site_values = [float(value) for value in outcomes if type(value) is float]
    return {
        "task_outcome_metric_id": P2_TASK_OUTCOME_METRIC_ID,
        "site_outcome_metric_id": P2_SITE_OUTCOME_METRIC_ID,
        "run_id": run["run_id"],
        "action_sequence": [trace["selected_action"] for trace in traces],
        "total_task_outcome": round(sum(site_values), 6),
        "site_visit_count": len(site_values),
        "mean_site_outcome": None
        if not site_values
        else round(sum(site_values) / len(site_values), 6),
        "prediction_error_macro_mae": round(
            sum(
                abs(float(value))
                for trace in traces
                for value in trace["prediction_error"].values()
            )
            / max(1, len(traces) * len(engine.STATE_KEYS)),
            6,
        ),
        "model_update_count": sum(bool(trace["model_update"]["applied"]) for trace in traces),
        "consolidation_application_count": sum(
            bool(trace["memory_update"]["consolidation_applied"]) for trace in traces
        ),
        "terminal_model_hash": engine.canonical_hash(run["state"]["model"]),
        "terminal_memory_hash": engine.canonical_hash(run["state"]["memory"]),
    }


def _p2_episode_curve(run: Mapping[str, Any]) -> dict[str, Any]:
    episodes: list[dict[str, Any]] = []
    slot_values: list[dict[tuple[str, str], list[float]]] = []
    offset = 0
    for episode_index, records in enumerate(run["episode_histories"]):
        results = run["results"][offset : offset + len(records)]
        offset += len(records)
        by_slot: dict[tuple[str, str], list[float]] = {}
        for result in results:
            trace = result.trace
            slot = (str(trace["context_key"]), str(trace["selected_action"]))
            error = sum(abs(float(value)) for value in trace["prediction_error"].values()) / len(engine.STATE_KEYS)
            by_slot.setdefault(slot, []).append(error)
        slot_values.append(by_slot)
        summary = _p2_run_summary({**run, "results": results})
        episodes.append(
            {
                "episode_index": episode_index,
                "checkpoint": offset,
                "raw_macro_mae": summary["prediction_error_macro_mae"],
                "site_visit_count": summary["site_visit_count"],
                "mean_site_outcome": summary["mean_site_outcome"],
                "total_task_outcome": summary["total_task_outcome"],
                "model_update_count": summary["model_update_count"],
                "consolidation_application_count": summary[
                    "consolidation_application_count"
                ],
                "context_action_slots": sorted(f"{context}|{action}" for context, action in by_slot),
            }
        )
    matched = sorted(set(slot_values[0]) & set(slot_values[-1]))

    def matched_mae(values: Mapping[tuple[str, str], list[float]]) -> float | None:
        if not matched:
            return None
        return round(
            sum(sum(values[slot]) / len(values[slot]) for slot in matched) / len(matched),
            6,
        )

    first = matched_mae(slot_values[0])
    final = matched_mae(slot_values[-1])
    return {
        "learning_curve_metric_id": P2_LEARNING_CURVE_METRIC_ID,
        "world_seed": run["world_seed"],
        "episodes": episodes,
        "matched_context_action_slots": [f"{context}|{action}" for context, action in matched],
        "matched_slot_count": len(matched),
        "first_matched_macro_mae": first,
        "final_matched_macro_mae": final,
        "bounded_error_reduction_observed": first is not None and final is not None and final < first,
    }


def _p2_equivalence_comparison(
    candidate_summary: Mapping[str, Any], control: Mapping[str, Any]
) -> dict[str, Any]:
    action_match = control["action_sequence"] == candidate_summary["action_sequence"]
    outcome_match = control["total_task_outcome"] == candidate_summary["total_task_outcome"]
    return {
        "equivalence_rule_id": P2_EQUIVALENCE_RULE_ID,
        "exact_action_sequence_match": action_match,
        "exact_aggregate_task_outcome_match": outcome_match,
        "control_equivalent": action_match or outcome_match,
    }


_P2_CONTROL_PRODUCERS: dict[str, Callable[[Mapping[str, Any]], str]] = {
    "no_update_prior": baseline_no_update,
    "exact_public_history_lookup": baseline_exact_public_history_lookup,
    "count_table": baseline_count_table,
    "transition_table": baseline_transition_table,
    "graph_lookup": baseline_graph_lookup,
    "episodic_traversal": baseline_episodic_traversal,
}

_P2_CONTROL_CUE_BONUSES: dict[str, dict[str, dict[str, float]]] = {
    "resource": {"forage": {"energy": 0.16}},
    "contact": {"approach": {"connection": 0.16}},
    "novelty": {"explore": {"stimulation": 0.16}},
    "threat": {
        "withdraw": {"safety": 0.18},
        "approach": {"safety": -0.09},
        "explore": {"safety": -0.08},
        "forage": {"safety": -0.07},
        "rest": {"safety": -0.05},
    },
    "quiet": {"rest": {"energy": 0.09, "safety": 0.04}},
}


def _p2_control_organism_step(
    organism: Mapping[str, float], *, cue: str, action: str, outcome: float | None
) -> dict[str, float]:
    delta = dict(_NO_UPDATE_PRIORS[action])
    for key, value in _P2_CONTROL_CUE_BONUSES.get(cue, {}).get(action, {}).items():
        delta[key] += value
    if outcome is not None:
        delta["energy"] += 0.05 * outcome
        delta["safety"] += 0.03 * outcome
    return {
        key: round(max(0.0, min(1.0, float(organism[key]) + delta[key])), 6)
        for key in _NO_UPDATE_STATE_KEYS
    }


def _p2_control_goal(organism: Mapping[str, float]) -> str:
    deficits = {
        key: max(0.0, _NO_UPDATE_TARGET - float(organism[key]))
        for key in _NO_UPDATE_STATE_KEYS
    }
    maximum = max(deficits.values())
    if maximum <= 0.0:
        return "homeostasis"
    return min(
        (key for key in _NO_UPDATE_STATE_KEYS if deficits[key] == maximum),
        key=_NO_UPDATE_STATE_KEYS.index,
    )


def run_p2_independent_control(
    *,
    control_id: str,
    world_seed: int,
    layout_id: str,
    schedule: Iterable[str],
    train_public_history: Iterable[Mapping[str, Any]],
    reference_episodes: Iterable[Iterable[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Run a public-only control without calling candidate reducer or scorer."""

    producer = _P2_CONTROL_PRODUCERS[control_id]
    world = microworld.initial_world_state(seed=world_seed, layout_id=layout_id)
    history = [deepcopy(dict(item)) for item in train_public_history]
    query_prefix: list[dict[str, Any]] = []
    lookup_provenance: list[dict[str, Any]] = []
    actions: list[str] = []
    selected_action_paths: list[dict[str, Any]] = []
    outcomes: list[float | None] = []
    organism = {"energy": 0.45, "safety": 0.62, "connection": 0.50, "stimulation": 0.43}
    schedule_list = list(schedule)
    for index, event in enumerate(schedule_list):
        observed = microworld.observe_world_event(world, str(event))
        gate = microworld.legal_action_gate(observed, engine.ACTIONS)
        access = {
            "schema_version": "ego.v2.p2.independent_baseline_access.v1",
            "observation": deepcopy(observed["public_observation"]),
            "legal_actions": list(gate["legal_actions"]),
            "action_paths": deepcopy(gate["action_paths"]),
            "organism": deepcopy(organism),
            "current_goal": _p2_control_goal(organism),
            "public_history": deepcopy(history),
            "query_history_prefix": deepcopy(query_prefix),
            "reference_episodes": [
                [deepcopy(dict(item)) for item in episode] for episode in reference_episodes
            ],
        }
        if control_id == "exact_public_history_lookup":
            lookup = baseline_exact_public_history_lookup_with_provenance(access)
            action = str(lookup["action"])
            lookup_provenance.append(deepcopy(lookup))
        else:
            action = producer(access)
        command_hash = _canonical_hash(
            {"control_id": control_id, "sequence": index + 1, "event": event, "action": action}
        )
        world, transition = microworld.transition_world(
            observed,
            action,
            source_sequence=index + 1,
            source_episode_id=f"control-{control_id}",
            source_command_hash=command_hash,
        )
        next_event = schedule_list[index + 1] if index + 1 < len(schedule_list) else None
        record = {
            "event": str(event),
            "cue": microworld.cue_for_event(str(event)),
            "next_cue": None if next_event is None else microworld.cue_for_event(str(next_event)),
            "action_taken": action,
            "revealed_outcome": transition["outcome"],
            "layout_id": layout_id,
        }
        query_prefix.append(record)
        history.append(record)
        actions.append(action)
        selected_action_paths.append(deepcopy(gate["action_paths"][action]))
        outcomes.append(transition["outcome"])
        organism = _p2_control_organism_step(
            organism,
            cue=microworld.cue_for_event(str(event)),
            action=action,
            outcome=transition["outcome"],
        )
    site_values = [float(value) for value in outcomes if type(value) is float]
    return {
        "control_id": control_id,
        "producer_function": f"verify_ego_life_kernel_v2_microworld.{producer.__name__}",
        "access_contract": [
            "current_public_observation_and_layout",
            "legal_actions",
            "public_label_free_action_paths",
            "fixed_public_organism_and_goal",
            "equal_access_train_public_history",
            "own_heldout_public_prefix",
        ],
        "exact_lookup_access_choice": (
            "layout_invariant_public_event_cue_action_outcome_prefix"
            if control_id == "exact_public_history_lookup"
            else None
        ),
        "action_sequence": actions,
        "selected_action_paths": selected_action_paths,
        "selected_action_path_hash": _canonical_hash(selected_action_paths),
        "lookup_provenance": lookup_provenance,
        "total_task_outcome": round(sum(site_values), 6),
        "site_visit_count": len(site_values),
        "mean_site_outcome": None
        if not site_values
        else round(sum(site_values) / len(site_values), 6),
    }


def _p2_baseline_arm_id(
    *, train_world_seed: int, context_id: str, control_id: str
) -> str:
    return f"{int(train_world_seed)}:{str(context_id)}:{str(control_id)}"


def _p2_baseline_independence_control(
    *,
    arms: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Disable candidate paths while invoking every declared baseline arm."""

    arm_records = [deepcopy(dict(arm)) for arm in arms]
    arm_ids = [str(arm.get("arm_id", "")) for arm in arm_records]
    trap_calls = {"candidate_reducer": 0, "candidate_scorer": 0}
    invocations: dict[str, Any] = {}
    arm_results: dict[str, Any] = {}
    original_reducer = engine.compute_step
    original_scorer = engine._score_candidate

    def reducer_trap(*_args: Any, **_kwargs: Any) -> Any:
        trap_calls["candidate_reducer"] += 1
        raise AssertionError("candidate reducer independence trap fired")

    def scorer_trap(*_args: Any, **_kwargs: Any) -> Any:
        trap_calls["candidate_scorer"] += 1
        raise AssertionError("candidate scorer independence trap fired")

    try:
        engine.compute_step = reducer_trap
        engine._score_candidate = scorer_trap
        for arm, arm_id in zip(arm_records, arm_ids):
            reducer_before = trap_calls["candidate_reducer"]
            scorer_before = trap_calls["candidate_scorer"]
            control_id = str(arm.get("control_id", ""))
            schedule_list = list(arm.get("schedule", []))
            invocation = {
                "arm_id": arm_id,
                "control_id": control_id,
                "train_world_seed": arm.get("train_world_seed"),
                "context_id": arm.get("context_id"),
                "world_seed": arm.get("world_seed"),
                "layout_id": arm.get("layout_id"),
                "expected_action_count": len(schedule_list),
            }
            try:
                result = run_p2_independent_control(
                    control_id=control_id,
                    world_seed=int(arm["world_seed"]),
                    layout_id=str(arm["layout_id"]),
                    schedule=schedule_list,
                    train_public_history=arm.get("train_public_history", []),
                    reference_episodes=arm.get("reference_episodes", []),
                )
                arm_results[arm_id] = result
                invocation.update(
                    {
                        "completed": True,
                        "action_count": len(result["action_sequence"]),
                        "action_sequence_hash": _canonical_hash(
                            result["action_sequence"]
                        ),
                    }
                )
            except Exception as exc:  # structured hostile-control evidence
                invocation.update(
                    {
                        "completed": False,
                        "action_count": None,
                        "action_sequence_hash": None,
                        "error_type": type(exc).__name__,
                    }
                )
            reducer_delta = trap_calls["candidate_reducer"] - reducer_before
            scorer_delta = trap_calls["candidate_scorer"] - scorer_before
            invocation.update(
                {
                    "candidate_reducer_trap_calls": reducer_delta,
                    "candidate_scorer_trap_calls": scorer_delta,
                    "candidate_reducer_called": reducer_delta > 0,
                    "candidate_scorer_called": scorer_delta > 0,
                }
            )
            invocations[arm_id] = invocation
    finally:
        engine.compute_step = original_reducer
        engine._score_candidate = original_scorer

    compatible = (
        bool(arm_records)
        and all(arm_ids)
        and len(arm_ids) == len(set(arm_ids))
        and set(invocations) == set(arm_ids)
        and all(
            item.get("completed") is True
            and item.get("action_count") == item.get("expected_action_count")
            and item.get("candidate_reducer_called") is False
            and item.get("candidate_scorer_called") is False
            for item in invocations.values()
        )
        and trap_calls == {"candidate_reducer": 0, "candidate_scorer": 0}
    )
    return {
        "producer_function": "verify_ego_life_kernel_v2_microworld._p2_baseline_independence_control",
        "computed": True,
        "candidate_reducer_disabled_compatible": compatible,
        "arm_count": len(arm_records),
        "unique_arm_count": len(set(arm_ids)),
        "duplicate_arm_ids": sorted(
            {arm_id for arm_id in arm_ids if arm_ids.count(arm_id) > 1}
        ),
        "candidate_reducer_trap_calls": trap_calls["candidate_reducer"],
        "candidate_scorer_trap_calls": trap_calls["candidate_scorer"],
        "control_invocations": invocations,
        "arm_results": arm_results,
    }


def _p2_modify_counterfactual_state(
    *,
    name: str,
    train: Mapping[str, Any],
    other_train: Mapping[str, Any],
    base_state: Mapping[str, Any],
    source_episode_index: int,
    irrelevant_episode_id: str,
) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    state = deepcopy(dict(base_state))
    memory_mode = "canonical"
    consolidation_mode = "canonical"
    report: dict[str, Any] = {"counterfactual": name, "reachable_state_claim": False}
    if name == "Memory_OFF":
        memory_mode = "off"
    elif name == "Freeze_Updates":
        report["note"] = "heldout candidate is already frozen; exact zero-effect control"
    elif name == "source_memory_deletion":
        source_episode_id = engine.episode_id_for(
            str(train["run_id"]), int(source_episode_index)
        )
        state, deletion = _p2_delete_episode_source(state, source_episode_id)
        report["deletion"] = deletion
        inert, inert_report = _p2_delete_episode_source(base_state, irrelevant_episode_id)
        report["irrelevant_deletion"] = inert_report
        report["irrelevant_state_bytes_equal"] = engine.canonical_json(inert) == engine.canonical_json(base_state)
    elif name == "consolidation_OFF":
        before = engine.canonical_hash(state["memory"]["consolidated"])
        consolidation_mode = "off_projection"
        report.update(
            {
                "projected_off_json_pointer": "/memory/consolidated",
                "before_hash": before,
                "persisted_memory_bytes_unchanged": True,
            }
        )
    elif name == "model_ONLY":
        state["memory"] = _p2_empty_memory()
    elif name == "memory_ONLY":
        state["model"] = {}
    elif name == "cross_replication_memory_swap":
        state["memory"] = deepcopy(other_train["state"]["memory"])
        report["source_train_world_seed"] = other_train["world_seed"]
    else:
        raise ValueError(f"unknown P2 counterfactual: {name}")
    report["model_hash"] = engine.canonical_hash(state["model"])
    report["memory_hash"] = engine.canonical_hash(state["memory"])
    return state, report, memory_mode, consolidation_mode


def _p2_write_trace(
    store: SQLiteEventStore, output: Path, run_ids: Iterable[str]
) -> None:
    rows: list[dict[str, Any]] = []
    for run_id in sorted(run_ids):
        recovered = store.recover_run(run_id)
        rows.append(
            {
                "record_type": "run",
                "producer_function": "verify_ego_life_kernel_v2_microworld._p2_write_trace",
                "input_artifacts": [P2_GENERATED_DB_LOGICAL_ID],
                "run_id": run_id,
                "seed": recovered.run_meta["seed"],
                "initial_state_hash": engine.state_hash(recovered.frames[0].state),
                "terminal_state_hash": engine.state_hash(recovered.state),
                "command_count": recovered.command_count,
                "aggregation_rule": "ordered_recomputed_p2_multi_run_trace_export",
                "code_path_hash": recovered.run_meta["code_path_hash"],
            }
        )
        command_rows = store.connection.execute(
            "SELECT sequence, command_json FROM commands WHERE run_id = ? ORDER BY sequence",
            (run_id,),
        ).fetchall()
        for command_row, trace in zip(command_rows, recovered.traces):
            command = json.loads(command_row["command_json"])
            rows.append({"record_type": "command", "run_id": run_id, "sequence": int(command_row["sequence"]), "command": command})
            rows.append({"record_type": "trace", "run_id": run_id, "sequence": int(command_row["sequence"]), "trace": trace})
    output.write_text(
        "".join(_canonical_json(row) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def _p2_create_runs(output: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    db_path = output / "continuity.sqlite3"
    trace_path = output / "trace.jsonl"
    for path in (db_path, trace_path):
        if path.exists():
            path.unlink()
    train_runs: dict[int, dict[str, Any]] = {}
    candidate_runs: dict[str, dict[str, Any]] = {}
    from_scratch_runs: dict[str, dict[str, Any]] = {}
    counterfactual_runs: dict[str, dict[str, Any]] = {}
    counterfactual_reports: dict[str, dict[str, Any]] = {}
    run_ids: list[str] = []
    product_controller_inputs = {
        "run_id": "p2-product-trigger",
        "policy_seed": int(config["policy_tie_seed"]),
        "world_seed": int(config["train_world_seeds"][0]),
        "layout_id": str(config["heldout_layout_ids"][0]),
    }
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(
            store,
            run_id=product_controller_inputs["run_id"],
            seed=product_controller_inputs["policy_seed"],
            world_seed=product_controller_inputs["world_seed"],
            layout_id=product_controller_inputs["layout_id"],
        )
        terminal = TerminalPlayground(controller)
        product_outputs = [
            terminal.execute("inject resource_appears"),
            terminal.execute("run 11"),
            terminal.execute("pause"),
            terminal.execute("inspect"),
        ]
        run_ids.append(controller.run_id)
        for seed in config["train_world_seeds"]:
            run_id = f"p2-train-{seed}"
            train_run = _p2_run_candidate(
                run_id=run_id,
                world_seed=int(seed),
                policy_seed=int(config["policy_tie_seed"]),
                layout_id=str(config["train_layout_id"]),
                schedules=config["train_episode_schedules"],
                store=store,
            )
            train_run["execution_context"] = {
                "verification_config_id": str(config["config_id"]),
                "run_role": "train",
            }
            train_runs[int(seed)] = train_run
            run_ids.append(run_id)
        contexts = {str(item["context_id"]): item for item in config["heldout_contexts"]}
        for train_seed in config["train_world_seeds"]:
            train = train_runs[int(train_seed)]
            other_seed = next(int(seed) for seed in config["train_world_seeds"] if int(seed) != int(train_seed))
            other_train = train_runs[other_seed]
            for context_id, context in contexts.items():
                schedule = config["heldout_event_schedules"][context["event_schedule_id"]]
                key = f"{train_seed}:{context_id}"
                candidate_id = f"p2-heldout-{train_seed}-{context_id}"
                base, transplant = _p2_transplant(
                    run_id=candidate_id,
                    world_seed=int(context["world_seed"]),
                    layout_id=str(context["layout_id"]),
                    model=train["state"]["model"],
                    memory=train["state"]["memory"],
                )
                candidate = _p2_run_candidate(
                    run_id=candidate_id,
                    world_seed=int(context["world_seed"]),
                    policy_seed=int(config["policy_tie_seed"]),
                    layout_id=str(context["layout_id"]),
                    schedules=[schedule],
                    base_state=base,
                    update_mode=str(config["heldout_update_mode"]),
                    store=store,
                )
                candidate["transplant"] = transplant
                candidate["execution_context"] = {
                    "verification_config_id": str(config["config_id"]),
                    "train_world_seed": int(train_seed),
                    "context_id": str(context_id),
                    "event_schedule_id": str(context["event_schedule_id"]),
                }
                candidate_runs[key] = candidate
                run_ids.append(candidate_id)

                scratch_id = f"p2-scratch-{train_seed}-{context_id}"
                scratch = _p2_run_candidate(
                    run_id=scratch_id,
                    world_seed=int(context["world_seed"]),
                    policy_seed=int(config["policy_tie_seed"]),
                    layout_id=str(context["layout_id"]),
                    schedules=[schedule],
                    update_mode=str(config["heldout_update_mode"]),
                    store=store,
                )
                scratch["execution_context"] = {
                    "verification_config_id": str(config["config_id"]),
                    "train_world_seed": int(train_seed),
                    "context_id": str(context_id),
                    "event_schedule_id": str(context["event_schedule_id"]),
                    "candidate_ablation": "from_scratch_empty_model_and_memory",
                }
                from_scratch_runs[key] = scratch
                run_ids.append(scratch_id)

                for name in config["counterfactuals"]:
                    cf_id = f"p2-cf-{str(name).lower().replace('_', '-')}-{train_seed}-{context_id}"
                    cf_fresh, _ = _p2_transplant(
                        run_id=cf_id,
                        world_seed=int(context["world_seed"]),
                        layout_id=str(context["layout_id"]),
                        model=train["state"]["model"],
                        memory=train["state"]["memory"],
                    )
                    modified, report, memory_mode, consolidation_mode = _p2_modify_counterfactual_state(
                        name=str(name),
                        train=train,
                        other_train=other_train,
                        base_state=cf_fresh,
                        source_episode_index=int(config["source_deletion_episode_index"]),
                        irrelevant_episode_id=str(config["irrelevant_source_episode_id"]),
                    )
                    report["execution_context"] = {
                        "verification_config_id": str(config["config_id"]),
                        "train_world_seed": int(train_seed),
                        "context_id": str(context_id),
                        "event_schedule_id": str(context["event_schedule_id"]),
                    }
                    cf = _p2_run_candidate(
                        run_id=cf_id,
                        world_seed=int(context["world_seed"]),
                        policy_seed=int(config["policy_tie_seed"]),
                        layout_id=str(context["layout_id"]),
                        schedules=[schedule],
                        base_state=modified,
                        update_mode=str(config["heldout_update_mode"]),
                        memory_mode=memory_mode,
                        consolidation_mode=consolidation_mode,
                        store=store,
                    )
                    cf["execution_context"] = deepcopy(report["execution_context"])
                    cf_key = f"{name}:{key}"
                    counterfactual_runs[cf_key] = cf
                    counterfactual_reports[cf_key] = report
                    run_ids.append(cf_id)
        product_snapshot_hash = _canonical_hash(product_outputs[-1]["snapshot"])
        expected_states = {
            controller.run_id: deepcopy(controller.state),
            **{run["run_id"]: deepcopy(run["state"]) for run in train_runs.values()},
            **{run["run_id"]: deepcopy(run["state"]) for run in candidate_runs.values()},
            **{run["run_id"]: deepcopy(run["state"]) for run in from_scratch_runs.values()},
            **{run["run_id"]: deepcopy(run["state"]) for run in counterfactual_runs.values()},
        }
    with SQLiteEventStore(db_path) as reopened:
        recovered = {run_id: reopened.recover_run(run_id) for run_id in sorted(run_ids)}
        _p2_write_trace(reopened, trace_path, run_ids)
    return {
        "train_runs": train_runs,
        "candidate_runs": candidate_runs,
        "from_scratch_runs": from_scratch_runs,
        "counterfactual_runs": counterfactual_runs,
        "counterfactual_reports": counterfactual_reports,
        "run_ids": sorted(run_ids),
        "recovered": recovered,
        "product_outputs": product_outputs,
        "product_snapshot_hash": product_snapshot_hash,
        "product_controller_inputs": deepcopy(product_controller_inputs),
        "expected_states": expected_states,
    }


def _p2_product_trigger_seed_provenance(
    *,
    recovery: Any,
    controller_inputs: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind policy/world seeds to recovered metadata and recomputed initial state."""

    failures: list[str] = []
    recorded = deepcopy(dict(controller_inputs))
    expected_policy_seed = int(config["policy_tie_seed"])
    expected_world_seed = int(config["train_world_seeds"][0])
    expected_layout_id = str(config["heldout_layout_ids"][0])
    recovered_run_id = str(getattr(recovery, "run_id", ""))
    run_meta = getattr(recovery, "run_meta", {})
    recovered_policy_seed = run_meta.get("seed") if isinstance(run_meta, Mapping) else None
    frames = tuple(getattr(recovery, "frames", ()))
    recovered_initial_state = frames[0].state if frames else None
    recovered_terminal_state = getattr(recovery, "state", None) if frames else None
    recovered_layout_id = None
    if isinstance(recovered_terminal_state, Mapping):
        recovered_layout_id = (
            recovered_terminal_state.get("world", {})
            .get("layout", {})
            .get("layout_id")
        )

    if recorded.get("run_id") != recovered_run_id:
        failures.append("recorded_run_id_not_recovered_run_id")
    if recorded.get("policy_seed") != expected_policy_seed:
        failures.append("recorded_policy_seed_not_frozen_policy_seed")
    if recovered_policy_seed != recorded.get("policy_seed"):
        failures.append("recovered_policy_seed_not_recorded_policy_seed")
    if recorded.get("world_seed") != expected_world_seed:
        failures.append("recorded_world_seed_not_frozen_train_seed")
    if recorded.get("layout_id") != expected_layout_id:
        failures.append("recorded_layout_not_frozen_product_layout")
    if recovered_layout_id != recorded.get("layout_id"):
        failures.append("recovered_layout_not_recorded_layout")

    recomputed_initial_state = None
    try:
        recomputed_initial_state = engine.initial_state(
            run_id=str(recorded["run_id"]),
            seed=int(recorded["world_seed"]),
            layout_id=str(recorded["layout_id"]),
        )
    except (KeyError, TypeError, ValueError, engine.EngineInvariantError):
        failures.append("recorded_controller_inputs_cannot_recompute_initial_state")
    recovered_initial_state_hash = (
        _canonical_hash(recovered_initial_state)
        if isinstance(recovered_initial_state, Mapping)
        else None
    )
    recomputed_initial_state_hash = (
        _canonical_hash(recomputed_initial_state)
        if isinstance(recomputed_initial_state, Mapping)
        else None
    )
    initial_state_matches = (
        recovered_initial_state_hash is not None
        and recovered_initial_state_hash == recomputed_initial_state_hash
    )
    if not initial_state_matches:
        failures.append("recorded_world_seed_does_not_recompute_recovered_initial_state")
    return {
        "producer_function": (
            "verify_ego_life_kernel_v2_microworld."
            "_p2_product_trigger_seed_provenance"
        ),
        "recorded_controller_inputs_hash": _canonical_hash(recorded),
        "recorded_run_id": recorded.get("run_id"),
        "recovered_run_id": recovered_run_id,
        "recorded_policy_seed": recorded.get("policy_seed"),
        "recovered_policy_seed": recovered_policy_seed,
        "expected_policy_seed": expected_policy_seed,
        "recorded_world_seed": recorded.get("world_seed"),
        "expected_world_seed": expected_world_seed,
        "recorded_layout_id": recorded.get("layout_id"),
        "recovered_layout_id": recovered_layout_id,
        "expected_layout_id": expected_layout_id,
        "recovered_initial_state_hash": recovered_initial_state_hash,
        "recomputed_initial_state_hash": recomputed_initial_state_hash,
        "world_seed_recomputed_initial_state_match": initial_state_matches,
        "failures": sorted(set(failures)),
        "valid": not failures,
    }


def _p2_input_artifacts(output: Path) -> list[dict[str, Any]]:
    return [
        _input_artifact(output / "continuity.sqlite3", logical_id=P2_GENERATED_DB_LOGICAL_ID),
        _input_artifact(output / "trace.jsonl", logical_id=P2_GENERATED_TRACE_LOGICAL_ID),
        _input_artifact(TASK_SCOPE_PATH, logical_id=P2_TASK_SCOPE_LOGICAL_ID),
    ]


def _p2_metric(
    *, name: str, value: Any, inputs: list[Mapping[str, Any]], ids: Mapping[str, Any], rule: str
) -> dict[str, Any]:
    return _evidence(
        producer_function=f"verify_ego_life_kernel_v2_microworld.{name}",
        input_artifacts=inputs,
        run_id=P2_RUN_ID,
        seed_context_episode_ids=ids,
        aggregation_rule=rule,
        value=value,
    )


def _p2_tamper_control(db_path: Path, control_id: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ego-v2-p2-tamper-") as temporary:
        copied = Path(temporary) / "tamper.sqlite3"
        shutil.copy2(db_path, copied)
        connection = sqlite3.connect(str(copied))
        connection.row_factory = sqlite3.Row
        run_id = "p2-product-trigger"
        if control_id == "stored_action_rehash":
            row = connection.execute(
                "SELECT trace_json FROM traces WHERE run_id = ? AND sequence = 1", (run_id,)
            ).fetchone()
            trace = json.loads(row["trace_json"])
            trace["selected_action"] = "withdraw" if trace["selected_action"] != "withdraw" else "rest"
            trace["trace_hash"] = engine.compute_trace_hash(trace)
            connection.execute(
                "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = 1",
                (engine.canonical_json(trace), trace["trace_hash"], run_id),
            )
        elif control_id == "heldout_layout_rehash":
            run_id = "p2-heldout-30-heldout_42_vertical_alpha"
            row = connection.execute(
                "SELECT initial_state_json FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            state = json.loads(row["initial_state_json"])
            state["world"]["layout"] = deepcopy(microworld.LAYOUTS["p2_offset_v1"])
            connection.execute(
                "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
                (engine.canonical_json(state), engine.canonical_hash(state), run_id),
            )
        elif control_id == "consolidation_lineage_rehash":
            run_id = "p2-heldout-30-heldout_42_vertical_alpha"
            row = connection.execute(
                "SELECT initial_state_json FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            state = json.loads(row["initial_state_json"])
            if not state["memory"]["consolidated"]:
                connection.close()
                return {"control_id": control_id, "control_available": False, "failed_closed": False}
            state["memory"]["consolidated"][0]["source_command_hashes"][0] = "f" * 64
            connection.execute(
                "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
                (engine.canonical_json(state), engine.canonical_hash(state), run_id),
            )
        else:
            connection.close()
            raise ValueError(control_id)
        connection.commit()
        connection.close()
        failed = False
        try:
            with SQLiteEventStore(copied) as store:
                store.recover_run(run_id)
        except (RecoveryError, ValueError):
            failed = True
        return {"control_id": control_id, "control_available": True, "failed_closed": failed}


def _p2_stored_action_input_control(
    tamper_control: Mapping[str, Any],
    *,
    db_path: str | Path,
    recovery_recomputed: Iterable[bool],
) -> dict[str, Any]:
    """Derive the input claim from persisted commands, recovery, and rehash tamper."""

    correct_control = tamper_control.get("control_id") == "stored_action_rehash"
    available = tamper_control.get("control_available") is True
    failed_closed = tamper_control.get("failed_closed") is True
    command_records: list[dict[str, Any]] = []
    command_read_error: str | None = None
    try:
        with sqlite3.connect(str(db_path)) as connection:
            rows = connection.execute(
                "SELECT command_json FROM commands ORDER BY run_id, sequence"
            ).fetchall()
        command_records = [json.loads(str(row[0])) for row in rows]
    except (json.JSONDecodeError, sqlite3.Error, TypeError, ValueError) as exc:
        command_read_error = type(exc).__name__
    forbidden = {"action", "selected_action", "stored_action", "stored_selected_action"}
    offender_hashes: list[str] = []

    def walk(value: Any, tokens: list[str]) -> None:
        if isinstance(value, Mapping):
            for index, (key, item) in enumerate(value.items()):
                normalized = str(key).strip().casefold().replace("-", "_")
                if normalized in forbidden:
                    offender_hashes.append(_canonical_hash([*tokens, f"key:{index}"]))
                walk(item, [*tokens, f"value:{index}"])
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, [*tokens, f"item:{index}"])

    for index, command in enumerate(command_records):
        walk(command, [f"command:{index}"])
    recoveries = [bool(item) for item in recovery_recomputed]
    all_recomputed = bool(recoveries) and all(recoveries)
    computed = (
        correct_control
        and available
        and command_read_error is None
        and bool(command_records)
        and bool(recoveries)
    )
    clean_input_path = (
        not offender_hashes and all_recomputed and failed_closed
    )
    return {
        "producer_function": "verify_ego_life_kernel_v2_microworld._p2_stored_action_input_control",
        "control_id": tamper_control.get("control_id"),
        "computed": computed,
        "tamper_failed_closed": failed_closed,
        "persisted_command_count": len(command_records),
        "persisted_command_set_hash": _canonical_hash(command_records),
        "command_read_error_type": command_read_error,
        "command_action_input_offender_count": len(offender_hashes),
        "command_action_input_offender_hashes": offender_hashes,
        "fresh_recovery_count": len(recoveries),
        "all_fresh_recoveries_recomputed": all_recomputed,
        "stored_action_used_as_input": False if computed and clean_input_path else (True if computed else None),
    }


def run_p2_verification(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    config = _load_frozen_p2_config()
    config_hash_before_execution = _canonical_hash(config)
    declared_plan = build_p2_invocation_plan(config)
    runs = _p2_create_runs(output, config)
    inputs = _p2_input_artifacts(output)
    recorded_product_run_id = str(runs["product_controller_inputs"]["run_id"])
    product_recovery = runs["recovered"][recorded_product_run_id]
    product_seed_provenance = _p2_product_trigger_seed_provenance(
        recovery=product_recovery,
        controller_inputs=runs["product_controller_inputs"],
        config=config,
    )

    train_curves = {
        str(seed): _p2_episode_curve(run) for seed, run in sorted(runs["train_runs"].items())
    }
    train_summaries = {
        str(seed): _p2_run_summary(run) for seed, run in sorted(runs["train_runs"].items())
    }
    for seed_text, curve in train_curves.items():
        seed = int(seed_text)
        for episode in curve["episodes"]:
            episode["metric"] = _p2_metric(
                name="p2_episode_curve_metric",
                value={key: deepcopy(value) for key, value in episode.items() if key != "metric"},
                inputs=inputs,
                ids={"train_world_seed": seed, "episode_index": episode["episode_index"], "checkpoint": episode["checkpoint"]},
                rule=str(config["learning_curve_metric"]),
            )
        curve["matched_metric"] = _p2_metric(
            name="p2_matched_slot_curve_metric",
            value={
                "matched_slot_count": curve["matched_slot_count"],
                "first_matched_macro_mae": curve["first_matched_macro_mae"],
                "final_matched_macro_mae": curve["final_matched_macro_mae"],
                "bounded_error_reduction_observed": curve["bounded_error_reduction_observed"],
            },
            inputs=inputs,
            ids={"train_world_seed": seed, "checkpoints": config["learning_checkpoints"]},
            rule=str(config["learning_curve_metric"]),
        )
        train_summaries[seed_text]["metric"] = _p2_metric(
            name="p2_train_summary_metric",
            value=deepcopy(train_summaries[seed_text]),
            inputs=inputs,
            ids={"train_world_seed": seed, "episode_indices": list(range(len(config["train_episode_schedules"])))},
            rule="aggregate_all_frozen_train_episode_traces_without_post_result_selection",
        )
    contexts = {str(item["context_id"]): item for item in config["heldout_contexts"]}
    baseline_arm_specs: list[dict[str, Any]] = []
    for candidate_arm in declared_plan["heldout_candidate_arms"]:
        arm_train_seed = int(candidate_arm["train_world_seed"])
        arm_context_id = str(candidate_arm["context_id"])
        arm_context = contexts[arm_context_id]
        for arm_control_id in config["independent_controls"]:
            baseline_arm_specs.append(
                {
                    "arm_id": _p2_baseline_arm_id(
                        train_world_seed=arm_train_seed,
                        context_id=arm_context_id,
                        control_id=str(arm_control_id),
                    ),
                    "control_id": str(arm_control_id),
                    "train_world_seed": arm_train_seed,
                    "context_id": arm_context_id,
                    "world_seed": int(arm_context["world_seed"]),
                    "layout_id": str(arm_context["layout_id"]),
                    "schedule": deepcopy(
                        config["heldout_event_schedules"][
                            arm_context["event_schedule_id"]
                        ]
                    ),
                    "train_public_history": deepcopy(
                        runs["train_runs"][arm_train_seed]["public_history"]
                    ),
                    "reference_episodes": deepcopy(
                        runs["train_runs"][arm_train_seed]["episode_histories"]
                    ),
                }
            )
    expected_baseline_arm_ids = [
        str(arm["arm_id"]) for arm in baseline_arm_specs
    ]
    baseline_independence_control = _p2_baseline_independence_control(
        arms=baseline_arm_specs
    )
    baseline_arm_results = baseline_independence_control.pop("arm_results")
    exact_baseline_arm_coverage = (
        len(expected_baseline_arm_ids) == len(set(expected_baseline_arm_ids))
        and set(baseline_independence_control["control_invocations"])
        == set(expected_baseline_arm_ids)
    )
    baseline_independence_control["expected_arm_count"] = len(
        expected_baseline_arm_ids
    )
    baseline_independence_control["exact_expected_arm_coverage"] = (
        exact_baseline_arm_coverage
    )
    baseline_independence_control["candidate_reducer_disabled_compatible"] = bool(
        baseline_independence_control["candidate_reducer_disabled_compatible"]
        and exact_baseline_arm_coverage
    )
    heldout_rows: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []
    for arm in declared_plan["heldout_candidate_arms"]:
        train_seed = int(arm["train_world_seed"])
        context_id = str(arm["context_id"])
        context = contexts[context_id]
        key = f"{train_seed}:{context_id}"
        candidate_summary = _p2_run_summary(runs["candidate_runs"][key])
        scratch_summary = _p2_run_summary(runs["from_scratch_runs"][key])
        candidate_summary["metric"] = _p2_metric(
            name="p2_heldout_candidate_summary",
            value=deepcopy(candidate_summary),
            inputs=inputs,
            ids={"train_world_seed": train_seed, "context_id": context_id},
            rule=f"{config['task_outcome_metric']}__and__{config['site_outcome_metric']}__updates_frozen",
        )
        scratch_summary["metric"] = _p2_metric(
            name="p2_heldout_from_scratch_summary",
            value=deepcopy(scratch_summary),
            inputs=inputs,
            ids={"train_world_seed": train_seed, "context_id": context_id, "ablation": config["candidate_ablation"]},
            rule=f"{config['task_outcome_metric']}__and__{config['site_outcome_metric']}__empty_model_and_memory",
        )
        controls: dict[str, Any] = {}
        for control_id in config["independent_controls"]:
            baseline_arm_id = _p2_baseline_arm_id(
                train_world_seed=train_seed,
                context_id=context_id,
                control_id=str(control_id),
            )
            independence_invocation = baseline_independence_control[
                "control_invocations"
            ][baseline_arm_id]
            control = baseline_arm_results.get(baseline_arm_id)
            if control is None:
                control = {
                    "control_id": str(control_id),
                    "producer_function": "unavailable__independence_trap_failed",
                    "access_contract": [],
                    "exact_lookup_access_choice": None,
                    "action_sequence": [],
                    "selected_action_paths": [],
                    "selected_action_path_hash": _canonical_hash([]),
                    "lookup_provenance": [],
                    "total_task_outcome": 0.0,
                    "site_visit_count": 0,
                    "mean_site_outcome": None,
                    "structured_failure": deepcopy(independence_invocation),
                }
            control = {
                **control,
                "candidate_reducer_called": bool(
                    independence_invocation["candidate_reducer_called"]
                ),
                "candidate_scorer_called": bool(
                    independence_invocation["candidate_scorer_called"]
                ),
                "candidate_reducer_trap_calls": int(
                    independence_invocation["candidate_reducer_trap_calls"]
                ),
                "candidate_scorer_trap_calls": int(
                    independence_invocation["candidate_scorer_trap_calls"]
                ),
                "independence_arm_id": baseline_arm_id,
            }
            equivalence = _p2_equivalence_comparison(candidate_summary, control)
            row = {
                **control,
                "train_world_seed": train_seed,
                "context_id": context_id,
                **equivalence,
                "metric": _p2_metric(
                    name="run_p2_independent_control",
                    value={**deepcopy(control), **deepcopy(equivalence)},
                    inputs=inputs,
                    ids={"train_world_seed": train_seed, "context_id": context_id, "control_id": control_id},
                    rule=str(config["equivalence_rule"]),
                ),
            }
            baseline_rows.append(row)
            controls[str(control_id)] = row
        heldout_rows.append(
            {
                "train_world_seed": train_seed,
                "context": deepcopy(dict(context)),
                "reachable_state_claim": False,
                "candidate": candidate_summary,
                "from_scratch": scratch_summary,
                "candidate_vs_from_scratch": _p2_metric(
                    name="p2_heldout_candidate_vs_from_scratch",
                    value={
                        "task_outcome_delta": round(candidate_summary["total_task_outcome"] - scratch_summary["total_task_outcome"], 6),
                        "exact_action_sequence_match": candidate_summary["action_sequence"] == scratch_summary["action_sequence"],
                    },
                    inputs=inputs,
                    ids={"train_world_seed": train_seed, "context_id": context_id},
                    rule="trained_adaptive_bytes_minus_fresh_empty_model_and_memory_under_frozen_updates",
                ),
                "independent_controls": controls,
            }
        )
    counterfactual_rows: list[dict[str, Any]] = []
    for key, run in runs["counterfactual_runs"].items():
        name, train_seed, context_id = key.split(":", 2)
        canonical = _p2_run_summary(runs["candidate_runs"][f"{train_seed}:{context_id}"])
        summary = _p2_run_summary(run)
        summary["metric"] = _p2_metric(
            name="p2_counterfactual_summary",
            value=deepcopy(summary),
            inputs=inputs,
            ids={"train_world_seed": int(train_seed), "context_id": context_id, "counterfactual": name},
            rule=f"{config['task_outcome_metric']}__and__{config['site_outcome_metric']}__counterfactual_rerun",
        )
        effect = {
            "exact_action_sequence_changed": summary["action_sequence"] != canonical["action_sequence"],
            "task_outcome_delta": round(summary["total_task_outcome"] - canonical["total_task_outcome"], 6),
            "site_visit_delta": summary["site_visit_count"] - canonical["site_visit_count"],
        }
        counterfactual_rows.append(
            {
                "counterfactual": name,
                "train_world_seed": int(train_seed),
                "context_id": context_id,
                "summary": summary,
                "intervention_report": runs["counterfactual_reports"][key],
                "effect": effect,
                "metric": _p2_metric(
                    name="p2_counterfactual_effect",
                    value=effect,
                    inputs=inputs,
                    ids={"train_world_seed": int(train_seed), "context_id": context_id, "counterfactual": name},
                    rule="same_fresh_world_and_schedule_counterfactual_minus_canonical_transplanted_candidate",
                ),
            }
        )

    update_traces = [
        result.trace
        for run in runs["train_runs"].values()
        for result in run["results"]
    ]
    update_equations_valid = all(
        trace["model_update"]["applied"]
        and all(
            trace["model_update"]["prediction_error"][key]
            == round(trace["actual_delta"][key] - trace["model_update"]["prediction_before"][key], 6)
            and trace["model_update"]["applied_delta"][key]
            == round(engine.EMA_ALPHA * trace["model_update"]["prediction_error"][key], 6)
            and trace["model_update"]["prediction_after"][key]
            == round(
                trace["model_update"]["prediction_before"][key]
                + trace["model_update"]["applied_delta"][key],
                6,
            )
            for key in engine.STATE_KEYS
        )
        and trace["model_update"]["model_before_hash"] == trace["model_bytes"]["before_hash"]
        and trace["model_update"]["model_after_hash"] == trace["model_bytes"]["after_hash"]
        for trace in update_traces
    )
    frozen_runs = list(runs["candidate_runs"].values()) + list(runs["counterfactual_runs"].values())
    frozen_model_memory_preserved = all(
        all(
            not result.trace["model_bytes"]["changed"]
            and not result.trace["memory_bytes"]["changed"]
            for result in run["results"]
        )
        for run in frozen_runs
    )
    consolidation_rebuilt = all(
        run["state"]["memory"]["consolidated"]
        == engine.rebuild_consolidated_memory(run["state"]["memory"]["episodic"])
        for run in runs["train_runs"].values()
    )
    consolidation_idempotent = all(
        engine.rebuild_consolidated_memory(run["state"]["memory"]["episodic"])
        == engine.rebuild_consolidated_memory(deepcopy(run["state"]["memory"]["episodic"]))
        for run in runs["train_runs"].values()
    )

    controls = [
        _p2_tamper_control(output / "continuity.sqlite3", control_id)
        for control_id in (
            "stored_action_rehash",
            "heldout_layout_rehash",
            "consolidation_lineage_rehash",
        )
    ]
    stored_action_tamper = next(
        control for control in controls if control["control_id"] == "stored_action_rehash"
    )
    stored_action_input_control = _p2_stored_action_input_control(
        stored_action_tamper,
        db_path=output / "continuity.sqlite3",
        recovery_recomputed=[
            recovery.recovered for recovery in runs["recovered"].values()
        ],
    )
    replay_value = {
        "recomputed_from_serialized_state_and_ordered_commands": all(
            recovery.recovered for recovery in runs["recovered"].values()
        ),
        "stored_action_used_as_input": stored_action_input_control[
            "stored_action_used_as_input"
        ],
        "run_count": len(runs["recovered"]),
        "all_terminal_states_match": all(
            engine.state_hash(recovery.state)
            == engine.state_hash(runs["expected_states"][run_id])
            for run_id, recovery in runs["recovered"].items()
        ),
        "tamper_controls_passed": all(
            control["control_available"] and control["failed_closed"] for control in controls
        ),
    }
    replay_report = {
        "schema_version": "ego.v2.p2.replay_report.v1",
        **replay_value,
        "stored_action_input_control": stored_action_input_control,
        "tamper_controls": controls,
        "metric": _p2_metric(
            name="p2_replay_report",
            value=replay_value,
            inputs=inputs,
            ids={"run_ids": runs["run_ids"]},
            rule="fresh_sqlite_recompute_from_initial_state_plus_commands_and_all_tamper_controls_fail_closed",
        ),
    }

    live_run_families = {
        "train": list(runs["train_runs"].values()),
        "candidate": list(runs["candidate_runs"].values()),
        "from_scratch": list(runs["from_scratch_runs"].values()),
        "counterfactual": list(runs["counterfactual_runs"].values()),
    }
    live_scans_by_family = {
        family: [
            scan_policy_projection(result.trace["policy_projection"])
            for run in family_runs
            for result in run["results"]
        ]
        for family, family_runs in live_run_families.items()
    }
    live_scans = [
        scan for family_scans in live_scans_by_family.values() for scan in family_scans
    ]
    positive_controls: dict[str, Any] = {}
    clean_projection = runs["train_runs"][int(config["train_world_seeds"][0])]["results"][0].trace["policy_projection"]
    p2_positive = {
        "private_regime": {"hidden_regime": "site_a_high"},
        "oracle_action": {"correct_action": "forage"},
        "future_outcome": {"future_outcome": 1.0},
        "layout_seed_alias": {"world_seed": 42},
    }
    for control_id, injected in p2_positive.items():
        payload = deepcopy(clean_projection)
        payload["non_memory"]["observation"]["p2_positive_control"] = injected
        scan = scan_policy_projection(payload)
        positive_controls[control_id] = {
            "offenders": scan["offenders"],
            "fired": any(item["reason"] == "forbidden_key_or_alias" for item in scan["offenders"]),
        }
    live_offender_count = sum(len(scan["offenders"]) for scan in live_scans)
    leakage_value = {
        "scan_scope": "direct_forbidden_key_or_alias_scan_only__not_distributional_leakage_resistance",
        "live_offender_count": live_offender_count,
        "positive_controls_fired": all(item["fired"] for item in positive_controls.values()),
        "positive_control_count": len(positive_controls),
        "direct_forbidden_key_or_alias_scan_clean": live_offender_count == 0,
    }
    leakage_report = {
        "schema_version": "ego.v2.p2.leakage_report.v1",
        **leakage_value,
        "live_scan_count": len(live_scans),
        "live_scan_count_by_family": {
            family: len(scans) for family, scans in live_scans_by_family.items()
        },
        "positive_controls": positive_controls,
        "metric": _p2_metric(
            name="p2_leakage_report",
            value=leakage_value,
            inputs=inputs,
            ids={"train_world_seeds": config["train_world_seeds"], "heldout_context_ids": list(contexts)},
            rule="all_live_policy_projections_clean_and_all_four_alias_positive_controls_fire",
        ),
    }

    topology_contrast = _p2_same_schedule_topology_contrast(config)
    topology_contrast["metric"] = _p2_metric(
        name="p2_same_schedule_topology_contrast",
        value=deepcopy(topology_contrast),
        inputs=inputs,
        ids={
            "world_seed": topology_contrast["world_seed"],
            "policy_seed": topology_contrast["policy_seed"],
            "layout_ids": topology_contrast["layout_ids"],
            "event_schedule_id": topology_contrast["event_schedule_id"],
        },
        rule="same_seed_same_schedule_three_layout_path_and_candidate_score_surface_contrast",
    )

    curve_directional = all(
        curve["matched_slot_count"] >= int(config["minimum_matched_context_action_slots"])
        and curve["bounded_error_reduction_observed"]
        for curve in train_curves.values()
    )
    coverage_sufficient = all(
        row["candidate"]["site_visit_count"]
        >= int(config["minimum_site_visits_per_context_for_directional_claim"])
        for row in heldout_rows
    )
    threshold_evaluations = {
        "minimum_matched_context_action_slots": {
            "producer_function": "verify_ego_life_kernel_v2_microworld.p2_curve_directional_threshold",
            "threshold": int(config["minimum_matched_context_action_slots"]),
            "observed_by_train_seed": {
                seed: int(curve["matched_slot_count"])
                for seed, curve in train_curves.items()
            },
            "predicate_result": curve_directional,
        },
        "minimum_site_visits_per_context_for_directional_claim": {
            "producer_function": "verify_ego_life_kernel_v2_microworld.p2_coverage_threshold",
            "threshold": int(
                config["minimum_site_visits_per_context_for_directional_claim"]
            ),
            "observed_by_arm": [
                {
                    "train_world_seed": int(row["train_world_seed"]),
                    "context_id": str(row["context"]["context_id"]),
                    "site_visit_count": int(row["candidate"]["site_visit_count"]),
                }
                for row in heldout_rows
            ],
            "predicate_result": coverage_sufficient,
        },
    }
    exact_lookup_provenance = [
        item
        for row in baseline_rows
        if row["control_id"] == "exact_public_history_lookup"
        for item in row["lookup_provenance"]
    ]
    exact_public_history_nonempty_match_count = sum(
        int(item["matched_prefix_length"]) > 0
        for item in exact_lookup_provenance
    )
    any_control_equivalence = any(row["control_equivalent"] for row in baseline_rows)
    claim_blockers: list[str] = []
    if not curve_directional:
        claim_blockers.append("bounded_error_curve_not_directional_for_both_frozen_train_seeds")
    if not coverage_sufficient:
        claim_blockers.append("heldout_site_coverage_below_frozen_minimum")
    if any_control_equivalence:
        claim_blockers.append("equal_access_control_equivalence")
    counterfactual_effect_counts = {
        str(name): {
            "arm_count": sum(row["counterfactual"] == name for row in counterfactual_rows),
            "zero_effect_arm_count": sum(
                row["counterfactual"] == name
                and not row["effect"]["exact_action_sequence_changed"]
                and row["effect"]["task_outcome_delta"] == 0.0
                for row in counterfactual_rows
            ),
        }
        for name in config["counterfactuals"]
    }
    inert_names = sorted(
        name
        for name, counts in counterfactual_effect_counts.items()
        if counts["arm_count"] > 0
        and counts["zero_effect_arm_count"] == counts["arm_count"]
    )
    if inert_names:
        claim_blockers.append("fully_inert_counterfactuals:" + ",".join(inert_names))

    actual_usage_ledger = build_p2_actual_usage_ledger(
        runs=runs,
        train_curves=train_curves,
        train_summaries=train_summaries,
        baseline_rows=baseline_rows,
        counterfactual_rows=counterfactual_rows,
        threshold_evaluations=threshold_evaluations,
        config_hash_before_execution=config_hash_before_execution,
        config_hash_after_evidence=_canonical_hash(config),
    )
    config_binding = bind_p2_frozen_config(config, actual_usage_ledger)

    blocking_failures = list(config_binding["blocking_failures"])
    if not update_equations_valid:
        blocking_failures.append("bounded_prediction_error_update_equation_mismatch")
    if not frozen_model_memory_preserved:
        blocking_failures.append("freeze_updates_changed_adaptive_bytes")
    if not consolidation_rebuilt or not consolidation_idempotent:
        blocking_failures.append("consolidation_not_rebuildable_or_idempotent")
    if (
        not replay_value["recomputed_from_serialized_state_and_ordered_commands"]
        or not replay_value["all_terminal_states_match"]
        or not replay_value["tamper_controls_passed"]
        or replay_value["stored_action_used_as_input"] is not False
    ):
        blocking_failures.append("replay_or_tamper_control_failed")
    if leakage_value["live_offender_count"] or not leakage_value["positive_controls_fired"]:
        blocking_failures.append("policy_leakage_or_positive_control_failure")
    if not baseline_independence_control["candidate_reducer_disabled_compatible"]:
        blocking_failures.append("independent_baseline_called_candidate_reducer_or_scorer")
    if exact_public_history_nonempty_match_count == 0:
        blocking_failures.append("exact_public_history_lookup_no_nonempty_match")
    if not product_seed_provenance["valid"]:
        blocking_failures.append("product_trigger_seed_provenance_mismatch")
    if topology_contrast["score_surfaces_all_identical"]:
        blocking_failures.append("same_schedule_three_layout_score_surfaces_identical")
    if set(context["layout_id"] for context in contexts.values()) != set(config["heldout_layout_ids"]):
        blocking_failures.append("heldout_layout_registry_not_fully_used")

    physical_root_scan = scan_physical_output_root(
        {
            "config": config,
            "inputs": inputs,
            "config_binding": config_binding,
            "train_curves": train_curves,
            "train_summaries": train_summaries,
            "heldout_rows": heldout_rows,
            "baseline_rows": baseline_rows,
            "counterfactual_rows": counterfactual_rows,
            "replay_value": replay_value,
            "replay_controls": controls,
            "leakage_value": leakage_value,
            "leakage_positive_controls": positive_controls,
            "baseline_independence_control": baseline_independence_control,
            "topology_contrast": topology_contrast,
            "threshold_evaluations": threshold_evaluations,
            "product_outputs": runs["product_outputs"],
            "product_seed_provenance": product_seed_provenance,
        },
        output,
    )
    if not physical_root_scan["physical_output_root_absent"]:
        blocking_failures.append("physical_output_root_leaked_into_artifact")
    blocking_failures = sorted(set(blocking_failures))
    leakage_report["physical_output_root_scan"] = physical_root_scan

    learning_report = {
        "schema_version": "ego.v2.p2.learning_report.v1",
        "result_vocabulary": "bounded_update_response_and_heldout_comparison_only",
        "forbidden_success_labels": ["bounded_online_learning_success", "generalization_or_transfer"],
        "frozen_config": deepcopy(config),
        "frozen_config_binding": config_binding,
        "train_curves": train_curves,
        "train_summaries": train_summaries,
        "heldout_full_cross_product": heldout_rows,
        "counterfactuals": counterfactual_rows,
        "same_schedule_three_layout_topology_contrast": topology_contrast,
        "threshold_evaluations": threshold_evaluations,
        "bounded_update_controls": {
            "update_equations_valid": update_equations_valid,
            "freeze_adaptive_bytes_preserved": frozen_model_memory_preserved,
            "consolidation_rebuilt_from_lineage": consolidation_rebuilt,
            "consolidation_idempotent": consolidation_idempotent,
        },
        "metric": _p2_metric(
            name="p2_learning_report",
            value={
                "curve_directional_both_seeds": curve_directional,
                "coverage_sufficient": coverage_sufficient,
                "control_equivalent": any_control_equivalence,
                "blocking_failures": blocking_failures,
            },
            inputs=inputs,
            ids={"train_world_seeds": config["train_world_seeds"], "heldout_context_ids": list(contexts), "checkpoints": config["learning_checkpoints"]},
            rule="frozen_two_seed_episode_curve_plus_full_train_by_heldout_cross_product_without_retuning",
        ),
    }
    baseline_report = {
        "schema_version": "ego.v2.p2.baseline_comparison.v1",
        "access_contract": "public_observation_layout_label_free_action_paths_legal_actions_equal_access_train_history_and_own_heldout_prefix_only",
        "exact_public_history_access_choice": (
            "layout_invariant_equal_access_public_event_cue_action_outcome_"
            "longest_query_suffix_to_training_episode_prefix"
        ),
        "exact_public_history_nonempty_match_count": (
            exact_public_history_nonempty_match_count
        ),
        "exact_public_history_lookup_sufficiently_exercised": (
            exact_public_history_nonempty_match_count > 0
        ),
        "candidate_reducer_disabled_compatible": baseline_independence_control[
            "candidate_reducer_disabled_compatible"
        ],
        "independence_control": baseline_independence_control,
        "invocation_count": len(baseline_rows),
        "rows": baseline_rows,
        "any_equal_access_control_equivalent": any_control_equivalence,
        "metric": _p2_metric(
            name="p2_baseline_comparison",
            value={
                "invocation_count": len(baseline_rows),
                "any_control_equivalence": any_control_equivalence,
                "exact_public_history_nonempty_match_count": (
                    exact_public_history_nonempty_match_count
                ),
                "all_baseline_arms_candidate_independent": (
                    baseline_independence_control[
                        "candidate_reducer_disabled_compatible"
                    ]
                ),
            },
            inputs=inputs,
            ids={"controls": config["independent_controls"], "heldout_arm_count": len(heldout_rows)},
            rule=str(config["equivalence_rule"]),
        ),
    }
    ablation_report = {
        "schema_version": "ego.v2.p2.ablation_report.v1",
        "candidate_ablation": config["candidate_ablation"],
        "counterfactual_rows": counterfactual_rows,
        "fully_inert_counterfactuals": inert_names,
        "counterfactual_effect_counts": counterfactual_effect_counts,
        "source_deletion_reran_every_heldout_arm": sum(row["counterfactual"] == "source_memory_deletion" for row in counterfactual_rows) == len(heldout_rows),
        "metric": _p2_metric(
            name="p2_ablation_report",
            value={"row_count": len(counterfactual_rows), "fully_inert_counterfactuals": inert_names, "effect_counts": counterfactual_effect_counts},
            inputs=inputs,
            ids={"counterfactuals": config["counterfactuals"], "heldout_arm_count": len(heldout_rows)},
            rule="each_frozen_counterfactual_rerun_on_every_train_by_heldout_arm",
        ),
    }
    headroom_report = {
        "schema_version": "ego.v2.p2.headroom_report.v1",
        "bounded_error_curve_directional_both_seeds": curve_directional,
        "heldout_coverage_sufficient": coverage_sufficient,
        "equal_access_control_equivalence": any_control_equivalence,
        "same_schedule_three_layout_score_surfaces_identical": topology_contrast[
            "score_surfaces_all_identical"
        ],
        "same_schedule_three_layout_selected_actions_equal": topology_contrast[
            "selected_action_sequences_all_equal"
        ],
        "same_schedule_three_layout_outcomes_equal": topology_contrast[
            "outcome_sequences_all_equal"
        ],
        "interpretation": "bounded_negative_or_control_equivalent" if claim_blockers else "bounded_comparison_observed_without_authorized_success_label",
        "metric": _p2_metric(
            name="p2_headroom_report",
            value={"curve_directional": curve_directional, "coverage_sufficient": coverage_sufficient, "control_equivalence": any_control_equivalence},
            inputs=inputs,
            ids={"train_world_seeds": config["train_world_seeds"], "heldout_context_ids": list(contexts)},
            rule="all_frozen_directional_requirements_conjoined_then_collided_with_equal_access_controls",
        ),
    }
    collision_record = {
        "schema_version": "ego.v2.p2.collision_record.v1",
        "strongest_baseline_family": "equal_access_public_history_lookup_count_transition_graph_or_episodic_control",
        "control_equivalence_observed": any_control_equivalence,
        "disposition": "retain_product_engineering_and_bound_adaptation_claim_to_negative_or_equivalent_comparison" if any_control_equivalence else "retain_only_frozen_context_metrics_without_success_label",
        "metric": _p2_metric(
            name="p2_collision_record",
            value={"control_equivalence": any_control_equivalence, "equivalent_row_count": sum(row["control_equivalent"] for row in baseline_rows)},
            inputs=inputs,
            ids={"controls": config["independent_controls"], "heldout_arm_count": len(heldout_rows)},
            rule=str(config["equivalence_rule"]),
        ),
    }

    product_receipt = {
        "schema_version": "ego.v2.p2.product_trigger_receipt.v1",
        "trigger_source": "terminal_event_then_terminal_run",
        "statuses": [item["status"] for item in runs["product_outputs"]],
        "run_id": product_seed_provenance["recovered_run_id"],
        "command_count": product_recovery.command_count,
        "fresh_process_recomputed": product_recovery.recovered,
        "policy_seed": product_seed_provenance["recovered_policy_seed"],
        "world_seed": product_seed_provenance["recorded_world_seed"],
        "layout_id": product_seed_provenance["recovered_layout_id"],
        "recorded_controller_inputs_hash": product_seed_provenance[
            "recorded_controller_inputs_hash"
        ],
        "seed_provenance": product_seed_provenance,
        "rendered_snapshot_hash": runs["product_snapshot_hash"],
        "explicit_local_launch_only": True,
        "switches": deepcopy(SWITCHES),
        "metric": _p2_metric(
            name="p2_product_trigger_receipt",
            value={
                "command_count": product_recovery.command_count,
                "fresh_recomputed": product_recovery.recovered,
                "seed_provenance_valid": product_seed_provenance["valid"],
                "recorded_controller_inputs_hash": product_seed_provenance[
                    "recorded_controller_inputs_hash"
                ],
            },
            inputs=inputs,
            ids={
                "run_id": product_seed_provenance["recovered_run_id"],
                "policy_seed": product_seed_provenance["recovered_policy_seed"],
                "world_seed": product_seed_provenance["recorded_world_seed"],
                "layout_id": product_seed_provenance["recovered_layout_id"],
            },
            rule="explicit_terminal_commands_committed_then_fresh_sqlite_recomputed",
        ),
    }

    result = {
        "schema_version": "ego.v2.p2.result.v1",
        "task_id": TASK_ID,
        "phase": "p2_bounded_adaptation_and_consolidation",
        "verdict": "implementation_control_failure" if blocking_failures else ("bounded_update_and_heldout_comparison_measured_with_control_equivalence" if any_control_equivalence else "bounded_update_and_heldout_comparison_measured"),
        "implementation_controls_passed": not blocking_failures,
        "blocking_failures": blocking_failures,
        "claim_blockers": claim_blockers,
        "claim_ceiling": P2_CLAIM_CEILING,
        "switches": deepcopy(SWITCHES),
        "frozen_config_hash": _canonical_hash(config),
        "actual_usage_ledger_hash": config_binding["actual_usage_ledger_hash"],
        "input_artifacts": inputs,
        "summary_metric": _p2_metric(
            name="aggregate_p2_result",
            value={"implementation_controls_passed": not blocking_failures, "claim_blockers": claim_blockers, "run_count": len(runs["run_ids"])},
            inputs=inputs,
            ids={"train_world_seeds": config["train_world_seeds"], "heldout_context_ids": list(contexts), "run_ids": runs["run_ids"]},
            rule="all_implementation_controls_must_pass_while_negative_claim_blockers_are_preserved",
        ),
    }
    failure_manifest = {
        "schema_version": "ego.v2.p2.failure_manifest.v1",
        "implementation_failures": blocking_failures,
        "claim_blockers": claim_blockers,
        "status": "fail" if blocking_failures else ("implementation_controls_passed_with_bounded_claim_blockers" if claim_blockers else "implementation_controls_passed"),
        "metric": _p2_metric(
            name="p2_failure_manifest",
            value={"implementation_failures": blocking_failures, "claim_blockers": claim_blockers},
            inputs=inputs,
            ids={"run_id": P2_RUN_ID},
            rule="union_computed_implementation_failures_separate_from_nonblocking_claim_limits",
        ),
    }

    payloads = {
        "product_trigger_receipt.json": product_receipt,
        "headroom_report.json": headroom_report,
        "collision_record.json": collision_record,
        "baseline_comparison.json": baseline_report,
        "ablation_report.json": ablation_report,
        "learning_report.json": learning_report,
        "replay_report.json": replay_report,
        "leakage_report.json": leakage_report,
        "failure_manifest.json": failure_manifest,
        "result.json": result,
    }
    final_physical_root_scan = scan_physical_output_root(payloads, output)
    if (
        not final_physical_root_scan["physical_output_root_absent"]
        and "physical_output_root_leaked_into_artifact" not in blocking_failures
    ):
        # Rebuild every blocking-dependent view from the augmented blocker set.
        blocking_failures = sorted(
            set(blocking_failures + ["physical_output_root_leaked_into_artifact"])
        )
        learning_metric_value = deepcopy(learning_report["metric"]["value"])
        learning_metric_value["blocking_failures"] = blocking_failures
        learning_report["metric"] = _p2_metric(
            name="p2_learning_report",
            value=learning_metric_value,
            inputs=inputs,
            ids={
                "train_world_seeds": config["train_world_seeds"],
                "heldout_context_ids": list(contexts),
                "checkpoints": config["learning_checkpoints"],
            },
            rule="frozen_two_seed_episode_curve_plus_full_train_by_heldout_cross_product_without_retuning",
        )
        result["blocking_failures"] = blocking_failures
        result["implementation_controls_passed"] = False
        result["verdict"] = "implementation_control_failure"
        result["summary_metric"] = _p2_metric(
            name="aggregate_p2_result",
            value={
                "implementation_controls_passed": False,
                "claim_blockers": claim_blockers,
                "run_count": len(runs["run_ids"]),
            },
            inputs=inputs,
            ids={
                "train_world_seeds": config["train_world_seeds"],
                "heldout_context_ids": list(contexts),
                "run_ids": runs["run_ids"],
            },
            rule="all_implementation_controls_must_pass_while_negative_claim_blockers_are_preserved",
        )
        failure_manifest["implementation_failures"] = blocking_failures
        failure_manifest["status"] = "fail"
        failure_manifest["metric"] = _p2_metric(
            name="p2_failure_manifest",
            value={
                "implementation_failures": blocking_failures,
                "claim_blockers": claim_blockers,
            },
            inputs=inputs,
            ids={"run_id": P2_RUN_ID},
            rule="union_computed_implementation_failures_separate_from_nonblocking_claim_limits",
        )
    if not final_physical_root_scan["physical_output_root_absent"]:
        payloads = _redact_physical_output_root(payloads, output)
        result = payloads["result.json"]
    for name, payload in payloads.items():
        _write_json(output / name, payload)
    (output / "claim_ceiling.txt").write_text(P2_CLAIM_CEILING + "\n", encoding="utf-8", newline="\n")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("p1", "p2"), default="p1")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = run_p1_verification(args.output) if args.phase == "p1" else run_p2_verification(args.output)
    print(_canonical_json(result))
    return 0 if not result["blocking_failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
