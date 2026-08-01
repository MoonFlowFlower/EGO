"""Independent stored-row verifier for the 001K dev-only research campaign."""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any, Mapping


TASK_ID = "EGO-V2-PUBLIC-ACQUISITION-CAPACITY-RECOVERY-001K"
PUBLIC_FIELDS = ["observation", "organism", "last_action", "last_delta"]
FORBIDDEN_PUBLIC_FIELDS = {
    "seed",
    "world_id",
    "context_id",
    "opaque_context_id",
    "layout_id",
    "layout",
    "mapping_index",
    "mapping_commitment",
    "token_mapping",
    "private_pose",
    "position",
    "cause",
    "oracle",
    "oracle_action",
    "split",
    "packet",
    "future",
    "verdict",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"row {line_number} is not an object")
        rows.append(value)
    return rows


def _group_trajectories(rows: list[dict[str, Any]]) -> dict[tuple[str, str, int], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row["opaque_context_id"]),
            str(row["candidate_id"]),
            int(row["policy_seed"]),
        )
        grouped[key].append(row)
    return grouped


def _verify_trace_chains(
    grouped: Mapping[tuple[str, str, int], list[dict[str, Any]]]
) -> list[str]:
    findings: list[str] = []
    for key, unordered in grouped.items():
        rows = sorted(unordered, key=lambda row: int(row["sequence"]))
        previous = None
        for expected_sequence, row in enumerate(rows, start=1):
            if int(row["sequence"]) != expected_sequence:
                findings.append(f"sequence_gap:{key}:{expected_sequence}")
            if row.get("prev_trace_hash") != previous:
                findings.append(f"prev_trace_mismatch:{key}:{expected_sequence}")
            unhashed = {
                field: value
                for field, value in row.items()
                if field not in {"trace_hash", "formal_packet_name"}
            }
            expected_hash = canonical_hash(unhashed)
            if row.get("trace_hash") != expected_hash:
                findings.append(f"trace_hash_mismatch:{key}:{expected_sequence}")
            previous = row.get("trace_hash")
    return findings


def _trajectory_losses(
    grouped: Mapping[tuple[str, str, int], list[dict[str, Any]]]
) -> dict[tuple[str, str, int], float]:
    result = {}
    for key, rows in grouped.items():
        result[key] = round(
            sum(float(row["deficit_loss"]) for row in rows) / len(rows), 12
        )
    return result


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 12)


