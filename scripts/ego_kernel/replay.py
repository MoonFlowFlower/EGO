from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from scripts.ego_kernel.probe_substate import run_probe_episode
from scripts.ego_kernel.state import KernelState


def replay_in_process(
    *,
    initial_state: dict[str, Any],
    observations: list[dict[str, Any]],
    allow_unregistered_seed: bool = False,
) -> dict[str, Any]:
    return run_probe_episode(
        KernelState.from_dict(initial_state),
        observations,
        allow_unregistered_seed=allow_unregistered_seed,
    )


def replay_fresh_subprocess(
    *,
    initial_state: dict[str, Any],
    observations: list[dict[str, Any]],
    repo_root: Path,
    allow_unregistered_seed: bool = False,
) -> dict[str, Any]:
    payload = {
        "initial_state": initial_state,
        "observations": observations,
        "allow_unregistered_seed": allow_unregistered_seed,
    }
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.ego_kernel.replay", "--stdin-json"],
        cwd=str(repo_root),
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout)
    return json.loads(completed.stdout)


def compare_action_hash_sequences(
    expected_rows: list[dict[str, Any]],
    actual_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mismatches = []
    if len(expected_rows) != len(actual_rows):
        mismatches.append({"kind": "length", "expected": len(expected_rows), "actual": len(actual_rows)})
    for index, (expected, actual) in enumerate(zip(expected_rows, actual_rows)):
        for field in ("state_before_hash", "action", "state_after_hash"):
            if expected.get(field) != actual.get(field):
                mismatches.append({
                    "index": index,
                    "field": field,
                    "expected": expected.get(field),
                    "actual": actual.get(field),
                })
                break
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdin-json", action="store_true")
    args = parser.parse_args()
    if not args.stdin_json:
        parser.error("--stdin-json is required")
    payload = json.loads(sys.stdin.read() or "{}")
    result = replay_in_process(
        initial_state=payload["initial_state"],
        observations=payload["observations"],
        allow_unregistered_seed=bool(payload.get("allow_unregistered_seed")),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
