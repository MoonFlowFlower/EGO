from labs.virtual_cat_pspc_v0.experiments import run_memory_consolidation_admission


def test_memory_consolidation_admission_distinguishes_relevant_irrelevant_and_corrupted_memory():
    audit = run_memory_consolidation_admission(seed=101)

    assert audit["status"] == "pass"
    assert audit["variants"] == [
        "normal",
        "relevant_deleted",
        "irrelevant_deleted",
        "corrupted_relevant",
    ]

    records = audit["variant_records"]
    normal = records["normal"]
    relevant_deleted = records["relevant_deleted"]
    irrelevant_deleted = records["irrelevant_deleted"]
    corrupted = records["corrupted_relevant"]

    assert normal["semantic_rule_candidate"]["admission_status"] == "admitted"
    assert normal["semantic_rule_candidate"]["evidence_count"] >= 2
    assert normal["semantic_rule_candidate"]["trace_refs"]
    assert normal["selected_action"] in {"observe", "retreat"}

    assert relevant_deleted["semantic_rule_candidate"]["admission_status"] == "no_relevant_memory"
    assert relevant_deleted["deleted_memory_count"] > 0
    assert relevant_deleted["selected_action"] == "approach"
    assert audit["relevant_deletion_regression"] > 0.20

    assert irrelevant_deleted["semantic_rule_candidate"]["admission_status"] == "admitted"
    assert irrelevant_deleted["deleted_memory_count"] > 0
    assert irrelevant_deleted["selected_action"] == normal["selected_action"]
    assert audit["irrelevant_deletion_delta"] <= 0.05

    assert corrupted["semantic_rule_candidate"]["admission_status"] == "admitted"
    assert corrupted["corrupted_memory_count"] > 0
    assert corrupted["selected_action"] == "approach"
    assert audit["corrupted_memory_bias"]["direction"] == "unsafe_risk_underestimate"
    assert audit["corrupted_memory_bias"]["normal_approach_danger"] > audit["corrupted_memory_bias"]["corrupted_approach_danger"]

    assert "semantic rule candidate" in audit["what_it_proves"]
    assert "does not prove durable memory consolidation outside this lab audit" in audit["what_it_does_not_prove"]


def test_memory_consolidation_admission_records_trace_refs_and_gate_packet():
    audit = run_memory_consolidation_admission(seed=102)

    for variant in audit["variants"]:
        record = audit["variant_records"][variant]
        assert record["trace_hash"]
        assert "selected_action" in record
        assert "world_prediction" in record
        assert "self_prediction" in record
        assert "semantic_rule_candidate" in record
        assert "admission_gate" in record
