from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_pspc_disabled_runtime_flag_contract.py"


def load_runner_module():
    assert RUNNER_PATH.exists(), "disabled runtime flag contract runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_disabled_runtime_flag_contract", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_flag_contract_defaults_to_false_and_no_authority():
    runner = load_runner_module()

    contract = runner.build_flag_contract(requested_value=False)
    validation = runner.validate_flag_contract(contract)

    assert validation["ok"] is True
    assert contract["flag_name"] == "PSPC_SHADOW_OBSERVATION_LOCAL"
    assert contract["default_value"] is False
    assert contract["admitted_runtime_value"] is False
    assert contract["enabled"] is False
    assert contract["mainline_connected"] is False
    assert contract["runtime_authority"] == "none"
    assert contract["audit_only"] is True
    assert contract["read_only"] is True
    assert contract["non_executable"] is True
    assert all(value is False for value in contract["side_effects"].values())


def test_requested_true_remains_artifact_only():
    runner = load_runner_module()

    contract = runner.build_flag_contract(requested_value=True)
    artifact = runner.build_flag_true_shadow_artifact(contract)

    assert runner.validate_flag_contract(contract)["ok"] is True
    assert contract["requested_value"] is True
    assert contract["admitted_runtime_value"] is False
    assert artifact["requested_value"] is True
    assert artifact["admitted_runtime_value"] is False
    assert artifact["artifact_output_written"] is True
    assert artifact["runtime_output_mutated"] is False
    assert artifact["audit_only"] is True
    assert artifact["read_only"] is True
    assert artifact["non_executable"] is True
    assert runner.runtime_field_hits(artifact["shadow_observation"]) == []
    assert all(value is False for value in artifact["side_effects"].values())


def test_invalid_contracts_are_rejected():
    runner = load_runner_module()

    contract = runner.build_flag_contract(requested_value=False)
    contract["default_value"] = True
    contract["enabled"] = True
    contract["mainline_connected"] = True
    contract["runtime_authority"] = "proposal"
    contract["can_write_memory"] = True
    contract["side_effects"]["memory_written"] = True

    validation = runner.validate_flag_contract(contract)

    assert validation["ok"] is False
    assert "default_value_must_be_false" in validation["errors"]
    assert "enabled_must_be_false" in validation["errors"]
    assert "mainline_connected_must_be_false" in validation["errors"]
    assert "runtime_authority_must_be_none" in validation["errors"]
    assert "can_write_memory_must_be_false" in validation["errors"]
    assert "side_effects_must_all_be_false" in validation["errors"]


def test_active_runtime_sources_do_not_import_register_or_branch_on_flag():
    runner = load_runner_module()

    scan = runner.scan_active_runtime_sources(ROOT)

    assert scan["ok"] is True
    assert scan["offenders"] == []
    assert scan["scanned_file_count"] > 0


def test_disabled_runtime_flag_contract_runner_passes(tmp_path):
    runner = load_runner_module()

    result = runner.run_flag_contract_review(ROOT, tmp_path)

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / disabled_runtime_flag_contract_only"
    assert result["next_allowed_step"] == "local_manual_shadow_session_harness_only"
    assert all(result["checks"].values())
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "DISABLED_RUNTIME_FLAG_CONTRACT_REPORT.md",
        "disabled_runtime_flag_contract.json",
    ]
    report = (tmp_path / "DISABLED_RUNTIME_FLAG_CONTRACT_REPORT.md").read_text(encoding="utf-8")
    assert "What This Proves" in report
    assert "What This Does Not Prove" in report
    assert "Rollback" in report
    assert "Failure Meaning" in report
