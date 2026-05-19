from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "ai-self-awareness-minimal-framework"
ARTIFACT_DIR = ROOT / "artifacts" / "self_awareness_research"

SAMPLE_PACK_PATH = TASK_DIR / "SUBJECTCORE_FOLLOWON_SAMPLE_PACK.json"
OUTPUT_SCHEMA_PATH = TASK_DIR / "SUBJECTCORE_FOLLOWON_BATCH_ARTIFACT_SCHEMA.md"
FOLLOWON_STUB_PATH = ROOT / "scripts" / "codex" / "render_subjectcore_followon_eval_stub.py"

OUTPUT_JSON_PATH = ARTIFACT_DIR / "SUBJECTCORE_FOLLOWON_BATCH_CURRENT.json"
OUTPUT_MD_PATH = ARTIFACT_DIR / "SUBJECTCORE_FOLLOWON_BATCH_CURRENT.md"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


followon_stub = _load_module(FOLLOWON_STUB_PATH, "subjectcore_followon_batch_stub")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the planning-side SubjectCore follow-on eval batch")
    parser.add_argument("--sample-pack", type=Path, default=SAMPLE_PACK_PATH)
    parser.add_argument("--output-json", type=Path, default=OUTPUT_JSON_PATH)
    parser.add_argument("--output-md", type=Path, default=OUTPUT_MD_PATH)
    return parser.parse_args()


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


def build_batch_payload(sample_pack: dict[str, Any], *, sample_pack_path: Path) -> dict[str, Any]:
    sample_results = []
    integrity_pass_count = 0
    boundary_pass_count = 0
    expectation_match_count = 0
    family_summary: dict[str, dict[str, int]] = {}
    for sample in sample_pack.get("samples") or []:
        sample_family = sample.get("sample_family", "unclassified")
        integrity, boundary = followon_stub.build_followon_eval_payloads(sample["sample_mode"])
        integrity_status = integrity["eval_status"]
        boundary_status = boundary["eval_status"]
        integrity_pass_count += int(integrity_status == "pass")
        boundary_pass_count += int(boundary_status == "pass")
        expectation_match = (
            integrity_status == sample["expected_integrity_status"]
            and boundary_status == sample["expected_boundary_status"]
        )
        expectation_match_count += int(expectation_match)
        family_counts = family_summary.setdefault(
            sample_family,
            {
                "sample_count": 0,
                "expectation_match_count": 0,
                "integrity_pass_count": 0,
                "boundary_pass_count": 0,
            },
        )
        family_counts["sample_count"] += 1
        family_counts["expectation_match_count"] += int(expectation_match)
        family_counts["integrity_pass_count"] += int(integrity_status == "pass")
        family_counts["boundary_pass_count"] += int(boundary_status == "pass")
        sample_results.append(
            {
                "sample_id": sample["sample_id"],
                "sample_family": sample_family,
                "sample_mode": sample["sample_mode"],
                "expected_integrity_status": sample["expected_integrity_status"],
                "expected_boundary_status": sample["expected_boundary_status"],
                "actual_integrity_status": integrity_status,
                "actual_boundary_status": boundary_status,
                "expectation_match": expectation_match,
            }
        )

    sample_count = len(sample_results)
    overall_status = "pass" if expectation_match_count == sample_count else "fail"
    return {
        "schema_version": "subjectcore.followon_batch.v1",
        "trial_id": sample_pack.get("trial_id", "subjectcore_followon_eval_batch"),
        "sample_pack_path": _display_path(sample_pack_path),
        "output_schema_path": _display_path(OUTPUT_SCHEMA_PATH),
        "claim_ceiling_note": (
            "Planning-side follow-on batch only. This artifact does not prove runtime efficacy, "
            "live user benefit, autonomous execution, or any consciousness-like claim."
        ),
        "overall_status": overall_status,
        "sample_count": sample_count,
        "integrity_pass_count": integrity_pass_count,
        "boundary_pass_count": boundary_pass_count,
        "expectation_match_count": expectation_match_count,
        "samples": sample_results,
        "family_summary": family_summary,
        "notes": [
            "This batch stays entirely inside the planning-side SubjectCore follow-on lane.",
            "A passing batch means the frozen sample pack matches the current contract behavior.",
            "Current family coverage distinguishes continuity integrity, proposal integrity, proposal quality, proposal consistency, proposal prioritization, proposal conflict/collapse resolution, proposal restabilization, proposal-set update hygiene, proposal-set remerge hygiene, proposal-set consolidation hygiene, proposal-set completion scoring failures, proposal-set closure failures, and governor-boundary failures without widening runtime authority.",
        ],
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SubjectCore Follow-On Batch",
        "",
        "> Planning-side regression batch for the SubjectCore follow-on eval.",
        "",
        "## Header",
        "",
        f"- trial id: `{payload['trial_id']}`",
        f"- overall status: `{payload['overall_status']}`",
        f"- sample pack: `{payload['sample_pack_path']}`",
        f"- artifact schema: `{payload['output_schema_path']}`",
        f"- claim ceiling: `{payload['claim_ceiling_note']}`",
        "",
        "## Summary",
        "",
        f"- sample count: `{payload['sample_count']}`",
        f"- integrity pass count: `{payload['integrity_pass_count']}`",
        f"- boundary pass count: `{payload['boundary_pass_count']}`",
        f"- expectation match count: `{payload['expectation_match_count']}`",
        "",
        "## Samples",
        "",
    ]
    for sample in payload["samples"]:
        lines.extend(
            [
                f"- `{sample['sample_id']}` / `{sample['sample_family']}` / `{sample['sample_mode']}`",
                f"  expected: integrity `{sample['expected_integrity_status']}`, boundary `{sample['expected_boundary_status']}`",
                f"  actual: integrity `{sample['actual_integrity_status']}`, boundary `{sample['actual_boundary_status']}`",
                f"  expectation_match: `{str(sample['expectation_match']).lower()}`",
            ]
        )
    lines.extend(["", "## Family summary", ""])
    for family, counts in payload["family_summary"].items():
        lines.append(
            f"- `{family}`: samples `{counts['sample_count']}`, expectation matches `{counts['expectation_match_count']}`, integrity passes `{counts['integrity_pass_count']}`, boundary passes `{counts['boundary_pass_count']}`"
        )
    lines.extend(["", "## Notes", ""])
    for note in payload["notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    sample_pack = _load_json(args.sample_pack)
    payload = build_batch_payload(sample_pack, sample_pack_path=args.sample_pack)
    _write_json(args.output_json, payload)
    args.output_md.write_text(build_markdown(payload), encoding="utf-8")
    print(_display_path(args.output_json))
    print(_display_path(args.output_md))


if __name__ == "__main__":
    main()