def _recompute_metrics(
    rows: list[dict[str, Any]], thresholds: Mapping[str, Any]
) -> dict[str, Any]:
    grouped = _group_trajectories(rows)
    losses = _trajectory_losses(grouped)
    candidate_ids = sorted({key[1] for key in losses})
    required = {
        "PRIVATE_ORACLE_NAVIGATOR",
        "UNIFORM_RANDOM",
        "S2_RISK_INFORMATION_GAIN",
        "FORMAL_NO_UPDATE",
        "FORMAL_FEEDBACK_SHUFFLE",
        "FORMAL_POSTERIOR_ABLATION",
    }
    if set(candidate_ids) != required:
        raise ValueError(f"formal arm set mismatch: {candidate_ids}")

    by_candidate = {
        candidate_id: [value for key, value in losses.items() if key[1] == candidate_id]
        for candidate_id in candidate_ids
    }
    mean_loss = {
        candidate_id: _mean(values) for candidate_id, values in by_candidate.items()
    }
    oracle_loss = mean_loss["PRIVATE_ORACLE_NAVIGATOR"]
    random_loss = mean_loss["UNIFORM_RANDOM"]
    public_loss = mean_loss["S2_RISK_INFORMATION_GAIN"]
    headroom = round(random_loss - oracle_loss, 12)
    gain = round(random_loss - public_loss, 12)
    recovery = round(gain / headroom, 12) if headroom > 0 else None

    public_keys = sorted(key for key in losses if key[1] == "S2_RISK_INFORMATION_GAIN")
    trajectory_positive = 0
    by_world_public: dict[str, list[float]] = defaultdict(list)
    by_world_random: dict[str, list[float]] = defaultdict(list)
    for context_id, _candidate, policy_seed in public_keys:
        public_value = losses[(context_id, "S2_RISK_INFORMATION_GAIN", policy_seed)]
        random_value = losses[(context_id, "UNIFORM_RANDOM", policy_seed)]
        trajectory_positive += public_value < random_value
        by_world_public[context_id].append(public_value)
        by_world_random[context_id].append(random_value)
    world_positive = sum(
        _mean(by_world_public[context]) < _mean(by_world_random[context])
        for context in by_world_public
    )
    public_final_rows = []
    for key in public_keys:
        trajectory_rows = sorted(
            grouped[key], key=lambda row: int(row["sequence"])
        )
        public_final_rows.append(trajectory_rows[-1])
    sign_accuracy = _mean(
        [float(row["effect_sign_accuracy"]) for row in public_final_rows]
    )

    ablation_rows = []
    damage_threshold = max(
        float(thresholds["material_ablation_absolute_floor"]),
        float(thresholds["material_ablation_relative_gain_fraction"]) * max(0.0, gain),
    )
    for candidate_id in (
        "FORMAL_NO_UPDATE",
        "FORMAL_FEEDBACK_SHUFFLE",
        "FORMAL_POSTERIOR_ABLATION",
    ):
        ablation_gain = round(random_loss - mean_loss[candidate_id], 12)
        damage = round(gain - ablation_gain, 12)
        ablation_rows.append(
            {
                "candidate_id": candidate_id,
                "ablation_gain": ablation_gain,
                "gain_damage": damage,
                "material": damage >= damage_threshold,
            }
        )
    return {
        "loss_by_candidate": mean_loss,
        "oracle_random_headroom": headroom,
        "public_reference_gain": gain,
        "recovery_fraction": recovery,
        "positive_trajectory_count": trajectory_positive,
        "trajectory_count": len(public_keys),
        "positive_world_count": world_positive,
        "world_count": len(by_world_public),
        "mean_final_effect_sign_accuracy": sign_accuracy,
        "ablation_damage_threshold": round(damage_threshold, 12),
        "material_ablation_count": sum(row["material"] for row in ablation_rows),
        "ablation_rows": ablation_rows,
    }


