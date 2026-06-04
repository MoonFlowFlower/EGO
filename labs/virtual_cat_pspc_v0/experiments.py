from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .environment import Action, GridObject, ObjectFeatures, VirtualCatGridWorld
from .memory import EpisodicMemory, Transition
from .models import HomeostaticValue, SelfModel, WorldModel
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


def run_world_model_causal_strength(seed: int) -> Dict[str, object]:
    env = VirtualCatGridWorld(seed=seed)
    memory = _build_memory(env=env, seed=seed, history="danger")
    normal_world = WorldModel(seed=seed)
    normal_world.fit(memory.transitions)
    self_model = SelfModel(seed=seed)
    self_model.fit(memory.transitions, normal_world)

    world_models = {
        "normal": normal_world,
        "frozen": WorldModel(seed=seed),
        "shuffled": _fit_corrupted_world_model(seed=seed, transitions=memory.transitions, mode="shuffled"),
        "random": _fit_corrupted_world_model(seed=seed, transitions=memory.transitions, mode="random"),
    }
    targets = {
        "danger": build_candidate_object(),
        "safe": build_candidate_object(
            object_id="world_model_safe_target",
            name="world model safe target",
            features=ObjectFeatures(instability=0.06, height=0.18, fragility=0.08, novelty=0.35),
        ),
    }
    variant_records: Dict[str, Dict[str, object]] = {}
    planner_support_scores: Dict[str, float] = {}
    for variant, world_model in world_models.items():
        danger = _evaluate_world_variant(
            seed=seed,
            variant=variant,
            target_kind="danger",
            target=targets["danger"],
            env=env,
            world_model=world_model,
            self_model=self_model,
        )
        safe = _evaluate_world_variant(
            seed=seed,
            variant=variant,
            target_kind="safe",
            target=targets["safe"],
            env=env,
            world_model=world_model,
            self_model=self_model,
        )
        variant_records[variant] = {"danger": danger, "safe": safe}
        planner_support_scores[variant] = _world_model_planner_support_score(danger=danger, safe=safe)

    status = (
        "pass"
        if planner_support_scores["normal"] > planner_support_scores["frozen"]
        and planner_support_scores["frozen"] > planner_support_scores["shuffled"]
        and planner_support_scores["frozen"] > planner_support_scores["random"]
        else "hold"
    )
    return {
        "seed": seed,
        "status": status,
        "variants": ["normal", "frozen", "shuffled", "random"],
        "ordering": "normal > frozen > shuffled/random",
        "planner_support_scores": planner_support_scores,
        "variant_records": variant_records,
        "what_it_proves": (
            "Replacing the learned world model with frozen, shuffled, or random baselines degrades "
            "planner support under the same self model and target set."
        ),
        "what_it_does_not_prove": (
            "This does not prove world-model causal strength outside this lab target set, real-world "
            "transfer, EgoOperator runtime efficacy, stable user benefit, live autonomy, consciousness, "
            "or subjective experience."
        ),
    }


