#!/usr/bin/env python3
"""Explicit launcher for the local, default-off continuity microworld."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0.app import (
    PlaygroundController,
    TerminalPlayground,
    public_state_hash,
    run_app,
)
from labs.ego_life_playground_v0.engine import DEFAULT_INTERVENTIONS
from labs.ego_life_playground_v0.store import SQLiteEventStore, default_db_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the deterministic V2 P0 local microworld state/memory/action playground. "
            "Science weight is zero."
        )
    )
    parser.add_argument("--db", type=Path, default=default_db_path(), help="SQLite path (outside repo by default)")
    parser.add_argument("--seed", type=int, default=17, help="deterministic tie-break seed")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--headless-smoke",
        action="store_true",
        help="exercise one real command + recomputing recovery without opening Tk",
    )
    mode.add_argument(
        "--terminal",
        action="store_true",
        help="open the interactive P0 microworld terminal instead of Tk",
    )
    parser.add_argument(
        "--run-id",
        help="load this durable run, or create it if it does not yet exist",
    )
    parser.add_argument(
        "--command",
        action="append",
        default=[],
        help="execute one terminal command non-interactively; repeat for a script",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command and not args.terminal:
        raise SystemExit("--command requires --terminal")
    if args.headless_smoke:
        with SQLiteEventStore(args.db) as store:
            controller = PlaygroundController(store, seed=args.seed)
            dispatched = controller.dispatch(
                "resource",
                DEFAULT_INTERVENTIONS,
                trigger_source="headless_acceptance",
            )
            if not dispatched.receipt.committed:
                raise RuntimeError(dispatched.receipt.error)
            recovered = controller.recover()
            print(
                json.dumps(
                    {
                        "run_id": controller.run_id,
                        "clock": recovered.state["clock"],
                        "current_goal": recovered.state["current_goal"],
                        "selected_action": recovered.traces[-1]["selected_action"],
                        "public_state_hash": public_state_hash(recovered.state),
                        "recovered": recovered.recovered,
                        "frame_count": len(recovered.frames),
                        "trigger_source": recovered.traces[-1]["trigger_source"],
                        "interventions": recovered.traces[-1]["interventions"],
                        "science_weight": 0,
                    },
                    sort_keys=True,
                )
            )
        return 0
    if args.terminal:
        with SQLiteEventStore(args.db) as store:
            controller = PlaygroundController(store, run_id=args.run_id, seed=args.seed)
            terminal = TerminalPlayground(controller)
            if args.command:
                exit_code = 0
                for command in args.command:
                    result = terminal.execute(command)
                    print(json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
                    if result["status"] == "error":
                        exit_code = 2
                        break
                return exit_code

            print("EGO V2 P0 local microworld (default-off; science_weight=0)")
            print(TerminalPlayground.HELP)
            print("allowed events: " + ", ".join(terminal.execute("help")["allowed_world_events"]))
            print(json.dumps(terminal.execute("inspect"), indent=2, ensure_ascii=False))
            while True:
                try:
                    command = input("ego> ")
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                result = terminal.execute(command)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                if result["status"] == "quit":
                    break
        return 0
    run_app(args.db, seed=args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
