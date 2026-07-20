from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from labs.ego_life_playground_v0 import microworld


def _forward_position(world):
    x, y = world["agent"]["position"]
    dx, dy = microworld.FACING_DELTAS[world["agent"]["facing"]]
    return [x + dx, y + dy]


def _first_free_cell(world, reserved):
    for cell in microworld.validate_layout_topology(world["layout"])["walkable_cells"]:
        if cell not in reserved:
            return list(cell)
    raise AssertionError("expected a free cell")


def _place_remaining_objects(world, reserved, fixed_causes=()):
    for cause in sorted(world["objects_by_cause"]):
        if cause in fixed_causes:
            continue
        world["objects_by_cause"][cause]["position"] = _first_free_cell(world, reserved)
        reserved.append(world["objects_by_cause"][cause]["position"])


def test_visual_life_world_schema_and_mapping_are_stable_across_lives():
    world_l1 = microworld.initial_world_state(seed=17, layout_id="p0_cross_v1", life_index=1)
    world_l3 = microworld.initial_world_state(seed=17, layout_id="p0_cross_v1", life_index=3)

    microworld.verify_world_state(world_l1)
    microworld.verify_world_state(world_l3)

    assert microworld.WORLD_STATE_SCHEMA_VERSION.endswith(".v4")
    assert microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION.endswith(".v4")
    assert microworld.PUBLIC_FRAME_SCHEMA_VERSION.endswith(".v5")
    assert world_l1["trial"]["token_mapping"] == world_l3["trial"]["token_mapping"]
    assert sorted(world_l1["trial"]["token_mapping"]) == ["v0", "v1", "v2", "v3", "v4"]
    assert sorted(world_l1["objects_by_cause"]) == [
        "novelty",
        "resource",
        "shelter",
        "social",
        "threat",
    ]
    assert sorted(world_l1["layout"]) == ["base_rows", "height", "layout_id", "width"]
    assert all(set(row) <= {"#", "."} for row in world_l1["layout"]["base_rows"])
    assert "positions" not in world_l1["layout"]
    assert "site" not in str(world_l1["layout"]).lower()
    assert "home" not in str(world_l1["layout"]).lower()
    assert "fork" not in str(world_l1["layout"]).lower()
    topology = microworld.validate_layout_topology(world_l1["layout"])
    assert "positions" not in topology


def test_life_reset_changes_positions_but_preserves_trial_mapping():
    world_l1 = microworld.initial_world_state(seed=21, layout_id="p2_vertical_v1", life_index=1)
    world_l2 = microworld.initial_world_state(seed=21, layout_id="p2_vertical_v1", life_index=2)

    placements_l1 = {cause: item["position"] for cause, item in world_l1["objects_by_cause"].items()}
    placements_l2 = {cause: item["position"] for cause, item in world_l2["objects_by_cause"].items()}

    assert world_l1["trial"]["token_mapping"] == world_l2["trial"]["token_mapping"]
    assert placements_l1 != placements_l2
    assert world_l1["agent"]["position"] != world_l2["agent"]["position"]

    reset = microworld.reset_world_for_life(world_l1, 2)
    assert reset == world_l2


def test_policy_observation_is_visual_only_and_deterministic():
    world = microworld.initial_world_state(seed=9, layout_id="p2_offset_v1", life_index=1)
    observed = microworld.public_world_projection(world)
    observed_again = microworld.public_world_projection(world)

    assert observed == observed_again
    assert sorted(observed) == ["observation", "schema_version", "world"]
    assert sorted(observed["world"]) == ["agent", "layout", "schema_version", "visible_objects"]
    assert sorted(observed["observation"]) == ["schema_version", "visual"]
    assert len(observed["observation"]["visual"]) == 5
    assert all(len(row) == 5 for row in observed["observation"]["visual"])

    allowed = {"self", "empty", "wall", "occluded", "v0", "v1", "v2", "v3", "v4"}
    flat = {token for row in observed["observation"]["visual"] for token in row}
    assert flat <= allowed
    assert observed["observation"]["visual"][2][2] == "self"
    assert set(observed["observation"]) == {"schema_version", "visual"}
    assert "trial" not in observed["world"]
    assert "objects_by_cause" not in observed["world"]
    assert "resource" not in str(observed["world"]).lower()
    assert "social" not in str(observed["world"]).lower()
    assert "site" not in str(observed["world"]).lower()
    assert "home" not in str(observed["world"]).lower()
    assert "fork" not in str(observed["world"]).lower()


@pytest.mark.parametrize(
    ("blocker_kind", "target_kind"),
    (("object", "object"), ("object", "empty"), ("wall", "wall")),
)
def test_no_occlusion_ablation_reveals_actual_cell_behind_blocker(blocker_kind, target_kind):
    world = microworld.initial_world_state(seed=3, layout_id="p0_cross_v1", life_index=1)
    fixed_causes = set()

    if blocker_kind == "object":
        world["agent"]["position"] = [4, 3]
        world["agent"]["facing"] = "N"
        world["objects_by_cause"]["resource"]["position"] = [4, 2]
        fixed_causes.add("resource")
        expected_target = "empty"
        if target_kind == "object":
            world["objects_by_cause"]["social"]["position"] = [4, 1]
            fixed_causes.add("social")
            expected_target = world["objects_by_cause"]["social"]["token"]
        reserved = [[4, 3], [4, 2], [4, 1]]
    else:
        world["agent"]["position"] = [1, 2]
        world["agent"]["facing"] = "W"
        expected_target = "wall"
        reserved = [[1, 2]]

    _place_remaining_objects(world, reserved, fixed_causes)
    before = deepcopy(world)

    canonical = microworld.policy_observation(world)
    no_occlusion = microworld.policy_observation(world, occlusion=False)

    assert canonical["schema_version"] == microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION
    assert canonical["visual"][0][2] == "occluded"
    assert no_occlusion["visual"][0][2] == expected_target
    assert no_occlusion["visual"][2][2] == "self"
    assert microworld.public_world_projection(world)["observation"] == canonical
    assert world == before


