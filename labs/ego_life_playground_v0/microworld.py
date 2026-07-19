"""Pure canonical P0/P1 microworld operations for the sole playground reducer.

The module owns data validation and pure observation/gate/transition helpers.
Only :func:`engine.compute_step` composes them into a causal state transition.
P1 adds a persisted private regime and RNG stream.  Those bytes are available
only to the world transition and the explicitly evidence-only oracle helper;
the public observation/frame functions intentionally omit them.
"""

from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping, Sequence


WORLD_STATE_SCHEMA_VERSION = "ego.life_playground.microworld.state.v3"
PUBLIC_OBSERVATION_SCHEMA_VERSION = "ego.life_playground.microworld.observation.v3"
PUBLIC_FRAME_SCHEMA_VERSION = "ego.life_playground.microworld.public_frame.v4"
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
LAYOUTS: dict[str, dict[str, Any]] = {
    "p0_cross_v1": {
        "layout_id": "p0_cross_v1",
        "width": 9,
        "height": 5,
        "base_rows": ["#########", "#A..F..B#", "#...H...#", "#.......#", "#########"],
        "positions": {"site_a": [1, 1], "fork": [4, 1], "site_b": [7, 1], "home": [4, 2]},
    },
    "p2_vertical_v1": {
        "layout_id": "p2_vertical_v1",
        "width": 7,
        "height": 7,
        "base_rows": ["#######", "#..A..#", "#.....#", "#..F..#", "#.....#", "#B.H..#", "#######"],
        "positions": {"site_a": [3, 1], "fork": [3, 3], "site_b": [1, 5], "home": [3, 5]},
    },
    "p2_offset_v1": {
        "layout_id": "p2_offset_v1",
        "width": 9,
        "height": 6,
        "base_rows": ["#########", "#A......#", "#..F....#", "#....B..#", "#..H....#", "#########"],
        "positions": {"site_a": [1, 1], "fork": [3, 2], "site_b": [5, 3], "home": [3, 4]},
    },
}
_ACTION_POSITION = {
    "approach": "site_b",
    "explore": "fork",
    "forage": "site_a",
    "rest": "home",
    "withdraw": "home",
}
_SITE_ACTION = {"forage": "site_a", "approach": "site_b"}
_POSITION_NAMES = frozenset(_ACTION_POSITION.values())
_GRID_NEIGHBOR_ORDER = ((0, -1), (-1, 0), (1, 0), (0, 1))
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


def validate_layout_topology(layout: Any) -> dict[str, Any]:
    """Validate and describe the public, label-free grid topology.

    Only ``#`` is treated as blocked.  Every other character is walkable; the
    letters drawn in ``base_rows`` are renderer labels and are never inspected
    by reachability or path selection.
    """

    required = {"layout_id", "width", "height", "base_rows", "positions"}
    if not isinstance(layout, Mapping) or set(layout) != required:
        raise ValueError("microworld layout topology schema mismatch")
    layout_id = layout["layout_id"]
    width = layout["width"]
    height = layout["height"]
    rows = layout["base_rows"]
    positions = layout["positions"]
    if type(layout_id) is not str or not layout_id:
        raise ValueError("microworld layout_id must be a non-empty string")
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise ValueError("microworld layout dimensions must be positive integers")
    if (
        not isinstance(rows, list)
        or len(rows) != height
        or any(type(row) is not str or len(row) != width for row in rows)
    ):
        raise ValueError("microworld base_rows must be rectangular and match dimensions")
    if not isinstance(positions, Mapping) or set(positions) != _POSITION_NAMES:
        raise ValueError("microworld semantic positions are not canonical")

    normalized_positions: dict[str, list[int]] = {}
    occupied: set[tuple[int, int]] = set()
    for name in sorted(_POSITION_NAMES):
        coordinate = positions[name]
        if (
            not isinstance(coordinate, list)
            or len(coordinate) != 2
            or any(type(value) is not int for value in coordinate)
        ):
            raise ValueError("microworld position coordinates must be [x,y] integers")
        x, y = coordinate
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError("microworld position coordinate is outside the grid")
        if rows[y][x] == "#":
            raise ValueError("microworld positions must occupy walkable cells")
        if (x, y) in occupied:
            raise ValueError("microworld positions must occupy distinct cells")
        occupied.add((x, y))
        normalized_positions[name] = [x, y]

    walkable_cell_count = sum(character != "#" for row in rows for character in row)
    if walkable_cell_count < len(normalized_positions):
        raise ValueError("microworld layout has too few walkable cells")
    return {
        "schema_version": "ego.life_playground.microworld.grid_topology.v1",
        "producer_function": "ego_life_playground_v0.microworld.validate_layout_topology",
        "layout_id": layout_id,
        "width": width,
        "height": height,
        "blocked_cell_marker": "#",
        "uses_cell_labels": False,
        "neighbor_order": [list(delta) for delta in _GRID_NEIGHBOR_ORDER],
        "walkable_cell_count": walkable_cell_count,
        "positions": normalized_positions,
    }


