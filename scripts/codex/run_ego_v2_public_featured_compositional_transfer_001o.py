#!/usr/bin/env python3
"""Run the bounded 001O public-featured exact-reference capacity campaign."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import sys
from typing import Any, Iterable, Mapping, MutableMapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from labs.ego_life_playground_v0 import public_featured_transfer as reference


TASK_ID = "EGO-V2-PUBLIC-FEATURED-COMPOSITIONAL-CAUSAL-TRANSFER-001O"
ARTIFACT_RELATIVE = Path("artifacts") / TASK_ID
ACTUAL_MECHANISM_INDEX = 17
STEPS = 48
EARLY_STEPS = 24
ARMS = (
    "UNIFORM_RANDOM",
    "PRIVATE_ORACLE",
    "PRIVATE_ALIGNED_REFERENCE",
    "SCRATCH_EXACT_BAYES",
    "TRANSFER_EXACT_HIERARCHICAL_BAYES",
    "NO_UPDATE",
    "CUE_SHUFFLE",
    "FEATURE_ABLATION",
    "HISTORY_SHUFFLE",
    "SURFACE_LOOKUP",
)
CONTROL_ARMS = ("NO_UPDATE", "CUE_SHUFFLE", "FEATURE_ABLATION", "HISTORY_SHUFFLE")


def canonical_json(value: Any) -> str:
    return reference.canonical_json(value)


def canonical_hash(value: Any) -> str:
    return reference.canonical_hash(value)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for value in values:
            handle.write(canonical_json(value) + "\n")


def artifact_root(root: Path = ROOT) -> Path:
    return root / ARTIFACT_RELATIVE


def _stable_int(*parts: Any) -> int:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def make_public_observation(
    packet_name: str,
    evaluator_seed: int,
    step: int,
    organism: Mapping[str, float],
) -> dict[str, Any]:
    if packet_name not in reference.FEATURE_COMBO_SPLITS:
        raise ValueError("unknown evaluator packet")
    pool = list(reference.FEATURE_COMBO_SPLITS[packet_name])
    rng = random.Random(_stable_int("slots", evaluator_seed, step, packet_name))
    selected = rng.sample(pool, reference.SLOT_COUNT)
    observation = {
        "organism": {
            "energy": float(organism["energy"]),
            "safety": float(organism["safety"]),
            "target": float(organism.get("target", reference.TARGET)),
        },
        "slots": [{"features": list(reference.combo_bits(index))} for index in selected],
        "previous": None,
    }
    reference.validate_public_payload(observation)
    return observation


def _noise_pair(evaluator_seed: int, step: int) -> tuple[float, float]:
    rng = random.Random(_stable_int("public-noise", evaluator_seed, step))
    weights = reference.NOISE_PROBABILITIES
    return (
        rng.choices(reference.ENERGY_NOISE_VALUES, weights=weights, k=1)[0],
        rng.choices(reference.SAFETY_NOISE_VALUES, weights=weights, k=1)[0],
    )


def _execute_evaluator_transition(
    observation: Mapping[str, Any],
    action: str,
    evaluator_seed: int,
    step: int,
    local_mode: str,
) -> dict[str, Any]:
    organism = observation["organism"]
    energy_before = float(organism["energy"])
    safety_before = float(organism["safety"])
    if action == "rest":
        delta_energy, delta_safety = reference.rest_delta(energy_before, safety_before)
    elif action.startswith("interact_"):
        slot_index = int(action.rsplit("_", 1)[1])
        noise_energy, noise_safety = _noise_pair(evaluator_seed, step)
        delta_energy, delta_safety = reference.transition_delta(
            reference.MECHANISMS[ACTUAL_MECHANISM_INDEX],
            observation["slots"][slot_index]["features"],
            local_mode,
            energy_before,
            safety_before,
            noise_energy,
            noise_safety,
        )
    else:
        raise ValueError("evaluator received action outside grammar")
    energy_after = energy_before + delta_energy
    safety_after = safety_before + delta_safety
    died = energy_after <= 0.0 or safety_after <= 0.0
    return {
        "energy_before": energy_before,
        "safety_before": safety_before,
        "energy_after": energy_after,
        "safety_after": safety_after,
        "died": died,
    }


def _organism_after(feedback: Mapping[str, Any]) -> dict[str, float]:
    if feedback["died"]:
        return {
            "energy": reference.INITIAL_ENERGY,
            "safety": reference.INITIAL_SAFETY,
            "target": reference.TARGET,
        }
    return {
        "energy": float(feedback["energy_after"]),
        "safety": float(feedback["safety_after"]),
        "target": reference.TARGET,
    }


def _deficit_loss(feedback: Mapping[str, Any]) -> float:
    deficit = max(0.0, reference.TARGET - float(feedback["energy_after"])) + max(
        0.0, reference.TARGET - float(feedback["safety_after"])
    )
    return deficit + (1.0 if feedback["died"] else 0.0)


def _candidate_rejection_count() -> int:
    observation = make_public_observation(
        "training_dev",
        1,
        1,
        {"energy": 0.5, "safety": 0.5, "target": reference.TARGET},
    )
    count = 0
    for forbidden in reference.FORBIDDEN_CANDIDATE_FIELDS:
        hostile = copy.deepcopy(observation)
        hostile["hostile"] = {forbidden: "evaluator-private"}
        try:
            reference.validate_public_payload(hostile)
        except ValueError:
            count += 1
    return count


def train_shared_reference(
    specs: Sequence[Mapping[str, Any]],
    steps: int = STEPS,
    history_shuffle: bool = False,
) -> dict[str, Any]:
    state = reference.new_reference_state()
    public_events: list[dict[str, Any]] = []
    previous_observation: Mapping[str, Any] | None = None
    for spec_index, spec in enumerate(specs):
        if spec_index:
            reference.reset_for_world(state, preserve_shared=True)
        organism = {
            "energy": reference.INITIAL_ENERGY,
            "safety": reference.INITIAL_SAFETY,
            "target": reference.TARGET,
        }
        previous_observation = None
        for step in range(1, steps + 1):
            observation = make_public_observation(
                "training_dev", int(spec["evaluator_seed"]), step, organism
            )
            action = f"interact_{(step - 1) % reference.SLOT_COUNT}"
            feedback = _execute_evaluator_transition(
                observation,
                action,
                int(spec["evaluator_seed"]),
                step,
                str(spec["local_mode"]),
            )
            update_observation = previous_observation if history_shuffle and previous_observation is not None else observation
            if not (history_shuffle and previous_observation is None):
                try:
                    reference.update_after_transition(state, update_observation, action, feedback)
                except ValueError as exc:
                    if not history_shuffle or "zero or non-finite mass" not in str(exc):
                        raise
                    # A deliberately mispaired public history can be outside the
                    # frozen finite likelihood support.  The ablation must not
                    # select a private-compatible hypothesis; it fails closed to
                    # the legal uninformative prior and records that loss below.
                    state = reference.new_reference_state()
            public_events.append(
                {
                    "observation": observation,
                    "action": action,
                    "feedback": feedback,
                }
            )
            previous_observation = observation
            organism = _organism_after(feedback)
    reference.reset_for_world(state, preserve_shared=True)
    truth_probability = reference.shared_marginal(state)[ACTUAL_MECHANISM_INDEX]
    return {
        "candidate_state": state,
        "public_events": len(public_events),
        "public_history_receipt": canonical_hash(public_events),
        "candidate_private_field_rejections": _candidate_rejection_count(),
        "shared_probability_at_evaluator_truth": truth_probability,
        "shared_entropy_bits": -sum(
            probability * math.log2(probability)
            for probability in reference.shared_marginal(state)
            if probability > 0.0
        ),
        "surface_events": public_events,
    }


def surface_key(features: Sequence[int]) -> str:
    return "".join(str(int(value)) for value in features)


def build_surface_lookup_table(
    public_events: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, dict[str, float]]:
    if public_events is None:
        public_events = [
            {
                "observation": {
                    "slots": [{"features": list(reference.combo_bits(index))}] * 3
                },
                "action": "interact_0",
                "feedback": {
                    "energy_before": 0.5,
                    "energy_after": 0.5,
                    "safety_before": 0.5,
                    "safety_after": 0.5,
                },
            }
            for index in reference.FEATURE_COMBO_SPLITS["training_dev"]
        ]
    buckets: dict[str, list[tuple[float, float]]] = {}
    for event in public_events:
        action = str(event["action"])
        if not action.startswith("interact_"):
            continue
        slot_index = int(action.rsplit("_", 1)[1])
        features = event["observation"]["slots"][slot_index]["features"]
        feedback = event["feedback"]
        buckets.setdefault(surface_key(features), []).append(
            (
                float(feedback["energy_after"]) - float(feedback["energy_before"]),
                float(feedback["safety_after"]) - float(feedback["safety_before"]),
            )
        )
    return {
        key: {
            "mean_energy_delta": sum(value[0] for value in values) / len(values),
            "mean_safety_delta": sum(value[1] for value in values) / len(values),
            "count": len(values),
        }
        for key, values in buckets.items()
    }


def _transform_observation(observation: Mapping[str, Any], arm: str) -> dict[str, Any]:
    transformed = copy.deepcopy(observation)
    if arm == "CUE_SHUFFLE":
        permutation = (2, 0, 4, 1, 3)
        for slot in transformed["slots"]:
            features = slot["features"]
            slot["features"] = [features[index] for index in permutation]
    elif arm == "FEATURE_ABLATION":
        for slot in transformed["slots"]:
            slot["features"] = [0] * reference.FEATURE_COUNT
    reference.validate_public_payload(transformed)
    return transformed


def _surface_plan(
    table: Mapping[str, Mapping[str, float]], observation: Mapping[str, Any]
) -> dict[str, Any]:
    organism = observation["organism"]
    energy_deficit = max(0.0, reference.TARGET - float(organism["energy"]))
    safety_deficit = max(0.0, reference.TARGET - float(organism["safety"]))
    scores: dict[str, float] = {"rest": energy_deficit + max(0.0, safety_deficit - reference.REST_SAFETY_GAIN)}
    for index, slot in enumerate(observation["slots"]):
        entry = table.get(surface_key(slot["features"]))
        if entry is None:
            scores[f"interact_{index}"] = scores["rest"] + 1.0
        else:
            scores[f"interact_{index}"] = max(
                0.0, energy_deficit - float(entry["mean_energy_delta"])
            ) + max(0.0, safety_deficit - float(entry["mean_safety_delta"]))
    ranking = sorted(reference.ACTIONS, key=lambda action: (scores[action], action))
    return {"action": ranking[0], "ranking": ranking, "scores": scores}


def _random_action(step: int) -> str:
    rng = random.Random(_stable_int("legal-policy-rng", step))
    return rng.choice(reference.ACTIONS)


def _prediction_sign_counts(
    plan: Mapping[str, Any],
    evaluator_observation: Mapping[str, Any],
    candidate_observation: Mapping[str, Any],
    local_mode: str,
) -> tuple[int, int]:
    predictions = plan.get("predictions")
    if not isinstance(predictions, Mapping):
        return 0, 0
    energy = float(candidate_observation["organism"]["energy"])
    safety = float(candidate_observation["organism"]["safety"])
    correct = 0
    total = 0
    for index in range(reference.SLOT_COUNT):
        action = f"interact_{index}"
        predicted = predictions[action]
        actual_delta = reference.transition_delta(
            reference.MECHANISMS[ACTUAL_MECHANISM_INDEX],
            evaluator_observation["slots"][index]["features"],
            local_mode,
            float(evaluator_observation["organism"]["energy"]),
            float(evaluator_observation["organism"]["safety"]),
            0.0,
            0.0,
        )
        predicted_delta = (
            float(predicted["expected_energy"]) - energy,
            float(predicted["expected_safety"]) - safety,
        )
        for expected, actual in zip(predicted_delta, actual_delta):
            if abs(actual) <= 1e-12:
                continue
            total += 1
            if (expected > 0.0) == (actual > 0.0):
                correct += 1
    return correct, total


def run_trajectory(
    arm: str,
    packet_name: str,
    spec: Mapping[str, Any],
    trained_state: Mapping[str, Any],
    steps: int = STEPS,
    *,
    history_shuffled_state: Mapping[str, Any] | None = None,
    surface_table: Mapping[str, Mapping[str, float]] | None = None,
) -> dict[str, Any]:
    if arm not in ARMS:
        raise ValueError("unknown capacity-certificate arm")
    if arm in ("PRIVATE_ORACLE", "PRIVATE_ALIGNED_REFERENCE"):
        state = reference.private_aligned_reference_state(
            ACTUAL_MECHANISM_INDEX, str(spec["local_mode"])
        )
    elif arm == "SCRATCH_EXACT_BAYES" or arm == "UNIFORM_RANDOM" or arm == "SURFACE_LOOKUP":
        state = reference.new_reference_state()
    elif arm == "HISTORY_SHUFFLE" and history_shuffled_state is not None:
        state = copy.deepcopy(history_shuffled_state)
    else:
        state = copy.deepcopy(trained_state)
    reference.validate_reference_state(state)
    organism = {
        "energy": reference.INITIAL_ENERGY,
        "safety": reference.INITIAL_SAFETY,
        "target": reference.TARGET,
    }
    rows: list[dict[str, Any]] = []
    previous_candidate_observation: Mapping[str, Any] | None = None
    sign_correct = 0
    sign_total = 0
    for step in range(1, steps + 1):
        evaluator_observation = make_public_observation(
            packet_name, int(spec["evaluator_seed"]), step, organism
        )
        candidate_observation = _transform_observation(evaluator_observation, arm)
        receipt_before = reference.public_state_receipt(state)
        if arm == "UNIFORM_RANDOM":
            plan = reference.plan_action(state, candidate_observation)
            action = _random_action(step)
            plan = dict(plan)
            plan["action"] = action
            plan["reason"] = {"policy": "legal_internal_uniform_rng"}
        elif arm == "SURFACE_LOOKUP":
            plan = _surface_plan(surface_table or {}, candidate_observation)
            action = str(plan["action"])
        else:
            plan = reference.plan_action(state, candidate_observation)
            action = str(plan["action"])
        correct, total = _prediction_sign_counts(
            plan,
            evaluator_observation,
            candidate_observation,
            str(spec["local_mode"]),
        )
        sign_correct += correct
        sign_total += total
        feedback = _execute_evaluator_transition(
            evaluator_observation,
            action,
            int(spec["evaluator_seed"]),
            step,
            str(spec["local_mode"]),
        )
        update_receipt: dict[str, Any] | None = None
        if arm not in ("NO_UPDATE", "PRIVATE_ORACLE", "PRIVATE_ALIGNED_REFERENCE", "SURFACE_LOOKUP", "UNIFORM_RANDOM"):
            update_observation = candidate_observation
            if arm == "HISTORY_SHUFFLE":
                update_observation = previous_candidate_observation or candidate_observation
            try:
                update_receipt = reference.update_after_transition(
                    state, update_observation, action, feedback
                )
            except ValueError as exc:
                if arm not in ("HISTORY_SHUFFLE", "CUE_SHUFFLE", "FEATURE_ABLATION") or "zero or non-finite mass" not in str(exc):
                    raise
                state = reference.new_reference_state()
                update_receipt = {
                    "fail_closed": "ABLATED_PUBLIC_HISTORY_OUTSIDE_FROZEN_SUPPORT",
                    "state_hash_after": canonical_hash(state),
                }
        receipt_after = reference.public_state_receipt(state)
        row_without_hash = {
            "task_id": TASK_ID,
            "arm": arm,
            "opaque_world": str(spec["opaque_world"]),
            "step": step,
            "public_observation": evaluator_observation,
            "candidate_input_receipt": canonical_hash(candidate_observation),
            "candidate_observation": candidate_observation,
            "action": action,
            "plan": plan,
            "feedback": feedback,
            "deficit_loss": _deficit_loss(feedback),
            "posterior_before": receipt_before,
            "posterior_after": receipt_after,
            "update_receipt": update_receipt,
            "evaluator_only": {
                "local_nuisance": str(spec["local_mode"]),
                "shared_truth_index": ACTUAL_MECHANISM_INDEX,
            },
        }
        row = dict(row_without_hash)
        row["row_hash"] = canonical_hash(row_without_hash)
        rows.append(row)
        previous_candidate_observation = candidate_observation
        organism = _organism_after(feedback)
    early = sum(float(row["deficit_loss"]) for row in rows[: min(EARLY_STEPS, steps)])
    late = sum(float(row["deficit_loss"]) for row in rows[min(EARLY_STEPS, steps) :])
    return {
        "task_id": TASK_ID,
        "arm": arm,
        "opaque_world": str(spec["opaque_world"]),
        "local_mode_evaluator_only": str(spec["local_mode"]),
        "early_deficit_auc": early,
        "late_deficit_auc": late,
        "total_deficit_auc": early + late,
        "effect_sign_accuracy": sign_correct / sign_total if sign_total else 0.0,
        "deaths": sum(int(row["feedback"]["died"]) for row in rows),
        "rows": rows,
        "trajectory_hash": canonical_hash([row["row_hash"] for row in rows]),
    }


def recompute_trajectory(trajectory: Mapping[str, Any]) -> dict[str, Any]:
    rows = trajectory["rows"]
    for row in rows:
        without_hash = {key: value for key, value in row.items() if key != "row_hash"}
        if canonical_hash(without_hash) != row.get("row_hash"):
            raise ValueError("row hash mismatch")
        reference.validate_public_payload(row["candidate_observation"])
        if canonical_hash(row["candidate_observation"]) != row["candidate_input_receipt"]:
            raise ValueError("candidate input receipt mismatch")
    early = sum(float(row["deficit_loss"]) for row in rows[: min(EARLY_STEPS, len(rows))])
    late = sum(float(row["deficit_loss"]) for row in rows[min(EARLY_STEPS, len(rows)) :])
    expected = {
        "early_deficit_auc": float(trajectory["early_deficit_auc"]),
        "late_deficit_auc": float(trajectory["late_deficit_auc"]),
        "total_deficit_auc": float(trajectory["total_deficit_auc"]),
    }
    actual = {
        "early_deficit_auc": early,
        "late_deficit_auc": late,
        "total_deficit_auc": early + late,
    }
    return {
        "match": all(math.isclose(expected[key], actual[key], abs_tol=1e-10) for key in expected),
        "expected": expected,
        "actual": actual,
        "trajectory_hash": canonical_hash([row["row_hash"] for row in rows]),
    }


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def summarize_packet(
    trajectories: Sequence[Mapping[str, Any]], positive_worlds_min: int = 12
) -> dict[str, Any]:
    by_arm: dict[str, list[Mapping[str, Any]]] = {}
    for trajectory in trajectories:
        by_arm.setdefault(str(trajectory["arm"]), []).append(trajectory)
    metrics: dict[str, Any] = {}
    for arm, arm_rows in by_arm.items():
        metrics[arm] = {
            "worlds": len(arm_rows),
            "mean_early_deficit_auc": _mean(float(row["early_deficit_auc"]) for row in arm_rows),
            "mean_late_deficit_auc": _mean(float(row["late_deficit_auc"]) for row in arm_rows),
            "mean_total_deficit_auc": _mean(float(row["total_deficit_auc"]) for row in arm_rows),
            "mean_effect_sign_accuracy": _mean(float(row["effect_sign_accuracy"]) for row in arm_rows),
            "total_deaths": sum(int(row["deaths"]) for row in arm_rows),
        }
    scratch = metrics["SCRATCH_EXACT_BAYES"]["mean_early_deficit_auc"]
    transfer = metrics["TRANSFER_EXACT_HIERARCHICAL_BAYES"]["mean_early_deficit_auc"]
    oracle = metrics["PRIVATE_ORACLE"]["mean_early_deficit_auc"]
    gain = scratch - transfer
    headroom = scratch - oracle
    paired: dict[str, dict[str, float]] = {}
    for arm in ("SCRATCH_EXACT_BAYES", "TRANSFER_EXACT_HIERARCHICAL_BAYES"):
        for row in by_arm[arm]:
            paired.setdefault(str(row["opaque_world"]), {})[arm] = float(row["early_deficit_auc"])
    directions = {
        world: values["SCRATCH_EXACT_BAYES"] - values["TRANSFER_EXACT_HIERARCHICAL_BAYES"]
        for world, values in paired.items()
        if len(values) == 2
    }
    controls: dict[str, Any] = {}
    for arm in CONTROL_ARMS:
        control_gain = scratch - metrics[arm]["mean_early_deficit_auc"]
        controls[arm] = {
            "gain": control_gain,
            "gain_removal_fraction": (gain - control_gain) / gain if gain > 0.0 else 0.0,
        }
    reversed_worlds = {
        str(row["opaque_world"])
        for row in trajectories
        if row.get("local_mode_evaluator_only") == "full_reverse"
    }
    reversed_late: dict[str, float] = {}
    for arm in ("SCRATCH_EXACT_BAYES", "TRANSFER_EXACT_HIERARCHICAL_BAYES"):
        reversed_late[arm] = _mean(
            float(row["late_deficit_auc"])
            for row in by_arm[arm]
            if str(row["opaque_world"]) in reversed_worlds
        )
    transfer_sign = metrics["TRANSFER_EXACT_HIERARCHICAL_BAYES"]["mean_effect_sign_accuracy"]
    positive_worlds = sum(value > 0.0 for value in directions.values())
    gate_checks = {
        "positive_transfer_gain": gain > 0.0,
        "recovery_fraction_at_least_0_10": headroom > 0.0 and gain / headroom >= 0.10,
        "positive_worlds_at_least_threshold": positive_worlds >= positive_worlds_min,
        "unseen_effect_sign_accuracy_at_least_0_80": transfer_sign >= 0.80,
        "each_control_removes_half_gain": all(
            controls[arm]["gain_removal_fraction"] >= 0.50 for arm in CONTROL_ARMS
        ),
        "surface_lookup_does_not_match_transfer": metrics["SURFACE_LOOKUP"]["mean_early_deficit_auc"] > transfer,
        "misleading_subset_late_recovers": reversed_late["TRANSFER_EXACT_HIERARCHICAL_BAYES"] <= reversed_late["SCRATCH_EXACT_BAYES"],
    }
    return {
        "metrics": metrics,
        "transfer_gain": gain,
        "scratch_oracle_headroom": headroom,
        "recovery_fraction": gain / headroom if headroom > 0.0 else 0.0,
        "positive_worlds": positive_worlds,
        "worlds_total": len(directions),
        "per_world_transfer_direction": directions,
        "controls": controls,
        "misleading_subset_late_auc": reversed_late,
        "gate_checks": gate_checks,
        "gate_pass": all(gate_checks.values()),
    }


def _one_step_expected_deficit(features: Sequence[int], local_mode: str) -> float:
    total = 0.0
    for noise_energy, probability_energy in zip(reference.ENERGY_NOISE_VALUES, reference.NOISE_PROBABILITIES):
        for noise_safety, probability_safety in zip(reference.SAFETY_NOISE_VALUES, reference.NOISE_PROBABILITIES):
            delta_energy, delta_safety = reference.transition_delta(
                reference.MECHANISMS[ACTUAL_MECHANISM_INDEX],
                features,
                local_mode,
                reference.INITIAL_ENERGY,
                reference.INITIAL_SAFETY,
                noise_energy,
                noise_safety,
            )
            deficit = max(0.0, reference.TARGET - reference.INITIAL_ENERGY - delta_energy) + max(
                0.0, reference.TARGET - reference.INITIAL_SAFETY - delta_safety
            )
            total += probability_energy * probability_safety * deficit
    return total


def symbolic_admission() -> dict[str, Any]:
    capacity = reference.symbolic_capacity_audit()
    per_combo = {}
    for index in range(32):
        features = reference.combo_bits(index)
        per_combo[index] = {
            mode: _one_step_expected_deficit(features, mode) for mode in reference.LOCAL_NAMES
        }
    prior_expected = {
        index: sum(reference.LOCAL_PRIOR[mode_index] * values[mode] for mode_index, mode in enumerate(reference.LOCAL_NAMES))
        for index, values in per_combo.items()
    }
    private_best = sum(
        reference.LOCAL_PRIOR[mode_index]
        * min(values[mode] for values in per_combo.values())
        for mode_index, mode in enumerate(reference.LOCAL_NAMES)
    )
    uniform_cost = _mean(prior_expected.values())
    informative = [
        index for index, values in per_combo.items() if not math.isclose(values["normal"], values["full_reverse"], abs_tol=1e-12)
    ]
    best_probe_index = min(informative, key=lambda index: prior_expected[index])
    best_probe_cost = prior_expected[best_probe_index]
    probe_excess = max(0.0, best_probe_cost - private_best)
    private_headroom = uniform_cost - private_best
    checks = {
        "cue_mutual_information_positive": capacity["public_cue_effect_mutual_information_bits"] > 0.0,
        "cue_mutual_information_incomplete": capacity["public_cue_effect_mutual_information_bits"] < capacity["shared_mechanism_entropy_bits"],
        "current_world_feedback_required": capacity["current_world_interaction_required"],
        "probe_cost_below_private_aligned_headroom": probe_excess < private_headroom,
        "all_factor_levels_covered_in_training": all(
            {reference.combo_bits(index)[axis] for index in reference.FEATURE_COMBO_SPLITS["training_dev"]} == {0, 1}
            for axis in range(reference.FEATURE_COUNT)
        ),
        "evaluation_combinations_unseen_in_training": set(reference.FEATURE_COMBO_SPLITS["training_dev"]).isdisjoint(
            set(reference.FEATURE_COMBO_SPLITS["search_dev"])
            | set(reference.FEATURE_COMBO_SPLITS["qualification"])
            | set(reference.FEATURE_COMBO_SPLITS["replication"])
        ),
    }
    return {
        **capacity,
        "best_informative_probe_combo_evaluator_only": best_probe_index,
        "best_probe_expected_deficit": best_probe_cost,
        "private_aligned_expected_deficit": private_best,
        "uniform_probe_expected_deficit": uniform_cost,
        "probe_excess_deficit": probe_excess,
        "private_aligned_headroom": private_headroom,
        "checks": checks,
        "pass": all(checks.values()),
    }


def load_packet_assignments(root: Path = ROOT) -> Mapping[str, Any]:
    return json.loads((artifact_root(root) / "packet_assignments.json").read_text(encoding="utf-8"))


def run_packet(
    packet_name: str,
    specs: Sequence[Mapping[str, Any]],
    trained: Mapping[str, Any],
    shuffled: Mapping[str, Any],
    root: Path = ROOT,
    steps: int = STEPS,
) -> dict[str, Any]:
    table = build_surface_lookup_table(trained["surface_events"])
    trajectories = [
        run_trajectory(
            arm,
            packet_name,
            spec,
            trained["candidate_state"],
            steps,
            history_shuffled_state=shuffled["candidate_state"],
            surface_table=table,
        )
        for spec in specs
        for arm in ARMS
    ]
    summary = summarize_packet(trajectories)
    rows_path = artifact_root(root) / f"{packet_name}_rows.jsonl"
    write_jsonl(rows_path, (row for trajectory in trajectories for row in trajectory["rows"]))
    result = {
        "task_id": TASK_ID,
        "packet": packet_name,
        "summary": summary,
        "trajectory_summaries": [
            {key: value for key, value in trajectory.items() if key != "rows"}
            for trajectory in trajectories
        ],
        "rows_file": rows_path.name,
        "rows_sha256": sha256(rows_path),
        "row_count": sum(len(trajectory["rows"]) for trajectory in trajectories),
        "all_row_recomputations_match": all(
            recompute_trajectory(trajectory)["match"] for trajectory in trajectories
        ),
    }
    write_json(artifact_root(root) / f"{packet_name}_result.json", result)
    return {"result": result, "trajectories": trajectories}


def _append_trial(root: Path, event: Mapping[str, Any]) -> None:
    path = artifact_root(root) / "trial_registry.jsonl"
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(event) + "\n")


def _candidate_freeze(root: Path) -> dict[str, Any]:
    paths = [
        root / "labs/ego_life_playground_v0/public_featured_transfer.py",
        root / "scripts/codex/run_ego_v2_public_featured_compositional_transfer_001o.py",
        root / "scripts/codex/verify_ego_v2_public_featured_compositional_transfer_001o.py",
        root / "tests/test_ego_life_playground_public_featured_transfer.py",
        root / "scripts/codex/tests/test_run_ego_v2_public_featured_compositional_transfer_001o.py",
        root / "scripts/codex/tests/test_verify_ego_v2_public_featured_compositional_transfer_001o.py",
        artifact_root(root) / "grammar_preregistration.json",
        artifact_root(root) / "packet_assignments.json",
        artifact_root(root) / "packet_commitment.json",
    ]
    return {
        "task_id": TASK_ID,
        "status": "FROZEN_AFTER_SEARCH_BEFORE_QUALIFICATION",
        "files": {str(path.relative_to(root)).replace("\\", "/"): sha256(path) for path in paths},
        "combined_hash": canonical_hash(
            {str(path.relative_to(root)).replace("\\", "/"): sha256(path) for path in paths}
        ),
    }


def run_campaign(stage: str, root: Path = ROOT) -> dict[str, Any]:
    artifacts = artifact_root(root)
    assignments = load_packet_assignments(root)
    packets = assignments["packets"]
    symbolic = symbolic_admission()
    write_json(artifacts / "symbolic_capacity_audit.json", symbolic)
    if stage == "symbolic":
        return {"symbolic": symbolic}
    if not symbolic["pass"]:
        decision = {
            "verdict": "PUBLIC_FEATURED_GRAMMAR_CAPACITY_NOT_ADMITTED",
            "qualification_consumed": False,
            "replication_consumed": False,
        }
        write_json(artifacts / "result.json", decision)
        return decision
    trained = train_shared_reference(packets["training_dev"])
    shuffled = train_shared_reference(packets["training_dev"], history_shuffle=True)
    training_receipt = {key: value for key, value in trained.items() if key not in ("candidate_state", "surface_events")}
    training_receipt["candidate_state_receipt"] = reference.public_state_receipt(trained["candidate_state"])
    training_receipt["history_shuffle_shared_probability_at_evaluator_truth"] = shuffled[
        "shared_probability_at_evaluator_truth"
    ]
    write_json(artifacts / "training_public_history_receipt.json", training_receipt)
    write_jsonl(artifacts / "training_public_history_rows.jsonl", trained["surface_events"])
    existing_search_path = artifacts / "search_dev_result.json"
    if stage == "full" and existing_search_path.exists():
        existing_search = json.loads(existing_search_path.read_text(encoding="utf-8"))
        if existing_search.get("summary", {}).get("gate_pass"):
            search = {"result": existing_search, "trajectories": []}
        else:
            search = run_packet("search_dev", packets["search_dev"], trained, shuffled, root)
    else:
        search = run_packet("search_dev", packets["search_dev"], trained, shuffled, root)
        _append_trial(
            root,
            {
                "event": "SEARCH_DEV_CANDIDATE_RESULT",
                "candidate": "CANDIDATE_2_OVERLAPPING_FEEDBACK_NOISE",
                "summary": search["result"]["summary"],
                "qualification_consumed": False,
                "replication_consumed": False,
            },
        )
    if stage == "search" or not search["result"]["summary"]["gate_pass"]:
        verdict = (
            "SEARCH_DEV_CAPACITY_GATE_PASSED_QUALIFICATION_NOT_CONSUMED"
            if search["result"]["summary"]["gate_pass"]
            else "PUBLIC_FEATURED_EXACT_TRANSFER_SEARCH_GATE_FAILED"
        )
        result = {
            "verdict": verdict,
            "symbolic_pass": True,
            "search_gate_pass": search["result"]["summary"]["gate_pass"],
            "qualification_consumed": False,
            "replication_consumed": False,
            "learner_implementation_authorized": False,
        }
        write_json(artifacts / "result.json", result)
        return result
    freeze = _candidate_freeze(root)
    write_json(artifacts / "candidate_freeze.json", freeze)
    qualification_consumption = {
        "task_id": TASK_ID,
        "packet": "qualification",
        "consumed_once": True,
        "candidate_freeze_hash": freeze["combined_hash"],
        "packet_assignment_hash": sha256(artifacts / "packet_assignments.json"),
    }
    write_json(artifacts / "qualification_consumption.json", qualification_consumption)
    qualification = run_packet("qualification", packets["qualification"], trained, shuffled, root)
    if not qualification["result"]["summary"]["gate_pass"]:
        result = {
            "verdict": "QUALIFICATION_FAILED_REPLICATION_NOT_CONSUMED",
            "symbolic_pass": True,
            "search_gate_pass": True,
            "qualification_gate_pass": False,
            "qualification_consumed": True,
            "replication_consumed": False,
            "learner_implementation_authorized": False,
        }
        write_json(artifacts / "result.json", result)
        return result
    replication_consumption = {
        "task_id": TASK_ID,
        "packet": "replication",
        "consumed_once": True,
        "candidate_freeze_hash": freeze["combined_hash"],
        "packet_assignment_hash": sha256(artifacts / "packet_assignments.json"),
    }
    write_json(artifacts / "replication_consumption.json", replication_consumption)
    replication = run_packet("replication", packets["replication"], trained, shuffled, root)
    authorized = replication["result"]["summary"]["gate_pass"]
    verdict = (
        "PUBLIC_FEATURED_EXACT_HIERARCHICAL_TRANSFER_CAPACITY_ESTABLISHED"
        if authorized
        else "REPLICATION_FAILED_MINIMAL_LEARNER_NOT_AUTHORIZED"
    )
    result = {
        "task_id": TASK_ID,
        "verdict": verdict,
        "claim_ceiling": "exact finite benchmark reference capacity under the 001O public featured grammar only",
        "symbolic_pass": True,
        "search_gate_pass": True,
        "qualification_gate_pass": True,
        "replication_gate_pass": authorized,
        "qualification_consumed": True,
        "replication_consumed": True,
        "learner_implementation_authorized": authorized,
        "product_default_changed": False,
        "anonymous_permutation_negative_control_retained": True,
    }
    write_json(artifacts / "result.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("symbolic", "search", "full"), default="full")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    result = run_campaign(args.stage, args.root.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
