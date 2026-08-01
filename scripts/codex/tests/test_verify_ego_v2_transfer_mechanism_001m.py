from __future__ import annotations

import json
from pathlib import Path

from scripts.codex import verify_ego_v2_transfer_mechanism_001m as verifier


def test_recompute_rejects_row_value_tamper(tmp_path: Path) -> None:
    row = {
        "candidate_id": "M1_PERMUTATION_INVARIANT_GRAMMAR",
        "opaque_context_id": "ctx",
        "arm": "TRANSFER",
        "sequence": 1,
        "deficit_loss": 0.25,
        "effect_sign_accuracy": 0.0,
        "public_input_clean": True,
        "evaluator_private": False,
        "prev_trace_hash": None,
    }
    row["trace_hash"] = verifier.canonical_hash(row)
    rows_path = tmp_path / "rows.jsonl"
    rows_path.write_text(json.dumps(row, sort_keys=True) + "\n")
    result = {
        "rows_sha256": verifier.sha256(rows_path),
        "summary": verifier.recompute_summary([row]),
    }
    clean = verifier.verify_rows_payload(result, [row], rows_path)
    assert clean["passed"] is True
    row["deficit_loss"] = 0.5
    tampered = verifier.verify_rows_payload(result, [row], rows_path)
    assert tampered["passed"] is False
    assert "row_hash_mismatch" in " ".join(tampered["findings"])


def test_private_diagnostic_rows_are_excluded_from_gate_recomputation() -> None:
    public = {
        "candidate_id": "M1_PERMUTATION_INVARIANT_GRAMMAR",
        "opaque_context_id": "ctx",
        "arm": "SCRATCH",
        "sequence": 1,
        "deficit_loss": 0.2,
        "effect_sign_accuracy": 1.0,
        "public_input_clean": True,
        "evaluator_private": False,
        "prev_trace_hash": None,
    }
    private = {**public, "arm": "LATENT_ALIGNMENT_UPPER_BOUND", "deficit_loss": 0.0, "evaluator_private": True}
    summary = verifier.recompute_summary([public, private])
    assert "LATENT_ALIGNMENT_UPPER_BOUND" not in summary["arms"]
    assert summary["private_diagnostic_row_count"] == 1
