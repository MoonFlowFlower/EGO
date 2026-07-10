"""Typed, immutable records and canonical JSON primitives for the K0 foundation."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, ClassVar, Mapping, Sequence


class ContractValidationError(ValueError):
    """A record violates the public foundation contract."""


class SchemaVersionError(ContractValidationError):
    """A serialized record uses an unsupported schema."""


class HashMismatchError(ContractValidationError):
    """Canonical bytes do not match the hash carried by a record."""


class CapabilityDeniedError(ContractValidationError):
    """An adapter capability is denied or unknown."""


FOUNDATION_CODE_CONTRACT_VERSION = (
    "ego_k0.kernel_adapter.v1+ego_k0.trace_replay.v1"
)
FORBIDDEN_KERNEL_INPUT_KEYS = frozenset(
    {
        "family_id",
        "split_id",
        "split_identity",
        "sequence_position",
        "heldout_label",
        "evaluator_verdict",
    }
)


def _validate_json(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractValidationError(f"non-finite number at {path}")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractValidationError(f"non-string object key at {path}")
            _validate_json(item, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_json(item, f"{path}[{index}]")
        return
    raise ContractValidationError(
        f"unsupported canonical JSON value {type(value).__name__} at {path}"
    )


def freeze_json(value: Any) -> Any:
    """Validate and recursively freeze JSON-compatible data."""

    _validate_json(value)
    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(item) for item in value)
    return value


def thaw_json(value: Any) -> Any:
    """Return a byte-independent mutable JSON tree."""

    if isinstance(value, Mapping):
        return {key: thaw_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw_json(item) for item in value]
    return value


def find_forbidden_input_keys(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in FORBIDDEN_KERNEL_INPUT_KEYS:
                findings.append(f"{path}.{key}")
            findings.extend(find_forbidden_input_keys(item, f"{path}.{key}"))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            findings.extend(find_forbidden_input_keys(item, f"{path}[{index}]"))
    return findings


def reject_forbidden_input_keys(value: Any, *, label: str) -> None:
    findings = find_forbidden_input_keys(value, label)
    if findings:
        raise ContractValidationError(f"forbidden kernel inputs: {findings}")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize using the contract's explicit UTF-8 canonical byte form."""

    if hasattr(value, "to_dict"):
        value = value.to_dict()
    mutable = thaw_json(value)
    _validate_json(mutable)
    text = json.dumps(
        mutable,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return text.encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def stable_id(prefix: str, value: Any) -> str:
    _require_identifier(prefix, "id prefix")
    return f"{prefix}_{canonical_hash(value)[:24]}"


def _require_identifier(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{label} must be a non-empty string")


def _require_step(value: int, label: str, *, minimum: int = 0) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractValidationError(f"{label} must be an integer >= {minimum}")


def _require_schema(data: Mapping[str, Any], expected: str) -> None:
    actual = data.get("schema_version")
    if actual != expected:
        raise SchemaVersionError(f"expected schema {expected!r}, got {actual!r}")


def _require_exact_keys(data: Mapping[str, Any], expected: set[str]) -> None:
    actual = set(data)
    if actual != expected:
        raise ContractValidationError(
            f"record keys mismatch; missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )


def _hash_record_body(body: Mapping[str, Any]) -> str:
    return canonical_hash(body)


@dataclass(frozen=True, slots=True)
class ObservationRecord:
    observation_id: str
    episode_id: str
    step_id: int
    payload: Mapping[str, Any]
    source_refs: Sequence[str] = ()
    schema_version: str = field(init=False, default="ego_k0.observation.v1")

    SCHEMA_VERSION: ClassVar[str] = "ego_k0.observation.v1"

    def __post_init__(self) -> None:
        _require_identifier(self.observation_id, "observation_id")
        _require_identifier(self.episode_id, "episode_id")
        _require_step(self.step_id, "step_id", minimum=1)
        reject_forbidden_input_keys(self.payload, label="observation.payload")
        object.__setattr__(self, "payload", freeze_json(self.payload))
        refs = tuple(self.source_refs)
        for ref in refs:
            _require_identifier(ref, "source_ref")
        object.__setattr__(self, "source_refs", refs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "observation_id": self.observation_id,
            "episode_id": self.episode_id,
            "step_id": self.step_id,
            "payload": thaw_json(self.payload),
            "source_refs": list(self.source_refs),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ObservationRecord":
        _require_schema(data, cls.SCHEMA_VERSION)
        _require_exact_keys(
            data,
            {
                "schema_version",
                "observation_id",
                "episode_id",
                "step_id",
                "payload",
                "source_refs",
            },
        )
        return cls(
            observation_id=data["observation_id"],
            episode_id=data["episode_id"],
            step_id=data["step_id"],
            payload=data["payload"],
            source_refs=data.get("source_refs", ()),
        )


@dataclass(frozen=True, slots=True)
class EventRecord:
    event_id: str
    episode_id: str
    step_id: int
    sequence: int
    event_type: str
    payload: Mapping[str, Any]
    provenance: Mapping[str, Any]
    event_hash: str = ""
    schema_version: str = field(init=False, default="ego_k0.event.v1")

    SCHEMA_VERSION: ClassVar[str] = "ego_k0.event.v1"

    def __post_init__(self) -> None:
        _require_identifier(self.event_id, "event_id")
        _require_identifier(self.episode_id, "episode_id")
        _require_identifier(self.event_type, "event_type")
        _require_step(self.step_id, "step_id", minimum=1)
        _require_step(self.sequence, "sequence", minimum=1)
        reject_forbidden_input_keys(self.payload, label="event.payload")
        reject_forbidden_input_keys(self.provenance, label="event.provenance")
        object.__setattr__(self, "payload", freeze_json(self.payload))
        object.__setattr__(self, "provenance", freeze_json(self.provenance))
        expected = _hash_record_body(self._body())
        if self.event_hash and self.event_hash != expected:
            raise HashMismatchError(
                f"event {self.event_id!r} hash mismatch: {self.event_hash} != {expected}"
            )
        object.__setattr__(self, "event_hash", expected)

    def _body(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "episode_id": self.episode_id,
            "step_id": self.step_id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "payload": thaw_json(self.payload),
            "provenance": thaw_json(self.provenance),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "event_hash": self.event_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EventRecord":
        _require_schema(data, cls.SCHEMA_VERSION)
        _require_exact_keys(
            data,
            {
                "schema_version",
                "event_id",
                "episode_id",
                "step_id",
                "sequence",
                "event_type",
                "payload",
                "provenance",
                "event_hash",
            },
        )
        return cls(
            event_id=data["event_id"],
            episode_id=data["episode_id"],
            step_id=data["step_id"],
            sequence=data["sequence"],
            event_type=data["event_type"],
            payload=data["payload"],
            provenance=data["provenance"],
            event_hash=data.get("event_hash", ""),
        )


@dataclass(frozen=True, slots=True)
class KernelStateRecord:
    episode_id: str
    step_id: int
    substates: Mapping[str, Any]
    rng_state: Mapping[str, Any]
    state_hash: str = ""
    schema_version: str = field(init=False, default="ego_k0.state.v1")

    SCHEMA_VERSION: ClassVar[str] = "ego_k0.state.v1"

    def __post_init__(self) -> None:
        _require_identifier(self.episode_id, "episode_id")
        _require_step(self.step_id, "step_id")
        reject_forbidden_input_keys(self.substates, label="state.substates")
        reject_forbidden_input_keys(self.rng_state, label="state.rng_state")
        object.__setattr__(self, "substates", freeze_json(self.substates))
        object.__setattr__(self, "rng_state", freeze_json(self.rng_state))
        expected = _hash_record_body(self._body())
        if self.state_hash and self.state_hash != expected:
            raise HashMismatchError(
                f"state hash mismatch: {self.state_hash} != {expected}"
            )
        object.__setattr__(self, "state_hash", expected)

    def _body(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "episode_id": self.episode_id,
            "step_id": self.step_id,
            "substates": thaw_json(self.substates),
            "rng_state": thaw_json(self.rng_state),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "state_hash": self.state_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "KernelStateRecord":
        _require_schema(data, cls.SCHEMA_VERSION)
        _require_exact_keys(
            data,
            {
                "schema_version",
                "episode_id",
                "step_id",
                "substates",
                "rng_state",
                "state_hash",
            },
        )
        return cls(
            episode_id=data["episode_id"],
            step_id=data["step_id"],
            substates=data["substates"],
            rng_state=data["rng_state"],
            state_hash=data.get("state_hash", ""),
        )


@dataclass(frozen=True, slots=True)
class ActionCandidate:
    action_id: str
    typed_parameters: Mapping[str, Any]
    admissible: bool
    constraint_reasons: Sequence[str] = ()
    schema_version: str = field(init=False, default="ego_k0.action_candidate.v1")

    SCHEMA_VERSION: ClassVar[str] = "ego_k0.action_candidate.v1"

    def __post_init__(self) -> None:
        _require_identifier(self.action_id, "action_id")
        if not isinstance(self.admissible, bool):
            raise ContractValidationError("admissible must be boolean")
        reject_forbidden_input_keys(
            self.typed_parameters, label="action_candidate.typed_parameters"
        )
        object.__setattr__(self, "typed_parameters", freeze_json(self.typed_parameters))
        reasons = tuple(self.constraint_reasons)
        for reason in reasons:
            _require_identifier(reason, "constraint_reason")
        object.__setattr__(self, "constraint_reasons", reasons)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "action_id": self.action_id,
            "typed_parameters": thaw_json(self.typed_parameters),
            "admissible": self.admissible,
            "constraint_reasons": list(self.constraint_reasons),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ActionCandidate":
        _require_schema(data, cls.SCHEMA_VERSION)
        _require_exact_keys(
            data,
            {
                "schema_version",
                "action_id",
                "typed_parameters",
                "admissible",
                "constraint_reasons",
            },
        )
        return cls(
            action_id=data["action_id"],
            typed_parameters=data["typed_parameters"],
            admissible=data["admissible"],
            constraint_reasons=data.get("constraint_reasons", ()),
        )


@dataclass(frozen=True, slots=True)
class ActionProposal:
    proposal_id: str
    episode_id: str
    step_id: int
    selected_action_id: str
    candidates: Sequence[ActionCandidate]
    decision_factors: Mapping[str, Any]
    execution_authority: bool = False
    schema_version: str = field(init=False, default="ego_k0.action_proposal.v1")

    SCHEMA_VERSION: ClassVar[str] = "ego_k0.action_proposal.v1"

    def __post_init__(self) -> None:
        _require_identifier(self.proposal_id, "proposal_id")
        _require_identifier(self.episode_id, "episode_id")
        _require_identifier(self.selected_action_id, "selected_action_id")
        _require_step(self.step_id, "step_id", minimum=1)
        candidates = tuple(self.candidates)
        if not candidates:
            raise ContractValidationError("proposal requires at least one candidate")
        if any(not isinstance(item, ActionCandidate) for item in candidates):
            raise ContractValidationError("candidates must be ActionCandidate records")
        ids = [item.action_id for item in candidates]
        if len(ids) != len(set(ids)):
            raise ContractValidationError("candidate action ids must be unique")
        selected = [item for item in candidates if item.action_id == self.selected_action_id]
        if len(selected) != 1 or not selected[0].admissible:
            raise ContractValidationError("selected action must identify one admissible candidate")
        if self.execution_authority is not False:
            raise ContractValidationError("Foundation proposals cannot execute actions")
        reject_forbidden_input_keys(
            self.decision_factors, label="action_proposal.decision_factors"
        )
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "decision_factors", freeze_json(self.decision_factors))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "proposal_id": self.proposal_id,
            "episode_id": self.episode_id,
            "step_id": self.step_id,
            "selected_action_id": self.selected_action_id,
            "candidates": [item.to_dict() for item in self.candidates],
            "decision_factors": thaw_json(self.decision_factors),
            "execution_authority": False,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ActionProposal":
        _require_schema(data, cls.SCHEMA_VERSION)
        _require_exact_keys(
            data,
            {
                "schema_version",
                "proposal_id",
                "episode_id",
                "step_id",
                "selected_action_id",
                "candidates",
                "decision_factors",
                "execution_authority",
            },
        )
        return cls(
            proposal_id=data["proposal_id"],
            episode_id=data["episode_id"],
            step_id=data["step_id"],
            selected_action_id=data["selected_action_id"],
            candidates=tuple(ActionCandidate.from_dict(item) for item in data["candidates"]),
            decision_factors=data["decision_factors"],
            execution_authority=data.get("execution_authority", False),
        )


@dataclass(frozen=True, slots=True)
class CheckpointRecord:
    checkpoint_id: str
    state: KernelStateRecord
    last_event_sequence: int
    code_contract_version: str
    checkpoint_hash: str = ""
    schema_version: str = field(init=False, default="ego_k0.checkpoint.v1")

    SCHEMA_VERSION: ClassVar[str] = "ego_k0.checkpoint.v1"

    def __post_init__(self) -> None:
        _require_identifier(self.checkpoint_id, "checkpoint_id")
        if not isinstance(self.state, KernelStateRecord):
            raise ContractValidationError("checkpoint state must be KernelStateRecord")
        _require_step(self.last_event_sequence, "last_event_sequence")
        _require_identifier(self.code_contract_version, "code_contract_version")
        if self.code_contract_version != FOUNDATION_CODE_CONTRACT_VERSION:
            raise SchemaVersionError(
                "unsupported checkpoint code contract version: "
                f"{self.code_contract_version!r}"
            )
        expected = _hash_record_body(self._body())
        if self.checkpoint_hash and self.checkpoint_hash != expected:
            raise HashMismatchError(
                f"checkpoint hash mismatch: {self.checkpoint_hash} != {expected}"
            )
        object.__setattr__(self, "checkpoint_hash", expected)

    def _body(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "checkpoint_id": self.checkpoint_id,
            "state": self.state.to_dict(),
            "last_event_sequence": self.last_event_sequence,
            "code_contract_version": self.code_contract_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "checkpoint_hash": self.checkpoint_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CheckpointRecord":
        _require_schema(data, cls.SCHEMA_VERSION)
        _require_exact_keys(
            data,
            {
                "schema_version",
                "checkpoint_id",
                "state",
                "last_event_sequence",
                "code_contract_version",
                "checkpoint_hash",
            },
        )
        return cls(
            checkpoint_id=data["checkpoint_id"],
            state=KernelStateRecord.from_dict(data["state"]),
            last_event_sequence=data["last_event_sequence"],
            code_contract_version=data["code_contract_version"],
            checkpoint_hash=data.get("checkpoint_hash", ""),
        )


@dataclass(frozen=True, slots=True)
class AdapterCapabilityManifest:
    adapter_id: str
    readable_fields: Sequence[str]
    writable_ports: Sequence[str]
    forbidden_capabilities: Sequence[str]
    manifest_hash: str = ""
    schema_version: str = field(init=False, default="ego_k0.adapter_capability.v1")

    SCHEMA_VERSION: ClassVar[str] = "ego_k0.adapter_capability.v1"

    def __post_init__(self) -> None:
        _require_identifier(self.adapter_id, "adapter_id")
        for name in ("readable_fields", "writable_ports", "forbidden_capabilities"):
            values = tuple(getattr(self, name))
            if len(values) != len(set(values)):
                raise ContractValidationError(f"{name} must not contain duplicates")
            for value in values:
                _require_identifier(value, name)
            object.__setattr__(self, name, values)
        expected = _hash_record_body(self._body())
        if self.manifest_hash and self.manifest_hash != expected:
            raise HashMismatchError(
                f"adapter manifest hash mismatch: {self.manifest_hash} != {expected}"
            )
        object.__setattr__(self, "manifest_hash", expected)

    def _body(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "readable_fields": list(self.readable_fields),
            "writable_ports": list(self.writable_ports),
            "forbidden_capabilities": list(self.forbidden_capabilities),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "manifest_hash": self.manifest_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AdapterCapabilityManifest":
        _require_schema(data, cls.SCHEMA_VERSION)
        _require_exact_keys(
            data,
            {
                "schema_version",
                "adapter_id",
                "readable_fields",
                "writable_ports",
                "forbidden_capabilities",
                "manifest_hash",
            },
        )
        return cls(
            adapter_id=data["adapter_id"],
            readable_fields=data["readable_fields"],
            writable_ports=data["writable_ports"],
            forbidden_capabilities=data["forbidden_capabilities"],
            manifest_hash=data.get("manifest_hash", ""),
        )
