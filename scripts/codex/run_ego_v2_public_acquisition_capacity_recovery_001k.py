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
import math
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.codex.check_ego_v2_homeostatic_compositional_transfer_001j_capacity import (
    PublicFactorBayes,
    _deficit_loss,
    _front_token,
    _initial_organism,
    _oracle_action,
    _random_action,
    _visible_tokens,
    canonical_hash,
    canonical_json,
)
from labs.ego_life_playground_v0 import engine, microworld


TASK_ID = "EGO-V2-PUBLIC-ACQUISITION-CAPACITY-RECOVERY-001K"
PREDECESSOR_TASK_ID = "EGO-V2-HOMEOSTATIC-COMPOSITIONAL-TRANSFER-001J"
PACKET_NAMES = ("search_dev", "qualification", "replication")
PUBLIC_INPUT_FIELDS = ("observation", "organism", "last_action", "last_delta")
SEARCH_POLICY_SEED = 1701
FORMAL_POLICY_SEEDS = (2701, 2702, 2703)


CANDIDATE_CONFIGS: dict[str, dict[str, Any]] = {
    "S1_FULL_HISTORY": {
        "candidate_id": "S1_FULL_HISTORY",
        "stage_id": "S1_OBSERVABILITY",
        "posterior_mode": "public_update",
        "geometry_mode": "legacy_x_first",
        "target_retention": False,
        "scoring_mode": "legacy",
        "exploration_mode": "legacy_unknown_prior",
        "budget": 96,
        "evaluator_only": False,
        "preregistered_prediction": (
            "If public history is already sufficient under the legacy planner, updates should "
            "outperform no-update and feedback shuffle."
        ),
    },
    "S1_NO_UPDATE": {
        "candidate_id": "S1_NO_UPDATE",
        "stage_id": "S1_OBSERVABILITY",
        "posterior_mode": "no_update",
        "geometry_mode": "legacy_x_first",
        "target_retention": False,
        "scoring_mode": "legacy",
        "exploration_mode": "legacy_unknown_prior",
        "budget": 96,
        "evaluator_only": False,
        "preregistered_prediction": "Removing public feedback should damage any real acquisition gain.",
    },
    "S1_FEEDBACK_SHUFFLE": {
        "candidate_id": "S1_FEEDBACK_SHUFFLE",
        "stage_id": "S1_OBSERVABILITY",
        "posterior_mode": "feedback_shuffle",
        "geometry_mode": "legacy_x_first",
        "target_retention": False,
        "scoring_mode": "legacy",
        "exploration_mode": "legacy_unknown_prior",
        "budget": 96,
        "evaluator_only": False,
        "preregistered_prediction": "Misassigning observed effects to another token should damage acquisition.",
    },
    "S1_TRUE_POSTERIOR_DIAGNOSTIC": {
        "candidate_id": "S1_TRUE_POSTERIOR_DIAGNOSTIC",
        "stage_id": "S1_OBSERVABILITY",
        "posterior_mode": "evaluator_true_posterior",
        "geometry_mode": "legacy_x_first",
        "target_retention": False,
        "scoring_mode": "legacy",
        "exploration_mode": "legacy_unknown_prior",
        "budget": 96,
        "evaluator_only": True,
        "preregistered_prediction": (
            "If learning rather than planning is limiting, a correct evaluator-only posterior "
            "should recover substantial headroom without changing navigation."
        ),
    },
    "S3_FORWARD_GEOMETRY": {
        "candidate_id": "S3_FORWARD_GEOMETRY",
        "stage_id": "S3_PLANNER_WIRING",
        "posterior_mode": "public_update",
        "geometry_mode": "forward_first",
        "target_retention": False,
        "scoring_mode": "legacy",
        "exploration_mode": "legacy_unknown_prior",
        "budget": 96,
        "evaluator_only": False,
        "preregistered_prediction": (
            "Changing only front-diagonal geometry should sharply reduce turn fraction and "
            "increase successful interactions."
        ),
    },
    "S3_TARGET_RETENTION": {
        "candidate_id": "S3_TARGET_RETENTION",
        "stage_id": "S3_PLANNER_WIRING",
        "posterior_mode": "public_update",
        "geometry_mode": "forward_first",
        "target_retention": True,
        "scoring_mode": "legacy",
        "exploration_mode": "legacy_unknown_prior",
        "budget": 96,
        "evaluator_only": False,
        "preregistered_prediction": (
            "Keeping a publicly visible token target across turns should further reduce retarget oscillation."
        ),
    },
    "S3_DEFICIT_RANKING": {
        "candidate_id": "S3_DEFICIT_RANKING",
        "stage_id": "S3_PLANNER_WIRING",
        "posterior_mode": "public_update",
        "geometry_mode": "forward_first",
        "target_retention": True,
        "scoring_mode": "deficit_reduction",
        "exploration_mode": "bounded_information_gain",
        "budget": 96,
        "evaluator_only": False,
        "preregistered_prediction": (
            "Using learned net deficit reduction with a bounded unknown bonus should exploit a "
            "known homeostatic token instead of endlessly preferring unknown tokens."
        ),
    },
    "S3_POSTERIOR_RANKING_ABLATION": {
        "candidate_id": "S3_POSTERIOR_RANKING_ABLATION",
        "stage_id": "S3_PLANNER_WIRING",
        "posterior_mode": "posterior_ablation",
        "geometry_mode": "forward_first",
        "target_retention": True,
        "scoring_mode": "deficit_reduction",
        "exploration_mode": "bounded_information_gain",
        "budget": 96,
        "evaluator_only": False,
        "preregistered_prediction": "Ignoring learned token values should remove any ranking-mediated gain.",
    },
    "S2_BUDGET_48": {
        "candidate_id": "S2_BUDGET_48",
        "stage_id": "S2_ACQUISITION_BUDGET",
        "posterior_mode": "public_update",
        "geometry_mode": "forward_first",
        "target_retention": False,
        "scoring_mode": "legacy",
        "exploration_mode": "legacy_unknown_prior",
        "budget": 48,
        "evaluator_only": False,
        "preregistered_prediction": "A 48-action prefix will expose whether acquisition cost dominates early behavior.",
    },
    "S2_BUDGET_96": {
        "candidate_id": "S2_BUDGET_96",
        "stage_id": "S2_ACQUISITION_BUDGET",
        "posterior_mode": "public_update",
        "geometry_mode": "forward_first",
        "target_retention": False,
        "scoring_mode": "legacy",
        "exploration_mode": "legacy_unknown_prior",
        "budget": 96,
        "evaluator_only": False,
        "preregistered_prediction": "The unchanged admission horizon should contain acquisition then exploitation.",
    },
    "S2_BUDGET_192": {
        "candidate_id": "S2_BUDGET_192",
        "stage_id": "S2_ACQUISITION_BUDGET",
        "posterior_mode": "public_update",
        "geometry_mode": "forward_first",
        "target_retention": False,
        "scoring_mode": "legacy",
        "exploration_mode": "legacy_unknown_prior",
        "budget": 192,
        "evaluator_only": False,
        "preregistered_prediction": (
            "If the reference learns but only too late, recovery should improve materially by 192 actions."
        ),
    },
    "S2_RISK_INFORMATION_GAIN": {
        "candidate_id": "S2_RISK_INFORMATION_GAIN",
        "stage_id": "S2_ACQUISITION_BUDGET",
        "posterior_mode": "public_update",
        "geometry_mode": "forward_first",
        "target_retention": False,
        "scoring_mode": "legacy",
        "exploration_mode": "risk_constrained_information_gain",
        "budget": 96,
        "evaluator_only": False,
        "preregistered_prediction": (
            "Changing only safe-probe scheduling should improve early acquisition without changing learned effects or geometry."
        ),
    },
}

