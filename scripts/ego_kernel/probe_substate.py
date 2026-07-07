from __future__ import annotations

import random
from typing import Any

from scripts.ego_kernel.state import KernelState, deep_copy
from scripts.ego_kernel.tick import consume_registered_rng, kernel_tick
from scripts.ego_kernel.trace import build_trace_row


TASK_ID = "EGO-R0-KERNEL-STATE-SUBSTRATE-001A"
OPTION_COUNT = 4
PREF_ALPHA = 0.001
OBS_STRENGTH = 0.05


def _pref_values_for_bias(option: int) -> list[float]:
    values = [0.02] * OPTION_COUNT
    values[int(option)] = 1.0
    return values


def zero_pref_ema() -> dict[str, Any]:
    return {"values": [0.0] * OPTION_COUNT}


def zero_counter() -> dict[str, Any]:
    return {"tick": 0}


def zero_noise_user() -> dict[str, Any]:
    return {"last_noise": 0.0, "last_draw_index": -1}


ZERO_FACTORIES = {
    "pref_ema": zero_pref_ema,
    "counter": zero_counter,
    "noise_user": zero_noise_user,
}


def build_probe_state(
    *,
    seed: int,
    run_id: str,
    episode_id: str,
    pref_bias: int = 0,
    ablations: dict[str, str] | None = None,
) -> KernelState:
    return KernelState(
        task_id=TASK_ID,
        run_id=run_id,
        episode_id=episode_id,
        step_id=0,
        substates={
            "pref_ema": {"values": _pref_values_for_bias(pref_bias)},
            "counter": {"tick": 0},
            "noise_user": {"last_noise": 0.0, "last_draw_index": -1},
        },
        seed_registry={"noise_user": {"seed": int(seed), "draws": 0}},
        ablations=ablations or {
            "pref_ema": "live",
            "counter": "live",
            "noise_user": "live",
        },
    )


def generate_observation_log(*, seed: int, episode_index: int, ticks: int) -> list[dict[str, Any]]:
    rng = random.Random((int(seed) * 1009) + int(episode_index))
    observations = []
    for step in range(1, int(ticks) + 1):
        observations.append({
            "step_id": step,
            "target_option": rng.randrange(OPTION_COUNT),
            "strength": OBS_STRENGTH,
            "generator_seed": int(seed),
            "episode_index": int(episode_index),
        })
    return observations


def _update_pref_ema(
    substate: dict[str, Any],
    observation: dict[str, Any],
    _context: dict[str, Any],
) -> dict[str, Any]:
    values = [float(value) for value in substate.get("values", [0.0] * OPTION_COUNT)]
    target = int(observation["target_option"])
    strength = float(observation.get("strength", OBS_STRENGTH))
    updated = [(1.0 - PREF_ALPHA) * value for value in values]
    updated[target] += PREF_ALPHA * strength
    return {"values": [round(value, 12) for value in updated]}


def _update_counter(
    substate: dict[str, Any],
    _observation: dict[str, Any],
    _context: dict[str, Any],
) -> dict[str, Any]:
    return {"tick": int(substate.get("tick", 0)) + 1}


def _update_noise_user(
    _substate: dict[str, Any],
    _observation: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    attribution = context["component_attribution"]
    return {
        "last_noise": attribution["noise_value"],
        "last_draw_index": attribution["noise_draw_index"],
    }


UPDATE_RULES = {
    "pref_ema": _update_pref_ema,
    "counter": _update_counter,
    "noise_user": _update_noise_user,
}


def _argmax_action_selector(
    state: KernelState,
    _observation: dict[str, Any],
    *,
    allow_unregistered_seed: bool = False,
) -> tuple[dict[str, Any], KernelState, dict[str, Any]]:
    values = [float(value) for value in state.substates["pref_ema"]["values"]]
    max_value = max(values)
    candidates = [index for index, value in enumerate(values) if abs(value - max_value) <= 1e-12]
    noise, state_after_noise, draw_index = consume_registered_rng(
        state,
        "noise_user",
        allow_unregistered_seed=allow_unregistered_seed,
    )
    selected = candidates[int(noise * len(candidates)) % len(candidates)]
    action = {"option": int(selected)}
    attribution = {
        "pref_ema_values": [round(value, 12) for value in values],
        "argmax_candidates": candidates,
        "selected_option": int(selected),
        "noise_value": round(float(noise), 12),
        "noise_draw_index": int(draw_index),
    }
    return action, state_after_noise, attribution


def run_probe_episode(
    initial_state: KernelState,
    observations: list[dict[str, Any]],
    *,
    checkpoint_ticks: set[int] | None = None,
    allow_unregistered_seed: bool = False,
) -> dict[str, Any]:
    state = initial_state
    checkpoints: dict[str, dict[str, Any]] = {}
    wanted = set(checkpoint_ticks or set())
    if 0 in wanted:
        checkpoints["0"] = state.to_dict()
    rows = []
    for observation in observations:
        before = state
        action, state, attribution = kernel_tick(
            state,
            observation,
            update_rules=UPDATE_RULES,
            zero_factories=ZERO_FACTORIES,
            action_selector=_argmax_action_selector,
            allow_unregistered_seed=allow_unregistered_seed,
        )
        rows.append(build_trace_row(
            state_before=before,
            observation=deep_copy(observation),
            action=action,
            state_after=state,
            component_attribution=attribution,
        ))
        if state.step_id in wanted:
            checkpoints[str(state.step_id)] = state.to_dict()
    return {
        "initial_state": initial_state.to_dict(),
        "final_state": state.to_dict(),
        "trace_rows": rows,
        "checkpoints": checkpoints,
    }
