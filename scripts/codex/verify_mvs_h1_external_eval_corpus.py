#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "mvs-h1-external-eval-corpus"
MANIFEST_JSON = TASK_DIR / "MVS_H1_EXTERNAL_EVAL_CORPUS_MANIFEST_CURRENT.json"

REQUIRED_FIELDS = {
    "sample_id",
    "bucket",
    "source_dataset_id",
    "source_url",
    "dataset_card_url",
    "license",
    "license_class",
    "source_split",
    "local_partition",
    "target_mechanism",
    "expected_observable",
    "selection_hint",
    "dedupe_key",
    "selection_status",
}
EXPECTED_BUCKETS = {
    "correction",
    "ask_vs_answer_uncertainty",
    "failure_revision_later_change",
    "tool_risk_ambiguity",
    "continuity",
    "adversarial_constraints",
}
ALLOWED_PARTITIONS = {"heldout_eval", "restricted_reserve", "rejected_overlap"}


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    manifest = _load_json(MANIFEST_JSON)
    rows = manifest.get("rows") or []
    heldout_rows = [row for row in rows if row.get("local_partition") == "heldout_eval"]
    reserve_rows = [row for row in rows if row.get("local_partition") == "restricted_reserve"]

    missing = []
    for row in rows:
        missing_fields = sorted(field for field in REQUIRED_FIELDS if not row.get(field))
        if missing_fields:
            missing.append((row.get("sample_id"), missing_fields))

    bucket_counts = Counter(row["bucket"] for row in heldout_rows)
    dedupe_keys = [row["dedupe_key"] for row in rows]
    duplicate_keys = sorted({key for key in dedupe_keys if dedupe_keys.count(key) > 1})

    hard_set = _load_json(
        ROOT / "docs" / "codex" / "tasks" / "ai-self-awareness-minimal-framework" / "TRIAL1_COUNTERFACTUAL_HARD_SET.json"
    )
    hard_set_terms = {
        step.get("user_input", "").strip().lower()
        for case in hard_set.get("cases") or []
        for step in case.get("steps") or []
        if step.get("user_input")
    }
    overlap_hits = []
    for row in rows:
        hint = str(row.get("selection_hint") or "").strip().lower()
        if hint in hard_set_terms:
            overlap_hits.append(row["sample_id"])
        if str(row.get("source_dataset_id") or "").startswith("trial1_"):
            overlap_hits.append(row["sample_id"])

    invalid_partitions = sorted({row["sample_id"] for row in rows if row.get("local_partition") not in ALLOWED_PARTITIONS})
    invalid_bucket_set = sorted(set(bucket_counts) - EXPECTED_BUCKETS)

    ok = True
    checks = []

    def add_check(name: str, passed: bool, detail: str) -> None:
        nonlocal ok
        ok = ok and passed
        checks.append({"name": name, "passed": passed, "detail": detail})

    add_check("required_fields", not missing, f"missing_rows={len(missing)}")
    add_check("heldout_count", len(heldout_rows) == 60, f"heldout_eval_count={len(heldout_rows)}")
    add_check("bucket_set", set(bucket_counts) == EXPECTED_BUCKETS and not invalid_bucket_set, f"bucket_counts={dict(bucket_counts)}")
    add_check(
        "bucket_balance",
        all(bucket_counts.get(bucket) == 10 for bucket in EXPECTED_BUCKETS),
        f"bucket_counts={dict(bucket_counts)}",
    )
    add_check("dedupe_keys", not duplicate_keys, f"duplicate_keys={duplicate_keys}")
    add_check("partition_values", not invalid_partitions, f"invalid_partitions={invalid_partitions}")
    add_check("hardset_overlap", not overlap_hits, f"overlap_hits={overlap_hits}")
    add_check("reserve_present", len(reserve_rows) >= 1, f"restricted_reserve_count={len(reserve_rows)}")

    print(json.dumps({"ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
