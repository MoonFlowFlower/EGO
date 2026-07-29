from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import uuid
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Any


TASK_ID = "EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-HOSTILE-COUNTEREXAMPLE-001D-X1"
REPO = Path(__file__).resolve().parents[2]
I1_PATH = REPO / "scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py"
INDEPENDENT_PATH = REPO / "scripts/codex/recompute_ego_v2_active_transfer_headroom_hostile_counterexample_001d_x1.py"
TEST_PATH = REPO / "scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_hostile_counterexample_001d_x1.py"

PRIMARY_ARM = "ARM_I_TRANSFER__A_L1_EVSI__D_LCB05_FALLBACK"
RAW_ARM = "ARM_I_TRANSFER__A_L1_EVSI__D_L1_MEDIAN"
PUBLIC_ARM = "ARM_I_SCRATCH__A_L1_EVSI__D_SCRATCH_L1"
ARM_ORDER = (PRIMARY_ARM, RAW_ARM, PUBLIC_ARM)

VERDICT_FALSIFIED = "FROZEN_PRIMARY_POSITIVE_GATE_FALSIFIED_BY_COUNTEREXAMPLE"
VERDICT_SURVIVES = "HASH00_CONSERVATIVE_GATE_SURVIVES_X1"
VERDICT_BLOCKED = "BLOCKED_X1_PROVENANCE_OR_RECOMPUTATION"

CLAIM_CEILING = (
    "Exact counterexample evidence for the frozen 001D conservative positive gate "
    "on HASH_00 under lexical midpoint only; no complete 001D verdict, learned "
    "representation, neural emergence, product effect, held-out adaptation, AGI, "
    "agency, consciousness, subjectivity, emotion, companion readiness, or electronic life."
)

