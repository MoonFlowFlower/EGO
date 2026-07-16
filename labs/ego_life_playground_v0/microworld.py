"""Pure canonical P0/P1 microworld operations for the sole playground reducer.

The module owns data validation and pure observation/gate/transition helpers.
Only :func:`engine.compute_step` composes them into a causal state transition.
P1 adds a persisted private regime and RNG stream.  Those bytes are available
only to the world transition and the explicitly evidence-only oracle helper;
the public observation/frame functions intentionally omit them.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping, Sequence


WORLD_STATE_SCHEMA_VERSION = "ego.life_playground.microworld.state.v2"
PUBLIC_OBSERVATION_SCHEMA_VERSION = "ego.life_playground.microworld.observation.v2"
PUBLIC_FRAME_SCHEMA_VERSION = "ego.life_playground.microworld.public_frame.v3"
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
_SITE_ACTION = {"forage": "site_a", "approach": "site_b"}
_HIDDEN_REGIMES = ("site_a_high", "site_b_high")
_PRIVATE_HISTORY_KEYS = {
    "selected_action",
    "visited_site",
    "outcome",
    "source_sequence",
    "source_episode_id",
    "source_command_hash",
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


def _public_observation(
    event: str, agent_position: str, *, revealed_outcome: float | None = None
) -> dict[str, Any]:
    event_object = _EVENT_OBJECT[event]
    return {
        "schema_version": PUBLIC_OBSERVATION_SCHEMA_VERSION,
        "event": event,
        "cue": cue_for_event(event),
        "summary": _EVENT_SUMMARY[event],
        "agent_position": agent_position,
        "visible_object_ids": [event_object["object_id"]],
        "revealed_outcome": revealed_outcome,
    }


def initial_world_state(*, seed: int = 17) -> dict[str, Any]:
    if type(seed) is not int:
        raise ValueError("microworld seed must be an integer")
    event = "quiet_interval"
    rng_state = int(hashlib.sha256(f"microworld|{seed}".encode("utf-8")).hexdigest()[:15], 16)
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
        "private_dynamics": {
            "hidden_regime": "site_a_high" if seed % 2 == 0 else "site_b_high",
            "rng_state": rng_state,
            "visit_count": 0,
            "outcome_history": [],
        },
    }


def verify_world_state(world: Any) -> None:
    if not isinstance(world, Mapping) or set(world) != {
        "schema_version",
        "layout",
        "agent",
        "objects",
        "public_observation",
        "private_dynamics",
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
        "revealed_outcome",
    }:
        raise ValueError("microworld public observation schema mismatch")
    event = observation["event"]
    if event not in ALLOWED_WORLD_EVENTS:
        raise ValueError("microworld observation event is not canonical")
    revealed = observation["revealed_outcome"]
    if revealed is not None and (type(revealed) is not float or revealed not in {-1.0, 1.0}):
        raise ValueError("microworld revealed outcome is not canonical")
    expected_observation = _public_observation(
        str(event), str(agent["position"]), revealed_outcome=revealed
    )
    if dict(observation) != expected_observation:
        raise ValueError("microworld public observation is inconsistent with state")
    if dict(objects[0]) != _EVENT_OBJECT[event]:
        raise ValueError("microworld object is inconsistent with public event")
    private = world["private_dynamics"]
    if not isinstance(private, Mapping) or set(private) != {
        "hidden_regime",
        "rng_state",
        "visit_count",
        "outcome_history",
    }:
        raise ValueError("microworld private dynamics schema mismatch")
    if private["hidden_regime"] not in _HIDDEN_REGIMES:
        raise ValueError("microworld hidden regime is not canonical")
    if type(private["rng_state"]) is not int or private["rng_state"] < 0:
        raise ValueError("microworld rng_state must be a non-negative integer")
    if type(private["visit_count"]) is not int or private["visit_count"] < 0:
        raise ValueError("microworld visit_count must be a non-negative integer")
    history = private["outcome_history"]
    if not isinstance(history, list) or len(history) != private["visit_count"]:
        raise ValueError("microworld outcome history does not match visit_count")
    for record in history:
        if not isinstance(record, Mapping) or set(record) != _PRIVATE_HISTORY_KEYS:
            raise ValueError("microworld private history schema mismatch")
        if record["selected_action"] not in _SITE_ACTION:
            raise ValueError("microworld private history action is not a site action")
        if record["visited_site"] != _SITE_ACTION[record["selected_action"]]:
            raise ValueError("microworld private history site/action mismatch")
        if type(record["outcome"]) is not float or record["outcome"] not in {-1.0, 1.0}:
            raise ValueError("microworld private history outcome is not canonical")
        if type(record["source_sequence"]) is not int or record["source_sequence"] <= 0:
            raise ValueError("microworld private history sequence is not positive")
        if type(record["source_episode_id"]) is not str or not record["source_episode_id"]:
            raise ValueError("microworld private history episode is not canonical")
        source_hash = record["source_command_hash"]
        if not (
            type(source_hash) is str
            and len(source_hash) == 64
            and all(character in "0123456789abcdef" for character in source_hash)
        ):
            raise ValueError("microworld private history command hash is not sha256")


def world_hash(world: Mapping[str, Any]) -> str:
    verify_world_state(world)
    return _canonical_hash(world)


def public_world_projection(world: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact renderer-visible world subset, excluding private dynamics."""

    verify_world_state(world)
    return {
        "schema_version": "ego.life_playground.microworld.public_projection.v1",
        "layout": deepcopy(world["layout"]),
        "agent": deepcopy(world["agent"]),
        "objects": deepcopy(world["objects"]),
        "public_observation": deepcopy(world["public_observation"]),
    }


