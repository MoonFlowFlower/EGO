#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
CASE_ROOT = ROOT / "artifacts" / "external_eval_replay_v1" / "cases" / "heldout_eval"
REPORT_ROOT = ROOT / "artifacts" / "external_eval_replay_v1" / "reports"

EXECUTION_JSON = REPORT_ROOT / "MVS_H1_EXTERNAL_REPLAY_EXECUTION_CURRENT.json"
BUCKET_JSON = REPORT_ROOT / "MVS_H1_EXTERNAL_REPLAY_BUCKET_SCORE_SUMMARY_CURRENT.json"
FAILURES_JSON = REPORT_ROOT / "MVS_H1_EXTERNAL_REPLAY_EXECUTION_FAILURES_CURRENT.json"
MECHANISM_JSON = REPORT_ROOT / "MVS_H1_EXTERNAL_REPLAY_MECHANISM_RELEVANCE_CURRENT.json"

EXPECTED_BUCKETS = {
    "correction",
    "ask_vs_answer_uncertainty",
    "failure_revision_later_change",
    "tool_risk_ambiguity",
    "continuity",
    "adversarial_constraints",
}
EXPECTED_VARIANTS = {
    "trial1_baseline_proto_self_mainline",
    "canonical_shadow_h1_on",
}


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    execution = _load(EXECUTION_JSON)
    bucket = _load(BUCKET_JSON)
    failures = _load(FAILURES_JSON)
    mechanism = _load(MECHANISM_JSON)

    expected_case_count = len(list(CASE_ROOT.glob("*.json")))
    checks: List[Dict[str, Any]] = []

    checks.append(
        {
            "name": "total_cases",
            "passed": execution["summary"]["total_cases"] == expected_case_count,
            "detail": f"expected={expected_case_count} actual={execution['summary']['total_cases']}",
        }
    )

    variants_run = set(execution["summary"]["variants_run"])
    checks.append(
        {
            "name": "variants_run",
            "passed": variants_run == EXPECTED_VARIANTS,
            "detail": f"expected={sorted(EXPECTED_VARIANTS)} actual={sorted(variants_run)}",
        }
    )

    executed_case_variants = int(execution["summary"]["executed_case_variants"])
    failure_count = int(execution["summary"]["execution_failures"])
    checks.append(
        {
            "name": "executed_plus_failed",
            "passed": executed_case_variants + failure_count == expected_case_count * len(EXPECTED_VARIANTS),
            "detail": f"executed={executed_case_variants} failed={failure_count}",
        }
    )

    checks.append(
        {
            "name": "failure_report_match",
            "passed": failure_count == int(failures["failure_count"]) == len(list(failures.get("failures") or [])),
            "detail": f"execution={failure_count} report={failures['failure_count']}",
        }
    )

    case_scores = execution.get("case_scores_by_variant") or {}
    results_by_variant = execution.get("results_by_variant") or {}
    preserved_partition = True
    missing_steps = []
    for variant_id in EXPECTED_VARIANTS:
        for row in results_by_variant.get(variant_id) or []:
            case_path = CASE_ROOT / f"{row['sample_id']}.json"
            if not case_path.exists():
                missing_steps.append(f"missing_case_file:{row['sample_id']}")
                preserved_partition = False
                continue
            case_payload = _load(case_path)
            if case_payload.get("local_partition") != "heldout_eval":
                preserved_partition = False
            if not list(row.get("steps") or []):
                missing_steps.append(row["sample_id"])
    checks.append(
        {
            "name": "heldout_only_and_steps_present",
            "passed": preserved_partition and not missing_steps,
            "detail": f"missing_steps={missing_steps}",
        }
    )

    bucket_rows = list(bucket.get("rows") or [])
    bucket_ids = {row["bucket"] for row in bucket_rows}
    checks.append(
        {
            "name": "bucket_completeness",
            "passed": bucket_ids == EXPECTED_BUCKETS,
            "detail": f"expected={sorted(EXPECTED_BUCKETS)} actual={sorted(bucket_ids)}",
        }
    )

    mechanism_rows = list(mechanism.get("rows") or [])
    mechanism_ids = {row["bucket"] for row in mechanism_rows}
    checks.append(
        {
            "name": "mechanism_table_completeness",
            "passed": mechanism_ids == EXPECTED_BUCKETS,
            "detail": f"expected={sorted(EXPECTED_BUCKETS)} actual={sorted(mechanism_ids)}",
        }
    )

    score_variant_ids = set(case_scores.keys())
    checks.append(
        {
            "name": "case_scores_variants",
            "passed": score_variant_ids == EXPECTED_VARIANTS,
            "detail": f"expected={sorted(EXPECTED_VARIANTS)} actual={sorted(score_variant_ids)}",
        }
    )

    shadow_bucket_rows = [row for row in bucket_rows if row["bucket"] in {"correction", "failure_revision_later_change", "tool_risk_ambiguity"}]
    shadow_positive = True
    for row in shadow_bucket_rows:
        candidate = next((item for item in row.get("variants") or [] if item["variant_id"] == "canonical_shadow_h1_on"), None)
        if candidate is None or int(candidate["shadow_present_step_count"]) <= 0:
            shadow_positive = False
            break
    checks.append(
        {
            "name": "candidate_shadow_present_on_direct_buckets",
            "passed": shadow_positive,
            "detail": f"checked_buckets={[row['bucket'] for row in shadow_bucket_rows]}",
        }
    )

    ok = all(check["passed"] for check in checks)
    print(json.dumps({"ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
