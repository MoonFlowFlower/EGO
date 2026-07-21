#!/usr/bin/env python3
"""Capture the pre-change 001B semantic fixture for the bounded 001C task."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
import tempfile
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine  # noqa: E402
from labs.ego_life_playground_v0.controller import PlaygroundController  # noqa: E402
from labs.ego_life_playground_v0.store import SQLiteEventStore  # noqa: E402


TASK_ID = "EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-BOUNDARY-GATE-001C"
FIXTURE_NAME = "prechange_semantic_fixture.json"
PRECHANGE_CONTEXTS = (
    ("p0_cross_v1", 52, 711),
    ("p2_vertical_v1", 54, 711),
)
SOURCE_FILES = (
    "scripts/codex/verify_ego_v2_factored_predictive_control_boundary_gate_001c.py",
    "labs/ego_life_playground_v0/controller.py",
    "labs/ego_life_playground_v0/engine.py",
    "labs/ego_life_playground_v0/predictive_control.py",
    "labs/ego_life_playground_v0/store.py",
)


def _canonical_json(value: Any) -> str:
    return engine.canonical_json(value)


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _context_id(layout_id: str, world_seed: int, policy_seed: int) -> str:
    return f"{layout_id}:world={world_seed}:policy={policy_seed}"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical_json(value) + "\n", encoding="utf-8", newline="\n")


def _step_record(
    trace: dict[str, Any],
    *,
    context_id: str,
    run_id: str,
    world_seed: int,
    policy_seed: int,
) -> dict[str, Any]:
    predictive = trace["predictive_control"]
    plan = predictive["plan"]
    if trace["selected_action"] is None or plan is None:
        raise ValueError("step record requires a committed action trace")
    life_index = int(trace["episode_index"]) + 1
    return {
        "run_id": run_id,
        "context_id": context_id,
        "seed": policy_seed,
        "world_seed": world_seed,
        "life": life_index,
        "episode_id": trace["episode_id"],
        "sequence": trace["sequence"],
        "command_hash": trace["command_hash"],
        "code_path_hash": trace["code_path_hash"],
        "trigger_source": trace["trigger_source"],
        "selected_action": trace["selected_action"],
        "world_transition": trace["world_transition"],
        "food_gain": trace["food_gain"],
        "metabolism": trace["metabolism"],
        "goal_progress": trace["goal_progress"],
        "goal_transition": trace["goal_transition"],
        "goal_before": trace["goal_before"],
        "goal_after": trace["goal_after"],
        "lifecycle": {
            "before": trace["lifecycle_before"],
            "after": trace["lifecycle_after"],
            "life_termination": trace["life_termination"],
            "episode_transition": trace["episode_transition"],
            "carry_reset_receipt": trace["carry_reset_receipt"],
        },
        "predictive_selection": {
            "mode": predictive["mode"],
            "producer_function": plan["producer_function"],
            "algorithm": plan["algorithm"],
            "horizon": plan["horizon"],
            "beam_width": plan["beam_width"],
            "discount": plan["discount"],
            "relative_map_mode": plan["relative_map_mode"],
            "goal_value_mode": plan["goal_value_mode"],
            "active_goal": plan["active_goal"],
            "predictor_input_goal_independent": plan["predictor_input_goal_independent"],
            "selection_mode": plan["selection_mode"],
            "exploration_reason": plan["exploration_reason"],
            "selected_action": plan["selected_action"],
            "mpc_selected_action": plan["mpc_selected_action"],
            "planned_actions": plan["planned_actions"],
            "coverage_step": plan["coverage_step"],
            "exploration_hash": plan["exploration_hash"],
            "tie_break_used": plan["tie_break_used"],
            "tie_break_source": plan["tie_break_source"],
            "model_hash": plan["model_hash"],
            "belief_hash": plan["belief_hash"],
        },
        "action_exposure_counts": plan["action_exposure_counts"],
        "token_interaction_counts": plan["token_interaction_counts"],
        "predictions_by_action": plan["predictions_by_action"],
        "candidate_values": plan["candidate_values"],
        "beam_receipt": plan["beam_receipt"],
    }


def _capture_context(
    layout_id: str,
    world_seed: int,
    policy_seed: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    context_id = _context_id(layout_id, world_seed, policy_seed)
    run_id = f"{TASK_ID}:prechange:{context_id}"
    interventions = dict(
        engine.DEFAULT_INTERVENTIONS,
        predictive_control_mode="factored_mpc",
    )
    with tempfile.TemporaryDirectory(
        prefix="ego-v2-fpc-boundary-001c-", ignore_cleanup_errors=True
    ) as raw_temp:
        db_path = Path(raw_temp) / "prechange.sqlite3"
        steps: list[dict[str, Any]] = []
        with SQLiteEventStore(db_path) as store:
            controller = PlaygroundController(
                store,
                run_id=run_id,
                seed=policy_seed,
                world_seed=world_seed,
                layout_id=layout_id,
            )
            while len(controller.state["lifecycle"]["life_results"]) < 4:
                dispatched = controller.dispatch(
                    interventions,
                    trigger_source="ui_run_button",
                )
                if not dispatched.receipt.committed:
                    raise RuntimeError(dispatched.receipt.error)
                trace = controller.last_trace
                if trace is None:
                    raise RuntimeError("controller dispatch committed without a trace")
                if trace.get("selected_action") is not None:
                    steps.append(
                        _step_record(
                            trace,
                            context_id=context_id,
                            run_id=run_id,
                            world_seed=world_seed,
                            policy_seed=policy_seed,
                        )
                    )
            run_summary = {
                "run_id": run_id,
                "context_id": context_id,
                "seed": policy_seed,
                "world_seed": world_seed,
                "life_count": len(controller.state["lifecycle"]["life_results"]),
                "step_count": len(steps),
                "final_sequence": controller.recovery.last_committed_sequence,
                "trigger_sources": sorted({step["trigger_source"] for step in steps}),
            }
    return run_summary, steps


def capture_prechange_baseline(output_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    runs: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []
    for context in PRECHANGE_CONTEXTS:
        run_summary, run_steps = _capture_context(*context)
        runs.append(run_summary)
        steps.extend(run_steps)
    fixture = {
        "schema_version": "ego.v2.factored_predictive_control_boundary_gate.prechange_fixture.v1",
        "task_id": TASK_ID,
        "producer_function": (
            "verify_ego_v2_factored_predictive_control_boundary_gate_001c.capture_prechange_baseline"
        ),
        "input_source_hashes": {
            relative: _hash_file(REPO_ROOT / relative) for relative in SOURCE_FILES
        },
        "run_ids": [run["run_id"] for run in runs],
        "context_ids": [_context_id(*context) for context in PRECHANGE_CONTEXTS],
        "aggregation_rule": "ordered_committed_controller_steps_until_four_completed_lives_per_context",
        "code_path_hash": engine.compute_code_path_hash(),
        "runs": runs,
        "steps": steps,
        "fresh_effect_seeds_consumed": False,
    }
    _write_json(output_dir / FIXTURE_NAME, fixture)
    return fixture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "artifacts" / TASK_ID,
    )
    parser.add_argument("--capture-baseline", action="store_true")
    args = parser.parse_args(argv)
    if not args.capture_baseline:
        raise SystemExit("this producer requires --capture-baseline")
    fixture = capture_prechange_baseline(args.output_dir)
    print(
        _canonical_json(
            {
                "fixture": str((args.output_dir / FIXTURE_NAME).resolve()),
                "contexts": fixture["context_ids"],
                "step_count": len(fixture["steps"]),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
