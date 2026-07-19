#!/usr/bin/env python3
"""Callable evidence producer for the bounded resource-interaction repair."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Mapping
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine, microworld
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import (
    RecoveryError,
    RecoveryFrame,
    SQLiteEventStore,
)
from labs.ego_life_playground_v0.visual_console import build_chinese_causal_view


TASK_ID = "EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A"
RUN_ID = "ego-v2-p0-resource-interaction-verify"
RUN_SEED = 18
CLAIM_CEILING = (
    "Layer 2 bounded product-engineering repair only: the explicit V2 path now "
    "records one command-derived resource instance, resolves stationary forage "
    "at site_a through the existing reducer/store/replay chain, and computes "
    "energy gain only from a resolved positive resource interaction. This does "
    "not establish viability as a mechanism, learning, memory causality, a "
    "dynamic causal boundary, initiative, agency, autonomy, emotion, "
    "subjectivity, consciousness, electronic life, or product readiness."
)
REQUIRED_ARTIFACTS = {
    "result.json",
    "trace.jsonl",
    "baseline_comparison.json",
    "ablation_report.json",
    "leakage_report.json",
    "replay_report.json",
    "failure_manifest.json",
    "progress_checkpoint.json",
    "experiment_ledger.jsonl",
    "stage_scorecard.json",
    "claim_ceiling.txt",
}

def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file_record(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": _sha256(raw)}


def _source_inputs() -> list[dict[str, Any]]:
    return [
        _file_record(Path(__file__)),
        _file_record(REPO_ROOT / "labs/ego_life_playground_v0/engine.py"),
        _file_record(REPO_ROOT / "labs/ego_life_playground_v0/microworld.py"),
        _file_record(REPO_ROOT / "labs/ego_life_playground_v0/visual_console.py"),
        _file_record(REPO_ROOT / "labs/ego_life_playground_v0/controller.py"),
        _file_record(REPO_ROOT / "labs/ego_life_playground_v0/store.py"),
        _file_record(
            REPO_ROOT
            / "docs/codex/tasks/EGO-V2-P0-RESOURCE-INTERACTION-OUTCOME-REPAIR-001A.md"
        ),
    ]


def _code_path_hash() -> str:
    return _sha256(
        _canonical_bytes(
            {
                "candidate_code_path_hash": engine.compute_code_path_hash(),
                "visual_console_sha256": _file_record(
                    REPO_ROOT / "labs/ego_life_playground_v0/visual_console.py"
                )["sha256"],
                "verifier_sha256": _file_record(Path(__file__))["sha256"],
            }
        )
    )


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_jsonl(path: Path, records: list[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _evidence(
    value: bool,
    *,
    producer_function: str,
    inputs: list[Any],
    context_ids: list[str],
) -> dict[str, Any]:
    return {
        "evidence_record_type": "computed_evidence",
        "producer_function": producer_function,
        "input_artifacts": deepcopy(inputs),
        "run_id": RUN_ID,
        "seed_context_episode_ids": {
            "run_seed": RUN_SEED,
            "context_ids": list(context_ids),
        },
        "aggregation_rule": "boolean result from the named callable computation path",
        "code_path_hash": _code_path_hash(),
        "value": bool(value),
    }


def aggregate_checks(checks: Mapping[str, Any]) -> dict[str, Any]:
    failed: list[str] = []
    for name, record in checks.items():
        if not isinstance(record, Mapping) or type(record.get("value")) is not bool:
            raise ValueError(f"computed check record required: {name}")
        if record["value"] is not True:
            failed.append(str(name))
    return {"verdict": "pass" if not failed else "fail", "failed_checks": sorted(failed)}


def scan_policy_for_resource_leakage(
    payload: Mapping[str, Any], *, instance_id: str
) -> dict[str, Any]:
    matches: list[dict[str, str]] = []
    forbidden_keys = {
        "resource_interaction",
        "instance_id",
        "food_obtained",
        "failure_reason",
    }

    def walk(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in forbidden_keys:
                    match = (
                        "forbidden_key_and_value"
                        if key == "instance_id" and child == instance_id
                        else "forbidden_post_outcome_key"
                    )
                    matches.append({"path": child_path, "match": match})
                elif child == instance_id:
                    matches.append(
                        {"path": child_path, "match": "forbidden_instance_value"}
                    )
                walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(payload, "$")
    return {"leak_detected": bool(matches), "matches": matches}


def _stationary_state(*, run_id: str, seed: int, energy: float) -> dict[str, Any]:
    state = engine.initial_state(
        {
            "energy": energy,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.9,
        },
        run_id=run_id,
        seed=seed,
    )
    state["world"]["agent"]["position"] = "site_a"
    state["world"]["public_observation"]["agent_position"] = "site_a"
    microworld.verify_world_state(state["world"])
    return state


def _make_command(
    state: Mapping[str, Any],
    *,
    cue: str,
    world_event: str,
    trigger_source: str = "headless_acceptance",
) -> dict[str, Any]:
    return engine.make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        cue=cue,
        world_event=world_event,
        trigger_source=trigger_source,
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=state["last_command_hash"],
    )


def _run_step(
    state: Mapping[str, Any],
    meta: Mapping[str, Any],
    *,
    cue: str,
    world_event: str,
    trigger_source: str = "headless_acceptance",
) -> tuple[engine.StepResult, dict[str, Any]]:
    command = _make_command(
        state,
        cue=cue,
        world_event=world_event,
        trigger_source=trigger_source,
    )
    return engine.compute_step(state, command, meta), command


def _legacy_moved_only_food(trace: Mapping[str, Any]) -> bool:
    transition = trace["world_transition"]
    return bool(
        transition["moved"]
        and trace["selected_action"] == "forage"
        and transition["visited_site"] == "site_a"
        and transition["outcome"] == 1.0
    )


def _legacy_cue_only_food(*, cue: str, world_event: str) -> bool:
    return cue == "resource" and world_event == "resource_appears"


def _baseline_report(
    positive_trace: Mapping[str, Any],
    negative_trace: Mapping[str, Any],
    *,
    non_forage_trace: Mapping[str, Any],
) -> dict[str, Any]:
    non_forage_transition = non_forage_trace["world_transition"]
    return {
        "schema_version": "ego.life_playground.resource_baseline_comparison.v1",
        "producer_function": "verify_ego_v2_p0_resource_interaction_outcome_repair_001a._baseline_report",
        "input_artifacts": [
            *_source_inputs(),
            f"trace:{positive_trace['trace_hash']}",
            f"trace:{negative_trace['trace_hash']}",
            f"trace:{non_forage_trace['trace_hash']}",
        ],
        "run_id": RUN_ID,
        "seed_context_episode_ids": {
            "run_seed": RUN_SEED,
            "context_ids": [
                positive_trace["episode_id"],
                negative_trace["episode_id"],
                non_forage_trace["episode_id"],
            ],
        },
        "aggregation_rule": "compare live candidate traces against independent moved-only and cue-only callables",
        "code_path_hash": _code_path_hash(),
        "moved_only": {
            "candidate_food_obtained": positive_trace["world_transition"]["food_obtained"],
            "baseline_food_obtained": _legacy_moved_only_food(positive_trace),
        },
        "cue_only": {
            "negative_candidate_food_obtained": negative_trace["world_transition"]["food_obtained"],
            "negative_baseline_food_obtained": _legacy_cue_only_food(
                cue="resource", world_event="resource_appears"
            ),
            "non_forage_candidate_food_obtained": non_forage_transition["food_obtained"],
            "non_forage_baseline_food_obtained": _legacy_cue_only_food(
                cue="resource", world_event="resource_appears"
            ),
        },
    }


def _food_gain_ablation() -> dict[str, Any]:
    run_id = f"{RUN_ID}-food-gain-ablation"
    state = _stationary_state(run_id=run_id, seed=18, energy=0.0)
    meta = engine.make_run_metadata(run_id, 18)
    canonical, command = _run_step(
        state,
        meta,
        cue="resource",
        world_event="resource_appears",
    )
    with patch.object(engine, "FOOD_ENERGY_GAIN", 0.0):
        ablated = engine.compute_step(state, command, meta)
    return {
        "schema_version": "ego.life_playground.resource_ablation.v1",
        "producer_function": "verify_ego_v2_p0_resource_interaction_outcome_repair_001a._food_gain_ablation",
        "input_artifacts": [
            f"state:{engine.state_hash(state)}",
            f"command:{command['command_hash']}",
        ],
        "run_id": run_id,
        "seed_context_episode_ids": {
            "run_seed": 18,
            "episode_id": canonical.trace["episode_id"],
        },
        "aggregation_rule": "rerun the same serialized state and command with in-memory FOOD_ENERGY_GAIN=0",
        "code_path_hash": _code_path_hash(),
        "food_gain_disabled": {
            "same_selected_action": canonical.trace["selected_action"]
            == ablated.trace["selected_action"],
            "same_resource_interaction": canonical.trace["world_transition"][
                "resource_interaction"
            ]
            == ablated.trace["world_transition"]["resource_interaction"],
            "canonical_energy_after": canonical.trace["energy_after"],
            "ablation_energy_after": ablated.trace["energy_after"],
        },
    }


def _recovery_summary(recovered: Any) -> dict[str, Any]:
    traces = recovered.traces
    return {
        "run_id": recovered.run_id,
        "command_count": recovered.command_count,
        "final_state_hash": engine.state_hash(recovered.state),
        "trace_hashes": [trace["trace_hash"] for trace in traces],
        "trigger_sources": [trace["trigger_source"] for trace in traces],
        "selected_actions": [trace["selected_action"] for trace in traces],
        "resource_instance_ids": [
            trace["world_transition"]["resource_interaction"]["instance_id"]
            for trace in traces
        ],
        "energy_afters": [trace["energy_after"] for trace in traces],
    }


def _visual_trace_binding_report(frame: RecoveryFrame) -> dict[str, Any]:
    if frame.trace is None:
        raise ValueError("visual trace-binding probe requires a recovered trace")
    recorded_view = build_chinese_causal_view(frame)
    variant_trace = deepcopy(frame.trace)
    variant_trace["world_transition"]["outcome"] = -1.0
    variant_trace["world_transition"]["food_obtained"] = False
    variant_trace["world_transition"]["resource_interaction"].update(
        {
            "outcome": -1.0,
            "food_obtained": False,
            "failure_reason": "harmful_or_unusable_resource",
        }
    )
    variant_trace["world_outcome"]["value"] = -1.0
    variant_trace["world_outcome"]["food_obtained"] = False
    variant_trace["food_gain"] = 0.0
    variant_trace["metabolism"]["food_gain"] = 0.0
    variant_trace["metabolism"]["energy_after"] = 0.0
    variant_trace["metabolism"]["energy_delta"] = 0.0
    variant_view = build_chinese_causal_view(
        RecoveryFrame(
            sequence=frame.sequence,
            state=deepcopy(frame.state),
            trace=variant_trace,
        )
    )
    invariant_metadata = all(
        variant_trace[key] == frame.trace[key]
        for key in ("seed", "run_id", "world_event", "selected_action")
    )
    return {
        "schema_version": "ego.life_playground.resource_visual_binding.v1",
        "producer_function": (
            "verify_ego_v2_p0_resource_interaction_outcome_repair_001a."
            "_visual_trace_binding_report"
        ),
        "input_artifacts": [
            f"trace:{frame.trace['trace_hash']}",
            _file_record(REPO_ROOT / "labs/ego_life_playground_v0/visual_console.py"),
        ],
        "run_id": frame.trace["run_id"],
        "seed_context_episode_ids": {
            "run_seed": frame.trace["seed"],
            "episode_id": frame.trace["episode_id"],
        },
        "aggregation_rule": (
            "render one store-recovered frame, then alter only post-outcome trace "
            "fields while holding seed/run/event/action fixed and require display "
            "to follow those fields"
        ),
        "code_path_hash": _code_path_hash(),
        "invariant_metadata": invariant_metadata,
        "recorded_result": recorded_view["结果与变化"]["资源结果"],
        "recorded_food_gain": recorded_view["结果与变化"]["食物补能"],
        "variant_result": variant_view["结果与变化"]["资源结果"],
        "variant_failure_reason": variant_view["结果与变化"]["失败原因"],
        "variant_food_gain": variant_view["结果与变化"]["食物补能"],
        "same_event_display": (
            recorded_view["外部事件"] == variant_view["外部事件"]
        ),
        "same_action_display": (
            recorded_view["候选与选择"]["选择的行动"]
            == variant_view["候选与选择"]["选择的行动"]
        ),
    }


def _run_fresh_recovery(db_path: Path, run_id: str) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__)),
        "--recover-db",
        str(db_path),
        "--run-id",
        run_id,
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return json.loads(completed.stdout)


def _tamper_trace_resource_interaction(
    db_path: Path, run_id: str
) -> tuple[bool, str | None]:
    tampered = db_path.with_name(f"{db_path.stem}-resource-tamper{db_path.suffix}")
    shutil.copy2(db_path, tampered)
    try:
        with SQLiteEventStore(tampered) as store:
            row = store.connection.execute(
                "SELECT trace_json FROM traces WHERE run_id = ? AND sequence = 1",
                (run_id,),
            ).fetchone()
            trace = json.loads(row["trace_json"])
            trace["world_transition"]["resource_interaction"]["failure_reason"] = (
                "no_resource_event"
            )
            trace["trace_hash"] = engine.compute_trace_hash(trace)
            store.connection.execute(
                "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = 1",
                (engine.canonical_json(trace), trace["trace_hash"], run_id),
            )
            try:
                store.recover_run(run_id)
            except RecoveryError as exc:
                return True, str(exc)
            return False, None
    finally:
        if tampered.exists():
            tampered.unlink()


def _tamper_stored_trace(db_path: Path, run_id: str) -> bool:
    tampered = db_path.with_name(f"{db_path.stem}-trace-tamper{db_path.suffix}")
    shutil.copy2(db_path, tampered)
    try:
        with SQLiteEventStore(tampered) as store:
            row = store.connection.execute(
                "SELECT trace_json FROM traces WHERE run_id = ? AND sequence = 2",
                (run_id,),
            ).fetchone()
            trace = json.loads(row["trace_json"])
            trace["energy_after"] = 0.999
            trace_hash = engine.compute_trace_hash(trace)
            store.connection.execute(
                "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = 2",
                (engine.canonical_json(trace), trace_hash, run_id),
            )
            try:
                store.recover_run(run_id)
            except RecoveryError:
                return True
            return False
    finally:
        if tampered.exists():
            tampered.unlink()


def _tamper_initial_state(db_path: Path, run_id: str) -> bool:
    tampered = db_path.with_name(f"{db_path.stem}-state-tamper{db_path.suffix}")
    shutil.copy2(db_path, tampered)
    try:
        with SQLiteEventStore(tampered) as store:
            row = store.connection.execute(
                "SELECT initial_state_json FROM runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            state = json.loads(row["initial_state_json"])
            state["organism"]["energy"] = 0.5
            store.connection.execute(
                "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
                (engine.canonical_json(state), engine.canonical_hash(state), run_id),
            )
            try:
                store.recover_run(run_id)
            except RecoveryError:
                return True
            return False
    finally:
        if tampered.exists():
            tampered.unlink()


def _controller_replay_report() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ego-resource-interaction-") as temp_dir:
        db_path = Path(temp_dir) / "controller.sqlite3"
        run_id = f"{RUN_ID}-controller"
        seed = 18
        state = _stationary_state(run_id=run_id, seed=seed, energy=0.0)
        run_meta = engine.make_run_metadata(run_id, seed)
        with SQLiteEventStore(db_path) as store:
            store.create_run(run_meta, state)
            controller = PlaygroundController(store, run_id=run_id)
            first = controller.dispatch(
                "resource",
                engine.DEFAULT_INTERVENTIONS,
                trigger_source="ui_step_button",
                world_event="resource_appears",
            )
            second = controller.dispatch(
                "resource",
                engine.DEFAULT_INTERVENTIONS,
                trigger_source="ui_step_button",
                world_event="resource_appears",
            )
            local_recovery = controller.recover()
            duplicate_receipt = store.append_step(
                second.step.trace["command"],
                second.step.trace,
            )
            subprocess_one = _run_fresh_recovery(db_path, run_id)
            subprocess_two = _run_fresh_recovery(db_path, run_id)
            local_summary = _recovery_summary(local_recovery)
            resource_tamper_closed, resource_tamper_error = (
                _tamper_trace_resource_interaction(db_path, run_id)
            )
            visual_trace_binding = _visual_trace_binding_report(
                local_recovery.frames[-1]
            )
            return {
                "schema_version": "ego.life_playground.resource_replay.v1",
                "producer_function": "verify_ego_v2_p0_resource_interaction_outcome_repair_001a._controller_replay_report",
                "input_artifacts": _source_inputs()
                + [
                    {
                        "path": "ephemeral://controller.sqlite3",
                        "bytes": _file_record(db_path)["bytes"],
                        "sha256": _file_record(db_path)["sha256"],
                        "kind": "ephemeral_sqlite_runtime_before_cleanup",
                    }
                ],
                "run_id": run_id,
                "seed_context_episode_ids": {
                    "run_seed": seed,
                    "episode_id": local_recovery.state["clock"]["episode_id"],
                },
                "aggregation_rule": "controller dispatches two resource commands, recover locally, then compare two fresh subprocess recoveries",
                "code_path_hash": _code_path_hash(),
                "two_resource_dispatch_committed": bool(
                    first.receipt.committed and second.receipt.committed
                ),
                "local_recovery": local_summary,
                "fresh_process_one": subprocess_one,
                "fresh_process_two": subprocess_two,
                "fresh_process_x2_matches_local_recovery": bool(
                    subprocess_one == subprocess_two == local_summary
                ),
                "duplicate_command_rejected": bool(not duplicate_receipt.committed),
                "resource_interaction_tamper_fail_closed": resource_tamper_closed,
                "resource_interaction_tamper_error": resource_tamper_error,
                "stored_trace_tamper_fail_closed": _tamper_stored_trace(
                    db_path, run_id
                ),
                "initial_state_tamper_fail_closed": _tamper_initial_state(
                    db_path, run_id
                ),
                "visual_trace_binding": visual_trace_binding,
            }


def recover_db_summary(db_path: str | Path, run_id: str) -> dict[str, Any]:
    with SQLiteEventStore(db_path) as store:
        recovered = store.recover_run(run_id)
    return _recovery_summary(recovered)


def run_resource_interaction_verification(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)

    positive_state = _stationary_state(
        run_id=f"{RUN_ID}-stationary-positive", seed=18, energy=0.0
    )
    positive_meta = engine.make_run_metadata(f"{RUN_ID}-stationary-positive", 18)
    positive_step, positive_command = _run_step(
        positive_state,
        positive_meta,
        cue="resource",
        world_event="resource_appears",
    )
    positive_observed_world = microworld.observe_world_event(
        positive_state["world"], "resource_appears"
    )
    same_command_recompute_a = microworld.transition_world(
        positive_observed_world,
        "forage",
        source_sequence=1,
        source_episode_id=positive_state["clock"]["episode_id"],
        source_command_hash=positive_command["command_hash"],
    )
    same_command_recompute_b = microworld.transition_world(
        positive_observed_world,
        "forage",
        source_sequence=1,
        source_episode_id=positive_state["clock"]["episode_id"],
        source_command_hash=positive_command["command_hash"],
    )

    negative_state = _stationary_state(
        run_id=f"{RUN_ID}-stationary-negative", seed=17, energy=0.4
    )
    negative_meta = engine.make_run_metadata(f"{RUN_ID}-stationary-negative", 17)
    negative_step, _ = _run_step(
        negative_state,
        negative_meta,
        cue="resource",
        world_event="resource_appears",
    )

    quiet_state = _stationary_state(
        run_id=f"{RUN_ID}-no-resource-control", seed=18, energy=0.4
    )
    quiet_meta = engine.make_run_metadata(f"{RUN_ID}-no-resource-control", 18)
    quiet_step, quiet_command = _run_step(
        quiet_state,
        quiet_meta,
        cue="quiet",
        world_event="quiet_interval",
    )
    quiet_transition = quiet_step.trace["world_transition"]

    non_forage_run_id = f"{RUN_ID}-non-forage-control"
    non_forage_state = engine.initial_state(
        {
            "energy": 0.2,
            "safety": 0.1,
            "connection": 0.0,
            "stimulation": 0.0,
        },
        run_id=non_forage_run_id,
        seed=1,
    )
    non_forage_meta = engine.make_run_metadata(non_forage_run_id, 1)
    non_forage_step, non_forage_command = _run_step(
        non_forage_state,
        non_forage_meta,
        cue="resource",
        world_event="resource_appears",
    )
    non_forage_transition = non_forage_step.trace["world_transition"]

    baseline = _baseline_report(
        positive_step.trace,
        negative_step.trace,
        non_forage_trace=non_forage_step.trace,
    )
    ablation = _food_gain_ablation()
    interaction = positive_step.trace["world_transition"]["resource_interaction"]
    leakage = {
        "schema_version": "ego.life_playground.resource_leakage_scan.v1",
        "producer_function": "verify_ego_v2_p0_resource_interaction_outcome_repair_001a.scan_policy_for_resource_leakage",
        "input_artifacts": _source_inputs(),
        "run_id": RUN_ID,
        "seed_context_episode_ids": {
            "run_seed": RUN_SEED,
            "context_ids": [positive_step.trace["episode_id"]],
        },
        "aggregation_rule": "scan clean candidate policy projection and positive-control payload for forbidden resource instance leakage",
        "code_path_hash": _code_path_hash(),
        "candidate_scan": scan_policy_for_resource_leakage(
            {
                "policy_projection": positive_step.trace["policy_projection"],
                "policy_non_memory_projection": positive_step.trace[
                    "policy_non_memory_projection"
                ],
            },
            instance_id=interaction["instance_id"],
        ),
        "positive_control_scan": scan_policy_for_resource_leakage(
            {"observation": {"instance_id": interaction["instance_id"]}},
            instance_id=interaction["instance_id"],
        ),
    }
    replay = _controller_replay_report()
    negative_interaction = negative_step.trace["world_transition"][
        "resource_interaction"
    ]
    quiet_interaction = quiet_transition["resource_interaction"]
    non_forage_interaction = non_forage_transition["resource_interaction"]
    local_instance_ids = replay["local_recovery"]["resource_instance_ids"]
    causal_iteration_evidence = bool(
        positive_step.trace["world_transition"]["moved"] is False
        and positive_step.trace["energy_after"] == 0.24
        and interaction["food_obtained"] is True
        and negative_interaction["outcome"] == -1.0
        and negative_interaction["food_obtained"] is False
        and quiet_step.trace["selected_action"] == "forage"
        and quiet_step.trace["food_gain"] == 0.0
        and quiet_step.trace["metabolism"]["food_gain"] == 0.0
        and quiet_transition["food_obtained"] is False
        and quiet_interaction["failure_reason"] == "no_resource_event"
        and non_forage_step.trace["selected_action"] == "approach"
        and non_forage_step.trace["food_gain"] == 0.0
        and non_forage_step.trace["metabolism"]["food_gain"] == 0.0
        and non_forage_transition["food_obtained"] is False
        and non_forage_interaction["failure_reason"] == "resource_not_attempted"
        and len(local_instance_ids) == 2
        and len(set(local_instance_ids)) == 2
        and replay["duplicate_command_rejected"] is True
    )
    visual_binding = replay["visual_trace_binding"]
    visual_iteration_evidence = bool(
        visual_binding["invariant_metadata"] is True
        and visual_binding["same_event_display"] is True
        and visual_binding["same_action_display"] is True
        and visual_binding["recorded_result"] == "成功：已获得食物"
        and visual_binding["recorded_food_gain"] == "+0.280"
        and visual_binding["variant_result"] == "失败：未获得食物"
        and visual_binding["variant_failure_reason"] == "资源有害或不可用"
        and visual_binding["variant_food_gain"] == "+0.000"
    )

    trace_records = [
        {"scenario": "stationary_positive", "command": positive_command, "trace": positive_step.trace},
        {"scenario": "stationary_negative", "trace": negative_step.trace},
        {
            "scenario": "no_resource_control",
            "command": quiet_command,
            "trace": quiet_step.trace,
        },
        {
            "scenario": "non_forage_control",
            "command": non_forage_command,
            "trace": non_forage_step.trace,
        },
    ]
    ledger_records = [
        {
            "task_id": TASK_ID,
            "focus_iteration": 1,
            "changed_variable": "resource_interaction_causal_path",
            "producer_function": (
                "verify_ego_v2_p0_resource_interaction_outcome_repair_001a."
                "run_resource_interaction_verification"
            ),
            "input_artifacts": [
                f"trace:{positive_step.trace['trace_hash']}",
                f"trace:{negative_step.trace['trace_hash']}",
                _file_record(Path(__file__)),
            ],
            "run_id": RUN_ID,
            "seed_context_episode_ids": {
                "run_seed": RUN_SEED,
                "context_ids": [
                    positive_step.trace["episode_id"],
                    negative_step.trace["episode_id"],
                    quiet_step.trace["episode_id"],
                    non_forage_step.trace["episode_id"],
                ],
            },
            "aggregation_rule": (
                "stationary positive succeeds, negative/no-resource/non-forage "
                "controls do not gain food, and two command instances remain unique"
            ),
            "code_path_hash": _code_path_hash(),
            "discriminative_evidence_increased": causal_iteration_evidence,
        },
        {
            "task_id": TASK_ID,
            "focus_iteration": 2,
            "changed_variable": "trace_bound_visual_result_expression",
            "producer_function": visual_binding["producer_function"],
            "input_artifacts": deepcopy(visual_binding["input_artifacts"]),
            "run_id": visual_binding["run_id"],
            "seed_context_episode_ids": deepcopy(
                visual_binding["seed_context_episode_ids"]
            ),
            "aggregation_rule": visual_binding["aggregation_rule"],
            "code_path_hash": visual_binding["code_path_hash"],
            "discriminative_evidence_increased": visual_iteration_evidence,
        },
    ]

    _write_json(output / "baseline_comparison.json", baseline)
    _write_json(output / "ablation_report.json", ablation)
    _write_json(output / "leakage_report.json", leakage)
    _write_json(output / "replay_report.json", replay)
    _write_jsonl(output / "trace.jsonl", trace_records)
    _write_jsonl(output / "experiment_ledger.jsonl", ledger_records)
    (output / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
    )

    checks = {
        "stationary_positive_causal_repair": _evidence(
            positive_step.trace["world_transition"]["food_obtained"] is True
            and positive_step.trace["energy_after"] == 0.24
            and interaction["resolved"] is True,
            producer_function="verify_ego_v2_p0_resource_interaction_outcome_repair_001a.run_resource_interaction_verification",
            inputs=[
                _file_record(output / "trace.jsonl"),
                f"command:{positive_command['command_hash']}",
            ],
            context_ids=[positive_step.trace["episode_id"]],
        ),
        "negative_and_no_gain_controls": _evidence(
            negative_interaction["resolved"] is True
            and negative_interaction["outcome"] == -1.0
            and negative_interaction["food_obtained"] is False
            and negative_step.trace["food_gain"] == 0.0
            and negative_interaction["failure_reason"]
            == "harmful_or_unusable_resource"
            and quiet_step.trace["schema_version"]
            == "ego.life_playground.trace.v6"
            and quiet_step.trace["selected_action"] == "forage"
            and quiet_transition["outcome"] is None
            and quiet_transition["food_obtained"] is False
            and quiet_interaction["failure_reason"] == "no_resource_event"
            and quiet_step.trace["food_gain"] == 0.0
            and quiet_step.trace["metabolism"]["food_gain"] == 0.0
            and non_forage_step.trace["schema_version"]
            == "ego.life_playground.trace.v6"
            and non_forage_step.trace["selected_action"] == "approach"
            and non_forage_transition["outcome"] == 1.0
            and non_forage_transition["food_obtained"] is False
            and non_forage_interaction["failure_reason"]
            == "resource_not_attempted"
            and non_forage_step.trace["food_gain"] == 0.0
            and non_forage_step.trace["metabolism"]["food_gain"] == 0.0,
            producer_function=(
                "verify_ego_v2_p0_resource_interaction_outcome_repair_001a."
                "run_resource_interaction_verification"
            ),
            inputs=[_file_record(output / "trace.jsonl")],
            context_ids=[
                negative_step.trace["episode_id"],
                quiet_step.trace["episode_id"],
                non_forage_step.trace["episode_id"],
            ],
        ),
        "resource_instance_identity_and_single_settlement": _evidence(
            interaction["instance_id"]
            == microworld.resource_instance_id_for_command(
                positive_command["command_hash"]
            )
            and same_command_recompute_a == same_command_recompute_b
            and len(
                same_command_recompute_a[0]["private_dynamics"]["outcome_history"]
            )
            == 1
            and len(local_instance_ids) == 2
            and len(set(local_instance_ids)) == 2
            and replay["duplicate_command_rejected"] is True,
            producer_function=(
                "ego_life_playground_v0.microworld.transition_world + "
                "SQLiteEventStore.append_step"
            ),
            inputs=[
                f"command:{positive_command['command_hash']}",
                _file_record(output / "replay_report.json"),
            ],
            context_ids=[positive_step.trace["episode_id"], replay["run_id"]],
        ),
        "hostile_baselines_diverge": _evidence(
            baseline["moved_only"]["candidate_food_obtained"] is True
            and baseline["moved_only"]["baseline_food_obtained"] is False
            and baseline["cue_only"]["negative_candidate_food_obtained"] is False
            and baseline["cue_only"]["negative_baseline_food_obtained"] is True
            and baseline["cue_only"]["non_forage_candidate_food_obtained"] is False
            and baseline["cue_only"]["non_forage_baseline_food_obtained"] is True,
            producer_function="verify_ego_v2_p0_resource_interaction_outcome_repair_001a._baseline_report",
            inputs=[_file_record(output / "baseline_comparison.json")],
            context_ids=[
                positive_step.trace["episode_id"],
                negative_step.trace["episode_id"],
                non_forage_step.trace["episode_id"],
            ],
        ),
        "food_gain_ablation_energy_only": _evidence(
            ablation["food_gain_disabled"]["same_selected_action"] is True
            and ablation["food_gain_disabled"]["same_resource_interaction"] is True
            and ablation["food_gain_disabled"]["canonical_energy_after"] == 0.24
            and ablation["food_gain_disabled"]["ablation_energy_after"] == 0.0,
            producer_function="verify_ego_v2_p0_resource_interaction_outcome_repair_001a._food_gain_ablation",
            inputs=[_file_record(output / "ablation_report.json")],
            context_ids=[ablation["seed_context_episode_ids"]["episode_id"]],
        ),
        "resource_leakage_scan": _evidence(
            leakage["candidate_scan"]["leak_detected"] is False
            and leakage["positive_control_scan"]["leak_detected"] is True
            and bool(leakage["positive_control_scan"]["matches"]),
            producer_function="verify_ego_v2_p0_resource_interaction_outcome_repair_001a.scan_policy_for_resource_leakage",
            inputs=[_file_record(output / "leakage_report.json")],
            context_ids=[positive_step.trace["episode_id"]],
        ),
        "trace_bound_visual_result": _evidence(
            visual_iteration_evidence,
            producer_function=visual_binding["producer_function"],
            inputs=[
                *visual_binding["input_artifacts"],
                _file_record(output / "replay_report.json"),
            ],
            context_ids=[visual_binding["seed_context_episode_ids"]["episode_id"]],
        ),
        "controller_replay_and_tamper_checks": _evidence(
            replay["two_resource_dispatch_committed"] is True
            and replay["fresh_process_x2_matches_local_recovery"] is True
            and replay["duplicate_command_rejected"] is True
            and replay["resource_interaction_tamper_fail_closed"] is True
            and "independent recomputation"
            in str(replay["resource_interaction_tamper_error"])
            and replay["stored_trace_tamper_fail_closed"] is True
            and replay["initial_state_tamper_fail_closed"] is True,
            producer_function="verify_ego_v2_p0_resource_interaction_outcome_repair_001a._controller_replay_report",
            inputs=[_file_record(output / "replay_report.json")],
            context_ids=[replay["seed_context_episode_ids"]["episode_id"]],
        ),
    }

    aggregate = aggregate_checks(checks)
    evidence_artifacts = [
        _file_record(output / name)
        for name in (
            "trace.jsonl",
            "baseline_comparison.json",
            "ablation_report.json",
            "leakage_report.json",
            "replay_report.json",
            "experiment_ledger.jsonl",
            "claim_ceiling.txt",
        )
    ]
    artifact_provenance = {
        "producer_function": (
            "verify_ego_v2_p0_resource_interaction_outcome_repair_001a."
            "run_resource_interaction_verification"
        ),
        "input_artifacts": [*_source_inputs(), *evidence_artifacts],
        "run_id": RUN_ID,
        "seed_context_episode_ids": {
            "run_seed": RUN_SEED,
            "context_ids": [
                positive_step.trace["episode_id"],
                negative_step.trace["episode_id"],
                replay["run_id"],
            ],
        },
        "aggregation_rule": (
            "derive task status only by aggregate_checks over callable computed "
            "evidence records"
        ),
        "code_path_hash": _code_path_hash(),
    }
    failure_manifest = {
        **deepcopy(artifact_provenance),
        "task_id": TASK_ID,
        "verdict": aggregate["verdict"],
        "failed_checks": aggregate["failed_checks"],
        "failure_count": len(aggregate["failed_checks"]),
    }
    progress_checkpoint = {
        **deepcopy(artifact_provenance),
        "task_id": TASK_ID,
        "focus_iterations_completed": [entry["focus_iteration"] for entry in ledger_records],
        "discriminative_evidence_increased": all(
            entry["discriminative_evidence_increased"] for entry in ledger_records
        ),
        "verdict": aggregate["verdict"],
    }
    stage_scorecard = {
        **deepcopy(artifact_provenance),
        "task_id": TASK_ID,
        "stage": "Phase A.1 product repair",
        "claim_ceiling": "Layer 2 repair only",
        "all_checks_pass": aggregate["verdict"] == "pass",
        "failed_checks": aggregate["failed_checks"],
    }
    _write_json(output / "failure_manifest.json", failure_manifest)
    _write_json(output / "progress_checkpoint.json", progress_checkpoint)
    _write_json(output / "stage_scorecard.json", stage_scorecard)

    provisional_result = {
        **deepcopy(artifact_provenance),
        "task_id": TASK_ID,
        "verdict": aggregate["verdict"],
        "claim_ceiling": "Layer 2 repair only",
        "checks": checks,
    }
    _write_json(output / "result.json", provisional_result)

    checks["required_artifacts_present"] = _evidence(
        {path.name for path in output.iterdir()} == REQUIRED_ARTIFACTS,
        producer_function="verify_ego_v2_p0_resource_interaction_outcome_repair_001a.run_resource_interaction_verification",
        inputs=[str(output)],
        context_ids=[TASK_ID],
    )
    aggregate = aggregate_checks(checks)
    failure_manifest["verdict"] = aggregate["verdict"]
    failure_manifest["failed_checks"] = aggregate["failed_checks"]
    failure_manifest["failure_count"] = len(aggregate["failed_checks"])
    progress_checkpoint["verdict"] = aggregate["verdict"]
    stage_scorecard["all_checks_pass"] = aggregate["verdict"] == "pass"
    stage_scorecard["failed_checks"] = aggregate["failed_checks"]
    _write_json(output / "failure_manifest.json", failure_manifest)
    _write_json(output / "progress_checkpoint.json", progress_checkpoint)
    _write_json(output / "stage_scorecard.json", stage_scorecard)

    result = {
        **deepcopy(artifact_provenance),
        "task_id": TASK_ID,
        "verdict": aggregate["verdict"],
        "claim_ceiling": "Layer 2 repair only",
        "checks": checks,
    }
    _write_json(output / "result.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    parser.add_argument("--recover-db")
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)

    if args.recover_db:
        if not args.run_id:
            raise SystemExit("--run-id is required with --recover-db")
        summary = recover_db_summary(args.recover_db, args.run_id)
        json.dump(summary, sys.stdout, ensure_ascii=False, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    if not args.output_dir:
        raise SystemExit("--output-dir is required")
    result = run_resource_interaction_verification(args.output_dir)
    json.dump(result, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
