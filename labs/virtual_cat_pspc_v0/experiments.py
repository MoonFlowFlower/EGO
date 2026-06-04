from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .environment import Action, GridObject, ObjectFeatures, VirtualCatGridWorld
from .memory import EpisodicMemory
from .models import SelfModel, WorldModel
from .planning import MPCPlanner


@dataclass(frozen=True)
class ConditionResult:
    seed: int
    scenario: str
    selected_action: str
    caution_score: float
    self_risk_score: float
    world_prediction_error: float
    trace_hash: str
    trace_payload: Dict[str, object]


def build_candidate_object(
    *,
    object_id: str = "blue_glass_bottle_unseen",
    name: str = "blue glass bottle",
    features: ObjectFeatures | None = None,
    position: Tuple[int, int] = (3, 1),
) -> GridObject:
    return GridObject(
        object_id=object_id,
        name=name,
        position=position,
        features=features or ObjectFeatures(instability=0.88, height=0.92, fragility=0.84, novelty=0.70),
    )


def run_condition(
    *,
    seed: int,
    history: str,
    target: GridObject,
    layout_id: str = "default",
    object_kind: str = "candidate",
    delete_relevant_memory: bool = False,
    freeze_world_model: bool = False,
    freeze_self_model: bool = False,
    disable_prediction_error_learning: bool = False,
) -> ConditionResult:
    env = VirtualCatGridWorld(seed=seed)
    memory = _build_memory(env=env, seed=seed, history=history)
    deleted_count = 0
    if delete_relevant_memory:
        deleted_count = memory.delete_relevant("unstable_tall_object")

    world_model = WorldModel(seed=seed)
    self_model = SelfModel(seed=seed)
    world_losses: List[float] = []
    self_losses: List[float] = []

    if not freeze_world_model and not disable_prediction_error_learning:
        world_losses = world_model.fit(memory.transitions)
    if not freeze_self_model and not disable_prediction_error_learning:
        self_losses = self_model.fit(memory.transitions, world_model)

    planner = MPCPlanner(world_model=world_model, self_model=self_model, seed=seed)
    plan = planner.plan(target)
    actual = env.simulate_action(target, Action.APPROACH).actual
    prediction_error = world_model.prediction_error(target, Action.APPROACH, actual)
    approach_world_prediction = world_model.predict(target, Action.APPROACH)
    approach_self_prediction = self_model.predict(approach_world_prediction, Action.APPROACH)
    scenario = _scenario_name(
        history=history,
        delete_relevant_memory=delete_relevant_memory,
        freeze_world_model=freeze_world_model,
        freeze_self_model=freeze_self_model,
        disable_prediction_error_learning=disable_prediction_error_learning,
    )
    trace_payload: Dict[str, object] = {
        "episode_id": f"trace_ep_{seed}",
        "seed": seed,
        "t": 42,
        "scenario": scenario,
        "layout_id": layout_id,
        "object_kind": object_kind,
        "target_object_id": target.object_id,
        "target_position": target.position,
        "candidate_object_features": target.features.to_dict(),
        "candidate_actions": plan.candidate_actions,
        "world_prediction": plan.world_prediction,
        "self_prediction": plan.self_prediction,
        "approach_world_prediction": approach_world_prediction,
        "approach_self_prediction": approach_self_prediction,
        "homeostatic_score": plan.homeostatic_score,
        "selected_action": plan.selected_action,
        "prediction_error": prediction_error,
        "memory_refs": memory.to_trace_refs(),
        "deleted_memory_count": deleted_count,
        "model_update_refs": world_model.update_refs + self_model.update_refs,
        "world_losses": world_losses,
        "self_losses": self_losses,
    }
    trace_hash = _hash_payload(trace_payload)
    trace_payload["trace_hash"] = trace_hash
    return ConditionResult(
        seed=seed,
        scenario=scenario,
        selected_action=plan.selected_action,
        caution_score=plan.caution_score,
        self_risk_score=round(float(approach_self_prediction["damage_risk"]), 4),
        world_prediction_error=prediction_error,
        trace_hash=trace_hash,
        trace_payload=trace_payload,
    )


def run_replay_pair(seed: int) -> Tuple[ConditionResult, ConditionResult]:
    target = build_candidate_object()
    first = run_condition(seed=seed, history="danger", target=target)
    second = run_condition(seed=seed, history="danger", target=target)
    return first, second


