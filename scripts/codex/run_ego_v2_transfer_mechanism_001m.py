"""Dev-only transfer-mechanism successor for the bounded Ego V2 microworld."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from labs.ego_life_playground_v0 import engine, homeostatic_transfer, microworld
from scripts.codex import run_ego_v2_public_acquisition_capacity_recovery_001k as capacity


TASK_ID = "EGO-V2-TRANSFER-MECHANISM-001M"
ARTIFACT_NAME = TASK_ID
CANDIDATES = (
    "M1_PERMUTATION_INVARIANT_GRAMMAR",
    "M2_CONCENTRATION_ONLY",
    "M3_ACQUISITION_POLICY_ONLY",
)
PUBLIC_ARMS = (
    "TRANSFER",
    "SCRATCH",
    "NO_TRANSFER",
    "SLOW_RESET",
    "FAST_RESET",
    "HISTORY_SHUFFLE",
    "NO_UPDATE",
    "PRIOR_CONTRADICTION",
    "UNCAPPED_TRANSFER",
)
DIAGNOSTIC_ARMS = (
    "UNIFORM_RANDOM",
    "PRIVATE_ORACLE_NAVIGATOR",
    "LATENT_ALIGNMENT_UPPER_BOUND",
)
ALL_ARMS = (*PUBLIC_ARMS, *DIAGNOSTIC_ARMS)
TRAINING_BUDGET = 96
EVALUATION_BUDGET = 96
EARLY_CUTOFF = 48
GAP_CHECKPOINTS = (8, 16, 24, 32, 48, 64, 80, 96)
CONFIDENCE_CAP = 2.0
SEARCH_RUN_ID = "history_shuffle_wiringfix"
PUBLIC_INPUT_FIELDS = homeostatic_transfer.PUBLIC_INPUT_FIELDS
PRIVATE_FIELD_NAMES = frozenset(
    {
        "world_id",
        "world_seed",
        "seed",
        "layout_id",
        "token_mapping",
        "mapping",
        "private_pose",
        "pose",
        "oracle_action",
        "split",
        "packet",
        "verdict",
        "future_outcome",
        "future",
    }
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(canonical_json(row) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(row) + "\n")


def artifact_root(root: Path) -> Path:
    return Path(root).resolve() / "artifacts" / ARTIFACT_NAME


def scan_candidate_input(payload: Any) -> dict[str, Any]:
    core = homeostatic_transfer.scan_public_input(payload)
    findings = [
        canonical_json(item) if isinstance(item, (Mapping, list)) else str(item)
        for item in core.get("findings", [])
    ]

    def visit(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                normalized = str(key).strip().lower()
                if normalized in PRIVATE_FIELD_NAMES:
                    findings.append(f"private_field:{path}.{normalized}")
                visit(item, f"{path}.{normalized}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, f"{path}[{index}]")

    visit(payload, "input")
    return {
        "schema_version": "ego.v2.transfer_mechanism.input_receipt.v1",
        "clean": bool(core.get("clean")) and not findings,
        "findings": sorted(set(findings)),
        "input_hash": canonical_hash(payload),
        "public_fields": list(PUBLIC_INPUT_FIELDS),
    }


def load_packets(root: Path) -> dict[str, list[dict[str, Any]]]:
    target = artifact_root(root)
    commitment = json.loads((target / "packet_commitment.json").read_text(encoding="utf-8"))
    packet_path = Path(root).resolve() / commitment["packet_path"]
    if sha256(packet_path) != commitment["packet_sha256"]:
        raise RuntimeError("001M packet commitment mismatch")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if (
        packet.get("task_id") != TASK_ID
        or packet.get("created_before_search_results") is not True
        or packet.get("original_001j_heldout") is not False
        or packet.get("product_001l_qualification") is not False
        or packet.get("world_grammar_changed") is not False
        or set(packet.get("splits", {}))
        != {"mechanism_training", "search_dev", "qualification"}
    ):
        raise RuntimeError("001M packet authority mismatch")
    seen_ids: set[str] = set()
    seen_seeds: set[int] = set()
    for split, specs in packet["splits"].items():
        for spec in specs:
            if spec.get("dev_only") is not True:
                raise RuntimeError(f"non-dev assignment in {split}")
            context = str(spec["opaque_context_id"])
            seed = int(spec["world_seed"])
            if context in seen_ids or seed in seen_seeds:
                raise RuntimeError("001M assignment collision")
            seen_ids.add(context)
            seen_seeds.add(seed)
            world = microworld.initial_world_state(
                seed=seed, layout_id=str(spec["layout_id"])
            )
            if dict(world["trial"]["token_mapping"]) != dict(
                spec["mapping_commitment"]
            ):
                raise RuntimeError("001M mapping commitment mismatch")
    return deepcopy(packet["splits"])


def audit_protected_predecessors(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    protected = json.loads(
        (artifact_root(root) / "protected_predecessor_hashes.json").read_text(
            encoding="utf-8"
        )
    )
    findings: list[str] = []
    checked = 0
    for files in protected["protected_trees"].values():
        for relative, expected in files.items():
            path = root / relative
            checked += 1
            if not path.is_file() or sha256(path) != expected:
                findings.append(relative)
    return {
        "schema_version": "ego.v2.transfer_mechanism.protected_audit.v1",
        "checked_file_count": checked,
        "findings": findings,
        "passed": not findings,
    }


def _signature(delta: Mapping[str, float]) -> str:
    def sign(value: float) -> str:
        return "+" if value > 1e-9 else "-" if value < -1e-9 else "0"

    return f"energy:{sign(float(delta['energy']))}|safety:{sign(float(delta['safety']))}"


def _signature_parts(signature: str) -> tuple[str, str]:
    parts = signature.split("|")
    return parts[0].split(":", 1)[1], parts[1].split(":", 1)[1]


def neutral_slow_meta(candidate_id: str) -> dict[str, Any]:
    if candidate_id == CANDIDATES[0]:
        payload = {
            "mechanism": "permutation_invariant_effect_grammar",
            "signature_multiplicity": {},
            "confidence": 0.0,
            "training_world_count": 0,
        }
    elif candidate_id == CANDIDATES[1]:
        payload = {
            "mechanism": "neutral_concentration_only",
            "prior_concentration": 0.0,
            "confidence": 0.0,
            "training_world_count": 0,
        }
    elif candidate_id == CANDIDATES[2]:
        payload = {
            "mechanism": "safe_acquisition_policy_only",
            "safe_margin_floor": 0.0,
            "unknown_probe_bonus": 0.0,
            "harm_rate": 0.0,
            "confidence": 0.0,
            "training_world_count": 0,
        }
    else:
        raise ValueError("unknown 001M candidate")
    return {
        "schema_version": "ego.v2.transfer_mechanism.slow_meta.v1",
        "candidate_id": candidate_id,
        **payload,
    }


def _validate_slow_meta(meta: Mapping[str, Any]) -> None:
    candidate_id = str(meta.get("candidate_id"))
    if candidate_id not in CANDIDATES:
        raise ValueError("invalid transfer candidate meta")
    encoded = canonical_json(meta).lower()
    forbidden = (
        "world_id",
        "world_seed",
        "layout_id",
        "mapping",
        '"token',
        "energy_mean",
        "safety_mean",
        "predicted_delta",
    )
    if any(item in encoded for item in forbidden):
        raise ValueError("slow transfer meta contains identity or consequence mean")


def empty_candidate_state(
    candidate_id: str,
    slow_meta: Mapping[str, Any],
    *,
    transfer_enabled: bool = True,
    confidence_capped: bool = True,
) -> dict[str, Any]:
    _validate_slow_meta(slow_meta)
    if str(slow_meta["candidate_id"]) != candidate_id:
        raise ValueError("candidate/meta mismatch")
    state = {
        "schema_version": "ego.v2.transfer_mechanism.candidate_state.v1",
        "candidate_id": candidate_id,
        "slow_meta": deepcopy(dict(slow_meta)),
        "fast_model": homeostatic_transfer.empty_state(),
        "fast_meta": {
            "observed_signature_counts": {},
            "observed_public_entities": [],
            "unique_interaction_count": 0,
            "harm_count": 0,
            "beneficial_count": 0,
            "contradiction_evidence": 0,
        },
        "transfer_enabled": bool(transfer_enabled),
        "confidence_capped": bool(confidence_capped),
        "update_count": 0,
    }
    validate_candidate_state(state)
    return state


def validate_candidate_state(state: Mapping[str, Any]) -> None:
    if set(state) != {
        "schema_version",
        "candidate_id",
        "slow_meta",
        "fast_model",
        "fast_meta",
        "transfer_enabled",
        "confidence_capped",
        "update_count",
    }:
        raise ValueError("candidate state schema mismatch")
    if state["schema_version"] != "ego.v2.transfer_mechanism.candidate_state.v1":
        raise ValueError("candidate state version mismatch")
    if state["candidate_id"] not in CANDIDATES:
        raise ValueError("candidate state id invalid")
    _validate_slow_meta(state["slow_meta"])
    homeostatic_transfer.validate_state(state["fast_model"])
    if type(state["transfer_enabled"]) is not bool or type(
        state["confidence_capped"]
    ) is not bool:
        raise ValueError("candidate state switches invalid")


def candidate_state_hash(state: Mapping[str, Any]) -> str:
    validate_candidate_state(state)
    return canonical_hash(state)


def _initial_organism() -> dict[str, float]:
    return {
        "energy": float(engine.INITIAL_ORGANISM["energy"]),
        "safety": float(engine.INITIAL_ORGANISM["safety"]),
    }


def _public_payload(
    world: Mapping[str, Any],
    organism: Mapping[str, float],
    last_action: str | None,
    last_delta: Mapping[str, float],
) -> dict[str, Any]:
    return {
        "observation": microworld.policy_observation(world, occlusion=False),
        "organism": {
            "energy": float(organism["energy"]),
            "safety": float(organism["safety"]),
        },
        "last_action": last_action,
        "last_delta": {
            "energy": float(last_delta["energy"]),
            "safety": float(last_delta["safety"]),
        },
    }


def _front_public_entity(public_input: Mapping[str, Any]) -> str | None:
    value = str(public_input["observation"]["visual"][1][2])
    return value if value in microworld.TOKENS else None


def _visible_entities(public_input: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for y, visual_row in enumerate(public_input["observation"]["visual"]):
        for x, value in enumerate(visual_row):
            if value in microworld.TOKENS:
                rows.append(
                    {
                        "entity": str(value),
                        "relative_x": x - 2,
                        "relative_y": y - 2,
                        "distance": abs(x - 2) + abs(y - 2),
                    }
                )
    return rows


def _effective_confidence(state: Mapping[str, Any]) -> float:
    if not state["transfer_enabled"]:
        return 0.0
    raw = float(state["slow_meta"].get("confidence", 0.0))
    if state["confidence_capped"]:
        raw = min(CONFIDENCE_CAP, raw)
    evidence = int(state["fast_meta"]["contradiction_evidence"])
    return round(raw / (1.0 + 0.5 * evidence), 12)


def _known_value(
    row: Mapping[str, Any],
    organism: Mapping[str, float],
    distance: int,
) -> float:
    drive = {
        key: max(0.0, engine.TARGET_LEVEL - float(organism[key]))
        for key in ("energy", "safety")
    }
    value = sum(drive[key] * float(row[f"{key}_mean"]) for key in drive)
    value += 0.05 / math.sqrt(int(row["count"]) + 1.0)
    value -= 0.50 * float(row["terminal_count"]) / max(1, int(row["count"]))
    return round(value - 0.004 * distance, 12)


def _grammar_unknown_adjustment(
    state: Mapping[str, Any], organism: Mapping[str, float]
) -> float:
    counts = Counter(
        {
            str(key): int(value)
            for key, value in state["slow_meta"]["signature_multiplicity"].items()
        }
    )
    counts.subtract(
        {
            str(key): int(value)
            for key, value in state["fast_meta"]["observed_signature_counts"].items()
        }
    )
    remaining = [signature for signature, count in counts.items() for _ in range(max(0, count))]
    if not remaining:
        return -0.02 * _effective_confidence(state)
    dominant = max(
        ("energy", "safety"),
        key=lambda key: max(0.0, engine.TARGET_LEVEL - float(organism[key])),
    )
    index = 0 if dominant == "energy" else 1
    beneficial_remaining = sum(_signature_parts(signature)[index] == "+" for signature in remaining)
    if beneficial_remaining:
        return 0.025 * _effective_confidence(state)
    return -0.025 * _effective_confidence(state)


def _unknown_adjustment(state: Mapping[str, Any], organism: Mapping[str, float]) -> float:
    candidate_id = str(state["candidate_id"])
    confidence = _effective_confidence(state)
    if confidence <= 0.0:
        return 0.0
    if candidate_id == CANDIDATES[0]:
        return _grammar_unknown_adjustment(state, organism)
    if candidate_id == CANDIDATES[1]:
        concentration = float(state["slow_meta"]["prior_concentration"])
        if state["confidence_capped"]:
            concentration = min(CONFIDENCE_CAP, concentration)
        return round(-0.012 * concentration / (1.0 + int(state["fast_meta"]["unique_interaction_count"])), 12)
    safe_floor = float(state["slow_meta"]["safe_margin_floor"])
    margin = min(float(organism["energy"]), float(organism["safety"]))
    bonus = float(state["slow_meta"]["unknown_probe_bonus"])
    if margin >= safe_floor:
        return round(bonus * min(1.0, confidence / CONFIDENCE_CAP), 12)
    return round(-max(0.02, bonus) * min(1.0, confidence / CONFIDENCE_CAP), 12)


def _navigation_action(target: Mapping[str, Any], public_input: Mapping[str, Any]) -> tuple[str, str]:
    front = str(public_input["observation"]["visual"][1][2])
    x = int(target["relative_x"])
    y = int(target["relative_y"])
    if y == -1 and x == 0:
        return "interact", "transfer_target_front"
    if y < 0 and front == "empty":
        return "move_forward", "approach_transfer_target"
    if x < 0:
        return "turn_left", "orient_transfer_target"
    if x > 0:
        return "turn_right", "orient_transfer_target"
    return "turn_right", "rotate_to_transfer_target"


def plan_action(
    state: Mapping[str, Any], *, public_input: Mapping[str, Any], sequence: int
) -> dict[str, Any]:
    validate_candidate_state(state)
    scan = scan_candidate_input(public_input)
    if not scan["clean"]:
        raise ValueError("candidate public input rejected")
    base = homeostatic_transfer.plan_action(
        state["fast_model"],
        public_input=public_input,
        sequence=sequence,
        mode="public_bayes",
        drive_mode="canonical",
        posterior_mode="canonical",
        action_costs=engine.ACTION_COSTS,
        target_level=engine.TARGET_LEVEL,
    )
    plan = deepcopy(base)
    plan.update(
        {
            "schema_version": "ego.v2.transfer_mechanism.plan.v1",
            "candidate_id": state["candidate_id"],
            "candidate_state_hash_before": candidate_state_hash(state),
            "public_input_clean": True,
            "public_input_hash": scan["input_hash"],
            "transfer_enabled": state["transfer_enabled"],
            "transfer_variable": state["slow_meta"]["mechanism"],
            "cross_world_effect_mean_applied": False,
            "raw_prior_confidence": float(state["slow_meta"].get("confidence", 0.0)),
            "effective_prior_confidence": _effective_confidence(state),
        }
    )
    if _effective_confidence(state) <= 0.0:
        plan["transfer_selection_applied"] = False
        return plan

    known = state["fast_model"]["fast_state"]["token_stats"]
    ranked = []
    for item in _visible_entities(public_input):
        entity = item["entity"]
        if entity in known:
            score = _known_value(known[entity], public_input["organism"], item["distance"])
            source = "current_world_public_posterior"
        else:
            score = round(
                0.04
                - 0.004 * int(item["distance"])
                + _unknown_adjustment(state, public_input["organism"]),
                12,
            )
            source = "transfer_acquisition_only"
        ranked.append({**item, "known": entity in known, "score": score, "source": source})
    ranked.sort(key=lambda row: (-float(row["score"]), int(row["distance"]), str(row["entity"])))
    plan["transfer_ranked_entities"] = ranked
    plan["transfer_selection_applied"] = bool(ranked)
    if not ranked:
        return plan
    target = ranked[0]
    front = _front_public_entity(public_input)
    front_row = next((row for row in ranked if row["entity"] == front), None)
    if front_row is not None:
        if front_row["known"] and float(front_row["score"]) <= 0.0:
            action, reason = "turn_right", "current_world_posterior_rejects_front"
        elif not front_row["known"] and float(front_row["score"]) <= 0.0:
            action, reason = "turn_right", "transfer_acquisition_rejects_front_probe"
        else:
            action, reason = "interact", "transfer_acquisition_front_probe_or_use"
            target = front_row
    else:
        action, reason = _navigation_action(target, public_input)
    plan["selected_action"] = action
    plan["selection_reason"] = reason
    plan["selected_target"] = target["entity"]
    plan["action_values"] = {
        key: round(float(value) + (1.0 if key == action else 0.0), 12)
        for key, value in base["action_values"].items()
    }
    return plan


def update_after_transition(
    state: Mapping[str, Any],
    *,
    public_input: Mapping[str, Any],
    selected_action: str,
    observed_outcome_type: str,
    actual_delta: Mapping[str, float],
    terminal: bool,
    updates_enabled: bool,
    feedback_mode: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_candidate_state(state)
    scan = scan_candidate_input(public_input)
    if not scan["clean"]:
        raise ValueError("candidate update input rejected")
    updated = deepcopy(dict(state))
    fast_model, core_receipt = homeostatic_transfer.update_after_transition(
        updated["fast_model"],
        public_input=public_input,
        selected_action=selected_action,
        observed_outcome_type=observed_outcome_type,
        actual_delta=actual_delta,
        terminal=terminal,
        updates_enabled=updates_enabled,
        feedback_mode=feedback_mode,
    )
    # This successor deliberately keeps consequence means world-local. The
    # canonical update is real, but its slow consequence accumulator is scrubbed
    # after every update while the fast posterior remains intact.
    updated["fast_model"] = homeostatic_transfer.reset_slow_state(fast_model)
    if updates_enabled:
        updated["update_count"] = int(updated["update_count"]) + 1
        # Use the exact entity to which the canonical updater attributed the
        # feedback. Otherwise HISTORY_SHUFFLE would corrupt the posterior while
        # leaking the unshuffled pairing through this candidate fast metadata.
        entity = core_receipt.get("updated_token")
        if selected_action == "interact" and entity is not None:
            seen = updated["fast_meta"]["observed_public_entities"]
            if entity not in seen:
                seen.append(entity)
                signature = _signature(actual_delta)
                counts = updated["fast_meta"]["observed_signature_counts"]
                counts[signature] = int(counts.get(signature, 0)) + 1
                updated["fast_meta"]["unique_interaction_count"] += 1
                updated["fast_meta"]["contradiction_evidence"] += 1
            harmful = float(actual_delta["energy"]) < -0.03 or float(actual_delta["safety"]) < -0.03
            beneficial = float(actual_delta["energy"]) > 0.03 or float(actual_delta["safety"]) > 0.03
            updated["fast_meta"]["harm_count"] += int(harmful)
            updated["fast_meta"]["beneficial_count"] += int(beneficial)
    validate_candidate_state(updated)
    receipt = {
        "schema_version": "ego.v2.transfer_mechanism.update_receipt.v1",
        "public_input_clean": True,
        "public_input_hash": scan["input_hash"],
        "selected_action": selected_action,
        "actual_delta": dict(actual_delta),
        "updates_enabled": bool(updates_enabled),
        "feedback_mode": feedback_mode,
        "core_update_receipt_hash": canonical_hash(core_receipt),
        "cross_world_effect_mean_stored": False,
        "candidate_state_hash_after": candidate_state_hash(updated),
    }
    return updated, receipt


def reset_for_respawn(state: Mapping[str, Any]) -> dict[str, Any]:
    updated = deepcopy(dict(state))
    updated["fast_model"] = homeostatic_transfer.reset_for_respawn(updated["fast_model"])
    validate_candidate_state(updated)
    return updated


def reset_fast_state(state: Mapping[str, Any]) -> dict[str, Any]:
    return empty_candidate_state(
        str(state["candidate_id"]),
        state["slow_meta"],
        transfer_enabled=bool(state["transfer_enabled"]),
        confidence_capped=bool(state["confidence_capped"]),
    )


def _deficit_loss(organism: Mapping[str, float], *, died: bool) -> float:
    return round(
        sum(max(0.0, engine.TARGET_LEVEL - float(organism[key])) for key in ("energy", "safety"))
        + (0.75 if died else 0.0),
        12,
    )


def _random_action(context: str, candidate_id: str, sequence: int) -> str:
    digest = hashlib.sha256(f"{TASK_ID}:{context}:{candidate_id}:{sequence}:random".encode()).digest()
    return microworld.ACTIONS[int.from_bytes(digest[:4], "big") % len(microworld.ACTIONS)]


def _expected_interaction_delta(cause: str) -> dict[str, float]:
    delta = engine.CAUSE_DELTAS[cause]
    return {
        "energy": round(
            -engine.PASSIVE_ENERGY_DECAY_PER_TICK
            - engine.ACTION_COSTS["interact"]
            + (float(delta["energy"]) if cause == "resource" else 0.0),
            12,
        ),
        "safety": round(float(delta["safety"]), 12),
    }


def effect_sign_accuracy(state: Mapping[str, Any], mapping: Mapping[str, str]) -> float:
    correct = 0
    for entity in microworld.TOKENS:
        row = state["fast_model"]["fast_state"]["token_stats"].get(entity)
        if row is None:
            continue
        expected = _expected_interaction_delta(str(mapping[entity]))
        observed_signature = _signature(
            {"energy": float(row["energy_mean"]), "safety": float(row["safety_mean"])}
        )
        expected_signature = _signature(expected)
        observed_parts = _signature_parts(observed_signature)
        expected_parts = _signature_parts(expected_signature)
        correct += int(observed_parts[0] == expected_parts[0])
        correct += int(observed_parts[1] == expected_parts[1])
    return round(correct / (2 * len(microworld.TOKENS)), 12)


def _collect_training_world(spec: Mapping[str, Any]) -> dict[str, Any]:
    world = microworld.initial_world_state(
        seed=int(spec["world_seed"]), layout_id=str(spec["layout_id"])
    )
    model = homeostatic_transfer.empty_state()
    organism = _initial_organism()
    last_action = None
    last_delta = {"energy": 0.0, "safety": 0.0}
    seen: set[str] = set()
    signature_counts: Counter[str] = Counter()
    first_interactions: list[dict[str, Any]] = []
    repeated_match = 0
    repeated_total = 0
    public_receipts: list[str] = []
    last_signature_by_entity: dict[str, str] = {}
    run_meta = {"run_id": f"{TASK_ID}:training:{spec['opaque_context_id']}", "seed": int(spec["world_seed"])}
    code_hash = engine.compute_code_path_hash()
    for sequence in range(1, TRAINING_BUDGET + 1):
        payload = _public_payload(world, organism, last_action, last_delta)
        scan = scan_candidate_input(payload)
        if not scan["clean"]:
            raise RuntimeError("training public receipt failed")
        public_receipts.append(scan["input_hash"])
        plan = homeostatic_transfer.plan_action(
            model,
            public_input=payload,
            sequence=sequence,
            mode="public_bayes",
            drive_mode="canonical",
            posterior_mode="canonical",
            action_costs=engine.ACTION_COSTS,
            target_level=engine.TARGET_LEVEL,
        )
        action = str(plan["selected_action"])
        world_before = deepcopy(world)
        command_hash = canonical_hash({"context": spec["opaque_context_id"], "sequence": sequence, "action": action})
        world, transition = microworld.transition_world(
            world_before,
            action,
            source_sequence=sequence,
            source_episode_id="001m-training",
            source_command_hash=command_hash,
        )
        actual = engine.compute_actual_delta(transition, selected_action=action)
        metabolism = engine.compute_metabolism_ledger(
            energy_before=float(organism["energy"]),
            selected_action=action,
            world_before=world_before,
            world_after=world,
            world_transition=transition,
            run_meta=run_meta,
            episode_id="001m-training",
            command_hash=command_hash,
            code_path_hash=code_hash,
        )
        actual_delta = {"energy": float(metabolism["energy_delta"]), "safety": float(actual["safety"])}
        entity = _front_public_entity(payload)
        if action == "interact" and entity is not None:
            signature = _signature(actual_delta)
            if entity not in seen:
                seen.add(entity)
                signature_counts[signature] += 1
                margin = min(float(payload["organism"]["energy"]), float(payload["organism"]["safety"]))
                first_interactions.append(
                    {
                        "margin": margin,
                        "harmful": float(actual_delta["energy"]) < -0.03 or float(actual_delta["safety"]) < -0.03,
                        "beneficial": float(actual_delta["energy"]) > 0.03 or float(actual_delta["safety"]) > 0.03,
                    }
                )
            elif entity in last_signature_by_entity:
                repeated_total += 1
                repeated_match += int(last_signature_by_entity[entity] == signature)
            last_signature_by_entity[entity] = signature
        model, _ = homeostatic_transfer.update_after_transition(
            model,
            public_input=payload,
            selected_action=action,
            observed_outcome_type=str(transition["outcome_type"]),
            actual_delta=actual_delta,
            terminal=False,
            updates_enabled=True,
            feedback_mode="canonical",
        )
        model = homeostatic_transfer.reset_slow_state(model)
        organism = {
            key: round(max(0.0, min(1.0, organism[key] + actual_delta[key])), 12)
            for key in ("energy", "safety")
        }
        last_action, last_delta = action, actual_delta
        if organism["energy"] == 0.0:
            world = microworld.reset_world_for_life(world, int(world["trial"]["life_index"]) + 1)
            organism = _initial_organism()
            model = homeostatic_transfer.reset_for_respawn(model)
    return {
        "signature_counts": dict(signature_counts),
        "first_interactions": first_interactions,
        "repeated_match": repeated_match,
        "repeated_total": repeated_total,
        "public_receipt_chain_hash": canonical_hash(public_receipts),
        "public_receipt_count": len(public_receipts),
    }


def collect_training_dataset(specs: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [_collect_training_world(spec) for spec in specs]


def train_transfer_meta(candidate_id: str, dataset: list[Mapping[str, Any]]) -> dict[str, Any]:
    meta = neutral_slow_meta(candidate_id)
    meta["training_world_count"] = len(dataset)
    meta["confidence"] = float(len(dataset))
    if candidate_id == CANDIDATES[0]:
        all_signatures = sorted(
            {signature for world in dataset for signature in world["signature_counts"]}
        )
        multiplicity = {}
        for signature in all_signatures:
            values = sorted(int(world["signature_counts"].get(signature, 0)) for world in dataset)
            multiplicity[signature] = int(values[len(values) // 2])
        meta["signature_multiplicity"] = multiplicity
    elif candidate_id == CANDIDATES[1]:
        matches = sum(int(world["repeated_match"]) for world in dataset)
        total = sum(int(world["repeated_total"]) for world in dataset)
        reliability = (matches + 1.0) / (total + 2.0)
        meta["prior_concentration"] = round(1.0 + 7.0 * reliability, 12)
    else:
        interactions = [row for world in dataset for row in world["first_interactions"]]
        safe = sorted(float(row["margin"]) for row in interactions if not row["harmful"])
        meta["safe_margin_floor"] = round(safe[len(safe) // 4] if safe else 0.25, 12)
        beneficial_rate = sum(bool(row["beneficial"]) for row in interactions) / max(1, len(interactions))
        harm_rate = sum(bool(row["harmful"]) for row in interactions) / max(1, len(interactions))
        meta["unknown_probe_bonus"] = round(max(0.0, 0.06 * beneficial_rate - 0.04 * harm_rate), 12)
        meta["harm_rate"] = round(harm_rate, 12)
    _validate_slow_meta(meta)
    return meta


def _contradicted_meta(meta: Mapping[str, Any]) -> dict[str, Any]:
    changed = deepcopy(dict(meta))
    candidate_id = str(changed["candidate_id"])
    if candidate_id == CANDIDATES[0]:
        rebuilt = {}
        for signature, count in changed["signature_multiplicity"].items():
            energy, safety = _signature_parts(signature)
            invert = lambda value: "-" if value == "+" else "+" if value == "-" else "0"
            rebuilt[f"energy:{invert(energy)}|safety:{invert(safety)}"] = int(count)
        changed["signature_multiplicity"] = rebuilt
    elif candidate_id == CANDIDATES[1]:
        changed["prior_concentration"] = 24.0
    else:
        changed["safe_margin_floor"] = 0.0
        changed["unknown_probe_bonus"] = 0.12
        changed["harm_rate"] = 0.0
    changed["confidence"] = 24.0
    _validate_slow_meta(changed)
    return changed


def _state_for_arm(candidate_id: str, trained_meta: Mapping[str, Any], arm: str) -> dict[str, Any] | None:
    if arm in {"UNIFORM_RANDOM", "PRIVATE_ORACLE_NAVIGATOR"}:
        return None
    meta = deepcopy(dict(trained_meta))
    transfer_enabled = arm not in {"SCRATCH", "NO_TRANSFER", "SLOW_RESET"}
    capped = arm != "UNCAPPED_TRANSFER"
    if arm in {"SCRATCH", "SLOW_RESET"}:
        meta = neutral_slow_meta(candidate_id)
    elif arm == "PRIOR_CONTRADICTION":
        meta = _contradicted_meta(meta)
    return empty_candidate_state(
        candidate_id,
        meta,
        transfer_enabled=transfer_enabled,
        confidence_capped=capped,
    )


def _evaluator_aligned_reference_state(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Build evaluator-owned aligned reference state, never candidate state."""

    state = homeostatic_transfer.empty_state()
    for entity in microworld.TOKENS:
        visual = [["empty"] * 5 for _ in range(5)]
        visual[2][2] = "self"
        visual[1][2] = entity
        payload = {
            "observation": {
                "schema_version": microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION,
                "visual": visual,
            },
            "organism": {"energy": 0.5, "safety": 0.5},
            "last_action": None,
            "last_delta": {"energy": 0.0, "safety": 0.0},
        }
        state, _ = homeostatic_transfer.update_after_transition(
            state,
            public_input=payload,
            selected_action="interact",
            observed_outcome_type="interacted",
            actual_delta=_expected_interaction_delta(
                str(spec["mapping_commitment"][entity])
            ),
            terminal=False,
            updates_enabled=True,
            feedback_mode="canonical",
        )
    return homeostatic_transfer.reset_slow_state(state)


