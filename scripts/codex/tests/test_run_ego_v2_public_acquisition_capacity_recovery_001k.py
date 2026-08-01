from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.codex.run_ego_v2_public_acquisition_capacity_recovery_001k import (
    TASK_ID,
    audit_predecessor_call_chain,
    load_packet_assignments,
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
