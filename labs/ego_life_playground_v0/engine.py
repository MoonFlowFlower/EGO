"""Deterministic product-clock engine for the visible life-proxy playground.

This module intentionally exposes its simple baseline: a deficit scorer, a
hard-coded toy outcome table, a context/action tabular EMA, and structured
memory bias.  It is an inspectable product surface, not mechanism evidence.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


STATE_KEYS = ("energy", "safety", "connection", "stimulation")
ACTIONS = ("approach", "explore", "forage", "rest", "withdraw")
CUES = ("resource", "contact", "novelty", "threat", "quiet")
TARGET_LEVEL = 0.72
EMA_ALPHA = 0.35
CONSOLIDATION_THRESHOLD = 3

DEFAULT_TOGGLES = {
    "memory_on": True,
    "learning_on": True,
    "consolidation_on": True,
}

# Generic priors deliberately under-specify cue-specific outcomes so that the
# disclosed online table has a real prediction error to update from.
ACTION_PRIORS: dict[str, dict[str, float]] = {
    "forage": {"energy": 0.12, "safety": -0.03, "connection": 0.00, "stimulation": 0.02},
    "rest": {"energy": 0.09, "safety": 0.04, "connection": 0.00, "stimulation": -0.04},
    "approach": {"energy": -0.02, "safety": -0.02, "connection": 0.11, "stimulation": 0.03},
    "explore": {"energy": -0.05, "safety": -0.03, "connection": 0.00, "stimulation": 0.10},
    "withdraw": {"energy": -0.01, "safety": 0.10, "connection": -0.04, "stimulation": -0.03},
}

CUE_BONUSES: dict[str, dict[str, dict[str, float]]] = {
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

ACTION_COSTS = {
    "approach": 0.018,
    "explore": 0.025,
    "forage": 0.020,
    "rest": 0.010,
    "withdraw": 0.015,
}


class EngineInvariantError(ValueError):
    """Raised when a serialized command or state violates the contract."""


@dataclass(frozen=True)
class StepResult:
    next_state: dict[str, Any]
    trace: dict[str, Any]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def compute_code_path_hash() -> str:
    """Bind both behavior rules and the replay/export acceptance producer."""

    source_paths = (Path(__file__), Path(__file__).with_name("store.py"))
    manifest = {
        "schema_version": "ego.life_playground.code_path.v0",
        "files": [
            {
                "path": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in source_paths
        ],
    }
    return canonical_hash(manifest)


def make_run_metadata(run_id: str, seed: int, episode_id: str = "manual-local") -> dict[str, Any]:
    if not run_id:
        raise EngineInvariantError("run_id must be non-empty")
    return {
        "run_id": run_id,
        "seed": int(seed),
        "episode_id": episode_id,
        "producer_function": "ego_life_playground_v0.engine.compute_step",
        "aggregation_rule": "single_step_deterministic_one_step_argmax",
        "code_path_hash": compute_code_path_hash(),
        "science_weight": 0,
    }


def initial_state(organism: Mapping[str, float] | None = None) -> dict[str, Any]:
    values = {
        "energy": 0.45,
        "safety": 0.62,
        "connection": 0.50,
        "stimulation": 0.43,
    }
    if organism is not None:
        values.update({key: float(value) for key, value in organism.items()})
    if set(values) != set(STATE_KEYS):
        raise EngineInvariantError("organism state keys do not match canonical schema")
    return {
        "schema_version": "ego.life_playground.state.v0",
        "step": 0,
        "organism": {key: _clamp(values[key]) for key in STATE_KEYS},
        "model": {},
        "memory": {"episodic": [], "consolidated": []},
        "last_action": None,
        "last_command_hash": None,
        "last_trace_hash": None,
    }


def make_command(
    *,
    sequence: int,
    cue: str,
    toggles: Mapping[str, bool],
    prev_command_hash: str | None,
) -> dict[str, Any]:
    if cue not in CUES:
        raise EngineInvariantError(f"unknown cue: {cue}")
    normalized_toggles = _normalize_toggles(toggles)
    payload: dict[str, Any] = {
        "sequence": int(sequence),
        "cue": cue,
        "toggles": normalized_toggles,
        "prev_command_hash": prev_command_hash,
    }
    payload["command_hash"] = canonical_hash(payload)
    return payload


def verify_command(command: Mapping[str, Any], state: Mapping[str, Any]) -> None:
    allowed = {"sequence", "cue", "toggles", "prev_command_hash", "command_hash"}
    if set(command) != allowed:
        extra = sorted(set(command) - allowed)
        missing = sorted(allowed - set(command))
        raise EngineInvariantError(f"command schema mismatch: extra={extra}, missing={missing}")
    if int(command["sequence"]) != int(state["step"]) + 1:
        raise EngineInvariantError("command sequence is not the next state sequence")
    if command["prev_command_hash"] != state.get("last_command_hash"):
        raise EngineInvariantError("command chain mismatch")
    if command["cue"] not in CUES:
        raise EngineInvariantError("command cue is not canonical")
    _normalize_toggles(command["toggles"])
    unsigned = {key: command[key] for key in allowed if key != "command_hash"}
    if canonical_hash(unsigned) != command["command_hash"]:
        raise EngineInvariantError("command hash mismatch")


def state_hash(state: Mapping[str, Any]) -> str:
    """Hash causal state while excluding the separately chained trace pointer."""

    causal_state = deepcopy(dict(state))
    causal_state.pop("last_trace_hash", None)
    return canonical_hash(causal_state)


def compute_trace_hash(trace: Mapping[str, Any]) -> str:
    unsigned = {key: value for key, value in trace.items() if key != "trace_hash"}
    return canonical_hash(unsigned)


def compute_step(
    state: Mapping[str, Any], command: Mapping[str, Any], run_meta: Mapping[str, Any]
) -> StepResult:
    """Compute one complete step for both live operation and recovery."""

    current_code_hash = compute_code_path_hash()
    if run_meta.get("code_path_hash") != current_code_hash:
        raise EngineInvariantError("engine code-path hash differs from frozen run metadata")
    verify_command(command, state)

    before = deepcopy(dict(state))
    before_hash = state_hash(before)
    cue = str(command["cue"])
    toggles = _normalize_toggles(command["toggles"])
    goals = propose_goals(before["organism"])
    dominant_goal = goals[0]["state_variable"]
    context_key = f"{cue}|{dominant_goal}"

    candidates = [
        _score_candidate(
            state=before,
            cue=cue,
            context_key=context_key,
            action=action,
            sequence=int(command["sequence"]),
            seed=int(run_meta["seed"]),
            use_memory=toggles["memory_on"],
        )
        for action in ACTIONS
    ]
    candidates.sort(key=lambda item: item["action"])
    selected = max(candidates, key=lambda item: (item["total_score"], item["tie_break"]))
    selected_action = selected["action"]
    predicted_delta = deepcopy(selected["predicted_delta"])
    actual_delta = _actual_delta(cue, selected_action)
    prediction_error = {
        key: _round(actual_delta[key] - predicted_delta[key]) for key in STATE_KEYS
    }

    next_state = deepcopy(before)
    next_state["step"] = int(command["sequence"])
    next_state["organism"] = _apply_delta(before["organism"], actual_delta)
    next_state["last_action"] = selected_action
    next_state["last_command_hash"] = command["command_hash"]

    model_update = _update_model(
        next_state,
        context_key=context_key,
        action=selected_action,
        actual_delta=actual_delta,
        apply_update=toggles["learning_on"],
    )
    memory_update = _update_memory(
        next_state,
        before_organism=before["organism"],
        after_organism=next_state["organism"],
        cue=cue,
        dominant_goal=dominant_goal,
        action=selected_action,
        sequence=int(command["sequence"]),
        command_hash=str(command["command_hash"]),
        use_memory=toggles["memory_on"],
        run_consolidation=toggles["consolidation_on"],
    )

    after_hash = state_hash(next_state)
    trace: dict[str, Any] = {
        "schema_version": "ego.life_playground.trace.v0",
        "producer_function": "ego_life_playground_v0.engine.compute_step",
        "input_artifacts": [
            f"run:{run_meta['run_id']}",
            f"command:{command['command_hash']}",
        ],
        "run_id": run_meta["run_id"],
        "seed": int(run_meta["seed"]),
        "episode_id": run_meta["episode_id"],
        "aggregation_rule": run_meta["aggregation_rule"],
        "sequence": int(command["sequence"]),
        "command": deepcopy(dict(command)),
        "toggles": toggles,
        "state_before_hash": before_hash,
        "state_after_hash": after_hash,
        "context_key": context_key,
        "goals": goals,
        "candidates": candidates,
        "selected_action": selected_action,
        "prediction": predicted_delta,
        "model_ref": selected["model_ref"],
        "memory_refs": selected["memory_refs"],
        "actual_delta": actual_delta,
        "prediction_error": prediction_error,
        "model_update": model_update,
        "memory_update": memory_update,
        "consolidation_refs": memory_update["consolidation_refs"],
        "code_path_hash": current_code_hash,
        "prev_trace_hash": before.get("last_trace_hash"),
    }
    trace["trace_hash"] = compute_trace_hash(trace)
    next_state["last_trace_hash"] = trace["trace_hash"]
    return StepResult(next_state=next_state, trace=trace)


def propose_goals(organism: Mapping[str, float]) -> list[dict[str, Any]]:
    goals = [
        {
            "state_variable": key,
            "current": _round(float(organism[key])),
            "target": TARGET_LEVEL,
            "deficit": _round(max(0.0, TARGET_LEVEL - float(organism[key]))),
        }
        for key in STATE_KEYS
    ]
    goals.sort(key=lambda item: (-item["deficit"], item["state_variable"]))
    for priority, goal in enumerate(goals, start=1):
        goal["priority"] = priority
    return goals


def _score_candidate(
    *,
    state: Mapping[str, Any],
    cue: str,
    context_key: str,
    action: str,
    sequence: int,
    seed: int,
    use_memory: bool,
) -> dict[str, Any]:
    model_entry = state["model"].get(context_key, {}).get(action)
    if model_entry and int(model_entry["count"]) > 0:
        predicted = {key: float(model_entry["ema_delta"][key]) for key in STATE_KEYS}
        model_ref = {
            "source": "tabular_ema",
            "context_key": context_key,
            "action": action,
            "count": int(model_entry["count"]),
        }
    else:
        predicted = _prior_prediction(cue, action)
        model_ref = {
            "source": "hardcoded_prior",
            "context_key": context_key,
            "action": action,
            "count": 0,
        }
    predicted_after = _apply_delta(state["organism"], predicted)
    deficit_reduction = _round(
        _total_deficit(state["organism"]) - _total_deficit(predicted_after)
    )
    memory_bias, memory_refs = _memory_bias(
        state["memory"], cue=cue, dominant_goal=context_key.split("|", 1)[1], action=action
    ) if use_memory else (0.0, [])
    untried_bonus = 0.025 if model_ref["count"] == 0 else 0.0
    tie_break = _deterministic_tie(seed, sequence, context_key, action)
    total_score = _round(
        deficit_reduction + memory_bias + untried_bonus - ACTION_COSTS[action] + tie_break,
        digits=9,
    )
    return {
        "action": action,
        "predicted_delta": {key: _round(predicted[key]) for key in STATE_KEYS},
        "deficit_reduction": deficit_reduction,
        "memory_bias": _round(memory_bias),
        "untried_bonus": untried_bonus,
        "action_cost": ACTION_COSTS[action],
        "tie_break": tie_break,
        "total_score": total_score,
        "model_ref": model_ref,
        "memory_refs": memory_refs,
    }


def _prior_prediction(cue: str, action: str) -> dict[str, float]:
    prior = dict(ACTION_PRIORS[action])
    for key, bonus in CUE_BONUSES.get(cue, {}).get(action, {}).items():
        prior[key] += 0.5 * bonus
    return {key: _round(prior[key]) for key in STATE_KEYS}


def _actual_delta(cue: str, action: str) -> dict[str, float]:
    delta = dict(ACTION_PRIORS[action])
    for key, bonus in CUE_BONUSES.get(cue, {}).get(action, {}).items():
        delta[key] += bonus
    return {key: _round(delta[key]) for key in STATE_KEYS}


def _update_model(
    state: dict[str, Any],
    *,
    context_key: str,
    action: str,
    actual_delta: Mapping[str, float],
    apply_update: bool,
) -> dict[str, Any]:
    if not apply_update:
        return {"applied": False, "reason": "learning_disabled", "context_key": context_key, "action": action}
    context = state["model"].setdefault(context_key, {})
    previous = context.get(action)
    if previous is None:
        new_delta = {key: _round(float(actual_delta[key])) for key in STATE_KEYS}
        previous_count = 0
    else:
        previous_count = int(previous["count"])
        new_delta = {
            key: _round(
                (1.0 - EMA_ALPHA) * float(previous["ema_delta"][key])
                + EMA_ALPHA * float(actual_delta[key])
            )
            for key in STATE_KEYS
        }
    context[action] = {"count": previous_count + 1, "ema_delta": new_delta}
    return {
        "applied": True,
        "alpha": EMA_ALPHA,
        "context_key": context_key,
        "action": action,
        "previous_count": previous_count,
        "new_count": previous_count + 1,
        "ema_delta": new_delta,
    }


def _update_memory(
    state: dict[str, Any],
    *,
    before_organism: Mapping[str, float],
    after_organism: Mapping[str, float],
    cue: str,
    dominant_goal: str,
    action: str,
    sequence: int,
    command_hash: str,
    use_memory: bool,
    run_consolidation: bool,
) -> dict[str, Any]:
    if not use_memory:
        return {
            "episodic_write": None,
            "consolidation_applied": False,
            "consolidation_refs": [],
            "reason": "memory_disabled",
        }
    utility = _round(_total_deficit(before_organism) - _total_deficit(after_organism))
    episode_id = canonical_hash(
        {
            "kind": "episode",
            "sequence": sequence,
            "command_hash": command_hash,
            "cue": cue,
            "goal": dominant_goal,
            "action": action,
        }
    )[:20]
    episode = {
        "memory_id": f"ep-{episode_id}",
        "kind": "episodic",
        "cue": cue,
        "dominant_goal": dominant_goal,
        "action": action,
        "utility": utility,
        "sequence": sequence,
        "provenance": {"command_hash": command_hash},
    }
    state["memory"]["episodic"].append(episode)
    if not run_consolidation:
        return {
            "episodic_write": episode["memory_id"],
            "consolidation_applied": False,
            "consolidation_refs": [],
            "reason": "consolidation_disabled",
        }
    matching = [
        entry
        for entry in state["memory"]["episodic"]
        if entry["cue"] == cue
        and entry["dominant_goal"] == dominant_goal
        and entry["action"] == action
    ]
    if len(matching) < CONSOLIDATION_THRESHOLD:
        return {
            "episodic_write": episode["memory_id"],
            "consolidation_applied": False,
            "consolidation_refs": [],
            "reason": "threshold_not_met",
        }
    provenance_ids = [entry["memory_id"] for entry in matching]
    strength = _round(sum(float(entry["utility"]) for entry in matching) / len(matching))
    key = f"{cue}|{dominant_goal}|{action}"
    consolidated_id = f"con-{canonical_hash({'key': key, 'provenance': provenance_ids})[:20]}"
    consolidated = {
        "memory_id": consolidated_id,
        "kind": "consolidated",
        "key": key,
        "cue": cue,
        "dominant_goal": dominant_goal,
        "action": action,
        "strength": strength,
        "provenance_ids": provenance_ids,
        "episode_count": len(matching),
    }
    existing = state["memory"]["consolidated"]
    state["memory"]["consolidated"] = [item for item in existing if item["key"] != key]
    state["memory"]["consolidated"].append(consolidated)
    state["memory"]["consolidated"].sort(key=lambda item: item["key"])
    return {
        "episodic_write": episode["memory_id"],
        "consolidation_applied": True,
        "consolidation_refs": provenance_ids,
        "consolidated_write": consolidated_id,
        "reason": "threshold_met",
    }


def _memory_bias(
    memory: Mapping[str, Any], *, cue: str, dominant_goal: str, action: str
) -> tuple[float, list[str]]:
    bias = 0.0
    refs: list[str] = []
    for entry in memory.get("episodic", []):
        if entry["cue"] == cue and entry["dominant_goal"] == dominant_goal and entry["action"] == action:
            bias += 0.20 * float(entry["utility"])
            refs.append(entry["memory_id"])
    for entry in memory.get("consolidated", []):
        if entry["cue"] == cue and entry["dominant_goal"] == dominant_goal and entry["action"] == action:
            bias += 0.65 * float(entry["strength"])
            refs.append(entry["memory_id"])
    return max(-0.5, min(0.5, bias)), sorted(refs)


def _normalize_toggles(toggles: Mapping[str, bool]) -> dict[str, bool]:
    if set(toggles) != set(DEFAULT_TOGGLES):
        raise EngineInvariantError("toggle keys do not match canonical schema")
    return {key: bool(toggles[key]) for key in sorted(DEFAULT_TOGGLES)}


def _deterministic_tie(seed: int, sequence: int, context_key: str, action: str) -> float:
    digest = hashlib.sha256(
        f"{seed}|{sequence}|{context_key}|{action}".encode("utf-8")
    ).digest()
    integer = int.from_bytes(digest[:8], "big")
    return _round((integer / float(2**64 - 1)) * 1e-6, digits=12)


def _apply_delta(organism: Mapping[str, float], delta: Mapping[str, float]) -> dict[str, float]:
    return {key: _round(_clamp(float(organism[key]) + float(delta[key]))) for key in STATE_KEYS}


def _total_deficit(organism: Mapping[str, float]) -> float:
    return sum(max(0.0, TARGET_LEVEL - float(organism[key])) for key in STATE_KEYS)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _round(value: float, *, digits: int = 6) -> float:
    return round(float(value), digits)
