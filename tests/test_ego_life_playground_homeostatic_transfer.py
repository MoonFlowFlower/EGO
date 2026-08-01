from __future__ import annotations

from copy import deepcopy

import pytest

from labs.ego_life_playground_v0 import engine, homeostatic_transfer, microworld
from labs.ego_life_playground_v0.controller import PlaygroundController
from labs.ego_life_playground_v0.store import SQLiteEventStore
from labs.ego_life_playground_v0.terminal import (
    TerminalPlayground,
    render_homeostatic_trace_html,
)


def _observation(*, left: str = "v0", right: str = "v1", front: str = "empty") -> dict:
    return {
        "schema_version": microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION,
        "visual": [
            ["empty", "empty", "empty", "empty", "empty"],
            ["empty", "empty", front, "empty", "empty"],
            ["empty", left, "self", right, "empty"],
            ["empty", "empty", "empty", "empty", "empty"],
            ["empty", "empty", "empty", "empty", "empty"],
        ],
    }


def _public_payload(observation: dict, *, energy: float, safety: float) -> dict:
    return {
        "observation": observation,
        "organism": {"energy": energy, "safety": safety},
        "last_action": None,
        "last_delta": {"energy": 0.0, "safety": 0.0},
    }


def _teach_token(state: dict, token: str, energy: float, safety: float) -> dict:
    updated, receipt = homeostatic_transfer.update_after_transition(
        state,
        public_input=_public_payload(
            _observation(front=token), energy=0.5, safety=0.5
        ),
        selected_action="interact",
        observed_outcome_type="interacted",
        actual_delta={"energy": energy, "safety": safety},
        terminal=False,
        updates_enabled=True,
        feedback_mode="canonical",
    )
    assert receipt["applied"] is True
    assert receipt["observed_token"] == token
    return updated


def test_public_input_scanner_rejects_private_fields() -> None:
    clean = _public_payload(_observation(), energy=0.3, safety=0.7)
    assert homeostatic_transfer.scan_public_input(clean)["clean"] is True
    contaminated = {**clean, "world_id": "private"}
    report = homeostatic_transfer.scan_public_input(contaminated)
    assert report["clean"] is False
    assert any(item["field"] == "world_id" for item in report["findings"])


def test_drive_intervention_changes_ranking_without_changing_predictions() -> None:
    state = homeostatic_transfer.empty_state()
    state = _teach_token(state, "v0", 0.24, 0.0)
    state = _teach_token(state, "v1", -0.018, 0.18)
    observation = _observation(left="v0", right="v1")

    energy_plan = homeostatic_transfer.plan_action(
        state,
        public_input=_public_payload(observation, energy=0.20, safety=0.70),
        sequence=3,
        mode="public_bayes",
        drive_mode="canonical",
        action_costs=engine.ACTION_COSTS,
        target_level=engine.TARGET_LEVEL,
    )
    safety_plan = homeostatic_transfer.plan_action(
        state,
        public_input=_public_payload(observation, energy=0.70, safety=0.20),
        sequence=3,
        mode="public_bayes",
        drive_mode="canonical",
        action_costs=engine.ACTION_COSTS,
        target_level=engine.TARGET_LEVEL,
    )

    assert energy_plan["predictions_hash"] == safety_plan["predictions_hash"]
    assert energy_plan["selected_target"] == "v0"
    assert safety_plan["selected_target"] == "v1"
    assert energy_plan["selected_action"] == "turn_left"
    assert safety_plan["selected_action"] == "turn_right"

    drive_off_low_energy = homeostatic_transfer.plan_action(
        state,
        public_input=_public_payload(observation, energy=0.20, safety=0.70),
        sequence=3,
        mode="public_bayes",
        drive_mode="off",
        action_costs=engine.ACTION_COSTS,
        target_level=engine.TARGET_LEVEL,
    )
    drive_off_low_safety = homeostatic_transfer.plan_action(
        state,
        public_input=_public_payload(observation, energy=0.70, safety=0.20),
        sequence=3,
        mode="public_bayes",
        drive_mode="off",
        action_costs=engine.ACTION_COSTS,
        target_level=engine.TARGET_LEVEL,
    )
    assert drive_off_low_energy["selected_target"] == drive_off_low_safety["selected_target"]
    assert drive_off_low_energy["predictions_hash"] == energy_plan["predictions_hash"]


