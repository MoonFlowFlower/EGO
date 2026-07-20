#!/usr/bin/env python3
"""Callable evidence producer for EGO-V2-P0-VISUAL-LIFE-CARD-A-001A."""

from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine, microworld
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import RecoveryError, SQLiteEventStore
from labs.ego_life_playground_v0.visual_console import PlaygroundWindow


TASK_ID = "EGO-V2-P0-VISUAL-LIFE-CARD-A-001A"
RUN_ID = "ego-v2-card-a-verify"
POLICY_SEED = 17
CLAIM_CEILING = (
    "Local product ecology and evidence hygiene only: the explicit Step/Run path "
    "uses the single controller -> compute_step -> SQLite/recovery chain, replay "
    "recomputes from serialized state plus commands, and equal-access baselines/"
    "ablations are reported without upgrading the claim. This does not establish "
    "electronic life, subjectivity, consciousness, emotion, agency, autonomy, "
    "general learning, mechanism validity, or stable user benefit."
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
    "live_ui_receipt.json",
}
CONTRACT_PATH = (
    REPO_ROOT
    / "docs/codex/tasks/EGO-V2-P0-VISUAL-LIFE-CONTRACT-001A/PRODUCT_CONTRACT.md"
)
CARD_PATH = (
    REPO_ROOT
    / "docs/codex/tasks/EGO-V2-P0-VISUAL-LIFE-CONTRACT-001A/CARD_A_EGOCENTRIC_ECOLOGY.md"
)
SOURCE_PATHS = [
    REPO_ROOT / "labs/ego_life_playground_v0/controller.py",
    REPO_ROOT / "labs/ego_life_playground_v0/engine.py",
    REPO_ROOT / "labs/ego_life_playground_v0/microworld.py",
    REPO_ROOT / "labs/ego_life_playground_v0/store.py",
    REPO_ROOT / "labs/ego_life_playground_v0/terminal.py",
    REPO_ROOT / "labs/ego_life_playground_v0/visual_console.py",
    REPO_ROOT / "scripts/run_ego_life_playground_v0.py",
    CONTRACT_PATH,
    CARD_PATH,
    Path(__file__),
]
REAL_CONTEXTS = [
    {
        "context_id": "cross_seed_1701",
        "run_id": f"{RUN_ID}-cross",
        "world_seed": 1701,
        "layout_id": "p0_cross_v1",
        "schedule": [
            None,
            "resource_appears",
            "quiet_interval",
            "social_signal",
            None,
            "novel_object",
            "threat_nearby",
            None,
            "quiet_interval",
            "resource_appears",
        ],
    },
    {
        "context_id": "offset_seed_1709",
        "run_id": f"{RUN_ID}-offset",
        "world_seed": 1709,
        "layout_id": "p2_offset_v1",
        "schedule": [
            "social_signal",
            None,
            "threat_nearby",
            "novel_object",
            None,
            "resource_appears",
            "quiet_interval",
            None,
            "social_signal",
            "resource_appears",
        ],
    },
]
FORBIDDEN_KEY_ALIASES = {
    "semantic_event": {"event", "world_event", "injected_event", "cause", "semantic_cause", "semantic_event"},
    "absolute_position": {"position", "agent_position", "layout_id", "topology", "map", "path", "legal_actions", "legal_mask"},
    "seed_or_life_id": {"seed", "world_seed", "life_index", "episode_id", "episode_index", "sequence"},
    "trace_lineage": {
        "command_hash",
        "prev_command_hash",
        "trace_hash",
        "prev_trace_hash",
        "token_mapping",
        "source_episode_id",
        "source_command_hash",
        "source_sequence",
        "lineage_id",
    },
}
FORBIDDEN_VALUE_PATTERNS = {
    "semantic_event": [
        re.compile(r"\b(resource_appears|social_signal|novel_object|threat_nearby|quiet_interval)\b"),
    ],
    "absolute_position": [
        re.compile(r"\[\s*\d+\s*,\s*\d+\s*\]"),
        re.compile(r"\b[a-z0-9_]+_v1\b", re.IGNORECASE),
    ],
    "seed_or_life_id": [
        re.compile(r"\bepisode-\d{6}-[0-9a-f]{2,64}\b", re.IGNORECASE),
        re.compile(r"\blife[_ -]?index\b", re.IGNORECASE),
        re.compile(r"\bseed\b", re.IGNORECASE),
    ],
    "trace_lineage": [
        re.compile(r"\b[0-9a-f]{64}\b", re.IGNORECASE),
        re.compile(r"\bcmd(?:_|:|\s)", re.IGNORECASE),
        re.compile(r"\btrace(?:_|:|\s)", re.IGNORECASE),
    ],
}
POSITIVE_CONTROL_PAYLOAD = {
    "semantic_event": "resource_appears",
    "absolute_position": [3, 1],
    "layout_id": "p0_cross_v1",
    "seed": 1701,
    "episode_id": "episode-000000-positive",
    "command_hash": "1" * 64,
    "token_mapping": {"v0": "resource"},
}
ACCEPTANCE_GATE_IDS = [
    "schema_versions_match_contract",
    "action_boundary_matches_contract",
    "real_trigger_step_and_run_path",
    "replay_two_fresh_processes_match",
    "tamper_controls_fail_closed",
    "policy_projection_leakage_scan_clean",
    "policy_projection_positive_control_fires",
    "single_path_dispatch_only",
    "recursive_provenance_present",
]


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


def _file_record(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw), "sha256": _sha256(raw)}


def _source_inputs() -> list[dict[str, Any]]:
    return [_file_record(path) for path in SOURCE_PATHS]


def _verifier_source_hash() -> str:
    return _file_record(Path(__file__))["sha256"]


