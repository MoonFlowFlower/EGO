"""Independent row recomputation and fail-closed controls for 001M.

This module intentionally does not import the producer or product runtime.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "EGO-V2-TRANSFER-MECHANISM-001M"
ARTIFACT_NAME = TASK_ID
EARLY_CUTOFF = 48
SEARCH_RUN_ID = "history_shuffle_wiringfix"
PUBLIC_FIELDS = ["observation", "organism", "last_action", "last_delta"]
PRIVATE_FIELDS = {
    "world_id",
    "world_seed",
    "seed",
    "layout_id",
    "token_mapping",
    "mapping",
    "private_pose",
    "pose",
    "oracle_action",
    "split",
    "packet",
    "verdict",
    "future_outcome",
    "future",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 12)


def recompute_summary(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    private_count = 0
    for row in rows:
        if bool(row.get("evaluator_private", False)):
            private_count += 1
            continue
        grouped[
            (
                str(row["candidate_id"]),
                str(row["opaque_context_id"]),
                str(row["arm"]),
            )
        ].append(row)
    trajectories = []
    for (candidate_id, context, arm), values in sorted(grouped.items()):
        ordered = sorted(values, key=lambda row: int(row["sequence"]))
        trajectories.append(
            {
                "candidate_id": candidate_id,
                "opaque_context_id": context,
                "arm": arm,
                "row_count": len(ordered),
                "early_deficit_auc": round(
                    sum(float(row["deficit_loss"]) for row in ordered[:EARLY_CUTOFF]), 12
                ),
                "late_deficit_auc": round(
                    sum(float(row["deficit_loss"]) for row in ordered[EARLY_CUTOFF:]), 12
                ),
                "total_deficit_auc": round(
                    sum(float(row["deficit_loss"]) for row in ordered), 12
                ),
                "final_effect_sign_accuracy": ordered[-1]["effect_sign_accuracy"],
                "trace_chain_hash": ordered[-1].get("trace_hash"),
            }
        )
    arms: dict[str, Any] = {}
    by_arm: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for trajectory in trajectories:
        by_arm[str(trajectory["arm"])].append(trajectory)
    for arm, values in sorted(by_arm.items()):
        arms[arm] = {
            "world_count": len(values),
            "mean_early_deficit_auc": _mean(
                [float(value["early_deficit_auc"]) for value in values]
            ),
            "mean_late_deficit_auc": _mean(
                [float(value["late_deficit_auc"]) for value in values]
            ),
            "mean_total_deficit_auc": _mean(
                [float(value["total_deficit_auc"]) for value in values]
            ),
        }
    return {
        "row_count": len(rows),
        "public_row_count": len(rows) - private_count,
        "private_diagnostic_row_count": private_count,
        "trajectories": trajectories,
        "arms": arms,
    }


def verify_rows_payload(
    result: Mapping[str, Any], rows: list[Mapping[str, Any]], rows_path: Path
) -> dict[str, Any]:
    findings: list[str] = []
    if result.get("rows_sha256") != sha256(rows_path):
        findings.append("rows_sha256_mismatch")
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for index, row in enumerate(rows):
        grouped[
            (
                str(row["candidate_id"]),
                str(row["opaque_context_id"]),
                str(row["arm"]),
            )
        ].append(row)
        unhashed = {key: value for key, value in row.items() if key != "trace_hash"}
        if row.get("trace_hash") != canonical_hash(unhashed):
            findings.append(f"row_hash_mismatch:{index}")
        if row.get("public_input_clean") is not True:
            findings.append(f"unclean_public_receipt:{index}")
        if row.get("public_input_fields") not in (None, PUBLIC_FIELDS):
            findings.append(f"public_field_mismatch:{index}")
        if row.get("cross_world_effect_mean_applied") is True:
            findings.append(f"cross_world_mean_applied:{index}")
    for key, values in grouped.items():
        previous = None
        for expected_sequence, row in enumerate(
            sorted(values, key=lambda item: int(item["sequence"])), start=1
        ):
            if int(row["sequence"]) != expected_sequence or row.get(
                "prev_trace_hash"
            ) != previous:
                findings.append(f"trace_chain_mismatch:{':'.join(key)}:{expected_sequence}")
            previous = row.get("trace_hash")
    recomputed = recompute_summary(rows)
    expected = result.get("row_recomputation_target", result.get("summary"))
    if expected != recomputed:
        findings.append("stored_row_recomputation_target_mismatch")
    return {
        "findings": sorted(set(findings)),
        "row_recomputation": recomputed,
        "row_recomputation_match": expected == recomputed,
        "passed": not findings,
    }


def _read_rows(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def _artifact_root(root: Path) -> Path:
    return Path(root).resolve() / "artifacts" / ARTIFACT_NAME


def _verify_result(root: Path, result_path: Path) -> dict[str, Any]:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    rows_path = root / result["rows_path"]
    rows = _read_rows(rows_path)
    report = verify_rows_payload(result, rows, rows_path)
    report.update(
        {
            "result_path": result_path.relative_to(root).as_posix(),
            "rows_path": rows_path.relative_to(root).as_posix(),
            "candidate_id": result["candidate_id"],
            "split": result["split"],
            "row_count": len(rows),
        }
    )
    return report


def _protected_audit(root: Path) -> dict[str, Any]:
    protected = json.loads(
        (_artifact_root(root) / "protected_predecessor_hashes.json").read_text(
            encoding="utf-8"
        )
    )
    findings = []
    checked = 0
    for files in protected["protected_trees"].values():
        for relative, expected in files.items():
            checked += 1
            path = root / relative
            if not path.is_file() or sha256(path) != expected:
                findings.append(relative)
    return {"checked_file_count": checked, "findings": findings, "passed": not findings}


def _packet_audit(root: Path) -> dict[str, Any]:
    target = _artifact_root(root)
    commitment = json.loads((target / "packet_commitment.json").read_text(encoding="utf-8"))
    path = root / commitment["packet_path"]
    passed = path.is_file() and sha256(path) == commitment["packet_sha256"]
    return {"packet_sha256_match": passed, "passed": passed}


def _private_payload_detected(payload: Mapping[str, Any]) -> bool:
    def visit(value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(str(key).lower() in PRIVATE_FIELDS or visit(item) for key, item in value.items())
        if isinstance(value, list):
            return any(visit(item) for item in value)
        return False

    return visit(payload)


def verify_campaign(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    target = _artifact_root(root)
    result_paths = sorted(target.glob("search_dev_*_result.json"))
    result_paths.extend(sorted(target.glob("latent_alignment_*_result.json")))
    if (target / "qualification_result.json").is_file():
        result_paths.append(target / "qualification_result.json")
    result_reports = [_verify_result(root, path) for path in result_paths]
    scientific_reports = [
        report
        for report in result_reports
        if f"search_dev_{SEARCH_RUN_ID}_" in report["result_path"]
        or report["split"] == "qualification"
    ]
    evaluator_diagnostic_reports = [
        report
        for report in result_reports
        if report["split"] == "evaluator_only_diagnostic"
    ]
    superseded_reports = [
        report
        for report in result_reports
        if report not in scientific_reports
        and report not in evaluator_diagnostic_reports
    ]
    protected = _protected_audit(root)
    packet = _packet_audit(root)

    tamper_findings = {}
    positive_control_path = next(
        (
            path
            for path in result_paths
            if f"search_dev_{SEARCH_RUN_ID}_" in path.name
        ),
        result_paths[0] if result_paths else None,
    )
    if positive_control_path is not None:
        result = json.loads(positive_control_path.read_text(encoding="utf-8"))
        rows_path = root / result["rows_path"]
        rows = _read_rows(rows_path)
        changed = deepcopy(rows)
        changed[0]["deficit_loss"] = round(float(changed[0]["deficit_loss"]) + 0.125, 12)
        tamper_findings["row_value_tamper_detected"] = not verify_rows_payload(
            result, changed, rows_path
        )["passed"]
        state_changed = deepcopy(rows)
        state_changed[0]["candidate_state_hash"] = "0" * 64
        tamper_findings["state_hash_tamper_detected"] = not verify_rows_payload(
            result, state_changed, rows_path
        )["passed"]
        result_changed = deepcopy(result)
        result_changed["row_recomputation_target"] = {}
        tamper_findings["summary_tamper_detected"] = not verify_rows_payload(
            result_changed, rows, rows_path
        )["passed"]
    else:
        tamper_findings = {
            "row_value_tamper_detected": False,
            "state_hash_tamper_detected": False,
            "summary_tamper_detected": False,
        }
    clean_payload = {
        "observation": {"schema_version": "public", "visual": []},
        "organism": {"energy": 0.5, "safety": 0.5},
        "last_action": None,
        "last_delta": {"energy": 0.0, "safety": 0.0},
    }
    leakage_controls = {}
    for field in sorted(PRIVATE_FIELDS):
        contaminated = deepcopy(clean_payload)
        contaminated[field] = "private"
        leakage_controls[field] = _private_payload_detected(contaminated)
    report = {
        "schema_version": "ego.v2.transfer_mechanism.independent_verification.v1",
        "task_id": TASK_ID,
        "producer_imported": False,
        "result_reports": result_reports,
        "scientific_result_reports": [
            report["result_path"] for report in scientific_reports
        ],
        "superseded_diagnostic_result_reports": [
            report["result_path"] for report in superseded_reports
        ],
        "evaluator_only_diagnostic_result_reports": [
            report["result_path"] for report in evaluator_diagnostic_reports
        ],
        "supersession_reason": "HISTORY_SHUFFLE_FAST_META_PAIRING_WIRING_FIX",
        "valid_latent_alignment_reference_report": next(
            (
                report["result_path"]
                for report in result_reports
                if report["result_path"].endswith(
                    "latent_alignment_reference_result.json"
                )
            ),
            None,
        ),
        "protected_predecessors": protected,
        "packet_commitment": packet,
        "tamper_positive_controls": tamper_findings,
        "leakage_positive_controls": leakage_controls,
        "latent_alignment_excluded_from_public_recomputation": all(
            report["row_recomputation"]["private_diagnostic_row_count"] > 0
            for report in scientific_reports
        ),
    }
    report["passed"] = (
        len(scientific_reports) == 3
        and all(item["passed"] for item in result_reports)
        and protected["passed"]
        and packet["passed"]
        and all(tamper_findings.values())
        and all(leakage_controls.values())
        and report["latent_alignment_excluded_from_public_recomputation"]
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    report = verify_campaign(args.root)
    target = _artifact_root(args.root)
    path = target / "independent_row_recomputation_report.json"
    path.write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