def run_anti_hardcoding_audit(seed: int) -> Dict[str, object]:
    unstable_features = ObjectFeatures(instability=0.88, height=0.72, fragility=0.35, novelty=0.70)
    baseline = run_condition(seed=seed, history="danger", target=build_candidate_object(features=unstable_features))
    renamed_a = run_condition(
        seed=seed,
        history="danger",
        target=build_candidate_object(object_id="object_A", name="object A", features=unstable_features),
    )
    renamed_b = run_condition(
        seed=seed,
        history="danger",
        target=build_candidate_object(object_id="object_B", name="object B", features=unstable_features),
    )
    no_cup_name = run_condition(
        seed=seed,
        history="danger",
        target=build_candidate_object(
            object_id="unstable_tall_object_no_cup_name",
            name="plain tall object",
            features=unstable_features,
        ),
    )
    instability_removed = run_condition(
        seed=seed,
        history="danger",
        target=build_candidate_object(
            object_id="object_A_instability_removed",
            name="object A instability removed",
            features=ObjectFeatures(instability=0.0, height=0.72, fragility=0.35, novelty=0.70),
        ),
    )

    return {
        "seed": seed,
        "status": "pass"
        if (
            not _object_name_rule_hits()
            and baseline.selected_action == renamed_a.selected_action == renamed_b.selected_action
            and no_cup_name.selected_action in {"observe", "retreat"}
            and instability_removed.caution_score < baseline.caution_score - 0.20
        )
        else "hold",
        "object_name_rule_hits": _object_name_rule_hits(),
        "baseline_unstable": _audit_result(baseline),
        "renamed_object_a": _audit_result(renamed_a),
        "renamed_object_b": _audit_result(renamed_b),
        "unstable_tall_object_without_cup_name": _audit_result(no_cup_name),
        "instability_feature_removed": _audit_result(instability_removed),
        "what_it_proves": (
            "Object renaming does not change the cautious decision, while removing the instability feature "
            "reduces cautious behavior in this deterministic lab audit."
        ),
        "what_it_does_not_prove": (
            "This does not prove absence of every possible shortcut, multi-layout generalization, "
            "runtime efficacy, stable user benefit, live autonomy, or consciousness."
        ),
    }


def run_generalization_matrix(
    *,
    seeds: Iterable[int],
    layout_ids: Iterable[str] | None = None,
    object_kinds: Iterable[str] | None = None,
) -> Dict[str, object]:
    seed_list = [int(seed) for seed in seeds]
    layout_list = list(layout_ids or ["center_room", "near_wall"])
    object_kind_list = list(object_kinds or ["cup", "vase", "bottle", "tall_box"])
    cases: List[Dict[str, object]] = []
    gaps: List[float] = []
    danger_cautions: List[float] = []
    safe_cautions: List[float] = []
    danger_action_count = 0

    for seed in seed_list:
        for layout_id in layout_list:
            for object_kind in object_kind_list:
                target = build_generalization_object(object_kind=object_kind, layout_id=layout_id)
                danger = run_condition(
                    seed=seed,
                    history="danger",
                    target=target,
                    layout_id=layout_id,
                    object_kind=object_kind,
                )
                safe = run_condition(
                    seed=seed,
                    history="safe",
                    target=target,
                    layout_id=layout_id,
                    object_kind=object_kind,
                )
                gap = round(danger.caution_score - safe.caution_score, 4)
                gaps.append(gap)
                danger_cautions.append(danger.caution_score)
                safe_cautions.append(safe.caution_score)
                if danger.selected_action in {"observe", "retreat"}:
                    danger_action_count += 1
                cases.append(
                    {
                        "seed": seed,
                        "layout_id": layout_id,
                        "object_kind": object_kind,
                        "caution_gap": gap,
                        "danger": _generalization_result(danger),
                        "safe": _generalization_result(safe),
                    }
                )

    case_count = len(cases)
    min_gap = min(gaps) if gaps else 0.0
    danger_action_rate = round(danger_action_count / case_count, 4) if case_count else 0.0
    status = "pass" if case_count > 0 and min_gap > 0.20 and danger_action_rate == 1.0 else "hold"
    return {
        "status": status,
        "seeds": seed_list,
        "layout_ids": layout_list,
        "object_kinds": object_kind_list,
        "case_count": case_count,
        "danger_caution_mean": round(sum(danger_cautions) / len(danger_cautions), 4) if danger_cautions else 0.0,
        "safe_caution_mean": round(sum(safe_cautions) / len(safe_cautions), 4) if safe_cautions else 0.0,
        "min_caution_gap": round(min_gap, 4),
        "danger_action_rate": danger_action_rate,
        "cases": cases,
        "what_it_proves": (
            "Danger-history caution stays above safe-history baseline across the configured seeds, "
            "layouts, and unstable object kinds."
        ),
        "what_it_does_not_prove": (
            "This does not prove unlimited layout generalization, real-world transfer, user benefit, "
            "EgoOperator runtime efficacy, live autonomy, consciousness, or subjective experience."
        ),
    }


