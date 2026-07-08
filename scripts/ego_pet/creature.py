from __future__ import annotations

from typing import Any

from scripts.ego_kernel.state import KernelState, deep_copy
from scripts.ego_kernel.tick import consume_registered_rng

from scripts.ego_pet.standin import (
    hardcoded_standin_action,
    schedule_aware_reference_action,
    static_policy_action,
)


PET_CREATURE_SCHEMA = "pet_creature_v0"
EXPLORATION_EPSILON = 0.05


def _pre_shift_yields(config: dict[str, Any]) -> dict[str, dict[str, float]]:
    return deep_copy(config["regimes"][0]["site_yields"])


def zero_creature_state(config: dict[str, Any], *, arm: str) -> dict[str, Any]:
    prior = _pre_shift_yields(config)
    return {
        "schema": PET_CREATURE_SCHEMA,
        "arm": str(arm),
        "model": prior,
        "model_counts": {site: 1 for site in prior},
        "last_prediction_error": 0.0,
        "last_observe_tick": -9999,
        "exploration_epsilon": EXPLORATION_EPSILON,
        "updates_enabled": arm not in {"frozen_updates", "static", "standin", "random"},
    }


def _site_score(yields: dict[str, float], need_key: str) -> float:
    other = "comfort" if need_key == "energy" else "energy"
    return float(yields[need_key]) + 0.25 * float(yields[other])


def _best_site(model: dict[str, dict[str, float]], need_key: str) -> str:
    return min(model, key=lambda site: (-_site_score(model[site], need_key), site))


def _exploration_action(config: dict[str, Any], value: float) -> dict[str, Any]:
    sites = list(config["world"]["resource_sites"])
    index = int(float(value) * len(sites)) % len(sites)
    site = sites[index]
    action_type = "forage_energy" if index % 2 == 0 else "seek_comfort"
    return {"policy": "candidate_epsilon_explore", "action_type": action_type, "site": site}


def _prediction_for_action(creature: dict[str, Any], action: dict[str, Any]) -> dict[str, float]:
    if action.get("action_type") == "observe":
        return {"energy": 0.0, "comfort": 0.0}
    site = action.get("site")
    if not site or site not in creature["model"]:
        return {"energy": 0.0, "comfort": 0.0}
    return {
        "energy": round(float(creature["model"][site]["energy"]), 12),
        "comfort": round(float(creature["model"][site]["comfort"]), 12),
    }


def _derived_prediction_error_trigger(config: dict[str, Any]) -> float:
    deltas: list[float] = []
    for drift in config["drift_schedule"]:
        before = next(r for r in config["regimes"] if r["regime_id"] == drift["from_regime"])
        after = next(r for r in config["regimes"] if r["regime_id"] == drift["to_regime"])
        for old_site, new_site in drift["best_site_change"].values():
            for need in ("energy", "comfort"):
                deltas.append(abs(float(after["site_yields"][new_site][need]) - float(before["site_yields"][old_site][need])))
    positives = [d for d in deltas if d > 0]
    return round((min(positives) if positives else 0.01) / 2.0, 12)


def select_action(
    state: KernelState,
    observation: dict[str, Any],
    config: dict[str, Any],
    *,
    arm: str,
    allow_unregistered_seed: bool = False,
) -> tuple[dict[str, Any], KernelState, dict[str, Any]]:
    creature = deep_copy(state.substates["pet_creature_v0"])
    needs = observation["needs"]
    if arm == "standin":
        action = hardcoded_standin_action(config, needs)
        return action, state, {"policy": "hardcoded_standin", "prediction": _prediction_for_action(creature, action)}
    if arm == "static":
        action = static_policy_action(config, needs)
        return action, state, {"policy": "static_no_update", "prediction": _prediction_for_action(creature, action)}
    if arm == "schedule_aware_reference":
        action = schedule_aware_reference_action(config, observation)
        return action, state, {"policy": "schedule_aware_reference", "prediction": _prediction_for_action(creature, action)}
    if arm == "random":
        value, state_after_rng, draw_index = consume_registered_rng(
            state, "pet_policy", allow_unregistered_seed=allow_unregistered_seed
        )
        action = _exploration_action(config, value)
        action["policy"] = "random_policy"
        return action, state_after_rng, {
            "policy": "random_policy",
            "rng_draw_index": draw_index,
            "rng_value": round(float(value), 12),
            "prediction": _prediction_for_action(creature, action),
        }

    tick = int(observation["tick_index"])
    trigger = _derived_prediction_error_trigger(config)
    if tick == 0 or float(creature.get("last_prediction_error", 0.0)) > trigger:
        action = {"policy": arm, "action_type": "observe", "site": None}
        return action, state, {
            "policy": arm,
            "observe_reason": "initial_or_prediction_error",
            "prediction_error_trigger": trigger,
            "prediction": _prediction_for_action(creature, action),
        }

    epsilon_value, state_after_rng, draw_index = consume_registered_rng(
        state, "pet_policy", allow_unregistered_seed=allow_unregistered_seed
    )
    if epsilon_value < EXPLORATION_EPSILON:
        action = _exploration_action(config, epsilon_value / EXPLORATION_EPSILON)
        return action, state_after_rng, {
            "policy": arm,
            "exploration": "epsilon_greedy",
            "epsilon": EXPLORATION_EPSILON,
            "rng_draw_index": draw_index,
            "rng_value": round(float(epsilon_value), 12),
            "prediction": _prediction_for_action(creature, action),
        }

    energy_deficit = 1.0 - float(needs["energy"])
    comfort_deficit = 1.0 - float(needs["comfort"])
    if energy_deficit >= comfort_deficit:
        site = _best_site(creature["model"], "energy")
        action = {"policy": arm, "action_type": "forage_energy", "site": site}
    else:
        site = _best_site(creature["model"], "comfort")
        action = {"policy": arm, "action_type": "seek_comfort", "site": site}
    return action, state_after_rng, {
        "policy": arm,
        "exploration": "none",
        "epsilon": EXPLORATION_EPSILON,
        "rng_draw_index": draw_index,
        "rng_value": round(float(epsilon_value), 12),
        "prediction": _prediction_for_action(creature, action),
    }


def update_creature_after_feedback(
    creature: dict[str, Any],
    action: dict[str, Any],
    feedback: dict[str, Any],
    *,
    updates_enabled: bool,
) -> dict[str, Any]:
    next_creature = deep_copy(creature)
    prediction = _prediction_for_action(creature, action)
    actual = feedback["action_yield"]
    prediction_error = abs(float(prediction["energy"]) - float(actual["energy"])) + abs(float(prediction["comfort"]) - float(actual["comfort"]))
    if updates_enabled:
        if action.get("action_type") == "observe" and feedback.get("observed_site_yields"):
            next_creature["model"] = deep_copy(feedback["observed_site_yields"])
            next_creature["last_observe_tick"] = int(feedback["tick_index"])
        elif action.get("site") in next_creature["model"]:
            site = str(action["site"])
            next_creature["model"][site] = deep_copy(actual)
            next_creature["model_counts"][site] = int(next_creature["model_counts"].get(site, 0)) + 1
    next_creature["last_prediction_error"] = round(float(prediction_error), 12)
    next_creature["updates_enabled"] = bool(updates_enabled)
    return next_creature

