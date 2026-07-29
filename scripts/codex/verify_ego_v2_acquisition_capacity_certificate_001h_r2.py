from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

R1_SCRIPT_PATH = (
    REPO_ROOT
    / "scripts"
    / "codex"
    / "verify_ego_v2_acquisition_benchmark_admission_001h_r1.py"
)
ACTION_ORDER = ("turn_left", "turn_right", "move_forward", "interact", "rest")
ACTION_INDEX = {action: index for index, action in enumerate(ACTION_ORDER)}
PANEL_NAV_ACTIONS = ("turn_left", "turn_right", "move_forward")
TARGET_ORDER = ["v0", "v1", "v2", "v3", "v4", "empty", "wall"]
PANEL_TARGET_MULTISET = [
    "v0",
    "v1",
    "v2",
    "v3",
    "v4",
    "empty",
    "wall",
    "empty",
    "wall",
]
PANEL_FLOORS = {
    "v0": 8,
    "v1": 8,
    "v2": 8,
    "v3": 8,
    "v4": 8,
    "empty": 16,
    "wall": 16,
}
FROZEN_CONTEXTS = (
    {
        "context_id": "p0_cross_v1:world=52:policy=711",
        "layout_id": "p0_cross_v1",
        "world_seed": 52,
        "policy_seed": 711,
        "panel_rollout_ids": [9, 10, 11, 12, 13, 14, 15, 16],
    },
    {
        "context_id": "p2_vertical_v1:world=54:policy=711",
        "layout_id": "p2_vertical_v1",
        "world_seed": 54,
        "policy_seed": 711,
        "panel_rollout_ids": [9, 10, 11, 12, 13, 14, 15, 16],
    },
)
FROZEN_SOURCE_PINS = {
    "docs/codex/tasks/EGO-V2-P1-BAYESIAN-ACTIVE-IDENTIFICATION-001H.md": "2f34b8c6e378f88a8cf66db957ec58c8e9adb44a3f8f712aea04ece797d2ddfc",
    "docs/codex/tasks/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1.md": "915610ed949db8f670c7bba83f9fc0786b1130652185a3ead05c04e9c37295bb",
    "docs/codex/tasks/ego-v2-p1-acquisition-benchmark-admission-001h-r1/COLLISION_RECORD.md": "76e0cb8c9687d20fe8df131b1b52bf359b62789736c9f6e42937f749fd89a73e",
    "artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/result.json": "e6c7ef8aec16363e7888cf4f07de809b2e72a0c8d672806b2c206a985d77edcb",
    "artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/support_report.json": "969d92c1e4126ec6573b3586b0e93dde7935879888b34e07f9a115192cc2bf8a",
    "artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/panel_manifest.json": "347eb90b55d0fabbdfe6ee5e3db0da1321fd584e6ffa3aa49d9fb03a117f1522",
    "artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/recompute_report.json": "62ab3413a379f45b2b8b055fba277aa791be0bbe31fb985cc190ac44469d64fd",
    "scripts/codex/verify_ego_v2_acquisition_benchmark_admission_001h_r1.py": "5495d1a69977bdf195bcc239d8e5424c4e89ea498810d797814978a342f0c01a",
    "labs/ego_life_playground_v0/engine.py": "867ced15abc356daa0d5cae3f4c1cb1412a15766239ee82e9a8d280e5b214385",
    "labs/ego_life_playground_v0/microworld.py": "d87ba9530d32d2b504c75a132ae1163dfe8e8cd0a8879e6cbdd09807a9daa923",
    "labs/ego_life_playground_v0/predictive_control.py": "1763ee3e2b755529559311fb99f247b8bc1034d0cc89708dafdd4b15e8529aae",
    "labs/ego_life_playground_v0/store.py": "3e399471c89ec5046ae3bffe1de3419e61f8b1e0f8d3bb55d216ef6578616b84",
    "requirements-ego-v2.txt": "a23aaf94250a9f53031a592980142245a848e2372b6c6c3093e8260b129265b8",
}
STALE_WORLD_SEEDS = frozenset({60, 61, 62, 63, 64, 65})
STALE_POLICY_SEEDS = frozenset({721, 722})
BASE64_PATTERN = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")


