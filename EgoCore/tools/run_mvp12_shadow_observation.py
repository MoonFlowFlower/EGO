#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EGOCORE_ROOT = ROOT / "EgoCore"
OPENEMOTION_ROOT = ROOT / "OpenEmotion"
sys.path.insert(0, str(EGOCORE_ROOT))
sys.path.insert(0, str(OPENEMOTION_ROOT))

from app.openemotion_adapter.proto_self_adapter import ProtoSelfAdapter
from app.runtime_v2.proto_self_runtime import RuntimeV2ProtoSelfRuntime
from app.runtime_v2.state import RuntimeV2State


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MVP12 controlled shadow observation via runtime_v2 mainline.")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--observation-source", default="synthetic", choices=["synthetic", "replay", "direct_real"])
    parser.add_argument("--trigger", default="idle", choices=["idle", "unresolved_tension", "long_term_goal", "replay_event"])
    parser.add_argument("--idle-seconds", type=float, default=90.0)
    parser.add_argument("--session-id", default="session:mvp12")
    parser.add_argument("--subject-profile", default=None)
    parser.add_argument("--replay-seed", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ["EGO_ENABLE_MVP12_SANDBOX"] = "true"

    adapter = ProtoSelfAdapter()
    runtime = RuntimeV2ProtoSelfRuntime(adapter=adapter)
    state = RuntimeV2State(session_id=args.session_id)
    state.ingress_context = {
        "proto_self_version": "v2",
        "proto_self_subject_profile": args.subject_profile,
        "interaction_kind": "system",
        "conversation_act": "developmental_tick",
    }

    results = []
    for index in range(args.cycles):
        turn_id = f"dev_{index + 1:03d}"
        result = runtime.process_developmental_tick(
            session_id=args.session_id,
            turn_id=turn_id,
            state=state,
            observation_source=args.observation_source,
            trigger=args.trigger,
            idle_seconds=args.idle_seconds,
            replay_seed=args.replay_seed,
            state_snapshot={
                "cycle_index": index,
                "task_status": state.task_status,
                "current_goal": state.current_goal,
            },
            force_enable=True,
        )
        if result:
            results.append(
                {
                    "event_id": result.get("event_id"),
                    "developmental_summary": result.get("developmental_summary"),
                    "developmental_gate": result.get("developmental_gate"),
                }
            )

    print(json.dumps({"cycles": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
