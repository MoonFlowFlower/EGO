#!/usr/bin/env python3
"""Callable evidence producer for the bounded metabolism/viability repair."""

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

from labs.ego_life_playground_v0 import engine
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore


TASK_ID = "EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A"
RUN_ID = "ego-v2-metabolism-verify"
RUN_SEED = 18
CLAIM_CEILING = (
    "Bounded product-engineering repair only: each explicit V2 tick now pays "
    "passive energy decay plus action cost, only a realized environment-owned "
    "food outcome can replenish energy, critical energy restricts the canonical "
    "action set, and SQLite replay recomputes the same ledger from serialized "
    "state plus ordered commands. This does not establish viability as a "
    "mechanism, learning, memory causality, dynamic causal boundary, "
    "initiative, agency, autonomy, emotion, subjectivity, consciousness, "
    "electronic life, Joi-like existence, or product readiness."
)
REQUIRED_ARTIFACTS = {
    "result.json",
    "trace.jsonl",
    "baseline_comparison.json",
    "ablation_report.json",
    "replay_report.json",
    "failure_manifest.json",
    "progress_checkpoint.json",
    "experiment_ledger.jsonl",
    "stage_scorecard.json",
    "claim_ceiling.txt",
}

# Independent copy of the pre-repair energy-only rule. These values are not
# read from the candidate module, so the baseline remains callable if the live
# predictor or metabolism implementation changes.
LEGACY_ACTION_ENERGY_PRIOR = {
    "approach": -0.02,
    "explore": -0.05,
    "forage": 0.12,
    "rest": 0.09,
    "withdraw": -0.01,
}
LEGACY_CUE_ENERGY_BONUS = {
    ("resource", "forage"): 0.16,
    ("quiet", "rest"): 0.09,
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
        _file_record(REPO_ROOT / "labs/ego_life_playground_v0/controller.py"),
        _file_record(REPO_ROOT / "labs/ego_life_playground_v0/store.py"),
        _file_record(
            REPO_ROOT
            / "docs/codex/tasks/EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A.md"
        ),
    ]


