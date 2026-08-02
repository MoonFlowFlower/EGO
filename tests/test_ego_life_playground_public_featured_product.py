from __future__ import annotations

from copy import deepcopy
import importlib
import json
from pathlib import Path

import pytest

from labs.ego_life_playground_v0 import engine
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import SQLiteEventStore
from labs.ego_life_playground_v0.terminal import (
    build_terminal_snapshot,
    render_homeostatic_trace_html,
)


PROFILE = "public_featured_hierarchical_transfer"
MODE = "hierarchical_bayes"


def _learner():
    return importlib.import_module(
        "labs.ego_life_playground_v0.public_featured_hierarchical"
    )


def _world():
    return importlib.import_module(
        "labs.ego_life_playground_v0.public_featured_product_world"
    )


def _observation() -> dict[str, object]:
    return {
        "organism": {"energy": 0.5, "safety": 0.5, "target": 0.72},
        "slots": [
            {"features": [0, 0, 0, 0, 0]},
            {"features": [0, 1, 0, 1, 0]},
            {"features": [1, 0, 1, 0, 1]},
        ],
        "previous": None,
    }


def _featured_interventions(**overrides: str) -> dict[str, str]:
    values = dict(
        engine.DEFAULT_INTERVENTIONS,
        public_featured_transfer_mode=MODE,
    )
    values.update(overrides)
    return values


def test_featured_product_profile_is_explicit_and_default_off() -> None:
    assert engine.DEFAULT_INTERVENTIONS["public_featured_transfer_mode"] == "off"
    normal = engine.initial_state(run_id="normal", seed=7)
    featured = engine.initial_state(
        run_id="featured", seed=7, product_profile=PROFILE
    )
    assert normal["public_featured_transfer"]["active"] is False
    assert featured["public_featured_transfer"]["active"] is True
    assert featured["organism"]["energy"] == 0.5
    assert featured["organism"]["safety"] == 0.5


def test_clean_learner_matches_frozen_public_reference_without_importing_it() -> None:
    learner = _learner()
    frozen = importlib.import_module(
        "labs.ego_life_playground_v0.public_featured_transfer"
    )
    source = Path(learner.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "FEATURE_COMBO_SPLITS",
        "private_aligned",
        "symbolic_capacity_audit",
        "ACTUAL_MECHANISM_INDEX",
        "evaluator_seed",
        "packet_name",
    ):
        assert forbidden not in source
    state = learner.new_learner_state()
    frozen_state = frozen.new_reference_state()
    observation = _observation()
    assert learner.plan_action(state, observation) == frozen.plan_action(
        frozen_state, observation
    )


def test_clean_learner_updates_only_from_public_transition_and_rejects_private_fields() -> None:
    learner = _learner()
    world = _world()
    state = learner.new_learner_state()
    environment = world.initial_environment(731)
    observation = world.public_observation(
        environment,
        {"energy": 0.5, "safety": 0.5, "target": 0.72},
        previous=None,
    )
    action = learner.plan_action(state, observation)["action"]
    _, feedback, _ = world.apply_action(
        environment, observation, action, private_step_entropy="step-1"
    )
    before = learner.state_hash(state)
    receipt = learner.update_after_transition(state, observation, action, feedback)
    assert learner.state_hash(state) != before
    assert state["update_count"] == 1
    assert receipt["public_input_receipt"]
    hostile = deepcopy(observation)
    hostile["seed"] = 731
    with pytest.raises(ValueError, match="private candidate field"):
        learner.plan_action(learner.new_learner_state(), hostile)


def test_world_truth_is_private_but_public_slots_and_feedback_are_complete() -> None:
    world = _world()
    environment = world.initial_environment(991)
    observation = world.public_observation(
        environment,
        {"energy": 0.5, "safety": 0.5, "target": 0.72},
        previous=None,
    )
    encoded = json.dumps(observation, sort_keys=True)
    assert set(observation) == {"organism", "slots", "previous"}
    assert len(observation["slots"]) == 3
    assert all(len(slot["features"]) == 5 for slot in observation["slots"])
    assert "mechanism" not in encoded
    assert "local_mode" not in encoded
    assert "seed" not in encoded
    next_environment, feedback, public_receipt = world.apply_action(
        environment, observation, "interact_0", private_step_entropy="step-1"
    )
    assert next_environment != environment
    assert set(feedback) == {
        "energy_before",
        "safety_before",
        "energy_after",
        "safety_after",
        "died",
    }
    assert "mechanism" not in json.dumps(public_receipt, sort_keys=True)


