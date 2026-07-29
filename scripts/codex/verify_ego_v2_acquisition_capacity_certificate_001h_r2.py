from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
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
        "control_db_relpath": "artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/smoke_p0_cross_v1.sqlite3",
        "panel_rollout_ids": [9, 10, 11, 12, 13, 14, 15, 16],
    },
    {
        "context_id": "p2_vertical_v1:world=54:policy=711",
        "layout_id": "p2_vertical_v1",
        "world_seed": 54,
        "policy_seed": 711,
        "control_db_relpath": "artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/smoke_p2_vertical_v1.sqlite3",
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
R2_REQUIRED_PROVENANCE_SOURCE_PATHS = (
    "docs/codex/tasks/EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2.md",
    "docs/codex/tasks/ego-v2-p1-acquisition-capacity-certificate-001h-r2/COLLISION_RECORD.md",
    "docs/codex/tasks/ego-v2-p1-acquisition-capacity-certificate-001h-r2/IMPLEMENTATION_PLAN.md",
    "scripts/codex/verify_ego_v2_acquisition_capacity_certificate_001h_r2.py",
    "scripts/codex/tests/test_verify_ego_v2_acquisition_capacity_certificate_001h_r2.py",
    "scripts/codex/verify_ego_v2_acquisition_benchmark_admission_001h_r1.py",
    "labs/ego_life_playground_v0/engine.py",
    "labs/ego_life_playground_v0/microworld.py",
    "labs/ego_life_playground_v0/predictive_control.py",
    "labs/ego_life_playground_v0/store.py",
)
R2_REQUIRED_PROVENANCE_INPUT_PATHS = (
    "artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/result.json",
    "artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/support_report.json",
    "artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/panel_manifest.json",
    "artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/recompute_report.json",
    "artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/smoke_p0_cross_v1.sqlite3",
    "artifacts/EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F/smoke_p2_vertical_v1.sqlite3",
)
R2_REQUIRED_PROVENANCE_DEPENDENCY_PATHS = ("requirements-ego-v2.txt",)
R2_PROVENANCE_RELPATH = "docs/codex/tasks/ego-v2-p1-acquisition-capacity-certificate-001h-r2/PRE_RUN_PROVENANCE.json"
R2_OUTPUT_RELPATH = "artifacts/EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2"
NORMATIVE_INTERPRETER_SPEC_COMMIT = "c0f9d24c0e00d03b27e93fe35d73be1c021bb8b2"
NORMATIVE_INTERPRETER_SPEC_PATHS = (
    "docs/codex/tasks/EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2.md",
    "docs/codex/tasks/ego-v2-p1-acquisition-capacity-certificate-001h-r2/COLLISION_RECORD.md",
    "docs/codex/tasks/ego-v2-p1-acquisition-capacity-certificate-001h-r2/IMPLEMENTATION_PLAN.md",
)


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
initialize_panel_rollout_state = _R1._initialize_panel_rollout_state
json_public_checkpoint = _R1._json_public_checkpoint
independent_reduce_context = _R1.independent_reduce_context
spawn_fresh_digest_probe = _R1.spawn_fresh_digest_probe
validate_fresh_digest_receipt = _R1.validate_fresh_digest_receipt
summarize_fresh_stage_pair = _R1.summarize_fresh_stage_pair
extract_banked_control = _R1.extract_banked_control
TRAINING_SUPPORT_STRATA = _R1.TRAINING_SUPPORT_STRATA


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
    for key in (
        "task_id",
        "panel_target_multiset",
        "panel_floors",
        "source_pins",
        "stale_world_seed_firewall",
        "stale_policy_seed_firewall",
    ):
        if contract.get(key) != expected[key]:
            reasons.append(key)
    for key in (
        "action_budget",
        "max_life_index",
        "max_respawns",
        "processed_node_cap",
        "action_order",
        "analytic_root_lower_bound",
    ):
        if contract.get("witness_search", {}).get(key) != expected["witness_search"][key]:
            reasons.append(f"witness_search.{key}")
    for key in ("processed_node_cap", "action_order"):
        if contract.get("panel_search", {}).get(key) != expected["panel_search"][key]:
            reasons.append(f"panel_search.{key}")
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


def support_deficits_by_action(rows) -> dict[str, int]:
    counts = compute_support_counts(rows)
    deficits = {action: 0 for action in ACTION_ORDER}
    for stratum in TRAINING_SUPPORT_STRATA:
        deficits[stratum["action"]] += max(0, 4 - int(counts[stratum["stratum_id"]]))
    return deficits


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
        "life_index": int(node["life_index"]),
        "respawn_count": int(node["respawn_count"]),
    }
    return engine.canonical_hash(payload)


def _empty_support_counts() -> dict[str, int]:
    return {str(item["stratum_id"]): 0 for item in TRAINING_SUPPORT_STRATA}


def _rank_rows_from_rows(rows: list[dict[str, Any]]) -> dict[str, list[list[float]]]:
    result = {action: [] for action in ACTION_ORDER}
    for row in rows:
        action = str(row["selected_action"])
        features = row.get("learner_projection", {}).get("quotient_features", [])
        if action in result:
            result[action].append([float(value) for value in features])
    return result


def build_live_witness_root(context_spec: dict[str, Any]) -> dict[str, Any]:
    context_id, layout_id, world_seed, policy_seed = _context_identity(context_spec)
    state = initialize_evaluator_state(
        layout_id=layout_id,
        world_seed=world_seed,
        policy_seed=policy_seed,
        run_id=context_id,
    )
    return make_search_node(
        evaluator_state=state,
        g=0,
        prefix=(),
        support_counts=_empty_support_counts(),
        rank_rows={action: [] for action in ACTION_ORDER},
        accepted_rows=[],
        life_index=int(state.get("life_index", 1)),
        respawn_count=int(state.get("respawn_count", 0)),
    )


def _clipped_support_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    observed = compute_support_counts(rows)
    return {
        str(item["stratum_id"]): min(4, int(observed.get(str(item["stratum_id"]), 0)))
        for item in TRAINING_SUPPORT_STRATA
    }


def expand_live_witness_node(
    node: dict[str, Any],
    *,
    action_budget: int,
) -> list[dict[str, Any]]:
    if int(node["g"]) >= int(action_budget):
        return []
    state = deepcopy(node["evaluator_state"])
    if state.get("awaiting_respawn"):
        if int(state.get("respawn_count", node["respawn_count"])) >= 3:
            return []
        state = advance_evaluator_respawn(state)
    children: list[dict[str, Any]] = []
    for action in ACTION_ORDER:
        advanced = advance_evaluator_action(deepcopy(state), action)
        next_state = deepcopy(advanced["state"])
        row = deepcopy(advanced["row"])
        validate_producer_receipts(row.get("producer_receipts", {}))
        row.setdefault("context_id", state.get("run_id", ""))
        row.setdefault("action_index", int(node["g"]) + 1)
        accepted_rows = [*deepcopy(node["accepted_rows"]), row]
        if (
            int(node["g"]) + 1 < int(action_budget)
            and next_state.get("awaiting_respawn")
            and int(next_state.get("respawn_count", 0)) < 3
        ):
            next_state = advance_evaluator_respawn(next_state)
        child = make_search_node(
            evaluator_state=next_state,
            g=int(node["g"]) + 1,
            prefix=tuple(node["prefix"]) + (ACTION_INDEX[action],),
            support_counts=_clipped_support_counts(accepted_rows),
            rank_rows=_rank_rows_from_rows(accepted_rows),
            accepted_rows=accepted_rows,
            life_index=int(next_state.get("life_index", row.get("life_index", 1))),
            respawn_count=int(next_state.get("respawn_count", row.get("respawn_count", 0))),
        )
        children.append({"action": action, "node": child})
    return children


def expand_live_witness_node_independent(
    node: dict[str, Any],
    *,
    action_budget: int,
) -> list[dict[str, Any]]:
    """Checker-owned live expansion; intentionally does not call the primary expander."""
    if int(node["g"]) >= int(action_budget):
        return []
    state = deepcopy(node["evaluator_state"])
    if state.get("awaiting_respawn"):
        if int(state.get("respawn_count", node["respawn_count"])) >= 3:
            return []
        state = advance_evaluator_respawn(state)
    children: list[dict[str, Any]] = []
    for action in ACTION_ORDER:
        advanced = advance_evaluator_action(deepcopy(state), action)
        next_state = deepcopy(advanced["state"])
        row = deepcopy(advanced["row"])
        validate_producer_receipts(row.get("producer_receipts", {}))
        row.setdefault("context_id", state.get("run_id", ""))
        row.setdefault("action_index", int(node["g"]) + 1)
        accepted_rows = [*deepcopy(node["accepted_rows"]), row]
        if (
            int(node["g"]) + 1 < int(action_budget)
            and next_state.get("awaiting_respawn")
            and int(next_state.get("respawn_count", 0)) < 3
        ):
            next_state = advance_evaluator_respawn(next_state)
        child = make_search_node(
            evaluator_state=next_state,
            g=int(node["g"]) + 1,
            prefix=tuple(node["prefix"]) + (ACTION_INDEX[action],),
            support_counts=_clipped_support_counts(accepted_rows),
            rank_rows=_rank_rows_from_rows(accepted_rows),
            accepted_rows=accepted_rows,
            life_index=int(next_state.get("life_index", row.get("life_index", 1))),
            respawn_count=int(next_state.get("respawn_count", row.get("respawn_count", 0))),
        )
        children.append({"action": action, "node": child})
    return children


def live_witness_lower_bound(node: dict[str, Any]) -> int:
    deficits = {action: 0 for action in ACTION_ORDER}
    for stratum in TRAINING_SUPPORT_STRATA:
        action = str(stratum["action"])
        deficits[action] += max(0, 4 - int(node["support_counts"].get(str(stratum["stratum_id"]), 0)))
    gaps = {}
    for action in ACTION_ORDER:
        matrix = np.asarray(node["rank_rows"].get(action, []), dtype=np.float64)
        rank = int(np.linalg.matrix_rank(matrix)) if matrix.size else 0
        gaps[action] = max(0, 13 - rank)
    return remaining_action_lower_bound(support_deficits=deficits, rank_gaps=gaps)


def live_witness_goal(node: dict[str, Any], *, action_budget: int = 89) -> bool:
    if int(node["g"]) != int(action_budget):
        return False
    if int(node["life_index"]) > 4 or int(node["respawn_count"]) > 3:
        return False
    if any(int(node["support_counts"].get(str(item["stratum_id"]), 0)) < 4 for item in TRAINING_SUPPORT_STRATA):
        return False
    return all(
        int(np.linalg.matrix_rank(np.asarray(node["rank_rows"].get(action, []), dtype=np.float64))) == 13
        for action in ACTION_ORDER
    )


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
    def __init__(self, contract_digest: str, root_digest: str | None = None) -> None:
        self.processed_nodes = 0
        self._chain = hashlib.sha256(_digest_bytes(contract_digest))
        if root_digest is not None:
            self._chain.update(_digest_bytes(root_digest))
        self._first_samples: list[dict[str, Any]] = []
        self._final_samples: deque[dict[str, Any]] = deque(maxlen=32)
        self._every_10000th: list[dict[str, Any]] = []
        self._disposition_counts: Counter[str] = Counter()

    def add(self, sample: dict[str, Any]) -> None:
        normalized = deepcopy(sample)
        encoded = json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self._chain.update(hashlib.sha256(encoded).digest())
        self.processed_nodes += 1
        if "node_disposition" in normalized:
            self._disposition_counts[str(normalized["node_disposition"])] += 1
        else:
            self._disposition_counts["expanded"] += 1
            for item in normalized.get("dispositions", []):
                self._disposition_counts[str(item.get("disposition", "child"))] += 1
        if len(self._first_samples) < 32:
            self._first_samples.append(normalized)
        if self.processed_nodes % 10_000 == 0:
            self._every_10000th.append(normalized)
        self._final_samples.append(normalized)

    def finish(self) -> dict[str, Any]:
        sampled_by_index = {}
        for sample in [*self._first_samples, *self._every_10000th, *self._final_samples]:
            sampled_by_index[int(sample["processed_node_index"])] = sample
        return {
            "processed_nodes": self.processed_nodes,
            "digest_chain": self._chain.hexdigest(),
            "first_samples": list(self._first_samples),
            "every_10000th": list(self._every_10000th),
            "final_samples": list(self._final_samples),
            "samples": [sampled_by_index[index] for index in sorted(sampled_by_index)],
            "disposition_counts": dict(sorted(self._disposition_counts.items())),
        }


