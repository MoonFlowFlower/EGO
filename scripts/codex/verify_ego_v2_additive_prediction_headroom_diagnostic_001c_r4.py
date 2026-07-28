#!/usr/bin/env python3
"""Banked development prediction-difference diagnostic for the frozen R2 build."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sqlite3
import statistics
import subprocess
import sys
import tempfile
from typing import Any, Callable, Iterable, Mapping
import zipfile

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "EGO-V2-P1-ADDITIVE-PREDICTION-HEADROOM-DIAGNOSTIC-001C-R4"
SOURCE_TASK_ID = "EGO-V2-P1-HIERARCHICAL-OUTCOME-DELTA-REPAIR-001C-R2"
SOURCE_PACKET = REPO_ROOT / "artifacts" / SOURCE_TASK_ID
CANONICAL_OUTPUT_DIR = REPO_ROOT / "artifacts" / TASK_ID
R4_CONTRACT_PATHS = (
    "docs/codex/tasks/EGO-V2-P1-ADDITIVE-PREDICTION-HEADROOM-DIAGNOSTIC-001C-R4.md",
    "docs/codex/tasks/ego-v2-p1-additive-prediction-headroom-diagnostic-001c-r4/COLLISION_RECORD.md",
    "scripts/codex/verify_ego_v2_additive_prediction_headroom_diagnostic_001c_r4.py",
    "scripts/codex/tests/test_verify_ego_v2_additive_prediction_headroom_diagnostic_001c_r4.py",
)
FROZEN_SOURCE_COMMIT = "363f6d49cbd54524ce283e7580e23c45ada4b532"
FROZEN_EVALUATOR_BLOBS = {
    "scripts/codex/verify_ego_v2_hierarchical_outcome_delta_repair_001c_r2.py": (
        "427f4453b682299774af45813f86645ba4ea0e93"
    ),
    "scripts/codex/verify_ego_v2_factored_predictive_control_boundary_gate_001c.py": (
        "d336be083e20c3fbf8586201397e8fb51a974a57"
    ),
}
R3_PROVENANCE_PACKET = REPO_ROOT / "artifacts" / (
    "EGO-V2-P1-ADDITIVE-PLANNER-BOUNDARY-001C-R3"
)
R3_TESTED_BUNDLE = R3_PROVENANCE_PACKET / "tested_implementation_bundle.zip"
R3_TESTED_BUNDLE_SHA256 = (
    "947f66d9bbc91e753d1f073b8c2b372b6e683c8ea814aeb9c995143a48c1104b"
)
R3_REVERSE_DELTA = R3_PROVENANCE_PACKET / "tested_tracked_diff.patch"
R3_REVERSE_DELTA_SHA256 = (
    "0fc421734dd183ea0281f4e7ed5722e9db0a488364c7b4058ebfaf475401d550"
)
R3_BOUNDARY_HELPER_SHA256 = (
    "b6e3ec342580821a0f43053f6c9baf96540ec6f8ae5c2239f99c8d56233bb321"
)
RECONSTRUCTED_RUNTIME_SHA256 = {
    "engine.py": "54190c093a0e0797bbc690c899231ad6b178092ecd4741ce10a925a2ccfe55e5",
    "microworld.py": "d87ba9530d32d2b504c75a132ae1163dfe8e8cd0a8879e6cbdd09807a9daa923",
    "claims.py": "0a72951078ab61ebf61414c73b41ff4ad13ad1a587477a4cbda81b09a38049c8",
    "predictive_control.py": "938a4715726d0dacfe0262e2fbd3edae050d22d26e50710935853e36def82edd",
    "survival_learning.py": "6b57a7a0712f178710662b6de33a6f8fdb4edf2af331bc790d939944576ca603",
    "store.py": "3e399471c89ec5046ae3bffe1de3419e61f8b1e0f8d3bb55d216ef6578616b84",
}
R2_RUNTIME_CODE_PATH_HASH = (
    "b6eadf0c8ba7244ea08cd67eb936438fda182f43e56c65918bde8264fd5b9d29"
)
FROZEN_PYTHON_VERSION = "3.13.7"
FROZEN_NUMPY_VERSION = "2.2.6"
FROZEN_INPUTS = {
    "smoke_result.json": "846981624e5dd74cd784f3531aa6c85375902c5b3094cfb2905ff8631e4c084a",
    "smoke_p0_cross_v1.sqlite3": "62ab24d298f0196c7dd752ea124319fdff17539e9cf51d0287a3ea8f97078354",
    "smoke_p2_vertical_v1.sqlite3": "d57476cad0e72054e1d8e215f7b05399e0e3a2c474365a1c3457ac5c52b81dc4",
    "result.json": "53e70f8fe8384c38fe65c953e4bb88fe9bc1bb6e2d91486147b91bc9c7379945",
}
ALLOWED_WORLD_SEEDS = frozenset({52, 54})
ALLOWED_POLICY_SEEDS = frozenset({711})
FORBIDDEN_WORLD_SEEDS = frozenset(range(60, 66))
FORBIDDEN_POLICY_SEEDS = frozenset({721, 722})
CONTEXTS = (
    ("p0_cross_v1", 52, 711),
    ("p2_vertical_v1", 54, 711),
)
STATE_KEYS = ("energy", "safety", "connection", "stimulation")
OUTCOMES = ("moved", "blocked", "interacted", "no_object", "rested", "turned")
ACTIONS = ("turn_left", "turn_right", "move_forward", "interact", "rest")
LEAKAGE_POSITIVE_CONTROL_FIELDS = frozenset(
    {"global_position", "cause", "token_mapping", "seed", "future_observation"}
)
REALIZABLE_STRATA = (
    ("move_forward", "moved"),
    ("move_forward", "blocked"),
    ("interact", "interacted"),
    ("interact", "no_object"),
    ("rest", "rested"),
    ("turn_left", "turned"),
    ("turn_right", "turned"),
)
MIN_STRATUM_SUPPORT = 16
CLAIM_CEILING = (
    "Outcome-stratified one-step prediction difference or failure on banked R2 "
    "worlds 52/54 with policy seed 711 relative to the old frozen controls only."
)
POSITIVE_VERDICT = (
    "ADDITIVE_DEVELOPMENT_PREDICTION_DIFFERENCE_UNDER_FROZEN_R2_CONTROLS"
)
NO_PREDICTION_DIFFERENCE_VERDICT = "ADDITIVE_NO_DEVELOPMENT_PREDICTION_DIFFERENCE"
INSUFFICIENT_VERDICT = "INSUFFICIENT_OUTCOME_SUPPORT"
BLOCKED_VERDICT = "BLOCKED_PROVENANCE_OR_RECOMPUTATION"
VALIDITY_CHECKS = frozenset(
    {
        "all_five_action_counts_exactly_equal",
        "no_snapshot_action_context_unused",
        "forced_action_truth_exists_for_every_balanced_row",
        "leakage_clean_and_all_positive_controls_detected",
        "fresh_subprocess_balanced_recompute_exact",
        "two_frozen_update_controls_pass",
    }
)
SUPPORT_CHECKS = frozenset(
    {
        "training_support_at_least_16_per_declared_stratum",
        "shared_base_feature_rank_is_full_for_every_action",
        "all_effect_strata_have_at_least_16_rows_per_phase",
    }
)
PREDICTION_CHECKS = frozenset(
    {
        "learned_late_brier_improves_by_at_least_0_02",
        "learned_late_nll_improves_by_at_least_0_05",
        "learned_late_brier_below_no_update_late",
        "learned_late_nll_below_no_update_late",
        "learned_late_macro_delta_mae_below_early",
        "learned_late_macro_delta_mae_below_no_update_late",
        "learned_late_macro_delta_mae_below_legacy_unconditional",
        "interact_strata_not_worse_than_no_update",
        "interact_strata_not_worse_than_legacy_unconditional",
        "base_only_ablation_changes_late_macro_delta",
        "residual_only_ablation_changes_late_macro_delta",
        "outcome_rotation_changes_late_macro_delta",
    }
)
EXPECTED_FROZEN_CHECKS = VALIDITY_CHECKS | SUPPORT_CHECKS | PREDICTION_CHECKS
SUCCESS_ARTIFACT_FILES = frozenset(
    {
        "ablation_report.json",
        "balanced_prediction_report.json",
        "baseline_comparison.json",
        "claim_ceiling.txt",
        "failure_manifest.json",
        "input_manifest.json",
        "leakage_report.json",
        "replay_report.json",
        "result.json",
        "trace.jsonl",
        "training_rows.jsonl",
    }
)
BLOCKED_ARTIFACT_FILES = frozenset(
    {"claim_ceiling.txt", "failure_manifest.json", "result.json"}
)


class HeadroomDiagnosticError(RuntimeError):
    """Fail-closed error for frozen-source or packet drift."""


class OutputTargetRefusal(HeadroomDiagnosticError):
    """No-write refusal for a wrong or already-populated artifact path."""


def provenance_receipt(
    component: str,
    aggregation_rule: str,
    code_path_hash: str,
    *,
    inputs: list[Any],
) -> dict[str, Any]:
    return {
        "producer_function": (
            "verify_ego_v2_additive_prediction_headroom_diagnostic_001c_r4."
            f"{component}"
        ),
        "input_artifacts": inputs,
        "run_id": f"{TASK_ID}:{component}",
        "seed": [711],
        "context_ids": [
            f"{layout}:world={world}:policy={policy}"
            for layout, world, policy in CONTEXTS
        ],
        "life_ids": [1, 4],
        "action_ids": [
            "turn_left",
            "turn_right",
            "move_forward",
            "interact",
            "rest",
        ],
        "aggregation_rule": aggregation_rule,
        "code_path_hash": code_path_hash,
    }


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_file_hash(path: Path, expected: str) -> dict[str, Any]:
    if not path.is_file():
        raise HeadroomDiagnosticError(f"frozen input is absent: {path}")
    actual = hash_file(path)
    if actual != expected:
        raise HeadroomDiagnosticError(f"frozen input SHA-256 drifted: {path}")
    return {"path": str(path), "sha256": actual, "bytes": path.stat().st_size}


def collect_contract_manifest(*, require_clean: bool) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    for relative in R4_CONTRACT_PATHS:
        path = REPO_ROOT / relative
        if not path.is_file():
            raise HeadroomDiagnosticError(f"R4 contract file is absent: {relative}")
        files[relative] = {
            "sha256": hash_file(path),
            "bytes": path.stat().st_size,
        }
    if require_clean:
        if (
            sys.version.split()[0] != FROZEN_PYTHON_VERSION
            or np.__version__ != FROZEN_NUMPY_VERSION
        ):
            raise HeadroomDiagnosticError("R4 frozen numeric runtime drifted")
        for relative in R4_CONTRACT_PATHS:
            try:
                _git("ls-files", "--error-unmatch", "--", relative)
            except subprocess.CalledProcessError as exc:
                raise HeadroomDiagnosticError(
                    f"R4 contract file is not frozen in Git: {relative}"
                ) from exc
        dirty = str(_git("status", "--porcelain", "--", *R4_CONTRACT_PATHS))
        if dirty:
            raise HeadroomDiagnosticError("R4 contract files have pre-run drift")
    return {
        "schema_version": "ego.v2.r4_pre_run_contract_manifest.v1",
        "head": str(_git("rev-parse", "HEAD")),
        "branch": str(_git("branch", "--show-current")),
        "files": files,
        "runtime": {
            "python_version": sys.version.split()[0],
            "numpy_version": np.__version__,
            "numpy_dtype": np.dtype(np.float64).str,
        },
        "clean_and_tracked_required": require_clean,
    }


def _git(*args: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=not binary,
    )
    return completed.stdout if binary else completed.stdout.strip()


def verify_source_pins() -> dict[str, Any]:
    commit_type = _git("cat-file", "-t", FROZEN_SOURCE_COMMIT)
    if commit_type != "commit":
        raise HeadroomDiagnosticError("frozen source authority is not a commit")
    blobs: dict[str, str] = {}
    for path, expected in FROZEN_EVALUATOR_BLOBS.items():
        actual = str(_git("rev-parse", f"{FROZEN_SOURCE_COMMIT}:{path}"))
        if actual != expected:
            raise HeadroomDiagnosticError(f"frozen source blob drifted: {path}")
        blobs[path] = actual
    bundle = verify_file_hash(R3_TESTED_BUNDLE, R3_TESTED_BUNDLE_SHA256)
    reverse_delta = verify_file_hash(R3_REVERSE_DELTA, R3_REVERSE_DELTA_SHA256)
    with zipfile.ZipFile(R3_TESTED_BUNDLE) as archive:
        try:
            manifest = json.loads(archive.read("TESTED_BUNDLE_MANIFEST.json"))
        except (KeyError, json.JSONDecodeError) as exc:
            raise HeadroomDiagnosticError("R3 tested-bundle manifest is invalid") from exc
        expected_entries = set(manifest.get("files", {})) | {
            "TESTED_BUNDLE_MANIFEST.json"
        }
        actual_entries = {item.filename for item in archive.infolist() if not item.is_dir()}
        if actual_entries != expected_entries:
            raise HeadroomDiagnosticError("R3 tested-bundle entry manifest drifted")
        for relative, receipt in manifest.get("files", {}).items():
            pure = Path(relative)
            if pure.is_absolute() or ".." in pure.parts:
                raise HeadroomDiagnosticError("R3 tested-bundle contains an unsafe path")
            data = archive.read(relative)
            if len(data) != int(receipt["bytes"]) or hashlib.sha256(data).hexdigest() != str(
                receipt["sha256"]
            ):
                raise HeadroomDiagnosticError(
                    f"R3 tested-bundle member drifted: {relative}"
                )
        if (
            manifest.get("task_id")
            != "EGO-V2-P1-ADDITIVE-PLANNER-BOUNDARY-001C-R3"
            or manifest.get("base_head") != FROZEN_SOURCE_COMMIT
            or manifest.get("numeric_backend")
            != {"id": "numpy", "version": FROZEN_NUMPY_VERSION}
        ):
            raise HeadroomDiagnosticError("R3 tested-bundle authority drifted")
    return {
        "commit": FROZEN_SOURCE_COMMIT,
        "evaluator_blobs": blobs,
        "tested_bundle": bundle,
        "reverse_delta": reverse_delta,
        "tested_bundle_manifest": manifest,
    }


def read_and_validate_db_context(
    db_path: Path, run_id: str, *, expected_layout: str | None = None
) -> dict[str, Any]:
    resolved = db_path.resolve()
    connection = sqlite3.connect(
        f"{resolved.as_uri()}?mode=ro&immutable=1", uri=True
    )
    try:
        row = connection.execute(
            "SELECT run_meta_json, initial_state_json FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
    except sqlite3.Error as exc:
        raise HeadroomDiagnosticError(f"invalid frozen SQLite packet: {exc}") from exc
    finally:
        connection.close()
    if row is None:
        raise HeadroomDiagnosticError("frozen SQLite run is absent")
    run_meta = json.loads(row[0])
    initial_state = json.loads(row[1])
    policy_seed = int(run_meta["seed"])
    world_seed = int(initial_state["world"]["trial"]["seed"])
    layout_id = str(initial_state["world"]["layout"]["layout_id"])
    if world_seed in FORBIDDEN_WORLD_SEEDS or policy_seed in FORBIDDEN_POLICY_SEEDS:
        raise HeadroomDiagnosticError("fresh-effect seed firewall rejected SQLite packet")
    if world_seed not in ALLOWED_WORLD_SEEDS or policy_seed not in ALLOWED_POLICY_SEEDS:
        raise HeadroomDiagnosticError("SQLite packet is outside the consumed-context allowlist")
    if expected_layout is not None and layout_id != expected_layout:
        raise HeadroomDiagnosticError("actual SQLite layout differs from frozen manifest")
    return {
        "run_id": run_id,
        "layout_id": layout_id,
        "world_seed": world_seed,
        "policy_seed": policy_seed,
        "sqlite_open_mode": "mode=ro&immutable=1",
    }


def snapshot_packet_tree(root: Path) -> dict[str, Any]:
    resolved = root.resolve()
    if not resolved.is_dir():
        raise HeadroomDiagnosticError(f"packet tree is absent: {resolved}")
    directories: list[str] = []
    files: dict[str, dict[str, Any]] = {}
    for path in sorted(resolved.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise HeadroomDiagnosticError("packet tree contains a symbolic link")
        relative = path.relative_to(resolved).as_posix()
        if path.is_dir():
            directories.append(relative)
        elif path.is_file():
            files[relative] = {
                "sha256": hash_file(path),
                "bytes": path.stat().st_size,
            }
        else:
            raise HeadroomDiagnosticError("packet tree contains an unsupported entry")
    body = {"directories": directories, "files": files}
    return {
        "schema_version": "ego.v2.packet_tree_manifest.v1",
        **body,
        "tree_hash": canonical_hash(body),
    }


def verify_frozen_packet() -> dict[str, Any]:
    if ALLOWED_WORLD_SEEDS & FORBIDDEN_WORLD_SEEDS:
        raise HeadroomDiagnosticError("world seed manifests overlap")
    if ALLOWED_POLICY_SEEDS & FORBIDDEN_POLICY_SEEDS:
        raise HeadroomDiagnosticError("policy seed manifests overlap")
    files = {
        name: verify_file_hash(SOURCE_PACKET / name, expected)
        for name, expected in FROZEN_INPUTS.items()
    }
    smoke = json.loads((SOURCE_PACKET / "smoke_result.json").read_text(encoding="utf-8"))
    expected_contexts = [
        f"{layout}:world={world}:policy={policy}" for layout, world, policy in CONTEXTS
    ]
    if smoke.get("context_ids") != expected_contexts:
        raise HeadroomDiagnosticError("frozen smoke context manifest drifted")
    if smoke.get("fresh_effect_seeds_consumed") is not False:
        raise HeadroomDiagnosticError("frozen smoke fresh-seed receipt drifted")
    if len(smoke.get("runs", [])) != len(CONTEXTS):
        raise HeadroomDiagnosticError("frozen smoke run count drifted")
    contexts: list[dict[str, Any]] = []
    for run, (layout, world_seed, policy_seed) in zip(smoke["runs"], CONTEXTS):
        context_id = f"{layout}:world={world_seed}:policy={policy_seed}"
        if run.get("context_ids") != [context_id] or run.get("seed") != [policy_seed]:
            raise HeadroomDiagnosticError("frozen smoke run manifest drifted")
        actual = read_and_validate_db_context(
            SOURCE_PACKET / str(run["database_path"]),
            str(run["run_id"]),
            expected_layout=layout,
        )
        if (
            actual["layout_id"] != layout
            or actual["world_seed"] != world_seed
            or actual["policy_seed"] != policy_seed
        ):
            raise HeadroomDiagnosticError("actual SQLite context differs from frozen manifest")
        contexts.append(actual | {"context_id": context_id})
    source_result = json.loads((SOURCE_PACKET / "result.json").read_text(encoding="utf-8"))
    if (
        source_result.get("verdict") != "BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION"
        or source_result.get("fresh_effect_seeds_consumed") is not False
        or source_result.get("eligible_for_separate_effect_card") is not False
    ):
        raise HeadroomDiagnosticError("R2 banked result boundary drifted")
    return {"files": files, "contexts": contexts, "source_result": source_result}


def recompute_score(
    prediction: Mapping[str, Any], truth: Mapping[str, Any]
) -> dict[str, float]:
    outcome = str(truth["outcome_type"])
    probabilities = prediction["outcome_probabilities"]
    return {
        "outcome_brier": sum(
            (float(probabilities[item]) - (1.0 if item == outcome else 0.0)) ** 2
            for item in OUTCOMES
        ),
        "outcome_nll": -math.log(max(float(probabilities[outcome]), 1e-12)),
        "delta_mae": statistics.fmean(
            abs(
                float(prediction["predicted_delta"][key])
                - float(truth["actual_delta"][key])
            )
            for key in STATE_KEYS
        ),
    }


def recompute_balanced_aggregate(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    aggregate: dict[str, Any] = {}
    for model in ("learned", "no_update"):
        aggregate[model] = {}
        for phase in ("early", "late"):
            selected = [
                row for row in rows if row["model"] == model and row["phase"] == phase
            ]
            cells: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
            for row in selected:
                cells[(str(row["context_id"]), str(row["action"]))].append(row)
            cell_metrics: list[dict[str, float]] = []
            for key in sorted(cells):
                cell_metrics.append(
                    {
                        metric: statistics.fmean(
                            float(row["scores"][metric]) for row in cells[key]
                        )
                        for metric in ("outcome_brier", "outcome_nll", "delta_mae")
                    }
                )
            aggregate[model][phase] = {
                "cell_count": len(cell_metrics),
                "outcome_brier": statistics.fmean(
                    item["outcome_brier"] for item in cell_metrics
                ),
                "outcome_nll": statistics.fmean(
                    item["outcome_nll"] for item in cell_metrics
                ),
                "delta_mae": statistics.fmean(item["delta_mae"] for item in cell_metrics),
                "aggregation_rule": (
                    "mean_within_context_action_then_equal_macro_mean_across_cells"
                ),
            }
    return aggregate


def _numbers_equal(left: Any, right: Any) -> bool:
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return set(left) == set(right) and all(
            _numbers_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _numbers_equal(a, b) for a, b in zip(left, right)
        )
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-15)
    return left == right


def _delta_mae(predicted: Mapping[str, Any], truth: Mapping[str, Any]) -> float:
    return statistics.fmean(
        abs(float(predicted[key]) - float(truth["actual_delta"][key]))
        for key in STATE_KEYS
    )


def _aggregate_delta(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    cells: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        cells[(str(row["context_id"]), str(row["action"]))].append(
            float(row["delta_mae"])
        )
    return {
        "cell_count": len(cells),
        "delta_mae": statistics.fmean(
            statistics.fmean(cells[key]) for key in sorted(cells)
        ),
        "aggregation_rule": "mean_within_context_action_then_equal_macro_mean_across_cells",
    }


def _stratified_delta(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    strata: dict[str, Any] = {}
    estimable: list[float] = []
    for action, outcome in REALIZABLE_STRATA:
        selected = [
            row
            for row in rows
            if str(row["action"]) == action
            and str(row.get("outcome_type", (row.get("truth") or {}).get("outcome_type")))
            == outcome
        ]
        support = len(selected)
        mae = (
            statistics.fmean(
                float(row.get("delta_mae", row.get("scores", {}).get("delta_mae")))
                for row in selected
            )
            if selected
            else None
        )
        is_estimable = support >= MIN_STRATUM_SUPPORT
        strata[f"{action}::{outcome}"] = {
            "support": support,
            "estimable": is_estimable,
            "delta_mae": mae,
        }
        if is_estimable and mae is not None:
            estimable.append(mae)
    all_estimable = len(estimable) == len(REALIZABLE_STRATA)
    return {
        "minimum_support": MIN_STRATUM_SUPPORT,
        "strata": strata,
        "all_strata_estimable": all_estimable,
        "macro_delta_mae": statistics.fmean(estimable) if all_estimable else None,
        "aggregation_rule": (
            "mean_within_declared_action_outcome_stratum_then_equal_macro_mean;"
            "not_estimable_if_any_stratum_below_minimum_support"
        ),
    }


def _recompute_training_support(training_rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    counts = Counter((str(row["action"]), str(row["outcome_type"])) for row in training_rows)
    features: dict[str, list[list[float]]] = defaultdict(list)
    for row in training_rows:
        features[str(row["action"])].append([float(value) for value in row["features"]])
    support = {
        f"{action}::{outcome}": int(counts[(action, outcome)])
        for action, outcome in REALIZABLE_STRATA
    }
    ranks: dict[str, int] = {}
    conditioning: dict[str, Any] = {}
    for action in ACTIONS:
        matrix = np.asarray(features.get(action, []), dtype=np.float64)
        if matrix.size == 0:
            ranks[action] = 0
            conditioning[action] = {
                "minimum_singular_value": None,
                "condition_number": None,
                "status": "no_rows",
            }
            continue
        singular = np.linalg.svd(matrix, compute_uv=False)
        ranks[action] = int(np.linalg.matrix_rank(matrix))
        minimum = float(singular[-1])
        conditioning[action] = {
            "minimum_singular_value": minimum,
            "condition_number": (None if minimum == 0.0 else float(singular[0] / minimum)),
            "status": "disclosure_only",
        }
    return {
        "minimum_support": MIN_STRATUM_SUPPORT,
        "stratum_support": support,
        "all_strata_supported": all(value >= MIN_STRATUM_SUPPORT for value in support.values()),
        "feature_count": 15,
        "feature_rank_by_action": ranks,
        "all_action_feature_ranks_full": all(value == 15 for value in ranks.values()),
        "conditioning_disclosure": conditioning,
    }


def _balanced_row_pairing_exact(rows: list[Mapping[str, Any]]) -> bool:
    pairs: dict[tuple[Any, ...], dict[str, Mapping[str, Any]]] = defaultdict(dict)
    identity_by_snapshot: dict[str, tuple[str, str, int]] = {}
    actions_by_snapshot_model: dict[
        tuple[str, str], Counter[str]
    ] = defaultdict(Counter)
    for row in rows:
        try:
            snapshot_hash = str(row["snapshot_hash"])
            snapshot_identity = (
                str(row["context_id"]),
                str(row["phase"]),
                int(row["sequence"]),
            )
            key = (
                snapshot_hash,
                *snapshot_identity,
                str(row["action"]),
            )
            model = str(row["model"])
        except (KeyError, TypeError, ValueError):
            return False
        if model not in {"learned", "no_update"} or model in pairs[key]:
            return False
        if (
            snapshot_hash in identity_by_snapshot
            and identity_by_snapshot[snapshot_hash] != snapshot_identity
        ):
            return False
        identity_by_snapshot[snapshot_hash] = snapshot_identity
        actions_by_snapshot_model[(snapshot_hash, model)][str(row["action"])] += 1
        pairs[key][model] = row
    if not pairs:
        return False
    expected_actions = Counter(ACTIONS)
    return all(
        set(models) == {"learned", "no_update"}
        and _numbers_equal(models["learned"]["truth"], models["no_update"]["truth"])
        for models in pairs.values()
    ) and all(
        actions_by_snapshot_model[(snapshot_hash, model)] == expected_actions
        for snapshot_hash in identity_by_snapshot
        for model in ("learned", "no_update")
    )


def _auxiliary_row_pairing_exact(
    learned_rows: list[Mapping[str, Any]],
    legacy_rows: list[Mapping[str, Any]],
    ablation_rows: Mapping[str, list[Mapping[str, Any]]],
) -> bool:
    def key(row: Mapping[str, Any]) -> tuple[str, int, str]:
        return (str(row["context_id"]), int(row["sequence"]), str(row["action"]))

    try:
        expected = [key(row) for row in learned_rows]
        if len(expected) != len(set(expected)):
            return False
        legacy = [key(row) for row in legacy_rows]
        if len(legacy) != len(set(legacy)) or set(legacy) != set(expected):
            return False
        if set(ablation_rows) != {
            "base_only",
            "residual_only",
            "residual_outcome_rotation",
        }:
            return False
        for mode_rows in ablation_rows.values():
            mode_keys = [key(row) for row in mode_rows]
            if len(mode_keys) != len(set(mode_keys)) or set(mode_keys) != set(expected):
                return False
    except (KeyError, TypeError, ValueError):
        return False
    return True


def _recompute_balanced_digest_base(
    rows: list[Mapping[str, Any]], aggregate: Mapping[str, Any]
) -> dict[str, Any]:
    snapshot_hashes: list[str] = []
    seen: set[str] = set()
    for row in rows:
        snapshot_hash = str(row["snapshot_hash"])
        if snapshot_hash not in seen:
            seen.add(snapshot_hash)
            snapshot_hashes.append(snapshot_hash)
    return {
        "snapshot_hashes": snapshot_hashes,
        "prediction_rows_hash": canonical_hash(
            [
                {
                    "snapshot_hash": row["snapshot_hash"],
                    "model": row["model"],
                    "action": row["action"],
                    "prediction": row["prediction"],
                }
                for row in rows
            ]
        ),
        "truth_rows_hash": canonical_hash(
            [
                {
                    "snapshot_hash": row["snapshot_hash"],
                    "action": row["action"],
                    "truth": row["truth"],
                }
                for row in rows
                if row["model"] == "learned"
            ]
        ),
        "aggregate_hash": canonical_hash(aggregate),
        "payload_hash": canonical_hash(
            {
                "snapshot_hashes": snapshot_hashes,
                "rows": rows,
                "aggregate_metrics": aggregate,
            }
        ),
    }


def validate_required_evidence_sections(
    report: Mapping[str, Any],
    training_rows: list[Mapping[str, Any]] | None,
    leakage: Mapping[str, Any] | None,
) -> None:
    required_types: dict[str, type | tuple[type, ...]] = {
        "rows": list,
        "aggregate_metrics": Mapping,
        "snapshot_count": int,
        "sample_counts_by_action": Mapping,
        "outcome_stratified_metrics": Mapping,
        "legacy_unconditional_metrics": Mapping,
        "legacy_rows": list,
        "hierarchical_ablation_metrics": Mapping,
        "hierarchical_ablation_rows": Mapping,
        "training_support_and_rank": Mapping,
        "fresh_subprocess_digest_expected": Mapping,
        "fresh_subprocess_digest_actual": Mapping,
        "frozen_update_controls": list,
        "checks": Mapping,
        "failed_checks": list,
        "passed": bool,
    }
    for name, expected_type in required_types.items():
        if name not in report or not isinstance(report[name], expected_type):
            raise HeadroomDiagnosticError(
                f"required evidence section is absent or malformed: {name}"
            )
    if type(report["snapshot_count"]) is not int or type(report["passed"]) is not bool:
        raise HeadroomDiagnosticError("required evidence scalar type drifted")
    ablation_modes = {
        "base_only",
        "residual_only",
        "residual_outcome_rotation",
    }
    if set(report["hierarchical_ablation_metrics"]) != ablation_modes or set(
        report["hierarchical_ablation_rows"]
    ) != ablation_modes:
        raise HeadroomDiagnosticError("required evidence ablation mode set drifted")
    if not isinstance(training_rows, list) or not training_rows:
        raise HeadroomDiagnosticError("required evidence training rows are absent")
    if not isinstance(leakage, Mapping):
        raise HeadroomDiagnosticError("required evidence leakage report is absent")
    clean_scan = leakage.get("clean_scan")
    positive = leakage.get("positive_controls")
    if (
        not isinstance(clean_scan, Mapping)
        or not isinstance(clean_scan.get("findings"), list)
        or type(clean_scan.get("clean")) is not bool
        or not isinstance(positive, Mapping)
        or set(positive) != set(LEAKAGE_POSITIVE_CONTROL_FIELDS)
        or type(leakage.get("all_positive_controls_detected")) is not bool
    ):
        raise HeadroomDiagnosticError("required evidence leakage schema drifted")
    for field, item in positive.items():
        if (
            not isinstance(item, Mapping)
            or type(item.get("detected")) is not bool
            or not isinstance(item.get("scan"), Mapping)
            or not isinstance(item["scan"].get("findings"), list)
        ):
            raise HeadroomDiagnosticError(
                f"required evidence leakage control drifted: {field}"
            )
    controls = report["frozen_update_controls"]
    if len(controls) != len(CONTEXTS) or not all(
        isinstance(item, Mapping) for item in controls
    ):
        raise HeadroomDiagnosticError("required evidence frozen controls drifted")
    for digest_name in (
        "fresh_subprocess_digest_expected",
        "fresh_subprocess_digest_actual",
    ):
        digest = report[digest_name]
        if not isinstance(digest.get("base"), Mapping) or not isinstance(
            digest.get("code_path_hash"), str
        ):
            raise HeadroomDiagnosticError(
                f"required evidence digest drifted: {digest_name}"
            )
    validate_frozen_report_contract(report)


def _independent_leakage_check(leakage: Mapping[str, Any]) -> tuple[bool, bool]:
    clean_scan = leakage["clean_scan"]
    clean_from_findings = len(clean_scan["findings"]) == 0
    internal_exact = clean_scan["clean"] is clean_from_findings
    detected_values: list[bool] = []
    for field in sorted(LEAKAGE_POSITIVE_CONTROL_FIELDS):
        item = leakage["positive_controls"][field]
        detected_from_findings = any(
            isinstance(finding, Mapping) and finding.get("field") == field
            for finding in item["scan"]["findings"]
        )
        internal_exact = internal_exact and item["detected"] is detected_from_findings
        detected_values.append(detected_from_findings)
    all_detected = all(detected_values)
    internal_exact = (
        internal_exact
        and leakage["all_positive_controls_detected"] is all_detected
    )
    return clean_from_findings and all_detected and internal_exact, internal_exact


def _independent_frozen_update_check(
    controls: list[Mapping[str, Any]],
) -> tuple[bool, bool]:
    internal_exact = len(controls) == len(CONTEXTS)
    passes: list[bool] = []
    seen_contexts: set[str] = set()
    for item in controls:
        actions = list(item.get("first_20_actions", []))
        counts = Counter(str(action) for action in actions)
        recomputed_counts = {action: counts[action] for action in ACTIONS}
        hashes_equal = item.get("initial_model_hash") == item.get("final_model_hash")
        coverage = (
            len(actions) == 20
            and set(actions).issubset(ACTIONS)
            and all(recomputed_counts[action] >= 4 for action in ACTIONS)
        )
        context_ids = item.get("context_ids")
        if isinstance(context_ids, list) and len(context_ids) == 1:
            seen_contexts.add(str(context_ids[0]))
        else:
            internal_exact = False
        internal_exact = (
            internal_exact
            and item.get("first_20_action_counts") == recomputed_counts
            and item.get("model_hash_unchanged") is hashes_equal
            and item.get("first_20_cover_each_action_at_least_four") is coverage
            and type(item.get("update_count")) is int
        )
        passes.append(hashes_equal and item.get("update_count") == 0 and coverage)
    expected_contexts = {
        f"{layout}:world={world}:policy={policy}"
        for layout, world, policy in CONTEXTS
    }
    internal_exact = internal_exact and seen_contexts == expected_contexts
    return all(passes) and internal_exact, internal_exact


def independently_derive_frozen_checks(
    report: Mapping[str, Any],
    recomputation: Mapping[str, Any],
    leakage: Mapping[str, Any],
) -> dict[str, bool]:
    rows = list(report["rows"])
    learned_rows = [row for row in rows if row.get("model") == "learned"]
    action_counts = Counter(str(row["action"]) for row in learned_rows)
    context_phase_counts = Counter(
        (str(row["context_id"]), str(row["phase"]), str(row["action"]))
        for row in learned_rows
    )
    expected_cells = {
        (
            f"{layout}:world={world}:policy={policy}",
            phase,
            action,
        )
        for layout, world, policy in CONTEXTS
        for phase in ("early", "late")
        for action in ACTIONS
    }
    aggregate = recomputation["aggregate_metrics"]
    stratified = recomputation["outcome_stratified_metrics"]
    ablations = recomputation["hierarchical_ablation_metrics"]
    training = recomputation["training_support_rank_and_conditioning"]
    leakage_pass, _leakage_internal_exact = _independent_leakage_check(leakage)
    frozen_pass, _frozen_internal_exact = _independent_frozen_update_check(
        list(report["frozen_update_controls"])
    )

    learned_late = aggregate["learned"]["late"]
    learned_early = aggregate["learned"]["early"]
    no_update_late = aggregate["no_update"]["late"]
    learned_late_macro = stratified["learned"]["late"]["macro_delta_mae"]
    learned_early_macro = stratified["learned"]["early"]["macro_delta_mae"]
    no_update_late_macro = stratified["no_update"]["late"]["macro_delta_mae"]
    legacy_late_macro = stratified["legacy_unconditional"]["late"][
        "macro_delta_mae"
    ]

    def macro_below(left: float | None, right: float | None) -> bool:
        return left is not None and right is not None and float(left) < float(right)

    def critical_strata_not_worse(reference: str) -> bool:
        learned_strata = stratified["learned"]["late"]["strata"]
        reference_strata = stratified[reference]["late"]["strata"]
        for key in ("interact::interacted", "interact::no_object"):
            left = learned_strata[key]
            right = reference_strata[key]
            if (
                not left["estimable"]
                or not right["estimable"]
                or float(left["delta_mae"]) > float(right["delta_mae"])
            ):
                return False
        return True

    unique_snapshots = {str(row["snapshot_hash"]) for row in learned_rows}
    learned_actions_by_snapshot: dict[str, Counter[str]] = defaultdict(Counter)
    learned_identities_by_snapshot: dict[str, set[tuple[str, str, int]]] = defaultdict(
        set
    )
    for row in learned_rows:
        snapshot_hash = str(row["snapshot_hash"])
        learned_actions_by_snapshot[snapshot_hash][str(row["action"])] += 1
        learned_identities_by_snapshot[snapshot_hash].add(
            (
                str(row["context_id"]),
                str(row["phase"]),
                int(row["sequence"]),
            )
        )
    per_snapshot_action_coverage = all(
        len(learned_identities_by_snapshot[snapshot_hash]) == 1
        and learned_actions_by_snapshot[snapshot_hash] == Counter(ACTIONS)
        for snapshot_hash in unique_snapshots
    )
    all_effect_strata_estimable = all(
        phase_report["all_strata_estimable"]
        for model_report in stratified.values()
        for phase_report in model_report.values()
    )
    return {
        "all_five_action_counts_exactly_equal": (
            set(action_counts) == set(ACTIONS)
            and len(set(action_counts.values())) == 1
        ),
        "no_snapshot_action_context_unused": (
            len(learned_rows) == int(report["snapshot_count"]) * len(ACTIONS)
            and len(unique_snapshots) == int(report["snapshot_count"])
            and per_snapshot_action_coverage
            and set(context_phase_counts) == expected_cells
            and all(count > 0 for count in context_phase_counts.values())
        ),
        "learned_late_brier_improves_by_at_least_0_02": (
            learned_late["outcome_brier"] <= learned_early["outcome_brier"] - 0.02
        ),
        "learned_late_nll_improves_by_at_least_0_05": (
            learned_late["outcome_nll"] <= learned_early["outcome_nll"] - 0.05
        ),
        "learned_late_brier_below_no_update_late": (
            learned_late["outcome_brier"] < no_update_late["outcome_brier"]
        ),
        "learned_late_nll_below_no_update_late": (
            learned_late["outcome_nll"] < no_update_late["outcome_nll"]
        ),
        "training_support_at_least_16_per_declared_stratum": bool(
            training["all_strata_supported"]
        ),
        "shared_base_feature_rank_is_full_for_every_action": bool(
            training["all_action_feature_ranks_full"]
        ),
        "all_effect_strata_have_at_least_16_rows_per_phase": (
            all_effect_strata_estimable
        ),
        "learned_late_macro_delta_mae_below_early": macro_below(
            learned_late_macro, learned_early_macro
        ),
        "learned_late_macro_delta_mae_below_no_update_late": macro_below(
            learned_late_macro, no_update_late_macro
        ),
        "learned_late_macro_delta_mae_below_legacy_unconditional": macro_below(
            learned_late_macro, legacy_late_macro
        ),
        "interact_strata_not_worse_than_no_update": critical_strata_not_worse(
            "no_update"
        ),
        "interact_strata_not_worse_than_legacy_unconditional": (
            critical_strata_not_worse("legacy_unconditional")
        ),
        "base_only_ablation_changes_late_macro_delta": (
            learned_late_macro is not None
            and ablations["base_only"]["late"]["macro_delta_mae"] is not None
            and not math.isclose(
                float(learned_late_macro),
                float(ablations["base_only"]["late"]["macro_delta_mae"]),
                abs_tol=1e-15,
            )
        ),
        "residual_only_ablation_changes_late_macro_delta": (
            learned_late_macro is not None
            and ablations["residual_only"]["late"]["macro_delta_mae"] is not None
            and not math.isclose(
                float(learned_late_macro),
                float(ablations["residual_only"]["late"]["macro_delta_mae"]),
                abs_tol=1e-15,
            )
        ),
        "outcome_rotation_changes_late_macro_delta": (
            learned_late_macro is not None
            and ablations["residual_outcome_rotation"]["late"]["macro_delta_mae"]
            is not None
            and not math.isclose(
                float(learned_late_macro),
                float(
                    ablations["residual_outcome_rotation"]["late"][
                        "macro_delta_mae"
                    ]
                ),
                abs_tol=1e-15,
            )
        ),
        "forced_action_truth_exists_for_every_balanced_row": all(
            str(row["truth"]["outcome_type"]) in OUTCOMES for row in rows
        ),
        "leakage_clean_and_all_positive_controls_detected": leakage_pass,
        "fresh_subprocess_balanced_recompute_exact": all(
            recomputation["checks"].get(name) is True
            for name in (
                "fresh_digest_expected_equals_actual",
                "row_recomputed_digest_matches_expected",
                "row_recomputed_digest_matches_actual",
            )
        ),
        "two_frozen_update_controls_pass": frozen_pass,
    }


def independent_recompute(
    report: Mapping[str, Any],
    training_rows: list[Mapping[str, Any]] | None = None,
    *,
    leakage: Mapping[str, Any] | None = None,
    require_complete: bool = False,
) -> dict[str, Any]:
    if require_complete:
        validate_required_evidence_sections(report, training_rows, leakage)
    rows = deepcopy(list(report["rows"]))
    row_scores_exact = True
    for row in rows:
        recomputed = recompute_score(row["prediction"], row["truth"])
        row_scores_exact = row_scores_exact and _numbers_equal(recomputed, row["scores"])
        row["scores"] = recomputed
    aggregate = recompute_balanced_aggregate(rows)
    aggregate_exact = _numbers_equal(aggregate, report["aggregate_metrics"])

    truth_by_key = {
        (str(row["context_id"]), int(row["sequence"]), str(row["action"])): row["truth"]
        for row in rows
        if row["model"] == "learned"
    }
    legacy_rows = deepcopy(list(report.get("legacy_rows", [])))
    auxiliary_scores_exact = True
    for row in legacy_rows:
        truth = truth_by_key[(str(row["context_id"]), int(row["sequence"]), str(row["action"]))]
        recomputed = _delta_mae(row["predicted_delta"], truth)
        auxiliary_scores_exact = auxiliary_scores_exact and _numbers_equal(
            recomputed, row["delta_mae"]
        )
        row["delta_mae"] = recomputed
    ablation_rows = deepcopy(dict(report.get("hierarchical_ablation_rows", {})))
    learned_rows = [row for row in rows if row.get("model") == "learned"]
    auxiliary_pairing_exact = _auxiliary_row_pairing_exact(
        learned_rows, legacy_rows, ablation_rows
    ) if legacy_rows or ablation_rows else None
    for mode_rows in ablation_rows.values():
        for row in mode_rows:
            truth = truth_by_key[(str(row["context_id"]), int(row["sequence"]), str(row["action"]))]
            recomputed = _delta_mae(row["predicted_delta"], truth)
            auxiliary_scores_exact = auxiliary_scores_exact and _numbers_equal(
                recomputed, row["delta_mae"]
            )
            row["delta_mae"] = recomputed

    stratified = None
    stratified_exact: bool | None = None
    if "outcome_stratified_metrics" in report:
        stratified = {
            model: {
                phase: _stratified_delta(
                    [row for row in model_rows if str(row["phase"]) == phase]
                )
                for phase in ("early", "late")
            }
            for model, model_rows in {
                "learned": [row for row in rows if row["model"] == "learned"],
                "no_update": [row for row in rows if row["model"] == "no_update"],
                "legacy_unconditional": legacy_rows,
            }.items()
        }
        stratified_exact = _numbers_equal(
            stratified, report["outcome_stratified_metrics"]
        )
    legacy = None
    legacy_exact: bool | None = None
    if "legacy_unconditional_metrics" in report:
        legacy = {
            phase: _aggregate_delta(
                [row for row in legacy_rows if row["phase"] == phase]
            )
            for phase in ("early", "late")
        }
        legacy_exact = _numbers_equal(legacy, report["legacy_unconditional_metrics"])
    ablations = None
    ablations_exact: bool | None = None
    if "hierarchical_ablation_metrics" in report:
        ablations = {
            mode: {
                phase: _stratified_delta(
                    [row for row in mode_rows if row["phase"] == phase]
                )
                for phase in ("early", "late")
            }
            for mode, mode_rows in ablation_rows.items()
        }
        ablations_exact = _numbers_equal(
            ablations, report["hierarchical_ablation_metrics"]
        )

    training = None
    training_exact: bool | None = None
    if training_rows is not None:
        training = _recompute_training_support(training_rows)
        frozen_training = dict(report["training_support_and_rank"])
        comparable = {key: training[key] for key in frozen_training}
        training_exact = _numbers_equal(comparable, frozen_training)
    pairing_exact = _balanced_row_pairing_exact(rows)
    expected_digest = report.get("fresh_subprocess_digest_expected")
    actual_digest = report.get("fresh_subprocess_digest_actual")
    digest_expected_equals_actual: bool | None = None
    recomputed_matches_expected: bool | None = None
    recomputed_matches_actual: bool | None = None
    recomputed_digest_base: dict[str, Any] | None = None
    if expected_digest is not None or actual_digest is not None:
        if not isinstance(expected_digest, Mapping) or not isinstance(
            actual_digest, Mapping
        ):
            digest_expected_equals_actual = False
            recomputed_matches_expected = False
            recomputed_matches_actual = False
        else:
            digest_expected_equals_actual = _numbers_equal(
                expected_digest, actual_digest
            )
            recomputed_digest_base = _recompute_balanced_digest_base(rows, aggregate)
            recomputed_matches_expected = _numbers_equal(
                recomputed_digest_base, expected_digest.get("base")
            )
            recomputed_matches_actual = _numbers_equal(
                recomputed_digest_base, actual_digest.get("base")
            )
    checks = {
        "all_row_scores_exact": row_scores_exact,
        "aggregate_metrics_exact": aggregate_exact,
        "auxiliary_delta_scores_exact": auxiliary_scores_exact,
        "outcome_stratified_metrics_exact": stratified_exact,
        "legacy_metrics_exact": legacy_exact,
        "ablation_metrics_exact": ablations_exact,
        "training_support_and_rank_exact": training_exact,
        "balanced_row_pairing_exact": pairing_exact,
        "auxiliary_row_pairing_exact": auxiliary_pairing_exact,
        "fresh_digest_expected_equals_actual": digest_expected_equals_actual,
        "row_recomputed_digest_matches_expected": recomputed_matches_expected,
        "row_recomputed_digest_matches_actual": recomputed_matches_actual,
    }
    learned_rows_for_counts = [row for row in rows if row.get("model") == "learned"]
    snapshot_count_exact: bool | None = None
    sample_counts_exact: bool | None = None
    if "snapshot_count" in report:
        snapshot_count_exact = (
            type(report["snapshot_count"]) is int
            and len({str(row["snapshot_hash"]) for row in learned_rows_for_counts})
            == report["snapshot_count"]
        )
    if "sample_counts_by_action" in report:
        sample_counts_exact = _numbers_equal(
            {
                action: sum(
                    str(row["action"]) == action for row in learned_rows_for_counts
                )
                for action in ACTIONS
            },
            report["sample_counts_by_action"],
        )
    checks["snapshot_count_exact"] = snapshot_count_exact
    checks["sample_counts_by_action_exact"] = sample_counts_exact

    derived_frozen_checks: dict[str, bool] | None = None
    leakage_internal_exact: bool | None = None
    frozen_controls_internal_exact: bool | None = None
    frozen_check_truth_exact: bool | None = None
    if require_complete:
        assert leakage is not None
        _leakage_pass, leakage_internal_exact = _independent_leakage_check(leakage)
        _frozen_pass, frozen_controls_internal_exact = _independent_frozen_update_check(
            list(report["frozen_update_controls"])
        )
        derivation_view = {
            "aggregate_metrics": aggregate,
            "outcome_stratified_metrics": stratified,
            "hierarchical_ablation_metrics": ablations,
            "training_support_rank_and_conditioning": training,
            "checks": checks,
        }
        derived_frozen_checks = independently_derive_frozen_checks(
            report, derivation_view, leakage
        )
        frozen_check_truth_exact = _numbers_equal(
            derived_frozen_checks, report["checks"]
        )
    checks["leakage_report_internal_exact"] = leakage_internal_exact
    checks["frozen_controls_internal_exact"] = frozen_controls_internal_exact
    checks["frozen_check_truth_exact"] = frozen_check_truth_exact
    required = [value for value in checks.values() if value is not None]
    return {
        "row_count": len(rows),
        "all_row_scores_exact": row_scores_exact,
        "aggregate_metrics_exact": aggregate_exact,
        "aggregate_metrics": aggregate,
        "outcome_stratified_metrics": stratified,
        "legacy_unconditional_metrics": legacy,
        "hierarchical_ablation_metrics": ablations,
        "training_support_rank_and_conditioning": training,
        "balanced_digest_base_recomputed": recomputed_digest_base,
        "derived_frozen_checks": derived_frozen_checks,
        "checks": checks,
        "all_exact": all(required),
        "rows_hash": canonical_hash(rows),
        "truth_hash": canonical_hash(
            [
                {"context_id": row["context_id"], "sequence": row["sequence"], "action": row["action"], "truth": row["truth"]}
                for row in rows
                if row["model"] == "learned"
            ]
        ),
    }


def validate_frozen_report_contract(report: Mapping[str, Any]) -> dict[str, bool]:
    raw_checks = report.get("checks")
    if not isinstance(raw_checks, Mapping):
        raise HeadroomDiagnosticError("frozen check contract omitted checks")
    checks = {str(name): value for name, value in raw_checks.items()}
    if set(checks) != set(EXPECTED_FROZEN_CHECKS) or any(
        type(value) is not bool for value in checks.values()
    ):
        raise HeadroomDiagnosticError("frozen check contract key/type set drifted")
    expected_failed = sorted(name for name, passed in checks.items() if not passed)
    actual_failed = report.get("failed_checks")
    if not isinstance(actual_failed, list) or sorted(actual_failed) != expected_failed:
        raise HeadroomDiagnosticError("frozen check contract failed-list drifted")
    expected_passed = all(checks.values())
    if report.get("passed") is not expected_passed:
        raise HeadroomDiagnosticError("frozen check contract passed flag drifted")
    return checks


def select_verdict(report: Mapping[str, Any], recomputation: Mapping[str, Any]) -> str:
    validate_frozen_report_contract(report)
    if not bool(recomputation.get("all_exact")):
        return BLOCKED_VERDICT
    failed = set(report.get("failed_checks", []))
    if failed & VALIDITY_CHECKS:
        return BLOCKED_VERDICT
    if failed & SUPPORT_CHECKS:
        return INSUFFICIENT_VERDICT
    return POSITIVE_VERDICT if not failed else NO_PREDICTION_DIFFERENCE_VERDICT


def _patch_sections(patch_text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            match = re.fullmatch(r"diff --git a/(.*?) b/(.*)", line)
            if match is None or match.group(1) != match.group(2):
                raise HeadroomDiagnosticError("reverse-delta path header is invalid")
            current = match.group(1)
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return sections


def _patch_hunks(section: list[str]) -> list[dict[str, Any]]:
    hunks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in section:
        if line.startswith("@@ "):
            match = re.match(
                r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line
            )
            if match is None:
                raise HeadroomDiagnosticError("reverse-delta hunk header is invalid")
            current = {"new_start": int(match.group(3)), "items": []}
            hunks.append(current)
        elif (
            current is not None
            and line[:1] in {" ", "+", "-"}
            and not line.startswith(("+++", "---"))
        ):
            current["items"].append((line[0], line[1:].encode("utf-8")))
        elif line == r"\ No newline at end of file":
            continue
    return hunks


def _split_byte_lines(data: bytes) -> list[tuple[bytes, bytes]]:
    lines: list[tuple[bytes, bytes]] = []
    for raw in data.splitlines(keepends=True):
        if raw.endswith(b"\r\n"):
            lines.append((raw[:-2], b"\r\n"))
        elif raw.endswith(b"\n"):
            lines.append((raw[:-1], b"\n"))
        elif raw.endswith(b"\r"):
            lines.append((raw[:-1], b"\r"))
        else:
            lines.append((raw, b""))
    return lines


def _reverse_patch_preserving_eol(
    data: bytes, section: list[str], *, inserted_eols: tuple[bytes, ...]
) -> bytes:
    lines = _split_byte_lines(data)
    offset = 0
    inserted_index = 0
    for hunk in _patch_hunks(section):
        target = [body for sign, body in hunk["items"] if sign in {" ", "+"}]
        position = int(hunk["new_start"]) - 1 + offset

        def matches(candidate: int) -> bool:
            return (
                candidate >= 0
                and candidate + len(target) <= len(lines)
                and [body for body, _ending in lines[candidate : candidate + len(target)]]
                == target
            )

        if not matches(position):
            nearby = [
                candidate
                for candidate in range(
                    max(0, position - 20), min(len(lines), position + 21)
                )
                if matches(candidate)
            ]
            if len(nearby) != 1:
                raise HeadroomDiagnosticError("reverse-delta hunk did not match uniquely")
            position = nearby[0]
        consumed = lines[position : position + len(target)]
        consumed_index = 0
        replacement: list[tuple[bytes, bytes]] = []
        for sign, body in hunk["items"]:
            if sign == " ":
                if consumed[consumed_index][0] != body:
                    raise HeadroomDiagnosticError("reverse-delta context drifted")
                replacement.append(consumed[consumed_index])
                consumed_index += 1
            elif sign == "+":
                if consumed[consumed_index][0] != body:
                    raise HeadroomDiagnosticError("reverse-delta addition drifted")
                consumed_index += 1
            else:
                if inserted_index >= len(inserted_eols):
                    raise HeadroomDiagnosticError("reverse-delta EOL authority is incomplete")
                replacement.append((body, inserted_eols[inserted_index]))
                inserted_index += 1
        lines[position : position + len(target)] = replacement
        offset += len(replacement) - len(target)
    if inserted_index != len(inserted_eols):
        raise HeadroomDiagnosticError("reverse-delta EOL authority was not fully consumed")
    return b"".join(body + ending for body, ending in lines)


def _write_git_object(destination: Path, relative: str) -> dict[str, Any]:
    data = _git("show", f"{FROZEN_SOURCE_COMMIT}:{relative}", binary=True)
    if not isinstance(data, bytes):
        raise HeadroomDiagnosticError("git source extraction did not return bytes")
    path = destination / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {
        "blob_oid": str(_git("rev-parse", f"{FROZEN_SOURCE_COMMIT}:{relative}")),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "authority": "git_object_frozen_evaluator_semantics",
    }


def _materialize_frozen_source(destination: Path) -> dict[str, Any]:
    pins = verify_source_pins()
    destination.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, Any]] = {}
    runtime_prefix = "labs/ego_life_playground_v0/"
    boundary_relative = (
        "scripts/codex/verify_ego_v2_factored_predictive_control_boundary_gate_001c.py"
    )
    with zipfile.ZipFile(R3_TESTED_BUNDLE) as archive:
        manifest_files = pins["tested_bundle_manifest"]["files"]
        selected = sorted(
            relative
            for relative in manifest_files
            if relative.startswith(runtime_prefix) and relative.endswith(".py")
        )
        for relative in selected:
            data = archive.read(relative)
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            files[relative] = {
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "authority": "R3_banked_tested_bundle_provenance_carrier",
            }
    patch_text = R3_REVERSE_DELTA.read_text(encoding="utf-8")
    sections = _patch_sections(patch_text)
    reconstruction = {
        "labs/ego_life_playground_v0/engine.py": (b"\n",) * 5,
        "labs/ego_life_playground_v0/predictive_control.py": (),
    }
    for relative, eols in reconstruction.items():
        if relative not in sections:
            raise HeadroomDiagnosticError(f"reverse-delta omitted runtime file: {relative}")
        path = destination / relative
        reconstructed = _reverse_patch_preserving_eol(
            path.read_bytes(), sections[relative], inserted_eols=eols
        )
        path.write_bytes(reconstructed)
        expected = RECONSTRUCTED_RUNTIME_SHA256[path.name]
        actual = hashlib.sha256(reconstructed).hexdigest()
        if actual != expected:
            raise HeadroomDiagnosticError(f"R2 runtime reconstruction drifted: {relative}")
        files[relative] = {
            "sha256": actual,
            "bytes": len(reconstructed),
            "authority": "R3_tested_bundle_plus_exact_reverse_delta_to_R2",
        }
    for name, expected in RECONSTRUCTED_RUNTIME_SHA256.items():
        path = destination / runtime_prefix / name
        if hash_file(path) != expected:
            raise HeadroomDiagnosticError(f"R2 runtime source hash drifted: {name}")
    for evaluator_relative in FROZEN_EVALUATOR_BLOBS:
        files[evaluator_relative] = _write_git_object(destination, evaluator_relative)
    if hash_file(destination / boundary_relative) != R3_BOUNDARY_HELPER_SHA256:
        raise HeadroomDiagnosticError("frozen boundary helper bytes drifted")
    for relative in (
        "labs/__init__.py",
        "labs/ego_life_playground_v0/__init__.py",
        "scripts/__init__.py",
        "scripts/codex/__init__.py",
    ):
        try:
            files[relative] = _write_git_object(destination, relative)
        except subprocess.CalledProcessError:
            # Namespace packages do not require an initializer; absence is explicit.
            continue
    independent_manifest = {
        "schema_version": "ego.life_playground.code_path.v11",
        "files": [
            {"path": name, "sha256": RECONSTRUCTED_RUNTIME_SHA256[name]}
            for name in (
                "engine.py",
                "microworld.py",
                "claims.py",
                "predictive_control.py",
                "survival_learning.py",
                "store.py",
            )
        ],
    }
    independent_hash = canonical_hash(independent_manifest)
    if independent_hash != R2_RUNTIME_CODE_PATH_HASH:
        raise HeadroomDiagnosticError("host-recomputed R2 code-path hash drifted")
    return {
        "authority": "r3_tested_bundle_reverse_delta_to_r2_runtime",
        "lineage_discontinuity": True,
        "evaluator_commit": FROZEN_SOURCE_COMMIT,
        "tested_bundle_sha256": R3_TESTED_BUNDLE_SHA256,
        "reverse_delta_sha256": R3_REVERSE_DELTA_SHA256,
        "independent_runtime_manifest": independent_manifest,
        "independent_runtime_code_path_hash": independent_hash,
        "files": files,
    }


def validate_import_receipt(
    receipt: Mapping[str, Any], source_manifest: Mapping[str, Any]
) -> dict[str, Any]:
    expected = {
        "r2": "scripts/codex/verify_ego_v2_hierarchical_outcome_delta_repair_001c_r2.py",
        "boundary": "scripts/codex/verify_ego_v2_factored_predictive_control_boundary_gate_001c.py",
        "controller": "labs/ego_life_playground_v0/controller.py",
        "engine": "labs/ego_life_playground_v0/engine.py",
        "microworld": "labs/ego_life_playground_v0/microworld.py",
        "predictive_control": "labs/ego_life_playground_v0/predictive_control.py",
        "store": "labs/ego_life_playground_v0/store.py",
    }
    modules = receipt.get("modules")
    files = source_manifest.get("files")
    if not isinstance(modules, Mapping) or not isinstance(files, Mapping):
        raise HeadroomDiagnosticError("materialized import receipt is malformed")
    if set(modules) != set(expected):
        raise HeadroomDiagnosticError("materialized import receipt module set drifted")
    for name, relative in expected.items():
        item = modules[name]
        if (
            not isinstance(item, Mapping)
            or item.get("path") != relative
            or relative not in files
            or item.get("sha256") != files[relative].get("sha256")
        ):
            raise HeadroomDiagnosticError(
                f"materialized import receipt drifted: {name}"
            )
    if receipt.get("engine_code_path_hash") != R2_RUNTIME_CODE_PATH_HASH:
        raise HeadroomDiagnosticError("materialized import receipt code-path drifted")
    return {"exact": True, "modules": dict(modules), "engine_code_path_hash": R2_RUNTIME_CODE_PATH_HASH}


_FROZEN_DRIVER = r'''
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

snapshot = Path(sys.argv[1]).resolve()
packet = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(snapshot))

from scripts.codex import verify_ego_v2_hierarchical_outcome_delta_repair_001c_r2 as r2
from scripts.codex import verify_ego_v2_factored_predictive_control_boundary_gate_001c as boundary
from labs.ego_life_playground_v0 import controller, engine, microworld, predictive_control, store
from labs.ego_life_playground_v0.microworld import policy_observation
from labs.ego_life_playground_v0.store import SQLiteEventStore

smoke = json.loads((packet / "smoke_result.json").read_text(encoding="utf-8"))
modules = {
    "r2": r2,
    "boundary": boundary,
    "controller": controller,
    "engine": engine,
    "microworld": microworld,
    "predictive_control": predictive_control,
    "store": store,
}
import_receipt = {"modules": {}}
for name, module in modules.items():
    module_path = Path(module.__file__).resolve()
    try:
        relative = module_path.relative_to(snapshot).as_posix()
    except ValueError as exc:
        raise RuntimeError(f"materialized module escaped snapshot: {name}") from exc
    import_receipt["modules"][name] = {
        "path": relative,
        "sha256": hashlib.sha256(module_path.read_bytes()).hexdigest(),
    }
import_receipt["engine_code_path_hash"] = engine.compute_code_path_hash()
if import_receipt["engine_code_path_hash"] != "b6eadf0c8ba7244ea08cd67eb936438fda182f43e56c65918bde8264fd5b9d29":
    raise RuntimeError("materialized runtime does not recover the banked R2 code path")
report = r2.run_balanced(packet, smoke)
training_rows = []
for run, (layout, world_seed, policy_seed) in zip(smoke["runs"], r2.CONTEXTS):
    context_id = r2._context_id(layout, world_seed, policy_seed)
    with SQLiteEventStore(packet / run["database_path"]) as store:
        recovered = store.recover_run(run["run_id"])
    for previous_frame, frame in zip(recovered.frames, recovered.frames[1:]):
        trace = frame.trace
        if trace is None or trace.get("selected_action") is None:
            continue
        action = str(trace["selected_action"])
        decision_state, _ = engine._decision_state_for_tick(
            previous_frame.state, run_id=run["run_id"], sequence=int(trace["sequence"])
        )
        observation = policy_observation(decision_state["world"], occlusion=True)
        prepared, _ = predictive_control.observe_belief(
            decision_state["predictive_control"],
            observation=observation,
            episode_index=int(decision_state["clock"]["episode_index"]),
            mode="relative",
        )
        payload = predictive_control.predictor_input_snapshot(
            prepared,
            observation=observation,
            organism=decision_state["organism"],
            relative_map_mode="relative",
        )
        features = predictive_control._feature_vector_from_summary(
            organism=payload["organism"], summary=payload["belief_summary"]
        )
        training_rows.append({
            "context_id": context_id,
            "sequence": int(trace["sequence"]),
            "action": action,
            "outcome_type": str(trace["world_transition"]["outcome_type"]),
            "features": [float(value) for value in features],
        })
report["_headroom_training_rows"] = training_rows
report["_headroom_import_receipt"] = import_receipt
print(r2._canonical_json(report))
'''


def _run_frozen_balanced() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="ego-r4-headroom-") as temporary:
        root = Path(temporary)
        snapshot = root / "source"
        packet = root / "packet"
        snapshot.mkdir()
        packet.mkdir()
        source_manifest = _materialize_frozen_source(snapshot)
        for name in ("smoke_result.json", "smoke_p0_cross_v1.sqlite3", "smoke_p2_vertical_v1.sqlite3"):
            shutil.copyfile(SOURCE_PACKET / name, packet / name)
        driver = root / "frozen_headroom_driver.py"
        driver.write_text(_FROZEN_DRIVER, encoding="utf-8", newline="\n")
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(snapshot) + os.pathsep + environment.get("PYTHONPATH", "")
        completed = subprocess.run(
            [sys.executable, str(driver), str(snapshot), str(packet)],
            cwd=snapshot,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(completed.stdout)
        leakage_path = packet / "leakage_report.json"
        if not leakage_path.is_file():
            raise HeadroomDiagnosticError("frozen balanced evaluator omitted leakage report")
        leakage = json.loads(leakage_path.read_text(encoding="utf-8"))
        return report, leakage, source_manifest


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(canonical_json(value) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical_json(row) + "\n")
    os.replace(temporary, path)


def build_artifact_manifest(output_dir: Path) -> dict[str, Any]:
    """Hash the complete published packet without creating a self-hash cycle."""
    files: dict[str, dict[str, Any]] = {}
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(output_dir).as_posix()
        if relative == "artifact_manifest.json":
            continue
        files[relative] = {
            "sha256": hash_file(path),
            "bytes": path.stat().st_size,
        }
    return {
        "schema_version": "ego.v2.r4_artifact_manifest.v1",
        "files": files,
        "artifact_set_hash": canonical_hash(files),
    }


def _publish_packet_atomically(
    output_dir: Path,
    writer: Callable[[Path], dict[str, Any]],
    *,
    expected_files: set[str] | frozenset[str] | None = None,
) -> dict[str, Any]:
    """Build a complete packet beside the target, then publish with one rename."""
    validate_output_target(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{output_dir.name}.staging-",
            dir=output_dir.parent,
        )
    )
    try:
        result = writer(staging)
        artifact_manifest = build_artifact_manifest(staging)
        if expected_files is not None and set(artifact_manifest["files"]) != set(
            expected_files
        ):
            raise HeadroomDiagnosticError("final artifact set is incomplete or widened")
        _write_json(staging / "artifact_manifest.json", artifact_manifest)
        validate_output_target(output_dir)
        if output_dir.exists():
            output_dir.rmdir()
        os.replace(staging, output_dir)
        return result
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def write_blocked_output(output_dir: Path, error: Exception) -> dict[str, Any]:
    result = {
        "task_id": TASK_ID,
        "verdict": BLOCKED_VERDICT,
        "prediction_difference_status": "invalid",
        "mechanism_headroom_status": "not_adjudicated_requires_cheap_challenger_stage",
        "product_sla_status": "BANKED_FAILED_R2",
        "failed_checks": ["provenance_or_recomputation_precondition"],
        "error_type": type(error).__name__,
        "error_message": str(error),
        "fresh_effect_seeds_consumed": False,
        "eligible_for_fresh_effect_card": False,
        "accepted_product_implementation": False,
        "eligible_for_separate_cheap_challenger_card": False,
        "claim_ceiling": CLAIM_CEILING,
        "producer_function": (
            "verify_ego_v2_additive_prediction_headroom_diagnostic_001c_r4."
            "write_blocked_output"
        ),
    }
    def populate(staging: Path) -> dict[str, Any]:
        _write_json(
            staging / "failure_manifest.json",
            {
                "verdict": BLOCKED_VERDICT,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "fresh_effect_seeds_consumed": False,
            },
        )
        _write_json(staging / "result.json", result)
        (staging / "claim_ceiling.txt").write_text(
            CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
        )
        return result

    return _publish_packet_atomically(
        output_dir,
        populate,
        expected_files=BLOCKED_ARTIFACT_FILES,
    )


def validate_output_target(output_dir: Path) -> None:
    resolved = output_dir.resolve()
    if resolved != CANONICAL_OUTPUT_DIR.resolve():
        raise OutputTargetRefusal(
            f"R4 output path must equal canonical path: {CANONICAL_OUTPUT_DIR}"
        )
    if resolved.exists():
        if not resolved.is_dir():
            raise OutputTargetRefusal(
                "R4 output path is not a directory; one-cycle gate refused without writes"
            )
        if any(resolved.iterdir()):
            raise OutputTargetRefusal(
                "R4 output directory is not empty; one-cycle gate refused without writes"
            )


def run_gate(output_dir: Path) -> dict[str, Any]:
    validate_output_target(output_dir)
    contract_manifest = collect_contract_manifest(require_clean=True)
    packet_tree_before = snapshot_packet_tree(SOURCE_PACKET)
    before = {name: hash_file(SOURCE_PACKET / name) for name in FROZEN_INPUTS}
    source_pins = verify_source_pins()
    input_manifest = verify_frozen_packet()
    try:
        report, leakage, source_manifest = _run_frozen_balanced()
    finally:
        after = {name: hash_file(SOURCE_PACKET / name) for name in FROZEN_INPUTS}
        packet_tree_after = snapshot_packet_tree(SOURCE_PACKET)
        if before != after or packet_tree_before != packet_tree_after:
            raise HeadroomDiagnosticError("frozen R2 packet was mutated")
    training_rows = list(report.pop("_headroom_training_rows"))
    import_receipt = validate_import_receipt(
        report.pop("_headroom_import_receipt"), source_manifest
    )
    recomputation = independent_recompute(
        report,
        training_rows,
        leakage=leakage,
        require_complete=True,
    )
    recomputation["fresh_subprocess_digest_exact"] = all(
        recomputation["checks"][name] is True
        for name in (
            "fresh_digest_expected_equals_actual",
            "row_recomputed_digest_matches_expected",
            "row_recomputed_digest_matches_actual",
        )
    )
    recomputation["source_packet_immutable"] = before == after
    recomputation["all_exact"] = bool(
        recomputation["all_exact"]
        and recomputation["fresh_subprocess_digest_exact"]
        and recomputation["source_packet_immutable"]
    )
    verdict = select_verdict(report, recomputation)
    successor_code_hash = canonical_hash(
        {
            "verifier_sha256": hash_file(Path(__file__).resolve()),
            "source_manifest": source_manifest,
            "contract_manifest": contract_manifest,
        }
    )
    frozen_inputs = [
        {"path": f"{SOURCE_TASK_ID}/{name}", "sha256": digest}
        for name, digest in FROZEN_INPUTS.items()
    ]
    prediction_status = {
        POSITIVE_VERDICT: "development_prediction_difference_under_frozen_R2_controls",
        NO_PREDICTION_DIFFERENCE_VERDICT: "not_observed",
        INSUFFICIENT_VERDICT: "insufficient_support",
        BLOCKED_VERDICT: "invalid",
    }[verdict]
    trace_rows: list[dict[str, Any]] = []
    for row in report["rows"]:
        trace_rows.append({"row_type": "balanced_prediction", **row})
    for row in report.get("legacy_rows", []):
        trace_rows.append({"row_type": "legacy_unconditional", **row})
    for mode, rows in report.get("hierarchical_ablation_rows", {}).items():
        for row in rows:
            trace_rows.append({"row_type": f"ablation:{mode}", **row})
    baseline_report = (
        provenance_receipt(
            "baseline_comparison",
            "same_snapshot_no_update_and_independent_legacy_unconditional",
            successor_code_hash,
            inputs=[{"path": "balanced_prediction_report.json"}],
        )
        | {
            "no_update": report["aggregate_metrics"]["no_update"],
            "legacy_unconditional": report["legacy_unconditional_metrics"],
            "outcome_stratified": report["outcome_stratified_metrics"],
            "cheap_challenger_stage": "required_separate_card_not_run",
        }
    )
    ablation_report = (
        provenance_receipt(
            "ablation_report",
            "base_only_residual_only_outcome_rotation_and_frozen_update_controls",
            successor_code_hash,
            inputs=[{"path": "balanced_prediction_report.json"}],
        )
        | {
            "hierarchical_ablations": report["hierarchical_ablation_metrics"],
            "frozen_update_controls": report["frozen_update_controls"],
        }
    )
    replay_report = (
        provenance_receipt(
            "replay_report",
            "frozen_subprocess_digest_plus_independent_row_metric_support_and_rank_recompute",
            successor_code_hash,
            inputs=[{"path": "trace.jsonl"}, {"path": "training_rows.jsonl"}],
        )
        | {
            "source_manifest": source_manifest,
            "materialized_import_receipt": import_receipt,
            "source_pins": source_pins,
            "pre_run_contract_manifest": contract_manifest,
            "frozen_balanced_expected": report["fresh_subprocess_digest_expected"],
            "frozen_balanced_actual": report["fresh_subprocess_digest_actual"],
            "independent_row_recomputation": recomputation,
        }
    )
    published_input_manifest = (
        provenance_receipt(
            "input_manifest",
            "exact_lineage_discontinuity_reconstruction_and_R2_packet_hash_binding",
            successor_code_hash,
            inputs=frozen_inputs,
        )
        | input_manifest
        | {
            "source_pins": source_pins,
            "materialized_import_receipt": import_receipt,
            "pre_run_contract_manifest": contract_manifest,
            "source_packet_hashes_before": before,
            "source_packet_hashes_after": after,
            "source_packet_tree_before": packet_tree_before,
            "source_packet_tree_after": packet_tree_after,
        }
    )
    failed = list(report.get("failed_checks", []))
    if not recomputation["all_exact"]:
        failed.append("independent_row_or_subprocess_recomputation_exact")
    result = {
        "task_id": TASK_ID,
        "verdict": verdict,
        "prediction_difference_status": prediction_status,
        "mechanism_headroom_status": "not_adjudicated_requires_cheap_challenger_stage",
        "product_sla_status": "BANKED_FAILED_R2",
        "frozen_r2_checks": report["checks"],
        "failed_checks": sorted(set(failed)),
        "independent_recomputation_all_exact": recomputation["all_exact"],
        "fresh_effect_seeds_consumed": False,
        "eligible_for_fresh_effect_card": False,
        "accepted_product_implementation": False,
        "eligible_for_separate_cheap_challenger_card": verdict == POSITIVE_VERDICT,
        "claim_ceiling": CLAIM_CEILING,
    } | provenance_receipt(
        "result",
        "frozen_R2_balanced_checks_then_independent_row_recomputation",
        successor_code_hash,
        inputs=frozen_inputs,
    )
    failure_manifest = (
        provenance_receipt(
            "failure_manifest",
            "all_frozen_and_independent_failed_checks_without_tuning",
            successor_code_hash,
            inputs=[{"path": "balanced_prediction_report.json"}, {"path": "replay_report.json"}],
        )
        | {"verdict": verdict, "failed_checks": result["failed_checks"]}
    )

    def populate(staging: Path) -> dict[str, Any]:
        _write_jsonl(staging / "trace.jsonl", trace_rows)
        _write_jsonl(staging / "training_rows.jsonl", training_rows)
        _write_json(staging / "balanced_prediction_report.json", report)
        _write_json(staging / "baseline_comparison.json", baseline_report)
        _write_json(staging / "ablation_report.json", ablation_report)
        _write_json(staging / "leakage_report.json", leakage)
        _write_json(staging / "replay_report.json", replay_report)
        _write_json(staging / "input_manifest.json", published_input_manifest)
        _write_json(staging / "failure_manifest.json", failure_manifest)
        _write_json(staging / "result.json", result)
        (staging / "claim_ceiling.txt").write_text(
            CLAIM_CEILING + "\n", encoding="utf-8", newline="\n"
        )
        return result

    return _publish_packet_atomically(
        output_dir,
        populate,
        expected_files=SUCCESS_ARTIFACT_FILES,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    output_dir = args.gate.resolve()
    try:
        validate_output_target(output_dir)
    except OutputTargetRefusal as error:
        print(
            canonical_json(
                {
                    "task_id": TASK_ID,
                    "verdict": BLOCKED_VERDICT,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "fresh_effect_seeds_consumed": False,
                    "eligible_for_fresh_effect_card": False,
                }
            )
        )
        return 1
    try:
        result = run_gate(output_dir)
    except Exception as error:  # fail closed into a machine-readable blocked packet
        result = write_blocked_output(output_dir, error)
    print(
        canonical_json(
            {
                "task_id": TASK_ID,
                "verdict": result["verdict"],
                "fresh_effect_seeds_consumed": False,
                "eligible_for_fresh_effect_card": False,
            }
        )
    )
    return 0 if result["verdict"] == POSITIVE_VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
