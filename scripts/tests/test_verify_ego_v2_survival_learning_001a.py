from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "codex" / "verify_ego_v2_survival_learning_001a.py"


def _load_verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_ego_v2_survival_learning_001a", SCRIPT
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_predeclared_context_matrix_is_exact_and_unique() -> None:
    verifier = _load_verifier()
    contexts = verifier.declared_contexts()

    assert len(contexts) == 12
    assert len({item["context_id"] for item in contexts}) == 12
    assert {(item["layout_id"], item["world_seed"]) for item in contexts} == {
        ("p0_cross_v1", 30),
        ("p0_cross_v1", 31),
        ("p2_vertical_v1", 42),
        ("p2_vertical_v1", 43),
        ("p2_offset_v1", 44),
        ("p2_offset_v1", 45),
    }
    assert {item["policy_seed"] for item in contexts} == {701, 702}


def test_leakage_scanner_fires_on_hidden_position_positive_control() -> None:
    verifier = _load_verifier()
    clean = {"policy_observation_hash": "a" * 64, "energy_milli": 450}

    assert verifier.scan_state_key_inputs([clean])["offenders"] == []
    positive = verifier.scan_state_key_inputs([{**clean, "position": [4, 2]}])
    assert len(positive["offenders"]) == 1
    assert "schema" in positive["offenders"][0]["error"]


def test_callable_no_update_run_consumes_all_sixteen_lives() -> None:
    verifier = _load_verifier()
    result = verifier.simulate_context(
        {**verifier.declared_contexts()[0], "control_id": "no_update"}
    )

    assert result["control_id"] == "no_update"
    assert len(result["life_results"]) == 16
    assert result["update_count"] == 0
    assert result["state_key_input_keys"] == [
        "energy_milli",
        "policy_observation_hash",
    ]
    assert len(result["first_command_hash"]) == 64
    assert len(result["product_code_path_hash"]) == 64


def test_mainline_sqlite_and_resource_boundaries_are_computed(tmp_path: Path) -> None:
    verifier = _load_verifier()

    sqlite = verifier._sqlite_report(tmp_path)
    resource = verifier._resource_boundary_report()
    source = verifier._source_path_report()

    assert sqlite["value"] is True
    assert sqlite["trigger_source"] == "ui_run_button"
    assert sqlite["td_trace_tamper_rejected"] is True
    assert sqlite["initial_q_tamper_rejected"] is True
    assert resource["value"] is True
    assert resource["forged_no_object_resource_rejected"] is True
    assert resource["exception_type"] == "EngineInvariantError"
    assert source["value"] is True