STAGE_CANDIDATES = {
    "S1_OBSERVABILITY": (
        "S1_FULL_HISTORY",
        "S1_NO_UPDATE",
        "S1_FEEDBACK_SHUFFLE",
        "S1_TRUE_POSTERIOR_DIAGNOSTIC",
    ),
    "S3_PLANNER_WIRING": (
        "S3_FORWARD_GEOMETRY",
        "S3_TARGET_RETENTION",
        "S3_DEFICIT_RANKING",
        "S3_POSTERIOR_RANKING_ABLATION",
    ),
    "S2_ACQUISITION_BUDGET": (
        "S2_BUDGET_48",
        "S2_BUDGET_96",
        "S2_BUDGET_192",
        "S2_RISK_INFORMATION_GAIN",
    ),
}


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


def scan_candidate_input(payload: Any) -> dict[str, Any]:
    forbidden = {
        "seed",
        "world_id",
        "context_id",
        "opaque_context_id",
        "layout_id",
        "layout",
        "mapping_index",
        "mapping_commitment",
        "token_mapping",
        "private_pose",
        "position",
        "global_position",
        "world_position",
        "objects_by_cause",
        "cause",
        "oracle",
        "oracle_action",
        "split",
        "packet",
        "packet_name",
        "future",
        "future_observation",
        "verdict",
    }
    findings: list[dict[str, str]] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for raw_key, child in value.items():
                key = str(raw_key)
                child_path = f"{path}.{key}" if path else key
                if key.lower() in forbidden:
                    findings.append({"field": key, "path": child_path})
                visit(child, child_path)
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    if not isinstance(payload, Mapping):
        findings.append({"field": "<root>", "path": ""})
    else:
        for key in sorted(set(payload) - set(PUBLIC_INPUT_FIELDS)):
            findings.append({"field": str(key), "path": str(key)})
    visit(payload, "")
    unique = {
        canonical_json(item): item for item in findings
    }
    ordered = sorted(unique.values(), key=lambda item: (item["field"], item["path"]))
    return {
        "schema_version": "ego.v2.public_acquisition.input_scan.v1",
        "clean": (
            not ordered
            and isinstance(payload, Mapping)
            and set(payload) == set(PUBLIC_INPUT_FIELDS)
        ),
        "findings": ordered,
        "input_hash": canonical_hash(payload),
    }


def _sign(value: float, *, tolerance: float = 1e-9) -> int:
    if value > tolerance:
        return 1
    if value < -tolerance:
        return -1
    return 0


def _expected_interaction_delta(cause: str) -> dict[str, float]:
    energy = -engine.PASSIVE_ENERGY_DECAY_PER_TICK - engine.ACTION_COSTS["interact"]
    if cause == "resource":
        energy += engine.CAUSE_DELTAS["resource"]["energy"]
    return {
        "energy": round(float(energy), 12),
        "safety": round(float(engine.CAUSE_DELTAS[cause]["safety"]), 12),
    }


