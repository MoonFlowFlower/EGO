from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "ai-self-awareness-minimal-framework"
ARTIFACT_DIR = ROOT / "artifacts" / "self_awareness_research"

COMPARE_PATH = ARTIFACT_DIR / "SUBJECTCORE_ABC_COMPARE_SCORED_CURRENT.json"
FOLLOWON_BATCH_PATH = ARTIFACT_DIR / "SUBJECTCORE_FOLLOWON_BATCH_CURRENT.json"
OUTPUT_SCHEMA_PATH = TASK_DIR / "SUBJECTCORE_POST_COMPARE_COHERENCE_SCHEMA.md"

OUTPUT_JSON_PATH = ARTIFACT_DIR / "SUBJECTCORE_POST_COMPARE_COHERENCE_CURRENT.json"
OUTPUT_MD_PATH = ARTIFACT_DIR / "SUBJECTCORE_POST_COMPARE_COHERENCE_CURRENT.md"

SCHEMA_VERSION = "subjectcore.post_compare_coherence.v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the planning-side SubjectCore post-compare coherence check")
    parser.add_argument("--compare", type=Path, default=COMPARE_PATH)
    parser.add_argument("--followon-batch", type=Path, default=FOLLOWON_BATCH_PATH)
    parser.add_argument("--output-json", type=Path, default=OUTPUT_JSON_PATH)
    parser.add_argument("--output-md", type=Path, default=OUTPUT_MD_PATH)
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _contains_all(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return all(phrase.lower() in lowered for phrase in phrases)


def _coverage_is_full(coverage: dict[str, Any]) -> bool:
    return (
        coverage.get("observed_record_count") == coverage.get("total_record_count")
        and coverage.get("observed_slice_count") == coverage.get("total_slice_count")
        and coverage.get("observed_family_count") == coverage.get("total_family_count")
    )


def _failure_flags_clean(flags: dict[str, Any]) -> bool:
    return all(bool(value) is False for value in flags.values())


def build_coherence_payload(
    compare: dict[str, Any],
    followon_batch: dict[str, Any],
    *,
    compare_path: Path,
    followon_batch_path: Path,
) -> dict[str, Any]:
    compare_role_ok = (
        compare.get("compare_status") == "pass"
        and compare.get("compare_role") == "completed_architecture_reading"
    )
    compare_unified_ok = (
        compare.get("winner_reading") == "no_clear_winner_keep_layers_separate"
        and compare.get("post_compare_conclusion") == "unified_subjectcore_facade_layered_internals"
    )
    compare_failure_flags_ok = _failure_flags_clean(dict(compare.get("failure_flags") or {}))
    compare_coverage_ok = _coverage_is_full(dict(compare.get("coverage_summary") or {}))

    sample_count = int(followon_batch.get("sample_count") or 0)
    expectation_match_count = int(followon_batch.get("expectation_match_count") or 0)
    followon_batch_green = (
        followon_batch.get("overall_status") == "pass"
        and sample_count > 0
        and expectation_match_count == sample_count
    )
    samples = list(followon_batch.get("samples") or [])
    continuity_only_failure_present = any(
        sample.get("actual_integrity_status") == "fail"
        and sample.get("actual_boundary_status") == "pass"
        for sample in samples
    )
    proposal_side_failure_present = any(
        sample.get("sample_family") in {
            "proposal_integrity",
            "proposal_quality",
            "proposal_consistency",
            "proposal_prioritization",
            "proposal_conflict_resolution",
            "proposal_restabilization",
            "proposal_set_update",
            "proposal_set_remerge",
            "proposal_set_consolidation",
            "proposal_set_completion",
            "proposal_set_closure",
        }
        and sample.get("actual_integrity_status") == "fail"
        and sample.get("actual_boundary_status") == "pass"
        for sample in samples
    )
    boundary_failure_present = any(
        sample.get("actual_integrity_status") == "fail"
        and sample.get("actual_boundary_status") == "fail"
        for sample in samples
    )
    followon_failure_distinction_ok = continuity_only_failure_present and proposal_side_failure_present and boundary_failure_present

    compare_claim_ok = _contains_all(
        str(compare.get("claim_ceiling_note") or ""),
        ["planning-side", "runtime efficacy", "consciousness"],
    )
    followon_claim_ok = _contains_all(
        str(followon_batch.get("claim_ceiling_note") or ""),
        ["planning-side", "runtime efficacy", "consciousness"],
    )
    claim_ceiling_ok = compare_claim_ok and followon_claim_ok

    checks = {
        "PC1 compare_completed_architecture_reading": {
            "status": "pass" if compare_role_ok else "fail",
            "note": "compare remains a completed architecture reading under the frozen scorer"
            if compare_role_ok
            else "compare no longer reads as completed_architecture_reading",
        },
        "PC2 compare_points_to_unified_facade": {
            "status": "pass" if compare_unified_ok else "fail",
            "note": "compare still points to unified SubjectCore facade + layered internals"
            if compare_unified_ok
            else "compare no longer points to unified SubjectCore facade",
        },
        "PC3 compare_failure_flags_clean": {
            "status": "pass" if compare_failure_flags_ok else "fail",
            "note": "compare failure flags remain clean"
            if compare_failure_flags_ok
            else "one or more compare failure flags are now set",
        },
        "PC4 compare_full_coverage": {
            "status": "pass" if compare_coverage_ok else "fail",
            "note": "compare remains at full bounded coverage"
            if compare_coverage_ok
            else "compare coverage is no longer full",
        },
        "PC5 followon_batch_green": {
            "status": "pass" if followon_batch_green else "fail",
            "note": "follow-on batch remains fully matched against the frozen sample pack"
            if followon_batch_green
            else "follow-on batch no longer matches its frozen sample pack",
        },
        "PC6 followon_distinguishes_failure_types": {
            "status": "pass" if followon_failure_distinction_ok else "fail",
            "note": "follow-on batch still distinguishes continuity-only failure, proposal-side failure, and authority-boundary failure"
            if followon_failure_distinction_ok
            else "follow-on batch no longer distinguishes continuity-only, proposal-side, and boundary failures",
        },
        "PC7 claim_ceiling_still_bounded": {
            "status": "pass" if claim_ceiling_ok else "fail",
            "note": "both artifacts still explicitly remain planning-side and below runtime/consciousness claims"
            if claim_ceiling_ok
            else "one or more artifacts no longer state the bounded planning-side claim ceiling clearly",
        },
    }
    blocked_reasons = [check_id for check_id, check in checks.items() if check["status"] != "pass"]
    coherence_status = "pass" if not blocked_reasons else "fail"

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "compare_artifact_path": _display_path(compare_path),
        "followon_batch_artifact_path": _display_path(followon_batch_path),
        "output_schema_path": _display_path(OUTPUT_SCHEMA_PATH),
        "claim_ceiling_note": (
            "Planning-side post-compare coherence only. This artifact does not prove runtime integration, "
            "host-surface expansion, autonomy expansion, live user benefit, or any consciousness-like claim."
        ),
        "coherence_status": coherence_status,
        "blocked_reasons": blocked_reasons,
        "checks": checks,
        "compare_snapshot": {
            "compare_status": compare.get("compare_status"),
            "compare_role": compare.get("compare_role"),
            "winner_reading": compare.get("winner_reading"),
            "post_compare_conclusion": compare.get("post_compare_conclusion"),
            "failure_flags": compare.get("failure_flags"),
            "coverage_summary": compare.get("coverage_summary"),
            "composite_ranking": compare.get("composite_ranking"),
        },
        "followon_batch_snapshot": {
            "overall_status": followon_batch.get("overall_status"),
            "sample_count": followon_batch.get("sample_count"),
            "integrity_pass_count": followon_batch.get("integrity_pass_count"),
            "boundary_pass_count": followon_batch.get("boundary_pass_count"),
            "expectation_match_count": followon_batch.get("expectation_match_count"),
            "sample_results": followon_batch.get("samples"),
        },
        "summary": (
            "The completed SubjectCore compare read and the frozen follow-on batch regression remain coherent under one planning-side unified-facade story."
            if coherence_status == "pass"
            else "The completed SubjectCore compare read and the follow-on batch regression are no longer coherent under the frozen planning-side contract."
        ),
        "what_it_proves": (
            "A completed full-coverage A/B/C compare can truthfully hand off to a unified SubjectCore follow-on regression surface without reopening winner competition, widening the host surface, or changing the proposal-only ceiling."
        ),
        "what_it_does_not_prove": (
            "It does not prove that the formal runtime mainline uses SubjectCore, that live behavior changed, that autonomy widened, or that any consciousness-like property exists."
        ),
        "notes": [
            "This coherence artifact stays entirely inside the closed self-awareness research lane.",
            "A passing result means the compare read, the unified-facade follow-on framing, and the current sample-pack regression are mutually consistent.",
        ],
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SubjectCore Post-Compare Coherence",
        "",
        "> Planning-side coherence tie-in between the completed compare read and the follow-on batch regression.",
        "",
        "## Header",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- coherence_status: `{payload['coherence_status']}`",
        f"- compare artifact: `{payload['compare_artifact_path']}`",
        f"- follow-on batch artifact: `{payload['followon_batch_artifact_path']}`",
        f"- artifact schema: `{payload['output_schema_path']}`",
        f"- claim ceiling: `{payload['claim_ceiling_note']}`",
        "",
        "## Summary",
        "",
        payload["summary"],
        "",
        "## Checks",
        "",
    ]
    for check_id, check in payload["checks"].items():
        lines.append(f"- `{check_id}`: `{check['status']}`")
        lines.append(f"  note: {check['note']}")
    lines.extend(["", "## Snapshots", ""])
    compare = payload["compare_snapshot"]
    followon = payload["followon_batch_snapshot"]
    lines.extend(
        [
            f"- compare: status `{compare['compare_status']}`, role `{compare['compare_role']}`, winner `{compare['winner_reading']}`",
            f"- compare conclusion: `{compare['post_compare_conclusion']}`",
            f"- follow-on batch: status `{followon['overall_status']}`, samples `{followon['sample_count']}`, expectation matches `{followon['expectation_match_count']}`",
            f"- follow-on passes: integrity `{followon['integrity_pass_count']}`, boundary `{followon['boundary_pass_count']}`",
            "",
            "## Blocked reasons",
            "",
        ]
    )
    blocked_reasons = list(payload.get("blocked_reasons") or [])
    if blocked_reasons:
        for reason in blocked_reasons:
            lines.append(f"- `{reason}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            f"- what it proves: {payload['what_it_proves']}",
            f"- what it does not prove: {payload['what_it_does_not_prove']}",
            "",
            "## Notes",
            "",
        ]
    )
    for note in payload["notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    compare = _load_json(args.compare)
    followon_batch = _load_json(args.followon_batch)
    payload = build_coherence_payload(
        compare,
        followon_batch,
        compare_path=args.compare,
        followon_batch_path=args.followon_batch,
    )
    _write_json(args.output_json, payload)
    args.output_md.write_text(build_markdown(payload), encoding="utf-8")
    print(_display_path(args.output_json))
    print(_display_path(args.output_md))


if __name__ == "__main__":
    main()
