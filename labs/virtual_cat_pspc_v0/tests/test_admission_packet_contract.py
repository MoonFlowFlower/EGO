import ast
from pathlib import Path
from typing import Any

from labs.virtual_cat_pspc_v0.admission_packet import (
    ADMISSION_PACKET_SCHEMA,
    build_admission_packet,
    validate_admission_packet,
)


ROOT = Path(__file__).resolve().parents[3]
ADMISSION_PACKET_PATH = ROOT / "labs" / "virtual_cat_pspc_v0" / "admission_packet.py"
ADAPTER_PATH = ROOT / "EgoOperator" / "adapters" / "pspc_lab_adapter.py"

REQUIRED_ADAPTER_FORBIDDEN_FLAGS = {
    "direct_action",
    "direct_user_message",
    "direct_memory_write",
    "runtime_gate_bypass",
    "runtime_registration",
    "proactive_trigger",
}
REQUIRED_FORBIDDEN_PACKET_FIELDS = {
    "action",
    "tool_call",
    "command",
    "user_message",
    "message_text",
    "memory_write",
    "memory_patch",
    "gate_decision",
    "approval_id",
    "transport",
    "send",
    "schedule",
}


def egooperator_imports_in(source: str) -> list[str]:
    tree = ast.parse(source)
    imports = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    imports.extend(
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    return [name for name in imports if name.startswith("EgoOperator")]


def _literal_value(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return tuple(_literal_value(element) for element in node.elts)
    return None


def _module_assignment_map(tree: ast.Module) -> dict[str, Any]:
    assignments: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        value = _literal_value(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                assignments[target.id] = value
    return assignments


def _class_assignment_map(tree: ast.Module, class_name: str, constants: dict[str, Any]) -> dict[str, Any]:
    class_node = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name),
        None,
    )
    if class_node is None:
        return {"__missing_class__": class_name}
    assignments: dict[str, Any] = {}
    for node in class_node.body:
        if not isinstance(node, ast.Assign):
            continue
        value = _literal_value(node.value)
        if value is None and isinstance(node.value, ast.Name):
            value = constants.get(node.value.id)
        for target in node.targets:
            if isinstance(target, ast.Name):
                assignments[target.id] = value
    return assignments


def inert_fact_violations(facts: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    if facts.get("adapter_status") != "disabled_read_only":
        violations.append("adapter_status_must_be_disabled_read_only")
    if facts.get("enabled") is not False:
        violations.append("enabled_must_be_false")
    if facts.get("mainline_connected") is not False:
        violations.append("mainline_connected_must_be_false")
    if facts.get("runtime_authority") != "none":
        violations.append("runtime_authority_must_be_none")
    forbidden_flags = set(facts.get("required_forbidden_flags") or ())
    missing_flags = REQUIRED_ADAPTER_FORBIDDEN_FLAGS - forbidden_flags
    if missing_flags:
        violations.append(f"missing_required_forbidden_flags:{','.join(sorted(missing_flags))}")
    forbidden_fields = set(facts.get("forbidden_packet_fields") or ())
    missing_fields = REQUIRED_FORBIDDEN_PACKET_FIELDS - forbidden_fields
    if missing_fields:
        violations.append(f"missing_forbidden_packet_fields:{','.join(sorted(missing_fields))}")
    runtime_registration_refs = list(facts.get("runtime_registration_refs") or ())
    if runtime_registration_refs:
        violations.append(f"runtime_registration_refs:{','.join(runtime_registration_refs)}")
    adapter_imports = list(facts.get("adapter_egooperator_imports") or ())
    if adapter_imports:
        violations.append(f"adapter_egooperator_imports:{','.join(adapter_imports)}")
    return violations


def adapter_facts_from_source(
    source: str,
    *,
    runtime_registration_refs: list[str] | None = None,
) -> dict[str, Any]:
    tree = ast.parse(source)
    constants = _module_assignment_map(tree)
    class_assignments = _class_assignment_map(tree, "PSPCLabAdapter", constants)
    return {
        "adapter_status": constants.get("ADAPTER_STATUS"),
        "enabled": class_assignments.get("enabled"),
        "mainline_connected": class_assignments.get("mainline_connected"),
        "runtime_authority": class_assignments.get("runtime_authority"),
        "required_forbidden_flags": constants.get("REQUIRED_FORBIDDEN_FLAGS") or (),
        "forbidden_packet_fields": constants.get("FORBIDDEN_PACKET_FIELDS") or (),
        "runtime_registration_refs": runtime_registration_refs or [],
        "adapter_egooperator_imports": egooperator_imports_in(source),
    }


def _active_runtime_sources() -> list[Path]:
    return [
        path
        for path in sorted((ROOT / "EgoOperator").rglob("*.py"))
        if "adapters" not in path.parts
        and "tests" not in path.parts
        and "__pycache__" not in path.parts
    ]


def runtime_registration_refs_for_pspc_adapter() -> list[str]:
    refs: list[str] = []
    for path in _active_runtime_sources():
        text = path.read_text(encoding="utf-8")
        if "pspc_lab_adapter" in text or "PSPCLabAdapter" in text:
            refs.append(path.relative_to(ROOT).as_posix())
    return refs


def test_admission_packet_contract_accepts_canonical_proposal_packet():
    packet = build_admission_packet(
        suggested_tendency="avoid_unstable_object",
        confidence=0.73,
        trace_refs=["trace_ep_003_t42"],
        world_prediction={"danger_contact": 0.91},
        self_prediction={"damage_risk": 0.78},
        homeostatic_score={"safety": -0.16, "total": -0.44},
        ablation_status="E4_passed",
    )

    assert packet == {
        "source": "virtual_cat_pspc_v0",
        "claim_level": "lab_only_proto_self_mechanism_candidate",
        "mainline_connected": False,
        "enabled": False,
        "proposal": {
            "suggested_tendency": "avoid_unstable_object",
            "confidence": 0.73,
            "trace_refs": ["trace_ep_003_t42"],
        },
        "evidence": {
            "world_prediction": {"danger_contact": 0.91},
            "self_prediction": {"damage_risk": 0.78},
            "homeostatic_score": {"safety": -0.16, "total": -0.44},
            "ablation_status": "E4_passed",
        },
        "forbidden": {
            "direct_action": True,
            "direct_user_message": True,
            "direct_memory_write": True,
            "runtime_gate_bypass": True,
        },
    }
    assert validate_admission_packet(packet) == []
    assert ADMISSION_PACKET_SCHEMA["required"] == [
        "source",
        "claim_level",
        "mainline_connected",
        "enabled",
        "proposal",
        "evidence",
        "forbidden",
    ]


def test_admission_packet_contract_rejects_runtime_authority_or_adapter_shape():
    invalid_packet = {
        "source": "virtual_cat_pspc_v0",
        "claim_level": "lab_only_proto_self_mechanism_candidate",
        "mainline_connected": True,
        "enabled": False,
        "proposal": {
            "suggested_tendency": "avoid_unstable_object",
            "confidence": 1.2,
            "reason_trace_refs": ["legacy_field"],
        },
        "evidence": {
            "world_prediction": {},
            "self_prediction": {},
            "homeostatic_score": {},
            "ablation_status": "E4_passed",
        },
        "forbidden": {
            "direct_action": True,
            "direct_user_message": True,
            "direct_memory_write": True,
            "runtime_gate_bypass": False,
        },
    }

    errors = validate_admission_packet(invalid_packet)

    assert "mainline_connected must be false" in errors
    assert "proposal.trace_refs is required" in errors
    assert "proposal.reason_trace_refs is forbidden; use trace_refs" in errors
    assert "proposal.confidence must be between 0.0 and 1.0" in errors
    assert "forbidden.runtime_gate_bypass must be true" in errors


def test_admission_packet_contract_preserves_lab_isolation_and_inert_adapter_if_present():
    assert egooperator_imports_in(ADMISSION_PACKET_PATH.read_text(encoding="utf-8")) == []

    if ADAPTER_PATH.exists():
        adapter_facts = adapter_facts_from_source(
            ADAPTER_PATH.read_text(encoding="utf-8"),
            runtime_registration_refs=runtime_registration_refs_for_pspc_adapter(),
        )
        assert inert_fact_violations(adapter_facts) == []


def test_negative_control_adapter_runtime_import_or_registration_fails():
    synthetic_adapter = """
from __future__ import annotations

import EgoOperator.agent_base

ADAPTER_STATUS = "disabled_read_only"
RUNTIME_AUTHORITY = "none"
REQUIRED_FORBIDDEN_FLAGS = (
    "direct_action",
    "direct_user_message",
    "direct_memory_write",
    "runtime_gate_bypass",
    "runtime_registration",
    "proactive_trigger",
)
FORBIDDEN_PACKET_FIELDS = (
    "action",
    "tool_call",
    "command",
    "user_message",
    "message_text",
    "memory_write",
    "memory_patch",
    "gate_decision",
    "approval_id",
    "transport",
    "send",
    "schedule",
)

class PSPCLabAdapter:
    enabled = False
    mainline_connected = False
    runtime_authority = RUNTIME_AUTHORITY
"""
    violations = inert_fact_violations(
        adapter_facts_from_source(
            synthetic_adapter,
            runtime_registration_refs=["EgoOperator/agent_base.py"],
        )
    )

    assert any(violation.startswith("adapter_egooperator_imports:") for violation in violations)
    assert any(violation.startswith("runtime_registration_refs:") for violation in violations)


def test_negative_control_non_inert_adapter_facts_fail():
    violations = inert_fact_violations(
        {
            "adapter_status": "enabled_runtime",
            "enabled": True,
            "mainline_connected": True,
            "runtime_authority": "runtime_gate",
            "required_forbidden_flags": REQUIRED_ADAPTER_FORBIDDEN_FLAGS,
            "forbidden_packet_fields": REQUIRED_FORBIDDEN_PACKET_FIELDS,
            "runtime_registration_refs": [],
            "adapter_egooperator_imports": [],
        }
    )

    assert "adapter_status_must_be_disabled_read_only" in violations
    assert "enabled_must_be_false" in violations
    assert "mainline_connected_must_be_false" in violations
    assert "runtime_authority_must_be_none" in violations


def test_negative_control_lab_admission_packet_egooperator_import_fails():
    imports = egooperator_imports_in("from EgoOperator.x import y")

    assert imports == ["EgoOperator.x"]
