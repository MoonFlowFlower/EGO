"""Dev-only public acquisition capacity-recovery campaign.

The initial implementation contains only packet loading and a read-only audit
of the frozen 001J reference call chain. Candidate behavior is added only after
that audit has executable evidence that update, planner read, and final action
selection are connected.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.codex.check_ego_v2_homeostatic_compositional_transfer_001j_capacity import (
    PublicFactorBayes,
    canonical_hash,
)


TASK_ID = "EGO-V2-PUBLIC-ACQUISITION-CAPACITY-RECOVERY-001K"
PREDECESSOR_TASK_ID = "EGO-V2-HOMEOSTATIC-COMPOSITIONAL-TRANSFER-001J"
PACKET_NAMES = ("search_dev", "qualification", "replication")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_root(root: Path) -> Path:
    return root / "artifacts" / TASK_ID


def load_packet_assignments(root: Path, packet_name: str) -> list[dict[str, Any]]:
    """Load one evaluator-private task-local packet and verify its commitment."""

    if packet_name not in PACKET_NAMES:
        raise ValueError(f"unknown 001K packet: {packet_name!r}")
    root = Path(root).resolve()
    artifact_root = _artifact_root(root)
    commitments = json.loads(
        (artifact_root / "packet_commitments.json").read_text(encoding="utf-8")
    )
    packet_path = artifact_root / f"{packet_name}_assignments.json"
    expected = commitments["packets"][packet_name]["assignment_sha256"]
    if _sha256(packet_path) != expected:
        raise RuntimeError(f"{packet_name} assignment commitment mismatch")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if (
        packet.get("task_id") != TASK_ID
        or packet.get("packet_name") != packet_name
        or packet.get("dev_only") is not True
        or packet.get("original_001j_assignment") is not False
    ):
        raise RuntimeError(f"{packet_name} packet authority mismatch")
    assignments = packet.get("assignments")
    if not isinstance(assignments, list) or len(assignments) != 16:
        raise RuntimeError(f"{packet_name} packet must contain exactly 16 assignments")
    return deepcopy(assignments)


def _call_name(node: ast.Call) -> str:
    target = node.func
    if isinstance(target, ast.Attribute):
        prefix = target.value.id if isinstance(target.value, ast.Name) else ""
        return f"{prefix}.{target.attr}" if prefix else target.attr
    if isinstance(target, ast.Name):
        return target.id
    return ""


def _predecessor_ast_call_order(source_path: Path) -> dict[str, Any]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    run_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_trajectory"
    )
    calls = sorted(
        (
            {"name": _call_name(node), "line": int(node.lineno)}
            for node in ast.walk(run_node)
            if isinstance(node, ast.Call)
        ),
        key=lambda item: item["line"],
    )
    selected: dict[str, int] = {}
    wanted = {
        "reference.plan": "plan",
        "microworld.transition_world": "transition",
        "engine.compute_actual_delta": "actual_delta",
        "engine.compute_metabolism_ledger": "metabolism",
        "reference.update": "update",
    }
    for call in calls:
        if call["name"] in wanted:
            selected[wanted[call["name"]]] = call["line"]
    complete = set(selected) == set(wanted.values())
    ordered = complete and (
        selected["plan"]
        < selected["transition"]
        < selected["actual_delta"]
        < selected["metabolism"]
        < selected["update"]
    )
    return {
        "source_path": source_path.as_posix(),
        "source_sha256": _sha256(source_path),
        "selected_call_lines": selected,
        "plan_before_transition_before_update": ordered,
    }


def _synthetic_state_intervention() -> dict[str, Any]:
    visual = [["empty"] * 5 for _ in range(5)]
    visual[2][2] = "self"
    visual[1][2] = "v3"
    payload = {
        "observation": {
            "schema_version": "ego.life_playground.microworld.observation.v4",
            "visual": visual,
        },
        "organism": {"energy": 0.30, "safety": 0.30},
        "last_action": None,
        "last_delta": {"energy": 0.0, "safety": 0.0},
    }
    reference = PublicFactorBayes.empty()
    before_state_hash = canonical_hash(reference.state)
    before_action, before_receipt = reference.plan(payload, sequence=1)
    update = reference.update(
        token="v3",
        action="interact",
        actual_delta={"energy": -0.018, "safety": -0.18},
    )
    after_update_state_hash = canonical_hash(reference.state)
    after_action, after_receipt = reference.plan(payload, sequence=2)
    return {
        "public_payload_hash": canonical_hash(payload),
        "state_hash_before": before_state_hash,
        "state_hash_after_update": after_update_state_hash,
        "update_receipt": update,
        "plan_before_update": before_receipt,
        "plan_after_update": after_receipt,
        "action_before_update": before_action,
        "action_after_update": after_action,
        "state_changed_on_update": before_state_hash != after_update_state_hash,
        "planner_read_changed_action": before_action != after_action,
        "planner_read_update_state": (
            after_receipt["state_hash_before"] == after_update_state_hash
        ),
    }


def _stored_row_diagnostics(rows_path: Path) -> dict[str, Any]:
    rows = [
        json.loads(line)
        for line in rows_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    public = [row for row in rows if row.get("arm") == "PUBLIC_FACTOR_BAYES"]
    successful = [
        row
        for row in public
        if row.get("world_transition", {}).get("outcome_type") == "interacted"
    ]
    by_world: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in public:
        by_world[str(row["context_id"])].append(row)
    complete_token_worlds = 0
    for world_rows in by_world.values():
        tokens = {
            str(row["world_transition"]["token"])
            for row in world_rows
            if row["world_transition"].get("outcome_type") == "interacted"
        }
        complete_token_worlds += len(tokens) == 5
    action_counts = Counter(str(row["selected_action"]) for row in public)
    reason_counts = Counter(str(row["selection_reason"]) for row in public)
    turn_count = action_counts["turn_left"] + action_counts["turn_right"]
    return {
        "rows_path": rows_path.as_posix(),
        "rows_sha256": _sha256(rows_path),
        "public_rows": len(public),
        "public_worlds": len(by_world),
        "successful_interactions": len(successful),
        "worlds_identifying_all_five_tokens": complete_token_worlds,
        "action_counts": dict(sorted(action_counts.items())),
        "selection_reason_counts": dict(sorted(reason_counts.items())),
        "turn_fraction": round(turn_count / len(public), 12),
        "stored_rows_only_no_trajectory_reexecution": True,
    }


def audit_predecessor_call_chain(root: Path) -> dict[str, Any]:
    """Audit stored 001J bytes and its call graph without rerunning its packet."""

    root = Path(root).resolve()
    commitments = json.loads(
        (_artifact_root(root) / "packet_commitments.json").read_text(encoding="utf-8")
    )
    predecessor_hashes = commitments["frozen_001j_sha256"]
    hash_matches = {
        relative: (root / relative).is_file()
        and _sha256(root / relative) == expected
        for relative, expected in predecessor_hashes.items()
    }
    source_path = (
        root
        / "scripts"
        / "codex"
        / "check_ego_v2_homeostatic_compositional_transfer_001j_capacity.py"
    )
    ast_order = _predecessor_ast_call_order(source_path)
    intervention = _synthetic_state_intervention()
    stored = _stored_row_diagnostics(
        root
        / "artifacts"
        / PREDECESSOR_TASK_ID
        / "capacity_rows.jsonl"
    )
    checks = {
        "predecessor_hashes_match": all(hash_matches.values()),
        "plan_before_transition_before_update": ast_order[
            "plan_before_transition_before_update"
        ],
        "state_changed_on_update": intervention["state_changed_on_update"],
        "planner_read_changed_action": intervention["planner_read_changed_action"],
        "planner_read_update_state": intervention["planner_read_update_state"],
        "stored_rows_not_reexecuted": stored[
            "stored_rows_only_no_trajectory_reexecution"
        ],
    }
    return {
        "schema_version": "ego.v2.public_acquisition.call_chain_audit.v1",
        "task_id": TASK_ID,
        "audit_target": PREDECESSOR_TASK_ID,
        "producer_function": (
            "run_ego_v2_public_acquisition_capacity_recovery_001k."
            "audit_predecessor_call_chain"
        ),
        "predecessor_hashes_match": all(hash_matches.values()),
        "predecessor_hash_checks": hash_matches,
        "ast_call_order": ast_order,
        "synthetic_state_intervention": intervention,
        "stored_row_diagnostics": stored,
        "original_001j_heldout_reexecuted": False,
        "checks": checks,
        "passed": all(checks.values()),
        "claim_ceiling": (
            "Call-chain wiring and stored-row diagnosis only; not public "
            "acquisition capacity or transfer evidence."
        ),
    }


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not args.audit:
        parser.error("the current frozen implementation supports --audit only")
    report = audit_predecessor_call_chain(args.root)
    if args.output is not None:
        _write_json(args.output, report)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