def _shortest_path_coordinates(
    layout: Mapping[str, Any], start: tuple[int, int], target: tuple[int, int]
) -> list[list[int]] | None:
    rows = layout["base_rows"]
    width = int(layout["width"])
    height = int(layout["height"])
    parents: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    pending: deque[tuple[int, int]] = deque([start])
    while pending:
        current = pending.popleft()
        if current == target:
            break
        for dx, dy in _GRID_NEIGHBOR_ORDER:
            neighbor = (current[0] + dx, current[1] + dy)
            x, y = neighbor
            if (
                neighbor in parents
                or not (0 <= x < width and 0 <= y < height)
                or rows[y][x] == "#"
            ):
                continue
            parents[neighbor] = current
            pending.append(neighbor)
    if target not in parents:
        return None
    reversed_path: list[tuple[int, int]] = []
    cursor: tuple[int, int] | None = target
    while cursor is not None:
        reversed_path.append(cursor)
        cursor = parents[cursor]
    return [[x, y] for x, y in reversed(reversed_path)]


def canonical_public_action_path(
    layout: Mapping[str, Any], agent_position: str, action: str
) -> dict[str, Any]:
    """Return a path from public layout/position bytes, with no private world read."""

    if type(action) is not str or action not in _ACTION_POSITION:
        raise ValueError(f"unknown microworld action: {action!r}")
    topology = validate_layout_topology(layout)
    if type(agent_position) is not str or agent_position not in topology["positions"]:
        raise ValueError("microworld agent_position is not a public semantic position")
    from_position = agent_position
    target_position = _ACTION_POSITION[action]
    from_coordinate = tuple(topology["positions"][from_position])
    target_coordinate = tuple(topology["positions"][target_position])
    coordinates = _shortest_path_coordinates(
        layout, from_coordinate, target_coordinate
    )
    reachable = coordinates is not None
    shortest_path_steps = None if coordinates is None else len(coordinates) - 1
    normalized_cost = (
        None
        if shortest_path_steps is None
        else round(shortest_path_steps / topology["walkable_cell_count"], 9)
    )
    return {
        "schema_version": "ego.life_playground.microworld.action_path.v1",
        "producer_function": "ego_life_playground_v0.microworld.canonical_public_action_path",
        "layout_id": topology["layout_id"],
        "action": action,
        "from_position": from_position,
        "target_position": target_position,
        "from_coordinate": list(from_coordinate),
        "target_coordinate": list(target_coordinate),
        "neighbor_order": deepcopy(topology["neighbor_order"]),
        "reachable": reachable,
        "shortest_path_coordinates": [] if coordinates is None else coordinates,
        "shortest_path_steps": shortest_path_steps,
        "walkable_cell_count": topology["walkable_cell_count"],
        "normalized_topology_cost": normalized_cost,
    }


def canonical_action_path(world: Mapping[str, Any], action: str) -> dict[str, Any]:
    """Validate canonical world bytes, then delegate to the public-only helper."""

    verify_world_state(world)
    return canonical_public_action_path(
        world["layout"], str(world["agent"]["position"]), action
    )


def _public_observation(
    event: str,
    agent_position: str,
    *,
    layout_id: str,
    revealed_outcome: float | None = None,
) -> dict[str, Any]:
    event_object = _EVENT_OBJECT[event]
    return {
        "schema_version": PUBLIC_OBSERVATION_SCHEMA_VERSION,
        "event": event,
        "cue": cue_for_event(event),
        "summary": _EVENT_SUMMARY[event],
        "layout_id": layout_id,
        "agent_position": agent_position,
        "visible_object_ids": [event_object["object_id"]],
        "revealed_outcome": revealed_outcome,
    }