def test_respawn_and_world_reset_have_distinct_fast_slow_semantics() -> None:
    state = _teach_token(homeostatic_transfer.empty_state(), "v0", 0.24, 0.0)
    state["fast_state"]["active_target"] = "v0"
    state["fast_state"]["short_history"] = [{"action": "interact"}]
    slow_hash = homeostatic_transfer.slow_state_hash(state)
    posterior_hash = homeostatic_transfer.posterior_hash(state)

    respawned = homeostatic_transfer.reset_for_respawn(state)
    assert homeostatic_transfer.slow_state_hash(respawned) == slow_hash
    assert homeostatic_transfer.posterior_hash(respawned) == posterior_hash
    assert respawned["fast_state"]["active_target"] is None
    assert respawned["fast_state"]["short_history"] == []

    new_world = homeostatic_transfer.reset_for_world(respawned)
    assert homeostatic_transfer.slow_state_hash(new_world) == slow_hash
    assert new_world["fast_state"]["token_stats"] == {}
    assert new_world["fast_state"]["world_epoch"] == 1


def test_slow_effect_prior_is_used_after_world_reset_and_slow_reset_ablates_it() -> None:
    learned = homeostatic_transfer.empty_state()
    learned = _teach_token(learned, "v0", 0.24, 0.0)
    learned = _teach_token(learned, "v1", -0.018, 0.18)
    learned = _teach_token(learned, "v2", -0.018, -0.18)
    transferred = homeostatic_transfer.reset_for_world(learned)
    payload = _public_payload(
        _observation(left="empty", right="empty", front="v3"),
        energy=0.20,
        safety=0.70,
    )

    transfer_plan = homeostatic_transfer.plan_action(
        transferred,
        public_input=payload,
        sequence=1,
        mode="public_bayes",
        drive_mode="canonical",
        action_costs=engine.ACTION_COSTS,
        target_level=engine.TARGET_LEVEL,
    )
    assert transfer_plan["predictions_by_action"]["interact"]["source"] == (
        "slow_effect_family_prior"
    )
    assert transfer_plan["slow_prior_applied"] is True
    assert transferred["fast_state"]["token_stats"] == {}

    slow_reset = homeostatic_transfer.reset_slow_state(transferred)
    scratch_plan = homeostatic_transfer.plan_action(
        slow_reset,
        public_input=payload,
        sequence=1,
        mode="public_bayes",
        drive_mode="canonical",
        action_costs=engine.ACTION_COSTS,
        target_level=engine.TARGET_LEVEL,
    )
    assert scratch_plan["predictions_by_action"]["interact"]["source"] == (
        "unobserved_public_prior"
    )
    assert scratch_plan["slow_prior_applied"] is False
    assert homeostatic_transfer.fast_state_hash(slow_reset) == (
        homeostatic_transfer.fast_state_hash(transferred)
    )


def test_fast_reset_removes_world_token_belief_but_preserves_slow_structure() -> None:
    learned = _teach_token(homeostatic_transfer.empty_state(), "v0", 0.24, 0.0)
    known_plan = homeostatic_transfer.plan_action(
        learned,
        public_input=_public_payload(
            _observation(left="empty", right="empty", front="v0"),
            energy=0.20,
            safety=0.70,
        ),
        sequence=2,
        mode="public_bayes",
        drive_mode="canonical",
        action_costs=engine.ACTION_COSTS,
        target_level=engine.TARGET_LEVEL,
    )
    reset = homeostatic_transfer.reset_fast_state(learned)
    reset_plan = homeostatic_transfer.plan_action(
        reset,
        public_input=_public_payload(
            _observation(left="empty", right="empty", front="v0"),
            energy=0.20,
            safety=0.70,
        ),
        sequence=2,
        mode="public_bayes",
        drive_mode="canonical",
        action_costs=engine.ACTION_COSTS,
        target_level=engine.TARGET_LEVEL,
    )
    assert known_plan["ranked_tokens"][0]["known"] is True
    assert reset_plan["ranked_tokens"][0]["known"] is False
    assert homeostatic_transfer.slow_state_hash(reset) == (
        homeostatic_transfer.slow_state_hash(learned)
    )