def build_generalization_object(*, object_kind: str, layout_id: str) -> GridObject:
    features_by_kind = {
        "cup": ObjectFeatures(instability=0.86, height=0.76, fragility=0.78, novelty=0.62),
        "vase": ObjectFeatures(instability=0.90, height=0.94, fragility=0.72, novelty=0.58),
        "bottle": ObjectFeatures(instability=0.84, height=0.88, fragility=0.84, novelty=0.70),
        "tall_box": ObjectFeatures(instability=0.82, height=0.91, fragility=0.55, novelty=0.52),
    }
    positions_by_layout = {
        "center_room": (3, 1),
        "near_wall": (4, 2),
        "narrow_corridor": (2, 3),
    }
    if object_kind not in features_by_kind:
        raise ValueError(f"unknown object_kind: {object_kind}")
    if layout_id not in positions_by_layout:
        raise ValueError(f"unknown layout_id: {layout_id}")
    return build_candidate_object(
        object_id=f"generalization_{layout_id}_{object_kind}",
        name=f"generalization {object_kind}",
        features=features_by_kind[object_kind],
        position=positions_by_layout[layout_id],
    )


def _generalization_result(result: ConditionResult) -> Dict[str, object]:
    payload = result.trace_payload
    return {
        "selected_action": result.selected_action,
        "caution_score": result.caution_score,
        "self_risk_score": result.self_risk_score,
        "world_prediction_error": result.world_prediction_error,
        "trace_hash": result.trace_hash,
        "trace_payload": {
            "layout_id": payload["layout_id"],
            "object_kind": payload["object_kind"],
            "target_object_id": payload["target_object_id"],
            "target_position": payload["target_position"],
            "candidate_object_features": payload["candidate_object_features"],
        },
    }


def evaluate_seeds(seeds: Iterable[int]) -> Dict[str, List[ConditionResult]]:
    target = build_candidate_object()
    results: Dict[str, List[ConditionResult]] = {
        "danger": [],
        "safe": [],
        "memory_deleted": [],
        "frozen_world": [],
        "frozen_self": [],
        "no_prediction_error_learning": [],
        "replay_first": [],
        "replay_second": [],
    }
    for seed in seeds:
        results["danger"].append(run_condition(seed=seed, history="danger", target=target))
        results["safe"].append(run_condition(seed=seed, history="safe", target=target))
        results["memory_deleted"].append(
            run_condition(seed=seed, history="danger", target=target, delete_relevant_memory=True)
        )
        results["frozen_world"].append(
            run_condition(seed=seed, history="danger", target=target, freeze_world_model=True)
        )
        results["frozen_self"].append(
            run_condition(seed=seed, history="danger", target=target, freeze_self_model=True)
        )
        results["no_prediction_error_learning"].append(
            run_condition(seed=seed, history="danger", target=target, disable_prediction_error_learning=True)
        )
        replay_first, replay_second = run_replay_pair(seed)
        results["replay_first"].append(replay_first)
        results["replay_second"].append(replay_second)
    return results


def _audit_result(result: ConditionResult) -> Dict[str, object]:
    return {
        "selected_action": result.selected_action,
        "caution_score": result.caution_score,
        "self_risk_score": result.self_risk_score,
        "world_prediction_error": result.world_prediction_error,
        "trace_hash": result.trace_hash,
        "target_object_id": result.trace_payload["target_object_id"],
        "candidate_object_features": result.trace_payload["candidate_object_features"],
    }


def _object_name_rule_hits() -> List[str]:
    decision_files = ["environment.py", "models.py", "planning.py", "memory.py"]
    hits: List[str] = []
    root = Path(__file__).parent
    for filename in decision_files:
        path = root / filename
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if ("if " in stripped and ("object_id" in stripped or "name" in stripped)) or (
                ("object_id ==" in stripped or "name ==" in stripped)
            ):
                hits.append(f"{filename}:{lineno}:{stripped}")
    return hits


