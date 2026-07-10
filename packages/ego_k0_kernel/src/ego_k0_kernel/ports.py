"""No-authority ports for persistence, policy injection, and trace output."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Sequence, runtime_checkable

from .contracts import (
    ActionProposal,
    AdapterCapabilityManifest,
    CapabilityDeniedError,
    CheckpointRecord,
    ContractValidationError,
    EventRecord,
    KernelStateRecord,
    ObservationRecord,
)

if TYPE_CHECKING:
    from .trace import TraceRow


REQUIRED_DENIED_CAPABILITIES = frozenset(
    {
        "execute_action",
        "send_user_message",
        "write_mainline_memory",
        "invoke_gate_or_approval",
        "network_or_transport",
        "schedule_background_work",
        "start_runtime",
        "select_or_rescore_action",
        "change_claim_or_verdict",
        "read_family_or_split_identity",
    }
)
KNOWN_ALLOWED_CAPABILITIES = frozenset(
    {"append_events", "read_events", "write_checkpoint", "read_latest_checkpoint"}
)
KNOWN_READABLE_FIELDS = frozenset({"events", "checkpoints"})
KNOWN_WRITABLE_PORTS = frozenset({"append_events", "write_checkpoint"})


@runtime_checkable
class EventStorePort(Protocol):
    def append_events(
        self, expected_sequence: int, events: Sequence[EventRecord]
    ) -> int: ...

    def read_events(self, episode_id: str, after_sequence: int) -> tuple[EventRecord, ...]: ...

    def write_checkpoint(
        self, expected_sequence: int, checkpoint: CheckpointRecord
    ) -> str: ...

    def read_latest_checkpoint(self, episode_id: str) -> CheckpointRecord | None: ...


@runtime_checkable
class PolicyPort(Protocol):
    def propose(
        self, state: KernelStateRecord, observation: ObservationRecord
    ) -> ActionProposal: ...


@runtime_checkable
class TraceSinkPort(Protocol):
    def append(self, row: "TraceRow") -> None: ...


def validate_adapter_manifest(
    manifest: AdapterCapabilityManifest,
) -> AdapterCapabilityManifest:
    if set(manifest.forbidden_capabilities) != REQUIRED_DENIED_CAPABILITIES:
        missing = sorted(REQUIRED_DENIED_CAPABILITIES - set(manifest.forbidden_capabilities))
        extra = sorted(set(manifest.forbidden_capabilities) - REQUIRED_DENIED_CAPABILITIES)
        raise ContractValidationError(
            f"adapter deny-list mismatch; missing={missing}, unknown={extra}"
        )
    unknown_reads = set(manifest.readable_fields) - KNOWN_READABLE_FIELDS
    unknown_writes = set(manifest.writable_ports) - KNOWN_WRITABLE_PORTS
    if unknown_reads or unknown_writes:
        raise CapabilityDeniedError(
            f"unknown adapter surface; readable={sorted(unknown_reads)}, "
            f"writable={sorted(unknown_writes)}"
        )
    return manifest


def assert_capability_allowed(
    manifest: AdapterCapabilityManifest, capability: str
) -> None:
    validate_adapter_manifest(manifest)
    if capability in REQUIRED_DENIED_CAPABILITIES:
        raise CapabilityDeniedError(f"capability {capability!r} is explicitly denied")
    if capability not in KNOWN_ALLOWED_CAPABILITIES:
        raise CapabilityDeniedError(f"capability {capability!r} is unknown")
    if capability in KNOWN_WRITABLE_PORTS and capability not in manifest.writable_ports:
        raise CapabilityDeniedError(f"capability {capability!r} is not declared writable")
