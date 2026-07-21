#!/usr/bin/env python3
"""Callable engineering-evidence producer for Visual Life Card C.

The verifier deliberately preserves the cheap explanation.  It measures the
sixteen-life reducer, persistence, UI, replay, baseline, and hostile controls; it
does not turn any of those observations into a science adjudication.
"""

from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import tkinter as tk
from typing import Any, Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import claims as claim_memory
from labs.ego_life_playground_v0 import engine, microworld
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.microworld import reset_world_for_life
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore
from labs.ego_life_playground_v0.terminal import TerminalPlayground, build_terminal_snapshot
from labs.ego_life_playground_v0.visual_console import PlaygroundWindow


TASK_ID = "EGO-V2-P0-VISUAL-LIFE-CARD-C-001A"
RUN_ID = "ego-v2-card-c-verify"
POLICY_SEED = 17
WORLD_SEED = 30
CLAIM_CEILING = (
    "Engineering lifecycle evidence only (science_weight=0): the local explicit V2 "
    "product path computes death/censor, pure respawn, sixteen-life termination, exact "
    "carry/reset receipts, SQLite recovery, Terminal/Tk triggers, independent scripted "
    "baseline comparison, a test-only no-carry intervention, leakage controls, and "
    "fresh-process replay. Science adjudication is unauthorized. This does not establish "
    "electronic life, subjectivity, consciousness, emotion, agency, autonomy, general "
    "learning, memory causality, mechanism validity, or stable user benefit."
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
    / "docs/codex/tasks/EGO-V2-P0-VISUAL-LIFE-CONTRACT-001A/CARD_C_FOUR_LIFE_LIFECYCLE.md"
)
CONTRACT_PATH = (
    REPO_ROOT
    / "docs/codex/tasks/EGO-V2-P0-VISUAL-LIFE-CONTRACT-001A/PRODUCT_CONTRACT.md"
)
COLLISION_PATH = (
    REPO_ROOT
    / "docs/codex/tasks/EGO-V2-P0-VISUAL-LIFE-CONTRACT-001A/COLLISION_RECORD.md"
)
SOURCE_PATHS = [
    REPO_ROOT / "labs/ego_life_playground_v0/claims.py",
    REPO_ROOT / "labs/ego_life_playground_v0/controller.py",
    REPO_ROOT / "labs/ego_life_playground_v0/engine.py",
    REPO_ROOT / "labs/ego_life_playground_v0/microworld.py",
    REPO_ROOT / "labs/ego_life_playground_v0/store.py",
    REPO_ROOT / "labs/ego_life_playground_v0/terminal.py",
    REPO_ROOT / "labs/ego_life_playground_v0/visual_console.py",
    REPO_ROOT / "scripts/run_ego_life_playground_v0.py",
    CARD_PATH,
    CONTRACT_PATH,
    COLLISION_PATH,
    Path(__file__),
]
LOGICAL_TRACE_PATH = "artifacts/EGO-V2-P0-VISUAL-LIFE-CARD-C-001A/trace.jsonl"

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
        "engineering_failures",
        "disposition",
        "positive_control_detected",
        "failed_closed",
        "invoked",
        "matched",
        "observable_equivalent",
        "behavior_equivalent",
        "retained_memory_equivalent",
        "fresh_process_match",
        "policy_invoked",
        "matches_expected",
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
POSITIVE_CONTROL_PAYLOAD = {
    "life_index": 99,
    "seed": 123456,
    "token_mapping": {"v0": "resource"},
}
ACCEPTANCE_GATE_IDS = [
    "declared_lifecycle_scenarios_observed",
    "death_respawn_next_action_chain",
    "censor_respawn_chain",
    "life_sixteen_terminal_reject",
    "real_terminal_controller_sqlite_path",
    "real_tk_run_controller_sqlite_path",
    "pure_respawn_carry_reset_exact",
    "independent_scripted_respawn_baseline_reported",
    "no_carry_ablation_executed",
    "policy_projection_leakage_scan_clean_positive_control_fires",
    "replay_two_fresh_processes_match",
    "replay_tamper_controls_fail_closed",
    "single_controller_reducer_store_path",
    "recursive_provenance_present",
]