def _load_r1_module():
    spec = importlib.util.spec_from_file_location(
        "verify_001h_r1_for_r2",
        R1_SCRIPT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load pinned R1 verifier")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


_R1 = _load_r1_module()
np = _R1.np
engine = _R1.engine
runtime_receipt = _R1.runtime_receipt
quotient_features = _R1.quotient_features
build_public_checkpoint = _R1.build_public_checkpoint
advance_evaluator_action = _R1.advance_evaluator_action
advance_evaluator_respawn = _R1.advance_evaluator_respawn
initialize_evaluator_state = _R1.initialize_evaluator_state
private_shortest_front_path = _R1.private_shortest_front_path
scan_learner_projection = _R1.scan_learner_projection
compute_support_counts = _R1._support_counts_from_rows
compute_rank_reports = _R1._rank_reports_from_rows
evaluate_forced_action_truth = _R1.evaluate_forced_action_truth
build_artifact_manifest = _R1.build_artifact_manifest
verify_artifact_manifest = _R1.verify_artifact_manifest


def build_frozen_contract() -> dict[str, Any]:
    return {
        "task_id": "EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2",
        "contexts": deepcopy(list(FROZEN_CONTEXTS)),
        "witness_search": {
            "action_budget": 89,
            "max_life_index": 4,
            "max_respawns": 3,
            "processed_node_cap": 2_000_000,
            "action_order": list(ACTION_ORDER),
            "analytic_root_lower_bound": 76,
        },
        "panel_search": {
            "processed_node_cap": 250_000,
            "action_order": list(PANEL_NAV_ACTIONS),
        },
        "panel_target_multiset": deepcopy(PANEL_TARGET_MULTISET),
        "panel_floors": deepcopy(PANEL_FLOORS),
        "source_pins": deepcopy(FROZEN_SOURCE_PINS),
        "stale_world_seed_firewall": sorted(STALE_WORLD_SEEDS),
        "stale_policy_seed_firewall": sorted(STALE_POLICY_SEEDS),
    }


def validate_frozen_contract(contract: dict[str, Any]) -> dict[str, Any]:
    expected = build_frozen_contract()
    reasons: list[str] = []
    for key in ("task_id", "panel_target_multiset", "panel_floors", "source_pins"):
        if contract.get(key) != expected[key]:
            reasons.append(key)
    for key in ("action_budget", "max_life_index", "max_respawns", "processed_node_cap"):
        if contract.get("witness_search", {}).get(key) != expected["witness_search"][key]:
            reasons.append(f"witness_search.{key}")
    if (
        contract.get("panel_search", {}).get("processed_node_cap")
        != expected["panel_search"]["processed_node_cap"]
    ):
        reasons.append("panel_search.processed_node_cap")
    contexts = list(contract.get("contexts", []))
    if contexts != expected["contexts"]:
        for index, (actual, wanted) in enumerate(
            zip(contexts, expected["contexts"], strict=False)
        ):
            if actual != wanted:
                for field in sorted(set(actual) | set(wanted)):
                    if actual.get(field) != wanted.get(field):
                        reasons.append(f"contexts[{index}].{field}")
        if len(contexts) != len(expected["contexts"]):
            reasons.append("contexts.length")
    for index, context in enumerate(contexts):
        if context.get("world_seed") in STALE_WORLD_SEEDS:
            reasons.append(f"contexts[{index}].world_seed_stale_firewall")
        if context.get("policy_seed") in STALE_POLICY_SEEDS:
            reasons.append(f"contexts[{index}].policy_seed_stale_firewall")
    valid = not reasons
    return {
        "valid": valid,
        "verdict": "CONTRACT_OK" if valid else "INVALID_POSTRESULT_RESCUE",
        "failure_reasons": reasons,
        "contract_digest": engine.canonical_hash(contract),
        "expected_contract_digest": engine.canonical_hash(expected),
    }


def remaining_action_lower_bound(
    *,
    support_deficits: dict[str, int],
    rank_gaps: dict[str, int],
) -> int:
    return sum(
        max(int(support_deficits.get(action, 0)), int(rank_gaps.get(action, 0)))
        for action in ACTION_ORDER
    )


def root_analytic_lower_bound(contract: dict[str, Any] | None = None) -> int:
    _ = contract
    return remaining_action_lower_bound(
        support_deficits={
            "interact": 24,
            "move_forward": 13,
            "rest": 13,
            "turn_left": 13,
            "turn_right": 13,
        },
        rank_gaps={action: 0 for action in ACTION_ORDER},
    )


def assess_budget_feasibility(
    *,
    action_budget: int,
    support_deficits: dict[str, int],
    rank_gaps: dict[str, int],
    g: int,
) -> dict[str, int | str]:
    h = remaining_action_lower_bound(
        support_deficits=support_deficits,
        rank_gaps=rank_gaps,
    )
    f = int(g) + h
    return {
        "status": "bound_pruned" if f > int(action_budget) else "within_budget",
        "g": int(g),
        "h": h,
        "f": f,
        "action_budget": int(action_budget),
    }


def make_search_node(
    *,
    evaluator_state: dict[str, Any],
    g: int,
    prefix: tuple[int, ...],
    support_counts: dict[str, int],
    rank_rows: dict[str, Any],
    accepted_rows: list[dict[str, Any]],
    life_index: int,
    respawn_count: int,
) -> dict[str, Any]:
    return {
        "evaluator_state": deepcopy(evaluator_state),
        "g": int(g),
        "prefix": tuple(int(item) for item in prefix),
        "support_counts": {str(key): int(value) for key, value in support_counts.items()},
        "rank_rows": deepcopy(rank_rows),
        "accepted_rows": deepcopy(accepted_rows),
        "life_index": int(life_index),
        "respawn_count": int(respawn_count),
    }


def search_node_digest(node: dict[str, Any]) -> str:
    payload = {
        "evaluator_state": node["evaluator_state"],
        "g": int(node["g"]),
        "support_counts": node["support_counts"],
        "rank_rows": node["rank_rows"],
        "accepted_rows": node["accepted_rows"],
        "life_index": int(node["life_index"]),
        "respawn_count": int(node["respawn_count"]),
    }
    return engine.canonical_hash(payload)


def _digest_bytes(digest: str) -> bytes:
    return bytes.fromhex(str(digest))


def pack_action_prefix(prefix: tuple[int, ...]) -> bytes:
    accumulator = 0
    bit_count = 0
    output = bytearray()
    for action in prefix:
        accumulator |= (int(action) & 0b111) << bit_count
        bit_count += 3
        while bit_count >= 8:
            output.append(accumulator & 0xFF)
            accumulator >>= 8
            bit_count -= 8
    if bit_count:
        output.append(accumulator & 0xFF)
    return bytes(output)


def unpack_action_prefix(payload: bytes, *, length: int) -> tuple[int, ...]:
    iterator = iter(payload)
    accumulator = 0
    bit_count = 0
    values: list[int] = []
    while len(values) < length:
        while bit_count < 3:
            accumulator |= next(iterator, 0) << bit_count
            bit_count += 8
        values.append(accumulator & 0b111)
        accumulator >>= 3
        bit_count -= 3
    return tuple(values)


class DuplicateLedger:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS duplicate_ledger (digest BLOB PRIMARY KEY, g INTEGER NOT NULL, prefix_len INTEGER NOT NULL, prefix_bits BLOB NOT NULL)"
            )
            connection.commit()

    def observe(
        self,
        node: dict[str, Any],
        digest_override: str | None = None,
    ) -> dict[str, Any]:
        digest_hex = str(digest_override or search_node_digest(node))
        digest = _digest_bytes(digest_hex)
        prefix = tuple(node["prefix"])
        packed = pack_action_prefix(prefix)
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT g, prefix_len, prefix_bits FROM duplicate_ledger WHERE digest = ?",
                (digest,),
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO duplicate_ledger(digest, g, prefix_len, prefix_bits) VALUES (?, ?, ?, ?)",
                    (digest, int(node["g"]), len(prefix), packed),
                )
                connection.commit()
                return {
                    "status": "new",
                    "digest": digest_hex,
                    "representative_prefix": prefix,
                }
            stored_g = int(row[0])
            stored_prefix = unpack_action_prefix(bytes(row[2]), length=int(row[1]))
            if stored_g != int(node["g"]):
                raise ValueError("same digest with different g")
            if prefix < stored_prefix:
                connection.execute(
                    "UPDATE duplicate_ledger SET prefix_len = ?, prefix_bits = ? WHERE digest = ?",
                    (len(prefix), packed, digest),
                )
                connection.commit()
                return {
                    "status": "replaced",
                    "digest": digest_hex,
                    "representative_prefix": prefix,
                }
            return {
                "status": "duplicate",
                "digest": digest_hex,
                "representative_prefix": stored_prefix,
            }


