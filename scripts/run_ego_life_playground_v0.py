#!/usr/bin/env python3
"""Explicit launcher for the local, default-off visible playground."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.app import PlaygroundController, run_app
from labs.ego_life_playground_v0.store import SQLiteEventStore, default_db_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the deterministic local product-clock state/memory/tabular-EMA playground. "
            "Science weight is zero."
        )
    )
    parser.add_argument("--db", type=Path, default=default_db_path(), help="SQLite path (outside repo by default)")
    parser.add_argument("--seed", type=int, default=17, help="deterministic tie-break seed")
    parser.add_argument(
        "--headless-smoke",
        action="store_true",
        help="exercise one real command + recomputing recovery without opening Tk",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.headless_smoke:
        with SQLiteEventStore(args.db) as store:
            controller = PlaygroundController(store, seed=args.seed)
            dispatched = controller.dispatch(
                "resource",
                {
                    "memory_on": True,
                    "learning_on": True,
                    "consolidation_on": True,
                },
            )
            if not dispatched.receipt.committed:
                raise RuntimeError(dispatched.receipt.error)
            recovered = controller.recover()
            print(
                json.dumps(
                    {
                        "run_id": controller.run_id,
                        "step": recovered.state["step"],
                        "selected_action": recovered.traces[-1]["selected_action"],
                        "trace_hash": recovered.traces[-1]["trace_hash"],
                        "recovered": recovered.recovered,
                        "science_weight": 0,
                    },
                    sort_keys=True,
                )
            )
        return 0
    run_app(args.db, seed=args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
