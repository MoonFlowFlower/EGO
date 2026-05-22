"""
Candidate-local primitives for EgoOperator.

These modules intentionally do not import EgoCore, OpenEmotion, or
ego_desktop_lab. They extract contracts and operator-facing behavior only.
"""

from .subject_context import (
    SubjectContextSnapshot,
    build_outcome_predictions_v0,
    build_minimal_subject_context,
    build_subject_state_v0,
    extract_viability_state_v0,
)
from .initiative import (
    InitiativeProposal,
    apply_quiet_mode_to_budget,
    build_initiative_proposal,
    derive_bounded_initiative_signal,
    derive_quiet_mode,
    evaluate_initiative_explanation,
    format_initiative_consent_text,
    validate_initiative_proposal,
)

__all__ = [
    "InitiativeProposal",
    "apply_quiet_mode_to_budget",
    "SubjectContextSnapshot",
    "build_outcome_predictions_v0",
    "build_initiative_proposal",
    "build_minimal_subject_context",
    "build_subject_state_v0",
    "derive_bounded_initiative_signal",
    "derive_quiet_mode",
    "extract_viability_state_v0",
    "evaluate_initiative_explanation",
    "format_initiative_consent_text",
    "validate_initiative_proposal",
]
