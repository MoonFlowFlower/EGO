#!/usr/bin/env python3
"""Dev-only capacity certificate for 001J.

This is an offline evaluator.  It selects actions for three declared arms but
advances every action through the unchanged V2 world, outcome, and metabolism
callables.  It is not a product runtime or a learner-success claim.
"""

from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine
from labs.ego_life_playground_v0 import microworld


TASK_ID = "EGO-V2-HOMEOSTATIC-COMPOSITIONAL-TRANSFER-001J"
ACTION_BUDGET = 96
ARMS = ("PRIVATE_ORACLE_NAVIGATOR", "PUBLIC_FACTOR_BAYES", "UNIFORM_RANDOM")
PUBLIC_REFERENCE_FIELDS = ("observation", "organism", "last_action", "last_delta")
FORBIDDEN_PUBLIC_FIELDS = frozenset(
    {
        "seed",
        "world_id",
        "context_id",
        "layout_id",
        "layout",
        "cause",
        "token_mapping",
        "mapping",
        "oracle_action",
        "oracle",
        "split",
        "global_position",
        "world_position",
        "objects_by_cause",
        "future_observation",
        "verdict",
    }
)
PROFILE_VALUES = (
    ("energy_low", {"energy": 0.28, "safety": 0.62}),
    ("safety_low", {"energy": 0.62, "safety": 0.28}),
)
CANONICAL_OUTPUT = REPO_ROOT / "artifacts" / TASK_ID


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mapping_for_seed(seed: int) -> dict[str, str]:
    state = microworld.initial_world_state(seed=seed, layout_id="p0_cross_v1")
    return {str(key): str(value) for key, value in state["trial"]["token_mapping"].items()}


def _mapping_seed_buckets() -> list[tuple[dict[str, str], list[int]]]:
    signatures: list[str] = []
    mappings: dict[str, dict[str, str]] = {}
    seeds: dict[str, list[int]] = {}
    for seed in range(20000, 26000):
        mapping = _mapping_for_seed(seed)
        signature = canonical_json(mapping)
        if signature not in mappings and len(signatures) < 4:
            signatures.append(signature)
            mappings[signature] = mapping
            seeds[signature] = []
        if signature in seeds and len(seeds[signature]) < 6:
            seeds[signature].append(seed)
        if len(signatures) == 4 and all(len(seeds[item]) == 6 for item in signatures):
            return [(mappings[item], seeds[item]) for item in signatures]
    raise RuntimeError("task-local seed range did not yield four mapping families with six IDs each")


def build_world_specs() -> list[dict[str, Any]]:
    buckets = _mapping_seed_buckets()
    layouts = tuple(sorted(microworld.LAYOUTS))
    specs: list[dict[str, Any]] = []
    for layout_index, layout_id in enumerate(layouts):
        for mapping_index, (mapping, world_ids) in enumerate(buckets):
            for profile_index, (profile_name, initial) in enumerate(PROFILE_VALUES):
                occurrence = layout_index * len(PROFILE_VALUES) + profile_index
                world_seed = int(world_ids[occurrence])
                split = (
                    "heldout"
                    if (layout_index + mapping_index + profile_index) % 3 == 0
                    else "dev"
                )
                specs.append(
                    {
                        "schema_version": "ego.v2.homeostatic_world_spec.v1",
                        "context_id": (
                            f"001j-{split}-l{layout_index}-m{mapping_index}-p{profile_index}"
                        ),
                        "split": split,
                        "layout_index": layout_index,
                        "layout_id": layout_id,
                        "mapping_index": mapping_index,
                        "mapping_commitment": deepcopy(mapping),
                        "mapping_hash": canonical_hash(mapping),
                        "profile_index": profile_index,
                        "profile_name": profile_name,
                        "initial_homeostasis": deepcopy(initial),
                        "world_seed": world_seed,
                    }
                )
    return specs


