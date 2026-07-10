"""Canonical, append-only trace row schema for Foundation runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar, Mapping, Sequence

from .contracts import (
    ActionCandidate,
    ActionProposal,
    ContractValidationError,
    EventRecord,
    HashMismatchError,
    KernelStateRecord,
    ObservationRecord,
    canonical_hash,
    freeze_json,
    reject_forbidden_input_keys,
    thaw_json,
)
from .events import UPDATE_EVENT_TYPE


TRACE_ROW_KEYS = frozenset(
    {
        "schema_version",
        "task_id",
        "run_id",
        "episode_id",
        "step_id",
        "state_before_hash",
        "observation",
        "observation_source_refs",
        "event_sequence_before",
        "memory_read_refs",
        "action_candidates",
        "prediction",
        "decision_factors",
        "selected_action_proposal",
        "feedback",
        "prediction_error",
        "update_events",
        "replay_batch_refs",
        "state_after_hash",
        "event_sequence_after",
        "component_attribution",
        "seed_context",
        "code_path_hash",
        "contract_hash",
        "trace_hash",
    }
)
ACTION_REMOVED_TRACE_KEYS = TRACE_ROW_KEYS - {
    "action_candidates",
    "selected_action_proposal",
    "trace_hash",
}


@dataclass(frozen=True, slots=True)
class TraceRow:
    task_id: str
    run_id: str
    episode_id: str
    step_id: int
    state_before_hash: str
    observation: Mapping[str, Any]
    observation_source_refs: Sequence[str]
    event_sequence_before: int
    memory_read_refs: Sequence[str]
    action_candidates: Sequence[Mapping[str, Any]]
    prediction: Any
    decision_factors: Mapping[str, Any]
    selected_action_proposal: Mapping[str, Any]
    feedback: Any
    prediction_error: Any
    update_events: Sequence[Mapping[str, Any]]
    replay_batch_refs: Sequence[str]
    state_after_hash: str
    event_sequence_after: int
    component_attribution: Mapping[str, Any]
    seed_context: Mapping[str, Any]
    code_path_hash: str
    contract_hash: str
    trace_hash: str = ""
    schema_version: str = field(init=False, default="ego_k0.trace.v1")

    SCHEMA_VERSION: ClassVar[str] = "ego_k0.trace.v1"

    def __post_init__(self) -> None:
        if (
            isinstance(self.step_id, bool)
            or not isinstance(self.step_id, int)
            or self.step_id < 1
            or isinstance(self.event_sequence_before, bool)
            or not isinstance(self.event_sequence_before, int)
            or self.event_sequence_before < 0
            or isinstance(self.event_sequence_after, bool)
            or not isinstance(self.event_sequence_after, int)
        ):
            raise ContractValidationError("trace step and sequence values are invalid")
        for label, value in (
            ("task_id", self.task_id),
            ("run_id", self.run_id),
            ("episode_id", self.episode_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ContractValidationError(f"trace {label} must be non-empty")
        for label, value in (
            ("state_before_hash", self.state_before_hash),
            ("state_after_hash", self.state_after_hash),
            ("code_path_hash", self.code_path_hash),
            ("contract_hash", self.contract_hash),
        ):
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise ContractValidationError(f"trace {label} must be lowercase sha256")
        if self.event_sequence_after != self.event_sequence_before + 1:
            raise ContractValidationError("trace event sequence must advance exactly once")
        for name in (
            "observation",
            "decision_factors",
            "selected_action_proposal",
            "component_attribution",
            "seed_context",
        ):
            object.__setattr__(self, name, freeze_json(getattr(self, name)))
        for name in ("prediction", "feedback", "prediction_error"):
            object.__setattr__(self, name, freeze_json(getattr(self, name)))
        for name in ("action_candidates", "update_events"):
            object.__setattr__(
                self, name, tuple(freeze_json(item) for item in getattr(self, name))
            )
        for name in ("observation_source_refs", "memory_read_refs", "replay_batch_refs"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        reject_forbidden_input_keys(
            {
                "observation": self.observation,
                "decision_factors": self.decision_factors,
                "selected_action_proposal": self.selected_action_proposal,
                "action_candidates": self.action_candidates,
                "prediction": self.prediction,
                "feedback": self.feedback,
                "prediction_error": self.prediction_error,
                "update_events": self.update_events,
                "component_attribution": self.component_attribution,
                "seed_context": self.seed_context,
            },
            label="trace",
        )
        observation = ObservationRecord.from_dict(self.observation)
        proposal = ActionProposal.from_dict(self.selected_action_proposal)
        candidates = tuple(ActionCandidate.from_dict(item) for item in self.action_candidates)
        update_events = tuple(EventRecord.from_dict(item) for item in self.update_events)
        if observation.episode_id != self.episode_id or observation.step_id != self.step_id:
            raise ContractValidationError("trace observation identity mismatch")
        if tuple(observation.source_refs) != tuple(self.observation_source_refs):
            raise ContractValidationError("trace observation source refs mismatch")
        if proposal.episode_id != self.episode_id or proposal.step_id != self.step_id:
            raise ContractValidationError("trace proposal identity mismatch")
        if [item.to_dict() for item in candidates] != [
            item.to_dict() for item in proposal.candidates
        ]:
            raise ContractValidationError("trace candidates do not match proposal candidates")
        if len(update_events) != 1:
            raise ContractValidationError("Foundation trace requires one derived update event")
        update_event = update_events[0]
        if (
            update_event.event_type != UPDATE_EVENT_TYPE
            or update_event.episode_id != self.episode_id
            or update_event.step_id != self.step_id
            or update_event.sequence != self.event_sequence_after
        ):
            raise ContractValidationError("trace update event identity/schema mismatch")
        if proposal.execution_authority is not False:
            raise ContractValidationError("trace proposal has execution authority")
        expected = canonical_hash(self._body())
        if self.trace_hash and self.trace_hash != expected:
            raise HashMismatchError(
                f"trace hash mismatch: {self.trace_hash} != {expected}"
            )
        object.__setattr__(self, "trace_hash", expected)

    def _body(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "episode_id": self.episode_id,
            "step_id": self.step_id,
            "state_before_hash": self.state_before_hash,
            "observation": thaw_json(self.observation),
            "observation_source_refs": list(self.observation_source_refs),
            "event_sequence_before": self.event_sequence_before,
            "memory_read_refs": list(self.memory_read_refs),
            "action_candidates": [thaw_json(item) for item in self.action_candidates],
            "prediction": thaw_json(self.prediction),
            "decision_factors": thaw_json(self.decision_factors),
            "selected_action_proposal": thaw_json(self.selected_action_proposal),
            "feedback": thaw_json(self.feedback),
            "prediction_error": thaw_json(self.prediction_error),
            "update_events": [thaw_json(item) for item in self.update_events],
            "replay_batch_refs": list(self.replay_batch_refs),
            "state_after_hash": self.state_after_hash,
            "event_sequence_after": self.event_sequence_after,
            "component_attribution": thaw_json(self.component_attribution),
            "seed_context": thaw_json(self.seed_context),
            "code_path_hash": self.code_path_hash,
            "contract_hash": self.contract_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._body(), "trace_hash": self.trace_hash}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TraceRow":
        if data.get("schema_version") != cls.SCHEMA_VERSION:
            raise ContractValidationError("unsupported trace schema")
        if set(data) != TRACE_ROW_KEYS:
            raise ContractValidationError(
                f"trace keys mismatch; missing={sorted(TRACE_ROW_KEYS - set(data))}, "
                f"unknown={sorted(set(data) - TRACE_ROW_KEYS)}"
            )
        values = dict(data)
        values.pop("schema_version", None)
        return cls(**values)


def validate_action_removed_trace(data: Mapping[str, Any]) -> None:
    """Validate the one explicit replay intervention schema with actions removed."""

    if set(data) != ACTION_REMOVED_TRACE_KEYS:
        raise ContractValidationError(
            "action-removed trace keys mismatch; "
            f"missing={sorted(ACTION_REMOVED_TRACE_KEYS - set(data))}, "
            f"unknown={sorted(set(data) - ACTION_REMOVED_TRACE_KEYS)}"
        )
    if data.get("schema_version") != TraceRow.SCHEMA_VERSION:
        raise ContractValidationError("unsupported action-removed trace schema")
    reject_forbidden_input_keys(data, label="action_removed_trace")
    observation = ObservationRecord.from_dict(data["observation"])
    update_events = tuple(EventRecord.from_dict(item) for item in data["update_events"])
    if (
        observation.episode_id != data["episode_id"]
        or observation.step_id != data["step_id"]
        or tuple(observation.source_refs) != tuple(data["observation_source_refs"])
    ):
        raise ContractValidationError("action-removed trace observation identity mismatch")
    if data["event_sequence_after"] != data["event_sequence_before"] + 1:
        raise ContractValidationError("action-removed trace sequence mismatch")
    if len(update_events) != 1:
        raise ContractValidationError("action-removed trace requires one update event")
    update_event = update_events[0]
    if (
        update_event.event_type != UPDATE_EVENT_TYPE
        or update_event.episode_id != data["episode_id"]
        or update_event.step_id != data["step_id"]
        or update_event.sequence != data["event_sequence_after"]
    ):
        raise ContractValidationError("action-removed trace update event mismatch")


def build_trace_row(
    *,
    task_id: str,
    run_id: str,
    state_before: KernelStateRecord,
    observation: ObservationRecord,
    proposal: ActionProposal,
    update_event: EventRecord,
    state_after: KernelStateRecord,
    event_sequence_before: int,
    code_path_hash: str,
    contract_hash: str,
) -> TraceRow:
    return TraceRow(
        task_id=task_id,
        run_id=run_id,
        episode_id=observation.episode_id,
        step_id=observation.step_id,
        state_before_hash=state_before.state_hash,
        observation=observation.to_dict(),
        observation_source_refs=observation.source_refs,
        event_sequence_before=event_sequence_before,
        memory_read_refs=(),
        action_candidates=tuple(item.to_dict() for item in proposal.candidates),
        prediction=None,
        decision_factors=proposal.decision_factors,
        selected_action_proposal=proposal.to_dict(),
        feedback=None,
        prediction_error=None,
        update_events=(update_event.to_dict(),),
        replay_batch_refs=(),
        state_after_hash=state_after.state_hash,
        event_sequence_after=event_sequence_before + 1,
        component_attribution={
            "policy": "caller_injected_policy_port",
            "state_update": "ego_k0_kernel.state.apply_observation",
            "execution_authority": False,
        },
        seed_context=state_before.rng_state,
        code_path_hash=code_path_hash,
        contract_hash=contract_hash,
    )
