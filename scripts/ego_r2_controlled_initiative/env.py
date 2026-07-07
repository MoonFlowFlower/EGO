from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from .constants import (
    DIP_OFFSET,
    DIP_WIDTH,
    GRID_8,
    TICKS_PER_EPISODE,
    U_IDEAL_ANALYTIC,
    UTILITY,
    WINDOW_OFFSETS,
    WINDOW_WIDTH,
)


@dataclass(frozen=True)
class R2Config:
    t: int = TICKS_PER_EPISODE
    sigma_x1: float = 0.30
    sigma_x2: float = 0.40
    cooldown: int = 5
    negative_delta: float = -0.20
    negative_ticks: int = 40
    positive_delta: float = 0.10
    positive_ticks: int = 20
    u_ideal_analytic: float = U_IDEAL_ANALYTIC


@dataclass
class EpisodeResult:
    episode_seed: int
    phase_offset: int
    raw_utility: float
    normalized_utility: float
    candidate_trace: list[dict[str, Any]] = field(default_factory=list)
    judge_trace: list[dict[str, Any]] = field(default_factory=list)
    action_count: int = 0
    accept_count: int = 0
    reject_count: int = 0
    ignore_count: int = 0


def episode_seed(master_seed: int, episode_index: int) -> int:
    return int(master_seed) * 100000 + int(episode_index)


def phase_offset_for_seed(seed: int) -> int:
    return GRID_8[seed % len(GRID_8)]


def _in_mod_window(tick: int, start: int, width: int, period: int) -> bool:
    return ((tick - start) % period) < width


def base_receptivity(tick: int, phase_offset: int, period: int = TICKS_PER_EPISODE) -> float:
    for offset in WINDOW_OFFSETS:
        if _in_mod_window(tick, phase_offset + offset, WINDOW_WIDTH, period):
            return 0.85
    if _in_mod_window(tick, phase_offset + DIP_OFFSET, DIP_WIDTH, period):
        return 0.10
    return 0.35


def effective_receptivity(base: float, negative_timer: int, positive_timer: int) -> float:
    value = base
    if negative_timer > 0:
        value -= 0.20
    if positive_timer > 0:
        value += 0.10
    return float(min(1.0, max(0.0, value)))


def feedback_for_action(rng: np.random.Generator, s_t: float) -> str:
    draw = float(rng.random())
    if s_t >= 0.60:
        return "accept" if draw < 0.90 else "ignore"
    if s_t <= 0.30:
        return "reject" if draw < 0.90 else "ignore"
    if draw < 0.10:
        return "accept"
    if draw < 0.20:
        return "reject"
    return "ignore"


def _call_policy(policy_fn: Callable[..., Any], obs: dict[str, Any], judge: dict[str, Any]) -> dict[str, Any]:
    try:
        decision = policy_fn(obs, judge)
    except TypeError:
        decision = policy_fn(obs)
    if isinstance(decision, dict):
        return dict(decision)
    return {"action": bool(decision)}


def simulate_episode(
    *,
    config: R2Config,
    master_seed: int,
    episode_index: int,
    policy_fn: Callable[..., Any],
    observer_fn: Callable[[dict[str, Any], str | None, float, dict[str, Any]], None] | None = None,
    force_actions: dict[int, bool] | None = None,
    suppress_actions: set[int] | None = None,
) -> EpisodeResult:
    """Simulate one deterministic episode.

    Candidate-visible observations are passed to policy_fn. Judge fields are
    recorded only in the returned judge_trace and in the optional second
    argument for explicitly privileged policies such as the ideal observer.
    """
    seed = episode_seed(master_seed, episode_index)
    rng = np.random.Generator(np.random.PCG64(seed))
    phase_offset = phase_offset_for_seed(seed)
    raw_utility = 0.0
    candidate_trace: list[dict[str, Any]] = []
    judge_trace: list[dict[str, Any]] = []
    cooldown_remaining = 0
    negative_timer = 0
    positive_timer = 0
    ticks_since_feedback = 100
    action_count = accept_count = reject_count = ignore_count = 0
    force_actions = force_actions or {}
    suppress_actions = suppress_actions or set()

    for tick in range(config.t):
        base = base_receptivity(tick, phase_offset, config.t)
        s_t = effective_receptivity(base, negative_timer, positive_timer)
        x1 = float(np.clip(s_t + rng.normal(0.0, config.sigma_x1), 0.0, 1.0))
        x2_signal = 0.5 + 0.5 * np.cos(2 * np.pi * ((tick - phase_offset) % config.t) / config.t)
        x2 = float(np.clip(x2_signal + rng.normal(0.0, config.sigma_x2), 0.0, 1.0))
        x4 = float(rng.random())
        obs = {
            "t": tick,
            "x1": x1,
            "x2": x2,
            "x3": min(ticks_since_feedback, 100) / 100,
            "x4": x4,
        }
        judge = {
            "s_t": s_t,
            "base_s": base,
            "phase_offset": phase_offset,
            "negative_timer": negative_timer,
            "positive_timer": positive_timer,
        }
        decision = _call_policy(policy_fn, obs, judge)
        action = bool(decision.get("action", False))
        if tick in force_actions:
            action = bool(force_actions[tick])
        if tick in suppress_actions:
            action = False
        if cooldown_remaining > 0 and tick not in force_actions:
            action = False

        feedback: str | None = None
        utility_delta = 0.0
        if action:
            action_count += 1
            feedback = feedback_for_action(rng, s_t)
            utility_delta = UTILITY[feedback]
            raw_utility += utility_delta
            if feedback == "accept":
                accept_count += 1
                ticks_since_feedback = 0
            elif feedback == "reject":
                reject_count += 1
                ticks_since_feedback = 0
            else:
                ignore_count += 1
                ticks_since_feedback += 1
        else:
            ticks_since_feedback += 1

        candidate_row = {
            **obs,
            "action": "act" if action else "silent",
            "probe_flag": bool(decision.get("probe_flag", False) and action),
            "expected_utility_act": float(decision.get("expected_utility_act", 0.0)),
            "belief": decision.get("belief", {}),
            "feedback": feedback,
            "raw_utility_delta": utility_delta,
        }
        judge_row = {
            "t": tick,
            "s_t": s_t,
            "base_s": base,
            "window_phase": "hi" if s_t >= 0.60 else ("lo" if s_t <= 0.30 else "mid"),
            "negative_timer": negative_timer,
            "positive_timer": positive_timer,
        }
        candidate_trace.append(candidate_row)
        judge_trace.append(judge_row)
        if observer_fn is not None:
            observer_fn(obs, feedback, utility_delta, decision)

        if negative_timer > 0:
            negative_timer -= 1
        if positive_timer > 0:
            positive_timer -= 1
        if action and s_t < 0.30:
            negative_timer = config.negative_ticks
        if action and s_t >= 0.60:
            positive_timer = config.positive_ticks
        if action:
            cooldown_remaining = config.cooldown
        elif cooldown_remaining > 0:
            cooldown_remaining -= 1

    return EpisodeResult(
        episode_seed=seed,
        phase_offset=phase_offset,
        raw_utility=raw_utility,
        normalized_utility=raw_utility / config.u_ideal_analytic,
        candidate_trace=candidate_trace,
        judge_trace=judge_trace,
        action_count=action_count,
        accept_count=accept_count,
        reject_count=reject_count,
        ignore_count=ignore_count,
    )
