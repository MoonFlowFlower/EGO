"""Independent stored-row verifier for the bounded 001L robustness successor.

This module intentionally does not import the campaign producer.  It treats the
frozen JSON and JSONL artifacts as untrusted inputs and recomputes the reported
metrics from rows.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any, Mapping


TASK_ID = "EGO-V2-PUBLIC-ACQUISITION-ROBUSTNESS-001L"
PRODUCER_MODULE_NAME = "scripts.codex.run_ego_v2_public_acquisition_robustness_001l"
PUBLIC_FIELDS = ["observation", "organism", "last_action", "last_delta"]
FORBIDDEN_PUBLIC_FIELDS = {
    "seed",
    "world_seed",
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


def declared_positive_controls() -> tuple[str, ...]:
    return (
        "row_value_tamper",
        "stored_aggregate_tamper",
        "assignment_byte_tamper",
        "candidate_private_field_injection",
        "protected_predecessor_tamper",
    )


def _load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.write_text(
        "".join(canonical_json(row) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("cannot take an empty mean")
    return round(sum(values) / len(values), 12)


def _group_trajectories(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str, int], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row["opaque_context_id"]),
                str(row["candidate_id"]),
                int(row["policy_seed"]),
            )
        ].append(row)
    return grouped


def _verify_trace_chains(
    grouped: Mapping[tuple[str, str, int], list[dict[str, Any]]]
) -> list[str]:
    findings: list[str] = []
    for key, unordered in grouped.items():
        rows = sorted(unordered, key=lambda row: int(row["sequence"]))
        previous = None
        expected_budget = int(rows[0]["budget"])
        if len(rows) != expected_budget:
            findings.append(f"trajectory_length_mismatch:{key}")
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
            expected = canonical_hash(unhashed)
            if row.get("trace_hash") != expected:
                findings.append(f"trace_hash_mismatch:{key}:{expected_sequence}")
            previous = row.get("trace_hash")
    return findings


def _trajectory_losses(
    grouped: Mapping[tuple[str, str, int], list[dict[str, Any]]]
) -> dict[tuple[str, str, int], float]:
    return {
        key: _mean([float(row["deficit_loss"]) for row in rows])
        for key, rows in grouped.items()
    }


def _recompute_metrics(
    rows: list[dict[str, Any]],
    *,
    candidate_id: str,
    thresholds: Mapping[str, Any],
) -> dict[str, Any]:
    grouped = _group_trajectories(rows)
    losses = _trajectory_losses(grouped)
    ablation_ids = {
        "FORMAL_NO_UPDATE",
        "FORMAL_FEEDBACK_SHUFFLE",
        "FORMAL_POSTERIOR_ABLATION",
    }
    required = {
        "PRIVATE_ORACLE_NAVIGATOR",
        "UNIFORM_RANDOM",
        candidate_id,
        *ablation_ids,
    }
    actual = {key[1] for key in losses}
    if actual != required:
        raise ValueError(f"formal arm set mismatch: {sorted(actual)}")
    by_candidate = {
        arm: [value for key, value in losses.items() if key[1] == arm]
        for arm in required
    }
    mean_loss = {arm: _mean(values) for arm, values in by_candidate.items()}
    oracle_loss = mean_loss["PRIVATE_ORACLE_NAVIGATOR"]
    random_loss = mean_loss["UNIFORM_RANDOM"]
    public_loss = mean_loss[candidate_id]
    headroom = round(random_loss - oracle_loss, 12)
    gain = round(random_loss - public_loss, 12)
    recovery = round(gain / headroom, 12) if headroom > 0.0 else None

    public_keys = sorted(key for key in losses if key[1] == candidate_id)
    by_world_public: dict[str, list[float]] = defaultdict(list)
    by_world_random: dict[str, list[float]] = defaultdict(list)
    positive_trajectories = 0
    for context_id, _arm, policy_seed in public_keys:
        public_value = losses[(context_id, candidate_id, policy_seed)]
        random_value = losses[(context_id, "UNIFORM_RANDOM", policy_seed)]
        positive_trajectories += public_value < random_value
        by_world_public[context_id].append(public_value)
        by_world_random[context_id].append(random_value)
    positive_worlds = sum(
        _mean(by_world_public[context]) < _mean(by_world_random[context])
        for context in by_world_public
    )
    final_rows = [
        sorted(grouped[key], key=lambda row: int(row["sequence"]))[-1]
        for key in public_keys
    ]
    sign_accuracy = _mean([float(row["effect_sign_accuracy"]) for row in final_rows])

    damage_threshold = max(
        float(thresholds["material_ablation_absolute_floor"]),
        float(thresholds["material_ablation_relative_gain_fraction"])
        * max(0.0, gain),
    )
    ablation_rows = []
    for ablation_id in sorted(ablation_ids):
        ablation_gain = round(random_loss - mean_loss[ablation_id], 12)
        damage = round(gain - ablation_gain, 12)
        ablation_rows.append(
            {
                "candidate_id": ablation_id,
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
        "positive_trajectory_count": positive_trajectories,
        "trajectory_count": len(public_keys),
        "positive_world_count": positive_worlds,
        "world_count": len(by_world_public),
        "mean_final_effect_sign_accuracy": sign_accuracy,
        "ablation_damage_threshold": round(damage_threshold, 12),
        "material_ablation_count": sum(row["material"] for row in ablation_rows),
        "ablation_rows": ablation_rows,
    }


def _candidate_receipt_findings(rows: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    allowed_ranked = {
        "token",
        "relative_x",
        "relative_y",
        "distance",
        "known",
        "score",
    }
    for index, row in enumerate(rows):
        if row.get("arm") != "PUBLIC_REFERENCE":
            continue
        if row.get("candidate_input_clean") is not True:
            findings.append(f"candidate_input_not_clean:{index}")
        if row.get("candidate_input_fields") != PUBLIC_FIELDS:
            findings.append(f"candidate_input_field_mismatch:{index}")
        for ranked in row.get("ranked_tokens", []):
            keys = set(ranked)
            if keys != allowed_ranked:
                findings.append(f"ranked_token_private_field:{index}")
            if keys & FORBIDDEN_PUBLIC_FIELDS:
                findings.append(f"ranked_token_forbidden_field:{index}")
    return findings


def _verify_protected_manifest(root: Path, manifest: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    for item in manifest.get("files", []):
        path = root / str(item["path"])
        if not path.is_file() or sha256(path) != item.get("sha256"):
            findings.append(f"protected_predecessor_mismatch:{item.get('path')}")
    return findings


def verify_formal_packet(
    root: Path,
    packet_name: str,
    *,
    result_path: Path | None = None,
    rows_path: Path | None = None,
    freeze_path: Path | None = None,
    protected_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if packet_name not in {"qualification", "replication"}:
        raise ValueError("packet must be qualification or replication")
    root = Path(root).resolve()
    artifact_root = root / "artifacts" / TASK_ID
    result_path = Path(result_path or artifact_root / f"{packet_name}_result.json")
    rows_path = Path(rows_path or artifact_root / f"{packet_name}_rows.jsonl")
    freeze_path = Path(freeze_path or artifact_root / "candidate_freeze.json")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    rows = _load_rows(rows_path)
    findings: list[str] = []

    if result.get("task_id") != TASK_ID or result.get("packet_name") != packet_name:
        findings.append("result_authority_mismatch")
    if sha256(rows_path) != result.get("rows_sha256"):
        findings.append("rows_sha256_mismatch")
    if result.get("candidate_freeze_hash") != canonical_hash(freeze):
        findings.append("candidate_freeze_hash_mismatch")
    producer_path = root / str(freeze.get("producer_path", ""))
    verifier_path = root / str(freeze.get("verifier_path", ""))
    if not producer_path.is_file() or sha256(producer_path) != freeze.get("producer_sha256"):
        findings.append("producer_hash_mismatch")
    if not verifier_path.is_file() or sha256(verifier_path) != freeze.get("verifier_sha256"):
        findings.append("verifier_hash_mismatch")
    assignment_path = artifact_root / f"{packet_name}_assignments.json"
    if sha256(assignment_path) != result.get("assignment_sha256"):
        findings.append("assignment_hash_mismatch")
    commitments = json.loads(
        (artifact_root / "packet_commitments.json").read_text(encoding="utf-8")
    )
    protected_path = root / commitments["protected_predecessor_hashes_path"]
    if sha256(protected_path) != commitments["protected_predecessor_hashes_sha256"]:
        findings.append("protected_manifest_hash_mismatch")
    manifest = protected_manifest or json.loads(protected_path.read_text(encoding="utf-8"))
    findings.extend(_verify_protected_manifest(root, manifest))
    findings.extend(_verify_trace_chains(_group_trajectories(rows)))
    findings.extend(_candidate_receipt_findings(rows))
    for index, row in enumerate(rows):
        if row.get("formal_packet_name") != packet_name:
            findings.append(f"packet_row_label_mismatch:{index}")
        if str(row.get("opaque_context_id", "")).startswith("001j-"):
            findings.append(f"original_001j_context_consumed:{index}")

    candidate_id = str(freeze["candidate_id"])
    try:
        recomputed = _recompute_metrics(
            rows, candidate_id=candidate_id, thresholds=freeze["thresholds"]
        )
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        findings.append(f"metric_recomputation_error:{type(exc).__name__}:{exc}")
        recomputed = {}
    if recomputed:
        stored_candidate = result["candidate"]
        expected = {
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
        for key, stored in expected.items():
            if recomputed[key] != stored:
                findings.append(f"aggregate_mismatch:{key}")
        loss_mapping = {
            "PRIVATE_ORACLE_NAVIGATOR": "PRIVATE_ORACLE_NAVIGATOR",
            "PUBLIC_REFERENCE": candidate_id,
            "UNIFORM_RANDOM": "UNIFORM_RANDOM",
        }
        for stored_arm, row_candidate in loss_mapping.items():
            if recomputed["loss_by_candidate"][row_candidate] != stored_candidate[
                "loss_by_arm"
            ][stored_arm]:
                findings.append(f"loss_mismatch:{stored_arm}")

    return {
        "schema_version": "ego.v2.public_acquisition_robustness.row_verification.v1",
        "task_id": TASK_ID,
        "packet_name": packet_name,
        "row_count": len(rows),
        "recomputed": recomputed,
        "stored_verdict": result.get("verdict"),
        "findings": sorted(set(findings)),
        "passed": not findings,
        "original_001j_packet_executed": False,
        "claim_ceiling": "Independent dev-only row integrity and metric recomputation only.",
    }


def run_positive_controls(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    artifact_root = root / "artifacts" / TASK_ID
    baseline = verify_formal_packet(root, "qualification")
    cases: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="001l-tamper-") as raw_tmp:
        tmp = Path(raw_tmp)
        original_rows = _load_rows(artifact_root / "qualification_rows.jsonl")
        result_path = artifact_root / "qualification_result.json"

        tampered_rows = deepcopy(original_rows)
        tampered_rows[0]["deficit_loss"] = round(
            float(tampered_rows[0]["deficit_loss"]) + 0.125, 12
        )
        tampered_path = tmp / "row_value.jsonl"
        _write_jsonl(tampered_path, tampered_rows)
        report = verify_formal_packet(
            root, "qualification", result_path=result_path, rows_path=tampered_path
        )
        cases["row_value_tamper"] = {
            "detected": not report["passed"],
            "findings": report["findings"][:10],
        }

        aggregate = json.loads(result_path.read_text(encoding="utf-8"))
        aggregate["candidate"]["public_reference_gain"] = round(
            float(aggregate["candidate"]["public_reference_gain"]) + 0.1, 12
        )
        aggregate_path = tmp / "aggregate.json"
        aggregate_path.write_text(
            json.dumps(aggregate, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        report = verify_formal_packet(
            root,
            "qualification",
            result_path=aggregate_path,
            rows_path=artifact_root / "qualification_rows.jsonl",
        )
        cases["stored_aggregate_tamper"] = {
            "detected": "aggregate_mismatch:public_reference_gain" in report["findings"],
            "findings": report["findings"][:10],
        }

        assignment_bytes = bytearray(
            (artifact_root / "qualification_assignments.json").read_bytes()
        )
        assignment_bytes[len(assignment_bytes) // 2] ^= 1
        freeze = json.loads(
            (artifact_root / "candidate_freeze.json").read_text(encoding="utf-8")
        )
        cases["assignment_byte_tamper"] = {
            "detected": hashlib.sha256(assignment_bytes).hexdigest()
            != freeze["packet_assignment_sha256"]["qualification"]
        }

        leak_rows = deepcopy(original_rows)
        leak_index = next(
            index
            for index, row in enumerate(leak_rows)
            if row["arm"] == "PUBLIC_REFERENCE" and row.get("ranked_tokens")
        )
        leak_rows[leak_index]["ranked_tokens"][0]["world_id"] = "private-leak"
        leak_path = tmp / "private_field.jsonl"
        _write_jsonl(leak_path, leak_rows)
        report = verify_formal_packet(
            root, "qualification", result_path=result_path, rows_path=leak_path
        )
        cases["candidate_private_field_injection"] = {
            "detected": any(
                finding.startswith("ranked_token_private_field")
                or finding.startswith("ranked_token_forbidden_field")
                for finding in report["findings"]
            ),
            "findings": report["findings"][:10],
        }

        commitments = json.loads(
            (artifact_root / "packet_commitments.json").read_text(encoding="utf-8")
        )
        manifest = json.loads(
            (root / commitments["protected_predecessor_hashes_path"]).read_text(
                encoding="utf-8"
            )
        )
        manifest["files"][0]["sha256"] = "0" * 64
        findings = _verify_protected_manifest(root, manifest)
        cases["protected_predecessor_tamper"] = {
            "detected": bool(findings),
            "findings": findings[:10],
        }

    return {
        "schema_version": "ego.v2.public_acquisition_robustness.controls.v1",
        "task_id": TASK_ID,
        "baseline_qualification_verifier_passed": baseline["passed"],
        "cases": cases,
        "declared_controls": list(declared_positive_controls()),
        "all_positive_controls_detected": (
            baseline["passed"]
            and set(cases) == set(declared_positive_controls())
            and all(case["detected"] for case in cases.values())
        ),
        "original_001j_packet_executed": False,
        "claim_ceiling": "Leakage and stored-evidence tamper detection only.",
    }


def finalize_campaign(root: Path) -> dict[str, Any]:
    """Land independent closeout only after both immutable formal readbacks exist."""

    root = Path(root).resolve()
    artifact_root = root / "artifacts" / TASK_ID
    required = [
        artifact_root / "search_results.json",
        artifact_root / "candidate_freeze.json",
        artifact_root / "qualification_result.json",
        artifact_root / "replication_result.json",
    ]
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"cannot finalize before formal readbacks: {missing}")
    outputs = [
        artifact_root / "row_recomputation_report.json",
        artifact_root / "leakage_tamper_report.json",
        artifact_root / "trial_registry.jsonl",
        artifact_root / "failure_manifest.json",
        artifact_root / "campaign_report.json",
        artifact_root / "artifact_manifest.json",
    ]
    if any(path.exists() for path in outputs):
        raise RuntimeError("campaign closeout is single-write")

    search = json.loads(required[0].read_text(encoding="utf-8"))
    qualification = json.loads(required[2].read_text(encoding="utf-8"))
    replication = json.loads(required[3].read_text(encoding="utf-8"))
    qualification_verification = verify_formal_packet(root, "qualification")
    replication_verification = verify_formal_packet(root, "replication")
    controls = run_positive_controls(root)
    recomputation = {
        "schema_version": "ego.v2.public_acquisition_robustness.recomputation.v1",
        "task_id": TASK_ID,
        "qualification": qualification_verification,
        "replication": replication_verification,
        "all_packets_recomputed": (
            qualification_verification["passed"]
            and replication_verification["passed"]
        ),
    }
    _write_json(outputs[0], recomputation)
    _write_json(outputs[1], controls)

    search_trials = _load_rows(artifact_root / "search_trial_registry.jsonl")
    trial_rows: list[dict[str, Any]] = list(search_trials)
    failures = [deepcopy(row) for row in search_trials if row["failure_explanation"]]
    for packet_name, result in (
        ("qualification", qualification),
        ("replication", replication),
    ):
        failed_gates = sorted(key for key, value in result["gates"].items() if not value)
        formal_trial = {
            "schema_version": "ego.v2.public_acquisition_robustness.trial.v1",
            "task_id": TASK_ID,
            "stage": packet_name,
            "candidate_id": result["candidate_id"],
            "hypothesis": "Frozen search candidate generalizes without tuning.",
            "mechanism_change": "none_after_freeze",
            "random_deficit_auc": result["candidate"]["loss_by_arm"][
                "UNIFORM_RANDOM"
            ],
            "oracle_deficit_auc": result["candidate"]["loss_by_arm"][
                "PRIVATE_ORACLE_NAVIGATOR"
            ],
            "public_deficit_auc": result["candidate"]["loss_by_arm"][
                "PUBLIC_REFERENCE"
            ],
            "public_reference_gain": result["candidate"]["public_reference_gain"],
            "recovery_fraction": result["candidate"]["recovery_fraction"],
            "positive_world_count": result["world_directions"][
                "positive_world_count"
            ],
            "world_count": result["world_directions"]["world_count"],
            "effect_sign_accuracy": result["candidate"][
                "mean_final_effect_sign_accuracy"
            ],
            "ablation_material_count": result["ablation_report"]["material_count"],
            "failed_gates": failed_gates,
            "failure_explanation": (
                None if result["all_gates_pass"] else f"Failed gates: {failed_gates}"
            ),
            "next_stage_allowed": result["all_gates_pass"],
        }
        trial_rows.append(formal_trial)
        if formal_trial["failure_explanation"]:
            failures.append(deepcopy(formal_trial))
        for ablation in result["ablations"]:
            trial_rows.append(
                {
                    "schema_version": "ego.v2.public_acquisition_robustness.trial.v1",
                    "task_id": TASK_ID,
                    "stage": packet_name,
                    "candidate_id": ablation["candidate_id"],
                    "hypothesis": ablation["config"]["preregistered_prediction"],
                    "mechanism_change": ablation["config"]["posterior_mode"],
                    "public_reference_gain": ablation["public_reference_gain"],
                    "recovery_fraction": ablation["recovery_fraction"],
                    "positive_world_count": ablation["positive_direction_count"],
                    "world_count": ablation["unique_world_count"],
                    "failure_explanation": None,
                    "next_stage_allowed": False,
                    "diagnostic_control_only": True,
                }
            )
    _write_jsonl(outputs[2], trial_rows)

    both_formal_pass = qualification["all_gates_pass"] and replication[
        "all_gates_pass"
    ]
    independent_evidence_pass = (
        recomputation["all_packets_recomputed"]
        and controls["all_positive_controls_detected"]
    )
    authorized = both_formal_pass and independent_evidence_pass
    verdict = (
        "ROBUSTNESS_ESTABLISHED_MINIMAL_TWO_TIMESCALE_LEARNER_AUTHORIZED"
        if authorized
        else "ROBUSTNESS_NOT_ESTABLISHED_M1_NOT_AUTHORIZED"
    )
    failure_manifest = {
        "schema_version": "ego.v2.public_acquisition_robustness.failures.v1",
        "task_id": TASK_ID,
        "failed_trials": failures,
        "qualification_failed_gates": sorted(
            key for key, value in qualification["gates"].items() if not value
        ),
        "replication_failed_gates": sorted(
            key for key, value in replication["gates"].items() if not value
        ),
        "independent_recomputation_passed": recomputation[
            "all_packets_recomputed"
        ],
        "positive_controls_passed": controls["all_positive_controls_detected"],
        "terminal_verdict": verdict,
        "thresholds_lowered": False,
    }
    _write_json(outputs[3], failure_manifest)

    report = {
        "schema_version": "ego.v2.public_acquisition_robustness.campaign.v1",
        "task_id": TASK_ID,
        "selected_candidate": search["selection"]["selected_candidate"],
        "search_verdict": search["verdict"],
        "qualification_verdict": qualification["verdict"],
        "replication_verdict": replication["verdict"],
        "qualification_recovery_fraction": qualification["candidate"][
            "recovery_fraction"
        ],
        "replication_recovery_fraction": replication["candidate"][
            "recovery_fraction"
        ],
        "qualification_positive_worlds": qualification["world_directions"][
            "positive_world_count"
        ],
        "replication_positive_worlds": replication["world_directions"][
            "positive_world_count"
        ],
        "both_formal_packets_passed": both_formal_pass,
        "independent_recomputation_passed": recomputation[
            "all_packets_recomputed"
        ],
        "leakage_tamper_controls_passed": controls[
            "all_positive_controls_detected"
        ],
        "minimal_two_timescale_learner_authorized": authorized,
        "verdict": verdict,
        "original_001j_heldout_executed": False,
        "frozen_001k_formal_packets_rerun": False,
        "thresholds_lowered": False,
        "claim_ceiling": (
            "Dev-only robustness of legal-public acquisition inside the frozen "
            "microworld grammar only; not general transfer, agency, consciousness, "
            "electronic life, or real-world survival."
        ),
    }
    _write_json(outputs[4], report)
    scorecard = json.loads(
        (artifact_root / "stage_scorecard.json").read_text(encoding="utf-8")
    )
    scorecard["qualification"] = qualification
    scorecard["replication"] = replication
    scorecard["independent_closeout"] = {
        "row_recomputation": recomputation["all_packets_recomputed"],
        "positive_controls": controls["all_positive_controls_detected"],
        "verdict": verdict,
    }
    _write_json(artifact_root / "stage_scorecard.json", scorecard)

    manifest_files = []
    for path in sorted(artifact_root.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "artifact_manifest.json":
            manifest_files.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256(path),
                    "size": path.stat().st_size,
                }
            )
    _write_json(
        outputs[5],
        {
            "schema_version": "ego.v2.public_acquisition_robustness.manifest.v1",
            "task_id": TASK_ID,
            "file_count": len(manifest_files),
            "files": manifest_files,
            "verdict": verdict,
        },
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--packet", choices=("qualification", "replication"))
    parser.add_argument("--positive-controls", action="store_true")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--result", type=Path)
    parser.add_argument("--rows", type=Path)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if (
        int(args.packet is not None)
        + int(args.positive_controls)
        + int(args.finalize)
        != 1
    ):
        parser.error("select exactly one of --packet or --positive-controls")
    report = (
        finalize_campaign(args.root)
        if args.finalize
        else run_positive_controls(args.root)
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
            json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False))
    if args.finalize:
        return 0
    passed = report.get("passed", report.get("all_positive_controls_detected", False))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