CARRY_COMPONENTS = (
    "model",
    "memory_schema_version",
    "memory_episodic",
    "memory_consolidated",
    "memory_claim_events",
    "memory_competing_claims",
    "token_mapping",
)
RESET_COMPONENTS = (
    "organism",
    "world",
    "agent_position",
    "agent_facing",
    "object_positions",
    "object_spawn_counts",
    "object_injection_counts",
    "current_goal",
    "goal_completed_latches",
    "last_action",
    "episode_tick",
    "working_spatial_state",
)
BASELINE_INITIAL_ORGANISM = {
    "energy": 0.45,
    "safety": 0.62,
    "connection": 0.50,
    "stimulation": 0.43,
}
BASELINE_TARGET_LEVEL = 0.72


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
    run_id: str = RUN_ID,
    **fields: Any,
) -> dict[str, Any]:
    return {
        **_provenance(
            producer_function=producer_function,
            input_artifacts=input_artifacts,
            seed_context_episode_ids=seed_context_episode_ids,
            aggregation_rule=aggregation_rule,
            run_id=run_id,
        ),
        **deepcopy(fields),
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
            if record_type == EVIDENCE_RECORD_TYPE or has_signal or has_any_provenance:
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
            aggregation_rule=(
                "fail closed on any nested evidence signal missing full provenance and "
                "on any raw_data record carrying an evidence signal"
            ),
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


def _active_life_state(
    *, run_id: str, life_index: int, episode_tick: int, energy: float
) -> dict[str, Any]:
    state = engine.initial_state(
        {
            "energy": energy,
            "safety": 0.62,
            "connection": 0.50,
            "stimulation": 0.43,
        },
        run_id=run_id,
        seed=WORLD_SEED,
    )
    completed_ticks = engine.EPISODE_SPAN_TICKS * (life_index - 1)
    completed_respawns = life_index - 1
    state["clock"] = {
        "global_tick": completed_ticks + completed_respawns + episode_tick,
        "episode_index": life_index - 1,
        "episode_id": engine.episode_id_for(run_id, life_index - 1),
        "episode_tick": episode_tick,
    }
    state["lifecycle"] = {
        "trial_status": "active",
        "life_index": life_index,
        "awaiting_respawn": False,
        "life_results": [
            {
                "life_index": index,
                "survival_ticks": engine.EPISODE_SPAN_TICKS,
                "censored": True,
                "termination": "censored",
            }
            for index in range(1, life_index)
        ],
        "terminal_life_result": None,
    }
    state["world"] = reset_world_for_life(state["world"], life_index)
    if state["clock"]["global_tick"]:
        state["last_action"] = "rest"
        state["last_command_hash"] = "a" * 64
        state["last_trace_hash"] = "b" * 64
    return state


def _command_for(
    state: Mapping[str, Any], *, trigger_source: str = "headless_acceptance"
) -> dict[str, Any]:
    return engine.make_command(
        sequence=int(state["clock"]["global_tick"]) + 1,
        trigger_source=trigger_source,
        interventions=deepcopy(engine.DEFAULT_INTERVENTIONS),
        prev_command_hash=state.get("last_command_hash"),
    )


def _run_commands(
    *,
    scenario_id: str,
    run_id: str,
    initial_state: Mapping[str, Any],
    command_count: int,
) -> dict[str, Any]:
    state = deepcopy(dict(initial_state))
    run_meta = engine.make_run_metadata(run_id, POLICY_SEED)
    commands: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    states: list[dict[str, Any]] = [deepcopy(state)]
    for _ in range(command_count):
        command = _command_for(state)
        result = engine.compute_step(state, command, run_meta)
        commands.append(command)
        traces.append(result.trace)
        state = result.next_state
        states.append(deepcopy(state))
    return {
        "scenario_id": scenario_id,
        "initial_state": deepcopy(dict(initial_state)),
        "run_meta": run_meta,
        "commands": commands,
        "traces": traces,
        "states": states,
        "final_state": state,
    }


def _build_declared_scenarios() -> dict[str, dict[str, Any]]:
    death_run = f"{RUN_ID}-death"
    censor_run = f"{RUN_ID}-censor"
    fourth_run = f"{RUN_ID}-sixteenth"
    return {
        "death_respawn_next_action": _run_commands(
            scenario_id="death_respawn_next_action",
            run_id=death_run,
            initial_state=_active_life_state(
                run_id=death_run, life_index=1, episode_tick=0, energy=0.011
            ),
            command_count=3,
        ),
        "censor_respawn": _run_commands(
            scenario_id="censor_respawn",
            run_id=censor_run,
            initial_state=_active_life_state(
                run_id=censor_run, life_index=1, episode_tick=255, energy=0.90
            ),
            command_count=2,
        ),
        "life_sixteen_terminal": _run_commands(
            scenario_id="life_sixteen_terminal",
            run_id=fourth_run,
            initial_state=_active_life_state(
                run_id=fourth_run,
                life_index=engine.MAX_LIVES,
                episode_tick=255,
                energy=0.90,
            ),
            command_count=1,
        ),
    }


def _receipt_is_exact(trace: Mapping[str, Any]) -> bool:
    receipt = trace.get("carry_reset_receipt")
    if not isinstance(receipt, Mapping):
        return False
    if not {*CARRY_COMPONENTS, *RESET_COMPONENTS} <= set(receipt):
        return False
    for component in CARRY_COMPONENTS:
        item = receipt[component]
        if not isinstance(item, Mapping):
            return False
        if item.get("matches_expected") is not True:
            return False
        if not (
            item.get("before_hash") == item.get("after_hash") == item.get("expected_hash")
            and item.get("absent_before") == item.get("absent_after") == item.get("expected_absent")
        ):
            return False
    for component in RESET_COMPONENTS:
        item = receipt[component]
        if not isinstance(item, Mapping) or item.get("matches_expected") is not True:
            return False
        if not (
            item.get("after_hash") == item.get("expected_hash")
            and item.get("absent_after") == item.get("expected_absent")
        ):
            return False
    return True


def _pure_respawn(trace: Mapping[str, Any]) -> bool:
    return (
        trace.get("transition_kind") == "respawn"
        and trace.get("policy_invoked") is False
        and trace.get("selected_action") is None
        and trace.get("candidates") == []
        and trace.get("observation") is None
        and trace.get("metabolism") is None
        and trace.get("model_update") == {"applied": False, "reason": "pure_respawn"}
        and trace.get("memory_update")
        == {"applied": False, "reason": "pure_respawn", "consolidation_refs": []}
        and trace.get("claim_update") == {"applied": False, "reason": "pure_respawn"}
        and trace.get("command_chain", {}).get("command_prev_matches_before") is True
        and trace.get("command_chain", {}).get("after_matches_command_hash") is True
        and trace.get("trace_chain", {}).get("trace_prev_matches_before") is True
        and trace.get("lifecycle_after", {}).get("life_index")
        == int(trace.get("lifecycle_before", {}).get("life_index", 0)) + 1
    )


def _life_sixteen_rejection_report(
    scenario: Mapping[str, Any], temp_root: Path
) -> dict[str, Any]:
    terminal_state = deepcopy(scenario["final_state"])
    direct_rejected = False
    direct_error_class = None
    try:
        engine.compute_step(
            terminal_state,
            _command_for(terminal_state),
            deepcopy(scenario["run_meta"]),
        )
    except Exception as exc:  # fail-closed product rejection evidence
        direct_rejected = isinstance(exc, engine.EngineInvariantError)
        direct_error_class = type(exc).__name__

    controller_rejected = False
    controller_error_class = None
    with SQLiteEventStore(temp_root / "terminal-reject.sqlite3") as store:
        controller = PlaygroundController(
            store,
            run_id=f"{RUN_ID}-controller-terminal-reject",
            seed=POLICY_SEED,
            world_seed=WORLD_SEED,
        )
        controller.state = terminal_state
        try:
            controller.dispatch(trigger_source="ui_step_button")
        except Exception as exc:  # fail-closed controller rejection evidence
            controller_rejected = isinstance(exc, engine.EngineInvariantError)
            controller_error_class = type(exc).__name__
    return _check_record(
        direct_rejected and controller_rejected,
        producer_function=(
            "engine.compute_step terminal guard + PlaygroundController.dispatch terminal guard"
        ),
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={"scenario_id": "life_sixteen_terminal", "life_index": engine.MAX_LIVES},
        aggregation_rule="terminal final-life state must reject both reducer and controller dispatch",
        direct_rejected=direct_rejected,
        direct_error_class=direct_error_class,
        controller_rejected=controller_rejected,
        controller_error_class=controller_error_class,
    )


def _commands_from_store(store: SQLiteEventStore, run_id: str) -> list[dict[str, Any]]:
    rows = store.connection.execute(
        "SELECT command_json FROM commands WHERE run_id = ? ORDER BY sequence",
        (run_id,),
    ).fetchall()
    return [json.loads(str(row["command_json"])) for row in rows]


def exercise_real_terminal_run(temp_root: Path) -> dict[str, Any]:
    run_id = f"{RUN_ID}-terminal-live"
    db_path = temp_root / "terminal-live.sqlite3"
    initial = _active_life_state(
        run_id=run_id, life_index=1, episode_tick=0, energy=0.011
    )
    run_meta = engine.make_run_metadata(run_id, POLICY_SEED)
    with SQLiteEventStore(db_path) as store:
        store.create_run(run_meta, initial)
        controller = PlaygroundController(
            store,
            run_id=run_id,
            seed=POLICY_SEED,
            world_seed=WORLD_SEED,
        )
        terminal = TerminalPlayground(controller)
        terminal_result = terminal.execute("run 3")
        snapshot = build_terminal_snapshot(controller)
        commands = _commands_from_store(store, run_id)
        row_counts = store.row_counts(run_id)
        recovered = controller.recover()
        traces = deepcopy(recovered.traces)
        final_state = deepcopy(recovered.state)
    with SQLiteEventStore(db_path) as second_store:
        fresh = second_store.recover_run(run_id)
    transition_kinds = [trace["transition_kind"] for trace in traces]
    ok = (
        terminal_result.get("status") == "committed"
        and terminal_result.get("ticks_committed") == 3
        and row_counts == (3, 3)
        and transition_kinds == ["action", "respawn", "action"]
        and snapshot["lifecycle"]["life_index"] == 2
        and snapshot["life_survival"] == [1]
        and [trace["trace_hash"] for trace in fresh.traces]
        == [trace["trace_hash"] for trace in traces]
    )
    bundle_source = {
        "scenario_id": "terminal_controller_sqlite",
        "initial_state": initial,
        "run_meta": run_meta,
        "commands": commands,
        "traces": traces,
        "states": list(fresh.frames),
        "final_state": final_state,
    }
    return _evidence_payload(
        {
            "value": ok,
            "transition_kinds": transition_kinds,
            "row_counts": list(row_counts),
            "fresh_recovery_match": [trace["trace_hash"] for trace in fresh.traces]
            == [trace["trace_hash"] for trace in traces],
            "life_survival": deepcopy(snapshot["life_survival"]),
            "bundle_source": bundle_source,
        },
        producer_function=(
            "TerminalPlayground.execute -> PlaygroundController.dispatch -> "
            "SQLiteEventStore.append_step/recover_run"
        ),
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={"scenario_id": "terminal_controller_sqlite", "life_indices": [1, 2]},
        aggregation_rule=(
            "real terminal run 3 must commit death, pure respawn, and next action to SQLite "
            "and a fresh store must recompute identical traces"
        ),
        run_id=run_id,
    )


def _pump_tk(root: tk.Tk, predicate: Any, *, timeout_s: float = 15.0) -> None:
    deadline = time.monotonic() + timeout_s
    while not predicate():
        if time.monotonic() >= deadline:
            raise RuntimeError("Tk lifecycle evidence condition timed out")
        root.update_idletasks()
        root.update()
        time.sleep(0.005)


def _prefill_until_before_terminal(
    store: SQLiteEventStore, *, run_id: str
) -> tuple[dict[str, Any], dict[str, Any], int]:
    run_meta = engine.make_run_metadata(run_id, POLICY_SEED)
    state = _active_life_state(
        run_id=run_id,
        life_index=engine.MAX_LIVES,
        episode_tick=engine.EPISODE_SPAN_TICKS - 1,
        energy=0.90,
    )
    store.create_run(run_meta, state)
    return state, run_meta, 0


def exercise_real_tk_run(
    temp_root: Path, *, root_factory: Any = tk.Tk
) -> dict[str, Any]:
    try:
        root = root_factory()
    except tk.TclError as exc:
        return _evidence_payload(
            {
                "value": False,
                "tk_available": False,
                "blocker": classify_raw_data(
                    {
                        "blocker_id": "tk_runtime_unavailable",
                        "error_class": type(exc).__name__,
                        "reason": str(exc),
                    }
                ),
            },
            producer_function="exercise_real_tk_run",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"scenario_id": "tk_controller_sqlite_terminal"},
            aggregation_rule="Tk unavailability is an explicit engineering evidence blocker",
            run_id=f"{RUN_ID}-tk-live",
        )

    run_id = f"{RUN_ID}-tk-live"
    db_path = temp_root / "tk-live.sqlite3"
    window: PlaygroundWindow | None = None
    try:
        root.withdraw()
        with SQLiteEventStore(db_path) as store:
            _prefill_state, _run_meta, prefilled = _prefill_until_before_terminal(
                store, run_id=run_id
            )
            controller = PlaygroundController(
                store,
                run_id=run_id,
                seed=POLICY_SEED,
                world_seed=WORLD_SEED,
            )
            before_count = controller.recovery.command_count
            window = PlaygroundWindow(root, controller)
            window.display_interval_ms = 1
            window.run_button.invoke()
            _pump_tk(
                root,
                lambda: (
                    controller.state["lifecycle"]["trial_status"] == "terminal"
                    and window is not None
                    and window.running is False
                ),
            )
            window._pause()
            window.redraw()
            root.update_idletasks()
            root.update()
            row_counts = store.row_counts(run_id)
            latest_trace = deepcopy(controller.recovery.traces[-1])
            fourth_result = deepcopy(controller.state["lifecycle"]["terminal_life_result"])
            controls_disabled = all(
                "disabled" in button.state()
                for button in (window.step_button, window.run_button, window.inject_button)
            )
            advanced_has_survival = "terminal_life_result" in window.advanced_text.get(
                "1.0", "end-1c"
            )
            ok = (
                prefilled == before_count
                and row_counts == (before_count + 1, before_count + 1)
                and latest_trace["trigger_source"] == "ui_run_button"
                and latest_trace["lifecycle_after"]["trial_status"] == "terminal"
                and latest_trace["life_termination"]["life_index"] == engine.MAX_LIVES
                and fourth_result is not None
                and controls_disabled
                and advanced_has_survival
            )
        with SQLiteEventStore(db_path) as fresh_store:
            fresh = fresh_store.recover_run(run_id)
        ok = ok and fresh.state["lifecycle"]["trial_status"] == "terminal"
        return _evidence_payload(
            {
                "value": ok,
                "tk_available": True,
                "prefilled_command_count": prefilled,
                "final_command_count": fresh.command_count,
                "final_trigger_source": latest_trace["trigger_source"],
                "final_transition_kind": latest_trace["transition_kind"],
                "terminal_life_result": fourth_result,
                "controls_disabled": controls_disabled,
                "advanced_has_survival": advanced_has_survival,
                "fresh_recovery_terminal": fresh.state["lifecycle"]["trial_status"] == "terminal",
                "final_trace_hash": latest_trace["trace_hash"],
            },
            producer_function=(
                "PlaygroundWindow.Run -> PlaygroundController.dispatch -> "
                "SQLiteEventStore.append_step/recover_run"
            ),
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={
                "scenario_id": "tk_controller_sqlite_terminal",
                "life_index": engine.MAX_LIVES,
            },
            aggregation_rule=(
                "prefill one canonical SQLite command chain to the last pre-terminal state, "
                "then require the real hidden Tk Run control to commit and render the final "
                "life-sixteen transition through controller plus SQLite"
            ),
            run_id=run_id,
        )
    finally:
        if window is not None:
            window.close()
        else:
            try:
                root.destroy()
            except tk.TclError:
                pass