def public_world_hash(world: Mapping[str, Any]) -> str:
    return _canonical_hash(public_world_projection(world))


def observation_hash(observation: Mapping[str, Any]) -> str:
    return _canonical_hash(observation)


def observe_world_event(world: Mapping[str, Any], event: str) -> dict[str, Any]:
    """Purely apply the explicit pre-decision event to a copied world state."""

    verify_world_state(world)
    cue_for_event(event)
    observed = deepcopy(dict(world))
    observed["objects"] = [deepcopy(_EVENT_OBJECT[event])]
    observed["public_observation"] = _public_observation(
        event, str(observed["agent"]["position"]), revealed_outcome=None
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
    world: Mapping[str, Any],
    selected_action: str,
    *,
    source_sequence: int,
    source_episode_id: str,
    source_command_hash: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Pure post-selection agent movement; never selects the action."""

    verify_world_state(world)
    if selected_action not in _ACTION_POSITION:
        raise ValueError(f"unknown microworld action: {selected_action!r}")
    transitioned = deepcopy(dict(world))
    from_position = str(transitioned["agent"]["position"])
    visited_site = _SITE_ACTION.get(selected_action)
    to_position = "fork" if visited_site is not None else _ACTION_POSITION[selected_action]
    transitioned["agent"]["position"] = to_position
    observation = deepcopy(transitioned["public_observation"])
    observation["agent_position"] = to_position
    outcome: float | None = None
    drift_applied = False
    if visited_site is not None:
        private = transitioned["private_dynamics"]
        preferred_site = (
            "site_a" if private["hidden_regime"] == "site_a_high" else "site_b"
        )
        outcome = 1.0 if visited_site == preferred_site else -1.0
        private["outcome_history"].append(
            {
                "selected_action": selected_action,
                "visited_site": visited_site,
                "outcome": outcome,
                "source_sequence": int(source_sequence),
                "source_episode_id": source_episode_id,
                "source_command_hash": source_command_hash,
            }
        )
        private["visit_count"] += 1
        next_rng = (
            (1103515245 * int(private["rng_state"]) + 12345) % (2**31)
        )
        private["rng_state"] = next_rng
        # Drift is private-RNG-driven and deliberately absent during the first
        # paired-history visits. It is neither a public clock table nor a
        # policy-visible schedule.
        if int(private["visit_count"]) > 2 and next_rng % 5 == 0:
            private["hidden_regime"] = (
                "site_b_high"
                if private["hidden_regime"] == "site_a_high"
                else "site_a_high"
            )
            drift_applied = True
    observation["revealed_outcome"] = outcome
    transitioned["public_observation"] = observation
    verify_world_state(transitioned)
    return transitioned, {
        "producer_function": "ego_life_playground_v0.microworld.transition_world",
        "selected_action": selected_action,
        "from_position": from_position,
        "to_position": to_position,
        "moved": from_position != to_position,
        "visited_site": visited_site,
        "outcome": outcome,
        "revealed_after_selection": outcome is not None,
    }


def oracle_evidence_record(world: Mapping[str, Any]) -> dict[str, Any]:
    """Return an evidence-only hidden-state read; never used by policy/renderer."""

    verify_world_state(world)
    regime = str(world["private_dynamics"]["hidden_regime"])
    return {
        "schema_version": "ego.life_playground.microworld.oracle.v1",
        "namespace": "evidence_oracle_only",
        "hidden_regime": regime,
        "correct_action": "forage" if regime == "site_a_high" else "approach",
        "world_hash": world_hash(world),
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
        "public_world_hash": public_world_hash(world),
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
    "public_world_hash",
    "public_world_projection",
    "oracle_evidence_record",
    "observe_world_event",
    "transition_world",
    "verify_world_state",
    "world_hash",
]
