from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class Transition:
    episode_id: str
    seed: int
    object_id: str
    action: str
    object_features: Dict[str, float]
    prediction: Dict[str, float]
    actual: Dict[str, bool]
    self_delta: Dict[str, float]
    prediction_error: float
    model_update_ref: str
    memory_write: bool = True


class EpisodicMemory:
    def __init__(self, transitions: Iterable[Transition] | None = None):
        self.transitions: List[Transition] = list(transitions or [])

    def add_transition(
        self,
        *,
        episode_id: str,
        seed: int,
        object_id: str,
        action: str,
        object_features: Dict[str, float],
        prediction: Dict[str, float],
        actual: Dict[str, bool],
        self_delta: Dict[str, float],
        prediction_error: float,
        model_update_ref: str,
    ) -> None:
        self.transitions.append(
            Transition(
                episode_id=episode_id,
                seed=int(seed),
                object_id=object_id,
                action=action,
                object_features=dict(object_features),
                prediction=dict(prediction),
                actual=dict(actual),
                self_delta=dict(self_delta),
                prediction_error=float(prediction_error),
                model_update_ref=model_update_ref,
            )
        )

    def delete_relevant(self, semantic_tag: str) -> int:
        if semantic_tag != "unstable_tall_object":
            return 0
        before = len(self.transitions)
        self.transitions = [
            transition
            for transition in self.transitions
            if not (
                transition.object_features.get("instability", 0.0) >= 0.65
                and transition.object_features.get("height", 0.0) >= 0.65
            )
        ]
        return before - len(self.transitions)

    def delete_irrelevant(self, semantic_tag: str) -> int:
        if semantic_tag != "unstable_tall_object":
            return 0
        before = len(self.transitions)
        self.transitions = [
            transition
            for transition in self.transitions
            if not _is_stable_control_transition(transition)
        ]
        return before - len(self.transitions)

    def corrupt_relevant(self, semantic_tag: str) -> int:
        if semantic_tag != "unstable_tall_object":
            return 0
        corrupted: List[Transition] = []
        count = 0
        for transition in self.transitions:
            if _is_relevant_unstable_transition(transition):
                count += 1
                corrupted.append(
                    replace(
                        transition,
                        actual={
                            "object_fell": False,
                            "noise": False,
                            "danger_contact": False,
                        },
                        self_delta={
                            "energy_delta": transition.self_delta.get("energy_delta", -0.04),
                            "stress_delta": 0.03,
                            "affinity_delta": 0.04,
                            "action_failure_prob": 0.03,
                            "damage_risk": 0.04,
                        },
                        prediction_error=0.0,
                        model_update_ref=f"{transition.model_update_ref}:corrupted_safe_bias",
                    )
                )
            else:
                corrupted.append(transition)
        self.transitions = corrupted
        return count

    def build_semantic_rule_candidate(self, semantic_tag: str) -> Dict[str, object]:
        if semantic_tag != "unstable_tall_object":
            return {
                "semantic_tag": semantic_tag,
                "admission_status": "unsupported_tag",
                "admitted": False,
                "evidence_count": 0,
                "trace_refs": [],
                "action_summaries": {},
                "feature_centroid": {},
            }
        relevant = [transition for transition in self.transitions if _is_relevant_unstable_transition(transition)]
        if not relevant:
            return {
                "semantic_tag": semantic_tag,
                "admission_status": "no_relevant_memory",
                "admitted": False,
                "evidence_count": 0,
                "trace_refs": [],
                "action_summaries": {},
                "feature_centroid": {},
            }
        action_summaries = {
            action: _summarize_transitions([transition for transition in relevant if transition.action == action])
            for action in sorted({transition.action for transition in relevant})
        }
        candidate = {
            "semantic_tag": semantic_tag,
            "admission_status": "admitted" if len(relevant) >= 2 else "insufficient_evidence",
            "admitted": len(relevant) >= 2,
            "evidence_count": len(relevant),
            "trace_refs": [
                f"{transition.episode_id}:{transition.object_id}:{transition.action}"
                for transition in relevant
            ],
            "action_summaries": action_summaries,
            "feature_centroid": _mean_feature_dict(relevant),
        }
        return candidate

    def to_trace_refs(self) -> List[str]:
        return [f"{transition.episode_id}:{transition.object_id}:{transition.action}" for transition in self.transitions]


def _is_relevant_unstable_transition(transition: Transition) -> bool:
    return (
        transition.object_features.get("instability", 0.0) >= 0.65
        and transition.object_features.get("height", 0.0) >= 0.65
    )


def _is_stable_control_transition(transition: Transition) -> bool:
    return (
        transition.object_features.get("instability", 1.0) <= 0.20
        and transition.object_features.get("height", 1.0) <= 0.30
    )


def _mean_feature_dict(transitions: List[Transition]) -> Dict[str, float]:
    keys = ["instability", "height", "fragility", "novelty"]
    return {
        key: round(sum(float(transition.object_features[key]) for transition in transitions) / len(transitions), 4)
        for key in keys
    }


def _summarize_transitions(transitions: List[Transition]) -> Dict[str, object]:
    if not transitions:
        return {
            "count": 0,
            "actual_probability": {},
            "self_delta_mean": {},
        }
    actual_keys = ["object_fell", "noise", "danger_contact"]
    self_keys = ["energy_delta", "stress_delta", "affinity_delta", "action_failure_prob", "damage_risk"]
    return {
        "count": len(transitions),
        "actual_probability": {
            key: round(
                sum(1.0 if transition.actual.get(key) else 0.0 for transition in transitions) / len(transitions),
                4,
            )
            for key in actual_keys
        },
        "self_delta_mean": {
            key: round(sum(float(transition.self_delta.get(key, 0.0)) for transition in transitions) / len(transitions), 4)
            for key in self_keys
        },
    }