def verify_formal_packet(
    root: Path,
    packet_name: str,
    *,
    result_path: Path | None = None,
    rows_path: Path | None = None,
    freeze_path: Path | None = None,
) -> dict[str, Any]:
    if packet_name not in {"qualification", "replication"}:
        raise ValueError("packet must be qualification or replication")
    root = Path(root).resolve()
    artifact_root = root / "artifacts" / TASK_ID
    result_path = Path(result_path or artifact_root / f"{packet_name}_result.json")
    rows_path = Path(rows_path or artifact_root / f"{packet_name}_rows.jsonl")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    freeze = json.loads(
        Path(freeze_path or artifact_root / "candidate_freeze.json").read_text(
            encoding="utf-8"
        )
    )
    rows = _load_rows(rows_path)
    findings: list[str] = []
    if sha256(rows_path) != result.get("rows_sha256"):
        findings.append("rows_sha256_mismatch")
    if result.get("packet_name") != packet_name or result.get("task_id") != TASK_ID:
        findings.append("result_authority_mismatch")
    if result.get("candidate_freeze_hash") != canonical_hash(freeze):
        findings.append("candidate_freeze_hash_mismatch")
    assignment_path = artifact_root / f"{packet_name}_assignments.json"
    if sha256(assignment_path) != result.get("assignment_sha256"):
        findings.append("assignment_hash_mismatch")
    findings.extend(_verify_trace_chains(_group_trajectories(rows)))

    for index, row in enumerate(rows):
        if row.get("formal_packet_name") != packet_name:
            findings.append(f"packet_row_label_mismatch:{index}")
        if row.get("arm") == "PUBLIC_REFERENCE":
            if row.get("candidate_input_clean") is not True:
                findings.append(f"candidate_input_not_clean:{index}")
            if row.get("candidate_input_fields") != PUBLIC_FIELDS:
                findings.append(f"candidate_input_field_mismatch:{index}")
            ranked = row.get("ranked_tokens", [])
            for ranked_row in ranked:
                if set(ranked_row) != {
                    "token",
                    "relative_x",
                    "relative_y",
                    "distance",
                    "known",
                    "score",
                }:
                    findings.append(f"ranked_token_private_field:{index}")
                if set(ranked_row) & FORBIDDEN_PUBLIC_FIELDS:
                    findings.append(f"ranked_token_forbidden_field:{index}")
        if str(row.get("opaque_context_id", "")).startswith("001j-"):
            findings.append(f"original_001j_context_consumed:{index}")

    recomputed = _recompute_metrics(rows, freeze["thresholds"])
    stored_candidate = result["candidate"]
    expected_pairs = {
        "oracle_random_headroom": stored_candidate["oracle_random_headroom"],
        "public_reference_gain": stored_candidate["public_reference_gain"],
        "recovery_fraction": stored_candidate["recovery_fraction"],
        "positive_trajectory_count": stored_candidate["positive_direction_count"],
        "positive_world_count": result["world_directions"]["positive_world_count"],
        "mean_final_effect_sign_accuracy": stored_candidate[
            "mean_final_effect_sign_accuracy"
        ],
        "material_ablation_count": result["ablation_report"]["material_count"],
    }
    for key, stored in expected_pairs.items():
        if recomputed[key] != stored:
            findings.append(f"aggregate_mismatch:{key}")
    for candidate_id, stored_loss in stored_candidate["loss_by_arm"].items():
        mapped = {
            "PRIVATE_ORACLE_NAVIGATOR": "PRIVATE_ORACLE_NAVIGATOR",
            "PUBLIC_REFERENCE": "S2_RISK_INFORMATION_GAIN",
            "UNIFORM_RANDOM": "UNIFORM_RANDOM",
        }[candidate_id]
        if recomputed["loss_by_candidate"][mapped] != stored_loss:
            findings.append(f"loss_mismatch:{candidate_id}")

    return {
        "schema_version": "ego.v2.public_acquisition.row_verification.v1",
        "task_id": TASK_ID,
        "packet_name": packet_name,
        "result_path": result_path.as_posix(),
        "rows_path": rows_path.as_posix(),
        "row_count": len(rows),
        "recomputed": recomputed,
        "stored_verdict": result["verdict"],
        "findings": sorted(set(findings)),
        "passed": not findings,
        "original_001j_packet_executed": False,
        "claim_ceiling": "Stored dev-only row integrity and metric recomputation only.",
    }


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8"
    )


def _payload_has_forbidden_key(payload: Any) -> bool:
    if isinstance(payload, Mapping):
        return any(
            str(key).lower() in FORBIDDEN_PUBLIC_FIELDS
            or _payload_has_forbidden_key(value)
            for key, value in payload.items()
        )
    if isinstance(payload, (list, tuple)):
        return any(_payload_has_forbidden_key(value) for value in payload)
    return False


