from __future__ import annotations

from copy import deepcopy

from scripts.codex import (
    run_ego_v2_public_latent_alignment_identifiability_001n as campaign,
)
from scripts.codex import (
    verify_ego_v2_public_latent_alignment_identifiability_001n as verifier,
)


def test_independent_posterior_recomputation_from_public_rows() -> None:
    rows = campaign.synthetic_recomputation_fixture_rows()
    report = verifier.recompute_rows(rows)
    assert report["passed"] is True
    assert report["trajectory_count"] == 1
    assert report["trajectories"][0]["final_equivalent_mapping_count"] == 24


def test_row_tamper_fails_closed() -> None:
    rows = campaign.synthetic_recomputation_fixture_rows()
    tampered = deepcopy(rows)
    tampered[0]["posterior_entropy_bits"] += 0.25
    report = verifier.recompute_rows(tampered)
    assert report["passed"] is False
    assert any("entropy" in finding or "hash" in finding for finding in report["findings"])


def test_leakage_positive_control_fails_closed() -> None:
    rows = campaign.synthetic_recomputation_fixture_rows()
    leaked = deepcopy(rows)
    leaked[0]["public_input_receipt"]["world_seed"] = 470003
    leaked[0]["trace_hash"] = verifier.canonical_hash(
        {key: value for key, value in leaked[0].items() if key != "trace_hash"}
    )
    report = verifier.recompute_rows(leaked)
    assert report["passed"] is False
    assert any("private_field" in finding for finding in report["findings"])
