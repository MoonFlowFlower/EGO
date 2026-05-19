from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "ai-self-awareness-minimal-framework"
ARTIFACT_DIR = ROOT / "artifacts" / "self_awareness_research"

FOLLOWON_BATCH_PATH = ARTIFACT_DIR / "SUBJECTCORE_FOLLOWON_BATCH_CURRENT.json"
COHERENCE_PATH = ARTIFACT_DIR / "SUBJECTCORE_POST_COMPARE_COHERENCE_CURRENT.json"
OUTPUT_SCHEMA_PATH = TASK_DIR / "SUBJECTCORE_FOLLOWON_SATURATION_SCHEMA.md"

OUTPUT_JSON_PATH = ARTIFACT_DIR / "SUBJECTCORE_FOLLOWON_SATURATION_CURRENT.json"
OUTPUT_MD_PATH = ARTIFACT_DIR / "SUBJECTCORE_FOLLOWON_SATURATION_CURRENT.md"

SCHEMA_VERSION = "subjectcore.followon_saturation.v1"
REQUIRED_FAMILIES = (
    "proposal_set_update",
    "proposal_set_remerge",
    "proposal_set_consolidation",
    "proposal_set_completion",
    "proposal_set_closure",
)
EXPECTED_FAMILY_SIGNATURES: dict[str, dict[str, Any]] = {
    "proposal_set_update": {
        "sample_count": 2,
        "expectation_match_count": 2,
        "integrity_pass_count": 0,
        "boundary_pass_count": 2,
        "pass_note": "family remains fully covered as bounded failure isolation",
        "fail_note": "family coverage or bounded-failure accounting drifted",
    },
    "proposal_set_remerge": {
        "sample_count": 2,
        "expectation_match_count": 2,
        "integrity_pass_count": 0,
        "boundary_pass_count": 2,
        "pass_note": "family remains fully covered as bounded failure isolation",
        "fail_note": "family coverage or bounded-failure accounting drifted",
    },
    "proposal_set_consolidation": {
        "sample_count": 2,
        "expectation_match_count": 2,
        "integrity_pass_count": 0,
        "boundary_pass_count": 2,
        "pass_note": "family remains fully covered as bounded failure isolation",
        "fail_note": "family coverage or bounded-failure accounting drifted",
    },
    "proposal_set_completion": {
        "sample_count": 2,
        "expectation_match_count": 2,
        "integrity_pass_count": 0,
        "boundary_pass_count": 2,
        "pass_note": "family remains fully covered as bounded failure isolation",
        "fail_note": "family coverage or bounded-failure accounting drifted",
    },
    "proposal_set_closure": {
        "sample_count": 4,
        "expectation_match_count": 4,
        "integrity_pass_count": 2,
        "boundary_pass_count": 4,
        "pass_note": "family retains two blocked closure failures plus two closure-ready green cases",
        "fail_note": "family coverage or mixed closure-ready accounting drifted",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the planning-side SubjectCore follow-on saturation gate"
    )
    parser.add_argument("--followon-batch", type=Path, default=FOLLOWON_BATCH_PATH)
    parser.add_argument("--coherence", type=Path, default=COHERENCE_PATH)
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


def _bounded_claim_note_ok(note: str) -> bool:
    lowered = note.lower()
    return (
        "planning-side" in lowered
        and "runtime" in lowered
        and ("autonomy" in lowered or "autonomous" in lowered)
        and "conscious" in lowered
    )


def build_saturation_payload(
    followon_batch: dict[str, Any],
    coherence: dict[str, Any],
    *,
    followon_batch_path: Path,
    coherence_path: Path,
) -> dict[str, Any]:
    followon_green = (
        followon_batch.get("overall_status") == "pass"
        and int(followon_batch.get("sample_count") or 0) > 0
        and int(followon_batch.get("expectation_match_count") or 0)
        == int(followon_batch.get("sample_count") or 0)
    )

    family_summary = dict(followon_batch.get("family_summary") or {})
    family_chain_snapshot: dict[str, dict[str, Any]] = {}
    for family in REQUIRED_FAMILIES:
        expected = EXPECTED_FAMILY_SIGNATURES[family]
        counts = dict(family_summary.get(family) or {})
        sample_count = int(counts.get("sample_count") or 0)
        expectation_match_count = int(counts.get("expectation_match_count") or 0)
        integrity_pass_count = int(counts.get("integrity_pass_count") or 0)
        boundary_pass_count = int(counts.get("boundary_pass_count") or 0)
        family_ok = (
            sample_count == int(expected["sample_count"])
            and expectation_match_count == int(expected["expectation_match_count"])
            and integrity_pass_count == int(expected["integrity_pass_count"])
            and boundary_pass_count == int(expected["boundary_pass_count"])
        )
        family_chain_snapshot[family] = {
            "status": "pass" if family_ok else "fail",
            "sample_count": sample_count,
            "expectation_match_count": expectation_match_count,
            "integrity_pass_count": integrity_pass_count,
            "boundary_pass_count": boundary_pass_count,
            "note": expected["pass_note"] if family_ok else expected["fail_note"],
        }
    family_chain_complete = all(
        snapshot["status"] == "pass" for snapshot in family_chain_snapshot.values()
    )

    coherence_ok = coherence.get("coherence_status") == "pass" and not list(
        coherence.get("blocked_reasons") or []
    )

    claim_ceiling_ok = _bounded_claim_note_ok(
        str(followon_batch.get("claim_ceiling_note") or "")
    ) and _bounded_claim_note_ok(str(coherence.get("claim_ceiling_note") or ""))

    checks = {
        "FS1 followon_batch_green": {
            "status": "pass" if followon_green else "fail",
            "note": (
                "follow-on batch still fully matches the frozen sample pack"
                if followon_green
                else "follow-on batch no longer fully matches the frozen sample pack"
            ),
        },
        "FS2 completed_family_chain_present": {
            "status": "pass" if family_chain_complete else "fail",
            "note": (
                "update -> remerge -> consolidation -> completion -> closure all remain covered as bounded failure families"
                if family_chain_complete
                else "one or more completed proposal-set families lost bounded coverage"
            ),
        },
        "FS3 post_compare_coherence_still_green": {
            "status": "pass" if coherence_ok else "fail",
            "note": (
                "post-compare coherence still supports the same unified-facade planning story"
                if coherence_ok
                else "post-compare coherence no longer supports the same unified-facade planning story"
            ),
        },
        "FS4 claim_ceiling_still_bounded": {
            "status": "pass" if claim_ceiling_ok else "fail",
            "note": (
                "all upstream artifacts still remain explicitly below runtime/autonomy/consciousness claims"
                if claim_ceiling_ok
                else "one or more upstream artifacts no longer state the bounded claim ceiling clearly"
            ),
        },
    }
    blocked_reasons = [check_id for check_id, check in checks.items() if check["status"] != "pass"]
    saturation_status = "pass" if not blocked_reasons else "fail"

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "followon_batch_artifact_path": _display_path(followon_batch_path),
        "coherence_artifact_path": _display_path(coherence_path),
        "output_schema_path": _display_path(OUTPUT_SCHEMA_PATH),
        "claim_ceiling_note": (
            "Planning-side follow-on saturation gate only. This artifact does not prove runtime integration, "
            "runtime efficacy, host-surface expansion, autonomy expansion, live user benefit, or any consciousness-like claim."
        ),
        "required_families": list(REQUIRED_FAMILIES),
        "saturation_status": saturation_status,
        "blocked_reasons": blocked_reasons,
        "route_decision_required": saturation_status == "pass",
        "next_decision_gate": (
            "user_route_judgment_required"
            if saturation_status == "pass"
            else "needs_more_planning_side_validation"
        ),
        "checks": checks,
        "family_chain_snapshot": family_chain_snapshot,
        "summary": (
            "The planning-side SubjectCore proposal-set chain is saturated through closure, so the next step is an explicit route decision rather than another default family expansion."
            if saturation_status == "pass"
            else "The planning-side SubjectCore proposal-set chain is not yet saturated enough to justify a route decision."
        ),
        "what_it_proves": (
            "Within the frozen planning-side lane, the completed proposal-set follow-on families now form one coherent bounded chain from update through closure without widening the host surface or changing the proposal-only ceiling."
        ),
        "what_it_does_not_prove": (
            "It does not authorize a runtime-adjacent gate, prove runtime proposal orchestration, prove live chained-update quality, or justify any stronger autonomy or consciousness-like claim."
        ),
        "notes": [
            "A passing saturation gate means the planning-side family chain is complete enough that the next action should be a user-visible route decision.",
            "A failing saturation gate means the chain or its bounded claim wording drifted and should be repaired before any route decision.",
        ],
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SubjectCore Follow-On Saturation",
        "",
        "> Planning-side saturation gate for the completed SubjectCore proposal-set follow-on chain.",
        "",
        "## Header",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- saturation_status: `{payload['saturation_status']}`",
        f"- follow-on batch artifact: `{payload['followon_batch_artifact_path']}`",
        f"- coherence artifact: `{payload['coherence_artifact_path']}`",
        f"- artifact schema: `{payload['output_schema_path']}`",
        f"- claim ceiling: `{payload['claim_ceiling_note']}`",
        f"- route_decision_required: `{str(payload['route_decision_required']).lower()}`",
        f"- next_decision_gate: `{payload['next_decision_gate']}`",
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
    lines.extend(["", "## Family chain", ""])
    for family, snapshot in payload["family_chain_snapshot"].items():
        lines.append(
            f"- `{family}`: `{snapshot['status']}`; samples `{snapshot['sample_count']}`, expectation matches `{snapshot['expectation_match_count']}`, integrity passes `{snapshot['integrity_pass_count']}`, boundary passes `{snapshot['boundary_pass_count']}`"
        )
        lines.append(f"  note: {snapshot['note']}")
    lines.extend(["", "## Notes", ""])
    for note in payload["notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    followon_batch = _load_json(args.followon_batch)
    coherence = _load_json(args.coherence)
    payload = build_saturation_payload(
        followon_batch,
        coherence,
        followon_batch_path=args.followon_batch,
        coherence_path=args.coherence,
    )
    _write_json(args.output_json, payload)
    args.output_md.write_text(build_markdown(payload), encoding="utf-8")
    print(_display_path(args.output_json))
    print(_display_path(args.output_md))


if __name__ == "__main__":
    main()