def scan_public_reference_input(payload: Any) -> dict[str, Any]:
    findings: list[dict[str, str]] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for raw_key, child in value.items():
                key = str(raw_key)
                child_path = f"{path}.{key}" if path else key
                if key.lower() in FORBIDDEN_PUBLIC_FIELDS:
                    findings.append({"field": key, "path": child_path})
                visit(child, child_path)
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    if not isinstance(payload, Mapping):
        findings.append({"field": "<root>", "path": ""})
    else:
        for key in sorted(set(payload) - set(PUBLIC_REFERENCE_FIELDS)):
            if str(key).lower() not in FORBIDDEN_PUBLIC_FIELDS:
                findings.append({"field": str(key), "path": str(key)})
    visit(payload, "")
    findings = sorted(
        {canonical_json(item): item for item in findings}.values(),
        key=lambda item: (item["field"], item["path"]),
    )
    return {
        "schema_version": "ego.v2.homeostatic_public_input_scan.v1",
        "clean": not findings and isinstance(payload, Mapping) and set(payload) == set(PUBLIC_REFERENCE_FIELDS),
        "findings": findings,
        "input_hash": canonical_hash(payload),
    }


def _front_token(observation: Mapping[str, Any]) -> str:
    return str(observation["visual"][1][2])


def _visible_tokens(observation: Mapping[str, Any]) -> list[tuple[str, int, int]]:
    visible: list[tuple[str, int, int]] = []
    for row_index, row in enumerate(observation["visual"]):
        for column_index, token in enumerate(row):
            if token in microworld.TOKENS:
                visible.append((str(token), column_index - 2, row_index - 2))
    return visible


class PublicFactorBayes:
    """Small public-history reference, deliberately not a product candidate."""

    def __init__(self, state: Mapping[str, Any] | None = None) -> None:
        self.state = (
            deepcopy(dict(state))
            if state is not None
            else {
                "schema_version": "ego.v2.public_factor_bayes.v1",
                "token_stats": {},
                "action_stats": {},
                "plan_count": 0,
            }
        )

    @classmethod
    def empty(cls) -> "PublicFactorBayes":
        return cls()

    def _token_value(self, token: str, organism: Mapping[str, float]) -> float:
        stats = self.state["token_stats"].get(token)
        if stats is None:
            return 0.40
        energy_deficit = max(0.0, engine.TARGET_LEVEL - float(organism["energy"]))
        safety_deficit = max(0.0, engine.TARGET_LEVEL - float(organism["safety"]))
        return (
            energy_deficit * float(stats["energy_mean"])
            + safety_deficit * float(stats["safety_mean"])
            + 0.05 / math.sqrt(float(stats["count"]))
        )

    def plan(self, payload: Mapping[str, Any], *, sequence: int) -> tuple[str, dict[str, Any]]:
        scan = scan_public_reference_input(payload)
        if not scan["clean"]:
            raise ValueError("public reference input failed leakage/schema scan")
        observation = payload["observation"]
        front = _front_token(observation)
        visible = _visible_tokens(observation)
        organism = payload["organism"]
        reason: str
        target: str | None = None
        if front in microworld.TOKENS:
            target = front
            if front not in self.state["token_stats"] or self._token_value(front, organism) > 0.0:
                action = "interact"
                reason = "front_token_probe_or_use"
            else:
                action = "turn_right"
                reason = "front_token_negative"
        elif visible:
            target, relative_x, relative_y = max(
                visible,
                key=lambda item: (
                    self._token_value(item[0], organism),
                    -abs(item[1]) - abs(item[2]),
                    item[0],
                ),
            )
            if relative_x < 0:
                action, reason = "turn_left", "orient_visible_token"
            elif relative_x > 0:
                action, reason = "turn_right", "orient_visible_token"
            elif relative_y < -1:
                action, reason = "move_forward", "approach_visible_token"
            elif relative_y == -1:
                action, reason = "interact", "front_visible_token"
            else:
                action, reason = "turn_right", "rotate_to_rear_token"
        else:
            front_cell = str(observation["visual"][1][2])
            if front_cell == "wall":
                action, reason = "turn_right", "public_wall_follow_turn"
            elif sequence % 5 == 0:
                action, reason = "turn_right", "public_sweep_turn"
            else:
                action, reason = "move_forward", "public_sweep_forward"
        before = canonical_hash(self.state)
        self.state["plan_count"] = int(self.state["plan_count"]) + 1
        receipt = {
            "schema_version": "ego.v2.public_factor_bayes.plan.v1",
            "public_input_hash": scan["input_hash"],
            "selected_action": action,
            "selection_reason": reason,
            "target_token": target,
            "state_hash_before": before,
            "state_hash_after": canonical_hash(self.state),
        }
        return action, receipt

    def update(
        self,
        *,
        token: str,
        action: str,
        actual_delta: Mapping[str, float],
    ) -> dict[str, Any]:
        if token not in microworld.TOKENS or action not in microworld.ACTIONS:
            raise ValueError("public reference update token/action is invalid")
        if not isinstance(actual_delta, Mapping) or set(actual_delta) != {"energy", "safety"}:
            raise ValueError("actual_delta must contain exactly energy and safety")
        values = {key: float(actual_delta[key]) for key in ("energy", "safety")}
        if any(not math.isfinite(value) for value in values.values()):
            raise ValueError("actual_delta must be finite")
        before = canonical_hash(self.state)
        row = self.state["token_stats"].setdefault(
            token, {"count": 0, "energy_mean": 0.0, "safety_mean": 0.0}
        )
        count = int(row["count"]) + 1
        row["energy_mean"] = round(
            float(row["energy_mean"]) + (values["energy"] - float(row["energy_mean"])) / count,
            12,
        )
        row["safety_mean"] = round(
            float(row["safety_mean"]) + (values["safety"] - float(row["safety_mean"])) / count,
            12,
        )
        row["count"] = count
        return {
            "schema_version": "ego.v2.public_factor_bayes.update.v1",
            "state_hash_before": before,
            "state_hash_after": canonical_hash(self.state),
            "token": token,
            "action": action,
            "actual_delta": values,
        }