def run_self_model_causal_strength(seed: int) -> Dict[str, object]:
    env = VirtualCatGridWorld(seed=seed)
    memory = _build_memory(env=env, seed=seed, history="danger")
    world_model = WorldModel(seed=seed)
    world_model.fit(memory.transitions)
    normal_self = SelfModel(seed=seed)
    normal_self.fit(memory.transitions, world_model)

    self_models = {
        "normal": normal_self,
        "frozen": SelfModel(seed=seed + 887),
        "stress_removed": _SelfModelHeadAblation(normal_self, "stress_removed"),
        "ability_removed": _SelfModelHeadAblation(normal_self, "ability_removed"),
        "affinity_removed": _SelfModelHeadAblation(normal_self, "affinity_removed"),
    }
    targets = {
        "risk_control": build_candidate_object(),
        "ability_planning": build_candidate_object(
            object_id="self_model_ability_target",
            name="self model ability target",
            features=ObjectFeatures(instability=0.25, height=0.40, fragility=0.50, novelty=0.40),
        ),
        "relationship_preference": build_candidate_object(
            object_id="self_model_relationship_target",
            name="self model relationship target",
            features=ObjectFeatures(instability=0.25, height=0.50, fragility=0.60, novelty=0.62),
        ),
    }

    variant_records: Dict[str, Dict[str, object]] = {}
    risk_control_scores: Dict[str, float] = {}
    ability_planning_scores: Dict[str, float] = {}
    relationship_preference_scores: Dict[str, float] = {}

    for variant, self_model in self_models.items():
        risk_record = _evaluate_self_variant(
            seed=seed,
            variant=variant,
            task="risk_control",
            target=targets["risk_control"],
            world_model=world_model,
            self_model=self_model,
        )
        ability_record = _evaluate_self_variant(
            seed=seed,
            variant=variant,
            task="ability_planning",
            target=targets["ability_planning"],
            world_model=world_model,
            self_model=self_model,
        )
        relationship_record = _evaluate_self_variant(
            seed=seed,
            variant=variant,
            task="relationship_preference",
            target=targets["relationship_preference"],
            world_model=world_model,
            self_model=self_model,
        )
        variant_records[variant] = {
            "risk_control": risk_record,
            "ability_planning": ability_record,
            "relationship_preference": relationship_record,
        }
        risk_control_scores[variant] = _self_risk_control_score(risk_record)
        ability_planning_scores[variant] = _self_ability_planning_score(ability_record)
        relationship_preference_scores[variant] = _self_relationship_preference_score(relationship_record)

    status = (
        "pass"
        if risk_control_scores["normal"] > risk_control_scores["frozen"]
        and risk_control_scores["normal"] - risk_control_scores["stress_removed"] > 0.20
        and ability_planning_scores["normal"] - ability_planning_scores["ability_removed"] > 0.20
        and relationship_preference_scores["normal"] - relationship_preference_scores["affinity_removed"] > 0.20
        else "hold"
    )
    return {
        "seed": seed,
        "status": status,
        "variants": [
            "normal",
            "frozen",
            "stress_removed",
            "ability_removed",
            "affinity_removed",
        ],
        "ordering": "normal > frozen/head-removed",
        "risk_control_scores": risk_control_scores,
        "ability_planning_scores": ability_planning_scores,
        "relationship_preference_scores": relationship_preference_scores,
        "variant_records": variant_records,
        "what_it_proves": (
            "Removing learned self-model stress/risk, ability, and affinity heads degrades the "
            "corresponding lab planner support under the same learned world model and target set."
        ),
        "what_it_does_not_prove": (
            "This does not prove self-model causal strength outside this lab target set, real-world "
            "transfer, EgoOperator runtime efficacy, stable user benefit, live autonomy, consciousness, "
            "or subjective experience."
        ),
    }


def run_memory_consolidation_admission(seed: int) -> Dict[str, object]:
    target = build_candidate_object()
    variants = {
        "normal": {},
        "relevant_deleted": {"delete_relevant": True},
        "irrelevant_deleted": {"delete_irrelevant": True},
        "corrupted_relevant": {"corrupt_relevant": True},
    }
    variant_records: Dict[str, Dict[str, object]] = {}
    for variant, flags in variants.items():
        variant_records[variant] = _evaluate_memory_consolidation_variant(
            seed=seed,
            variant=variant,
            target=target,
            delete_relevant=bool(flags.get("delete_relevant")),
            delete_irrelevant=bool(flags.get("delete_irrelevant")),
            corrupt_relevant=bool(flags.get("corrupt_relevant")),
        )

    normal = variant_records["normal"]
    relevant_deleted = variant_records["relevant_deleted"]
    irrelevant_deleted = variant_records["irrelevant_deleted"]
    corrupted = variant_records["corrupted_relevant"]
    relevant_deletion_regression = round(
        float(normal["caution_score"]) - float(relevant_deleted["caution_score"]),
        4,
    )
    irrelevant_deletion_delta = round(
        abs(float(normal["caution_score"]) - float(irrelevant_deleted["caution_score"])),
        4,
    )
    normal_approach_danger = float(normal["approach_world_prediction"]["danger_contact"])
    corrupted_approach_danger = float(corrupted["approach_world_prediction"]["danger_contact"])
    corrupted_memory_bias = {
        "direction": "unsafe_risk_underestimate",
        "normal_approach_danger": round(normal_approach_danger, 4),
        "corrupted_approach_danger": round(corrupted_approach_danger, 4),
        "selected_action_shift": f"{normal['selected_action']} -> {corrupted['selected_action']}",
    }
    status = (
        "pass"
        if normal["semantic_rule_candidate"]["admission_status"] == "admitted"
        and relevant_deleted["semantic_rule_candidate"]["admission_status"] == "no_relevant_memory"
        and relevant_deletion_regression > 0.20
        and irrelevant_deleted["semantic_rule_candidate"]["admission_status"] == "admitted"
        and irrelevant_deletion_delta <= 0.05
        and corrupted["semantic_rule_candidate"]["admission_status"] == "admitted"
        and str(corrupted["selected_action"]) == Action.APPROACH.value
        and normal_approach_danger > corrupted_approach_danger + 0.20
        else "hold"
    )
    return {
        "seed": seed,
        "status": status,
        "variants": list(variants.keys()),
        "variant_records": variant_records,
        "relevant_deletion_regression": relevant_deletion_regression,
        "irrelevant_deletion_delta": irrelevant_deletion_delta,
        "corrupted_memory_bias": corrupted_memory_bias,
        "what_it_proves": (
            "Episodic traces can produce an admitted semantic rule candidate that is consumed as "
            "semantic replay by the lab models: deleting relevant memory regresses behavior, deleting "
            "irrelevant memory does not, and corrupted relevant memory creates an explainable unsafe bias."
        ),
        "what_it_does_not_prove": (
            "This does not prove durable memory consolidation outside this lab audit, real-world "
            "transfer, EgoOperator runtime efficacy, stable user benefit, live autonomy, consciousness, "
            "or subjective experience."
        ),
    }