def initial_world_state(*, seed: int = 17, layout_id: str = "p0_cross_v1") -> dict[str, Any]:
    if type(seed) is not int:
        raise ValueError("microworld seed must be an integer")
    if type(layout_id) is not str or layout_id not in LAYOUTS:
        raise ValueError(f"unknown microworld layout: {layout_id!r}")
    validate_layout_topology(LAYOUTS[layout_id])
    event = "quiet_interval"
    rng_state = int(hashlib.sha256(f"microworld|{seed}".encode("utf-8")).hexdigest()[:15], 16)
    return {
        "schema_version": WORLD_STATE_SCHEMA_VERSION,
        "layout": deepcopy(LAYOUTS[layout_id]),
        "agent": {"agent_id": "ego-local", "position": "home"},
        "objects": [deepcopy(_EVENT_OBJECT[event])],
        "public_observation": _public_observation(event, "home", layout_id=layout_id),
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
    layout_id = layout.get("layout_id") if isinstance(layout, Mapping) else None
    expected_layout = LAYOUTS.get(layout_id)
    if expected_layout is None or dict(layout) != expected_layout:
        raise ValueError("microworld layout is not canonical")
    validate_layout_topology(layout)
    agent = world["agent"]
    if not isinstance(agent, Mapping) or set(agent) != {"agent_id", "position"}:
        raise ValueError("microworld agent schema mismatch")
    if agent["agent_id"] != "ego-local" or agent["position"] not in layout["positions"]:
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
        "layout_id",
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
        str(event),
        str(agent["position"]),
        layout_id=str(layout_id),
        revealed_outcome=revealed,
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
        event,
        str(observed["agent"]["position"]),
        layout_id=str(observed["layout"]["layout_id"]),
        revealed_outcome=None,
    )
    verify_world_state(observed)
    return observed


def legal_action_gate(
    world: Mapping[str, Any], actions: Sequence[str]
) -> dict[str, Any]:
    """Gate actions whose public-grid target has no canonical BFS path."""

    verify_world_state(world)
    canonical = list(actions)
    if not canonical or any(type(action) is not str or action not in _ACTION_POSITION for action in canonical):
        raise ValueError("microworld action set is not canonical")
    if len(canonical) != len(set(canonical)):
        raise ValueError("microworld action set contains duplicates")
    action_paths = {action: canonical_action_path(world, action) for action in canonical}
    legal_actions = [action for action in canonical if action_paths[action]["reachable"]]
    gated_actions = [action for action in canonical if not action_paths[action]["reachable"]]
    return {
        "rule": "label_free_grid_topology_reachability_v1",
        "legal_actions": legal_actions,
        "gated_actions": gated_actions,
        "action_paths": action_paths,
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
    path = canonical_action_path(world, selected_action)
    if not path["reachable"]:
        raise ValueError(f"microworld action target is unreachable: {selected_action!r}")
    transitioned = deepcopy(dict(world))
    from_position = str(transitioned["agent"]["position"])
    to_position = str(path["target_position"])
    moved = from_position != to_position
    visited_site = _SITE_ACTION.get(selected_action) if moved else None
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
    food_obtained = bool(
        selected_action == "forage"
        and moved
        and visited_site == "site_a"
        and outcome == 1.0
    )
    observation["revealed_outcome"] = outcome
    transitioned["public_observation"] = observation
    verify_world_state(transitioned)
    return transitioned, {
        "producer_function": "ego_life_playground_v0.microworld.transition_world",
        "selected_action": selected_action,
        "from_position": from_position,
        "to_position": to_position,
        "moved": moved,
        "path": path,
        "visited_site": visited_site,
        "outcome": outcome,
        "food_obtained": food_obtained,
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
    "LAYOUTS",
    "PUBLIC_FRAME_SCHEMA_VERSION",
    "PUBLIC_OBSERVATION_SCHEMA_VERSION",
    "WORLD_STATE_SCHEMA_VERSION",
    "canonical_action_path",
    "canonical_public_action_path",
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
    "validate_layout_topology",
    "verify_world_state",
    "world_hash",
]
