from __future__ import annotations

from copy import deepcopy

from labs.ego_life_playground_v0 import public_featured_hierarchical as learner
from labs.ego_life_playground_v0 import public_featured_product_world as world
from scripts.codex.run_ego_v2_public_featured_product_qualification_001q import (
    _code_path_tamper_check,
    _drive_intervention,
    _leakage_check,
    _no_update_check,
)


def _trained_public_state() -> dict[str, object]:
    state = learner.new_learner_state()
    environment = world.initial_environment("drive-test")
    organism = {"energy": 0.5, "safety": 0.5, "target": 0.72}
    previous = None
    for step in range(24):
        observation = world.public_observation(
            environment, organism, previous=previous
        )
        plan = learner.plan_action(state, observation)
        environment, feedback, previous = world.apply_action(
            environment,
            observation,
            plan["action"],
            private_step_entropy=f"drive-{step}",
        )
        learner.update_after_transition(
            state, observation, plan["action"], feedback
        )
        organism = {
            "energy": feedback["energy_after"],
            "safety": feedback["safety_after"],
            "target": 0.72,
        }
    return deepcopy(state)


def test_qualification_positive_controls_are_real() -> None:
    assert _no_update_check()["passed"] is True
    assert _leakage_check()["passed"] is True
    assert _code_path_tamper_check()["passed"] is True


def test_drive_intervention_changes_ranking_without_updating_posterior() -> None:
    report = _drive_intervention(_trained_public_state())
    assert report["passed"] is True
    assert report["posterior_unchanged"] is True
    assert (
        report["energy_deficit_plan"]["ranking"]
        != report["safety_deficit_plan"]["ranking"]
    )
