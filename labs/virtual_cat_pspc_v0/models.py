from __future__ import annotations

import random
from typing import Dict, Iterable, List, Sequence

import torch
from torch import nn

from .environment import Action, GridObject
from .memory import Transition


ACTION_ORDER = [Action.APPROACH.value, Action.OBSERVE.value, Action.RETREAT.value]


def _action_one_hot(action: str | Action) -> List[float]:
    value = action.value if isinstance(action, Action) else str(action)
    return [1.0 if value == known else 0.0 for known in ACTION_ORDER]


def world_features(obj: GridObject | Dict[str, float], action: str | Action) -> List[float]:
    if isinstance(obj, GridObject):
        features = obj.features.to_dict()
    else:
        features = obj
    return [
        float(features["instability"]),
        float(features["height"]),
        float(features["fragility"]),
        float(features["novelty"]),
        *_action_one_hot(action),
    ]


def self_features(world_prediction: Dict[str, float], action: str | Action) -> List[float]:
    return [
        float(world_prediction["object_fell"]),
        float(world_prediction["noise"]),
        float(world_prediction["danger_contact"]),
    ]


class WorldModel(nn.Module):
    def __init__(self, seed: int):
        super().__init__()
        torch.manual_seed(int(seed))
        random.seed(int(seed))
        self.linear = nn.Linear(7, 3)
        nn.init.zeros_(self.linear.weight)
        nn.init.constant_(self.linear.bias, -2.2)
        self.trained = False
        self.update_refs: List[str] = []

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)

    def predict(self, obj: GridObject, action: Action) -> Dict[str, float]:
        with torch.no_grad():
            x = torch.tensor([world_features(obj, action)], dtype=torch.float32)
            probs = torch.sigmoid(self.forward(x))[0].tolist()
        return {
            "object_fell": round(float(probs[0]), 4),
            "noise": round(float(probs[1]), 4),
            "danger_contact": round(float(probs[2]), 4),
        }

    def fit(self, transitions: Sequence[Transition], epochs: int = 160) -> List[float]:
        if not transitions:
            return []
        x = torch.tensor([world_features(t.object_features, t.action) for t in transitions], dtype=torch.float32)
        y = torch.tensor(
            [
                [
                    1.0 if t.actual.get("object_fell") else 0.0,
                    1.0 if t.actual.get("noise") else 0.0,
                    1.0 if t.actual.get("danger_contact") else 0.0,
                ]
                for t in transitions
            ],
            dtype=torch.float32,
        )
        optimizer = torch.optim.Adam(self.parameters(), lr=0.08)
        losses: List[float] = []
        for epoch in range(epochs):
            optimizer.zero_grad()
            loss = nn.functional.binary_cross_entropy_with_logits(self.forward(x), y)
            loss.backward()
            optimizer.step()
            if epoch in (0, epochs - 1):
                losses.append(round(float(loss.item()), 6))
        self.trained = True
        self.update_refs.append(f"world_train_epochs_{epochs}")
        return losses

    def prediction_error(self, obj: GridObject, action: Action, actual: Dict[str, bool]) -> float:
        pred = self.predict(obj, action)
        diffs = [
            abs(pred["object_fell"] - (1.0 if actual.get("object_fell") else 0.0)),
            abs(pred["noise"] - (1.0 if actual.get("noise") else 0.0)),
            abs(pred["danger_contact"] - (1.0 if actual.get("danger_contact") else 0.0)),
        ]
        return round(sum(diffs) / len(diffs), 4)