def _code_path_hash() -> str:
    return _sha256(
        _canonical_bytes(
            {
                "candidate_code_path_hash": engine.compute_code_path_hash(),
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


def _legacy_energy_after(
    *,
    energy_before: float,
    cue: str,
    selected_action: str,
    world_outcome: float | None,
) -> float:
    if selected_action not in LEGACY_ACTION_ENERGY_PRIOR:
        raise ValueError(f"legacy baseline action is not supported: {selected_action}")
    delta = LEGACY_ACTION_ENERGY_PRIOR[selected_action]
    delta += LEGACY_CUE_ENERGY_BONUS.get((cue, selected_action), 0.0)
    if world_outcome is not None:
        delta += 0.05 * world_outcome
    return round(max(0.0, min(1.0, energy_before + delta)), 6)


def _make_command(
    state: Mapping[str, Any],
    *,
    cue: str,
    world_event: str,
    interventions: Mapping[str, str] | None = None,
    trigger_source: str = "headless_acceptance",
) -> dict[str, Any]:
    return engine.make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        cue=cue,
        world_event=world_event,
        trigger_source=trigger_source,
        interventions=engine.DEFAULT_INTERVENTIONS
        if interventions is None
        else interventions,
        prev_command_hash=state["last_command_hash"],
    )


def _run_step(
    state: Mapping[str, Any],
    meta: Mapping[str, Any],
    *,
    cue: str,
    world_event: str,
    interventions: Mapping[str, str] | None = None,
    trigger_source: str = "headless_acceptance",
) -> tuple[engine.StepResult, dict[str, Any]]:
    command = _make_command(
        state,
        cue=cue,
        world_event=world_event,
        interventions=interventions,
        trigger_source=trigger_source,
    )
    return engine.compute_step(state, command, meta), command


def _energy_focused_state(run_id: str, seed: int) -> dict[str, Any]:
    return engine.initial_state(
        {
            "energy": 0.4,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.9,
        },
        run_id=run_id,
        seed=seed,
    )


def _negative_resource_trace() -> dict[str, Any]:
    run_id = f"{RUN_ID}-negative-resource"
    state = _energy_focused_state(run_id, seed=17)
    meta = engine.make_run_metadata(run_id, 17)
    step, _ = _run_step(state, meta, cue="resource", world_event="resource_appears")
    return step.trace


def _positive_resource_trace() -> dict[str, Any]:
    run_id = f"{RUN_ID}-positive-resource"
    state = _energy_focused_state(run_id, seed=18)
    meta = engine.make_run_metadata(run_id, 18)
    step, _ = _run_step(state, meta, cue="resource", world_event="resource_appears")
    return step.trace


def _zero_distance_resource_trace() -> dict[str, Any]:
    run_id = f"{RUN_ID}-zero-distance-resource"
    state = _energy_focused_state(run_id, seed=17)
    meta = engine.make_run_metadata(run_id, 17)
    first, _ = _run_step(
        state, meta, cue="resource", world_event="resource_appears"
    )
    second, _ = _run_step(
        first.next_state,
        meta,
        cue="resource",
        world_event="resource_appears",
    )
    return second.trace


def _quiet_decay_traces() -> list[dict[str, Any]]:
    run_id = f"{RUN_ID}-quiet-decay"
    state = engine.initial_state(
        {
            "energy": 0.5,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.9,
        },
        run_id=run_id,
        seed=17,
    )
    meta = engine.make_run_metadata(run_id, 17)
    traces: list[dict[str, Any]] = []
    for _ in range(3):
        step, _ = _run_step(state, meta, cue="quiet", world_event="quiet_interval")
        traces.append(step.trace)
        state = step.next_state
    return traces


def _critical_gate_traces() -> list[dict[str, Any]]:
    run_id = f"{RUN_ID}-critical-gate"
    state = engine.initial_state(
        {
            "energy": 0.16,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.0,
        },
        run_id=run_id,
        seed=17,
    )
    meta = engine.make_run_metadata(run_id, 17)
    traces: list[dict[str, Any]] = []
    for _ in range(2):
        step, _ = _run_step(state, meta, cue="quiet", world_event="quiet_interval")
        traces.append(step.trace)
        state = step.next_state
    return traces


def _positive_food_ablation() -> dict[str, Any]:
    run_id = f"{RUN_ID}-food-ablation"
    state = _energy_focused_state(run_id, seed=18)
    meta = engine.make_run_metadata(run_id, 18)
    canonical, _ = _run_step(state, meta, cue="resource", world_event="resource_appears")
    with patch.object(engine, "FOOD_ENERGY_GAIN", 0.0):
        ablated, _ = _run_step(state, meta, cue="resource", world_event="resource_appears")
    return {
        "schema_version": "ego.life_playground.metabolism_ablation.v1",
        "producer_function": "engine.compute_step with in-memory FOOD_ENERGY_GAIN intervention",
        "input_artifacts": [
            f"state:{engine.state_hash(state)}",
            f"command:{canonical.trace['command']['command_hash']}",
        ],
        "run_id": run_id,
        "seed_context_episode_ids": {
            "run_seed": 18,
            "episode_id": canonical.trace["episode_id"],
        },
        "aggregation_rule": "same serialized state and command, then rerun with food gain zeroed in-memory",
        "code_path_hash": _code_path_hash(),
        "food_gain_disabled": {
            "canonical_food_gain": canonical.trace["food_gain"],
            "canonical_energy_after": canonical.trace["energy_after"],
            "ablation_food_gain": ablated.trace["food_gain"],
            "ablation_energy_after": ablated.trace["energy_after"],
            "same_selected_action": canonical.trace["selected_action"]
            == ablated.trace["selected_action"],
        },
    }


def _recovery_summary(recovered: Any) -> dict[str, Any]:
    payload = {
        "run_id": recovered.run_id,
        "command_count": recovered.command_count,
        "state_hash": engine.state_hash(recovered.state),
        "trace_hashes": [trace["trace_hash"] for trace in recovered.traces],
        "metabolism_ledgers": [
            {
                "energy_before": trace["energy_before"],
                "passive_decay": trace["passive_decay"],
                "action_cost": trace["action_cost"],
                "food_gain": trace["food_gain"],
                "energy_after": trace["energy_after"],
                "downstream_effect": trace["downstream_effect"],
            }
            for trace in recovered.traces
        ],
    }
    return {
        "producer_function": "SQLiteEventStore.recover_run",
        "payload": payload,
        "digest": _sha256(_canonical_bytes(payload)),
    }


def _sqlite_recovery_summary(db_path: Path, run_id: str) -> dict[str, Any]:
    with SQLiteEventStore(db_path) as store:
        return _recovery_summary(store.recover_run(run_id))


def _run_fresh_sqlite_recovery(db_path: Path, run_id: str) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--sqlite-recovery-summary",
            str(db_path),
            "--run-id",
            run_id,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _sqlite_replay_probe() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ego-metabolism-replay-") as temp_name:
        db_path = Path(temp_name) / "replay.sqlite3"
        run_id = f"{RUN_ID}-sqlite-replay"
        initial = _energy_focused_state(run_id, seed=18)
        meta = engine.make_run_metadata(run_id, 18)
        state = deepcopy(initial)
        canonical_traces: list[dict[str, Any]] = []
        with SQLiteEventStore(db_path) as store:
            store.create_run(meta, initial)
            for cue, event in (
                ("resource", "resource_appears"),
                ("quiet", "quiet_interval"),
            ):
                step, command = _run_step(state, meta, cue=cue, world_event=event)
                receipt = store.append_step(command, step.trace)
                if not receipt.committed:
                    raise RuntimeError(f"canonical append failed: {receipt.error}")
                canonical_traces.append(step.trace)
                state = step.next_state
            recovered = store.recover_run(run_id)
            local_summary = _recovery_summary(recovered)
        fresh_process_a = _run_fresh_sqlite_recovery(db_path, run_id)
        fresh_process_b = _run_fresh_sqlite_recovery(db_path, run_id)

        trace_tamper_path = Path(temp_name) / "trace-tamper.sqlite3"
        initial_tamper_path = Path(temp_name) / "initial-tamper.sqlite3"
        shutil.copy2(db_path, trace_tamper_path)
        shutil.copy2(db_path, initial_tamper_path)

        with SQLiteEventStore(trace_tamper_path) as store:
            stored_trace_tamper_fail_closed = False
            tampered = deepcopy(canonical_traces[0])
            tampered["food_gain"] = 0.99
            tampered["metabolism"]["food_gain"] = 0.99
            tampered["trace_hash"] = engine.compute_trace_hash(tampered)
            store.connection.execute(
                "UPDATE traces SET trace_json = ?, trace_hash = ? "
                "WHERE run_id = ? AND sequence = 1",
                (
                    engine.canonical_json(tampered),
                    tampered["trace_hash"],
                    run_id,
                ),
            )
            try:
                store.recover_run(run_id)
            except RecoveryError:
                stored_trace_tamper_fail_closed = True
        with SQLiteEventStore(initial_tamper_path) as tamper_store:
            initial_state_tamper_fail_closed = False
            tampered_initial = deepcopy(initial)
            tampered_initial["organism"]["energy"] = 0.99
            tamper_store.connection.execute(
                "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
                (
                    engine.canonical_json(tampered_initial),
                    engine.canonical_hash(tampered_initial),
                    run_id,
                ),
            )
            try:
                tamper_store.recover_run(run_id)
            except RecoveryError:
                initial_state_tamper_fail_closed = True
    return {
        "producer_function": "_sqlite_replay_probe",
        "command_count": len(canonical_traces),
        "canonical_trace_hashes": [trace["trace_hash"] for trace in canonical_traces],
        "recovered_trace_hashes": [trace["trace_hash"] for trace in recovered.traces],
        "final_state_hash": engine.state_hash(state),
        "recovered_state_hash": engine.state_hash(recovered.state),
        "sqlite_recovery_matches_canonical": recovered.state == state
        and recovered.traces == canonical_traces,
        "local_recovery_summary": local_summary,
        "fresh_process_summaries": [fresh_process_a, fresh_process_b],
        "fresh_process_x2_matches_local_recovery": (
            local_summary == fresh_process_a == fresh_process_b
        ),
        "stored_trace_tamper_fail_closed": stored_trace_tamper_fail_closed,
        "initial_state_tamper_fail_closed": initial_state_tamper_fail_closed,
    }


def _controller_trigger_probe() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ego-metabolism-controller-") as temp_name:
        db_path = Path(temp_name) / "controller.sqlite3"
        with SQLiteEventStore(db_path) as store:
            controller = PlaygroundController(
                store,
                run_id=f"{RUN_ID}-controller",
                seed=17,
                world_seed=17,
            )
            dispatched = controller.dispatch(
                "quiet",
                engine.DEFAULT_INTERVENTIONS,
                trigger_source="ui_step_button",
                world_event="quiet_interval",
            )
            if not dispatched.receipt.committed or dispatched.step is None:
                raise RuntimeError(f"controller dispatch failed: {dispatched.receipt.error}")
            recovered = controller.recover()
    return {
        "producer_function": "PlaygroundController.dispatch -> SQLiteEventStore.recover_run",
        "receipt_committed": dispatched.receipt.committed,
        "trigger_source": dispatched.step.trace["trigger_source"],
        "trace_hash": dispatched.step.trace["trace_hash"],
        "recovered_trace_hash": recovered.traces[0]["trace_hash"],
        "ledger_reconciles": dispatched.step.trace["energy_after"]
        == dispatched.step.trace["metabolism"]["energy_after"],
    }


def _ensure_clean_output_dir(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for child in output.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def run_metabolism_verification(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    _ensure_clean_output_dir(output)
    inputs = _source_inputs()

    negative = _negative_resource_trace()
    positive = _positive_resource_trace()
    zero_distance = _zero_distance_resource_trace()
    quiet = _quiet_decay_traces()
    critical = _critical_gate_traces()
    controller = _controller_trigger_probe()
    ablation = _positive_food_ablation()
    replay_probe = _sqlite_replay_probe()

    trace_records = [
        {"record_type": "trace", "scenario": "negative_resource", "trace": negative},
        {"record_type": "trace", "scenario": "positive_resource", "trace": positive},
        {
            "record_type": "trace",
            "scenario": "zero_distance_resource",
            "trace": zero_distance,
        },
        *[
            {"record_type": "trace", "scenario": "quiet_decay", "index": index, "trace": trace}
            for index, trace in enumerate(quiet, start=1)
        ],
        *[
            {
                "record_type": "trace",
                "scenario": "critical_gate",
                "index": index,
                "trace": trace,
            }
            for index, trace in enumerate(critical, start=1)
        ],
    ]
    _write_jsonl(output / "trace.jsonl", trace_records)

    baseline = {
        "schema_version": "ego.life_playground.metabolism_baseline.v1",
        "producer_function": "_legacy_energy_after",
        "input_artifacts": [
            *inputs,
            f"trace:{negative['trace_hash']}",
            f"trace:{quiet[0]['trace_hash']}",
        ],
        "run_id": RUN_ID,
        "seed_context_episode_ids": {
            "run_seed": RUN_SEED,
            "context_ids": ["resource_negative_outcome", "quiet_decay"],
        },
        "aggregation_rule": "compare repaired energy_after against independent pre-repair heuristic energy update",
        "code_path_hash": _code_path_hash(),
        "legacy_resource_forage_negative_outcome": {
            "legacy_energy_after": _legacy_energy_after(
                energy_before=negative["energy_before"],
                cue=negative["cue"],
                selected_action=negative["selected_action"],
                world_outcome=negative["world_outcome"]["value"],
            ),
            "task_energy_after": negative["energy_after"],
        },
        "legacy_quiet_rest": {
            "legacy_energy_after": _legacy_energy_after(
                energy_before=quiet[0]["energy_before"],
                cue=quiet[0]["cue"],
                selected_action=quiet[0]["selected_action"],
                world_outcome=quiet[0]["world_outcome"]["value"],
            ),
            "task_energy_after": quiet[0]["energy_after"],
        },
    }

    replay = {
        "schema_version": "ego.life_playground.metabolism_replay_report.v1",
        "producer_function": "_sqlite_replay_probe + fresh SQLiteEventStore.recover_run x2",
        "input_artifacts": [*inputs, _file_record(output / "trace.jsonl")],
        "run_id": RUN_ID,
        "seed_context_episode_ids": {
            "run_seed": RUN_SEED,
            "context_ids": ["sqlite_recovery", "fresh_sqlite_process_a", "fresh_sqlite_process_b"],
        },
        "aggregation_rule": "require local sqlite recomputation and two fresh-process recover_run summaries to match byte-for-byte, with independent trace and initial-state tamper clones failing closed",
        "code_path_hash": _code_path_hash(),
        "sqlite_recovery_matches_fresh_process": replay_probe[
            "sqlite_recovery_matches_canonical"
        ]
        and replay_probe["final_state_hash"] == replay_probe["recovered_state_hash"]
        and replay_probe["fresh_process_x2_matches_local_recovery"],
        "fresh_process_runs_equal": replay_probe[
            "fresh_process_x2_matches_local_recovery"
        ],
        "tamper_fail_closed": replay_probe["stored_trace_tamper_fail_closed"]
        and replay_probe["initial_state_tamper_fail_closed"],
        "local_recovery_digest": replay_probe["local_recovery_summary"]["digest"],
        "fresh_process_digests": [
            summary["digest"] for summary in replay_probe["fresh_process_summaries"]
        ],
        "sqlite_probe": replay_probe,
    }

    checks = {
        "monotonic_no_food_decay": _evidence(
            all(after["energy_after"] < before["energy_after"] for before, after in zip(quiet, quiet[1:]))
            and quiet[0]["food_gain"] == quiet[1]["food_gain"] == quiet[2]["food_gain"] == 0.0,
            producer_function="_quiet_decay_traces",
            inputs=inputs,
            context_ids=["quiet_decay"],
        ),
        "negative_or_zero_distance_forage_has_no_food_gain": _evidence(
            negative["food_gain"] == 0.0
            and negative["world_transition"]["food_obtained"] is False
            and zero_distance["selected_action"] == "forage"
            and zero_distance["world_transition"]["moved"] is False
            and zero_distance["world_outcome"]["value"] is None
            and zero_distance["food_gain"] == 0.0
            and zero_distance["energy_after"] < zero_distance["energy_before"],
            producer_function="_negative_resource_trace + _zero_distance_resource_trace",
            inputs=inputs,
            context_ids=["resource_negative_outcome"],
        ),
        "positive_food_outcome_replenishes_by_frozen_amount": _evidence(
            positive["food_gain"] == engine.FOOD_ENERGY_GAIN
            and positive["world_transition"]["food_obtained"] is True
            and positive["selected_action"] == "forage",
            producer_function="_positive_resource_trace",
            inputs=inputs,
            context_ids=["resource_positive_outcome"],
        ),
        "critical_energy_restricts_next_selector_call": _evidence(
            critical[0]["downstream_effect"]["entered_critical"] is True
            and critical[1]["viability_gate"]["active"] is True
            and set(critical[1]["legal_actions"]) <= set(engine.CRITICAL_ENERGY_ALLOWED_ACTIONS),
            producer_function="_critical_gate_traces",
            inputs=inputs,
            context_ids=["critical_gate"],
        ),
        "baseline_shows_pre_repair_false_gain": _evidence(
            baseline["legacy_resource_forage_negative_outcome"]["legacy_energy_after"]
            > baseline["legacy_resource_forage_negative_outcome"]["task_energy_after"]
            and baseline["legacy_quiet_rest"]["legacy_energy_after"]
            > baseline["legacy_quiet_rest"]["task_energy_after"],
            producer_function="_legacy_energy_after",
            inputs=inputs,
            context_ids=["baseline_comparison"],
        ),
        "food_gain_ablation_load_bears": _evidence(
            ablation["food_gain_disabled"]["canonical_food_gain"] > 0.0
            and ablation["food_gain_disabled"]["ablation_food_gain"] == 0.0
            and ablation["food_gain_disabled"]["ablation_energy_after"]
            < ablation["food_gain_disabled"]["canonical_energy_after"],
            producer_function="engine.compute_step with in-memory FOOD_ENERGY_GAIN intervention",
            inputs=inputs,
            context_ids=["food_gain_ablation"],
        ),
        "replay_and_tamper_checks_pass": _evidence(
            replay["sqlite_recovery_matches_fresh_process"] is True
            and replay["fresh_process_runs_equal"] is True
            and replay["tamper_fail_closed"] is True,
            producer_function="_sqlite_replay_probe + fresh SQLiteEventStore.recover_run x2",
            inputs=inputs,
            context_ids=["sqlite_replay", "fresh_process"],
        ),
        "real_controller_dispatch_exercises_live_path": _evidence(
            controller["receipt_committed"] is True
            and controller["trigger_source"] == "ui_step_button"
            and controller["trace_hash"] == controller["recovered_trace_hash"]
            and controller["ledger_reconciles"] is True,
            producer_function="PlaygroundController.dispatch -> SQLiteEventStore.recover_run",
            inputs=inputs,
            context_ids=["controller_dispatch"],
        ),
    }
    aggregation = aggregate_checks(checks)

    result = {
        "schema_version": "ego.life_playground.metabolism_result.v1",
        "task_id": TASK_ID,
        "producer_function": "run_metabolism_verification",
        "input_artifacts": [*inputs, _file_record(output / "trace.jsonl")],
        "run_id": RUN_ID,
        "seed_context_episode_ids": {
            "run_seed": RUN_SEED,
            "context_ids": [
                "negative_resource",
                "positive_resource",
                "quiet_decay",
                "critical_gate",
                "sqlite_replay",
                "controller_dispatch",
            ],
        },
        "aggregation_rule": "pass iff every named computed repair check is true",
        "code_path_hash": _code_path_hash(),
        "checks": checks,
        "verdict": aggregation["verdict"],
        "failed_checks": aggregation["failed_checks"],
        "claim_ceiling": CLAIM_CEILING,
    }
    progress_checkpoint = {
        "schema_version": "ego.life_playground.metabolism_progress_checkpoint.v1",
        "producer_function": "run_metabolism_verification",
        "input_artifacts": [*inputs, _file_record(output / "result.json")] if (output / "result.json").exists() else inputs,
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED, "focus_iteration": 2},
        "aggregation_rule": "second scoped checkpoint after product coupling and replay-provenance hardening",
        "code_path_hash": _code_path_hash(),
        "focus_iteration": 2,
        "phase": "A",
        "verdict": aggregation["verdict"],
        "changed_variable": "fresh_process_replay_and_tamper_provenance",
        "stop_condition_triggered": None,
    }
    stage_scorecard = {
        "schema_version": "ego.life_playground.metabolism_stage_scorecard.v1",
        "producer_function": "run_metabolism_verification",
        "input_artifacts": inputs,
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED, "focus_iteration": 2},
        "aggregation_rule": "stage score equals scoped verifier verdict after two single-variable iterations",
        "code_path_hash": _code_path_hash(),
        "focus_iteration": 2,
        "phase": "A",
        "verdict": aggregation["verdict"],
        "failed_checks": aggregation["failed_checks"],
    }
    failure_manifest = {
        "schema_version": "ego.life_playground.metabolism_failure_manifest.v1",
        "producer_function": "run_metabolism_verification.failure_manifest",
        "input_artifacts": inputs,
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED},
        "aggregation_rule": "preserve scoped failed checks and bounded negative controls without upgrading the claim",
        "code_path_hash": _code_path_hash(),
        "scoped_verdict_failures": aggregation["failed_checks"],
        "preserved_negative_evidence": {
            "legacy_resource_forage_negative_outcome": baseline[
                "legacy_resource_forage_negative_outcome"
            ],
            "legacy_quiet_rest": baseline["legacy_quiet_rest"],
        },
    }
    ledger_records = [
        {
            "schema_version": "ego.life_playground.metabolism_experiment_ledger_entry.v1",
            "producer_function": "run_metabolism_verification",
            "task_id": TASK_ID,
            "run_id": RUN_ID,
            "focus_iteration": 1,
            "phase": "A",
            "changed_variable": "metabolism_viability_coupling",
            "verdict": aggregation["verdict"],
            "failed_checks": aggregation["failed_checks"],
            "code_path_hash": _code_path_hash(),
        },
        {
            "schema_version": "ego.life_playground.metabolism_experiment_ledger_entry.v1",
            "producer_function": "run_metabolism_verification",
            "task_id": TASK_ID,
            "run_id": RUN_ID,
            "focus_iteration": 2,
            "phase": "A",
            "changed_variable": "fresh_process_replay_and_tamper_provenance",
            "verdict": aggregation["verdict"],
            "failed_checks": aggregation["failed_checks"],
            "code_path_hash": _code_path_hash(),
        },
    ]

    _write_json(output / "baseline_comparison.json", baseline)
    _write_json(output / "ablation_report.json", ablation)
    _write_json(output / "replay_report.json", replay)
    _write_json(output / "failure_manifest.json", failure_manifest)
    _write_json(output / "result.json", result)
    _write_json(output / "progress_checkpoint.json", progress_checkpoint)
    _write_json(output / "stage_scorecard.json", stage_scorecard)
    _write_jsonl(output / "experiment_ledger.jsonl", ledger_records)
    (output / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
    )

    actual = {path.name for path in output.iterdir() if path.is_file()}
    if actual != REQUIRED_ARTIFACTS:
        raise RuntimeError(
            f"metabolism verification output set is not exact: {sorted(actual)}"
        )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--sqlite-recovery-summary",
        type=Path,
        help="Open one SQLite database in this fresh process and recompute a run.",
    )
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    if args.sqlite_recovery_summary is not None:
        if not args.run_id:
            raise SystemExit("--run-id is required with --sqlite-recovery-summary")
        print(
            json.dumps(
                _sqlite_recovery_summary(args.sqlite_recovery_summary, args.run_id),
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    if args.output_dir is None:
        raise SystemExit("--output-dir is required unless SQLite summary mode is used")
    result = run_metabolism_verification(args.output_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