def test_validated_harm_escape_is_connected_to_fast_planner_state() -> None:
    state = _teach_token(homeostatic_transfer.empty_state(), "v0", -0.018, -0.18)
    harmful_payload = _public_payload(
        _observation(left="empty", right="empty", front="v0"),
        energy=0.50,
        safety=0.50,
    )
    trigger = homeostatic_transfer.plan_action(
        state,
        public_input=harmful_payload,
        sequence=2,
        mode="public_bayes",
        drive_mode="canonical",
        action_costs=engine.ACTION_COSTS,
        target_level=engine.TARGET_LEVEL,
    )
    assert trigger["selection_reason"] == "front_token_predicted_risk_or_deficit_harm"
    state, _receipt = homeostatic_transfer.update_after_transition(
        state,
        public_input=harmful_payload,
        selected_action="turn_right",
        observed_outcome_type="rotated",
        actual_delta={"energy": -0.014, "safety": 0.0},
        terminal=False,
        updates_enabled=True,
        feedback_mode="canonical",
    )
    assert state["fast_state"]["escape_steps_remaining"] == 3
    escape = homeostatic_transfer.plan_action(
        state,
        public_input=_public_payload(
            _observation(left="empty", right="empty", front="empty"),
            energy=0.486,
            safety=0.50,
        ),
        sequence=3,
        mode="public_bayes",
        drive_mode="canonical",
        action_costs=engine.ACTION_COSTS,
        target_level=engine.TARGET_LEVEL,
    )
    assert escape["selected_action"] == "move_forward"
    assert escape["selection_reason"] == "public_harm_escape_macro"


def test_engine_mode_is_default_off_and_mutually_exclusive() -> None:
    assert engine.DEFAULT_INTERVENTIONS["homeostatic_transfer_mode"] == "off"
    state = engine.initial_state(run_id="mode-test", seed=17)
    with pytest.raises(engine.EngineInvariantError, match="mutually exclusive"):
        engine.make_command(
            sequence=1,
            trigger_source="headless_acceptance",
            interventions={
                **engine.DEFAULT_INTERVENTIONS,
                "homeostatic_transfer_mode": "public_bayes",
                "predictive_control_mode": "factored_mpc",
            },
            prev_command_hash=None,
        )


def test_planner_update_and_downstream_selection_are_really_connected() -> None:
    state = engine.initial_state(run_id="wiring-test", seed=17)
    interventions = {
        **engine.DEFAULT_INTERVENTIONS,
        "homeostatic_transfer_mode": "public_bayes",
        "vision_mode": "no_occlusion",
    }
    command = engine.make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=interventions,
        prev_command_hash=None,
    )
    result = engine.compute_step(
        state,
        command,
        engine.make_run_metadata("wiring-test", 17),
    )
    trace = result.trace["homeostatic_transfer"]
    assert trace["mode"] == "public_bayes"
    assert trace["plan"]["selected_action"] == result.trace["selected_action"]
    assert trace["plan"]["public_input_clean"] is True
    assert trace["slow_state_hash"] == homeostatic_transfer.slow_state_hash(
        result.next_state["homeostatic_transfer"]
    )
    assert result.trace["survival_learning"]["selection"]["selection_mode"] == (
        "delegated_homeostatic_transfer"
    )


def test_state_tamper_fails_validation() -> None:
    state = engine.initial_state(run_id="tamper-test", seed=17)
    tampered = deepcopy(state)
    tampered["homeostatic_transfer"]["slow_state"]["update_count"] = 1
    command = engine.make_command(
        sequence=1,
        trigger_source="headless_acceptance",
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    with pytest.raises(engine.EngineInvariantError):
        engine.compute_step(
            tampered,
            command,
            engine.make_run_metadata("tamper-test", 17),
        )


def test_terminal_mode_persists_replays_and_renders_real_trace(tmp_path) -> None:
    db_path = tmp_path / "homeostatic.sqlite3"
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(
            store, run_id="homeostatic-terminal", seed=17, world_seed=1701
        )
        terminal = TerminalPlayground(controller)
        enabled = terminal.execute("homeostatic on")
        assert enabled["homeostatic_transfer_mode"] == "public_bayes"
        result = terminal.execute("run 12")
        assert result["status"] == "committed"
        assert controller.state["survival_learner"]["update_count"] == 0
        assert controller.state["predictive_control"]["model"]["update_count"] == 0
        assert controller.state["homeostatic_transfer"]["slow_state"]["update_count"] == 12
        state_hash_before = homeostatic_transfer.state_hash(
            controller.state["homeostatic_transfer"]
        )
        recovered = controller.recover()
        assert homeostatic_transfer.state_hash(
            recovered.state["homeostatic_transfer"]
        ) == state_hash_before
        assert recovered.traces[-1]["homeostatic_transfer"]["plan"][
            "public_input_clean"
        ] is True
        report = render_homeostatic_trace_html(
            recovered, tmp_path / "homeostatic.html"
        )
        html = report.read_text(encoding="utf-8")
        assert "Data source: recovered trace rows" in html
        assert recovered.traces[-1]["trace_hash"] in html
        assert recovered.traces[-1]["selected_action"] in html
