"""The V2 product's only dispatch/controller implementation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
import uuid

from .engine import (
    DEFAULT_PRIVATE_WORLD_SEED,
    EngineInvariantError,
    StepResult,
    canonical_hash,
    compute_step,
    initial_state,
    make_command,
    make_run_metadata,
)
from .microworld import LAYOUTS, public_world_projection
from .store import CommitReceipt, RecoveryResult, SQLiteEventStore

DISCLOSURE = (
    "Deterministic visible microworld + deficit scorer + tabular EMA; "
    "local default-off product surface; science weight 0."
)


def public_state_projection(state: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact normal-product state commitment, excluding private dynamics."""

    return {
        "schema_version": "ego.life_playground.public_state_projection.v1",
        "clock": deepcopy(state["clock"]),
        "organism": deepcopy(state["organism"]),
        "current_goal": deepcopy(state["current_goal"]),
        "world": public_world_projection(state["world"]),
    }


def public_state_hash(state: Mapping[str, Any]) -> str:
    """Hash only renderer-visible state; never commit private world bytes."""

    return canonical_hash(public_state_projection(state))


@dataclass(frozen=True)
class DispatchResult:
    receipt: CommitReceipt
    step: StepResult | None


class PlaygroundController:
    """The UI's only state-changing entrypoint."""

    def __init__(
        self,
        store: SQLiteEventStore,
        *,
        run_id: str | None = None,
        seed: int = 17,
        world_seed: int = DEFAULT_PRIVATE_WORLD_SEED,
        layout_id: str | None = None,
        on_committed: Callable[[dict[str, Any], dict[str, Any]], None] | None = None,
        on_recovered: Callable[[RecoveryResult], None] | None = None,
    ) -> None:
        self.store = store
        if type(world_seed) is not int:
            raise EngineInvariantError("world_seed must be an integer")
        self.world_seed = world_seed
        self.on_committed = on_committed
        self.on_recovered = on_recovered
        selected_run_id = run_id if run_id is not None else store.latest_compatible_run_id()

        if selected_run_id is not None and store.run_exists(selected_run_id):
            recovered = store.recover_run(selected_run_id)
            recovered_layout = recovered.state["world"]["layout"]["layout_id"]
            if layout_id is not None and recovered_layout != layout_id:
                if run_id is not None:
                    raise EngineInvariantError(
                        f"stored run layout {recovered_layout!r} does not match requested {layout_id!r}"
                    )
                selected_run_id = None
            else:
                self.run_id = selected_run_id
                self._adopt_recovery(recovered)
                self.recovery_status = f"recomputed {recovered.command_count} command(s)"
                if self.on_recovered is not None:
                    self.on_recovered(recovered)
                return

        self.run_id = selected_run_id or f"local-{uuid.uuid4().hex[:16]}"
        self.run_meta = make_run_metadata(self.run_id, seed)
        selected_layout = layout_id or "p0_cross_v1"
        if selected_layout not in LAYOUTS:
            raise EngineInvariantError(f"unknown microworld layout: {selected_layout!r}")
        state = initial_state(
            run_id=self.run_id, seed=self.world_seed, layout_id=selected_layout
        )
        store.create_run(self.run_meta, state)
        recovered = store.recover_run(self.run_id)
        self._adopt_recovery(recovered)
        self.recovery_status = "new run"

    def _adopt_recovery(self, recovered: RecoveryResult) -> None:
        self.recovery = recovered
        self.run_meta = recovered.run_meta
        self.state = recovered.state
        self.last_trace = recovered.traces[-1] if recovered.traces else None

    def dispatch(
        self,
        cue: str,
        interventions: Mapping[str, str],
        *,
        trigger_source: str = "ui_step_button",
        world_event: str | None = None,
    ) -> DispatchResult:
        command = make_command(
            sequence=int(self.state["clock"]["global_tick"]) + 1,
            cue=cue,
            trigger_source=trigger_source,
            interventions=interventions,
            prev_command_hash=self.state.get("last_command_hash"),
            world_event=world_event,
        )
        computed = compute_step(self.state, command, self.run_meta)
        receipt = self.store.append_step(command, computed.trace)
        if not receipt.committed:
            # Neither controller state, its derived recovery timeline, nor a
            # renderer callback changes after an atomic transaction failure.
            return DispatchResult(receipt=receipt, step=None)

        # Timeline truth is always rebuilt from serialized initial state plus
        # ordered commands.  Stored traces remain comparison-only inputs.
        recovered = self.store.recover_run(self.run_id)
        self._adopt_recovery(recovered)
        self.recovery_status = f"committed tick {receipt.sequence}"
        if self.on_committed is not None:
            self.on_committed(deepcopy(self.state), deepcopy(self.last_trace))
        return DispatchResult(receipt=receipt, step=computed)

    def recover(self) -> RecoveryResult:
        recovered = self.store.recover_run(self.run_id)
        self._adopt_recovery(recovered)
        self.recovery_status = f"recomputed {recovered.command_count} command(s)"
        if self.on_recovered is not None:
            self.on_recovered(recovered)
        return recovered

    def export(self, output_path: str | Path) -> Path:
        output = self.store.export_run(self.run_id, output_path)
        self.recovery_status = f"recomputed + exported {output.name}"
        return output

    def load_run(self, run_id: str) -> RecoveryResult:
        """Adopt an existing durable run after complete recomputation."""

        if type(run_id) is not str or not run_id:
            raise EngineInvariantError("run_id must be a non-empty string")
        if not self.store.run_exists(run_id):
            raise EngineInvariantError(f"unknown run: {run_id}")
        recovered = self.store.recover_run(run_id)
        self.run_id = run_id
        self._adopt_recovery(recovered)
        self.recovery_status = f"loaded + recomputed {recovered.command_count} command(s)"
        if self.on_recovered is not None:
            self.on_recovered(recovered)
        return recovered

    def reset_run(self, run_id: str | None = None) -> RecoveryResult:
        """Start a new run without deleting any prior episode history."""

        selected = run_id or f"local-{uuid.uuid4().hex[:16]}"
        if type(selected) is not str or not selected:
            raise EngineInvariantError("run_id must be a non-empty string")
        if self.store.run_exists(selected):
            raise EngineInvariantError(f"run already exists: {selected}")
        seed = int(self.run_meta["seed"])
        layout_id = str(self.state["world"]["layout"]["layout_id"])
        run_meta = make_run_metadata(selected, seed)
        state = initial_state(
            run_id=selected, seed=self.world_seed, layout_id=layout_id
        )
        self.store.create_run(run_meta, state)
        recovered = self.store.recover_run(selected)
        self.run_id = selected
        self._adopt_recovery(recovered)
        self.recovery_status = "new run after reset"
        if self.on_recovered is not None:
            self.on_recovered(recovered)
        return recovered
