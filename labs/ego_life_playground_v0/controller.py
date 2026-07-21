"""The V2 product's only dispatch/controller implementation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Callable, Mapping
import uuid

from .engine import (
    DEFAULT_INTERVENTIONS,
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
from .store import (
    CommitReceipt,
    RecoveryError,
    RecoveryFrame,
    RecoveryResult,
    SQLiteEventStore,
)

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
        self.integrity_blocked = False
        self.last_dispatch_duration_seconds: float | None = None
        self.last_commit_receipt: CommitReceipt | None = None
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
                self.recovery_status = f"fully replayed {recovered.command_count} command(s)"
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

    def _adopt_committed_step(self, computed: StepResult) -> None:
        """Adopt one atomically persisted step without claiming full replay."""

        prior = self.recovery
        frame = RecoveryFrame(
            sequence=int(computed.trace["sequence"]),
            state=computed.next_state,
            trace=computed.trace,
        )
        timeline = RecoveryResult(
            run_id=self.run_id,
            run_meta=self.run_meta,
            frames=(*prior.frames, frame),
            recovered=False,
            verification_mode="incremental_committed",
            last_full_replay_sequence=prior.last_full_replay_sequence,
        )
        self._adopt_recovery(timeline)

    def _full_replay_after_terminal(self) -> None:
        try:
            recovered = self.store.recover_run(self.run_id)
        except RecoveryError as exc:
            self.integrity_blocked = True
            self.recovery_status = f"integrity_blocked at terminal: {exc}"
            raise EngineInvariantError(self.recovery_status) from exc
        self._adopt_recovery(recovered)
        self.integrity_blocked = False
        self.recovery_status = f"fully replayed {recovered.command_count} command(s) at terminal"

    def dispatch(
        self,
        interventions: Mapping[str, str] | None = None,
        *,
        trigger_source: str = "ui_step_button",
        injected_event: str | None = None,
    ) -> DispatchResult:
        if self.integrity_blocked:
            raise EngineInvariantError("controller is integrity_blocked; explicit recovery required")
        started = time.perf_counter()
        lifecycle = self.state.get("lifecycle", {})
        if isinstance(lifecycle, Mapping) and lifecycle.get("trial_status") == "terminal":
            raise EngineInvariantError("trial is terminal")
        command = make_command(
            sequence=int(self.state["clock"]["global_tick"]) + 1,
            trigger_source=trigger_source,
            interventions=DEFAULT_INTERVENTIONS if interventions is None else interventions,
            prev_command_hash=self.state.get("last_command_hash"),
            injected_event=injected_event,
        )
        computed = compute_step(self.state, command, self.run_meta)
        receipt = self.store.append_step(command, computed.trace)
        self.last_commit_receipt = receipt
        if not receipt.committed:
            # Neither controller state, its derived recovery timeline, nor a
            # renderer callback changes after an atomic transaction failure.
            self.last_dispatch_duration_seconds = time.perf_counter() - started
            return DispatchResult(receipt=receipt, step=None)

        self._adopt_committed_step(computed)
        self.recovery_status = (
            f"incrementally committed tick {receipt.sequence}; "
            f"full replay through {self.recovery.last_full_replay_sequence}"
        )
        self.last_dispatch_duration_seconds = time.perf_counter() - started
        lifecycle = self.state.get("lifecycle", {})
        if isinstance(lifecycle, Mapping) and lifecycle.get("trial_status") == "terminal":
            self._full_replay_after_terminal()
        if self.on_committed is not None:
            # The in-process renderer is a read-only observer of the committed
            # controller objects.  Copying the complete growing state here
            # reintroduced the same per-tick scaling problem after persistence.
            self.on_committed(self.state, self.last_trace)
        return DispatchResult(receipt=receipt, step=computed)

    def recover(self) -> RecoveryResult:
        recovered = self.store.recover_run(self.run_id)
        self._adopt_recovery(recovered)
        self.integrity_blocked = False
        self.recovery_status = f"fully replayed {recovered.command_count} command(s)"
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
        self.integrity_blocked = False
        self.recovery_status = f"loaded + fully replayed {recovered.command_count} command(s)"
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
        self.integrity_blocked = False
        self.recovery_status = "new run after reset"
        if self.on_recovered is not None:
            self.on_recovered(recovered)
        return recovered