class SelfModel(nn.Module):
    def __init__(self, seed: int):
        super().__init__()
        torch.manual_seed(int(seed) + 17)
        self.linear = nn.Linear(3, 4)
        nn.init.zeros_(self.linear.weight)
        nn.init.zeros_(self.linear.bias)
        with torch.no_grad():
            self.linear.bias[:3].fill_(-3.0)
        self.trained = False
        self.update_refs: List[str] = []

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)

    def predict(self, world_prediction: Dict[str, float], action: Action) -> Dict[str, float]:
        with torch.no_grad():
            x = torch.tensor([self_features(world_prediction, action)], dtype=torch.float32)
            raw = self.forward(x)[0]
            stress = torch.sigmoid(raw[0]).item()
            damage_risk = torch.sigmoid(raw[1]).item()
            failure_prob = torch.sigmoid(raw[2]).item()
            affinity_delta = (torch.tanh(raw[3]) * 0.15).item()
        if action == Action.APPROACH:
            energy_cost = -0.12
        elif action == Action.OBSERVE:
            energy_cost = -0.04
        else:
            energy_cost = 0.03
        return {
            "stress_delta": round(float(stress), 4),
            "energy_delta": round(float(energy_cost), 4),
            "damage_risk": round(float(damage_risk), 4),
            "action_failure_prob": round(float(failure_prob), 4),
            "affinity_delta": round(float(affinity_delta), 4),
        }

    def fit(self, transitions: Sequence[Transition], world_model: WorldModel, epochs: int = 140) -> List[float]:
        if not transitions:
            return []
        xs: List[List[float]] = []
        ys: List[List[float]] = []
        for transition in transitions:
            obj = GridObject(
                object_id=transition.object_id,
                name=transition.object_id,
                position=(0, 0),
                features=_features_from_transition(transition),
            )
            world_prediction = world_model.predict(obj, Action(transition.action))
            xs.append(self_features(world_prediction, transition.action))
            ys.append(
                [
                    float(transition.self_delta.get("stress_delta", 0.0)),
                    float(transition.self_delta.get("damage_risk", 0.0)),
                    float(transition.self_delta.get("action_failure_prob", 0.0)),
                    float(transition.self_delta.get("affinity_delta", 0.0)),
                ]
            )
        x = torch.tensor(xs, dtype=torch.float32)
        y = torch.tensor(ys, dtype=torch.float32)
        optimizer = torch.optim.Adam(self.parameters(), lr=0.08)
        losses: List[float] = []
        for epoch in range(epochs):
            optimizer.zero_grad()
            raw = self.forward(x)
            pred = torch.cat(
                [
                    torch.sigmoid(raw[:, :3]),
                    torch.tanh(raw[:, 3:4]) * 0.15,
                ],
                dim=1,
            )
            loss = nn.functional.mse_loss(pred, y)
            loss.backward()
            optimizer.step()
            if epoch in (0, epochs - 1):
                losses.append(round(float(loss.item()), 6))
        self.trained = True
        self.update_refs.append(f"self_train_epochs_{epochs}")
        return losses


def _features_from_transition(transition: Transition):
    from .environment import ObjectFeatures

    return ObjectFeatures(
        instability=float(transition.object_features["instability"]),
        height=float(transition.object_features["height"]),
        fragility=float(transition.object_features["fragility"]),
        novelty=float(transition.object_features["novelty"]),
    )


class HomeostaticValue:
    def score(
        self,
        *,
        obj: GridObject,
        action: Action,
        world_prediction: Dict[str, float],
        self_prediction: Dict[str, float],
        uncertainty: float,
    ) -> Dict[str, float]:
        danger = float(world_prediction["danger_contact"])
        stress = float(self_prediction["stress_delta"])
        self_risk = float(self_prediction["damage_risk"])
        failure_prob = float(self_prediction.get("action_failure_prob", 0.0))
        affinity_delta = float(self_prediction.get("affinity_delta", 0.0))
        energy = abs(float(self_prediction["energy_delta"]))
        approach_bonus = 0.47 if action == Action.APPROACH else 0.02
        observation_bonus = 0.05 if action == Action.OBSERVE else 0.0
        reversibility = 0.18 if action == Action.RETREAT else (0.05 if action == Action.OBSERVE else 0.02)
        components = {
            "safety": -0.18 * danger,
            "energy_balance": -0.35 * energy,
            "stress_control": -0.75 * stress,
            "ability_control": -0.70 * failure_prob,
            "curiosity_gain": (0.12 * obj.features.novelty) + observation_bonus,
            "information_gain": uncertainty * (0.22 if action == Action.OBSERVE else 0.04),
            "relationship_stability": -0.08 * float(world_prediction["noise"]) - (0.30 * max(0.0, -affinity_delta)),
            "capability_growth": 0.04 if action == Action.OBSERVE else 0.0,
            "future_action_space": 0.03 if action != Action.APPROACH else -0.01,
            "reversibility": reversibility,
            "affinity_gain": approach_bonus + (2.00 * affinity_delta),
            "self_risk_control": -0.98 * self_risk,
        }
        components["total"] = round(sum(components.values()), 6)
        return {key: round(float(value), 6) for key, value in components.items()}
