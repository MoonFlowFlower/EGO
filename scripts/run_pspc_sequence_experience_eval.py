#!/usr/bin/env python3
"""Run PSPC sequence-experience eval as artifact-only shadow evidence.

This runner tests whether controlled history sequences can produce different
shadow-only relationship/self-state profiles for the same trigger. It never
calls EgoOperator runtime, gates, memory, transport, PSPC planner, training, or
model execution.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
for candidate in (ROOT, SCRIPT_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from pspc_shadow_contracts import (  # noqa: E402
    SIDE_EFFECTS_FALSE,
    runtime_field_hits,
    scan_active_runtime_sources,
    sha256_text,
)


CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only"
SOURCE = "pspc_sequence_experience_eval_v0"
DEFAULT_DATASET = Path("docs") / "codex" / "tasks" / "pspc-sequence-experience-eval-v0" / "sequence_eval_dataset_v0.jsonl"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_sequence_experience_eval_v0"
FLAG_CONTRACT = Path("artifacts") / "pspc_disabled_runtime_flag_contract_v0" / "disabled_runtime_flag_contract.json"
TRIGGER_TEXT = "我回来了。"
ACTIVE_RUNTIME_SCAN_MARKERS = (
    "run_pspc_sequence_experience_eval",
    "pspc_sequence_experience_eval",
    "sequence_experience_eval",
)

STATE_KEYS = (
    "trust",
    "stress",
    "affinity",
    "approach_tendency",
    "avoidance_tendency",
    "care_tendency",
    "boundary_expression",
    "low_interrupt",
    "late_night_pattern",
    "preference_conflict",
)

CATEGORY_DELTAS: dict[str, dict[str, float]] = {
    "gentle_interaction": {
        "trust": 0.085,
        "stress": -0.045,
        "affinity": 0.065,
        "approach_tendency": 0.075,
        "avoidance_tendency": -0.030,
        "care_tendency": 0.020,
        "boundary_expression": -0.010,
        "low_interrupt": 0.030,
        "late_night_pattern": 0.000,
        "preference_conflict": 0.000,
    },
    "frequent_interruption": {
        "trust": -0.065,
        "stress": 0.095,
        "affinity": -0.035,
        "approach_tendency": -0.075,
        "avoidance_tendency": 0.090,
        "care_tendency": 0.005,
        "boundary_expression": 0.080,
        "low_interrupt": 0.020,
        "late_night_pattern": 0.000,
        "preference_conflict": 0.010,
    },
    "late_night_care": {
        "trust": 0.020,
        "stress": 0.025,
        "affinity": 0.015,
        "approach_tendency": 0.010,
        "avoidance_tendency": 0.000,
        "care_tendency": 0.085,
        "boundary_expression": 0.005,
        "low_interrupt": 0.075,
        "late_night_pattern": 0.095,
        "preference_conflict": 0.000,
    },
}

EXPECTED_FUTURE_BEHAVIOR = {
    "gentle_interaction": "approach",
    "frequent_interruption": "avoid_or_set_boundary",
    "late_night_care": "care_low_interrupt",
}


def empty_state() -> dict[str, float]:
    return {key: 0.0 for key in STATE_KEYS}


def round_state(state: dict[str, float]) -> dict[str, float]:
    return {key: round(float(state.get(key, 0.0)), 4) for key in STATE_KEYS}


def clamp(value: float, lower: float = -1.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def bounded_positive(value: float) -> float:
    return round(clamp(value, 0.0, 1.0), 4)


def vector_distance(a: dict[str, float], b: dict[str, float], keys: tuple[str, ...] = STATE_KEYS) -> float:
    return math.sqrt(sum((float(a.get(key, 0.0)) - float(b.get(key, 0.0))) ** 2 for key in keys))


def load_dataset(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError(f"line {line_number} must be a JSON object")
        group_id = item.get("group_id")
        history = item.get("history_inputs")
        trigger = item.get("trigger")
        if group_id not in CATEGORY_DELTAS:
            raise ValueError(f"line {line_number} has unknown group_id {group_id!r}")
        if not isinstance(history, list) or len(history) != 10 or not all(isinstance(text, str) and text for text in history):
            raise ValueError(f"line {line_number} history_inputs must contain 10 non-empty strings")
        if trigger != TRIGGER_TEXT:
            raise ValueError(f"line {line_number} trigger must be {TRIGGER_TEXT!r}")
        records.append(
            {
                "group_id": group_id,
                "history_inputs": history,
                "trigger": trigger,
                "expected_trigger_profile": item.get("expected_trigger_profile") or {},
                "must_not": item.get("must_not") or [],
            }
        )
    if sorted(record["group_id"] for record in records) != sorted(CATEGORY_DELTAS):
        raise ValueError("dataset must contain exactly gentle_interaction, frequent_interruption, and late_night_care")
    return records


def scaled_delta(category: str, turn_index: int, text: str) -> tuple[dict[str, float], float]:
    base = CATEGORY_DELTAS[category]
    recency_weight = 0.82 + min(turn_index, 10) * 0.018
    text_sensitivity = 1.0 + min(len(text), 32) / 640.0
    delta = {key: round(base[key] * recency_weight * text_sensitivity, 4) for key in STATE_KEYS}
    salience = bounded_positive(sum(abs(value) for value in delta.values()) / 0.55)
    return delta, salience


def apply_delta(state: dict[str, float], delta: dict[str, float]) -> dict[str, float]:
    next_state = {}
    for key in STATE_KEYS:
        decayed = state[key] * 0.986
        next_state[key] = round(clamp(decayed + delta.get(key, 0.0)), 4)
    return next_state


def build_turn_record(
    sequence_id: str,
    category: str,
    turn_index: int,
    text: str,
    state_before: dict[str, float],
) -> tuple[dict[str, Any], dict[str, float]]:
    delta, salience = scaled_delta(category, turn_index, text)
    state_after = apply_delta(state_before, delta)
    shadow_memory_event = {
        "shadow_memory_candidate": salience >= 0.35,
        "salience": salience,
        "expected_future_behavior": EXPECTED_FUTURE_BEHAVIOR[category],
        "trace_ref": f"{sequence_id}:history:{turn_index:02d}",
        "audit_only": True,
        "non_executable": True,
    }
    return (
        {
            "turn_index": turn_index,
            "category": category,
            "user_text": text,
            "user_text_hash": sha256_text(text),
            "state_before": round_state(state_before),
            "state_delta": round_state(delta),
            "state_after": round_state(state_after),
            "shadow_memory_event": shadow_memory_event,
            "salience": salience,
            "expected_future_behavior": EXPECTED_FUTURE_BEHAVIOR[category],
            "runtime_field_hits": runtime_field_hits(shadow_memory_event),
        },
        state_after,
    )


def trigger_profile(state: dict[str, float]) -> dict[str, Any]:
    approach = bounded_positive(
        state["approach_tendency"]
        + state["trust"] * 0.45
        + state["affinity"] * 0.20
        - state["stress"] * 0.25
        - state["avoidance_tendency"] * 0.15
    )
    avoidance = bounded_positive(
        state["avoidance_tendency"]
        + state["stress"] * 0.45
        + state["boundary_expression"] * 0.25
        - state["trust"] * 0.20
    )
    care = bounded_positive(state["care_tendency"] + state["late_night_pattern"] * 0.55 + state["stress"] * 0.10)
    boundary = bounded_positive(state["boundary_expression"] + state["avoidance_tendency"] * 0.15)
    low_interrupt = bounded_positive(state["low_interrupt"] + state["care_tendency"] * 0.25 + state["late_night_pattern"] * 0.20)
    scores = {
        "approach_tendency": approach,
        "avoidance_tendency": avoidance,
        "care_tendency": care,
        "boundary_expression": boundary,
        "low_interrupt": low_interrupt,
    }
    dominant_key, dominant_score = max(scores.items(), key=lambda item: item[1])
    dominant = "neutral" if dominant_score < 0.16 else dominant_key.replace("_tendency", "")
    return {
        **scores,
        "dominant_tendency": dominant,
    }


def evaluate_sequence(sequence_id: str, category: str, history_inputs: list[str], trigger: str) -> dict[str, Any]:
    state = empty_state()
    turns: list[dict[str, Any]] = []
    for turn_index, text in enumerate(history_inputs, start=1):
        turn, state = build_turn_record(sequence_id, category, turn_index, text, state)
        turns.append(turn)
    profile = trigger_profile(state)
    observation = {
        "source": SOURCE,
        "claim_level": "lab_only_proto_self_mechanism_candidate",
        "claim_ceiling": CLAIM_CEILING,
        "sequence_id": sequence_id,
        "history_category": category,
        "history_turn_count": len(history_inputs),
        "trigger": trigger,
        "state_after_history": round_state(state),
        "trigger_behavior_profile": profile,
        "reason_trace_refs": [turn["shadow_memory_event"]["trace_ref"] for turn in turns[-3:]],
        "evidence_refs": [str(FLAG_CONTRACT)],
        "audit_only": True,
        "read_only": True,
        "non_executable": True,
        "can_drive_runtime": False,
        "can_change_user_response": False,
        "can_write_memory": False,
        "can_invoke_gate": False,
    }
    return {
        "sequence_id": sequence_id,
        "category": category,
        "history_turns": turns,
        "shadow_observation": observation,
        "runtime_field_hits": runtime_field_hits(observation) + [hit for turn in turns for hit in turn["runtime_field_hits"]],
        "side_effects": dict(SIDE_EFFECTS_FALSE),
    }


def build_controls(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    no_history = {
        "sequence_id": "control_no_history",
        "category": "no_history",
        "history_turns": [],
        "shadow_observation": {
            "source": SOURCE,
            "claim_level": "lab_only_proto_self_mechanism_candidate",
            "claim_ceiling": CLAIM_CEILING,
            "sequence_id": "control_no_history",
            "history_category": "no_history",
            "history_turn_count": 0,
            "trigger": TRIGGER_TEXT,
            "state_after_history": round_state(empty_state()),
            "trigger_behavior_profile": trigger_profile(empty_state()),
            "reason_trace_refs": [],
            "evidence_refs": [str(FLAG_CONTRACT)],
            "audit_only": True,
            "read_only": True,
            "non_executable": True,
            "can_drive_runtime": False,
            "can_change_user_response": False,
            "can_write_memory": False,
            "can_invoke_gate": False,
        },
        "runtime_field_hits": [],
        "side_effects": dict(SIDE_EFFECTS_FALSE),
    }
    mixed_inputs: list[tuple[str, str]] = []
    by_group = {record["group_id"]: record["history_inputs"] for record in records}
    for index in range(10):
        category = ("gentle_interaction", "frequent_interruption", "late_night_care")[index % 3]
        mixed_inputs.append((category, by_group[category][index]))
    state = empty_state()
    turns: list[dict[str, Any]] = []
    for turn_index, (category, text) in enumerate(mixed_inputs, start=1):
        turn, state = build_turn_record("control_shuffled_history", category, turn_index, text, state)
        turns.append(turn)
    observation = {
        "source": SOURCE,
        "claim_level": "lab_only_proto_self_mechanism_candidate",
        "claim_ceiling": CLAIM_CEILING,
        "sequence_id": "control_shuffled_history",
        "history_category": "shuffled_history",
        "history_turn_count": len(turns),
        "trigger": TRIGGER_TEXT,
        "state_after_history": round_state(state),
        "trigger_behavior_profile": trigger_profile(state),
        "reason_trace_refs": [turn["shadow_memory_event"]["trace_ref"] for turn in turns[-3:]],
        "evidence_refs": [str(FLAG_CONTRACT)],
        "audit_only": True,
        "read_only": True,
        "non_executable": True,
        "can_drive_runtime": False,
        "can_change_user_response": False,
        "can_write_memory": False,
        "can_invoke_gate": False,
    }
    shuffled = {
        "sequence_id": "control_shuffled_history",
        "category": "shuffled_history",
        "history_turns": turns,
        "shadow_observation": observation,
        "runtime_field_hits": runtime_field_hits(observation) + [hit for turn in turns for hit in turn["runtime_field_hits"]],
        "side_effects": dict(SIDE_EFFECTS_FALSE),
    }
    return [no_history, shuffled]


def profile_for(sequence_result: dict[str, Any]) -> dict[str, float]:
    profile = sequence_result["shadow_observation"]["trigger_behavior_profile"]
    return {
        "approach_tendency": profile["approach_tendency"],
        "avoidance_tendency": profile["avoidance_tendency"],
        "care_tendency": profile["care_tendency"],
        "boundary_expression": profile["boundary_expression"],
        "low_interrupt": profile["low_interrupt"],
    }


def build_checks(sequences: list[dict[str, Any]], controls: list[dict[str, Any]], runtime_scan: dict[str, Any]) -> dict[str, bool]:
    by_category = {sequence["category"]: sequence for sequence in sequences + controls}
    gentle = by_category["gentle_interaction"]
    interruption = by_category["frequent_interruption"]
    late = by_category["late_night_care"]
    no_history = by_category["no_history"]
    shuffled = by_category["shuffled_history"]
    gentle_state = gentle["shadow_observation"]["state_after_history"]
    interruption_state = interruption["shadow_observation"]["state_after_history"]
    late_state = late["shadow_observation"]["state_after_history"]
    gentle_profile = profile_for(gentle)
    interruption_profile = profile_for(interruption)
    late_profile = profile_for(late)
    no_history_profile = profile_for(no_history)
    shuffled_profile = profile_for(shuffled)
    all_results = sequences + controls
    clean_profiles = [gentle_profile, interruption_profile, late_profile]
    return {
        "dataset_has_three_groups": len(sequences) == 3,
        "each_group_has_ten_history_inputs": all(len(sequence["history_turns"]) == 10 for sequence in sequences),
        "controls_present": set(by_category) >= {"no_history", "shuffled_history"},
        "gentle_trigger_biases_approach_trust": gentle_profile["approach_tendency"] > 0.58
        and gentle_state["trust"] > 0.45
        and gentle_profile["approach_tendency"] > gentle_profile["avoidance_tendency"],
        "interruption_trigger_biases_avoidance_boundary": interruption_profile["avoidance_tendency"] > 0.62
        and interruption_profile["boundary_expression"] > 0.52
        and interruption_state["stress"] > 0.50,
        "late_night_trigger_biases_care_low_interrupt": late_profile["care_tendency"] > 0.70
        and late_profile["low_interrupt"] > 0.60
        and late_state["late_night_pattern"] > 0.55,
        "trigger_observations_diverge": min(
            vector_distance(clean_profiles[0], clean_profiles[1], tuple(clean_profiles[0].keys())),
            vector_distance(clean_profiles[0], clean_profiles[2], tuple(clean_profiles[0].keys())),
            vector_distance(clean_profiles[1], clean_profiles[2], tuple(clean_profiles[0].keys())),
        )
        > 0.42,
        "no_history_neutral": no_history["shadow_observation"]["trigger_behavior_profile"]["dominant_tendency"] == "neutral"
        and max(no_history_profile.values()) < 0.16,
        "shuffled_history_not_identical_to_clean_groups": all(
            vector_distance(shuffled_profile, profile, tuple(shuffled_profile.keys())) > 0.18 for profile in clean_profiles
        ),
        "runtime_fields_absent": all(result["runtime_field_hits"] == [] for result in all_results),
        "side_effects_absent": all(all(value is False for value in result["side_effects"].values()) for result in all_results),
        "active_runtime_scan_clean": bool(runtime_scan["ok"]),
    }


def run_sequence_experience_eval(
    repo_root: Path,
    out_dir: Path = DEFAULT_OUT_DIR,
    *,
    dataset_path: Path = DEFAULT_DATASET,
) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    if not dataset_path.is_absolute():
        dataset_path = repo_root / dataset_path
    out_dir.mkdir(parents=True, exist_ok=True)
    records = load_dataset(dataset_path)
    sequences = [
        evaluate_sequence(f"sequence_{record['group_id']}", record["group_id"], record["history_inputs"], record["trigger"])
        for record in records
    ]
    controls = build_controls(records)
    runtime_scan = scan_active_runtime_sources(repo_root, ACTIVE_RUNTIME_SCAN_MARKERS)
    checks = build_checks(sequences, controls, runtime_scan)
    status = "pass" if all(checks.values()) else "fail"
    result = {
        "status": status,
        "verdict": (
            "sequence_experience_eval_pass__manual_review_still_required"
            if status == "pass"
            else "no_go_keep_shadow_only_for_sequence_eval"
        ),
        "source": SOURCE,
        "claim_ceiling": CLAIM_CEILING,
        "dataset_path": str(dataset_path.relative_to(repo_root)),
        "trigger": TRIGGER_TEXT,
        "sequence_count": len(sequences),
        "control_count": len(controls),
        "sequences": sequences,
        "controls": controls,
        "runtime_scan": runtime_scan,
        "checks": checks,
        "artifact_only": True,
        "runtime_connected": False,
        "enabled": False,
        "mainline_connected": False,
        "side_effects": dict(SIDE_EFFECTS_FALSE),
        "next_allowed_step": "manual_shadow_review_go_no_go_remains_human_required",
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    json_path = Path(out_dir) / "sequence_experience_eval.json"
    report_path = Path(out_dir) / "SEQUENCE_EXPERIENCE_EVAL_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["checks"].items()))
    profiles = []
    for sequence in result["sequences"] + result["controls"]:
        observation = sequence["shadow_observation"]
        profile = observation["trigger_behavior_profile"]
        profiles.append(
            f"- `{sequence['category']}`: dominant=`{profile['dominant_tendency']}`, "
            f"approach=`{profile['approach_tendency']}`, avoidance=`{profile['avoidance_tendency']}`, "
            f"care=`{profile['care_tendency']}`, boundary=`{profile['boundary_expression']}`, "
            f"low_interrupt=`{profile['low_interrupt']}`"
        )
    profile_block = "\n".join(profiles)
    return f"""# PSPC Sequence Experience Eval v0