class CandidateReference:
    """Task-local public-history reference; never part of the product runtime."""

    def __init__(
        self,
        config: Mapping[str, Any],
        *,
        evaluator_private_mapping: Mapping[str, str] | None = None,
    ) -> None:
        self.config = deepcopy(dict(config))
        self.state: dict[str, Any] = {
            "schema_version": "ego.v2.public_acquisition.reference_state.v1",
            "candidate_id": str(self.config["candidate_id"]),
            "token_stats": {},
            "active_target": None,
            "plan_count": 0,
            "update_count": 0,
            "public_interaction_count": 0,
        }
        if self.config["posterior_mode"] == "evaluator_true_posterior":
            if not self.config.get("evaluator_only") or evaluator_private_mapping is None:
                raise ValueError("true posterior is evaluator-only and requires private mapping")
            for token, cause in evaluator_private_mapping.items():
                delta = _expected_interaction_delta(str(cause))
                self.state["token_stats"][str(token)] = {
                    "count": 1,
                    "energy_mean": delta["energy"],
                    "safety_mean": delta["safety"],
                }
        elif evaluator_private_mapping is not None:
            raise ValueError("legal public candidate must not receive evaluator mapping")

    def _stats_for_planning(self, token: str) -> Mapping[str, Any] | None:
        if self.config["posterior_mode"] == "posterior_ablation":
            return None
        value = self.state["token_stats"].get(token)
        return value if isinstance(value, Mapping) else None

    def _legacy_value(self, token: str, organism: Mapping[str, float]) -> float:
        stats = self._stats_for_planning(token)
        if stats is None:
            if self.config["exploration_mode"] == "risk_constrained_information_gain":
                # One public-history mechanism change: once a beneficial token
                # is known, a bounded information value no longer dominates it.
                # When no beneficial token is known, all unknown tokens retain
                # the same legal, identity-free probe value.
                safe_margin = max(
                    0.0,
                    min(float(organism["energy"]), float(organism["safety"])) - 0.12,
                )
                return 0.04 + min(0.04, safe_margin * 0.10)
            return 0.40
        energy_deficit = max(0.0, engine.TARGET_LEVEL - float(organism["energy"]))
        safety_deficit = max(0.0, engine.TARGET_LEVEL - float(organism["safety"]))
        return (
            energy_deficit * float(stats["energy_mean"])
            + safety_deficit * float(stats["safety_mean"])
            + 0.05 / math.sqrt(float(stats["count"]))
        )

    def _deficit_value(
        self,
        token: str,
        organism: Mapping[str, float],
        *,
        distance: int,
    ) -> float:
        stats = self._stats_for_planning(token)
        energy = float(organism["energy"])
        safety = float(organism["safety"])
        before = max(0.0, engine.TARGET_LEVEL - energy) + max(
            0.0, engine.TARGET_LEVEL - safety
        )
        if stats is None:
            if self.config["exploration_mode"] == "risk_constrained_information_gain":
                safe_margin = max(0.0, min(energy, safety) - 0.12)
                bonus = 0.04 + min(0.10, safe_margin * 0.20)
            else:
                bonus = 0.075
            return bonus - 0.004 * distance
        energy_after = max(0.0, min(1.0, energy + float(stats["energy_mean"])))
        safety_after = max(0.0, min(1.0, safety + float(stats["safety_mean"])))
        after = max(0.0, engine.TARGET_LEVEL - energy_after) + max(
            0.0, engine.TARGET_LEVEL - safety_after
        )
        uncertainty = 0.012 / math.sqrt(float(stats["count"]))
        return (before - after) + uncertainty - 0.004 * distance

    def _rank_visible(
        self,
        visible: list[tuple[str, int, int]],
        organism: Mapping[str, float],
    ) -> list[dict[str, Any]]:
        ranked: list[dict[str, Any]] = []
        for token, relative_x, relative_y in visible:
            distance = abs(relative_x) + abs(relative_y)
            if self.config["scoring_mode"] == "legacy":
                score = self._legacy_value(token, organism)
            else:
                score = self._deficit_value(
                    token,
                    organism,
                    distance=distance,
                )
            ranked.append(
                {
                    "token": token,
                    "relative_x": relative_x,
                    "relative_y": relative_y,
                    "distance": distance,
                    "known": self._stats_for_planning(token) is not None,
                    "score": round(float(score), 12),
                }
            )
        return sorted(
            ranked,
            key=lambda item: (
                -float(item["score"]),
                int(item["distance"]),
                str(item["token"]),
            ),
        )

    def _select_target(self, ranked: list[dict[str, Any]]) -> dict[str, Any]:
        active = self.state.get("active_target")
        if self.config["target_retention"] and active is not None:
            retained = next((item for item in ranked if item["token"] == active), None)
            if retained is not None:
                return retained
        selected = ranked[0]
        if self.config["target_retention"]:
            self.state["active_target"] = selected["token"]
        return selected

    def plan(self, payload: Mapping[str, Any], *, sequence: int) -> tuple[str, dict[str, Any]]:
        scan = scan_candidate_input(payload)
        if not scan["clean"]:
            raise ValueError("candidate public input failed leakage/schema scan")
        before_hash = canonical_hash(self.state)
        observation = payload["observation"]
        organism = payload["organism"]
        front = _front_token(observation)
        visible = _visible_tokens(observation)
        ranked = self._rank_visible(visible, organism) if visible else []
        selected_target: dict[str, Any] | None = None
        if ranked:
            selected_target = self._select_target(ranked)

        if front in microworld.TOKENS:
            front_stats = self._stats_for_planning(front)
            if self.config["scoring_mode"] == "legacy":
                should_interact = front_stats is None or self._legacy_value(front, organism) > 0.0
            else:
                front_row = next(item for item in ranked if item["token"] == front)
                should_interact = front_stats is None or float(front_row["score"]) > 0.0
            if should_interact:
                action, reason = "interact", "front_token_probe_or_use"
                self.state["active_target"] = front
            else:
                action, reason = "turn_right", "front_token_predicted_harm"
                if self.state.get("active_target") == front:
                    self.state["active_target"] = None
        elif selected_target is not None:
            relative_x = int(selected_target["relative_x"])
            relative_y = int(selected_target["relative_y"])
            if self.config["geometry_mode"] == "legacy_x_first":
                if relative_x < 0:
                    action, reason = "turn_left", "orient_visible_token_x_first"
                elif relative_x > 0:
                    action, reason = "turn_right", "orient_visible_token_x_first"
                elif relative_y < -1:
                    action, reason = "move_forward", "approach_visible_token"
                elif relative_y == -1:
                    action, reason = "interact", "front_visible_token"
                else:
                    action, reason = "turn_right", "rotate_to_rear_token"
            else:
                front_cell = str(observation["visual"][1][2])
                if relative_y < 0 and front_cell == "empty":
                    action, reason = "move_forward", "approach_front_half_token"
                elif relative_x < 0:
                    action, reason = "turn_left", "orient_side_or_rear_token"
                elif relative_x > 0:
                    action, reason = "turn_right", "orient_side_or_rear_token"
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

        self.state["plan_count"] = int(self.state["plan_count"]) + 1
        receipt = {
            "schema_version": "ego.v2.public_acquisition.plan.v1",
            "candidate_id": self.config["candidate_id"],
            "public_input_hash": scan["input_hash"],
            "public_input_fields": list(PUBLIC_INPUT_FIELDS),
            "posterior_hash": canonical_hash(self.state["token_stats"]),
            "ranked_tokens": ranked,
            "selected_target": None if selected_target is None else selected_target["token"],
            "selected_action": action,
            "selection_reason": reason,
            "state_hash_before": before_hash,
            "state_hash_after": canonical_hash(self.state),
        }
        return action, receipt

    def update_after_public_transition(
        self,
        *,
        observed_token: str,
        selected_action: str,
        observed_outcome_type: str,
        actual_delta: Mapping[str, float],
    ) -> dict[str, Any]:
        if (
            observed_token not in microworld.TOKENS
            or selected_action != "interact"
            or observed_outcome_type != "interacted"
            or not isinstance(actual_delta, Mapping)
            or set(actual_delta) != {"energy", "safety"}
        ):
            raise ValueError("public update input is invalid")
        values = {key: float(actual_delta[key]) for key in ("energy", "safety")}
        if any(not math.isfinite(value) for value in values.values()):
            raise ValueError("public update deltas must be finite")
        before_hash = canonical_hash(self.state)
        mode = str(self.config["posterior_mode"])
        updated_token: str | None = observed_token
        if mode in {"no_update", "evaluator_true_posterior"}:
            updated_token = None
        elif mode == "feedback_shuffle":
            index = microworld.TOKENS.index(observed_token)
            updated_token = microworld.TOKENS[(index + 1) % len(microworld.TOKENS)]
        if updated_token is not None:
            row = self.state["token_stats"].setdefault(
                updated_token,
                {"count": 0, "energy_mean": 0.0, "safety_mean": 0.0},
            )
            count = int(row["count"]) + 1
            for key in ("energy", "safety"):
                row[f"{key}_mean"] = round(
                    float(row[f"{key}_mean"])
                    + (values[key] - float(row[f"{key}_mean"])) / count,
                    12,
                )
            row["count"] = count
            self.state["update_count"] = int(self.state["update_count"]) + 1
        self.state["public_interaction_count"] = int(
            self.state["public_interaction_count"]
        ) + 1
        if self.state.get("active_target") == observed_token:
            self.state["active_target"] = None
        return {
            "schema_version": "ego.v2.public_acquisition.update.v1",
            "candidate_id": self.config["candidate_id"],
            "observed_token": observed_token,
            "updated_token": updated_token,
            "selected_action": selected_action,
            "observed_outcome_type": observed_outcome_type,
            "actual_delta": values,
            "state_hash_before": before_hash,
            "state_hash_after": canonical_hash(self.state),
        }

    def effect_sign_predictions(self) -> dict[str, dict[str, int] | None]:
        result: dict[str, dict[str, int] | None] = {}
        for token in microworld.TOKENS:
            stats = self._stats_for_planning(token)
            result[token] = (
                None
                if stats is None
                else {
                    "energy": _sign(float(stats["energy_mean"])),
                    "safety": _sign(float(stats["safety_mean"])),
                }
            )
        return result

    def reset_for_respawn(self) -> None:
        self.state["active_target"] = None


