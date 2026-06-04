from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple


class Action(str, Enum):
    APPROACH = "approach"
    OBSERVE = "observe"
    RETREAT = "retreat"


@dataclass(frozen=True)
class ObjectFeatures:
    instability: float
    height: float
    fragility: float
    novelty: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "instability": float(self.instability),
            "height": float(self.height),
            "fragility": float(self.fragility),
            "novelty": float(self.novelty),
        }

    def to_vector(self) -> List[float]:
        return [float(self.instability), float(self.height), float(self.fragility), float(self.novelty)]


@dataclass(frozen=True)
class GridObject:
    object_id: str
    name: str
    position: Tuple[int, int]
    features: ObjectFeatures


@dataclass(frozen=True)
class CatState:
    position: Tuple[int, int] = (1, 1)
    energy: float = 0.75
    stress: float = 0.20
    affinity: float = 0.50
    mobility: float = 1.00


@dataclass(frozen=True)
class StepResult:
    object_id: str
    action: Action
    actual: Dict[str, bool]
    self_delta: Dict[str, float]
    event_probability: Dict[str, float]


class VirtualCatGridWorld:
    """Small deterministic gridworld surface for lab evidence.

    Object names are carried only for trace readability. Feedback is driven by
    object features and action type, which lets the ablation tests distinguish
    feature generalization from object-name scripting.
    """

    def __init__(self, seed: int = 0, width: int = 5, height: int = 4):
        self.seed = int(seed)
        self.width = int(width)
        self.height = int(height)
        self.cat_state = CatState()

    def reset(self) -> CatState:
        self.cat_state = CatState()
        return self.cat_state

    def risk_probability(self, obj: GridObject, action: Action) -> float:
        f = obj.features
        feature_risk = 0.42 * f.instability + 0.28 * f.height + 0.20 * f.fragility + 0.08 * f.novelty
        if action == Action.APPROACH:
            action_factor = 0.24
        elif action == Action.OBSERVE:
            action_factor = -0.20
        else:
            action_factor = -0.38
        return max(0.01, min(0.99, feature_risk + action_factor - 0.25))

    def simulate_action(self, obj: GridObject, action: Action) -> StepResult:
        danger_prob = self.risk_probability(obj, action)
        danger_contact = danger_prob >= 0.55
        noise = danger_prob >= 0.50 and action == Action.APPROACH
        object_fall = danger_prob >= 0.58 and obj.features.height >= 0.55

        if action == Action.APPROACH:
            energy_delta = -0.12
            affinity_delta = 0.05 if not noise else -0.10
        elif action == Action.OBSERVE:
            energy_delta = -0.04
            affinity_delta = 0.01
        else:
            energy_delta = 0.03
            affinity_delta = -0.01

        stress_delta = 0.05 + (0.42 if noise else 0.0) + (0.22 if danger_contact else 0.0)
        self_delta = {
            "energy_delta": round(energy_delta, 4),
            "stress_delta": round(stress_delta, 4),
            "affinity_delta": round(affinity_delta, 4),
            "action_failure_prob": round(max(0.02, danger_prob * 0.65), 4),
            "damage_risk": round(danger_prob, 4),
        }
        actual = {
            "object_fell": bool(object_fall),
            "noise": bool(noise),
            "danger_contact": bool(danger_contact),
        }
        event_probability = {
            "object_fell": round(max(0.01, min(0.99, danger_prob + (0.08 if obj.features.height > 0.7 else -0.05))), 4),
            "noise": round(max(0.01, min(0.99, danger_prob + (0.05 if action == Action.APPROACH else -0.25))), 4),
            "danger_contact": round(danger_prob, 4),
        }
        return StepResult(
            object_id=obj.object_id,
            action=action,
            actual=actual,
            self_delta=self_delta,
            event_probability=event_probability,
        )