def gate_status(results: Dict[str, List[ConditionResult]]) -> Dict[str, bool]:
    statuses = {
        "different_histories": all(
            danger.caution_score > safe.caution_score + 0.20 and danger.selected_action != safe.selected_action
            for danger, safe in zip(results["danger"], results["safe"])
        ),
        "danger_generalization": all(
            result.selected_action in {"observe", "retreat"}
            and result.trace_payload["target_object_id"] == "blue_glass_bottle_unseen"
            for result in results["danger"]
        ),
        "memory_deletion": all(
            danger.caution_score > deleted.caution_score + 0.20 and deleted.selected_action == "approach"
            for danger, deleted in zip(results["danger"], results["memory_deleted"])
        ),
        "frozen_world_model": all(
            danger.world_prediction_error < frozen.world_prediction_error
            and danger.caution_score > frozen.caution_score + 0.20
            for danger, frozen in zip(results["danger"], results["frozen_world"])
        ),
        "frozen_self_model": all(
            danger.self_risk_score > frozen.self_risk_score + 0.20 and danger.selected_action != frozen.selected_action
            for danger, frozen in zip(results["danger"], results["frozen_self"])
        ),
        "no_prediction_error_learning": all(
            danger.world_prediction_error < no_learning.world_prediction_error
            and danger.caution_score > no_learning.caution_score + 0.20
            for danger, no_learning in zip(results["danger"], results["no_prediction_error_learning"])
        ),
        "replay_determinism": all(
            first.selected_action == second.selected_action and first.trace_hash == second.trace_hash
            for first, second in zip(results["replay_first"], results["replay_second"])
        ),
    }
    return statuses


def _build_memory(env: VirtualCatGridWorld, seed: int, history: str) -> EpisodicMemory:
    memory = EpisodicMemory()
    if history == "danger":
        objects = [
            GridObject(
                "red_cup_seen",
                "red cup",
                (2, 1),
                ObjectFeatures(instability=0.90, height=0.91, fragility=0.80, novelty=0.20),
            ),
            GridObject(
                "tall_wobbly_vase_seen",
                "tall wobbly vase",
                (2, 2),
                ObjectFeatures(instability=0.86, height=0.94, fragility=0.78, novelty=0.30),
            ),
        ]
    elif history == "safe":
        objects = [
            GridObject(
                "stable_ball_seen",
                "stable ball",
                (2, 1),
                ObjectFeatures(instability=0.10, height=0.20, fragility=0.10, novelty=0.45),
            ),
            GridObject(
                "soft_toy_seen",
                "soft toy",
                (2, 2),
                ObjectFeatures(instability=0.08, height=0.24, fragility=0.08, novelty=0.60),
            ),
        ]
    else:
        raise ValueError(f"unknown history: {history}")

    stable_controls = [
        GridObject(
            "food_bowl_control",
            "food bowl",
            (1, 2),
            ObjectFeatures(instability=0.14, height=0.20, fragility=0.12, novelty=0.25),
        ),
        GridObject(
            "flat_mat_control",
            "flat mat",
            (1, 3),
            ObjectFeatures(instability=0.05, height=0.08, fragility=0.05, novelty=0.15),
        ),
    ]
    episode = 0
    for obj in [*objects, *stable_controls]:
        for action in [Action.APPROACH, Action.OBSERVE]:
            episode += 1
            result = env.simulate_action(obj, action)
            naive_prediction = {"object_fell": 0.10, "noise": 0.10, "danger_contact": 0.10}
            actual_vec = [1.0 if result.actual[key] else 0.0 for key in ("object_fell", "noise", "danger_contact")]
            prediction_error = sum(abs(0.10 - actual) for actual in actual_vec) / len(actual_vec)
            memory.add_transition(
                episode_id=f"ep_{seed}_{episode:03d}",
                seed=seed,
                object_id=obj.object_id,
                action=action.value,
                object_features=obj.features.to_dict(),
                prediction=naive_prediction,
                actual=result.actual,
                self_delta=result.self_delta,
                prediction_error=prediction_error,
                model_update_ref=f"train_step_{seed}_{episode:03d}",
            )
    return memory


def _scenario_name(**flags: object) -> str:
    history = str(flags["history"])
    suffixes = [
        name
        for name in [
            "delete_relevant_memory",
            "freeze_world_model",
            "freeze_self_model",
            "disable_prediction_error_learning",
        ]
        if flags.get(name)
    ]
    return history if not suffixes else f"{history}__{'__'.join(suffixes)}"


def _hash_payload(payload: Dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def result_to_dict(result: ConditionResult) -> Dict[str, object]:
    return asdict(result)