def run_homeostatic_value_anti_hacking(seed: int) -> Dict[str, object]:
    scenario_specs = {
        "high_curiosity_high_risk": {
            "target": build_candidate_object(
                object_id="value_curiosity_high_risk",
                name="value curiosity high risk",
                features=ObjectFeatures(instability=0.88, height=0.92, fragility=0.84, novelty=1.0),
            ),
            "context": {"curiosity_pressure": 0.85},
            "dominant_tradeoff": {"positive_axis": "curiosity", "blocking_axis": "safety"},
            "anti_hacking_check": "not_always_explore",
        },
        "food_reward_danger_conflict": {
            "target": build_candidate_object(
                object_id="value_food_danger",
                name="value food danger",
                features=ObjectFeatures(instability=0.90, height=0.90, fragility=0.80, novelty=0.30),
            ),
            "context": {"food_reward": 0.35, "energy_need": 0.45},
            "dominant_tradeoff": {"positive_axis": "energy", "blocking_axis": "safety"},
            "anti_hacking_check": "not_always_eat",
        },
        "user_affinity_self_risk_conflict": {
            "target": build_candidate_object(
                object_id="value_affinity_self_risk",
                name="value affinity self risk",
                features=ObjectFeatures(instability=0.84, height=0.86, fragility=0.78, novelty=0.40),
            ),
            "context": {"user_affinity_reward": 0.46},
            "dominant_tradeoff": {"positive_axis": "affinity", "blocking_axis": "self_risk"},
            "anti_hacking_check": "not_always_please",
        },
        "repetition_penalty": {
            "target": build_candidate_object(
                object_id="value_repetition_penalty",
                name="value repetition penalty",
                features=ObjectFeatures(instability=0.72, height=0.80, fragility=0.66, novelty=0.95),
            ),
            "context": {"curiosity_pressure": 0.68, "repeated_action": Action.OBSERVE.value, "repetition_penalty": 0.95},
            "baseline_context": {"curiosity_pressure": 0.68},
            "dominant_tradeoff": {"positive_axis": "curiosity", "blocking_axis": "repetition"},
            "anti_hacking_check": "not_always_repeat_or_explore",
        },
        "safe_energy_recovery": {
            "target": build_candidate_object(
                object_id="value_safe_energy_recovery",
                name="value safe energy recovery",
                features=ObjectFeatures(instability=0.04, height=0.10, fragility=0.05, novelty=0.22),
            ),
            "context": {"food_reward": 0.38, "energy_need": 0.80},
            "dominant_tradeoff": {"positive_axis": "energy", "blocking_axis": "none_low_risk"},
            "anti_hacking_check": "not_always_avoid",
        },
    }
    records: Dict[str, Dict[str, object]] = {}
    for scenario, spec in scenario_specs.items():
        record = _evaluate_homeostatic_value_scenario(
            seed=seed,
            scenario=scenario,
            target=spec["target"],
            context=spec["context"],
            dominant_tradeoff=spec["dominant_tradeoff"],
            anti_hacking_check=str(spec["anti_hacking_check"]),
        )
        baseline_context = spec.get("baseline_context")
        if isinstance(baseline_context, dict):
            baseline = _evaluate_homeostatic_value_scenario(
                seed=seed,
                scenario=f"{scenario}_baseline",
                target=spec["target"],
                context=baseline_context,
                dominant_tradeoff=spec["dominant_tradeoff"],
                anti_hacking_check=str(spec["anti_hacking_check"]),
            )
            record["baseline_without_penalty_action"] = baseline["selected_action"]
            record["baseline_without_penalty_trace_hash"] = baseline["trace_hash"]
        records[scenario] = record

    balance_summary = {
        "not_always_explore": records["high_curiosity_high_risk"]["selected_action"] == Action.OBSERVE.value,
        "not_always_eat": records["food_reward_danger_conflict"]["selected_action"] in {Action.OBSERVE.value, Action.RETREAT.value},
        "not_always_please": records["user_affinity_self_risk_conflict"]["selected_action"]
        in {Action.OBSERVE.value, Action.RETREAT.value},
        "not_always_avoid": records["safe_energy_recovery"]["selected_action"] == Action.APPROACH.value,
        "not_single_reward": len({str(record["selected_action"]) for record in records.values()}) > 1,
    }
    repetition = records["repetition_penalty"]
    balance_summary["not_always_repeat_or_explore"] = (
        repetition.get("baseline_without_penalty_action") == Action.OBSERVE.value
        and repetition["selected_action"] != repetition.get("baseline_without_penalty_action")
    )
    status = "pass" if all(balance_summary.values()) else "hold"
    return {
        "seed": seed,
        "status": status,
        "scenarios": list(scenario_specs.keys()),
        "scenario_records": records,
        "balance_summary": balance_summary,
        "what_it_proves": (
            "The lab homeostatic value can balance safety / curiosity / energy / affinity / repetition "
            "pressures in the configured conflict scenarios without collapsing into a single reward policy."
        ),
        "what_it_does_not_prove": (
            "This does not prove homeostatic value robustness outside this lab audit, real-world transfer, "
            "EgoOperator runtime efficacy, stable user benefit, live autonomy, consciousness, or subjective experience."
        ),
    }


