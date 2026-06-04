from labs.virtual_cat_pspc_v0.experiments import (
    build_candidate_object,
    run_condition,
    run_replay_pair,
)


def test_different_histories_produce_different_future_behavior():
    target = build_candidate_object()

    danger = run_condition(seed=101, history="danger", target=target)
    safe = run_condition(seed=101, history="safe", target=target)

    assert danger.selected_action in {"observe", "retreat"}
    assert safe.selected_action == "approach"
    assert danger.caution_score > safe.caution_score + 0.20


def test_memory_deletion_regresses_cautious_behavior():
    target = build_candidate_object()

    baseline = run_condition(seed=102, history="danger", target=target)
    deleted = run_condition(seed=102, history="danger", target=target, delete_relevant_memory=True)

    assert baseline.selected_action in {"observe", "retreat"}
    assert deleted.selected_action == "approach"
    assert baseline.caution_score > deleted.caution_score + 0.20


def test_frozen_world_model_degrades_prediction_and_planning():
    target = build_candidate_object()

    baseline = run_condition(seed=103, history="danger", target=target)
    frozen = run_condition(seed=103, history="danger", target=target, freeze_world_model=True)

    assert baseline.world_prediction_error < frozen.world_prediction_error
    assert baseline.caution_score > frozen.caution_score + 0.20


def test_frozen_self_model_degrades_risk_judgment():
    target = build_candidate_object()

    baseline = run_condition(seed=104, history="danger", target=target)
    frozen = run_condition(seed=104, history="danger", target=target, freeze_self_model=True)

    assert baseline.self_risk_score > frozen.self_risk_score + 0.20
    assert baseline.selected_action != frozen.selected_action


def test_no_prediction_error_learning_blocks_learning_effect():
    target = build_candidate_object()

    baseline = run_condition(seed=105, history="danger", target=target)
    no_learning = run_condition(seed=105, history="danger", target=target, disable_prediction_error_learning=True)

    assert baseline.world_prediction_error < no_learning.world_prediction_error
    assert baseline.caution_score > no_learning.caution_score + 0.20


def test_same_seed_and_state_replay_same_decision_digest():
    first, second = run_replay_pair(seed=106)

    assert first.selected_action == second.selected_action
    assert first.trace_hash == second.trace_hash
