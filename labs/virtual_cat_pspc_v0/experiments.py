from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
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


def build_candidate_object() -> GridObject:
    return GridObject(
        object_id="blue_glass_bottle_unseen",
        name="blue glass bottle",
        position=(3, 1),
        features=ObjectFeatures(instability=0.88, height=0.92, fragility=0.84, novelty=0.70),
    )


def run_condition(
    *,
    seed: int,
    history: str,
    target: GridObject,
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
        "target_object_id": target.object_id,
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
