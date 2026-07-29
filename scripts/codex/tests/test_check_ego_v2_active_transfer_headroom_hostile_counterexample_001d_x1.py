from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[3]
PRIMARY_PATH = REPO / "scripts/codex/check_ego_v2_active_transfer_headroom_hostile_counterexample_001d_x1.py"
INDEPENDENT_PATH = REPO / "scripts/codex/recompute_ego_v2_active_transfer_headroom_hostile_counterexample_001d_x1.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing module: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def primary():
    return _load(PRIMARY_PATH, "ego_x1_primary")


@pytest.fixture(scope="module")
def independent():
    return _load(INDEPENDENT_PATH, "ego_x1_independent")


def test_authority_and_independent_import_boundary(primary, independent):
    receipts = primary.validate_authority()
    assert len(receipts) == 10
    assert all(row["matches_expected"] for row in receipts)

    tree = ast.parse(INDEPENDENT_PATH.read_text(encoding="utf-8-sig"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert not any("active_transfer_headroom_preflight_001d" in name for name in imported)
    assert not any("hostile_counterexample" in name for name in imported)
    assert independent.TASK_ID == primary.TASK_ID


def test_independent_primitives_and_hash00_match(primary, independent):
    assert independent.round_half_even(1, 2) == 0
    assert independent.round_half_even(3, 2) == 2
    assert independent.round_half_even(-3, 2) == -2
    assert independent.weighted_median_endpoints([0, 10], [1, 1]) == (0, 5, 10)

    i1 = primary.load_i1_verified()
    expected = i1.build_hash_bank(0)
    assert independent.build_hash_bank_zero() == expected
    assert len(expected) == 6
    assert len(set(expected)) == 6


def test_all_360_rows_match_separate_implementation(primary, independent):
    primary_payload = primary.build_primary_evidence()
    independent_payload = independent.build_independent_evidence()
    comparison = primary.compare_evidence(primary_payload, independent_payload)

    assert comparison["passed"] is True
    assert comparison["row_count"] == 360
    assert comparison["first_mismatch"] is None
    assert primary_payload["bank_sha256"] == independent_payload["bank_sha256"]
    assert primary_payload["aggregate"] == independent_payload["aggregate"]


@pytest.mark.parametrize(
    "mutation",
    ["bank", "selected_query", "rational", "classification", "threshold"],
)
def test_tamper_controls_fail_closed(primary, independent, mutation):
    left = primary.build_primary_evidence()
    right = independent.build_independent_evidence()
    broken = copy.deepcopy(right)
    if mutation == "bank":
        broken["bank"][0][0], broken["bank"][0][1] = broken["bank"][0][1], broken["bank"][0][0]
    elif mutation == "selected_query":
        broken["rows"][0]["metric"]["selected_query_token"] = 4
    elif mutation == "rational":
        broken["rows"][0]["metric"]["metric_rationals"]["full_endpoint_improvement"] = {"n": 999, "d": 1}
    elif mutation == "classification":
        broken["rows"][0]["classification"]["distance"] = 5
    elif mutation == "threshold":
        broken["thresholds"]["member_full_improvement_min"] = {"n": 0, "d": 1}
    with pytest.raises(ValueError, match="independent evidence mismatch"):
        primary.compare_evidence(left, broken)


def test_formal_packet_replay_and_artifact_manifest(primary, tmp_path):
    out = tmp_path / "packet"
    result = primary.run_formal(out)
    assert result["task_id"] == primary.TASK_ID
    assert result["fresh_process_replay_equal"] is True
    assert result["independent_recompute_equal"] is True

    required = {
        "result.json",
        "trace.jsonl",
        "baseline_comparison.json",
        "ablation_report.json",
        "replay_report.json",
        "claim_ceiling.txt",
        "input_manifest.json",
        "independent_recompute_report.json",
        "artifact_manifest.json",
    }
    assert required <= {path.name for path in out.iterdir()}
    manifest = json.loads((out / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["files"]) == {path.name for path in out.iterdir()} - {"artifact_manifest.json"}
    primary.verify_artifact_packet(out)

    with pytest.raises(ValueError, match="output directory must be absent"):
        primary.run_formal(out)


def test_result_dispatch_is_computed_and_not_literal(primary, independent):
    left = primary.build_primary_evidence()
    right = independent.build_independent_evidence()
    comparison = primary.compare_evidence(left, right)
    verdict = primary.dispatch_verdict(left["aggregate"], comparison)
    assert verdict in {
        "FROZEN_PRIMARY_POSITIVE_GATE_FALSIFIED_BY_COUNTEREXAMPLE",
        "HASH00_CONSERVATIVE_GATE_SURVIVES_X1",
    }
    synthetic = copy.deepcopy(left["aggregate"])
    synthetic["conservative"]["member_and_forward"] = True
    synthetic["conservative"]["bounded_safety"] = True
    assert primary.dispatch_verdict(synthetic, comparison) == "HASH00_CONSERVATIVE_GATE_SURVIVES_X1"


def test_no_world_seed_or_free_form_science_input(primary):
    parser = primary.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--world", "60"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--seed", "721"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--target", "0,1,2,3,4"])
