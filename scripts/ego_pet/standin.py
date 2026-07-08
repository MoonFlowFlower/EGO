from __future__ import annotations

from typing import Any


def _deficit(needs: dict[str, float], key: str) -> float:
    return 1.0 - float(needs[key])


def hardcoded_standin_action(config: dict[str, Any], needs: dict[str, float]) -> dict[str, Any]:
    standin = config["hardcoded_standin"]
    if _deficit(needs, "energy") >= _deficit(needs, "comfort"):
        return {
            "policy": "hardcoded_standin",
            "action_type": "forage_energy",
            "site": standin["preferred_energy_site"],
        }
    return {
        "policy": "hardcoded_standin",
        "action_type": "seek_comfort",
        "site": standin["preferred_comfort_site"],
    }


def static_policy_action(config: dict[str, Any], needs: dict[str, float]) -> dict[str, Any]:
    action = hardcoded_standin_action(config, needs)
    return {**action, "policy": "static_no_update"}


def schedule_aware_reference_action(config: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    regime = next(r for r in config["regimes"] if r["regime_id"] == observation["regime_id"])
    needs = observation["needs"]
    if _deficit(needs, "energy") >= _deficit(needs, "comfort"):
        return {
            "policy": "schedule_aware_reference",
            "action_type": "forage_energy",
            "site": regime["energy_best_site"],
        }
    return {
        "policy": "schedule_aware_reference",
        "action_type": "seek_comfort",
        "site": regime["comfort_best_site"],
    }

