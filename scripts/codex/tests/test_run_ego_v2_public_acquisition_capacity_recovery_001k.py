from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.codex.run_ego_v2_public_acquisition_capacity_recovery_001k import (
    CANDIDATE_CONFIGS,
    TASK_ID,
    CandidateReference,
    audit_predecessor_call_chain,
    build_candidate_freeze,
    evaluate_search_stage,
    load_packet_assignments,
    run_formal_packet,
    scan_candidate_input,
)


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = ROOT / "artifacts" / TASK_ID


def test_packet_assignments_were_frozen_before_candidate_source() -> None:
    commitments = json.loads(
        (ARTIFACT_ROOT / "packet_commitments.json").read_text(encoding="utf-8")
    )
    assert commitments["created_before_candidate_source"] is True
    assert commitments["original_001j_heldout_executed"] is False

    seen_seeds: set[int] = set()
    seen_mappings: set[tuple[tuple[str, str], ...]] = set()
    for packet_name in ("search_dev", "qualification", "replication"):
        path = ARTIFACT_ROOT / f"{packet_name}_assignments.json"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == commitments["packets"][
            packet_name
        ]["assignment_sha256"]
        specs = load_packet_assignments(ROOT, packet_name)
        assert len(specs) == 16
        assert not ({int(spec["world_seed"]) for spec in specs} & seen_seeds)
        seen_seeds.update(int(spec["world_seed"]) for spec in specs)
        signatures = {
            tuple(sorted(dict(spec["mapping_commitment"]).items())) for spec in specs
        }
        assert len(signatures) == 4
        assert not (signatures & seen_mappings)
        seen_mappings.update(signatures)


def test_predecessor_call_chain_audit_proves_update_planner_action_wiring() -> None:
    report = audit_predecessor_call_chain(ROOT)

    assert report["passed"] is True
    assert report["predecessor_hashes_match"] is True
    assert report["stored_row_diagnostics"]["public_rows"] == 1536
    assert report["stored_row_diagnostics"]["successful_interactions"] == 64
    assert report["stored_row_diagnostics"]["turn_fraction"] > 0.90
    assert report["synthetic_state_intervention"]["state_changed_on_update"] is True
    assert report["synthetic_state_intervention"]["planner_read_changed_action"] is True
    assert report["ast_call_order"]["plan_before_transition_before_update"] is True
    assert report["original_001j_heldout_reexecuted"] is False


def _payload_with_token(*, token: str, relative_x: int, relative_y: int) -> dict:
    visual = [["empty"] * 5 for _ in range(5)]
    visual[2][2] = "self"
    visual[relative_y + 2][relative_x + 2] = token
    return {
        "observation": {
            "schema_version": "ego.life_playground.microworld.observation.v4",
            "visual": visual,
        },
        "organism": {"energy": 0.30, "safety": 0.62},
        "last_action": None,
        "last_delta": {"energy": 0.0, "safety": 0.0},
    }


def test_candidate_boundary_rejects_identity_private_pose_and_future_fields() -> None:
    payload = _payload_with_token(token="v1", relative_x=0, relative_y=-1)
    assert scan_candidate_input(payload)["clean"] is True

    for forbidden in (
        "world_id",
        "seed",
        "layout_id",
        "token_mapping",
        "private_pose",
        "oracle_action",
        "split",
        "future",
    ):
        contaminated = dict(payload)
        contaminated[forbidden] = "forbidden"
        report = scan_candidate_input(contaminated)
        assert report["clean"] is False
        assert any(item["field"] == forbidden for item in report["findings"])


def test_geometry_only_candidate_repairs_front_diagonal_turn_oscillation() -> None:
    payload = _payload_with_token(token="v1", relative_x=-1, relative_y=-1)
    legacy = CandidateReference(CANDIDATE_CONFIGS["S1_FULL_HISTORY"])
    geometry = CandidateReference(CANDIDATE_CONFIGS["S3_FORWARD_GEOMETRY"])

    legacy_action, legacy_receipt = legacy.plan(payload, sequence=1)
    geometry_action, geometry_receipt = geometry.plan(payload, sequence=1)

    assert legacy_action == "turn_left"
    assert legacy_receipt["selection_reason"] == "orient_visible_token_x_first"
    assert geometry_action == "move_forward"
    assert geometry_receipt["selection_reason"] == "approach_front_half_token"
    assert geometry_receipt["ranked_tokens"][0]["token"] == "v1"


def test_public_update_is_observation_conditioned_and_changes_effect_sign() -> None:
    reference = CandidateReference(CANDIDATE_CONFIGS["S3_DEFICIT_RANKING"])
    payload = _payload_with_token(token="v3", relative_x=0, relative_y=-1)
    reference.plan(payload, sequence=1)
    before = reference.effect_sign_predictions()
    receipt = reference.update_after_public_transition(
        observed_token="v3",
        selected_action="interact",
        observed_outcome_type="interacted",
        actual_delta={"energy": 0.262, "safety": 0.0},
    )
    after = reference.effect_sign_predictions()

    assert before["v3"] is None
    assert after["v3"] == {"energy": 1, "safety": 0}
    assert receipt["updated_token"] == "v3"
    assert "cause" not in json.dumps(receipt)

    with pytest.raises(ValueError, match="public update"):
        reference.update_after_public_transition(
            observed_token="v3",
            selected_action="interact",
            observed_outcome_type="interacted",
            actual_delta={"energy": 0.1, "safety": 0.0, "cause": "resource"},
        )


def test_tiny_search_stage_uses_real_world_outcome_and_metabolism(tmp_path: Path) -> None:
    result = evaluate_search_stage(
        ROOT,
        "S1_OBSERVABILITY",
        output_root=tmp_path,
        test_only=True,
    )

    assert result["stage_id"] == "S1_OBSERVABILITY"
    assert len(result["candidates"]) == 4
    assert all(candidate["executed_world_count"] == 2 for candidate in result["candidates"])
    assert all(
        candidate["invocation_counts"]
        == {
            "transition_world": 24,
            "compute_actual_delta": 24,
            "compute_metabolism_ledger": 24,
        }
        for candidate in result["candidates"]
    )
    assert result["original_001j_packet_executed"] is False
    assert (tmp_path / "search_results.json").is_file()
    assert (tmp_path / "search_rows.jsonl").is_file()


def test_candidate_freeze_and_formal_packet_are_single_write(tmp_path: Path) -> None:
    freeze_path = tmp_path / "candidate_freeze.json"
    freeze = build_candidate_freeze(
        ROOT,
        "S2_RISK_INFORMATION_GAIN",
        output_path=freeze_path,
    )
    assert freeze["formal_action_budget"] == 96
    assert freeze["thresholds"]["m1_recovery_fraction_minimum"] == 0.50
    assert freeze["thresholds"]["m1_world_directions_minimum"] == 12

    formal_root = tmp_path / "formal"
    result = run_formal_packet(
        ROOT,
        "qualification",
        output_root=formal_root,
        freeze_path=freeze_path,
        test_only=True,
    )
    assert result["test_only"] is True
    assert result["executed_world_count"] == 2
    assert result["trajectory_count_by_arm"] == 2
    assert result["original_001j_packet_executed"] is False
    assert len(result["ablations"]) == 3
    assert all(row["match"] for row in result["replay_checks"])

    with pytest.raises(RuntimeError, match="single-use"):
        run_formal_packet(
            ROOT,
            "qualification",
            output_root=formal_root,
            freeze_path=freeze_path,
            test_only=True,
        )
