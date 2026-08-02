from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from labs.ego_life_playground_v0 import public_featured_transfer as frozen
from labs.ego_life_playground_v0 import public_featured_product_world as world
from scripts.codex.verify_ego_v2_public_featured_product_qualification_001q import (
    _canonical_hash,
    verify_rows,
)


def _rows() -> list[dict[str, object]]:
    state = frozen.new_reference_state()
    environment = world.initial_environment("verifier-test")
    observation = world.public_observation(
        environment,
        {"energy": 0.5, "safety": 0.5, "target": 0.72},
        previous=None,
    )
    plan = frozen.plan_action(state, observation)
    before = frozen.canonical_hash(state)
    _, feedback, _ = world.apply_action(
        environment,
        observation,
        plan["action"],
        private_step_entropy="public-row-test",
    )
    update = frozen.update_after_transition(
        state, observation, plan["action"], feedback
    )
    action = {
        "schema_version": "ego.v2.public_featured_product_public_row.001q.v1",
        "sequence": 1,
        "transition_kind": "action",
        "observation": observation,
        "plan": plan,
        "selected_action": plan["action"],
        "actual_feedback": feedback,
        "update_applied": True,
        "learner_state_hash_before": before,
        "learner_state_hash_after": update["state_hash_after"],
        "slow_state_hash_after": None,
        "fast_state_hash_after": None,
        "posterior_entropy_bits": frozen.posterior_entropy(state),
        "world_switch_count": 0,
        "trace_hash": "1" * 64,
    }
    action["row_hash"] = _canonical_hash(action)
    respawn = {
        "schema_version": "ego.v2.public_featured_product_public_row.001q.v1",
        "sequence": 2,
        "transition_kind": "respawn",
        "observation": None,
        "plan": None,
        "selected_action": None,
        "actual_feedback": None,
        "update_applied": False,
        "learner_state_hash_before": None,
        "learner_state_hash_after": None,
        "slow_state_hash_after": None,
        "fast_state_hash_after": None,
        "posterior_entropy_bits": None,
        "world_switch_count": 1,
        "trace_hash": "2" * 64,
    }
    respawn["row_hash"] = _canonical_hash(respawn)
    return [action, respawn]


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_independent_verifier_recomputes_frozen_reference(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl"
    _write(path, _rows())
    report = verify_rows(path)
    assert report["passed"] is True
    assert report["action_count"] == 1
    assert report["respawn_count"] == 1


def test_independent_verifier_rejects_row_tamper(tmp_path: Path) -> None:
    rows = _rows()
    rows[0]["selected_action"] = "rest"
    path = tmp_path / "tampered.jsonl"
    _write(path, rows)
    report = verify_rows(path)
    assert report["passed"] is False
    assert any("mismatch" in failure for failure in report["failures"])


def test_independent_verifier_rejects_private_field(tmp_path: Path) -> None:
    rows = deepcopy(_rows())
    rows[0]["observation"]["seed"] = 17
    rows[0]["row_hash"] = _canonical_hash(
        {key: value for key, value in rows[0].items() if key != "row_hash"}
    )
    path = tmp_path / "private.jsonl"
    _write(path, rows)
    report = verify_rows(path)
    assert report["passed"] is False
    assert any("private fields" in failure for failure in report["failures"])
