from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    REPO_ROOT
    / "scripts"
    / "codex"
    / "verify_ego_v2_predictive_replay_kernel_repair_001f.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_001f", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_source_scan_binds_predictor_and_single_product_path():
    module = _load_module()

    report = module.source_path_scan()

    assert report["passed"] is True
    assert any(
        item["path"].endswith("predictive_control.py")
        for item in report["input_artifacts"]
    )
    assert report["checks"]["predictive_control_bound_once"] is True


def test_boundary_checks_require_every_frozen_threshold():
    module = _load_module()
    passing = {
        "fresh_recoveries": [
            {"seconds": 9.99, "exact": True},
            {"seconds": 9.50, "exact": True},
            {"seconds": 8.75, "exact": True},
        ],
        "trace_mean_bytes": 32768.0,
        "trace_max_bytes": 65536,
        "dispatch_p95_seconds": 0.25,
        "dispatch_max_seconds": 0.5,
        "row_readbacks_verified": True,
        "tamper_controls_passed": True,
        "source_path_scan_passed": True,
        "scalar_trace_rows_exact": True,
        "scalar_final_state_exact": True,
    }

    assert all(module.boundary_checks(passing).values())
    for key, value in (
        ("trace_mean_bytes", 32768.000001),
        ("trace_max_bytes", 65537),
        ("dispatch_p95_seconds", 0.250001),
        ("dispatch_max_seconds", 0.500001),
    ):
        failed = deepcopy(passing)
        failed[key] = value
        assert not all(module.boundary_checks(failed).values())


def test_sqlite_row_comparison_is_byte_exact_and_detects_one_mutation(tmp_path: Path):
    module = _load_module()
    left = tmp_path / "left.sqlite3"
    right = tmp_path / "right.sqlite3"
    for path in (left, right):
        connection = sqlite3.connect(path)
        connection.executescript(
            "CREATE TABLE commands(sequence INTEGER, command_json TEXT);"
            "CREATE TABLE traces(sequence INTEGER, trace_json TEXT);"
        )
        connection.execute("INSERT INTO commands VALUES(1, ?)", (json.dumps({"a": 1}),))
        connection.execute("INSERT INTO traces VALUES(1, ?)", (json.dumps({"b": 2}),))
        connection.commit()
        connection.close()

    exact = module.compare_sqlite_rows(left, right)
    assert exact["command_rows_exact"] is True
    assert exact["trace_rows_exact"] is True

    connection = sqlite3.connect(right)
    connection.execute("UPDATE traces SET trace_json = ?", (json.dumps({"b": 3}),))
    connection.commit()
    connection.close()
    changed = module.compare_sqlite_rows(left, right)
    assert changed["command_rows_exact"] is True
    assert changed["trace_rows_exact"] is False


def test_result_verdict_fails_closed_on_one_context_failure():
    module = _load_module()
    reports = [
        {"checks": {"a": True, "b": True}},
        {"checks": {"a": True, "b": False}},
    ]

    assert module.result_verdict(reports) == "BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION"
    assert module.result_verdict([{"checks": {"a": True}}]) == (
        "PREDICTIVE_REPLAY_KERNEL_BOUNDARY_REPAIRED"
    )