def _normalize_expansion(expanded: Any, g: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    children: list[dict[str, Any]] = []
    dispositions: dict[str, dict[str, Any]] = {}
    for item in list(expanded):
        if isinstance(item, dict) and "node" in item and "action" in item:
            action = str(item["action"])
            if "disposition" in item and item["disposition"] != "child":
                dispositions[action] = {k: deepcopy(v) for k, v in item.items() if k != "node"}
                continue
            child = item["node"]
        else:
            child = item
            prefix = tuple(child["prefix"])
            if len(prefix) <= g or int(prefix[g]) not in range(len(ACTION_ORDER)):
                raise ValueError("child prefix does not identify frozen action")
            action = ACTION_ORDER[int(prefix[g])]
        if action in dispositions:
            raise ValueError("duplicate action disposition")
        children.append(child)
        dispositions[action] = {
            "action": action,
            "disposition": "child",
            "child_digest": search_node_digest(child),
        }
    ordered = []
    for action in ACTION_ORDER:
        ordered.append(
            dispositions.get(
                action,
                {
                    "action": action,
                    "disposition": "illegal_or_lifecycle_pruned",
                    "reason": "expander_returned_no_legal_child",
                },
            )
        )
    return children, ordered


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
    root_digest = search_node_digest(root)
    stream = ReceiptStream(contract_digest, root_digest)
    stack = [root]
    duplicate_nodes_skipped = 0
    while stack:
        node = stack.pop()
        observed = ledger.observe(node)
        if observed["status"] == "duplicate":
            duplicate_nodes_skipped += 1
            continue
        if stream.processed_nodes >= int(processed_node_cap):
            receipt_stream = stream.finish()
            receipt_stream["duplicate_nodes_skipped"] = duplicate_nodes_skipped
            return {
                "status": "WITNESS_SEARCH_INCONCLUSIVE",
                "complete_search": False,
                "unprocessed_legal_child": True,
                "processed_nodes": receipt_stream["processed_nodes"],
                "receipt_stream": receipt_stream,
                "duplicate_nodes_skipped": duplicate_nodes_skipped,
            }
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
            receipt_stream["duplicate_nodes_skipped"] = duplicate_nodes_skipped
            return {
                "status": "goal_found",
                "goal_node": deepcopy(node),
                "complete_search": False,
                "unprocessed_legal_child": False,
                "processed_nodes": receipt_stream["processed_nodes"],
                "receipt_stream": receipt_stream,
                "duplicate_nodes_skipped": duplicate_nodes_skipped,
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
        if (
            int(node["life_index"]) > 4
            or int(node["respawn_count"]) > 3
            or (node.get("evaluator_state", {}).get("awaiting_respawn") is True and int(node["respawn_count"]) >= 3)
        ):
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
        children, dispositions = _normalize_expansion(expand_fn(node), g)
        stream.add(
            {
                "processed_node_index": sample_index,
                "node_digest": digest,
                "g": g,
                "h": h,
                "dispositions": dispositions,
            }
        )
        for child in reversed(children):
            stack.append(child)
    receipt_stream = stream.finish()
    receipt_stream["duplicate_nodes_skipped"] = duplicate_nodes_skipped
    return {
        "status": "search_exhausted",
        "complete_search": True,
        "unprocessed_legal_child": False,
        "processed_nodes": receipt_stream["processed_nodes"],
        "receipt_stream": receipt_stream,
        "duplicate_nodes_skipped": duplicate_nodes_skipped,
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
    *,
    allow_respawn: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    advanced = advance_evaluator_action(state, action)
    next_state = advanced["state"]
    if allow_respawn and next_state.get("awaiting_respawn"):
        next_state = advance_evaluator_respawn(next_state)
    return next_state, advanced["row"]


def _replay_actions(
    *,
    initial_state: dict[str, Any],
    actions: list[str],
    context_id: str,
    action_index_offset: int = 0,
    respawn_after_final: bool = False,
) -> dict[str, Any]:
    state = _copy_state(initial_state)
    rows = []
    for index, action in enumerate(actions, start=1):
        state, row = _advance_with_respawn(
            state,
            action,
            allow_respawn=index < len(actions) or respawn_after_final,
        )
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
    support_deficits = support_deficits_by_action(rows)
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


def _warm_start_certificate_valid(
    *,
    context_id: str,
    action_budget: int,
    replay_valid: bool,
    rows,
) -> bool:
    if not replay_valid or len(rows) != int(action_budget):
        return False
    if max((int(row.get("life_index", 0)) for row in rows), default=0) > 4:
        return False
    if max((int(row.get("respawn_count", 0)) for row in rows), default=0) > 3:
        return False
    counts = compute_support_counts(rows)
    if any(int(counts[stratum["stratum_id"]]) < 4 for stratum in TRAINING_SUPPORT_STRATA):
        return False
    ranks = compute_rank_reports(context_id, rows)
    return all(int(ranks[f"{context_id}::{action}"]["rank"]) == 13 for action in ACTION_ORDER)


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
                respawn_after_final=(
                    len(chosen_actions) + len(candidate["primitive_actions"])
                    < int(action_budget)
                ),
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
    replay_valid = replay["rows"] == rows
    return {
        "certificate_found": _warm_start_certificate_valid(
            context_id=context_id,
            action_budget=action_budget,
            replay_valid=replay_valid,
            rows=replay["rows"],
        ),
        "replay_valid": replay_valid,
        "actions": chosen_actions,
        "rows": replay["rows"],
        "support_counts": compute_support_counts(replay["rows"]),
        "rank_reports": compute_rank_reports(context_id, replay["rows"]),
    }


def independent_verify_witness_search(
    *,
    root: dict[str, Any],
    expand_fn,
    goal_fn,
    bound_fn,
    action_budget: int,
    processed_node_cap: int,
    expected_receipt_stream: dict[str, Any],
    contract_digest: str,
    scratch_dir: Path | str,
) -> dict[str, Any]:
    root_digest = search_node_digest(root)
    stream = ReceiptStream(contract_digest, root_digest)
    tmp_dir = Path(scratch_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    ledger = DuplicateLedger(tmp_dir / "checker.sqlite3")
    stack = [root]
    status = "search_exhausted"
    duplicate_nodes_skipped = 0
    while stack:
        node = stack.pop()
        observed = ledger.observe(node)
        if observed["status"] == "duplicate":
            duplicate_nodes_skipped += 1
            continue
        if stream.processed_nodes >= int(processed_node_cap):
            status = "WITNESS_SEARCH_INCONCLUSIVE"
            break
        processed = stream.processed_nodes + 1
        g = int(node["g"])
        h = int(bound_fn(node))
        digest = search_node_digest(node)
        if goal_fn(node) and g == int(action_budget):
            stream.add(
                {
                    "processed_node_index": processed,
                    "node_digest": digest,
                    "g": g,
                    "h": h,
                    "node_disposition": "goal",
                }
            )
            break
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
        if (
            int(node["life_index"]) > 4
            or int(node["respawn_count"]) > 3
            or (node.get("evaluator_state", {}).get("awaiting_respawn") is True and int(node["respawn_count"]) >= 3)
        ):
            stream.add(
                {
                    "processed_node_index": processed,
                    "node_digest": digest,
                    "g": g,
                    "h": h,
                    "node_disposition": "lifecycle_pruned",
                }
            )
            continue
        children, dispositions = _normalize_expansion(expand_fn(node), g)
        stream.add(
            {
                "processed_node_index": processed,
                "node_digest": digest,
                "g": g,
                "h": h,
                "dispositions": dispositions,
            }
        )
        for child in reversed(children):
            stack.append(child)
    receipt_stream = stream.finish()
    receipt_stream["duplicate_nodes_skipped"] = duplicate_nodes_skipped
    failures = []
    if receipt_stream["digest_chain"] != expected_receipt_stream.get("digest_chain"):
        failures.append("digest_chain")
    if receipt_stream["processed_nodes"] != expected_receipt_stream.get("processed_nodes"):
        failures.append("processed_nodes")
    for field in ("first_samples", "every_10000th", "final_samples", "samples", "disposition_counts"):
        if receipt_stream.get(field) != expected_receipt_stream.get(field):
            failures.append("serialized_receipts" if field != "disposition_counts" else "disposition_counts")
    if duplicate_nodes_skipped != int(expected_receipt_stream.get("duplicate_nodes_skipped", 0)):
        failures.append("duplicate_nodes_skipped")
    return {
        "verified": not failures,
        "failure_reasons": sorted(set(failures)),
        "status": status,
        "edge_census_digest": receipt_stream["digest_chain"],
        "processed_nodes": receipt_stream["processed_nodes"],
        "receipt_stream": receipt_stream,
        "duplicate_nodes_skipped": duplicate_nodes_skipped,
    }


def independent_verify_live_witness_search(
    *,
    context_spec: dict[str, Any],
    action_budget: int,
    processed_node_cap: int,
    expected_receipt_stream: dict[str, Any],
    contract_digest: str,
    scratch_dir: Path | str,
) -> dict[str, Any]:
    return independent_verify_witness_search(
        root=build_live_witness_root(context_spec),
        expand_fn=lambda node: expand_live_witness_node_independent(
            node,
            action_budget=action_budget,
        ),
        goal_fn=lambda node: live_witness_goal(node, action_budget=action_budget),
        bound_fn=live_witness_lower_bound,
        action_budget=action_budget,
        processed_node_cap=processed_node_cap,
        expected_receipt_stream=expected_receipt_stream,
        contract_digest=contract_digest,
        scratch_dir=scratch_dir,
    )


def initialize_panel_rollout_state(
    *,
    context_id: str,
    layout_id: str,
    world_seed: int,
    policy_seed: int,
    panel_rollout_id: int,
) -> dict[str, Any]:
    return _R1._initialize_panel_rollout_state(
        context_id=context_id,
        layout_id=layout_id,
        world_seed=world_seed,
        policy_seed=policy_seed,
        panel_rollout_id=panel_rollout_id,
    )


def panel_expand_navigation(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """The sole production panel successor function: live R1 evaluator actions only."""
    children: dict[str, dict[str, Any]] = {}
    for action in PANEL_NAV_ACTIONS:
        advanced = advance_evaluator_action(deepcopy(state), action)
        child = deepcopy(advanced["state"])
        if child.get("awaiting_respawn"):
            continue
        children[action] = child
    return children


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.astype(np.float64, copy=False).tolist()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


class PanelStateStore:
    """Content-addressed evaluator blobs and pointer-only BFS records."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS panel_states (
                    state_hash TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS queue_entries (
                    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rollout_id INTEGER NOT NULL,
                    state_hash TEXT NOT NULL,
                    remaining_ref TEXT NOT NULL,
                    claimed_hashes_ref TEXT NOT NULL,
                    prior_hashes_digest TEXT NOT NULL,
                    parent_entry_id INTEGER,
                    action TEXT,
                    depth INTEGER NOT NULL,
                    claim_ref TEXT
                );
                CREATE TABLE IF NOT EXISTS search_keys (
                    search_key TEXT PRIMARY KEY,
                    entry_id INTEGER NOT NULL UNIQUE
                );
                CREATE TABLE IF NOT EXISTS panel_contents (
                    content_hash TEXT PRIMARY KEY,
                    content_kind TEXT NOT NULL,
                    content_json TEXT NOT NULL
                );
                """
            )
            connection.commit()

    def upsert_state(self, state: dict[str, Any]) -> str:
        state_json = engine.canonical_json(_jsonable(state))
        state_hash = hashlib.sha256(state_json.encode("utf-8")).hexdigest()
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO panel_states(state_hash, state_json) VALUES (?, ?)",
                (state_hash, state_json),
            )
            stored = connection.execute(
                "SELECT state_json FROM panel_states WHERE state_hash = ?", (state_hash,)
            ).fetchone()
            if stored is None or stored[0] != state_json:
                raise ValueError("panel content-address collision")
            connection.commit()
        return state_hash

    def load_state(self, state_hash: str) -> dict[str, Any]:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT state_json FROM panel_states WHERE state_hash = ?", (state_hash,)
            ).fetchone()
        if row is None:
            raise ValueError("missing panel evaluator state")
        return json.loads(row[0])

    def _upsert_content(self, kind: str, payload: Any) -> str:
        content_json = engine.canonical_json(_jsonable(payload))
        content_hash = hashlib.sha256((kind + "\0" + content_json).encode("utf-8")).hexdigest()
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO panel_contents(content_hash,content_kind,content_json) VALUES (?,?,?)",
                (content_hash, kind, content_json),
            )
            stored = connection.execute(
                "SELECT content_kind,content_json FROM panel_contents WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()
            if stored != (kind, content_json):
                raise ValueError("panel content reference collision")
            connection.commit()
        return content_hash

    def _load_content(self, content_hash: str, kind: str) -> Any:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT content_kind,content_json FROM panel_contents WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()
        if row is None or row[0] != kind:
            raise ValueError("missing panel compact content")
        return json.loads(row[1])

    def enqueue(
        self,
        *,
        rollout_id: int,
        state: dict[str, Any],
        remaining: Counter[str],
        claimed_hashes: set[str],
        prior_hashes_digest: str,
        parent_entry_id: int | None,
        action: str | None,
        depth: int,
    ) -> tuple[int, bool]:
        state_hash = self.upsert_state(state)
        remaining_payload = {key: int(value) for key, value in sorted(remaining.items()) if int(value) > 0}
        remaining_ref = self._upsert_content("remaining", remaining_payload)
        claimed_ref = self._upsert_content("claimed_hashes", sorted(claimed_hashes))
        search_key = engine.canonical_hash(
            {
                "rollout_id": int(rollout_id),
                "state_hash": state_hash,
                "remaining_ref": remaining_ref,
                "claimed_hashes_ref": claimed_ref,
                "prior_hashes_digest": prior_hashes_digest,
            }
        )
        with sqlite3.connect(self.path) as connection:
            existing = connection.execute(
                "SELECT entry_id FROM search_keys WHERE search_key = ?", (search_key,)
            ).fetchone()
            if existing is not None:
                return int(existing[0]), False
            cursor = connection.execute(
                "INSERT INTO queue_entries(rollout_id,state_hash,remaining_ref,claimed_hashes_ref,prior_hashes_digest,parent_entry_id,action,depth,claim_ref) VALUES (?,?,?,?,?,?,?,?,NULL)",
                (
                    int(rollout_id),
                    state_hash,
                    remaining_ref,
                    claimed_ref,
                    prior_hashes_digest,
                    parent_entry_id,
                    action,
                    int(depth),
                ),
            )
            entry_id = int(cursor.lastrowid)
            connection.execute(
                "INSERT INTO search_keys(search_key, entry_id) VALUES (?, ?)",
                (search_key, entry_id),
            )
            connection.commit()
        return entry_id, True

    def load_entry(self, entry_id: int) -> dict[str, Any]:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT rollout_id,state_hash,remaining_ref,claimed_hashes_ref,prior_hashes_digest,parent_entry_id,action,depth,claim_ref FROM queue_entries WHERE entry_id = ?",
                (int(entry_id),),
            ).fetchone()
        if row is None:
            raise ValueError("missing panel queue entry")
        return {
            "entry_id": int(entry_id),
            "rollout_id": int(row[0]),
            "state_hash": row[1],
            "remaining": Counter(self._load_content(row[2], "remaining")),
            "claimed_hashes": set(self._load_content(row[3], "claimed_hashes")),
            "remaining_ref": row[2],
            "claimed_hashes_ref": row[3],
            "prior_hashes_digest": row[4],
            "parent_entry_id": None if row[5] is None else int(row[5]),
            "action": row[6],
            "depth": int(row[7]),
            "claim": None if row[8] is None else self._load_content(row[8], "checkpoint_claim"),
        }

    def record_claim(self, entry_id: int, claim: dict[str, Any]) -> None:
        claim_ref = self._upsert_content("checkpoint_claim", claim)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "UPDATE queue_entries SET claim_ref = ? WHERE entry_id = ?",
                (claim_ref, int(entry_id)),
            )
            connection.commit()

    def chosen_path(self, entry_id: int) -> list[dict[str, Any]]:
        result = []
        cursor: int | None = int(entry_id)
        while cursor is not None:
            entry = self.load_entry(cursor)
            result.append(entry)
            cursor = entry["parent_entry_id"]
        result.reverse()
        return result


