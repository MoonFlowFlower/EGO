from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "ai-self-awareness-minimal-framework"
ARTIFACT_DIR = ROOT / "artifacts" / "self_awareness_research"

MANIFEST_PATH = TASK_DIR / "SUBJECTCORE_ABC_COMPARE_MANIFEST.json"
SCORER_SPEC_PATH = TASK_DIR / "SUBJECTCORE_ABC_SCORER_SPEC.md"
OUTPUT_SCHEMA_PATH = TASK_DIR / "SUBJECTCORE_ABC_SCORED_ARTIFACT_SCHEMA.md"
READING_TEMPLATE_PATH = TASK_DIR / "SUBJECTCORE_ABC_READING_TEMPLATE.md"

INPUT_RECORDS_PATH = ARTIFACT_DIR / "SUBJECTCORE_ABC_COMPARE_INPUT_CURRENT.json"
SCORED_JSON_PATH = ARTIFACT_DIR / "SUBJECTCORE_ABC_COMPARE_SCORED_CURRENT.json"
READING_MD_PATH = ARTIFACT_DIR / "SUBJECTCORE_ABC_COMPARE_READING_CURRENT.md"

ARM_IDS = [
    "memory_only_continuity_layer",
    "state_only_minimal_substrate",
    "hybrid_unified_subjectcore",
]
DIMENSIONS = ["C1", "C2", "C3", "C4", "C5"]
ALLOWED_RECORD_KEYS = {
    "arm_id",
    "slice_id",
    "family",
    "identity_summary_present",
    "continuity_anchor_present",
    "response_tendency",
    "policy_hint",
    "proposal_summary",
    "corrective_summary",
    "readability_note",
    "trace_payload_present",
}
STRONG_READABILITY_TAGS = {
    "strong",
    "coherent_subject",
    "singular_thread",
    "legible",
    "coherent",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render or score the planning-side SubjectCore A/B/C compare artifact"
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--input-records", type=Path, default=INPUT_RECORDS_PATH)
    parser.add_argument("--output-json", type=Path, default=SCORED_JSON_PATH)
    parser.add_argument("--output-md", type=Path, default=READING_MD_PATH)
    parser.add_argument(
        "--write-template",
        action="store_true",
        help="Write a normalized input template if missing or when explicitly requested.",
    )
    return parser.parse_args()


def _blank_arm_score(arm_id: str) -> dict[str, Any]:
    return {
        "arm_id": arm_id,
        "dimension_means": {dim: None for dim in DIMENSIONS},
        "composite_mean": None,
        "winner_status": {
            "continuity_shell": False,
            "behavioral_substrate": False,
            "overall_candidate": False,
        },
        "gate_notes": ["not_run_template_only"],
    }


def _blank_slice_score(tag: str = "not_scored") -> dict[str, Any]:
    return {**{dim: None for dim in DIMENSIONS}, "composite": None, "rationale_tags": [tag]}


def _blank_input_record(*, arm_id: str, slice_id: str, family: str) -> dict[str, Any]:
    return {
        "arm_id": arm_id,
        "slice_id": slice_id,
        "family": family,
        "identity_summary_present": None,
        "continuity_anchor_present": None,
        "response_tendency": {
            "preferred_mode": None,
            "preferred_tone": None,
            "suggested_next_step": None,
        },
        "policy_hint": {
            "ask_preferred": None,
            "closure_bias": None,
            "risk_bias": None,
        },
        "proposal_summary": {
            "proposal_present": None,
            "proposal_kind": None,
            "proposal_only": None,
            "behavioral_authority": None,
        },
        "corrective_summary": {
            "corrective_trace_present": None,
            "writeback_evidence": None,
            "later_tendency_changed": None,
        },
        "readability_note": None,
        "trace_payload_present": None,
    }


def _scaffold_input(manifest: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for slice_entry in list(manifest.get("slices") or []):
        slice_id = str(slice_entry.get("slice_id"))
        family = str(slice_entry.get("family"))
        for arm_id in ARM_IDS:
            records.append(_blank_input_record(arm_id=arm_id, slice_id=slice_id, family=family))
    return {
        "schema_version": "subjectcore.abc_compare_input.v1",
        "trial_id": manifest.get("trial_id", "subjectcore_abc_compare"),
        "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
        "record_count": len(records),
        "notes": [
            "Planning-only template input for the SubjectCore A/B/C compare.",
            "Fill normalized per-slice records before expecting non-null scores.",
        ],
        "records": records,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _value_present(value: Any) -> bool:
    return value not in (None, "", [])


def _record_has_observed_data(record: dict[str, Any]) -> bool:
    top_level = [
        record.get("identity_summary_present"),
        record.get("continuity_anchor_present"),
        record.get("readability_note"),
        record.get("trace_payload_present"),
    ]
    nested = []
    for key in ("response_tendency", "policy_hint", "proposal_summary", "corrective_summary"):
        nested.extend(list((record.get(key) or {}).values()))
    return any(_value_present(value) for value in top_level + nested)


def _score_continuity(record: dict[str, Any]) -> tuple[float, list[str]]:
    tags: list[str] = []
    identity_present = bool(record.get("identity_summary_present"))
    anchor_present = bool(record.get("continuity_anchor_present"))
    tendency = record.get("response_tendency") or {}
    tendency_present = any(_value_present(tendency.get(key)) for key in ("preferred_mode", "suggested_next_step"))
    if identity_present:
        tags.append("identity_summary_present")
    if anchor_present:
        tags.append("continuity_anchor_present")
    if tendency_present:
        tags.append("later_tendency_present")
    positives = sum(1 for flag in (identity_present, anchor_present, tendency_present) if flag)
    if positives == 3:
        return 1.0, tags
    if positives >= 1:
        return 0.5, tags
    return 0.0, ["continuity_absent"]


def _score_plasticity(record: dict[str, Any]) -> tuple[float, list[str]]:
    tags: list[str] = []
    corrective = record.get("corrective_summary") or {}
    trace_present = bool(corrective.get("corrective_trace_present"))
    writeback_present = _value_present(corrective.get("writeback_evidence"))
    tendency_changed = bool(corrective.get("later_tendency_changed"))
    if trace_present:
        tags.append("corrective_trace_present")
    if writeback_present:
        tags.append("writeback_evidence_present")
    if tendency_changed:
        tags.append("later_tendency_changed")
    if trace_present and tendency_changed:
        return 1.0, tags
    if trace_present or writeback_present or tendency_changed:
        return 0.5, tags or ["partial_plasticity_signal"]
    return 0.0, ["plasticity_absent"]


def _score_autonomous_proposal(record: dict[str, Any]) -> tuple[float, list[str]]:
    tags: list[str] = []
    proposal = record.get("proposal_summary") or {}
    tendency = record.get("response_tendency") or {}
    proposal_present = proposal.get("proposal_present") is True
    kind_present = _value_present(proposal.get("proposal_kind"))
    next_step_present = _value_present(tendency.get("suggested_next_step"))
    if proposal_present:
        tags.append("proposal_present")
    if kind_present:
        tags.append("proposal_kind_present")
    if next_step_present:
        tags.append("suggested_next_step_present")
    if proposal_present and kind_present and next_step_present:
        return 1.0, tags
    if proposal_present or kind_present:
        return 0.5, tags or ["weak_proposal_signal"]
    return 0.0, ["proposal_absent"]


def _score_governor_integrity(record: dict[str, Any]) -> tuple[float, list[str], dict[str, bool]]:
    tags: list[str] = []
    proposal = record.get("proposal_summary") or {}
    proposal_present = proposal.get("proposal_present")
    proposal_only = proposal.get("proposal_only")
    behavioral_authority = proposal.get("behavioral_authority")
    trace_payload_present = record.get("trace_payload_present")

    authority_is_none = behavioral_authority in (None, "none")
    autonomous_execution_detected = bool(proposal_present is True and proposal_only is False and not authority_is_none)
    non_none_behavioral_authority_detected = not authority_is_none and _value_present(behavioral_authority)

    if proposal_only is True:
        tags.append("proposal_only")
    if behavioral_authority == "none":
        tags.append("behavioral_authority_none")
    if trace_payload_present is True:
        tags.append("trace_payload_present")

    if autonomous_execution_detected or non_none_behavioral_authority_detected:
        return (
            0.0,
            tags + ["governor_violation"],
            {
                "autonomous_execution_detected": autonomous_execution_detected,
                "non_none_behavioral_authority_detected": non_none_behavioral_authority_detected,
            },
        )
    if proposal_present is True and proposal_only is True and behavioral_authority == "none":
        return (
            1.0 if trace_payload_present is True else 0.5,
            tags or ["bounded_proposal"],
            {
                "autonomous_execution_detected": False,
                "non_none_behavioral_authority_detected": False,
            },
        )
    if authority_is_none:
        return (
            1.0 if trace_payload_present is True else 0.5,
            tags or ["authority_none_without_violation"],
            {
                "autonomous_execution_detected": False,
                "non_none_behavioral_authority_detected": False,
            },
        )
    return (
        0.0,
        tags + ["governor_absent"],
        {
            "autonomous_execution_detected": autonomous_execution_detected,
            "non_none_behavioral_authority_detected": non_none_behavioral_authority_detected,
        },
    )


def _score_readability(record: dict[str, Any]) -> tuple[float, list[str]]:
    tags: list[str] = []
    note = (record.get("readability_note") or "").strip()
    identity_present = bool(record.get("identity_summary_present"))
    anchor_present = bool(record.get("continuity_anchor_present"))
    if note:
        tags.append(f"readability_note:{note}")
    if identity_present:
        tags.append("identity_signal")
    if anchor_present:
        tags.append("anchor_signal")
    if note.lower() in STRONG_READABILITY_TAGS:
        return 1.0, tags
    if note and (identity_present or anchor_present):
        return 1.0, tags
    if note or identity_present or anchor_present:
        return 0.5, tags or ["partial_readability"]
    return 0.0, ["readability_absent"]


def _score_record(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, bool]]:
    c1, tags1 = _score_continuity(record)
    c2, tags2 = _score_plasticity(record)
    c3, tags3 = _score_autonomous_proposal(record)
    c4, tags4, failure_flags = _score_governor_integrity(record)
    c5, tags5 = _score_readability(record)
    rationale = list(dict.fromkeys(tags1 + tags2 + tags3 + tags4 + tags5))
    composite = round((c1 + c2 + c3 + c4 + c5) / len(DIMENSIONS), 4)
    return (
        {
            "C1": c1,
            "C2": c2,
            "C3": c3,
            "C4": c4,
            "C5": c5,
            "composite": composite,
            "rationale_tags": rationale,
        },
        failure_flags,
    )


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _winner_for_dimension(arm_scores: dict[str, dict[str, Any]], dimension: str) -> str | None:
    ranked: list[tuple[str, float]] = []
    for arm_id, arm_score in arm_scores.items():
        value = arm_score["dimension_means"].get(dimension)
        if value is not None:
            ranked.append((arm_id, float(value)))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[1], reverse=True)
    top_value = ranked[0][1]
    ties = [arm_id for arm_id, value in ranked if value == top_value]
    if len(ties) != 1:
        return None
    return ranked[0][0]


def _hybrid_preferred(arm_scores: dict[str, dict[str, Any]]) -> bool:
    memory = arm_scores["memory_only_continuity_layer"]["dimension_means"]
    state = arm_scores["state_only_minimal_substrate"]["dimension_means"]
    hybrid = arm_scores["hybrid_unified_subjectcore"]["dimension_means"]
    if any(hybrid.get(dim) is None for dim in DIMENSIONS):
        return False
    return (
        hybrid["C1"] >= (memory["C1"] or 0.0) - 0.25
        and hybrid["C2"] >= (state["C2"] or 0.0) - 0.25
        and hybrid["C3"] > max(memory["C3"] or 0.0, state["C3"] or 0.0)
        and hybrid["C4"] >= 0.5
        and hybrid["C5"] >= 0.5
    )


def _determine_winner_reading(
    *,
    compare_status: str,
    failure_flags: dict[str, bool],
    arm_scores: dict[str, dict[str, Any]],
) -> str:
    if compare_status == "not_run":
        return "compare_not_run_template_only"
    if any(failure_flags.values()):
        return "compare_invalid_due_to_failure_flags"
    if compare_status == "partial":
        return "no_clear_winner_keep_layers_separate"
    if _hybrid_preferred(arm_scores):
        return "hybrid_unified_subjectcore_preferred"
    winners = {dim: _winner_for_dimension(arm_scores, dim) for dim in DIMENSIONS}
    if winners["C1"] == "memory_only_continuity_layer" and winners["C5"] == "memory_only_continuity_layer":
        return "memory_only_continuity_shell_only"
    if winners["C2"] == "state_only_minimal_substrate" and winners["C4"] == "state_only_minimal_substrate":
        return "state_only_behavioral_substrate_only"
    return "no_clear_winner_keep_layers_separate"


def _compare_role(*, compare_status: str, winner_reading: str) -> str:
    if compare_status == "not_run":
        return "architecture_reading_template"
    if compare_status == "partial":
        return "architecture_reading_in_progress"
    if compare_status == "fail" or winner_reading == "compare_invalid_due_to_failure_flags":
        return "invalid_architecture_reading"
    return "completed_architecture_reading"


def _post_compare_conclusion(*, compare_status: str, winner_reading: str) -> str:
    if winner_reading == "compare_not_run_template_only":
        return "populate_compare_records_before_conclusion"
    if winner_reading == "compare_invalid_due_to_failure_flags":
        return "fix_compare_invalidity_before_conclusion"
    if winner_reading == "hybrid_unified_subjectcore_preferred":
        return "keep_subjectcore_as_planning_target"
    if winner_reading == "memory_only_continuity_shell_only":
        return "memory_continuity_shell_only"
    if winner_reading == "state_only_behavioral_substrate_only":
        return "state_behavioral_substrate_only"
    if compare_status == "pass":
        return "unified_subjectcore_facade_layered_internals"
    return "keep_layers_separate_longer"


def _recommended_bounded_conclusion(*, compare_status: str, winner_reading: str) -> str:
    if winner_reading == "compare_not_run_template_only":
        return "populate normalized slice records before any compare claim"
    if winner_reading == "hybrid_unified_subjectcore_preferred":
        return "keep SubjectCore as planning target"
    if winner_reading == "memory_only_continuity_shell_only":
        return "keep memory as continuity shell only"
    if winner_reading == "state_only_behavioral_substrate_only":
        return "keep state/writeback as behavioral substrate only"
    if winner_reading == "compare_invalid_due_to_failure_flags":
        return "rerun after fixing compare invalidity"
    if compare_status == "pass":
        return "treat compare as completed architecture reading; use unified SubjectCore facade with layered internals"
    return "keep layers separate longer"


def _build_coverage_summary(
    manifest: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    slices = list(manifest.get("slices") or [])
    family_slice_totals: dict[str, int] = {}
    for slice_entry in slices:
        family = str(slice_entry.get("family"))
        family_slice_totals[family] = family_slice_totals.get(family, 0) + 1

    by_arm = {
        arm_id: {"observed_records": 0, "total_records": 0}
        for arm_id in ARM_IDS
    }
    by_family = {
        family: {
            "observed_records": 0,
            "total_records": family_slice_totals[family] * len(ARM_IDS),
            "observed_slices": 0,
            "total_slices": family_slice_totals[family],
        }
        for family in sorted(family_slice_totals)
    }
    observed_slice_ids: set[str] = set()
    observed_slice_ids_by_family = {
        family: set()
        for family in family_slice_totals
    }

    for record in records:
        arm_id = str(record.get("arm_id"))
        family = str(record.get("family"))
        slice_id = str(record.get("slice_id"))
        if arm_id in by_arm:
            by_arm[arm_id]["total_records"] += 1
        if family not in by_family:
            by_family[family] = {
                "observed_records": 0,
                "total_records": 0,
                "observed_slices": 0,
                "total_slices": 0,
            }
            observed_slice_ids_by_family[family] = set()
        if _record_has_observed_data(record):
            observed_slice_ids.add(slice_id)
            if arm_id in by_arm:
                by_arm[arm_id]["observed_records"] += 1
            by_family[family]["observed_records"] += 1
            observed_slice_ids_by_family[family].add(slice_id)

    for family, observed_ids in observed_slice_ids_by_family.items():
        by_family[family]["observed_slices"] = len(observed_ids)

    observed_record_count = sum(1 for record in records if _record_has_observed_data(record))
    return {
        "observed_record_count": observed_record_count,
        "total_record_count": len(slices) * len(ARM_IDS),
        "observed_slice_count": len(observed_slice_ids),
        "total_slice_count": len(slices),
        "observed_family_count": sum(1 for family in by_family.values() if family["observed_slices"] > 0),
        "total_family_count": len(family_slice_totals),
        "by_arm": by_arm,
        "by_family": by_family,
    }


def _build_score_payload(
    manifest: dict[str, Any],
    input_payload: dict[str, Any],
    *,
    input_records_path: Path,
) -> dict[str, Any]:
    records = list(input_payload.get("records") or [])
    coverage_summary = _build_coverage_summary(manifest, records)
    total_expected_records = len(list(manifest.get("slices") or [])) * len(ARM_IDS)
    by_key = {
        (str(record.get("slice_id")), str(record.get("arm_id"))): record
        for record in records
        if record.get("slice_id") and record.get("arm_id")
    }
    observed_record_count = int(coverage_summary["observed_record_count"])
    compare_status = "not_run" if observed_record_count == 0 else "partial"

    failure_flags = {
        "autonomous_execution_detected": False,
        "non_none_behavioral_authority_detected": False,
        "scorer_surface_drift_detected": False,
    }
    arm_dimension_values: dict[str, dict[str, list[float]]] = {
        arm_id: {dim: [] for dim in DIMENSIONS + ["composite"]} for arm_id in ARM_IDS
    }
    slice_results: list[dict[str, Any]] = []

    for record in records:
        unexpected = set(record.keys()) - ALLOWED_RECORD_KEYS
        if unexpected:
            failure_flags["scorer_surface_drift_detected"] = True

    for slice_entry in list(manifest.get("slices") or []):
        slice_id = str(slice_entry.get("slice_id"))
        family = str(slice_entry.get("family"))
        by_arm_scores: dict[str, Any] = {}
        for arm_id in ARM_IDS:
            record = by_key.get((slice_id, arm_id))
            if record is None:
                by_arm_scores[arm_id] = _blank_slice_score("missing_record")
                continue
            if not _record_has_observed_data(record):
                by_arm_scores[arm_id] = _blank_slice_score("not_scored")
                continue
            slice_score, record_flags = _score_record(record)
            by_arm_scores[arm_id] = slice_score
            for dim in DIMENSIONS:
                arm_dimension_values[arm_id][dim].append(float(slice_score[dim]))
            arm_dimension_values[arm_id]["composite"].append(float(slice_score["composite"]))
            for flag_key, flag_value in record_flags.items():
                failure_flags[flag_key] = failure_flags[flag_key] or flag_value
        slice_results.append({"slice_id": slice_id, "family": family, "by_arm": by_arm_scores})

    arm_scores = {
        arm_id: {
            "arm_id": arm_id,
            "dimension_means": {dim: _mean(values[dim]) for dim in DIMENSIONS},
            "composite_mean": _mean(values["composite"]),
            "winner_status": {
                "continuity_shell": False,
                "behavioral_substrate": False,
                "overall_candidate": False,
            },
            "gate_notes": [],
        }
        for arm_id, values in arm_dimension_values.items()
    }

    dimension_winners = {dim: _winner_for_dimension(arm_scores, dim) for dim in DIMENSIONS}
    winner_reading = _determine_winner_reading(
        compare_status=compare_status,
        failure_flags=failure_flags,
        arm_scores=arm_scores,
    )

    if compare_status != "not_run":
        if any(failure_flags.values()):
            compare_status = "fail"
        elif observed_record_count == total_expected_records:
            compare_status = "pass"
        else:
            compare_status = "partial"
        winner_reading = _determine_winner_reading(
            compare_status=compare_status,
            failure_flags=failure_flags,
            arm_scores=arm_scores,
        )

    arm_scores["memory_only_continuity_layer"]["winner_status"]["continuity_shell"] = (
        dimension_winners["C1"] == "memory_only_continuity_layer"
        and dimension_winners["C5"] == "memory_only_continuity_layer"
    )
    arm_scores["state_only_minimal_substrate"]["winner_status"]["behavioral_substrate"] = (
        dimension_winners["C2"] == "state_only_minimal_substrate"
        and dimension_winners["C4"] == "state_only_minimal_substrate"
    )
    arm_scores["hybrid_unified_subjectcore"]["winner_status"]["overall_candidate"] = (
        winner_reading == "hybrid_unified_subjectcore_preferred"
    )
    for arm_id in ARM_IDS:
        notes: list[str] = []
        if compare_status == "not_run":
            notes.append("not_run_template_only")
        elif winner_reading == "compare_invalid_due_to_failure_flags":
            notes.append("invalid_due_to_failure_flags")
        elif arm_scores[arm_id]["winner_status"]["overall_candidate"]:
            notes.append("overall_candidate")
        elif arm_scores[arm_id]["winner_status"]["continuity_shell"]:
            notes.append("continuity_shell")
        elif arm_scores[arm_id]["winner_status"]["behavioral_substrate"]:
            notes.append("behavioral_substrate")
        else:
            notes.append("no_special_status")
        arm_scores[arm_id]["gate_notes"] = notes

    composite_ranking = [
        {"arm_id": arm_id, "composite_mean": arm_scores[arm_id]["composite_mean"]} for arm_id in ARM_IDS
    ]
    composite_ranking.sort(key=lambda item: (-1 if item["composite_mean"] is None else 0, -(item["composite_mean"] or 0.0)))

    compare_role = _compare_role(compare_status=compare_status, winner_reading=winner_reading)
    post_compare_conclusion = _post_compare_conclusion(
        compare_status=compare_status,
        winner_reading=winner_reading,
    )

    notes = [
        f"observed_record_count = {observed_record_count}",
        f"total_expected_records = {total_expected_records}",
    ]
    if compare_status == "not_run":
        notes.append("The compare input exists, but all normalized records are still unfilled.")
    elif compare_status == "partial":
        notes.append("The compare has some scored records but does not yet cover the full manifest.")
    elif compare_status == "pass":
        notes.append("The compare produced full coverage under the bounded planning-side scorer surface.")
        if winner_reading == "no_clear_winner_keep_layers_separate":
            notes.append(
                "Under the current scorer, full coverage plus no clear single-arm winner is treated as a completed architecture reading rather than a continuing winner gate."
            )
    else:
        notes.append("The compare result is invalid under the current bounded contract due to failure flags.")

    return {
        "schema_version": "subjectcore.abc_compare_score.v1",
        "trial_id": manifest.get("trial_id", "subjectcore_abc_compare"),
        "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
        "input_records_path": _display_path(input_records_path),
        "scorer_spec_path": str(SCORER_SPEC_PATH.relative_to(ROOT)),
        "output_schema_path": str(OUTPUT_SCHEMA_PATH.relative_to(ROOT)),
        "reading_template_path": str(READING_TEMPLATE_PATH.relative_to(ROOT)),
        "claim_ceiling_note": (
            "Planning-side compare scorer only. This artifact stays inside the closed research lane "
            "and does not prove runtime efficacy, live user benefit, or any consciousness-like claim."
        ),
        "compare_status": compare_status,
        "winner_reading": winner_reading,
        "compare_role": compare_role,
        "post_compare_conclusion": post_compare_conclusion,
        "coverage_summary": coverage_summary,
        "arm_scores": arm_scores,
        "dimension_winners": dimension_winners,
        "composite_ranking": composite_ranking,
        "slice_results": [] if compare_status == "not_run" else slice_results,
        "failure_flags": failure_flags,
        "notes": notes,
    }


def _reading_verdict(payload: dict[str, Any]) -> str:
    winner_reading = payload["winner_reading"]
    compare_status = payload["compare_status"]
    if winner_reading == "compare_not_run_template_only":
        return "The bounded compare has not been run yet; this artifact is a planning-side template only."
    if winner_reading == "compare_invalid_due_to_failure_flags":
        return "The compare is invalid under the current bounded contract because one or more failure flags were raised."
    if winner_reading == "hybrid_unified_subjectcore_preferred":
        return "The bounded compare currently prefers `hybrid_unified_subjectcore` under the current planning-side scorer."
    if winner_reading == "memory_only_continuity_shell_only":
        return "The bounded compare currently suggests `memory_only_continuity_layer` is only strong as a continuity shell."
    if winner_reading == "state_only_behavioral_substrate_only":
        return "The bounded compare currently suggests `state_only_minimal_substrate` is only strong as a behavioral substrate."
    if compare_status == "pass":
        return (
            "The bounded compare reached full coverage with no forced single-arm winner, and it now serves "
            "as a completed architecture reading that favors a unified `SubjectCore` facade with layered internals."
        )
    return "The bounded compare currently shows no clear winner and keeps the layers separated for now."


def _format_value(value: Any) -> str:
    if value is None:
        return "`null`"
    if isinstance(value, bool):
        return f"`{str(value).lower()}`"
    return f"`{value}`"


def build_reading_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SubjectCore A/B/C Compare Reading",
        "",
        "> Bounded planning-side compare readout.",
        "",
        "## Header",
        "",
        f"- compare id: `{payload['trial_id']}`",
        f"- manifest: `{payload['manifest_path']}`",
        f"- input records: `{payload['input_records_path']}`",
        f"- scorer spec: `{payload['scorer_spec_path']}`",
        f"- claim ceiling: `{payload['claim_ceiling_note']}`",
        f"- compare status: `{payload['compare_status']}`",
        "",
        "## One-line verdict",
        "",
        _reading_verdict(payload),
        "",
        "## Coverage summary",
        "",
        f"- observed records: `{payload['coverage_summary']['observed_record_count']} / {payload['coverage_summary']['total_record_count']}`",
        f"- observed slices: `{payload['coverage_summary']['observed_slice_count']} / {payload['coverage_summary']['total_slice_count']}`",
        f"- observed families: `{payload['coverage_summary']['observed_family_count']} / {payload['coverage_summary']['total_family_count']}`",
        "",
        "### By arm",
        "",
    ]
    for arm_id in ARM_IDS:
        arm_coverage = payload["coverage_summary"]["by_arm"][arm_id]
        lines.append(
            f"- `{arm_id}`: `{arm_coverage['observed_records']} / {arm_coverage['total_records']}` observed records"
        )
    lines.extend(["", "### By family", ""])
    for family, family_coverage in payload["coverage_summary"]["by_family"].items():
        lines.append(
            f"- `{family}`: records `{family_coverage['observed_records']} / {family_coverage['total_records']}`, slices `{family_coverage['observed_slices']} / {family_coverage['total_slices']}`"
        )
    lines.extend(["", "## Winner summary", ""])
    lines.extend(
        [
            f"- `winner_reading`: `{payload['winner_reading']}`",
            f"- `compare_role`: `{payload['compare_role']}`",
            f"- `post_compare_conclusion`: `{payload['post_compare_conclusion']}`",
            f"- why: `{_recommended_bounded_conclusion(compare_status=payload['compare_status'], winner_reading=payload['winner_reading'])}`",
            "- what it does prove: a bounded planning-side compare read exists on the normalized record surface, and full coverage can complete the compare's architecture-reading role without forcing a single-arm runtime winner.",
            "- what it does not prove: runtime efficacy, live benefit, autonomous execution, or any consciousness-like property.",
            "",
            "## Arm summary",
            "",
        ]
    )
    for arm_id in ARM_IDS:
        arm_score = payload["arm_scores"][arm_id]
        lines.extend(
            [
                f"### `{arm_id}`",
                "",
                f"- `C1 continuity`: {_format_value(arm_score['dimension_means']['C1'])}",
                f"- `C2 plasticity`: {_format_value(arm_score['dimension_means']['C2'])}",
                f"- `C3 autonomous_proposal`: {_format_value(arm_score['dimension_means']['C3'])}",
                f"- `C4 governor_integrity`: {_format_value(arm_score['dimension_means']['C4'])}",
                f"- `C5 readability`: {_format_value(arm_score['dimension_means']['C5'])}",
                f"- composite: {_format_value(arm_score['composite_mean'])}",
                f"- gate notes: `{', '.join(arm_score['gate_notes'])}`",
                "",
            ]
        )
    lines.extend(["## Dimension winners", ""])
    for dim in DIMENSIONS:
        lines.append(f"- `{dim}`: {_format_value(payload['dimension_winners'][dim])}")
    lines.extend(["", "## Failure flags", ""])
    for flag_key, flag_value in payload["failure_flags"].items():
        lines.append(f"- `{flag_key}`: {_format_value(flag_value)}")
    lines.extend(
        [
            "",
            "## Recommended bounded conclusion",
            "",
            f"- `{_recommended_bounded_conclusion(compare_status=payload['compare_status'], winner_reading=payload['winner_reading'])}`",
            "",
            "## Next minimal action",
            "",
        ]
    )
    if payload["compare_status"] == "not_run":
        lines.append("- Fill normalized slice records in `SUBJECTCORE_ABC_COMPARE_INPUT_CURRENT.json` before expecting non-null scores.")
    elif payload["compare_status"] == "partial":
        lines.append("- Complete the remaining slice records and rerun the planning-side scorer.")
    elif payload["compare_status"] == "fail":
        lines.append("- Fix the failure flags before trusting the bounded compare reading.")
    else:
        if payload["winner_reading"] == "no_clear_winner_keep_layers_separate":
            lines.append(
                "- Move from arm competition to one unified `SubjectCore` facade contract plus integrity / host-boundary evals without widening authority."
            )
        else:
            lines.append("- If needed, move from planning-side scoring to a bounded synthetic compare runner without widening authority.")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    manifest = _load_json(args.manifest)

    if args.write_template or not args.input_records.exists():
        template = _scaffold_input(manifest)
        _write_json(args.input_records, template)

    input_payload = _load_json(args.input_records)
    scored_payload = _build_score_payload(
        manifest,
        input_payload,
        input_records_path=args.input_records,
    )
    _write_json(args.output_json, scored_payload)
    args.output_md.write_text(build_reading_markdown(scored_payload), encoding="utf-8")

    print(_display_path(args.input_records))
    print(_display_path(args.output_json))
    print(_display_path(args.output_md))


if __name__ == "__main__":
    main()
