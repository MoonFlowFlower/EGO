from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.codex.check_ego_v2_homeostatic_compositional_transfer_001j_capacity import (
    ACTION_BUDGET,
    PUBLIC_REFERENCE_FIELDS,
    PublicFactorBayes,
    build_world_specs,
    canonical_hash,
    generate_capacity_evidence,
    run_trajectory,
    scan_public_reference_input,
)


def test_factor_grammar_is_complete_compositional_and_balanced() -> None:
    specs = build_world_specs()

    assert len(specs) == 24
    assert len({spec["context_id"] for spec in specs}) == 24
    assert len({spec["world_seed"] for spec in specs}) == 24
    assert sum(spec["split"] == "dev" for spec in specs) == 16
    assert sum(spec["split"] == "heldout" for spec in specs) == 8

    for factor in ("layout_index", "mapping_index", "profile_index"):
        all_levels = {spec[factor] for spec in specs}
        assert {spec[factor] for spec in specs if spec["split"] == "dev"} == all_levels
        assert {spec[factor] for spec in specs if spec["split"] == "heldout"} == all_levels

    for mapping_index in range(4):
        signatures = {
            tuple(sorted(spec["mapping_commitment"].items()))
            for spec in specs
            if spec["mapping_index"] == mapping_index
        }
        assert len(signatures) == 1


def test_public_reference_boundary_rejects_private_identity_and_accepts_exact_schema() -> None:
    payload = {
        "observation": {
            "schema_version": "ego.life_playground.microworld.observation.v4",
            "visual": [["empty"] * 5 for _ in range(5)],
        },
        "organism": {"energy": 0.4, "safety": 0.6},
        "last_action": None,
        "last_delta": {"energy": 0.0, "safety": 0.0},
    }
    payload["observation"]["visual"][2][2] = "self"

    clean = scan_public_reference_input(payload)
    assert set(payload) == set(PUBLIC_REFERENCE_FIELDS)
    assert clean["clean"] is True
    assert clean["input_hash"] == canonical_hash(payload)

    for forbidden in ("seed", "world_id", "layout_id", "cause", "token_mapping", "oracle_action"):
        contaminated = dict(payload)
        contaminated[forbidden] = "private"
        report = scan_public_reference_input(contaminated)
        assert report["clean"] is False
        assert any(item["field"] == forbidden for item in report["findings"])


def test_public_factor_bayes_updates_only_from_observed_transition() -> None:
    learner = PublicFactorBayes.empty()
    observation = {
        "schema_version": "ego.life_playground.microworld.observation.v4",
        "visual": [["empty"] * 5 for _ in range(5)],
    }
    observation["visual"][2][2] = "self"
    observation["visual"][1][2] = "v3"
    payload = {
        "observation": observation,
        "organism": {"energy": 0.3, "safety": 0.6},
        "last_action": None,
        "last_delta": {"energy": 0.0, "safety": 0.0},
    }

    action, receipt = learner.plan(payload, sequence=1)
    assert action == "interact"
    assert receipt["public_input_hash"] == canonical_hash(payload)
    assert learner.state["token_stats"] == {}

    before = canonical_hash(learner.state)
    update = learner.update(
        token="v3",
        action="interact",
        actual_delta={"energy": 0.25, "safety": -0.1},
    )
    assert update["state_hash_before"] == before
    assert learner.state["token_stats"]["v3"] == {
        "count": 1,
        "energy_mean": 0.25,
        "safety_mean": -0.1,
    }

    with pytest.raises(ValueError, match="actual_delta"):
        learner.update(
            token="v3",
            action="interact",
            actual_delta={"energy": 0.1, "safety": 0.0, "cause": "resource"},
        )


def test_capacity_trajectory_uses_real_transition_and_metabolism_and_replays() -> None:
    spec = next(spec for spec in build_world_specs() if spec["split"] == "dev")
    trajectory = run_trajectory(spec, "PUBLIC_FACTOR_BAYES", budget=12, policy_seed=7)
    replayed = run_trajectory(spec, "PUBLIC_FACTOR_BAYES", budget=12, policy_seed=7)

    assert trajectory["action_count"] == 12
    assert trajectory["invocation_counts"] == {
        "transition_world": 12,
        "compute_actual_delta": 12,
        "compute_metabolism_ledger": 12,
    }
    assert trajectory["trace_chain_hash"] == replayed["trace_chain_hash"]
    assert trajectory["rows"] == replayed["rows"]
    assert all(row["public_input_clean"] for row in trajectory["rows"])
    assert all(row["metabolism_producer"].endswith("compute_metabolism_ledger") for row in trajectory["rows"])


def test_test_packet_writes_complete_negative_evidence_without_heldout(tmp_path: Path) -> None:
    result = generate_capacity_evidence(tmp_path, test_only=True)

    assert result["task_id"] == "EGO-V2-HOMEOSTATIC-COMPOSITIONAL-TRANSFER-001J"
    assert result["formal_action_budget"] == ACTION_BUDGET
    assert result["heldout_executed"] is False
    assert result["verdict"] in {
        "BENCHMARK_CAPACITY_ESTABLISHED",
        "BENCHMARK_CAPACITY_NOT_ESTABLISHED",
    }
    required = {
        "capacity_result.json",
        "capacity_rows.jsonl",
        "capacity_replay_report.json",
        "leakage_report.json",
        "artifact_manifest.json",
    }
    assert required <= {path.name for path in tmp_path.iterdir()}
    if result["verdict"] != "BENCHMARK_CAPACITY_ESTABLISHED":
        assert (tmp_path / "failure_manifest.json").exists()

    manifest = json.loads((tmp_path / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert manifest["heldout_artifact_count"] == 0
    assert manifest["all_hashes_match"] is True