def _evaluate_homeostatic_value_scenario(
    *,
    seed: int,
    scenario: str,
    target: GridObject,
    context: Dict[str, object],
    dominant_tradeoff: Dict[str, str],
    anti_hacking_check: str,
) -> Dict[str, object]:
    env = VirtualCatGridWorld(seed=seed)
    memory = _build_memory(env=env, seed=seed, history="danger")
    world_model = WorldModel(seed=seed)
    world_model.fit(memory.transitions)
    self_model = SelfModel(seed=seed)
    self_model.fit(memory.transitions, world_model)
    value = HomeostaticValue()
    candidate_actions: List[Dict[str, object]] = []
    for action in Action:
        world_prediction = world_model.predict(target, action)
        self_prediction = self_model.predict(world_prediction, action)
        score = value.score(
            obj=target,
            action=action,
            world_prediction=world_prediction,
            self_prediction=self_prediction,
            uncertainty=_prediction_uncertainty(world_prediction),
            context=context,
        )
        candidate_actions.append(
            {
                "action": action.value,
                "world_prediction": world_prediction,
                "self_prediction": self_prediction,
                "homeostatic_score": score,
                "rollout_mean_score": score["total"],
            }
        )
    candidate_actions.sort(key=lambda item: (float(item["rollout_mean_score"]), str(item["action"])), reverse=True)
    selected = candidate_actions[0]
    by_action = {str(item["action"]): item for item in candidate_actions}
    trace_payload = {
        "seed": seed,
        "scenario": scenario,
        "target_object_id": target.object_id,
        "candidate_object_features": target.features.to_dict(),
        "context": context,
        "dominant_tradeoff": dominant_tradeoff,
        "selected_action": selected["action"],
        "candidate_actions": candidate_actions,
    }
    return {
        "scenario": scenario,
        "selected_action": selected["action"],
        "world_prediction": selected["world_prediction"],
        "self_prediction": selected["self_prediction"],
        "homeostatic_score": selected["homeostatic_score"],
        "candidate_actions": candidate_actions,
        "candidate_actions_by_action": by_action,
        "approach_components": by_action[Action.APPROACH.value]["homeostatic_score"],
        "dominant_tradeoff": dominant_tradeoff,
        "anti_hacking_check": anti_hacking_check,
        "context": context,
        "trace_hash": _hash_payload(trace_payload),
    }


