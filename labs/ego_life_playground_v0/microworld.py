"""Pure canonical P0 microworld operations for the sole playground reducer.

The module owns data validation and pure observation/gate/transition helpers.
Only :func:`engine.compute_step` composes them into a causal state transition.
There is no hidden regime, oracle label, future outcome, or renderer-owned
state in P0.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping, Sequence


WORLD_STATE_SCHEMA_VERSION = "ego.life_playground.microworld.state.v1"
PUBLIC_OBSERVATION_SCHEMA_VERSION = "ego.life_playground.microworld.observation.v1"
PUBLIC_FRAME_SCHEMA_VERSION = "ego.life_playground.microworld.public_frame.v2"
ALLOWED_WORLD_EVENTS = (
    "resource_appears",
    "social_signal",
    "novel_object",
    "threat_nearby",
    "quiet_interval",
)

_EVENT_TO_CUE = {
    "resource_appears": "resource",
    "social_signal": "contact",
    "novel_object": "novelty",
    "threat_nearby": "threat",
    "quiet_interval": "quiet",
}
_CUE_TO_EVENT = {cue: event for event, cue in _EVENT_TO_CUE.items()}
_EVENT_SUMMARY = {
    "resource_appears": "A visible resource is present at site A.",
    "social_signal": "A visible social signal is present at site B.",
    "novel_object": "A novel object is visible at the fork.",
    "threat_nearby": "A visible hazard is near the fork.",
    "quiet_interval": "The home area is quiet.",
}
_EVENT_OBJECT = {
    "resource_appears": {"object_id": "resource", "kind": "resource", "glyph": "$", "position": "site_a", "visible": True},
    "social_signal": {"object_id": "signal", "kind": "social_signal", "glyph": "S", "position": "site_b", "visible": True},
    "novel_object": {"object_id": "novelty", "kind": "novel_object", "glyph": "?", "position": "fork", "visible": True},
    "threat_nearby": {"object_id": "hazard", "kind": "threat", "glyph": "!", "position": "fork", "visible": True},
    "quiet_interval": {"object_id": "shelter", "kind": "shelter", "glyph": "~", "position": "home", "visible": True},
}
_POSITIONS = {
    "site_a": [1, 1],
    "fork": [4, 1],
    "site_b": [7, 1],
    "home": [4, 2],
}
_BASE_ROWS = ["#########", "#A..F..B#", "#...H...#", "#.......#", "#########"]
_ACTION_POSITION = {
    "approach": "site_b",
    "explore": "fork",
    "forage": "site_a",
    "rest": "home",
    "withdraw": "home",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def cue_for_event(event: str) -> str:
    if type(event) is not str or event not in _EVENT_TO_CUE:
        raise ValueError(
            f"unknown world event {event!r}; allowed={','.join(ALLOWED_WORLD_EVENTS)}"
        )
    return _EVENT_TO_CUE[event]


def event_for_cue(cue: str) -> str:
    if type(cue) is not str or cue not in _CUE_TO_EVENT:
        raise ValueError(f"unknown public cue: {cue!r}")
    return _CUE_TO_EVENT[cue]


def default_event_for_sequence(sequence: int) -> str:
    """Frozen visible P0 event cycle used only when the user omits an event."""

    if type(sequence) is not int or sequence <= 0:
        raise ValueError("sequence must be a positive integer")
    return ALLOWED_WORLD_EVENTS[(sequence - 1) % len(ALLOWED_WORLD_EVENTS)]


def _public_observation(event: str, agent_position: str) -> dict[str, Any]:
    event_object = _EVENT_OBJECT[event]
    return {
        "schema_version": PUBLIC_OBSERVATION_SCHEMA_VERSION,
        "event": event,
        "cue": cue_for_event(event),
        "summary": _EVENT_SUMMARY[event],
        "agent_position": agent_position,
        "visible_object_ids": [event_object["object_id"]],
    }


def initial_world_state() -> dict[str, Any]:
    event = "quiet_interval"
    return {
        "schema_version": WORLD_STATE_SCHEMA_VERSION,
        "layout": {
            "layout_id": "p0_cross_v1",
            "width": 9,
            "height": 5,
            "base_rows": list(_BASE_ROWS),
            "positions": deepcopy(_POSITIONS),
        },
        "agent": {"agent_id": "ego-local", "position": "home"},
        "objects": [deepcopy(_EVENT_OBJECT[event])],
        "public_observation": _public_observation(event, "home"),
    }


def verify_world_state(world: Any) -> None:
    if not isinstance(world, Mapping) or set(world) != {
        "schema_version",
        "layout",
        "agent",
        "objects",
        "public_observation",
    }:
        raise ValueError("microworld state schema mismatch")
    if world["schema_version"] != WORLD_STATE_SCHEMA_VERSION:
        raise ValueError("microworld state schema_version is not canonical")
    layout = world["layout"]
    expected_layout = {
        "layout_id": "p0_cross_v1",
        "width": 9,
        "height": 5,
        "base_rows": list(_BASE_ROWS),
        "positions": _POSITIONS,
    }
    if layout != expected_layout:
        raise ValueError("microworld layout is not canonical")
    agent = world["agent"]
    if not isinstance(agent, Mapping) or set(agent) != {"agent_id", "position"}:
        raise ValueError("microworld agent schema mismatch")
    if agent["agent_id"] != "ego-local" or agent["position"] not in _POSITIONS:
        raise ValueError("microworld agent is not canonical")
    objects = world["objects"]
    if not isinstance(objects, list) or len(objects) != 1 or not isinstance(objects[0], Mapping):
        raise ValueError("microworld objects schema mismatch")
    observation = world["public_observation"]
    if not isinstance(observation, Mapping) or set(observation) != {
        "schema_version",
        "event",
        "cue",
        "summary",
        "agent_position",
        "visible_object_ids",
    }:
        raise ValueError("microworld public observation schema mismatch")
    event = observation["event"]
    if event not in ALLOWED_WORLD_EVENTS:
        raise ValueError("microworld observation event is not canonical")
    expected_observation = _public_observation(str(event), str(agent["position"]))
    if dict(observation) != expected_observation:
        raise ValueError("microworld public observation is inconsistent with state")
    if dict(objects[0]) != _EVENT_OBJECT[event]:
        raise ValueError("microworld object is inconsistent with public event")


def world_hash(world: Mapping[str, Any]) -> str:
    verify_world_state(world)
    return _canonical_hash(world)


def observation_hash(observation: Mapping[str, Any]) -> str:
    return _canonical_hash(observation)


def observe_world_event(world: Mapping[str, Any], event: str) -> dict[str, Any]:
    """Purely apply the explicit pre-decision event to a copied world state."""

    verify_world_state(world)
    cue_for_event(event)
    observed = deepcopy(dict(world))
    observed["objects"] = [deepcopy(_EVENT_OBJECT[event])]
    observed["public_observation"] = _public_observation(
        event, str(observed["agent"]["position"])
    )
    verify_world_state(observed)
    return observed


def legal_action_gate(
    world: Mapping[str, Any], actions: Sequence[str]
) -> dict[str, Any]:
    """Return the explicit P0 hard-gate surface.

    P0 has no blocked action: all five canonical local actions remain legal.
    The explicit empty gated set prevents a renderer from inventing legality.
    """

    verify_world_state(world)
    canonical = list(actions)
    if not canonical or any(type(action) is not str or action not in _ACTION_POSITION for action in canonical):
        raise ValueError("microworld action set is not canonical")
    if len(canonical) != len(set(canonical)):
        raise ValueError("microworld action set contains duplicates")
    return {
        "rule": "p0_all_canonical_actions_legal",
        "legal_actions": canonical,
        "gated_actions": [],
    }


def transition_world(
    world: Mapping[str, Any], selected_action: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Pure post-selection agent movement; never selects the action."""

    verify_world_state(world)
    if selected_action not in _ACTION_POSITION:
        raise ValueError(f"unknown microworld action: {selected_action!r}")
    transitioned = deepcopy(dict(world))
    from_position = str(transitioned["agent"]["position"])
    to_position = _ACTION_POSITION[selected_action]
    transitioned["agent"]["position"] = to_position
    observation = deepcopy(transitioned["public_observation"])
    observation["agent_position"] = to_position
    transitioned["public_observation"] = observation
    verify_world_state(transitioned)
    return transitioned, {
        "producer_function": "ego_life_playground_v0.microworld.transition_world",
        "selected_action": selected_action,
        "from_position": from_position,
        "to_position": to_position,
        "moved": from_position != to_position,
    }