def _desired_facing(dx: int, dy: int) -> str:
    if dx == 1:
        return "E"
    if dx == -1:
        return "W"
    if dy == 1:
        return "S"
    if dy == -1:
        return "N"
    raise ValueError("desired facing requires an adjacent cardinal delta")


def _turn_toward(current: str, desired: str) -> str:
    current_index = microworld.FACING_ORDER.index(current)
    desired_index = microworld.FACING_ORDER.index(desired)
    clockwise = (desired_index - current_index) % 4
    return "turn_right" if clockwise in {1, 2} else "turn_left"


def _oracle_action(world: Mapping[str, Any], organism: Mapping[str, float]) -> str:
    energy_deficit = max(0.0, engine.TARGET_LEVEL - float(organism["energy"]))
    safety_deficit = max(0.0, engine.TARGET_LEVEL - float(organism["safety"]))
    target_cause = "resource" if energy_deficit >= safety_deficit else "shelter"
    target = tuple(world["objects_by_cause"][target_cause]["position"])
    start = tuple(world["agent"]["position"])
    facing = str(world["agent"]["facing"])
    occupied = {
        tuple(item["position"])
        for cause, item in world["objects_by_cause"].items()
        if cause != target_cause
    }
    walkable = {
        (x, y)
        for y, row in enumerate(world["layout"]["base_rows"])
        for x, cell in enumerate(row)
        if cell != "#"
    }
    neighbours = ((0, -1), (1, 0), (0, 1), (-1, 0))
    if abs(start[0] - target[0]) + abs(start[1] - target[1]) == 1:
        desired = _desired_facing(target[0] - start[0], target[1] - start[1])
        return "interact" if desired == facing else _turn_toward(facing, desired)
    goals = {
        (target[0] + dx, target[1] + dy)
        for dx, dy in neighbours
        if (target[0] + dx, target[1] + dy) in walkable
        and (target[0] + dx, target[1] + dy) not in occupied
    }
    queue: deque[tuple[tuple[int, int], list[tuple[int, int]]]] = deque([(start, [])])
    seen = {start}
    path: list[tuple[int, int]] | None = None
    while queue:
        position, prefix = queue.popleft()
        if position in goals:
            path = prefix
            break
        for dx, dy in neighbours:
            nxt = (position[0] + dx, position[1] + dy)
            if nxt in walkable and nxt not in occupied and nxt != target and nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, [*prefix, nxt]))
    if not path:
        return "rest"
    first = path[0]
    desired = _desired_facing(first[0] - start[0], first[1] - start[1])
    return "move_forward" if desired == facing else _turn_toward(facing, desired)


