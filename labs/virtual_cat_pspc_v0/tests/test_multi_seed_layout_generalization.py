from labs.virtual_cat_pspc_v0.experiments import run_generalization_matrix


def test_generalization_matrix_covers_multiple_seeds_layouts_and_unstable_objects():
    matrix = run_generalization_matrix(
        seeds=[101, 102],
        layout_ids=["center_room", "near_wall"],
        object_kinds=["cup", "vase", "bottle", "tall_box"],
    )

    assert matrix["status"] == "pass"
    assert matrix["case_count"] == 16
    assert matrix["seeds"] == [101, 102]
    assert matrix["layout_ids"] == ["center_room", "near_wall"]
    assert matrix["object_kinds"] == ["cup", "vase", "bottle", "tall_box"]
    assert matrix["danger_caution_mean"] > matrix["safe_caution_mean"] + 0.20
    assert matrix["min_caution_gap"] > 0.20
    assert matrix["danger_action_rate"] == 1.0
    assert matrix["what_it_proves"] == (
        "Danger-history caution stays above safe-history baseline across the configured seeds, "
        "layouts, and unstable object kinds."
    )
    assert "does not prove unlimited layout generalization" in matrix["what_it_does_not_prove"]


def test_generalization_cases_record_layout_and_object_kind_in_trace():
    matrix = run_generalization_matrix(
        seeds=[101],
        layout_ids=["center_room"],
        object_kinds=["tall_box"],
    )

    case = matrix["cases"][0]
    assert case["seed"] == 101
    assert case["layout_id"] == "center_room"
    assert case["object_kind"] == "tall_box"
    assert case["danger"]["selected_action"] in {"observe", "retreat"}
    assert case["safe"]["selected_action"] == "approach"
    assert case["danger"]["trace_payload"]["layout_id"] == "center_room"
    assert case["danger"]["trace_payload"]["object_kind"] == "tall_box"
