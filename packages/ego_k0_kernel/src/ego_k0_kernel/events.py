"""Canonical source-event and derived update-event constructors."""

from __future__ import annotations

from collections.abc import Sequence

from .contracts import (
    ActionProposal,
    ContractValidationError,
    EventRecord,
    KernelStateRecord,
    ObservationRecord,
    canonical_hash,
    stable_id,
)


SOURCE_EVENT_TYPE = "observation.accepted"
UPDATE_EVENT_TYPE = "kernel.state_transition"


def observation_to_event(observation: ObservationRecord, *, sequence: int) -> EventRecord:
    body = {
        "episode_id": observation.episode_id,
        "step_id": observation.step_id,
        "sequence": sequence,
        "observation": observation.to_dict(),
    }
    return EventRecord(
        event_id=stable_id("evt_obs", body),
        episode_id=observation.episode_id,
        step_id=observation.step_id,
        sequence=sequence,
        event_type=SOURCE_EVENT_TYPE,
        payload={"observation": observation.to_dict()},
        provenance={"producer_function": "ego_k0_kernel.events.observation_to_event"},
    )


def observation_from_event(event: EventRecord) -> ObservationRecord:
    if event.event_type != SOURCE_EVENT_TYPE:
        raise ContractValidationError(
            f"replay accepts only {SOURCE_EVENT_TYPE!r} source events, got {event.event_type!r}"
        )
    payload = event.payload.get("observation")
    if not isinstance(payload, dict) and not hasattr(payload, "items"):
        raise ContractValidationError("source event lacks a typed observation")
    observation = ObservationRecord.from_dict(payload)
    if observation.episode_id != event.episode_id or observation.step_id != event.step_id:
        raise ContractValidationError("source event identity does not match its observation")
    return observation


def state_transition_event(
    state_before: KernelStateRecord,
    observation: ObservationRecord,
    proposal: ActionProposal,
    state_after: KernelStateRecord,
    *,
    sequence: int,
) -> EventRecord:
    payload = {
        "observation_id": observation.observation_id,
        "observation_hash": canonical_hash(observation),
        "proposal_hash": canonical_hash(proposal),
        "state_before_hash": state_before.state_hash,
        "state_after_hash": state_after.state_hash,
    }
    return EventRecord(
        event_id=stable_id(
            "evt_update",
            {
                "episode_id": observation.episode_id,
                "step_id": observation.step_id,
                "sequence": sequence,
                "payload": payload,
            },
        ),
        episode_id=observation.episode_id,
        step_id=observation.step_id,
        sequence=sequence,
        event_type=UPDATE_EVENT_TYPE,
        payload=payload,
        provenance={"producer_function": "ego_k0_kernel.events.state_transition_event"},
    )


def verify_event_sequence(
    events: Sequence[EventRecord],
    *,
    episode_id: str,
    after_sequence: int,
) -> None:
    seen: set[str] = set()
    expected = after_sequence + 1
    for event in events:
        if not isinstance(event, EventRecord):
            raise ContractValidationError("event sequence contains a non-EventRecord value")
        if event.episode_id != episode_id:
            raise ContractValidationError("event sequence crosses episode boundary")
        if event.sequence != expected:
            raise ContractValidationError(
                f"event sequence mismatch: expected {expected}, got {event.sequence}"
            )
        if event.event_id in seen:
            raise ContractValidationError(f"duplicate event id {event.event_id!r}")
        seen.add(event.event_id)
        expected += 1
