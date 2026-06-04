from labs.virtual_cat_pspc_v0.experiments import run_self_model_causal_strength


def test_self_model_causal_strength_orders_head_ablations():
    audit = run_self_model_causal_strength(seed=101)

    assert audit["status"] == "pass"
    assert audit["variants"] == [
        "normal",
        "frozen",
        "stress_removed",
        "ability_removed",
        "affinity_removed",
    ]
    assert audit["ordering"] == "normal > frozen/head-removed"

    risk_scores = audit["risk_control_scores"]
    assert risk_scores["normal"] > risk_scores["frozen"]
    assert risk_scores["normal"] > risk_scores["stress_removed"]
    assert risk_scores["normal"] - risk_scores["stress_removed"] > 0.20

    ability_scores = audit["ability_planning_scores"]
    assert ability_scores["normal"] > ability_scores["ability_removed"]
    assert ability_scores["normal"] - ability_scores["ability_removed"] > 0.20

    relationship_scores = audit["relationship_preference_scores"]
    assert relationship_scores["normal"] > relationship_scores["affinity_removed"]
    assert relationship_scores["normal"] - relationship_scores["affinity_removed"] > 0.20

    records = audit["variant_records"]
    assert records["normal"]["risk_control"]["selected_action"] in {"observe", "retreat"}
    assert records["frozen"]["risk_control"]["selected_action"] == "approach"
    assert records["normal"]["ability_planning"]["selected_action"] in {"observe", "retreat"}
    assert records["ability_removed"]["ability_planning"]["selected_action"] == "approach"
    assert records["normal"]["relationship_preference"]["selected_action"] in {"observe", "retreat"}
    assert records["affinity_removed"]["relationship_preference"]["selected_action"] == "approach"

    assert "stress/risk, ability, and affinity" in audit["what_it_proves"]
    assert "does not prove self-model causal strength outside this lab target set" in audit["what_it_does_not_prove"]


def test_self_model_causal_strength_records_predictions_and_trace_refs():
    audit = run_self_model_causal_strength(seed=102)

    for variant in audit["variants"]:
        record = audit["variant_records"][variant]
        for task in ["risk_control", "ability_planning", "relationship_preference"]:
            task_record = record[task]
            assert task_record["trace_hash"]
            assert "selected_action" in task_record
            assert "world_prediction" in task_record
            assert "self_prediction" in task_record
            assert "homeostatic_score" in task_record
