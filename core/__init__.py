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
from .self_model import (
    Identity,
    CapabilityBoundary,
    OwnershipBoundary,
    SelfModel,
    BoundaryType,
    render_self_report,
    validate_self_report,
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
    # Self-Model
    "Identity",
    "CapabilityBoundary",
    "OwnershipBoundary",
    "SelfModel",
    "BoundaryType",
    "render_self_report",
    "validate_self_report",
]
from .episodic_memory import (
    Episode,
    EpisodeStore,
)
__all__.extend(["Episode", "EpisodeStore"])
