from __future__ import annotations

from pathlib import Path

from labs.ego_life_playground_v0 import homeostatic_transfer
from scripts.codex import run_ego_v2_homeostatic_survival_loop_001l as campaign


ROOT = Path(__file__).resolve().parents[3]


def test_product_packets_are_committed_new_dev_only_worlds() -> None:
    packets = campaign.load_packets(ROOT)
    assert {name: len(rows) for name, rows in packets.items()} == {
        "structure_training": 8,
        "search_dev": 8,
        "qualification": 16,
    }
    ids = [row["opaque_context_id"] for values in packets.values() for row in values]
    assert len(ids) == len(set(ids))
    assert all(not value.startswith("001j-") for value in ids)


def test_product_trajectory_uses_clean_public_input_and_hash_chain() -> None:
    spec = campaign.load_packets(ROOT)["search_dev"][0]
    trajectory = campaign.run_trajectory(
        spec,
        arm="SCRATCH",
        trained_state=homeostatic_transfer.empty_state(),
        budget=8,
    )
    assert len(trajectory["rows"]) == 8
    previous = None
    for row in trajectory["rows"]:
        assert row["public_input_clean"] is True
        assert row["prev_trace_hash"] == previous
        unhashed = {key: value for key, value in row.items() if key != "trace_hash"}
        assert row["trace_hash"] == campaign.canonical_hash(unhashed)
        previous = row["trace_hash"]


def test_wrong_prior_is_explicit_valid_slow_state_intervention() -> None:
    state = homeostatic_transfer.empty_state()
    packet = campaign.load_packets(ROOT)["search_dev"][0]
    trained = campaign.run_trajectory(
        packet,
        arm="TRANSFER",
        trained_state=state,
        budget=32,
    )["state"]
    assert trained is not None
    wrong = campaign.invert_slow_prior(trained)
    homeostatic_transfer.validate_state(wrong)
    assert homeostatic_transfer.fast_state_hash(wrong) == (
        homeostatic_transfer.fast_state_hash(trained)
    )
