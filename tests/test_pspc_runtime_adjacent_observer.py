from __future__ import annotations

import importlib.util
import re
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
OBSERVER_PATH = ROOT / "EgoOperator" / "adapters" / "pspc_runtime_adjacent_observer.py"
RUNNER_PATH = ROOT / "scripts" / "run_pspc_runtime_adjacent_observer.py"


def load_observer_module():
    assert OBSERVER_PATH.exists(), "runtime-adjacent observer must exist"
    spec = importlib.util.spec_from_file_location("pspc_runtime_adjacent_observer", OBSERVER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_runner_module():
    assert RUNNER_PATH.exists(), "observer runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_runtime_adjacent_observer", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def boundary_result():
    return load_runner_module().load_json(
        ROOT, Path("artifacts") / "pspc_runtime_trace_fixture_boundary_v0" / "runtime_trace_fixture_boundary.json"
    )


def test_observer_defaults_are_disabled_and_no_authority():
    module = load_observer_module()
    observer = module.PSPCRuntimeAdjacentObserver()

    assert observer.enabled is False
    assert observer.mainline_connected is False
    assert observer.runtime_authority == "none"
    assert observer.mode == "runtime_adjacent_audit_only"
    assert observer.side_effects_allowed is False
    observer.assert_no_runtime_authority()


def test_observer_assertion_rejects_enabled_or_mainline_connected():
    module = load_observer_module()

    enabled = module.PSPCRuntimeAdjacentObserver()
    enabled.enabled = True
    with pytest.raises(RuntimeError, match="enabled_must_be_false"):
        enabled.assert_no_runtime_authority()

    connected = module.PSPCRuntimeAdjacentObserver()
    connected.mainline_connected = True
    with pytest.raises(RuntimeError, match="mainline_connected_must_be_false"):
        connected.assert_no_runtime_authority()


def test_observer_validates_fixture_boundary_artifact():
    module = load_observer_module()
    observer = module.PSPCRuntimeAdjacentObserver()

    validation = observer.validate_fixture_boundary(boundary_result())

    assert validation == {"ok": True, "errors": []}


def test_observer_rejects_runtime_connected_or_executable_fixture():
    module = load_observer_module()
    observer = module.PSPCRuntimeAdjacentObserver()
    payload = boundary_result()

    connected = deepcopy(payload)
    connected["shadow_trace"]["runtime_connected"] = True
    assert "shadow_trace.runtime_connected_must_be_false" in observer.validate_fixture_boundary(connected)["errors"]

    executable = deepcopy(payload)
    executable["shadow_trace"]["non_executable"] = False
    assert "shadow_trace.non_executable_must_be_true" in observer.validate_fixture_boundary(executable)["errors"]

    side_effect = deepcopy(payload)
    side_effect["shadow_trace"]["side_effects"]["memory_written"] = True
    assert "shadow_trace.side_effects_must_all_be_false" in observer.validate_fixture_boundary(side_effect)["errors"]


def test_observer_rejects_runtime_authority_fields_in_audit_observation():
    module = load_observer_module()
    observer = module.PSPCRuntimeAdjacentObserver()
    payload = boundary_result()
    payload["shadow_trace"]["audit_observation"]["gate_decision"] = "allow"

    errors = observer.validate_fixture_boundary(payload)["errors"]

    assert any("audit_observation_has_runtime_authority_fields" in error for error in errors)


def test_observer_outputs_audit_only_non_executable_data():
    module = load_observer_module()
    observer = module.PSPCRuntimeAdjacentObserver()

    observation = observer.to_audit_observation(boundary_result())

    assert observation["source"] == "pspc_runtime_adjacent_observer_v0"
    assert observation["enabled"] is False
    assert observation["mainline_connected"] is False
    assert observation["runtime_authority"] == "none"
    assert observation["non_executable"] is True
    assert observation["audit_only"] is True
    assert observation["audit_observation"]["can_drive_runtime"] is False
    assert observation["audit_observation"]["can_change_user_response"] is False
    assert observation["audit_observation"]["can_write_memory"] is False
    assert observation["audit_observation"]["can_invoke_gate"] is False
    assert all(value is False for value in observation["side_effects"].values())
    assert observation["forbidden_mutations"]["runtime_registry"] is True
    assert observation["forbidden_mutations"]["memory"] is True
    assert observation["forbidden_mutations"]["gate_decision"] is True


def test_observer_runner_writes_only_artifacts(tmp_path):
    runner = load_runner_module()

    result = runner.run_observer(ROOT, tmp_path)

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / default_off_observer_only"
    assert result["observer"]["enabled"] is False
    assert result["observer"]["mainline_connected"] is False
    assert result["observer"]["runtime_authority"] == "none"
    assert result["runtime_behavior_unchanged"] is True
    assert result["next_allowed_step"] == "recorded_trace_replay_no_diff_only"
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "RUNTIME_ADJACENT_OBSERVER_REPORT.md",
        "runtime_adjacent_observer.json",
    ]


def test_observer_and_runner_have_no_runtime_imports_or_side_effect_calls():
    for path in (OBSERVER_PATH, RUNNER_PATH):
        source = path.read_text(encoding="utf-8") if path.exists() else ""
        banned = [
            "EgoOperator.agent_base",
            "agent_base",
            "memory_system",
            "real_use_gate",
            "human_operator_trial",
            "operator_comparison",
            "runtime_gate",
            "send_message",
            "write_memory",
            "select_action",
            "register_runtime",
            "invoke_gate",
            "run_planner",
            "train_model",
        ]
        for item in banned:
            assert not re.search(rf"^\s*(from|import)\s+.*{re.escape(item)}", source, flags=re.MULTILINE)
            assert not re.search(rf"\b{re.escape(item)}\s*\(", source)


def test_runtime_sources_still_do_not_import_or_register_observer():
    runtime_sources = [
        path
        for path in (ROOT / "EgoOperator").rglob("*.py")
        if "adapters" not in path.parts and "tests" not in path.parts
    ]
    assert runtime_sources

    offenders = []
    markers = [
        "pspc_runtime_adjacent_observer",
        "PSPCRuntimeAdjacentObserver",
        "pspc_runtime_adjacent",
        "PSPCRuntime",
    ]
    for path in runtime_sources:
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in markers):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
