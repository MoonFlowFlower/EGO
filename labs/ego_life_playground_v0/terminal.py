"""Terminal view routed through the single PlaygroundController."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .controller import DispatchResult, PlaygroundController, public_state_hash
from .engine import DEFAULT_INTERVENTIONS, EngineInvariantError
from .microworld import (
    ALLOWED_WORLD_EVENTS,
    cue_for_event,
    default_event_for_sequence,
    event_for_cue,
    make_public_frame,
)
from .store import RecoveryResult

def _timeline_from_recovery(recovery: RecoveryResult) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for frame in recovery.frames:
        trace = frame.trace
        clock = frame.state["clock"]
        model_update = {} if trace is None else trace.get("model_update", {})
        memory_update = {} if trace is None else trace.get("memory_update", {})
        prediction_error = {} if trace is None else trace.get("prediction_error", {})
        timeline.append(
            {
                "sequence": frame.sequence,
                "global_tick": clock["global_tick"],
                "episode_index": clock["episode_index"],
                "episode_tick": clock["episode_tick"],
                "layout_id": frame.state["world"]["layout"]["layout_id"],
                "event": "quiet_interval" if trace is None else event_for_cue(trace["cue"]),
                "observation": "quiet" if trace is None else trace["cue"],
                "observation_hash": None if trace is None else trace["observation_hash"],
                "selected_action": None if trace is None else trace["selected_action"],
                "world_outcome": None if trace is None else deepcopy(trace.get("world_outcome")),
                "prediction_error_l1": None
                if trace is None
                else round(sum(abs(float(value)) for value in prediction_error.values()), 6),
                "model_count_before": None if trace is None else model_update.get("previous_count"),
                "model_count_after": None if trace is None else model_update.get("new_count"),
                "bounded_update_applied": False if trace is None else bool(model_update.get("applied")),
                "consolidation_applied": False
                if trace is None
                else bool(memory_update.get("consolidation_applied")),
                "consolidation_lineage_count": 0
                if trace is None
                else len(memory_update.get("consolidation_refs", [])),
                "consolidation_lineage_hashes": []
                if trace is None
                else deepcopy(memory_update.get("consolidation_refs", [])),
                "claim_support_margin": None
                if trace is None
                else trace.get("claim_retrieval", {}).get("support_margin"),
                "claim_provenance_event_ids": []
                if trace is None
                else deepcopy(
                    trace.get("claim_retrieval", {}).get("provenance_event_ids", [])
                ),
                "public_state_hash": public_state_hash(frame.state),
            }
        )
    return timeline


def build_terminal_snapshot(controller: PlaygroundController) -> dict[str, Any]:
    """Expose one understandable view derived only from recovered truth."""

    recovery = controller.recovery
    frame = recovery.frames[-1]
    state = frame.state
    trace = frame.trace
    previous_state = recovery.frames[-2].state if len(recovery.frames) > 1 else state
    selected_candidate = None
    if trace is not None:
        selected_candidate = next(
            item for item in trace["candidates"] if item["action"] == trace["selected_action"]
        )
    world_frame = make_public_frame(state, trace)
    return {
        "run_id": controller.run_id,
        "world": world_frame,
        "observation": deepcopy(world_frame["observation"]),
        "observation_hash": world_frame["observation_hash"],
        "decision_observation": deepcopy(world_frame["observation"])
        if trace is None
        else deepcopy(trace["observation"]),
        "decision_observation_hash": world_frame["observation_hash"]
        if trace is None
        else trace["observation_hash"],
        "internal_state": deepcopy(state["organism"]),
        "current_goal": deepcopy(state["current_goal"]),
        "candidates": [] if trace is None else deepcopy(trace["candidates"]),
        "legal_actions": [] if trace is None else deepcopy(trace["legal_actions"]),
        "gated_actions": [] if trace is None else deepcopy(trace["gated_actions"]),
        "selected_action": None if trace is None else trace["selected_action"],
        "selected_score": None if selected_candidate is None else selected_candidate["total_score"],
        "prediction": None if trace is None else deepcopy(trace["prediction"]),
        "actual_delta": None if trace is None else deepcopy(trace["actual_delta"]),
        "prediction_error": None if trace is None else deepcopy(trace["prediction_error"]),
        "model_update": None if trace is None else deepcopy(trace["model_update"]),
        "memory": {
            "read": None
            if trace is None
            else {
                "refs": deepcopy(trace["memory_refs"]),
                "projection": deepcopy(trace["provenance_projection"]),
                "claim_retrieval": deepcopy(trace.get("claim_retrieval")),
            },
            "write": None if trace is None else deepcopy(trace["memory_update"]),
            "claim_write": None if trace is None else deepcopy(trace.get("claim_update")),
            "persistent_state": deepcopy(state["memory"]),
        },
        "world_outcome": None if trace is None else deepcopy(trace.get("world_outcome")),
        "policy_projection_hash": None
        if trace is None
        else trace.get("policy_projection_hash"),
        "policy_non_memory_projection_hash": None
        if trace is None
        else trace.get("policy_non_memory_projection_hash"),
        "state_transition": {
            "public_before_hash": public_state_hash(previous_state),
            "public_after_hash": public_state_hash(state),
            "organism_before": deepcopy(previous_state["organism"]),
            "organism_after": deepcopy(state["organism"]),
            "world_before": make_public_frame(previous_state),
            "world_after": deepcopy(world_frame),
        },
        "timeline": _timeline_from_recovery(recovery),
        "public_state_hash": public_state_hash(state),
        "recovered": recovery.recovered,
        "science_weight": 0,
    }


class TerminalPlayground:
    """Synchronous, paused-by-default P0 operator surface.

    Every state-changing command calls ``PlaygroundController.dispatch``;
    inspect, pause, save/load and replay do not implement a second reducer.
    """

    HELP = (
        "step [event] | run N | pause | inspect | inject EVENT | "
        "save PATH | load RUN_ID | reset [RUN_ID] | replay | help | quit"
    )

    def __init__(self, controller: PlaygroundController) -> None:
        self.controller = controller
        self.paused = True

    def _dispatch_event(self, event: str, trigger_source: str) -> DispatchResult:
        return self.controller.dispatch(
            cue_for_event(event),
            DEFAULT_INTERVENTIONS,
            trigger_source=trigger_source,
            world_event=event,
        )

    def execute(self, command_line: str) -> dict[str, Any]:
        raw = command_line.strip()
        if not raw:
            return {"command": "", "status": "error", "error": "empty command"}
        parts = raw.split()
        operation = parts[0].lower()
        try:
            if operation in {"help", "?"}:
                return {
                    "command": "help",
                    "status": "ok",
                    "usage": self.HELP,
                    "allowed_world_events": list(ALLOWED_WORLD_EVENTS),
                }
            if operation in {"quit", "exit"}:
                self.paused = True
                return {"command": operation, "status": "quit"}
            if operation == "pause":
                self.paused = True
                return {
                    "command": "pause",
                    "status": "paused",
                    "global_tick": self.controller.state["clock"]["global_tick"],
                }
            if operation == "inspect":
                if len(parts) != 1:
                    raise ValueError("usage: inspect")
                return {"command": "inspect", "status": "ok", "snapshot": build_terminal_snapshot(self.controller)}
            if operation == "step":
                if len(parts) > 2:
                    raise ValueError("usage: step [event]")
                sequence = int(self.controller.state["clock"]["global_tick"]) + 1
                event = parts[1] if len(parts) == 2 else default_event_for_sequence(sequence)
                result = self._dispatch_event(event, "terminal_step")
                if not result.receipt.committed:
                    raise RuntimeError(result.receipt.error or "atomic commit rejected")
                self.paused = True
                return {
                    "command": "step",
                    "event": event,
                    "status": "committed",
                    "snapshot": build_terminal_snapshot(self.controller),
                }
            if operation == "inject":
                if len(parts) != 2:
                    raise ValueError("usage: inject EVENT")
                event = parts[1]
                result = self._dispatch_event(event, "terminal_event")
                if not result.receipt.committed:
                    raise RuntimeError(result.receipt.error or "atomic commit rejected")
                self.paused = True
                return {
                    "command": "inject",
                    "event": event,
                    "status": "committed",
                    "snapshot": build_terminal_snapshot(self.controller),
                }
            if operation == "run":
                if len(parts) != 2:
                    raise ValueError("usage: run N")
                ticks = int(parts[1])
                if ticks <= 0 or ticks > 10000:
                    raise ValueError("run tick count must be between 1 and 10000")
                self.paused = False
                for _ in range(ticks):
                    sequence = int(self.controller.state["clock"]["global_tick"]) + 1
                    event = default_event_for_sequence(sequence)
                    result = self._dispatch_event(event, "terminal_run")
                    if not result.receipt.committed:
                        self.paused = True
                        raise RuntimeError(result.receipt.error or "atomic commit rejected")
                self.paused = True
                return {
                    "command": "run",
                    "status": "committed",
                    "ticks_committed": ticks,
                    "snapshot": build_terminal_snapshot(self.controller),
                }
            if operation == "save":
                path_text = raw[len(parts[0]) :].strip()
                if not path_text:
                    raise ValueError("usage: save PATH")
                output = self.controller.export(path_text)
                return {"command": "save", "status": "saved", "path": str(output)}
            if operation == "load":
                if len(parts) != 2:
                    raise ValueError("usage: load RUN_ID")
                recovery = self.controller.load_run(parts[1])
                self.paused = True
                return {
                    "command": "load",
                    "status": "loaded",
                    "run_id": self.controller.run_id,
                    "frame_count": len(recovery.frames),
                    "snapshot": build_terminal_snapshot(self.controller),
                }
            if operation == "reset":
                if len(parts) > 2:
                    raise ValueError("usage: reset [RUN_ID]")
                recovery = self.controller.reset_run(parts[1] if len(parts) == 2 else None)
                self.paused = True
                return {
                    "command": "reset",
                    "status": "reset",
                    "run_id": self.controller.run_id,
                    "frame_count": len(recovery.frames),
                    "snapshot": build_terminal_snapshot(self.controller),
                }
            if operation == "replay":
                if len(parts) != 1:
                    raise ValueError("usage: replay")
                recovery = self.controller.recover()
                self.paused = True
                return {
                    "command": "replay",
                    "status": "recomputed",
                    "run_id": self.controller.run_id,
                    "frame_count": len(recovery.frames),
                    "timeline": _timeline_from_recovery(recovery),
                }
            raise ValueError(f"unknown command {operation!r}; {self.HELP}")
        except (EngineInvariantError, OSError, RuntimeError, ValueError) as exc:
            self.paused = True
            return {
                "command": operation,
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
            }