def _effect_sign_accuracy(
    reference: CandidateReference,
    mapping: Mapping[str, str],
) -> float:
    predictions = reference.effect_sign_predictions()
    correct = 0
    total = 0
    for token in microworld.TOKENS:
        expected = _expected_interaction_delta(str(mapping[token]))
        predicted = predictions[token]
        for key in ("energy", "safety"):
            total += 1
            if predicted is not None and int(predicted[key]) == _sign(expected[key]):
                correct += 1
    return round(correct / total, 12)


def _candidate_from_config(
    config: Mapping[str, Any], spec: Mapping[str, Any]
) -> CandidateReference:
    mapping = (
        spec["mapping_commitment"]
        if config["posterior_mode"] == "evaluator_true_posterior"
        else None
    )
    return CandidateReference(config, evaluator_private_mapping=mapping)


def run_public_trajectory(
    spec: Mapping[str, Any],
    arm: str,
    *,
    budget: int,
    policy_seed: int,
    candidate_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if type(budget) is not int or budget <= 0:
        raise ValueError("trajectory budget must be positive")
    if arm not in {"PRIVATE_ORACLE_NAVIGATOR", "UNIFORM_RANDOM", "PUBLIC_REFERENCE"}:
        raise ValueError("unknown trajectory arm")
    if arm == "PUBLIC_REFERENCE" and candidate_config is None:
        raise ValueError("public trajectory requires candidate config")
    if arm != "PUBLIC_REFERENCE" and candidate_config is not None:
        raise ValueError("baseline trajectory must not receive candidate config")

    private_spec = deepcopy(dict(spec))
    private_spec["context_id"] = str(spec["opaque_context_id"])
    world = microworld.initial_world_state(
        seed=int(spec["world_seed"]), layout_id=str(spec["layout_id"])
    )
    if dict(world["trial"]["token_mapping"]) != dict(spec["mapping_commitment"]):
        raise RuntimeError("packet mapping commitment mismatch")
    organism = _initial_organism(private_spec)
    reference = (
        _candidate_from_config(candidate_config, private_spec)
        if candidate_config is not None
        else None
    )
    last_action: str | None = None
    last_delta = {"energy": 0.0, "safety": 0.0}
    life_index = 1
    deaths = 0
    previous_trace_hash: str | None = None
    rows: list[dict[str, Any]] = []
    code_hash = engine.compute_code_path_hash()
    candidate_id = (
        str(candidate_config["candidate_id"])
        if candidate_config is not None
        else arm
    )
    run_meta = {
        "run_id": (
            f"{TASK_ID}:{spec['opaque_context_id']}:{candidate_id}:{policy_seed}:{budget}"
        ),
        "seed": policy_seed,
    }
    invocation_counts = {
        "transition_world": 0,
        "compute_actual_delta": 0,
        "compute_metabolism_ledger": 0,
    }
    cumulative_deficit_loss = 0.0

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
        scan = scan_candidate_input(payload)
        if not scan["clean"]:
            raise RuntimeError("constructed candidate payload is contaminated")
        if arm == "PRIVATE_ORACLE_NAVIGATOR":
            selected_action = _oracle_action(world, organism)
            plan_receipt = {
                "public_input_hash": scan["input_hash"],
                "public_input_fields": list(PUBLIC_INPUT_FIELDS),
                "selected_action": selected_action,
                "selection_reason": "private_evaluator_shortest_survival_route",
                "selected_target": None,
                "ranked_tokens": [],
                "posterior_hash": None,
            }
        elif arm == "UNIFORM_RANDOM":
            selected_action = _random_action(
                private_spec, policy_seed=policy_seed, sequence=sequence
            )
            plan_receipt = {
                "public_input_hash": scan["input_hash"],
                "public_input_fields": list(PUBLIC_INPUT_FIELDS),
                "selected_action": selected_action,
                "selection_reason": "deterministic_uniform_hash",
                "selected_target": None,
                "ranked_tokens": [],
                "posterior_hash": None,
            }
        else:
            assert reference is not None
            selected_action, plan_receipt = reference.plan(payload, sequence=sequence)

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
            source_episode_id=f"001k-life-{life_index}",
            source_command_hash=command_hash,
        )
        invocation_counts["transition_world"] += 1
        actual = engine.compute_actual_delta(
            transition, selected_action=selected_action
        )
        invocation_counts["compute_actual_delta"] += 1
        metabolism = engine.compute_metabolism_ledger(
            energy_before=float(organism["energy"]),
            selected_action=selected_action,
            world_before=world_before,
            world_after=world,
            world_transition=transition,
            run_meta=run_meta,
            episode_id=f"001k-life-{life_index}",
            command_hash=command_hash,
            code_path_hash=code_hash,
        )
        invocation_counts["compute_metabolism_ledger"] += 1
        actual["energy"] = float(metabolism["energy_delta"])
        organism = {
            key: round(
                max(0.0, min(1.0, float(organism[key]) + float(actual[key]))),
                12,
            )
            for key in engine.STATE_KEYS
        }
        observed_delta = {
            "energy": round(float(actual["energy"]), 12),
            "safety": round(float(actual["safety"]), 12),
        }
        update_receipt: dict[str, Any] | None = None
        front_before = _front_token(observation)
        if reference is not None and transition.get("outcome_type") == "interacted":
            if front_before not in microworld.TOKENS:
                raise RuntimeError("public observation did not expose interacted token")
            if str(transition.get("token")) != front_before:
                raise RuntimeError("evaluator transition token disagrees with public front token")
            update_receipt = reference.update_after_public_transition(
                observed_token=front_before,
                selected_action=selected_action,
                observed_outcome_type="interacted",
                actual_delta=observed_delta,
            )

        died = float(organism["energy"]) == 0.0
        if died:
            deaths += 1
        step_loss = _deficit_loss(organism, died=died)
        cumulative_deficit_loss = round(cumulative_deficit_loss + step_loss, 12)
        sign_accuracy = (
            None
            if reference is None
            else _effect_sign_accuracy(reference, spec["mapping_commitment"])
        )
        known_token_count = (
            None
            if reference is None
            else sum(
                prediction is not None
                for prediction in reference.effect_sign_predictions().values()
            )
        )
        row_without_hash = {
            "schema_version": "ego.v2.public_acquisition.row.v1",
            "task_id": TASK_ID,
            "opaque_context_id": spec["opaque_context_id"],
            "candidate_id": candidate_id,
            "arm": arm,
            "policy_seed": policy_seed,
            "budget": budget,
            "sequence": sequence,
            "life_index": life_index,
            "candidate_input_fields": list(PUBLIC_INPUT_FIELDS),
            "candidate_input_hash": scan["input_hash"],
            "candidate_input_clean": scan["clean"],
            "selected_action": selected_action,
            "selection_reason": plan_receipt["selection_reason"],
            "selected_target": plan_receipt.get("selected_target"),
            "ranked_tokens": plan_receipt.get("ranked_tokens", []),
            "posterior_hash": plan_receipt.get("posterior_hash"),
            "world_transition": transition,
            "actual_delta": observed_delta,
            "energy_after": organism["energy"],
            "safety_after": organism["safety"],
            "died": died,
            "deficit_loss": step_loss,
            "cumulative_deficit_loss": cumulative_deficit_loss,
            "effect_sign_accuracy": sign_accuracy,
            "known_token_count": known_token_count,
            "reference_update_hash": (
                None if update_receipt is None else canonical_hash(update_receipt)
            ),
            "metabolism_producer": metabolism["producer_function"],
            "metabolism_hash": canonical_hash(metabolism),
            "prev_trace_hash": previous_trace_hash,
        }
        trace_hash = canonical_hash(row_without_hash)
        rows.append({**row_without_hash, "trace_hash": trace_hash})
        previous_trace_hash = trace_hash
        last_action = selected_action
        last_delta = observed_delta
        if died:
            life_index += 1
            world = microworld.reset_world_for_life(world, life_index)
            organism = _initial_organism(private_spec)
            if reference is not None:
                reference.reset_for_respawn()

    return {
        "schema_version": "ego.v2.public_acquisition.trajectory.v1",
        "opaque_context_id": spec["opaque_context_id"],
        "candidate_id": candidate_id,
        "arm": arm,
        "policy_seed": policy_seed,
        "budget": budget,
        "action_count": budget,
        "death_count": deaths,
        "deficit_auc": cumulative_deficit_loss,
        "mean_deficit_loss": round(cumulative_deficit_loss / budget, 12),
        "successful_interactions": sum(
            row["world_transition"].get("outcome_type") == "interacted"
            for row in rows
        ),
        "turn_count": sum(
            row["selected_action"] in {"turn_left", "turn_right"} for row in rows
        ),
        "final_effect_sign_accuracy": (
            None if reference is None else rows[-1]["effect_sign_accuracy"]
        ),
        "final_known_token_count": (
            None if reference is None else rows[-1]["known_token_count"]
        ),
        "trace_chain_hash": previous_trace_hash,
        "reference_state_hash": (
            None if reference is None else canonical_hash(reference.state)
        ),
        "invocation_counts": invocation_counts,
        "rows": rows,
    }


