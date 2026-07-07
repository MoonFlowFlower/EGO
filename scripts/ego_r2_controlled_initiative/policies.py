from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .constants import TICKS_PER_EPISODE, UTILITY


def expected_utility_from_probs(p_hi: float, p_lo: float, p_mid: float) -> float:
    return 0.88 * p_hi - 0.92 * p_lo - 0.16 * p_mid


def _phase_from_x2(prefix: list[tuple[int, float]], default: int = 0) -> int:
    if len(prefix) < 12:
        return default
    offsets = (0, 62, 125, 187, 250, 312, 375, 437)
    best = default
    best_score = -1e9
    for offset in offsets:
        score = 0.0
        for tick, x2 in prefix[-80:]:
            expected = 0.5 + 0.5 * np.cos(2 * np.pi * ((tick - offset) % TICKS_PER_EPISODE) / TICKS_PER_EPISODE)
            score -= (x2 - expected) ** 2
        if score > best_score:
            best_score = score
            best = offset
    return best


@dataclass
class GatedInitiativeLearner:
    h_accept: np.ndarray = field(default_factory=lambda: np.ones(50))
    h_reject: np.ndarray = field(default_factory=lambda: np.ones(50))
    x1_accept: np.ndarray = field(default_factory=lambda: np.ones(10))
    x1_reject: np.ndarray = field(default_factory=lambda: np.ones(10))
    x2_prefix: list[tuple[int, float]] = field(default_factory=list)
    accept_boost_until: int = -1
    reject_suppress_until: int = -1
    probes_used: int = 0
    last_feedback: str | None = None

    @classmethod
    def synthetic_with_tables(cls, *, phase_bin: int) -> "GatedInitiativeLearner":
        learner = cls()
        learner.h_accept[:] = 1.0
        learner.h_reject[:] = 4.0
        learner.h_accept[phase_bin] = 40.0
        learner.h_reject[phase_bin] = 1.0
        learner.x1_accept[6:] = 20.0
        learner.x1_reject[:3] = 20.0
        return learner

    def clone_frozen(self) -> "GatedInitiativeLearner":
        return GatedInitiativeLearner(
            h_accept=self.h_accept.copy(),
            h_reject=self.h_reject.copy(),
            x1_accept=self.x1_accept.copy(),
            x1_reject=self.x1_reject.copy(),
        )

    def reset_episode(self) -> None:
        self.x2_prefix = []
        self.accept_boost_until = -1
        self.reject_suppress_until = -1
        self.probes_used = 0
        self.last_feedback = None

    def _belief(self, obs: dict[str, Any]) -> dict[str, float | int | bool]:
        tick = int(obs["t"])
        self.x2_prefix.append((tick, float(obs["x2"])))
        a_hat = _phase_from_x2(self.x2_prefix)
        tau = (tick - a_hat) % TICKS_PER_EPISODE
        phase_bin = min(49, int(tau / 10))
        x1_bin = min(9, max(0, int(float(obs["x1"]) * 10)))
        phase_hi = self.h_accept[phase_bin] / (self.h_accept[phase_bin] + self.h_reject[phase_bin] + 2.0)
        phase_lo = self.h_reject[phase_bin] / (self.h_accept[phase_bin] + self.h_reject[phase_bin] + 2.0)
        x1_hi = self.x1_accept[x1_bin] / (self.x1_accept[x1_bin] + self.x1_reject[x1_bin] + 2.0)
        x1_lo = self.x1_reject[x1_bin] / (self.x1_accept[x1_bin] + self.x1_reject[x1_bin] + 2.0)
        p_hi = 0.55 * phase_hi + 0.45 * x1_hi
        p_lo = 0.55 * phase_lo + 0.45 * x1_lo
        if tick < self.accept_boost_until:
            p_hi = min(0.95, p_hi + 0.20)
            p_lo = max(0.02, p_lo - 0.10)
        if tick < self.reject_suppress_until:
            p_lo = min(0.95, p_lo + 0.30)
            p_hi = max(0.02, p_hi - 0.15)
        total = max(1.0, p_hi + p_lo)
        p_hi = min(0.98, p_hi / total)
        p_lo = min(0.98 - p_hi, p_lo / total)
        p_mid = max(0.0, 1.0 - p_hi - p_lo)
        uncertainty = len(self.x2_prefix) < 150 and abs(phase_hi - phase_lo) < 0.25
        return {
            "p_hi": float(p_hi),
            "p_lo": float(p_lo),
            "p_mid": float(p_mid),
            "a_hat": int(a_hat),
            "uncertainty_flag": bool(uncertainty),
        }

    def decide(self, obs: dict[str, Any]) -> dict[str, Any]:
        belief = self._belief(obs)
        eu = expected_utility_from_probs(float(belief["p_hi"]), float(belief["p_lo"]), float(belief["p_mid"]))
        probe = (
            self.probes_used < 3
            and int(obs["t"]) < 150
            and bool(belief["uncertainty_flag"])
            and float(belief["p_lo"]) < 0.20
        )
        action = eu > 0.0 or probe
        if probe and action:
            self.probes_used += 1
        return {"action": action, "expected_utility_act": eu, "belief": belief, "probe_flag": probe}

    def observe_feedback(self, obs: dict[str, Any], feedback: str | None) -> None:
        if feedback is None:
            return
        tick = int(obs["t"])
        if feedback == "accept":
            self.accept_boost_until = tick + 20
        elif feedback == "reject":
            self.reject_suppress_until = tick + 50

    def observe_training_event(self, obs: dict[str, Any], feedback: str | None) -> None:
        if feedback not in {"accept", "reject"}:
            return
        tick = int(obs["t"])
        a_hat = _phase_from_x2(self.x2_prefix)
        phase_bin = min(49, int(((tick - a_hat) % TICKS_PER_EPISODE) / 10))
        x1_bin = min(9, max(0, int(float(obs["x1"]) * 10)))
        if feedback == "accept":
            self.h_accept[phase_bin] += 1.0
            self.x1_accept[x1_bin] += 1.0
        else:
            self.h_reject[phase_bin] += 1.0
            self.x1_reject[x1_bin] += 1.0


