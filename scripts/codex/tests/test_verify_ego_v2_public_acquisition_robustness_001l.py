from __future__ import annotations

from pathlib import Path

from scripts.codex import verify_ego_v2_public_acquisition_robustness_001l as verifier


ROOT = Path(__file__).resolve().parents[3]


def test_verifier_has_independent_row_and_positive_control_paths() -> None:
    assert verifier.PRODUCER_MODULE_NAME not in verifier.__dict__
    controls = verifier.declared_positive_controls()
    assert set(controls) == {
        "row_value_tamper",
        "stored_aggregate_tamper",
        "assignment_byte_tamper",
        "candidate_private_field_injection",
        "protected_predecessor_tamper",
    }
