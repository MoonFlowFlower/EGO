#!/usr/bin/env python3
"""Callable old-smoke and balanced five-action gate for bounded task 001C.

The public execution surface contains only ``--gate``.  Private modes recover
or re-evaluate the two already-consumed contexts.  This module has no callable
that creates worlds 60--65 or policy seeds 721/722.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import statistics
import subprocess
import sys
import time
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine, predictive_control  # noqa: E402
from labs.ego_life_playground_v0.controller import PlaygroundController  # noqa: E402
from labs.ego_life_playground_v0.microworld import (  # noqa: E402
    policy_observation,
    transition_world,
)
from labs.ego_life_playground_v0.store import (  # noqa: E402
    RecoveryResult,
    SQLiteEventStore,
)


TASK_ID = "EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-BOUNDARY-GATE-001C"
FIXTURE_NAME = "prechange_semantic_fixture.json"
PRECHANGE_SOURCE_COMMIT = "a18771497a16f51aeba22fddb93f4ca7d266871c"
CONTEXTS = (
    ("p0_cross_v1", 52, 711),
    ("p2_vertical_v1", 54, 711),
)
ALLOWED_WORLD_SEEDS = frozenset({52, 54})
ALLOWED_POLICY_SEEDS = frozenset({711})
FORBIDDEN_WORLD_SEEDS = frozenset(range(60, 66))
FORBIDDEN_POLICY_SEEDS = frozenset({721, 722})
CLAIM_CEILING = (
    "Old-context product runtime/replay boundary evidence and balanced five-action "
    "predictor-error change within worlds 52/54 and policy seed 711 only."
)
PRODUCER = "verify_ego_v2_factored_predictive_control_boundary_gate_001c"


def _canonical_json(value: Any) -> str:
    return engine.canonical_json(value)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hash_file(path: Path) -> str:
    return _hash_bytes(path.read_bytes())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        _canonical_json(value) + "\n", encoding="utf-8", newline="\n"
    )
    os.replace(temporary, path)


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(_canonical_json(row) + "\n")
    os.replace(temporary, path)


def _artifact_ref(path: Path, *, relative_to: Path | None = None) -> dict[str, str]:
    display = path.name if relative_to is None else path.relative_to(relative_to).as_posix()
    return {"path": display, "sha256": _hash_file(path)}


def _context_id(layout: str, world_seed: int, policy_seed: int) -> str:
    return f"{layout}:world={world_seed}:policy={policy_seed}"


def _current_smoke_run_id(context_id: str) -> str:
    return f"{TASK_ID}:current-smoke:{context_id}"


def _gate_code_path_hash() -> str:
    return _canonical_hash(
        {
            "engine_code_path_hash": engine.compute_code_path_hash(),
            "verifier_sha256": _hash_file(Path(__file__).resolve()),
        }
    )


def _provenance(
    producer_function: str,
    *,
    inputs: list[Any],
    run_id: str,
    aggregation_rule: str,
    context_ids: list[str] | None = None,
    seeds: list[int] | None = None,
    life_ids: list[int] | None = None,
    action_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "producer_function": f"{PRODUCER}.{producer_function}",
        "input_artifacts": inputs,
        "run_id": run_id,
        "seed": [] if seeds is None else seeds,
        "context_ids": [] if context_ids is None else context_ids,
        "life_ids": [] if life_ids is None else life_ids,
        "action_ids": [] if action_ids is None else action_ids,
        "aggregation_rule": aggregation_rule,
        "code_path_hash": _gate_code_path_hash(),
    }


def _git_bytes(commit: str, relative: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _git_blob(commit: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", f"{commit}:{relative}"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def verify_prechange_fixture(fixture_path: Path) -> dict[str, Any]:
    """Verify the immutable fixture and every recorded source from its commit."""

    fixture_path = fixture_path.resolve()
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    expected_contexts = [_context_id(*context) for context in CONTEXTS]
    if fixture.get("context_ids") != expected_contexts:
        raise RuntimeError("sealed pre-change fixture context boundary drifted")
    if fixture.get("fresh_effect_seeds_consumed") is not False:
        raise RuntimeError("sealed pre-change fixture consumed a forbidden context")
    if len(fixture.get("steps", [])) != 204:
        raise RuntimeError("sealed pre-change fixture must contain 204 action steps")

    relative_fixture = fixture_path.relative_to(REPO_ROOT).as_posix()
    committed_fixture = _git_bytes(PRECHANGE_SOURCE_COMMIT, relative_fixture)
    current_fixture = fixture_path.read_bytes()
    if current_fixture != committed_fixture:
        raise RuntimeError("sealed pre-change fixture bytes differ from source commit")

    source_receipts: dict[str, dict[str, Any]] = {}
    for relative, expected_hash in sorted(fixture["input_source_hashes"].items()):
        source_bytes = _git_bytes(PRECHANGE_SOURCE_COMMIT, relative)
        actual_hash = _hash_bytes(source_bytes)
        source_receipts[relative] = {
            "git_blob_id": _git_blob(PRECHANGE_SOURCE_COMMIT, relative),
            "recorded_sha256": expected_hash,
            "canonical_git_blob_sha256": actual_hash,
            "legacy_worktree_raw_sha_reproducible": actual_hash == expected_hash,
            "transport_note": (
                None
                if actual_hash == expected_hash
                else "recorded capture-time raw working-tree SHA used mixed CRLF/LF bytes; "
                "the canonical Git blob is normalized and does not reproduce that transport hash"
            ),
        }
    all_raw_reproducible = all(
        item["legacy_worktree_raw_sha_reproducible"] for item in source_receipts.values()
    )
    return {
        "producer_function": f"{PRODUCER}.verify_prechange_fixture",
        "source_commit": PRECHANGE_SOURCE_COMMIT,
        "fixture": {
            "path": relative_fixture,
            "git_blob_id": _git_blob(PRECHANGE_SOURCE_COMMIT, relative_fixture),
            "sha256": _hash_bytes(current_fixture),
            "bytes_equal_to_commit": True,
        },
        "source_files": source_receipts,
        "all_historical_paths_git_bound": all(
            bool(item["git_blob_id"]) for item in source_receipts.values()
        ),
        "all_legacy_worktree_raw_sha_reproducible": all_raw_reproducible,
        "provenance_limitation": (
            None
            if all_raw_reproducible
            else "some legacy raw working-tree SHA-256 values are not reproducible from "
            "normalized Git blobs because capture-time files used mixed line endings"
        ),
        "aggregation_rule": "fixture_blob_exact_plus_each_historical_path_git_blob_binding_with_raw_transport_caveat",
        "code_path_hash": _gate_code_path_hash(),
    }


def capture_prechange_baseline(_output_dir: Path) -> dict[str, Any]:
    raise RuntimeError(
        "sealed pre-change fixture cannot be overwritten by current product bytes"
    )


def _metabolism_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "energy_before",
        "passive_decay",
        "action_cost",
        "food_gain",
        "food_obtained",
        "energy_after",
        "energy_delta",
        "selected_action",
    )
    return {key: deepcopy(value.get(key)) for key in keys}


def _lifecycle_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    transition = value.get("episode_transition")
    projected_transition = transition
    if isinstance(transition, Mapping):
        projected_transition = {
            key: deepcopy(transition.get(key))
            for key in (
                "kind",
                "from_episode_index",
                "to_episode_index",
                "rollover_global_tick",
            )
            if key in transition
        }
    return {
        "before": deepcopy(value.get("before")),
        "after": deepcopy(value.get("after")),
        "life_termination": deepcopy(value.get("life_termination")),
        "episode_transition": projected_transition,
        "carry_reset_receipt_is_none": value.get("carry_reset_receipt") is None,
    }


def _prediction_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(value.get(key))
        for key in (
            "outcome_probabilities",
            "predicted_delta",
            "resource_interaction_probability",
            "terminal_risk",
        )
    }


def _beam_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    roots = value.get("root_action_counts_by_depth")
    if roots is None and isinstance(value.get("root_actions_by_depth"), list):
        roots = [len(set(actions)) for actions in value["root_actions_by_depth"]]
    return {
        "expanded_by_depth": deepcopy(value.get("expanded_by_depth")),
        "retained_by_depth": deepcopy(value.get("retained_by_depth")),
        "root_action_counts_by_depth": deepcopy(roots),
        "all_probability_mass_normalized": deepcopy(
            value.get("all_probability_mass_normalized")
        ),
    }


def _semantic_projection(step: Mapping[str, Any]) -> dict[str, Any]:
    predictions = step.get("predictions_by_action") or {}
    return {
        "selected_action": deepcopy(step.get("selected_action")),
        "world_transition": deepcopy(step.get("world_transition")),
        "food_gain": deepcopy(step.get("food_gain")),
        "metabolism": _metabolism_projection(step.get("metabolism") or {}),
        "goal_before": deepcopy(step.get("goal_before")),
        "goal_progress": deepcopy(step.get("goal_progress")),
        "goal_transition": deepcopy(step.get("goal_transition")),
        "goal_after": deepcopy(step.get("goal_after")),
        "lifecycle": _lifecycle_projection(step.get("lifecycle") or {}),
        "action_exposure_counts": deepcopy(step.get("action_exposure_counts")),
        "token_interaction_counts": deepcopy(step.get("token_interaction_counts")),
        "predictions_by_action": {
            action: _prediction_projection(predictions[action])
            for action in engine.ACTIONS
        },
        "candidate_values": deepcopy(step.get("candidate_values")),
        "beam_receipt": _beam_projection(step.get("beam_receipt") or {}),
    }


def _compare_values(
    expected: Any,
    actual: Any,
    *,
    path: str,
    differences: list[dict[str, Any]],
) -> float:
    if isinstance(expected, bool) or isinstance(actual, bool):
        if type(expected) is not type(actual) or expected != actual:
            differences.append({"field": path, "expected": expected, "actual": actual})
        return 0.0
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        difference = abs(float(expected) - float(actual))
        if difference > 1e-12:
            differences.append(
                {
                    "field": path,
                    "expected": expected,
                    "actual": actual,
                    "abs_difference": difference,
                }
            )
        return difference
    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        if set(expected) != set(actual):
            differences.append(
                {
                    "field": path,
                    "expected_keys": sorted(expected),
                    "actual_keys": sorted(actual),
                }
            )
        maximum = 0.0
        for key in sorted(set(expected) & set(actual), key=str):
            maximum = max(
                maximum,
                _compare_values(
                    expected[key],
                    actual[key],
                    path=f"{path}.{key}",
                    differences=differences,
                ),
            )
        return maximum
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            differences.append(
                {"field": path, "expected_length": len(expected), "actual_length": len(actual)}
            )
        maximum = 0.0
        for index, (left, right) in enumerate(zip(expected, actual)):
            maximum = max(
                maximum,
                _compare_values(
                    left,
                    right,
                    path=f"{path}[{index}]",
                    differences=differences,
                ),
            )
        return maximum
    if expected != actual:
        differences.append({"field": path, "expected": expected, "actual": actual})
    return 0.0


def compare_semantic_steps(
    fixture: Mapping[str, Any], current_steps: list[Mapping[str, Any]]
) -> dict[str, Any]:
    expected_steps = list(fixture.get("steps", []))
    differences: list[dict[str, Any]] = []
    if len(expected_steps) != len(current_steps):
        differences.append(
            {
                "field": "action_step_count",
                "expected": len(expected_steps),
                "actual": len(current_steps),
            }
        )
    maximum = 0.0
    for index, (expected, actual) in enumerate(zip(expected_steps, current_steps)):
        expected_identity = (
            expected.get("context_id"),
            expected.get("sequence"),
            expected.get("life"),
        )
        actual_identity = (
            actual.get("context_id"),
            actual.get("sequence"),
            actual.get("life"),
        )
        if expected_identity != actual_identity:
            differences.append(
                {
                    "field": f"steps[{index}].identity",
                    "expected": expected_identity,
                    "actual": actual_identity,
                }
            )
        maximum = max(
            maximum,
            _compare_values(
                _semantic_projection(expected),
                _semantic_projection(actual),
                path=f"steps[{index}]",
                differences=differences,
            ),
        )
    return {
        "producer_function": f"{PRODUCER}.compare_semantic_steps",
        "compared_action_steps": min(len(expected_steps), len(current_steps)),
        "expected_action_steps": len(expected_steps),
        "current_action_steps": len(current_steps),
        "all_exact_semantics_equal": not differences,
        "max_abs_numeric_difference": maximum,
        "numeric_tolerance": 1e-12,
        "differences": differences[:200],
        "difference_count": len(differences),
        "aggregation_rule": "ordered_204_action_step_exact_semantics_and_recursive_numeric_max",
        "code_path_hash": _gate_code_path_hash(),
    }


def _current_step_record(
    trace: Mapping[str, Any], *, context_id: str, world_seed: int
) -> dict[str, Any]:
    predictive = trace["predictive_control"]
    plan = predictive["plan"]
    if trace.get("selected_action") is None or plan is None:
        raise RuntimeError("semantic action record requires a selected action")
    return {
        "run_id": trace["run_id"],
        "context_id": context_id,
        "seed": trace["seed"],
        "world_seed": world_seed,
        "life": int(trace["action_episode"]["episode_index"]) + 1,
        "sequence": trace["sequence"],
        "selected_action": trace["selected_action"],
        "world_transition": deepcopy(trace["world_transition"]),
        "food_gain": trace["food_gain"],
        "metabolism": deepcopy(trace["metabolism"]),
        "goal_progress": deepcopy(trace["goal_progress"]),
        "goal_transition": deepcopy(trace["goal_transition"]),
        "goal_before": deepcopy(trace["goal_before"]),
        "goal_after": deepcopy(trace["goal_after"]),
        "lifecycle": {
            "before": deepcopy(trace["lifecycle_before"]),
            "after": deepcopy(trace["lifecycle_after"]),
            "life_termination": deepcopy(trace["life_termination"]),
            "episode_transition": deepcopy(trace["episode_transition"]),
            "carry_reset_receipt": deepcopy(trace["carry_reset_receipt"]),
        },
        "action_exposure_counts": deepcopy(plan["action_exposure_counts"]),
        "token_interaction_counts": deepcopy(plan["token_interaction_counts"]),
        "predictions_by_action": deepcopy(plan["predictions_by_action"]),
        "candidate_values": deepcopy(plan["candidate_values"]),
        "beam_receipt": deepcopy(plan["beam_receipt"]),
    }


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]


def _recovery_signature(recovered: RecoveryResult) -> dict[str, Any]:
    return {
        "sequence": recovered.last_committed_sequence,
        "state_hash": engine.state_hash(recovered.state),
        "trace_chain_hash": engine.canonical_hash(recovered.traces),
        "verification_mode": recovered.verification_mode,
    }


def _export_signature(path: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    traces = [row["trace"] for row in rows[1:]]
    return {
        "sequence": traces[-1]["sequence"] if traces else 0,
        "state_hash": traces[-1]["state_after_hash"] if traces else None,
        "trace_chain_hash": engine.canonical_hash(traces),
        "verification_mode": "full_replay",
    }


def _assert_db_context_allowed(db_path: Path, run_id: str) -> tuple[int, int]:
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute(
            "SELECT run_meta_json, initial_state_json FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise RuntimeError("private recovery run is absent")
    run_meta = json.loads(row[0])
    initial = json.loads(row[1])
    policy_seed = int(run_meta["seed"])
    world_seed = int(initial["world"]["trial"]["seed"])
    if world_seed in FORBIDDEN_WORLD_SEEDS or policy_seed in FORBIDDEN_POLICY_SEEDS:
        raise RuntimeError("fresh-effect context firewall rejected private recovery")
    if world_seed not in ALLOWED_WORLD_SEEDS or policy_seed not in ALLOWED_POLICY_SEEDS:
        raise RuntimeError("private recovery is outside the exact consumed-context allowlist")
    return world_seed, policy_seed


def _private_replay(db_path: Path, run_id: str) -> dict[str, Any]:
    world_seed, policy_seed = _assert_db_context_allowed(db_path, run_id)
    started = time.perf_counter()
    with SQLiteEventStore(db_path) as store:
        recovered = store.recover_run(run_id)
    recover_run_seconds = time.perf_counter() - started
    return _recovery_signature(recovered) | {
        "world_seed": world_seed,
        "seed": policy_seed,
        "recover_run_seconds": recover_run_seconds,
    }


def _fresh_replay_subprocess(db_path: Path, run_id: str) -> dict[str, Any]:
    started = time.perf_counter()
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--private-replay",
            str(db_path),
            "--private-run-id",
            run_id,
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    process_wall_seconds = time.perf_counter() - started
    payload = json.loads(completed.stdout)
    payload["process_wall_seconds"] = process_wall_seconds
    return payload


def _db_live_bytes(db_path: Path) -> int:
    return sum(
        path.stat().st_size
        for path in (
            db_path,
            Path(str(db_path) + "-wal"),
            Path(str(db_path) + "-shm"),
        )
        if path.exists()
    )


def _reject_recovery(path: Path, run_id: str) -> tuple[bool, str | None, str | None]:
    try:
        with SQLiteEventStore(path) as store:
            store.recover_run(run_id)
    except Exception as exc:  # exact fail-closed exception is evidence output
        return True, type(exc).__name__, str(exc)
    return False, None, None


def run_tamper_controls(
    db_path: Path, run_id: str, working_dir: Path
) -> dict[str, dict[str, Any]]:
    """Apply four independent mutations and require recomputing recovery rejection."""

    _assert_db_context_allowed(db_path, run_id)
    working_dir.mkdir(parents=True, exist_ok=True)
    reports: dict[str, dict[str, Any]] = {}
    for name in (
        "command",
        "predictive_model_hash",
        "plan_prediction",
        "update_receipt",
    ):
        target = working_dir / f"{name}.sqlite3"
        if target.exists():
            target.unlink()
        shutil.copy2(db_path, target)
        connection = sqlite3.connect(target)
        try:
            if name == "command":
                sequence, raw = connection.execute(
                    "SELECT sequence, command_json FROM commands WHERE run_id = ? ORDER BY sequence LIMIT 1",
                    (run_id,),
                ).fetchone()
                command = json.loads(raw)
                command["trigger_source"] = "headless_acceptance"
                unsigned = {key: value for key, value in command.items() if key != "command_hash"}
                command["command_hash"] = engine.canonical_hash(unsigned)
                connection.execute(
                    "UPDATE commands SET command_json = ?, command_hash = ? WHERE run_id = ? AND sequence = ?",
                    (_canonical_json(command), command["command_hash"], run_id, sequence),
                )
            elif name == "predictive_model_hash":
                raw = connection.execute(
                    "SELECT initial_state_json FROM runs WHERE run_id = ?", (run_id,)
                ).fetchone()[0]
                state = json.loads(raw)
                state["predictive_control"]["model"]["outcome_weights"][0][0][0] = 1.0
                state["component_hashes"]["predictive_control"] = engine.canonical_hash(
                    state["predictive_control"]
                )
                connection.execute(
                    "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
                    (_canonical_json(state), engine.canonical_hash(state), run_id),
                )
            else:
                sequence, raw = connection.execute(
                    "SELECT sequence, trace_json FROM traces WHERE run_id = ? "
                    "AND json_extract(trace_json, '$.selected_action') IS NOT NULL "
                    "ORDER BY sequence LIMIT 1",
                    (run_id,),
                ).fetchone()
                trace = json.loads(raw)
                if name == "plan_prediction":
                    prediction = trace["predictive_control"]["plan"]["predictions_by_action"][
                        engine.ACTIONS[0]
                    ]
                    prediction["outcome_probabilities"][predictive_control.OUTCOMES[0]] += 0.001
                else:
                    update = trace["predictive_control"]["update"]
                    update["outcome_brier"] = float(update["outcome_brier"]) + 1.0
                trace["trace_hash"] = engine.compute_trace_hash(trace)
                connection.execute(
                    "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = ?",
                    (_canonical_json(trace), trace["trace_hash"], run_id, sequence),
                )
            connection.commit()
        finally:
            connection.close()
        rejected, exception_type, exception_message = _reject_recovery(target, run_id)
        reports[name] = {
            "producer_function": f"{PRODUCER}.run_tamper_controls",
            "source_sqlite_sha256": _hash_file(db_path),
            "tampered_sqlite_sha256": _hash_file(target),
            "mutation": name,
            "rehashed": True,
            "rejected": rejected,
            "exception_type": exception_type,
            "exception_message": exception_message,
            "aggregation_rule": "mutate_copy_recompute_affected_hashes_then_full_recovery",
            "code_path_hash": _gate_code_path_hash(),
        }
        target.unlink()
    return reports


def _source_path_scan() -> dict[str, Any]:
    paths = {
        "engine": REPO_ROOT / "labs/ego_life_playground_v0/engine.py",
        "controller": REPO_ROOT / "labs/ego_life_playground_v0/controller.py",
        "store": REPO_ROOT / "labs/ego_life_playground_v0/store.py",
        "ui": REPO_ROOT / "labs/ego_life_playground_v0/visual_console.py",
        "terminal": REPO_ROOT / "labs/ego_life_playground_v0/terminal.py",
    }
    trees = {
        name: ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for name, path in paths.items()
    }

    def function_defs(tree: ast.AST, name: str) -> int:
        return sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
            for node in ast.walk(tree)
        )

    def class_defs(tree: ast.AST, name: str) -> int:
        return sum(isinstance(node, ast.ClassDef) and node.name == name for node in ast.walk(tree))

    def call_count(tree: ast.AST, name: str) -> int:
        return sum(
            isinstance(node, ast.Call)
            and (
                isinstance(node.func, ast.Name)
                and node.func.id == name
                or isinstance(node.func, ast.Attribute)
                and node.func.attr == name
            )
            for node in ast.walk(tree)
        )

    forbidden_defs = sorted(
        {
            node.name
            for tree in trees.values()
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and ("checkpoint" in node.name.lower() or "stored_plan" in node.name.lower())
        }
    )
    checks = {
        "one_compute_step_definition": function_defs(trees["engine"], "compute_step") == 1,
        "one_product_controller_class": class_defs(trees["controller"], "PlaygroundController") == 1,
        "one_product_store_class": class_defs(trees["store"], "SQLiteEventStore") == 1,
        "controller_calls_compute_step_once": call_count(trees["controller"], "compute_step") == 1,
        "store_calls_compute_step_once": call_count(trees["store"], "compute_step") == 1,
        "ui_calls_controller_dispatch": call_count(trees["ui"], "dispatch") >= 1,
        "terminal_calls_controller_dispatch": call_count(trees["terminal"], "dispatch") >= 1,
        "no_checkpoint_or_stored_plan_reducer": not forbidden_defs,
    }
    return {
        "producer_function": f"{PRODUCER}._source_path_scan",
        "inputs": [
            {"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": _hash_file(path)}
            for path in paths.values()
        ],
        "checks": checks,
        "forbidden_definitions": forbidden_defs,
        "passed": all(checks.values()),
        "aggregation_rule": "python_ast_single_reducer_controller_store_and_ui_terminal_dispatch_scan",
        "code_path_hash": _gate_code_path_hash(),
    }


def _reconstruct_command_from_trace(trace: Mapping[str, Any]) -> dict[str, Any]:
    command = {
        "schema_version": engine.COMMAND_SCHEMA_VERSION,
        "sequence": trace["sequence"],
        "injected_event": deepcopy(trace["injected_event"]),
        "trigger_source": trace["trigger_source"],
        "interventions": deepcopy(trace["interventions"]),
        "prev_command_hash": trace["prev_command_hash"],
        "command_hash": trace["command_hash"],
    }
    unsigned = {key: value for key, value in command.items() if key != "command_hash"}
    if engine.canonical_hash(unsigned) != command["command_hash"]:
        raise RuntimeError("compact trace command projection does not rehash")
    if trace.get("command") != command:
        raise RuntimeError("trace command copy differs from compact command projection")
    return command


def _run_smoke_context(
    output_dir: Path,
    fixture: Mapping[str, Any],
    layout: str,
    world_seed: int,
    policy_seed: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    context_id = _context_id(layout, world_seed, policy_seed)
    fixture_run_id = next(
        run["run_id"] for run in fixture["runs"] if run["context_id"] == context_id
    )
    run_id = _current_smoke_run_id(context_id)
    db_path = output_dir / f"smoke_{layout}.sqlite3"
    for candidate in (db_path, Path(str(db_path) + "-wal"), Path(str(db_path) + "-shm")):
        if candidate.exists():
            candidate.unlink()
    export_path = output_dir / f"smoke_{layout}_export.jsonl"
    if export_path.exists():
        export_path.unlink()
    interventions = dict(
        engine.DEFAULT_INTERVENTIONS,
        predictive_control_mode="factored_mpc",
        update_mode="canonical",
    )
    durations: list[float] = []
    trace_rows: list[dict[str, Any]] = []
    semantic_steps: list[dict[str, Any]] = []
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(
            store,
            run_id=run_id,
            seed=policy_seed,
            world_seed=world_seed,
            layout_id=layout,
        )
        while len(controller.state["lifecycle"]["life_results"]) < 4:
            started = time.perf_counter()
            dispatched = controller.dispatch(
                interventions,
                trigger_source="ui_run_button",
            )
            duration = time.perf_counter() - started
            if not dispatched.receipt.committed:
                raise RuntimeError(dispatched.receipt.error)
            trace = controller.last_trace
            if trace is None:
                raise RuntimeError("committed controller dispatch lacks a trace")
            trace_bytes = len(_canonical_json(trace).encode("utf-8"))
            durations.append(duration)
            trace_rows.append(
                _provenance(
                    "_run_smoke_context",
                    inputs=[
                        f"command:{trace['command_hash']}",
                        f"trace:{trace['trace_hash']}",
                    ],
                    run_id=run_id,
                    aggregation_rule="one_committed_controller_command_including_respawn",
                    context_ids=[context_id],
                    seeds=[policy_seed],
                    life_ids=[
                        int(
                            (
                                trace.get("action_episode")
                                or trace["episode_before"]
                            )["episode_index"]
                        )
                        + 1
                    ],
                    action_ids=([] if trace["selected_action"] is None else [trace["selected_action"]]),
                )
                | {
                    "world_seed": world_seed,
                    "episode_id": trace["episode_id"],
                    "sequence": trace["sequence"],
                    "transition_kind": trace["transition_kind"],
                    "selected_action": trace["selected_action"],
                    "command": _reconstruct_command_from_trace(trace),
                    "trace_hash": trace["trace_hash"],
                    "state_after_hash": trace["state_after_hash"],
                    "dispatch_seconds": duration,
                    "trace_bytes": trace_bytes,
                    "row_readback_verified": dispatched.receipt.row_readback_verified,
                }
            )
            if trace["selected_action"] is not None:
                semantic_steps.append(
                    _current_step_record(
                        trace, context_id=context_id, world_seed=world_seed
                    )
                )

        online = _recovery_signature(controller.recovery)
        same_process = _recovery_signature(store.recover_run(run_id))
        startup_controller = PlaygroundController(store, run_id=run_id)
        startup = _recovery_signature(startup_controller.recovery)
        loaded = _recovery_signature(startup_controller.load_run(run_id))
        explicit = _recovery_signature(startup_controller.recover())
        startup_controller.export(export_path)
        exported = _export_signature(export_path)
        row_readbacks = all(row["row_readback_verified"] for row in trace_rows)
        final_model_hash = predictive_control.model_hash(controller.state["predictive_control"])
        final_update_count = int(controller.state["predictive_control"]["model"]["update_count"])
    sqlite_bytes = _db_live_bytes(db_path)
    sqlite_hash = _hash_file(db_path)
    recoveries = [_fresh_replay_subprocess(db_path, run_id) for _ in range(3)]
    recovery_signatures = [
        {
            key: value
            for key, value in item.items()
            if key not in {"recover_run_seconds", "process_wall_seconds", "verification_mode"}
        }
        for item in recoveries
    ]
    expected_private = {
        key: value for key, value in online.items() if key != "verification_mode"
    } | {"world_seed": world_seed, "seed": policy_seed}
    for item, signature in zip(recoveries, recovery_signatures):
        item["exact"] = signature == expected_private
    tamper = run_tamper_controls(db_path, run_id, output_dir / ".tamper_work")
    recovery_surfaces = {
        "online": online,
        "same_process_recover_run": same_process,
        "controller_startup": startup,
        "load_run": loaded,
        "explicit_recover": explicit,
        "export": exported,
    }
    result = _provenance(
        "_run_smoke_context",
        inputs=[{"path": db_path.name, "sha256": sqlite_hash}],
        run_id=run_id,
        aggregation_rule="four_completed_lives_real_controller_dispatch_and_sqlite",
        context_ids=[context_id],
        seeds=[policy_seed],
        life_ids=[1, 2, 3, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "world_seed": world_seed,
        "prechange_fixture_run_id": fixture_run_id,
        "database_path": db_path.name,
        "export_path": export_path.name,
        "command_count": len(trace_rows),
        "action_step_count": len(semantic_steps),
        "dispatch_p95_seconds": _p95(durations),
        "dispatch_max_seconds": max(durations),
        "duration_first_32_mean": statistics.fmean(durations[:32]),
        "duration_last_32_mean": statistics.fmean(durations[-32:]),
        "duration_tail_ratio": statistics.fmean(durations[-32:])
        / statistics.fmean(durations[:32]),
        "recovery_attempts": recoveries,
        "trace_mean_bytes": statistics.fmean(row["trace_bytes"] for row in trace_rows),
        "trace_max_bytes": max(row["trace_bytes"] for row in trace_rows),
        "sqlite_and_sidecar_bytes": sqlite_bytes,
        "row_readbacks_verified": row_readbacks,
        "recovery_surfaces": recovery_surfaces,
        "all_recovery_surfaces_exact": all(
            {key: value for key, value in surface.items() if key != "verification_mode"}
            == {key: value for key, value in online.items() if key != "verification_mode"}
            for surface in recovery_surfaces.values()
        ),
        "tamper_controls": tamper,
        "all_tamper_controls_rejected": all(item["rejected"] for item in tamper.values()),
        "final_model_hash": final_model_hash,
        "final_update_count": final_update_count,
    }
    return result, trace_rows, semantic_steps


def compute_smoke_checks(runs: list[Mapping[str, Any]]) -> dict[str, bool]:
    return {
        "semantic_equivalence_exact_204_steps": all(
            bool(run.get("semantic_equivalence_passed")) for run in runs
        ),
        "dispatch_p95_at_most_250ms": all(
            float(run["dispatch_p95_seconds"]) <= 0.250 for run in runs
        ),
        "dispatch_max_at_most_500ms": all(
            float(run["dispatch_max_seconds"]) <= 0.500 for run in runs
        ),
        "last32_first32_ratio_below_2": all(
            float(run["duration_tail_ratio"]) < 2.0 for run in runs
        ),
        "three_fresh_recoveries_each_at_most_10s_and_exact": all(
            len(run["recovery_attempts"]) == 3
            and all(
                float(item["recover_run_seconds"]) <= 10.0 and bool(item["exact"])
                for item in run["recovery_attempts"]
            )
            for run in runs
        ),
        "trace_mean_at_most_32768_bytes": all(
            float(run["trace_mean_bytes"]) <= 32768 for run in runs
        ),
        "trace_max_at_most_65536_bytes": all(
            int(run["trace_max_bytes"]) <= 65536 for run in runs
        ),
        "sqlite_plus_sidecars_at_most_20mib": all(
            int(run["sqlite_and_sidecar_bytes"]) <= 20 * 1024 * 1024 for run in runs
        ),
        "all_row_readbacks_verified": all(
            bool(run["row_readbacks_verified"]) for run in runs
        ),
        "all_recovery_surfaces_exact": all(
            bool(run["all_recovery_surfaces_exact"]) for run in runs
        ),
        "all_four_rehash_tamper_controls_rejected": all(
            bool(run["all_tamper_controls_rejected"]) for run in runs
        ),
        "single_product_path_ast_scan_passed": all(
            bool(run["single_path_scan_passed"]) for run in runs
        ),
    }


def run_old_smoke(output_dir: Path) -> dict[str, Any]:
    fixture_path = REPO_ROOT / "artifacts" / TASK_ID / FIXTURE_NAME
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    fixture_receipt = verify_prechange_fixture(fixture_path)
    source_scan = _source_path_scan()
    runs: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    semantic_steps: list[dict[str, Any]] = []
    for context in CONTEXTS:
        run, rows, steps = _run_smoke_context(output_dir, fixture, *context)
        runs.append(run)
        trace_rows.extend(rows)
        semantic_steps.extend(steps)
    equivalence = compare_semantic_steps(fixture, semantic_steps)
    equivalence.update(
        _provenance(
            "run_old_smoke",
            inputs=[
                _artifact_ref(fixture_path, relative_to=REPO_ROOT),
                {"source_commit": PRECHANGE_SOURCE_COMMIT},
            ],
            run_id=f"{TASK_ID}:equivalence",
            aggregation_rule="sealed_commit_provenance_plus_ordered_204_action_semantic_comparison",
            context_ids=[_context_id(*context) for context in CONTEXTS],
            seeds=[711],
            life_ids=[1, 2, 3, 4],
            action_ids=list(engine.ACTIONS),
        )
    )
    equivalence["prechange_fixture_verification"] = fixture_receipt
    for run in runs:
        run["semantic_equivalence_passed"] = (
            equivalence["all_exact_semantics_equal"]
            and equivalence["compared_action_steps"] == 204
            and equivalence["max_abs_numeric_difference"] <= 1e-12
        )
        run["single_path_scan_passed"] = source_scan["passed"]
    checks = compute_smoke_checks(runs)
    failed = sorted(name for name, value in checks.items() if not value)
    smoke_trace_path = output_dir / "smoke_trace.jsonl"
    _write_jsonl(smoke_trace_path, trace_rows)
    (output_dir / "trace.jsonl").write_bytes(smoke_trace_path.read_bytes())
    performance = _provenance(
        "run_old_smoke",
        inputs=[
            {"path": run["database_path"], "sha256": _hash_file(output_dir / run["database_path"])}
            for run in runs
        ],
        run_id=f"{TASK_ID}:performance",
        aggregation_rule="per_context_exact_threshold_checks_over_all_committed_commands",
        context_ids=[run["context_ids"][0] for run in runs],
        seeds=[711],
        life_ids=[1, 2, 3, 4],
        action_ids=list(engine.ACTIONS),
    ) | {"runs": runs, "checks": checks, "failed_checks": failed}
    replay = _provenance(
        "run_old_smoke",
        inputs=[
            {"path": run["database_path"], "sha256": _hash_file(output_dir / run["database_path"])}
            for run in runs
        ],
        run_id=f"{TASK_ID}:replay",
        aggregation_rule="same_process_controller_load_recover_export_three_fresh_processes_and_tamper",
        context_ids=[run["context_ids"][0] for run in runs],
        seeds=[711],
        life_ids=[1, 2, 3, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "smoke_runs": [
            {
                "context_id": run["context_ids"][0],
                "recovery_surfaces": run["recovery_surfaces"],
                "recovery_attempts": run["recovery_attempts"],
                "tamper_controls": run["tamper_controls"],
            }
            for run in runs
        ],
        "source_path_scan": source_scan,
        "balanced_replay": "pending_smoke_decision",
    }
    result = _provenance(
        "run_old_smoke",
        inputs=[_artifact_ref(smoke_trace_path)],
        run_id=f"{TASK_ID}:smoke",
        aggregation_rule="all_old_smoke_checks_must_pass_before_balanced_evaluation",
        context_ids=[run["context_ids"][0] for run in runs],
        seeds=[711],
        life_ids=[1, 2, 3, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "schema_version": "ego.v2.factored_predictive_control_boundary_gate.smoke.v1",
        "runs": runs,
        "checks": checks,
        "failed_checks": failed,
        "boundary_passed": not failed,
        "fresh_effect_seeds_consumed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_json(output_dir / "smoke_result.json", result)
    _write_json(output_dir / "performance_report.json", performance)
    _write_json(output_dir / "equivalence_report.json", equivalence)
    _write_json(output_dir / "replay_report.json", replay)
    return result


def evaluate_no_update_predictions(
    learned_state: Mapping[str, Any],
    *,
    observation: Mapping[str, Any],
    organism: Mapping[str, float],
) -> dict[str, dict[str, Any]]:
    no_update = deepcopy(dict(learned_state))
    no_update["model"] = deepcopy(predictive_control.empty_state()["model"])
    predictions: dict[str, dict[str, Any]] = {}
    for action in engine.ACTIONS:
        predictions[action] = predictive_control.predict_action(
            no_update,
            observation=observation,
            organism=organism,
            action=action,
            relative_map_mode="relative",
        )
    return predictions


def score_prediction(
    prediction: Mapping[str, Any], truth: Mapping[str, Any]
) -> dict[str, float]:
    outcome = str(truth["outcome_type"])
    probabilities = prediction["outcome_probabilities"]
    brier = sum(
        (float(probabilities[item]) - (1.0 if item == outcome else 0.0)) ** 2
        for item in predictive_control.OUTCOMES
    )
    nll = -math.log(max(float(probabilities[outcome]), 1e-12))
    mae = statistics.fmean(
        abs(float(prediction["predicted_delta"][key]) - float(truth["actual_delta"][key]))
        for key in predictive_control.STATE_KEYS
    )
    return {"outcome_brier": brier, "outcome_nll": nll, "delta_mae": mae}


def aggregate_balanced_metrics(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    cells: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        cells[(str(row["context_id"]), str(row["action"]))].append(row)
    cell_metrics: list[dict[str, float]] = []
    for key in sorted(cells):
        cell_rows = cells[key]
        cell_metrics.append(
            {
                metric: statistics.fmean(float(row["scores"][metric]) for row in cell_rows)
                for metric in ("outcome_brier", "outcome_nll", "delta_mae")
            }
        )
    return {
        "cell_count": len(cell_metrics),
        "outcome_brier": statistics.fmean(item["outcome_brier"] for item in cell_metrics),
        "outcome_nll": statistics.fmean(item["outcome_nll"] for item in cell_metrics),
        "delta_mae": statistics.fmean(item["delta_mae"] for item in cell_metrics),
        "aggregation_rule": "mean_within_context_action_then_equal_macro_mean_across_cells",
    }


def evaluate_balanced_snapshots(
    snapshots: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for snapshot in snapshots:
        learned: dict[str, dict[str, Any]] = {}
        for action in engine.ACTIONS:
            prediction = predictive_control.predict_action(
                snapshot["predictive_state"],
                observation=snapshot["observation"],
                organism=snapshot["organism"],
                action=action,
                relative_map_mode="relative",
            )
            if not snapshot.get("skip_root_hash_check"):
                if engine.canonical_hash(prediction) != snapshot["root_prediction_hashes"][action]:
                    raise RuntimeError("balanced root prediction differs from product trace")
            learned[action] = prediction
        no_update = evaluate_no_update_predictions(
            snapshot["predictive_state"],
            observation=snapshot["observation"],
            organism=snapshot["organism"],
        )
        truth_by_action: dict[str, dict[str, Any]] = {}
        for action in engine.ACTIONS:
            next_world, world_transition = transition_world(
                snapshot["world"],
                action,
                source_sequence=int(snapshot["sequence"]),
                source_episode_id=str(snapshot["episode_id"]),
                source_command_hash=str(snapshot["command_hash"]),
            )
            metabolism = engine.compute_metabolism_ledger(
                energy_before=float(snapshot["organism"]["energy"]),
                selected_action=action,
                world_before=snapshot["world"],
                world_after=next_world,
                world_transition=world_transition,
                run_meta=snapshot.get("run_meta", {"run_id": snapshot["run_id"], "seed": snapshot["seed"]}),
                episode_id=str(snapshot["episode_id"]),
                command_hash=str(snapshot["command_hash"]),
                code_path_hash=engine.compute_code_path_hash(),
            )
            actual_delta = engine.compute_actual_delta(
                world_transition, selected_action=action
            )
            actual_delta["energy"] = metabolism["energy_delta"]
            truth_by_action[action] = {
                "outcome_type": world_transition["outcome_type"],
                "world_transition": world_transition,
                "actual_delta": actual_delta,
                "metabolism_energy_delta": metabolism["energy_delta"],
            }
        for model_name, predictions in (("learned", learned), ("no_update", no_update)):
            for action in engine.ACTIONS:
                truth = truth_by_action[action]
                prediction = predictions[action]
                rows.append(
                    _provenance(
                        "evaluate_balanced_snapshots",
                        inputs=[
                            f"snapshot:{snapshot['snapshot_hash'] if 'snapshot_hash' in snapshot else _canonical_hash(snapshot)}",
                            f"prediction:{engine.canonical_hash(prediction)}",
                            f"truth:{engine.canonical_hash(truth)}",
                        ],
                        run_id=str(snapshot["run_id"]),
                        aggregation_rule="one_snapshot_one_action_one_model_independent_prediction_then_private_truth",
                        context_ids=[str(snapshot["context_id"])],
                        seeds=[int(snapshot["seed"])],
                        life_ids=[int(snapshot["life"])],
                        action_ids=[action],
                    )
                    | {
                        "context_id": snapshot["context_id"],
                        "snapshot_hash": snapshot.get("snapshot_hash", _canonical_hash(snapshot)),
                        "world_seed": snapshot["world_seed"],
                        "phase": snapshot["phase"],
                        "sequence": snapshot["sequence"],
                        "model": model_name,
                        "action": action,
                        "prediction": prediction,
                        "truth": truth,
                        "scores": score_prediction(prediction, truth),
                    }
                )
    return rows


def _collect_balanced_snapshots(
    db_path: Path, run_id: str, context_id: str, world_seed: int, policy_seed: int
) -> list[dict[str, Any]]:
    _assert_db_context_allowed(db_path, run_id)
    with SQLiteEventStore(db_path) as store:
        recovered = store.recover_run(run_id)
        command_rows = store.connection.execute(
            "SELECT sequence, command_json FROM commands WHERE run_id = ? ORDER BY sequence",
            (run_id,),
        ).fetchall()
    commands = {int(row["sequence"]): json.loads(row["command_json"]) for row in command_rows}
    snapshots: list[dict[str, Any]] = []
    for previous_frame, frame in zip(recovered.frames, recovered.frames[1:]):
        trace = frame.trace
        if trace is None or trace.get("selected_action") is None:
            continue
        life = int(trace["action_episode"]["episode_index"]) + 1
        if life not in {1, 4}:
            continue
        command = commands[int(trace["sequence"])]
        if command["injected_event"] is not None:
            raise RuntimeError("balanced snapshot encountered forbidden injection")
        decision_state, _ = engine._decision_state_for_tick(  # noqa: SLF001
            previous_frame.state,
            run_id=run_id,
            sequence=int(trace["sequence"]),
        )
        observation = policy_observation(decision_state["world"], occlusion=True)
        prepared, _ = predictive_control.observe_belief(
            decision_state["predictive_control"],
            observation=observation,
            episode_index=int(decision_state["clock"]["episode_index"]),
            mode="relative",
        )
        prepared_decision = dict(decision_state)
        prepared_decision["predictive_control"] = prepared
        component_hashes = dict(prepared_decision["component_hashes"])
        component_hashes["predictive_control"] = engine.canonical_hash(prepared)
        prepared_decision["component_hashes"] = component_hashes
        if engine.state_hash(prepared_decision) != trace["decision_state_hash"]:
            raise RuntimeError("balanced pre-action decision state differs from product trace")
        root_hashes = {
            action: trace["predictive_control"]["plan"]["predictions_by_action"][action][
                "prediction_hash"
            ]
            for action in engine.ACTIONS
        }
        snapshot = {
            "context_id": context_id,
            "run_id": run_id,
            "seed": policy_seed,
            "world_seed": world_seed,
            "life": life,
            "phase": "early" if life == 1 else "late",
            "sequence": trace["sequence"],
            "episode_id": trace["episode_id"],
            "command_hash": trace["command_hash"],
            "run_meta": recovered.run_meta,
            "predictive_state": prepared,
            "observation": observation,
            "organism": deepcopy(decision_state["organism"]),
            "world": deepcopy(decision_state["world"]),
            "root_prediction_hashes": root_hashes,
        }
        snapshot["snapshot_hash"] = _canonical_hash(snapshot)
        snapshots.append(snapshot)
    return snapshots


def _aggregate_all(rows: list[dict[str, Any]]) -> dict[str, Any]:
    aggregate: dict[str, Any] = {}
    for model in ("learned", "no_update"):
        aggregate[model] = {}
        for phase in ("early", "late"):
            selected = [row for row in rows if row["model"] == model and row["phase"] == phase]
            aggregate[model][phase] = aggregate_balanced_metrics(selected)
    return aggregate


def _balanced_digest(payload: Mapping[str, Any]) -> dict[str, Any]:
    rows = payload["rows"]
    return {
        "snapshot_hashes": list(payload["snapshot_hashes"]),
        "prediction_rows_hash": _canonical_hash(
            [
                {
                    "snapshot_hash": row["snapshot_hash"],
                    "model": row["model"],
                    "action": row["action"],
                    "prediction": row["prediction"],
                }
                for row in rows
            ]
        ),
        "truth_rows_hash": _canonical_hash(
            [
                {
                    "snapshot_hash": row["snapshot_hash"],
                    "action": row["action"],
                    "truth": row["truth"],
                }
                for row in rows
                if row["model"] == "learned"
            ]
        ),
        "aggregate_hash": _canonical_hash(payload["aggregate_metrics"]),
        "payload_hash": _canonical_hash(
            {
                "snapshot_hashes": payload["snapshot_hashes"],
                "rows": rows,
                "aggregate_metrics": payload["aggregate_metrics"],
            }
        ),
    }


def _compute_balanced_payload(output_dir: Path) -> dict[str, Any]:
    smoke = json.loads((output_dir / "smoke_result.json").read_text(encoding="utf-8"))
    expected_contexts = [_context_id(*context) for context in CONTEXTS]
    if smoke.get("context_ids") != expected_contexts:
        raise RuntimeError("private balanced evaluator context manifest drifted")
    snapshots: list[dict[str, Any]] = []
    for run, (layout, world_seed, policy_seed) in zip(smoke["runs"], CONTEXTS):
        context_id = _context_id(layout, world_seed, policy_seed)
        if run["context_ids"] != [context_id] or run["seed"] != [policy_seed]:
            raise RuntimeError("private balanced evaluator seed/context manifest drifted")
        snapshots.extend(
            _collect_balanced_snapshots(
                output_dir / run["database_path"],
                run["run_id"],
                context_id,
                world_seed,
                policy_seed,
            )
        )
    rows = evaluate_balanced_snapshots(snapshots)
    return {
        "snapshot_hashes": [snapshot["snapshot_hash"] for snapshot in snapshots],
        "rows": rows,
        "aggregate_metrics": _aggregate_all(rows),
    }


def run_leakage_controls(clean_payload: Mapping[str, Any]) -> dict[str, Any]:
    clean_scan = predictive_control.scan_predictor_input_leakage(clean_payload)
    controls = {
        "global_position": [4, 3],
        "cause": "resource",
        "token_mapping": {"v0": "resource"},
        "seed": 52,
        "future_observation": deepcopy(clean_payload),
    }
    positive: dict[str, dict[str, Any]] = {}
    for field, value in controls.items():
        contaminated = deepcopy(dict(clean_payload))
        contaminated[field] = value
        scan = predictive_control.scan_predictor_input_leakage(contaminated)
        detected = any(item["field"] == field for item in scan["findings"])
        positive[field] = {"detected": detected, "scan": scan}
    return {
        "producer_function": "ego_life_playground_v0.predictive_control.scan_predictor_input_leakage",
        "clean_scan": clean_scan,
        "positive_controls": positive,
        "all_positive_controls_detected": all(item["detected"] for item in positive.values()),
        "aggregation_rule": "clean_scan_plus_five_independent_forbidden_field_positive_controls",
        "code_path_hash": _gate_code_path_hash(),
    }


def _run_frozen_control(
    output_dir: Path, layout: str, world_seed: int, policy_seed: int
) -> dict[str, Any]:
    context_id = _context_id(layout, world_seed, policy_seed)
    run_id = f"{TASK_ID}:frozen-update:{context_id}"
    db_path = output_dir / f"frozen_{layout}.sqlite3"
    for candidate in (db_path, Path(str(db_path) + "-wal"), Path(str(db_path) + "-shm")):
        if candidate.exists():
            candidate.unlink()
    interventions = dict(
        engine.DEFAULT_INTERVENTIONS,
        predictive_control_mode="factored_mpc",
        update_mode="frozen",
    )
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(
            store,
            run_id=run_id,
            seed=policy_seed,
            world_seed=world_seed,
            layout_id=layout,
        )
        initial_hash = predictive_control.model_hash(controller.state["predictive_control"])
        selected: list[str] = []
        while len(controller.state["lifecycle"]["life_results"]) < 4:
            dispatched = controller.dispatch(interventions, trigger_source="ui_run_button")
            if not dispatched.receipt.committed:
                raise RuntimeError(dispatched.receipt.error)
            if controller.last_trace["selected_action"] is not None:
                selected.append(controller.last_trace["selected_action"])
        recovered = store.recover_run(run_id)
        final_hash = predictive_control.model_hash(recovered.state["predictive_control"])
        update_count = int(recovered.state["predictive_control"]["model"]["update_count"])
    first_twenty = Counter(selected[:20])
    return _provenance(
        "_run_frozen_control",
        inputs=[{"path": db_path.name, "sha256": _hash_file(db_path)}],
        run_id=run_id,
        aggregation_rule="four_completed_lives_frozen_predictor_updates",
        context_ids=[context_id],
        seeds=[policy_seed],
        life_ids=[1, 2, 3, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "world_seed": world_seed,
        "database_path": db_path.name,
        "initial_model_hash": initial_hash,
        "final_model_hash": final_hash,
        "model_hash_unchanged": initial_hash == final_hash,
        "update_count": update_count,
        "first_20_actions": selected[:20],
        "first_20_action_counts": {action: first_twenty[action] for action in engine.ACTIONS},
        "first_20_cover_each_action_at_least_four": all(
            first_twenty[action] >= 4 for action in engine.ACTIONS
        ),
    }


def run_balanced_evaluation(output_dir: Path) -> dict[str, Any]:
    payload = _compute_balanced_payload(output_dir)
    aggregate = payload["aggregate_metrics"]
    rows = payload["rows"]
    snapshot_count = len(payload["snapshot_hashes"])
    learned_rows = [row for row in rows if row["model"] == "learned"]
    action_counts = Counter(row["action"] for row in learned_rows)
    context_phase_counts = Counter(
        (row["context_id"], row["phase"], row["action"]) for row in learned_rows
    )
    smoke_manifest = json.loads((output_dir / "smoke_result.json").read_text(encoding="utf-8"))
    first_run = smoke_manifest["runs"][0]
    first_snapshot = _collect_balanced_snapshots(
        output_dir / first_run["database_path"],
        first_run["run_id"],
        _context_id(*CONTEXTS[0]),
        CONTEXTS[0][1],
        CONTEXTS[0][2],
    )[0]
    clean_payload = predictive_control.predictor_input_snapshot(
        first_snapshot["predictive_state"],
        observation=first_snapshot["observation"],
        organism=first_snapshot["organism"],
        relative_map_mode="relative",
    )
    leakage = run_leakage_controls(clean_payload)
    frozen = [_run_frozen_control(output_dir, *context) for context in CONTEXTS]
    expected_digest = _balanced_digest(payload)
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--private-evaluate", str(output_dir)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    fresh_digest = json.loads(completed.stdout)
    replay_exact = fresh_digest == expected_digest
    checks = {
        "all_five_action_counts_exactly_equal": len(set(action_counts.values())) == 1
        and set(action_counts) == set(engine.ACTIONS),
        "no_snapshot_action_context_unused": len(learned_rows) == snapshot_count * len(engine.ACTIONS)
        and len(context_phase_counts) == len(CONTEXTS) * 2 * len(engine.ACTIONS)
        and all(count > 0 for count in context_phase_counts.values()),
        "learned_late_brier_improves_by_at_least_0_02": aggregate["learned"]["late"][
            "outcome_brier"
        ]
        <= aggregate["learned"]["early"]["outcome_brier"] - 0.02,
        "learned_late_nll_improves_by_at_least_0_05": aggregate["learned"]["late"][
            "outcome_nll"
        ]
        <= aggregate["learned"]["early"]["outcome_nll"] - 0.05,
        "learned_late_brier_below_no_update_late": aggregate["learned"]["late"][
            "outcome_brier"
        ]
        < aggregate["no_update"]["late"]["outcome_brier"],
        "learned_late_nll_below_no_update_late": aggregate["learned"]["late"]["outcome_nll"]
        < aggregate["no_update"]["late"]["outcome_nll"],
        "learned_late_delta_mae_below_early_and_no_update": aggregate["learned"]["late"][
            "delta_mae"
        ]
        < aggregate["learned"]["early"]["delta_mae"]
        and aggregate["learned"]["late"]["delta_mae"]
        < aggregate["no_update"]["late"]["delta_mae"],
        "leakage_clean_and_all_positive_controls_detected": leakage["clean_scan"]["clean"]
        and leakage["all_positive_controls_detected"],
        "fresh_subprocess_balanced_recompute_exact": replay_exact,
        "two_frozen_update_controls_pass": all(
            item["model_hash_unchanged"]
            and item["update_count"] == 0
            and item["first_20_cover_each_action_at_least_four"]
            for item in frozen
        ),
    }
    failed = sorted(name for name, value in checks.items() if not value)
    report = _provenance(
        "run_balanced_evaluation",
        inputs=[
            _artifact_ref(output_dir / "smoke_result.json"),
            *[
                {"path": item["database_path"], "sha256": _hash_file(output_dir / item["database_path"])}
                for item in frozen
            ],
        ],
        run_id=f"{TASK_ID}:balanced",
        aggregation_rule="mean_within_context_phase_action_then_equal_macro_over_ten_cells_per_phase_model",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        seeds=[711],
        life_ids=[1, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "schema_version": "ego.v2.factored_predictive_control_boundary_gate.balanced_prediction.v1",
        "status": "completed",
        "snapshot_count": snapshot_count,
        "snapshot_hashes": payload["snapshot_hashes"],
        "sample_counts_by_action": {action: action_counts[action] for action in engine.ACTIONS},
        "aggregate_metrics": aggregate,
        "rows": rows,
        "frozen_update_controls": frozen,
        "checks": checks,
        "failed_checks": failed,
        "passed": not failed,
        "fresh_subprocess_digest_expected": expected_digest,
        "fresh_subprocess_digest_actual": fresh_digest,
        "fresh_effect_seeds_consumed": False,
    }
    _write_json(output_dir / "leakage_report.json", leakage | _provenance(
        "run_leakage_controls",
        inputs=[f"clean:{leakage['clean_scan']['input_hash']}"],
        run_id=f"{TASK_ID}:leakage",
        aggregation_rule="clean_plus_five_independent_positive_controls",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        seeds=[711],
        life_ids=[1, 4],
        action_ids=list(engine.ACTIONS),
    ))
    return report


def _not_run_report(
    name: str, output_dir: Path, smoke: Mapping[str, Any]
) -> dict[str, Any]:
    return _provenance(
        "run_gate",
        inputs=[_artifact_ref(output_dir / "smoke_result.json")]
        if (output_dir / "smoke_result.json").exists()
        else [],
        run_id=f"{TASK_ID}:{name}:not-run",
        aggregation_rule="not_run_boundary_failed",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        seeds=[711],
        life_ids=[],
        action_ids=list(engine.ACTIONS),
    ) | {
        "status": "not_run_boundary_failed",
        "boundary_failed_checks": sorted(
            name for name, value in smoke.get("checks", {}).items() if not value
        ),
        "fresh_effect_seeds_consumed": False,
    }


def run_gate(output_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    smoke = run_old_smoke(output_dir)
    boundary_passed = all(smoke.get("checks", {}).values())
    if not boundary_passed:
        balanced = _not_run_report("balanced", output_dir, smoke)
        baseline = _not_run_report("baseline", output_dir, smoke)
        ablation = _not_run_report("ablation", output_dir, smoke)
        leakage = _not_run_report("leakage", output_dir, smoke)
        verdict = "BOUNDARY_REPAIR_FAILED"
        eligible = False
        balanced_status = "not_run_boundary_failed"
    else:
        balanced = run_balanced_evaluation(output_dir)
        baseline = _provenance(
            "run_gate",
            inputs=[{"path": "balanced_prediction_report.json", "sha256": "written-after-computation"}],
            run_id=f"{TASK_ID}:baseline",
            aggregation_rule="same_snapshots_independently_callable_zero_initialized_no_update_predictor",
            context_ids=[_context_id(*context) for context in CONTEXTS],
            seeds=[711],
            life_ids=[1, 4],
            action_ids=list(engine.ACTIONS),
        ) | {
            "status": "completed",
            "baseline": "zero_initialized_no_update_predictor",
            "metrics": balanced["aggregate_metrics"]["no_update"],
            "independent_callable": True,
        }
        ablation = _provenance(
            "run_gate",
            inputs=[{"path": "balanced_prediction_report.json", "sha256": "written-after-computation"}],
            run_id=f"{TASK_ID}:ablation",
            aggregation_rule="two_real_four_life_frozen_update_controller_runs",
            context_ids=[_context_id(*context) for context in CONTEXTS],
            seeds=[711],
            life_ids=[1, 2, 3, 4],
            action_ids=list(engine.ACTIONS),
        ) | {
            "status": "completed",
            "ablation": "predictor_updates_frozen",
            "runs": balanced["frozen_update_controls"],
        }
        leakage = json.loads((output_dir / "leakage_report.json").read_text(encoding="utf-8"))
        if balanced["passed"]:
            verdict = "BOUNDARY_AND_BALANCED_PREDICTION_VERIFIED"
            eligible = True
        else:
            verdict = "BOUNDARY_REPAIRED_PREDICTION_NOT_IMPROVED"
            eligible = False
        balanced_status = "completed"
    _write_json(output_dir / "balanced_prediction_report.json", balanced)
    if boundary_passed:
        balanced_ref = _artifact_ref(output_dir / "balanced_prediction_report.json")
        baseline["input_artifacts"] = [balanced_ref]
        ablation["input_artifacts"] = [balanced_ref]
    _write_json(output_dir / "baseline_comparison.json", baseline)
    _write_json(output_dir / "ablation_report.json", ablation)
    if not boundary_passed:
        _write_json(output_dir / "leakage_report.json", leakage)

    replay_path = output_dir / "replay_report.json"
    if replay_path.exists():
        replay = json.loads(replay_path.read_text(encoding="utf-8"))
    else:
        replay = _not_run_report("replay", output_dir, smoke)
    replay["balanced_replay"] = (
        {
            "status": "completed",
            "exact": balanced["checks"]["fresh_subprocess_balanced_recompute_exact"],
            "expected": balanced["fresh_subprocess_digest_expected"],
            "actual": balanced["fresh_subprocess_digest_actual"],
        }
        if boundary_passed
        else "not_run_boundary_failed"
    )
    _write_json(replay_path, replay)

    failed_checks = list(smoke.get("failed_checks", []))
    if boundary_passed:
        failed_checks.extend(balanced["failed_checks"])
    failure_manifest = _provenance(
        "run_gate",
        inputs=[
            _artifact_ref(output_dir / "smoke_result.json")
            if (output_dir / "smoke_result.json").exists()
            else {"path": "smoke_result.json", "sha256": "test-double"},
            _artifact_ref(output_dir / "balanced_prediction_report.json"),
        ],
        run_id=f"{TASK_ID}:failure-manifest",
        aggregation_rule="record_all_failed_boundary_or_balanced_checks_without_threshold_tuning",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        seeds=[711],
        life_ids=[1, 2, 3, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "verdict": verdict,
        "status": "none" if not failed_checks else "failed_checks_recorded",
        "failed_checks": failed_checks,
        "fresh_effect_seeds_consumed": False,
    }
    _write_json(output_dir / "failure_manifest.json", failure_manifest)
    eligibility = _provenance(
        "run_gate",
        inputs=[
            _artifact_ref(output_dir / "smoke_result.json")
            if (output_dir / "smoke_result.json").exists()
            else {"path": "smoke_result.json", "sha256": "test-double"},
            _artifact_ref(output_dir / "balanced_prediction_report.json"),
        ],
        run_id=f"{TASK_ID}:effect-gate-eligibility",
        aggregation_rule="true_only_for_full_positive_verdict",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        seeds=[711],
        life_ids=[1, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "eligible": eligible,
        "eligible_for_separate_effect_card": eligible,
        "verdict": verdict,
        "fresh_effect_seeds_consumed": False,
        "route_or_enablement_record": False,
    }
    _write_json(output_dir / "effect_gate_eligibility.json", eligibility)
    (output_dir / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
    )
    result_inputs = [
        _artifact_ref(output_dir / name)
        for name in (
            "smoke_result.json",
            "performance_report.json",
            "equivalence_report.json",
            "balanced_prediction_report.json",
            "baseline_comparison.json",
            "ablation_report.json",
            "leakage_report.json",
            "replay_report.json",
            "failure_manifest.json",
            "effect_gate_eligibility.json",
        )
        if (output_dir / name).exists()
    ]
    result = _provenance(
        "run_gate",
        inputs=result_inputs,
        run_id=f"{TASK_ID}:result",
        aggregation_rule="old_smoke_must_pass_before_balanced_and_all_balanced_checks_for_positive",
        context_ids=[_context_id(*context) for context in CONTEXTS],
        seeds=[711],
        life_ids=[1, 2, 3, 4],
        action_ids=list(engine.ACTIONS),
    ) | {
        "schema_version": "ego.v2.factored_predictive_control_boundary_gate.result.v1",
        "task_id": TASK_ID,
        "verdict": verdict,
        "boundary_passed": boundary_passed,
        "balanced_prediction_status": balanced_status,
        "effect_gate_eligibility": eligible,
        "fresh_effect_seeds_consumed": False,
        "default_predictive_control_mode": engine.DEFAULT_INTERVENTIONS[
            "predictive_control_mode"
        ],
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_json(output_dir / "result.json", result)
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "artifacts" / TASK_ID,
    )
    parser.add_argument("--gate", action="store_true")
    parser.add_argument("--capture-baseline", action="store_true")
    parser.add_argument("--private-replay", type=Path)
    parser.add_argument("--private-run-id")
    parser.add_argument("--private-evaluate", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.capture_baseline:
        raise SystemExit(
            "sealed pre-change fixture cannot be overwritten by current product bytes"
        )
    if args.private_replay is not None:
        if not args.private_run_id:
            raise SystemExit("--private-run-id is required with --private-replay")
        print(_canonical_json(_private_replay(args.private_replay, args.private_run_id)))
        return 0
    if args.private_evaluate is not None:
        payload = _compute_balanced_payload(args.private_evaluate.resolve())
        print(_canonical_json(_balanced_digest(payload)))
        return 0
    if not args.gate:
        raise SystemExit("the only public execution mode is --gate")
    result = run_gate(args.output_dir.resolve())
    print(
        _canonical_json(
            {
                "verdict": result["verdict"],
                "effect_gate_eligibility": result["effect_gate_eligibility"],
                "fresh_effect_seeds_consumed": False,
                "result": str((args.output_dir / "result.json").resolve()),
            }
        )
    )
    return 0 if result["verdict"] == "BOUNDARY_AND_BALANCED_PREDICTION_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
