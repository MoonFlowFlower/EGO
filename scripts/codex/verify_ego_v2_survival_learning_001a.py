"""Callable product acceptance for EGO-V2-P1-SURVIVAL-EXPECTED-SARSA-001A."""

from __future__ import annotations

import argparse
import ast
from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterator, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine, survival_learning
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.microworld import (
    ACTIONS,
    transition_world,
    verify_world_state,
)
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore


TASK_ID = "EGO-V2-P1-SURVIVAL-EXPECTED-SARSA-001A"
CLAIM_CEILING = (
    "Replayable product adaptation evidence, if observed, is limited to the "
    "predeclared 16-life layouts and seeds; science_weight remains 0."
)
EQUIVALENCE_BAND = 0.05
POLICY_SEEDS = (701, 702)
LAYOUT_WORLD_SEEDS = {
    "p0_cross_v1": (30, 31),
    "p2_vertical_v1": (42, 43),
    "p2_offset_v1": (44, 45),
}
CONTROL_IDS = (
    "expected_sarsa_lambda",
    "learner_off",
    "no_update",
    "rest_only",
    "uniform_random",
    "shield_only",
    "empirical_lookup",
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


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _file_record(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        logical = resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        logical = resolved.name
    return {
        "path": logical,
        "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
    }


def _source_records() -> list[dict[str, Any]]:
    return [
        _file_record(REPO_ROOT / relative)
        for relative in (
            "labs/ego_life_playground_v0/engine.py",
            "labs/ego_life_playground_v0/survival_learning.py",
            "labs/ego_life_playground_v0/microworld.py",
            "labs/ego_life_playground_v0/store.py",
            "labs/ego_life_playground_v0/controller.py",
            "labs/ego_life_playground_v0/terminal.py",
            "labs/ego_life_playground_v0/visual_console.py",
            "scripts/codex/verify_ego_v2_survival_learning_001a.py",
        )
    ]


def evidence_code_path_hash() -> str:
    return canonical_hash(
        {
            "product_code_path_hash": engine.compute_code_path_hash(),
            "acceptance_sources": _source_records(),
        }
    )


def declared_contexts() -> list[dict[str, Any]]:
    return [
        {
            "context_id": f"{layout_id}:world={world_seed}:policy={policy_seed}",
            "layout_id": layout_id,
            "world_seed": world_seed,
            "policy_seed": policy_seed,
        }
        for layout_id, world_seeds in LAYOUT_WORLD_SEEDS.items()
        for world_seed in world_seeds
        for policy_seed in POLICY_SEEDS
    ]


def _heuristic_choice(scores: Mapping[str, float], eligible: tuple[str, ...]) -> str:
    maximum = max(float(scores[action]) for action in eligible)
    return min(action for action in eligible if float(scores[action]) == maximum)


class _ControlSelector:
    def __init__(self, control_id: str) -> None:
        self.control_id = control_id
        self.energy = 0.0
        self.life_index = 1
        self.lookup: dict[str, dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._original = survival_learning.select_action

    def observe(self, trace: Mapping[str, Any]) -> None:
        if self.control_id != "empirical_lookup" or self.life_index > 8:
            return
        receipt = trace["survival_learning"]
        state_key = str(receipt["state_key"])
        action = str(trace["selected_action"])
        reward = float(receipt["update"]["reward"])
        self.lookup[state_key][action].append(reward)

    def select(self, learner: Mapping[str, Any], **kwargs: Any) -> tuple[str, dict[str, Any]]:
        _selected, receipt = self._original(learner, **kwargs)
        scores = {key: float(value) for key, value in kwargs["candidate_scores"].items()}
        state_key = str(kwargs["state_key"])
        if self.control_id == "rest_only":
            selected = "rest"
        elif self.control_id == "uniform_random":
            digest = hashlib.sha256(
                canonical_json(
                    {
                        "producer": "uniform_random_control",
                        "run_seed": kwargs["run_seed"],
                        "episode_index": kwargs["episode_index"],
                        "sequence": kwargs["sequence"],
                        "state_key": state_key,
                    }
                ).encode("utf-8")
            ).digest()
            selected = str(ACTIONS[int.from_bytes(digest[:8], "big") % len(ACTIONS)])
        elif self.control_id == "shield_only":
            safe = tuple(
                action
                for action in ACTIONS
                if self.energy
                - engine.PASSIVE_ENERGY_DECAY_PER_TICK
                - engine.ACTION_COSTS[action]
                > 0.0
            )
            selected = _heuristic_choice(scores, safe or tuple(ACTIONS))
        elif self.control_id == "empirical_lookup":
            lookup_scores = {
                action: (
                    sum(self.lookup[state_key][action])
                    / len(self.lookup[state_key][action])
                    if self.lookup[state_key][action]
                    else 0.0
                )
                for action in ACTIONS
            }
            maximum = max(lookup_scores.values())
            eligible = tuple(action for action in ACTIONS if lookup_scores[action] == maximum)
            selected = _heuristic_choice(scores, eligible)
            receipt["q_by_action"] = {
                action: round(float(lookup_scores[action]), 12) for action in ACTIONS
            }
        else:
            raise ValueError(self.control_id)
        receipt["selected_action"] = selected
        receipt["selection_mode"] = self.control_id
        receipt["exploration_applied"] = self.control_id == "uniform_random"
        receipt["requested_mode"] = "off"
        return selected, receipt


@contextmanager
def _control_selector(control_id: str) -> Iterator[_ControlSelector | None]:
    if control_id not in {"rest_only", "uniform_random", "shield_only", "empirical_lookup"}:
        yield None
        return
    selector = _ControlSelector(control_id)
    original = survival_learning.select_action
    survival_learning.select_action = selector.select
    try:
        yield selector
    finally:
        survival_learning.select_action = original


def _interventions(control_id: str) -> dict[str, str]:
    if control_id == "expected_sarsa_lambda":
        return dict(
            engine.DEFAULT_INTERVENTIONS,
            survival_learning_mode=survival_learning.ALGORITHM,
        )
    if control_id == "no_update":
        return dict(
            engine.DEFAULT_INTERVENTIONS,
            survival_learning_mode=survival_learning.ALGORITHM,
            update_mode="frozen",
        )
    if control_id == "learner_off":
        return deepcopy(engine.DEFAULT_INTERVENTIONS)
    return dict(engine.DEFAULT_INTERVENTIONS, update_mode="frozen")


def simulate_context(spec: Mapping[str, Any]) -> dict[str, Any]:
    control_id = str(spec["control_id"])
    context_id = str(spec["context_id"])
    layout_id = str(spec["layout_id"])
    world_seed = int(spec["world_seed"])
    policy_seed = int(spec["policy_seed"])
    run_id = f"{TASK_ID}:{control_id}:{context_id}"
    state = engine.initial_state(
        run_id=run_id,
        seed=world_seed,
        layout_id=layout_id,
    )
    run_meta = engine.make_run_metadata(run_id, policy_seed)
    interventions = _interventions(control_id)
    command_hashes: list[str] = []
    trace_hashes: list[str] = []
    state_key_payloads: list[dict[str, Any]] = []
    resource_by_life = [0 for _ in range(engine.MAX_LIVES)]
    selection_modes: dict[str, int] = defaultdict(int)

    with _control_selector(control_id) as selector:
        while state["lifecycle"]["trial_status"] != "terminal":
            if selector is not None:
                selector.energy = float(state["organism"]["energy"])
                selector.life_index = int(state["lifecycle"]["life_index"])
            command = engine.make_command(
                sequence=int(state["clock"]["global_tick"]) + 1,
                trigger_source="headless_acceptance",
                interventions=interventions,
                prev_command_hash=state["last_command_hash"],
            )
            step = engine.compute_step(state, command, run_meta)
            state = step.next_state
            trace = step.trace
            command_hashes.append(str(command["command_hash"]))
            trace_hashes.append(str(trace["trace_hash"]))
            learning_trace = trace.get("survival_learning") or {}
            if trace.get("transition_kind") == "action":
                state_key_payloads.append(deepcopy(learning_trace["state_key_inputs"]))
                selection = learning_trace.get("selection") or {}
                selection_modes[str(selection.get("selection_mode"))] += 1
                life_index = int(trace["lifecycle_before"]["life_index"])
                if learning_trace.get("successful_resource_interaction") is True:
                    resource_by_life[life_index - 1] += 1
                if selector is not None:
                    selector.observe(trace)
            if len(command_hashes) > engine.MAX_LIVES * (engine.EPISODE_SPAN_TICKS + 1):
                raise RuntimeError("simulation exceeded the fixed lifecycle command bound")

    life_results = deepcopy(state["lifecycle"]["life_results"])
    survival = [int(item["survival_ticks"]) for item in life_results]
    if len(survival) != engine.MAX_LIVES:
        raise RuntimeError("simulation did not consume all sixteen lives")
    early_ticks = sum(survival[:4]) / 4.0
    late_ticks = sum(survival[12:16]) / 4.0
    source_records = _source_records()
    return {
        "schema_version": "ego.v2.survival_acceptance.run.v1",
        "producer_function": "verify_ego_v2_survival_learning_001a.simulate_context",
        "input_artifacts": source_records,
        "run_id": run_id,
        "context_id": context_id,
        "control_id": control_id,
        "layout_id": layout_id,
        "world_seed": world_seed,
        "policy_seed": policy_seed,
        "episode_ids": [engine.episode_id_for(run_id, index) for index in range(engine.MAX_LIVES)],
        "aggregation_rule": "early=mean(lives1..4)/256;late=mean(lives13..16)/256",
        "code_path_hash": evidence_code_path_hash(),
        "product_code_path_hash": run_meta["code_path_hash"],
        "life_results": life_results,
        "survival_ticks": survival,
        "early": early_ticks / engine.EPISODE_SPAN_TICKS,
        "late": late_ticks / engine.EPISODE_SPAN_TICKS,
        "late_minus_early": (late_ticks - early_ticks) / engine.EPISODE_SPAN_TICKS,
        "early_resource_interactions": sum(resource_by_life[:4]),
        "late_resource_interactions": sum(resource_by_life[12:16]),
        "resource_interactions_by_life": resource_by_life,
        "command_count": len(command_hashes),
        "first_command_hash": command_hashes[0],
        "last_command_hash": command_hashes[-1],
        "final_trace_hash": trace_hashes[-1],
        "trace_chain_hash": canonical_hash(trace_hashes),
        "final_state_hash": engine.state_hash(state),
        "final_learner_hash": survival_learning.learner_state_hash(
            state["survival_learner"]
        ),
        "q_table_size": survival_learning.q_table_size(state["survival_learner"]),
        "update_count": int(state["survival_learner"]["update_count"]),
        "selection_modes": dict(sorted(selection_modes.items())),
        "state_key_input_keys": sorted(
            {key for payload in state_key_payloads for key in payload}
        ),
        "state_key_input_hash": canonical_hash(state_key_payloads),
    }


def _run_worker(spec_path: Path, output_path: Path) -> int:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    result = simulate_context(spec)
    output_path.write_text(canonical_json(result) + "\n", encoding="utf-8", newline="\n")
    return 0


def _run_workers(
    specs: list[dict[str, Any]], *, temp_root: Path, batch_id: str, max_workers: int = 6
) -> list[dict[str, Any]]:
    batch = temp_root / batch_id
    batch.mkdir(parents=True, exist_ok=True)
    pending: list[tuple[dict[str, Any], Path, Path]] = []
    for index, spec in enumerate(specs):
        spec_path = batch / f"{index:03d}.input.json"
        output_path = batch / f"{index:03d}.output.json"
        spec_path.write_text(canonical_json(spec) + "\n", encoding="utf-8", newline="\n")
        pending.append((spec, spec_path, output_path))

    active: list[tuple[subprocess.Popen[str], dict[str, Any], Path]] = []
    completed: list[dict[str, Any]] = []
    while pending or active:
        while pending and len(active) < max_workers:
            spec, spec_path, output_path = pending.pop(0)
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker-input",
                    str(spec_path),
                    "--worker-output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            active.append((process, spec, output_path))
        progressed = False
        for item in list(active):
            process, spec, output_path = item
            if process.poll() is None:
                continue
            stdout, stderr = process.communicate()
            active.remove(item)
            progressed = True
            if process.returncode != 0:
                raise RuntimeError(
                    f"worker failed for {spec['control_id']} {spec['context_id']}: "
                    f"{stderr or stdout}"
                )
            completed.append(json.loads(output_path.read_text(encoding="utf-8")))
        if not progressed:
            time.sleep(0.05)
    return sorted(completed, key=lambda item: (item["control_id"], item["context_id"]))


def scan_state_key_inputs(payloads: list[Mapping[str, Any]]) -> dict[str, Any]:
    offenders: list[dict[str, Any]] = []
    for index, payload in enumerate(payloads):
        try:
            survival_learning.validate_state_key_payload(payload)
        except survival_learning.SurvivalLearningInvariantError as exc:
            offenders.append({"index": index, "error": str(exc), "keys": sorted(payload)})
    return {
        "producer_function": "verify_ego_v2_survival_learning_001a.scan_state_key_inputs",
        "scan_count": len(payloads),
        "offenders": offenders,
    }


def _source_path_report() -> dict[str, Any]:
    targets = {
        "engine": REPO_ROOT / "labs/ego_life_playground_v0/engine.py",
        "controller": REPO_ROOT / "labs/ego_life_playground_v0/controller.py",
        "store": REPO_ROOT / "labs/ego_life_playground_v0/store.py",
        "terminal": REPO_ROOT / "labs/ego_life_playground_v0/terminal.py",
        "visual_console": REPO_ROOT / "labs/ego_life_playground_v0/visual_console.py",
    }
    call_counts: dict[str, dict[str, int]] = {}
    function_counts: dict[str, dict[str, int]] = {}
    for name, path in targets.items():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls: dict[str, int] = defaultdict(int)
        functions: dict[str, int] = defaultdict(int)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions[node.name] += 1
            if isinstance(node, ast.Call):
                target = node.func.id if isinstance(node.func, ast.Name) else (
                    node.func.attr if isinstance(node.func, ast.Attribute) else ""
                )
                if target:
                    calls[target] += 1
        call_counts[name] = dict(calls)
        function_counts[name] = dict(functions)
    clean = (
        function_counts["engine"].get("compute_step") == 1
        and call_counts["controller"].get("compute_step") == 1
        and call_counts["store"].get("compute_step") == 1
        and call_counts["terminal"].get("compute_step", 0) == 0
        and call_counts["visual_console"].get("compute_step", 0) == 0
        and call_counts["terminal"].get("dispatch", 0) >= 1
        and call_counts["visual_console"].get("dispatch", 0) >= 1
        and call_counts["engine"].get("select_action") == 1
    )
    return {
        "producer_function": "verify_ego_v2_survival_learning_001a._source_path_report",
        "value": clean,
        "call_counts": call_counts,
        "function_counts": function_counts,
        "aggregation_rule": "one reducer and learner selection call; UI paths dispatch only",
        "code_path_hash": evidence_code_path_hash(),
    }


def _resource_boundary_report() -> dict[str, Any]:
    run_id = f"{TASK_ID}:resource-boundary"
    meta = engine.make_run_metadata(run_id, 701)
    state = engine.initial_state(run_id=run_id, seed=30, layout_id="p0_cross_v1")
    world = deepcopy(state["world"])
    world["agent"]["position"] = [4, 2]
    world["agent"]["facing"] = "N"
    placements = {
        "resource": [4, 1],
        "social": [1, 1],
        "novelty": [7, 1],
        "threat": [2, 3],
        "shelter": [6, 3],
    }
    for cause, position in placements.items():
        world["objects_by_cause"][cause]["position"] = position
    verify_world_state(world)
    command_hash = "a" * 64
    world_after, transition = transition_world(
        world,
        "interact",
        source_sequence=1,
        source_episode_id=state["clock"]["episode_id"],
        source_command_hash=command_hash,
    )
    legal = engine.compute_metabolism_ledger(
        energy_before=0.10,
        selected_action="interact",
        world_before=world,
        world_after=world_after,
        world_transition=transition,
        run_meta=meta,
        episode_id=state["clock"]["episode_id"],
        command_hash=command_hash,
        code_path_hash=meta["code_path_hash"],
    )
    forged = deepcopy(transition)
    forged["outcome_type"] = "no_object"
    forged["cause"] = "resource"
    forged_rejected = False
    forged_error = None
    try:
        engine.compute_metabolism_ledger(
            energy_before=0.10,
            selected_action="interact",
            world_before=world,
            world_after=world_after,
            world_transition=forged,
            run_meta=meta,
            episode_id=state["clock"]["episode_id"],
            command_hash=command_hash,
            code_path_hash=meta["code_path_hash"],
        )
    except engine.EngineInvariantError as exc:
        forged_rejected = True
        forged_error = type(exc).__name__
    return {
        "producer_function": "verify_ego_v2_survival_learning_001a._resource_boundary_report",
        "value": legal["food_gain"] > 0.0 and forged_rejected,
        "legal_resource_food_gain": legal["food_gain"],
        "forged_no_object_resource_rejected": forged_rejected,
        "exception_type": forged_error,
        "command_hash": command_hash,
        "run_id": run_id,
        "code_path_hash": evidence_code_path_hash(),
    }


def _sqlite_report(temp_root: Path) -> dict[str, Any]:
    db_path = temp_root / "mainline.sqlite3"
    run_id = f"{TASK_ID}:sqlite-mainline"
    td_tamper_rejected = False
    q_tamper_rejected = False
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(store, run_id=run_id, seed=701, world_seed=30)
        dispatch = controller.dispatch(
            interventions=dict(
                engine.DEFAULT_INTERVENTIONS,
                survival_learning_mode=survival_learning.ALGORITHM,
            ),
            trigger_source="ui_run_button",
        )
        recovered = store.recover_run(run_id)
        trace = deepcopy(recovered.traces[-1])
        command_hash = str(trace["command_hash"])
        trace["survival_learning"]["update"]["td_error"] = round(
            float(trace["survival_learning"]["update"]["td_error"]) + 0.25, 12
        )
        trace["trace_hash"] = engine.compute_trace_hash(trace)
        store.connection.execute(
            "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = ?",
            (engine.canonical_json(trace), trace["trace_hash"], run_id, trace["sequence"]),
        )
        try:
            store.recover_run(run_id)
        except RecoveryError:
            td_tamper_rejected = True

    q_db = temp_root / "q-mainline.sqlite3"
    q_run = f"{TASK_ID}:sqlite-q-tamper"
    with SQLiteEventStore(q_db) as store:
        PlaygroundController(store, run_id=q_run, seed=701, world_seed=30)
        row = store.connection.execute(
            "SELECT initial_state_json FROM runs WHERE run_id = ?", (q_run,)
        ).fetchone()
        initial = json.loads(str(row["initial_state_json"]))
        initial["survival_learner"]["q_values"] = {"f" * 64: {"rest": 9.0}}
        store.connection.execute(
            "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
            (engine.canonical_json(initial), engine.canonical_hash(initial), q_run),
        )
        try:
            store.recover_run(q_run)
        except RecoveryError:
            q_tamper_rejected = True
    return {
        "producer_function": "verify_ego_v2_survival_learning_001a._sqlite_report",
        "value": bool(dispatch.receipt.committed)
        and recovered.state["survival_learner"]["update_count"] == 1
        and td_tamper_rejected
        and q_tamper_rejected,
        "run_id": run_id,
        "seed": 701,
        "trigger_source": "ui_run_button",
        "command_hash": command_hash,
        "trace_hash": recovered.traces[-1]["trace_hash"],
        "learner_hash": survival_learning.learner_state_hash(
            recovered.state["survival_learner"]
        ),
        "td_trace_tamper_rejected": td_tamper_rejected,
        "initial_q_tamper_rejected": q_tamper_rejected,
        "exception_type": "RecoveryError",
        "code_path_hash": evidence_code_path_hash(),
    }


def _aggregate_by_control(runs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_control: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        by_control[str(run["control_id"])].append(run)
    result: dict[str, dict[str, Any]] = {}
    for control_id in CONTROL_IDS:
        values = sorted(by_control[control_id], key=lambda item: item["context_id"])
        result[control_id] = {
            "producer_function": "verify_ego_v2_survival_learning_001a._aggregate_by_control",
            "input_artifacts": [item["run_id"] for item in values],
            "run_ids": [item["run_id"] for item in values],
            "context_ids": [item["context_id"] for item in values],
            "aggregation_rule": "unweighted mean across all twelve predeclared contexts",
            "code_path_hash": evidence_code_path_hash(),
            "early": sum(float(item["early"]) for item in values) / len(values),
            "late": sum(float(item["late"]) for item in values) / len(values),
            "late_minus_early": sum(float(item["late_minus_early"]) for item in values)
            / len(values),
            "positive_contexts": sum(float(item["late_minus_early"]) > 0.0 for item in values),
            "early_resource_interactions": sum(
                int(item["early_resource_interactions"]) for item in values
            ),
            "late_resource_interactions": sum(
                int(item["late_resource_interactions"]) for item in values
            ),
        }
    return result


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8", newline="\n")


def run_product_acceptance(output_dir: str | Path, *, max_workers: int = 6) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for child in output.iterdir():
        if child.is_file():
            child.unlink()
    contexts = declared_contexts()
    specs = [{**context, "control_id": control_id} for control_id in CONTROL_IDS for context in contexts]
    with tempfile.TemporaryDirectory(prefix="ego-v2-survival-acceptance-") as temp_name:
        temp_root = Path(temp_name)
        runs = _run_workers(specs, temp_root=temp_root, batch_id="main", max_workers=max_workers)
        replay_specs = [
            {**context, "control_id": "expected_sarsa_lambda"} for context in contexts
        ]
        replay_runs = _run_workers(
            replay_specs,
            temp_root=temp_root,
            batch_id="replay",
            max_workers=max_workers,
        )
        sqlite_report = _sqlite_report(temp_root)

    aggregates = _aggregate_by_control(runs)
    candidate = aggregates["expected_sarsa_lambda"]
    off = aggregates["learner_off"]
    no_update = aggregates["no_update"]
    shield = aggregates["shield_only"]
    lookup = aggregates["empirical_lookup"]
    replay_by_context = {item["context_id"]: item for item in replay_runs}
    main_candidate = {
        item["context_id"]: item
        for item in runs
        if item["control_id"] == "expected_sarsa_lambda"
    }
    replay_matches = {
        context_id: canonical_hash(main_candidate[context_id])
        == canonical_hash(replay_by_context[context_id])
        for context_id in sorted(main_candidate)
    }
    expected_context_ids = {item["context_id"] for item in contexts}
    consumed = {
        control_id: {
            item["context_id"] for item in runs if item["control_id"] == control_id
        }
        for control_id in CONTROL_IDS
    }
    no_unused_context = all(value == expected_context_ids for value in consumed.values())

    gates = {
        "aggregate_late_minus_early_gt_0_05": candidate["late_minus_early"] > 0.05,
        "positive_direction_at_least_9_of_12": candidate["positive_contexts"] >= 9,
        "late_beats_off_and_no_update": (
            candidate["late"] - off["late"] > 0.05
            and candidate["late"] - no_update["late"] > 0.05
        ),
        "no_update_reduces_advantage": (
            candidate["late_minus_early"] - no_update["late_minus_early"] >= 0.05
        ),
        "late_ticks_gt_38": candidate["late"] * engine.EPISODE_SPAN_TICKS > 38.0,
        "late_resource_interactions_gt_early": (
            candidate["late_resource_interactions"]
            > candidate["early_resource_interactions"]
        ),
        "lookup_outside_equivalence_band": (
            abs(candidate["late"] - lookup["late"]) > EQUIVALENCE_BAND
        ),
        "fresh_process_replay_and_all_contexts_consumed": (
            all(replay_matches.values()) and no_unused_context
        ),
    }
    source_path = _source_path_report()
    resource_boundary = _resource_boundary_report()
    engineering_gates = {
        "default_mode_off": engine.DEFAULT_INTERVENTIONS["survival_learning_mode"] == "off",
        "max_lives_16": engine.MAX_LIVES == 16,
        "single_path_source_scan": source_path["value"] is True,
        "sqlite_live_recompute_and_tamper_rejection": sqlite_report["value"] is True,
        "resource_fail_closed_boundary": resource_boundary["value"] is True,
    }

    payloads = [
        {"policy_observation_hash": "a" * 64, "energy_milli": 450},
        {"policy_observation_hash": "b" * 64, "energy_milli": 0},
    ]
    clean_scan = scan_state_key_inputs(payloads)
    positive_scan = scan_state_key_inputs([{**payloads[0], "position": [4, 2]}])
    leakage = {
        "schema_version": "ego.v2.survival_acceptance.leakage.v1",
        "producer_function": "verify_ego_v2_survival_learning_001a.scan_state_key_inputs",
        "input_artifacts": _source_records(),
        "run_id": TASK_ID,
        "seed_context_episode_ids": {"positive_control_id": "hidden_position"},
        "aggregation_rule": "runtime exact-key scanner must accept clean inputs and reject hidden-position positive control",
        "code_path_hash": evidence_code_path_hash(),
        "clean_scan": clean_scan,
        "positive_control_scan": positive_scan,
        "value": clean_scan["offenders"] == [] and len(positive_scan["offenders"]) == 1,
    }
    engineering_gates["state_key_leakage_scan_positive_control"] = leakage["value"]

    shield_match = abs(candidate["late"] - shield["late"]) <= EQUIVALENCE_BAND
    adaptation_observed = gates["aggregate_late_minus_early_gt_0_05"] and gates[
        "positive_direction_at_least_9_of_12"
    ]
    all_product_gates = all(gates.values())
    all_engineering_gates = all(engineering_gates.values())
    if all_engineering_gates and all_product_gates and not shield_match:
        verdict = "PRODUCT_SURVIVAL_LEARNING_ACCEPTED"
        default_enablement = "promotion_required_then_full_rerun"
    elif all_engineering_gates and adaptation_observed and shield_match:
        verdict = "ADAPTATION_OBSERVED_NO_PRODUCT_HEADROOM"
        default_enablement = "off"
    else:
        verdict = "PRODUCT_SURVIVAL_LEARNING_NOT_OBSERVED"
        default_enablement = "off"

    baseline = {
        "schema_version": "ego.v2.survival_acceptance.baseline.v1",
        "producer_function": "verify_ego_v2_survival_learning_001a._aggregate_by_control",
        "input_artifacts": _source_records(),
        "run_id": TASK_ID,
        "seed_context_episode_ids": {"context_ids": sorted(expected_context_ids)},
        "aggregation_rule": "compare candidate late survival to six independent callable controls",
        "code_path_hash": evidence_code_path_hash(),
        "controls": aggregates,
        "shield_within_equivalence_band": shield_match,
        "lookup_within_equivalence_band": abs(candidate["late"] - lookup["late"])
        <= EQUIVALENCE_BAND,
    }
    ablation = {
        "schema_version": "ego.v2.survival_acceptance.ablation.v1",
        "producer_function": "verify_ego_v2_survival_learning_001a._aggregate_by_control",
        "input_artifacts": _source_records(),
        "run_id": TASK_ID,
        "seed_context_episode_ids": {"context_ids": sorted(expected_context_ids)},
        "aggregation_rule": "candidate late-minus-early minus no-update late-minus-early",
        "code_path_hash": evidence_code_path_hash(),
        "candidate": candidate,
        "no_update": no_update,
        "advantage_drop": candidate["late_minus_early"] - no_update["late_minus_early"],
        "value": gates["no_update_reduces_advantage"],
    }
    replay = {
        "schema_version": "ego.v2.survival_acceptance.replay.v1",
        "producer_function": "verify_ego_v2_survival_learning_001a._run_workers",
        "input_artifacts": _source_records(),
        "run_id": TASK_ID,
        "seed_context_episode_ids": {"context_ids": sorted(expected_context_ids)},
        "aggregation_rule": "each candidate context must match a separately spawned fresh worker byte-for-byte",
        "code_path_hash": evidence_code_path_hash(),
        "context_matches": replay_matches,
        "all_contexts_consumed": no_unused_context,
        "value": all(replay_matches.values()) and no_unused_context,
        "sqlite": sqlite_report,
    }
    failures = [key for key, value in {**engineering_gates, **gates}.items() if not value]
    failure_manifest = {
        "schema_version": "ego.v2.survival_acceptance.failure.v1",
        "producer_function": "verify_ego_v2_survival_learning_001a.run_product_acceptance",
        "input_artifacts": _source_records(),
        "run_id": TASK_ID,
        "seed_context_episode_ids": {"context_ids": sorted(expected_context_ids)},
        "aggregation_rule": "preserve every failed predeclared engineering/product gate without tuning",
        "code_path_hash": evidence_code_path_hash(),
        "failed_gates": failures,
        "status": "clean" if not failures else "negative_boundary",
    }
    result = {
        "schema_version": "ego.v2.survival_acceptance.result.v1",
        "task_id": TASK_ID,
        "producer_function": "verify_ego_v2_survival_learning_001a.run_product_acceptance",
        "input_artifacts": _source_records(),
        "run_id": TASK_ID,
        "seed_context_episode_ids": {"context_ids": sorted(expected_context_ids)},
        "aggregation_rule": "default enablement requires all eight predeclared product gates and all engineering gates",
        "code_path_hash": evidence_code_path_hash(),
        "product_code_path_hash": engine.compute_code_path_hash(),
        "layer": "Layer 4 product learning/adaptation; science_weight=0",
        "mainline_integration_status": "PlaygroundController.dispatch -> compute_step -> transition_world -> metabolism -> SQLite recovery",
        "enabled_status": "product enabled=true; product default_enabled=false; learner default=off",
        "real_trigger_evidence": sqlite_report,
        "context_count": len(contexts),
        "run_count": len(runs),
        "aggregates": aggregates,
        "product_gates": gates,
        "engineering_gates": engineering_gates,
        "source_path_report": source_path,
        "resource_boundary_report": resource_boundary,
        "verdict": verdict,
        "default_enablement": default_enablement,
        "claim_ceiling": CLAIM_CEILING,
    }

    _write_json(output / "result.json", result)
    _write_json(output / "baseline_comparison.json", baseline)
    _write_json(output / "ablation_report.json", ablation)
    _write_json(output / "leakage_report.json", leakage)
    _write_json(output / "replay_report.json", replay)
    _write_json(output / "failure_manifest.json", failure_manifest)
    with (output / "trace.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for run in runs:
            handle.write(canonical_json(run) + "\n")
    (output / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
    )
    actual = {path.name for path in output.iterdir()}
    if actual != REQUIRED_ARTIFACTS:
        raise RuntimeError(f"artifact set mismatch: {sorted(actual)}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-workers", type=int, default=max(1, min(6, os.cpu_count() or 1)))
    parser.add_argument("--worker-input", type=Path)
    parser.add_argument("--worker-output", type=Path)
    args = parser.parse_args(argv)
    if args.worker_input is not None or args.worker_output is not None:
        if args.worker_input is None or args.worker_output is None:
            raise SystemExit("both worker paths are required")
        return _run_worker(args.worker_input, args.worker_output)
    if args.output_dir is None:
        raise SystemExit("--output-dir is required")
    result = run_product_acceptance(args.output_dir, max_workers=args.max_workers)
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
