#!/usr/bin/env python3
"""Independent read-only verifier for the 001J M0 capacity packet."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "EGO-V2-HOMEOSTATIC-COMPOSITIONAL-TRANSFER-001J"
CANONICAL_ROOT = REPO_ROOT / "artifacts" / TASK_ID
ARMS = ("PRIVATE_ORACLE_NAVIGATOR", "PUBLIC_FACTOR_BAYES", "UNIFORM_RANDOM")
PROTECTED = {
    "artifacts/EGO-V2-CAUSAL-SPROUT-DEMO-001A/result.json": (
        "0f67ce21df28a4919f3b66a0e4d73f1b4416d50616c8620742f584c2e06c8783"
    ),
    "artifacts/EGO-V2-CAUSAL-SPROUT-DEMO-001A/freeze_manifest.json": (
        "8d577465bb535d70f5283e45164c69d0bb6ea7f2a2883bcacdd5b2d5427a4530"
    ),
    "docs/codex/tasks/EGO-V2-CAUSAL-SPROUT-DEMO-001A.md": (
        "5b1c0496832aff22fc277e354a90ef555577ac249e0494409da9b9d11630c787"
    ),
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _close(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-12)


def verify_capacity_artifacts(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    findings: list[str] = []
    required = {
        "capacity_result.json",
        "capacity_rows.jsonl",
        "capacity_replay_report.json",
        "leakage_report.json",
        "artifact_manifest.json",
        "failure_manifest.json",
    }
    present = {path.name for path in root.iterdir()} if root.is_dir() else set()
    missing = sorted(required - present)
    if missing:
        return {
            "schema_version": "ego.v2.homeostatic_capacity_verification.v1",
            "passed": False,
            "findings": [f"missing:{name}" for name in missing],
            "stored_verdict": None,
            "recomputed_verdict": None,
            "heldout_rows": 0,
            "neural_candidate_source_present": (
                REPO_ROOT / "labs" / "ego_life_playground_v0" / "homeostatic_transfer.py"
            ).exists(),
            "protected_predecessor_hashes_match": False,
        }

    result = _load_json(root / "capacity_result.json")
    replay = _load_json(root / "capacity_replay_report.json")
    leakage = _load_json(root / "leakage_report.json")
    manifest = _load_json(root / "artifact_manifest.json")
    failure = _load_json(root / "failure_manifest.json")
    if result.get("task_id") != TASK_ID or failure.get("task_id") != TASK_ID:
        findings.append("task_id_mismatch")

    listed = {str(item.get("path")): item for item in manifest.get("artifacts", [])}
    expected_listed = present - {"artifact_manifest.json"}
    if set(listed) != expected_listed:
        findings.append("manifest_file_set_mismatch")
    for name, item in listed.items():
        path = root / name
        if not path.is_file() or _file_hash(path) != item.get("sha256"):
            findings.append(f"manifest_hash_mismatch:{name}")
        elif path.stat().st_size != item.get("bytes"):
            findings.append(f"manifest_size_mismatch:{name}")

    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        (root / "capacity_rows.jsonl").read_text(encoding="utf-8").splitlines(), start=1
    ):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            findings.append(f"row_json_invalid:{line_number}")
            continue
        unsigned = {key: value for key, value in row.items() if key != "trace_hash"}
        if _canonical_hash(unsigned) != row.get("trace_hash"):
            findings.append(f"row_hash_mismatch:{line_number}")
        rows.append(row)

    heldout_rows = sum("-heldout-" in str(row.get("context_id")) for row in rows)
    if heldout_rows:
        findings.append("heldout_rows_present")
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row.get("context_id")), str(row.get("arm")))].append(row)
    if len(groups) != 48:
        findings.append("trajectory_group_count_mismatch")
    loss_by_trajectory: dict[tuple[str, str], float] = {}
    for key, group in groups.items():
        ordered = sorted(group, key=lambda row: int(row.get("sequence", -1)))
        sequences = [int(row.get("sequence", -1)) for row in ordered]
        if sequences != list(range(1, 97)):
            findings.append(f"row_sequence_mismatch:{key[0]}:{key[1]}")
        previous = None
        for row in ordered:
            if row.get("prev_trace_hash") != previous:
                findings.append(f"trace_chain_mismatch:{key[0]}:{key[1]}")
                break
            previous = row.get("trace_hash")
        if ordered:
            loss_by_trajectory[key] = round(
                sum(float(row["deficit_loss"]) for row in ordered) / len(ordered), 12
            )

    loss_by_arm: dict[str, float] = {}
    for arm in ARMS:
        arm_losses = [loss for (context, item_arm), loss in loss_by_trajectory.items() if item_arm == arm]
        if len(arm_losses) != 16:
            findings.append(f"arm_trajectory_count_mismatch:{arm}")
            loss_by_arm[arm] = math.nan
        else:
            loss_by_arm[arm] = round(sum(arm_losses) / len(arm_losses), 12)
    if all(math.isfinite(value) for value in loss_by_arm.values()):
        headroom = round(
            loss_by_arm["UNIFORM_RANDOM"] - loss_by_arm["PRIVATE_ORACLE_NAVIGATOR"], 12
        )
        reference_gain = round(
            loss_by_arm["UNIFORM_RANDOM"] - loss_by_arm["PUBLIC_FACTOR_BAYES"], 12
        )
        recovery = 0.0 if headroom <= 0.0 else round(reference_gain / headroom, 12)
        reference_beats = sum(
            loss_by_trajectory[(context, "PUBLIC_FACTOR_BAYES")]
            < loss_by_trajectory[(context, "UNIFORM_RANDOM")]
            for context in {context for context, arm in groups if arm == "PUBLIC_FACTOR_BAYES"}
            if (context, "UNIFORM_RANDOM") in loss_by_trajectory
        )
    else:
        headroom = reference_gain = recovery = math.nan
        reference_beats = -1
    recomputed_aggregate = {
        "loss_by_arm": loss_by_arm,
        "random_oracle_headroom": headroom,
        "public_reference_gain": reference_gain,
        "public_reference_recovery_fraction": recovery,
        "public_reference_beats_random_count": reference_beats,
    }
    stored_aggregate = result.get("aggregate", {})
    for arm in ARMS:
        if arm not in stored_aggregate.get("loss_by_arm", {}) or not _close(
            loss_by_arm[arm], stored_aggregate["loss_by_arm"][arm]
        ):
            findings.append(f"aggregate_loss_mismatch:{arm}")
    for key in (
        "random_oracle_headroom",
        "public_reference_gain",
        "public_reference_recovery_fraction",
    ):
        if key not in stored_aggregate or not _close(recomputed_aggregate[key], stored_aggregate[key]):
            findings.append(f"aggregate_metric_mismatch:{key}")
    if reference_beats != stored_aggregate.get("public_reference_beats_random_count"):
        findings.append("aggregate_reference_count_mismatch")

    gates = {
        "complete_dev_population": len(groups) == 48,
        "three_arms_and_real_callable_receipts": all(
            row.get("metabolism_producer")
            == "ego_life_playground_v0.engine.compute_metabolism_ledger"
            for row in rows
        ),
        "random_oracle_headroom_at_least_0_10": headroom >= 0.10,
        "public_reference_recovers_half_headroom": recovery >= 0.50,
        "public_reference_beats_random_12_of_16": reference_beats >= 12,
        "fresh_replay_exact": bool(replay.get("all_match"))
        and replay.get("stored_actions_used_as_replay_input") is False,
    }
    if gates != result.get("gates"):
        findings.append("gate_recomputation_mismatch")
    recomputed_verdict = (
        "BENCHMARK_CAPACITY_ESTABLISHED"
        if all(gates.values())
        else "BENCHMARK_CAPACITY_NOT_ESTABLISHED"
    )
    stored_verdict = result.get("verdict")
    if stored_verdict != recomputed_verdict:
        findings.append("verdict_mismatch")
    if recomputed_verdict == "BENCHMARK_CAPACITY_NOT_ESTABLISHED":
        expected_failed = sorted(key for key, value in gates.items() if not value)
        if failure.get("failed_gates") != expected_failed:
            findings.append("failure_manifest_gate_mismatch")
        if result.get("next_action") != "stop_before_neural_candidate":
            findings.append("negative_next_action_mismatch")

    if not leakage.get("ordinary_inputs_clean") or not all(
        leakage.get("positive_controls", {}).values()
    ):
        findings.append("leakage_report_failed")
    if not replay.get("independent_aggregate_recomputed"):
        findings.append("producer_recompute_report_failed")

    protected_match = all(
        (REPO_ROOT / relative).is_file() and _file_hash(REPO_ROOT / relative) == expected
        for relative, expected in PROTECTED.items()
    )
    if not protected_match:
        findings.append("protected_predecessor_hash_mismatch")
    neural_source_present = (
        REPO_ROOT / "labs" / "ego_life_playground_v0" / "homeostatic_transfer.py"
    ).exists()
    if stored_verdict == "BENCHMARK_CAPACITY_NOT_ESTABLISHED" and neural_source_present:
        findings.append("neural_candidate_source_present_after_capacity_stop")

    return {
        "schema_version": "ego.v2.homeostatic_capacity_verification.v1",
        "passed": not findings,
        "findings": sorted(set(findings)),
        "stored_verdict": stored_verdict,
        "recomputed_verdict": recomputed_verdict,
        "recomputed_aggregate": recomputed_aggregate,
        "heldout_rows": heldout_rows,
        "neural_candidate_source_present": neural_source_present,
        "protected_predecessor_hashes_match": protected_match,
        "artifact_manifest_hashes_match": not any(
            finding.startswith("manifest_") for finding in findings
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=CANONICAL_ROOT)
    args = parser.parse_args(argv)
    report = verify_capacity_artifacts(args.root)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
