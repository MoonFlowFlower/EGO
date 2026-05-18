"""
Candidate-local primitives for EgoOperator.

These modules intentionally do not import EgoCore, OpenEmotion, or
ego_desktop_lab. They extract contracts and operator-facing behavior only.
"""

from .subject_context import SubjectContextSnapshot, build_minimal_subject_context

__all__ = [
    "SubjectContextSnapshot",
    "build_minimal_subject_context",
]
