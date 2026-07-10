"""Single canonical state transition used by source execution and replay."""

from __future__ import annotations

from typing import Any

from .contracts import (
    ActionProposal,
    ContractValidationError,
    KernelStateRecord,
    ObservationRecord,
    canonical_hash,
    thaw_json,
)


def initial_state(episode_id: str, *, seed: int) -> KernelStateRecord:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ContractValidationError("seed must be an integer")
    return KernelStateRecord(
        episode_id=episode_id,
        step_id=0,
        substates={
            "observation_count": 0,
            "observation_chain_hash": canonical_hash([]),
            "proposal_chain_hash": canonical_hash([]),
        },
        rng_state={"seed": seed, "draw_count": 0},
    )


def apply_observation(
    state: KernelStateRecord,
    observation: ObservationRecord,
    proposal: ActionProposal,
) -> KernelStateRecord:
    """Return the next state; no adapter, trace sink, or environment is consulted."""

    if observation.episode_id != state.episode_id:
        raise ContractValidationError("observation episode does not match state")
    if proposal.episode_id != state.episode_id:
        raise ContractValidationError("proposal episode does not match state")
    expected_step = state.step_id + 1
    if observation.step_id != expected_step or proposal.step_id != expected_step:
        raise ContractValidationError(
            f"step mismatch: expected {expected_step}, got observation={observation.step_id}, "
            f"proposal={proposal.step_id}"
        )
    if proposal.execution_authority is not False:
        raise ContractValidationError("proposal execution authority must remain false")

    substates: dict[str, Any] = thaw_json(state.substates)
    rng_state: dict[str, Any] = thaw_json(state.rng_state)
    count = substates.get("observation_count")
    draw_count = rng_state.get("draw_count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ContractValidationError("state observation_count is invalid")
    if isinstance(draw_count, bool) or not isinstance(draw_count, int) or draw_count < 0:
        raise ContractValidationError("state rng draw_count is invalid")

    substates.update(
        {
            "observation_count": count + 1,
            "last_observation_id": observation.observation_id,
            "observation_chain_hash": canonical_hash(
                {
                    "previous": substates["observation_chain_hash"],
                    "observation": observation.to_dict(),
                }
            ),
            "proposal_chain_hash": canonical_hash(
                {
                    "previous": substates["proposal_chain_hash"],
                    "proposal": proposal.to_dict(),
                }
            ),
        }
    )
    rng_state["draw_count"] = draw_count + 1
    return KernelStateRecord(
        episode_id=state.episode_id,
        step_id=expected_step,
        substates=substates,
        rng_state=rng_state,
    )
