#!/usr/bin/env python3
"""Independent standard-library verifier for the frozen 001O row evidence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "EGO-V2-PUBLIC-FEATURED-COMPOSITIONAL-CAUSAL-TRANSFER-001O"
ARTIFACT_RELATIVE = Path("artifacts") / TASK_ID
FEATURE_COUNT = 5
SLOT_COUNT = 3
TARGET = 0.72
INITIAL_ENERGY = 0.5
INITIAL_SAFETY = 0.5
ENERGY_SCALE = 0.035
SAFETY_SCALE = 0.03
PASSIVE_ENERGY_DECAY = 0.008
INTERACTION_ENERGY_COST = 0.004
REST_ENERGY_COST = 0.002
REST_SAFETY_GAIN = 0.015
ENERGY_NOISE_VALUES = (-0.14, -0.07, 0.0, 0.07, 0.14)
SAFETY_NOISE_VALUES = (-0.12, -0.06, 0.0, 0.06, 0.12)
NOISE_PROBABILITIES = (0.10, 0.20, 0.40, 0.20, 0.10)
LOCAL_NAMES = ("normal", "full_reverse")
LOCAL_MULTIPLIERS = (1, -1)
LOCAL_PRIOR = (0.75, 0.25)
ACTUAL_MECHANISM_INDEX = 17
STEPS = 48
EARLY_STEPS = 24
FORBIDDEN_FIELDS = {
    "token_id", "combo_id", "permutation", "mapping", "world_id", "layout_id",
    "seed", "split", "global_mechanism", "local_mode", "oracle_action", "future",
}
UPDATING_ARMS = {
    "SCRATCH_EXACT_BAYES",
    "TRANSFER_EXACT_HIERARCHICAL_BAYES",
    "CUE_SHUFFLE",
    "FEATURE_ABLATION",
    "HISTORY_SHUFFLE",
}
CONTROL_FAIL_CLOSED_ARMS = {"CUE_SHUFFLE", "FEATURE_ABLATION", "HISTORY_SHUFFLE"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_root(root: Path = ROOT) -> Path:
    return root / ARTIFACT_RELATIVE


def _rotate(values: Sequence[int], amount: int) -> tuple[int, ...]:
    amount %= len(values)
    return tuple(values[amount:]) + tuple(values[:amount])


def mechanism_family() -> tuple[tuple[tuple[int, ...], tuple[int, ...]], ...]:
    energy_base = (2, 1, -1, -2, 1)
    safety_base = (-1, 2, 1, -1, -2)
    result = []
    for swap in (False, True):
        first, second = (safety_base, energy_base) if swap else (energy_base, safety_base)
        for rotation in range(FEATURE_COUNT):
            energy = _rotate(first, rotation)
            safety = _rotate(second, rotation)
            for energy_sign in (1, -1):
                for safety_sign in (1, -1):
                    result.append(
                        (
                            tuple(energy_sign * value for value in energy),
                            tuple(safety_sign * value for value in safety),
                        )
                    )
    if len(result) != 40 or len(set(result)) != 40:
        raise RuntimeError("independent mechanism construction mismatch")
    return tuple(result)


MECHANISMS = mechanism_family()


def _scan_private(payload: Any, path: str = "$") -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if str(key).lower() in FORBIDDEN_FIELDS:
                raise ValueError(f"private candidate field at {path}.{key}")
            _scan_private(value, f"{path}.{key}")
    elif isinstance(payload, (list, tuple)):
        for index, value in enumerate(payload):
            _scan_private(value, f"{path}[{index}]")


def validate_public_observation(observation: Any) -> None:
    _scan_private(observation)
    if not isinstance(observation, Mapping):
        raise ValueError("candidate observation is not a mapping")
    organism = observation.get("organism")
    slots = observation.get("slots")
    if not isinstance(organism, Mapping) or any(
        name not in organism for name in ("energy", "safety", "target")
    ):
        raise ValueError("candidate organism is incomplete")
    if not isinstance(slots, list) or len(slots) != SLOT_COUNT:
        raise ValueError("candidate slot count mismatch")
    for slot in slots:
        features = slot.get("features") if isinstance(slot, Mapping) else None
        if not isinstance(features, list) or len(features) != FEATURE_COUNT:
            raise ValueError("candidate feature vector shape mismatch")
        if any(value not in (0, 1) for value in features):
            raise ValueError("candidate feature vector is not binary")


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


def _latent_effect(
    mechanism_index: int, features: Sequence[int], mode_index: int
) -> tuple[float, float]:
    energy_weights, safety_weights = MECHANISMS[mechanism_index]
    centered = tuple(2 * int(value) - 1 for value in features)
    multiplier = LOCAL_MULTIPLIERS[mode_index]
    energy = ENERGY_SCALE * sum(weight * value for weight, value in zip(energy_weights, centered))
    safety = SAFETY_SCALE * sum(weight * value for weight, value in zip(safety_weights, centered))
    return multiplier * energy, multiplier * safety


def _interaction_after(
    mechanism_index: int,
    features: Sequence[int],
    mode_index: int,
    energy_before: float,
    safety_before: float,
    noise_energy: float,
    noise_safety: float,
) -> tuple[float, float]:
    latent_energy, latent_safety = _latent_effect(mechanism_index, features, mode_index)
    return (
        _clamp01(
            energy_before + latent_energy - PASSIVE_ENERGY_DECAY - INTERACTION_ENERGY_COST + noise_energy
        ),
        _clamp01(safety_before + latent_safety + noise_safety),
    )


def _rest_after(energy_before: float, safety_before: float) -> tuple[float, float]:
    return (
        _clamp01(energy_before - PASSIVE_ENERGY_DECAY - REST_ENERGY_COST),
        _clamp01(safety_before + REST_SAFETY_GAIN),
    )


def _key(energy: float, safety: float) -> tuple[float, float]:
    return round(float(energy), 12), round(float(safety), 12)


def _normalise(joint: Sequence[Sequence[float]]) -> list[list[float]]:
    total = sum(float(value) for row in joint for value in row)
    if total <= 0.0 or not math.isfinite(total):
        raise ValueError("posterior has zero or non-finite mass")
    return [[float(value) / total for value in row] for row in joint]


def new_state(shared: Sequence[float] | None = None) -> dict[str, Any]:
    if shared is None:
        shared = [1.0 / len(MECHANISMS)] * len(MECHANISMS)
    return {
        "joint": _normalise(
            [[float(probability) * LOCAL_PRIOR[0], float(probability) * LOCAL_PRIOR[1]] for probability in shared]
        ),
        "update_count": 0,
        "world_update_count": 0,
        "public_history_hash": canonical_hash([]),
    }


def aligned_state(mode: str) -> dict[str, Any]:
    joint = [[0.0, 0.0] for _ in MECHANISMS]
    joint[ACTUAL_MECHANISM_INDEX][LOCAL_NAMES.index(mode)] = 1.0
    return {
        "joint": joint,
        "update_count": 0,
        "world_update_count": 0,
        "public_history_hash": canonical_hash([]),
    }


def _entropy(state: Mapping[str, Any]) -> float:
    return -sum(
        probability * math.log2(probability)
        for row in state["joint"]
        for probability in row
        if probability > 0.0
    )


def state_receipt(state: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "state_hash": canonical_hash(state),
        "joint_hypotheses": 80,
        "support_hypotheses": sum(
            1 for row in state["joint"] for probability in row if probability > 1e-15
        ),
        "entropy_bits": _entropy(state),
        "update_count": int(state["update_count"]),
        "world_update_count": int(state["world_update_count"]),
    }


def reset_world(state: MutableMapping[str, Any]) -> None:
    shared = [sum(row) for row in state["joint"]]
    total_updates = int(state["update_count"])
    state.clear()
    state.update(new_state(shared))
    state["update_count"] = total_updates


def _likelihood(
    mechanism_index: int,
    mode_index: int,
    features: Sequence[int],
    feedback: Mapping[str, Any],
) -> float:
    expected_key = _key(feedback["energy_after"], feedback["safety_after"])
    likelihood = 0.0
    for noise_energy, probability_energy in zip(ENERGY_NOISE_VALUES, NOISE_PROBABILITIES):
        for noise_safety, probability_safety in zip(SAFETY_NOISE_VALUES, NOISE_PROBABILITIES):
            outcome = _interaction_after(
                mechanism_index,
                features,
                mode_index,
                float(feedback["energy_before"]),
                float(feedback["safety_before"]),
                noise_energy,
                noise_safety,
            )
            if _key(*outcome) == expected_key:
                likelihood += probability_energy * probability_safety
    return likelihood


def update_state(
    state: MutableMapping[str, Any],
    observation: Mapping[str, Any],
    action: str,
    feedback: Mapping[str, Any],
) -> None:
    if action == "rest":
        if _key(*_rest_after(float(feedback["energy_before"]), float(feedback["safety_before"]))) != _key(
            feedback["energy_after"], feedback["safety_after"]
        ):
            raise ValueError("rest feedback outside frozen grammar")
        updated = [list(row) for row in state["joint"]]
        features = None
    else:
        slot_index = int(action.rsplit("_", 1)[1])
        features = list(observation["slots"][slot_index]["features"])
        updated = [
            [
                float(probability) * _likelihood(mechanism_index, mode_index, features, feedback)
                for mode_index, probability in enumerate(row)
            ]
            for mechanism_index, row in enumerate(state["joint"])
        ]
    state["joint"] = _normalise(updated)
    state["update_count"] += 1
    state["world_update_count"] += 1
    state["public_history_hash"] = canonical_hash(
        {
            "previous_hash": state["public_history_hash"],
            "action": action,
            "features": features,
            "feedback": {
                name: feedback[name]
                for name in ("energy_before", "safety_before", "energy_after", "safety_after", "died")
            },
        }
    )


def _verify_feedback_grammar(row: Mapping[str, Any]) -> None:
    if "action" not in row or "public_observation" not in row:
        return
    action = row["action"]
    feedback = row["feedback"]
    if action == "rest":
        possible = {_key(*_rest_after(float(feedback["energy_before"]), float(feedback["safety_before"])))}
    else:
        slot_index = int(str(action).rsplit("_", 1)[1])
        features = row["public_observation"]["slots"][slot_index]["features"]
        mode_index = LOCAL_NAMES.index(row["evaluator_only"]["local_nuisance"])
        possible = {
            _key(
                *_interaction_after(
                    ACTUAL_MECHANISM_INDEX,
                    features,
                    mode_index,
                    float(feedback["energy_before"]),
                    float(feedback["safety_before"]),
                    noise_energy,
                    noise_safety,
                )
            )
            for noise_energy in ENERGY_NOISE_VALUES
            for noise_safety in SAFETY_NOISE_VALUES
        }
    if _key(feedback["energy_after"], feedback["safety_after"]) not in possible:
        raise ValueError("feedback outside frozen evaluator support")
    died = float(feedback["energy_after"]) <= 0.0 or float(feedback["safety_after"]) <= 0.0
    if bool(feedback["died"]) != died:
        raise ValueError("terminal flag mismatch")


def verify_row_integrity(row: Mapping[str, Any]) -> dict[str, Any]:
    expected_hash = canonical_hash({key: value for key, value in row.items() if key != "row_hash"})
    if row.get("row_hash") != expected_hash:
        raise ValueError("row hash mismatch")
    observation = row["candidate_observation"]
    validate_public_observation(observation)
    if canonical_hash(observation) != row["candidate_input_receipt"]:
        raise ValueError("candidate input receipt hash mismatch")
    feedback = row["feedback"]
    deficit = max(0.0, TARGET - float(feedback["energy_after"])) + max(
        0.0, TARGET - float(feedback["safety_after"])
    ) + (1.0 if feedback["died"] else 0.0)
    if not math.isclose(float(row["deficit_loss"]), deficit, abs_tol=1e-10):
        raise ValueError("deficit row recomputation mismatch")
    _verify_feedback_grammar(row)
    return {"pass": True, "row_hash": expected_hash, "deficit_loss": deficit}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def replay_training(events: Sequence[Mapping[str, Any]], shuffled: bool = False) -> dict[str, Any]:
    state = new_state()
    previous: Mapping[str, Any] | None = None
    for index, event in enumerate(events):
        if index and index % STEPS == 0:
            reset_world(state)
            previous = None
        observation = event["observation"]
        if shuffled and previous is None:
            previous = observation
            continue
        update_observation = previous if shuffled else observation
        try:
            update_state(state, update_observation, event["action"], event["feedback"])
        except ValueError as exc:
            if not shuffled or "zero or non-finite mass" not in str(exc):
                raise
            state = new_state()
        previous = observation
    reset_world(state)
    return state


def _initial_eval_state(
    arm: str,
    row: Mapping[str, Any],
    trained: Mapping[str, Any],
    shuffled: Mapping[str, Any],
) -> dict[str, Any]:
    if arm in ("PRIVATE_ORACLE", "PRIVATE_ALIGNED_REFERENCE"):
        return aligned_state(row["evaluator_only"]["local_nuisance"])
    if arm in ("SCRATCH_EXACT_BAYES", "UNIFORM_RANDOM", "SURFACE_LOOKUP"):
        return new_state()
    if arm == "HISTORY_SHUFFLE":
        return copy.deepcopy(shuffled)
    return copy.deepcopy(trained)


def verify_packet(root: Path, packet: str, trained: Mapping[str, Any], shuffled: Mapping[str, Any]) -> dict[str, Any]:
    artifacts = artifact_root(root)
    result = json.loads((artifacts / f"{packet}_result.json").read_text(encoding="utf-8"))
    rows = _load_jsonl(artifacts / result["rows_file"])
    if sha256(artifacts / result["rows_file"]) != result["rows_sha256"]:
        raise ValueError("rows file hash mismatch")
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        verify_row_integrity(row)
        groups.setdefault((row["opaque_world"], row["arm"]), []).append(row)
    trajectory_index = {
        (row["opaque_world"], row["arm"]): row for row in result["trajectory_summaries"]
    }
    posterior_receipt_matches = 0
    auc_matches = 0
    total_transitions = 0
    for key, group in groups.items():
        group.sort(key=lambda row: row["step"])
        state = _initial_eval_state(key[1], group[0], trained, shuffled)
        previous: Mapping[str, Any] | None = None
        for row in group:
            if state_receipt(state) != row["posterior_before"]:
                raise ValueError(f"posterior-before recomputation mismatch at {key} step {row['step']}")
            if key[1] in UPDATING_ARMS:
                update_observation = previous if key[1] == "HISTORY_SHUFFLE" and previous is not None else row[
                    "candidate_observation"
                ]
                try:
                    update_state(state, update_observation, row["action"], row["feedback"])
                except ValueError as exc:
                    if key[1] not in CONTROL_FAIL_CLOSED_ARMS or "zero or non-finite mass" not in str(exc):
                        raise
                    state = new_state()
            if state_receipt(state) != row["posterior_after"]:
                raise ValueError(f"posterior-after recomputation mismatch at {key} step {row['step']}")
            posterior_receipt_matches += 1
            total_transitions += 1
            previous = row["candidate_observation"]
        early = sum(float(row["deficit_loss"]) for row in group[:EARLY_STEPS])
        late = sum(float(row["deficit_loss"]) for row in group[EARLY_STEPS:])
        summary = trajectory_index[key]
        if not (
            math.isclose(early, float(summary["early_deficit_auc"]), abs_tol=1e-10)
            and math.isclose(late, float(summary["late_deficit_auc"]), abs_tol=1e-10)
            and math.isclose(early + late, float(summary["total_deficit_auc"]), abs_tol=1e-10)
        ):
            raise ValueError(f"trajectory AUC recomputation mismatch at {key}")
        auc_matches += 1
    return {
        "packet": packet,
        "pass": True,
        "rows": len(rows),
        "trajectories": len(groups),
        "posterior_receipts_recomputed": posterior_receipt_matches,
        "auc_trajectories_recomputed": auc_matches,
        "all_row_hashes_and_public_receipts_valid": True,
        "all_feedback_within_frozen_support": True,
    }


def verify_all(root: Path = ROOT) -> dict[str, Any]:
    artifacts = artifact_root(root)
    commitment = json.loads((artifacts / "packet_commitment.json").read_text(encoding="utf-8"))
    commitment_checks = {
        "packet_assignments_hash": sha256(artifacts / "packet_assignments.json")
        == commitment["packet_assignments_sha256"],
        "candidate_1_grammar_preserved": sha256(artifacts / "grammar_candidate_1.json")
        == commitment["candidate_1_grammar_sha256"],
        "candidate_2_grammar_hash": sha256(artifacts / "grammar_preregistration.json")
        == commitment["candidate_2_grammar_sha256"],
        "candidate_2_amendment_hash": sha256(artifacts / "candidate_2_amendment.json")
        == commitment["candidate_2_amendment_sha256"],
    }
    if not all(commitment_checks.values()):
        raise ValueError("packet or grammar commitment mismatch")
    training_path = artifacts / "training_public_history_rows.jsonl"
    events = _load_jsonl(training_path)
    trained = replay_training(events)
    shuffled = replay_training(events, shuffled=True)
    training_receipt = json.loads((artifacts / "training_public_history_receipt.json").read_text(encoding="utf-8"))
    training_checks = {
        "public_history_hash": canonical_hash(events) == training_receipt["public_history_receipt"],
        "candidate_state_receipt": state_receipt(trained) == training_receipt["candidate_state_receipt"],
        "private_fields_rejected": training_receipt["candidate_private_field_rejections"] == len(FORBIDDEN_FIELDS),
    }
    if not all(training_checks.values()):
        raise ValueError("training public-history replay mismatch")
    packet_reports = []
    for packet in ("search_dev", "qualification", "replication"):
        if (artifacts / f"{packet}_result.json").exists():
            packet_reports.append(verify_packet(root, packet, trained, shuffled))
    rows = _load_jsonl(artifacts / f"{packet_reports[0]['packet']}_rows.jsonl")
    tampered = copy.deepcopy(rows[0])
    tampered["deficit_loss"] += 0.01
    tamper_rejected = False
    try:
        verify_row_integrity(tampered)
    except ValueError:
        tamper_rejected = True
    leaked = copy.deepcopy(rows[0])
    leaked["candidate_observation"]["seed"] = 123
    leaked["candidate_input_receipt"] = canonical_hash(leaked["candidate_observation"])
    leaked["row_hash"] = canonical_hash({key: value for key, value in leaked.items() if key != "row_hash"})
    leakage_rejected = False
    try:
        verify_row_integrity(leaked)
    except ValueError:
        leakage_rejected = True
    positive_controls = {
        "row_tamper_rejected": tamper_rejected,
        "private_field_with_rehash_rejected": leakage_rejected,
    }
    report = {
        "task_id": TASK_ID,
        "verifier_independence": "standard_library_only_no_producer_import",
        "commitment_checks": commitment_checks,
        "training_recomputation_checks": training_checks,
        "packet_reports": packet_reports,
        "positive_controls": positive_controls,
        "pass": all(commitment_checks.values())
        and all(training_checks.values())
        and all(item["pass"] for item in packet_reports)
        and all(positive_controls.values()),
    }
    (artifacts / "independent_row_recomputation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (artifacts / "leakage_tamper_report.json").write_text(
        json.dumps(
            {
                "task_id": TASK_ID,
                "commitment_checks": commitment_checks,
                "positive_controls": positive_controls,
                "fail_closed": all(commitment_checks.values()) and all(positive_controls.values()),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    report = verify_all(args.root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