def _trajectory_mean(trajectories: list[Mapping[str, Any]]) -> float:
    return round(
        sum(float(item["mean_deficit_loss"]) for item in trajectories)
        / len(trajectories),
        12,
    )


def _sum_invocations(trajectories: list[Mapping[str, Any]]) -> dict[str, int]:
    return {
        key: sum(int(item["invocation_counts"][key]) for item in trajectories)
        for key in (
            "transition_world",
            "compute_actual_delta",
            "compute_metabolism_ledger",
        )
    }


def _summarize_candidate(
    candidate_id: str,
    config: Mapping[str, Any],
    public: list[Mapping[str, Any]],
    oracle: list[Mapping[str, Any]],
    random: list[Mapping[str, Any]],
) -> dict[str, Any]:
    public_loss = _trajectory_mean(public)
    oracle_loss = _trajectory_mean(oracle)
    random_loss = _trajectory_mean(random)
    headroom = round(random_loss - oracle_loss, 12)
    gain = round(random_loss - public_loss, 12)
    recovery = round(gain / headroom, 12) if headroom > 0 else None
    public_by_key = {
        (str(item["opaque_context_id"]), int(item["policy_seed"])): item
        for item in public
    }
    oracle_by_key = {
        (str(item["opaque_context_id"]), int(item["policy_seed"])): item
        for item in oracle
    }
    random_by_key = {
        (str(item["opaque_context_id"]), int(item["policy_seed"])): item
        for item in random
    }
    keys = sorted(public_by_key)
    per_world = []
    for key in keys:
        p = float(public_by_key[key]["mean_deficit_loss"])
        o = float(oracle_by_key[key]["mean_deficit_loss"])
        r = float(random_by_key[key]["mean_deficit_loss"])
        per_world.append(
            {
                "opaque_context_id": key[0],
                "policy_seed": key[1],
                "public_loss": p,
                "oracle_loss": o,
                "random_loss": r,
                "public_gain": round(r - p, 12),
                "public_better_than_random": p < r,
            }
        )
    checkpoints = [step for step in (12, 24, 48, 96, 192) if step <= int(config["budget"])]
    acquisition_curve = []
    for checkpoint in checkpoints:
        endpoint_rows = [
            item["rows"][checkpoint - 1]
            for item in public
            if len(item["rows"]) >= checkpoint
        ]
        acquisition_curve.append(
            {
                "step": checkpoint,
                "mean_effect_sign_accuracy": round(
                    sum(float(row["effect_sign_accuracy"]) for row in endpoint_rows)
                    / len(endpoint_rows),
                    12,
                ),
                "mean_known_token_count": round(
                    sum(int(row["known_token_count"]) for row in endpoint_rows)
                    / len(endpoint_rows),
                    12,
                ),
                "mean_cumulative_deficit_loss": round(
                    sum(float(row["cumulative_deficit_loss"]) for row in endpoint_rows)
                    / len(endpoint_rows),
                    12,
                ),
            }
        )
    return {
        "candidate_id": candidate_id,
        "stage_id": config["stage_id"],
        "config": deepcopy(dict(config)),
        "preregistered_prediction": config["preregistered_prediction"],
        "evaluator_only": bool(config["evaluator_only"]),
        "budget": int(config["budget"]),
        "executed_world_count": len(public),
        "loss_by_arm": {
            "PRIVATE_ORACLE_NAVIGATOR": oracle_loss,
            "PUBLIC_REFERENCE": public_loss,
            "UNIFORM_RANDOM": random_loss,
        },
        "oracle_random_headroom": headroom,
        "public_reference_gain": gain,
        "recovery_fraction": recovery,
        "positive_direction_count": sum(
            bool(item["public_better_than_random"]) for item in per_world
        ),
        "direction_denominator": len(per_world),
        "mean_successful_interactions": round(
            sum(int(item["successful_interactions"]) for item in public) / len(public),
            12,
        ),
        "mean_turn_fraction": round(
            sum(int(item["turn_count"]) / int(item["action_count"]) for item in public)
            / len(public),
            12,
        ),
        "mean_final_effect_sign_accuracy": round(
            sum(float(item["final_effect_sign_accuracy"]) for item in public)
            / len(public),
            12,
        ),
        "mean_final_known_token_count": round(
            sum(int(item["final_known_token_count"]) for item in public) / len(public),
            12,
        ),
        "acquisition_curve": acquisition_curve,
        "per_world": per_world,
        "invocation_counts": _sum_invocations(public),
        "phase_signal": gain > 0,
        "m1_numeric_gate": (
            gain > 0
            and recovery is not None
            and recovery >= 0.50
            and sum(bool(item["public_better_than_random"]) for item in per_world) >= 12
        ),
    }


