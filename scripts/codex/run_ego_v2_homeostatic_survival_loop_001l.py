"""Dev-only acquisition/transfer evidence for the runnable 001L product lane."""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from labs.ego_life_playground_v0 import engine, homeostatic_transfer, microworld
from scripts.codex import run_ego_v2_public_acquisition_capacity_recovery_001k as predecessor


TASK_ID = "EGO-V2-HOMEOSTATIC-SURVIVAL-LOOP-001L"
ARTIFACT_NAME = TASK_ID
PUBLIC_ARMS = (
    "TRANSFER",
    "SCRATCH",
    "NO_UPDATE",
    "FEEDBACK_SHUFFLE",
    "SLOW_RESET",
    "FAST_RESET",
    "POSTERIOR_ABLATION",
    "WRONG_PRIOR",
)
ALL_ARMS = (*PUBLIC_ARMS, "UNIFORM_RANDOM", "PRIVATE_ORACLE_NAVIGATOR")
TRAINING_BUDGET = 96
EVALUATION_BUDGET = 96
EARLY_CUTOFF = 48


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_root(root: Path) -> Path:
    return Path(root).resolve() / "artifacts" / ARTIFACT_NAME


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(canonical_json(row) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def load_packets(root: Path) -> dict[str, list[dict[str, Any]]]:
    root = Path(root).resolve()
    target = artifact_root(root)
    commitment = json.loads(
        (target / "product_packet_commitment.json").read_text(encoding="utf-8")
    )
    packet_path = root / commitment["packet_path"]
    if sha256(packet_path) != commitment["packet_sha256"]:
        raise RuntimeError("product evaluation packet commitment mismatch")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if (
        packet.get("task_id") != TASK_ID
        or packet.get("created_before_evaluation_results") is not True
        or packet.get("original_001j_heldout") is not False
        or set(packet.get("splits", {}))
        != {"structure_training", "search_dev", "qualification"}
    ):
        raise RuntimeError("product evaluation packet authority mismatch")
    return deepcopy(packet["splits"])


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


def _random_action(context_id: str, sequence: int) -> str:
    digest = hashlib.sha256(f"{TASK_ID}:{context_id}:{sequence}:random".encode()).digest()
    return microworld.ACTIONS[int.from_bytes(digest[:4], "big") % len(microworld.ACTIONS)]


def _deficit_loss(organism: Mapping[str, float], *, died: bool) -> float:
    value = sum(
        max(0.0, engine.TARGET_LEVEL - float(organism[key]))
        for key in ("energy", "safety")
    )
    return round(value + (0.75 if died else 0.0), 12)


def _sign(value: float) -> int:
    return 1 if value > 1e-9 else -1 if value < -1e-9 else 0


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


def effect_sign_accuracy(
    state: Mapping[str, Any], mapping: Mapping[str, str]
) -> float:
    correct = 0
    denominator = 2 * len(microworld.TOKENS)
    for token in microworld.TOKENS:
        row = state["fast_state"]["token_stats"].get(token)
        if row is None:
            continue
        expected = _expected_interaction_delta(str(mapping[token]))
        correct += _sign(float(row["energy_mean"])) == _sign(expected["energy"])
        correct += _sign(float(row["safety_mean"])) == _sign(expected["safety"])
    return round(correct / denominator, 12)


def invert_slow_prior(state: Mapping[str, Any]) -> dict[str, Any]:
    inverted = deepcopy(dict(state))
    rebuilt: dict[str, Any] = {}
    for row in inverted["slow_state"]["effect_prototypes"].values():
        changed = deepcopy(row)
        changed["energy_mean"] = round(-float(changed["energy_mean"]), 12)
        changed["safety_mean"] = round(-float(changed["safety_mean"]), 12)
        signature = (
            f"energy:{'+' if changed['energy_mean'] > 0 else '-' if changed['energy_mean'] < 0 else '0'}"
            f"|safety:{'+' if changed['safety_mean'] > 0 else '-' if changed['safety_mean'] < 0 else '0'}"
        )
        rebuilt[signature] = changed
    inverted["slow_state"]["effect_prototypes"] = rebuilt
    homeostatic_transfer.validate_state(inverted)
    return inverted


def _state_for_arm(trained: Mapping[str, Any], arm: str) -> dict[str, Any] | None:
    if arm in {"UNIFORM_RANDOM", "PRIVATE_ORACLE_NAVIGATOR"}:
        return None
    if arm == "SCRATCH":
        return homeostatic_transfer.empty_state()
    state = homeostatic_transfer.reset_for_world(trained)
    if arm == "SLOW_RESET":
        state = homeostatic_transfer.reset_slow_state(state)
    elif arm == "WRONG_PRIOR":
        state = invert_slow_prior(state)
    return state


def run_trajectory(
    spec: Mapping[str, Any],
    *,
    arm: str,
    trained_state: Mapping[str, Any],
    budget: int,
) -> dict[str, Any]:
    if arm not in ALL_ARMS:
        raise ValueError("unknown product evaluation arm")
    world = microworld.initial_world_state(
        seed=int(spec["world_seed"]), layout_id=str(spec["layout_id"])
    )
    if dict(world["trial"]["token_mapping"]) != dict(spec["mapping_commitment"]):
        raise RuntimeError("product packet mapping changed")
    state = _state_for_arm(trained_state, arm)
    organism = _initial_organism()
    last_action = None
    last_delta = {"energy": 0.0, "safety": 0.0}
    previous_hash = None
    rows: list[dict[str, Any]] = []
    life_index = 1
    run_meta = {
        "run_id": f"{TASK_ID}:{spec['opaque_context_id']}:{arm}",
        "seed": int(spec["world_seed"]),
    }
    code_hash = engine.compute_code_path_hash()
    for sequence in range(1, budget + 1):
        if arm == "FAST_RESET" and sequence > 1:
            assert state is not None
            state = homeostatic_transfer.reset_fast_state(state)
        payload = _public_payload(world, organism, last_action, last_delta)
        scan = homeostatic_transfer.scan_public_input(payload)
        if not scan["clean"]:
            raise RuntimeError("product candidate input leakage")
        if arm == "UNIFORM_RANDOM":
            action = _random_action(str(spec["opaque_context_id"]), sequence)
            plan = None
        elif arm == "PRIVATE_ORACLE_NAVIGATOR":
            action = predecessor._oracle_action(world, organism)
            plan = None
        else:
            assert state is not None
            plan = homeostatic_transfer.plan_action(
                state,
                public_input=payload,
                sequence=sequence,
                mode="public_bayes",
                drive_mode="canonical",
                posterior_mode=(
                    "ablated" if arm == "POSTERIOR_ABLATION" else "two_timescale"
                ),
                action_costs=engine.ACTION_COSTS,
                target_level=engine.TARGET_LEVEL,
            )
            action = str(plan["selected_action"])
        command_hash = canonical_hash(
            {
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
            source_episode_id=f"p-eval-life-{life_index}",
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
            episode_id=f"p-eval-life-{life_index}",
            command_hash=command_hash,
            code_path_hash=code_hash,
        )
        actual_delta = {
            "energy": float(metabolism["energy_delta"]),
            "safety": float(actual["safety"]),
        }
        organism = {
            key: round(max(0.0, min(1.0, organism[key] + actual_delta[key])), 12)
            for key in ("energy", "safety")
        }
        died = organism["energy"] == 0.0
        update = None
        if state is not None:
            state, update = homeostatic_transfer.update_after_transition(
                state,
                public_input=payload,
                selected_action=action,
                observed_outcome_type=str(transition["outcome_type"]),
                actual_delta=actual_delta,
                terminal=died,
                updates_enabled=arm != "NO_UPDATE",
                feedback_mode=("shuffle" if arm == "FEEDBACK_SHUFFLE" else "canonical"),
            )
        row_without_hash = {
            "schema_version": "ego.v2.homeostatic_survival_loop.row.v1",
            "task_id": TASK_ID,
            "opaque_context_id": spec["opaque_context_id"],
            "arm": arm,
            "sequence": sequence,
            "public_input_clean": scan["clean"],
            "public_input_fields": list(homeostatic_transfer.PUBLIC_INPUT_FIELDS),
            "selected_action": action,
            "selection_reason": None if plan is None else plan["selection_reason"],
            "drive": None if plan is None else plan["drive"],
            "predictions_hash": None if plan is None else plan["predictions_hash"],
            "slow_prior_applied": None if plan is None else plan["slow_prior_applied"],
            "actual_delta": actual_delta,
            "outcome_type": transition["outcome_type"],
            "energy_after": organism["energy"],
            "safety_after": organism["safety"],
            "died": died,
            "deficit_loss": _deficit_loss(organism, died=died),
            "effect_sign_accuracy": (
                None
                if state is None
                else effect_sign_accuracy(state, spec["mapping_commitment"])
            ),
            "slow_state_hash": (
                None if state is None else homeostatic_transfer.slow_state_hash(state)
            ),
            "fast_state_hash": (
                None if state is None else homeostatic_transfer.fast_state_hash(state)
            ),
            "update_hash": None if update is None else canonical_hash(update),
            "prev_trace_hash": previous_hash,
        }
        row_hash = canonical_hash(row_without_hash)
        rows.append({**row_without_hash, "trace_hash": row_hash})
        previous_hash = row_hash
        last_action = action
        last_delta = actual_delta
        if died:
            life_index += 1
            world = microworld.reset_world_for_life(world, life_index)
            organism = _initial_organism()
            if state is not None:
                state = homeostatic_transfer.reset_for_respawn(state)
    early = rows[: min(EARLY_CUTOFF, len(rows))]
    late = rows[min(EARLY_CUTOFF, len(rows)) :]
    return {
        "opaque_context_id": spec["opaque_context_id"],
        "arm": arm,
        "budget": budget,
        "early_deficit_auc": round(sum(row["deficit_loss"] for row in early), 12),
        "late_deficit_auc": round(sum(row["deficit_loss"] for row in late), 12),
        "total_deficit_auc": round(sum(row["deficit_loss"] for row in rows), 12),
        "death_count": sum(row["died"] for row in rows),
        "final_effect_sign_accuracy": (
            None if state is None else effect_sign_accuracy(state, spec["mapping_commitment"])
        ),
        "final_state_hash": None if state is None else homeostatic_transfer.state_hash(state),
        "trace_chain_hash": previous_hash,
        "rows": rows,
        "state": state,
    }


def train_slow_structure(specs: list[Mapping[str, Any]]) -> dict[str, Any]:
    state = homeostatic_transfer.empty_state()
    for spec in specs:
        trajectory = run_trajectory(
            spec, arm="TRANSFER", trained_state=state, budget=TRAINING_BUDGET
        )
        assert trajectory["state"] is not None
        state = trajectory["state"]
    return homeostatic_transfer.reset_for_world(state)


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 12)


def summarize(trajectories: list[Mapping[str, Any]]) -> dict[str, Any]:
    by_arm: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for item in trajectories:
        by_arm[str(item["arm"])].append(item)
    arm_rows = {}
    for arm, values in sorted(by_arm.items()):
        arm_rows[arm] = {
            "world_count": len(values),
            "mean_early_deficit_auc": _mean([float(v["early_deficit_auc"]) for v in values]),
            "mean_late_deficit_auc": _mean([float(v["late_deficit_auc"]) for v in values]),
            "mean_total_deficit_auc": _mean([float(v["total_deficit_auc"]) for v in values]),
            "mean_final_effect_sign_accuracy": (
                None
                if arm in {"UNIFORM_RANDOM", "PRIVATE_ORACLE_NAVIGATOR"}
                else _mean([float(v["final_effect_sign_accuracy"]) for v in values])
            ),
        }
    transfer_by_world = {v["opaque_context_id"]: v for v in by_arm["TRANSFER"]}
    scratch_by_world = {v["opaque_context_id"]: v for v in by_arm["SCRATCH"]}
    random_by_world = {v["opaque_context_id"]: v for v in by_arm["UNIFORM_RANDOM"]}
    oracle_by_world = {v["opaque_context_id"]: v for v in by_arm["PRIVATE_ORACLE_NAVIGATOR"]}
    wrong_by_world = {v["opaque_context_id"]: v for v in by_arm["WRONG_PRIOR"]}
    fast_by_world = {v["opaque_context_id"]: v for v in by_arm["FAST_RESET"]}
    world_rows = []
    for context in sorted(transfer_by_world):
        transfer = transfer_by_world[context]
        scratch = scratch_by_world[context]
        world_rows.append(
            {
                "opaque_context_id": context,
                "early_transfer_gain": round(
                    float(scratch["early_deficit_auc"])
                    - float(transfer["early_deficit_auc"]),
                    12,
                ),
                "transfer_better_than_scratch": float(transfer["early_deficit_auc"])
                < float(scratch["early_deficit_auc"]),
                "fast_reset_worse_than_transfer": float(
                    fast_by_world[context]["early_deficit_auc"]
                )
                > float(transfer["early_deficit_auc"]),
                "wrong_prior_late_excess_vs_scratch": round(
                    float(wrong_by_world[context]["late_deficit_auc"])
                    - float(scratch["late_deficit_auc"]),
                    12,
                ),
                "early_scratch_oracle_headroom": round(
                    float(scratch["early_deficit_auc"])
                    - float(oracle_by_world[context]["early_deficit_auc"]),
                    12,
                ),
                "random_total_loss": random_by_world[context]["total_deficit_auc"],
            }
        )
    early_gain = round(
        arm_rows["SCRATCH"]["mean_early_deficit_auc"]
        - arm_rows["TRANSFER"]["mean_early_deficit_auc"],
        12,
    )
    early_headroom = round(
        arm_rows["SCRATCH"]["mean_early_deficit_auc"]
        - arm_rows["PRIVATE_ORACLE_NAVIGATOR"]["mean_early_deficit_auc"],
        12,
    )
    ablation_damage = {
        arm: round(
            arm_rows[arm]["mean_early_deficit_auc"]
            - arm_rows["TRANSFER"]["mean_early_deficit_auc"],
            12,
        )
        for arm in ("NO_UPDATE", "FEEDBACK_SHUFFLE", "POSTERIOR_ABLATION")
    }
    wrong_tolerance = 0.05 * max(
        0.0,
        arm_rows["UNIFORM_RANDOM"]["mean_total_deficit_auc"]
        - arm_rows["PRIVATE_ORACLE_NAVIGATOR"]["mean_total_deficit_auc"],
    )
    gates = {
        "effect_sign_accuracy": arm_rows["TRANSFER"][
            "mean_final_effect_sign_accuracy"
        ]
        >= 0.80,
        "early_transfer_gain": early_gain > 0.0,
        "early_transfer_fraction": (
            early_headroom > 0.0 and early_gain >= 0.05 * early_headroom
        ),
        "positive_world_majority": sum(
            row["transfer_better_than_scratch"] for row in world_rows
        )
        >= max(1, (3 * len(world_rows) + 3) // 4),
        "posterior_controls_damage": sum(value > 0.0 for value in ablation_damage.values())
        >= 2,
        "slow_reset_eliminates_half_gain": (
            early_gain > 0.0
            and arm_rows["SLOW_RESET"]["mean_early_deficit_auc"]
            - arm_rows["TRANSFER"]["mean_early_deficit_auc"]
            >= 0.5 * early_gain
        ),
        "fast_reset_worsens_majority": sum(
            row["fast_reset_worse_than_transfer"] for row in world_rows
        )
        >= max(1, (3 * len(world_rows) + 3) // 4),
        "wrong_prior_late_recovery": arm_rows["WRONG_PRIOR"][
            "mean_late_deficit_auc"
        ]
        <= arm_rows["SCRATCH"]["mean_late_deficit_auc"] + wrong_tolerance,
    }
    return {
        "arms": arm_rows,
        "worlds": world_rows,
        "early_transfer_gain": early_gain,
        "early_scratch_oracle_headroom": early_headroom,
        "early_transfer_fraction": (
            None if early_headroom <= 0.0 else round(early_gain / early_headroom, 12)
        ),
        "ablation_damage": ablation_damage,
        "wrong_prior_late_tolerance": round(wrong_tolerance, 12),
        "gates": gates,
        "all_gates_pass": all(gates.values()),
    }


def drive_intervention_probe() -> dict[str, Any]:
    state = homeostatic_transfer.empty_state()
    visual = [["empty"] * 5 for _ in range(5)]
    visual[2][2] = "self"
    for token, delta in (("v0", (0.24, 0.0)), ("v1", (-0.018, 0.18))):
        token_visual = deepcopy(visual)
        token_visual[1][2] = token
        payload = {
            "observation": {
                "schema_version": microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION,
                "visual": token_visual,
            },
            "organism": {"energy": 0.5, "safety": 0.5},
            "last_action": None,
            "last_delta": {"energy": 0.0, "safety": 0.0},
        }
        state, _receipt = homeostatic_transfer.update_after_transition(
            state,
            public_input=payload,
            selected_action="interact",
            observed_outcome_type="interacted",
            actual_delta={"energy": delta[0], "safety": delta[1]},
            terminal=False,
            updates_enabled=True,
            feedback_mode="canonical",
        )
    comparison_visual = deepcopy(visual)
    comparison_visual[2][1] = "v0"
    comparison_visual[2][3] = "v1"
    observation = {
        "schema_version": microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION,
        "visual": comparison_visual,
    }
    plans = []
    for energy, safety in ((0.2, 0.7), (0.7, 0.2)):
        plans.append(
            homeostatic_transfer.plan_action(
                state,
                public_input={
                    "observation": observation,
                    "organism": {"energy": energy, "safety": safety},
                    "last_action": None,
                    "last_delta": {"energy": 0.0, "safety": 0.0},
                },
                sequence=1,
                mode="public_bayes",
                drive_mode="canonical",
                action_costs=engine.ACTION_COSTS,
                target_level=engine.TARGET_LEVEL,
            )
        )
    return {
        "predictions_unchanged": plans[0]["predictions_hash"]
        == plans[1]["predictions_hash"],
        "energy_deficit_target": plans[0]["selected_target"],
        "safety_deficit_target": plans[1]["selected_target"],
        "ranking_shifted": plans[0]["selected_target"] != plans[1]["selected_target"],
    }


def execute_packet(root: Path, split: str, *, output_prefix: str) -> dict[str, Any]:
    root = Path(root).resolve()
    target = artifact_root(root)
    result_path = target / f"{output_prefix}_result.json"
    rows_path = target / f"{output_prefix}_rows.jsonl"
    if result_path.exists() or rows_path.exists():
        raise RuntimeError(f"{output_prefix} packet is single-use")
    packets = load_packets(root)
    trained = train_slow_structure(packets["structure_training"])
    trajectories = []
    all_rows = []
    for spec in packets[split]:
        for arm in ALL_ARMS:
            trajectory = run_trajectory(
                spec,
                arm=arm,
                trained_state=trained,
                budget=EVALUATION_BUDGET,
            )
            trajectories.append({key: value for key, value in trajectory.items() if key not in {"rows", "state"}})
            all_rows.extend(trajectory["rows"])
    summary = summarize(trajectories)
    replay_a = run_trajectory(
        packets[split][0],
        arm="TRANSFER",
        trained_state=trained,
        budget=EVALUATION_BUDGET,
    )
    replay_b = run_trajectory(
        packets[split][0],
        arm="TRANSFER",
        trained_state=trained,
        budget=EVALUATION_BUDGET,
    )
    replay_exact = canonical_hash(replay_a) == canonical_hash(replay_b)
    drive_probe = drive_intervention_probe()
    acceptance = {
        "numeric_transfer_and_ablation_gates": summary["all_gates_pass"],
        "drive_predictions_invariant": drive_probe["predictions_unchanged"],
        "drive_ranking_shifted": drive_probe["ranking_shifted"],
        "exact_behavior_replay": replay_exact,
    }
    write_jsonl(rows_path, all_rows)
    result = {
        "schema_version": "ego.v2.homeostatic_survival_loop.result.v1",
        "task_id": TASK_ID,
        "split": split,
        "single_use": True,
        "training_world_count": len(packets["structure_training"]),
        "evaluation_world_count": len(packets[split]),
        "action_budget": EVALUATION_BUDGET,
        "trained_slow_state_hash": homeostatic_transfer.slow_state_hash(trained),
        "trained_effect_prototypes": deepcopy(trained["slow_state"]["effect_prototypes"]),
        "summary": summary,
        "drive_intervention": drive_probe,
        "replay": {
            "produced_hash": canonical_hash(replay_a),
            "replayed_hash": canonical_hash(replay_b),
            "stored_actions_used_as_replay_input": False,
            "exact": replay_exact,
        },
        "acceptance": acceptance,
        "all_gates_pass": all(acceptance.values()),
        "rows_path": rows_path.relative_to(root).as_posix(),
        "rows_sha256": sha256(rows_path),
        "verdict": (
            "MINIMAL_TWO_TIMESCALE_DEV_GATE_PASS"
            if all(acceptance.values())
            else "MINIMAL_TWO_TIMESCALE_DEV_GATE_FAIL"
        ),
        "claim_ceiling": (
            "Dev-only public-feedback learning and limited compositional transfer "
            "inside this microworld grammar only."
        ),
    }
    write_json(result_path, result)
    return result


def build_freeze(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    target = artifact_root(root)
    path = target / "product_candidate_freeze.json"
    if path.exists():
        raise RuntimeError("product candidate freeze is single-write")
    selected_search_path = (
        target / "product_search_multiplicity_result.json"
        if (target / "product_search_multiplicity_result.json").is_file()
        else target / "product_search_result.json"
    )
    search = json.loads(selected_search_path.read_text(encoding="utf-8"))
    if not search["all_gates_pass"]:
        raise RuntimeError("search did not authorize product qualification")
    packet_commitment = json.loads(
        (target / "product_packet_commitment.json").read_text(encoding="utf-8")
    )
    sources = [
        Path(__file__).resolve(),
        root / "labs/ego_life_playground_v0/homeostatic_transfer.py",
        root / "labs/ego_life_playground_v0/engine.py",
        root / "labs/ego_life_playground_v0/microworld.py",
    ]
    freeze = {
        "schema_version": "ego.v2.homeostatic_survival_loop.freeze.v1",
        "task_id": TASK_ID,
        "source_hashes": {
            path.relative_to(root).as_posix(): sha256(path) for path in sources
        },
        "packet_sha256": packet_commitment["packet_sha256"],
        "selected_search_path": selected_search_path.relative_to(root).as_posix(),
        "selected_search_result_sha256": sha256(selected_search_path),
        "failed_search_result_sha256": sha256(target / "product_search_result.json"),
        "budgets": {"training": TRAINING_BUDGET, "evaluation": EVALUATION_BUDGET},
        "thresholds": {
            "effect_sign_accuracy": 0.80,
            "early_transfer_headroom_fraction": 0.05,
            "positive_world_fraction": 0.75,
            "material_posterior_controls": 2,
            "slow_reset_gain_elimination": 0.50,
            "wrong_prior_headroom_tolerance": 0.05,
        },
        "numpy": "2.2.6",
        "qualification_single_use": True,
        "original_001j_heldout_executed": False,
    }
    write_json(path, freeze)
    return freeze


def load_freeze(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    target = artifact_root(root)
    freeze = json.loads((target / "product_candidate_freeze.json").read_text(encoding="utf-8"))
    for relative, expected in freeze["source_hashes"].items():
        if sha256(root / relative) != expected:
            raise RuntimeError(f"product source changed after freeze: {relative}")
    if sha256(target / "product_evaluation_packets.json") != freeze["packet_sha256"]:
        raise RuntimeError("product packet changed after freeze")
    import numpy as np

    if np.__version__ != freeze["numpy"]:
        raise RuntimeError("product NumPy dependency drift")
    return freeze


def verify_rows(root: Path, prefix: str) -> dict[str, Any]:
    root = Path(root).resolve()
    target = artifact_root(root)
    result = json.loads((target / f"{prefix}_result.json").read_text(encoding="utf-8"))
    rows_path = target / f"{prefix}_rows.jsonl"
    rows = load_rows(rows_path)
    findings = []
    if sha256(rows_path) != result["rows_sha256"]:
        findings.append("rows_sha256_mismatch")
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(rows):
        grouped[(str(row["opaque_context_id"]), str(row["arm"]))].append(row)
        if row["public_input_clean"] is not True or row["public_input_fields"] != list(
            homeostatic_transfer.PUBLIC_INPUT_FIELDS
        ):
            findings.append(f"public_input_mismatch:{index}")
    trajectories = []
    for (context, arm), values in grouped.items():
        ordered = sorted(values, key=lambda row: int(row["sequence"]))
        previous = None
        for sequence, row in enumerate(ordered, start=1):
            unhashed = {key: value for key, value in row.items() if key != "trace_hash"}
            if row["sequence"] != sequence or row["prev_trace_hash"] != previous:
                findings.append(f"trace_chain_mismatch:{context}:{arm}:{sequence}")
            if row["trace_hash"] != canonical_hash(unhashed):
                findings.append(f"row_hash_mismatch:{context}:{arm}:{sequence}")
            previous = row["trace_hash"]
        early = ordered[:EARLY_CUTOFF]
        late = ordered[EARLY_CUTOFF:]
        trajectories.append(
            {
                "opaque_context_id": context,
                "arm": arm,
                "early_deficit_auc": round(sum(row["deficit_loss"] for row in early), 12),
                "late_deficit_auc": round(sum(row["deficit_loss"] for row in late), 12),
                "total_deficit_auc": round(sum(row["deficit_loss"] for row in ordered), 12),
                "final_effect_sign_accuracy": ordered[-1]["effect_sign_accuracy"],
            }
        )
    recomputed = summarize(trajectories)
    if recomputed != result["summary"]:
        findings.append("stored_summary_mismatch")

    with tempfile.TemporaryDirectory(prefix="001l-product-tamper-") as raw_tmp:
        tampered = deepcopy(rows)
        tampered[0]["deficit_loss"] = round(float(tampered[0]["deficit_loss"]) + 0.1, 12)
        tamper_path = Path(raw_tmp) / "rows.jsonl"
        write_jsonl(tamper_path, tampered)
        row_tamper_detected = sha256(tamper_path) != result["rows_sha256"]
    clean_payload = {
        "observation": {
            "schema_version": microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION,
            "visual": [["empty"] * 5 for _ in range(5)],
        },
        "organism": {"energy": 0.5, "safety": 0.5},
        "last_action": None,
        "last_delta": {"energy": 0.0, "safety": 0.0},
    }
    clean_payload["observation"]["visual"][2][2] = "self"
    contaminated = {**clean_payload, "world_id": "private"}
    leakage_detected = not homeostatic_transfer.scan_public_input(contaminated)["clean"]
    report = {
        "schema_version": "ego.v2.homeostatic_survival_loop.verification.v1",
        "task_id": TASK_ID,
        "prefix": prefix,
        "row_count": len(rows),
        "findings": sorted(set(findings)),
        "row_recomputation_match": "stored_summary_mismatch" not in findings,
        "row_value_tamper_detected": row_tamper_detected,
        "candidate_private_input_detected": leakage_detected,
        "passed": not findings and row_tamper_detected and leakage_detected,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--search", action="store_true")
    group.add_argument("--search-multiplicity", action="store_true")
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--qualification", action="store_true")
    group.add_argument(
        "--verify",
        choices=(
            "product_search",
            "product_search_multiplicity",
            "product_qualification",
        ),
    )
    args = parser.parse_args(argv)
    if args.search:
        report = execute_packet(args.root, "search_dev", output_prefix="product_search")
    elif args.search_multiplicity:
        report = execute_packet(
            args.root,
            "search_dev",
            output_prefix="product_search_multiplicity",
        )
    elif args.freeze:
        report = build_freeze(args.root)
    elif args.qualification:
        load_freeze(args.root)
        report = execute_packet(
            args.root, "qualification", output_prefix="product_qualification"
        )
    else:
        report = verify_rows(args.root, str(args.verify))
    print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