def _prediction_uncertainty(prediction: Dict[str, float]) -> float:
    return round(sum(1.0 - abs(float(value) - 0.5) * 2.0 for value in prediction.values()) / len(prediction), 6)


def _evaluate_memory_consolidation_variant(
    *,
    seed: int,
    variant: str,
    target: GridObject,
    delete_relevant: bool = False,
    delete_irrelevant: bool = False,
    corrupt_relevant: bool = False,
) -> Dict[str, object]:
    env = VirtualCatGridWorld(seed=seed)
    memory = _build_memory(env=env, seed=seed, history="danger")
    deleted_memory_count = 0
    corrupted_memory_count = 0
    if delete_relevant:
        deleted_memory_count = memory.delete_relevant("unstable_tall_object")
    if delete_irrelevant:
        deleted_memory_count = memory.delete_irrelevant("unstable_tall_object")
    if corrupt_relevant:
        corrupted_memory_count = memory.corrupt_relevant("unstable_tall_object")

    semantic_rule_candidate = memory.build_semantic_rule_candidate("unstable_tall_object")
    admission_gate = {
        "gate": "semantic_rule_candidate_admission",
        "status": semantic_rule_candidate["admission_status"],
        "min_evidence_count": 2,
        "evidence_count": semantic_rule_candidate["evidence_count"],
        "admitted": semantic_rule_candidate["admitted"],
    }
    replay_transitions = _semantic_replay_transitions(
        seed=seed,
        variant=variant,
        candidate=semantic_rule_candidate,
    )
    world_model = WorldModel(seed=seed)
    self_model = SelfModel(seed=seed)
    if replay_transitions:
        world_model.fit(replay_transitions)
        self_model.fit(replay_transitions, world_model)

    planner = MPCPlanner(world_model=world_model, self_model=self_model, seed=seed)
    plan = planner.plan(target)
    approach_world_prediction = world_model.predict(target, Action.APPROACH)
    approach_self_prediction = self_model.predict(approach_world_prediction, Action.APPROACH)
    trace_payload = {
        "seed": seed,
        "variant": variant,
        "selected_action": plan.selected_action,
        "caution_score": plan.caution_score,
        "semantic_rule_candidate": semantic_rule_candidate,
        "admission_gate": admission_gate,
        "deleted_memory_count": deleted_memory_count,
        "corrupted_memory_count": corrupted_memory_count,
        "semantic_replay_refs": [transition.episode_id for transition in replay_transitions],
        "world_prediction": plan.world_prediction,
        "self_prediction": plan.self_prediction,
        "approach_world_prediction": approach_world_prediction,
        "approach_self_prediction": approach_self_prediction,
        "homeostatic_score": plan.homeostatic_score,
        "planner_trace_hash": plan.trace_hash,
    }
    return {
        "selected_action": plan.selected_action,
        "caution_score": plan.caution_score,
        "self_risk_score": round(float(plan.self_risk_score), 4),
        "world_prediction": plan.world_prediction,
        "self_prediction": plan.self_prediction,
        "approach_world_prediction": approach_world_prediction,
        "approach_self_prediction": approach_self_prediction,
        "homeostatic_score": plan.homeostatic_score,
        "semantic_rule_candidate": semantic_rule_candidate,
        "admission_gate": admission_gate,
        "deleted_memory_count": deleted_memory_count,
        "corrupted_memory_count": corrupted_memory_count,
        "semantic_replay_refs": [transition.episode_id for transition in replay_transitions],
        "trace_hash": _hash_payload(trace_payload),
    }