def _append_rows(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical_json(row) + "\n")


def evaluate_search_stage(
    root: Path,
    stage_id: str,
    *,
    output_root: Path,
    test_only: bool = False,
) -> dict[str, Any]:
    if stage_id not in STAGE_CANDIDATES:
        raise ValueError(f"unknown search stage: {stage_id!r}")
    root = Path(root).resolve()
    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    result_path = output_root / "search_results.json"
    rows_path = output_root / "search_rows.jsonl"
    stored = (
        json.loads(result_path.read_text(encoding="utf-8"))
        if result_path.exists()
        else {
            "schema_version": "ego.v2.public_acquisition.search_results.v1",
            "task_id": TASK_ID,
            "packet_name": "search_dev",
            "stages": [],
            "original_001j_packet_executed": False,
        }
    )
    if any(stage.get("stage_id") == stage_id for stage in stored["stages"]):
        raise RuntimeError(f"search stage already recorded: {stage_id}")
    specs = load_packet_assignments(root, "search_dev")
    if test_only:
        specs = specs[:2]
    candidates = STAGE_CANDIDATES[stage_id]
    baseline_cache: dict[int, tuple[list[dict[str, Any]], list[dict[str, Any]]]] = {}
    stage_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for candidate_id in candidates:
        config = deepcopy(CANDIDATE_CONFIGS[candidate_id])
        if test_only:
            config["budget"] = 12
        budget = int(config["budget"])
        if budget not in baseline_cache:
            oracle = [
                run_public_trajectory(
                    spec,
                    "PRIVATE_ORACLE_NAVIGATOR",
                    budget=budget,
                    policy_seed=SEARCH_POLICY_SEED,
                )
                for spec in specs
            ]
            random = [
                run_public_trajectory(
                    spec,
                    "UNIFORM_RANDOM",
                    budget=budget,
                    policy_seed=SEARCH_POLICY_SEED,
                )
                for spec in specs
            ]
            baseline_cache[budget] = (oracle, random)
            for trajectory in [*oracle, *random]:
                stage_rows.extend(
                    {**row, "search_stage_id": stage_id}
                    for row in trajectory["rows"]
                )
        oracle, random = baseline_cache[budget]
        public = [
            run_public_trajectory(
                spec,
                "PUBLIC_REFERENCE",
                budget=budget,
                policy_seed=SEARCH_POLICY_SEED,
                candidate_config=config,
            )
            for spec in specs
        ]
        summaries.append(_summarize_candidate(candidate_id, config, public, oracle, random))
        for trajectory in public:
            stage_rows.extend(
                {**row, "search_stage_id": stage_id}
                for row in trajectory["rows"]
            )
    stage_result = {
        "schema_version": "ego.v2.public_acquisition.search_stage.v1",
        "task_id": TASK_ID,
        "stage_id": stage_id,
        "packet_name": "search_dev",
        "candidate_count": len(candidates),
        "candidate_budget_limit": 4,
        "test_only": test_only,
        "candidates": summaries,
        "source_sha256": _sha256(Path(__file__)),
        "original_001j_packet_executed": False,
    }
    stored["stages"].append(stage_result)
    _write_json(result_path, stored)
    _append_rows(rows_path, stage_rows)
    return stage_result


