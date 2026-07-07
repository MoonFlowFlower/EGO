from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PrefLearner:
    topic_count: int
    option_count: int
    alpha: float = 0.2
    values: list[list[float]] | None = None

    def __post_init__(self) -> None:
        if self.values is None:
            base = 1.0 / float(self.option_count)
            self.values = [[base for _ in range(self.option_count)] for _ in range(self.topic_count)]

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "PrefLearner":
        return cls(
            topic_count=int(state["topic_count"]),
            option_count=int(state["option_count"]),
            alpha=float(state["alpha"]),
            values=[[float(x) for x in row] for row in state["values"]],
        )

    def to_state(self) -> dict[str, Any]:
        return {
            "topic_count": self.topic_count,
            "option_count": self.option_count,
            "alpha": self.alpha,
            "values": [[round(float(x), 12) for x in row] for row in self.values or []],
        }

    def fit(self, *, topic: int, option: int) -> None:
        row = [float(x) * (1.0 - self.alpha) for x in (self.values or [])[int(topic)]]
        row[int(option)] += self.alpha
        self.values[int(topic)] = [round(x, 12) for x in row]

    def predict(self, topic: int) -> int:
        row = [float(x) for x in (self.values or [])[int(topic)]]
        return min(range(len(row)), key=lambda idx: (-row[idx], idx))

    def scores(self, topic: int) -> list[float]:
        return [float(x) for x in (self.values or [])[int(topic)]]


def zero_pref_model(topic_count: int, option_count: int) -> dict[str, Any]:
    return {
        "topic_count": int(topic_count),
        "option_count": int(option_count),
        "alpha": 0.2,
        "values": [[0.0 for _ in range(option_count)] for _ in range(topic_count)],
    }


def static_pref_standin(initial_preferences: dict[int, int] | dict[str, int], *, topic: int) -> int:
    return int(initial_preferences.get(int(topic), initial_preferences.get(str(topic), 0)))
