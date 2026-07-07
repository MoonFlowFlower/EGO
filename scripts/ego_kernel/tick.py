from __future__ import annotations

import hashlib
import secrets
from typing import Any, Callable

from scripts.ego_kernel.state import KernelState, deep_copy


UpdateRule = Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], dict[str, Any]]
ActionSelector = Callable[..., tuple[dict[str, Any], KernelState, dict[str, Any]]]
ZeroFactory = Callable[[], dict[str, Any]]


def deterministic_unit_interval(seed: int, draw_index: int, stream_name: str) -> float:
    payload = f"{stream_name}:{int(seed)}:{int(draw_index)}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:16], 16) / float(16**16)


def consume_registered_rng(
    state: KernelState,
    stream_name: str,
    *,
    allow_unregistered_seed: bool = False,
) -> tuple[float, KernelState, int]:
    registry = deep_copy(state.seed_registry)
    if stream_name not in registry:
        if not allow_unregistered_seed:
            raise ValueError(f"missing registered seed stream: {stream_name}")
        return secrets.randbits(53) / float(2**53), state, -1
    entry = registry[stream_name]
    seed = int(entry["seed"])
    draw_index = int(entry.get("draws", 0))
    value = deterministic_unit_interval(seed, draw_index, stream_name)
    registry[stream_name] = {"seed": seed, "draws": draw_index + 1}
    return value, state.with_updates(seed_registry=registry), draw_index


def _state_for_action(
    state: KernelState,
    zero_factories: dict[str, ZeroFactory],
) -> KernelState:
    substates = deep_copy(state.substates)
    for name, mode in state.ablations.items():
        if mode == "zeroed" and name in zero_factories:
            substates[name] = zero_factories[name]()
    return state.replace_substates(substates)


def kernel_tick(
    state: KernelState,
    observation: dict[str, Any],
    *,
    update_rules: dict[str, UpdateRule],
    zero_factories: dict[str, ZeroFactory],
    action_selector: ActionSelector,
    allow_unregistered_seed: bool = False,
) -> tuple[dict[str, Any], KernelState, dict[str, Any]]:
    effective_state = _state_for_action(state, zero_factories)
    action, working_state, attribution = action_selector(
        effective_state,
        observation,
        allow_unregistered_seed=allow_unregistered_seed,
    )
    next_substates = deep_copy(working_state.substates)
    context = {"action": action, "component_attribution": attribution}
    for name, rule in update_rules.items():
        mode = str(working_state.ablations.get(name, "live"))
        if mode == "frozen":
            continue
        if mode == "zeroed":
            next_substates[name] = zero_factories[name]()
            continue
        next_substates[name] = rule(deep_copy(next_substates.get(name, {})), observation, context)
    return (
        action,
        working_state.with_updates(step_id=working_state.step_id + 1, substates=next_substates),
        attribution,
    )