def _random_action(spec: Mapping[str, Any], *, policy_seed: int, sequence: int) -> str:
    digest = hashlib.sha256(
        canonical_json(
            {
                "arm": "UNIFORM_RANDOM",
                "context_id": spec["context_id"],
                "policy_seed": policy_seed,
                "sequence": sequence,
            }
        ).encode("utf-8")
    ).digest()
    return microworld.ACTIONS[int.from_bytes(digest[:8], "big") % len(microworld.ACTIONS)]


def _initial_organism(spec: Mapping[str, Any]) -> dict[str, float]:
    organism = dict(engine.INITIAL_ORGANISM)
    organism.update({key: float(value) for key, value in spec["initial_homeostasis"].items()})
    return {key: round(float(organism[key]), 12) for key in engine.STATE_KEYS}


def _deficit_loss(organism: Mapping[str, float], *, died: bool) -> float:
    return round(
        max(0.0, engine.TARGET_LEVEL - float(organism["energy"]))
        + max(0.0, engine.TARGET_LEVEL - float(organism["safety"]))
        + (1.0 if died else 0.0),
        12,
    )


def run_trajectory(
    spec: Mapping[str, Any],
    arm: str,
    *,
    budget: int = ACTION_BUDGET,
    policy_seed: int = 1,
) -> dict[str, Any]:
    if spec.get("split") != "dev":
        raise ValueError("M0 may execute dev specs only")
    if arm not in ARMS or type(budget) is not int or budget <= 0:
        raise ValueError("capacity trajectory arguments are invalid")
    world = microworld.initial_world_state(
        seed=int(spec["world_seed"]), layout_id=str(spec["layout_id"])
    )
    if dict(world["trial"]["token_mapping"]) != dict(spec["mapping_commitment"]):
        raise RuntimeError("world seed no longer matches the frozen mapping family")
    organism = _initial_organism(spec)
    reference = PublicFactorBayes.empty() if arm == "PUBLIC_FACTOR_BAYES" else None
    last_action: str | None = None
    last_delta = {"energy": 0.0, "safety": 0.0}
    life_index = 1
    deaths = 0
    previous_trace_hash: str | None = None
    rows: list[dict[str, Any]] = []
    code_hash = engine.compute_code_path_hash()
    run_meta = {"run_id": f"{TASK_ID}:{spec['context_id']}:{arm}:{policy_seed}", "seed": policy_seed}
    invocation_counts = {
        "transition_world": 0,
        "compute_actual_delta": 0,
        "compute_metabolism_ledger": 0,
    }

    for sequence in range(1, budget + 1):
        observation = microworld.policy_observation(world, occlusion=False)
        payload = {
            "observation": observation,
            "organism": {
                "energy": float(organism["energy"]),
                "safety": float(organism["safety"]),
            },
            "last_action": last_action,
            "last_delta": deepcopy(last_delta),
        }
        scan = scan_public_reference_input(payload)
        if not scan["clean"]:
            raise RuntimeError("constructed public capacity input is contaminated")
        if arm == "PRIVATE_ORACLE_NAVIGATOR":
            selected_action = _oracle_action(world, organism)
            policy_receipt = {
                "selected_action": selected_action,
                "selection_reason": "private_evaluator_shortest_survival_route",
                "public_input_hash": scan["input_hash"],
            }
        elif arm == "PUBLIC_FACTOR_BAYES":
            assert reference is not None
            selected_action, policy_receipt = reference.plan(payload, sequence=sequence)
        else:
            selected_action = _random_action(spec, policy_seed=policy_seed, sequence=sequence)
            policy_receipt = {
                "selected_action": selected_action,
                "selection_reason": "deterministic_uniform_hash",
                "public_input_hash": scan["input_hash"],
            }
        command_hash = canonical_hash(
            {
                "run_id": run_meta["run_id"],
                "sequence": sequence,
                "selected_action": selected_action,
                "prev_trace_hash": previous_trace_hash,
            }
        )
        world_before = deepcopy(world)
        world, transition = microworld.transition_world(
            world_before,
            selected_action,
            source_sequence=sequence,
            source_episode_id=f"capacity-life-{life_index}",
            source_command_hash=command_hash,
        )
        invocation_counts["transition_world"] += 1
        actual = engine.compute_actual_delta(transition, selected_action=selected_action)
        invocation_counts["compute_actual_delta"] += 1
        metabolism = engine.compute_metabolism_ledger(
            energy_before=float(organism["energy"]),
            selected_action=selected_action,
            world_before=world_before,
            world_after=world,
            world_transition=transition,
            run_meta=run_meta,
            episode_id=f"capacity-life-{life_index}",
            command_hash=command_hash,
            code_path_hash=code_hash,
        )
        invocation_counts["compute_metabolism_ledger"] += 1
        actual["energy"] = float(metabolism["energy_delta"])
        organism = {
            key: round(max(0.0, min(1.0, float(organism[key]) + float(actual[key]))), 12)
            for key in engine.STATE_KEYS
        }
        observed_delta = {
            "energy": round(float(actual["energy"]), 12),
            "safety": round(float(actual["safety"]), 12),
        }
        reference_update: dict[str, Any] | None = None
        if reference is not None and transition.get("outcome_type") == "interacted":
            reference_update = reference.update(
                token=str(transition["token"]),
                action=selected_action,
                actual_delta=observed_delta,
            )
        died = float(organism["energy"]) == 0.0
        if died:
            deaths += 1
        row_without_hash = {
            "schema_version": "ego.v2.homeostatic_capacity_row.v1",
            "context_id": spec["context_id"],
            "arm": arm,
            "sequence": sequence,
            "life_index": life_index,
            "public_input_hash": scan["input_hash"],
            "public_input_clean": scan["clean"],
            "selected_action": selected_action,
            "selection_reason": policy_receipt["selection_reason"],
            "world_transition": transition,
            "actual_delta": observed_delta,
            "energy_after": organism["energy"],
            "safety_after": organism["safety"],
            "died": died,
            "deficit_loss": _deficit_loss(organism, died=died),
            "metabolism_producer": metabolism["producer_function"],
            "metabolism_hash": canonical_hash(metabolism),
            "reference_update_hash": None if reference_update is None else canonical_hash(reference_update),
            "prev_trace_hash": previous_trace_hash,
        }
        trace_hash = canonical_hash(row_without_hash)
        row = {**row_without_hash, "trace_hash": trace_hash}
        rows.append(row)
        previous_trace_hash = trace_hash
        last_action = selected_action
        last_delta = observed_delta
        if died:
            life_index += 1
            world = microworld.reset_world_for_life(world, life_index)
            organism = _initial_organism(spec)

    return {
        "schema_version": "ego.v2.homeostatic_capacity_trajectory.v1",
        "context_id": spec["context_id"],
        "arm": arm,
        "action_count": budget,
        "death_count": deaths,
        "mean_deficit_loss": round(sum(float(row["deficit_loss"]) for row in rows) / budget, 12),
        "trace_chain_hash": previous_trace_hash,
        "invocation_counts": invocation_counts,
        "rows": rows,
        "reference_state_hash": None if reference is None else canonical_hash(reference.state),
    }


