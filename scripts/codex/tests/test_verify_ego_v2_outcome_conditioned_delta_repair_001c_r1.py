from __future__ import annotations

import pytest

from labs.ego_life_playground_v0 import engine, predictive_control
from scripts.codex import verify_ego_v2_outcome_conditioned_delta_repair_001c_r1 as verifier


def test_seed_boundary_has_no_fresh_effect_overlap() -> None:
    assert verifier.ALLOWED_WORLD_SEEDS == {52, 54}
    assert verifier.ALLOWED_POLICY_SEEDS == {711}
    assert not (verifier.ALLOWED_WORLD_SEEDS & verifier.FORBIDDEN_WORLD_SEEDS)
    assert not (verifier.ALLOWED_POLICY_SEEDS & verifier.FORBIDDEN_POLICY_SEEDS)
    parser = verifier._build_parser()  # noqa: SLF001
    with pytest.raises(SystemExit):
        parser.parse_args(["--world-seed", "60"])


def test_outcome_agnostic_ablation_is_callable_and_changes_prediction() -> None:
    conditional = {
        outcome: {
            key: float(outcome_index + state_index) / 100.0
            for state_index, key in enumerate(engine.STATE_KEYS)
        }
        for outcome_index, outcome in enumerate(predictive_control.OUTCOMES)
    }
    learned = {
        "run_id": "unit",
        "context_id": "p0_cross_v1:world=52:policy=711",
        "phase": "late",
        "sequence": 9,
        "action": "interact",
        "prediction": {
            "conditional_delta_by_outcome": conditional,
            "predicted_delta": {key: -1.0 for key in engine.STATE_KEYS},
        },
        "truth": {"actual_delta": {key: 0.0 for key in engine.STATE_KEYS}},
    }

    rows = verifier._outcome_agnostic_rows([learned])  # noqa: SLF001

    assert len(rows) == 1
    expected_energy = sum(
        conditional[outcome]["energy"] for outcome in predictive_control.OUTCOMES
    ) / len(predictive_control.OUTCOMES)
    assert rows[0]["predicted_delta"]["energy"] == pytest.approx(expected_energy)
    assert rows[0]["producer_function"].endswith("._outcome_agnostic_rows")
    assert rows[0]["code_path_hash"]


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