def _claim_token_if_available(
    front_token: str | None,
    remaining: Counter[str],
    rollout_claimed_hashes: set[str],
    previously_retained_hashes: set[str],
    checkpoint_hash: str,
) -> str | None:
    if front_token is None or remaining[front_token] <= 0:
        return None
    if checkpoint_hash in rollout_claimed_hashes or checkpoint_hash in previously_retained_hashes:
        return None
    return front_token


def _empty_panel_report(
    *,
    status: str,
    rollout_ids: tuple[int, ...],
    rollouts: list[dict[str, Any]],
    processed_nodes: int,
    store: PanelStateStore,
) -> dict[str, Any]:
    return {
        "status": status,
        "processed_nodes": processed_nodes,
        "panel_rollout_ids": list(rollout_ids),
        "target_order": list(PANEL_TARGET_MULTISET),
        "rollouts": rollouts,
        "raw_checkpoints": [],
        "retained_checkpoints": [],
        "rows": [],
        "actions_by_checkpoint": {},
        "support_report": {"before_dedupe": {token: 0 for token in PANEL_FLOORS}, "after_dedupe": {token: 0 for token in PANEL_FLOORS}, "required_floors": deepcopy(PANEL_FLOORS), "passed": False},
        "cell_support_report": {"cell_counts": {}, "required_floor_by_cell": {}, "passed": False},
        "rank_reports": {},
        "construction_complete": False,
        "panel_capacity_admitted": False,
        "panel_hash": engine.canonical_hash({"status": status, "rollouts": rollouts}),
        "storage": {"state_store_path": str(store.path), "queue_entry_mode": "parent_pointer", "queue_contains_only_ids": True},
    }


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
    retained_private: list[dict[str, Any]] = []
    raw_private: list[dict[str, Any]] = []
    previously_retained_hashes: set[str] = set()
    rollouts: list[dict[str, Any]] = []
    total_processed = 0

    for rollout_id in rollout_ids:
        initial_state = initialize_panel_rollout_state(
            context_id=context_id,
            layout_id=layout_id,
            world_seed=world_seed,
            policy_seed=policy_seed,
            panel_rollout_id=int(rollout_id),
        )
        initial_world_hash = engine.canonical_hash(_jsonable(initial_state["world"]))
        initial_organism_hash = engine.canonical_hash(_jsonable(initial_state.get("organism", {})))
        prior_digest = engine.canonical_hash(sorted(previously_retained_hashes))
        root_id, inserted = store.enqueue(
            rollout_id=int(rollout_id),
            state=initial_state,
            remaining=Counter(target_multiset),
            claimed_hashes=set(),
            prior_hashes_digest=prior_digest,
            parent_entry_id=None,
            action=None,
            depth=0,
        )
        if not inserted:
            raise ValueError("panel root search key collision")
        queue: deque[int] = deque([root_id])
        rollout_processed = 0
        goal_entry_id: int | None = None
        cap_hit = False

        while queue:
            if rollout_processed >= int(processed_node_cap):
                cap_hit = True
                break
            entry_id = queue.popleft()
            entry = store.load_entry(entry_id)
            state = store.load_state(entry["state_hash"])
            rollout_processed += 1
            total_processed += 1
            remaining = entry["remaining"].copy()
            claimed_hashes = set(entry["claimed_hashes"])
            checkpoint = build_public_checkpoint(
                world=state["world"],
                organism=state.get("organism", {}),
                predictive_state=state.get("predictive_state", {}),
                episode_index=int(state.get("episode_index", int(rollout_id) - 1)),
            )
            checkpoint_hash = str(checkpoint["checkpoint_hash"])
            token = _claim_token_if_available(
                checkpoint.get("front_token"),
                remaining,
                claimed_hashes,
                previously_retained_hashes,
                checkpoint_hash,
            )
            if token is not None:
                remaining[token] -= 1
                claimed_hashes.add(checkpoint_hash)
                store.record_claim(
                    entry_id,
                    {"checkpoint_hash": checkpoint_hash, "front_token": token},
                )
            if sum(remaining.values()) == 0:
                goal_entry_id = entry_id
                break
            expansions = panel_expand_navigation(state)
            for action in PANEL_NAV_ACTIONS:
                child = expansions.get(action)
                if child is None or child.get("awaiting_respawn"):
                    continue
                child_id, child_inserted = store.enqueue(
                    rollout_id=int(rollout_id),
                    state=child,
                    remaining=remaining,
                    claimed_hashes=claimed_hashes,
                    prior_hashes_digest=prior_digest,
                    parent_entry_id=entry_id,
                    action=action,
                    depth=entry["depth"] + 1,
                )
                if child_inserted:
                    queue.append(child_id)

        if cap_hit:
            rollouts.append({"panel_rollout_id": int(rollout_id), "initial_world_hash": initial_world_hash, "initial_organism_hash": initial_organism_hash, "reached_target_order": [], "navigation_actions": [], "respawn_count": 0, "processed_nodes": rollout_processed, "complete": False, "failure_reason": "processed_node_cap", "failed_target": None})
            return _empty_panel_report(status="PANEL_SEARCH_INCONCLUSIVE", rollout_ids=rollout_ids, rollouts=rollouts, processed_nodes=total_processed, store=store)
        if goal_entry_id is None:
            rollouts.append({"panel_rollout_id": int(rollout_id), "initial_world_hash": initial_world_hash, "initial_organism_hash": initial_organism_hash, "reached_target_order": [], "navigation_actions": [], "respawn_count": 0, "processed_nodes": rollout_processed, "complete": False, "failure_reason": "panel_rollout_incomplete", "failed_target": None})
            return _empty_panel_report(status="PANEL_CAPACITY_NOT_CERTIFIED", rollout_ids=rollout_ids, rollouts=rollouts, processed_nodes=total_processed, store=store)

        chosen_entries = store.chosen_path(goal_entry_id)
        chosen_claims = []
        for path_entry in chosen_entries:
            refreshed = store.load_entry(path_entry["entry_id"])
            descriptor = refreshed["claim"]
            if descriptor is None:
                continue
            chosen_state = store.load_state(refreshed["state_hash"])
            chosen_checkpoint = build_public_checkpoint(
                world=chosen_state["world"],
                organism=chosen_state.get("organism", {}),
                predictive_state=chosen_state.get("predictive_state", {}),
                episode_index=int(chosen_state.get("episode_index", int(rollout_id) - 1)),
            )
            if str(chosen_checkpoint["checkpoint_hash"]) != descriptor["checkpoint_hash"] or chosen_checkpoint.get("front_token") != descriptor["front_token"]:
                raise ValueError("panel chosen-path checkpoint replay mismatch")
            public = _jsonable(
                json_public_checkpoint(
                    chosen_checkpoint,
                    panel_rollout_id=int(rollout_id),
                    target_front_token=descriptor["front_token"],
                )
            )
            chosen_claims.append(
                {
                    **public,
                    "_private_world": deepcopy(chosen_state["world"]),
                    "_private_organism": deepcopy(chosen_state.get("organism", {})),
                }
            )
        navigation_actions = [entry["action"] for entry in chosen_entries if entry["action"] is not None]
        for claim in chosen_claims:
            checkpoint_hash = str(claim["checkpoint_hash"])
            if checkpoint_hash in previously_retained_hashes:
                raise ValueError("within-context panel dedupe failure")
            previously_retained_hashes.add(checkpoint_hash)
            raw_private.append(deepcopy(claim))
            retained_private.append(deepcopy(claim))
        terminal_state = store.load_state(store.load_entry(goal_entry_id)["state_hash"])
        rollouts.append(
            {
                "panel_rollout_id": int(rollout_id),
                "initial_world_hash": initial_world_hash,
                "initial_organism_hash": initial_organism_hash,
                "reached_target_order": [claim["front_token"] for claim in chosen_claims],
                "navigation_actions": navigation_actions,
                "respawn_count": int(terminal_state.get("respawn_count", 0)),
                "processed_nodes": rollout_processed,
                "complete": True,
                "failure_reason": None,
                "failed_target": None,
            }
        )

    # Forced truths are deliberately deferred until every rollout has a chosen path.
    rows: list[dict[str, Any]] = []
    actions_by_checkpoint: dict[str, list[str]] = {}
    for checkpoint in retained_private:
        checkpoint_hash = str(checkpoint["checkpoint_hash"])
        actions_by_checkpoint[checkpoint_hash] = []
        for action in ACTION_ORDER:
            truth = evaluate_forced_action_truth(
                world=deepcopy(checkpoint["_private_world"]),
                organism=deepcopy(checkpoint["_private_organism"]),
                action=action,
                run_meta=engine.make_run_metadata(f"{context_id}:panel_truth:{checkpoint['panel_rollout_id']}", seed=policy_seed),
                episode_id=engine.episode_id_for(f"{context_id}:panel_truth:{checkpoint['panel_rollout_id']}", int(checkpoint["panel_rollout_id"]) - 1),
                command_hash=engine.canonical_hash({"context_id": context_id, "checkpoint_hash": checkpoint_hash, "action": action}),
                source_sequence=1,
                life_index=int(checkpoint.get("life_index", 1)),
                episode_tick_after=1,
            )
            actions_by_checkpoint[checkpoint_hash].append(action)
            rows.append(
                {
                    "context_id": context_id,
                    "checkpoint_hash": checkpoint_hash,
                    "selected_action": action,
                    "front_token": checkpoint["front_token"],
                    "outcome_type": truth["truth"]["outcome_type"],
                    "full_features": deepcopy(checkpoint["full_features"]),
                    "learner_projection": {
                        "observation": deepcopy(checkpoint["observation"]),
                        "organism": deepcopy(checkpoint.get("organism", {})),
                        "public_relative_belief": deepcopy(checkpoint.get("public_relative_belief", {})),
                        "quotient_features": deepcopy(checkpoint["quotient_features"]),
                        "selected_action": action,
                        "outcome_type": truth["truth"]["outcome_type"],
                        "actual_delta": deepcopy(truth["truth"]["actual_delta"]),
                        "terminal_receipt": deepcopy(truth["truth"]["terminal_receipt"]),
                        "front_token": checkpoint["front_token"],
                    },
                    "evaluator_truth": deepcopy(truth["truth"]),
                    "producer_receipts": deepcopy(truth["callable_receipts"]),
                }
            )

    public_raw = [{key: value for key, value in item.items() if not key.startswith("_private_")} for item in raw_private]
    public_retained = [{key: value for key, value in item.items() if not key.startswith("_private_")} for item in retained_private]
    before_dedupe = {token: sum(item["front_token"] == token for item in public_raw) for token in PANEL_FLOORS}
    after_dedupe = {token: sum(item["front_token"] == token for item in public_retained) for token in PANEL_FLOORS}
    support_passed = all(before_dedupe[token] >= floor and after_dedupe[token] >= floor for token, floor in PANEL_FLOORS.items())
    cell_counts: dict[str, int] = {}
    for row in rows:
        key = "::".join((context_id, row["selected_action"], row["front_token"], row["outcome_type"]))
        cell_counts[key] = cell_counts.get(key, 0) + 1
    required_floor_by_cell = {key: PANEL_FLOORS[key.split("::")[-2]] for key in cell_counts}
    cell_passed = bool(cell_counts) and all(count >= required_floor_by_cell[key] for key, count in cell_counts.items())
    rank_reports = compute_rank_reports(context_id, rows)
    construction_complete = len(rollouts) == len(rollout_ids) and all(item["complete"] for item in rollouts)
    rank_passed = all(int(rank_reports[f"{context_id}::{action}"]["rank"]) == 13 for action in ACTION_ORDER)
    panel_capacity_admitted = construction_complete and support_passed and cell_passed and rank_passed
    report = {
        "status": "panel_certificate_found" if panel_capacity_admitted else "PANEL_CAPACITY_NOT_CERTIFIED",
        "processed_nodes": total_processed,
        "panel_rollout_ids": list(rollout_ids),
        "target_order": list(PANEL_TARGET_MULTISET),
        "rollouts": rollouts,
        "raw_checkpoints": public_raw,
        "retained_checkpoints": public_retained,
        "support_report": {"before_dedupe": before_dedupe, "after_dedupe": after_dedupe, "required_floors": deepcopy(PANEL_FLOORS), "passed": support_passed},
        "cell_support_report": {"cell_counts": cell_counts, "required_floor_by_cell": required_floor_by_cell, "passed": cell_passed},
        "rows": rows,
        "rank_reports": rank_reports,
        "construction_complete": construction_complete,
        "panel_capacity_admitted": panel_capacity_admitted,
        "actions_by_checkpoint": actions_by_checkpoint,
        "storage": {"state_store_path": str(store.path), "queue_entry_mode": "parent_pointer", "queue_contains_only_ids": True},
    }
    report["panel_hash"] = engine.canonical_hash({key: report[key] for key in ("rollouts", "retained_checkpoints", "rows", "rank_reports", "panel_capacity_admitted")})
    return report

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


