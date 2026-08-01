from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from scripts.codex import run_ego_v2_public_acquisition_robustness_001l as campaign


ROOT = Path(__file__).resolve().parents[3]


def test_packets_are_precommitted_dev_only_and_protected_hashes_match() -> None:
    audit = campaign.audit_frozen_boundaries(ROOT)
    assert audit["protected_predecessors_unchanged"] is True
    assert audit["candidate_source_created_after_packet_commitment"] is True
    assert audit["original_001j_heldout_executed"] is False
    signatures = set()
    for name in campaign.PACKET_NAMES:
        specs = campaign.load_packet_assignments(ROOT, name)
        assert len(specs) == 16
        assert all(spec["opaque_context_id"].startswith(f"001l-{name.replace('_', '-')}") for spec in specs)
        current = {campaign.canonical_json(spec["mapping_commitment"]) for spec in specs}
        assert signatures.isdisjoint(current)
        signatures.update(current)


def test_only_two_substantive_candidates_and_escape_uses_public_state() -> None:
    assert campaign.SUBSTANTIVE_CANDIDATES == (
        "S4_HARM_ESCAPE",
        "S4_UNSEEN_FRONTIER_PRIORITY",
    )
    config = deepcopy(campaign.CANDIDATE_CONFIGS["S4_UNSEEN_FRONTIER_PRIORITY"])
    reference = campaign.RobustCandidateReference(config)
    reference.state["token_stats"]["v0"] = {
        "count": 1,
        "energy_mean": -0.018,
        "safety_mean": -0.18,
    }
    payload = {
        "observation": {
            "schema_version": "ego.life_playground.microworld.observation.v4",
            "visual": [
                ["empty"] * 5,
                ["empty", "empty", "empty", "empty", "empty"],
                ["empty", "v0", "self", "empty", "empty"],
                ["empty"] * 5,
                ["empty"] * 5,
            ],
        },
        "organism": {"energy": 0.5, "safety": 0.5},
        "last_action": "turn_right",
        "last_delta": {"energy": -0.014, "safety": 0.0},
    }
    action, receipt = reference.plan(payload, sequence=7)
    assert action == "move_forward"
    assert receipt["selection_reason"] == "public_frontier_escape_known_harm"
    assert receipt["public_input_fields"] == list(campaign.PUBLIC_INPUT_FIELDS)
    assert campaign.scan_candidate_input(payload)["clean"] is True


def test_candidate_rejects_private_field_positive_control() -> None:
    payload = {
        "observation": {},
        "organism": {"energy": 0.5, "safety": 0.5},
        "last_action": None,
        "last_delta": {"energy": 0.0, "safety": 0.0},
        "world_seed": 70000,
    }
    assert campaign.scan_candidate_input(payload)["clean"] is False
    with pytest.raises(ValueError):
        campaign.RobustCandidateReference(
            campaign.CANDIDATE_CONFIGS["S4_HARM_ESCAPE"]
        ).plan(payload, sequence=1)