def _evaluator_latent_alignment_action(
    reference_state: Mapping[str, Any],
    public_input: Mapping[str, Any],
    sequence: int,
) -> str:
    """Private diagnostic upper bound that never enters candidate state.

    The evaluator-owned reference aligns anonymous entities to their correct
    effects and calls the canonical fixed planner directly. Candidate state and
    the candidate wrapper are never involved, and the arm is excluded from all
    public gates.
    """

    plan = homeostatic_transfer.plan_action(
        reference_state,
        public_input=public_input,
        sequence=sequence,
        mode="public_bayes",
        drive_mode="canonical",
        posterior_mode="canonical",
        action_costs=engine.ACTION_COSTS,
        target_level=engine.TARGET_LEVEL,
    )
    return str(plan["selected_action"])


def run_trajectory(
    spec: Mapping[str, Any],
    *,
    candidate_id: str,
    arm: str,
    trained_meta: Mapping[str, Any],
    budget: int,
) -> dict[str, Any]:
    if candidate_id not in CANDIDATES or arm not in ALL_ARMS:
        raise ValueError("unknown 001M trajectory")
    world = microworld.initial_world_state(seed=int(spec["world_seed"]), layout_id=str(spec["layout_id"]))
    if dict(world["trial"]["token_mapping"]) != dict(spec["mapping_commitment"]):
        raise RuntimeError("trajectory mapping commitment mismatch")
    state = (
        None
        if arm == "LATENT_ALIGNMENT_UPPER_BOUND"
        else _state_for_arm(candidate_id, trained_meta, arm)
    )
    evaluator_reference_state = (
        _evaluator_aligned_reference_state(spec)
        if arm == "LATENT_ALIGNMENT_UPPER_BOUND"
        else None
    )
    organism = _initial_organism()
    last_action = None
    last_delta = {"energy": 0.0, "safety": 0.0}
    previous_hash = None
    rows: list[dict[str, Any]] = []
    life_index = 1
    run_meta = {"run_id": f"{TASK_ID}:{candidate_id}:{spec['opaque_context_id']}:{arm}", "seed": int(spec["world_seed"])}
    code_hash = engine.compute_code_path_hash()
    evaluator_private = arm in {"PRIVATE_ORACLE_NAVIGATOR", "LATENT_ALIGNMENT_UPPER_BOUND"}
    for sequence in range(1, budget + 1):
        if arm == "FAST_RESET" and sequence > 1:
            assert state is not None
            state = reset_fast_state(state)
        payload = _public_payload(world, organism, last_action, last_delta)
        scan = scan_candidate_input(payload)
        if not scan["clean"]:
            raise RuntimeError("trajectory public input leakage")
        if arm == "UNIFORM_RANDOM":
            action = _random_action(str(spec["opaque_context_id"]), candidate_id, sequence)
            plan = None
        elif arm == "PRIVATE_ORACLE_NAVIGATOR":
            action = capacity._oracle_action(world, organism)
            plan = None
        elif arm == "LATENT_ALIGNMENT_UPPER_BOUND":
            assert evaluator_reference_state is not None
            action = _evaluator_latent_alignment_action(
                evaluator_reference_state, payload, sequence
            )
            plan = None
        else:
            assert state is not None
            plan = plan_action(state, public_input=payload, sequence=sequence)
            action = str(plan["selected_action"])
        command_hash = canonical_hash(
            {
                "candidate_id": candidate_id,
                "context": spec["opaque_context_id"],
                "arm": arm,
                "sequence": sequence,
                "action": action,
                "previous": previous_hash,
            }
        )
        world_before = deepcopy(world)
        world, transition = microworld.transition_world(
            world_before,
            action,
            source_sequence=sequence,
            source_episode_id=f"001m-life-{life_index}",
            source_command_hash=command_hash,
        )
        actual = engine.compute_actual_delta(transition, selected_action=action)
        metabolism = engine.compute_metabolism_ledger(
            energy_before=float(organism["energy"]),
            selected_action=action,
            world_before=world_before,
            world_after=world,
            world_transition=transition,
            run_meta=run_meta,
            episode_id=f"001m-life-{life_index}",
            command_hash=command_hash,
            code_path_hash=code_hash,
        )
        actual_delta = {"energy": float(metabolism["energy_delta"]), "safety": float(actual["safety"])}
        organism = {
            key: round(max(0.0, min(1.0, organism[key] + actual_delta[key])), 12)
            for key in ("energy", "safety")
        }
        died = organism["energy"] == 0.0
        update_receipt = None
        if state is not None:
            state, update_receipt = update_after_transition(
                state,
                public_input=payload,
                selected_action=action,
                observed_outcome_type=str(transition["outcome_type"]),
                actual_delta=actual_delta,
                terminal=died,
                updates_enabled=arm != "NO_UPDATE",
                feedback_mode="shuffle" if arm == "HISTORY_SHUFFLE" else "canonical",
            )
        row_without_hash = {
            "schema_version": "ego.v2.transfer_mechanism.row.v1",
            "task_id": TASK_ID,
            "candidate_id": candidate_id,
            "opaque_context_id": spec["opaque_context_id"],
            "arm": arm,
            "sequence": sequence,
            "public_input_clean": scan["clean"],
            "public_input_hash": scan["input_hash"],
            "public_input_fields": list(PUBLIC_INPUT_FIELDS),
            "evaluator_private": evaluator_private,
            "selected_action": action,
            "selection_reason": None if plan is None else plan["selection_reason"],
            "transfer_selection_applied": None if plan is None else plan.get("transfer_selection_applied", False),
            "cross_world_effect_mean_applied": None if plan is None else plan["cross_world_effect_mean_applied"],
            "raw_prior_confidence": None if plan is None else plan["raw_prior_confidence"],
            "effective_prior_confidence": None if plan is None else plan["effective_prior_confidence"],
            "predictions_hash": None if plan is None else plan["predictions_hash"],
            "actual_delta": actual_delta,
            "outcome_type": transition["outcome_type"],
            "energy_after": organism["energy"],
            "safety_after": organism["safety"],
            "died": died,
            "deficit_loss": _deficit_loss(organism, died=died),
            "effect_sign_accuracy": None if state is None else effect_sign_accuracy(state, spec["mapping_commitment"]),
            "candidate_state_hash": None if state is None else candidate_state_hash(state),
            "fast_model_hash": None if state is None else homeostatic_transfer.state_hash(state["fast_model"]),
            "update_receipt_hash": None if update_receipt is None else canonical_hash(update_receipt),
            "prev_trace_hash": previous_hash,
        }
        trace_hash = canonical_hash(row_without_hash)
        row = {**row_without_hash, "trace_hash": trace_hash}
        rows.append(row)
        previous_hash = trace_hash
        last_action, last_delta = action, actual_delta
        if died:
            life_index += 1
            world = microworld.reset_world_for_life(world, life_index)
            organism = _initial_organism()
            if state is not None:
                state = reset_for_respawn(state)
    early = rows[: min(EARLY_CUTOFF, len(rows))]
    late = rows[min(EARLY_CUTOFF, len(rows)) :]
    curve = {
        str(checkpoint): round(sum(float(row["deficit_loss"]) for row in rows[: min(checkpoint, len(rows))]), 12)
        for checkpoint in GAP_CHECKPOINTS
        if checkpoint <= budget
    }
    return {
        "candidate_id": candidate_id,
        "opaque_context_id": spec["opaque_context_id"],
        "arm": arm,
        "budget": budget,
        "early_deficit_auc": round(sum(float(row["deficit_loss"]) for row in early), 12),
        "late_deficit_auc": round(sum(float(row["deficit_loss"]) for row in late), 12),
        "total_deficit_auc": round(sum(float(row["deficit_loss"]) for row in rows), 12),
        "cumulative_deficit_auc": curve,
        "death_count": sum(bool(row["died"]) for row in rows),
        "final_effect_sign_accuracy": None if state is None else effect_sign_accuracy(state, spec["mapping_commitment"]),
        "final_state_hash": None if state is None else candidate_state_hash(state),
        "trace_chain_hash": previous_hash,
        "rows": rows,
    }


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return round(sum(values) / len(values), 12)


