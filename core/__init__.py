"""Core modules for OpenEmotion MVP-7."""
from .provenance import (
    Provenance,
    Source,
    sign_payload,
    verify_signature,
    sign_artifact,
    verify_artifact,
    is_internal_source,
    validate_provenance_for_write,
)
from .drive_homeostasis import (
    DriveType,
    DriveRange,
    DriveState,
    drive_error,
    emotion_from_drive,
    modulate_strategy,
    score_rollout_candidate,
)

__all__ = [
    # Provenance
    "Provenance",
    "Source",
    "sign_payload",
    "verify_signature",
    "sign_artifact",
    "verify_artifact",
    "is_internal_source",
    "validate_provenance_for_write",
    # Drive
    "DriveType",
    "DriveRange",
    "DriveState",
    "drive_error",
    "emotion_from_drive",
    "modulate_strategy",
    "score_rollout_candidate",
]