def test_engine_featured_branch_uses_single_reducer_and_updates_component() -> None:
    state = engine.initial_state(
        run_id="engine-featured", seed=19, product_profile=PROFILE
    )
    run_meta = engine.make_run_metadata(
        "engine-featured", 19, product_profile=PROFILE
    )
    command = engine.make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=_featured_interventions(),
        prev_command_hash=None,
    )
    result = engine.compute_step(state, command, run_meta)
    trace = result.trace
    assert trace["producer_function"] == "ego_life_playground_v0.engine.compute_step"
    assert trace["selected_action"] in {
        "interact_0",
        "interact_1",
        "interact_2",
        "rest",
    }
    assert trace["candidate_actions"] == [
        "interact_0",
        "interact_1",
        "interact_2",
        "rest",
    ]
    featured = trace["public_featured_transfer"]
    assert featured["mode"] == MODE
    assert featured["plan"]["predictions"]
    assert featured["update"]["applied"] is True
    assert featured["slow_state_hash"]
    assert featured["fast_state_hash"]
    assert result.next_state["model"] == state["model"]
    assert result.next_state["memory"] == state["memory"]


def test_featured_profile_is_mutually_exclusive_with_existing_policy_modes() -> None:
    state = engine.initial_state(
        run_id="exclusive", seed=29, product_profile=PROFILE
    )
    run_meta = engine.make_run_metadata("exclusive", 29, product_profile=PROFILE)
    for override in (
        {"homeostatic_transfer_mode": "public_bayes"},
        {"predictive_control_mode": "factored_mpc"},
        {"survival_learning_mode": "expected_sarsa_lambda"},
    ):
        command = engine.make_command(
            sequence=1,
            trigger_source="headless_acceptance",
            interventions=_featured_interventions(**override),
            prev_command_hash=None,
        )
        with pytest.raises(engine.EngineInvariantError, match="mutually exclusive"):
            engine.compute_step(state, command, run_meta)


def test_controller_store_recovery_recomputes_featured_action(tmp_path: Path) -> None:
    db = tmp_path / "featured.sqlite3"
    with SQLiteEventStore(db) as store:
        controller = PlaygroundController(
            store,
            run_id="featured-product",
            seed=43,
            public_featured_transfer=True,
        )
        dispatched = controller.dispatch(
            _featured_interventions(), trigger_source="headless_acceptance"
        )
        assert dispatched.receipt.committed is True
        recovered = controller.recover()
        assert recovered.recovered is True
        assert recovered.traces[-1]["trace_hash"] == controller.last_trace["trace_hash"]
        assert recovered.traces[-1]["public_featured_transfer"]["update"]["applied"] is True
        snapshot = build_terminal_snapshot(controller)
        summary = snapshot["public_featured_summary"]
        assert summary["predictions"]
        assert summary["ranking"][0] == controller.last_trace["selected_action"]
        assert summary["actual_feedback"]
        report = render_homeostatic_trace_html(
            recovered, tmp_path / "featured-trace.html"
        )
        html = report.read_text(encoding="utf-8")
        assert "public_featured_hierarchical_transfer" in html
        assert "trace-data" in html


def test_public_projection_exposes_slots_but_not_private_featured_truth(
    tmp_path: Path,
) -> None:
    from labs.ego_life_playground_v0.controller import public_state_projection

    with SQLiteEventStore(tmp_path / "public.sqlite3") as store:
        controller = PlaygroundController(
            store,
            run_id="featured-public",
            seed=47,
            public_featured_transfer=True,
        )
        projection = public_state_projection(controller.state)
        featured = projection["public_featured_transfer"]
        assert len(featured["observation"]["slots"]) == 3
        encoded = json.dumps(projection, sort_keys=True).lower()
        for forbidden in ("private_entropy", "local_mode", "slot_indices", "seed"):
            assert forbidden not in encoded


def test_featured_world_reset_preserves_slow_and_resets_fast() -> None:
    learner = _learner()
    world = _world()
    state = learner.new_learner_state()
    environment = world.initial_environment(123)
    observation = world.public_observation(
        environment,
        {"energy": 0.5, "safety": 0.5, "target": 0.72},
        previous=None,
    )
    action = learner.plan_action(state, observation)["action"]
    _, feedback, _ = world.apply_action(
        environment, observation, action, private_step_entropy="first"
    )
    learner.update_after_transition(state, observation, action, feedback)
    slow_before = learner.slow_state_hash(state)
    learner.reset_for_world(state)
    assert learner.slow_state_hash(state) == slow_before
    assert state["world_update_count"] == 0
    assert learner.fast_state_hash(state) == learner.fast_state_hash(
        learner.new_learner_state(learner.shared_marginal(state))
    )