- status: `{result['status']}`
- verdict: `{result['verdict']}`
- claim_ceiling: `{result['claim_ceiling']}`
- dataset_path: `{result['dataset_path']}`
- trigger: `{result['trigger']}`
- sequence_count: `{result['sequence_count']}`
- control_count: `{result['control_count']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Trigger Profiles

{profile_block}

## Checks

{checks}

## What This Proves

This proves a controlled lab/shadow sequence accumulator can record history inputs as proxy state deltas and produce different audit-only trigger observations for the same trigger across gentle interaction, frequent interruption, late-night care, no-history, and shuffled-history conditions. It also proves this runner writes artifacts only and keeps runtime authority, EgoOperator user output, memory, gate, approval, transport, proactive behavior, planner, training, and model execution out of scope.

## What This Does Not Prove

It does not prove PSPC is integrated into EgoOperator, live runtime integration safety, adapter readiness, real user benefit, durable EgoOperator memory efficacy, live autonomy, philosophical consciousness, subjective experience, or that the proxy state variables are real emotion or real selfhood.

## Failure Meaning

Failure means this sequence proxy does not yet demonstrate behavior-level divergence from interaction history under the bounded lab/shadow contract. The correct verdict is `no_go_keep_shadow_only_for_sequence_eval`; do not move closer to runtime based on this evidence.

## Rollback

Delete `scripts/run_pspc_sequence_experience_eval.py`, `scripts/pspc_shadow_contracts.py` only if no other PSPC shadow runner depends on it, `tests/test_pspc_sequence_experience_eval.py`, `docs/codex/tasks/pspc-sequence-experience-eval-v0/`, `artifacts/pspc_sequence_experience_eval_v0/`, and matching task-board/program-state/evidence-ledger/generated-view entries.

## Claim Ceiling

`{result['claim_ceiling']}`.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PSPC sequence experience eval as artifact-only shadow evidence.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for eval artifacts.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET), help="Sequence eval JSONL dataset.")
    args = parser.parse_args()
    result = run_sequence_experience_eval(ROOT, Path(args.out), dataset_path=Path(args.dataset))
    print(
        json.dumps(
            {
                "status": result["status"],
                "verdict": result["verdict"],
                "out": args.out,
                "sequence_count": result["sequence_count"],
                "control_count": result["control_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