def _semantic_replay_transitions(*, seed: int, variant: str, candidate: Dict[str, object]) -> List[Transition]:
    if not candidate.get("admitted"):
        return []
    action_summaries = candidate.get("action_summaries") if isinstance(candidate.get("action_summaries"), dict) else {}
    feature_centroid = candidate.get("feature_centroid") if isinstance(candidate.get("feature_centroid"), dict) else {}
    replay_transitions: List[Transition] = []
    for index, action in enumerate(sorted(action_summaries), start=1):
        summary = action_summaries[action] if isinstance(action_summaries.get(action), dict) else {}
        actual_probability = (
            summary.get("actual_probability") if isinstance(summary.get("actual_probability"), dict) else {}
        )
        self_delta_mean = summary.get("self_delta_mean") if isinstance(summary.get("self_delta_mean"), dict) else {}
        replay_transitions.append(
            Transition(
                episode_id=f"semantic_{variant}_{seed}_{index:03d}",
                seed=seed,
                object_id="semantic_unstable_tall_object",
                action=str(action),
                object_features={key: float(feature_centroid[key]) for key in feature_centroid},
                prediction={
                    "object_fell": float(actual_probability.get("object_fell", 0.0)),
                    "noise": float(actual_probability.get("noise", 0.0)),
                    "danger_contact": float(actual_probability.get("danger_contact", 0.0)),
                },
                actual={
                    "object_fell": float(actual_probability.get("object_fell", 0.0)) >= 0.5,
                    "noise": float(actual_probability.get("noise", 0.0)) >= 0.5,
                    "danger_contact": float(actual_probability.get("danger_contact", 0.0)) >= 0.5,
                },
                self_delta={key: float(value) for key, value in self_delta_mean.items()},
                prediction_error=0.0,
                model_update_ref=f"semantic_rule_candidate:{variant}:{action}",
            )
        )
    return replay_transitions


class _SelfModelHeadAblation:
    def __init__(self, base_model: SelfModel, mode: str):
        self.base_model = base_model
        self.mode = mode

    def predict(self, world_prediction: Dict[str, float], action: Action) -> Dict[str, float]:
        prediction = dict(self.base_model.predict(world_prediction, action))
        if self.mode == "stress_removed":
            prediction["stress_delta"] = 0.0
        elif self.mode == "ability_removed":
            prediction["action_failure_prob"] = 0.0
        elif self.mode == "affinity_removed":
            prediction["affinity_delta"] = 0.0
        else:
            raise ValueError(f"unknown self-model head ablation mode: {self.mode}")
        return prediction


def _evaluate_self_variant(
    *,
    seed: int,
    variant: str,
    task: str,
    target: GridObject,
    world_model: WorldModel,
    self_model,
) -> Dict[str, object]:
    planner = MPCPlanner(world_model=world_model, self_model=self_model, seed=seed)
    plan = planner.plan(target)
    approach_world_prediction = world_model.predict(target, Action.APPROACH)
    approach_self_prediction = self_model.predict(approach_world_prediction, Action.APPROACH)
    trace_payload = {
        "seed": seed,
        "variant": variant,
        "task": task,
        "target_object_id": target.object_id,
        "candidate_object_features": target.features.to_dict(),
        "selected_action": plan.selected_action,
        "caution_score": plan.caution_score,
        "world_prediction": plan.world_prediction,
        "self_prediction": plan.self_prediction,
        "approach_world_prediction": approach_world_prediction,
        "approach_self_prediction": approach_self_prediction,
        "homeostatic_score": plan.homeostatic_score,
        "planner_trace_hash": plan.trace_hash,
    }
    return {
        "selected_action": plan.selected_action,
        "caution_score": plan.caution_score,
        "self_risk_score": round(float(plan.self_risk_score), 4),
        "world_prediction": plan.world_prediction,
        "self_prediction": plan.self_prediction,
        "approach_world_prediction": approach_world_prediction,
        "approach_self_prediction": approach_self_prediction,
        "homeostatic_score": plan.homeostatic_score,
        "trace_hash": _hash_payload(trace_payload),
    }


def _self_risk_control_score(record: Dict[str, object]) -> float:
    approach_self = record["approach_self_prediction"] if isinstance(record.get("approach_self_prediction"), dict) else {}
    protective_action = 0.35 if str(record.get("selected_action")) in {"observe", "retreat"} else 0.0
    return round(
        float(record.get("caution_score", 0.0))
        + protective_action
        + float(approach_self.get("stress_delta", 0.0))
        + float(approach_self.get("damage_risk", 0.0)),
        4,
    )


