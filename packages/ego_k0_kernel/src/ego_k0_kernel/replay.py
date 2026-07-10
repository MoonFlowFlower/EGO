"""Source execution and replay through one proposal/update computation path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .contracts import (
    ActionProposal,
    CheckpointRecord,
    ContractValidationError,
    EventRecord,
    KernelStateRecord,
    ObservationRecord,
    canonical_hash,
)
from .events import (
    observation_from_event,
    observation_to_event,
    state_transition_event,
    verify_event_sequence,
)
from .ports import EventStorePort, PolicyPort, TraceSinkPort
from .state import apply_observation
from .trace import TraceRow, build_trace_row, validate_action_removed_trace


@dataclass(frozen=True, slots=True)
class StepComputation:
    state_before: KernelStateRecord
    observation: ObservationRecord
    proposal: ActionProposal
    source_event: EventRecord
    update_event: EventRecord
    state_after: KernelStateRecord
    trace_row: TraceRow


@dataclass(frozen=True, slots=True)
class ReplayMismatch:
    step_id: int
    field: str
    expected: Any
    actual: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass(frozen=True, slots=True)
class ReplayResult:
    final_state: KernelStateRecord
    steps: tuple[StepComputation, ...]
    mismatches: tuple[ReplayMismatch, ...]
    producer_function: str
    input_artifact_hashes: Mapping[str, str]
    task_id: str
    run_id: str
    episode_ids: tuple[str, ...]
    context_ids: tuple[str, ...]
    seed_context: Mapping[str, Any]
    aggregation_rule: str
    code_path_hash: str
    contract_hash: str

    @property
    def ok(self) -> bool:
        return not self.mismatches

    def to_report(self) -> dict[str, Any]:
        return {
            "schema_version": "ego_k0.replay_report.v1",
            "producer_function": self.producer_function,
            "input_artifact_hashes": dict(self.input_artifact_hashes),
            "task_id": self.task_id,
            "run_id": self.run_id,
            "episode_ids": list(self.episode_ids),
            "context_ids": list(self.context_ids),
            "seed_context": dict(self.seed_context),
            "aggregation_rule": self.aggregation_rule,
            "code_path_hash": self.code_path_hash,
            "contract_hash": self.contract_hash,
            "ok": self.ok,
            "mismatch_count": len(self.mismatches),
            "mismatches": [item.to_dict() for item in self.mismatches],
            "final_state_hash": self.final_state.state_hash,
            "proposal_hashes": [canonical_hash(item.proposal) for item in self.steps],
            "trace_hashes": [item.trace_row.trace_hash for item in self.steps],
        }


def compute_step(
    *,
    state: KernelStateRecord,
    observation: ObservationRecord,
    policy: PolicyPort,
    sequence: int,
    task_id: str,
    run_id: str,
    code_path_hash: str,
    contract_hash: str,
) -> StepComputation:
    """The only proposal/update path used by source execution and replay."""

    proposal = policy.propose(state, observation)
    if not isinstance(proposal, ActionProposal):
        raise ContractValidationError("PolicyPort must return ActionProposal")
    if proposal.episode_id != observation.episode_id or proposal.step_id != observation.step_id:
        raise ContractValidationError("policy proposal identity does not match observation")
    if proposal.execution_authority is not False:
        raise ContractValidationError("policy proposal cannot have execution authority")

    state_after = apply_observation(state, observation, proposal)
    source_event = observation_to_event(observation, sequence=sequence)
    update_event = state_transition_event(
        state,
        observation,
        proposal,
        state_after,
        sequence=sequence,
    )
    trace_row = build_trace_row(
        task_id=task_id,
        run_id=run_id,
        state_before=state,
        observation=observation,
        proposal=proposal,
        update_event=update_event,
        state_after=state_after,
        event_sequence_before=sequence - 1,
        code_path_hash=code_path_hash,
        contract_hash=contract_hash,
    )
    return StepComputation(
        state_before=state,
        observation=observation,
        proposal=proposal,
        source_event=source_event,
        update_event=update_event,
        state_after=state_after,
        trace_row=trace_row,
    )


def execute_observation(
    *,
    state: KernelStateRecord,
    observation: ObservationRecord,
    policy: PolicyPort,
    event_store: EventStorePort,
    trace_sink: TraceSinkPort,
    expected_sequence: int,
    task_id: str,
    run_id: str,
    code_path_hash: str,
    contract_hash: str,
) -> StepComputation:
    """Compute, transactionally persist the source event, then emit the trace."""

    step = compute_step(
        state=state,
        observation=observation,
        policy=policy,
        sequence=expected_sequence + 1,
        task_id=task_id,
        run_id=run_id,
        code_path_hash=code_path_hash,
        contract_hash=contract_hash,
    )
    committed = event_store.append_events(expected_sequence, (step.source_event,))
    if committed != expected_sequence + 1:
        raise ContractValidationError(
            f"EventStorePort returned sequence {committed}, expected {expected_sequence + 1}"
        )
    trace_sink.append(step.trace_row)
    return step


def _compare_expected_trace(
    expected: Mapping[str, Any], step: StepComputation
) -> list[ReplayMismatch]:
    mismatches: list[ReplayMismatch] = []
    comparisons = {
        "task_id": step.trace_row.task_id,
        "episode_id": step.trace_row.episode_id,
        "step_id": step.trace_row.step_id,
        "state_before_hash": step.state_before.state_hash,
        "observation": step.observation.to_dict(),
        "observation_source_refs": list(step.observation.source_refs),
        "event_sequence_before": step.source_event.sequence - 1,
        "memory_read_refs": [],
        "prediction": None,
        "decision_factors": dict(step.proposal.decision_factors),
        "feedback": None,
        "prediction_error": None,
        "state_after_hash": step.state_after.state_hash,
        "update_events": [step.update_event.to_dict()],
        "replay_batch_refs": [],
        "event_sequence_after": step.source_event.sequence,
        "component_attribution": dict(step.trace_row.component_attribution),
        "seed_context": dict(step.state_before.rng_state),
        "code_path_hash": step.trace_row.code_path_hash,
        "contract_hash": step.trace_row.contract_hash,
    }
    if "selected_action_proposal" in expected:
        comparisons["selected_action_proposal"] = step.proposal.to_dict()
    if "action_candidates" in expected:
        comparisons["action_candidates"] = [
            item.to_dict() for item in step.proposal.candidates
        ]
    for field, actual in comparisons.items():
        expected_value = expected.get(field)
        if expected_value != actual:
            mismatches.append(
                ReplayMismatch(
                    step_id=step.observation.step_id,
                    field=field,
                    expected=expected_value,
                    actual=actual,
                )
            )
    return mismatches


def replay_from_checkpoint(
    *,
    checkpoint: CheckpointRecord,
    events: Sequence[EventRecord],
    policy: PolicyPort,
    task_id: str,
    run_id: str,
    code_path_hash: str,
    contract_hash: str,
    context_ids: Sequence[str] = (),
    expected_traces: Sequence[Mapping[str, Any]] | None = None,
) -> ReplayResult:
    """Recompute proposals, update events, traces, and state from source events."""

    verify_event_sequence(
        events,
        episode_id=checkpoint.state.episode_id,
        after_sequence=checkpoint.last_event_sequence,
    )
    if expected_traces is not None and len(expected_traces) != len(events):
        raise ContractValidationError("expected trace count does not match source events")

    state = checkpoint.state
    steps: list[StepComputation] = []
    mismatches: list[ReplayMismatch] = []
    for index, stored_event in enumerate(events):
        observation = observation_from_event(stored_event)
        step = compute_step(
            state=state,
            observation=observation,
            policy=policy,
            sequence=stored_event.sequence,
            task_id=task_id,
            run_id=run_id,
            code_path_hash=code_path_hash,
            contract_hash=contract_hash,
        )
        if step.source_event.to_dict() != stored_event.to_dict():
            mismatches.append(
                ReplayMismatch(
                    step_id=observation.step_id,
                    field="source_event",
                    expected=stored_event.to_dict(),
                    actual=step.source_event.to_dict(),
                )
            )
        if expected_traces is not None:
            if "trace_hash" in expected_traces[index]:
                TraceRow.from_dict(expected_traces[index])
            else:
                validate_action_removed_trace(expected_traces[index])
            mismatches.extend(_compare_expected_trace(expected_traces[index], step))
        steps.append(step)
        state = step.state_after

    input_artifact_hashes = {
        "checkpoint": canonical_hash(checkpoint),
        "ordered_source_events": canonical_hash([item.to_dict() for item in events]),
    }
    if expected_traces is not None:
        input_artifact_hashes["expected_traces"] = canonical_hash(expected_traces)

    return ReplayResult(
        final_state=state,
        steps=tuple(steps),
        mismatches=tuple(mismatches),
        producer_function="ego_k0_kernel.replay.replay_from_checkpoint",
        input_artifact_hashes=input_artifact_hashes,
        task_id=task_id,
        run_id=run_id,
        episode_ids=(checkpoint.state.episode_id,),
        context_ids=tuple(context_ids),
        seed_context=dict(checkpoint.state.rng_state),
        aggregation_rule="all ordered source events recomputed; zero field mismatches required",
        code_path_hash=code_path_hash,
        contract_hash=contract_hash,
    )