def run_positive_controls(root: Path) -> dict[str, Any]:
    """Inject representative leakage and evidence tampering; every case must reject."""

    root = Path(root).resolve()
    artifact_root = root / "artifacts" / TASK_ID
    baseline = verify_formal_packet(root, "qualification")
    cases: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="001k-tamper-") as raw_tmp:
        tmp = Path(raw_tmp)
        original_rows = _load_rows(artifact_root / "qualification_rows.jsonl")
        result_path = artifact_root / "qualification_result.json"

        deficit_rows = deepcopy(original_rows)
        deficit_rows[0]["deficit_loss"] = round(
            float(deficit_rows[0]["deficit_loss"]) + 0.125, 12
        )
        deficit_path = tmp / "deficit_rows.jsonl"
        _write_jsonl(deficit_path, deficit_rows)
        deficit_report = verify_formal_packet(
            root,
            "qualification",
            result_path=result_path,
            rows_path=deficit_path,
        )
        cases["row_value_tamper"] = {
            "detected": not deficit_report["passed"],
            "finding_prefixes": sorted(deficit_report["findings"])[:8],
        }

        leak_rows = deepcopy(original_rows)
        leak_index = next(
            index
            for index, row in enumerate(leak_rows)
            if row["candidate_id"] == "S2_RISK_INFORMATION_GAIN"
            and row["ranked_tokens"]
        )
        leak_rows[leak_index]["ranked_tokens"][0]["world_id"] = "private-leak"
        leak_path = tmp / "leak_rows.jsonl"
        _write_jsonl(leak_path, leak_rows)
        leak_report = verify_formal_packet(
            root,
            "qualification",
            result_path=result_path,
            rows_path=leak_path,
        )
        cases["candidate_receipt_leak"] = {
            "detected": (
                not leak_report["passed"]
                and any(
                    finding.startswith("ranked_token_private_field")
                    for finding in leak_report["findings"]
                )
            ),
            "finding_prefixes": sorted(leak_report["findings"])[:8],
        }

        stored_result = json.loads(result_path.read_text(encoding="utf-8"))
        aggregate_result = deepcopy(stored_result)
        aggregate_result["candidate"]["public_reference_gain"] = round(
            float(aggregate_result["candidate"]["public_reference_gain"]) + 0.1,
            12,
        )
        aggregate_path = tmp / "aggregate_result.json"
        aggregate_path.write_text(
            json.dumps(aggregate_result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        aggregate_report = verify_formal_packet(
            root,
            "qualification",
            result_path=aggregate_path,
            rows_path=artifact_root / "qualification_rows.jsonl",
        )
        cases["stored_aggregate_tamper"] = {
            "detected": (
                not aggregate_report["passed"]
                and "aggregate_mismatch:public_reference_gain"
                in aggregate_report["findings"]
            ),
            "finding_prefixes": aggregate_report["findings"],
        }

        assignment_path = artifact_root / "qualification_assignments.json"
        assignment_bytes = bytearray(assignment_path.read_bytes())
        assignment_bytes[len(assignment_bytes) // 2] ^= 1
        commitments = json.loads(
            (artifact_root / "packet_commitments.json").read_text(encoding="utf-8")
        )
        tampered_assignment_hash = hashlib.sha256(assignment_bytes).hexdigest()
        cases["assignment_tamper"] = {
            "detected": (
                tampered_assignment_hash
                != commitments["packets"]["qualification"]["assignment_sha256"]
            ),
            "tampered_hash": tampered_assignment_hash,
        }

    clean_payload = {
        "observation": {"visual": [["empty"] * 5 for _ in range(5)]},
        "organism": {"energy": 0.4, "safety": 0.5},
        "last_action": None,
        "last_delta": {"energy": 0.0, "safety": 0.0},
    }
    leakage_cases = {}
    for field in (
        "seed",
        "world_id",
        "layout_id",
        "mapping_commitment",
        "private_pose",
        "cause",
        "oracle_action",
        "split",
        "future",
    ):
        payload = deepcopy(clean_payload)
        payload[field] = "forbidden"
        leakage_cases[field] = _payload_has_forbidden_key(payload)
    cases["public_input_leakage_fields"] = {
        "detected": all(leakage_cases.values()),
        "cases": leakage_cases,
    }
    return {
        "schema_version": "ego.v2.public_acquisition.leakage_tamper_controls.v1",
        "task_id": TASK_ID,
        "baseline_qualification_verifier_passed": baseline["passed"],
        "cases": cases,
        "all_positive_controls_detected": (
            baseline["passed"] and all(case["detected"] for case in cases.values())
        ),
        "original_001j_packet_executed": False,
        "claim_ceiling": "Integrity and leakage positive controls only.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--packet", choices=("qualification", "replication"))
    parser.add_argument("--positive-controls", action="store_true")
    parser.add_argument("--result", type=Path)
    parser.add_argument("--rows", type=Path)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if int(args.packet is not None) + int(args.positive_controls) != 1:
        parser.error("select exactly one of --packet or --positive-controls")
    report = (
        run_positive_controls(args.root)
        if args.positive_controls
        else verify_formal_packet(
            args.root,
            str(args.packet),
            result_path=args.result,
            rows_path=args.rows,
            freeze_path=args.freeze,
        )
    )
    if args.output is not None:
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    passed = report.get("passed", report.get("all_positive_controls_detected", False))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
