#!/usr/bin/env python3
"""Callable evidence producer for the bounded action-perseveration repair."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Mapping
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import claims, engine, microworld
from scripts.codex.verify_ego_v2_p0_visual_console_live_001a import (
    run_visual_verification,
)


TASK_ID = "EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A-R1"
RUN_ID = "life-visual-001"
RUN_SEED = 701
DIAGNOSTIC_PATH = (
    REPO_ROOT
    / "artifacts"
    / "EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A"
    / "diagnostic_readback.json"
)
RED_OUTPUT_PATH = (
    REPO_ROOT.parent
    / "external-plans"
    / "EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A"
    / "PHASE-III-RED.txt"
)
CLAIM_CEILING = (
    "Local default-off visual console engineering repair on the frozen command stream: "
    "claim retrieval is conditioned on recorded public cue and current goal, zero-distance "
    "site repeats do not create outcomes, and legal positive current-goal progress precedes "
    "zero-or-negative progress. Evidence is limited to canonical controller/SQLite/replay "
    "integration and this frozen distribution; it does not establish general learning, "
    "memory causality, initiative, agency, emotion, subjectivity, consciousness, electronic "
    "life, product readiness, or user value."
)
REQUIRED_ARTIFACTS = {
    "result.json",
    "trace.jsonl",
    "baseline_comparison.json",
    "ablation_report.json",
    "replay_report.json",
    "leakage_report.json",
    "failure_manifest.json",
    "diagnostic_readback.json",
    "live_repair_receipt.json",
    "claim_ceiling.txt",
}
FORBIDDEN_VALUES = (
    "oracle_evidence_record",
    "private_dynamics",
    "hidden_regime",
    "correct_action",
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file_record(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": _sha256(raw)}


def _code_path_hash() -> str:
    return _sha256(
        _canonical_bytes(
            {
                "candidate_code_path_hash": engine.compute_code_path_hash(),
                "verifier_sha256": _file_record(Path(__file__))["sha256"],
            }
        )
    )


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _evidence(value: bool, *, producer_function: str, inputs: list[Any]) -> dict[str, Any]:
    return {
        "evidence_record_type": "computed_evidence",
        "producer_function": producer_function,
        "input_artifacts": deepcopy(inputs),
        "run_id": RUN_ID,
        "seed_context_episode_ids": {
            "run_seed": RUN_SEED,
            "context_ids": ["frozen_71_command_stream", "post_71_social_signal"],
        },
        "aggregation_rule": "boolean result from the named callable computation path",
        "code_path_hash": _code_path_hash(),
        "value": bool(value),
    }


def aggregate_checks(checks: Mapping[str, Any]) -> dict[str, Any]:
    failed: list[str] = []
    for name, record in checks.items():
        if not isinstance(record, Mapping) or type(record.get("value")) is not bool:
            raise ValueError(f"computed check record required: {name}")
        if record["value"] is not True:
            failed.append(str(name))
    return {"verdict": "pass" if not failed else "fail", "failed_checks": sorted(failed)}


def scan_forbidden_values(value: Any) -> dict[str, Any]:
    """Scan actual keys and strings; the scanner constants do not self-match."""

    matches: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                key_text = str(key)
                for token in FORBIDDEN_VALUES:
                    if token in key_text:
                        matches.add(token)
                visit(nested)
        elif isinstance(item, list):
            for nested in item:
                visit(nested)
        elif isinstance(item, str):
            for token in FORBIDDEN_VALUES:
                if token in item:
                    matches.add(token)

    visit(value)
    return {
        "producer_function": "scan_forbidden_values",
        "input_hash": _sha256(_canonical_bytes(value)),
        "matches": sorted(matches),
    }


def _action_summary(actions: list[str]) -> dict[str, Any]:
    trailing_forage = 0
    for action in reversed(actions):
        if action != "forage":
            break
        trailing_forage += 1
    return {
        "action_counts": dict(sorted(Counter(actions).items())),
        "action_sequence_hash": _sha256(_canonical_bytes(actions)),
        "trailing_forage_suffix": trailing_forage,
        "sequence_length": len(actions),
    }


def always_forage_baseline(command_count: int) -> list[str]:
    return ["forage" for _ in range(command_count)]


def round_robin_baseline(command_count: int) -> list[str]:
    actions = tuple(engine.ACTIONS)
    return [actions[index % len(actions)] for index in range(command_count)]


def seeded_hash_baseline(command_count: int, seed: int) -> list[str]:
    actions = tuple(engine.ACTIONS)
    return [
        actions[int(hashlib.sha256(f"{seed}:{index}".encode()).hexdigest()[:16], 16) % len(actions)]
        for index in range(command_count)
    ]


def _replay_commands(diagnostic: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    state = deepcopy(diagnostic["initial_state"])
    meta = engine.make_run_metadata(str(diagnostic["run_id"]), int(diagnostic["seed"]))
    traces: list[dict[str, Any]] = []
    for command in diagnostic["commands"]:
        step = engine.compute_step(state, deepcopy(command), meta)
        state = step.next_state
        traces.append(step.trace)
    return state, traces


def _post_71_command(state: Mapping[str, Any], diagnostic: Mapping[str, Any]) -> dict[str, Any]:
    event = "social_signal"
    return engine.make_command(
        sequence=len(diagnostic["commands"]) + 1,
        cue=microworld.cue_for_event(event),
        world_event=event,
        trigger_source="ui_step_button",
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=state["last_command_hash"],
    )


def legacy_unfiltered_claim_retrieval(
    memory: Mapping[str, Any], *, observation: Mapping[str, Any], current_goal: str
) -> dict[str, Any]:
    """Independent hostile baseline reproducing the removed all-context shortcut."""

    claims.verify_claim_memory(memory)
    position = str(observation.get("agent_position", "unknown"))
    association = 1.0 if position == "fork" else 0.65
    retrieved: list[dict[str, Any]] = []
    for claim in memory["competing_claims"]:
        if claim["subject"] != "microworld:opaque_fork":
            continue
        item = deepcopy(claim)
        item["association_score"] = association
        item["retrieval_score"] = round(float(claim["support"]) * association, 6)
        item["eligible_provenance_event_ids"] = list(item["provenance_event_ids"])
        retrieved.append(item)
    retrieved.sort(key=lambda item: (-float(item["retrieval_score"]), str(item["value"])))
    support = [float(item["retrieval_score"]) for item in retrieved]
    refs = sorted(
        {event_id for item in retrieved for event_id in item["provenance_event_ids"]}
    )
    support_by_action = {
        str(item["value"]): float(item["retrieval_score"]) for item in retrieved
    }
    return {
        "schema_version": claims.CLAIM_RETRIEVAL_SCHEMA_VERSION,
        "status": "retrieved" if retrieved else "no_matching_claims",
        "producer_function": "legacy_unfiltered_claim_retrieval",
        "query": {
            "subject": "microworld:opaque_fork",
            "predicate": "preferred_site_action",
            "agent_position": position,
            "cue": observation.get("cue"),
            "current_goal": current_goal,
        },
        "claims": retrieved,
        "withheld_claims": [],
        "support_by_action": support_by_action,
        "raw_support_by_action": deepcopy(support_by_action),
        "support_margin": round(max(support) - min(support), 6) if len(support) >= 2 else 0.0,
        "uncertainty": round(1.0 / (1.0 + max(support) - min(support)), 6)
        if len(support) >= 2
        else 1.0,
        "provenance_event_ids": refs,
        "withheld_provenance_event_ids": [],
        "source_episode_ids": sorted(
            {episode_id for item in retrieved for episode_id in item["source_episode_ids"]}
        ),
    }


def legacy_score_argmax(candidates: list[Mapping[str, Any]]) -> str:
    """Independent old selection baseline that ignores the progress eligibility gate."""

    return str(
        max(
            (item for item in candidates if item["legal"]),
            key=lambda item: (item["total_score"], item["deterministic_tie"]),
        )["action"]
    )


def _zero_distance_repeat() -> dict[str, Any]:
    run_id = "action-repair-zero-distance-evidence"
    state = engine.initial_state(
        {"energy": 0.0, "safety": 0.9, "connection": 0.9, "stimulation": 0.9},
        run_id=run_id,
        seed=18,
    )
    meta = engine.make_run_metadata(run_id, 18)
    traces: list[dict[str, Any]] = []
    for sequence in (1, 2):
        event = "resource_appears"
        command = engine.make_command(
            sequence=sequence,
            cue=microworld.cue_for_event(event),
            world_event=event,
            trigger_source="paired_intervention",
            interventions=engine.DEFAULT_INTERVENTIONS,
            prev_command_hash=state["last_command_hash"],
        )
        step = engine.compute_step(state, command, meta)
        state = step.next_state
        traces.append(step.trace)
    return {
        "producer_function": "_zero_distance_repeat",
        "selected_actions": [trace["selected_action"] for trace in traces],
        "first_moved": traces[0]["world_transition"]["moved"],
        "second_moved": traces[1]["world_transition"]["moved"],
        "second_outcome": traces[1]["world_transition"]["outcome"],
        "second_claim_update_applied": traces[1]["claim_update"]["applied"],
        "second_claim_update_reason": traces[1]["claim_update"]["reason"],
    }


def _matched_context_scoring_probe() -> dict[str, Any]:
    """Run context-matched claims through the real candidate scorer."""

    run_id = "action-repair-matched-context-probe"
    seed = 29
    state = engine.initial_state(
        {
            "energy": 0.9,
            "safety": 0.9,
            "connection": 0.2,
            "stimulation": 0.9,
        },
        run_id=run_id,
        seed=seed,
        layout_id="p2_offset_v1",
    )
    claim_state = claims.empty_claim_memory()
    for sequence, action, strength in (
        (1, "approach", 1.0),
        (2, "forage", -1.0),
    ):
        claim_state, _ = claims.record_outcome_evidence(
            claim_state,
            subject="microworld:opaque_fork",
            predicate="preferred_site_action",
            value=action,
            evidence_strength=strength,
            event_id=f"matched-context-{action}",
            source_episode_id="episode-matched-context",
            source_command_hash=(str(sequence) * 64),
            source_sequence=sequence,
            observed_public_features={
                "agent_position": "fork",
                "visible_object_ids": ["signal"],
                "cue": "contact",
                "current_goal": "connection",
            },
        )
    state["memory"].update(claim_state)
    command = engine.make_command(
        sequence=1,
        cue="contact",
        world_event="social_signal",
        trigger_source="paired_intervention",
        interventions=engine.DEFAULT_INTERVENTIONS,
        prev_command_hash=None,
    )
    meta = engine.make_run_metadata(run_id, seed)
    canonical = engine.compute_step(deepcopy(state), command, meta)
    memory_off_command = deepcopy(command)
    memory_off_command["interventions"] = dict(
        engine.DEFAULT_INTERVENTIONS, memory_mode="off"
    )
    memory_off_command["command_hash"] = engine.canonical_hash(
        {
            key: value
            for key, value in memory_off_command.items()
            if key != "command_hash"
        }
    )
    memory_off = engine.compute_step(deepcopy(state), memory_off_command, meta)
    canonical_candidates = {
        str(item["action"]): item for item in canonical.trace["candidates"]
    }
    memory_off_candidates = {
        str(item["action"]): item for item in memory_off.trace["candidates"]
    }
    return {
        "producer_function": "claims.record_outcome_evidence -> engine.compute_step",
        "query": deepcopy(canonical.trace["claim_retrieval"]["query"]),
        "support_by_action": deepcopy(
            canonical.trace["claim_retrieval"]["support_by_action"]
        ),
        "provenance_event_ids": list(
            canonical.trace["claim_retrieval"]["provenance_event_ids"]
        ),
        "canonical_selected_action": canonical.trace["selected_action"],
        "memory_off_selected_action": memory_off.trace["selected_action"],
        "approach_claim_memory_bias": canonical_candidates["approach"][
            "claim_memory_bias"
        ],
        "approach_total_score": canonical_candidates["approach"]["total_score"],
        "memory_off_approach_total_score": memory_off_candidates["approach"][
            "total_score"
        ],
        "context_memory_eligible": canonical_candidates["approach"][
            "context_memory_eligible"
        ],
    }


def run_action_repair_verification(
    output_dir: str | Path, *, screenshot_path: str | Path
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    diagnostic_target = output / "diagnostic_readback.json"
    if diagnostic_target.resolve() != DIAGNOSTIC_PATH.resolve():
        shutil.copyfile(DIAGNOSTIC_PATH, diagnostic_target)
    diagnostic = json.loads(diagnostic_target.read_text(encoding="utf-8"))
    inputs = [_file_record(diagnostic_target), _file_record(Path(__file__))]

    repaired_state, repaired_traces = _replay_commands(diagnostic)
    _, second_traces = _replay_commands(diagnostic)
    repaired_actions = [str(trace["selected_action"]) for trace in repaired_traces]
    second_hashes_equal = [trace["trace_hash"] for trace in repaired_traces] == [
        trace["trace_hash"] for trace in second_traces
    ]

    with (output / "trace.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for trace in repaired_traces:
            handle.write(json.dumps({"record_type": "trace", "trace": trace}, ensure_ascii=False, sort_keys=True) + "\n")

    old_actions = [str(item["selected_action"]) for item in diagnostic["stored_trace_summary"]]
    baseline = {
        "schema_version": "ego.action_repair.baseline_comparison.v1",
        "producer_function": "run_action_repair_verification.baseline_comparison",
        "input_artifacts": inputs,
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED, "command_count": len(old_actions)},
        "aggregation_rule": "compare trailing identical action suffix and action counts on the exact frozen command stream",
        "code_path_hash": _code_path_hash(),
        "frozen_old_trace": _action_summary(old_actions),
        "repaired_replay": _action_summary(repaired_actions),
        "always_forage_baseline": _action_summary(always_forage_baseline(len(old_actions))),
        "round_robin_baseline": _action_summary(round_robin_baseline(len(old_actions))),
        "seeded_hash_baseline": _action_summary(seeded_hash_baseline(len(old_actions), RUN_SEED)),
    }

    frozen_state = deepcopy(diagnostic["old_final_state"])
    meta = engine.make_run_metadata(str(diagnostic["run_id"]), int(diagnostic["seed"]))
    post_command = _post_71_command(frozen_state, diagnostic)
    default_step = engine.compute_step(deepcopy(frozen_state), post_command, meta)
    memory_off_command = deepcopy(post_command)
    memory_off_command["interventions"] = dict(
        engine.DEFAULT_INTERVENTIONS, memory_mode="off"
    )
    memory_off_command["command_hash"] = engine.canonical_hash(
        {key: value for key, value in memory_off_command.items() if key != "command_hash"}
    )
    memory_off_step = engine.compute_step(
        deepcopy(frozen_state), memory_off_command, meta
    )
    with patch.object(
        engine.claim_memory,
        "retrieve_competing_claims",
        side_effect=legacy_unfiltered_claim_retrieval,
    ):
        unfiltered_step = engine.compute_step(deepcopy(frozen_state), post_command, meta)
    legacy_selected = legacy_score_argmax(unfiltered_step.trace["candidates"])
    zero_distance = _zero_distance_repeat()
    matched_context = _matched_context_scoring_probe()
    ablation = {
        "schema_version": "ego.action_repair.ablation_report.v1",
        "producer_function": "run_action_repair_verification.ablation_report",
        "input_artifacts": inputs,
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED, "post_sequence": len(old_actions) + 1},
        "aggregation_rule": "rerun the frozen post-71 state under named callable retrieval/memory/selection interventions",
        "code_path_hash": _code_path_hash(),
        "canonical_context_filter": {
            "selected_action": default_step.trace["selected_action"],
            "support_by_action": default_step.trace["claim_retrieval"]["support_by_action"],
            "raw_support_by_action": default_step.trace["claim_retrieval"]["raw_support_by_action"],
            "withheld_count": len(default_step.trace["claim_retrieval"]["withheld_provenance_event_ids"]),
        },
        "memory_off": {"selected_action": memory_off_step.trace["selected_action"]},
        "unfiltered_claims_with_progress_gate": {
            "producer_function": "legacy_unfiltered_claim_retrieval -> engine.compute_step",
            "selected_action": unfiltered_step.trace["selected_action"],
        },
        "unfiltered_claims_without_progress_gate": {
            "producer_function": "legacy_score_argmax",
            "selected_action": legacy_selected,
        },
        "zero_distance_repeat": zero_distance,
        "matched_context_scoring_probe": matched_context,
    }

    policy_scan = scan_forbidden_values(
        [
            {
                "policy_projection": trace["policy_projection"],
                "candidates": trace["candidates"],
                "claim_retrieval": trace["claim_retrieval"],
            }
            for trace in repaired_traces
        ]
    )
    positive_scan = scan_forbidden_values(
        {"observation": {"cue": "contact"}, "hidden_regime": "positive-control"}
    )
    leakage = {
        "schema_version": "ego.action_repair.leakage_report.v1",
        "producer_function": "scan_forbidden_values",
        "input_artifacts": inputs,
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED, "trace_count": len(repaired_traces)},
        "aggregation_rule": "policy-facing values must scan clean and the hostile private-field control must fire",
        "code_path_hash": _code_path_hash(),
        "policy_scan": policy_scan,
        "positive_control_scan": positive_scan,
    }

    replay_report = {
        "schema_version": "ego.action_repair.replay_report.v1",
        "producer_function": "_replay_commands",
        "input_artifacts": [*inputs, _file_record(output / "trace.jsonl")],
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED, "command_count": len(repaired_traces)},
        "aggregation_rule": "recompute twice from serialized initial_state plus every ordered command and require exact trace hashes",
        "code_path_hash": _code_path_hash(),
        "command_count": len(repaired_traces),
        "second_recompute_trace_hashes_equal": second_hashes_equal,
        "final_state_hash": engine.state_hash(repaired_state),
        "unused_frozen_commands": [],
        "stored_selected_action_used_as_input": False,
    }

    screenshot = Path(screenshot_path)
    with tempfile.TemporaryDirectory(prefix="ego-action-repair-visual-") as temp_name:
        visual_output = Path(temp_name) / "evidence"
        visual_result = run_visual_verification(
            visual_output, screenshot_path=screenshot
        )
        visual_receipt = json.loads(
            (visual_output / "live_ui_receipt.json").read_text(encoding="utf-8")
        )
        visual_result_record = _file_record(visual_output / "result.json")
        visual_result_record["path"] = "generated://visual-console-verifier/result.json"
    live_receipt = {
        "schema_version": "ego.action_repair.live_repair_receipt.v1",
        "producer_function": "run_visual_verification",
        "input_artifacts": inputs,
        "run_id": visual_result["run_id"],
        "seed_context_episode_ids": visual_result["seed_context_episode_ids"],
        "aggregation_rule": "real Tk Step/Run must traverse canonical dispatch, SQLite commit, recover, and trace waypoint animation",
        "code_path_hash": _code_path_hash(),
        "visual_verifier_verdict": visual_result["verdict"],
        "visual_result_record": visual_result_record,
        "visual_check_values": {
            name: record["value"] for name, record in visual_result["checks"].items()
        },
        "real_tk_trigger": visual_result["checks"]["ui_step_calls_canonical_dispatch"]["value"],
        "sqlite_commit": visual_result["checks"]["sqlite_committed_transition"]["value"],
        "fresh_recover": visual_result["checks"]["fresh_process_recover"]["value"],
        "waypoints_equal_recovered_trace": visual_result["checks"]["scheduled_waypoints_equal_trace"]["value"],
        "run_lockstep": visual_result["checks"]["run_commit_recover_animate_lockstep"]["value"],
        "pause_close_zero_extra_dispatch": visual_result["checks"]["pause_close_zero_extra_dispatch"]["value"],
        "default_off": visual_receipt["default_off"],
        "runtime_authority": visual_receipt["runtime_authority"],
        "screenshot": _file_record(screenshot),
    }

    checks = {
        "frozen_old_trace_recompute_was_bound": _evidence(
            diagnostic["old_replay_provenance"]["matched_trace_hashes"] == 71
            and diagnostic["old_trace_hash_recompute_match_count"] == 71,
            producer_function="freeze_old_final_state.main",
            inputs=inputs,
        ),
        "frozen_suffix_removed_with_action_variation": _evidence(
            baseline["frozen_old_trace"]["trailing_forage_suffix"] == 62
            and baseline["repaired_replay"]["trailing_forage_suffix"] < 62
            and len(baseline["repaired_replay"]["action_counts"]) >= 4,
            producer_function="_replay_commands + _action_summary",
            inputs=inputs,
        ),
        "post_71_matches_memory_off": _evidence(
            default_step.trace["selected_action"]
            == memory_off_step.trace["selected_action"]
            == "approach",
            producer_function="engine.compute_step memory intervention pair",
            inputs=inputs,
        ),
        "mismatched_claims_are_observable_but_inert": _evidence(
            default_step.trace["claim_retrieval"]["support_by_action"] == {}
            and bool(default_step.trace["claim_retrieval"]["raw_support_by_action"])
            and bool(default_step.trace["claim_retrieval"]["withheld_provenance_event_ids"]),
            producer_function="claims.retrieve_competing_claims",
            inputs=inputs,
        ),
        "matched_context_memory_reaches_candidate_score": _evidence(
            matched_context["support_by_action"]
            == {"approach": 0.65, "forage": -0.65}
            and matched_context["provenance_event_ids"]
            == ["matched-context-approach", "matched-context-forage"]
            and matched_context["context_memory_eligible"] is True
            and matched_context["approach_claim_memory_bias"] != 0.0
            and matched_context["approach_total_score"]
            != matched_context["memory_off_approach_total_score"],
            producer_function=(
                "claims.record_outcome_evidence -> "
                "claims.retrieve_competing_claims -> engine.compute_step"
            ),
            inputs=inputs,
        ),
        "hostile_unfiltered_no_progress_baseline_reproduces_forage": _evidence(
            unfiltered_step.trace["selected_action"] == "approach"
            and legacy_selected == "forage",
            producer_function="legacy_unfiltered_claim_retrieval + legacy_score_argmax",
            inputs=inputs,
        ),
        "zero_distance_repeat_is_outcome_inert": _evidence(
            zero_distance["first_moved"] is True
            and zero_distance["second_moved"] is False
            and zero_distance["second_outcome"] is None
            and zero_distance["second_claim_update_applied"] is False,
            producer_function="_zero_distance_repeat",
            inputs=inputs,
        ),
        "replay_recomputes_every_frozen_command": _evidence(
            second_hashes_equal and len(repaired_traces) == len(diagnostic["commands"]),
            producer_function="_replay_commands",
            inputs=inputs,
        ),
        "leakage_scan_and_positive_control": _evidence(
            policy_scan["matches"] == []
            and positive_scan["matches"] == ["hidden_regime"],
            producer_function="scan_forbidden_values",
            inputs=inputs,
        ),
        "real_visual_console_path_still_passes": _evidence(
            visual_result["verdict"] == "pass"
            and live_receipt["real_tk_trigger"] is True
            and live_receipt["sqlite_commit"] is True
            and live_receipt["fresh_recover"] is True
            and live_receipt["waypoints_equal_recovered_trace"] is True,
            producer_function="run_visual_verification",
            inputs=inputs,
        ),
    }
    aggregation = aggregate_checks(checks)
    result = {
        "schema_version": "ego.action_repair.result.v1",
        "task_id": TASK_ID,
        "producer_function": "run_action_repair_verification",
        "input_artifacts": [*inputs, _file_record(output / "trace.jsonl")],
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED, "command_count": len(repaired_traces)},
        "aggregation_rule": "pass iff every named computed repair and live-path check is true",
        "code_path_hash": _code_path_hash(),
        "checks": checks,
        "verdict": aggregation["verdict"],
        "failed_checks": aggregation["failed_checks"],
        "claim_ceiling": CLAIM_CEILING,
    }
    red_record = (
        _file_record(RED_OUTPUT_PATH)
        if RED_OUTPUT_PATH.is_file()
        else {"path": str(RED_OUTPUT_PATH), "status": "unavailable"}
    )
    failure_manifest = {
        "schema_version": "ego.action_repair.failure_manifest.v1",
        "producer_function": "run_action_repair_verification.failure_manifest",
        "input_artifacts": inputs,
        "run_id": RUN_ID,
        "seed_context_episode_ids": {"run_seed": RUN_SEED},
        "aggregation_rule": "preserve pre-repair negative evidence and never translate it into the scoped verdict",
        "code_path_hash": _code_path_hash(),
        "scoped_verdict_failures": aggregation["failed_checks"],
        "preserved_negative_evidence": {
            "tdd_red": red_record,
            "old_trailing_forage_suffix": diagnostic["old_trailing_forage_suffix"],
            "old_action_counts": diagnostic["old_action_counts"],
            "historical_p1_claim": "memory_conditioned_effect_not_observed_in_frozen_pair",
        },
        "full_repository_suite": "not_claimed_by_this_scoped_verifier",
    }

    _write_json(output / "baseline_comparison.json", baseline)
    _write_json(output / "ablation_report.json", ablation)
    _write_json(output / "replay_report.json", replay_report)
    _write_json(output / "leakage_report.json", leakage)
    _write_json(output / "live_repair_receipt.json", live_receipt)
    _write_json(output / "failure_manifest.json", failure_manifest)
    _write_json(output / "result.json", result)
    (output / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
    )
    actual = {path.name for path in output.iterdir() if path.is_file()}
    if actual != REQUIRED_ARTIFACTS:
        raise RuntimeError(f"action repair evidence output set is not exact: {sorted(actual)}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--screenshot", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_action_repair_verification(
        args.output_dir, screenshot_path=args.screenshot
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
