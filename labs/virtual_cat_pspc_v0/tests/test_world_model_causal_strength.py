from labs.virtual_cat_pspc_v0.experiments import run_world_model_causal_strength


def test_world_model_causal_strength_orders_normal_frozen_shuffled_random():
    audit = run_world_model_causal_strength(seed=101)

    assert audit["status"] == "pass"
    assert audit["variants"] == ["normal", "frozen", "shuffled", "random"]
    scores = audit["planner_support_scores"]
    assert scores["normal"] > scores["frozen"]
    assert scores["frozen"] > scores["shuffled"]
    assert scores["frozen"] > scores["random"]
    assert scores["normal"] - scores["frozen"] > 0.50
    assert scores["frozen"] - max(scores["shuffled"], scores["random"]) > 0.05
    assert audit["ordering"] == "normal > frozen > shuffled/random"
    assert audit["what_it_proves"] == (
        "Replacing the learned world model with frozen, shuffled, or random baselines degrades "
        "planner support under the same self model and target set."
    )
    assert "does not prove world-model causal strength outside this lab target set" in audit["what_it_does_not_prove"]


def test_world_model_causal_strength_records_variant_predictions_and_trace_refs():
    audit = run_world_model_causal_strength(seed=102)

    for variant in audit["variants"]:
        record = audit["variant_records"][variant]
        assert record["danger"]["trace_hash"]
        assert record["safe"]["trace_hash"]
        assert "world_prediction" in record["danger"]
        assert "world_prediction" in record["safe"]
        assert "selected_action" in record["danger"]
        assert "selected_action" in record["safe"]
        assert "prediction_error" in record["danger"]
        assert "prediction_error" in record["safe"]