EXPECTED_AUTHORITY = {
    "docs/codex/tasks/EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-001D.md": "c9a7d71dcd92b0bc4571a4e5aa975e04fc97485d47b23b826894f13cac96072e",
    "docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/FROZEN_DESIGN.json": "f54b998bf952f662b92f4734517cdb1405b63a4f75258eb6c5de917174970916",
    "docs/codex/tasks/EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-IMPLEMENTATION-001D-I1.md": "5aefb07fde2dee95ba714796ab55fe57e894e24114ee03e8d16efbb224b23bd3",
    "scripts/codex/check_ego_v2_active_transfer_headroom_preflight_001d.py": "abb91bcccd218c38b100059fccc54235b1d46bee55e8389ce502a40454ea6a6f",
    "scripts/codex/tests/test_check_ego_v2_active_transfer_headroom_preflight_001d.py": "09c163707a6e45af2acaad849a01fb24b677d5a06ece26cde1179da3b470575a",
    "docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/I1_TDD_REPORT.md": "8afc438093b7be571013d8d8bb3dfa4475ed00933566631de8fd8c5d474ac043",
    "docs/codex/tasks/EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-001D-I2-PRE-RUN-PROVENANCE.md": "1eba3c14fc9e3f6f9e7220061068f25f6a984f8a2b80ecbc2b1a61a15ad89de2",
    "docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/I2_COLLISION_RECORD.md": "cc374789f46f9cf44a3b570902bab856e48deb66f11af0ba80c1e56cce9bb946",
    "docs/codex/tasks/EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-HOSTILE-COUNTEREXAMPLE-001D-X1.md": "56da5cc36ba53d0a33dfdf09a12df8440a0f19325f5e527b94b9d6414be1a390",
    "docs/codex/tasks/ego-v2-p1-active-transfer-headroom-preflight-001d/X1_COLLISION_RECORD.md": "074d915a8305b75c526fedf6412f20d425fdfd6334485c1b199cd369f4f7c724",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha256_path(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def validate_authority() -> list[dict[str, Any]]:
    receipts = []
    for relative, expected in sorted(EXPECTED_AUTHORITY.items()):
        path = REPO / relative
        if not path.is_file():
            raise ValueError(f"missing authority path: {relative}")
        actual = _sha256_path(path)
        row = {
            "path": relative,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "matches_expected": actual == expected,
        }
        receipts.append(row)
        if actual != expected:
            raise ValueError(f"authority hash drift: {relative}")
    return receipts


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def load_i1_verified():
    validate_authority()
    module = _load_module(I1_PATH, "ego_x1_pinned_i1")
    module.validate_authority_hashes()
    return module


@lru_cache(maxsize=1)
def _load_independent():
    module = _load_module(INDEPENDENT_PATH, "ego_x1_independent_runtime")
    if module.TASK_ID != TASK_ID:
        raise ValueError("independent task id drift")
    return module


def _fraction(value: dict[str, int]) -> Fraction:
    if type(value) is not dict or set(value) != {"n", "d"}:
        raise ValueError("rational shape drift")
    return Fraction(value["n"], value["d"])


def _rational(value: Fraction | int) -> dict[str, int]:
    fraction = value if isinstance(value, Fraction) else Fraction(value, 1)
    return {"n": fraction.numerator, "d": fraction.denominator}


def _metric_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "arm_id": row["arm_id"],
        "target_mapping": row["target_mapping"],
        "selected_query_token": row["selected_query_token"],
        "public_selected_query_token": row["public_selected_query_token"],
        "candidate_prediction_micro": row["prediction_decision"]["prediction_micro"],
        "public_prediction_micro": row["public_prediction_decision"]["prediction_micro"],
        "same_history_scratch_prediction_micro": row["same_history_scratch_prediction_decision"]["prediction_micro"],
        "used_transfer": row["used_transfer"],
        "lcb05_benefit_micro": row["prediction_decision"]["lcb05_benefit_micro"],
        "candidate_token_losses_raw": row["candidate_token_losses_raw"],
        "baseline_token_losses_raw": row["baseline_token_losses_raw"],
        "same_history_scratch_token_losses_raw": row["same_history_scratch_token_losses_raw"],
        "full_improvement_raw": row["full_improvement_raw"],
        "common_raw": row["common_raw"],
        "query_asymmetry_raw": row["query_asymmetry_raw"],
        "same_history_forward_raw": row["same_history_forward_raw"],
        "metric_denominators": row["metric_denominators"],
        "metric_rationals": row["metric_rationals"],
    }


def _thresholds(i1) -> dict[str, dict[str, int]]:
    source = i1.load_frozen_design()["thresholds"]
    keys = (
        "member_full_improvement_min",
        "member_common_forward_min",
        "member_same_history_forward_min",
        "canonical_member_common_forward_min",
        "canonical_member_same_history_forward_min",
        "nonmember_bounded_full_regret_max",
        "nonmember_strict_full_regret_max",
    )
    return {key: _rational(Fraction(source[key])) for key in keys}


def _aggregate_arm(
    bank: tuple[tuple[int, ...], ...],
    rows: list[dict[str, Any]],
    arm_id: str,
    thresholds: dict[str, dict[str, int]],
) -> dict[str, Any]:
    arm_rows = [row for row in rows if row["arm_id"] == arm_id]
    if len(arm_rows) != 120:
        raise ValueError("arm row coverage drift")
    by_target = {tuple(row["target_mapping"]): row for row in arm_rows}
    support = tuple(sorted(set(bank)))
    member_rows = []
    for target in support:
        metric = by_target[target]["metric"]
        full = _fraction(metric["metric_rationals"]["full_endpoint_improvement"])
        common = _fraction(metric["metric_rationals"]["common_unqueried_forward_improvement"])
        same = _fraction(metric["metric_rationals"]["same_history_forward_improvement"])
        passed = (
            full >= _fraction(thresholds["member_full_improvement_min"])
            and common >= _fraction(thresholds["member_common_forward_min"])
            and same >= _fraction(thresholds["member_same_history_forward_min"])
        )
        member_rows.append({
            "target_mapping": list(target),
            "full_improvement": _rational(full),
            "common_improvement": _rational(common),
            "same_history_improvement": _rational(same),
            "passes": passed,
        })
    canonical = support[0]
    canonical_row = next(row for row in member_rows if tuple(row["target_mapping"]) == canonical)
    canonical_pass = (
        _fraction(canonical_row["common_improvement"]) >= _fraction(thresholds["canonical_member_common_forward_min"])
        and _fraction(canonical_row["same_history_improvement"]) >= _fraction(thresholds["canonical_member_same_history_forward_min"])
    )
    nonmembers = [row for row in arm_rows if row["classification"]["distance"] > 0]
    worst = min(
        nonmembers,
        key=lambda row: _fraction(row["metric"]["metric_rationals"]["full_endpoint_improvement"]),
    )
    worst_improvement = _fraction(worst["metric"]["metric_rationals"]["full_endpoint_improvement"])
    bounded = all(
        -_fraction(row["metric"]["metric_rationals"]["full_endpoint_improvement"])
        <= _fraction(thresholds["nonmember_bounded_full_regret_max"])
        for row in nonmembers
    )
    strict = all(
        -_fraction(row["metric"]["metric_rationals"]["full_endpoint_improvement"])
        <= _fraction(thresholds["nonmember_strict_full_regret_max"])
        for row in nonmembers
    )
    return {
        "arm_id": arm_id,
        "canonical_member": list(canonical),
        "member_rows": member_rows,
        "all_distinct_members_pass": all(row["passes"] for row in member_rows),
        "canonical_member_passes": canonical_pass,
        "member_and_forward": all(row["passes"] for row in member_rows) and canonical_pass,
        "bounded_safety": bounded,
        "strict_safety": strict,
        "worst_nonmember": {
            "target_mapping": worst["target_mapping"],
            "classification": worst["classification"],
            "full_improvement": _rational(worst_improvement),
            "regret": _rational(-worst_improvement),
        },
    }


@lru_cache(maxsize=1)
def _build_primary_cached() -> dict[str, Any]:
    i1 = load_i1_verified()
    bank = i1.build_hash_bank(0)
    targets = i1.mapping_space()
    thresholds = _thresholds(i1)
    rows = []
    for arm_id in ARM_ORDER:
        for target in targets:
            metric = i1.validate_arm_target_metric(
                i1.evaluate_target(
                    bank,
                    target,
                    arm_id,
                    median_convention="midpoint_integer",
                    query_policy=None,
                )
            )
            classification = i1.classify_target(bank, target)
            rows.append({
                "arm_id": arm_id,
                "target_mapping": list(target),
                "classification": classification,
                "metric": _metric_projection(metric),
            })
    if len(rows) != 360:
        raise ValueError("exact 360 X1 rows required")
    aggregate = {
        "schema_version": "X1_GATE_AGGREGATE_V1",
        "bank_role_id": "HASH_00",
        "median_convention": "midpoint_integer",
        "query_tie_rule": "lexical_minimum",
        "target_count": 120,
        "row_count": 360,
        "conservative": _aggregate_arm(bank, rows, PRIMARY_ARM, thresholds),
        "raw": _aggregate_arm(bank, rows, RAW_ARM, thresholds),
        "public": _aggregate_arm(bank, rows, PUBLIC_ARM, thresholds),
    }
    payload = {
        "schema_version": "X1_PRIMARY_EVIDENCE_V1",
        "task_id": TASK_ID,
        "bank": [list(row) for row in bank],
        "bank_sha256": sha256(i1.canonical_bank_bytes(bank)).hexdigest(),
        "thresholds": thresholds,
        "rows": rows,
        "aggregate": aggregate,
    }
    payload["payload_sha256"] = sha256(canonical_bytes(payload)).hexdigest()
    return payload


def build_primary_evidence() -> dict[str, Any]:
    return deepcopy(_build_primary_cached())


def _comparison_projection(payload: dict[str, Any]) -> dict[str, Any]:
    required = {"bank", "bank_sha256", "thresholds", "rows", "aggregate"}
    if not required <= set(payload):
        raise ValueError("independent evidence mismatch: missing projection fields")
    return {key: payload[key] for key in sorted(required)}


def compare_evidence(primary: dict[str, Any], independent: dict[str, Any]) -> dict[str, Any]:
    left = _comparison_projection(primary)
    right = _comparison_projection(independent)
    if canonical_bytes(left) == canonical_bytes(right):
        return {
            "schema_version": "X1_INDEPENDENT_COMPARISON_V1",
            "passed": True,
            "row_count": len(left["rows"]),
            "first_mismatch": None,
            "primary_projection_sha256": sha256(canonical_bytes(left)).hexdigest(),
            "independent_projection_sha256": sha256(canonical_bytes(right)).hexdigest(),
        }
    mismatch = None
    if canonical_bytes(left["bank"]) != canonical_bytes(right["bank"]):
        mismatch = "bank"
    elif canonical_bytes(left["thresholds"]) != canonical_bytes(right["thresholds"]):
        mismatch = "thresholds"
    else:
        for index, (lrow, rrow) in enumerate(zip(left["rows"], right["rows"])):
            if canonical_bytes(lrow) != canonical_bytes(rrow):
                mismatch = f"row:{index}"
                break
        if mismatch is None and len(left["rows"]) != len(right["rows"]):
            mismatch = "row_count"
        if mismatch is None:
            mismatch = "aggregate"
    raise ValueError(f"independent evidence mismatch: {mismatch}")


def dispatch_verdict(aggregate: dict[str, Any], comparison: dict[str, Any]) -> str:
    if not comparison.get("passed"):
        return VERDICT_BLOCKED
    conservative = aggregate["conservative"]
    if conservative["member_and_forward"] and conservative["bounded_safety"]:
        return VERDICT_SURVIVES
    return VERDICT_FALSIFIED


def _runtime_receipt() -> dict[str, Any]:
    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "isolated": bool(sys.flags.isolated),
        "no_user_site": bool(sys.flags.no_user_site),
        "hash_algorithm": "sha256",
        "numeric_policy": "fractions.Fraction and unbounded Python integers",
    }