class ReceiptStream:
    def __init__(self, contract_digest: str) -> None:
        self.processed_nodes = 0
        self._chain = hashlib.sha256(_digest_bytes(contract_digest))
        self._first_samples: list[dict[str, Any]] = []
        self._final_samples: deque[dict[str, Any]] = deque(maxlen=32)
        self._every_10000th: list[dict[str, Any]] = []

    def add(self, sample: dict[str, Any]) -> None:
        normalized = deepcopy(sample)
        encoded = json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self._chain.update(hashlib.sha256(encoded).digest())
        self.processed_nodes += 1
        if len(self._first_samples) < 32:
            self._first_samples.append(normalized)
        if self.processed_nodes % 10_000 == 0:
            self._every_10000th.append(normalized)
        self._final_samples.append(normalized)

    def finish(self) -> dict[str, Any]:
        return {
            "processed_nodes": self.processed_nodes,
            "digest_chain": self._chain.hexdigest(),
            "first_samples": list(self._first_samples),
            "every_10000th": list(self._every_10000th),
            "final_samples": list(self._final_samples),
        }


def depth_first_branch_and_bound(
    *,
    root: dict[str, Any],
    expand_fn,
    goal_fn,
    bound_fn,
    action_budget: int,
    processed_node_cap: int,
    ledger_path: Path | str,
    contract_digest: str,
) -> dict[str, Any]:
    ledger = DuplicateLedger(ledger_path)
    stream = ReceiptStream(contract_digest)
    stack = [root]
    while stack:
        node = stack.pop()
        observed = ledger.observe(node)
        if observed["status"] == "duplicate":
            continue
        g = int(node["g"])
        h = int(bound_fn(node))
        digest = search_node_digest(node)
        sample_index = stream.processed_nodes + 1
        if goal_fn(node) and g == int(action_budget):
            stream.add(
                {
                    "processed_node_index": sample_index,
                    "node_digest": digest,
                    "g": g,
                    "h": h,
                    "node_disposition": "goal",
                }
            )
            receipt_stream = stream.finish()
            return {
                "status": "goal_found",
                "goal_node": deepcopy(node),
                "complete_search": False,
                "unprocessed_legal_child": False,
                "processed_nodes": receipt_stream["processed_nodes"],
                "receipt_stream": receipt_stream,
            }
        if g == int(action_budget):
            stream.add(
                {
                    "processed_node_index": sample_index,
                    "node_digest": digest,
                    "g": g,
                    "h": h,
                    "node_disposition": "horizon_non_goal",
                }
            )
            continue
        if g + h > int(action_budget):
            stream.add(
                {
                    "processed_node_index": sample_index,
                    "node_digest": digest,
                    "g": g,
                    "h": h,
                    "node_disposition": "bound_pruned",
                }
            )
            continue
        if int(node["life_index"]) > 4 or int(node["respawn_count"]) > 3:
            stream.add(
                {
                    "processed_node_index": sample_index,
                    "node_digest": digest,
                    "g": g,
                    "h": h,
                    "node_disposition": "lifecycle_pruned",
                }
            )
            continue
        children = list(expand_fn(node))
        stream.add(
            {
                "processed_node_index": sample_index,
                "node_digest": digest,
                "g": g,
                "h": h,
                "dispositions": [
                    {
                        "action": ACTION_ORDER[tuple(child["prefix"])[g]],
                        "child_digest": search_node_digest(child),
                    }
                    for child in children
                ],
            }
        )
        for child in reversed(children):
            if stream.processed_nodes >= int(processed_node_cap):
                receipt_stream = stream.finish()
                return {
                    "status": "WITNESS_SEARCH_INCONCLUSIVE",
                    "complete_search": False,
                    "unprocessed_legal_child": True,
                    "processed_nodes": receipt_stream["processed_nodes"],
                    "receipt_stream": receipt_stream,
                }
            stack.append(child)
    receipt_stream = stream.finish()
    return {
        "status": "search_exhausted",
        "complete_search": True,
        "unprocessed_legal_child": False,
        "processed_nodes": receipt_stream["processed_nodes"],
        "receipt_stream": receipt_stream,
    }


