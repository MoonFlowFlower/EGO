"""Pure visual microworld helpers for the bounded V2 playground."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping, Sequence


WORLD_STATE_SCHEMA_VERSION = "ego.life_playground.microworld.state.v4"
PUBLIC_OBSERVATION_SCHEMA_VERSION = "ego.life_playground.microworld.observation.v4"
PUBLIC_FRAME_SCHEMA_VERSION = "ego.life_playground.microworld.public_frame.v5"

CAUSES = ("resource", "social", "novelty", "threat", "shelter")
TOKENS = ("v0", "v1", "v2", "v3", "v4")
VISUAL_TOKENS = frozenset({"self", "empty", "wall", "occluded", *TOKENS})
ACTIONS = ("turn_left", "turn_right", "move_forward", "interact", "rest")
FACING_ORDER = ("N", "E", "S", "W")
FACING_DELTAS = {
    "N": (0, -1),
    "E": (1, 0),
    "S": (0, 1),
    "W": (-1, 0),
}
ALLOWED_WORLD_EVENTS = (
    "resource_appears",
    "social_signal",
    "novel_object",
    "threat_nearby",
    "quiet_interval",
)
_EVENT_TO_CAUSE = {
    "resource_appears": "resource",
    "social_signal": "social",
    "novel_object": "novelty",
    "threat_nearby": "threat",
    "quiet_interval": "shelter",
}
_CAUSE_TO_EVENT = {cause: event for event, cause in _EVENT_TO_CAUSE.items()}
_EVENT_TO_CUE = {
    "resource_appears": "resource",
    "social_signal": "contact",
    "novel_object": "novelty",
    "threat_nearby": "threat",
    "quiet_interval": "quiet",
}
_CUE_TO_EVENT = {cue: event for event, cue in _EVENT_TO_CUE.items()}

LAYOUTS: dict[str, dict[str, Any]] = {
    "p0_cross_v1": {
        "layout_id": "p0_cross_v1",
        "width": 9,
        "height": 5,
        "base_rows": ["#########", "#.......#", "#.......#", "#.......#", "#########"],
    },
    "p2_vertical_v1": {
        "layout_id": "p2_vertical_v1",
        "width": 7,
        "height": 7,
        "base_rows": ["#######", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", "#######"],
    },
    "p2_offset_v1": {
        "layout_id": "p2_offset_v1",
        "width": 9,
        "height": 6,
        "base_rows": ["#########", "#.......#", "#.......#", "#.......#", "#.......#", "#########"],
    },
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def resource_instance_id_for_command(source_command_hash: str) -> str:
    if not (
        type(source_command_hash) is str
        and len(source_command_hash) == 64
        and all(character in "0123456789abcdef" for character in source_command_hash)
    ):
        raise ValueError("resource source command hash must be sha256")
    return hashlib.sha256(f"resource_instance|{source_command_hash}".encode("utf-8")).hexdigest()


def cue_for_event(event: str) -> str:
    if type(event) is not str or event not in _EVENT_TO_CUE:
        raise ValueError(f"unknown world event {event!r}; allowed={','.join(ALLOWED_WORLD_EVENTS)}")
    return _EVENT_TO_CUE[event]


def event_for_cue(cue: str) -> str:
    if type(cue) is not str or cue not in _CUE_TO_EVENT:
        raise ValueError(f"unknown public cue: {cue!r}")
    return _CUE_TO_EVENT[cue]


def default_event_for_sequence(sequence: int) -> str:
    if type(sequence) is not int or sequence <= 0:
        raise ValueError("sequence must be a positive integer")
    return ALLOWED_WORLD_EVENTS[(sequence - 1) % len(ALLOWED_WORLD_EVENTS)]


def validate_layout_topology(layout: Any) -> dict[str, Any]:
    required = {"layout_id", "width", "height", "base_rows"}
    if not isinstance(layout, Mapping) or set(layout) != required:
        raise ValueError("microworld layout topology schema mismatch")
    layout_id = layout["layout_id"]
    width = layout["width"]
    height = layout["height"]
    rows = layout["base_rows"]
    if type(layout_id) is not str or layout_id not in LAYOUTS:
        raise ValueError("microworld layout_id must be canonical")
    if dict(layout) != LAYOUTS[layout_id]:
        raise ValueError("microworld layout is not canonical")
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise ValueError("microworld layout dimensions must be positive integers")
    if (
        not isinstance(rows, list)
        or len(rows) != height
        or any(type(row) is not str or len(row) != width for row in rows)
    ):
        raise ValueError("microworld base_rows must be rectangular and match dimensions")
    if any(set(row) - {"#", "."} for row in rows):
        raise ValueError("microworld base_rows must use only '#' and '.'")
    walkable_cells = [
        [x, y]
        for y, row in enumerate(rows)
        for x, character in enumerate(row)
        if character != "#"
    ]
    return {
        "schema_version": "ego.life_playground.microworld.grid_topology.v2",
        "layout_id": layout_id,
        "width": width,
        "height": height,
        "walkable_cell_count": len(walkable_cells),
        "walkable_cells": walkable_cells,
        "uses_cell_labels": False,
    }


def _walkable_cells(layout: Mapping[str, Any]) -> list[list[int]]:
    return validate_layout_topology(layout)["walkable_cells"]


def _sorted_free_cells(
    layout: Mapping[str, Any],
    occupied: Sequence[Sequence[int]],
    exclude: Sequence[int] | None = None,
) -> list[list[int]]:
    occupied_set = {tuple(cell) for cell in occupied}
    excluded = None if exclude is None else tuple(exclude)
    free = []
    for candidate in _walkable_cells(layout):
        candidate_key = tuple(candidate)
        if candidate_key in occupied_set or candidate_key == excluded:
            continue
        free.append(candidate)
    return sorted(free)


def _placement_digest(
    *,
    trial_seed: int,
    namespace: str,
    life_index: int,
    entity_id: str,
    counter: int,
    candidate: Sequence[int],
) -> str:
    payload = {
        "trial_seed": trial_seed,
        "namespace": namespace,
        "life_index": life_index,
        "entity_id": entity_id,
        "spawn_count": counter,
        "candidate": list(candidate),
    }
    return _canonical_hash(payload)


def _select_cell(
    *,
    trial_seed: int,
    namespace: str,
    life_index: int,
    entity_id: str,
    counter: int,
    candidates: Sequence[Sequence[int]],
) -> list[int]:
    if not candidates:
        raise ValueError("microworld requires at least one free candidate cell")
    ranked = sorted(
        (
            _placement_digest(
                trial_seed=trial_seed,
                namespace=namespace,
                life_index=life_index,
                entity_id=entity_id,
                counter=counter,
                candidate=candidate,
            ),
            list(candidate),
        )
        for candidate in candidates
    )
    return ranked[0][1]


def _token_mapping(seed: int) -> dict[str, str]:
    ranking = sorted((_canonical_hash({"seed": seed, "cause": cause}), cause) for cause in CAUSES)
    return {token: cause for token, (_, cause) in zip(TOKENS, ranking)}


def _cause_to_token(seed: int) -> dict[str, str]:
    return {cause: token for token, cause in _token_mapping(seed).items()}


def _initial_agent(layout: Mapping[str, Any], seed: int, life_index: int) -> dict[str, Any]:
    position = _select_cell(
        trial_seed=seed,
        namespace="agent",
        life_index=life_index,
        entity_id="ego-local",
        counter=0,
        candidates=_walkable_cells(layout),
    )
    facing = FACING_ORDER[
        int(_canonical_hash({"seed": seed, "life_index": life_index, "entity_id": "ego-local"})[:8], 16)
        % len(FACING_ORDER)
    ]
    return {"agent_id": "ego-local", "position": position, "facing": facing}


def _initial_objects(layout: Mapping[str, Any], seed: int, life_index: int, agent_position: Sequence[int]) -> dict[str, Any]:
    objects: dict[str, Any] = {}
    occupied = [agent_position]
    cause_tokens = _cause_to_token(seed)
    for cause in CAUSES:
        position = _select_cell(
            trial_seed=seed,
            namespace="spawn",
            life_index=life_index,
            entity_id=cause,
            counter=0,
            candidates=_sorted_free_cells(layout, occupied),
        )
        objects[cause] = {
            "cause": cause,
            "token": cause_tokens[cause],
            "position": position,
            "spawn_count": 0,
            "injection_count": 0,
        }
        occupied.append(position)
    return objects


def _rotate_relative(dx: int, dy: int, facing: str) -> tuple[int, int]:
    if facing == "N":
        return dx, dy
    if facing == "E":
        return -dy, dx
    if facing == "S":
        return -dx, -dy
    return dy, -dx


def _ray_cells(relative_x: int, relative_y: int) -> list[tuple[int, int]]:
    steps = max(abs(relative_x), abs(relative_y))
    if steps == 0:
        return []
    cells: list[tuple[int, int]] = []
    last: tuple[int, int] | None = None
    for index in range(1, steps + 1):
        x = round(relative_x * index / steps)
        y = round(relative_y * index / steps)
        if last != (x, y):
            cells.append((x, y))
            last = (x, y)
    return cells


def _cell_token(world: Mapping[str, Any], absolute_x: int, absolute_y: int) -> str:
    layout = world["layout"]
    rows = layout["base_rows"]
    if not (0 <= absolute_x < layout["width"] and 0 <= absolute_y < layout["height"]):
        return "wall"
    if rows[absolute_y][absolute_x] == "#":
        return "wall"
    for item in world["objects_by_cause"].values():
        if item["position"] == [absolute_x, absolute_y]:
            return item["token"]
    return "empty"


def _public_observation(
    world: Mapping[str, Any], *, occlusion: bool = True
) -> dict[str, Any]:
    agent = world["agent"]
    center_x, center_y = agent["position"]
    facing = agent["facing"]
    visual: list[list[str]] = []
    for row_index in range(5):
        row: list[str] = []
        for column_index in range(5):
            relative_x = column_index - 2
            relative_y = row_index - 2
            if relative_x == 0 and relative_y == 0:
                row.append("self")
                continue
            world_dx, world_dy = _rotate_relative(relative_x, relative_y, facing)
            occluded = False
            if occlusion:
                ray = _ray_cells(world_dx, world_dy)
                for ray_x, ray_y in ray[:-1]:
                    token = _cell_token(world, center_x + ray_x, center_y + ray_y)
                    if token not in {"empty", "self"}:
                        occluded = True
                        break
            row.append("occluded" if occluded else _cell_token(world, center_x + world_dx, center_y + world_dy))
        visual.append(row)
    return {"schema_version": PUBLIC_OBSERVATION_SCHEMA_VERSION, "visual": visual}


def policy_observation(
    world: Mapping[str, Any], *, occlusion: bool = True
) -> dict[str, Any]:
    """Return the validated visual-only policy observation."""

    if type(occlusion) is not bool:
        raise ValueError("occlusion must be a boolean")
    verify_world_state(world)
    return _public_observation(world, occlusion=occlusion)


def initial_world_state(*, seed: int = 17, layout_id: str = "p0_cross_v1", life_index: int = 1) -> dict[str, Any]:
    if type(seed) is not int:
        raise ValueError("microworld seed must be an integer")
    if type(life_index) is not int or life_index <= 0:
        raise ValueError("life_index must be a positive integer")
    if type(layout_id) is not str or layout_id not in LAYOUTS:
        raise ValueError(f"unknown microworld layout: {layout_id!r}")
    layout = deepcopy(LAYOUTS[layout_id])
    agent = _initial_agent(layout, seed, life_index)
    objects = _initial_objects(layout, seed, life_index, agent["position"])
    world = {
        "schema_version": WORLD_STATE_SCHEMA_VERSION,
        "layout": layout,
        "trial": {
            "seed": seed,
            "life_index": life_index,
            "token_mapping": _token_mapping(seed),
        },
        "agent": agent,
        "objects_by_cause": objects,
    }
    verify_world_state(world)
    return world


def reset_world_for_life(world: Mapping[str, Any], life_index: int) -> dict[str, Any]:
    verify_world_state(world)
    return initial_world_state(
        seed=int(world["trial"]["seed"]),
        layout_id=str(world["layout"]["layout_id"]),
        life_index=life_index,
    )


def verify_world_state(world: Any) -> None:
    if not isinstance(world, Mapping) or set(world) != {
        "schema_version",
        "layout",
        "trial",
        "agent",
        "objects_by_cause",
    }:
        raise ValueError("microworld state schema mismatch")
    if world["schema_version"] != WORLD_STATE_SCHEMA_VERSION:
        raise ValueError("microworld state schema_version is not canonical")
    validate_layout_topology(world["layout"])
    trial = world["trial"]
    if not isinstance(trial, Mapping) or set(trial) != {"seed", "life_index", "token_mapping"}:
        raise ValueError("microworld trial schema mismatch")
    if type(trial["seed"]) is not int or type(trial["life_index"]) is not int or trial["life_index"] <= 0:
        raise ValueError("microworld trial values are not canonical")
    if dict(trial["token_mapping"]) != _token_mapping(int(trial["seed"])):
        raise ValueError("microworld token mapping is not canonical")
    agent = world["agent"]
    if not isinstance(agent, Mapping) or set(agent) != {"agent_id", "position", "facing"}:
        raise ValueError("microworld agent schema mismatch")
    if agent["agent_id"] != "ego-local" or agent["facing"] not in FACING_ORDER:
        raise ValueError("microworld agent is not canonical")
    if (
        not isinstance(agent["position"], list)
        or len(agent["position"]) != 2
        or any(type(value) is not int for value in agent["position"])
    ):
        raise ValueError("microworld agent position must be [x,y] integers")
    if agent["position"] not in _walkable_cells(world["layout"]):
        raise ValueError("microworld agent position must be walkable")
    objects = world["objects_by_cause"]
    if not isinstance(objects, Mapping) or sorted(objects) != sorted(CAUSES):
        raise ValueError("microworld objects_by_cause schema mismatch")
    expected_tokens = _cause_to_token(int(trial["seed"]))
    occupied = {tuple(agent["position"])}
    for cause in CAUSES:
        item = objects[cause]
        if not isinstance(item, Mapping) or set(item) != {
            "cause",
            "token",
            "position",
            "spawn_count",
            "injection_count",
        }:
            raise ValueError("microworld object schema mismatch")
        if item["cause"] != cause or item["token"] != expected_tokens[cause]:
            raise ValueError("microworld object metadata is not canonical")
        if (
            not isinstance(item["position"], list)
            or len(item["position"]) != 2
            or any(type(value) is not int for value in item["position"])
            or item["position"] not in _walkable_cells(world["layout"])
        ):
            raise ValueError("microworld object position must be a walkable [x,y] cell")
        position_key = tuple(item["position"])
        if position_key in occupied:
            raise ValueError("microworld positions must be unique")
        occupied.add(position_key)
        if type(item["spawn_count"]) is not int or item["spawn_count"] < 0:
            raise ValueError("microworld spawn_count must be non-negative integer")
        if type(item["injection_count"]) is not int or item["injection_count"] < 0:
            raise ValueError("microworld injection_count must be non-negative integer")
    observation = _public_observation(world)
    if observation["schema_version"] != PUBLIC_OBSERVATION_SCHEMA_VERSION:
        raise ValueError("microworld observation schema mismatch")


def world_hash(world: Mapping[str, Any]) -> str:
    verify_world_state(world)
    return _canonical_hash(world)


def public_world_projection(world: Mapping[str, Any]) -> dict[str, Any]:
    observation = policy_observation(world)
    visible_objects = [
        {"token": item["token"], "position": list(item["position"])}
        for item in sorted(world["objects_by_cause"].values(), key=lambda value: value["token"])
    ]
    return {
        "schema_version": "ego.life_playground.microworld.public_projection.v2",
        "world": {
            "schema_version": WORLD_STATE_SCHEMA_VERSION,
            "layout": deepcopy(world["layout"]),
            "agent": deepcopy(world["agent"]),
            "visible_objects": visible_objects,
        },
        "observation": observation,
    }


def public_world_hash(world: Mapping[str, Any]) -> str:
    return _canonical_hash(public_world_projection(world))


def observation_hash(observation: Mapping[str, Any]) -> str:
    if not isinstance(observation, Mapping) or set(observation) != {"schema_version", "visual"}:
        raise ValueError("microworld observation schema mismatch")
    if observation["schema_version"] != PUBLIC_OBSERVATION_SCHEMA_VERSION:
        raise ValueError("microworld observation schema_version is not canonical")
    visual = observation["visual"]
    if (
        not isinstance(visual, list)
        or len(visual) != 5
        or any(not isinstance(row, list) or len(row) != 5 for row in visual)
        or any(token not in VISUAL_TOKENS for row in visual for token in row)
    ):
        raise ValueError("microworld visual observation is not canonical")
    return _canonical_hash(observation)


def _turn(facing: str, direction: str) -> str:
    index = FACING_ORDER.index(facing)
    return FACING_ORDER[(index + (1 if direction == "right" else -1)) % len(FACING_ORDER)]


def _occupied_positions(world: Mapping[str, Any], *, exclude_cause: str | None = None) -> list[list[int]]:
    occupied = [world["agent"]["position"]]
    for cause, item in world["objects_by_cause"].items():
        if cause == exclude_cause:
            continue
        occupied.append(item["position"])
    return occupied


def _cause_at_position(world: Mapping[str, Any], position: Sequence[int]) -> str | None:
    for cause, item in world["objects_by_cause"].items():
        if item["position"] == list(position):
            return cause
    return None


def _forward_position(world: Mapping[str, Any]) -> list[int]:
    x, y = world["agent"]["position"]
    dx, dy = FACING_DELTAS[world["agent"]["facing"]]
    return [x + dx, y + dy]


def transition_world(
    world: Mapping[str, Any],
    selected_action: str,
    *,
    source_sequence: int | None = None,
    source_episode_id: str | None = None,
    source_command_hash: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _ = (source_sequence, source_episode_id, source_command_hash)
    verify_world_state(world)
    if type(selected_action) is not str or selected_action not in ACTIONS:
        raise ValueError(f"unknown microworld action: {selected_action!r}")
    next_world = deepcopy(dict(world))
    if selected_action == "turn_left":
        next_world["agent"]["facing"] = _turn(next_world["agent"]["facing"], "left")
        verify_world_state(next_world)
        return next_world, {"outcome_type": "turned", "direction": "left"}
    if selected_action == "turn_right":
        next_world["agent"]["facing"] = _turn(next_world["agent"]["facing"], "right")
        verify_world_state(next_world)
        return next_world, {"outcome_type": "turned", "direction": "right"}
    if selected_action == "rest":
        verify_world_state(next_world)
        return next_world, {"outcome_type": "rested"}

    forward = _forward_position(next_world)
    token = _cell_token(next_world, forward[0], forward[1])
    if selected_action == "move_forward":
        if token == "wall":
            return next_world, {"outcome_type": "blocked", "blocked_by": "wall"}
        if token in TOKENS:
            return next_world, {"outcome_type": "blocked", "blocked_by": "object"}
        next_world["agent"]["position"] = forward
        verify_world_state(next_world)
        return next_world, {"outcome_type": "moved"}
    cause = _cause_at_position(next_world, forward)
    if cause is None:
        return next_world, {"outcome_type": "no_object"}
    item = next_world["objects_by_cause"][cause]
    item["spawn_count"] += 1
    item["position"] = _select_cell(
        trial_seed=int(next_world["trial"]["seed"]),
        namespace="spawn",
        life_index=int(next_world["trial"]["life_index"]),
        entity_id=cause,
        counter=int(item["spawn_count"]),
        candidates=_sorted_free_cells(next_world["layout"], _occupied_positions(next_world, exclude_cause=cause)),
    )
    verify_world_state(next_world)
    return next_world, {"outcome_type": "interacted", "cause": cause, "token": item["token"]}


def apply_operator_injection(world: Mapping[str, Any], event: str) -> dict[str, Any]:
    verify_world_state(world)
    if type(event) is not str or event not in ALLOWED_WORLD_EVENTS:
        raise ValueError(f"unknown world event {event!r}; allowed={','.join(ALLOWED_WORLD_EVENTS)}")
    cause = _EVENT_TO_CAUSE[event]
    injected = deepcopy(dict(world))
    item = injected["objects_by_cause"][cause]
    item["injection_count"] += 1
    item["position"] = _select_cell(
        trial_seed=int(injected["trial"]["seed"]),
        namespace="inject",
        life_index=int(injected["trial"]["life_index"]),
        entity_id=cause,
        counter=int(item["injection_count"]),
        candidates=_sorted_free_cells(
            injected["layout"],
            _occupied_positions(injected, exclude_cause=cause),
            exclude=world["objects_by_cause"][cause]["position"],
        ),
    )
    verify_world_state(injected)
    return injected


def observe_world_event(world: Mapping[str, Any], event: str) -> dict[str, Any]:
    return apply_operator_injection(world, event)


def canonical_public_action_path(
    layout: Mapping[str, Any], agent_position: Sequence[int], action: str
) -> dict[str, Any]:
    validate_layout_topology(layout)
    if type(action) is not str or action not in ACTIONS:
        raise ValueError(f"unknown microworld action: {action!r}")
    if (
        not isinstance(agent_position, Sequence)
        or len(agent_position) != 2
        or any(type(value) is not int for value in agent_position)
    ):
        raise ValueError("microworld agent_position must be [x,y] integers")
    return {
        "schema_version": "ego.life_playground.microworld.action_path.v2",
        "layout_id": layout["layout_id"],
        "action": action,
        "agent_position": list(agent_position),
        "path_kind": "visual_local_only",
    }


def canonical_action_path(world: Mapping[str, Any], action: str) -> dict[str, Any]:
    verify_world_state(world)
    return canonical_public_action_path(world["layout"], world["agent"]["position"], action)


def legal_action_gate(world: Mapping[str, Any], actions: Sequence[str]) -> dict[str, Any]:
    verify_world_state(world)
    canonical = list(actions)
    if not canonical or any(type(action) is not str or action not in ACTIONS for action in canonical):
        raise ValueError("microworld action set is not canonical")
    if len(canonical) != len(set(canonical)):
        raise ValueError("microworld action set contains duplicates")
    return {
        "rule": "all_actions_selectable_visual_world_v1",
        "legal_actions": canonical,
        "gated_actions": [],
        "action_paths": {action: canonical_action_path(world, action) for action in canonical},
    }


def oracle_evidence_record(world: Mapping[str, Any]) -> dict[str, Any]:
    verify_world_state(world)
    return {
        "schema_version": "ego.life_playground.microworld.oracle.v2",
        "namespace": "evidence_oracle_only",
        "token_mapping": deepcopy(dict(world["trial"]["token_mapping"])),
        "world_hash": world_hash(world),
    }


def make_public_frame(
    state: Mapping[str, Any], trace: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    _ = trace
    world = state.get("world")
    if not isinstance(world, Mapping):
        raise ValueError("canonical state is missing microworld state")
    verify_world_state(world)
    return {
        "schema_version": PUBLIC_FRAME_SCHEMA_VERSION,
        "world": deepcopy(dict(world)),
        "observation": _public_observation(world),
        "public_world_hash": public_world_hash(world),
        "observation_hash": observation_hash(_public_observation(world)),
        "clock": deepcopy(state.get("clock", {})),
        "organism": deepcopy(state.get("organism", {})),
        "current_goal": deepcopy(state.get("current_goal", {})),
        "last_action": state.get("last_action"),
    }


__all__ = [
    "ALLOWED_WORLD_EVENTS",
    "ACTIONS",
    "FACING_DELTAS",
    "LAYOUTS",
    "PUBLIC_FRAME_SCHEMA_VERSION",
    "PUBLIC_OBSERVATION_SCHEMA_VERSION",
    "WORLD_STATE_SCHEMA_VERSION",
    "apply_operator_injection",
    "canonical_action_path",
    "canonical_public_action_path",
    "cue_for_event",
    "default_event_for_sequence",
    "event_for_cue",
    "initial_world_state",
    "legal_action_gate",
    "make_public_frame",
    "observation_hash",
    "observe_world_event",
    "oracle_evidence_record",
    "policy_observation",
    "public_world_hash",
    "public_world_projection",
    "reset_world_for_life",
    "resource_instance_id_for_command",
    "transition_world",
    "validate_layout_topology",
    "verify_world_state",
    "world_hash",
]