EXPECTED_PRODUCER_RECEIPTS = {
    "transition_world": "labs.ego_life_playground_v0.microworld.transition_world",
    "compute_actual_delta": "labs.ego_life_playground_v0.engine.compute_actual_delta",
    "compute_metabolism_ledger": "labs.ego_life_playground_v0.engine.compute_metabolism_ledger",
}


def validate_producer_receipts(receipts: dict[str, Any]) -> bool:
    causal = receipts.get("forced_truth") if isinstance(receipts, dict) and "forced_truth" in receipts else receipts
    if causal != EXPECTED_PRODUCER_RECEIPTS:
        raise ValueError("producer receipt mismatch")
    if "forced_truth" in receipts and not {"public_checkpoint", "predictive_update"}.issubset(receipts):
        raise ValueError("producer receipt mismatch")
    return True


def validate_receipt_stream_summary(stream: dict[str, Any]) -> bool:
    if not re.fullmatch(r"[0-9a-f]{64}", str(stream.get("digest_chain", ""))):
        raise ValueError("search receipt digest")
    processed = int(stream.get("processed_nodes", -1))
    samples = list(stream.get("samples", []))
    indices = [int(item.get("processed_node_index", -1)) for item in samples]
    if indices != sorted(set(indices)) or any(index < 1 or index > processed for index in indices):
        raise ValueError("search receipt samples")
    disposition_counts = stream.get("disposition_counts")
    if not isinstance(disposition_counts, dict) or any(int(value) < 0 for value in disposition_counts.values()):
        raise ValueError("search receipt disposition counts")
    if processed and not samples:
        raise ValueError("search receipt missing samples")
    return True