def _code_receipts() -> list[dict[str, Any]]:
    paths = [Path(__file__).resolve(), INDEPENDENT_PATH, TEST_PATH]
    return [
        {
            "path": path.relative_to(REPO).as_posix(),
            "sha256": _sha256_path(path),
            "bytes": path.stat().st_size,
        }
        for path in paths
    ]


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_bytes(value) + b"\n")


def _fresh_bundle() -> dict[str, Any]:
    primary = build_primary_evidence()
    independent = _load_independent().build_independent_evidence()
    comparison = compare_evidence(primary, independent)
    return {"primary": primary, "independent": independent, "comparison": comparison}


def _spawn_fresh_bundle(target: Path) -> None:
    nonce = uuid.uuid4().hex
    environment = dict(os.environ)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["EGO_X1_INTERNAL_NONCE"] = nonce
    command = [
        sys.executable,
        "-I",
        "-B",
        str(Path(__file__).resolve()),
        "--internal-payload",
        str(target),
        "--internal-nonce",
        nonce,
    ]
    completed = subprocess.run(
        command,
        cwd=REPO,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if completed.returncode != 0:
        raise ValueError(f"fresh process failed: {completed.stderr.strip()}")
    if not target.is_file():
        raise ValueError("fresh process payload missing")


def _manifest_for(directory: Path) -> dict[str, Any]:
    files = {}
    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "artifact_manifest.json":
            files[path.name] = {"sha256": _sha256_path(path), "bytes": path.stat().st_size}
    return {
        "schema_version": "X1_ARTIFACT_MANIFEST_V1",
        "task_id": TASK_ID,
        "files": files,
        "artifact_set_sha256": sha256(canonical_bytes(files)).hexdigest(),
    }


def _write_packet(directory: Path, bundle: dict[str, Any], replay: dict[str, Any]) -> dict[str, Any]:
    primary = bundle["primary"]
    independent = bundle["independent"]
    comparison = bundle["comparison"]
    verdict = dispatch_verdict(primary["aggregate"], comparison)
    positive_ruled_out = verdict == VERDICT_FALSIFIED
    result = {
        "schema_version": "X1_RESULT_V1",
        "task_id": TASK_ID,
        "verdict": verdict,
        "status": "complete" if comparison["passed"] else "blocked",
        "bank_role_id": "HASH_00",
        "bank_sha256": primary["bank_sha256"],
        "median_convention": "midpoint_integer",
        "query_tie_rule": "lexical_minimum",
        "target_count": 120,
        "row_count": 360,
        "positive_branch_ruled_out": positive_ruled_out,
        "conservative_member_and_forward": primary["aggregate"]["conservative"]["member_and_forward"],
        "conservative_bounded_safety": primary["aggregate"]["conservative"]["bounded_safety"],
        "raw_member_and_forward": primary["aggregate"]["raw"]["member_and_forward"],
        "raw_bounded_safety": primary["aggregate"]["raw"]["bounded_safety"],
        "independent_recompute_equal": comparison["passed"],
        "fresh_process_replay_equal": replay["equal"],
        "fresh_effect_worlds_or_seeds_consumed": False,
        "complete_001d_verdict_adjudicated": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_json(directory / "result.json", result)
    with (directory / "trace.jsonl").open("wb") as handle:
        for row in primary["rows"]:
            handle.write(canonical_bytes(row) + b"\n")
    _write_json(directory / "baseline_comparison.json", {
        "schema_version": "X1_BASELINE_COMPARISON_V1",
        "task_id": TASK_ID,
        "baseline_arm_id": PUBLIC_ARM,
        "candidate_arm_id": PRIMARY_ARM,
        "raw_arm_id": RAW_ARM,
        "thresholds": primary["thresholds"],
        "aggregate": primary["aggregate"],
        "aggregation_rule": "exact pointwise member thresholds and universal nonmember regret over all 120 HASH_00 targets",
    })
    _write_json(directory / "ablation_report.json", {
        "schema_version": "X1_ABLATION_REPORT_V1",
        "task_id": TASK_ID,
        "contrast": "D_LCB05_FALLBACK versus D_L1_MEDIAN with identical I_TRANSFER and A_L1_EVSI",
        "conservative": primary["aggregate"]["conservative"],
        "raw": primary["aggregate"]["raw"],
        "full_13_ablation_suite_run": False,
        "causal_attribution_claim_allowed": False,
        "reason": "one universal-gate counterexample is sufficient to rule out the positive branch; full 001D attribution was not executed",
    })
    _write_json(directory / "replay_report.json", replay)
    _write_json(directory / "independent_recompute_report.json", comparison | {
        "schema_version": "X1_INDEPENDENT_RECOMPUTE_REPORT_V1",
        "independence_boundary": "separate standard-library code path, same Codex/model lineage, not external independent audit",
        "independent_payload_sha256": independent["payload_sha256"],
    })
    _write_json(directory / "input_manifest.json", {
        "schema_version": "X1_INPUT_MANIFEST_V1",
        "task_id": TASK_ID,
        "authority_receipts": validate_authority(),
        "code_receipts": _code_receipts(),
        "runtime_receipt": _runtime_receipt(),
        "inputs": ["frozen 001D design bytes", "derived HASH_00", "all 120 target permutations"],
        "forbidden_inputs_used": [],
    })
    if verdict != VERDICT_SURVIVES:
        _write_json(directory / "failure_manifest.json", {
            "schema_version": "X1_FAILURE_MANIFEST_V1",
            "task_id": TASK_ID,
            "verdict": verdict,
            "failures": [
                "conservative_member_and_forward_failed" if not result["conservative_member_and_forward"] else None,
                "conservative_bounded_safety_failed" if not result["conservative_bounded_safety"] else None,
            ],
            "allowed_next_action": "freeze the frozen 001D conservative candidate and redesign under a separate task",
            "forbidden_next_actions": ["full I2 packet as a rescue", "neural/product implementation under the failed frozen candidate", "threshold retuning"],
            "claim_ceiling": CLAIM_CEILING,
        })
    (directory / "claim_ceiling.txt").write_text(CLAIM_CEILING + "\n", encoding="utf-8", newline="\n")
    _write_json(directory / "artifact_manifest.json", _manifest_for(directory))
    return result


def verify_artifact_packet(directory: Path | str) -> dict[str, Any]:
    directory = Path(directory)
    manifest_path = directory / "artifact_manifest.json"
    if not manifest_path.is_file():
        raise ValueError("artifact manifest missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    observed = _manifest_for(directory)
    if canonical_bytes(manifest) != canonical_bytes(observed):
        raise ValueError("artifact manifest mismatch")
    result = json.loads((directory / "result.json").read_text(encoding="utf-8"))
    if result["task_id"] != TASK_ID or result["row_count"] != 360:
        raise ValueError("result contract mismatch")
    lines = (directory / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    if len(lines) != 360:
        raise ValueError("trace row count mismatch")
    return result


def run_formal(output_dir: Path | str) -> dict[str, Any]:
    output = Path(output_dir).resolve()
    if output.exists():
        raise ValueError("output directory must be absent")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / f".{output.name}.staging-{uuid.uuid4().hex}"
    fresh_path = output.parent / f".{output.name}.fresh-{uuid.uuid4().hex}.json"
    if staging.exists() or fresh_path.exists():
        raise ValueError("temporary output collision")
    staging.mkdir()
    try:
        bundle = _fresh_bundle()
        _spawn_fresh_bundle(fresh_path)
        fresh = json.loads(fresh_path.read_text(encoding="utf-8"))
        replay_equal = canonical_bytes(bundle) == canonical_bytes(fresh)
        if not replay_equal:
            raise ValueError("fresh process replay mismatch")
        replay = {
            "schema_version": "X1_REPLAY_REPORT_V1",
            "task_id": TASK_ID,
            "equal": replay_equal,
            "comparison_mode": "fresh isolated process recomputed before parent read",
            "primary_bundle_sha256": sha256(canonical_bytes(bundle)).hexdigest(),
            "fresh_bundle_sha256": sha256(canonical_bytes(fresh)).hexdigest(),
            "stored_result_used_as_input": False,
        }
        result = _write_packet(staging, bundle, replay)
        verify_artifact_packet(staging)
        staging.rename(output)
        verify_artifact_packet(output)
        return result
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        fresh_path.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--internal-payload", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--internal-nonce", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.internal_payload is not None:
        if args.output_dir is not None:
            raise ValueError("internal and formal output are mutually exclusive")
        expected_nonce = os.environ.get("EGO_X1_INTERNAL_NONCE")
        if not expected_nonce or args.internal_nonce != expected_nonce:
            raise ValueError("internal nonce mismatch")
        if args.internal_payload.exists():
            raise ValueError("internal payload path must be absent")
        args.internal_payload.write_bytes(canonical_bytes(_fresh_bundle()) + b"\n")
        return 0
    if args.internal_nonce is not None:
        raise ValueError("orphan internal nonce")
    if args.output_dir is None:
        raise ValueError("--output-dir is required")
    result = run_formal(args.output_dir)
    print(json.dumps({"task_id": TASK_ID, "verdict": result["verdict"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
