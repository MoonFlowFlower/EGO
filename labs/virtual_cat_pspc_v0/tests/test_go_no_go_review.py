from labs.virtual_cat_pspc_v0.admission_review import GO_CRITERIA, run_go_no_go_review


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


def test_go_no_go_review_blocks_if_core_condition_fails():
    summary = _passing_summary()
    summary["world_model_causal_strength_status"] = "hold"

    review = run_go_no_go_review(summary=summary, adapter_exists=False)

    assert review["status"] == "no_go"
    assert review["verdict"] == "no_go_for_adapter_design"
    assert "world_model_ablation_not_passed" in review["no_go_triggers"]
    failed = [condition for condition in review["go_conditions"] if condition["id"] == "world_model_ablation_passed"]
    assert failed[0]["status"] == "fail"


def test_go_no_go_review_blocks_if_adapter_already_exists():
    review = run_go_no_go_review(summary=_passing_summary(), adapter_exists=True)

    assert review["status"] == "no_go"
    assert review["verdict"] == "no_go_for_adapter_design"
    assert "adapter_already_created_in_wrong_phase" in review["no_go_triggers"]