def build_candidate_freeze(
    root: Path,
    candidate_id: str,
    *,
    output_path: Path | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    if candidate_id != "S2_RISK_INFORMATION_GAIN":
        raise ValueError("the campaign decision selected only S2_RISK_INFORMATION_GAIN")
    config = deepcopy(CANDIDATE_CONFIGS[candidate_id])
    if config["evaluator_only"] or int(config["budget"]) != 96:
        raise RuntimeError("qualification candidate must be legal and use 96 actions")
    artifact_root = _artifact_root(root)
    output_path = Path(output_path or artifact_root / "candidate_freeze.json").resolve()
    if output_path.exists():
        raise RuntimeError("candidate freeze is single-write")
    search_path = artifact_root / "search_results.json"
    search = json.loads(search_path.read_text(encoding="utf-8"))
    if [stage["stage_id"] for stage in search["stages"]] != [
        "S1_OBSERVABILITY",
        "S3_PLANNER_WIRING",
        "S2_ACQUISITION_BUDGET",
    ]:
        raise RuntimeError("all three search stages must complete before freeze")
    commitments = json.loads(
        (artifact_root / "packet_commitments.json").read_text(encoding="utf-8")
    )
    source_path = Path(__file__).resolve()
    freeze = {
        "schema_version": "ego.v2.public_acquisition.candidate_freeze.v1",
        "task_id": TASK_ID,
        "candidate_id": candidate_id,
        "candidate_config": config,
        "candidate_config_hash": canonical_hash(config),
        "producer_path": source_path.relative_to(root).as_posix(),
        "producer_sha256": _sha256(source_path),
        "search_results_sha256": _sha256(search_path),
        "packet_assignment_sha256": {
            name: commitments["packets"][name]["assignment_sha256"]
            for name in PACKET_NAMES
        },
        "formal_action_budget": 96,
        "formal_policy_seeds": list(FORMAL_POLICY_SEEDS),
        "thresholds": {
            "phase_public_reference_gain_strictly_positive": 0.0,
            "majority_trajectory_directions_minimum": 25,
            "majority_world_directions_minimum": 9,
            "m1_recovery_fraction_minimum": 0.50,
            "m1_world_directions_minimum": 12,
            "material_ablation_absolute_floor": 0.02,
            "material_ablation_relative_gain_fraction": 0.30,
            "material_ablation_count_minimum": 2,
            "effect_sign_accuracy_minimum": 0.80,
        },
        "ablation_ids": [
            "FORMAL_NO_UPDATE",
            "FORMAL_FEEDBACK_SHUFFLE",
            "FORMAL_POSTERIOR_ABLATION",
        ],
        "dependency_contract": {
            "numpy": "2.2.6",
            "requirements_path": "requirements-ego-v2.txt",
            "network": False,
            "llm": False,
        },
        "qualification_executed": False,
        "replication_executed": False,
        "original_001j_packet_executed": False,
        "claim_ceiling": (
            "Frozen dev-only public acquisition candidate; no qualification, "
            "M1, transfer, agency, or real-world claim."
        ),
    }
    _write_json(output_path, freeze)
    return freeze


def _load_and_verify_freeze(root: Path, freeze_path: Path | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    path = Path(freeze_path or _artifact_root(root) / "candidate_freeze.json").resolve()
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if (
        freeze.get("task_id") != TASK_ID
        or freeze.get("candidate_id") != "S2_RISK_INFORMATION_GAIN"
        or freeze.get("candidate_config_hash")
        != canonical_hash(freeze.get("candidate_config"))
        or freeze.get("producer_sha256") != _sha256(Path(__file__).resolve())
    ):
        raise RuntimeError("candidate freeze/source mismatch")
    for packet_name, expected in freeze["packet_assignment_sha256"].items():
        actual = _sha256(
            _artifact_root(root) / f"{packet_name}_assignments.json"
        )
        if actual != expected:
            raise RuntimeError(f"{packet_name} assignment changed after freeze")
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - environment gate
        raise RuntimeError("NumPy dependency unavailable") from exc
    if np.__version__ != freeze["dependency_contract"]["numpy"]:
        raise RuntimeError("NumPy dependency drift after candidate freeze")
    return freeze


def _formal_configs(base: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {
        "PUBLIC_REFERENCE": deepcopy(dict(base)),
    }
    modes = {
        "FORMAL_NO_UPDATE": "no_update",
        "FORMAL_FEEDBACK_SHUFFLE": "feedback_shuffle",
        "FORMAL_POSTERIOR_ABLATION": "posterior_ablation",
    }
    for candidate_id, posterior_mode in modes.items():
        config = deepcopy(dict(base))
        config["candidate_id"] = candidate_id
        config["posterior_mode"] = posterior_mode
        config["evaluator_only"] = False
        config["preregistered_prediction"] = (
            f"{candidate_id} should materially damage any posterior-mediated qualification gain."
        )
        result[candidate_id] = config
    return result


def _world_direction_summary(
    public: list[Mapping[str, Any]],
    random: list[Mapping[str, Any]],
) -> dict[str, Any]:
    public_by_world: dict[str, list[float]] = defaultdict(list)
    random_by_world: dict[str, list[float]] = defaultdict(list)
    for item in public:
        public_by_world[str(item["opaque_context_id"])].append(
            float(item["mean_deficit_loss"])
        )
    for item in random:
        random_by_world[str(item["opaque_context_id"])].append(
            float(item["mean_deficit_loss"])
        )
    rows = []
    for context_id in sorted(public_by_world):
        public_loss = sum(public_by_world[context_id]) / len(public_by_world[context_id])
        random_loss = sum(random_by_world[context_id]) / len(random_by_world[context_id])
        rows.append(
            {
                "opaque_context_id": context_id,
                "public_loss": round(public_loss, 12),
                "random_loss": round(random_loss, 12),
                "gain": round(random_loss - public_loss, 12),
                "positive": public_loss < random_loss,
            }
        )
    return {
        "positive_world_count": sum(bool(row["positive"]) for row in rows),
        "world_count": len(rows),
        "rows": rows,
    }


def _material_ablation_report(
    candidate: Mapping[str, Any],
    ablations: list[Mapping[str, Any]],
    thresholds: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_gain = float(candidate["public_reference_gain"])
    damage_threshold = max(
        float(thresholds["material_ablation_absolute_floor"]),
        float(thresholds["material_ablation_relative_gain_fraction"])
        * max(0.0, candidate_gain),
    )
    rows = []
    for ablation in ablations:
        damage = round(
            candidate_gain - float(ablation["public_reference_gain"]), 12
        )
        rows.append(
            {
                "candidate_id": ablation["candidate_id"],
                "ablation_gain": ablation["public_reference_gain"],
                "gain_damage": damage,
                "material": damage >= damage_threshold,
            }
        )
    return {
        "candidate_gain": candidate_gain,
        "damage_threshold": round(damage_threshold, 12),
        "material_count": sum(bool(row["material"]) for row in rows),
        "required_material_count": int(
            thresholds["material_ablation_count_minimum"]
        ),
        "rows": rows,
    }


def run_formal_packet(
    root: Path,
    packet_name: str,
    *,
    output_root: Path | None = None,
    freeze_path: Path | None = None,
    test_only: bool = False,
) -> dict[str, Any]:
    if packet_name not in {"qualification", "replication"}:
        raise ValueError("formal packet must be qualification or replication")
    root = Path(root).resolve()
    artifact_root = _artifact_root(root)
    output_root = Path(output_root or artifact_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    result_path = output_root / f"{packet_name}_result.json"
    rows_path = output_root / f"{packet_name}_rows.jsonl"
    if result_path.exists() or rows_path.exists():
        raise RuntimeError(f"{packet_name} packet is single-use and already has output")
    freeze = _load_and_verify_freeze(root, freeze_path)
    if packet_name == "replication" and not test_only:
        qualification_path = artifact_root / "qualification_result.json"
        if not qualification_path.is_file():
            raise RuntimeError("replication requires stored qualification result")
        qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
        if qualification["verdict"] == "QUALIFICATION_FAILED":
            raise RuntimeError("failed qualification does not authorize replication consumption")
    specs = load_packet_assignments(root, packet_name)
    policy_seeds = list(FORMAL_POLICY_SEEDS)
    budget = int(freeze["formal_action_budget"])
    if test_only:
        specs = specs[:2]
        policy_seeds = policy_seeds[:1]
        budget = 12
    base_config = deepcopy(freeze["candidate_config"])
    base_config["budget"] = budget
    configs = _formal_configs(base_config)

    oracle: list[dict[str, Any]] = []
    random: list[dict[str, Any]] = []
    by_candidate: dict[str, list[dict[str, Any]]] = {
        key: [] for key in configs
    }
    all_rows: list[dict[str, Any]] = []
    replay_checks: list[dict[str, Any]] = []
    for spec in specs:
        for policy_seed in policy_seeds:
            oracle_item = run_public_trajectory(
                spec,
                "PRIVATE_ORACLE_NAVIGATOR",
                budget=budget,
                policy_seed=policy_seed,
            )
            random_item = run_public_trajectory(
                spec,
                "UNIFORM_RANDOM",
                budget=budget,
                policy_seed=policy_seed,
            )
            oracle.append(oracle_item)
            random.append(random_item)
            for item in (oracle_item, random_item):
                all_rows.extend(
                    {**row, "formal_packet_name": packet_name}
                    for row in item["rows"]
                )
            for candidate_id, config in configs.items():
                produced = run_public_trajectory(
                    spec,
                    "PUBLIC_REFERENCE",
                    budget=budget,
                    policy_seed=policy_seed,
                    candidate_config=config,
                )
                by_candidate[candidate_id].append(produced)
                all_rows.extend(
                    {**row, "formal_packet_name": packet_name}
                    for row in produced["rows"]
                )
                if candidate_id == "PUBLIC_REFERENCE":
                    replayed = run_public_trajectory(
                        spec,
                        "PUBLIC_REFERENCE",
                        budget=budget,
                        policy_seed=policy_seed,
                        candidate_config=config,
                    )
                    match = canonical_hash(produced) == canonical_hash(replayed)
                    replay_checks.append(
                        {
                            "opaque_context_id": spec["opaque_context_id"],
                            "policy_seed": policy_seed,
                            "produced_hash": canonical_hash(produced),
                            "replayed_hash": canonical_hash(replayed),
                            "stored_actions_used_as_replay_input": False,
                            "match": match,
                        }
                    )

    candidate_summary = _summarize_candidate(
        "PUBLIC_REFERENCE", configs["PUBLIC_REFERENCE"], by_candidate["PUBLIC_REFERENCE"], oracle, random
    )
    ablation_summaries = [
        _summarize_candidate(candidate_id, configs[candidate_id], trajectories, oracle, random)
        for candidate_id, trajectories in by_candidate.items()
        if candidate_id != "PUBLIC_REFERENCE"
    ]
    thresholds = freeze["thresholds"]
    world_directions = _world_direction_summary(
        by_candidate["PUBLIC_REFERENCE"], random
    )
    ablation_report = _material_ablation_report(
        candidate_summary, ablation_summaries, thresholds
    )
    gates = {
        "public_reference_gain_positive": (
            float(candidate_summary["public_reference_gain"])
            > float(thresholds["phase_public_reference_gain_strictly_positive"])
        ),
        "majority_trajectory_directions": (
            int(candidate_summary["positive_direction_count"])
            >= (1 if test_only else int(thresholds["majority_trajectory_directions_minimum"]))
        ),
        "majority_world_directions": (
            int(world_directions["positive_world_count"])
            >= (1 if test_only else int(thresholds["majority_world_directions_minimum"]))
        ),
        "effect_sign_accuracy": (
            float(candidate_summary["mean_final_effect_sign_accuracy"])
            >= float(thresholds["effect_sign_accuracy_minimum"])
        ),
        "material_ablation_count": (
            int(ablation_report["material_count"])
            >= int(ablation_report["required_material_count"])
        ),
        "candidate_replay_exact": all(row["match"] for row in replay_checks),
        "candidate_inputs_clean": all(
            row["candidate_input_clean"]
            and row["candidate_input_fields"] == list(PUBLIC_INPUT_FIELDS)
            for row in all_rows
            if row["arm"] == "PUBLIC_REFERENCE"
        ),
        "original_001j_packet_unexecuted": True,
    }
    phase_qualified = all(gates.values())
    m1_numeric = (
        phase_qualified
        and float(candidate_summary["recovery_fraction"])
        >= float(thresholds["m1_recovery_fraction_minimum"])
        and int(world_directions["positive_world_count"])
        >= int(thresholds["m1_world_directions_minimum"])
    )
    if not phase_qualified:
        verdict = (
            "QUALIFICATION_FAILED"
            if packet_name == "qualification"
            else "PUBLIC_ACQUISITION_CAPACITY_STILL_INCONCLUSIVE"
        )
    elif not m1_numeric:
        verdict = "POSITIVE_SIGNAL_BUT_M1_NOT_AUTHORIZED"
    elif packet_name == "qualification":
        verdict = "QUALIFICATION_CAPACITY_ESTABLISHED_PENDING_REPLICATION"
    else:
        verdict = "PUBLIC_ACQUISITION_CAPACITY_RECOVERED_M1_GATE_MET"

    _append_rows(rows_path, all_rows)
    result = {
        "schema_version": "ego.v2.public_acquisition.formal_result.v1",
        "task_id": TASK_ID,
        "packet_name": packet_name,
        "test_only": test_only,
        "single_use": not test_only,
        "candidate_id": freeze["candidate_id"],
        "candidate_freeze_hash": canonical_hash(freeze),
        "producer_sha256": freeze["producer_sha256"],
        "assignment_sha256": freeze["packet_assignment_sha256"][packet_name],
        "action_budget": budget,
        "policy_seeds": policy_seeds,
        "executed_world_count": len(specs),
        "trajectory_count_by_arm": len(specs) * len(policy_seeds),
        "candidate": candidate_summary,
        "ablations": ablation_summaries,
        "ablation_report": ablation_report,
        "world_directions": world_directions,
        "replay_checks": replay_checks,
        "gates": gates,
        "phase_qualified": phase_qualified,
        "m1_numeric_gate": m1_numeric,
        "verdict": verdict,
        "rows_path": rows_path.relative_to(root).as_posix()
        if rows_path.is_relative_to(root)
        else rows_path.as_posix(),
        "rows_sha256": _sha256(rows_path),
        "original_001j_packet_executed": False,
        "claim_ceiling": (
            "Single dev-only packet evidence for public benchmark rule acquisition; "
            "not general transfer, agency, subjectivity, consciousness, or real-world survival."
        ),
    }
    _write_json(result_path, result)
    return result


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
    parser.add_argument("--search-stage", choices=tuple(STAGE_CANDIDATES))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--test-only", action="store_true")
    parser.add_argument("--freeze-candidate", choices=("S2_RISK_INFORMATION_GAIN",))
    parser.add_argument("--freeze-path", type=Path)
    parser.add_argument("--formal-packet", choices=("qualification", "replication"))
    args = parser.parse_args(argv)
    selected = (
        int(bool(args.audit))
        + int(args.search_stage is not None)
        + int(args.freeze_candidate is not None)
        + int(args.formal_packet is not None)
    )
    if selected != 1:
        parser.error(
            "select exactly one of --audit, --search-stage, --freeze-candidate, or --formal-packet"
        )
    if args.audit:
        report = audit_predecessor_call_chain(args.root)
        if args.output is not None:
            _write_json(args.output, report)
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if report["passed"] else 2
    if args.freeze_candidate is not None:
        report = build_candidate_freeze(
            args.root,
            args.freeze_candidate,
            output_path=args.freeze_path,
        )
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    if args.formal_packet is not None:
        report = run_formal_packet(
            args.root,
            args.formal_packet,
            output_root=args.output_root,
            freeze_path=args.freeze_path,
            test_only=args.test_only,
        )
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if report["verdict"] != "QUALIFICATION_FAILED" else 2
    output_root = args.output_root or _artifact_root(Path(args.root).resolve())
    report = evaluate_search_stage(
        args.root,
        str(args.search_stage),
        output_root=output_root,
        test_only=args.test_only,
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
