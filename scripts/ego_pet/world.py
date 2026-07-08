from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "egodesktop-pet-world-integration-001a"
WORLD_CONFIG_PATH = TASK_DIR / "world_config_v0.json"


def jcopy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def load_world_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or WORLD_CONFIG_PATH
    return json.loads(config_path.read_text(encoding="utf-8"))


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def regime_for_tick(config: dict[str, Any], tick_index: int) -> dict[str, Any]:
    tick = int(tick_index)
    for regime in config["regimes"]:
        start, end = [int(x) for x in regime["tick_range"]]
        if start <= tick <= end:
            return regime
    raise ValueError(f"tick out of configured regime ranges: {tick}")


def regime_id_for_tick(config: dict[str, Any], tick_index: int) -> str:
    return str(regime_for_tick(config, tick_index)["regime_id"])


def zero_world_state(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "pet_world_v0",
        "tick_index": 0,
        "needs": jcopy(config["needs"]["initial"]),
        "interaction_history": [],
        "last_regime_id": regime_id_for_tick(config, 0),
    }


def viability(needs: dict[str, float], config: dict[str, Any]) -> float:
    energy = float(needs["energy"])
    comfort = float(needs["comfort"])
    floor = float(config["needs"]["critical_floor"])
    penalty_each = float(config["viability_function"]["critical_penalty"]["per_need_below_critical_floor"])
    penalty = 0.0
    if energy < floor:
        penalty += penalty_each
    if comfort < floor:
        penalty += penalty_each
    return round(clamp(0.5 * energy + 0.5 * comfort - penalty), 12)


def quantize_tick(value: Any, *, current_tick: int = 0) -> int:
    tick = int(float(value))
    if tick < int(current_tick):
        return int(current_tick)
    return tick


def build_observation(world_state: dict[str, Any], config: dict[str, Any], raw_event: dict[str, Any] | None = None) -> dict[str, Any]:
    tick = int(world_state["tick_index"])
    return {
        "tick_index": tick,
        "regime_id": regime_id_for_tick(config, tick),
        "needs": jcopy(world_state["needs"]),
        "viability": viability(world_state["needs"], config),
        "user_event": jcopy(raw_event) if raw_event else None,
    }


def _rate_limited(history: list[dict[str, Any]], event_type: str, tick: int, config: dict[str, Any]) -> bool:
    effect = config["world"]["interaction_effects"].get(event_type, {})
    max_per_20 = effect.get("max_per_20_ticks")
    if max_per_20 is None:
        return False
    recent = [
        item for item in history
        if item.get("event_type") == event_type and int(tick) - int(item.get("tick_index", -9999)) < 20
    ]
    return len(recent) >= int(max_per_20)


def apply_user_event(world_state: dict[str, Any], user_event: dict[str, Any] | None, config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if not user_event:
        return jcopy(world_state), None
    event_type = str(user_event.get("event_type") or user_event.get("type") or "")
    if event_type not in config["world"]["interaction_set"]:
        raise ValueError(f"unknown pet interaction event: {event_type}")
    tick = quantize_tick(user_event.get("tick_index", world_state["tick_index"]), current_tick=int(world_state["tick_index"]))
    next_state = jcopy(world_state)
    history = list(next_state.get("interaction_history", []))
    if _rate_limited(history, event_type, tick, config):
        decision = {"event_type": event_type, "tick_index": tick, "admitted": False, "reason": "rate_limited"}
        history.append(decision)
        next_state["interaction_history"] = history
        return next_state, decision
    effect = config["world"]["interaction_effects"].get(event_type, {})
    needs = dict(next_state["needs"])
    needs["energy"] = clamp(float(needs["energy"]) + float(effect.get("energy_delta", 0.0)))
    needs["comfort"] = clamp(float(needs["comfort"]) + float(effect.get("comfort_delta", 0.0)))
    next_state["needs"] = {k: round(float(v), 12) for k, v in needs.items()}
    decision = {"event_type": event_type, "tick_index": tick, "admitted": True, "reason": "accepted"}
    history.append(decision)
    next_state["interaction_history"] = history
    return next_state, decision


def site_yields_for_tick(config: dict[str, Any], tick_index: int) -> dict[str, dict[str, float]]:
    return jcopy(regime_for_tick(config, tick_index)["site_yields"])


def _action_yield(action: dict[str, Any], yields: dict[str, dict[str, float]]) -> dict[str, float]:
    action_type = str(action.get("action_type", "observe"))
    site = str(action.get("site", ""))
    if action_type == "observe":
        return {"energy": 0.0, "comfort": 0.0}
    if action_type == "rest":
        return {"energy": 0.0, "comfort": 0.0}
    if site not in yields:
        raise ValueError(f"unknown resource site: {site}")
    return {"energy": float(yields[site]["energy"]), "comfort": float(yields[site]["comfort"])}


def advance_world(world_state: dict[str, Any], action: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    current = jcopy(world_state)
    tick = int(current["tick_index"])
    yields = site_yields_for_tick(config, tick)
    gained = _action_yield(action, yields)
    decays = config["needs"]["per_tick_decay"]
    needs = {
        "energy": clamp(float(current["needs"]["energy"]) + gained["energy"] - float(decays["energy"])),
        "comfort": clamp(float(current["needs"]["comfort"]) + gained["comfort"] - float(decays["comfort"])),
    }
    next_state = {
        **current,
        "tick_index": tick + 1,
        "needs": {k: round(float(v), 12) for k, v in needs.items()},
        "last_regime_id": regime_id_for_tick(config, tick),
    }
    feedback = {
        "tick_index": tick,
        "regime_id": regime_id_for_tick(config, tick),
        "action_yield": {k: round(float(v), 12) for k, v in gained.items()},
        "observed_site_yields": yields if action.get("action_type") == "observe" else None,
        "needs_after": jcopy(next_state["needs"]),
        "viability_after": viability(next_state["needs"], config),
    }
    return next_state, feedback

