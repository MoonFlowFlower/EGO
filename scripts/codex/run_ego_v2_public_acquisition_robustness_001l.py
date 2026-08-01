"""Single bounded dev-only robustness successor for the frozen 001K candidate."""

from __future__ import annotations

import argparse
from collections import defaultdict
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

from labs.ego_life_playground_v0 import engine, microworld
from scripts.codex import run_ego_v2_public_acquisition_capacity_recovery_001k as predecessor


TASK_ID = "EGO-V2-PUBLIC-ACQUISITION-ROBUSTNESS-001L"
PREDECESSOR_TASK_ID = "EGO-V2-PUBLIC-ACQUISITION-CAPACITY-RECOVERY-001K"
PACKET_NAMES = ("search_dev", "qualification", "replication")
PUBLIC_INPUT_FIELDS = predecessor.PUBLIC_INPUT_FIELDS
SEARCH_POLICY_SEED = 3701
FORMAL_POLICY_SEEDS = (4701, 4702, 4703)
CARRYOVER_CANDIDATE = "S2_RISK_INFORMATION_GAIN_CARRYOVER"
SUBSTANTIVE_CANDIDATES = (
    "S4_HARM_ESCAPE",
    "S4_UNSEEN_FRONTIER_PRIORITY",
)


_BASE_CONFIG = deepcopy(predecessor.CANDIDATE_CONFIGS["S2_RISK_INFORMATION_GAIN"])
CANDIDATE_CONFIGS: dict[str, dict[str, Any]] = {
    CARRYOVER_CANDIDATE: {
        **deepcopy(_BASE_CONFIG),
        "candidate_id": CARRYOVER_CANDIDATE,
        "stage_id": "R0_CARRYOVER_CONTROL",
        "robustness_mode": "carryover",
        "preregistered_prediction": (
            "The unchanged 001K candidate estimates packet variance on new search-dev worlds."
        ),
    },
    "S4_HARM_ESCAPE": {
        **deepcopy(_BASE_CONFIG),
        "candidate_id": "S4_HARM_ESCAPE",
        "stage_id": "R1_ROBUSTNESS_SEARCH",
        "robustness_mode": "harm_escape",
        "preregistered_prediction": (
            "A public-history escape macro should shorten repeated harmful-front loops and "
            "improve recovery without changing posterior updates or token scoring."
        ),
    },
    "S4_UNSEEN_FRONTIER_PRIORITY": {
        **deepcopy(_BASE_CONFIG),
        "candidate_id": "S4_UNSEEN_FRONTIER_PRIORITY",
        "stage_id": "R1_ROBUSTNESS_SEARCH",
        "robustness_mode": "unseen_frontier_priority",
        "preregistered_prediction": (
            "When every visible learned token is harmful, a stateless public sweep should avoid "
            "reorienting toward known harm and discover a beneficial token earlier."
        ),
    },
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _append_rows(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical_json(row) + "\n")


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(canonical_json(row) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def _artifact_root(root: Path) -> Path:
    return Path(root).resolve() / "artifacts" / TASK_ID


def scan_candidate_input(payload: Any) -> dict[str, Any]:
    return predecessor.scan_candidate_input(payload)


def load_packet_assignments(root: Path, packet_name: str) -> list[dict[str, Any]]:
    if packet_name not in PACKET_NAMES:
        raise ValueError("unknown packet")
    artifact_root = _artifact_root(root)
    commitments = json.loads(
        (artifact_root / "packet_commitments.json").read_text(encoding="utf-8")
    )
    packet_path = artifact_root / f"{packet_name}_assignments.json"
    if _sha256(packet_path) != commitments["packets"][packet_name]["assignment_sha256"]:
        raise RuntimeError(f"{packet_name} assignment commitment mismatch")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if (
        packet.get("task_id") != TASK_ID
        or packet.get("packet_name") != packet_name
        or packet.get("dev_only") is not True
        or packet.get("original_001j_assignment") is not False
        or not isinstance(packet.get("assignments"), list)
        or len(packet["assignments"]) != 16
    ):
        raise RuntimeError(f"{packet_name} packet authority mismatch")
    return deepcopy(packet["assignments"])


def audit_frozen_boundaries(root: Path) -> dict[str, Any]:
    artifact_root = _artifact_root(root)
    commitments = json.loads(
        (artifact_root / "packet_commitments.json").read_text(encoding="utf-8")
    )
    protected_path = Path(root).resolve() / commitments[
        "protected_predecessor_hashes_path"
    ]
    if _sha256(protected_path) != commitments["protected_predecessor_hashes_sha256"]:
        raise RuntimeError("protected predecessor manifest changed")
    protected = json.loads(protected_path.read_text(encoding="utf-8"))
    findings = []
    for item in protected["files"]:
        path = Path(root).resolve() / item["path"]
        if not path.is_file() or _sha256(path) != item["sha256"]:
            findings.append(item["path"])
    for packet_name in PACKET_NAMES:
        load_packet_assignments(root, packet_name)
    result = {
        "schema_version": "ego.v2.public_acquisition_robustness.boundary_audit.v1",
        "task_id": TASK_ID,
        "protected_file_count": protected["file_count"],
        "protected_predecessors_unchanged": not findings,
        "protected_findings": findings,
        "candidate_source_created_after_packet_commitment": bool(
            commitments["created_before_candidate_source"]
        ),
        "original_001j_heldout_executed": bool(
            commitments["original_001j_heldout_executed"]
        ),
        "frozen_001k_qualification_rerun": bool(
            commitments["frozen_001k_qualification_rerun"]
        ),
        "frozen_001k_replication_rerun": bool(
            commitments["frozen_001k_replication_rerun"]
        ),
        "packet_hashes_match": True,
    }
    if findings:
        raise RuntimeError("protected predecessor drift")
    return result


class RobustCandidateReference(predecessor.CandidateReference):
    """001K reference plus one preregistered public navigation mechanism."""

    def __init__(self, config: Mapping[str, Any]) -> None:
        if config.get("robustness_mode") not in {
            "carryover",
            "harm_escape",
            "unseen_frontier_priority",
        }:
            raise ValueError("unknown robustness mode")
        super().__init__(config)
        self.state["robustness_state"] = {
            "escape_steps_remaining": 0,
            "escape_token": None,
            "escape_trigger_count": 0,
        }

    def _all_visible_known_harm(
        self,
        ranked: list[Mapping[str, Any]],
        organism: Mapping[str, float],
    ) -> bool:
        """Classify learned effects without reusing the exploration bonus.

        The inherited score intentionally adds uncertainty to encourage a first
        probe.  Reusing that score here would label a one-sample harmful token
        as attractive and would make this mechanism a no-op precisely at the
        preregistered failure boundary.  This check therefore uses only the
        public posterior means and the same fixed homeostatic deficits.
        """

        energy_deficit = max(
            0.0, engine.TARGET_LEVEL - float(organism["energy"])
        )
        safety_deficit = max(
            0.0, engine.TARGET_LEVEL - float(organism["safety"])
        )
        expected_values = []
        for row in ranked:
            stats = self._stats_for_planning(str(row["token"]))
            if stats is None:
                return False
            expected_values.append(
                energy_deficit * float(stats["energy_mean"])
                + safety_deficit * float(stats["safety_mean"])
            )
        return bool(expected_values and all(value <= 0.0 for value in expected_values))

    def plan(self, payload: Mapping[str, Any], *, sequence: int) -> tuple[str, dict[str, Any]]:
        action, receipt = super().plan(payload, sequence=sequence)
        mode = str(self.config["robustness_mode"])
        ranked = list(receipt.get("ranked_tokens", []))
        observation = payload["observation"]
        front = predecessor._front_token(observation)
        front_cell = str(observation["visual"][1][2])
        robustness = self.state["robustness_state"]

        if mode == "unseen_frontier_priority" and self._all_visible_known_harm(
            ranked, payload["organism"]
        ):
            if front_cell in {"wall", *microworld.TOKENS}:
                action = "turn_right"
            else:
                action = "move_forward"
            receipt["selection_reason"] = "public_frontier_escape_known_harm"
            receipt["selected_target"] = None
        elif mode == "harm_escape":
            if receipt["selection_reason"] == "front_token_predicted_harm":
                robustness["escape_steps_remaining"] = 3
                robustness["escape_token"] = front
                robustness["escape_trigger_count"] = int(
                    robustness["escape_trigger_count"]
                ) + 1
                action = "turn_right"
                receipt["selection_reason"] = "public_harm_escape_trigger"
                receipt["selected_target"] = None
            elif int(robustness["escape_steps_remaining"]) > 0:
                action = "turn_right" if front_cell in {"wall", *microworld.TOKENS} else "move_forward"
                robustness["escape_steps_remaining"] = max(
                    0, int(robustness["escape_steps_remaining"]) - 1
                )
                receipt["selection_reason"] = "public_harm_escape_macro"
                receipt["selected_target"] = None

        receipt["selected_action"] = action
        receipt["public_input_fields"] = list(PUBLIC_INPUT_FIELDS)
        receipt["robustness_mode"] = mode
        receipt["robustness_state_hash"] = canonical_hash(robustness)
        receipt["state_hash_after"] = canonical_hash(self.state)
        return action, receipt

    def update_after_public_transition(self, **kwargs: Any) -> dict[str, Any]:
        before_known = set(self.state["token_stats"])
        receipt = super().update_after_public_transition(**kwargs)
        after_known = set(self.state["token_stats"])
        if after_known != before_known:
            self.state["robustness_state"]["escape_steps_remaining"] = 0
            self.state["robustness_state"]["escape_token"] = None
        receipt["robustness_state_hash"] = canonical_hash(
            self.state["robustness_state"]
        )
        receipt["state_hash_after"] = canonical_hash(self.state)
        return receipt

    def reset_for_respawn(self) -> None:
        super().reset_for_respawn()
        self.state["robustness_state"]["escape_steps_remaining"] = 0
        self.state["robustness_state"]["escape_token"] = None


def _candidate(config: Mapping[str, Any]) -> RobustCandidateReference:
    if config.get("evaluator_only"):
        raise ValueError("001L has no evaluator-only candidate")
    return RobustCandidateReference(config)


def _beneficial_cause(spec: Mapping[str, Any]) -> str:
    return "resource" if spec["profile_name"] == "energy_low" else "shelter"


def _effect_sign_accuracy(
    reference: RobustCandidateReference, mapping: Mapping[str, str]
) -> float:
    predictions = reference.effect_sign_predictions()
    correct = 0
    total = 0
    for token in microworld.TOKENS:
        expected = predecessor._expected_interaction_delta(str(mapping[token]))
        predicted = predictions[token]
        for key in ("energy", "safety"):
            total += 1
            if predicted is not None and int(predicted[key]) == predecessor._sign(expected[key]):
                correct += 1
    return round(correct / total, 12)


def run_trajectory(
    spec: Mapping[str, Any],
    arm: str,
    *,
    budget: int,
    policy_seed: int,
    candidate_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if arm not in {"PRIVATE_ORACLE_NAVIGATOR", "UNIFORM_RANDOM", "PUBLIC_REFERENCE"}:
        raise ValueError("unknown trajectory arm")
    if (arm == "PUBLIC_REFERENCE") != (candidate_config is not None):
        raise ValueError("candidate config/arm mismatch")
    world = microworld.initial_world_state(
        seed=int(spec["world_seed"]), layout_id=str(spec["layout_id"])
    )
    if dict(world["trial"]["token_mapping"]) != dict(spec["mapping_commitment"]):
        raise RuntimeError("packet mapping commitment mismatch")
    private_spec = {**deepcopy(dict(spec)), "context_id": spec["opaque_context_id"]}
    organism = predecessor._initial_organism(private_spec)
    reference = _candidate(candidate_config) if candidate_config is not None else None
    candidate_id = (
        str(candidate_config["candidate_id"])
        if candidate_config is not None
        else arm
    )
    last_action: str | None = None
    last_delta = {"energy": 0.0, "safety": 0.0}
    life_index = 1
    deaths = 0
    previous_trace_hash: str | None = None
    rows: list[dict[str, Any]] = []
    cumulative_deficit_loss = 0.0
    first_beneficial_step: int | None = None
    current_harm_loop = 0
    max_harm_loop = 0
    code_hash = engine.compute_code_path_hash()
    run_meta = {
        "run_id": f"{TASK_ID}:{spec['opaque_context_id']}:{candidate_id}:{policy_seed}:{budget}",
        "seed": policy_seed,
    }
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
        scan = scan_candidate_input(payload)
        if not scan["clean"]:
            raise RuntimeError("constructed candidate payload is contaminated")
        if arm == "PRIVATE_ORACLE_NAVIGATOR":
            selected_action = predecessor._oracle_action(world, organism)
            plan_receipt = {
                "selected_action": selected_action,
                "selection_reason": "private_evaluator_shortest_survival_route",
                "selected_target": None,
                "ranked_tokens": [],
                "posterior_hash": None,
                "public_input_fields": list(PUBLIC_INPUT_FIELDS),
            }
        elif arm == "UNIFORM_RANDOM":
            selected_action = predecessor._random_action(
                private_spec, policy_seed=policy_seed, sequence=sequence
            )
            plan_receipt = {
                "selected_action": selected_action,
                "selection_reason": "deterministic_uniform_hash",
                "selected_target": None,
                "ranked_tokens": [],
                "posterior_hash": None,
                "public_input_fields": list(PUBLIC_INPUT_FIELDS),
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
            source_episode_id=f"001l-life-{life_index}",
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
            episode_id=f"001l-life-{life_index}",
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
        update_receipt = None
        front_before = predecessor._front_token(observation)
        if reference is not None and transition.get("outcome_type") == "interacted":
            if front_before not in microworld.TOKENS or str(transition.get("token")) != front_before:
                raise RuntimeError("public front token disagrees with interaction")
            update_receipt = reference.update_after_public_transition(
                observed_token=front_before,
                selected_action=selected_action,
                observed_outcome_type="interacted",
                actual_delta=observed_delta,
            )
        beneficial = bool(
            transition.get("outcome_type") == "interacted"
            and transition.get("cause") == _beneficial_cause(spec)
        )
        if beneficial and first_beneficial_step is None:
            first_beneficial_step = sequence
        reason = str(plan_receipt["selection_reason"])
        harm_loop_step = reason in {
            "front_token_predicted_harm",
            "orient_side_or_rear_token",
            "public_harm_escape_trigger",
            "public_harm_escape_macro",
            "public_frontier_escape_known_harm",
        } and transition.get("outcome_type") != "interacted"
        current_harm_loop = current_harm_loop + 1 if harm_loop_step else 0
        max_harm_loop = max(max_harm_loop, current_harm_loop)
        died = float(organism["energy"]) == 0.0
        if died:
            deaths += 1
        step_loss = predecessor._deficit_loss(organism, died=died)
        cumulative_deficit_loss = round(cumulative_deficit_loss + step_loss, 12)
        sign_accuracy = (
            None
            if reference is None
            else _effect_sign_accuracy(reference, spec["mapping_commitment"])
        )
        known_count = (
            None
            if reference is None
            else sum(
                prediction is not None
                for prediction in reference.effect_sign_predictions().values()
            )
        )
        row_without_hash = {
            "schema_version": "ego.v2.public_acquisition_robustness.row.v1",
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
            "front_public_token": (
                front_before if front_before in microworld.TOKENS else None
            ),
            "selected_action": selected_action,
            "selection_reason": reason,
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
            "known_token_count": known_count,
            "beneficial_interaction": beneficial,
            "harm_loop_step": harm_loop_step,
            "harm_loop_run": current_harm_loop,
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
            organism = predecessor._initial_organism(private_spec)
            if reference is not None:
                reference.reset_for_respawn()

    return {
        "schema_version": "ego.v2.public_acquisition_robustness.trajectory.v1",
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
        "first_beneficial_interaction_step": (
            budget + 1 if first_beneficial_step is None else first_beneficial_step
        ),
        "harmful_front_loop_run_max": max_harm_loop,
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


def summarize_candidate(
    candidate_id: str,
    config: Mapping[str, Any],
    public: list[Mapping[str, Any]],
    oracle: list[Mapping[str, Any]],
    random: list[Mapping[str, Any]],
) -> dict[str, Any]:
    summary = predecessor._summarize_candidate(
        candidate_id, config, public, oracle, random
    )
    summary["unique_world_count"] = len(
        {str(item["opaque_context_id"]) for item in public}
    )
    summary["mean_first_beneficial_interaction_step"] = round(
        sum(int(item["first_beneficial_interaction_step"]) for item in public)
        / len(public),
        12,
    )
    summary["mean_harmful_front_loop_run_max"] = round(
        sum(int(item["harmful_front_loop_run_max"]) for item in public)
        / len(public),
        12,
    )
    return summary


def _world_direction_summary(
    public: list[Mapping[str, Any]], random: list[Mapping[str, Any]]
) -> dict[str, Any]:
    return predecessor._world_direction_summary(public, random)


def _candidate_selection(
    summaries: list[Mapping[str, Any]],
) -> dict[str, Any]:
    by_id = {str(item["candidate_id"]): item for item in summaries}
    control = by_id[CARRYOVER_CANDIDATE]
    eligible = []
    comparisons = []
    for candidate_id in SUBSTANTIVE_CANDIDATES:
        item = by_id[candidate_id]
        recovery_improved = float(item["recovery_fraction"]) > float(
            control["recovery_fraction"]
        )
        first_good_improved = float(
            item["mean_first_beneficial_interaction_step"]
        ) < float(control["mean_first_beneficial_interaction_step"])
        loop_improved = float(item["mean_harmful_front_loop_run_max"]) < float(
            control["mean_harmful_front_loop_run_max"]
        )
        targeted = loop_improved if candidate_id == "S4_HARM_ESCAPE" else (
            first_good_improved or loop_improved
        )
        row = {
            "candidate_id": candidate_id,
            "recovery_improved": recovery_improved,
            "first_beneficial_step_improved": first_good_improved,
            "harm_loop_improved": loop_improved,
            "targeted_diagnostic_improved": targeted,
            "formal_eligible": recovery_improved and targeted,
        }
        comparisons.append(row)
        if row["formal_eligible"]:
            eligible.append(item)
    eligible.sort(
        key=lambda item: (
            -float(item["recovery_fraction"]),
            -int(item["positive_direction_count"]),
            float(item["mean_first_beneficial_interaction_step"]),
            float(item["mean_harmful_front_loop_run_max"]),
            str(item["candidate_id"]),
        )
    )
    return {
        "schema_version": "ego.v2.public_acquisition_robustness.selection.v1",
        "preregistered_order": [
            "highest_unique_world_mean_recovery",
            "highest_positive_world_count",
            "earliest_first_beneficial_interaction",
            "shortest_harmful_front_loop",
        ],
        "control_candidate": CARRYOVER_CANDIDATE,
        "comparisons": comparisons,
        "selected_candidate": (
            None if not eligible else str(eligible[0]["candidate_id"])
        ),
        "formal_authorized": bool(eligible),
    }


def run_search(root: Path, *, output_root: Path | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    output_root = Path(output_root or _artifact_root(root)).resolve()
    result_path = output_root / "search_results.json"
    rows_path = output_root / "search_rows.jsonl"
    if result_path.exists() or rows_path.exists():
        raise RuntimeError("001L search result already exists")
    audit = audit_frozen_boundaries(root)
    specs = load_packet_assignments(root, "search_dev")
    oracle = [
        run_trajectory(
            spec, "PRIVATE_ORACLE_NAVIGATOR", budget=96, policy_seed=SEARCH_POLICY_SEED
        )
        for spec in specs
    ]
    random = [
        run_trajectory(
            spec, "UNIFORM_RANDOM", budget=96, policy_seed=SEARCH_POLICY_SEED
        )
        for spec in specs
    ]
    by_candidate: dict[str, list[dict[str, Any]]] = {}
    all_rows = [
        {**row, "search_packet_name": "search_dev"}
        for item in [*oracle, *random]
        for row in item["rows"]
    ]
    for candidate_id in (CARRYOVER_CANDIDATE, *SUBSTANTIVE_CANDIDATES):
        config = deepcopy(CANDIDATE_CONFIGS[candidate_id])
        trajectories = [
            run_trajectory(
                spec,
                "PUBLIC_REFERENCE",
                budget=96,
                policy_seed=SEARCH_POLICY_SEED,
                candidate_config=config,
            )
            for spec in specs
        ]
        by_candidate[candidate_id] = trajectories
        all_rows.extend(
            {**row, "search_packet_name": "search_dev"}
            for item in trajectories
            for row in item["rows"]
        )
    summaries = [
        summarize_candidate(
            candidate_id,
            CANDIDATE_CONFIGS[candidate_id],
            by_candidate[candidate_id],
            oracle,
            random,
        )
        for candidate_id in (CARRYOVER_CANDIDATE, *SUBSTANTIVE_CANDIDATES)
    ]
    selection = _candidate_selection(summaries)
    result = {
        "schema_version": "ego.v2.public_acquisition_robustness.search.v1",
        "task_id": TASK_ID,
        "packet_name": "search_dev",
        "candidate_budget": 2,
        "substantive_candidates_executed": list(SUBSTANTIVE_CANDIDATES),
        "carryover_control_executed": CARRYOVER_CANDIDATE,
        "policy_seed": SEARCH_POLICY_SEED,
        "action_budget": 96,
        "boundary_audit": audit,
        "candidates": summaries,
        "selection": selection,
        "verdict": (
            "SEARCH_CANDIDATE_FROZEN_READY"
            if selection["formal_authorized"]
            else "ROBUSTNESS_SEARCH_FAILED_STOP_WITHOUT_FORMAL_CONSUMPTION"
        ),
    }
    _append_rows(rows_path, all_rows)
    result["rows_path"] = rows_path.relative_to(root).as_posix()
    result["rows_sha256"] = _sha256(rows_path)
    _write_json(result_path, result)
    comparisons = {
        row["candidate_id"]: row for row in selection["comparisons"]
    }
    trial_rows = []
    for summary in summaries:
        candidate_id = str(summary["candidate_id"])
        comparison = comparisons.get(candidate_id)
        allowed = (
            candidate_id == CARRYOVER_CANDIDATE
            or bool(comparison and comparison["formal_eligible"])
        )
        trial_rows.append(
            {
                "schema_version": "ego.v2.public_acquisition_robustness.trial.v1",
                "task_id": TASK_ID,
                "stage": "search_dev",
                "candidate_id": candidate_id,
                "hypothesis": CANDIDATE_CONFIGS[candidate_id][
                    "preregistered_prediction"
                ],
                "mechanism_change": CANDIDATE_CONFIGS[candidate_id][
                    "robustness_mode"
                ],
                "random_deficit_auc": summary["loss_by_arm"]["UNIFORM_RANDOM"],
                "oracle_deficit_auc": summary["loss_by_arm"][
                    "PRIVATE_ORACLE_NAVIGATOR"
                ],
                "public_deficit_auc": summary["loss_by_arm"]["PUBLIC_REFERENCE"],
                "public_reference_gain": summary["public_reference_gain"],
                "recovery_fraction": summary["recovery_fraction"],
                "positive_world_count": summary["positive_direction_count"],
                "world_count": summary["unique_world_count"],
                "first_beneficial_interaction_step": summary[
                    "mean_first_beneficial_interaction_step"
                ],
                "harmful_front_loop_run_max": summary[
                    "mean_harmful_front_loop_run_max"
                ],
                "comparison_to_carryover": comparison,
                "failure_explanation": (
                    None
                    if allowed
                    else "Did not improve both recovery and the preregistered diagnostic."
                ),
                "next_stage_allowed": bool(
                    comparison and comparison["formal_eligible"]
                ),
            }
        )
    _write_jsonl(output_root / "search_trial_registry.jsonl", trial_rows)
    _write_json(
        output_root / "stage_scorecard.json",
        {
            "schema_version": "ego.v2.public_acquisition_robustness.scorecard.v1",
            "task_id": TASK_ID,
            "search": result,
            "qualification": "NOT_RUN",
            "replication": "NOT_RUN",
            "thresholds_lowered": False,
            "original_001j_heldout_executed": False,
        },
    )
    if not selection["formal_authorized"]:
        _write_json(
            output_root / "failure_manifest.json",
            {
                "schema_version": "ego.v2.public_acquisition_robustness.failures.v1",
                "task_id": TASK_ID,
                "failed_trials": [row for row in trial_rows if row["failure_explanation"]],
                "terminal_verdict": "ROBUSTNESS_NOT_ESTABLISHED_M1_NOT_AUTHORIZED",
                "formal_packets_consumed": [],
                "thresholds_lowered": False,
            },
        )
    return result


def build_candidate_freeze(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    artifact_root = _artifact_root(root)
    output_path = artifact_root / "candidate_freeze.json"
    if output_path.exists():
        raise RuntimeError("candidate freeze is single-write")
    search_path = artifact_root / "search_results.json"
    search = json.loads(search_path.read_text(encoding="utf-8"))
    selected = search["selection"]["selected_candidate"]
    if selected not in SUBSTANTIVE_CANDIDATES or not search["selection"]["formal_authorized"]:
        raise RuntimeError("search did not authorize a formal candidate")
    commitments = json.loads(
        (artifact_root / "packet_commitments.json").read_text(encoding="utf-8")
    )
    source_path = Path(__file__).resolve()
    verifier_path = root / "scripts" / "codex" / (
        "verify_ego_v2_public_acquisition_robustness_001l.py"
    )
    if not verifier_path.is_file():
        raise RuntimeError("independent verifier must exist before candidate freeze")
    freeze = {
        "schema_version": "ego.v2.public_acquisition_robustness.freeze.v1",
        "task_id": TASK_ID,
        "candidate_id": selected,
        "candidate_config": deepcopy(CANDIDATE_CONFIGS[selected]),
        "candidate_config_hash": canonical_hash(CANDIDATE_CONFIGS[selected]),
        "producer_path": source_path.relative_to(root).as_posix(),
        "producer_sha256": _sha256(source_path),
        "verifier_path": verifier_path.relative_to(root).as_posix(),
        "verifier_sha256": _sha256(verifier_path),
        "search_results_sha256": _sha256(search_path),
        "packet_assignment_sha256": {
            name: commitments["packets"][name]["assignment_sha256"]
            for name in PACKET_NAMES
        },
        "formal_action_budget": 96,
        "formal_policy_seeds": list(FORMAL_POLICY_SEEDS),
        "thresholds": {
            "public_reference_gain_strictly_positive": 0.0,
            "recovery_fraction_minimum": 0.50,
            "positive_world_count_minimum": 12,
            "effect_sign_accuracy_minimum": 0.80,
            "material_ablation_absolute_floor": 0.02,
            "material_ablation_relative_gain_fraction": 0.30,
            "material_ablation_count_minimum": 2,
        },
        "ablation_ids": [
            "FORMAL_NO_UPDATE",
            "FORMAL_FEEDBACK_SHUFFLE",
            "FORMAL_POSTERIOR_ABLATION",
        ],
        "qualification_single_use": True,
        "replication_single_use": True,
        "replication_runs_unchanged_even_if_qualification_fails": True,
        "dependency_contract": {
            "numpy": "2.2.6",
            "network": False,
            "llm": False,
        },
        "original_001j_heldout_executed": False,
        "frozen_001k_formal_packets_rerun": False,
    }
    _write_json(output_path, freeze)
    return freeze


def _load_freeze(root: Path) -> dict[str, Any]:
    artifact_root = _artifact_root(root)
    freeze_path = artifact_root / "candidate_freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if (
        freeze.get("task_id") != TASK_ID
        or freeze.get("candidate_id") not in SUBSTANTIVE_CANDIDATES
        or freeze.get("candidate_config_hash")
        != canonical_hash(freeze.get("candidate_config"))
        or freeze.get("producer_sha256") != _sha256(Path(__file__).resolve())
    ):
        raise RuntimeError("candidate freeze/source mismatch")
    verifier_path = Path(root).resolve() / str(freeze.get("verifier_path", ""))
    if (
        not verifier_path.is_file()
        or freeze.get("verifier_sha256") != _sha256(verifier_path)
    ):
        raise RuntimeError("independent verifier changed after candidate freeze")
    for packet_name, expected in freeze["packet_assignment_sha256"].items():
        if _sha256(artifact_root / f"{packet_name}_assignments.json") != expected:
            raise RuntimeError("formal packet changed after freeze")
    import numpy as np

    if np.__version__ != freeze["dependency_contract"]["numpy"]:
        raise RuntimeError("NumPy dependency drift after candidate freeze")
    audit_frozen_boundaries(root)
    return freeze


def _formal_configs(base: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result = {"PUBLIC_REFERENCE": deepcopy(dict(base))}
    for candidate_id, posterior_mode in {
        "FORMAL_NO_UPDATE": "no_update",
        "FORMAL_FEEDBACK_SHUFFLE": "feedback_shuffle",
        "FORMAL_POSTERIOR_ABLATION": "posterior_ablation",
    }.items():
        config = deepcopy(dict(base))
        config["candidate_id"] = candidate_id
        config["posterior_mode"] = posterior_mode
        config["preregistered_prediction"] = (
            f"{candidate_id} should materially damage posterior-mediated gain."
        )
        result[candidate_id] = config
    return result


def _material_ablation_report(
    candidate: Mapping[str, Any],
    ablations: list[Mapping[str, Any]],
    thresholds: Mapping[str, Any],
) -> dict[str, Any]:
    return predecessor._material_ablation_report(candidate, ablations, thresholds)


def run_formal_packet(root: Path, packet_name: str) -> dict[str, Any]:
    if packet_name not in {"qualification", "replication"}:
        raise ValueError("formal packet must be qualification or replication")
    root = Path(root).resolve()
    artifact_root = _artifact_root(root)
    result_path = artifact_root / f"{packet_name}_result.json"
    rows_path = artifact_root / f"{packet_name}_rows.jsonl"
    if result_path.exists() or rows_path.exists():
        raise RuntimeError(f"{packet_name} packet is single-use and already executed")
    if packet_name == "replication" and not (
        artifact_root / "qualification_result.json"
    ).is_file():
        raise RuntimeError("replication requires the single qualification readback")
    freeze = _load_freeze(root)
    specs = load_packet_assignments(root, packet_name)
    configs = _formal_configs(freeze["candidate_config"])
    budget = int(freeze["formal_action_budget"])
    seeds = list(freeze["formal_policy_seeds"])
    oracle: list[dict[str, Any]] = []
    random: list[dict[str, Any]] = []
    by_candidate: dict[str, list[dict[str, Any]]] = {key: [] for key in configs}
    all_rows: list[dict[str, Any]] = []
    replay_checks = []
    for spec in specs:
        for policy_seed in seeds:
            o = run_trajectory(
                spec,
                "PRIVATE_ORACLE_NAVIGATOR",
                budget=budget,
                policy_seed=policy_seed,
            )
            r = run_trajectory(
                spec,
                "UNIFORM_RANDOM",
                budget=budget,
                policy_seed=policy_seed,
            )
            oracle.append(o)
            random.append(r)
            for item in (o, r):
                all_rows.extend(
                    {**row, "formal_packet_name": packet_name} for row in item["rows"]
                )
            for candidate_id, config in configs.items():
                item = run_trajectory(
                    spec,
                    "PUBLIC_REFERENCE",
                    budget=budget,
                    policy_seed=policy_seed,
                    candidate_config=config,
                )
                by_candidate[candidate_id].append(item)
                all_rows.extend(
                    {**row, "formal_packet_name": packet_name}
                    for row in item["rows"]
                )
                if candidate_id == "PUBLIC_REFERENCE":
                    replayed = run_trajectory(
                        spec,
                        "PUBLIC_REFERENCE",
                        budget=budget,
                        policy_seed=policy_seed,
                        candidate_config=config,
                    )
                    replay_checks.append(
                        {
                            "opaque_context_id": spec["opaque_context_id"],
                            "policy_seed": policy_seed,
                            "produced_hash": canonical_hash(item),
                            "replayed_hash": canonical_hash(replayed),
                            "stored_actions_used_as_replay_input": False,
                            "match": canonical_hash(item) == canonical_hash(replayed),
                        }
                    )
    candidate = summarize_candidate(
        "PUBLIC_REFERENCE",
        configs["PUBLIC_REFERENCE"],
        by_candidate["PUBLIC_REFERENCE"],
        oracle,
        random,
    )
    ablations = [
        summarize_candidate(
            candidate_id, configs[candidate_id], values, oracle, random
        )
        for candidate_id, values in by_candidate.items()
        if candidate_id != "PUBLIC_REFERENCE"
    ]
    world_directions = _world_direction_summary(
        by_candidate["PUBLIC_REFERENCE"], random
    )
    thresholds = freeze["thresholds"]
    ablation_report = _material_ablation_report(candidate, ablations, thresholds)
    gates = {
        "public_reference_gain_positive": float(candidate["public_reference_gain"])
        > float(thresholds["public_reference_gain_strictly_positive"]),
        "recovery_fraction": float(candidate["recovery_fraction"])
        >= float(thresholds["recovery_fraction_minimum"]),
        "positive_world_count": int(world_directions["positive_world_count"])
        >= int(thresholds["positive_world_count_minimum"]),
        "effect_sign_accuracy": float(candidate["mean_final_effect_sign_accuracy"])
        >= float(thresholds["effect_sign_accuracy_minimum"]),
        "material_ablation_count": int(ablation_report["material_count"])
        >= int(ablation_report["required_material_count"]),
        "candidate_replay_exact": all(item["match"] for item in replay_checks),
        "candidate_inputs_clean": all(
            row["candidate_input_clean"]
            and row["candidate_input_fields"] == list(PUBLIC_INPUT_FIELDS)
            for row in all_rows
            if row["arm"] == "PUBLIC_REFERENCE"
        ),
        "protected_predecessors_unchanged": True,
    }
    passed = all(gates.values())
    result = {
        "schema_version": "ego.v2.public_acquisition_robustness.formal.v1",
        "task_id": TASK_ID,
        "packet_name": packet_name,
        "single_use": True,
        "candidate_id": freeze["candidate_id"],
        "candidate_freeze_hash": canonical_hash(freeze),
        "producer_sha256": freeze["producer_sha256"],
        "assignment_sha256": freeze["packet_assignment_sha256"][packet_name],
        "action_budget": budget,
        "policy_seeds": seeds,
        "public_policy_seed_independence_note": (
            "Public policy is deterministic; unique-world aggregates are primary. "
            "Policy seeds create paired random baselines, not independent public policies."
        ),
        "executed_world_count": len(specs),
        "trajectory_count_by_arm": len(specs) * len(seeds),
        "candidate": candidate,
        "ablations": ablations,
        "ablation_report": ablation_report,
        "world_directions": world_directions,
        "replay_checks": replay_checks,
        "gates": gates,
        "all_gates_pass": passed,
        "verdict": (
            f"{packet_name.upper()}_ROBUSTNESS_GATE_PASS"
            if passed
            else f"{packet_name.upper()}_ROBUSTNESS_GATE_FAIL"
        ),
        "original_001j_heldout_executed": False,
        "frozen_001k_formal_packets_rerun": False,
    }
    _append_rows(rows_path, all_rows)
    result["rows_path"] = rows_path.relative_to(root).as_posix()
    result["rows_sha256"] = _sha256(rows_path)
    _write_json(result_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--audit", action="store_true")
    group.add_argument("--search", action="store_true")
    group.add_argument("--freeze-candidate", action="store_true")
    group.add_argument("--formal", choices=("qualification", "replication"))
    args = parser.parse_args(argv)
    if args.audit:
        result = audit_frozen_boundaries(args.root)
    elif args.search:
        result = run_search(args.root)
    elif args.freeze_candidate:
        result = build_candidate_freeze(args.root)
    else:
        result = run_formal_packet(args.root, args.formal)
    print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
