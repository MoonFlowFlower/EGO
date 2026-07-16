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
    "runtime_authority": "none",
    "science_weight": 0,
    "remote_anchor": False,
    "proactive_action_enabled": False,
    "background_dispatch": False,
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
_INPUT_ARTIFACT_LOGICAL_IDS = {
    GENERATED_DB_LOGICAL_ID,
    GENERATED_TRACE_LOGICAL_ID,
    TASK_SCOPE_LOGICAL_ID,
}


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


def baseline_exact_public_history_lookup(access: Mapping[str, Any]) -> str:
    query = list(access.get("query_history_prefix", []))
    for episode in access.get("reference_episodes", []):
        records = list(episode)
        if len(records) > len(query) and _canonical_json(records[: len(query)]) == _canonical_json(query):
            return _fallback(
                access, str(records[len(query)].get("action_taken", "approach"))
            )
    return _fallback(access, "approach")


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
    if root_keys != {"schema_version", "non_memory", "claim_retrieval"}:
        offenders.append(
            {"path": "/", "category": "schema", "reason": "policy_projection_root_schema_mismatch"}
        )
    non_memory = payload.get("non_memory")
    if isinstance(non_memory, Mapping):
        expected = {"schema_version", "observation", "organism", "current_goal", "legal_actions", "model"}
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

    relevant = next(
        event
        for event in state_a["memory"]["claim_events"]
        if event["value"] == canonical_a.trace["selected_action"]
        and float(event["evidence_strength"]) > 0.0
    )
    deleted_memory, deletion_report = claims.delete_sources(
        state_a["memory"], event_ids=[relevant["event_id"]]
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
            persisted_invariance[side] = False
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
    shuffle_value = {
        "status": projection_a["status"],
        "seed": projection_a.get("seed"),
        "configured_seed": PROVENANCE_SHUFFLE_SEED,
        "event_value_multiset_preserved": all(
            bool(item.get("event_value_multiset_preserved")) for item in projections.values()
        ),
        "non_provenance_claim_fields_preserved": all(
            bool(item.get("non_provenance_claim_fields_preserved")) for item in projections.values()
        ),
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
            state["memory"]["claim_events"][0]["evidence_strength"] = 0.25
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
            and bool(pair["deletion_report"]["deleted_event_ids"]),
            pair["deletion_report"]["deleted_event_ids"],
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
    blocking.extend(
        f"required_effect_false:{key}" for key, value in required_effects.items() if not value
    )
    strongest_rate = float(baseline.get("strongest_match_rate", 0.0)) if isinstance(baseline, Mapping) else 0.0
    claim_blockers: list[str] = []
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("p1",), default="p1")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = run_p1_verification(args.output)
    print(_canonical_json(result))
    return 0 if not result["blocking_failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
