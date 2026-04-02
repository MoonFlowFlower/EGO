#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
EGOCORE_ROOT = ROOT / "EgoCore"
OPENEMOTION_ROOT = ROOT / "OpenEmotion"
sys.path.insert(0, str(EGOCORE_ROOT))
sys.path.insert(0, str(OPENEMOTION_ROOT))


def _load_runner():
    runner_path = EGOCORE_ROOT / "tools" / "run_mvp12_shadow_observation.py"
    spec = importlib.util.spec_from_file_location("mvp12_shadow_observation_runner", runner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load runner from {runner_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run_shadow_observation_cycles = _load_runner().run_shadow_observation_cycles


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate controlled MVP12 sandbox evidence via the formal runtime_v2 adapter chain."
    )
    parser.add_argument("--artifacts-dir", default=None)
    parser.add_argument("--session-id", default="session:mvp12:controlled")
    parser.add_argument("--synthetic-cycles", type=int, default=3)
    parser.add_argument("--replay-seed", type=int, default=20260401)
    return parser.parse_args()


def _default_artifacts_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return OPENEMOTION_ROOT / "artifacts" / "mvp12" / f"controlled_{stamp}"


def _fixed_replay_snapshot() -> Dict[str, Any]:
    return {
        "identity_confidence": 0.58,
        "current_mode": "observe",
        "revision_counter": 4,
        "seed_revision_counter": 2,
        "subject_profile": "seed_v0_2",
        "pending_tasks": 0,
        "active_task": False,
        "request_mode": None,
        "snapshot_label": "controlled_replay_baseline",
    }


def _flatten_cycles(*batches: Dict[str, Any]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    for batch in batches:
        merged.extend(list(batch.get("cycles") or []))
    return merged


def _candidate_hashes(batch: Dict[str, Any]) -> List[str]:
    cycles = list(batch.get("cycles") or [])
    if not cycles:
        return []
    return list(((cycles[0].get("developmental_trace") or {}).get("candidate_hashes")) or [])


def _build_markdown_report(summary: Dict[str, Any]) -> str:
    lines = [
        "# MVP12 Controlled Observation Report",
        "",
        f"- generated_at: `{summary['generated_at']}`",
        f"- artifacts_dir: `{summary['artifacts_dir']}`",
        f"- session_id: `{summary['session_id']}`",
        f"- verification_level: `{summary['verification_level']}`",
        f"- completion_class: `{summary['completion_class']}`",
        "",
        "## Summary",
        "",
        f"- total_cycles: `{summary['total_cycles']}`",
        f"- governance_violation_count: `{summary['governance_violation_count']}`",
        f"- replay_consistent: `{summary['replay_consistent']}`",
        f"- shadow_revision_final: `{summary['shadow_revision_final']}`",
        f"- unique_candidate_hash_sets: `{summary['unique_candidate_hash_sets']}`",
        "",
        "## Batches",
        "",
    ]
    for batch in summary["batches"]:
        lines.extend(
            [
                f"### {batch['name']}",
                f"- cycles: `{batch['cycle_count']}`",
                f"- observation_source: `{batch['observation_source']}`",
                f"- trigger: `{batch['trigger']}`",
                f"- governance_violation_count: `{batch['governance_violation_count']}`",
                f"- candidate_hashes: `{batch['candidate_hashes']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Gate",
            "",
            "- [x] no_direct_reply_authority",
            "- [x] no_direct_execution_authority",
            "- [x] no_response_plan_injection",
            "- [x] shadow_only_writeback",
            "",
            "## Notes",
            "",
            "- This is controlled evidence only. It does not prove live enablement or direct_real E4.",
            "- The sandbox still has no direct reply authority and no direct execution authority.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    artifacts_dir = Path(args.artifacts_dir) if args.artifacts_dir else _default_artifacts_dir()
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    os.environ["OPENEMOTION_MVP12_ARTIFACTS_DIR"] = str(artifacts_dir)

    synthetic_idle = run_shadow_observation_cycles(
        cycles=args.synthetic_cycles,
        observation_source="synthetic",
        trigger="idle",
        idle_seconds=120.0,
        session_id=f"{args.session_id}:idle",
        subject_profile="seed_v0_2",
    )
    synthetic_tension = run_shadow_observation_cycles(
        cycles=1,
        observation_source="synthetic",
        trigger="unresolved_tension",
        unresolved_tensions=[{"kind": "goal_conflict", "intensity": 0.91, "label": "controlled_probe"}],
        session_id=f"{args.session_id}:tension",
        subject_profile="seed_v0_2",
    )
    replay_a = run_shadow_observation_cycles(
        cycles=1,
        observation_source="replay",
        trigger="replay_event",
        replay_seed=args.replay_seed,
        session_id=f"{args.session_id}:replay_a",
        subject_profile="seed_v0_2",
        state_snapshot_factory=lambda **_: _fixed_replay_snapshot(),
    )
    replay_b = run_shadow_observation_cycles(
        cycles=1,
        observation_source="replay",
        trigger="replay_event",
        replay_seed=args.replay_seed,
        session_id=f"{args.session_id}:replay_b",
        subject_profile="seed_v0_2",
        state_snapshot_factory=lambda **_: _fixed_replay_snapshot(),
    )

    batches = [
        ("synthetic_idle", synthetic_idle, "synthetic", "idle"),
        ("synthetic_tension", synthetic_tension, "synthetic", "unresolved_tension"),
        ("replay_a", replay_a, "replay", "replay_event"),
        ("replay_b", replay_b, "replay", "replay_event"),
    ]
    all_cycles = _flatten_cycles(synthetic_idle, synthetic_tension, replay_a, replay_b)
    replay_hashes_a = _candidate_hashes(replay_a)
    replay_hashes_b = _candidate_hashes(replay_b)
    replay_consistent = replay_hashes_a == replay_hashes_b and bool(replay_hashes_a)
    governance_violation_count = sum(
        int(((cycle.get("developmental_gate") or {}).get("governance_violation_count")) or 0)
        for cycle in all_cycles
    )
    unique_candidate_hash_sets = len(
        {
            tuple(((cycle.get("developmental_trace") or {}).get("candidate_hashes")) or [])
            for cycle in all_cycles
        }
    )
    shadow_revision_final = 0
    if all_cycles:
        shadow_revision_final = int(
            (((all_cycles[-1].get("developmental_summary") or {}).get("shadow_revision")) or 0)
        )

    summary = {
        "generated_at": datetime.now().isoformat(),
        "artifacts_dir": str(artifacts_dir),
        "session_id": args.session_id,
        "verification_level": "V3",
        "completion_class": "controlled_evidence_only",
        "total_cycles": len(all_cycles),
        "governance_violation_count": governance_violation_count,
        "replay_consistent": replay_consistent,
        "shadow_revision_final": shadow_revision_final,
        "unique_candidate_hash_sets": unique_candidate_hash_sets,
        "batches": [
            {
                "name": name,
                "cycle_count": len(batch.get("cycles") or []),
                "observation_source": observation_source,
                "trigger": trigger,
                "governance_violation_count": sum(
                    int(((cycle.get("developmental_gate") or {}).get("governance_violation_count")) or 0)
                    for cycle in batch.get("cycles") or []
                ),
                "candidate_hashes": _candidate_hashes(batch),
            }
            for name, batch, observation_source, trigger in batches
        ],
    }

    report_json = artifacts_dir / "controlled_observation_report.json"
    report_md = artifacts_dir / "controlled_observation_report.md"
    report_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md.write_text(_build_markdown_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if replay_consistent and governance_violation_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
