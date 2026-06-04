from labs.virtual_cat_pspc_v0.experiments import run_anti_hardcoding_audit


def test_anti_hardcoding_audit_survives_object_rename_and_feature_deletion():
    audit = run_anti_hardcoding_audit(seed=211)

    assert audit["object_name_rule_hits"] == []
    assert audit["baseline_unstable"]["selected_action"] in {"observe", "retreat"}
    assert audit["renamed_object_a"]["selected_action"] == audit["baseline_unstable"]["selected_action"]
    assert audit["renamed_object_b"]["selected_action"] == audit["baseline_unstable"]["selected_action"]
    assert audit["unstable_tall_object_without_cup_name"]["selected_action"] in {"observe", "retreat"}
    assert audit["instability_feature_removed"]["caution_score"] < (
        audit["baseline_unstable"]["caution_score"] - 0.20
    )
    assert audit["what_it_proves"] == (
        "Object renaming does not change the cautious decision, while removing the instability feature "
        "reduces cautious behavior in this deterministic lab audit."
    )
    assert "does not prove absence of every possible shortcut" in audit["what_it_does_not_prove"]
