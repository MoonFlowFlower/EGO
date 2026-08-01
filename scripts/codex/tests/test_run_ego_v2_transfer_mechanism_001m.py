from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from labs.ego_life_playground_v0 import engine, homeostatic_transfer, microworld
from scripts.codex import run_ego_v2_transfer_mechanism_001m as campaign


ROOT = Path(__file__).resolve().parents[3]


def _payload() -> dict:
    visual = [["empty"] * 5 for _ in range(5)]
    visual[2][2] = "self"
    visual[1][2] = "v0"
    return {
        "observation": {
            "schema_version": microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION,
            "visual": visual,
        },
        "organism": {"energy": 0.5, "safety": 0.5},
        "last_action": None,
        "last_delta": {"energy": 0.0, "safety": 0.0},
    }


def test_packets_are_new_dev_only_and_qualification_unconsumed() -> None:
    packets = campaign.load_packets(ROOT)
    assert {name: len(rows) for name, rows in packets.items()} == {
        "mechanism_training": 12,
        "search_dev": 16,
        "qualification": 16,
    }
    ids = [row["opaque_context_id"] for rows in packets.values() for row in rows]
    seeds = [row["world_seed"] for rows in packets.values() for row in rows]
    assert len(ids) == len(set(ids))
    assert len(seeds) == len(set(seeds))
    assert all(row["dev_only"] is True for rows in packets.values() for row in rows)
    commitment = json.loads(
        (campaign.artifact_root(ROOT) / "packet_commitment.json").read_text()
    )
    assert commitment["qualification_consumed"] is False


@pytest.mark.parametrize("candidate_id", campaign.CANDIDATES)
def test_candidate_slow_state_excludes_identity_and_effect_means(candidate_id: str) -> None:
    slow = campaign.neutral_slow_meta(candidate_id)
    encoded = json.dumps(slow, sort_keys=True)
    for forbidden in (
        "world_id",
        "world_seed",
        "layout_id",
        "mapping",
        "token",
        "energy_mean",
        "safety_mean",
        "predicted_delta",
    ):
        assert forbidden not in encoded


def test_public_input_positive_controls_fail_closed() -> None:
    assert campaign.scan_candidate_input(_payload())["clean"] is True
    for field in (
        "world_id",
        "seed",
        "layout_id",
        "token_mapping",
        "private_pose",
        "oracle_action",
        "split",
        "future_outcome",
    ):
        contaminated = deepcopy(_payload())
        contaminated[field] = "private"
        assert campaign.scan_candidate_input(contaminated)["clean"] is False


def test_required_arms_and_gap_checkpoints_are_frozen() -> None:
    assert {
        "TRANSFER",
        "SCRATCH",
        "NO_TRANSFER",
        "SLOW_RESET",
        "FAST_RESET",
        "HISTORY_SHUFFLE",
        "NO_UPDATE",
        "PRIOR_CONTRADICTION",
        "UNCAPPED_TRANSFER",
    }.issubset(campaign.PUBLIC_ARMS)
    assert "LATENT_ALIGNMENT_UPPER_BOUND" in campaign.DIAGNOSTIC_ARMS
    assert campaign.GAP_CHECKPOINTS == (8, 16, 24, 32, 48, 64, 80, 96)


def test_plan_and_update_use_canonical_public_call_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    state = campaign.empty_candidate_state(
        "M1_PERMUTATION_INVARIANT_GRAMMAR",
        campaign.neutral_slow_meta("M1_PERMUTATION_INVARIANT_GRAMMAR"),
    )
    seen = {"plan": 0, "update": 0}
    real_plan = homeostatic_transfer.plan_action
    real_update = homeostatic_transfer.update_after_transition

    def wrapped_plan(*args, **kwargs):
        seen["plan"] += 1
        return real_plan(*args, **kwargs)

    def wrapped_update(*args, **kwargs):
        seen["update"] += 1
        return real_update(*args, **kwargs)

    monkeypatch.setattr(homeostatic_transfer, "plan_action", wrapped_plan)
    monkeypatch.setattr(homeostatic_transfer, "update_after_transition", wrapped_update)
    plan = campaign.plan_action(state, public_input=_payload(), sequence=1)
    updated, receipt = campaign.update_after_transition(
        state,
        public_input=_payload(),
        selected_action=plan["selected_action"],
        observed_outcome_type="interacted",
        actual_delta={"energy": 0.2, "safety": 0.0},
        terminal=False,
        updates_enabled=True,
        feedback_mode="canonical",
    )
    assert seen == {"plan": 1, "update": 1}
    assert plan["public_input_clean"] is True
    assert receipt["public_input_clean"] is True
    assert updated["fast_model"]["slow_state"] == homeostatic_transfer.empty_state()[
        "slow_state"
    ]


def test_history_shuffle_applies_to_candidate_fast_meta_too() -> None:
    state = campaign.empty_candidate_state(
        "M1_PERMUTATION_INVARIANT_GRAMMAR",
        campaign.neutral_slow_meta("M1_PERMUTATION_INVARIANT_GRAMMAR"),
    )
    updated, _ = campaign.update_after_transition(
        state,
        public_input=_payload(),
        selected_action="interact",
        observed_outcome_type="interacted",
        actual_delta={"energy": 0.2, "safety": 0.0},
        terminal=False,
        updates_enabled=True,
        feedback_mode="shuffle",
    )
    assert updated["fast_meta"]["observed_public_entities"] == ["v1"]
    assert "v1" in updated["fast_model"]["fast_state"]["token_stats"]
    assert "v0" not in updated["fast_model"]["fast_state"]["token_stats"]


def test_small_real_trajectory_uses_public_receipts() -> None:
    spec = campaign.load_packets(ROOT)["search_dev"][0]
    trained = campaign.neutral_slow_meta("M1_PERMUTATION_INVARIANT_GRAMMAR")
    result = campaign.run_trajectory(
        spec,
        candidate_id="M1_PERMUTATION_INVARIANT_GRAMMAR",
        arm="SCRATCH",
        trained_meta=trained,
        budget=4,
    )
    assert len(result["rows"]) == 4
    assert all(row["public_input_clean"] for row in result["rows"])
    assert all(row["evaluator_private"] is False for row in result["rows"])
    assert result["final_state_hash"]


def test_latent_alignment_is_evaluator_only_not_candidate_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = campaign.load_packets(ROOT)["search_dev"][0]

    def forbidden_candidate_plan(*args, **kwargs):
        raise AssertionError("latent alignment entered candidate planner")

    monkeypatch.setattr(campaign, "plan_action", forbidden_candidate_plan)
    result = campaign.run_trajectory(
        spec,
        candidate_id="M1_PERMUTATION_INVARIANT_GRAMMAR",
        arm="LATENT_ALIGNMENT_UPPER_BOUND",
        trained_meta=campaign.neutral_slow_meta(
            "M1_PERMUTATION_INVARIANT_GRAMMAR"
        ),
        budget=2,
    )
    assert result["final_state_hash"] is None
    assert all(row["evaluator_private"] for row in result["rows"])
    assert all(row["candidate_state_hash"] is None for row in result["rows"])


def test_product_default_and_frozen_product_gate_remain_unchanged() -> None:
    params = homeostatic_transfer.hyperparameters()
    assert params["default_mode"] == "off"
    assert params["default_posterior_mode"] == "canonical"
    assert params["two_timescale_qualification_consumed"] is False
    assert set(engine.ACTION_COSTS) == set(microworld.ACTIONS)
