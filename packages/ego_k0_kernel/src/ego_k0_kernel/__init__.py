"""Default-off K0 Foundation contracts; importing this package has no effects."""

from .contracts import (
    ActionCandidate,
    ActionProposal,
    AdapterCapabilityManifest,
    CapabilityDeniedError,
    CheckpointRecord,
    ContractValidationError,
    EventRecord,
    FOUNDATION_CODE_CONTRACT_VERSION,
    HashMismatchError,
    KernelStateRecord,
    ObservationRecord,
    SchemaVersionError,
    canonical_hash,
    canonical_json_bytes,
    stable_id,
)
from .ports import EventStorePort, PolicyPort, TraceSinkPort
from .replay import (
    ReplayMismatch,
    ReplayResult,
    StepComputation,
    compute_step,
    execute_observation,
    replay_from_checkpoint,
)
from .state import apply_observation, initial_state
from .trace import TraceRow

__all__ = [
    "ActionCandidate",
    "ActionProposal",
    "AdapterCapabilityManifest",
    "CapabilityDeniedError",
    "CheckpointRecord",
    "ContractValidationError",
    "EventRecord",
    "EventStorePort",
    "FOUNDATION_CODE_CONTRACT_VERSION",
    "HashMismatchError",
    "KernelStateRecord",
    "ObservationRecord",
    "PolicyPort",
    "ReplayMismatch",
    "ReplayResult",
    "SchemaVersionError",
    "StepComputation",
    "TraceRow",
    "TraceSinkPort",
    "apply_observation",
    "canonical_hash",
    "canonical_json_bytes",
    "compute_step",
    "execute_observation",
    "initial_state",
    "replay_from_checkpoint",
    "stable_id",
]
