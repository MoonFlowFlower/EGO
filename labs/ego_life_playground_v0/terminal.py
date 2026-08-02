"""Terminal view routed through the single PlaygroundController."""

from __future__ import annotations

from copy import deepcopy
from html import escape
import json
from pathlib import Path
from typing import Any, Mapping

from .controller import DispatchResult, PlaygroundController, public_state_hash
from .engine import DEFAULT_INTERVENTIONS, EngineInvariantError, MAX_LIVES
from .microworld import (
    ALLOWED_WORLD_EVENTS,
    make_public_frame,
)
from .store import RecoveryResult


def _trace_mapping(trace: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return trace if isinstance(trace, Mapping) else {}


def _lifecycle_summary(state: Mapping[str, Any]) -> dict[str, Any]:
    lifecycle = deepcopy(state.get("lifecycle", {}))
    results = lifecycle.get("life_results", []) if isinstance(lifecycle, dict) else []
    return {
        "lifecycle": lifecycle,
        "life_survival": [int(item["survival_ticks"]) for item in results],
        "terminal_life_result": None
        if not isinstance(lifecycle, dict)
        else deepcopy(lifecycle.get("terminal_life_result")),
    }

def _timeline_from_recovery(recovery: RecoveryResult) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for frame in recovery.frames:
        trace = frame.trace
        trace_mapping = _trace_mapping(trace)
        clock = frame.state["clock"]
        model_update = trace_mapping.get("model_update", {})
        memory_update = trace_mapping.get("memory_update", {})
        prediction_error = trace_mapping.get("prediction_error", {})
        claim_retrieval = trace_mapping.get("claim_retrieval") or {}
        consolidation_receipt = memory_update.get("consolidation_refs") or {}
        entry = {
            "sequence": frame.sequence,
            "global_tick": clock["global_tick"],
            "episode_index": clock["episode_index"],
            "episode_tick": clock["episode_tick"],
            "layout_id": frame.state["world"]["layout"]["layout_id"],
            "injected_event": trace_mapping.get("injected_event"),
            "observation": deepcopy(trace_mapping.get("observation")),
            "observation_hash": trace_mapping.get("observation_hash"),
            "selected_action": trace_mapping.get("selected_action"),
            "world_transition": deepcopy(trace_mapping.get("world_transition")),
            "prediction_error_l1": None
            if not prediction_error
            else round(sum(abs(float(value)) for value in prediction_error.values()), 6),
            "model_count_before": model_update.get("previous_count"),
            "model_count_after": model_update.get("new_count"),
            "bounded_update_applied": bool(model_update.get("applied")),
            "consolidation_applied": bool(memory_update.get("consolidation_applied")),
            "consolidation_lineage_count": consolidation_receipt.get("count", 0),
            "consolidation_lineage": deepcopy(consolidation_receipt),
            "claim_support_margin": claim_retrieval.get("support_margin"),
            "claim_provenance": deepcopy(claim_retrieval.get("provenance", {})),
            "transition_kind": trace_mapping.get("transition_kind"),
            "policy_invoked": bool(trace_mapping.get("policy_invoked")) if trace is not None else None,
            "life_termination": deepcopy(trace_mapping.get("life_termination")),
            "carry_reset_receipt": deepcopy(trace_mapping.get("carry_reset_receipt")),
            "survival_learning": deepcopy(trace_mapping.get("survival_learning")),
            "predictive_control": deepcopy(trace_mapping.get("predictive_control")),
            "homeostatic_transfer": deepcopy(trace_mapping.get("homeostatic_transfer")),
            "public_featured_transfer": deepcopy(
                trace_mapping.get("public_featured_transfer")
            ),
            "public_state_hash": public_state_hash(frame.state),
        }
        entry.update(_lifecycle_summary(frame.state))
        timeline.append(entry)
    return timeline


def build_terminal_snapshot(controller: PlaygroundController) -> dict[str, Any]:
    """Expose one understandable view derived only from recovered truth."""

    recovery = controller.recovery
    frame = recovery.frames[-1]
    state = frame.state
    trace = frame.trace
    trace_mapping = _trace_mapping(trace)
    claim_retrieval = trace_mapping.get("claim_retrieval") or {}
    previous_state = recovery.frames[-2].state if len(recovery.frames) > 1 else state
    selected_candidate = None
    selected_action = trace_mapping.get("selected_action")
    if selected_action is not None:
        selected_candidate = next(
            (
                item
                for item in trace_mapping.get("candidates", [])
                if item.get("action") == selected_action
            ),
            None,
        )
    world_frame = make_public_frame(state, trace)
    lifecycle_summary = _lifecycle_summary(state)
    life_survival = lifecycle_summary["life_survival"]
    early = life_survival[:4]
    late = life_survival[12:16]
    resource_successes = sum(
        1
        for recovered_frame in recovery.frames
        if isinstance(recovered_frame.trace, Mapping)
        and bool(
            (recovered_frame.trace.get("survival_learning") or {}).get(
                "successful_resource_interaction"
            )
        )
    )
    return {
        "run_id": controller.run_id,
        "world": world_frame,
        "observation": deepcopy(world_frame["observation"]),
        "observation_hash": world_frame["observation_hash"],
        "decision_observation": deepcopy(world_frame["observation"])
        if trace is None
        else deepcopy(trace_mapping.get("observation")),
        "decision_observation_hash": world_frame["observation_hash"]
        if trace is None
        else trace_mapping.get("observation_hash"),
        "internal_state": deepcopy(state["organism"]),
        "current_goal": deepcopy(state["current_goal"]),
        "candidates": [] if trace is None else deepcopy(trace_mapping.get("candidates", [])),
        "candidate_actions": []
        if trace is None
        else deepcopy(trace_mapping.get("candidate_actions", [])),
        "selected_action": None if trace is None else trace_mapping.get("selected_action"),
        "selected_score": None
        if selected_candidate is None
        else selected_candidate.get("total_score", selected_candidate.get("score")),
        "prediction": None if trace is None else deepcopy(trace_mapping.get("prediction")),
        "actual_delta": None if trace is None else deepcopy(trace_mapping.get("actual_delta")),
        "prediction_error": None if trace is None else deepcopy(trace_mapping.get("prediction_error")),
        "goal_trace": None
        if trace is None
        else {
            "goal_before": deepcopy(trace_mapping.get("goal_before")),
            "goal_progress": deepcopy(trace_mapping.get("goal_progress")),
            "goal_transition": deepcopy(trace_mapping.get("goal_transition")),
            "goal_after": deepcopy(trace_mapping.get("goal_after")),
        },
        "model_update": None if trace is None else deepcopy(trace_mapping.get("model_update")),
        "memory": {
            "read": None
            if trace is None
            else {
                "refs": deepcopy(trace_mapping.get("memory_refs")),
                "projection": deepcopy(trace_mapping.get("provenance_projection")),
                "claim_retrieval": deepcopy(claim_retrieval),
            },
            "write": None if trace is None else deepcopy(trace_mapping.get("memory_update")),
            "claim_write": None if trace is None else deepcopy(trace_mapping.get("claim_update")),
            "persistent_state": deepcopy(state["memory"]),
        },
        "world_transition": None
        if trace is None
        else deepcopy(trace_mapping.get("world_transition")),
        "policy_projection_hash": None
        if trace is None
        else trace_mapping.get("policy_projection_hash"),
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
        "verification_mode": recovery.verification_mode,
        "last_committed_sequence": recovery.last_committed_sequence,
        "last_full_replay_sequence": recovery.last_full_replay_sequence,
        "integrity_blocked": bool(getattr(controller, "integrity_blocked", False)),
        "last_dispatch_duration_seconds": getattr(
            controller, "last_dispatch_duration_seconds", None
        ),
        "row_readback_verified": bool(
            getattr(getattr(controller, "last_commit_receipt", None), "row_readback_verified", False)
        ),
        "science_weight": 0,
        "transition_kind": trace_mapping.get("transition_kind"),
        "policy_invoked": bool(trace_mapping.get("policy_invoked")) if trace is not None else None,
        "life_termination": deepcopy(trace_mapping.get("life_termination")),
        "carry_reset_receipt": deepcopy(trace_mapping.get("carry_reset_receipt")),
        "survival_learning": deepcopy(trace_mapping.get("survival_learning")),
        "predictive_control": deepcopy(trace_mapping.get("predictive_control")),
        "homeostatic_transfer": deepcopy(trace_mapping.get("homeostatic_transfer")),
        "public_featured_transfer": deepcopy(
            trace_mapping.get("public_featured_transfer")
        ),
        "public_featured_summary": {
            "energy": float(state["organism"]["energy"]),
            "safety": float(state["organism"]["safety"]),
            "deficits": deepcopy(
                (((trace_mapping.get("public_featured_transfer") or {}).get("plan") or {}).get("reason", {}))
            ),
            "predictions": deepcopy(
                (((trace_mapping.get("public_featured_transfer") or {}).get("plan") or {}).get("predictions", {}))
            ),
            "ranking": deepcopy(
                (((trace_mapping.get("public_featured_transfer") or {}).get("plan") or {}).get("ranking", []))
            ),
            "actual_feedback": deepcopy(
                (trace_mapping.get("public_featured_transfer") or {}).get(
                    "actual_feedback"
                )
            ),
            "slow_state_hash": (
                (trace_mapping.get("public_featured_transfer") or {}).get(
                    "slow_state_hash"
                )
            ),
            "fast_state_hash": (
                (trace_mapping.get("public_featured_transfer") or {}).get(
                    "fast_state_hash"
                )
            ),
            "posterior_entropy_bits": (
                (trace_mapping.get("public_featured_transfer") or {}).get(
                    "posterior_entropy_bits"
                )
            ),
            "update_count": (
                (trace_mapping.get("public_featured_transfer") or {}).get(
                    "update_count"
                )
            ),
            "world_switch_count": (
                (trace_mapping.get("public_featured_transfer") or {}).get(
                    "world_switch_count"
                )
            ),
        },
        "homeostatic_summary": {
            "energy": float(state["organism"]["energy"]),
            "safety": float(state["organism"]["safety"]),
            "deficits": deepcopy(
                ((trace_mapping.get("homeostatic_transfer") or {}).get("plan") or {}).get(
                    "drive", {}
                )
            ),
            "predictions_by_action": deepcopy(
                ((trace_mapping.get("homeostatic_transfer") or {}).get("plan") or {}).get(
                    "predictions_by_action", {}
                )
            ),
            "selection_reason": (
                ((trace_mapping.get("homeostatic_transfer") or {}).get("plan") or {}).get(
                    "selection_reason"
                )
            ),
            "slow_state_hash": (
                (trace_mapping.get("homeostatic_transfer") or {}).get("slow_state_hash")
            ),
            "fast_state_hash": (
                (trace_mapping.get("homeostatic_transfer") or {}).get("fast_state_hash")
            ),
            "posterior_hash": (
                (trace_mapping.get("homeostatic_transfer") or {}).get("posterior_hash")
            ),
            "update_count": (
                (trace_mapping.get("homeostatic_transfer") or {}).get("update_count")
            ),
        },
        "survival_learning_summary": {
            "max_lives": MAX_LIVES,
            "lives_1_4_mean": None if len(early) < 4 else round(sum(early) / 4.0, 3),
            "lives_13_16_mean": None if len(late) < 4 else round(sum(late) / 4.0, 3),
            "successful_resource_interactions": resource_successes,
        },
        **lifecycle_summary,
    }


def render_homeostatic_trace_html(
    recovery: RecoveryResult, output_path: str | Path
) -> Path:
    """Render recovered trace evidence without owning behavior logic."""

    rows: list[dict[str, Any]] = []
    for frame in recovery.frames:
        trace = _trace_mapping(frame.trace)
        homeostatic = _trace_mapping(trace.get("homeostatic_transfer"))
        plan = _trace_mapping(homeostatic.get("plan"))
        update = _trace_mapping(homeostatic.get("update"))
        featured = _trace_mapping(trace.get("public_featured_transfer"))
        featured_plan = _trace_mapping(featured.get("plan"))
        if featured.get("mode") == "hierarchical_bayes":
            mode = "public_featured_hierarchical_transfer"
            deficits = deepcopy(featured_plan.get("reason", {}))
            predictions = deepcopy(featured_plan.get("predictions", {}))
            action_values = deepcopy(featured_plan.get("ranking", []))
            selection_reason = deepcopy(featured_plan.get("reason", {}))
            actual_outcome = deepcopy(featured.get("actual_feedback"))
            update = _trace_mapping(featured.get("update"))
            posterior_hash = featured.get("state_hash")
            slow_hash = featured.get("slow_state_hash")
            fast_hash = featured.get("fast_state_hash")
            update_count = featured.get("update_count")
        else:
            mode = "within_world_homeostatic"
            deficits = deepcopy(plan.get("drive", {}))
            predictions = deepcopy(plan.get("predictions_by_action", {}))
            action_values = deepcopy(plan.get("action_values", {}))
            selection_reason = plan.get("selection_reason")
            actual_outcome = _trace_mapping(
                trace.get("world_transition")
            ).get("outcome_type")
            posterior_hash = homeostatic.get("posterior_hash")
            slow_hash = homeostatic.get("slow_state_hash")
            fast_hash = homeostatic.get("fast_state_hash")
            update_count = homeostatic.get("update_count")
        rows.append(
            {
                "sequence": frame.sequence,
                "mode": mode,
                "energy": frame.state["organism"]["energy"],
                "safety": frame.state["organism"]["safety"],
                "deficits": deficits,
                "predictions_by_action": predictions,
                "action_values": action_values,
                "selected_action": trace.get("selected_action"),
                "selection_reason": selection_reason,
                "actual_outcome": actual_outcome,
                "actual_delta": deepcopy(trace.get("actual_delta")),
                "update_applied": update.get("applied"),
                "posterior_hash": posterior_hash,
                "slow_state_hash": slow_hash,
                "fast_state_hash": fast_hash,
                "update_count": update_count,
                "trace_hash": trace.get("trace_hash"),
            }
        )
    fields = (
        "sequence",
        "mode",
        "energy",
        "safety",
        "deficits",
        "predictions_by_action",
        "selected_action",
        "selection_reason",
        "actual_outcome",
        "actual_delta",
        "posterior_hash",
        "slow_state_hash",
        "fast_state_hash",
        "update_count",
    )
    table_rows = [
        "<tr>"
        + "".join(
            f"<td><pre>{escape(json.dumps(row[field], ensure_ascii=False, sort_keys=True))}</pre></td>"
            for field in fields
        )
        + "</tr>"
        for row in rows
    ]
    headers = "".join(f"<th>{escape(field)}</th>" for field in fields)
    document = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>EGO V2 homeostatic learning trace</title>
<style>body{{font-family:system-ui;background:#0b1118;color:#dce7f3}}table{{border-collapse:collapse}}th,td{{border:1px solid #405267;padding:4px;vertical-align:top}}pre{{white-space:pre-wrap;max-width:420px}}</style>
</head><body><h1>EGO V2 homeostatic learning trace</h1>
<p>Data source: recovered trace rows. This renderer owns no action or update logic.</p>
<table><thead><tr>{headers}</tr></thead><tbody>{''.join(table_rows)}</tbody></table>
<script type="application/json" id="trace-data">{escape(json.dumps(rows, ensure_ascii=False, sort_keys=True))}</script>
</body></html>"""
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")
    return path


class TerminalPlayground:
    """Synchronous, paused-by-default P0 operator surface.

    Every state-changing command calls ``PlaygroundController.dispatch``;
    inspect, pause, save/load and replay do not implement a second reducer.
    """

    HELP = (
        "step | run N | learning {on|off} | predictive {on|off} | homeostatic {on|off} | pause | inspect | inject EVENT | save PATH | "
        "load RUN_ID | reset [RUN_ID] | replay | help | quit"
    )

    def __init__(self, controller: PlaygroundController) -> None:
        self.controller = controller
        self.paused = True
        self.survival_learning_mode = "off"
        self.predictive_control_mode = "off"
        self.homeostatic_transfer_mode = "off"
        self.public_featured_transfer_mode = (
            "hierarchical_bayes"
            if getattr(controller, "product_profile", "standard")
            == "public_featured_hierarchical_transfer"
            else "off"
        )

    def _interventions(self) -> dict[str, str]:
        return dict(
            DEFAULT_INTERVENTIONS,
            survival_learning_mode=self.survival_learning_mode,
            predictive_control_mode=self.predictive_control_mode,
            homeostatic_transfer_mode=self.homeostatic_transfer_mode,
            public_featured_transfer_mode=self.public_featured_transfer_mode,
        )

    def _dispatch_event(self, event: str, trigger_source: str) -> DispatchResult:
        return self.controller.dispatch(
            trigger_source=trigger_source,
            interventions=self._interventions(),
            injected_event=event,
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
            if operation == "learning":
                if len(parts) != 2 or parts[1].lower() not in {"on", "off"}:
                    raise ValueError("usage: learning {on|off}")
                self.survival_learning_mode = (
                    "expected_sarsa_lambda" if parts[1].lower() == "on" else "off"
                )
                if self.survival_learning_mode != "off":
                    self.predictive_control_mode = "off"
                    self.homeostatic_transfer_mode = "off"
                return {
                    "command": "learning",
                    "status": "ok",
                    "survival_learning_mode": self.survival_learning_mode,
                }
            if operation == "predictive":
                if len(parts) != 2 or parts[1].lower() not in {"on", "off"}:
                    raise ValueError("usage: predictive {on|off}")
                self.predictive_control_mode = (
                    "factored_mpc" if parts[1].lower() == "on" else "off"
                )
                if self.predictive_control_mode != "off":
                    self.survival_learning_mode = "off"
                    self.homeostatic_transfer_mode = "off"
                return {
                    "command": "predictive",
                    "status": "ok",
                    "predictive_control_mode": self.predictive_control_mode,
                }
            if operation == "homeostatic":
                if len(parts) != 2 or parts[1].lower() not in {"on", "off"}:
                    raise ValueError("usage: homeostatic {on|off}")
                self.homeostatic_transfer_mode = (
                    "public_bayes" if parts[1].lower() == "on" else "off"
                )
                if self.homeostatic_transfer_mode != "off":
                    self.survival_learning_mode = "off"
                    self.predictive_control_mode = "off"
                return {
                    "command": "homeostatic",
                    "status": "ok",
                    "homeostatic_transfer_mode": self.homeostatic_transfer_mode,
                }
            if operation == "step":
                if len(parts) != 1:
                    raise ValueError("usage: step")
                result = self.controller.dispatch(
                    self._interventions(),
                    trigger_source="terminal_step",
                )
                if not result.receipt.committed:
                    raise RuntimeError(result.receipt.error or "atomic commit rejected")
                self.paused = True
                return {
                    "command": "step",
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
                ticks_committed = 0
                for _ in range(ticks):
                    result = self.controller.dispatch(
                        self._interventions(),
                        trigger_source="terminal_run",
                    )
                    if not result.receipt.committed:
                        self.paused = True
                        raise RuntimeError(result.receipt.error or "atomic commit rejected")
                    ticks_committed += 1
                    lifecycle = self.controller.state.get("lifecycle", {})
                    if isinstance(lifecycle, Mapping) and lifecycle.get("trial_status") == "terminal":
                        break
                self.paused = True
                snapshot = build_terminal_snapshot(self.controller)
                return {
                    "command": "run",
                    "status": "committed",
                    "requested_ticks": ticks,
                    "ticks_committed": ticks_committed,
                    "survival_summary": {
                        "life_survival": deepcopy(snapshot["life_survival"]),
                        "terminal_life_result": deepcopy(snapshot["terminal_life_result"]),
                        "trial_status": snapshot["lifecycle"].get("trial_status"),
                    },
                    "snapshot": snapshot,
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
