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
    render_homeostatic_trace_html,
    run_app,
)
from labs.ego_life_playground_v0.engine import (
    DEFAULT_INTERVENTIONS,
    DEFAULT_PRIVATE_WORLD_SEED,
    EngineInvariantError,
)
from labs.ego_life_playground_v0.microworld import LAYOUTS
from labs.ego_life_playground_v0.store import SQLiteEventStore, default_db_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the deterministic V2 P0 local microworld state/memory/action playground. "
            "Science weight is zero."
        )
    )
    parser.add_argument("--db", type=Path, default=default_db_path(), help="SQLite path (outside repo by default)")
    parser.add_argument("--seed", type=int, default=17, help="deterministic run seed recorded in run metadata")
    parser.add_argument(
        "--world-seed",
        type=int,
        default=DEFAULT_PRIVATE_WORLD_SEED,
        help="independent private-world seed used only when creating a new run",
    )
    parser.add_argument(
        "--layout",
        choices=tuple(LAYOUTS),
        default=None,
        help="layout for a new local run; an existing run's layout is immutable",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--headless-smoke",
        action="store_true",
        help="exercise one real command + recomputing recovery without opening Tk",
    )
    mode.add_argument(
        "--quick-check",
        action="store_true",
        help="exercise one real command + SQLite commit + recomputing recovery without Tk",
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
        "--homeostatic-transfer",
        action="store_true",
        help="enable the default-off legal-public homeostatic Bayesian mode for terminal/headless execution",
    )
    parser.add_argument(
        "--html-report",
        type=Path,
        help="write a recovered-trace-only HTML report after terminal/headless execution",
    )
    parser.add_argument(
        "--command",
        action="append",
        default=[],
        help="execute one terminal command non-interactively; repeat for a script",
    )
    return parser


def _print_controller_construction_error(
    args: argparse.Namespace, exc: EngineInvariantError
) -> None:
    print(
        json.dumps(
            {
                "status": "error",
                "error_code": "controller_construction_failed",
                "error": str(exc),
                "run_id": args.run_id,
                "layout_id": args.layout,
            },
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command and not args.terminal:
        raise SystemExit("--command requires --terminal")
    if args.homeostatic_transfer and not (
        args.terminal or args.headless_smoke or args.quick_check
    ):
        raise SystemExit("--homeostatic-transfer requires --terminal or a headless check")
    if args.html_report is not None and not (
        args.terminal or args.headless_smoke or args.quick_check
    ):
        raise SystemExit("--html-report requires --terminal or a headless check")
    if args.headless_smoke or args.quick_check:
        with SQLiteEventStore(args.db) as store:
            try:
                controller = PlaygroundController(
                    store,
                    run_id=args.run_id,
                    seed=args.seed,
                    world_seed=args.world_seed,
                    layout_id=args.layout,
                )
            except EngineInvariantError as exc:
                _print_controller_construction_error(args, exc)
                return 2
            dispatched = controller.dispatch(
                dict(
                    DEFAULT_INTERVENTIONS,
                    homeostatic_transfer_mode=(
                        "public_bayes" if args.homeostatic_transfer else "off"
                    ),
                ),
                trigger_source="headless_acceptance",
            )
            if not dispatched.receipt.committed:
                raise RuntimeError(dispatched.receipt.error)
            recovered = controller.recover()
            trace = recovered.traces[-1]
            html_report = (
                None
                if args.html_report is None
                else str(render_homeostatic_trace_html(recovered, args.html_report))
            )
            print(
                json.dumps(
                    {
                        "run_id": controller.run_id,
                        "state_schema_version": recovered.state["schema_version"],
                        "command_schema_version": trace["command"]["schema_version"],
                        "clock": recovered.state["clock"],
                        "current_goal": recovered.state["current_goal"],
                        "selected_action": trace["selected_action"],
                        "observation_hash": trace["observation_hash"],
                        "public_state_hash": public_state_hash(recovered.state),
                        "recovered": recovered.recovered,
                        "frame_count": len(recovered.frames),
                        "trigger_source": trace["trigger_source"],
                        "interventions": trace["interventions"],
                        "homeostatic_transfer": trace.get("homeostatic_transfer"),
                        "science_weight": 0,
                        "html_report": html_report,
                    },
                    sort_keys=True,
                )
            )
        return 0
    if args.terminal:
        with SQLiteEventStore(args.db) as store:
            try:
                controller = PlaygroundController(
                    store,
                    run_id=args.run_id,
                    seed=args.seed,
                    world_seed=args.world_seed,
                    layout_id=args.layout,
                )
            except EngineInvariantError as exc:
                _print_controller_construction_error(args, exc)
                return 2
            terminal = TerminalPlayground(controller)
            if args.homeostatic_transfer:
                terminal.homeostatic_transfer_mode = "public_bayes"
            if args.command:
                exit_code = 0
                for command in args.command:
                    result = terminal.execute(command)
                    print(json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
                    if result["status"] == "error":
                        exit_code = 2
                        break
                if args.html_report is not None:
                    render_homeostatic_trace_html(
                        controller.recover(), args.html_report
                    )
                return exit_code

            print("EGO V2 P0 local microworld (default-off; science_weight=0)")
            print(TerminalPlayground.HELP)
            print("injection events: " + ", ".join(terminal.execute("help")["allowed_world_events"]))
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
            if args.html_report is not None:
                render_homeostatic_trace_html(controller.recover(), args.html_report)
        return 0
    try:
        run_app(
            args.db,
            seed=args.seed,
            world_seed=args.world_seed,
            layout_id=args.layout,
            run_id=args.run_id,
        )
    except EngineInvariantError as exc:
        _print_controller_construction_error(args, exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
