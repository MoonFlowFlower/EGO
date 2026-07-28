from __future__ import annotations

import pytest

from labs.ego_life_playground_v0 import engine, predictive_control
from scripts.codex import verify_ego_v2_hierarchical_outcome_delta_repair_001c_r2 as verifier


def test_seed_boundary_has_no_fresh_effect_overlap() -> None:
    assert verifier.ALLOWED_WORLD_SEEDS == {52, 54}
    assert verifier.ALLOWED_POLICY_SEEDS == {711}
    assert not (verifier.ALLOWED_WORLD_SEEDS & verifier.FORBIDDEN_WORLD_SEEDS)
    assert not (verifier.ALLOWED_POLICY_SEEDS & verifier.FORBIDDEN_POLICY_SEEDS)
    parser = verifier._build_parser()  # noqa: SLF001
    with pytest.raises(SystemExit):
        parser.parse_args(["--world-seed", "60"])


def test_base_only_ablation_is_callable_and_changes_prediction() -> None:
    predictive_state = predictive_control.empty_state()
    action_index = predictive_control.ACTION_INDEX["interact"]
    interacted_index = predictive_control.OUTCOME_INDEX["interacted"]
    no_object_index = predictive_control.OUTCOME_INDEX["no_object"]
    predictive_state["model"]["delta_outcome_offsets"][action_index][interacted_index][0] = 0.2
    predictive_state["model"]["delta_outcome_offsets"][action_index][no_object_index][0] = -0.2
    observation = {
        "schema_version": predictive_control.PUBLIC_OBSERVATION_SCHEMA_VERSION,
        "visual": [
            ["occluded"] * 5,
            ["occluded", "occluded", "empty", "occluded", "occluded"],
            ["occluded", "empty", "self", "empty", "occluded"],
            ["occluded", "occluded", "empty", "occluded", "occluded"],
            ["occluded"] * 5,
        ],
    }
    predictive_state, _ = predictive_control.observe_belief(
        predictive_state,
        observation=observation,
        episode_index=0,
        mode="relative",
    )
    learned = {
        "run_id": "unit",
        "context_id": "p0_cross_v1:world=52:policy=711",
        "snapshot_hash": "snapshot-1",
        "phase": "late",
        "sequence": 9,
        "action": "interact",
        "truth": {
            "outcome_type": "interacted",
            "actual_delta": {key: 0.0 for key in engine.STATE_KEYS},
        },
    }
    snapshot = {
        "snapshot_hash": "snapshot-1",
        "predictive_state": predictive_state,
        "observation": observation,
        "organism": {
            "energy": 0.45,
            "safety": 0.62,
            "connection": 0.50,
            "stimulation": 0.43,
        },
    }

    rows = verifier._model_ablation_rows(  # noqa: SLF001
        [learned], [snapshot], mode="base_only"
    )

    assert len(rows) == 1
    assert rows[0]["predicted_delta"]["energy"] == pytest.approx(0.0)
    assert rows[0]["outcome_type"] == "interacted"
    assert rows[0]["producer_function"].endswith("._model_ablation_rows")
    assert rows[0]["code_path_hash"]


def test_stratified_delta_refuses_under_supported_macro() -> None:
    rows = [
        {
            "action": "interact",
            "outcome_type": "interacted",
            "delta_mae": 0.1,
        }
    ] * (verifier.MIN_STRATUM_SUPPORT - 1)

    report = verifier._stratified_delta(rows)  # noqa: SLF001

    assert report["strata"]["interact::interacted"]["estimable"] is False
    assert report["all_strata_estimable"] is False
    assert report["macro_delta_mae"] is None


def test_delta_aggregation_macro_averages_context_action_cells() -> None:
    rows = [
        {"context_id": "a", "action": "rest", "delta_mae": 0.0},
        {"context_id": "a", "action": "rest", "delta_mae": 0.2},
        {"context_id": "b", "action": "interact", "delta_mae": 0.4},
    ]

    aggregate = verifier._aggregate_delta(rows)  # noqa: SLF001

    assert aggregate["cell_count"] == 2
    assert aggregate["delta_mae"] == pytest.approx(0.25)


def test_boundary_checks_fail_on_runtime_or_replay_regression() -> None:
    run = {
        "dispatch_p95_seconds": 0.251,
        "dispatch_max_seconds": 0.2,
        "duration_tail_ratio": 1.0,
        "recovery_attempts": [
            {"recover_run_seconds": 1.0, "exact": True},
            {"recover_run_seconds": 1.0, "exact": True},
            {"recover_run_seconds": 1.0, "exact": True},
        ],
        "trace_mean_bytes": 100,
        "trace_max_bytes": 200,
        "sqlite_and_sidecar_bytes": 300,
        "row_readbacks_verified": True,
        "all_recovery_surfaces_exact": True,
        "all_tamper_controls_rejected": True,
        "single_path_scan_passed": True,
    }

    checks = verifier._boundary_checks([run])  # noqa: SLF001

    assert checks["dispatch_p95_at_most_250ms"] is False
    assert all(
        passed
        for name, passed in checks.items()
        if name != "dispatch_p95_at_most_250ms"
    )