def _self_ability_planning_score(record: Dict[str, object]) -> float:
    approach_self = record["approach_self_prediction"] if isinstance(record.get("approach_self_prediction"), dict) else {}
    protective_action = 0.35 if str(record.get("selected_action")) in {"observe", "retreat"} else 0.0
    return round(
        float(record.get("caution_score", 0.0))
        + protective_action
        + (2.0 * float(approach_self.get("action_failure_prob", 0.0))),
        4,
    )


def _self_relationship_preference_score(record: Dict[str, object]) -> float:
    approach_self = record["approach_self_prediction"] if isinstance(record.get("approach_self_prediction"), dict) else {}
    selected_self = record["self_prediction"] if isinstance(record.get("self_prediction"), dict) else {}
    selected_action = str(record.get("selected_action"))
    avoids_affinity_harm = 0.50 if selected_action != Action.APPROACH.value else 0.0
    affinity_warning = 5.0 * max(0.0, -float(approach_self.get("affinity_delta", 0.0)))
    selected_affinity_gain = 3.0 * max(0.0, float(selected_self.get("affinity_delta", 0.0)))
    return round(avoids_affinity_harm + affinity_warning + selected_affinity_gain, 4)


def _fit_corrupted_world_model(*, seed: int, transitions, mode: str) -> WorldModel:
    model = WorldModel(seed=seed + (311 if mode == "shuffled" else 719))
    if mode == "shuffled":
        actuals = [dict(transition.actual) for transition in reversed(transitions)]
        corrupted = [
            replace(transition, actual=actuals[index])
            for index, transition in enumerate(transitions)
        ]
    elif mode == "random":
        rng = random.Random(seed + 1701)
        corrupted = [
            replace(
                transition,
                actual={
                    "object_fell": bool(rng.getrandbits(1)),
                    "noise": bool(rng.getrandbits(1)),
                    "danger_contact": bool(rng.getrandbits(1)),
                },
            )
            for transition in transitions
        ]
    else:
        raise ValueError(f"unknown corruption mode: {mode}")
    model.fit(corrupted)
    return model


def _evaluate_world_variant(
    *,
    seed: int,
    variant: str,
    target_kind: str,
    target: GridObject,
    env: VirtualCatGridWorld,
    world_model: WorldModel,
    self_model: SelfModel,
) -> Dict[str, object]:
    planner = MPCPlanner(world_model=world_model, self_model=self_model, seed=seed)
    plan = planner.plan(target)
    actual = env.simulate_action(target, Action.APPROACH).actual
    prediction_error = world_model.prediction_error(target, Action.APPROACH, actual)
    world_prediction = world_model.predict(target, Action.APPROACH)
    trace_payload = {
        "seed": seed,
        "variant": variant,
        "target_kind": target_kind,
        "target_object_id": target.object_id,
        "candidate_object_features": target.features.to_dict(),
        "selected_action": plan.selected_action,
        "caution_score": plan.caution_score,
        "prediction_error": prediction_error,
        "world_prediction": world_prediction,
        "planner_trace_hash": plan.trace_hash,
    }
    return {
        "selected_action": plan.selected_action,
        "caution_score": plan.caution_score,
        "self_risk_score": round(float(plan.self_risk_score), 4),
        "prediction_error": prediction_error,
        "world_prediction": world_prediction,
        "trace_hash": _hash_payload(trace_payload),
    }


def _world_model_planner_support_score(*, danger: Dict[str, object], safe: Dict[str, object]) -> float:
    danger_caution = float(danger["caution_score"])
    safe_caution = float(safe["caution_score"])
    danger_prediction_quality = 1.0 - float(danger["prediction_error"])
    safe_prediction_quality = 1.0 - float(safe["prediction_error"])
    prediction_quality = (0.75 * danger_prediction_quality) + (0.25 * safe_prediction_quality)
    discrimination = danger_caution - (1.50 * safe_caution)
    action_alignment = 0.0
    if str(danger["selected_action"]) in {"observe", "retreat"}:
        action_alignment += 0.25
    if str(safe["selected_action"]) == "approach":
        action_alignment += 0.25
    return round(discrimination + prediction_quality + action_alignment, 4)


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