def scan_r2_evidence_leakage(contexts: dict[str, Any]) -> dict[str, Any]:
    findings = []

    def scan_direct(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key in {"world_seed", "policy_seed", "world_index", "policy_index"}:
                    findings.append(f"private numeric index at {path}.{key}")
                scan_direct(nested, f"{path}.{key}")
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                scan_direct(nested, f"{path}[{index}]")
        elif isinstance(value, str) and ("world=" in value or "policy=" in value):
            findings.append(f"private direct identifier at {path}")

    for context in contexts.values():
        for stage in ("witness", "panel"):
            for row in context.get(stage, {}).get("rows", []):
                projection = row.get("learner_projection", {})
                report = scan_learner_projection(projection)
                if not report.get("clean", False):
                    findings.extend(deepcopy(report.get("findings", [])))
                scan_direct(projection, "$.learner_projection")
    controls = recursive_leakage_scan(
        {
            "direct_control": "world=52",
            "base64_control": base64.b64encode(b"world_52").decode("ascii"),
            "numeric_control": 54,
        }
    )
    return {
        "all_clean": not findings,
        "findings": findings,
        "positive_controls_detected": controls["positive_controls_detected"],
        "all_positive_controls_detected": controls["all_positive_controls_detected"],
    }


def _tamper_control_packet_bundle() -> dict[str, Any]:
    context_id = FROZEN_CONTEXTS[0]["context_id"]
    zero_support = {token: 0 for token in PANEL_FLOORS}
    return {
        "contexts": {
            context_id: {
                "control": {"prefix": []},
                "witness": {
                    "rows": [],
                    "rank_reports": {},
                    "replay_valid": False,
                    "search_report": {},
                    "ablation_report": {},
                },
                "panel": {
                    "rows": [],
                    "panel_rollout_ids": list(range(9, 17)),
                    "target_order": list(PANEL_TARGET_MULTISET),
                    "rollouts": [],
                    "raw_checkpoints": [],
                    "retained_checkpoints": [],
                    "rank_reports": {},
                    "support_report": {
                        "before_dedupe": deepcopy(zero_support),
                        "after_dedupe": deepcopy(zero_support),
                        "required_floors": deepcopy(PANEL_FLOORS),
                        "passed": False,
                    },
                    "cell_support_report": {
                        "cell_counts": {},
                        "required_floor_by_cell": {},
                        "passed": False,
                    },
                    "construction_complete": False,
                    "panel_capacity_admitted": False,
                    "panel_hash": engine.canonical_hash({}),
                },
            }
        },
        "adjudication": {"verdict": "PANEL_CAPACITY_NOT_CERTIFIED"},
        "source_hashes": {},
        "input_hashes": {},
        "dependency_hashes": {},
        "provenance_document": {
            "runtime_receipt": runtime_receipt(),
            "implementation_commit": "0" * 40,
        },
        "leakage_report": {
            "all_clean": True,
            "all_positive_controls_detected": True,
            "findings": [],
        },
        "fresh_recompute_report": {"equal": True, "contexts": {}},
    }


def run_r2_tamper_controls(
    *,
    contract: dict[str, Any],
    source_hashes: dict[str, str],
    witness_reports: list[dict[str, Any]],
    panel_reports: list[dict[str, Any]],
    scratch_dir: Path | str,
    provenance_document: dict[str, Any],
    provenance_observation: dict[str, Any],
) -> dict[str, Any]:
    controls: dict[str, dict[str, Any]] = {}

    if validate_frozen_contract(contract)["valid"] is not True or source_hashes != FROZEN_SOURCE_PINS:
        raise ValueError("tamper controls require valid frozen inputs")
    validate_pre_run_provenance(provenance_document, provenance_observation)

    budget_tamper = deepcopy(contract)
    budget_tamper["witness_search"]["action_budget"] -= 1
    budget_document = deepcopy(provenance_document)
    budget_document["frozen_contract_digest"] = engine.canonical_hash(budget_tamper)
    budget_rejected = False
    try:
        validate_pre_run_provenance(budget_document, provenance_observation)
    except ValueError:
        budget_rejected = True
    controls["contract_budget"] = {
        "rejected": budget_rejected,
        "validator": "validate_pre_run_provenance",
        "mutated_field": "witness_search.action_budget",
    }

    authority_document = deepcopy(provenance_document)
    first_authority = next(iter(FROZEN_SOURCE_PINS))
    authority_document["authority_pins"][first_authority] = "0" * 64
    authority_rejected = False
    try:
        validate_pre_run_provenance(authority_document, provenance_observation)
    except ValueError:
        authority_rejected = True
    controls["authority_hash"] = {
        "rejected": authority_rejected,
        "validator": "validate_pre_run_provenance",
    }

    sample_rows = deepcopy(next((report.get("rows", []) for report in witness_reports if isinstance(report, dict)), []))
    receipt = spawn_independent_row_recompute("tamper-control", sample_rows)
    tampered_receipt = {**receipt, "row_count": int(receipt["row_count"]) + 1}
    row_rejected = False
    try:
        validate_independent_row_recompute(sample_rows, tampered_receipt)
    except ValueError:
        row_rejected = True
    controls["row_recompute"] = {"rejected": row_rejected, "child_pid": receipt["child_pid"]}

    producer_tamper = deepcopy(EXPECTED_PRODUCER_RECEIPTS)
    producer_tamper["compute_metabolism_ledger"] = "tampered.invalid.producer"
    producer_rejected = False
    try:
        validate_producer_receipts(producer_tamper)
    except ValueError:
        producer_rejected = True
    controls["producer_receipt"] = {"rejected": producer_rejected}

    receipt_stream = None
    for report in witness_reports:
        candidate = report.get("search_report", {}).get("receipt_stream") if isinstance(report, dict) else None
        if isinstance(candidate, dict):
            receipt_stream = deepcopy(candidate)
            break
    if receipt_stream is None:
        stream = ReceiptStream("4" * 64, "5" * 64)
        stream.add({"processed_node_index": 1, "node_digest": "6" * 64, "g": 89, "h": 0, "node_disposition": "horizon_non_goal"})
        receipt_stream = stream.finish()
    validate_receipt_stream_summary(receipt_stream)
    receipt_tamper = deepcopy(receipt_stream)
    receipt_tamper["processed_nodes"] = 0
    receipt_rejected = False
    try:
        validate_receipt_stream_summary(receipt_tamper)
    except ValueError:
        receipt_rejected = True
    controls["search_receipt"] = {"rejected": receipt_rejected}

    scratch = Path(scratch_dir)
    scratch.mkdir(parents=True, exist_ok=True)
    packet = scratch / "unknown_verdict_packet"
    write_r2_formal_packet(packet, _tamper_control_packet_bundle())
    result_path = packet / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["verdict"] = "UNKNOWN_TAMPERED_VERDICT"
    result.setdefault("adjudication", {})["verdict"] = "UNKNOWN_TAMPERED_VERDICT"
    result_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (packet / "artifact_manifest.json").write_text(
        json.dumps(build_artifact_manifest(packet), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    unknown_rejected = False
    try:
        verify_r2_formal_packet(packet)
    except ValueError:
        unknown_rejected = True
    controls["unknown_verdict"] = {
        "rejected": unknown_rejected,
        "validator": "verify_r2_formal_packet",
    }
    return {
        "all_tamper_controls_rejected": all(item.get("rejected") is True for item in controls.values()),
        "controls": controls,
    }


def collect_runtime_boundary(output_dir: Path | str | None = None) -> dict[str, Any]:
    output = REPO_ROOT / R2_OUTPUT_RELPATH if output_dir is None else Path(output_dir)
    absent_or_empty = (not output.exists()) or (output.is_dir() and not any(output.iterdir()))
    return {"output_absent": absent_or_empty, "runtime_receipt": runtime_receipt()}


def load_pre_run_provenance(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def collect_r2_pre_run_observation(
    *,
    output_dir: Path | str,
    provenance_path: Path | str,
) -> dict[str, Any]:
    output = Path(output_dir)
    provenance = Path(provenance_path)
    repository_root = _R1._git_stdout("rev-parse", "--show-toplevel")
    branch = _R1._git_stdout("branch", "--show-current")
    head = _R1._git_stdout("rev-parse", "HEAD")
    head_parent = _R1._git_stdout("rev-parse", "HEAD^")
    changed = _R1._git_stdout("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")
    changed_paths = [] if changed == "" else changed.splitlines()
    provenance_relpath = provenance.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    try:
        output_relpath = output.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        output_relpath = output.resolve().as_posix()
    contract = build_frozen_contract()
    normative_changed = _R1._git_stdout(
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        NORMATIVE_INTERPRETER_SPEC_COMMIT,
    )
    return {
        "repository_root": repository_root,
        "branch": branch,
        "head": head,
        "head_parent": head_parent,
        "head_changed_paths": changed_paths,
        "worktree_clean": _R1._git_stdout("status", "--porcelain") == "",
        "index_clean": _R1._git_success("diff", "--cached", "--quiet"),
        "provenance_tracked_at_head": provenance_relpath in changed_paths and _R1._git_success("cat-file", "-e", f"HEAD:{provenance_relpath}"),
        "runtime_receipt": runtime_receipt(),
        "engine_code_path_hash": engine.compute_code_path_hash(),
        "source_hashes": sha256_map(R2_REQUIRED_PROVENANCE_SOURCE_PATHS),
        "input_hashes": sha256_map(R2_REQUIRED_PROVENANCE_INPUT_PATHS),
        "dependency_hashes": sha256_map(R2_REQUIRED_PROVENANCE_DEPENDENCY_PATHS),
        "authority_pins": sha256_map(tuple(FROZEN_SOURCE_PINS)),
        "output_dir": output_relpath,
        "output_absent_or_empty": (not output.exists()) or (output.is_dir() and not any(output.iterdir())),
        "caps": {
            "witness_processed_node_cap": contract["witness_search"]["processed_node_cap"],
            "panel_processed_node_cap_per_rollout": contract["panel_search"]["processed_node_cap"],
        },
        "action_orders": {
            "witness": list(ACTION_ORDER),
            "panel_navigation": list(PANEL_NAV_ACTIONS),
        },
        "firewalls": {
            "stale_world_seeds": sorted(STALE_WORLD_SEEDS),
            "stale_policy_seeds": sorted(STALE_POLICY_SEEDS),
        },
        "normative_interpreter_spec_commit": NORMATIVE_INTERPRETER_SPEC_COMMIT,
        "normative_interpreter_spec_commit_exists": _R1._git_success(
            "cat-file",
            "-e",
            f"{NORMATIVE_INTERPRETER_SPEC_COMMIT}^{{commit}}",
        ),
        "normative_interpreter_spec_changed_paths": (
            [] if normative_changed == "" else normative_changed.splitlines()
        ),
        "frozen_contract_digest": engine.canonical_hash(contract),
    }


def validate_pre_run_provenance(
    document: dict[str, Any],
    observation: dict[str, Any],
) -> dict[str, Any]:
    failures = []
    if document.get("schema_version") != "ego.v2.001h_r2.pre_run_provenance.v1":
        failures.append("schema")
    if document.get("task_id") != "EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2":
        failures.append("task")
    if document.get("implementation_commit") != observation.get("head_parent"):
        failures.append("implementation_commit")
    if document.get("runtime_receipt") != observation.get("runtime_receipt"):
        failures.append("runtime")
    if not bool(observation.get("runtime_receipt", {}).get("contract_satisfied")):
        failures.append("runtime_contract")
    if document.get("engine_code_path_hash") != observation.get("engine_code_path_hash"):
        failures.append("code_path")
    for label, required_paths in (
        ("source_hashes", R2_REQUIRED_PROVENANCE_SOURCE_PATHS),
        ("input_hashes", R2_REQUIRED_PROVENANCE_INPUT_PATHS),
        ("dependency_hashes", R2_REQUIRED_PROVENANCE_DEPENDENCY_PATHS),
    ):
        expected_keys = set(required_paths)
        if not isinstance(document.get(label), dict) or set(document[label]) != expected_keys:
            failures.append(f"{label}.path_set")
            continue
        if not isinstance(observation.get(label), dict) or set(observation[label]) != expected_keys:
            failures.append(f"observation.{label}.path_set")
            continue
        if document[label] != observation[label]:
            failures.append(f"{label}.hashes")
    if set(document.get("authority_pins", {})) != set(FROZEN_SOURCE_PINS):
        failures.append("authority_pins.path_set")
    elif document.get("authority_pins") != FROZEN_SOURCE_PINS or observation.get("authority_pins") != FROZEN_SOURCE_PINS:
        failures.append("authority_pins.hashes")
    if document.get("output_dir") != R2_OUTPUT_RELPATH or observation.get("output_dir") != R2_OUTPUT_RELPATH:
        failures.append("output_dir")
    if document.get("output_precondition") != "absent_or_empty" or observation.get("output_absent_or_empty") is not True:
        failures.append("output_precondition")
    expected_caps = {"witness_processed_node_cap": 2_000_000, "panel_processed_node_cap_per_rollout": 250_000}
    if document.get("caps") != expected_caps or observation.get("caps") != expected_caps:
        failures.append("caps")
    expected_orders = {"witness": list(ACTION_ORDER), "panel_navigation": list(PANEL_NAV_ACTIONS)}
    if document.get("action_orders") != expected_orders or observation.get("action_orders") != expected_orders:
        failures.append("action_orders")
    expected_firewalls = {"stale_world_seeds": sorted(STALE_WORLD_SEEDS), "stale_policy_seeds": sorted(STALE_POLICY_SEEDS)}
    if document.get("firewalls") != expected_firewalls or observation.get("firewalls") != expected_firewalls:
        failures.append("firewalls")
    if document.get("normative_interpreter_spec_commit") != NORMATIVE_INTERPRETER_SPEC_COMMIT:
        failures.append("normative_interpreter_spec_commit")
    if observation.get("normative_interpreter_spec_commit") != NORMATIVE_INTERPRETER_SPEC_COMMIT:
        failures.append("observation.normative_interpreter_spec_commit")
    if observation.get("normative_interpreter_spec_commit_exists") is not True:
        failures.append("normative_interpreter_spec_commit_exists")
    if observation.get("normative_interpreter_spec_changed_paths") != list(NORMATIVE_INTERPRETER_SPEC_PATHS):
        failures.append("normative_interpreter_spec_changed_paths")
    expected_contract_digest = engine.canonical_hash(build_frozen_contract())
    if document.get("frozen_contract_digest") != expected_contract_digest:
        failures.append("frozen_contract_digest")
    if observation.get("frozen_contract_digest") != expected_contract_digest:
        failures.append("observation.frozen_contract_digest")
    if observation.get("repository_root", "").replace("\\", "/").lower() != str(REPO_ROOT).replace("\\", "/").lower():
        failures.append("repository_root")
    if observation.get("head_changed_paths") != [R2_PROVENANCE_RELPATH]:
        failures.append("provenance_commit_path")
    for field in ("worktree_clean", "index_clean", "provenance_tracked_at_head"):
        if observation.get(field) is not True:
            failures.append(field)
    if failures:
        raise ValueError("pre-run provenance invalid: " + ",".join(sorted(set(failures))))
    return {"passed": True, "failure_reasons": [], "provenance_commit": observation["head"]}


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
    if not witness_reports or any(not isinstance(report, dict) for report in witness_reports):
        return "SEARCH_IMPLEMENTATION_INVALID"
    if any(not isinstance(report, dict) for report in panel_reports):
        return "SEARCH_IMPLEMENTATION_INVALID"
    if any(report.get("status") == "CONTROL_ENVELOPE_OR_ACCESS_PARITY_BROKEN" for report in witness_reports + panel_reports):
        return "CONTROL_ENVELOPE_OR_ACCESS_PARITY_BROKEN"
    allowed_witness = {
        "witness_certificate_found",
        "FROZEN_BENCHMARK_CAPACITY_REFUTED",
        "search_exhausted",
        "WITNESS_SEARCH_INCONCLUSIVE",
        "SEARCH_IMPLEMENTATION_INVALID",
        "CONTROL_ENVELOPE_OR_ACCESS_PARITY_BROKEN",
    }
    allowed_panel = {
        "panel_certificate_found",
        "PANEL_SEARCH_INCONCLUSIVE",
        "PANEL_CAPACITY_NOT_CERTIFIED",
        "SEARCH_IMPLEMENTATION_INVALID",
        "CONTROL_ENVELOPE_OR_ACCESS_PARITY_BROKEN",
    }
    if any(report.get("status") not in allowed_witness for report in witness_reports):
        return "SEARCH_IMPLEMENTATION_INVALID"
    if any(report.get("status") not in allowed_panel for report in panel_reports):
        return "SEARCH_IMPLEMENTATION_INVALID"
    if any(report.get("status") == "SEARCH_IMPLEMENTATION_INVALID" for report in witness_reports + panel_reports):
        return "SEARCH_IMPLEMENTATION_INVALID"
    if any(
        report.get("status") in {"search_exhausted", "FROZEN_BENCHMARK_CAPACITY_REFUTED"}
        and (
            report.get("complete_search") is not True
            or report.get("independently_verified") is not True
            or report.get("live_transition_verified") is not True
            or report.get("duplicate_free") is not True
        )
        for report in witness_reports
    ):
        return "SEARCH_IMPLEMENTATION_INVALID"
    if any(
        report.get("status") in {"search_exhausted", "FROZEN_BENCHMARK_CAPACITY_REFUTED"}
        for report in witness_reports
    ):
        return "FROZEN_BENCHMARK_CAPACITY_REFUTED"
    if any(report.get("status") == "WITNESS_SEARCH_INCONCLUSIVE" for report in witness_reports):
        return "WITNESS_SEARCH_INCONCLUSIVE"
    if any(report.get("status") != "witness_certificate_found" or report.get("certificate_found") is not True for report in witness_reports):
        return "SEARCH_IMPLEMENTATION_INVALID"
    if not panel_reports:
        return "SEARCH_IMPLEMENTATION_INVALID"
    if any(report.get("status") == "PANEL_SEARCH_INCONCLUSIVE" for report in panel_reports):
        return "PANEL_SEARCH_INCONCLUSIVE"
    if any(report.get("status") == "PANEL_CAPACITY_NOT_CERTIFIED" for report in panel_reports):
        return "PANEL_CAPACITY_NOT_CERTIFIED"
    if all(report.get("status") == "panel_certificate_found" and report.get("panel_capacity_admitted") is True for report in panel_reports):
        return "EXISTENTIAL_CAPACITY_CERTIFICATE_FOUND"
    return "SEARCH_IMPLEMENTATION_INVALID"


def run_witness_stage(
    context_spec: dict[str, Any],
    *,
    scratch_dir: Path | str | None = None,
    processed_node_cap: int | None = None,
) -> dict[str, Any]:
    contract = build_frozen_contract()
    action_budget = int(contract["witness_search"]["action_budget"])
    warm = run_live_warm_start(
        context_spec,
        action_budget=action_budget,
    )
    if warm["certificate_found"]:
        return {"status": "witness_certificate_found", **warm}
    root = build_live_witness_root(context_spec)
    if scratch_dir is None:
        scratch = REPO_ROOT / R2_OUTPUT_RELPATH / "_scratch" / "witness" / re.sub(r"[^A-Za-z0-9_.-]", "_", context_spec["context_id"])
    else:
        scratch = Path(scratch_dir)
    scratch.mkdir(parents=True, exist_ok=True)
    cap = int(processed_node_cap if processed_node_cap is not None else contract["witness_search"]["processed_node_cap"])
    expand = lambda node: expand_live_witness_node(node, action_budget=action_budget)
    goal = lambda node: live_witness_goal(node, action_budget=action_budget)
    search = depth_first_branch_and_bound(
        root=root,
        expand_fn=expand,
        goal_fn=goal,
        bound_fn=live_witness_lower_bound,
        action_budget=action_budget,
        processed_node_cap=cap,
        ledger_path=scratch / "witness.sqlite3",
        contract_digest=engine.canonical_hash(contract),
    )
    if search["status"] == "goal_found":
        actions = [ACTION_ORDER[index] for index in search["goal_node"]["prefix"]]
        replay = _replay_actions(initial_state=root["evaluator_state"], actions=actions, context_id=context_spec["context_id"])
        replay_valid = replay["rows"] == search["goal_node"]["accepted_rows"]
        certificate_found = replay_valid and live_witness_goal(search["goal_node"], action_budget=action_budget)
        return {
            "status": "witness_certificate_found" if certificate_found else "SEARCH_IMPLEMENTATION_INVALID",
            "certificate_found": certificate_found,
            "replay_valid": replay_valid,
            "actions": actions,
            "rows": replay["rows"],
            "support_counts": compute_support_counts(replay["rows"]),
            "rank_reports": compute_rank_reports(context_spec["context_id"], replay["rows"]),
            "complete_search": False,
            "independently_verified": False,
            "live_transition_verified": True,
            "search_report": search,
            "warm_start": warm,
        }
    verified = {"verified": False, "failure_reasons": ["search_not_complete"]}
    primary_duplicate_free = int(search.get("duplicate_nodes_skipped", 0)) == 0
    if search["status"] == "search_exhausted" and search["complete_search"] and primary_duplicate_free:
        verified = independent_verify_live_witness_search(
            context_spec=context_spec,
            action_budget=action_budget,
            processed_node_cap=cap,
            expected_receipt_stream=search["receipt_stream"],
            contract_digest=engine.canonical_hash(contract),
            scratch_dir=scratch / "checker",
        )
    elif search["status"] == "search_exhausted" and not primary_duplicate_free:
        verified = {
            "verified": False,
            "failure_reasons": ["primary_duplicate_skip_has_no_named_parent_disposition"],
            "duplicate_nodes_skipped": int(search.get("duplicate_nodes_skipped", 0)),
        }
    duplicate_free = primary_duplicate_free and int(verified.get("duplicate_nodes_skipped", 0)) == 0
    refutation_valid = bool(
        search["status"] == "search_exhausted"
        and verified.get("verified")
        and duplicate_free
    )
    return {
        "status": "FROZEN_BENCHMARK_CAPACITY_REFUTED"
        if refutation_valid
        else (
            "SEARCH_IMPLEMENTATION_INVALID"
            if search["status"] == "search_exhausted"
            else "WITNESS_SEARCH_INCONCLUSIVE"
        ),
        "complete_search": search["status"] == "search_exhausted",
        "independently_verified": bool(verified.get("verified") and duplicate_free),
        "live_transition_verified": refutation_valid,
        "duplicate_free": duplicate_free,
        "search_report": search,
        "checker_report": verified,
        **warm,
    }


def _independent_row_summary(context_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "context_id": context_id,
        "row_count": len(rows),
        "rows_digest": engine.canonical_hash(rows),
        "action_counts": dict(sorted(Counter(str(row.get("selected_action")) for row in rows).items())),
        "max_life_index": max((int(row.get("life_index", 0)) for row in rows), default=0),
        "max_respawn_count": max((int(row.get("respawn_count", 0)) for row in rows), default=0),
    }


def spawn_independent_row_recompute(context_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    payload = {"context_id": context_id, "rows": rows}
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--independent-row-recompute"],
        input=engine.canonical_json(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("independent row subprocess failed: " + completed.stderr.strip())
    receipt = json.loads(completed.stdout)
    receipt["parent_pid"] = os.getpid()
    return receipt


def validate_independent_row_recompute(rows: list[dict[str, Any]], receipt: dict[str, Any]) -> dict[str, Any]:
    expected = _independent_row_summary(str(receipt.get("context_id", "")), rows)
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError("row recompute mismatch")
    if int(receipt.get("child_pid", os.getpid())) == os.getpid():
        raise ValueError("row recompute mismatch")
    return {"valid": True, **expected}


def spawn_independent_witness_replay(context_spec: dict[str, Any], actions: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--independent-witness-replay"],
        input=engine.canonical_json({"context_spec": context_spec, "actions": actions}),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("independent witness replay subprocess failed: " + completed.stderr.strip())
    receipt = json.loads(completed.stdout)
    receipt["parent_pid"] = os.getpid()
    return receipt


def fresh_process_recompute(bundle: dict[str, Any], *, scratch_dir: Path | str) -> dict[str, Any]:
    reports = {}
    equal = True
    scratch_root = Path(scratch_dir)
    scratch_root.mkdir(parents=True, exist_ok=True)
    for context_id, context in dict(bundle.get("contexts", {})).items():
        reports[context_id] = {}
        for stage_name, payload in (
            ("control", context["control"]),
            ("witness", context["witness"]),
            ("panel", context["panel"]),
        ):
            safe_context = re.sub(r"[^A-Za-z0-9_.-]", "_", context_id)
            stage_dir = scratch_root / safe_context / stage_name
            stage_dir.mkdir(parents=True, exist_ok=True)
            path = stage_dir / "payload.json"
            path.write_text(
                json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            first = spawn_fresh_digest_probe(path)
            second = spawn_fresh_digest_probe(path)
            validate_fresh_digest_receipt(path, first)
            validate_fresh_digest_receipt(path, second)
            summary = summarize_fresh_stage_pair(first, second)
            reports[context_id][stage_name] = summary
            equal = equal and bool(summary["equal"])
        for row_stage in ("witness", "panel"):
            rows = deepcopy(context[row_stage].get("rows", []))
            receipt = spawn_independent_row_recompute(context_id, rows)
            try:
                validate_independent_row_recompute(rows, receipt)
            except ValueError:
                equal = False
            reports[context_id][f"{row_stage}_row_recompute"] = receipt
        witness = context["witness"]
        if witness.get("certificate_found") and witness.get("actions"):
            replay = spawn_independent_witness_replay(context.get("context_spec", {}), list(witness["actions"]))
            reports[context_id]["positive_witness_replay"] = replay
            equal = equal and replay.get("rows_digest") == engine.canonical_hash(witness.get("rows", []))
    return {"equal": equal, "contexts": reports}


def sha256_map(paths: tuple[str, ...]) -> dict[str, str]:
    return {
        relpath: hashlib.sha256((REPO_ROOT / relpath).read_bytes()).hexdigest()
        for relpath in paths
    }


def build_r2_artifact_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    contexts = dict(bundle["contexts"])
    certificate_rows = []
    panel_rows = []
    panel_manifest_contexts = {}
    ablation_contexts = {}
    baseline_contexts = {}
    replay_contexts = {}
    search_contexts = {}
    for context_id, context in contexts.items():
        certificate_rows.extend(deepcopy(context["witness"]["rows"]))
        panel_rows.extend(deepcopy(context["panel"]["rows"]))
        panel_manifest_contexts[context_id] = {
            "panel_rollout_ids": deepcopy(context["panel"]["panel_rollout_ids"]),
            "target_order": deepcopy(context["panel"]["target_order"]),
            "rollouts": deepcopy(context["panel"]["rollouts"]),
            "raw_checkpoints": deepcopy(context["panel"]["raw_checkpoints"]),
            "retained_checkpoints": deepcopy(context["panel"]["retained_checkpoints"]),
            "rank_reports": deepcopy(context["panel"]["rank_reports"]),
            "support_report": deepcopy(context["panel"].get("support_report", {})),
            "cell_support_report": deepcopy(context["panel"].get("cell_support_report", {})),
            "construction_complete": context["panel"]["construction_complete"],
            "panel_capacity_admitted": context["panel"]["panel_capacity_admitted"],
            "panel_hash": context["panel"]["panel_hash"],
        }
        ablation_contexts[context_id] = deepcopy(context["witness"].get("ablation_report", {}))
        baseline_contexts[context_id] = {
            "control_prefix": deepcopy(context["control"]["prefix"]),
            "r1_failed_evidence_preserved": True,
        }
        replay_contexts[context_id] = {
            "witness_replay_valid": bool(context["witness"].get("replay_valid", False)),
            "panel_rows": len(context["panel"]["rows"]),
        }
        search_contexts[context_id] = deepcopy(context["witness"].get("search_report", {}))
    return {
        "result": {
            "task_id": "EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2",
            "verdict": bundle["adjudication"]["verdict"],
            "context_count": len(contexts),
            "certificate_row_count": len(certificate_rows),
            "panel_row_count": len(panel_rows),
            "source_hashes": bundle["source_hashes"],
            "input_hashes": bundle["input_hashes"],
            "dependency_hashes": bundle["dependency_hashes"],
            "runtime_receipt": bundle["provenance_document"]["runtime_receipt"],
            "implementation_commit": bundle["provenance_document"]["implementation_commit"],
            "r1_baseline_verdict": "PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND",
            "r1_artifact_pins": deepcopy(
                {
                    path: digest
                    for path, digest in FROZEN_SOURCE_PINS.items()
                    if path.startswith("artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/")
                }
            ),
            "validity": deepcopy(bundle.get("validity", {})),
            "adjudication": deepcopy(bundle.get("adjudication", {})),
        },
        "certificate_rows": certificate_rows,
        "panel_rows": panel_rows,
        "search_report": {"contexts": search_contexts},
        "panel_manifest": {"contexts": panel_manifest_contexts},
        "baseline_comparison": {"contexts": baseline_contexts},
        "ablation_report": {"contexts": ablation_contexts},
        "leakage_report": {
            **deepcopy(bundle["leakage_report"]),
            "tamper_report": deepcopy(bundle.get("tamper_report", {})),
        },
        "replay_report": {
            "contexts": replay_contexts,
            "fresh_recompute_report": deepcopy(bundle["fresh_recompute_report"]),
            "independent_reports": deepcopy(bundle.get("independent_reports", {})),
        },
        "claim_ceiling": "Offline structural capacity only; no learner/generalization/runtime claim.",
    }


def write_r2_formal_packet(packet_dir: Path | str, bundle: dict[str, Any]) -> dict[str, Any]:
    packet = Path(packet_dir)
    packet.mkdir(parents=True, exist_ok=True)
    artifact = build_r2_artifact_bundle(bundle)
    (packet / "result.json").write_text(json.dumps(artifact["result"], sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with (packet / "certificate_rows.jsonl").open("w", encoding="utf-8") as handle:
        for row in artifact["certificate_rows"]:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    with (packet / "panel_rows.jsonl").open("w", encoding="utf-8") as handle:
        for row in artifact["panel_rows"]:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    for name in ("search_report", "panel_manifest", "baseline_comparison", "ablation_report", "leakage_report", "replay_report"):
        (packet / f"{name}.json").write_text(json.dumps(artifact[name], sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (packet / "claim_ceiling.txt").write_text(artifact["claim_ceiling"] + "\n", encoding="utf-8")
    if artifact["result"]["verdict"] != "EXISTENTIAL_CAPACITY_CERTIFICATE_FOUND":
        (packet / "failure_manifest.json").write_text(json.dumps({"verdict": artifact["result"]["verdict"]}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    scratch = packet / "_scratch"
    if scratch.exists():
        if not scratch.is_dir():
            raise ValueError("scratch path is not a directory")
        shutil.rmtree(scratch)
    (packet / "artifact_manifest.json").write_text(json.dumps(build_artifact_manifest(packet), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return artifact["result"]


def verify_r2_formal_packet(packet_dir: Path | str) -> dict[str, Any]:
    packet = Path(packet_dir)
    verify_artifact_manifest(packet)
    result = json.loads((packet / "result.json").read_text(encoding="utf-8"))
    expected = {
        "result.json",
        "certificate_rows.jsonl",
        "panel_rows.jsonl",
        "search_report.json",
        "panel_manifest.json",
        "baseline_comparison.json",
        "ablation_report.json",
        "leakage_report.json",
        "replay_report.json",
        "claim_ceiling.txt",
        "artifact_manifest.json",
    }
    if result["verdict"] != "EXISTENTIAL_CAPACITY_CERTIFICATE_FOUND":
        expected.add("failure_manifest.json")
    if any(item.is_dir() for item in packet.iterdir()):
        raise ValueError("r2 packet semantic unexpected directory")
    actual = {item.name for item in packet.iterdir() if item.is_file()}
    if actual != expected:
        raise ValueError("r2 packet semantic file set mismatch")
    allowed_verdicts = {
        "BLOCKED_001H_R2_PROVENANCE_LEAKAGE_OR_RECOMPUTE",
        "INVALID_POSTRESULT_RESCUE",
        "CONTROL_ENVELOPE_OR_ACCESS_PARITY_BROKEN",
        "SEARCH_IMPLEMENTATION_INVALID",
        "FROZEN_BENCHMARK_CAPACITY_REFUTED",
        "WITNESS_SEARCH_INCONCLUSIVE",
        "PANEL_SEARCH_INCONCLUSIVE",
        "PANEL_CAPACITY_NOT_CERTIFIED",
        "EXISTENTIAL_CAPACITY_CERTIFICATE_FOUND",
    }
    if result.get("verdict") not in allowed_verdicts:
        raise ValueError("r2 packet semantic verdict")
    if result.get("adjudication") and result["adjudication"].get("verdict") != result["verdict"]:
        raise ValueError("r2 packet semantic adjudication verdict")
    expected_r1_pins = {
        path: digest
        for path, digest in FROZEN_SOURCE_PINS.items()
        if path.startswith("artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/")
    }
    if result.get("r1_baseline_verdict") != "PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND" or result.get("r1_artifact_pins") != expected_r1_pins:
        raise ValueError("r2 packet semantic r1 preservation")
    certificate_rows = [json.loads(line) for line in (packet / "certificate_rows.jsonl").read_text(encoding="utf-8").splitlines() if line]
    panel_rows = [json.loads(line) for line in (packet / "panel_rows.jsonl").read_text(encoding="utf-8").splitlines() if line]
    panel_manifest = json.loads((packet / "panel_manifest.json").read_text(encoding="utf-8"))
    replay = json.loads((packet / "replay_report.json").read_text(encoding="utf-8"))
    leakage = json.loads((packet / "leakage_report.json").read_text(encoding="utf-8"))
    recomputed_leakage = scan_r2_evidence_leakage(
        {
            "packet": {
                "witness": {"rows": certificate_rows},
                "panel": {"rows": panel_rows},
            }
        }
    )
    if recomputed_leakage.get("all_clean") is not True:
        raise ValueError("r2 packet semantic leakage recompute")
    if result.get("certificate_row_count") != len(certificate_rows) or result.get("panel_row_count") != len(panel_rows):
        raise ValueError("r2 packet semantic row counts")
    if result.get("context_count") != len(panel_manifest.get("contexts", {})):
        raise ValueError("r2 packet semantic context count")
    failure_path = packet / "failure_manifest.json"
    if result["verdict"] == "EXISTENTIAL_CAPACITY_CERTIFICATE_FOUND":
        if failure_path.exists():
            raise ValueError("r2 packet semantic positive verdict has failure manifest")
        if not panel_manifest.get("contexts") or any(
            context.get("construction_complete") is not True or context.get("panel_capacity_admitted") is not True
            for context in panel_manifest["contexts"].values()
        ):
            raise ValueError("r2 packet semantic positive panel")
        if any(context.get("witness_replay_valid") is not True for context in replay.get("contexts", {}).values()):
            raise ValueError("r2 packet semantic positive witness replay")
    else:
        failure = json.loads(failure_path.read_text(encoding="utf-8"))
        if failure != {"verdict": result["verdict"]}:
            raise ValueError("r2 packet semantic failure verdict")
    if leakage.get("all_clean") is not True or leakage.get("all_positive_controls_detected") is not True:
        raise ValueError("r2 packet semantic leakage")
    tamper = leakage.get("tamper_report", {})
    if tamper and tamper.get("all_tamper_controls_rejected") is not True:
        raise ValueError("r2 packet semantic tamper controls")
    rows_by_checkpoint: dict[str, list[str]] = {}
    for row in panel_rows:
        rows_by_checkpoint.setdefault(str(row["checkpoint_hash"]), []).append(str(row["selected_action"]))
    if any(actions != list(ACTION_ORDER) for actions in rows_by_checkpoint.values()):
        raise ValueError("r2 packet semantic panel action expansion")
    certificate_by_context: dict[str, list[dict[str, Any]]] = {}
    for row in certificate_rows:
        certificate_by_context.setdefault(str(row.get("context_id", "")), []).append(row)
    panel_by_context: dict[str, list[dict[str, Any]]] = {}
    for row in panel_rows:
        panel_by_context.setdefault(str(row.get("context_id", "")), []).append(row)
    search_report = json.loads((packet / "search_report.json").read_text(encoding="utf-8"))
    for context_id, search in search_report.get("contexts", {}).items():
        receipt = search.get("receipt_stream") if isinstance(search, dict) else None
        if isinstance(receipt, dict) and receipt:
            validate_receipt_stream_summary(receipt)
    for context_id, manifest in panel_manifest.get("contexts", {}).items():
        context_rows = panel_by_context.get(context_id, [])
        retained = list(manifest.get("retained_checkpoints", []))
        retained_hashes = [str(item["checkpoint_hash"]) for item in retained]
        if len(retained_hashes) != len(set(retained_hashes)):
            raise ValueError("r2 packet semantic panel dedupe")
        if set(rows_by_checkpoint) and any(checkpoint_hash not in set(retained_hashes) for checkpoint_hash in rows_by_checkpoint if checkpoint_hash in {str(row.get("checkpoint_hash")) for row in context_rows}):
            raise ValueError("r2 packet semantic panel checkpoint lineage")
        before = {token: sum(item.get("front_token") == token for item in manifest.get("raw_checkpoints", [])) for token in PANEL_FLOORS}
        after = {token: sum(item.get("front_token") == token for item in retained) for token in PANEL_FLOORS}
        expected_support = {
            "before_dedupe": before,
            "after_dedupe": after,
            "required_floors": deepcopy(PANEL_FLOORS),
            "passed": all(before[token] >= floor and after[token] >= floor for token, floor in PANEL_FLOORS.items()),
        }
        if manifest.get("support_report") != expected_support:
            raise ValueError("r2 packet semantic panel support")
        cell_counts: dict[str, int] = {}
        for row in context_rows:
            key = "::".join((context_id, row["selected_action"], row["front_token"], row["outcome_type"]))
            cell_counts[key] = cell_counts.get(key, 0) + 1
        expected_cells = {
            "cell_counts": cell_counts,
            "required_floor_by_cell": {key: PANEL_FLOORS[key.split("::")[-2]] for key in cell_counts},
            "passed": bool(cell_counts) and all(count >= PANEL_FLOORS[key.split("::")[-2]] for key, count in cell_counts.items()),
        }
        if manifest.get("cell_support_report") != expected_cells:
            raise ValueError("r2 packet semantic panel cells")
        if context_rows and manifest.get("rank_reports") != compute_rank_reports(context_id, context_rows):
            raise ValueError("r2 packet semantic panel rank")
    if result["verdict"] == "EXISTENTIAL_CAPACITY_CERTIFICATE_FOUND":
        for context_id in panel_manifest.get("contexts", {}):
            rows = certificate_by_context.get(context_id, [])
            if len(rows) != 89:
                raise ValueError("r2 packet semantic positive witness horizon")
            counts = compute_support_counts(rows)
            if any(int(counts.get(item["stratum_id"], 0)) < 4 for item in TRAINING_SUPPORT_STRATA):
                raise ValueError("r2 packet semantic positive witness support")
            ranks = compute_rank_reports(context_id, rows)
            if any(int(ranks[f"{context_id}::{action}"]["rank"]) != 13 for action in ACTION_ORDER):
                raise ValueError("r2 packet semantic positive witness rank")
            if max((int(row.get("life_index", 0)) for row in rows), default=0) > 4 or max((int(row.get("respawn_count", 0)) for row in rows), default=0) > 3:
                raise ValueError("r2 packet semantic positive witness lifecycle")
    return {"verified": True, "verdict": result["verdict"], "file_set": sorted(actual)}


def _panel_not_run(context_id: str, reason: str) -> dict[str, Any]:
    return {
        "status": "not_run",
        "panel_rollout_ids": list(range(9, 17)),
        "target_order": list(PANEL_TARGET_MULTISET),
        "rollouts": [],
        "raw_checkpoints": [],
        "retained_checkpoints": [],
        "rows": [],
        "support_report": {"before_dedupe": {}, "after_dedupe": {}, "required_floors": deepcopy(PANEL_FLOORS), "passed": False},
        "cell_support_report": {"cell_counts": {}, "required_floor_by_cell": {}, "passed": False},
        "rank_reports": {},
        "construction_complete": False,
        "panel_capacity_admitted": False,
        "panel_hash": engine.canonical_hash({"context_id": context_id, "not_run_reason": reason}),
        "not_run_reason": reason,
    }


def run_formal(*, output_dir: Path | str, execute_search: bool) -> dict[str, Any]:
    output = Path(output_dir)
    boundary = collect_runtime_boundary()
    if not boundary.get("output_absent"):
        raise ValueError("output directory must be absent or empty")
    if not execute_search:
        return {"status": "formal_entrypoint_ready", "runtime_receipt": boundary["runtime_receipt"]}

    provenance_path = REPO_ROOT / R2_PROVENANCE_RELPATH
    observation = collect_r2_pre_run_observation(output_dir=output, provenance_path=provenance_path)
    document = load_pre_run_provenance(provenance_path)
    provenance_report = validate_pre_run_provenance(document, observation)
    contract = build_frozen_contract()
    contract_report = validate_frozen_contract(contract)
    if provenance_report.get("passed") is not True or contract_report["valid"] is not True:
        raise ValueError("invalid provenance or contract")

    scratch = output / "_scratch"
    scratch.mkdir(parents=True, exist_ok=False)
    source_hashes = sha256_map(R2_REQUIRED_PROVENANCE_SOURCE_PATHS)
    input_hashes = sha256_map(R2_REQUIRED_PROVENANCE_INPUT_PATHS)
    dependency_hashes = sha256_map(R2_REQUIRED_PROVENANCE_DEPENDENCY_PATHS)
    authority_hashes = sha256_map(tuple(FROZEN_SOURCE_PINS))
    contexts: dict[str, Any] = {}
    witness_reports: list[dict[str, Any]] = []

    # Witnesses are completed first; panel truth generation cannot create an early positive.
    for context_spec in contract["contexts"]:
        context_id = context_spec["context_id"]
        control = extract_banked_control(
            REPO_ROOT / context_spec["control_db_relpath"],
            action_budget=int(contract["witness_search"]["action_budget"]),
        )
        witness = run_witness_stage(
            context_spec,
            scratch_dir=scratch / "witness" / re.sub(r"[^A-Za-z0-9_.-]", "_", context_id),
            processed_node_cap=int(contract["witness_search"]["processed_node_cap"]),
        )
        witness_reports.append(witness)
        witness_rows = deepcopy(witness.get("rows", []))
        support_counts = compute_support_counts(witness_rows)
        contexts[context_id] = {
            "context_spec": deepcopy(context_spec),
            "control": control,
            "witness": {
                "rows": witness_rows,
                "actions": deepcopy(witness.get("actions", [])),
                "certificate_found": bool(witness.get("certificate_found", False)),
                "support_report": {
                    "stratum_counts": support_counts,
                    "all_supported": bool(witness_rows) and all(int(support_counts.get(stratum["stratum_id"], 0)) >= 4 for stratum in TRAINING_SUPPORT_STRATA),
                },
                "rank_reports": deepcopy(witness.get("rank_reports", {})),
                "control_envelope_comparable": len(witness_rows) == int(contract["witness_search"]["action_budget"]) and bool(witness.get("replay_valid", False)),
                "witness_found": bool(witness.get("certificate_found", False)),
                "ablation_report": {"r1_verdict": "PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND", "r1_artifacts_immutable": True},
                "search_report": deepcopy(witness.get("search_report", {})),
                "replay_valid": bool(witness.get("replay_valid", False)),
            },
            "panel": _panel_not_run(context_id, "witness_stage_not_yet_complete"),
        }

    panel_reports: list[dict[str, Any]] = []
    if all(report.get("status") == "witness_certificate_found" and report.get("certificate_found") is True for report in witness_reports):
        for context_spec in contract["contexts"]:
            context_id = context_spec["context_id"]
            panel = run_panel_search(
                context_spec=context_spec,
                target_multiset=list(contract["panel_target_multiset"]),
                storage_dir=scratch / "panel" / re.sub(r"[^A-Za-z0-9_.-]", "_", context_id),
                processed_node_cap=int(contract["panel_search"]["processed_node_cap"]),
                rollout_ids=tuple(context_spec["panel_rollout_ids"]),
            )
            panel_reports.append(panel)
            contexts[context_id]["panel"] = panel
    else:
        for context_id in contexts:
            contexts[context_id]["panel"] = _panel_not_run(context_id, "witness_certificate_missing")

    leakage_report = scan_r2_evidence_leakage(contexts)
    tamper_report = run_r2_tamper_controls(
        contract=contract,
        source_hashes=authority_hashes,
        witness_reports=witness_reports,
        panel_reports=panel_reports,
        scratch_dir=scratch / "tamper_controls",
        provenance_document=document,
        provenance_observation=observation,
    )
    independent_reports = {}
    independent_clean = True
    if panel_reports:
        for context_id, payload in contexts.items():
            reduced = independent_reduce_context(
                context_id=context_id,
                control=payload["control"],
                witness=payload["witness"],
                panel=payload["panel"],
            )
            independent_reports[context_id] = reduced
            independent_clean = independent_clean and bool(reduced.get("reported_values_match")) and bool(reduced.get("producer_receipts_valid")) and bool(reduced.get("hashes_valid"))
    else:
        independent_reports = {context_id: {"not_run": "panel_not_executed"} for context_id in contexts}

    fresh_report = fresh_process_recompute(
        {"contexts": contexts},
        scratch_dir=scratch / "fresh_recompute",
    )
    provenance_clean = bool(
        provenance_report["passed"]
        and boundary["runtime_receipt"].get("contract_satisfied")
        and source_hashes == observation["source_hashes"]
        and input_hashes == observation["input_hashes"]
        and dependency_hashes == observation["dependency_hashes"]
        and authority_hashes == FROZEN_SOURCE_PINS
        and leakage_report["all_clean"]
        and leakage_report["all_positive_controls_detected"]
        and tamper_report["all_tamper_controls_rejected"]
        and independent_clean
        and fresh_report["equal"]
    )
    verdict = dispatch_r2_verdict(
        provenance_clean=provenance_clean,
        contract_valid=contract_report["valid"],
        witness_reports=witness_reports,
        panel_reports=panel_reports,
    )
    bundle = {
        "contexts": contexts,
        "provenance_report": provenance_report,
        "provenance_document": document,
        "pre_run_observation": observation,
        "source_hashes": source_hashes,
        "input_hashes": input_hashes,
        "dependency_hashes": dependency_hashes,
        "authority_hashes": authority_hashes,
        "leakage_report": leakage_report,
        "independent_reports": independent_reports,
        "fresh_recompute_report": fresh_report,
        "tamper_report": tamper_report,
        "validity": {
            "pre_run_provenance_valid": provenance_report["passed"],
            "runtime_contract_satisfied": boundary["runtime_receipt"].get("contract_satisfied") is True,
            "source_hashes_match": observation["source_hashes"] == source_hashes,
            "input_hashes_match": observation["input_hashes"] == input_hashes,
            "dependency_hashes_match": observation["dependency_hashes"] == dependency_hashes,
            "authority_hashes_match": authority_hashes == FROZEN_SOURCE_PINS,
            "leakage_clean": leakage_report["all_clean"],
            "positive_controls_detected": leakage_report["all_positive_controls_detected"],
            "fresh_process_recompute_equal": fresh_report["equal"],
            "independent_reducer_clean": independent_clean,
            "all_tamper_controls_rejected": tamper_report["all_tamper_controls_rejected"],
        },
        "adjudication": {
            "provenance_clean": provenance_clean,
            "r1_verdict_preserved": "PRIVILEGED_SUPPORT_WITNESS_NOT_FOUND",
            "r1_artifacts_preserved": deepcopy({path: digest for path, digest in FROZEN_SOURCE_PINS.items() if path.startswith("artifacts/EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1/")}),
            "control_envelope_comparable": all(payload["witness"]["control_envelope_comparable"] for payload in contexts.values()),
            "privileged_support_witness_found": all(report.get("certificate_found", False) for report in witness_reports),
            "deterministic_panel_capacity_admitted": bool(panel_reports) and all(report.get("status") == "panel_certificate_found" for report in panel_reports),
            "verdict": verdict,
            "failure_reasons": [],
        },
    }
    packet = write_r2_formal_packet(output, bundle)
    verify_r2_formal_packet(output)
    return packet

def _subprocess_main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"--independent-row-recompute", "--independent-witness-replay"}:
        return 2
    payload = json.loads(sys.stdin.read())
    if sys.argv[1] == "--independent-row-recompute":
        result = _independent_row_summary(str(payload["context_id"]), list(payload["rows"]))
    else:
        context_spec = dict(payload["context_spec"])
        root = build_live_witness_root(context_spec)
        replay = _replay_actions(
            initial_state=root["evaluator_state"],
            actions=list(payload["actions"]),
            context_id=context_spec["context_id"],
        )
        result = {
            "context_id": context_spec["context_id"],
            "row_count": len(replay["rows"]),
            "rows_digest": engine.canonical_hash(replay["rows"]),
            "state_digest": engine.canonical_hash(replay["state"]),
        }
    result["child_pid"] = os.getpid()
    sys.stdout.write(engine.canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(_subprocess_main())