def _baseline_initial_goal(global_tick: int) -> dict[str, Any]:
    latches = {
        key: value >= BASELINE_TARGET_LEVEL
        for key, value in BASELINE_INITIAL_ORGANISM.items()
    }
    ordered = list(BASELINE_INITIAL_ORGANISM)
    selected = min(
        ordered,
        key=lambda key: (
            -round(BASELINE_TARGET_LEVEL - BASELINE_INITIAL_ORGANISM[key], 6),
            ordered.index(key),
        ),
    )
    return {
        "state_variable": selected,
        "target": BASELINE_TARGET_LEVEL,
        "selected_global_tick": int(global_tick),
        "entry_deficit": round(
            BASELINE_TARGET_LEVEL - BASELINE_INITIAL_ORGANISM[selected], 6
        ),
        "status": "active",
        "selection_reason": "initial_deficit_priority",
        "completed_latches": latches,
    }


def _world_component_values(world: Mapping[str, Any]) -> dict[str, Any]:
    objects = world["objects_by_cause"]
    return {
        "agent_position": deepcopy(world["agent"]["position"]),
        "agent_facing": world["agent"]["facing"],
        "object_positions": {
            cause: deepcopy(objects[cause]["position"]) for cause in sorted(objects)
        },
        "object_spawn_counts": {
            cause: objects[cause]["spawn_count"] for cause in sorted(objects)
        },
        "object_injection_counts": {
            cause: objects[cause]["injection_count"] for cause in sorted(objects)
        },
    }


def _baseline_respawn_summary(pre_respawn: Mapping[str, Any]) -> dict[str, Any]:
    lifecycle = pre_respawn["lifecycle"]
    if (
        lifecycle.get("trial_status") != "awaiting_respawn"
        or lifecycle.get("awaiting_respawn") is not True
    ):
        raise ValueError("baseline respawn input must be awaiting_respawn")
    life_index = int(lifecycle["life_index"])
    if not 1 <= life_index < engine.MAX_LIVES:
        raise ValueError("baseline respawn input life index must precede max_lives")
    next_life = life_index + 1
    expected_world = reset_world_for_life(pre_respawn["world"], next_life)
    expected_goal = _baseline_initial_goal(
        int(pre_respawn["clock"]["global_tick"]) + 1
    )
    memory = pre_respawn["memory"]
    carry_hashes = {
        "model": engine.canonical_hash(pre_respawn["model"]),
        "memory_schema_version": engine.canonical_hash(memory["schema_version"]),
        "memory_episodic": engine.canonical_hash(memory["episodic"]),
        "memory_consolidated": engine.canonical_hash(memory["consolidated"]),
        "memory_claim_events": engine.canonical_hash(memory["claim_events"]),
        "memory_competing_claims": engine.canonical_hash(memory["competing_claims"]),
        "token_mapping": engine.canonical_hash(
            pre_respawn["world"]["trial"]["token_mapping"]
        ),
    }
    expected_world_components = _world_component_values(expected_world)
    reset_hashes = {
        "organism": engine.canonical_hash(BASELINE_INITIAL_ORGANISM),
        "world": engine.canonical_hash(expected_world),
        **{
            key: engine.canonical_hash(value)
            for key, value in expected_world_components.items()
        },
        "current_goal": engine.canonical_hash(expected_goal),
        "goal_completed_latches": engine.canonical_hash(
            expected_goal["completed_latches"]
        ),
        "last_action": engine.canonical_hash(None),
        "episode_tick": engine.canonical_hash(0),
        "working_spatial_state": None,
    }
    lifecycle_after = {
        "trial_status": "active",
        "life_index": next_life,
        "awaiting_respawn": False,
        "life_results": deepcopy(lifecycle["life_results"]),
        "terminal_life_result": deepcopy(lifecycle["terminal_life_result"]),
    }
    return {
        "transition_kind": "respawn",
        "policy_called": False,
        "life_index_after": next_life,
        "life_result": deepcopy(lifecycle["life_results"][-1]),
        "carry_hashes": carry_hashes,
        "reset_hashes": reset_hashes,
        "lifecycle_after": lifecycle_after,
    }


def _baseline_terminal_output(terminal_state: Mapping[str, Any]) -> dict[str, Any]:
    lifecycle = terminal_state["lifecycle"]
    if lifecycle.get("trial_status") != "terminal":
        raise ValueError("baseline terminal input must be terminal")
    life_results = lifecycle["life_results"]
    if (
        int(lifecycle["life_index"]) != engine.MAX_LIVES
        or len(life_results) != engine.MAX_LIVES
        or [int(item["life_index"]) for item in life_results]
        != list(range(1, engine.MAX_LIVES + 1))
    ):
        raise ValueError("baseline terminal input must contain the complete ordered lives")
    fourth = life_results[-1]
    derived_fourth_result = {
        "survival_ticks": min(int(fourth["survival_ticks"]), 256),
        "censored": bool(fourth["censored"]),
    }
    return {
        "trial_status": "terminal",
        "life_index": engine.MAX_LIVES,
        "life_results_hash": engine.canonical_hash(life_results),
        "terminal_life_result": derived_fourth_result,
        "further_dispatch": "rejected",
    }