class A1NoLearnedTablesCandidate(GatedInitiativeLearner):
    @classmethod
    def synthetic_with_uninformative_priors(cls) -> "A1NoLearnedTablesCandidate":
        return cls()

    def clone_frozen(self) -> "A1NoLearnedTablesCandidate":
        return A1NoLearnedTablesCandidate()


@dataclass
class BehaviorTreePolicy:
    threshold: float = 0.60
    base_cooldown: int = 20
    dynamic_cooldown: int = 20
    last_action_tick: int = -100000
    consecutive_rejects: int = 0

    def reset_episode(self) -> None:
        self.dynamic_cooldown = self.base_cooldown
        self.last_action_tick = -100000
        self.consecutive_rejects = 0

    def decide(self, obs: dict[str, Any]) -> dict[str, Any]:
        tick = int(obs["t"])
        action = (
            float(obs["x1"]) >= self.threshold
            and tick - self.last_action_tick >= self.dynamic_cooldown
            and self.consecutive_rejects < 2
        )
        if action:
            self.last_action_tick = tick
        return {"action": action, "expected_utility_act": float(obs["x1"]) - self.threshold}

    def observe_feedback(self, obs: dict[str, Any], feedback: str | None) -> None:
        if feedback == "reject":
            self.consecutive_rejects += 1
            self.dynamic_cooldown = min(80, self.dynamic_cooldown * 2)
        elif feedback == "accept":
            self.consecutive_rejects = 0
            self.dynamic_cooldown = self.base_cooldown


def always_silent(obs: dict[str, Any]) -> dict[str, Any]:
    return {"action": False}


def always_act(obs: dict[str, Any]) -> dict[str, Any]:
    return {"action": True, "expected_utility_act": 1.0}


def fixed_rate_policy(rate: float):
    def _policy(obs: dict[str, Any]) -> dict[str, Any]:
        return {"action": float(obs["x4"]) < rate, "expected_utility_act": rate - 0.5}

    return _policy


def single_threshold_policy(channel: str, theta: float):
    def _policy(obs: dict[str, Any]) -> dict[str, Any]:
        return {"action": float(obs[channel]) >= theta, "expected_utility_act": float(obs[channel]) - theta}

    return _policy


def ideal_observer_policy(obs: dict[str, Any], judge: dict[str, Any]) -> dict[str, Any]:
    p_hi = 1.0 if float(judge["s_t"]) >= 0.60 else 0.0
    p_lo = 1.0 if float(judge["s_t"]) <= 0.30 else 0.0
    p_mid = 1.0 - p_hi - p_lo
    eu = expected_utility_from_probs(p_hi, p_lo, p_mid)
    return {"action": eu > 0.0, "expected_utility_act": eu, "belief": {"privileged": True}}


def policy_with_feedback(policy_obj: Any):
    def decide(obs: dict[str, Any], judge: dict[str, Any] | None = None) -> dict[str, Any]:
        return policy_obj.decide(obs)

    def observe(obs: dict[str, Any], feedback: str | None, utility_delta: float, decision: dict[str, Any]) -> None:
        if hasattr(policy_obj, "observe_feedback"):
            policy_obj.observe_feedback(obs, feedback)

    return decide, observe
