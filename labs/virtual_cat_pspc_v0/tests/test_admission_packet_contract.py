import ast
from pathlib import Path

from labs.virtual_cat_pspc_v0.admission_packet import (
    ADMISSION_PACKET_SCHEMA,
    build_admission_packet,
    validate_admission_packet,
)


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


def test_admission_packet_contract_has_no_egooperator_import_or_adapter_file():
    module_path = Path("labs/virtual_cat_pspc_v0/admission_packet.py")
    adapter_path = Path("EgoOperator/adapters/pspc_lab_adapter.py")

    assert not adapter_path.exists()
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
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
    assert not any(name.startswith("EgoOperator") for name in imports)
