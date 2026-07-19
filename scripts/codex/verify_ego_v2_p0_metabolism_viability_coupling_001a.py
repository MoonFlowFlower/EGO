#!/usr/bin/env python3
"""Callable evidence producer for the bounded V2 metabolism/viability repair."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
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
RUN_ID = "ego-v2-metabolism-viability-001"
RUN_SEED = 18
CLAIM_CEILING = (
    "Bounded local V2 product engineering repair only: each canonical tick now pays "
    "a passive decay, action cost is charged through the sole reducer/replay path, "
    "only environment-owned moved positive forage outcomes replenish energy, and "
    "critical energy causes a real reducer-side capability restriction. Evidence is "
    "limited to this explicit default-off product path and frozen distributions; it "
    "does not establish viability as a mechanism, learning, dynamic causal boundary, "
    "agency, subjectivity, consciousness, electronic life, Joi-like existence, "
    "product readiness, or stable user benefit."
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
TRACE_FIELDS = (
    "energy_before",
    "passive_decay",
    "action_cost",
    "food_gain",
    "energy_after",
    "downstream_effect",
    "viability_gate",
    "metabolism",
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _file_record(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": _sha256(raw)}


def _code_path_hash() -> str:
    return _sha256(
        _canonical_bytes(
            {
                "candidate_code_path_hash": engine.compute_code_path_hash(),
                "verifier_sha256": _file_record(Path(__file__))["sha256"],
            }
        )
    )


def _evidence(value: bool, *, producer_function: str, inputs: list[Any]) -> dict[str, Any]:
    return {
        "evidence_record_type": "computed_evidence",
        "producer_function": producer_function,
        "input_artifacts": deepcopy(inputs),
        "run_id": RUN_ID,
        "seed_context_episode_ids": {
            "run_seed": RUN_SEED,
            "context_ids": [
                "no_food_monotonic",
                "positive_food",
                "critical_gate",
                "sqlite_replay",
                "controller_dispatch",
            ],
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


def _step(
    state: dict[str, Any],
    meta: dict[str, Any],
    *,
    cue: str,
    world_event: str,
    trigger_source: str = "headless_acceptance",
) -> tuple[engine.StepResult, dict[str, Any]]:
    command = engine.make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        cue=cue,
        world_event=world_event,
        trigger_source=trigger_source,
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=state["last_command_hash"],
    )
    return engine.compute_step(state, command, meta), command


def _legacy_energy_after(*, energy_before: float, cue: str, action: str) -> float:
    delta = float(engine.ACTION_PRIORS[action]["energy"])
    delta += float(engine.CUE_BONUSES.get(cue, {}).get(action, {}).get("energy", 0.0))
    return round(max(0.0, min(1.0, energy_before + delta)), 6)


def _summary_from_recovery(recovered: Any) -> dict[str, Any]:
    return {
        "producer_function": "SQLiteEventStore.recover_run",
        "run_id": recovered.run_id,
        "command_count": recovered.command_count,
        "final_state_hash": engine.state_hash(recovered.state),
        "selected_actions": [trace["selected_action"] for trace in recovered.traces],
        "trace_hashes": [trace["trace_hash"] for trace in recovered.traces],
        "energy_path": [trace["energy_after"] for trace in recovered.traces],
        "food_gains": [trace["food_gain"] for trace in recovered.traces],
        "downstream_effects": [
            trace["downstream_effect"]["effect"] for trace in recovered.traces
        ],
    }


def _fresh_process_summary(db_path: Path, run_id: str) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__)),
        "--helper",
        "sqlite-summary",
        "--db",
        str(db_path),
        "--run-id",
        run_id,
    ]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"fresh process summary failed: rc={completed.returncode} stderr={completed.stderr.strip()}"
        )
    return json.loads(completed.stdout)


def _fresh_process_summary_main(db_path: Path, run_id: str) -> int:
    with SQLiteEventStore(db_path) as store:
        recovered = store.recover_run(run_id)
    print(
        json.dumps(_summary_from_recovery(recovered), ensure_ascii=False, sort_keys=True)
    )
    return 0


def _run_no_food_monotonic() -> dict[str, Any]:
    run_id = "metabolism-verifier-no-food"
    state = engine.initial_state(
        {
            "energy": 0.5,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.0,
        },
        run_id=run_id,
        seed=17,
    )
    meta = engine.make_run_metadata(run_id, 17)
    traces: list[dict[str, Any]] = []
    energies = [state["organism"]["energy"]]
    for _ in range(3):
        result, _ = _step(state, meta, cue="quiet", world_event="quiet_interval")
        traces.append(result.trace)
        state = result.next_state
        energies.append(state["organism"]["energy"])
    return {
        "producer_function": "_run_no_food_monotonic",
        "energies": energies,
        "traces": traces,
        "strictly_decreasing": all(
            after < before for before, after in zip(energies, energies[1:])
        ),
    }


def _run_positive_food() -> dict[str, Any]:
    run_id = "metabolism-verifier-positive-food"
    state = engine.initial_state(
        {
            "energy": 0.4,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.9,
        },
        run_id=run_id,
        seed=18,
    )
    meta = engine.make_run_metadata(run_id, 18)
    result, _ = _step(
        state, meta, cue="resource", world_event="resource_appears"
    )
    return {
        "producer_function": "_run_positive_food",
        "trace": result.trace,
        "next_state": result.next_state,
    }


def _run_negative_food() -> dict[str, Any]:
    run_id = "metabolism-verifier-negative-food"
    state = engine.initial_state(
        {
            "energy": 0.4,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.9,
        },
        run_id=run_id,
        seed=17,
    )
    meta = engine.make_run_metadata(run_id, 17)
    result, _ = _step(
        state, meta, cue="resource", world_event="resource_appears"
    )
    return {
        "producer_function": "_run_negative_food",
        "trace": result.trace,
        "next_state": result.next_state,
    }


def _run_critical_gate() -> dict[str, Any]:
    run_id = "metabolism-verifier-critical-gate"
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
    crossing, _ = _step(state, meta, cue="quiet", world_event="quiet_interval")
    restricted, _ = _step(
        crossing.next_state, meta, cue="quiet", world_event="quiet_interval"
    )
    return {
        "producer_function": "_run_critical_gate",
        "crossing_trace": crossing.trace,
        "restricted_trace": restricted.trace,
    }


def _run_sqlite_replay() -> dict[str, Any]:
    run_id = "metabolism-verifier-sqlite"
    with tempfile.TemporaryDirectory(prefix="ego-metabolism-verifier-") as temp_name:
        root = Path(temp_name)
        db_path = root / "metabolism.sqlite3"
        meta = engine.make_run_metadata(run_id, 18)
        state = engine.initial_state(
            {
                "energy": 0.4,
                "safety": 0.9,
                "connection": 0.9,
                "stimulation": 0.9,
            },
            run_id=run_id,
            seed=18,
        )
        commands: list[dict[str, Any]] = []
        traces: list[dict[str, Any]] = []
        with SQLiteEventStore(db_path) as store:
            store.create_run(meta, state)
            for cue, world_event in (
                ("resource", "resource_appears"),
                ("quiet", "quiet_interval"),
                ("quiet", "quiet_interval"),
            ):
                result, command = _step(
                    state, meta, cue=cue, world_event=world_event
                )
                receipt = store.append_step(command, result.trace)
                if receipt.committed is not True:
                    raise RuntimeError(f"unexpected commit failure: {receipt.error}")
                commands.append(command)
                traces.append(result.trace)
                state = result.next_state
            recovered = store.recover_run(run_id)
        fresh_a = _fresh_process_summary(db_path, run_id)
        fresh_b = _fresh_process_summary(db_path, run_id)

        tamper_db = root / "metabolism-tamper.sqlite3"
        tamper_db.write_bytes(db_path.read_bytes())
        tamper_error = None
        with SQLiteEventStore(tamper_db) as tampered_store:
            tampered = deepcopy(traces[0])
            tampered["food_gain"] = 0.99
            tampered["metabolism"]["food_gain"] = 0.99
            tampered["trace_hash"] = engine.compute_trace_hash(tampered)
            tampered_store.connection.execute(
                "UPDATE traces SET trace_json = ?, trace_hash = ? "
                "WHERE run_id = ? AND sequence = 1",
                (
                    engine.canonical_json(tampered),
                    tampered["trace_hash"],
                    run_id,
                ),
            )
            try:
                tampered_store.recover_run(run_id)
            except RecoveryError as exc:
                tamper_error = str(exc)

        connection = sqlite3.connect(db_path)
        try:
            counts = {
                table: int(
                    connection.execute(
                        f"SELECT COUNT(*) FROM {table} WHERE run_id = ?", (run_id,)
                    ).fetchone()[0]
                )
                for table in ("runs", "commands", "traces")
            }
        finally:
            connection.close()

        return {
            "producer_function": "_run_sqlite_replay",
            "run_id": run_id,
            "db_path": str(db_path),
            "row_counts": counts,
            "recovered": _summary_from_recovery(recovered),
            "fresh_process_a": fresh_a,
            "fresh_process_b": fresh_b,
            "tamper_error": tamper_error,
            "serialized_command_count": len(commands),
        }


def _run_controller_dispatch() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ego-metabolism-controller-") as temp_name:
        db_path = Path(temp_name) / "controller.sqlite3"
        with SQLiteEventStore(db_path) as store:
            controller = PlaygroundController(
                store,
                run_id="metabolism-verifier-controller",
                seed=17,
                world_seed=17,
            )
            dispatched = controller.dispatch(
                "quiet",
                engine.DEFAULT_INTERVENTIONS,
                trigger_source="ui_step_button",
                world_event="quiet_interval",
            )
            recovered = controller.recover()
        return {
            "producer_function": "_run_controller_dispatch",
            "receipt": {
                "committed": dispatched.receipt.committed,
                "sequence": dispatched.receipt.sequence,
                "error": dispatched.receipt.error,
            },
            "trace": None if dispatched.step is None else dispatched.step.trace,
            "recovered": _summary_from_recovery(recovered),
        }


def run_metabolism_verification(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    inputs = [_file_record(Path(__file__))]

    monotonic = _run_no_food_monotonic()
    negative = _run_negative_food()
    positive = _run_positive_food()
    critical = _run_critical_gate()
    replay = _run_sqlite_replay()
    controller = _run_controller_dispatch()

    with (output / "trace.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for trace in (
            *monotonic["traces"],
            negative["trace"],
            positive["trace"],
            critical["crossing_trace"],
            critical["restricted_trace"],
            controller["trace"],
        ):
            handle.write(
                json.dumps(
                    {"record_type": "trace", "trace": trace},
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )

    baseline = {
        "schema_version": "ego.metabolism_viability.baseline_comparison.v1",
        "producer_function": "run_metabolism_verification.baseline_comparison",
        "input_artifacts": inputs,
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED},
        "aggregation_rule": "compare the task reducer against an independent legacy heuristic energy equation on fixed counterexamples",
        "code_path_hash": _code_path_hash(),
        "legacy_resource_forage_negative_outcome": {
            "energy_before": negative["trace"]["energy_before"],
            "legacy_energy_after": _legacy_energy_after(
                energy_before=negative["trace"]["energy_before"],
                cue="resource",
                action="forage",
            ),
            "task_energy_after": negative["trace"]["energy_after"],
            "realized_outcome": negative["trace"]["world_outcome"]["value"],
        },
        "legacy_quiet_rest": {
            "energy_before": monotonic["traces"][0]["energy_before"],
            "legacy_energy_after": _legacy_energy_after(
                energy_before=monotonic["traces"][0]["energy_before"],
                cue="quiet",
                action="rest",
            ),
            "task_energy_after": monotonic["traces"][0]["energy_after"],
            "selected_action": monotonic["traces"][0]["selected_action"],
        },
    }

    positive_state = engine.initial_state(
        {
            "energy": 0.4,
            "safety": 0.9,
            "connection": 0.9,
            "stimulation": 0.9,
        },
        run_id="metabolism-verifier-ablation",
        seed=18,
    )
    positive_meta = engine.make_run_metadata("metabolism-verifier-ablation", 18)
    canonical_step, _ = _step(
        positive_state, positive_meta, cue="resource", world_event="resource_appears"
    )
    with patch.object(engine, "FOOD_ENERGY_GAIN", 0.0):
        ablated_step, _ = _step(
            positive_state,
            positive_meta,
            cue="resource",
            world_event="resource_appears",
        )
    ablation = {
        "schema_version": "ego.metabolism_viability.ablation_report.v1",
        "producer_function": "run_metabolism_verification.ablation_report",
        "input_artifacts": inputs,
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED, "context_ids": ["food_gain_disabled"]},
        "aggregation_rule": "rerun the same realized food outcome under an in-memory food_gain=0 reducer intervention",
        "code_path_hash": _code_path_hash(),
        "food_gain_disabled": {
            "canonical_food_gain": canonical_step.trace["food_gain"],
            "canonical_energy_after": canonical_step.trace["energy_after"],
            "ablation_food_gain": ablated_step.trace["food_gain"],
            "ablation_energy_after": ablated_step.trace["energy_after"],
            "same_world_outcome": canonical_step.trace["world_outcome"]
            == ablated_step.trace["world_outcome"],
        },
    }

    replay_report = {
        "schema_version": "ego.metabolism_viability.replay_report.v1",
        "producer_function": "run_metabolism_verification.replay_report",
        "input_artifacts": [*inputs, _file_record(output / "trace.jsonl")],
        "run_id": replay["run_id"],
        "seed_context_episode_ids": {"run_seed": RUN_SEED},
        "aggregation_rule": "recover the SQLite run from serialized initial state plus ordered commands, require fresh-process x2 equality, and require tamper to fail closed",
        "code_path_hash": _code_path_hash(),
        "row_counts": replay["row_counts"],
        "serialized_command_count": replay["serialized_command_count"],
        "sqlite_recovery_matches_fresh_process": replay["recovered"]
        == replay["fresh_process_a"],
        "fresh_process_runs_equal": replay["fresh_process_a"]
        == replay["fresh_process_b"],
        "tamper_fail_closed": type(replay["tamper_error"]) is str
        and "independent recomputation" in replay["tamper_error"],
        "recovered": replay["recovered"],
        "fresh_process_a": replay["fresh_process_a"],
        "fresh_process_b": replay["fresh_process_b"],
        "tamper_error": replay["tamper_error"],
    }

    checks = {
        "no_food_ticks_monotonic_energy_decay": _evidence(
            monotonic["strictly_decreasing"]
            and all(trace["food_gain"] == 0.0 for trace in monotonic["traces"]),
            producer_function="_run_no_food_monotonic",
            inputs=inputs,
        ),
        "no_real_food_outcome_no_gain": _evidence(
            negative["trace"]["selected_action"] == "forage"
            and negative["trace"]["world_transition"]["food_obtained"] is False
            and negative["trace"]["food_gain"] == 0.0
            and negative["trace"]["energy_after"] < negative["trace"]["energy_before"],
            producer_function="_run_negative_food",
            inputs=inputs,
        ),
        "real_food_outcome_exact_gain": _evidence(
            positive["trace"]["selected_action"] == "forage"
            and positive["trace"]["world_transition"]["food_obtained"] is True
            and positive["trace"]["food_gain"] == engine.FOOD_ENERGY_GAIN
            and positive["trace"]["energy_after"] == 0.64,
            producer_function="_run_positive_food",
            inputs=inputs,
        ),
        "critical_energy_has_real_downstream_capability_restriction": _evidence(
            critical["crossing_trace"]["downstream_effect"]["entered_critical"] is True
            and critical["restricted_trace"]["viability_gate"]["active"] is True
            and set(critical["restricted_trace"]["legal_actions"])
            <= set(engine.CRITICAL_ENERGY_ALLOWED_ACTIONS)
            and {
                action
                for action, candidate in {
                    item["action"]: item for item in critical["restricted_trace"]["candidates"]
                }.items()
                if "critical_energy_capability_restriction" in candidate["gate_reasons"]
            }
            == {"approach", "explore"},
            producer_function="_run_critical_gate",
            inputs=inputs,
        ),
        "trace_contains_required_ledger_fields": _evidence(
            all(
                all(field in trace for field in TRACE_FIELDS)
                and trace["metabolism"]["producer_function"]
                == "ego_life_playground_v0.engine.compute_metabolism_ledger"
                and type(trace["metabolism"]["input_artifacts"]) is list
                and type(trace["metabolism"]["run_id"]) is str
                and type(trace["metabolism"]["seed"]) is int
                and type(trace["metabolism"]["episode_id"]) is str
                and type(trace["metabolism"]["aggregation_rule"]) is str
                and type(trace["metabolism"]["code_path_hash"]) is str
                for trace in (
                    *monotonic["traces"],
                    negative["trace"],
                    positive["trace"],
                    critical["crossing_trace"],
                    critical["restricted_trace"],
                    controller["trace"],
                )
            ),
            producer_function="run_metabolism_verification.trace_field_scan",
            inputs=inputs,
        ),
        "sqlite_replay_recomputes_from_serialized_state_and_commands": _evidence(
            replay_report["sqlite_recovery_matches_fresh_process"] is True
            and replay["row_counts"]["commands"] == replay["row_counts"]["traces"]
            == replay["serialized_command_count"],
            producer_function="_run_sqlite_replay",
            inputs=inputs,
        ),
        "fresh_process_x2_consistent": _evidence(
            replay_report["fresh_process_runs_equal"] is True,
            producer_function="_fresh_process_summary",
            inputs=inputs,
        ),
        "tamper_failure_closes": _evidence(
            replay_report["tamper_fail_closed"] is True,
            producer_function="_run_sqlite_replay",
            inputs=inputs,
        ),
        "real_controller_dispatch_commits_and_recovers": _evidence(
            controller["receipt"]["committed"] is True
            and controller["recovered"]["command_count"] == 1
            and controller["recovered"]["trace_hashes"] == [controller["trace"]["trace_hash"]],
            producer_function="_run_controller_dispatch",
            inputs=inputs,
        ),
    }
    aggregation = aggregate_checks(checks)

    progress_checkpoint = {
        "task_id": TASK_ID,
        "focus_iteration": 1,
        "phase": "Phase A",
        "status": aggregation["verdict"],
        "verifier": "run_metabolism_verification",
        "next_frontier": (
            "Stop at Phase B authorization boundary; do not run science-lane headroom work without route authorization."
        ),
        "code_path_hash": _code_path_hash(),
    }
    scorecard = {
        "task_id": TASK_ID,
        "focus_iteration": 1,
        "verdict": aggregation["verdict"],
        "failed_checks": aggregation["failed_checks"],
        "mainline_target": "existing explicit default-off V2 product chain only",
        "enabled_state": "explicit Step/Run only",
        "claim_ceiling": CLAIM_CEILING,
        "code_path_hash": _code_path_hash(),
    }
    ledger_entry = {
        "experiment_id": f"{TASK_ID}-iter-1",
        "focus_iteration": 1,
        "hypothesis": "one reducer-side metabolism ledger plus a low-energy gate repairs the product-only viability coupling defect",
        "action_type": "product_engineering_repair_verification",
        "changed_paths": [
            "labs/ego_life_playground_v0/engine.py",
            "labs/ego_life_playground_v0/microworld.py",
            "tests/test_ego_v2_p0_metabolism_viability_coupling_001a.py",
            "tests/test_ego_life_playground_v0.py",
            "tests/test_ego_life_playground_v2_microworld.py",
            "scripts/codex/verify_ego_v2_p0_metabolism_viability_coupling_001a.py",
            "scripts/tests/test_verify_ego_v2_p0_metabolism_viability_coupling_001a.py",
        ],
        "eval_summary": {
            "verdict": aggregation["verdict"],
            "failed_checks": aggregation["failed_checks"],
        },
        "reviewer_verdict": (
            "success_reached" if aggregation["verdict"] == "pass" else "needs_more_implementation"
        ),
        "next_frontier": progress_checkpoint["next_frontier"],
        "code_path_hash": _code_path_hash(),
    }
    failure_manifest = {
        "schema_version": "ego.metabolism_viability.failure_manifest.v1",
        "producer_function": "run_metabolism_verification.failure_manifest",
        "input_artifacts": inputs,
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED},
        "aggregation_rule": "preserve baseline shortcut evidence and scoped verification failures without upgrading claims",
        "code_path_hash": _code_path_hash(),
        "scoped_verdict_failures": aggregation["failed_checks"],
        "preserved_negative_evidence": {
            "legacy_shortcut_can_fake_energy_gain": baseline[
                "legacy_resource_forage_negative_outcome"
            ]["legacy_energy_after"]
            > baseline["legacy_resource_forage_negative_outcome"]["task_energy_after"],
            "legacy_quiet_rest_shortcut": baseline["legacy_quiet_rest"][
                "legacy_energy_after"
            ]
            > baseline["legacy_quiet_rest"]["task_energy_after"],
        },
        "full_repository_suite": "not_claimed_by_this_scoped_verifier",
    }
    result = {
        "schema_version": "ego.metabolism_viability.result.v1",
        "task_id": TASK_ID,
        "producer_function": "run_metabolism_verification",
        "input_artifacts": [*inputs, _file_record(output / "trace.jsonl")],
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED},
        "aggregation_rule": "pass iff every named monotonic decay, real food gain, critical restriction, replay, tamper, and controller-path check is true",
        "code_path_hash": _code_path_hash(),
        "checks": checks,
        "verdict": aggregation["verdict"],
        "failed_checks": aggregation["failed_checks"],
        "claim_ceiling": CLAIM_CEILING,
    }

    _write_json(output / "baseline_comparison.json", baseline)
    _write_json(output / "ablation_report.json", ablation)
    _write_json(output / "replay_report.json", replay_report)
    _write_json(output / "failure_manifest.json", failure_manifest)
    _write_json(output / "progress_checkpoint.json", progress_checkpoint)
    _write_json(output / "stage_scorecard.json", scorecard)
    _write_json(output / "result.json", result)
    with (output / "experiment_ledger.jsonl").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(json.dumps(ledger_entry, ensure_ascii=False, sort_keys=True) + "\n")
    (output / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
    )

    actual = {path.name for path in output.iterdir() if path.is_file()}
    if actual != REQUIRED_ARTIFACTS:
        raise RuntimeError(
            f"metabolism verification artifact set is not exact: {sorted(actual)}"
        )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--helper", choices=("sqlite-summary",))
    parser.add_argument("--db", type=Path)
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)

    if args.helper == "sqlite-summary":
        if args.db is None or args.run_id is None:
            raise SystemExit("--helper sqlite-summary requires --db and --run-id")
        return _fresh_process_summary_main(args.db, args.run_id)

    if args.output_dir is None:
        raise SystemExit("--output-dir is required unless --helper is used")
    result = run_metabolism_verification(args.output_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