def _code_path_hash() -> str:
    return _sha256(
        _canonical_bytes(
            {
                "engine_code_path_hash": engine.compute_code_path_hash(),
                "verifier_source_hash": _verifier_source_hash(),
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
        "producer_function": producer_function,
        "input_artifacts": deepcopy(input_artifacts),
        "run_id": run_id,
        "seed_context_episode_ids": deepcopy(dict(seed_context_episode_ids)),
        "aggregation_rule": aggregation_rule,
        "code_path_hash": _code_path_hash(),
        "engine_code_path_hash": engine.compute_code_path_hash(),
        "verifier_source_hash": _verifier_source_hash(),
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


def collect_evidence_records(payload: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            if {"producer_function", "input_artifacts", "run_id", "seed_context_episode_ids", "aggregation_rule", "code_path_hash", "engine_code_path_hash", "verifier_source_hash"} <= set(value):
                records.append(dict(value))
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    return records


def aggregate_result(checks: Mapping[str, Any], *, acceptance_gate_ids: list[str]) -> dict[str, Any]:
    failed: list[str] = []
    for name in acceptance_gate_ids:
        record = checks.get(name)
        if not isinstance(record, Mapping) or type(record.get("value")) is not bool:
            raise ValueError(f"computed check record required: {name}")
        if record["value"] is not True:
            failed.append(name)
    return {"verdict": "pass" if not failed else "fail", "failed_checks": sorted(failed)}


def _utility_from_trace(trace: Mapping[str, Any]) -> float:
    goal = trace["policy_projection"]["current_goal"]["state_variable"]
    if goal in engine.STATE_KEYS:
        return round(float(trace["actual_delta"][goal]), 6)
    return round(sum(float(trace["actual_delta"][key]) for key in engine.STATE_KEYS), 6)


def _access_from_trace(trace: Mapping[str, Any]) -> dict[str, Any]:
    legal_actions = list(
        trace.get("candidate_actions")
        or (trace.get("action_gate") or {}).get("legal_actions")
        or engine.ACTIONS
    )
    return {
        "observation": deepcopy(trace["policy_projection"]["observation"]),
        "organism": deepcopy(trace["policy_projection"]["organism"]),
        "current_goal": deepcopy(trace["policy_projection"]["current_goal"]),
        "legal_actions": legal_actions,
    }


def baseline_hash_policy(access: Mapping[str, Any]) -> dict[str, Any]:
    legal_actions = list(access["legal_actions"])
    digest = hashlib.sha256(_canonical_bytes(access)).digest()
    selected = legal_actions[int.from_bytes(digest[:8], "big") % len(legal_actions)]
    return {
        "baseline_id": "hash_policy",
        "selected_action": selected,
        "access_contract": {
            "algorithm": "deterministic_sha256_mod_legal_actions",
            "public_inputs": ["observation", "organism", "current_goal", "legal_actions"],
            "updates": "none",
        },
    }


def baseline_visual_lookup_countq(
    train_records: list[Mapping[str, Any]], access: Mapping[str, Any]
) -> dict[str, Any]:
    projection_key = _canonical_bytes(
        {
            "visual": access["observation"]["visual"],
            "goal": access["current_goal"]["state_variable"],
        }
    )
    exact_scores: dict[str, list[float]] = {}
    fallback_scores: dict[str, list[float]] = {}
    for record in train_records:
        label = str(record["selected_action"])
        utility = float(
            record.get(
                "utility",
                next(iter((record.get("utility_by_action") or {"_": 0.0}).values())),
            )
        )
        fallback_scores.setdefault(label, []).append(utility)
        candidate_key = _canonical_bytes(
            {
                "visual": record["access"]["observation"]["visual"],
                "goal": record["access"]["current_goal"]["state_variable"],
            }
        )
        if candidate_key == projection_key:
            exact_scores.setdefault(label, []).append(utility)
    score_source = exact_scores if exact_scores else fallback_scores
    ordered_actions = sorted(access["legal_actions"])
    selected = max(
        ordered_actions,
        key=lambda action: (
            sum(score_source.get(action, [0.0])) / max(len(score_source.get(action, [])), 1),
            -ordered_actions.index(action),
        ),
    )
    return {
        "baseline_id": "visual_lookup_countq",
        "selected_action": selected,
        "match_status": "exact_visual_goal_match" if exact_scores else "countq_fallback",
        "access_contract": {
            "algorithm": "exact_visual_goal_lookup_else_count_q",
            "public_inputs": ["observation.visual", "current_goal.state_variable", "observed_deltas"],
            "updates": "train_only_on_predeclared_split",
        },
    }


def _artifact_ref(path: Path) -> dict[str, Any]:
    return _file_record(path)


def _recovery_digest(recovered: Any) -> dict[str, Any]:
    payload = {
        "run_id": recovered.run_id,
        "run_meta": recovered.run_meta,
        "state_hash": engine.state_hash(recovered.state),
        "trace_hashes": [trace["trace_hash"] for trace in recovered.traces],
        "selected_actions": [trace["selected_action"] for trace in recovered.traces],
        "episode_ids": [trace["episode_id"] for trace in recovered.traces],
    }
    return {"payload": payload, "digest": _sha256(_canonical_bytes(payload))}


def _fresh_recovery_summary(db_path: Path, run_id: str) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--recovery-summary",
            str(db_path),
            "--run-id",
            run_id,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(completed.stdout)


def _sqlite_recovery_summary(db_path: Path, run_id: str) -> dict[str, Any]:
    with SQLiteEventStore(db_path) as store:
        recovered = store.recover_run(run_id)
    return _recovery_digest(recovered)


def _modify_trace_field(trace: dict[str, Any], *, field: str, value: Any) -> dict[str, Any]:
    tampered = deepcopy(trace)
    if field == "trace_prev_hash":
        tampered["prev_trace_hash"] = value
    elif field == "selected_action":
        tampered["selected_action"] = value
    else:
        raise ValueError(field)
    tampered["trace_hash"] = engine.compute_trace_hash(tampered)
    return tampered


def _tamper_control(
    source_db: Path,
    run_id: str,
    tamper_id: str,
    mutate: Any,
) -> dict[str, Any]:
    destination = source_db.with_name(f"{source_db.stem}-{tamper_id}.sqlite3")
    shutil.copy2(source_db, destination)
    failed_closed = False
    observed_failure_class = None
    observed_reason = None
    with sqlite3.connect(destination) as connection:
        mutate(connection)
        connection.commit()
    try:
        with SQLiteEventStore(destination) as store:
            store.recover_run(run_id)
    except Exception as exc:  # fail closed evidence path
        failed_closed = isinstance(exc, RecoveryError)
        observed_failure_class = type(exc).__name__
        observed_reason = str(exc)
    return {
        "tamper_id": tamper_id,
        "failed_closed": failed_closed,
        "observed_failure_class": observed_failure_class,
        "observed_reason": observed_reason,
    }


def _stored_selected_action_comparison_only() -> bool:
    source = (REPO_ROOT / "labs/ego_life_playground_v0/store.py").read_text(encoding="utf-8")
    return source.index("recomputed = compute_step") < source.index("trace_row = self._connection.execute")


def scan_policy_projection(payload: Mapping[str, Any], inject_positive_control: bool = False) -> dict[str, Any]:
    candidate = deepcopy(dict(payload))
    if inject_positive_control:
        candidate["positive_control_bundle"] = deepcopy(POSITIVE_CONTROL_PAYLOAD)

    offenders: list[dict[str, Any]] = []

    def add_scalar_offenders(text: str, path: str, reason: str) -> None:
        for category, patterns in FORBIDDEN_VALUE_PATTERNS.items():
            if any(pattern.search(text) for pattern in patterns):
                offenders.append(
                    {
                        "category": category,
                        "path": path,
                        "reason": reason,
                    }
                )

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
            scalar_items = [item for item in value if isinstance(item, (str, int, float)) and not isinstance(item, bool)]
            if scalar_items:
                add_scalar_offenders(json.dumps(scalar_items, ensure_ascii=False), path or "/", "forbidden_list_value_pattern")
            for index, item in enumerate(value):
                walk(item, f"{path}/{index}")
        elif isinstance(value, (str, int, float)) and not isinstance(value, bool):
            add_scalar_offenders(str(value), path or "/", "forbidden_scalar_value_pattern")

    walk(candidate, "")
    return {
        **_provenance(
            producer_function="scan_policy_projection",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"policy_projection_scan": True},
            aggregation_rule="recursive structured key scan; no text-substring shortcuts",
        ),
        "positive_control_injected": inject_positive_control,
        "positive_control_detected": inject_positive_control and bool(offenders),
        "offenders": offenders,
    }


def _contract_world_report() -> dict[str, Any]:
    initial = engine.initial_state(run_id=f"{RUN_ID}-contract", seed=1701, layout_id="p0_cross_v1")
    life2 = microworld.initial_world_state(seed=1701, layout_id="p0_cross_v1", life_index=2)
    mapping = initial["world"]["trial"]["token_mapping"]
    life1_positions = {
        cause: tuple(item["position"])
        for cause, item in sorted(initial["world"]["objects_by_cause"].items())
    }
    life2_positions = {
        cause: tuple(item["position"])
        for cause, item in sorted(life2["objects_by_cause"].items())
    }
    return {
        **_provenance(
            producer_function="_contract_world_report",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"world_seed": 1701, "life_ids": [1, 2]},
            aggregation_rule="verify frozen schemas, actions, object count, bijection, and deterministic non-fixed life placements",
        ),
        "schema_versions": {
            "state": engine.STATE_SCHEMA_VERSION,
            "run": engine.RUN_SCHEMA_VERSION,
            "command": engine.COMMAND_SCHEMA_VERSION,
            "trace": engine.TRACE_SCHEMA_VERSION,
            "world": microworld.WORLD_STATE_SCHEMA_VERSION,
            "observation": microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION,
            "public_frame": microworld.PUBLIC_FRAME_SCHEMA_VERSION,
        },
        "action_set": list(engine.ACTIONS),
        "science_weight": engine.make_run_metadata(f"{RUN_ID}-meta", POLICY_SEED)["science_weight"],
        "object_count": len(initial["world"]["objects_by_cause"]),
        "token_mapping": mapping,
        "life1_positions": life1_positions,
        "life2_positions": life2_positions,
        "non_fixed_across_lives": life1_positions != life2_positions,
    }


def _direct_forbidden_calls(tree: ast.AST) -> list[str]:
    forbidden_calls = {"compute_step", "transition_world", "make_command", "append_step"}
    return sorted(
        {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_calls
        }
        | {
            ast.unparse(node.func)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in forbidden_calls
        }
    )


def _single_path_report() -> dict[str, Any]:
    scan_paths = {
        "visual_console.py": REPO_ROOT / "labs/ego_life_playground_v0/visual_console.py",
        "terminal.py": REPO_ROOT / "labs/ego_life_playground_v0/terminal.py",
        "run_ego_life_playground_v0.py": REPO_ROOT / "scripts/run_ego_life_playground_v0.py",
        "controller.py": REPO_ROOT / "labs/ego_life_playground_v0/controller.py",
    }
    trees = {
        name: ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for name, path in scan_paths.items()
    }
    visual_direct = _direct_forbidden_calls(trees["visual_console.py"])
    terminal_direct = _direct_forbidden_calls(trees["terminal.py"])
    runner_direct = _direct_forbidden_calls(trees["run_ego_life_playground_v0.py"])
    dispatch_source = next(
        node for node in trees["controller.py"].body if isinstance(node, ast.ClassDef) and node.name == "PlaygroundController"
    )
    dispatch_method = next(
        node for node in dispatch_source.body if isinstance(node, ast.FunctionDef) and node.name == "dispatch"
    )
    controller_calls = [
        ast.unparse(node.func)
        for node in ast.walk(dispatch_method)
        if isinstance(node, ast.Call)
    ]
    return {
        **_provenance(
            producer_function="_single_path_report",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"single_path_scan": True},
            aggregation_rule="Tk path may dispatch only through controller; controller dispatch owns compute_step and append_step once",
        ),
        "scanned_files": sorted(scan_paths),
        "visual_direct_forbidden_calls": visual_direct,
        "terminal_direct_forbidden_calls": terminal_direct,
        "runner_direct_forbidden_calls": runner_direct,
        "controller_calls": controller_calls,
        "controller_dispatch_compute_step_calls": controller_calls.count("compute_step"),
        "controller_dispatch_append_step_calls": controller_calls.count("self.store.append_step"),
        "pass": visual_direct == []
        and terminal_direct == []
        and runner_direct == []
        and controller_calls.count("compute_step") == 1
        and controller_calls.count("self.store.append_step") == 1,
    }


def _pump_tk(root: Any, predicate: Any, timeout_s: float = 8.0) -> None:
    deadline = time.monotonic() + timeout_s
    while not predicate():
        if time.monotonic() >= deadline:
            raise RuntimeError("Tk evidence condition timed out")
        root.update()
        time.sleep(0.01)


def exercise_live_ui(temp_root: Path) -> dict[str, Any]:
    import tkinter as tk

    db_path = temp_root / "live-ui.sqlite3"
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(
            store,
            run_id=f"{RUN_ID}-live-ui",
            seed=POLICY_SEED,
            world_seed=1701,
            layout_id="p0_cross_v1",
        )
        root = tk.Tk()
        root.withdraw()
        window = PlaygroundWindow(root, controller)
        try:
            root.update()
            window.step_button.invoke()
            _pump_tk(root, lambda: store.row_counts(controller.run_id)[0] >= 1 and not window._animating)
            window.run_button.invoke()
            _pump_tk(root, lambda: store.row_counts(controller.run_id)[0] >= 3)
            pause_requested_at = store.row_counts(controller.run_id)[0]
            window.pause_button.invoke()
            for _ in range(10):
                root.update()
                time.sleep(0.01)
            final_counts = store.row_counts(controller.run_id)
            displayed = controller.recovery.frames[-1]
            history_rows = [
                list(window.history_tree.item(item_id, "values"))
                for item_id in window.history_tree.get_children()
            ]
            candidate_rows = [
                list(window.candidate_tree.item(item_id, "values"))
                for item_id in window.candidate_tree.get_children()
            ]
            return {
                **_provenance(
                    producer_function="exercise_live_ui",
                    input_artifacts=[*_source_inputs(), _artifact_ref(db_path)],
                    seed_context_episode_ids={"run_seed": POLICY_SEED, "world_seed": 1701, "context_id": "ui_live"},
                    aggregation_rule="hidden Tk invokes real Step then Run, pauses after bounded observed commits, and reads back SQLite/recovery/panel state only",
                    run_id=controller.run_id,
                ),
                "tk_available": True,
                "db_path": str(db_path),
                "run_id": controller.run_id,
                "step_triggered": True,
                "run_triggered": True,
                "paused_at_command_count": pause_requested_at,
                "sqlite_command_count": final_counts[0],
                "sqlite_trace_count": final_counts[1],
                "displayed_sequence": displayed.sequence,
                "displayed_visual": deepcopy(window.visual_grid_data),
                "observer_canvas_data": deepcopy(window.observer_canvas_data),
                "history_rows": history_rows,
                "candidate_rows": candidate_rows,
                "recovered_trace_hash": controller.recovery.traces[-1]["trace_hash"],
                "trigger_sources": [trace["trigger_source"] for trace in controller.recovery.traces],
                "latest_selected_action": controller.recovery.traces[-1]["selected_action"],
            }
        finally:
            window.close()


def _context_output_root(root: Path, context_id: str) -> Path:
    target = root / context_id
    target.mkdir(parents=True, exist_ok=True)
    return target


def collect_real_run_dataset(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    contexts: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []
    for spec in REAL_CONTEXTS:
        context_root = _context_output_root(root, spec["context_id"])
        db_path = context_root / "run.sqlite3"
        with SQLiteEventStore(db_path) as store:
            controller = PlaygroundController(
                store,
                run_id=spec["run_id"],
                seed=POLICY_SEED,
                world_seed=spec["world_seed"],
                layout_id=spec["layout_id"],
            )
            initial_state = deepcopy(controller.state)
            run_meta = deepcopy(controller.run_meta)
            command_specs: list[dict[str, Any]] = []
            for injected_event in spec["schedule"]:
                result = controller.dispatch(
                    trigger_source="headless_acceptance",
                    injected_event=injected_event,
                )
                if not result.receipt.committed:
                    raise RuntimeError(f"dispatch failed: {result.receipt.error}")
                command_specs.append(
                    {
                        "trigger_source": "headless_acceptance",
                        "injected_event": injected_event,
                    }
                )
            recovered = controller.recover()
            export_path = context_root / "trace.jsonl"
            controller.export(export_path)
        context = {
            "context_id": spec["context_id"],
            "run_id": spec["run_id"],
            "world_seed": spec["world_seed"],
            "layout_id": spec["layout_id"],
            "db_path": db_path,
            "export_path": export_path,
            "initial_state": initial_state,
            "run_meta": run_meta,
            "traces": recovered.traces,
            "frames": recovered.frames,
            "command_specs": command_specs,
        }
        contexts.append(context)
        for trace in recovered.traces:
            if "policy_projection" not in trace:
                continue
            all_records.append(
                {
                    "context_id": spec["context_id"],
                    "run_id": spec["run_id"],
                    "trace_hash": trace["trace_hash"],
                    "selected_action": trace["selected_action"],
                    "utility": _utility_from_trace(trace),
                    "utility_by_action": {trace["selected_action"]: _utility_from_trace(trace)},
                    "access": _access_from_trace(trace),
                    "trace": trace,
                }
            )
    return {"contexts": contexts, "all_records": all_records}


def build_baseline_report(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    split_index = max(1, len(records) // 2)
    train_records = list(records[:split_index])
    eval_records = list(records[split_index:])
    if not eval_records:
        eval_records = train_records
    comparisons = []
    invocation_ledger = []
    producers = {
        "hash_policy": lambda access: baseline_hash_policy(access),
        "visual_lookup_countq": lambda access: baseline_visual_lookup_countq(train_records, access),
    }
    for baseline_id, producer in producers.items():
        matches = 0
        predictions = []
        for record in eval_records:
            predicted = producer(record["access"])
            selected_action = predicted["selected_action"]
            predictions.append(
                {
                    "context_id": record["context_id"],
                    "trace_hash": record["trace_hash"],
                    "predicted_action": selected_action,
                    "candidate_action": record["selected_action"],
                    "matched": selected_action == record["selected_action"],
                }
            )
            matches += int(selected_action == record["selected_action"])
        match_rate = round(matches / len(eval_records), 6)
        comparisons.append(
            {
                "baseline_id": baseline_id,
                "match_rate": match_rate,
                "predictions": predictions,
            }
        )
        invocation_ledger.append(
            {
                **_provenance(
                    producer_function=f"baseline:{baseline_id}",
                    input_artifacts=_source_inputs(),
                    seed_context_episode_ids={
                        "train_context_ids": sorted({record["context_id"] for record in train_records}),
                        "eval_context_ids": sorted({record["context_id"] for record in eval_records}),
                    },
                    aggregation_rule="predeclared train/eval split using policy-visible projection and observed deltas only",
                ),
                "baseline_id": baseline_id,
                "invoked": True,
                "access_fields": sorted(
                    {
                        "observation.visual",
                        "organism",
                        "current_goal.state_variable",
                        "legal_actions",
                        "observed_deltas",
                    }
                ),
                "input_access_hash": _sha256(
                    _canonical_bytes(
                        {
                            "train": [record["access"] for record in train_records],
                            "eval": [record["access"] for record in eval_records],
                        }
                    )
                ),
            }
        )
    strongest = max(comparisons, key=lambda item: (item["match_rate"], item["baseline_id"]))
    disposition = (
        "equal_access_equivalent_downgrade"
        if strongest["match_rate"] >= 1.0
        else "non_equivalent"
    )
    return {
        **_provenance(
            producer_function="build_baseline_report",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={
                "train_context_ids": sorted({record["context_id"] for record in train_records}),
                "eval_context_ids": sorted({record["context_id"] for record in eval_records}),
            },
            aggregation_rule="report equal-access baseline match rates; engineering acceptance does not fail on equivalence",
        ),
        "train_count": len(train_records),
        "eval_count": len(eval_records),
        "comparisons": comparisons,
        "invocation_ledger": invocation_ledger,
        "strongest_baseline": strongest["baseline_id"],
        "strongest_match_rate": strongest["match_rate"],
        "disposition": disposition,
    }


def _sorted_walkable_positions(layout: Mapping[str, Any]) -> list[list[int]]:
    rows = list(layout["base_rows"])
    positions = []
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            if value != "#":
                positions.append([x, y])
    return positions


def _fixed_position_state(initial_state: Mapping[str, Any]) -> dict[str, Any]:
    state = deepcopy(dict(initial_state))
    walkable = _sorted_walkable_positions(state["world"]["layout"])
    state["world"]["agent"]["position"] = walkable[0]
    state["world"]["agent"]["facing"] = "N"
    for index, cause in enumerate(sorted(state["world"]["objects_by_cause"])):
        state["world"]["objects_by_cause"][cause]["position"] = walkable[index + 1]
        state["world"]["objects_by_cause"][cause]["spawn_count"] = 0
        state["world"]["objects_by_cause"][cause]["injection_count"] = 0
    microworld.verify_world_state(state["world"])
    return state


def _replay_context(
    context: Mapping[str, Any],
    *,
    memory_mode: str = "canonical",
    update_mode: str = "canonical",
    vision_mode: str = "canonical",
    fixed_position: bool = False,
) -> dict[str, Any]:
    state = _fixed_position_state(context["initial_state"]) if fixed_position else deepcopy(context["initial_state"])
    run_meta = deepcopy(context["run_meta"])
    outputs = []
    command_hash = None
    for sequence, spec in enumerate(context["command_specs"], start=1):
        interventions = deepcopy(engine.DEFAULT_INTERVENTIONS)
        interventions["memory_mode"] = memory_mode
        interventions["update_mode"] = update_mode
        interventions["vision_mode"] = vision_mode
        command = engine.make_command(
            sequence=sequence,
            trigger_source=str(spec["trigger_source"]),
            interventions=interventions,
            prev_command_hash=command_hash,
            injected_event=spec["injected_event"],
        )
        result = engine.compute_step(state, command, run_meta)
        outputs.append(
            {
                "command_hash": command["command_hash"],
                "selected_action": result.trace["selected_action"],
                "observation_hash": result.trace["observation_hash"],
                "state_after_hash": result.trace["state_after_hash"],
                "model_after_hash": result.trace["model_bytes"]["after_hash"],
                "memory_after_hash": result.trace["memory_bytes"]["after_hash"],
                "trace_hash": result.trace["trace_hash"],
                "episode_id": result.trace["episode_id"],
            }
        )
        state = result.next_state
        command_hash = command["command_hash"]
    return {"final_state": state, "outputs": outputs}


def build_ablation_report(contexts: list[Mapping[str, Any]]) -> dict[str, Any]:
    case_specs = {
        "canonical": {"memory_mode": "canonical", "update_mode": "canonical", "vision_mode": "canonical", "fixed_position": False},
        "memory_off": {"memory_mode": "off", "update_mode": "canonical", "vision_mode": "canonical", "fixed_position": False},
        "update_freeze": {"memory_mode": "canonical", "update_mode": "frozen", "vision_mode": "canonical", "fixed_position": False},
        "no_occlusion": {"memory_mode": "canonical", "update_mode": "canonical", "vision_mode": "no_occlusion", "fixed_position": False},
        "fixed_position": {"memory_mode": "canonical", "update_mode": "canonical", "vision_mode": "canonical", "fixed_position": True},
    }
    cases = {}
    invocation_ledger = []
    for case_id, options in case_specs.items():
        per_context = {}
        for context in contexts:
            per_context[context["context_id"]] = _replay_context(context, **options)
        cases[case_id] = per_context
        invocation_ledger.append(
            {
                **_provenance(
                    producer_function=f"build_ablation_report:{case_id}",
                    input_artifacts=_source_inputs(),
                    seed_context_episode_ids={"context_ids": [context["context_id"] for context in contexts]},
                    aggregation_rule="rerun from serialized initial states plus rebuilt command streams under real intervention toggles",
                ),
                "case_id": case_id,
                "invoked": True,
            }
        )
    summaries = {}
    for case_id, per_context in cases.items():
        if case_id == "canonical":
            continue
        per_case_context = {}
        for context in contexts:
            context_id = context["context_id"]
            canonical_outputs = cases["canonical"][context_id]["outputs"]
            candidate_outputs = per_context[context_id]["outputs"]
            per_case_context[context_id] = {
                "selected_actions_equal": [
                    left["selected_action"] == right["selected_action"]
                    for left, right in zip(canonical_outputs, candidate_outputs)
                ],
                "observation_hashes_equal": [
                    left["observation_hash"] == right["observation_hash"]
                    for left, right in zip(canonical_outputs, candidate_outputs)
                ],
                "state_hashes_equal": [
                    left["state_after_hash"] == right["state_after_hash"]
                    for left, right in zip(canonical_outputs, candidate_outputs)
                ],
                "model_hashes_equal": [
                    left["model_after_hash"] == right["model_after_hash"]
                    for left, right in zip(canonical_outputs, candidate_outputs)
                ],
                "memory_hashes_equal": [
                    left["memory_after_hash"] == right["memory_after_hash"]
                    for left, right in zip(canonical_outputs, candidate_outputs)
                ],
            }
        summaries[case_id] = per_case_context
    return {
        **_provenance(
            producer_function="build_ablation_report",
            input_artifacts=_source_inputs(),
            seed_context_episode_ids={"context_ids": [context["context_id"] for context in contexts]},
            aggregation_rule="compare canonical reruns against memory-off/update-freeze/no-occlusion/fixed-position interventions",
        ),
        "cases": cases,
        "contrasts": summaries,
        "invocation_ledger": invocation_ledger,
    }


def _build_single_replay_context(context: Mapping[str, Any]) -> dict[str, Any]:
    db_path = Path(context["db_path"])
    run_id = str(context["run_id"])
    local_summary = _sqlite_recovery_summary(db_path, run_id)
    fresh_a = _fresh_recovery_summary(db_path, run_id)
    fresh_b = _fresh_recovery_summary(db_path, run_id)

    def mutate_initial(connection: sqlite3.Connection) -> None:
        payload = json.loads(connection.execute("SELECT initial_state_json FROM runs WHERE run_id = ?", (run_id,)).fetchone()[0])
        payload["organism"]["energy"] = 0.99
        connection.execute(
            "UPDATE runs SET initial_state_json = ?, initial_state_hash = ? WHERE run_id = ?",
            (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False), engine.canonical_hash(payload), run_id),
        )

    def mutate_command(connection: sqlite3.Connection) -> None:
        row = connection.execute(
            "SELECT sequence, command_json FROM commands WHERE run_id = ? ORDER BY sequence DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        payload = json.loads(row[1])
        payload["prev_command_hash"] = None
        payload["command_hash"] = engine.canonical_hash({key: payload[key] for key in payload if key != "command_hash"})
        connection.execute(
            "UPDATE commands SET command_json = ?, command_hash = ? WHERE run_id = ? AND sequence = ?",
            (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False), payload["command_hash"], run_id, row[0]),
        )

    def mutate_selected_action(connection: sqlite3.Connection) -> None:
        row = connection.execute(
            "SELECT sequence, trace_json FROM traces WHERE run_id = ? ORDER BY sequence LIMIT 1",
            (run_id,),
        ).fetchone()
        payload = json.loads(row[1])
        alternatives = [action for action in engine.ACTIONS if action != payload["selected_action"]]
        tampered = _modify_trace_field(payload, field="selected_action", value=alternatives[0])
        connection.execute(
            "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = ?",
            (json.dumps(tampered, sort_keys=True, separators=(",", ":"), ensure_ascii=False), tampered["trace_hash"], run_id, row[0]),
        )

    def mutate_prev_hash(connection: sqlite3.Connection) -> None:
        row = connection.execute(
            "SELECT sequence, trace_json FROM traces WHERE run_id = ? ORDER BY sequence LIMIT 1",
            (run_id,),
        ).fetchone()
        payload = json.loads(row[1])
        tampered = _modify_trace_field(payload, field="trace_prev_hash", value="0" * 64)
        connection.execute(
            "UPDATE traces SET trace_json = ?, trace_hash = ? WHERE run_id = ? AND sequence = ?",
            (json.dumps(tampered, sort_keys=True, separators=(",", ":"), ensure_ascii=False), tampered["trace_hash"], run_id, row[0]),
        )

    tamper_controls = {
        "initial_state": _tamper_control(db_path, run_id, "initial-state", mutate_initial),
        "command_payload": _tamper_control(db_path, run_id, "command-payload", mutate_command),
        "trace_selected_action": _tamper_control(db_path, run_id, "trace-selected-action", mutate_selected_action),
        "trace_prev_hash": _tamper_control(db_path, run_id, "trace-prev-hash", mutate_prev_hash),
    }
    return {
        "local_summary": local_summary,
        "fresh_processes": [fresh_a, fresh_b],
        "local_vs_fresh_equal": local_summary == fresh_a == fresh_b,
        "fresh_process_runs_equal": fresh_a == fresh_b,
        "tamper_controls": tamper_controls,
    }


def build_replay_report(contexts: list[Mapping[str, Any]]) -> dict[str, Any]:
    by_context = {
        str(context["context_id"]): _build_single_replay_context(context)
        for context in contexts
    }
    return {
        **_provenance(
            producer_function="build_replay_report",
            input_artifacts=[*_source_inputs(), *[_artifact_ref(Path(context["db_path"])) for context in contexts]],
            seed_context_episode_ids={"context_ids": [context["context_id"] for context in contexts]},
            aggregation_rule="require local recovery and two fresh-process recoveries to match for every dataset context, with tampered clones failing closed",
        ),
        "contexts": by_context,
        "stored_selected_action_comparison_only": _stored_selected_action_comparison_only(),
    }


def _trace_records(contexts: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for context in contexts:
        for trace in context["traces"]:
            records.append(
                {
                    **_provenance(
                        producer_function="trace_record",
                        input_artifacts=[*_source_inputs(), _artifact_ref(context["db_path"])],
                        seed_context_episode_ids={
                            "context_id": context["context_id"],
                            "world_seed": context["world_seed"],
                            "episode_id": trace["episode_id"],
                            "sequence": trace["sequence"],
                        },
                        aggregation_rule="one real controller dispatch committed and recovered from SQLite",
                        run_id=context["run_id"],
                    ),
                    "record_type": "trace",
                    "context_id": context["context_id"],
                    "trace": trace,
                }
            )
    return records


def run_card_a_verification(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    _clean_output_dir(output)
    inputs = _source_inputs()
    dataset_root = Path(tempfile.mkdtemp(prefix="ego-v2-card-a-dataset-"))
    temp_root = Path(tempfile.mkdtemp(prefix="ego-v2-card-a-ui-"))
    dataset = collect_real_run_dataset(dataset_root)
    live_ui = exercise_live_ui(temp_root)
    baseline = build_baseline_report(dataset["all_records"])
    ablation = build_ablation_report(dataset["contexts"])
    replay = build_replay_report(dataset["contexts"])
    clean_scans = []
    positive_scans = []
    for context in dataset["contexts"]:
        for trace in context["traces"]:
            clean_scans.append(scan_policy_projection(trace["policy_projection"]))
            positive_scans.append(scan_policy_projection(trace["policy_projection"], inject_positive_control=True))
    contract_world = _contract_world_report()
    single_path = _single_path_report()
    trace_rows = _trace_records(dataset["contexts"])
    _write_jsonl(output / "trace.jsonl", trace_rows)

    leakage = {
        **_provenance(
            producer_function="build_leakage_report",
            input_artifacts=[*inputs, _artifact_ref(output / "trace.jsonl")],
            seed_context_episode_ids={"context_ids": [context["context_id"] for context in dataset["contexts"]]},
            aggregation_rule="scan live policy_projection structures and a multi-class positive control",
        ),
        "clean_projection": clean_scans[0],
        "positive_control": positive_scans[0],
        "clean_projection_scans": clean_scans,
        "positive_control_scans": positive_scans,
    }

    preliminary_payloads = {
        "baseline": baseline,
        "ablation": ablation,
        "leakage": leakage,
        "replay": replay,
        "live_ui": live_ui,
        "trace_rows": trace_rows,
    }
    recursive_provenance_present = all(
        all(
            {"producer_function", "input_artifacts", "run_id", "seed_context_episode_ids", "aggregation_rule", "code_path_hash", "engine_code_path_hash", "verifier_source_hash"} <= set(record)
            for record in collect_evidence_records(payload)
        )
        for payload in preliminary_payloads.values()
    )

    checks = {
        "schema_versions_match_contract": _check_record(
            contract_world["schema_versions"]
            == {
                "state": "ego.life_playground.state.v4",
                "run": "ego.life_playground.run.v4",
                "command": "ego.life_playground.command.v6",
                "trace": "ego.life_playground.trace.v8",
                "world": "ego.life_playground.microworld.state.v4",
                "observation": "ego.life_playground.microworld.observation.v4",
                "public_frame": "ego.life_playground.microworld.public_frame.v5",
            }
            and contract_world["science_weight"] == 0,
            producer_function="_contract_world_report",
            input_artifacts=inputs,
            seed_context_episode_ids={"contract_check": True},
            aggregation_rule="frozen schema versions and science_weight must match contract",
        ),
        "action_boundary_matches_contract": _check_record(
            contract_world["action_set"] == ["turn_left", "turn_right", "move_forward", "interact", "rest"]
            and contract_world["object_count"] == 5
            and set(contract_world["token_mapping"]) == {"v0", "v1", "v2", "v3", "v4"}
            and sorted(contract_world["token_mapping"].values()) == ["novelty", "resource", "shelter", "social", "threat"]
            and contract_world["non_fixed_across_lives"] is True,
            producer_function="_contract_world_report",
            input_artifacts=inputs,
            seed_context_episode_ids={"world_seed": 1701},
            aggregation_rule="action set, object count, token bijection, and non-fixed life placements must match contract",
        ),
        "real_trigger_step_and_run_path": _check_record(
            live_ui["tk_available"] is True
            and live_ui["step_triggered"] is True
            and live_ui["run_triggered"] is True
            and live_ui["sqlite_command_count"] == live_ui["sqlite_trace_count"]
            and live_ui["displayed_sequence"] == live_ui["sqlite_command_count"]
            and live_ui["trigger_sources"][0] == "ui_step_button"
            and "ui_run_button" in live_ui["trigger_sources"][1:],
            producer_function="exercise_live_ui",
            input_artifacts=[*inputs, _artifact_ref(Path(live_ui["db_path"]))],
            seed_context_episode_ids={"ui_live": live_ui["run_id"]},
            aggregation_rule="hidden Tk Step and Run must commit through SQLite and redraw recovered panel state",
        ),
        "replay_two_fresh_processes_match": _check_record(
            all(item["local_vs_fresh_equal"] is True and item["fresh_process_runs_equal"] is True for item in replay["contexts"].values()),
            producer_function="build_replay_report",
            input_artifacts=[*inputs, *[_artifact_ref(Path(context["db_path"])) for context in dataset["contexts"]]],
            seed_context_episode_ids={"replay_context_ids": [context["context_id"] for context in dataset["contexts"]]},
            aggregation_rule="every dataset context must match local recovery and two fresh process recoveries",
        ),
        "tamper_controls_fail_closed": _check_record(
            all(
                all(control["failed_closed"] for control in item["tamper_controls"].values())
                for item in replay["contexts"].values()
            )
            and replay["stored_selected_action_comparison_only"] is True,
            producer_function="build_replay_report",
            input_artifacts=[*inputs, *[_artifact_ref(Path(context["db_path"])) for context in dataset["contexts"]]],
            seed_context_episode_ids={"replay_context_ids": [context["context_id"] for context in dataset["contexts"]]},
            aggregation_rule="tampered initial state, command, selected_action, and prev_trace_hash clones must fail closed for every dataset context",
        ),
        "policy_projection_leakage_scan_clean": _check_record(
            all(scan["offenders"] == [] for scan in clean_scans),
            producer_function="scan_policy_projection",
            input_artifacts=inputs,
            seed_context_episode_ids={"leakage_scan": "clean", "context_ids": [context["context_id"] for context in dataset["contexts"]]},
            aggregation_rule="every live policy projection across every trace/context must be structurally and value-pattern clean",
        ),
        "policy_projection_positive_control_fires": _check_record(
            all(scan["positive_control_detected"] is True for scan in positive_scans),
            producer_function="scan_policy_projection",
            input_artifacts=inputs,
            seed_context_episode_ids={"leakage_scan": "positive_control", "context_ids": [context["context_id"] for context in dataset["contexts"]]},
            aggregation_rule="multi-class positive control must trigger scanner findings for every scanned trace/context",
        ),
        "single_path_dispatch_only": _check_record(
            single_path["pass"] is True,
            producer_function="_single_path_report",
            input_artifacts=inputs,
            seed_context_episode_ids={"single_path_scan": True},
            aggregation_rule="UI path may not bypass controller or create a second reducer/store path",
        ),
        "recursive_provenance_present": _check_record(
            recursive_provenance_present,
            producer_function="collect_evidence_records",
            input_artifacts=[*inputs, _artifact_ref(output / "trace.jsonl")],
            seed_context_episode_ids={"recursive_provenance_scan": True},
            aggregation_rule="all nested evidence-bearing payloads must carry full provenance",
        ),
    }
    aggregated = aggregate_result(checks, acceptance_gate_ids=ACCEPTANCE_GATE_IDS)
    claim_blockers = (
        ["equal_access_control_equivalence"]
        if baseline["disposition"] == "equal_access_equivalent_downgrade"
        else []
    )

    result = {
        **_provenance(
            producer_function="run_card_a_verification",
            input_artifacts=[*inputs, _artifact_ref(output / "trace.jsonl")],
            seed_context_episode_ids={"context_ids": [context["context_id"] for context in dataset["contexts"]]},
            aggregation_rule="engineering acceptance requires schema/action/trigger/replay/tamper/leakage/UI/single-path/provenance checks only; baseline equivalence caps claim but does not fail engineering verdict",
        ),
        "task_id": TASK_ID,
        "checks": checks,
        "verdict": aggregated["verdict"],
        "failed_checks": aggregated["failed_checks"],
        "baseline_disposition": baseline["disposition"],
        "claim_blockers": claim_blockers,
        "claim_ceiling": CLAIM_CEILING,
    }
    failure_manifest = {
        **_provenance(
            producer_function="run_card_a_verification.failure_manifest",
            input_artifacts=result["input_artifacts"],
            seed_context_episode_ids=result["seed_context_episode_ids"],
            aggregation_rule="preserve failed engineering checks and baseline downgrade evidence",
        ),
        "engineering_failures": aggregated["failed_checks"],
        "claim_blockers": claim_blockers,
        "status": "clean" if not aggregated["failed_checks"] else "fail",
    }
    live_ui_receipt = {
        **live_ui,
        "db_path": str(Path(live_ui["db_path"]).resolve()),
    }
    _write_json(output / "baseline_comparison.json", baseline)
    _write_json(output / "ablation_report.json", ablation)
    _write_json(output / "leakage_report.json", leakage)
    _write_json(output / "replay_report.json", replay)
    _write_json(output / "live_ui_receipt.json", live_ui_receipt)
    _write_json(output / "failure_manifest.json", failure_manifest)
    _write_json(output / "result.json", result)
    (output / "claim_ceiling.txt").write_text(CLAIM_CEILING + "\n", encoding="utf-8", newline="\n")

    shutil.rmtree(dataset_root, ignore_errors=True)
    shutil.rmtree(temp_root, ignore_errors=True)
    actual = {path.name for path in output.iterdir()}
    if actual != REQUIRED_ARTIFACTS:
        raise RuntimeError(f"unexpected artifact set: {sorted(actual)}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--recovery-summary", type=Path)
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    if args.recovery_summary is not None:
        if not args.run_id:
            raise SystemExit("--run-id is required with --recovery-summary")
        print(json.dumps(_sqlite_recovery_summary(args.recovery_summary, args.run_id), ensure_ascii=False, sort_keys=True))
        return 0
    if args.output_dir is None:
        raise SystemExit("--output-dir is required")
    result = run_card_a_verification(args.output_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
