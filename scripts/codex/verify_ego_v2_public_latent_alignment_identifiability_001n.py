"""Independent public-row recomputation for the 001N certificate.

This verifier intentionally does not import the producer or product runtime.
The frozen five-token/five-cause grammar is repeated as independent constants.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping


TASK_ID = "EGO-V2-PUBLIC-LATENT-ALIGNMENT-IDENTIFIABILITY-001N"
TOKENS = ("v0", "v1", "v2", "v3", "v4")
CAUSES = ("resource", "social", "novelty", "threat", "shelter")
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
    "true_mapping",
}
PASSIVE_DECAY = 0.010
INTERACT_COST = 0.008
CAUSE_DELTAS = {
    "resource": {"energy": 0.280, "safety": 0.0},
    "social": {"energy": 0.0, "safety": 0.0},
    "novelty": {"energy": 0.0, "safety": -0.020},
    "threat": {"energy": 0.0, "safety": -0.180},
    "shelter": {"energy": 0.0, "safety": 0.120},
}
TARGET_LEVEL = 0.72
EARLY_CUTOFF = 48
ARTIFACT_NAME = TASK_ID
ALL_ARMS = (
    "EXACT_BAYES_ADAPTIVE",
    "SCRATCH",
    "EXISTING_PUBLIC_BAYES",
    "NO_POSTERIOR_UPDATE",
    "FEEDBACK_SHUFFLE",
    "NO_INFORMATION_GAIN",
    "PRIVATE_ALIGNED_REFERENCE",
    "UNIFORM_RANDOM",
    "PRIVATE_ORACLE_NAVIGATOR",
)
EXACT_STATE_ARMS = {
    "EXACT_BAYES_ADAPTIVE",
    "NO_POSTERIOR_UPDATE",
    "FEEDBACK_SHUFFLE",
    "NO_INFORMATION_GAIN",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _all_mappings() -> list[dict[str, str]]:
    return [
        {token: cause for token, cause in zip(TOKENS, permutation)}
        for permutation in itertools.permutations(CAUSES)
    ]


def _expected_delta(cause: str, energy_before: float) -> dict[str, float]:
    energy_after = max(
        0.0,
        min(
            1.0,
            energy_before
            - PASSIVE_DECAY
            - INTERACT_COST
            + (CAUSE_DELTAS[cause]["energy"] if cause == "resource" else 0.0),
        ),
    )
    return {
        "energy": round(energy_after - energy_before, 12),
        "safety": round(CAUSE_DELTAS[cause]["safety"], 12),
    }


def _cause(actual_delta: Mapping[str, Any], energy_before: float) -> str | None:
    matches = []
    for cause in CAUSES:
        expected = _expected_delta(cause, energy_before)
        if all(abs(float(actual_delta[key]) - expected[key]) <= 1e-9 for key in expected):
            matches.append(cause)
    return matches[0] if len(matches) == 1 else None


def _metrics(hypotheses: list[dict[str, str]]) -> dict[str, Any]:
    count = len(hypotheses)
    marginals = {
        token: {
            cause: sum(mapping[token] == cause for mapping in hypotheses) / count
            for cause in CAUSES
        }
        for token in TOKENS
    }
    behavioral = sum(1.0 - max(row.values()) for row in marginals.values()) / len(TOKENS)
    return {
        "posterior_entropy_bits": round(math.log2(count), 12),
        "equivalent_mapping_count": count,
        "exact_alignment_bayes_error": round(1.0 - 1.0 / count, 12),
        "behavioral_alignment_bayes_error": round(behavioral, 12),
    }


def _information_gain(hypotheses: list[dict[str, str]], token: str) -> float:
    if token not in TOKENS:
        return 0.0
    before = math.log2(len(hypotheses))
    counts = [sum(mapping[token] == cause for mapping in hypotheses) for cause in CAUSES]
    after = sum(
        (count / len(hypotheses)) * math.log2(count) for count in counts if count
    )
    return round(before - after, 12)


def _private_findings(payload: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if str(key).lower() in PRIVATE_FIELDS:
                findings.append(f"private_field:{path}.{key}")
            findings.extend(_private_findings(value, f"{path}.{key}"))
    elif isinstance(payload, (list, tuple)):
        for index, value in enumerate(payload):
            findings.extend(_private_findings(value, f"{path}[{index}]"))
    return findings


def recompute_rows(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    findings: list[str] = []
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for index, row in enumerate(rows):
        grouped[(str(row["opaque_context_id"]), str(row["arm"]))].append(row)
        unhashed = {key: value for key, value in row.items() if key != "trace_hash"}
        if row.get("trace_hash") != canonical_hash(unhashed):
            findings.append(f"row_hash_mismatch:{index}")
        receipt = row.get("public_input_receipt")
        if not isinstance(receipt, Mapping) or list(receipt.keys()) != PUBLIC_FIELDS:
            # Producer insertion order is part of the public receipt contract.
            if not isinstance(receipt, Mapping) or set(receipt) != set(PUBLIC_FIELDS):
                findings.append(f"public_input_schema:{index}")
        findings.extend(f"{finding}:{index}" for finding in _private_findings(receipt))
        if row.get("public_input_hash") != canonical_hash(receipt):
            findings.append(f"public_input_hash:{index}")
    trajectories = []
    for (context, arm), values in sorted(grouped.items()):
        ordered = sorted(values, key=lambda row: int(row["sequence"]))
        hypotheses = _all_mappings()
        exact_arm = arm in EXACT_STATE_ARMS
        previous = None
        reliable_step = None
        reliable_cumulative = None
        cumulative = 0.0
        for expected_sequence, row in enumerate(ordered, start=1):
            index_label = f"{context}:{arm}:{expected_sequence}"
            if int(row["sequence"]) != expected_sequence or row.get("prev_trace_hash") != previous:
                findings.append(f"trace_chain:{index_label}")
            before = _metrics(hypotheses)
            if row.get("posterior_entropy_bits_before") is not None and abs(
                float(row["posterior_entropy_bits_before"]) - before["posterior_entropy_bits"]
            ) > 1e-9:
                findings.append(f"entropy_before:{index_label}")
            receipt = row["public_input_receipt"]
            front = str(receipt["observation"]["visual"][1][2])
            diagnostics = row.get("action_diagnostics")
            if exact_arm:
                if not isinstance(diagnostics, Mapping) or set(diagnostics) != {
                    "turn_left",
                    "turn_right",
                    "move_forward",
                    "interact",
                    "rest",
                }:
                    findings.append(f"action_diagnostics_schema:{index_label}")
                else:
                    expected_information = _information_gain(hypotheses, front)
                    if abs(
                        float(diagnostics["interact"]["information_gain_bits"])
                        - expected_information
                    ) > 1e-9:
                        findings.append(f"information_gain:{index_label}")
                    for action in ("turn_left", "turn_right", "move_forward", "rest"):
                        if abs(float(diagnostics[action]["information_gain_bits"])) > 1e-12:
                            findings.append(f"noninteract_information_gain:{index_label}:{action}")
            if (
                exact_arm
                and
                row["selected_action"] == "interact"
                and row["outcome_type"] == "interacted"
                and front in TOKENS
                and arm != "NO_POSTERIOR_UPDATE"
            ):
                token = front
                if arm == "FEEDBACK_SHUFFLE":
                    token = TOKENS[(TOKENS.index(token) + 1) % len(TOKENS)]
                cause = _cause(row["actual_delta"], float(receipt["organism"]["energy"]))
                if cause is None:
                    findings.append(f"unmatched_public_delta:{index_label}")
                else:
                    hypotheses = [mapping for mapping in hypotheses if mapping[token] == cause]
                    if not hypotheses:
                        findings.append(f"empty_posterior:{index_label}")
                        hypotheses = _all_mappings()
            after = _metrics(hypotheses)
            expected_fields = {
                "posterior_entropy_bits": after["posterior_entropy_bits"],
                "equivalent_mapping_count": after["equivalent_mapping_count"],
                "exact_alignment_bayes_error": after["exact_alignment_bayes_error"],
                "behavioral_alignment_bayes_error": after["behavioral_alignment_bayes_error"],
            }
            for field, expected in expected_fields.items():
                stored = row.get(field)
                if exact_arm:
                    if stored is None or abs(float(stored) - float(expected)) > 1e-9:
                        findings.append(f"{field}:{index_label}")
                elif stored is not None:
                    findings.append(f"unexpected_exact_metric:{field}:{index_label}")
            expected_loss = round(
                max(0.0, TARGET_LEVEL - float(row["energy_after"]))
                + max(0.0, TARGET_LEVEL - float(row["safety_after"]))
                + (0.75 if bool(row["died"]) else 0.0),
                12,
            )
            if abs(float(row["deficit_loss"]) - expected_loss) > 1e-9:
                findings.append(f"deficit_loss:{index_label}")
            cumulative += float(row["deficit_loss"])
            if (
                exact_arm
                and reliable_step is None
                and after["behavioral_alignment_bayes_error"] <= 0.05
            ):
                reliable_step = expected_sequence
                reliable_cumulative = round(cumulative, 12)
            previous = row.get("trace_hash")
        trajectories.append(
            {
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
                "final_equivalent_mapping_count": len(hypotheses) if exact_arm else None,
                "final_posterior_entropy_bits": (
                    _metrics(hypotheses)["posterior_entropy_bits"] if exact_arm else None
                ),
                "first_reliable_alignment_step": reliable_step,
                "cumulative_deficit_at_reliable_alignment": reliable_cumulative,
                "trace_chain_hash": previous,
            }
        )
    arms = {}
    for arm in ALL_ARMS:
        values = [row for row in trajectories if row["arm"] == arm]
        if not values:
            continue
        arms[arm] = {
            "world_count": len(values),
            "mean_early_deficit_auc": round(
                sum(float(row["early_deficit_auc"]) for row in values) / len(values), 12
            ),
            "mean_late_deficit_auc": round(
                sum(float(row["late_deficit_auc"]) for row in values) / len(values), 12
            ),
            "mean_total_deficit_auc": round(
                sum(float(row["total_deficit_auc"]) for row in values) / len(values), 12
            ),
        }
    target = {
        "row_count": len(rows),
        "trajectory_count": len(trajectories),
        "trajectories": trajectories,
        "arms": arms,
    }
    return {
        "schema_version": "ego.v2.public_latent_alignment.independent_recomputation.v1",
        "task_id": TASK_ID,
        **target,
        "row_recomputation_target": target,
        "findings": sorted(set(findings)),
        "passed": not findings,
    }


def _independent_summary(target: Mapping[str, Any]) -> dict[str, Any]:
    arms = target["arms"]
    scratch = float(arms["SCRATCH"]["mean_early_deficit_auc"])
    exact = float(arms["EXACT_BAYES_ADAPTIVE"]["mean_early_deficit_auc"])
    aligned = float(arms["PRIVATE_ALIGNED_REFERENCE"]["mean_early_deficit_auc"])
    gain = scratch - exact
    headroom = scratch - aligned
    recovery = gain / headroom if headroom > 1e-12 else None
    index = {
        (str(row["opaque_context_id"]), str(row["arm"])): row
        for row in target["trajectories"]
    }
    contexts = sorted(
        context for context, arm in index if arm == "EXACT_BAYES_ADAPTIVE"
    )
    paired = [
        {
            "opaque_context_id": context,
            "scratch_early_deficit_auc": index[(context, "SCRATCH")]["early_deficit_auc"],
            "exact_early_deficit_auc": index[(context, "EXACT_BAYES_ADAPTIVE")][
                "early_deficit_auc"
            ],
            "gain": round(
                float(index[(context, "SCRATCH")]["early_deficit_auc"])
                - float(index[(context, "EXACT_BAYES_ADAPTIVE")]["early_deficit_auc"]),
                12,
            ),
        }
        for context in contexts
    ]
    ablation_gains = {
        arm: round(scratch - float(arms[arm]["mean_early_deficit_auc"]), 12)
        for arm in ("NO_POSTERIOR_UPDATE", "FEEDBACK_SHUFFLE", "NO_INFORMATION_GAIN")
    }
    removal = {
        arm: (round((gain - value) / gain, 12) if gain > 1e-12 else None)
        for arm, value in ablation_gains.items()
    }
    exact_rows = [
        row for row in target["trajectories"] if row["arm"] == "EXACT_BAYES_ADAPTIVE"
    ]
    positive = sum(float(row["gain"]) > 0.0 for row in paired)
    gates = {
        "public_reference_gain_positive": gain > 0.0,
        "recovery_at_least_5pct": recovery is not None and recovery >= 0.05,
        "positive_worlds_at_least_12_of_16": positive >= 12,
        "relevant_ablation_removes_half_gain": any(
            value is not None and float(value) >= 0.50 for value in removal.values()
        ),
        "reliable_alignment_in_majority": sum(
            row["first_reliable_alignment_step"] is not None for row in exact_rows
        )
        >= 12,
    }
    reliable_steps = [
        float(row["first_reliable_alignment_step"])
        for row in exact_rows
        if row["first_reliable_alignment_step"] is not None
    ]
    reliable_costs = [
        float(row["cumulative_deficit_at_reliable_alignment"])
        for row in exact_rows
        if row["cumulative_deficit_at_reliable_alignment"] is not None
    ]
    return {
        "arms": arms,
        "public_reference_gain": round(gain, 12),
        "scratch_private_aligned_headroom": round(headroom, 12),
        "headroom_recovery_fraction": None if recovery is None else round(recovery, 12),
        "positive_world_count": positive,
        "paired_world_directions": paired,
        "ablation_gains": ablation_gains,
        "ablation_removal_fractions": removal,
        "first_reliable_alignment_step_mean": (
            round(sum(reliable_steps) / len(reliable_steps), 12) if reliable_steps else None
        ),
        "cumulative_deficit_at_reliable_alignment_mean": (
            round(sum(reliable_costs) / len(reliable_costs), 12) if reliable_costs else None
        ),
        "gates": gates,
        "passed": all(gates.values()),
    }


def _read_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _artifact_root(root: Path) -> Path:
    return Path(root).resolve() / "artifacts" / ARTIFACT_NAME


def _verify_freeze(root: Path, out: Path) -> dict[str, Any]:
    freeze = json.loads((out / "candidate_freeze.json").read_text(encoding="utf-8"))
    findings = []
    for relative, expected in freeze["source_and_packet_hashes"].items():
        path = root / relative
        if not path.is_file() or sha256(path) != expected:
            findings.append(f"freeze_hash_mismatch:{relative}")
    return {"passed": not findings, "findings": findings}


def _verify_protected_trees(root: Path, out: Path) -> dict[str, Any]:
    receipt = json.loads((out / "protected_predecessor_trees.json").read_text(encoding="utf-8"))
    findings = []
    actual = {}
    for path, expected in receipt["git_tree_oids"].items():
        try:
            oid = subprocess.check_output(
                ["git", "rev-parse", f"HEAD:{path}"], cwd=root, text=True
            ).strip()
        except subprocess.CalledProcessError:
            findings.append(f"protected_tree_missing:{path}")
            continue
        actual[path] = oid
        if oid != expected:
            findings.append(f"protected_tree_changed:{path}")
    return {"passed": not findings, "findings": findings, "actual_git_tree_oids": actual}


def verify_campaign(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    out = _artifact_root(root)
    packet_reports = {}
    all_passed = True
    first_public_row = None
    for packet in ("search_dev", "replication_dev"):
        result_path = out / f"{packet}_result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        rows_path = root / result["rows_path"]
        rows = _read_rows(rows_path)
        if first_public_row is None:
            first_public_row = deepcopy(rows[0])
        recomputed = recompute_rows(rows)
        rows_hash_match = sha256(rows_path) == result["rows_sha256"]
        target_match = (
            recomputed["row_recomputation_target"] == result["row_recomputation_target"]
        )
        summary = _independent_summary(recomputed["row_recomputation_target"])
        summary_match = summary == result["summary"]
        passed = bool(recomputed["passed"] and rows_hash_match and target_match and summary_match)
        all_passed = all_passed and passed
        packet_reports[packet] = {
            "passed": passed,
            "rows_sha256_match": rows_hash_match,
            "row_recomputation_target_match": target_match,
            "summary_match": summary_match,
            "recomputed_summary": summary,
            "recomputation_findings": recomputed["findings"],
            "row_count": recomputed["row_count"],
            "trajectory_count": recomputed["trajectory_count"],
        }
    assert first_public_row is not None
    original_fixture_report = recompute_rows([first_public_row])
    hash_tamper = deepcopy(first_public_row)
    hash_tamper["deficit_loss"] = float(hash_tamper["deficit_loss"]) + 0.01
    hash_tamper_caught = not recompute_rows([hash_tamper])["passed"]
    entropy_tamper = deepcopy(first_public_row)
    entropy_tamper["posterior_entropy_bits"] = float(
        entropy_tamper["posterior_entropy_bits"]
    ) + 0.25
    entropy_tamper["trace_hash"] = canonical_hash(
        {key: value for key, value in entropy_tamper.items() if key != "trace_hash"}
    )
    entropy_tamper_caught = not recompute_rows([entropy_tamper])["passed"]
    leakage = deepcopy(first_public_row)
    leakage["public_input_receipt"]["world_seed"] = 470003
    leakage["public_input_hash"] = canonical_hash(leakage["public_input_receipt"])
    leakage["trace_hash"] = canonical_hash(
        {key: value for key, value in leakage.items() if key != "trace_hash"}
    )
    leakage_caught = not recompute_rows([leakage])["passed"]
    packet_bytes = (out / "packet_assignments.json").read_bytes()
    packet_tamper_hash = hashlib.sha256(packet_bytes + b"tamper").hexdigest()
    commitment = json.loads((out / "packet_commitment.json").read_text(encoding="utf-8"))
    packet_tamper_caught = packet_tamper_hash != commitment["packet_assignments_sha256"]
    freeze_report = _verify_freeze(root, out)
    protected_report = _verify_protected_trees(root, out)
    positive_controls = {
        "untampered_single_row_passes": original_fixture_report["passed"],
        "row_hash_tamper_caught": hash_tamper_caught,
        "rehashed_entropy_tamper_caught": entropy_tamper_caught,
        "rehashed_private_field_leakage_caught": leakage_caught,
        "packet_assignment_tamper_caught": packet_tamper_caught,
    }
    controls_passed = all(positive_controls.values())
    verification = {
        "schema_version": "ego.v2.public_latent_alignment.verification.v1",
        "task_id": TASK_ID,
        "packet_reports": packet_reports,
        "candidate_freeze": freeze_report,
        "protected_predecessor_trees": protected_report,
        "positive_controls": positive_controls,
        "independent_verifier_imports_producer": False,
        "independent_verifier_imports_product_runtime": False,
        "passed": bool(
            all_passed and controls_passed and freeze_report["passed"] and protected_report["passed"]
        ),
    }
    _write_json(out / "independent_row_recomputation_report.json", packet_reports)
    _write_json(
        out / "leakage_tamper_report.json",
        {
            "schema_version": "ego.v2.public_latent_alignment.leakage_tamper.v1",
            "task_id": TASK_ID,
            "positive_controls": positive_controls,
            "passed": controls_passed,
        },
    )
    _write_json(out / "verification_report.json", verification)
    campaign = json.loads(
        (out / "campaign_report_preverification.json").read_text(encoding="utf-8")
    )
    stable = bool(
        verification["passed"]
        and all(
            packet_reports[packet]["recomputed_summary"]["passed"]
            for packet in packet_reports
        )
    )
    verdict = (
        "PUBLIC_LATENT_ALIGNMENT_LEARNER_IMPLEMENTATION_GAP"
        if stable
        else "PUBLIC_LATENT_ALIGNMENT_NOT_IDENTIFIABLE_OR_NOT_ECONOMIC_UNDER_CURRENT_GRAMMAR"
    )
    campaign["independent_verification_passed"] = verification["passed"]
    campaign["stable_public_headroom"] = stable
    campaign["verdict"] = verdict
    campaign.pop("verdict_before_independent_verification", None)
    _write_json(out / "campaign_report.json", campaign)
    _write_json(
        out / "qualification_status.json",
        {
            "schema_version": "ego.v2.public_latent_alignment.qualification_status.v1",
            "task_id": TASK_ID,
            "qualification_split_exists": False,
            "qualification_consumed": False,
            "original_001j_heldout_consumed": False,
            "verdict": verdict,
        },
    )
    return verification


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    report = verify_campaign(args.root)
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["passed"] else 1


__all__ = ["canonical_hash", "recompute_rows", "sha256", "verify_campaign"]


if __name__ == "__main__":
    raise SystemExit(main())
