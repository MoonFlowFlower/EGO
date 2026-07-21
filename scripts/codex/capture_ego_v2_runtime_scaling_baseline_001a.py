#!/usr/bin/env python3
"""Capture the pinned pre-optimization semantic command fixture."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.engine import (  # noqa: E402
    DEFAULT_INTERVENTIONS,
    canonical_hash,
    canonical_json,
    compute_code_path_hash,
    compute_step,
    initial_state,
    make_command,
    make_run_metadata,
    world_hash,
)


TASK_ID = "EGO-V2-P0-RUNTIME-SCALING-001A"
PINNED_SOURCE_COMMIT = "21ed758c7e359a0b75e81d1a2a6b877bb537ca5a"
RUN_ID = f"{TASK_ID}:semantic-baseline"
SEED = 17
WORLD_SEED = 23
COMMAND_COUNT = 355


def _candidate_projection(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(candidate.get(key))
        for key in (
            "action",
            "predicted_delta",
            "current_goal_deficit_reduction",
            "total_deficit_reduction",
            "legacy_memory_bias",
            "claim_memory_bias",
            "memory_bias",
            "explore_score",
            "action_cost",
            "total_score",
            "selected",
            "survival_q",
        )
    }


def semantic_projection(state: Mapping[str, Any], trace: Mapping[str, Any]) -> dict[str, Any]:
    survival = trace.get("survival_learning") or {}
    selection = survival.get("selection")
    update = survival.get("update")
    survival_projection = None
    if isinstance(selection, Mapping) and isinstance(update, Mapping):
        survival_projection = {
            "selection_mode": selection["selection_mode"],
            "selected_action": selection["selected_action"],
            "q_by_action": deepcopy(selection["q_by_action"]),
            "reward": update["reward"],
            "td_target": update["td_target"],
            "td_error": update["td_error"],
            "applied": update["applied"],
            "q_selected_before": update["q_selected_before"],
            "q_selected_after": update["q_selected_after"],
            "update_count_after": update["update_count_after"],
        }
    return {
        "sequence": int(trace["sequence"]),
        "selected_action": trace["selected_action"],
        "transition_kind": trace["transition_kind"],
        "world_transition": deepcopy(trace["world_transition"]),
        "metabolism": deepcopy(trace["metabolism"]),
        "goal_transition": deepcopy(trace["goal_transition"]),
        "goal_after": deepcopy(trace["goal_after"]),
        "candidates": [
            _candidate_projection(item) for item in trace.get("candidates", [])
        ],
        "survival": survival_projection,
        "state": {
            "clock": deepcopy(state["clock"]),
            "organism": deepcopy(state["organism"]),
            "current_goal": deepcopy(state["current_goal"]),
            "lifecycle": deepcopy(state["lifecycle"]),
            "world_hash": world_hash(state["world"]),
            "last_action": state["last_action"],
        },
    }


def capture() -> dict[str, Any]:
    run_meta = make_run_metadata(RUN_ID, SEED)
    state = initial_state(run_id=RUN_ID, seed=WORLD_SEED)
    records: list[dict[str, Any]] = []
    durations: list[float] = []
    trace_sizes: list[int] = []
    for _ in range(COMMAND_COUNT):
        command = make_command(
            sequence=int(state["clock"]["global_tick"]) + 1,
            trigger_source="ui_run_button",
            interventions=deepcopy(DEFAULT_INTERVENTIONS),
            prev_command_hash=state["last_command_hash"],
        )
        started = time.perf_counter()
        result = compute_step(state, command, run_meta)
        durations.append(time.perf_counter() - started)
        state = result.next_state
        projection = semantic_projection(state, result.trace)
        records.append(
            {
                "command": command,
                "semantic_projection": projection,
                "semantic_hash": canonical_hash(projection),
            }
        )
        trace_sizes.append(len(canonical_json(result.trace).encode("utf-8")))
    ordered = sorted(durations)
    p95 = ordered[max(0, int(len(ordered) * 0.95) - 1)]
    return {
        "schema_version": "ego.v2.runtime_scaling.semantic_baseline.v1",
        "task_id": TASK_ID,
        "producer_function": (
            "capture_ego_v2_runtime_scaling_baseline_001a.capture"
        ),
        "input_artifacts": [
            {
                "path": "labs/ego_life_playground_v0/engine.py",
                "sha256": hashlib.sha256(
                    (REPO_ROOT / "labs/ego_life_playground_v0/engine.py").read_bytes()
                ).hexdigest(),
            }
        ],
        "source_commit": PINNED_SOURCE_COMMIT,
        "run_id": RUN_ID,
        "seed": SEED,
        "world_seed": WORLD_SEED,
        "context_ids": ["p0_cross_v1:world=23:policy=17"],
        "aggregation_rule": "ordered 355-command canonical semantic projection",
        "code_path_hash": compute_code_path_hash(),
        "command_count": COMMAND_COUNT,
        "records": records,
        "records_hash": canonical_hash(records),
        "baseline_metrics": {
            "compute_step_p95_seconds": p95,
            "compute_step_max_seconds": max(durations),
            "trace_mean_bytes": sum(trace_sizes) / len(trace_sizes),
            "trace_max_bytes": max(trace_sizes),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT
        / "artifacts"
        / TASK_ID
        / "semantic_baseline.json",
    )
    args = parser.parse_args(argv)
    payload = capture()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "records_hash": payload["records_hash"],
                "baseline_metrics": payload["baseline_metrics"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