def row_recomputation_target(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    private_count = 0
    for row in rows:
        if row["evaluator_private"]:
            private_count += 1
            continue
        grouped[
            (
                str(row["candidate_id"]),
                str(row["opaque_context_id"]),
                str(row["arm"]),
            )
        ].append(row)
    trajectories = []
    for (candidate_id, context, arm), values in sorted(grouped.items()):
        ordered = sorted(values, key=lambda row: int(row["sequence"]))
        trajectories.append(
            {
                "candidate_id": candidate_id,
                "opaque_context_id": context,
                "arm": arm,
                "row_count": len(ordered),
                "early_deficit_auc": round(
                    sum(float(row["deficit_loss"]) for row in ordered[:EARLY_CUTOFF]), 12
                ),
                "late_deficit_auc": round(
                    sum(float(row["deficit_loss"]) for row in ordered[EARLY_CUTOFF:]), 12
                ),
                "total_deficit_auc": round(
                    sum(float(row["deficit_loss"]) for row in ordered), 12
                ),
                "final_effect_sign_accuracy": ordered[-1]["effect_sign_accuracy"],
                "trace_chain_hash": ordered[-1]["trace_hash"],
            }
        )
    arms: dict[str, Any] = {}
    by_arm: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for trajectory in trajectories:
        by_arm[str(trajectory["arm"])].append(trajectory)
    for arm, values in sorted(by_arm.items()):
        arms[arm] = {
            "world_count": len(values),
            "mean_early_deficit_auc": _mean(float(value["early_deficit_auc"]) for value in values),
            "mean_late_deficit_auc": _mean(float(value["late_deficit_auc"]) for value in values),
            "mean_total_deficit_auc": _mean(float(value["total_deficit_auc"]) for value in values),
        }
    return {
        "row_count": len(rows),
        "public_row_count": len(rows) - private_count,
        "private_diagnostic_row_count": private_count,
        "trajectories": trajectories,
        "arms": arms,
    }


def summarize_candidate(trajectories: list[Mapping[str, Any]]) -> dict[str, Any]:
    by_arm: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for trajectory in trajectories:
        by_arm[str(trajectory["arm"])].append(trajectory)
    arms: dict[str, Any] = {}
    for arm, values in sorted(by_arm.items()):
        arms[arm] = {
            "world_count": len(values),
            "mean_early_deficit_auc": _mean(float(value["early_deficit_auc"]) for value in values),
            "mean_late_deficit_auc": _mean(float(value["late_deficit_auc"]) for value in values),
            "mean_total_deficit_auc": _mean(float(value["total_deficit_auc"]) for value in values),
            "mean_final_effect_sign_accuracy": (
                None
                if all(value["final_effect_sign_accuracy"] is None for value in values)
                else _mean(float(value["final_effect_sign_accuracy"]) for value in values if value["final_effect_sign_accuracy"] is not None)
            ),
        }
    indexed = {
        arm: {str(value["opaque_context_id"]): value for value in values}
        for arm, values in by_arm.items()
    }
    worlds = []
    for context in sorted(indexed["TRANSFER"]):
        transfer = indexed["TRANSFER"][context]
        scratch = indexed["SCRATCH"][context]
        gaps = {
            checkpoint: round(
                float(scratch["cumulative_deficit_auc"][checkpoint])
                - float(transfer["cumulative_deficit_auc"][checkpoint]),
                12,
            )
            for checkpoint in transfer["cumulative_deficit_auc"]
        }
        worlds.append(
            {
                "opaque_context_id": context,
                "early_transfer_gain": round(float(scratch["early_deficit_auc"]) - float(transfer["early_deficit_auc"]), 12),
                "late_transfer_gain": round(float(scratch["late_deficit_auc"]) - float(transfer["late_deficit_auc"]), 12),
                "transfer_better_early": float(transfer["early_deficit_auc"]) < float(scratch["early_deficit_auc"]),
                "gap_curve": gaps,
                "gap_pattern": (
                    "initially_negative_then_recovered"
                    if float(gaps.get("8", 0.0)) < 0.0 and float(gaps.get("96", 0.0)) >= 0.0
                    else "persistent_negative"
                    if float(gaps.get("96", 0.0)) < 0.0
                    else "nonnegative_terminal"
                ),
                "contradiction_late_excess_vs_scratch": round(
                    float(indexed["PRIOR_CONTRADICTION"][context]["late_deficit_auc"])
                    - float(scratch["late_deficit_auc"]),
                    12,
                ),
            }
        )
    mean_gap_curve = {
        str(checkpoint): _mean(float(world["gap_curve"][str(checkpoint)]) for world in worlds)
        for checkpoint in GAP_CHECKPOINTS
    }
    early_gain = round(arms["SCRATCH"]["mean_early_deficit_auc"] - arms["TRANSFER"]["mean_early_deficit_auc"], 12)
    early_headroom = round(arms["SCRATCH"]["mean_early_deficit_auc"] - arms["PRIVATE_ORACLE_NAVIGATOR"]["mean_early_deficit_auc"], 12)
    total_headroom = max(0.0, arms["UNIFORM_RANDOM"]["mean_total_deficit_auc"] - arms["PRIVATE_ORACLE_NAVIGATOR"]["mean_total_deficit_auc"])
    ablation_damage = {
        arm: round(arms[arm]["mean_early_deficit_auc"] - arms["TRANSFER"]["mean_early_deficit_auc"], 12)
        for arm in ("NO_TRANSFER", "SLOW_RESET", "FAST_RESET", "HISTORY_SHUFFLE", "NO_UPDATE")
    }
    contradiction_tolerance = round(0.05 * total_headroom, 12)
    gates = {
        "within_world_effect_learning": arms["SCRATCH"]["mean_final_effect_sign_accuracy"] >= 0.80,
        "early_transfer_positive": early_gain > 0.0,
        "early_headroom_fraction": early_headroom > 0.0 and early_gain >= 0.05 * early_headroom,
        "positive_worlds": sum(bool(world["transfer_better_early"]) for world in worlds) >= 12,
        "no_transfer_removes_half_gain": early_gain > 0.0 and ablation_damage["NO_TRANSFER"] >= 0.5 * early_gain,
        "slow_reset_removes_half_gain": early_gain > 0.0 and ablation_damage["SLOW_RESET"] >= 0.5 * early_gain,
        "history_shuffle_damages_learning": (
            arms["HISTORY_SHUFFLE"]["mean_final_effect_sign_accuracy"]
            <= arms["TRANSFER"]["mean_final_effect_sign_accuracy"] - 0.20
            or ablation_damage["HISTORY_SHUFFLE"] > 0.0
        ),
        "prior_contradiction_recovers": arms["PRIOR_CONTRADICTION"]["mean_late_deficit_auc"]
        <= arms["SCRATCH"]["mean_late_deficit_auc"] + contradiction_tolerance,
        "cross_world_mean_never_applied": True,
    }
    return {
        "arms": arms,
        "worlds": worlds,
        "mean_gap_curve": mean_gap_curve,
        "early_transfer_gain": early_gain,
        "early_scratch_oracle_headroom": early_headroom,
        "early_transfer_fraction": None if early_headroom <= 0.0 else round(early_gain / early_headroom, 12),
        "positive_world_count": sum(bool(world["transfer_better_early"]) for world in worlds),
        "ablation_damage": ablation_damage,
        "contradiction_late_tolerance": contradiction_tolerance,
        "latent_alignment_diagnostic_early_auc": arms["LATENT_ALIGNMENT_UPPER_BOUND"]["mean_early_deficit_auc"],
        "latent_alignment_excluded_from_gates": True,
        "gates": gates,
        "all_gates_pass": all(gates.values()),
    }


def _result_prefix(candidate_id: str) -> str:
    return candidate_id.lower()


def _run_candidate_packet(
    *,
    candidate_id: str,
    specs: list[Mapping[str, Any]],
    trained_meta: Mapping[str, Any],
    split: str,
    target: Path,
) -> dict[str, Any]:
    trajectories = []
    rows = []
    for spec in specs:
        for arm in ALL_ARMS:
            trajectory = run_trajectory(
                spec,
                candidate_id=candidate_id,
                arm=arm,
                trained_meta=trained_meta,
                budget=EVALUATION_BUDGET,
            )
            trajectories.append({key: value for key, value in trajectory.items() if key != "rows"})
            rows.extend(trajectory["rows"])
    summary = summarize_candidate(trajectories)
    prefix = (
        f"{split}_{SEARCH_RUN_ID}_{_result_prefix(candidate_id)}"
        if split == "search_dev"
        else f"{split}_{_result_prefix(candidate_id)}"
    )
    rows_path = target / f"{prefix}_rows.jsonl"
    result_path = target / f"{prefix}_result.json"
    if rows_path.exists() or result_path.exists():
        raise RuntimeError(f"single-use candidate output already exists: {prefix}")
    write_jsonl(rows_path, rows)
    result = {
        "schema_version": "ego.v2.transfer_mechanism.candidate_result.v1",
        "task_id": TASK_ID,
        "candidate_id": candidate_id,
        "split": split,
        "single_use": split == "qualification",
        "training_world_count": int(trained_meta["training_world_count"]),
        "evaluation_world_count": len(specs),
        "action_budget": EVALUATION_BUDGET,
        "slow_meta": deepcopy(dict(trained_meta)),
        "slow_meta_hash": canonical_hash(trained_meta),
        "summary": summary,
        "row_recomputation_target": row_recomputation_target(rows),
        "rows_path": rows_path.relative_to(ROOT).as_posix(),
        "rows_sha256": sha256(rows_path),
        "public_learner_received_private_alignment": False,
        "latent_alignment_evaluator_only": True,
        "claim_ceiling": "Dev-only benchmark-local mechanism diagnosis only.",
        "verdict": "SEARCH_TRANSFER_GATE_PASS" if split == "search_dev" and summary["all_gates_pass"] else "SEARCH_TRANSFER_GATE_FAIL" if split == "search_dev" else "QUALIFICATION_TRANSFER_GATE_PASS" if summary["all_gates_pass"] else "QUALIFICATION_TRANSFER_GATE_FAIL",
    }
    write_json(result_path, result)
    return result


def _select_candidate(results: list[Mapping[str, Any]]) -> str | None:
    passing = [result for result in results if result["summary"]["all_gates_pass"]]
    if not passing:
        return None
    passing.sort(
        key=lambda result: (
            -float(result["summary"]["early_transfer_fraction"]),
            -int(result["summary"]["positive_world_count"]),
            -min(float(row["early_transfer_gain"]) for row in result["summary"]["worlds"]),
            str(result["candidate_id"]),
        )
    )
    return str(passing[0]["candidate_id"])


def _write_gap_plot(target: Path, results: list[Mapping[str, Any]]) -> None:
    data = {
        str(result["candidate_id"]): result["summary"]["mean_gap_curve"]
        for result in results
    }
    write_json(target / f"transfer_gap_curves_{SEARCH_RUN_ID}.json", data)
    colors = ["#2563eb", "#16a34a", "#dc2626"]
    width, height, pad = 760, 360, 45
    all_values = [float(value) for curves in data.values() for value in curves.values()] or [0.0]
    bound = max(1.0, max(abs(value) for value in all_values))
    points = []
    legend = []
    for index, (candidate, curve) in enumerate(data.items()):
        coords = []
        for checkpoint in GAP_CHECKPOINTS:
            x = pad + (width - 2 * pad) * (checkpoint - GAP_CHECKPOINTS[0]) / (GAP_CHECKPOINTS[-1] - GAP_CHECKPOINTS[0])
            y = height / 2 - float(curve[str(checkpoint)]) / bound * (height / 2 - pad)
            coords.append(f"{x:.1f},{y:.1f}")
        points.append(f'<polyline fill="none" stroke="{colors[index]}" stroke-width="3" points="{" ".join(coords)}"/>')
        legend.append(f'<li style="color:{colors[index]}">{candidate}</li>')
    html = f"""<!doctype html><meta charset="utf-8"><title>001M transfer gap curves</title>
<h1>Transfer - scratch cumulative deficit-AUC gap</h1>
<p>Positive is better. The evaluator-only latent arm is excluded.</p>
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
<line x1="{pad}" y1="{height/2}" x2="{width-pad}" y2="{height/2}" stroke="#111"/>
<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{height-pad}" stroke="#111"/>
{''.join(points)}</svg><ul>{''.join(legend)}</ul>
<pre>{json.dumps(data, sort_keys=True, indent=2)}</pre>
"""
    (target / f"transfer_gap_curves_{SEARCH_RUN_ID}.html").write_text(
        html, encoding="utf-8", newline="\n"
    )


def run_search(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    target = artifact_root(root)
    combined_path = target / f"search_results_{SEARCH_RUN_ID}.json"
    if combined_path.exists():
        raise RuntimeError("001M search is already recorded")
    protected = audit_protected_predecessors(root)
    if not protected["passed"]:
        raise RuntimeError("protected 001L artifact drift")
    packets = load_packets(root)
    dataset = collect_training_dataset(packets["mechanism_training"])
    write_json(
        target / "training_public_receipts.json",
        {
            "schema_version": "ego.v2.transfer_mechanism.training_receipts.v1",
            "world_count": len(dataset),
            "receipt_counts": [int(row["public_receipt_count"]) for row in dataset],
            "receipt_chain_hashes": [row["public_receipt_chain_hash"] for row in dataset],
            "private_fields_received": False,
        },
    )
    results = []
    for candidate_id in CANDIDATES:
        trained_meta = train_transfer_meta(candidate_id, dataset)
        prefix = f"search_dev_{SEARCH_RUN_ID}_{_result_prefix(candidate_id)}"
        existing_result_path = target / f"{prefix}_result.json"
        existing_rows_path = target / f"{prefix}_rows.jsonl"
        if existing_result_path.exists() or existing_rows_path.exists():
            if not (existing_result_path.is_file() and existing_rows_path.is_file()):
                raise RuntimeError(f"incomplete existing candidate output: {prefix}")
            result = json.loads(existing_result_path.read_text(encoding="utf-8"))
            if (
                result.get("candidate_id") != candidate_id
                or result.get("split") != "search_dev"
                or result.get("slow_meta_hash") != canonical_hash(trained_meta)
                or result.get("rows_sha256") != sha256(existing_rows_path)
            ):
                raise RuntimeError(f"existing candidate output failed resume audit: {prefix}")
        else:
            result = _run_candidate_packet(
                candidate_id=candidate_id,
                specs=packets["search_dev"],
                trained_meta=trained_meta,
                split="search_dev",
                target=target,
            )
            append_jsonl(
                target / "experiment_log.jsonl",
                {
                    "experiment_id": f"001M-{candidate_id}-SEARCH",
                    "hypothesis": trained_meta["mechanism"],
                    "action_type": "single_variable_search_dev",
                    "changed_paths": [result["rows_path"]],
                    "eval_commands": ["--run-search"],
                    "eval_summary": result["summary"],
                    "reviewer_verdict": "success_reached" if result["summary"]["all_gates_pass"] else "needs_more_exploration",
                    "next_frontier": "freeze_new_qualification" if result["summary"]["all_gates_pass"] else "next_preregistered_candidate_or_stop",
                },
            )
        results.append(result)
    selected = _select_candidate(results)
    combined = {
        "schema_version": "ego.v2.transfer_mechanism.search_results.v1",
        "task_id": TASK_ID,
        "search_run_id": SEARCH_RUN_ID,
        "supersedes_diagnostic_run": "search_results.json",
        "supersession_reason": "HISTORY_SHUFFLE_FAST_META_PAIRING_WIRING_FIX",
        "candidate_order": list(CANDIDATES),
        "candidate_count": len(results),
        "results": results,
        "selected_candidate": selected,
        "search_authorizes_qualification": selected is not None,
        "qualification_consumed": False,
        "original_001j_heldout_consumed": False,
        "product_001l_qualification_consumed": False,
        "verdict": "SEARCH_STABLE_POSITIVE_TRANSFER" if selected else "WITHIN_WORLD_LEARNING_ESTABLISHED_COMPOSITIONAL_TRANSFER_STILL_ABSENT",
    }
    write_json(combined_path, combined)
    _write_gap_plot(target, results)
    return combined


def build_candidate_freeze(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    target = artifact_root(root)
    path = target / "candidate_freeze.json"
    if path.exists():
        raise RuntimeError("001M candidate freeze is single-write")
    search = json.loads(
        (target / f"search_results_{SEARCH_RUN_ID}.json").read_text(encoding="utf-8")
    )
    selected = search.get("selected_candidate")
    if not selected or not search.get("search_authorizes_qualification"):
        raise RuntimeError("001M search does not authorize qualification")
    selected_result = next(result for result in search["results"] if result["candidate_id"] == selected)
    sources = [
        Path(__file__).resolve(),
        root / "scripts/codex/verify_ego_v2_transfer_mechanism_001m.py",
        root / "labs/ego_life_playground_v0/homeostatic_transfer.py",
        root / "labs/ego_life_playground_v0/engine.py",
        root / "labs/ego_life_playground_v0/microworld.py",
    ]
    commitment = json.loads((target / "packet_commitment.json").read_text(encoding="utf-8"))
    freeze = {
        "schema_version": "ego.v2.transfer_mechanism.freeze.v1",
        "task_id": TASK_ID,
        "selected_candidate": selected,
        "selected_slow_meta": selected_result["slow_meta"],
        "selected_search_result_sha256": sha256(
            target
            / f"search_dev_{SEARCH_RUN_ID}_{_result_prefix(selected)}_result.json"
        ),
        "source_hashes": {path.relative_to(root).as_posix(): sha256(path) for path in sources},
        "packet_sha256": commitment["packet_sha256"],
        "thresholds": {
            "early_headroom_recovery_fraction": 0.05,
            "positive_worlds": 12,
            "effect_sign_accuracy": 0.80,
            "slow_reset_gain_elimination_fraction": 0.50,
            "contradiction_total_headroom_tolerance": 0.05,
        },
        "numpy": "2.2.6",
        "qualification_single_use": True,
        "original_001j_heldout_consumed": False,
        "product_001l_qualification_consumed": False,
    }
    write_json(path, freeze)
    return freeze


def _load_freeze(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    target = artifact_root(root)
    freeze = json.loads((target / "candidate_freeze.json").read_text(encoding="utf-8"))
    for relative, expected in freeze["source_hashes"].items():
        if sha256(root / relative) != expected:
            raise RuntimeError(f"001M source changed after freeze: {relative}")
    if sha256(target / "packet_assignments.json") != freeze["packet_sha256"]:
        raise RuntimeError("001M packet changed after freeze")
    import numpy as np

    if np.__version__ != freeze["numpy"]:
        raise RuntimeError("001M NumPy dependency drift")
    return freeze


def run_qualification(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    target = artifact_root(root)
    if (target / "qualification_result.json").exists():
        raise RuntimeError("001M qualification is single-use")
    freeze = _load_freeze(root)
    packets = load_packets(root)
    selected = str(freeze["selected_candidate"])
    result = _run_candidate_packet(
        candidate_id=selected,
        specs=packets["qualification"],
        trained_meta=freeze["selected_slow_meta"],
        split="qualification",
        target=target,
    )
    write_json(target / "qualification_result.json", result)
    commitment_path = target / "packet_commitment.json"
    commitment = json.loads(commitment_path.read_text(encoding="utf-8"))
    commitment["qualification_consumed"] = True
    commitment["qualification_result_sha256"] = sha256(target / "qualification_result.json")
    write_json(commitment_path, commitment)
    return result


def write_campaign_closeout(root: Path, qualification: Mapping[str, Any] | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    target = artifact_root(root)
    search = json.loads(
        (target / f"search_results_{SEARCH_RUN_ID}.json").read_text(encoding="utf-8")
    )
    search_pass = bool(search["search_authorizes_qualification"])
    qualification_pass = bool(qualification and qualification["summary"]["all_gates_pass"])
    established = search_pass and qualification_pass
    verdict = (
        "DEV_ONLY_TRANSFER_MECHANISM_QUALIFIED"
        if established
        else "WITHIN_WORLD_LEARNING_ESTABLISHED_COMPOSITIONAL_TRANSFER_STILL_ABSENT"
    )
    failed = []
    for result in search["results"]:
        if not result["summary"]["all_gates_pass"]:
            failed.append(
                {
                    "candidate_id": result["candidate_id"],
                    "early_transfer_gain": result["summary"]["early_transfer_gain"],
                    "early_transfer_fraction": result["summary"]["early_transfer_fraction"],
                    "positive_world_count": result["summary"]["positive_world_count"],
                    "failed_gates": [name for name, passed in result["summary"]["gates"].items() if not passed],
                    "gap_curve": result["summary"]["mean_gap_curve"],
                    "failure_explanation": "preregistered search gate failed; no tuning or threshold change",
                }
            )
    if qualification is not None and not qualification_pass:
        failed.append(
            {
                "candidate_id": qualification["candidate_id"],
                "stage": "qualification",
                "failed_gates": [name for name, passed in qualification["summary"]["gates"].items() if not passed],
                "failure_explanation": "single-use qualification did not reproduce search gate",
            }
        )
    write_json(
        target / "failure_manifest.json",
        {
            "schema_version": "ego.v2.transfer_mechanism.failures.v1",
            "task_id": TASK_ID,
            "failed_candidates": failed,
            "thresholds_lowered": False,
            "qualification_consumed": qualification is not None,
            "terminal_verdict": verdict,
        },
    )
    report = {
        "schema_version": "ego.v2.transfer_mechanism.campaign.v1",
        "task_id": TASK_ID,
        "verdict": verdict,
        "search_run_id": SEARCH_RUN_ID,
        "invalidated_diagnostic_search_preserved": "search_results.json",
        "search_authorized_qualification": search_pass,
        "selected_candidate": search["selected_candidate"],
        "qualification_consumed": qualification is not None,
        "qualification_passed": qualification_pass,
        "original_001j_heldout_consumed": False,
        "product_001l_qualification_consumed": False,
        "product_default": "within_world_public_bayesian_posterior",
        "dialogue_or_llm_enabled": False,
        "claim_ceiling": "Benchmark-local dev-only transfer mechanism evidence only; not general transfer or electronic life.",
    }
    write_json(target / "campaign_report.json", report)
    return report


def write_artifact_manifest(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    target = artifact_root(root)
    manifest_path = target / "artifact_manifest.json"
    files = {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(target.iterdir())
        if path.is_file() and path != manifest_path
    }
    manifest = {
        "schema_version": "ego.v2.transfer_mechanism.manifest.v1",
        "task_id": TASK_ID,
        "files": files,
        "manifest_excludes_self": True,
    }
    write_json(manifest_path, manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--run-search", action="store_true")
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--run-qualification", action="store_true")
    parser.add_argument("--closeout", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    args = parser.parse_args(argv)
    if args.audit:
        print(json.dumps(audit_protected_predecessors(args.root), sort_keys=True, indent=2))
    if args.run_search:
        print(json.dumps(run_search(args.root), sort_keys=True, indent=2))
    if args.freeze:
        print(json.dumps(build_candidate_freeze(args.root), sort_keys=True, indent=2))
    qualification = None
    if args.run_qualification:
        qualification = run_qualification(args.root)
        print(json.dumps(qualification, sort_keys=True, indent=2))
    if args.closeout:
        if qualification is None and (artifact_root(args.root) / "qualification_result.json").is_file():
            qualification = json.loads((artifact_root(args.root) / "qualification_result.json").read_text(encoding="utf-8"))
        print(json.dumps(write_campaign_closeout(args.root, qualification), sort_keys=True, indent=2))
    if args.manifest:
        print(json.dumps(write_artifact_manifest(args.root), sort_keys=True, indent=2))
    if not any((args.audit, args.run_search, args.freeze, args.run_qualification, args.closeout, args.manifest)):
        parser.error("select an operation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
