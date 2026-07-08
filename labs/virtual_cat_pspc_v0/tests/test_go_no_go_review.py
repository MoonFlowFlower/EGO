from labs.virtual_cat_pspc_v0.admission_review import (
    GO_CRITERIA,
    REQUIRED_ADAPTER_FORBIDDEN_FLAGS,
    REQUIRED_FORBIDDEN_PACKET_FIELDS,
    adapter_contract_facts_from_source,
    run_go_no_go_review,
)


def _passing_summary():
    return {
        "anti_hardcoding_status": "pass",
        "multi_seed_layout_generalization_status": "pass",
        "world_model_causal_strength_status": "pass",
        "self_model_causal_strength_status": "pass",
        "memory_consolidation_admission_status": "pass",
        "homeostatic_value_anti_hacking_status": "pass",
        "admission_packet_contract_status": "pass",
        "mainline_connected": False,
        "enabled": False,
        "repo_wide_evidence_remains": "E3",
        "gates": {
            "danger_generalization": True,
            "frozen_world_model": True,
            "frozen_self_model": True,
            "memory_deletion": True,
        },
    }


def _inert_adapter_contract():
    return {
        "adapter_status": "disabled_read_only",
        "enabled": False,
        "mainline_connected": False,
        "runtime_authority": "none",
        "required_forbidden_flags": sorted(REQUIRED_ADAPTER_FORBIDDEN_FLAGS),
        "forbidden_packet_fields": sorted(REQUIRED_FORBIDDEN_PACKET_FIELDS),
        "runtime_registration_refs": [],
        "adapter_egooperator_imports": [],
    }


def test_go_no_go_review_goes_only_for_separate_read_only_adapter_design():
    review = run_go_no_go_review(summary=_passing_summary(), adapter_exists=False)

    assert review["status"] == "go"
    assert review["verdict"] == "go_for_separate_read_only_adapter_design_review_only"
    assert len(review["go_conditions"]) == len(GO_CRITERIA)
    assert all(condition["status"] == "pass" for condition in review["go_conditions"])
    assert review["no_go_triggers"] == []
    assert review["scope_limits"]["adapter_created"] is False
    assert review["scope_limits"]["ego_operator_runtime_change_allowed"] is False
    assert review["scope_limits"]["repo_wide_claim_ceiling_change_allowed"] is False
    assert "future read-only adapter design" in review["what_it_proves"]
    assert "does not prove adapter readiness" in review["what_it_does_not_prove"]
    assert review["provenance"]["producer_function"] == (
        "labs.virtual_cat_pspc_v0.admission_review.run_go_no_go_review"
    )
    assert review["provenance"]["aggregation_rule"] == "all_go_conditions_pass_and_no_no_go_triggers"


def test_go_no_go_review_blocks_if_core_condition_fails():
    summary = _passing_summary()
    summary["world_model_causal_strength_status"] = "hold"

    review = run_go_no_go_review(summary=summary, adapter_exists=False)

    assert review["status"] == "no_go"
    assert review["verdict"] == "no_go_for_adapter_design"
    assert "world_model_ablation_not_passed" in review["no_go_triggers"]
    failed = [condition for condition in review["go_conditions"] if condition["id"] == "world_model_ablation_passed"]
    assert failed[0]["status"] == "fail"


def test_go_no_go_review_allows_sanctioned_inert_adapter_if_present():
    review = run_go_no_go_review(
        summary=_passing_summary(),
        adapter_exists=True,
        adapter_contract=_inert_adapter_contract(),
    )

    assert review["status"] == "go"
    assert review["verdict"] == "go_for_separate_read_only_adapter_design_review_only"
    assert review["no_go_triggers"] == []
    assert review["scope_limits"]["adapter_created"] is True
    assert review["scope_limits"]["adapter_contract_status"] == "pass"


def test_go_no_go_review_blocks_if_existing_adapter_contract_is_missing():
    review = run_go_no_go_review(summary=_passing_summary(), adapter_exists=True)

    assert review["status"] == "no_go"
    assert review["verdict"] == "no_go_for_adapter_design"
    assert "adapter_contract_missing_for_existing_adapter" in review["no_go_triggers"]


def test_go_no_go_review_blocks_if_adapter_non_inert():
    adapter_contract = _inert_adapter_contract()
    adapter_contract.update(
        {
            "adapter_status": "enabled_runtime",
            "enabled": True,
            "mainline_connected": True,
            "runtime_authority": "runtime_gate",
        }
    )

    review = run_go_no_go_review(
        summary=_passing_summary(),
        adapter_exists=True,
        adapter_contract=adapter_contract,
    )

    assert review["status"] == "no_go"
    assert "adapter_contract_violation:adapter_status_must_be_disabled_read_only" in review["no_go_triggers"]
    assert "adapter_contract_violation:enabled_must_be_false" in review["no_go_triggers"]
    assert "adapter_contract_violation:mainline_connected_must_be_false" in review["no_go_triggers"]
    assert "adapter_contract_violation:runtime_authority_must_be_none" in review["no_go_triggers"]


def test_go_no_go_review_blocks_lab_import_or_runtime_registration():
    adapter_contract = _inert_adapter_contract()
    adapter_contract["runtime_registration_refs"] = ["EgoOperator/agent_base.py"]

    review = run_go_no_go_review(
        summary=_passing_summary(),
        adapter_exists=True,
        adapter_contract=adapter_contract,
        lab_egooperator_import_refs=["labs/virtual_cat_pspc_v0/admission_review.py:EgoOperator.agent_base"],
    )

    assert review["status"] == "no_go"
    assert "lab_imports_egooperator" in review["no_go_triggers"]
    assert any(
        trigger.startswith("adapter_contract_violation:runtime_registration_refs:")
        for trigger in review["no_go_triggers"]
    )


def test_go_no_go_review_blocks_missing_side_effect_field_guards():
    adapter_contract = _inert_adapter_contract()
    adapter_contract["forbidden_packet_fields"] = []

    review = run_go_no_go_review(
        summary=_passing_summary(),
        adapter_exists=True,
        adapter_contract=adapter_contract,
    )

    assert review["status"] == "no_go"
    assert any(
        trigger.startswith("adapter_contract_violation:missing_forbidden_packet_fields:")
        for trigger in review["no_go_triggers"]
    )


def test_adapter_contract_facts_from_source_extracts_static_inert_contract():
    source = """
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
    "operator_memory_update",
    "gate_decision",
    "approval_id",
    "preapproved",
    "transport",
    "send",
    "schedule",
    "enable",
    "mainline_authority",
    "consciousness_claim",
    "subjective_experience_claim",
)

class PSPCLabAdapter:
    enabled = False
    mainline_connected = False
    runtime_authority = RUNTIME_AUTHORITY
"""

    facts = adapter_contract_facts_from_source(source)

    assert facts["adapter_status"] == "disabled_read_only"
    assert facts["enabled"] is False
    assert facts["mainline_connected"] is False
    assert facts["runtime_authority"] == "none"
    assert set(facts["required_forbidden_flags"]) == REQUIRED_ADAPTER_FORBIDDEN_FLAGS
    assert set(facts["forbidden_packet_fields"]) == REQUIRED_FORBIDDEN_PACKET_FIELDS
