from __future__ import annotations

from scripts.codex.score_mvs_replay_validator import _canonical_trace, _trace_replayable


def test_canonical_trace_accepts_v2_surface_with_cycles_delta() -> None:
    step = {
        "policy_hint": {"mvs_boundary_guard": "low_boundary_confidence"},
        "trace_payload": {
            "event_id": "evt_001",
            "perceived": {"boundary_state": "boundary_touched"},
            "drives_delta": {"viability_pressure": 0.53},
            "self_model_delta": {"current_mode": "repair"},
            "identity_delta": {"identity_conflict": 0.0},
            "cycles_delta": {
                "closure_signature": "sig_001",
                "closure_family_id": "fam_001",
                "action_signature": "tool:file",
                "outcome_signature": "blocked",
                "closure_consistency_score": 0.75,
                "repair_closure": True,
            },
            "predicted_outcome": 0.55,
            "actual_outcome": "blocked",
            "adjustment_applied": "repair_and_request_replan",
            "next_guard": "request_replan",
            "replay_variant_id": "mvs_candidate_aligned_compact",
        },
    }

    canonical = _canonical_trace(step)

    assert canonical["appraisal_delta"]["viability_pressure"] == 0.53
    assert canonical["cycle_delta"]["repair_closure"] is True
    assert canonical["closure_signature"] == "sig_001"
    assert canonical["action_signature"] == "tool:file"
    assert _trace_replayable(step, require_corrective_fields=True) is True