def test_turn_rest_and_move_forward_outcomes_cover_wall_and_object_blocks():
    world = microworld.initial_world_state(seed=12, layout_id="p2_vertical_v1", life_index=1)
    world["agent"]["facing"] = "N"
    turned_left, left = microworld.transition_world(world, "turn_left")
    turned_right, right = microworld.transition_world(world, "turn_right")
    rested, rest = microworld.transition_world(world, "rest")

    assert turned_left["agent"]["facing"] == "W"
    assert left == {"outcome_type": "turned", "direction": "left"}
    assert turned_right["agent"]["facing"] == "E"
    assert right == {"outcome_type": "turned", "direction": "right"}
    assert rested == world
    assert rest == {"outcome_type": "rested"}

    world = microworld.initial_world_state(seed=12, layout_id="p0_cross_v1", life_index=1)
    world["agent"]["position"] = [1, 1]
    world["agent"]["facing"] = "W"
    stayed, blocked = microworld.transition_world(world, "move_forward")
    assert stayed["agent"]["position"] == [1, 1]
    assert blocked["outcome_type"] == "blocked"
    assert blocked["blocked_by"] == "wall"

    world = microworld.initial_world_state(seed=12, layout_id="p2_vertical_v1", life_index=1)
    world["agent"]["position"] = [3, 3]
    world["agent"]["facing"] = "N"
    front = _forward_position(world)
    target_cause = "resource"
    before_spawn = world["objects_by_cause"][target_cause]["spawn_count"]
    world["objects_by_cause"][target_cause]["position"] = front
    reserved = [world["agent"]["position"], front]
    for cause, item in world["objects_by_cause"].items():
        if cause == target_cause:
            continue
        if item["position"] in reserved:
            item["position"] = _first_free_cell(world, reserved)
            reserved.append(item["position"])
    stayed, blocked = microworld.transition_world(world, "move_forward")
    assert stayed["agent"]["position"] == [3, 3]
    assert blocked == {"outcome_type": "blocked", "blocked_by": "object"}


def test_interact_respawn_includes_just_vacated_forward_cell():
    world = microworld.initial_world_state(seed=12, layout_id="p2_vertical_v1", life_index=1)
    world["agent"]["position"] = [3, 3]
    world["agent"]["facing"] = "N"
    front = _forward_position(world)
    target_cause = "resource"
    before_spawn = world["objects_by_cause"][target_cause]["spawn_count"]
    world["objects_by_cause"][target_cause]["position"] = front
    reserved = [world["agent"]["position"], front]
    for cause, item in world["objects_by_cause"].items():
        if cause == target_cause:
            continue
        if item["position"] in reserved:
            item["position"] = _first_free_cell(world, reserved)
            reserved.append(item["position"])
    after, interacted = microworld.transition_world(world, "interact")
    assert interacted["outcome_type"] == "interacted"
    assert interacted["cause"] == target_cause
    assert after["objects_by_cause"][target_cause]["spawn_count"] == before_spawn + 1
    assert after["objects_by_cause"][target_cause]["position"] in microworld.validate_layout_topology(
        world["layout"]
    )["walkable_cells"]


def test_operator_injection_and_public_frame_keep_policy_observer_split():
    world = microworld.initial_world_state(seed=5, layout_id="p2_offset_v1", life_index=1)
    before = deepcopy(world["objects_by_cause"]["threat"])
    injected = microworld.apply_operator_injection(world, "threat_nearby")
    after = injected["objects_by_cause"]["threat"]

    assert after["injection_count"] == before["injection_count"] + 1
    assert after["position"] != before["position"]
    observation = microworld.public_world_projection(injected)["observation"]
    assert set(observation) == {"schema_version", "visual"}
    assert "threat" not in str(observation).lower()

    state = {
        "world": injected,
        "clock": {"global_tick": 0},
        "organism": {"energy": 0.45},
        "current_goal": {"status": "explore"},
        "last_action": None,
    }
    frame = microworld.make_public_frame(state)
    assert frame["schema_version"] == microworld.PUBLIC_FRAME_SCHEMA_VERSION
    assert "objects_by_cause" in frame["world"]
    assert "trial" in frame["world"]
    assert "observation" in frame
    assert sorted(frame["observation"]) == ["schema_version", "visual"]


def test_verify_world_state_rejects_tampered_mapping_and_hashes_are_stable():
    world = microworld.initial_world_state(seed=8, layout_id="p0_cross_v1", life_index=1)
    observation = microworld.public_world_projection(world)["observation"]

    assert microworld.world_hash(world) == microworld.world_hash(deepcopy(world))
    assert microworld.public_world_hash(world) == microworld.public_world_hash(deepcopy(world))
    assert microworld.observation_hash(observation) == microworld.observation_hash(deepcopy(observation))

    tampered = deepcopy(world)
    tampered["objects_by_cause"]["resource"]["token"] = "v9"
    with pytest.raises(ValueError):
        microworld.verify_world_state(tampered)