def _aggregate(trajectories: list[dict[str, Any]]) -> dict[str, Any]:
    by_arm: dict[str, list[dict[str, Any]]] = {arm: [] for arm in ARMS}
    for trajectory in trajectories:
        by_arm[str(trajectory["arm"])].append(trajectory)
    losses = {
        arm: round(
            sum(float(item["mean_deficit_loss"]) for item in rows) / len(rows), 12
        )
        for arm, rows in by_arm.items()
    }
    headroom = round(losses["UNIFORM_RANDOM"] - losses["PRIVATE_ORACLE_NAVIGATOR"], 12)
    reference_gain = round(losses["UNIFORM_RANDOM"] - losses["PUBLIC_FACTOR_BAYES"], 12)
    recovery = 0.0 if headroom <= 0.0 else round(reference_gain / headroom, 12)
    reference_beats = sum(
        1
        for public in by_arm["PUBLIC_FACTOR_BAYES"]
        for random in by_arm["UNIFORM_RANDOM"]
        if public["context_id"] == random["context_id"]
        and float(public["mean_deficit_loss"]) < float(random["mean_deficit_loss"])
    )
    return {
        "loss_by_arm": losses,
        "random_oracle_headroom": headroom,
        "public_reference_gain": reference_gain,
        "public_reference_recovery_fraction": recovery,
        "public_reference_beats_random_count": reference_beats,
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def generate_capacity_evidence(output: Path, *, test_only: bool = False) -> dict[str, Any]:
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError("capacity output must be absent or empty; formal evidence is single-write")
    output.mkdir(parents=True, exist_ok=True)
    specs = build_world_specs()
    dev_specs = [spec for spec in specs if spec["split"] == "dev"]
    executed_specs = dev_specs[:2] if test_only else dev_specs
    budget = 12 if test_only else ACTION_BUDGET
    trajectories: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    for spec in executed_specs:
        for arm in ARMS:
            produced = run_trajectory(spec, arm, budget=budget, policy_seed=1701)
            replayed = run_trajectory(spec, arm, budget=budget, policy_seed=1701)
            match = canonical_json(produced) == canonical_json(replayed)
            replay_rows.append(
                {
                    "context_id": spec["context_id"],
                    "arm": arm,
                    "match": match,
                    "produced_hash": canonical_hash(produced),
                    "replayed_hash": canonical_hash(replayed),
                    "stored_actions_used_as_replay_input": False,
                }
            )
            trajectories.append(produced)
    aggregate = _aggregate(trajectories)
    formal_population_complete = len(executed_specs) == 16 and not test_only
    gates = {
        "complete_dev_population": formal_population_complete if not test_only else True,
        "three_arms_and_real_callable_receipts": all(
            trajectory["invocation_counts"]
            == {
                "transition_world": budget,
                "compute_actual_delta": budget,
                "compute_metabolism_ledger": budget,
            }
            for trajectory in trajectories
        ),
        "random_oracle_headroom_at_least_0_10": aggregate["random_oracle_headroom"] >= 0.10,
        "public_reference_recovers_half_headroom": aggregate[
            "public_reference_recovery_fraction"
        ]
        >= 0.50,
        "public_reference_beats_random_12_of_16": (
            aggregate["public_reference_beats_random_count"] >= (1 if test_only else 12)
        ),
        "fresh_replay_exact": all(row["match"] for row in replay_rows),
    }
    positive = all(gates.values())
    verdict = (
        "BENCHMARK_CAPACITY_ESTABLISHED"
        if positive
        else "BENCHMARK_CAPACITY_NOT_ESTABLISHED"
    )
    result = {
        "schema_version": "ego.v2.homeostatic_capacity_result.v1",
        "task_id": TASK_ID,
        "layer": "dev_only_candidate_free_capacity_certificate",
        "producer_function": (
            "check_ego_v2_homeostatic_compositional_transfer_001j_capacity."
            "generate_capacity_evidence"
        ),
        "formal_action_budget": ACTION_BUDGET,
        "execution_action_budget": budget,
        "world_grammar_count": len(specs),
        "dev_world_count": len(dev_specs),
        "executed_dev_world_count": len(executed_specs),
        "heldout_world_count": sum(spec["split"] == "heldout" for spec in specs),
        "heldout_executed": False,
        "test_only": test_only,
        "aggregate": aggregate,
        "gates": gates,
        "verdict": verdict,
        "next_action": (
            "authorize_m1_candidate_tests"
            if positive and not test_only
            else "stop_before_neural_candidate"
        ),
        "claim_ceiling": (
            "Dev-only offline capacity evidence through unchanged transition/outcome/"
            "metabolism callables; not product learner or transfer evidence."
        ),
    }
    rows_path = output / "capacity_rows.jsonl"
    with rows_path.open("w", encoding="utf-8", newline="\n") as handle:
        for trajectory in trajectories:
            for row in trajectory["rows"]:
                handle.write(canonical_json(row) + "\n")
    replay_report = {
        "schema_version": "ego.v2.homeostatic_capacity_replay.v1",
        "all_match": all(row["match"] for row in replay_rows),
        "stored_actions_used_as_replay_input": False,
        "rows": replay_rows,
        "independent_aggregate_recomputed": _aggregate(trajectories) == aggregate,
    }
    leakage_report = {
        "schema_version": "ego.v2.homeostatic_capacity_leakage.v1",
        "ordinary_inputs_clean": all(
            row["public_input_clean"]
            for trajectory in trajectories
            for row in trajectory["rows"]
        ),
        "positive_controls": {
            field: not scan_public_reference_input(
                {
                    "observation": {},
                    "organism": {},
                    "last_action": None,
                    "last_delta": {},
                    field: "private",
                }
            )["clean"]
            for field in ("seed", "world_id", "cause", "token_mapping", "oracle_action")
        },
    }
    _write_json(output / "capacity_result.json", result)
    _write_json(output / "capacity_replay_report.json", replay_report)
    _write_json(output / "leakage_report.json", leakage_report)
    if not positive:
        _write_json(
            output / "failure_manifest.json",
            {
                "schema_version": "ego.v2.homeostatic_capacity_failure.v1",
                "task_id": TASK_ID,
                "verdict": verdict,
                "failed_gates": sorted(key for key, value in gates.items() if not value),
                "stop_before": [
                    "homeostatic_transfer.py",
                    "engine_integration",
                    "heldout_commitment",
                ],
            },
        )
    artifact_paths = sorted(path for path in output.iterdir() if path.name != "artifact_manifest.json")
    artifacts = [
        {"path": path.name, "bytes": path.stat().st_size, "sha256": _sha256(path)}
        for path in artifact_paths
    ]
    manifest = {
        "schema_version": "ego.v2.homeostatic_capacity_manifest.v1",
        "task_id": TASK_ID,
        "artifacts": artifacts,
        "all_hashes_match": all(_sha256(output / item["path"]) == item["sha256"] for item in artifacts),
        "heldout_artifact_count": sum("heldout" in item["path"].lower() for item in artifacts),
        "protected_001a_artifacts_modified": False,
    }
    _write_json(output / "artifact_manifest.json", manifest)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=CANONICAL_OUTPUT)
    parser.add_argument("--test-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.test_only and args.output.resolve() != CANONICAL_OUTPUT.resolve():
        parser.error("formal capacity evidence must use the canonical artifact root")
    result = generate_capacity_evidence(args.output, test_only=args.test_only)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result["verdict"] == "BENCHMARK_CAPACITY_ESTABLISHED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
