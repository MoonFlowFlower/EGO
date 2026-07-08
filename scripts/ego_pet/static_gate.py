from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "egodesktop-pet-world-integration-001a"
STATIC_GATE_CONFIG_PATH = TASK_DIR / "static_gate_config_v0.json"


def load_static_gate_config(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or STATIC_GATE_CONFIG_PATH).read_text(encoding="utf-8"))


def zero_static_gate_state() -> dict[str, Any]:
    return {"schema": "pet_static_gate_v0", "last_emit_tick": -999999, "episode_emit_count": 0, "window_emit_ticks": []}


def maybe_emit_bubble(
    gate_state: dict[str, Any],
    *,
    tick_index: int,
    world_needs: dict[str, float],
    config: dict[str, Any],
    config_sha256: str,
    user_event_type: str | None = None,
    drift_boundary_crossed: bool = False,
    ablation_toggled: bool = False,
    ablation_enabled: bool = False,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    state = json.loads(json.dumps(gate_state, sort_keys=True))
    rate = config["rate_limit"]
    recent = [t for t in state.get("window_emit_ticks", []) if int(tick_index) - int(t) < 200]
    state["window_emit_ticks"] = recent
    blocked = (
        int(tick_index) - int(state.get("last_emit_tick", -999999)) < int(rate["min_ticks_between_bubbles"])
        or int(state.get("episode_emit_count", 0)) >= int(rate["max_bubbles_per_episode"])
        or len(recent) >= int(rate["max_bubbles_per_200_ticks"])
    )
    condition_id = None
    template_id = None
    if ablation_toggled:
        condition_id = "ablation_state_bubble"
        template_id = "static_ablation_state_on" if ablation_enabled else "static_ablation_state_off"
        blocked = False
    elif user_event_type in set(config["conditions"]["post_user_care_ack"]["input_events"]):
        condition_id = "post_user_care_ack"
        template_id = "static_care_ack"
        blocked = False
    elif drift_boundary_crossed and config["conditions"]["drift_disclosure_bubble"]["enabled"]:
        condition_id = "drift_disclosure_bubble"
        template_id = "static_drift_disclosure"
    elif float(world_needs["energy"]) < float(config["conditions"]["low_energy_bubble"]["energy_below"]):
        condition_id = "low_energy_bubble"
        template_id = "static_need_energy"
    elif float(world_needs["comfort"]) < float(config["conditions"]["low_comfort_bubble"]["comfort_below"]):
        condition_id = "low_comfort_bubble"
        template_id = "static_need_comfort"
    if not condition_id or blocked:
        return state, None
    state["last_emit_tick"] = int(tick_index)
    state["episode_emit_count"] = int(state.get("episode_emit_count", 0)) + 1
    state["window_emit_ticks"] = recent + [int(tick_index)]
    row = {
        "tick_index": int(tick_index),
        "surface": config["surface"]["allowed_surface"],
        "template_id": template_id,
        "text": config["templates"][template_id],
        "static_gate_config_sha256": config_sha256,
        "condition_id": condition_id,
        "rate_limit_decision": "emit",
        "learner_originated": False,
    }
    return state, row

