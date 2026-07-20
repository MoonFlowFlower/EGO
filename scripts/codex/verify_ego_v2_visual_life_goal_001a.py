#!/usr/bin/env python3
"""Callable evidence producer for EGO-V2-P0-VISUAL-LIFE-CARD-B-001A."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.microworld import policy_observation, verify_world_state
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore
from labs.ego_life_playground_v0.terminal import build_terminal_snapshot
from labs.ego_life_playground_v0.visual_console import build_tk_trace_payload


TASK_ID = "EGO-V2-P0-VISUAL-LIFE-CARD-B-001A"
RUN_ID = "ego-v2-card-b-verify"
POLICY_SEED = 17
CLAIM_CEILING = (
    "Engineering goal-control evidence only: one canonical compute_step path records "
    "goal hysteresis, completion latch, reentry below 0.60, severe override with "
    "energy priority, explore scoring from visual transition counts, equal-access "
    "baseline comparison, ablation reruns, SQLite recovery, and replay hygiene. "
    "This does not establish electronic life, subjectivity, consciousness, emotion, "
    "agency, autonomy, general learning, mechanism validity, or stable user benefit."
)
REQUIRED_ARTIFACTS = {
    "result.json",
    "trace.jsonl",
    "baseline_comparison.json",
    "ablation_report.json",
    "leakage_report.json",
    "replay_report.json",
    "failure_manifest.json",
    "claim_ceiling.txt",
}
CARD_PATH = (
    REPO_ROOT
    / "docs/codex/tasks/EGO-V2-P0-VISUAL-LIFE-CONTRACT-001A/CARD_B_GOAL_HYSTERESIS.md"
)
CONTRACT_PATH = (
    REPO_ROOT
    / "docs/codex/tasks/EGO-V2-P0-VISUAL-LIFE-CONTRACT-001A/PRODUCT_CONTRACT.md"
)
SOURCE_PATHS = [
    REPO_ROOT / "labs/ego_life_playground_v0/controller.py",
    REPO_ROOT / "labs/ego_life_playground_v0/engine.py",
    REPO_ROOT / "labs/ego_life_playground_v0/store.py",
    REPO_ROOT / "labs/ego_life_playground_v0/terminal.py",
    REPO_ROOT / "labs/ego_life_playground_v0/visual_console.py",
    CARD_PATH,
    CONTRACT_PATH,
    Path(__file__),
]
FORBIDDEN_KEY_ALIASES = {
    "semantic_event": {"event", "world_event", "injected_event", "cause", "token_mapping"},
    "absolute_position": {"position", "agent_position", "layout_id", "topology", "map"},
    "seed_or_life_id": {"seed", "world_seed", "life_id", "episode_id", "episode_index"},
    "trace_lineage": {"command_hash", "trace_hash", "prev_trace_hash", "source_command_hash"},
}
FORBIDDEN_VALUE_PATTERNS = {
    "semantic_event": [r"\b(resource_appears|social_signal|novel_object|threat_nearby|quiet_interval)\b"],
    "absolute_position": [r"\[\s*\d+\s*,\s*\d+\s*\]", r"\bp\d+_[a-z0-9_]+_v1\b"],
    "seed_or_life_id": [r"\bepisode-\d{6}-[0-9a-f]{2,64}\b", r"\bseed\b", r"\blife[_ -]?id\b"],
    "trace_lineage": [r"\b[0-9a-f]{64}\b", r"\bcmd(?:_|:|\s)", r"\btrace(?:_|:|\s)"],
}
POSITIVE_CONTROL_PAYLOAD = {
    "world_event": "resource_appears",
    "position": [3, 1],
    "layout_id": "p0_cross_v1",
    "seed": 1701,
    "life_id": "episode-000000-positive",
    "trace_hash": "1" * 64,
    "token_mapping": {"v0": "resource"},
}
ACCEPTANCE_GATE_IDS = [
    "declared_goal_scenarios_observed",
    "live_controller_sqlite_terminal_tk_payload_path",
    "goal_hysteresis_completion_reentry_override_explore",
    "equal_access_baseline_reported",
    "real_ablations_invoked_and_load_bearing",
    "goal_payload_leakage_scan_clean_positive_control_fires",
    "replay_two_fresh_processes_match",
    "replay_tamper_controls_fail_closed",
    "recursive_provenance_present",
]
EVIDENCE_RECORD_TYPE = "evidence_record"
RAW_DATA_RECORD_TYPE = "raw_data"
PROVENANCE_FIELDS = (
    "record_type",
    "producer_function",
    "input_artifacts",
    "run_id",
    "seed_context_episode_ids",
    "aggregation_rule",
    "code_path_hash",
    "engine_code_path_hash",
    "verifier_source_hash",
)
EVIDENCE_SIGNAL_KEYS = frozenset(
    {
        "value",
        "verdict",
        "failed_checks",
        "disposition",
        "positive_control_detected",
        "failed_closed",
        "invoked",
        "matched",
        "fresh_process_match",
        "producer_function",
        "aggregation_rule",
        "input_artifacts",
        "run_id",
        "seed_context_episode_ids",
        "code_path_hash",
        "engine_code_path_hash",
        "verifier_source_hash",
    }
)
LOGICAL_TRACE_PATH = "artifacts/EGO-V2-P0-VISUAL-LIFE-CARD-B-001A/trace.jsonl"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _normalized_path_id(path: Path, *, logical_path: str | None = None) -> str:
    if logical_path is not None:
        return logical_path
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError as exc:
        raise ValueError(f"logical path required for non-repo artifact: {resolved}") from exc


def _file_record(path: Path, *, logical_path: str | None = None) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "path": _normalized_path_id(path, logical_path=logical_path),
        "bytes": len(raw),
        "sha256": _sha256(raw),
    }


def _source_inputs() -> list[dict[str, Any]]:
    return [_file_record(path) for path in SOURCE_PATHS]


def _code_path_hash() -> str:
    return _sha256(
        _canonical_bytes(
            {
                "engine_code_path_hash": engine.compute_code_path_hash(),
                "verifier_source_hash": _file_record(Path(__file__))["sha256"],
            }
        )
    )


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _clean_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def _provenance(
    *,
    producer_function: str,
    input_artifacts: list[Any],
    seed_context_episode_ids: Mapping[str, Any],
    aggregation_rule: str,
    run_id: str = RUN_ID,
) -> dict[str, Any]:
    return {
        "record_type": EVIDENCE_RECORD_TYPE,
        "producer_function": producer_function,
        "input_artifacts": deepcopy(input_artifacts),
        "run_id": run_id,
        "seed_context_episode_ids": deepcopy(dict(seed_context_episode_ids)),
        "aggregation_rule": aggregation_rule,
        "code_path_hash": _code_path_hash(),
        "engine_code_path_hash": engine.compute_code_path_hash(),
        "verifier_source_hash": _file_record(Path(__file__))["sha256"],
    }


def _check_record(
    value: bool,
    *,
    producer_function: str,
    input_artifacts: list[Any],
    seed_context_episode_ids: Mapping[str, Any],
    aggregation_rule: str,
) -> dict[str, Any]:
    return {
        **_provenance(
            producer_function=producer_function,
            input_artifacts=input_artifacts,
            seed_context_episode_ids=seed_context_episode_ids,
            aggregation_rule=aggregation_rule,
        ),
        "value": bool(value),
    }


def _evidence_payload(
    payload: Mapping[str, Any],
    *,
    producer_function: str,
    input_artifacts: list[Any],
    seed_context_episode_ids: Mapping[str, Any],
    aggregation_rule: str,
    run_id: str = RUN_ID,
) -> dict[str, Any]:
    return {
        **_provenance(
            producer_function=producer_function,
            input_artifacts=input_artifacts,
            seed_context_episode_ids=seed_context_episode_ids,
            aggregation_rule=aggregation_rule,
            run_id=run_id,
        ),
        **deepcopy(dict(payload)),
    }


def collect_evidence_records(payload: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            if {
                *PROVENANCE_FIELDS,
            } <= set(value):
                records.append(dict(value))
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    return records


def classify_raw_data(mapping: Mapping[str, Any], **fields: Any) -> dict[str, Any]:
    payload = {"record_type": RAW_DATA_RECORD_TYPE}
    payload.update(deepcopy(dict(mapping)))
    payload.update(deepcopy(fields))
    return payload


def validate_recursive_provenance(payload: Any) -> dict[str, Any]:
    offenders: list[dict[str, Any]] = []
    evidence_records: list[dict[str, Any]] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            record_type = value.get("record_type")
            has_signal = bool(EVIDENCE_SIGNAL_KEYS & set(value))
            has_any_provenance = any(field in value for field in PROVENANCE_FIELDS)
            if record_type == RAW_DATA_RECORD_TYPE:
                raw_signal_keys = sorted(EVIDENCE_SIGNAL_KEYS & set(value))
                raw_provenance_keys = [
                    field
                    for field in PROVENANCE_FIELDS
                    if field != "record_type" and field in value
                ]
                if raw_signal_keys or raw_provenance_keys:
                    offenders.append(
                        {
                            "path": path or "/",
                            "reason": "raw_data_contains_evidence_signal",
                            "signal_keys": raw_signal_keys + raw_provenance_keys,
                        }
                    )
                for key, item in value.items():
                    walk(item, f"{path}/{key}" if path else f"/{key}")
                return
            elif record_type == EVIDENCE_RECORD_TYPE or has_signal or has_any_provenance:
                missing = [field for field in PROVENANCE_FIELDS if field not in value]
                if missing:
                    offenders.append(
                        {
                            "path": path or "/",
                            "reason": "missing_provenance_fields",
                            "missing_fields": missing,
                        }
                    )
                else:
                    evidence_records.append(dict(value))
            for key, item in value.items():
                walk(item, f"{path}/{key}" if path else f"/{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}/{index}")

    walk(payload, "")
    return {
        **_provenance(
            producer_function="validate_recursive_provenance",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"recursive_provenance_scan": True},
            aggregation_rule="fail closed on any evidence-bearing nested mapping missing full provenance unless explicitly marked raw_data",
        ),
        "offenders": offenders,
        "evidence_record_count": len(evidence_records),
    }


def aggregate_result(checks: Mapping[str, Any]) -> dict[str, Any]:
    failed: list[str] = []
    for name, record in checks.items():
        if not isinstance(record, Mapping) or type(record.get("value")) is not bool:
            raise ValueError(f"computed check record required: {name}")
        if record["value"] is not True:
            failed.append(str(name))
    return {"verdict": "pass" if not failed else "fail", "failed_checks": sorted(failed)}


def _observation_hash(observation: Mapping[str, Any]) -> str:
    return engine.canonical_hash(observation)


def _state_with_resource_ahead(*, run_id: str, organism: dict[str, float]) -> dict[str, Any]:
    state = engine.initial_state(organism, run_id=run_id)
    world = deepcopy(state["world"])
    world["agent"]["position"] = [4, 2]
    world["agent"]["facing"] = "N"
    world["objects_by_cause"]["resource"]["position"] = [4, 1]
    world["objects_by_cause"]["social"]["position"] = [1, 1]
    world["objects_by_cause"]["novelty"]["position"] = [7, 1]
    world["objects_by_cause"]["threat"]["position"] = [2, 3]
    world["objects_by_cause"]["shelter"]["position"] = [6, 3]
    verify_world_state(world)
    state["world"] = world
    return state


def _state_with_empty_front(*, run_id: str, organism: dict[str, float]) -> dict[str, Any]:
    state = _state_with_resource_ahead(run_id=run_id, organism=organism)
    world = deepcopy(state["world"])
    world["objects_by_cause"]["resource"]["position"] = [1, 3]
    verify_world_state(world)
    state["world"] = world
    return state


def _set_goal_model(
    state: dict[str, Any],
    *,
    goal_key: str,
    action: str,
    ema_delta: dict[str, float],
) -> None:
    observation = policy_observation(state["world"])
    observation_hash = _observation_hash(observation)
    state["current_goal"]["state_variable"] = goal_key
    state["current_goal"]["status"] = "active"
    state["current_goal"]["entry_deficit"] = round(
        engine.TARGET_LEVEL - state["organism"][goal_key], 6
    )
    state["model"] = {
        f"{observation_hash}|{goal_key}": {
            action: {"count": 1, "ema_delta": deepcopy(ema_delta)}
        }
    }


def _make_command(state: Mapping[str, Any], *, interventions: Mapping[str, str]) -> dict[str, Any]:
    return engine.make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        trigger_source="headless_acceptance",
        interventions=interventions,
        prev_command_hash=state["last_command_hash"],
    )


def _scenario_completion() -> dict[str, Any]:
    state = _state_with_resource_ahead(
        run_id=f"{RUN_ID}-completion",
        organism={
            "energy": 0.71,
            "safety": 0.74,
            "connection": 0.74,
            "stimulation": 0.74,
        },
    )
    _set_goal_model(
        state,
        goal_key="energy",
        action="interact",
        ema_delta={
            "energy": 0.40,
            "safety": 0.0,
            "connection": 0.0,
            "stimulation": 0.0,
        },
    )
    return {
        "scenario_id": "completion",
        "initial_state": state,
        "run_meta": engine.make_run_metadata(f"{RUN_ID}-completion", POLICY_SEED),
        "commands": [_make_command(state, interventions=engine.DEFAULT_INTERVENTIONS)],
    }


def _scenario_carry() -> dict[str, Any]:
    state = _state_with_empty_front(
        run_id=f"{RUN_ID}-carry",
        organism={
            "energy": 0.50,
            "safety": 0.30,
            "connection": 0.74,
            "stimulation": 0.74,
        },
    )
    _set_goal_model(
        state,
        goal_key="energy",
        action="rest",
        ema_delta={
            "energy": 0.0,
            "safety": 0.20,
            "connection": 0.0,
            "stimulation": 0.0,
        },
    )
    return {
        "scenario_id": "carry",
        "initial_state": state,
        "run_meta": engine.make_run_metadata(f"{RUN_ID}-carry", POLICY_SEED),
        "commands": [_make_command(state, interventions=engine.DEFAULT_INTERVENTIONS)],
    }


def _scenario_reentry() -> dict[str, Any]:
    state = _state_with_empty_front(
        run_id=f"{RUN_ID}-reentry",
        organism={
            "energy": 0.59,
            "safety": 0.74,
            "connection": 0.74,
            "stimulation": 0.74,
        },
    )
    state["current_goal"].update(
        {
            "state_variable": None,
            "status": "explore",
            "entry_deficit": 0.0,
            "selection_reason": "explore_no_eligible_body_goal",
            "completed_latches": {
                "energy": True,
                "safety": True,
                "connection": True,
                "stimulation": True,
            },
        }
    )
    return {
        "scenario_id": "reentry",
        "initial_state": state,
        "run_meta": engine.make_run_metadata(f"{RUN_ID}-reentry", POLICY_SEED),
        "commands": [_make_command(state, interventions=engine.DEFAULT_INTERVENTIONS)],
    }


def _scenario_severe_initial() -> dict[str, Any]:
    state = engine.initial_state(
        {
            "energy": 0.14,
            "safety": 0.05,
            "connection": 0.40,
            "stimulation": 0.40,
        },
        run_id=f"{RUN_ID}-severe-initial",
    )
    return {
        "scenario_id": "severe_initial",
        "initial_state": state,
        "run_meta": engine.make_run_metadata(f"{RUN_ID}-severe-initial", POLICY_SEED),
        "commands": [_make_command(state, interventions=engine.DEFAULT_INTERVENTIONS)],
    }


def _scenario_severe_post_action() -> dict[str, Any]:
    state = _state_with_empty_front(
        run_id=f"{RUN_ID}-severe-post",
        organism={
            "energy": 0.16,
            "safety": 0.40,
            "connection": 0.20,
            "stimulation": 0.74,
        },
    )
    _set_goal_model(
        state,
        goal_key="connection",
        action="turn_left",
        ema_delta={
            "energy": 0.0,
            "safety": 0.0,
            "connection": 0.30,
            "stimulation": 0.0,
        },
    )
    return {
        "scenario_id": "severe_post_action",
        "initial_state": state,
        "run_meta": engine.make_run_metadata(f"{RUN_ID}-severe-post", POLICY_SEED),
        "commands": [_make_command(state, interventions=engine.DEFAULT_INTERVENTIONS)],
    }


def _scenario_explore() -> dict[str, Any]:
    state = _state_with_resource_ahead(
        run_id=f"{RUN_ID}-explore",
        organism={
            "energy": 0.74,
            "safety": 0.74,
            "connection": 0.74,
            "stimulation": 0.74,
        },
    )
    observation_hash = _observation_hash(policy_observation(state["world"]))
    state["current_goal"].update(
        {
            "state_variable": None,
            "status": "explore",
            "entry_deficit": 0.0,
            "selection_reason": "explore_no_eligible_body_goal",
        }
    )
    state["model"] = {
        engine.VISUAL_TRANSITION_MODEL_KEY: {
            observation_hash: {
                "turn_left": {"total": 8, "next_counts": {"a" * 64: 8}},
                "turn_right": {"total": 8, "next_counts": {"b" * 64: 8}},
                "move_forward": {"total": 8, "next_counts": {"c" * 64: 8}},
                "rest": {"total": 8, "next_counts": {"d" * 64: 8}},
                "interact": {"total": 0, "next_counts": {}},
            }
        }
    }
    return {
        "scenario_id": "explore",
        "initial_state": state,
        "run_meta": engine.make_run_metadata(f"{RUN_ID}-explore", POLICY_SEED),
        "commands": [_make_command(state, interventions=engine.DEFAULT_INTERVENTIONS)],
    }


def _replay_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    state = deepcopy(bundle["initial_state"])
    run_meta = deepcopy(bundle["run_meta"])
    traces: list[dict[str, Any]] = []
    for command in bundle["commands"]:
        step = engine.compute_step(state, deepcopy(command), run_meta)
        state = step.next_state
        traces.append(step.trace)
    expected_hashes = bundle.get("stored_trace_hashes")
    if expected_hashes is not None:
        actual_hashes = [trace["trace_hash"] for trace in traces]
        if actual_hashes != expected_hashes:
            raise RecoveryError("stored trace differs from independent recomputation")
    return {
        "scenario_id": bundle["scenario_id"],
        "trace_hashes": [trace["trace_hash"] for trace in traces],
        "selected_actions": [trace["selected_action"] for trace in traces],
        "goal_reasons": [trace["goal_transition"]["reason"] for trace in traces],
        "final_state_hash": engine.state_hash(state),
    }


def _fresh_replay_summary(bundle_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--replay-summary", str(bundle_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(completed.stdout)


def _tamper_bundle(bundle: Mapping[str, Any], tamper_id: str) -> dict[str, Any]:
    tampered = deepcopy(dict(bundle))
    if tamper_id == "initial_state":
        tampered["initial_state"]["schema_version"] = "broken.state.v0"
    elif tamper_id == "command":
        tampered["commands"][0]["prev_command_hash"] = "0" * 64
        tampered["commands"][0]["command_hash"] = engine.canonical_hash(
            {key: tampered["commands"][0][key] for key in tampered["commands"][0] if key != "command_hash"}
        )
    elif tamper_id == "stored_trace":
        tampered["stored_trace_hashes"] = ["0" * 64 for _ in tampered["stored_trace_hashes"]]
    else:
        raise ValueError(tamper_id)
    failed_closed = False
    observed_failure_class = None
    observed_reason = None
    try:
        _replay_bundle(tampered)
    except Exception as exc:  # fail-closed evidence path
        failed_closed = True
        observed_failure_class = type(exc).__name__
        observed_reason = str(exc)
    return {
        "tamper_id": tamper_id,
        "failed_closed": failed_closed,
        "observed_failure_class": observed_failure_class,
        "observed_reason": observed_reason,
    }


def _tamper_evidence(bundle: Mapping[str, Any], tamper_id: str) -> dict[str, Any]:
    scenario_id = str(bundle["scenario_id"])
    payload = _tamper_bundle(bundle, tamper_id)
    return _evidence_payload(
        {**payload, "value": bool(payload["failed_closed"])},
        producer_function=f"build_replay_report.tamper:{tamper_id}",
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={"scenario_id": scenario_id, "tamper_id": tamper_id},
        aggregation_rule="tampered replay bundle must fail closed",
    )


def _run_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    state = deepcopy(bundle["initial_state"])
    run_meta = deepcopy(bundle["run_meta"])
    traces: list[dict[str, Any]] = []
    commands = [deepcopy(command) for command in bundle["commands"]]
    for command in commands:
        step = engine.compute_step(state, command, run_meta)
        state = step.next_state
        traces.append(step.trace)
    return {
        "scenario_id": bundle["scenario_id"],
        "initial_state": deepcopy(bundle["initial_state"]),
        "run_meta": run_meta,
        "commands": commands,
        "traces": traces,
        "final_state": state,
        "stored_trace_hashes": [trace["trace_hash"] for trace in traces],
    }


def _scenario_inputs() -> dict[str, Mapping[str, Any]]:
    bundles = [
        _scenario_completion(),
        _scenario_carry(),
        _scenario_reentry(),
        _scenario_severe_initial(),
        _scenario_severe_post_action(),
        _scenario_explore(),
    ]
    return {bundle["scenario_id"]: bundle for bundle in bundles}


def equal_access_fixed_priority_fsm(access: Mapping[str, Any]) -> str:
    current_goal = access["current_goal"]
    state_variable = current_goal.get("state_variable")
    status = current_goal.get("status")
    if status == "explore":
        ordered = ["interact", "turn_left", "turn_right", "move_forward", "rest"]
    elif state_variable == "energy":
        ordered = ["interact", "rest", "move_forward", "turn_left", "turn_right"]
    elif state_variable == "safety":
        ordered = ["rest", "move_forward", "turn_left", "turn_right", "interact"]
    elif state_variable == "connection":
        ordered = ["turn_left", "move_forward", "turn_right", "interact", "rest"]
    elif state_variable == "stimulation":
        ordered = ["interact", "turn_right", "turn_left", "move_forward", "rest"]
    else:
        ordered = list(engine.ACTIONS)
    for action in ordered:
        if action in engine.ACTIONS:
            return action
    raise ValueError("baseline action ordering is empty")


def _baseline_access(trace: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "observation": deepcopy(trace["policy_projection"]["observation"]),
        "organism": deepcopy(trace["policy_projection"]["organism"]),
        "current_goal": deepcopy(trace["goal_before"]),
    }


def build_baseline_report(scenarios: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    comparisons = {}
    matches = []
    for scenario_id, scenario in scenarios.items():
        trace = scenario["traces"][-1]
        baseline_action = equal_access_fixed_priority_fsm(_baseline_access(trace))
        candidate_action = trace["selected_action"]
        matched = baseline_action == candidate_action
        matches.append(matched)
        comparisons[scenario_id] = _evidence_payload(
            {
                "candidate_selected_action": candidate_action,
                "baseline_selected_action": baseline_action,
                "matched": matched,
                "goal_transition_reason": trace["goal_transition"]["reason"],
            },
            producer_function="equal_access_fixed_priority_fsm",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"scenario_id": scenario_id},
            aggregation_rule="compare equal-access fixed-priority FSM selected action against canonical selected action for one scenario",
        )
    disposition = (
        "equal_access_equivalent_downgrade" if all(matches) else "non_equivalent"
    )
    return {
        **_provenance(
            producer_function="build_baseline_report",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule="compare one independent equal-access fixed-priority FSM against the canonical selected action per predeclared scenario",
        ),
        "baseline_id": "equal_access_fixed_priority_fsm",
        "comparisons": comparisons,
        "match_count": sum(1 for matched in matches if matched),
        "scenario_count": len(matches),
        "disposition": disposition,
    }


def build_ablation_report(bundles: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    case_specs = {
        "canonical": ("carry", engine.DEFAULT_INTERVENTIONS),
        "no_hysteresis": ("carry", dict(engine.DEFAULT_INTERVENTIONS, hysteresis_mode="no_hysteresis")),
        "no_novelty": ("explore", dict(engine.DEFAULT_INTERVENTIONS, novelty_mode="no_novelty")),
        "no_override": ("severe_post_action", dict(engine.DEFAULT_INTERVENTIONS, override_mode="no_override")),
    }
    cases = {}
    invocation_ledger = []
    for case_id, (scenario_id, interventions) in case_specs.items():
        bundle = deepcopy(dict(bundles[scenario_id]))
        bundle["commands"] = [_make_command(bundle["initial_state"], interventions=interventions)]
        scenario = _run_bundle(bundle)
        cases[case_id] = {
            **_evidence_payload(
                {
                    "scenario_id": scenario_id,
                    "interventions": deepcopy(interventions),
                    "selected_action": scenario["traces"][-1]["selected_action"],
                    "goal_after": classify_raw_data(deepcopy(scenario["traces"][-1]["goal_after"])),
                    "goal_transition": classify_raw_data(deepcopy(scenario["traces"][-1]["goal_transition"])),
                    "invoked": True,
                },
                producer_function=f"build_ablation_report.case:{case_id}",
                input_artifacts=_source_inputs(),
                seed_context_episode_ids={"scenario_id": scenario_id},
                aggregation_rule="single declared ablation rerun through compute_step for one scenario",
            )
        }
        invocation_ledger.append(
            {
                **_provenance(
                    producer_function=f"build_ablation_report:{case_id}",
                    input_artifacts=_source_inputs(),
                    seed_context_episode_ids={"scenario_id": scenario_id},
                    aggregation_rule="rerun the named scenario through the real reducer under the named intervention",
                ),
                "case_id": case_id,
                "invoked": True,
            }
        )
    canonical_carry = cases["canonical"]
    canonical_explore = _run_bundle(deepcopy(dict(bundles["explore"])))
    canonical_override = _run_bundle(deepcopy(dict(bundles["severe_post_action"])))
    load_bearing = {
        "no_hysteresis_changes_goal": _check_record(
            cases["no_hysteresis"]["goal_after"]["state_variable"]
            != canonical_carry["goal_after"]["state_variable"],
            producer_function="build_ablation_report.load_bearing:no_hysteresis_changes_goal",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"scenario_id": "carry"},
            aggregation_rule="no_hysteresis rerun must change declared carry scenario goal selection",
        ),
        "no_novelty_changes_action": _check_record(
            cases["no_novelty"]["selected_action"]
            != canonical_explore["traces"][-1]["selected_action"],
            producer_function="build_ablation_report.load_bearing:no_novelty_changes_action",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"scenario_id": "explore"},
            aggregation_rule="no_novelty rerun must change declared explore scenario action selection",
        ),
        "no_override_changes_goal": _check_record(
            cases["no_override"]["goal_after"]["state_variable"]
            != canonical_override["traces"][-1]["goal_after"]["state_variable"],
            producer_function="build_ablation_report.load_bearing:no_override_changes_goal",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"scenario_id": "severe_post_action"},
            aggregation_rule="no_override rerun must change declared severe-post-action goal selection",
        ),
    }
    return {
        **_provenance(
            producer_function="build_ablation_report",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"scenario_ids": sorted(bundles)},
            aggregation_rule="named hysteresis, novelty, and override interventions must execute through compute_step and either change the declared scenario or record negative evidence",
        ),
        "cases": cases,
        "load_bearing": load_bearing,
        "invocation_ledger": invocation_ledger,
    }


def scan_goal_payloads(payload: Mapping[str, Any], inject_positive_control: bool = False) -> dict[str, Any]:
    import re

    candidate = deepcopy(dict(payload))
    if inject_positive_control:
        candidate["positive_control_bundle"] = deepcopy(POSITIVE_CONTROL_PAYLOAD)

    offenders: list[dict[str, Any]] = []

    def add_scalar_offenders(text: str, path: str, reason: str) -> None:
        for category, patterns in FORBIDDEN_VALUE_PATTERNS.items():
            if any(re.search(pattern, text) for pattern in patterns):
                offenders.append({"category": category, "path": path, "reason": reason})

    def walk(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                category = next(
                    (name for name, aliases in FORBIDDEN_KEY_ALIASES.items() if key in aliases),
                    None,
                )
                next_path = f"{path}/{key}" if path else f"/{key}"
                if category is not None:
                    offenders.append(
                        {
                            "category": category,
                            "path": next_path,
                            "reason": "forbidden_key_or_alias",
                        }
                    )
                walk(item, next_path)
        elif isinstance(value, list):
            scalar_items = [
                item
                for item in value
                if isinstance(item, (str, int, float)) and not isinstance(item, bool)
            ]
            if scalar_items:
                add_scalar_offenders(
                    json.dumps(scalar_items, ensure_ascii=False),
                    path or "/",
                    "forbidden_list_value_pattern",
                )
            for index, item in enumerate(value):
                walk(item, f"{path}/{index}")
        elif isinstance(value, (str, int, float)) and not isinstance(value, bool):
            add_scalar_offenders(str(value), path or "/", "forbidden_scalar_value_pattern")

    walk(candidate, "")
    return {
        **_provenance(
            producer_function="scan_goal_payloads",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"goal_payload_scan": True},
            aggregation_rule="recursive structured key and value-pattern scan over goal and payload projections",
        ),
        "positive_control_injected": inject_positive_control,
        "positive_control_detected": inject_positive_control and bool(offenders),
        "offenders": offenders,
    }


def _goal_scan_record(trace: Mapping[str, Any]) -> dict[str, Any]:
    goal_progress = deepcopy(trace["goal_progress"])
    goal_progress.pop("novelty_counter_hash_before", None)
    goal_progress.pop("novelty_counter_hash_after", None)
    transition_update = deepcopy(goal_progress.get("novelty_transition_update", {}))
    for key in (
        "observation_hash",
        "next_observation_hash",
        "entry_hash_before",
        "entry_hash_after",
    ):
        transition_update.pop(key, None)
    if transition_update:
        goal_progress["novelty_transition_update"] = transition_update
    return {
        "goal_before": deepcopy(trace["goal_before"]),
        "goal_progress": goal_progress,
        "goal_transition": deepcopy(trace["goal_transition"]),
        "goal_after": deepcopy(trace["goal_after"]),
        "policy_projection": deepcopy(trace["policy_projection"]),
    }


def _build_live_controller_scenario(temp_root: Path) -> dict[str, Any]:
    db_path = temp_root / "card-b-live.sqlite3"
    store = SQLiteEventStore(db_path)
    try:
        controller = PlaygroundController(
            store,
            run_id=f"{RUN_ID}-live",
            seed=POLICY_SEED,
            world_seed=1701,
            layout_id="p2_offset_v1",
        )
        dispatch = controller.dispatch(trigger_source="ui_step_button")
        if not dispatch.receipt.committed:
            raise RuntimeError(dispatch.receipt.error or "dispatch not committed")
        recovered = store.recover_run(controller.run_id)
        frame = recovered.frames[-1]
        terminal_snapshot = build_terminal_snapshot(controller)
        tk_payload = build_tk_trace_payload(frame.state, frame.trace)
        with SQLiteEventStore(db_path) as second_store:
            fresh = second_store.recover_run(controller.run_id)
        command_row = store.connection.execute(
            "SELECT command_json FROM commands WHERE run_id = ? ORDER BY sequence",
            (controller.run_id,),
        ).fetchone()
        live_bundle = {
            "scenario_id": "live_controller_step",
            "initial_state": json.loads(
                store.connection.execute(
                    "SELECT initial_state_json FROM runs WHERE run_id = ?",
                    (controller.run_id,),
                ).fetchone()[0]
            ),
            "run_meta": json.loads(
                store.connection.execute(
                    "SELECT run_meta_json FROM runs WHERE run_id = ?",
                    (controller.run_id,),
                ).fetchone()[0]
            ),
            "commands": [json.loads(command_row[0])],
            "stored_trace_hashes": [frame.trace["trace_hash"]],
        }
        return {
            "db_path": str(db_path),
            "run_id": controller.run_id,
            "frame": frame,
            "terminal_snapshot": terminal_snapshot,
            "tk_payload": tk_payload,
            "fresh_trace_hash": fresh.traces[-1]["trace_hash"],
            "bundle": live_bundle,
        }
    finally:
        store.close()


def build_replay_report(
    scenarios: Mapping[str, Mapping[str, Any]], live_bundle: Mapping[str, Any]
) -> dict[str, Any]:
    temp_root = Path(tempfile.mkdtemp(prefix="ego-v2-card-b-replay-"))
    try:
        by_scenario = {}
        all_bundles = {
            scenario_id: {
                "scenario_id": scenario_id,
                "initial_state": deepcopy(scenario["initial_state"]),
                "run_meta": deepcopy(scenario["run_meta"]),
                "commands": deepcopy(scenario["commands"]),
                "stored_trace_hashes": deepcopy(scenario["stored_trace_hashes"]),
            }
            for scenario_id, scenario in scenarios.items()
        }
        all_bundles["live_controller_step"] = deepcopy(dict(live_bundle))
        for scenario_id, bundle in all_bundles.items():
            local = _replay_bundle(bundle)
            bundle_path = temp_root / f"{scenario_id}.json"
            _write_json(bundle_path, bundle)
            fresh_a = _fresh_replay_summary(bundle_path)
            fresh_b = _fresh_replay_summary(bundle_path)
            by_scenario[scenario_id] = _evidence_payload(
                {
                    "scenario_id": scenario_id,
                    "local_summary": classify_raw_data(local),
                    "fresh_summaries": [classify_raw_data(fresh_a), classify_raw_data(fresh_b)],
                    "fresh_process_match": _check_record(
                        local == fresh_a == fresh_b,
                        producer_function="build_replay_report.fresh_process_match",
                        input_artifacts=_source_inputs(),
                        seed_context_episode_ids={"scenario_id": scenario_id},
                        aggregation_rule="local replay summary must equal two fresh-process replay summaries for one scenario",
                    ),
                    "tamper_controls": {
                        "initial_state": _tamper_evidence(bundle, "initial_state"),
                        "command": _tamper_evidence(bundle, "command"),
                        "stored_trace": _tamper_evidence(bundle, "stored_trace"),
                    },
                },
                producer_function="build_replay_report.scenario",
                input_artifacts=_source_inputs(),
                seed_context_episode_ids={"scenario_id": scenario_id},
                aggregation_rule="one scenario-level replay evidence wrapper containing raw summaries plus replay/tamper evidence records",
            )
        return {
            **_provenance(
                producer_function="build_replay_report",
                input_artifacts=_source_inputs(),
                seed_context_episode_ids={"scenario_ids": sorted(all_bundles)},
                aggregation_rule="every declared scenario must replay locally and in two fresh processes from serialized initial state plus ordered commands, with tamper controls failing closed",
            ),
            "scenarios": by_scenario,
            "stored_selected_action_used_as_input": False,
        }
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def _trace_records(
    scenarios: Mapping[str, Mapping[str, Any]], live_payload: Mapping[str, Any]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for scenario_id, scenario in scenarios.items():
        for trace in scenario["traces"]:
            records.append(
                {
                    **_provenance(
                        producer_function="trace_record",
                        input_artifacts=_source_inputs(),
                        seed_context_episode_ids={
                            "scenario_id": scenario_id,
                            "episode_id": trace["episode_id"],
                            "sequence": trace["sequence"],
                        },
                        aggregation_rule="one canonical compute_step result for the declared Card-B scenario",
                    ),
                    "record_type": "trace",
                    "scenario_id": scenario_id,
                    "trace": classify_raw_data(trace),
                }
            )
    records.append(
        {
            **_provenance(
                producer_function="live_payload_record",
                input_artifacts=_source_inputs(),
                seed_context_episode_ids={"scenario_id": "live_controller_step"},
                aggregation_rule="one real controller dispatch recovered through SQLite and rendered by terminal/tk payload helpers",
            ),
            "record_type": "live_payload",
            "scenario_id": "live_controller_step",
            "terminal_goal_trace": classify_raw_data(
                deepcopy(live_payload["terminal_snapshot"]["goal_trace"])
            ),
            "tk_goal_payload": classify_raw_data(
                {
                    "goal_before": deepcopy(live_payload["tk_payload"]["goal_before"]),
                    "goal_progress": deepcopy(live_payload["tk_payload"]["goal_progress"]),
                    "goal_transition": deepcopy(live_payload["tk_payload"]["goal_transition"]),
                    "goal_after": deepcopy(live_payload["tk_payload"]["goal_after"]),
                }
            ),
        }
    )
    return records


def run_card_b_verification(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    _clean_output_dir(output)
    inputs = _source_inputs()
    bundles = _scenario_inputs()
    scenarios = {scenario_id: _run_bundle(bundle) for scenario_id, bundle in bundles.items()}

    with tempfile.TemporaryDirectory(prefix="ego-v2-card-b-live-") as temp_name:
        live_payload = _build_live_controller_scenario(Path(temp_name))

    baseline = build_baseline_report(scenarios)
    ablation = build_ablation_report(bundles)
    replay = build_replay_report(scenarios, live_payload["bundle"])

    clean_scan_payload = {
        "goal_records": [_goal_scan_record(trace) for scenario in scenarios.values() for trace in scenario["traces"]],
        "terminal_goal_trace": _goal_scan_record(
            {
                "goal_before": live_payload["terminal_snapshot"]["goal_trace"]["goal_before"],
                "goal_progress": live_payload["terminal_snapshot"]["goal_trace"]["goal_progress"],
                "goal_transition": live_payload["terminal_snapshot"]["goal_trace"]["goal_transition"],
                "goal_after": live_payload["terminal_snapshot"]["goal_trace"]["goal_after"],
                "policy_projection": {"observation": {"visual": live_payload["tk_payload"]["policy_visual"]["visual"]}},
            }
        ),
        "tk_goal_payload": _goal_scan_record(
            {
                "goal_before": live_payload["tk_payload"]["goal_before"],
                "goal_progress": live_payload["tk_payload"]["goal_progress"],
                "goal_transition": live_payload["tk_payload"]["goal_transition"],
                "goal_after": live_payload["tk_payload"]["goal_after"],
                "policy_projection": {"observation": {"visual": live_payload["tk_payload"]["policy_visual"]["visual"]}},
            }
        ),
    }
    clean_scan = scan_goal_payloads(clean_scan_payload)
    positive_scan = scan_goal_payloads(clean_scan_payload, inject_positive_control=True)

    trace_records = _trace_records(scenarios, live_payload)
    _write_jsonl(output / "trace.jsonl", trace_records)

    leakage = {
        **_provenance(
            producer_function="build_leakage_report",
            input_artifacts=[*inputs, _file_record(output / "trace.jsonl", logical_path=LOGICAL_TRACE_PATH)],
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule="scan goal, policy, terminal, and tk payload projections plus a positive control bundle",
        ),
        "clean_scan": clean_scan,
        "positive_control_scan": positive_scan,
    }
    provenance_scan = validate_recursive_provenance(
        {
            "baseline": baseline,
            "ablation": ablation,
            "leakage": leakage,
            "replay": replay,
        }
    )
    recursive_provenance_present = provenance_scan["offenders"] == []

    carry_trace = scenarios["carry"]["traces"][-1]
    completion_trace = scenarios["completion"]["traces"][-1]
    reentry_trace = scenarios["reentry"]["traces"][-1]
    severe_initial_bundle = bundles["severe_initial"]
    severe_initial_trace = scenarios["severe_initial"]["traces"][-1]
    severe_post_trace = scenarios["severe_post_action"]["traces"][-1]
    explore_trace = scenarios["explore"]["traces"][-1]
    live_frame = live_payload["frame"]
    terminal_goal_trace = live_payload["terminal_snapshot"]["goal_trace"]
    tk_goal_payload = live_payload["tk_payload"]

    checks = {
        "declared_goal_scenarios_observed": _check_record(
            set(scenarios) == {
                "completion",
                "carry",
                "reentry",
                "severe_initial",
                "severe_post_action",
                "explore",
            },
            producer_function="_scenario_inputs",
            input_artifacts=inputs,
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule="all predeclared Card-B scenarios must execute through the canonical reducer",
        ),
        "live_controller_sqlite_terminal_tk_payload_path": _check_record(
            live_frame.trace is not None
            and live_frame.trace["trigger_source"] == "ui_step_button"
            and live_frame.trace["trace_hash"] == live_payload["fresh_trace_hash"]
            and terminal_goal_trace["goal_transition"] == live_frame.trace["goal_transition"]
            and tk_goal_payload["goal_transition"] == live_frame.trace["goal_transition"]
            and terminal_goal_trace["goal_after"] == live_frame.trace["goal_after"]
            and tk_goal_payload["goal_after"] == live_frame.trace["goal_after"],
            producer_function="PlaygroundController.dispatch -> SQLiteEventStore.recover_run -> build_terminal_snapshot/build_tk_trace_payload",
            input_artifacts=inputs,
            seed_context_episode_ids={"scenario_id": "live_controller_step"},
            aggregation_rule="one real controller dispatch must commit to SQLite, recover, and render identical recovered goal payloads in terminal and tk helpers",
        ),
        "goal_hysteresis_completion_reentry_override_explore": _check_record(
            carry_trace["goal_after"]["state_variable"] == "energy"
            and carry_trace["goal_transition"]["reason"] == "hysteresis_carry"
            and completion_trace["goal_progress"]["completed"] is True
            and completion_trace["goal_after"]["status"] == "explore"
            and reentry_trace["goal_transition"]["reason"] == "reentry_below_threshold"
            and severe_initial_bundle["initial_state"]["current_goal"]["state_variable"] == "energy"
            and severe_initial_bundle["initial_state"]["current_goal"]["selection_reason"] == "critical_override_energy"
            and severe_initial_trace["goal_before"]["state_variable"] == "energy"
            and severe_post_trace["goal_transition"]["reason"] == "critical_override_energy"
            and severe_post_trace["goal_after"]["state_variable"] == "energy"
            and explore_trace["goal_before"]["status"] == "explore"
            and explore_trace["selected_action"] == "interact",
            producer_function="engine.compute_step",
            input_artifacts=inputs,
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule="carry, completion, reentry, severe override, and explore transitions must appear on the declared scenarios",
        ),
        "equal_access_baseline_reported": _check_record(
            baseline["baseline_id"] == "equal_access_fixed_priority_fsm"
            and baseline["disposition"]
            in {"non_equivalent", "equal_access_equivalent_downgrade"}
            and bool(baseline["comparisons"]),
            producer_function="build_baseline_report",
            input_artifacts=inputs,
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule="the independent equal-access baseline must run and either downgrade or remain non-equivalent without fabricating failure",
        ),
        "real_ablations_invoked_and_load_bearing": _check_record(
            all(case["invoked"] is True for case in ablation["invocation_ledger"])
            and ablation["load_bearing"]["no_hysteresis_changes_goal"]["value"] is True
            and ablation["load_bearing"]["no_novelty_changes_action"]["value"] is True
            and ablation["load_bearing"]["no_override_changes_goal"]["value"] is True,
            producer_function="build_ablation_report",
            input_artifacts=inputs,
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule="named hysteresis, novelty, and override ablations must be real compute_step reruns and change the declared load-bearing scenario",
        ),
        "goal_payload_leakage_scan_clean_positive_control_fires": _check_record(
            clean_scan["offenders"] == []
            and positive_scan["positive_control_detected"] is True,
            producer_function="scan_goal_payloads",
            input_artifacts=[*inputs, _file_record(output / "trace.jsonl", logical_path=LOGICAL_TRACE_PATH)],
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule="goal and payload projections must scan clean while the multi-class positive control fires",
        ),
        "replay_two_fresh_processes_match": _check_record(
            all(
                item["fresh_process_match"]["value"] is True
                for item in replay["scenarios"].values()
            )
            and replay["stored_selected_action_used_as_input"] is False,
            producer_function="build_replay_report",
            input_artifacts=[*inputs, _file_record(output / "trace.jsonl", logical_path=LOGICAL_TRACE_PATH)],
            seed_context_episode_ids={"scenario_ids": sorted(replay["scenarios"])},
            aggregation_rule="all declared scenarios must replay identically locally and in two fresh processes from serialized state plus commands",
        ),
        "replay_tamper_controls_fail_closed": _check_record(
            all(
                all(control["value"] is True for control in item["tamper_controls"].values())
                for item in replay["scenarios"].values()
            ),
            producer_function="build_replay_report",
            input_artifacts=[*inputs, _file_record(output / "trace.jsonl", logical_path=LOGICAL_TRACE_PATH)],
            seed_context_episode_ids={"scenario_ids": sorted(replay["scenarios"])},
            aggregation_rule="tampered initial state, command chain, and stored trace expectations must fail closed for every declared scenario",
        ),
        "recursive_provenance_present": _check_record(
            recursive_provenance_present,
            producer_function="validate_recursive_provenance",
            input_artifacts=[*inputs, _file_record(output / "trace.jsonl", logical_path=LOGICAL_TRACE_PATH)],
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule="all nested evidence-bearing payloads must carry full provenance or be explicitly marked raw_data",
        ),
    }
    aggregated = aggregate_result({key: checks[key] for key in ACCEPTANCE_GATE_IDS})
    claim_blockers = (
        ["equal_access_control_equivalence"]
        if baseline["disposition"] == "equal_access_equivalent_downgrade"
        else []
    )

    result = {
        **_provenance(
            producer_function="run_card_b_verification",
            input_artifacts=[*inputs, _file_record(output / "trace.jsonl", logical_path=LOGICAL_TRACE_PATH)],
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule="pass iff all declared Card-B engineering checks are true; equal-access baseline equivalence downgrades only the claim ceiling",
        ),
        "task_id": TASK_ID,
        "checks": checks,
        "verdict": aggregated["verdict"],
        "failed_checks": aggregated["failed_checks"],
        "baseline_disposition": baseline["disposition"],
        "claim_blockers": claim_blockers,
        "claim_ceiling": CLAIM_CEILING,
        "provenance_scan": provenance_scan,
    }
    failure_manifest = {
        **_provenance(
            producer_function="run_card_b_verification.failure_manifest",
            input_artifacts=result["input_artifacts"],
            seed_context_episode_ids=result["seed_context_episode_ids"],
            aggregation_rule="preserve engineering failures and baseline-equivalence blockers without claim inflation",
        ),
        "engineering_failures": aggregated["failed_checks"],
        "claim_blockers": claim_blockers,
        "status": "clean" if not aggregated["failed_checks"] else "fail",
    }

    _write_json(output / "baseline_comparison.json", baseline)
    _write_json(output / "ablation_report.json", ablation)
    _write_json(output / "leakage_report.json", leakage)
    _write_json(output / "replay_report.json", replay)
    _write_json(output / "failure_manifest.json", failure_manifest)
    _write_json(output / "result.json", result)
    (output / "claim_ceiling.txt").write_text(CLAIM_CEILING + "\n", encoding="utf-8", newline="\n")

    actual = {path.name for path in output.iterdir()}
    if actual != REQUIRED_ARTIFACTS:
        raise RuntimeError(f"unexpected artifact set: {sorted(actual)}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--replay-summary", type=Path)
    args = parser.parse_args(argv)
    if args.replay_summary is not None:
        bundle = json.loads(args.replay_summary.read_text(encoding="utf-8"))
        print(json.dumps(_replay_bundle(bundle), ensure_ascii=False, sort_keys=True))
        return 0
    if args.output_dir is None:
        raise SystemExit("--output-dir is required")
    result = run_card_b_verification(args.output_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
