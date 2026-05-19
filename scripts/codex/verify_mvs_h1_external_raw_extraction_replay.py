#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = ROOT / "artifacts" / "external_eval_replay_v1"
REPORTS_DIR = OUTPUT_ROOT / "reports"
EXTRACTION_MAP_JSON = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_EXTRACTION_MAP_CURRENT.json"
BUCKET_REPORT_JSON = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_BUCKET_REPORT_CURRENT.json"
FAILURES_JSON = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_FAILURES_CURRENT.json"
DEDUPE_RECHECK_JSON = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_DEDUPE_RECHECK_CURRENT.json"
RESTRICTED_RESERVE_JSON = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_RESTRICTED_RESERVE_CURRENT.json"
SOURCE_MANIFEST_JSON = (
    ROOT / "docs" / "codex" / "tasks" / "mvs-h1-external-eval-corpus" / "MVS_H1_EXTERNAL_EVAL_CORPUS_MANIFEST_CURRENT.json"
)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    source_manifest = _load_json(SOURCE_MANIFEST_JSON)
    extraction_map = _load_json(EXTRACTION_MAP_JSON)
    bucket_report = _load_json(BUCKET_REPORT_JSON)
    failures = _load_json(FAILURES_JSON)
    dedupe = _load_json(DEDUPE_RECHECK_JSON)
    reserve = _load_json(RESTRICTED_RESERVE_JSON)

    heldout_rows = [row for row in source_manifest.get("rows") or [] if row.get("local_partition") == "heldout_eval"]
    reserve_rows = [row for row in source_manifest.get("rows") or [] if row.get("local_partition") == "restricted_reserve"]
    extracted_rows = list(extraction_map.get("heldout_rows") or [])
    extracted_success = [row for row in extracted_rows if row.get("status") == "extracted"]
    extracted_failures = [row for row in extracted_rows if row.get("status") == "failed"]

    checks = []
    ok = True

    def add_check(name: str, passed: bool, detail: str) -> None:
        nonlocal ok
        ok = ok and passed
        checks.append({"name": name, "passed": passed, "detail": detail})

    add_check("heldout_row_count", len(extracted_rows) == len(heldout_rows), f"expected={len(heldout_rows)} actual={len(extracted_rows)}")
    add_check("success_plus_failures", len(extracted_success) + len(extracted_failures) == len(heldout_rows), f"success={len(extracted_success)} failed={len(extracted_failures)}")
    add_check("restricted_reserve_separate", len(reserve.get("rows") or []) == len(reserve_rows), f"expected={len(reserve_rows)} actual={len(reserve.get('rows') or [])}")
    add_check("failure_report_match", failures.get("failure_count") == len(extracted_failures), f"report={failures.get('failure_count')} extracted={len(extracted_failures)}")
    add_check("dedupe_zero", not dedupe.get("duplicate_initial_prompt_digests"), f"duplicates={len(dedupe.get('duplicate_initial_prompt_digests') or [])}")
    add_check("trial1_overlap_zero", not dedupe.get("trial1_hard_set_overlap_hits"), f"overlaps={len(dedupe.get('trial1_hard_set_overlap_hits') or [])}")

    bucket_selected = {row["bucket"]: 0 for row in heldout_rows}
    bucket_success = {row["bucket"]: 0 for row in heldout_rows}
    for row in heldout_rows:
        bucket_selected[row["bucket"]] = bucket_selected.get(row["bucket"], 0) + 1
    for row in extracted_success:
        bucket_success[row["bucket"]] = bucket_success.get(row["bucket"], 0) + 1

    bucket_summary_rows = {row["bucket"]: row for row in bucket_report.get("buckets") or []}
    add_check("bucket_report_complete", set(bucket_selected) == set(bucket_summary_rows), f"buckets={sorted(bucket_summary_rows)}")
    add_check(
        "bucket_report_selected_counts",
        all(bucket_summary_rows[bucket]["selected_count"] == count for bucket, count in bucket_selected.items()),
        f"selected_counts={bucket_selected}",
    )
    add_check(
        "bucket_report_success_counts",
        all(bucket_summary_rows[bucket]["success_count"] == bucket_success.get(bucket, 0) for bucket in bucket_selected),
        f"success_counts={bucket_success}",
    )

    missing_case_files = []
    missing_source_fields = []
    for row in extracted_success:
        case_path = ROOT / row["case_file"]
        if not case_path.exists():
            missing_case_files.append(row["sample_id"])
            continue
        case_payload = _load_json(case_path)
        required_source_fields = ["source_dataset_id", "source_url", "dataset_card_url", "license", "license_class", "source_split", "selection_hint", "target_mechanism", "expected_observable"]
        missing_fields = [field for field in required_source_fields if not case_payload.get("source", {}).get(field)]
        if missing_fields:
            missing_source_fields.append({"sample_id": row["sample_id"], "missing_fields": missing_fields})

    add_check("case_files_exist", not missing_case_files, f"missing_case_files={missing_case_files}")
    add_check("case_source_fields", not missing_source_fields, f"missing_source_fields={missing_source_fields}")

    print(json.dumps({"ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
