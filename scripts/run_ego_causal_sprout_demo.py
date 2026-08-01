#!/usr/bin/env python3
"""Run the default-off Causal Sprout dev demo through the shared V2 boundary."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys
import uuid


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.causal_sprout import (
    CausalSproutConfig,
    CausalSproutRuntime,
    reduce_trace_rows,
    render_trace_html,
)
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import SQLiteEventStore


def _judgment(report: dict[str, object]) -> str:
    rows = list(report["rows"])  # type: ignore[arg-type]
    if len(rows) < 8:
        return "INCONCLUSIVE"
    final = rows[-1]
    candidate = float(final["candidate_mse_so_far"])
    control = min(float(final["lookup_mse_so_far"]), float(final["no_update_mse_so_far"]))
    return "LEARNING" if candidate <= 0.75 * max(control, 1e-12) else "SURFACE_FIT"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=96)
    parser.add_argument("--db", type=Path, default=REPO_ROOT / "temp" / "causal_sprout_demo.sqlite3")
    parser.add_argument("--html", type=Path, default=REPO_ROOT / "temp" / "causal_sprout_demo.html")
    parser.add_argument("--seed", type=int, default=424242)
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    if args.steps <= 0:
        parser.error("--steps must be positive")

    steps_per_context = 16
    context_count = max(1, math.ceil(args.steps / steps_per_context))
    config = CausalSproutConfig(
        namespace_prefix="causal_sprout_dev_demo",
        split="dev",
        context_count=context_count,
        steps_per_context=steps_per_context,
        hidden_size=24,
        bptt_steps=8,
        learning_rate=0.012,
        correlation_probability=0.9,
        seed=args.seed,
        exploration_rate=0.50,
    )
    runtime = CausalSproutRuntime(config)
    run_id = args.run_id or f"causal-sprout-demo-{uuid.uuid4().hex[:12]}"
    with SQLiteEventStore(args.db, runtime=runtime) as store:
        controller = PlaygroundController(store, run_id=run_id, seed=args.seed + 1, runtime=runtime)
        for _ in range(args.steps):
            dispatched = controller.dispatch(trigger_source="headless_acceptance")
            if not dispatched.receipt.committed:
                raise RuntimeError(dispatched.receipt.error)
        recovery = controller.recover()

    report = reduce_trace_rows(recovery.traces)
    report["current_judgment"] = _judgment(report)
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(render_trace_html(report), encoding="utf-8")

    print("tick energy feature_a feature_b action actual_delta pred_error updates candidate_mse lookup_mse no_update_mse")
    for row in report["rows"]:
        predictions = row["predicted_delta_by_action"]
        action = row["selected_action"]
        print(
            f"{row['sequence']:>4} {row['energy']:>6.3f} {row['feature_a']:>9.1f} "
            f"{row['feature_b']:>9.1f} {action:>8} {row['actual_delta']:>11.3f} "
            f"{row['prediction_error']:>10.3f} {row['update_count']:>7} "
            f"{row['candidate_mse_so_far']:>13.5f} {row['lookup_mse_so_far']:>10.5f} "
            f"{row['no_update_mse_so_far']:>13.5f} pred={predictions[action]:.3f} "
            f"predicted_delta_by_action={predictions}"
        )
    print(f"current_judgment={report['current_judgment']}")
    print(f"recurrent_state_hash={report['rows'][-1]['recurrent_state_hash']}")
    print(f"model_weight_hash={report['rows'][-1]['model_weight_hash']}")
    print(f"trace_html={args.html.resolve()}")
    print("claim_ceiling=bounded local nursery demo only; not AGI/consciousness/agency/electronic-life evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