def make_public_frame(
    state: Mapping[str, Any], trace: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Render only recovered canonical world state; ``trace`` is ignored."""

    _ = trace
    world = state.get("world")
    organism = state.get("organism")
    current_goal = state.get("current_goal")
    clock = state.get("clock")
    if not isinstance(world, Mapping):
        raise ValueError("canonical state is missing microworld state")
    verify_world_state(world)
    if not isinstance(clock, Mapping) or not isinstance(organism, Mapping):
        raise ValueError("canonical state is missing clock or organism")
    if not isinstance(current_goal, Mapping):
        raise ValueError("canonical state is missing current_goal")

    rows = [list(row) for row in world["layout"]["base_rows"]]
    positions = world["layout"]["positions"]
    for item in world["objects"]:
        object_x, object_y = positions[item["position"]]
        rows[object_y][object_x] = item["glyph"]
    agent_x, agent_y = positions[world["agent"]["position"]]
    rows[agent_y][agent_x] = "@"
    rendered_rows = ["".join(row) for row in rows]
    observation = deepcopy(dict(world["public_observation"]))
    return {
        "schema_version": PUBLIC_FRAME_SCHEMA_VERSION,
        "product_clock": deepcopy(dict(clock)),
        "layout": deepcopy(world["layout"]),
        "map_legend": {
            "@": "agent",
            "A": "site_a",
            "B": "site_b",
            "F": "fork",
            "H": "home",
            "$": "resource",
            "S": "social_signal",
            "?": "novel_object",
            "!": "threat",
            "~": "shelter",
        },
        "map_rows": rendered_rows,
        "ascii_map": "\n".join(rendered_rows),
        "agent": deepcopy(world["agent"]),
        "objects": deepcopy(world["objects"]),
        "observation": observation,
        "observation_hash": observation_hash(observation),
        "world_state_hash": world_hash(world),
        "internal_state": deepcopy(dict(organism)),
        "current_goal": deepcopy(dict(current_goal)),
        "last_action": state.get("last_action"),
    }


__all__ = [
    "ALLOWED_WORLD_EVENTS",
    "PUBLIC_FRAME_SCHEMA_VERSION",
    "PUBLIC_OBSERVATION_SCHEMA_VERSION",
    "WORLD_STATE_SCHEMA_VERSION",
    "cue_for_event",
    "default_event_for_sequence",
    "event_for_cue",
    "initial_world_state",
    "legal_action_gate",
    "make_public_frame",
    "observation_hash",
    "observe_world_event",
    "transition_world",
    "verify_world_state",
    "world_hash",
]
