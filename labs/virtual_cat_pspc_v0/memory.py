from __future__ import annotations

from dataclasses import dataclass
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

    def to_trace_refs(self) -> List[str]:
        return [f"{transition.episode_id}:{transition.object_id}:{transition.action}" for transition in self.transitions]