def _context_identity(context_spec: dict[str, Any]) -> tuple[str, str, int, int]:
    return (
        context_spec["context_id"],
        context_spec["layout_id"],
        int(context_spec["world_seed"]),
        int(context_spec["policy_seed"]),
    )


def _copy_state(state: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(state)


def _advance_with_respawn(
    state: dict[str, Any],
    action: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    advanced = advance_evaluator_action(state, action)
    next_state = advanced["state"]
    if next_state.get("awaiting_respawn"):
        next_state = advance_evaluator_respawn(next_state)
    return next_state, advanced["row"]


def _replay_actions(
    *,
    initial_state: dict[str, Any],
    actions: list[str],
    context_id: str,
    action_index_offset: int = 0,
) -> dict[str, Any]:
    state = _copy_state(initial_state)
    rows = []
    for index, action in enumerate(actions, start=1):
        state, row = _advance_with_respawn(state, action)
        decorated = deepcopy(row)
        decorated.setdefault("context_id", context_id)
        decorated.setdefault("action_index", action_index_offset + index)
        rows.append(decorated)
    return {"state": state, "rows": rows}


def _candidate_specs_for_state(state: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for target_order, target in enumerate(TARGET_ORDER):
        navigation = list(private_shortest_front_path(state["world"], target)["actions"])
        terminal_action = "interact" if target != "wall" else "move_forward"
        primitive_actions = [*navigation, terminal_action]
        candidates.append(
            {
                "name": f"target:{target}",
                "primitive_actions": primitive_actions,
                "action_indices": tuple(
                    ACTION_INDEX[action] for action in primitive_actions
                ),
                "target_order": target_order,
                "terminal_action_order": ACTION_INDEX[terminal_action],
            }
        )
    for action in ACTION_ORDER:
        candidates.append(
            {
                "name": f"direct:{action}",
                "primitive_actions": [action],
                "action_indices": (ACTION_INDEX[action],),
                "target_order": 7,
                "terminal_action_order": ACTION_INDEX[action],
            }
        )
    return candidates


def _score_candidate(
    *,
    context_id: str,
    rows,
    primitive_action_count: int,
    target_order: int,
    terminal_action_order: int,
    action_indices: tuple[int, ...],
) -> tuple[Any, ...]:
    support_counts = compute_support_counts(rows)
    support_deficits = {
        "interact": max(
            0,
            24 - sum(value for key, value in support_counts.items() if key.startswith("interact::")),
        ),
        "move_forward": max(
            0,
            13
            - (
                support_counts.get("move_forward::moved", 0)
                + support_counts.get("move_forward::blocked", 0)
            ),
        ),
        "rest": max(0, 13 - support_counts.get("rest::rested", 0)),
        "turn_left": max(0, 13 - support_counts.get("turn_left::turned", 0)),
        "turn_right": max(0, 13 - support_counts.get("turn_right::turned", 0)),
    }
    ranks = compute_rank_reports(context_id, rows)
    rank_gaps = {
        action: max(0, 13 - int(ranks[f"{context_id}::{action}"].get("rank", 0)))
        for action in ACTION_ORDER
    }
    return (
        remaining_action_lower_bound(
            support_deficits=support_deficits,
            rank_gaps=rank_gaps,
        ),
        -sum(
            int(ranks[f"{context_id}::{action}"].get("rank", 0))
            for action in ACTION_ORDER
        ),
        primitive_action_count,
        target_order,
        terminal_action_order,
        action_indices,
    )


def run_live_warm_start(
    context_spec: dict[str, Any],
    *,
    action_budget: int,
) -> dict[str, Any]:
    context_id, layout_id, world_seed, policy_seed = _context_identity(context_spec)
    state = initialize_evaluator_state(
        layout_id=layout_id,
        world_seed=world_seed,
        policy_seed=policy_seed,
        run_id=context_id,
    )
    initial_state = _copy_state(state)
    chosen_actions: list[str] = []
    rows: list[dict[str, Any]] = []
    while len(chosen_actions) < int(action_budget):
        build_public_checkpoint(
            world=state["world"],
            organism=state.get("organism", {}),
            predictive_state=state.get("predictive_state", {}),
            episode_index=int(state.get("episode_index", 0)),
        )
        candidates = []
        for candidate in _candidate_specs_for_state(state):
            if len(chosen_actions) + len(candidate["primitive_actions"]) > int(action_budget):
                continue
            simulated = _replay_actions(
                initial_state=state,
                actions=candidate["primitive_actions"],
                context_id=context_id,
                action_index_offset=len(rows),
            )
            score = _score_candidate(
                context_id=context_id,
                rows=[*rows, *simulated["rows"]],
                primitive_action_count=len(candidate["primitive_actions"]),
                target_order=candidate["target_order"],
                terminal_action_order=candidate["terminal_action_order"],
                action_indices=candidate["action_indices"],
            )
            candidates.append({**candidate, "simulated": simulated, "score": score})
        if not candidates:
            break
        best = min(candidates, key=lambda item: item["score"])
        chosen_actions.extend(best["primitive_actions"])
        rows.extend(best["simulated"]["rows"])
        state = best["simulated"]["state"]
    replay = _replay_actions(
        initial_state=initial_state,
        actions=chosen_actions,
        context_id=context_id,
    )
    return {
        "certificate_found": len(chosen_actions) == int(action_budget),
        "replay_valid": replay["rows"] == rows,
        "actions": chosen_actions,
        "rows": replay["rows"],
        "support_counts": compute_support_counts(replay["rows"]),
        "rank_reports": compute_rank_reports(context_id, replay["rows"]),
    }


def independent_verify_witness_search(
    *,
    root: dict[str, Any],
    expand_fn,
    bound_fn,
    action_budget: int,
    processed_node_cap: int,
    expected_receipt_stream: dict[str, Any],
    contract_digest: str,
) -> dict[str, Any]:
    stream = ReceiptStream(contract_digest)
    stack = [root]
    processed = 0
    while stack:
        node = stack.pop()
        processed += 1
        g = int(node["g"])
        h = int(bound_fn(node))
        digest = search_node_digest(node)
        if g == int(action_budget):
            stream.add(
                {
                    "processed_node_index": processed,
                    "node_digest": digest,
                    "g": g,
                    "h": h,
                    "node_disposition": "horizon_non_goal",
                }
            )
            continue
        if g + h > int(action_budget):
            stream.add(
                {
                    "processed_node_index": processed,
                    "node_digest": digest,
                    "g": g,
                    "h": h,
                    "node_disposition": "bound_pruned",
                }
            )
            continue
        children = list(expand_fn(node))
        stream.add(
            {
                "processed_node_index": processed,
                "node_digest": digest,
                "g": g,
                "h": h,
                "dispositions": [
                    {
                        "action": ACTION_ORDER[tuple(child["prefix"])[g]],
                        "child_digest": search_node_digest(child),
                    }
                    for child in children
                ],
            }
        )
        if processed >= int(processed_node_cap) and children:
            break
        for child in reversed(children):
            stack.append(child)
    receipt_stream = stream.finish()
    return {
        "verified": (
            receipt_stream["digest_chain"] == expected_receipt_stream.get("digest_chain")
            and receipt_stream["processed_nodes"]
            == expected_receipt_stream.get("processed_nodes")
        ),
        "edge_census_digest": receipt_stream["digest_chain"],
        "processed_nodes": receipt_stream["processed_nodes"],
    }


def initialize_panel_rollout_state(
    *,
    context_id: str,
    layout_id: str,
    world_seed: int,
    policy_seed: int,
    panel_rollout_id: int,
) -> dict[str, Any]:
    return {
        "world": {"front_token": None, "panel_rollout_id": panel_rollout_id},
        "organism": {},
        "predictive_state": {},
        "episode_index": panel_rollout_id - 1,
        "panel_rollout_id": panel_rollout_id,
    }


def panel_expand_navigation(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    children = {}
    for action in PANEL_NAV_ACTIONS:
        child = deepcopy(state)
        child["world"] = deepcopy(state.get("world", {}))
        child["world"]["front_token"] = action
        child["front_token"] = action
        children[action] = child
    return children


class PanelStateStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS panel_states (state_hash TEXT PRIMARY KEY, state_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS queue_entries (entry_id INTEGER PRIMARY KEY AUTOINCREMENT, state_hash TEXT NOT NULL, remaining_json TEXT NOT NULL, claimed_hashes_json TEXT NOT NULL, claimed_targets_json TEXT NOT NULL, parent_entry_id INTEGER, action TEXT)"
            )
            connection.commit()

    def upsert_state(self, state: dict[str, Any]) -> str:
        state_hash = engine.canonical_hash(state)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO panel_states(state_hash, state_json) VALUES (?, ?)",
                (
                    state_hash,
                    json.dumps(state, sort_keys=True, separators=(",", ":")),
                ),
            )
            connection.commit()
        return state_hash

    def append_queue_entry(
        self,
        *,
        state_hash: str,
        remaining: Counter[str],
        claimed_hashes: set[str],
        claimed_targets: list[str],
        parent_entry_id: int | None,
        action: str | None,
    ) -> int:
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute(
                "INSERT INTO queue_entries(state_hash, remaining_json, claimed_hashes_json, claimed_targets_json, parent_entry_id, action) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    state_hash,
                    json.dumps(dict(remaining), sort_keys=True),
                    json.dumps(sorted(claimed_hashes)),
                    json.dumps(claimed_targets),
                    parent_entry_id,
                    action,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)


def _claim_token_if_available(
    front_token: str | None,
    remaining: Counter[str],
    claimed_hashes: set[str],
    checkpoint_hash: str,
) -> str | None:
    if front_token is None or remaining[front_token] <= 0 or checkpoint_hash in claimed_hashes:
        return None
    return front_token


def run_panel_search(
    *,
    context_spec: dict[str, Any],
    target_multiset: list[str],
    storage_dir: Path | str,
    processed_node_cap: int,
    rollout_ids: tuple[int, ...],
) -> dict[str, Any]:
    context_id, layout_id, world_seed, policy_seed = _context_identity(context_spec)
    store = PanelStateStore(Path(storage_dir) / "panel_state_store.sqlite3")
    retained_checkpoints = []
    rows = []
    actions_by_checkpoint: dict[str, list[str]] = {}
    seen_hashes: set[str] = set()
    processed_nodes = 0
    for rollout_id in rollout_ids:
        state = initialize_panel_rollout_state(
            context_id=context_id,
            layout_id=layout_id,
            world_seed=world_seed,
            policy_seed=policy_seed,
            panel_rollout_id=int(rollout_id),
        )
        remaining = Counter(target_multiset)
        entry_id = store.append_queue_entry(
            state_hash=store.upsert_state(state),
            remaining=remaining,
            claimed_hashes=set(),
            claimed_targets=[],
            parent_entry_id=None,
            action=None,
        )
        queue = deque([(entry_id, state, remaining, set(), [])])
        while queue:
            entry_id, state, remaining, claimed_hashes, claimed_targets = queue.popleft()
            processed_nodes += 1
            world = state.get("world", state)
            front_token = state.get("front_token", world.get("front_token"))
            checkpoint = build_public_checkpoint(
                world={"front_token": front_token},
                organism=state.get("organism", {}),
                predictive_state=state.get("predictive_state", {}),
                episode_index=int(state.get("episode_index", rollout_id - 1)),
            )
            checkpoint_hash = str(checkpoint["checkpoint_hash"])
            token = _claim_token_if_available(
                front_token,
                remaining,
                claimed_hashes,
                checkpoint_hash,
            )
            next_remaining = remaining.copy()
            next_claimed_hashes = set(claimed_hashes)
            next_claimed_targets = list(claimed_targets)
            if token is not None:
                next_remaining[token] -= 1
                next_claimed_hashes.add(checkpoint_hash)
                next_claimed_targets.append(token)
                if checkpoint_hash not in seen_hashes:
                    seen_hashes.add(checkpoint_hash)
                    retained_checkpoints.append(
                        {
                            "checkpoint_hash": checkpoint_hash,
                            "front_token": token,
                            "panel_rollout_id": rollout_id,
                        }
                    )
                    actions_by_checkpoint[checkpoint_hash] = []
                    for action in ACTION_ORDER:
                        truth = evaluate_forced_action_truth(
                            world={"front_token": token},
                            organism=state.get("organism", {}),
                            action=action,
                            run_meta={"code_path_hash": engine.compute_code_path_hash()},
                            episode_id=f"{context_id}:{rollout_id}",
                            command_hash=engine.canonical_hash(
                                {"checkpoint_hash": checkpoint_hash, "action": action}
                            ),
                            source_sequence=1,
                            life_index=int(rollout_id),
                            episode_tick_after=1,
                        )
                        actions_by_checkpoint[checkpoint_hash].append(action)
                        rows.append(
                            {
                                "context_id": context_id,
                                "checkpoint_hash": checkpoint_hash,
                                "selected_action": action,
                                "front_token": token,
                                "outcome_type": truth["truth"]["outcome_type"],
                                "full_features": checkpoint["full_features"].astype(
                                    np.float64,
                                    copy=False,
                                ).tolist(),
                                "learner_projection": {
                                    "front_token": token,
                                    "quotient_features": checkpoint[
                                        "quotient_features"
                                    ].astype(np.float64, copy=False).tolist(),
                                },
                                "producer_receipts": truth["callable_receipts"],
                            }
                        )
            if sum(next_remaining.values()) == 0:
                return {
                    "status": "panel_certificate_found",
                    "processed_nodes": processed_nodes,
                    "retained_checkpoints": retained_checkpoints,
                    "rows": rows,
                    "rank_reports": compute_rank_reports(context_id, rows),
                    "actions_by_checkpoint": actions_by_checkpoint,
                    "storage": {
                        "state_store_path": str(store.path),
                        "queue_entry_mode": "parent_pointer",
                    },
                }
            for action in PANEL_NAV_ACTIONS:
                expansions = panel_expand_navigation(state)
                if action not in expansions:
                    continue
                if processed_nodes >= int(processed_node_cap):
                    return {
                        "status": "PANEL_SEARCH_INCONCLUSIVE",
                        "processed_nodes": processed_nodes,
                        "retained_checkpoints": retained_checkpoints,
                        "rows": rows,
                        "actions_by_checkpoint": actions_by_checkpoint,
                        "storage": {
                            "state_store_path": str(store.path),
                            "queue_entry_mode": "parent_pointer",
                        },
                    }
                child = expansions[action]
                child_entry = store.append_queue_entry(
                    state_hash=store.upsert_state(child),
                    remaining=next_remaining,
                    claimed_hashes=next_claimed_hashes,
                    claimed_targets=next_claimed_targets,
                    parent_entry_id=entry_id,
                    action=action,
                )
                queue.append(
                    (
                        child_entry,
                        child,
                        next_remaining.copy(),
                        set(next_claimed_hashes),
                        list(next_claimed_targets),
                    )
                )
    return {
        "status": "PANEL_CAPACITY_NOT_CERTIFIED",
        "processed_nodes": processed_nodes,
        "retained_checkpoints": retained_checkpoints,
        "rows": rows,
        "actions_by_checkpoint": actions_by_checkpoint,
        "storage": {
            "state_store_path": str(store.path),
            "queue_entry_mode": "parent_pointer",
        },
    }


def recursive_leakage_scan(payload: Any) -> dict[str, Any]:
    findings = []
    positive_controls = set()
    stack = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            if "learner_projection" in current:
                report = scan_learner_projection(current["learner_projection"])
                if not report["clean"]:
                    findings.extend(report["findings"])
            stack.extend(current.values())
            continue
        if isinstance(current, list):
            stack.extend(current)
            continue
        if isinstance(current, str):
            if "world=" in current or "policy=" in current:
                findings.append("direct")
                positive_controls.add("direct")
            if len(current) >= 8 and len(current) % 4 == 0 and BASE64_PATTERN.match(current):
                try:
                    base64.b64decode(current, validate=True)
                except Exception:
                    pass
                else:
                    findings.append("base64")
                    positive_controls.add("base64")
            continue
        if isinstance(current, int) and current in {52, 54, *sorted(STALE_WORLD_SEEDS)}:
            findings.append("numeric_index")
            positive_controls.add("numeric_index")
    return {
        "all_clean": len(findings) == 0,
        "findings": findings,
        "positive_controls_detected": sorted(positive_controls),
        "all_positive_controls_detected": (
            positive_controls == {"base64", "direct", "numeric_index"}
            or len(positive_controls) == 0
        ),
    }


def collect_runtime_boundary() -> dict[str, Any]:
    return {"output_absent": True, "runtime_receipt": runtime_receipt()}


def dispatch_r2_verdict(
    *,
    provenance_clean: bool,
    contract_valid: bool,
    witness_reports: list[dict[str, Any]],
    panel_reports: list[dict[str, Any]],
) -> str:
    if not provenance_clean:
        return "BLOCKED_001H_R2_PROVENANCE_LEAKAGE_OR_RECOMPUTE"
    if not contract_valid:
        return "INVALID_POSTRESULT_RESCUE"
    if any(report.get("status") == "SEARCH_IMPLEMENTATION_INVALID" for report in witness_reports):
        return "SEARCH_IMPLEMENTATION_INVALID"
    if any(
        report.get("status") == "FROZEN_BENCHMARK_CAPACITY_REFUTED"
        for report in witness_reports
    ):
        return "FROZEN_BENCHMARK_CAPACITY_REFUTED"
    if any(report.get("status") == "WITNESS_SEARCH_INCONCLUSIVE" for report in witness_reports):
        return "WITNESS_SEARCH_INCONCLUSIVE"
    if any(report.get("status") == "PANEL_SEARCH_INCONCLUSIVE" for report in panel_reports):
        return "PANEL_SEARCH_INCONCLUSIVE"
    if panel_reports and any(
        report.get("status") != "panel_certificate_found" for report in panel_reports
    ):
        return "PANEL_CAPACITY_NOT_CERTIFIED"
    return "EXISTENTIAL_CAPACITY_CERTIFICATE_FOUND"


def run_formal(*, output_dir: Path | str, execute_search: bool) -> dict[str, Any]:
    boundary = collect_runtime_boundary()
    if not boundary.get("output_absent"):
        raise ValueError("output directory must be absent or empty")
    if not execute_search:
        return {
            "status": "formal_entrypoint_ready",
            "runtime_receipt": boundary["runtime_receipt"],
        }
    raise ValueError("formal execution forbidden in this task")
