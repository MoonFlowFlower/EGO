from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from typing import Dict, List

from .environment import Action, GridObject
from .models import HomeostaticValue, SelfModel, WorldModel


@dataclass(frozen=True)
class PlanResult:
    selected_action: str
    caution_score: float
    self_risk_score: float
    world_prediction: Dict[str, float]
    self_prediction: Dict[str, float]
    homeostatic_score: Dict[str, float]
    candidate_actions: List[Dict[str, object]]
    trace_hash: str


class MPCPlanner:
    def __init__(self, world_model: WorldModel, self_model: SelfModel, seed: int, horizon: int = 3, samples: int = 96):
        self.world_model = world_model
        self.self_model = self_model
        self.rng = random.Random(int(seed))
        self.horizon = int(horizon)
        self.samples = int(samples)
        self.value = HomeostaticValue()

    def plan(self, obj: GridObject) -> PlanResult:
        first_action_scores: Dict[Action, List[float]] = {action: [] for action in Action}
        first_action_payloads: Dict[Action, Dict[str, object]] = {}

        base_sequences = [[action] * self.horizon for action in Action]
        sampled_sequences = [
            [self.rng.choice(list(Action)) for _ in range(self.horizon)]
            for _ in range(max(0, self.samples - len(base_sequences)))
        ]
        sequences = base_sequences + sampled_sequences

        for sequence in sequences:
            total = 0.0
            first_payload: Dict[str, object] | None = None
            for action in sequence:
                world_prediction = self.world_model.predict(obj, action)
                self_prediction = self.self_model.predict(world_prediction, action)
                uncertainty = _uncertainty(world_prediction)
                score = self.value.score(
                    obj=obj,
                    action=action,
                    world_prediction=world_prediction,
                    self_prediction=self_prediction,
                    uncertainty=uncertainty,
                )
                total += score["total"]
                if first_payload is None:
                    first_payload = {
                        "action": action.value,
                        "world_prediction": world_prediction,
                        "self_prediction": self_prediction,
                        "homeostatic_score": score,
                    }
            first = sequence[0]
            first_action_scores[first].append(total)
            first_action_payloads.setdefault(first, first_payload or {})

        candidate_actions: List[Dict[str, object]] = []
        for action, scores in first_action_scores.items():
            mean_score = sum(scores) / len(scores) if scores else -999.0
            payload = dict(first_action_payloads.get(action, {"action": action.value}))
            payload["rollout_mean_score"] = round(float(mean_score), 6)
            candidate_actions.append(payload)

        candidate_actions.sort(key=lambda item: (float(item["rollout_mean_score"]), item["action"]), reverse=True)
        selected = candidate_actions[0]
        selected_action = str(selected["action"])
        caution_score = {"approach": 0.0, "observe": 0.72, "retreat": 1.0}[selected_action]
        trace_hash = _stable_hash(
            {
                "object_features": obj.features.to_dict(),
                "candidate_actions": candidate_actions,
                "selected_action": selected_action,
            }
        )
        return PlanResult(
            selected_action=selected_action,
            caution_score=round(caution_score, 4),
            self_risk_score=float(selected["self_prediction"]["damage_risk"]),
            world_prediction=selected["world_prediction"],
            self_prediction=selected["self_prediction"],
            homeostatic_score=selected["homeostatic_score"],
            candidate_actions=candidate_actions,
            trace_hash=trace_hash,
        )


def _uncertainty(prediction: Dict[str, float]) -> float:
    return round(sum(1.0 - abs(float(value) - 0.5) * 2.0 for value in prediction.values()) / len(prediction), 6)


def _stable_hash(payload: Dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]