def independent_scripted_respawn_baseline(
    pre_respawn_states: Sequence[Mapping[str, Any]],
    *,
    terminal_states: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Independent scripted carry/reset implementation with no policy/reducer calls."""

    return {
        "respawns": [
            _baseline_respawn_summary(state) for state in pre_respawn_states
        ],
        "terminal_outputs": [
            _baseline_terminal_output(state) for state in terminal_states
        ],
    }


def _candidate_respawn_summary(
    post_respawn: Mapping[str, Any], trace: Mapping[str, Any]
) -> dict[str, Any]:
    memory = post_respawn["memory"]
    world = post_respawn["world"]
    world_components = _world_component_values(world)
    return {
        "transition_kind": trace["transition_kind"],
        "policy_called": trace["policy_invoked"],
        "life_index_after": post_respawn["lifecycle"]["life_index"],
        "life_result": deepcopy(trace["life_termination"]),
        "carry_hashes": {
            "model": engine.canonical_hash(post_respawn["model"]),
            "memory_schema_version": engine.canonical_hash(memory["schema_version"]),
            "memory_episodic": engine.canonical_hash(memory["episodic"]),
            "memory_consolidated": engine.canonical_hash(memory["consolidated"]),
            "memory_claim_events": engine.canonical_hash(memory["claim_events"]),
            "memory_competing_claims": engine.canonical_hash(memory["competing_claims"]),
            "token_mapping": engine.canonical_hash(world["trial"]["token_mapping"]),
        },
        "reset_hashes": {
            "organism": engine.canonical_hash(post_respawn["organism"]),
            "world": engine.canonical_hash(world),
            **{
                key: engine.canonical_hash(value)
                for key, value in world_components.items()
            },
            "current_goal": engine.canonical_hash(post_respawn["current_goal"]),
            "goal_completed_latches": engine.canonical_hash(
                post_respawn["current_goal"]["completed_latches"]
            ),
            "last_action": engine.canonical_hash(post_respawn["last_action"]),
            "episode_tick": engine.canonical_hash(
                post_respawn["clock"]["episode_tick"]
            ),
            "working_spatial_state": None,
        },
        "lifecycle_after": deepcopy(post_respawn["lifecycle"]),
    }


def _candidate_terminal_output(terminal_state: Mapping[str, Any]) -> dict[str, Any]:
    lifecycle = terminal_state["lifecycle"]
    return {
        "trial_status": lifecycle["trial_status"],
        "life_index": lifecycle["life_index"],
        "life_results_hash": engine.canonical_hash(lifecycle["life_results"]),
        "terminal_life_result": deepcopy(lifecycle["terminal_life_result"]),
        "further_dispatch": "rejected",
    }


def _baseline_independence_probe(
    pre_respawn_states: Sequence[Mapping[str, Any]],
    terminal_states: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source = textwrap.dedent(inspect.getsource(independent_scripted_respawn_baseline))
    source_tree = ast.parse(source)
    forbidden_findings = sorted(
        {
            ast.unparse(node.func)
            for node in ast.walk(source_tree)
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id in {"compute_step", "_score_candidate"})
                or (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"compute_step", "_score_candidate"}
                )
            )
        }
    )
    call_attempts = {"compute_step": 0, "_score_candidate": 0}
    original_compute = engine.compute_step
    original_score = engine._score_candidate

    def reject_compute(*_args: Any, **_kwargs: Any) -> Any:
        call_attempts["compute_step"] += 1
        raise AssertionError("independent baseline called candidate reducer")

    def reject_score(*_args: Any, **_kwargs: Any) -> Any:
        call_attempts["_score_candidate"] += 1
        raise AssertionError("independent baseline called candidate scorer")

    error_class = None
    error_reason = None
    output: dict[str, Any] = {}
    engine.compute_step = reject_compute
    engine._score_candidate = reject_score
    try:
        output = independent_scripted_respawn_baseline(
            pre_respawn_states, terminal_states=terminal_states
        )
    except Exception as exc:
        error_class = type(exc).__name__
        error_reason = str(exc)
    finally:
        engine.compute_step = original_compute
        engine._score_candidate = original_score
    ok = (
        error_class is None
        and forbidden_findings == []
        and call_attempts == {"compute_step": 0, "_score_candidate": 0}
    )
    record = _check_record(
        ok,
        producer_function="_baseline_independence_probe",
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={"baseline_independence_probe": True},
        aggregation_rule=(
            "invoke the independent callable with candidate reducer/scorer replaced by "
            "failing counters and scan its callable AST for direct forbidden calls"
        ),
        invoked=True,
        callable_source_hash=_sha256(source.encode("utf-8")),
        forbidden_call_findings=forbidden_findings,
        forbidden_call_attempts=call_attempts,
        observed_error_class=error_class,
        observed_error_reason=error_reason,
    )
    if not ok:
        raise RuntimeError("independent baseline provenance probe failed")
    return output, record


def _component_match_records(
    *,
    scenario_id: str,
    baseline_summary: Mapping[str, Any],
    candidate_summary: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for family in ("carry_hashes", "reset_hashes"):
        for component in sorted(baseline_summary[family]):
            matched = (
                baseline_summary[family][component]
                == candidate_summary[family][component]
            )
            records[f"{family}:{component}"] = _check_record(
                matched,
                producer_function="build_baseline_report.component_match",
                input_artifacts=_source_inputs(),
                seed_context_episode_ids={
                    "scenario_id": scenario_id,
                    "component": component,
                },
                aggregation_rule="independently computed scripted component hash must equal candidate post-respawn bytes",
                component=component,
                component_family=family,
                baseline_hash=baseline_summary[family][component],
                candidate_hash=candidate_summary[family][component],
            )
    for component in (
        "transition_kind",
        "policy_called",
        "life_index_after",
        "life_result",
        "lifecycle_after",
    ):
        records[component] = _check_record(
            baseline_summary[component] == candidate_summary[component],
            producer_function="build_baseline_report.component_match",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={
                "scenario_id": scenario_id,
                "component": component,
            },
            aggregation_rule="scripted lifecycle output must equal candidate lifecycle output",
            component=component,
            baseline_hash=engine.canonical_hash(baseline_summary[component]),
            candidate_hash=engine.canonical_hash(candidate_summary[component]),
        )
    return records


def build_baseline_report(
    scenarios: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    respawn_specs = {
        "death_respawn": scenarios["death_respawn_next_action"],
        "censor_respawn": scenarios["censor_respawn"],
    }
    pre_respawn_states = [scenario["states"][1] for scenario in respawn_specs.values()]
    terminal_states = [scenarios["life_sixteen_terminal"]["final_state"]]
    baseline_output, independence_probe = _baseline_independence_probe(
        pre_respawn_states, terminal_states
    )
    comparisons: dict[str, dict[str, Any]] = {}
    for index, (comparison_id, scenario) in enumerate(respawn_specs.items()):
        baseline_summary = baseline_output["respawns"][index]
        candidate_summary = _candidate_respawn_summary(
            scenario["states"][2], scenario["traces"][1]
        )
        component_matches = _component_match_records(
            scenario_id=comparison_id,
            baseline_summary=baseline_summary,
            candidate_summary=candidate_summary,
        )
        equivalent = all(record["value"] for record in component_matches.values())
        comparisons[comparison_id] = _evidence_payload(
            {
                "comparison_id": comparison_id,
                "baseline_summary_hash": engine.canonical_hash(baseline_summary),
                "candidate_summary_hash": engine.canonical_hash(candidate_summary),
                "baseline_component_hashes": {
                    **baseline_summary["carry_hashes"],
                    **baseline_summary["reset_hashes"],
                },
                "candidate_component_hashes": {
                    **candidate_summary["carry_hashes"],
                    **candidate_summary["reset_hashes"],
                },
                "component_matches": component_matches,
                "observable_equivalent": equivalent,
                "matched": equivalent,
            },
            producer_function="build_baseline_report.respawn_comparison",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"scenario_id": comparison_id},
            aggregation_rule=(
                "compare independently scripted carry/reset/lifecycle hashes to the candidate "
                "post-respawn serialized state and trace"
            ),
        )

    baseline_terminal = baseline_output["terminal_outputs"][0]
    candidate_terminal = _candidate_terminal_output(terminal_states[0])
    terminal_fields = (
        "trial_status",
        "life_index",
        "life_results_hash",
        "terminal_life_result",
        "further_dispatch",
    )
    terminal_matches = {
        field: _check_record(
            baseline_terminal[field] == candidate_terminal[field],
            producer_function="build_baseline_report.terminal_match",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"scenario_id": "life_sixteen_terminal", "component": field},
            aggregation_rule="scripted terminal output must equal candidate serialized terminal output",
            component=field,
            baseline_hash=engine.canonical_hash(baseline_terminal[field]),
            candidate_hash=engine.canonical_hash(candidate_terminal[field]),
        )
        for field in terminal_fields
    }
    terminal_equivalent = all(record["value"] for record in terminal_matches.values())
    comparisons["life_sixteen_terminal"] = _evidence_payload(
        {
            "comparison_id": "life_sixteen_terminal",
            "baseline_summary_hash": engine.canonical_hash(baseline_terminal),
            "candidate_summary_hash": engine.canonical_hash(candidate_terminal),
            "component_matches": terminal_matches,
            "observable_equivalent": terminal_equivalent,
            "matched": terminal_equivalent,
        },
        producer_function="build_baseline_report.terminal_comparison",
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={"scenario_id": "life_sixteen_terminal", "life_index": engine.MAX_LIVES},
        aggregation_rule="compare independently scripted final-life output to candidate state",
    )

    all_equivalent = all(item["observable_equivalent"] for item in comparisons.values())
    disposition = (
        "observable_equivalence_claim_blocker" if all_equivalent else "non_equivalent"
    )
    return _evidence_payload(
        {
            "baseline_id": "independent_scripted_respawn_baseline",
            "independent_callable": "independent_scripted_respawn_baseline",
            "independence_probe": independence_probe,
            "candidate_reducer_called": independence_probe["forbidden_call_attempts"]["compute_step"] > 0,
            "candidate_scorer_called": independence_probe["forbidden_call_attempts"]["_score_candidate"] > 0,
            "comparisons": comparisons,
            "disposition": disposition,
            "engineering_failure": False,
        },
        producer_function="build_baseline_report",
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
        aggregation_rule=(
            "independently construct respawn carry/reset hashes and terminal output; observable "
            "equivalence is retained as a claim blocker, never an engineering failure"
        ),
    )


def build_no_carry_ablation_report(
    death_scenario: Mapping[str, Any]
) -> dict[str, Any]:
    post_respawn = deepcopy(death_scenario["states"][2])
    next_command = deepcopy(death_scenario["commands"][2])
    run_meta = deepcopy(death_scenario["run_meta"])
    canonical_result = engine.compute_step(post_respawn, next_command, run_meta)

    no_carry_state = deepcopy(post_respawn)
    empty = engine.initial_state(run_id=f"{RUN_ID}-empty-memory", seed=WORLD_SEED)
    no_carry_state["model"] = deepcopy(empty["model"])
    no_carry_state["memory"] = deepcopy(empty["memory"])
    no_carry_result = engine.compute_step(no_carry_state, next_command, run_meta)

    canonical_case = _evidence_payload(
        {
            "case_id": "canonical_carry",
            "invoked": True,
            "selected_action": canonical_result.trace["selected_action"],
            "transition_kind": canonical_result.trace["transition_kind"],
            "model_before_hash": engine.canonical_hash(post_respawn["model"]),
            "memory_before_hash": engine.canonical_hash(post_respawn["memory"]),
            "model_after_hash": engine.canonical_hash(canonical_result.next_state["model"]),
            "memory_after_hash": engine.canonical_hash(canonical_result.next_state["memory"]),
        },
        producer_function="build_no_carry_ablation_report.canonical_carry",
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={"scenario_id": "death_respawn_next_action", "life_index": 2},
        aggregation_rule="rerun the exact post-respawn serialized state and same next command through compute_step",
    )
    no_carry_case = _evidence_payload(
        {
            "case_id": "no_carry",
            "invoked": True,
            "selected_action": no_carry_result.trace["selected_action"],
            "transition_kind": no_carry_result.trace["transition_kind"],
            "model_before_hash": engine.canonical_hash(no_carry_state["model"]),
            "memory_before_hash": engine.canonical_hash(no_carry_state["memory"]),
            "model_after_hash": engine.canonical_hash(no_carry_result.next_state["model"]),
            "memory_after_hash": engine.canonical_hash(no_carry_result.next_state["memory"]),
        },
        producer_function="build_no_carry_ablation_report.no_carry",
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={"scenario_id": "death_respawn_next_action", "life_index": 2},
        aggregation_rule=(
            "test-only intervention clears model plus all retained memory on a valid "
            "post-respawn state, then reruns the same next command through compute_step"
        ),
    )
    behavior_equivalent = (
        canonical_result.trace["selected_action"] == no_carry_result.trace["selected_action"]
        and canonical_result.trace["goal_after"] == no_carry_result.trace["goal_after"]
        and canonical_result.trace["actual_delta"] == no_carry_result.trace["actual_delta"]
    )
    memory_equivalent = (
        engine.canonical_hash(canonical_result.next_state["memory"])
        == engine.canonical_hash(no_carry_result.next_state["memory"])
    )
    empty_model_hash = engine.canonical_hash(empty["model"])
    empty_memory_hash = engine.canonical_hash(empty["memory"])
    canonical_model_hash = engine.canonical_hash(post_respawn["model"])
    canonical_memory_hash = engine.canonical_hash(post_respawn["memory"])
    cleared_model_hash = engine.canonical_hash(no_carry_state["model"])
    cleared_memory_hash = engine.canonical_hash(no_carry_state["memory"])
    model_matches_empty = cleared_model_hash == empty_model_hash
    memory_matches_empty = cleared_memory_hash == empty_memory_hash
    model_differs_from_canonical = cleared_model_hash != canonical_model_hash
    memory_differs_from_canonical = cleared_memory_hash != canonical_memory_hash
    comparison = _evidence_payload(
        {
            "behavior_equivalent": behavior_equivalent,
            "retained_memory_equivalent": memory_equivalent,
            "model_matches_empty_constructor": model_matches_empty,
            "memory_matches_empty_constructor": memory_matches_empty,
            "model_differs_from_canonical_post_respawn": model_differs_from_canonical,
            "memory_differs_from_canonical_post_respawn": memory_differs_from_canonical,
            "starting_model_memory_were_cleared": (
                model_matches_empty
                and memory_matches_empty
                and model_differs_from_canonical
                and memory_differs_from_canonical
            ),
            "constructor_hashes": {
                "model": empty_model_hash,
                "memory": empty_memory_hash,
            },
            "canonical_post_respawn_hashes": {
                "model": canonical_model_hash,
                "memory": canonical_memory_hash,
            },
            "intervened_post_respawn_hashes": {
                "model": cleared_model_hash,
                "memory": cleared_memory_hash,
            },
        },
        producer_function="build_no_carry_ablation_report.compare",
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={"scenario_id": "death_respawn_next_action", "life_index": 2},
        aggregation_rule=(
            "compare action/goal/delta behavior and post-command memory bytes without "
            "authorizing a science conclusion"
        ),
    )
    return _evidence_payload(
        {
            "cases": {
                "canonical_carry": canonical_case,
                "no_carry": no_carry_case,
            },
            "invocation_ledger": [
                _evidence_payload(
                    {"case_id": case_id, "invoked": True},
                    producer_function=f"build_no_carry_ablation_report.invoke:{case_id}",
                    input_artifacts=_source_inputs(),
                    seed_context_episode_ids={"scenario_id": "death_respawn_next_action"},
                    aggregation_rule="record a completed compute_step rerun for the named case",
                )
                for case_id in ("canonical_carry", "no_carry")
            ],
            "comparison": comparison,
            "science_adjudication_authorized": False,
            "product_api_modified_for_intervention": False,
        },
        producer_function="build_no_carry_ablation_report",
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={"scenario_id": "death_respawn_next_action", "life_index": 2},
        aggregation_rule=(
            "report the real test-only clear intervention and equivalence outcomes honestly; "
            "science adjudication remains unauthorized"
        ),
    )


def scan_policy_projection(
    payload: Any, *, inject_positive_control: bool = False
) -> dict[str, Any]:
    candidate = deepcopy(payload)
    if inject_positive_control:
        candidate = {
            "projection_under_test": candidate,
            "positive_control": deepcopy(POSITIVE_CONTROL_PAYLOAD),
        }
    forbidden = {
        "life_index": "life_index",
        "life_id": "life_metadata",
        "episode_id": "life_metadata",
        "episode_index": "life_metadata",
        "global_tick": "life_metadata",
        "trial_status": "life_metadata",
        "awaiting_respawn": "life_metadata",
        "life_results": "life_metadata",
        "terminal_life_result": "life_metadata",
        "seed": "seed",
        "world_seed": "seed",
        "trial_seed": "seed",
        "token_mapping": "token_mapping",
    }
    offenders: list[dict[str, Any]] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                next_path = f"{path}/{key}" if path else f"/{key}"
                if key in forbidden:
                    offenders.append(
                        {
                            "category": forbidden[key],
                            "path": next_path,
                            "reason": "forbidden_policy_projection_key",
                        }
                    )
                walk(item, next_path)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}/{index}")

    walk(candidate, "")
    return _evidence_payload(
        {
            "scan_scope": "policy_projection_only",
            "positive_control_injected": inject_positive_control,
            "positive_control_detected": inject_positive_control and bool(offenders),
            "offenders": offenders,
        },
        producer_function="scan_policy_projection",
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={"policy_projection_scan": True},
        aggregation_rule=(
            "recursive structured-key scan restricted to policy projections; the only "
            "positive controls are life_index, seed, and token_mapping"
        ),
    )


def _bundle_for_replay(scenario: Mapping[str, Any]) -> dict[str, Any]:
    traces = scenario["traces"]
    expected_carry_receipts = {
        str(trace["sequence"]): deepcopy(trace["carry_reset_receipt"])
        for trace in traces
        if trace.get("carry_reset_receipt") is not None
    }
    bundle = {
        "scenario_id": scenario["scenario_id"],
        "initial_state": deepcopy(scenario["initial_state"]),
        "run_meta": deepcopy(scenario["run_meta"]),
        "commands": deepcopy(scenario["commands"]),
        "stored_trace_hashes": [trace["trace_hash"] for trace in traces],
        "expected_policy_flags": [trace["policy_invoked"] for trace in traces],
        "expected_carry_receipts": expected_carry_receipts,
    }
    fourth = scenario["final_state"]["lifecycle"].get("terminal_life_result")
    if fourth is not None:
        bundle["expected_terminal_life_result"] = deepcopy(fourth)
    return bundle


def _replay_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    forbidden_selected_inputs = {
        "stored_selected_actions",
        "selected_actions",
        "expected_selected_actions",
    }
    if forbidden_selected_inputs & set(bundle):
        raise RecoveryError("stored selected action supplied as replay input")
    state = deepcopy(bundle["initial_state"])
    run_meta = deepcopy(bundle["run_meta"])
    traces: list[dict[str, Any]] = []
    for command in bundle["commands"]:
        result = engine.compute_step(state, deepcopy(command), run_meta)
        state = result.next_state
        traces.append(result.trace)

    actual_trace_hashes = [trace["trace_hash"] for trace in traces]
    if actual_trace_hashes != bundle["stored_trace_hashes"]:
        raise RecoveryError("stored trace differs from independent recomputation")
    actual_policy_flags = [trace["policy_invoked"] for trace in traces]
    if actual_policy_flags != bundle["expected_policy_flags"]:
        raise RecoveryError("stored policy-invoked flag differs from recomputation")
    for sequence, expected in bundle["expected_carry_receipts"].items():
        index = int(sequence) - int(bundle["commands"][0]["sequence"])
        actual = traces[index]["carry_reset_receipt"]
        if engine.canonical_json(actual) != engine.canonical_json(expected):
            raise RecoveryError("stored carry/reset receipt differs from recomputation")
    if "expected_terminal_life_result" in bundle:
        if (
            state["lifecycle"]["terminal_life_result"]
            != bundle["expected_terminal_life_result"]
        ):
            raise RecoveryError("stored final-life result differs from recomputation")
    return {
        "scenario_id": bundle["scenario_id"],
        "trace_hashes": actual_trace_hashes,
        "transition_kinds": [trace["transition_kind"] for trace in traces],
        "policy_flags": actual_policy_flags,
        "selected_actions": [trace["selected_action"] for trace in traces],
        "life_indices": [trace["lifecycle_after"]["life_index"] for trace in traces],
        "carry_receipt_hashes": {
            str(trace["sequence"]): engine.canonical_hash(trace["carry_reset_receipt"])
            for trace in traces
            if trace.get("carry_reset_receipt") is not None
        },
        "terminal_life_result": deepcopy(state["lifecycle"]["terminal_life_result"]),
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
        command = tampered["commands"][0]
        command["prev_command_hash"] = "0" * 64
        command["command_hash"] = engine.canonical_hash(
            {key: value for key, value in command.items() if key != "command_hash"}
        )
    elif tamper_id == "stored_trace":
        tampered["stored_trace_hashes"] = ["0" * 64] * len(
            tampered["stored_trace_hashes"]
        )
    elif tamper_id == "carry_receipt":
        sequence = sorted(tampered["expected_carry_receipts"], key=int)[0]
        tampered["expected_carry_receipts"][sequence]["model"]["after_hash"] = "0" * 64
    elif tamper_id == "policy_flag":
        tampered["expected_policy_flags"][0] = not tampered["expected_policy_flags"][0]
    elif tamper_id == "terminal_life_result":
        tampered["expected_terminal_life_result"]["survival_ticks"] = -1
    else:
        raise ValueError(tamper_id)
    return tampered


def _tamper_evidence(bundle: Mapping[str, Any], tamper_id: str) -> dict[str, Any]:
    failed_closed = False
    error_class = None
    reason = None
    try:
        _replay_bundle(_tamper_bundle(bundle, tamper_id))
    except Exception as exc:  # real fail-closed replay control
        failed_closed = True
        error_class = type(exc).__name__
        reason = str(exc)
    return _evidence_payload(
        {
            "tamper_id": tamper_id,
            "failed_closed": failed_closed,
            "value": failed_closed,
            "observed_error_class": error_class,
            "observed_reason": reason,
        },
        producer_function=f"build_replay_report.tamper:{tamper_id}",
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={
            "scenario_id": bundle["scenario_id"],
            "tamper_id": tamper_id,
        },
        aggregation_rule="the named serialized replay/evidence tamper must fail closed",
    )


def build_replay_report(
    scenarios: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    temp_root = Path(tempfile.mkdtemp(prefix="ego-v2-card-c-replay-"))
    try:
        by_scenario: dict[str, dict[str, Any]] = {}
        for scenario_id in sorted(scenarios):
            bundle = _bundle_for_replay(scenarios[scenario_id])
            local = _replay_bundle(bundle)
            bundle_path = temp_root / f"{scenario_id}.json"
            _write_json(bundle_path, bundle)
            fresh_a = _fresh_replay_summary(bundle_path)
            fresh_b = _fresh_replay_summary(bundle_path)
            tamper_ids = ["initial_state", "command", "stored_trace", "policy_flag"]
            if bundle["expected_carry_receipts"]:
                tamper_ids.append("carry_receipt")
            if "expected_terminal_life_result" in bundle:
                tamper_ids.append("terminal_life_result")
            by_scenario[scenario_id] = _evidence_payload(
                {
                    "scenario_id": scenario_id,
                    "local_summary": classify_raw_data(
                        {
                            "trace_hashes": local["trace_hashes"],
                            "transition_kinds": local["transition_kinds"],
                            "policy_flags": local["policy_flags"],
                            "selected_actions": local["selected_actions"],
                            "life_indices": local["life_indices"],
                            "carry_receipt_hashes": local["carry_receipt_hashes"],
                            "terminal_life_result": local["terminal_life_result"],
                            "final_state_hash": local["final_state_hash"],
                        }
                    ),
                    "fresh_summary_hashes": [
                        _sha256(_canonical_bytes(fresh_a)),
                        _sha256(_canonical_bytes(fresh_b)),
                    ],
                    "fresh_process_match": _check_record(
                        local == fresh_a == fresh_b,
                        producer_function="build_replay_report.fresh_process_match",
                        input_artifacts=_source_inputs(),
                        seed_context_episode_ids={"scenario_id": scenario_id},
                        aggregation_rule=(
                            "local replay must equal two fresh Python process replays from "
                            "serialized initial state plus ordered commands"
                        ),
                    ),
                    "tamper_controls": {
                        tamper_id: _tamper_evidence(bundle, tamper_id)
                        for tamper_id in tamper_ids
                    },
                },
                producer_function="build_replay_report.scenario",
                input_artifacts=_source_inputs(),
                seed_context_episode_ids={"scenario_id": scenario_id},
                aggregation_rule=(
                    "one replay scenario wrapper with raw comparison summaries plus fully "
                    "provenanced fresh-process and hostile-tamper records"
                ),
            )
        return _evidence_payload(
            {
                "scenarios": by_scenario,
                "stored_selected_actions_used_as_input": False,
            },
            producer_function="build_replay_report",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule=(
                "recompute all lifecycle behavior from serialized initial state plus commands "
                "in-process and in two fresh processes; selected actions are outputs only"
            ),
        )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def _direct_forbidden_calls(tree: ast.AST) -> list[str]:
    forbidden = {
        "compute_step",
        "transition_world",
        "make_command",
        "append_step",
        "create_run",
        "reset_world_for_life",
    }
    return sorted(
        {
            ast.unparse(node.func)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id in forbidden)
                or (isinstance(node.func, ast.Attribute) and node.func.attr in forbidden)
            )
        }
    )


def _method_calls(method: ast.FunctionDef) -> list[str]:
    return [
        ast.unparse(node.func)
        for node in ast.walk(method)
        if isinstance(node, ast.Call)
    ]


def build_single_path_source_report() -> dict[str, Any]:
    package_root = REPO_ROOT / "labs/ego_life_playground_v0"
    package_files = sorted(package_root.glob("*.py"))
    package_trees = {
        path.name: ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for path in package_files
    }
    definition_counts = {
        "PlaygroundController": sum(
            isinstance(node, ast.ClassDef) and node.name == "PlaygroundController"
            for tree in package_trees.values()
            for node in ast.walk(tree)
        ),
        "compute_step": sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "compute_step"
            for tree in package_trees.values()
            for node in ast.walk(tree)
        ),
        "SQLiteEventStore": sum(
            isinstance(node, ast.ClassDef) and node.name == "SQLiteEventStore"
            for tree in package_trees.values()
            for node in ast.walk(tree)
        ),
    }
    controller_tree = package_trees["controller.py"]
    controller_class = next(
        node
        for node in controller_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "PlaygroundController"
    )
    dispatch = next(
        node
        for node in controller_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "dispatch"
    )
    dispatch_calls = _method_calls(dispatch)
    store_tree = package_trees["store.py"]
    store_class = next(
        node
        for node in store_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SQLiteEventStore"
    )
    recover = next(
        node
        for node in store_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "recover_run"
    )
    recover_calls = _method_calls(recover)
    ui_forbidden = {
        name: _direct_forbidden_calls(package_trees[name])
        for name in ("terminal.py", "visual_console.py")
    }
    runner_tree = ast.parse(
        (REPO_ROOT / "scripts/run_ego_life_playground_v0.py").read_text(encoding="utf-8")
    )
    runner_forbidden = _direct_forbidden_calls(runner_tree)
    store_source = (package_root / "store.py").read_text(encoding="utf-8").upper()
    versions = {
        "state": engine.STATE_SCHEMA_VERSION,
        "run": engine.RUN_SCHEMA_VERSION,
        "command": engine.COMMAND_SCHEMA_VERSION,
        "trace": engine.TRACE_SCHEMA_VERSION,
        "world": microworld.WORLD_STATE_SCHEMA_VERSION,
        "policy_observation": microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION,
        "observer_frame": microworld.PUBLIC_FRAME_SCHEMA_VERSION,
        "claim_memory": claim_memory.CLAIM_MEMORY_SCHEMA_VERSION,
        "code_path_manifest": engine.compute_code_path_manifest()["schema_version"],
    }
    expected_versions = {
        "state": "ego.life_playground.state.v7",
        "run": "ego.life_playground.run.v7",
        "command": "ego.life_playground.command.v7",
        "trace": "ego.life_playground.trace.v12",
        "world": "ego.life_playground.microworld.state.v4",
        "policy_observation": "ego.life_playground.microworld.observation.v4",
        "observer_frame": "ego.life_playground.microworld.public_frame.v5",
        "claim_memory": "ego.life_playground.claim_memory.v2",
        "code_path_manifest": "ego.life_playground.code_path.v8",
    }
    ok = (
        definition_counts
        == {"PlaygroundController": 1, "compute_step": 1, "SQLiteEventStore": 1}
        and dispatch_calls.count("compute_step") == 1
        and dispatch_calls.count("self.store.append_step") == 1
        and recover_calls.count("compute_step") == 1
        and all(not calls for calls in ui_forbidden.values())
        and runner_forbidden == []
        and "ALTER TABLE" not in store_source
        and versions == expected_versions
    )
    return _check_record(
        ok,
        producer_function="build_single_path_source_report",
        input_artifacts=_source_inputs(),
        seed_context_episode_ids={"source_scan": True},
        aggregation_rule=(
            "AST scan requires one controller, one reducer, one SQLite store; UI/runner may "
            "not call reducer/store mutation helpers; dispatch/recovery own their declared "
            "single calls; versions and table shape stay frozen"
        ),
        definition_counts=definition_counts,
        controller_dispatch_compute_step_calls=dispatch_calls.count("compute_step"),
        controller_dispatch_append_step_calls=dispatch_calls.count("self.store.append_step"),
        store_recovery_compute_step_calls=recover_calls.count("compute_step"),
        ui_forbidden_calls=ui_forbidden,
        runner_forbidden_calls=runner_forbidden,
        sqlite_migration_detected="ALTER TABLE" in store_source,
        versions=versions,
    )


def _carry_hash_summary(trace: Mapping[str, Any]) -> dict[str, Any] | None:
    receipt = trace.get("carry_reset_receipt")
    if not isinstance(receipt, Mapping):
        return None
    return {
        component: {
            "before_hash": item.get("before_hash"),
            "after_hash": item.get("after_hash"),
            "expected_hash": item.get("expected_hash"),
            "absent_before": item.get("absent_before"),
            "absent_after": item.get("absent_after"),
            "expected_absent": item.get("expected_absent"),
        }
        for component, item in sorted(receipt.items())
    }


def _trace_records(
    scenarios: Mapping[str, Mapping[str, Any]],
    terminal_live: Mapping[str, Any],
    tk_live: Mapping[str, Any],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for scenario_id in sorted(scenarios):
        for trace in scenarios[scenario_id]["traces"]:
            records.append(
                _evidence_payload(
                    {
                        "evidence_kind": "computed_lifecycle_trace",
                        "scenario_id": scenario_id,
                        "sequence": trace["sequence"],
                        "trace_hash": trace["trace_hash"],
                        "transition_kind": trace["transition_kind"],
                        "policy_invoked": trace["policy_invoked"],
                        "life_index_after": trace["lifecycle_after"]["life_index"],
                        "trial_status_after": trace["lifecycle_after"]["trial_status"],
                        "life_termination": deepcopy(trace["life_termination"]),
                        "carry_component_hashes": _carry_hash_summary(trace),
                        "policy_projection_hash": trace.get("policy_projection_hash"),
                    },
                    producer_function="trace_record",
                    input_artifacts=_source_inputs(),
                    seed_context_episode_ids={
                        "scenario_id": scenario_id,
                        "episode_id": trace["episode_id"],
                        "sequence": trace["sequence"],
                    },
                    aggregation_rule="one canonical compute_step lifecycle transition",
                    run_id=trace["run_id"],
                )
            )
    records.append(
        _evidence_payload(
            {
                "evidence_kind": "real_terminal_controller_sqlite_summary",
                "value": terminal_live["value"],
                "transition_kinds": deepcopy(terminal_live["transition_kinds"]),
                "row_counts": deepcopy(terminal_live["row_counts"]),
            },
            producer_function="trace_record.terminal_live",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"scenario_id": "terminal_controller_sqlite"},
            aggregation_rule="summary of the real TerminalPlayground plus SQLite trigger path",
            run_id=str(terminal_live["run_id"]),
        )
    )
    records.append(
        _evidence_payload(
            {
                "evidence_kind": "real_tk_controller_sqlite_summary",
                "value": tk_live["value"],
                "tk_available": tk_live["tk_available"],
                "final_trace_hash": tk_live.get("final_trace_hash"),
                "terminal_life_result": deepcopy(tk_live.get("terminal_life_result")),
            },
            producer_function="trace_record.tk_live",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"scenario_id": "tk_controller_sqlite_terminal"},
            aggregation_rule="summary of the real Tk Run plus controller/SQLite trigger path",
            run_id=str(tk_live["run_id"]),
        )
    )
    return records


def run_card_c_verification(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    _clean_output_dir(output)
    inputs = _source_inputs()
    scenarios = _build_declared_scenarios()

    with tempfile.TemporaryDirectory(prefix="ego-v2-card-c-live-") as temp_name:
        temp_root = Path(temp_name)
        life_sixteen_reject = _life_sixteen_rejection_report(
            scenarios["life_sixteen_terminal"], temp_root
        )
        terminal_live = exercise_real_terminal_run(temp_root)
        tk_live = exercise_real_tk_run(temp_root)

    replay_scenarios = dict(scenarios)
    terminal_bundle_source = deepcopy(terminal_live["bundle_source"])
    terminal_bundle_source["states"] = []
    replay_scenarios["terminal_controller_sqlite"] = terminal_bundle_source

    baseline = build_baseline_report(scenarios)
    ablation = build_no_carry_ablation_report(
        scenarios["death_respawn_next_action"]
    )
    replay = build_replay_report(replay_scenarios)
    source_scan = build_single_path_source_report()

    policy_projections = [
        deepcopy(trace["policy_projection"])
        for scenario in scenarios.values()
        for trace in scenario["traces"]
        if trace.get("policy_projection") is not None
    ]
    clean_scan = scan_policy_projection({"projections": policy_projections})
    positive_scan = scan_policy_projection(
        {"projections": policy_projections}, inject_positive_control=True
    )

    trace_records = _trace_records(scenarios, terminal_live, tk_live)
    trace_provenance_scan = validate_recursive_provenance(trace_records)
    _write_jsonl(output / "trace.jsonl", trace_records)
    trace_input = _file_record(output / "trace.jsonl", logical_path=LOGICAL_TRACE_PATH)
    leakage = _evidence_payload(
        {
            "scan_scope": "policy_projection_only",
            "projection_count": len(policy_projections),
            "clean_scan": clean_scan,
            "positive_control_scan": positive_scan,
        },
        producer_function="build_leakage_report",
        input_artifacts=[*inputs, trace_input],
        seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
        aggregation_rule=(
            "scan only exact action-trace policy projections and prove the scanner with "
            "life_index/seed/token_mapping positive controls"
        ),
    )

    provenance_scan = validate_recursive_provenance(
        {
            "baseline": baseline,
            "ablation": ablation,
            "leakage": leakage,
            "replay": replay,
            "source_scan": source_scan,
            "life_sixteen_reject": life_sixteen_reject,
            "terminal_live": {
                key: value for key, value in terminal_live.items() if key != "bundle_source"
            },
            "tk_live": tk_live,
            "trace_provenance_scan": trace_provenance_scan,
        }
    )

    death = scenarios["death_respawn_next_action"]
    censor = scenarios["censor_respawn"]
    fourth = scenarios["life_sixteen_terminal"]
    death_transitions = [trace["transition_kind"] for trace in death["traces"]]
    death_flags = [trace["policy_invoked"] for trace in death["traces"]]
    censor_transitions = [trace["transition_kind"] for trace in censor["traces"]]
    all_respawn_traces = [death["traces"][1], censor["traces"][1]]
    all_tamper_controls = [
        control
        for scenario in replay["scenarios"].values()
        for control in scenario["tamper_controls"].values()
    ]

    checks = {
        "declared_lifecycle_scenarios_observed": _check_record(
            set(scenarios)
            == {"death_respawn_next_action", "censor_respawn", "life_sixteen_terminal"},
            producer_function="_build_declared_scenarios",
            input_artifacts=inputs,
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule="all three predeclared Card-C reducer scenarios must execute",
        ),
        "death_respawn_next_action_chain": _check_record(
            death_transitions == ["action", "respawn", "action"]
            and death_flags == [True, False, True]
            and death["traces"][0]["life_termination"]["termination"] == "death"
            and death["traces"][0]["model_update"]["applied"] is True
            and death["traces"][0]["memory_update"]["applied"] is True
            and death["final_state"]["lifecycle"]["life_index"] == 2,
            producer_function="engine.compute_step",
            input_artifacts=inputs,
            seed_context_episode_ids={"scenario_id": "death_respawn_next_action", "life_indices": [1, 2]},
            aggregation_rule=(
                "terminal death action keeps updates, next command is pure respawn, and the "
                "following command invokes one life-two policy action"
            ),
        ),
        "censor_respawn_chain": _check_record(
            censor_transitions == ["action", "respawn"]
            and censor["traces"][0]["life_termination"]
            == {
                "life_index": 1,
                "survival_ticks": 256,
                "censored": True,
                "termination": "censored",
            }
            and censor["final_state"]["lifecycle"]["life_index"] == 2,
            producer_function="engine.compute_step",
            input_artifacts=inputs,
            seed_context_episode_ids={"scenario_id": "censor_respawn", "life_indices": [1, 2]},
            aggregation_rule="living tick 256 must censor and the next command must be pure respawn",
        ),
        "life_sixteen_terminal_reject": _check_record(
            fourth["final_state"]["lifecycle"]["trial_status"] == "terminal"
            and len(fourth["final_state"]["lifecycle"]["life_results"])
            == engine.MAX_LIVES
            and fourth["final_state"]["lifecycle"]["terminal_life_result"]
            == {"survival_ticks": 256, "censored": True}
            and life_sixteen_reject["value"] is True,
            producer_function="engine.compute_step + terminal guards",
            input_artifacts=inputs,
            seed_context_episode_ids={"scenario_id": "life_sixteen_terminal", "life_index": engine.MAX_LIVES},
            aggregation_rule=(
                "final-life censor must end the trial, emit the terminal-life metric, and reject "
                "both reducer and controller follow-up dispatch"
            ),
        ),
        "real_terminal_controller_sqlite_path": _check_record(
            terminal_live["value"] is True,
            producer_function=str(terminal_live["producer_function"]),
            input_artifacts=[*inputs, trace_input],
            seed_context_episode_ids={"scenario_id": "terminal_controller_sqlite"},
            aggregation_rule="real TerminalPlayground run must traverse controller plus SQLite and recover",
        ),
        "real_tk_run_controller_sqlite_path": _check_record(
            tk_live["value"] is True,
            producer_function=str(tk_live["producer_function"]),
            input_artifacts=[*inputs, trace_input],
            seed_context_episode_ids={"scenario_id": "tk_controller_sqlite_terminal"},
            aggregation_rule=(
                "real Tk Run control must traverse controller plus SQLite to a recovered "
                "life-four terminal state; Tk unavailability is a blocker"
            ),
        ),
        "pure_respawn_carry_reset_exact": _check_record(
            all(_pure_respawn(trace) and _receipt_is_exact(trace) for trace in all_respawn_traces),
            producer_function="engine.compute_step respawn branch",
            input_artifacts=inputs,
            seed_context_episode_ids={"scenario_ids": ["death_respawn_next_action", "censor_respawn"]},
            aggregation_rule=(
                "every declared respawn must invoke no policy/metabolism/update and every "
                "named carry/reset component must match its recomputed expected bytes"
            ),
        ),
        "independent_scripted_respawn_baseline_reported": _check_record(
            baseline["independence_probe"]["value"] is True
            and baseline["candidate_reducer_called"] is False
            and baseline["candidate_scorer_called"] is False
            and baseline["disposition"]
            in {"observable_equivalence_claim_blocker", "non_equivalent"}
            and bool(baseline["comparisons"]),
            producer_function="build_baseline_report",
            input_artifacts=inputs,
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule=(
                "independent scripted lifecycle baseline must run without candidate reducer "
                "or scorer; equivalence blocks claims but not engineering"
            ),
        ),
        "no_carry_ablation_executed": _check_record(
            all(item["invoked"] is True for item in ablation["invocation_ledger"])
            and ablation["science_adjudication_authorized"] is False
            and ablation["product_api_modified_for_intervention"] is False
            and ablation["comparison"]["starting_model_memory_were_cleared"] is True
            and ablation["comparison"]["model_matches_empty_constructor"] is True
            and ablation["comparison"]["memory_matches_empty_constructor"] is True
            and ablation["comparison"]["model_differs_from_canonical_post_respawn"] is True
            and ablation["comparison"]["memory_differs_from_canonical_post_respawn"] is True,
            producer_function="build_no_carry_ablation_report",
            input_artifacts=inputs,
            seed_context_episode_ids={"scenario_id": "death_respawn_next_action", "life_index": 2},
            aggregation_rule=(
                "canonical and test-only cleared post-respawn states must rerun the same "
                "command through compute_step; observed equivalence is reported, not adjudicated"
            ),
        ),
        "policy_projection_leakage_scan_clean_positive_control_fires": _check_record(
            clean_scan["offenders"] == []
            and positive_scan["positive_control_detected"] is True
            and {item["category"] for item in positive_scan["offenders"]}
            == {"life_index", "seed", "token_mapping"},
            producer_function="scan_policy_projection",
            input_artifacts=[*inputs, trace_input],
            seed_context_episode_ids={"scenario_ids": sorted(scenarios)},
            aggregation_rule=(
                "only policy projections are scanned; they must be clean while all three "
                "declared structured positive controls fire"
            ),
        ),
        "replay_two_fresh_processes_match": _check_record(
            all(
                item["fresh_process_match"]["value"] is True
                for item in replay["scenarios"].values()
            )
            and replay["stored_selected_actions_used_as_input"] is False,
            producer_function="build_replay_report",
            input_artifacts=[*inputs, trace_input],
            seed_context_episode_ids={"scenario_ids": sorted(replay["scenarios"])},
            aggregation_rule=(
                "all declared bundles must replay identically locally and in two fresh "
                "processes from initial state plus commands without stored action inputs"
            ),
        ),
        "replay_tamper_controls_fail_closed": _check_record(
            all(control["value"] is True for control in all_tamper_controls),
            producer_function="build_replay_report",
            input_artifacts=[*inputs, trace_input],
            seed_context_episode_ids={"scenario_ids": sorted(replay["scenarios"])},
            aggregation_rule=(
                "initial/command/trace/carry/policy-flag/fourth-result hostile controls must "
                "all fail closed where applicable"
            ),
        ),
        "single_controller_reducer_store_path": _check_record(
            source_scan["value"] is True,
            producer_function="build_single_path_source_report",
            input_artifacts=inputs,
            seed_context_episode_ids={"source_scan": True},
            aggregation_rule="AST/source scan must find no second controller/reducer/store/UI bypass",
        ),
        "recursive_provenance_present": _check_record(
            provenance_scan["offenders"] == [] and trace_provenance_scan["offenders"] == [],
            producer_function="validate_recursive_provenance",
            input_artifacts=[*inputs, trace_input],
            seed_context_episode_ids={"scenario_ids": sorted(replay["scenarios"])},
            aggregation_rule=(
                "all nested metric/verdict records including trace records require complete "
                "provenance and raw_data cannot hide evidence signals"
            ),
        ),
    }
    aggregated = aggregate_result({key: checks[key] for key in ACCEPTANCE_GATE_IDS})
    claim_blockers: list[str] = []
    if baseline["disposition"] == "observable_equivalence_claim_blocker":
        claim_blockers.append("scripted_respawn_observable_equivalence")
    if ablation["comparison"]["behavior_equivalent"] is True:
        claim_blockers.append("no_carry_behavior_equivalence_science_unadjudicated")
    environment_blockers = [] if tk_live["tk_available"] else ["tk_runtime_unavailable"]

    result = _evidence_payload(
        {
            "task_id": TASK_ID,
            "layer": "Layer 2 engineering plus bounded Layer 3 mechanism hypothesis",
            "mainline_integration_status": "existing explicit local V2 product path",
            "enabled_status": "enabled=true; default_enabled=false; explicit launch only",
            "science_weight": engine.make_run_metadata(
                f"{RUN_ID}-science-weight", POLICY_SEED
            )["science_weight"],
            "checks": checks,
            "source_scan": deepcopy(source_scan),
            "verdict": aggregated["verdict"],
            "failed_checks": aggregated["failed_checks"],
            "baseline_disposition": baseline["disposition"],
            "ablation_observation": deepcopy(ablation["comparison"]),
            "science_adjudication_authorized": False,
            "claim_blockers": claim_blockers,
            "environment_blockers": environment_blockers,
            "claim_ceiling": CLAIM_CEILING,
            "provenance_scan": provenance_scan,
        },
        producer_function="run_card_c_verification",
        input_artifacts=[*inputs, trace_input],
        seed_context_episode_ids={
            "scenario_ids": sorted(replay["scenarios"]),
            "life_indices": list(range(1, engine.MAX_LIVES + 1)),
        },
        aggregation_rule=(
            "pass iff every declared Card-C engineering check is computed true; baseline or "
            "ablation equivalence blocks science claims but is not an engineering failure"
        ),
    )
    failure_manifest = _evidence_payload(
        {
            "engineering_failures": aggregated["failed_checks"],
            "environment_blockers": environment_blockers,
            "claim_blockers": claim_blockers,
            "science_adjudication_authorized": False,
            "status": "clean" if not aggregated["failed_checks"] else "fail",
        },
        producer_function="run_card_c_verification.failure_manifest",
        input_artifacts=result["input_artifacts"],
        seed_context_episode_ids=result["seed_context_episode_ids"],
        aggregation_rule=(
            "preserve engineering failures, environment blockers, and negative/equivalent "
            "claim blockers without upgrading or hiding them"
        ),
    )

    _write_json(output / "baseline_comparison.json", baseline)
    _write_json(output / "ablation_report.json", ablation)
    _write_json(output / "leakage_report.json", leakage)
    _write_json(output / "replay_report.json", replay)
    _write_json(output / "failure_manifest.json", failure_manifest)
    _write_json(output / "result.json", result)
    (output / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
    )

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
    result = run_card_c_verification(args.output_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
