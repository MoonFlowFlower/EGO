#!/usr/bin/env python3
"""Independent public-row verifier for the 001Q product qualification.

This verifier deliberately uses the frozen 001O public reference rather than
the clean product learner module. It sees only qualification rows, never the
product environment state or SQLite packet assignment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import public_featured_transfer as frozen


FORBIDDEN_PUBLIC_KEYS = {
    "private_entropy_hash",
    "local_mode",
    "slot_indices",
    "world_id",
    "layout_id",
    "seed",
    "mapping",
    "oracle_action",
    "future",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _scan_public(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if str(key).lower() in FORBIDDEN_PUBLIC_KEYS:
                findings.append(f"{path}.{key}")
            findings.extend(_scan_public(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            findings.extend(_scan_public(nested, f"{path}[{index}]"))
    return findings


def verify_rows(rows_path: str | Path) -> dict[str, Any]:
    rows = [
        json.loads(line)
        for line in Path(rows_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    state = frozen.new_reference_state()
    failures: list[str] = []
    action_count = 0
    respawn_count = 0
    expected_sequence = 1
    for row in rows:
        supplied_hash = row.get("row_hash")
        unsigned = {key: value for key, value in row.items() if key != "row_hash"}
        if supplied_hash != _canonical_hash(unsigned):
            failures.append(f"sequence {row.get('sequence')}: row hash mismatch")
        if row.get("sequence") != expected_sequence:
            failures.append(f"sequence discontinuity at {row.get('sequence')}")
        expected_sequence += 1
        findings = _scan_public(unsigned)
        if findings:
            failures.append(
                f"sequence {row.get('sequence')}: private fields {findings}"
            )
        kind = row.get("transition_kind")
        if kind == "respawn":
            frozen.reset_for_world(state, preserve_shared=True)
            respawn_count += 1
            if row.get("plan") is not None:
                failures.append(f"sequence {row.get('sequence')}: respawn has plan")
            continue
        if kind != "action":
            failures.append(f"sequence {row.get('sequence')}: unknown transition kind")
            continue
        action_count += 1
        observation = row.get("observation")
        action = row.get("selected_action")
        feedback = row.get("actual_feedback")
        try:
            expected_plan = frozen.plan_action(state, observation)
        except (TypeError, ValueError) as exc:
            failures.append(f"sequence {row.get('sequence')}: plan failed: {exc}")
            continue
        if _canonical_json(expected_plan) != _canonical_json(row.get("plan")):
            failures.append(f"sequence {row.get('sequence')}: plan parity mismatch")
        if action != expected_plan["action"]:
            failures.append(f"sequence {row.get('sequence')}: action parity mismatch")
        if row.get("update_applied"):
            try:
                update = frozen.update_after_transition(
                    state, observation, action, feedback
                )
            except (TypeError, ValueError) as exc:
                failures.append(f"sequence {row.get('sequence')}: update failed: {exc}")
                continue
            if update.get("state_hash_after") != row.get("learner_state_hash_after"):
                failures.append(
                    f"sequence {row.get('sequence')}: learner hash mismatch"
                )
        elif row.get("learner_state_hash_before") != row.get(
            "learner_state_hash_after"
        ):
            failures.append(
                f"sequence {row.get('sequence')}: frozen update changed learner"
            )
    passed = not failures and action_count > 0 and respawn_count > 0
    return {
        "schema_version": "ego.v2.public_featured_product_row_verifier.001q.v1",
        "verifier": "frozen_001o_public_reference_public_rows_only",
        "passed": passed,
        "row_count": len(rows),
        "action_count": action_count,
        "respawn_count": respawn_count,
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rows", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = verify_rows(args.rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
