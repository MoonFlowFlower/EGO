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
    build_subject_state_mutation_proposal_v0,
    decide_subject_state_mutation_v0,
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
from .developmental_shadow import (
    DevelopmentalShadowProposal,
    FeedbackLinkedOutcomeObservation,
    FeedbackPolicyPatchAdmissionRecord,
    FeedbackUpdateCandidate,
    PredictionCalibrationCandidate,
    PredictionRecord,
    build_developmental_shadow_proposal,
    build_feedback_linked_outcome_observation,
    build_feedback_policy_patch_admission_record,
    build_feedback_update_candidate,
    build_prediction_calibration_candidate,
    build_prediction_record,
    validate_feedback_linked_outcome_observation,
    validate_feedback_policy_patch_admission_record,
    validate_feedback_update_candidate,
    validate_prediction_calibration_boundary,
    validate_shadow_proposal_boundary,
)

__all__ = [
    "DevelopmentalShadowProposal",
    "FeedbackLinkedOutcomeObservation",
    "FeedbackPolicyPatchAdmissionRecord",
    "FeedbackUpdateCandidate",
    "InitiativeProposal",
    "PredictionCalibrationCandidate",
    "PredictionRecord",
    "apply_quiet_mode_to_budget",
    "build_developmental_shadow_proposal",
    "build_feedback_linked_outcome_observation",
    "build_feedback_policy_patch_admission_record",
    "build_feedback_update_candidate",
    "SubjectContextSnapshot",
    "build_outcome_predictions_v0",
    "build_initiative_proposal",
    "build_minimal_subject_context",
    "build_prediction_calibration_candidate",
    "build_prediction_record",
    "build_subject_state_v0",
    "build_subject_state_mutation_proposal_v0",
    "decide_subject_state_mutation_v0",
    "derive_bounded_initiative_signal",
    "derive_quiet_mode",
    "extract_viability_state_v0",
    "evaluate_initiative_explanation",
    "format_initiative_consent_text",
    "validate_prediction_calibration_boundary",
    "validate_feedback_linked_outcome_observation",
    "validate_feedback_policy_patch_admission_record",
    "validate_feedback_update_candidate",
    "validate_shadow_proposal_boundary",
    "validate_initiative_proposal",
]
