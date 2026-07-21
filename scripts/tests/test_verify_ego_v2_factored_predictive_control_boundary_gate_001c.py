from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from labs.ego_life_playground_v0 import engine, predictive_control  # noqa: E402
from labs.ego_life_playground_v0.controller import PlaygroundController  # noqa: E402
from labs.ego_life_playground_v0.store import SQLiteEventStore  # noqa: E402
from scripts.codex import (  # type: ignore[attr-defined]  # noqa: E402
    verify_ego_v2_factored_predictive_control_boundary_gate_001c as target,
)


ARTIFACT_DIR = REPO_ROOT / "artifacts" / target.TASK_ID
FIXTURE_PATH = ARTIFACT_DIR / target.FIXTURE_NAME


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _metric_prediction(
    *, true_outcome: str = "moved", energy: float = 0.1
) -> dict[str, object]:
    probabilities = {outcome: 0.0 for outcome in predictive_control.OUTCOMES}
    probabilities[true_outcome] = 0.75
    remaining = 0.25 / (len(probabilities) - 1)
    for outcome in probabilities:
        if outcome != true_outcome:
            probabilities[outcome] = remaining
    return {
        "outcome_probabilities": probabilities,
        "predicted_delta": {
            "energy": energy,
            "safety": 0.2,
            "connection": 0.3,
            "stimulation": 0.4,
        },
    }


def test_prechange_fixture_is_sealed_to_historical_commit_and_capture_refuses_overwrite(
    tmp_path,
):
    before = FIXTURE_PATH.read_bytes()
    receipt = target.verify_prechange_fixture(FIXTURE_PATH)

    assert receipt["source_commit"] == target.PRECHANGE_SOURCE_COMMIT
    assert receipt["source_commit"] == "a18771497a16f51aeba22fddb93f4ca7d266871c"
    assert receipt["fixture"]["bytes_equal_to_commit"] is True
    assert receipt["all_historical_paths_git_bound"] is True
    assert receipt["all_legacy_worktree_raw_sha_reproducible"] is False
    assert "mixed line endings" in receipt["provenance_limitation"]
    assert set(receipt["source_files"]) == set(_fixture()["input_source_hashes"])
    assert all(item["git_blob_id"] for item in receipt["source_files"].values())
    assert all(item["canonical_git_blob_sha256"] for item in receipt["source_files"].values())
    assert any(
        not item["legacy_worktree_raw_sha_reproducible"]
        for item in receipt["source_files"].values()
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(Path(target.__file__).resolve()),
            "--capture-baseline",
            "--output-dir",
            str(ARTIFACT_DIR),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert completed.returncode != 0
    assert "sealed pre-change fixture" in completed.stderr
    assert FIXTURE_PATH.read_bytes() == before
    assert not (tmp_path / target.FIXTURE_NAME).exists()


def test_cli_exposes_gate_and_private_modes_without_fresh_seed_surface():
    parser = target._build_parser()  # noqa: SLF001
    options = parser.format_help()
    assert "--gate" in options
    assert "--private-replay" in options
    assert "--private-evaluate" in options
    assert "--output-dir" in options
    assert "--world-seed" not in options
    assert "--policy-seed" not in options
    assert "--fresh-effect" not in options


def test_semantic_comparison_covers_all_204_actions_and_rejects_five_drift_types():
    fixture = _fixture()
    current = deepcopy(fixture["steps"])
    clean = target.compare_semantic_steps(fixture, current)
    assert clean["compared_action_steps"] == 204
    assert clean["all_exact_semantics_equal"] is True
    assert clean["max_abs_numeric_difference"] == 0.0

    mutations = (
        ("selected_action", lambda step: step.__setitem__("selected_action", "rest")),
        (
            "world_transition",
            lambda step: step["world_transition"].__setitem__("outcome_type", "rested"),
        ),
        (
            "candidate_values",
            lambda step: step["candidate_values"]["rest"].__setitem__(
                "total", step["candidate_values"]["rest"]["total"] + 0.01
            ),
        ),
        (
            "action_exposure_counts",
            lambda step: step["action_exposure_counts"].__setitem__(
                "rest", step["action_exposure_counts"]["rest"] + 1
            ),
        ),
        (
            "beam_receipt",
            lambda step: step["beam_receipt"]["expanded_by_depth"].__setitem__(
                0, step["beam_receipt"]["expanded_by_depth"][0] + 1
            ),
        ),
    )
    for expected_field, mutate in mutations:
        altered = deepcopy(current)
        mutate(altered[0])
        report = target.compare_semantic_steps(fixture, altered)
        assert report["all_exact_semantics_equal"] is False or report[
            "max_abs_numeric_difference"
        ] > 1e-12
        assert any(expected_field in item["field"] for item in report["differences"])


def test_smoke_thresholds_are_exact_and_balanced_is_blocked(monkeypatch, tmp_path):
    passing_run = {
        "dispatch_p95_seconds": 0.250,
        "dispatch_max_seconds": 0.500,
        "duration_tail_ratio": 1.999999,
        "recovery_attempts": [
            {"recover_run_seconds": 10.0, "exact": True},
            {"recover_run_seconds": 9.0, "exact": True},
            {"recover_run_seconds": 8.0, "exact": True},
        ],
        "trace_mean_bytes": 32768.0,
        "trace_max_bytes": 65536,
        "sqlite_and_sidecar_bytes": 20 * 1024 * 1024,
        "row_readbacks_verified": True,
        "all_recovery_surfaces_exact": True,
        "all_tamper_controls_rejected": True,
        "single_path_scan_passed": True,
        "semantic_equivalence_passed": True,
    }
    checks = target.compute_smoke_checks([passing_run, deepcopy(passing_run)])
    assert all(checks.values())

    failing_run = deepcopy(passing_run)
    failing_run["dispatch_p95_seconds"] = math.nextafter(0.250, math.inf)
    smoke_payload = {
        "runs": [failing_run, deepcopy(passing_run)],
        "checks": target.compute_smoke_checks([failing_run, deepcopy(passing_run)]),
    }
    called = False

    def fake_smoke(*_args, **_kwargs):
        return smoke_payload

    def forbidden_balanced(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("balanced evaluator ran after a smoke failure")

    monkeypatch.setattr(target, "run_old_smoke", fake_smoke)
    monkeypatch.setattr(target, "run_balanced_evaluation", forbidden_balanced)
    result = target.run_gate(tmp_path)
    assert called is False
    assert result["verdict"] == "BOUNDARY_REPAIR_FAILED"
    assert result["balanced_prediction_status"] == "not_run_boundary_failed"
    assert result["effect_gate_eligibility"] is False


def test_five_action_evaluator_calls_product_predictor_and_truth_without_feedback(
    monkeypatch,
):
    prepared = predictive_control.empty_state()
    snapshot = {
        "context_id": "p0_cross_v1:world=52:policy=711",
        "run_id": "bounded",
        "seed": 711,
        "world_seed": 52,
        "life": 1,
        "phase": "early",
        "sequence": 1,
        "episode_id": "episode-0",
        "command_hash": "0" * 64,
        "predictive_state": prepared,
        "observation": {
            "schema_version": "ego.life_playground.microworld.observation.v4",
            "visual": [["empty"] * 5 for _ in range(5)],
        },
        "organism": {
            "energy": 0.5,
            "safety": 0.5,
            "connection": 0.5,
            "stimulation": 0.5,
        },
        "world": {"sentinel": "original"},
        "root_prediction_hashes": {action: "ignored" for action in engine.ACTIONS},
        "skip_root_hash_check": True,
    }
    calls = {"predict": [], "world": [], "metabolism": [], "delta": []}

    def fake_predict(state, *, observation, organism, action, relative_map_mode):
        calls["predict"].append((action, id(state["model"])))
        return _metric_prediction()

    def fake_transition(world, action, **_kwargs):
        calls["world"].append((action, deepcopy(world)))
        return {"sentinel": action}, {"outcome_type": "moved"}

    def fake_metabolism(**kwargs):
        calls["metabolism"].append(kwargs["selected_action"])
        return {"energy_delta": -0.01, "food_gain": 0.0}

    def fake_delta(transition, *, selected_action):
        calls["delta"].append(selected_action)
        return {
            "energy": 999.0,
            "safety": 0.2,
            "connection": 0.3,
            "stimulation": 0.4,
        }

    monkeypatch.setattr(target.predictive_control, "predict_action", fake_predict)
    monkeypatch.setattr(target, "transition_world", fake_transition)
    monkeypatch.setattr(target.engine, "compute_metabolism_ledger", fake_metabolism)
    monkeypatch.setattr(target.engine, "compute_actual_delta", fake_delta)

    rows = target.evaluate_balanced_snapshots([snapshot])
    assert len(rows) == len(engine.ACTIONS) * 2
    assert all(row["context_id"] == snapshot["context_id"] for row in rows)
    assert [item[0] for item in calls["predict"]] == list(engine.ACTIONS) * 2
    assert calls["world"] == [(action, {"sentinel": "original"}) for action in engine.ACTIONS]
    assert calls["metabolism"] == list(engine.ACTIONS)
    assert calls["delta"] == list(engine.ACTIONS)
    assert all(row["truth"]["actual_delta"]["energy"] == -0.01 for row in rows)
    assert snapshot["world"] == {"sentinel": "original"}
    assert snapshot["predictive_state"] == prepared


def test_no_update_evaluator_is_independent_zero_model(monkeypatch):
    learned = predictive_control.empty_state()
    learned["model"]["update_count"] = 9
    learned["model"]["outcome_weights"][0][0][0] = 1.25
    observed_models: list[dict[str, object]] = []

    def fake_predict(state, **_kwargs):
        observed_models.append(deepcopy(state["model"]))
        return _metric_prediction()

    monkeypatch.setattr(target.predictive_control, "predict_action", fake_predict)
    predictions = target.evaluate_no_update_predictions(
        learned,
        observation={"schema_version": "x", "visual": []},
        organism={key: 0.5 for key in predictive_control.STATE_KEYS},
    )
    assert set(predictions) == set(engine.ACTIONS)
    assert len(observed_models) == len(engine.ACTIONS)
    assert all(model["update_count"] == 0 for model in observed_models)
    assert all(model["outcome_weights"][0][0][0] == 0.0 for model in observed_models)
    assert all(model is not learned["model"] for model in observed_models)
    assert learned["model"]["update_count"] == 9
    assert learned["model"]["outcome_weights"][0][0][0] == 1.25


def test_brier_nll_delta_mae_and_equal_macro_aggregation_are_numeric():
    prediction = _metric_prediction(true_outcome="moved", energy=0.1)
    truth = {
        "outcome_type": "moved",
        "actual_delta": {
            "energy": 0.0,
            "safety": 0.0,
            "connection": 0.0,
            "stimulation": 0.0,
        },
    }
    score = target.score_prediction(prediction, truth)
    expected_brier = (0.75 - 1.0) ** 2 + 5 * (0.05**2)
    assert score["outcome_brier"] == pytest.approx(expected_brier)
    assert score["outcome_nll"] == pytest.approx(-math.log(0.75))
    assert score["delta_mae"] == pytest.approx((0.1 + 0.2 + 0.3 + 0.4) / 4)

    rows = []
    for context in ("a", "b"):
        for action_index, action in enumerate(engine.ACTIONS):
            rows.append(
                {
                    "context_id": context,
                    "phase": "late",
                    "action": action,
                    "model": "learned",
                    "scores": {
                        "outcome_brier": float(action_index),
                        "outcome_nll": float(action_index + 1),
                        "delta_mae": float(action_index + 2),
                    },
                }
            )
            if context == "a" and action == "turn_left":
                rows.append(deepcopy(rows[-1]))  # longer cell must not get extra weight
    aggregate = target.aggregate_balanced_metrics(rows)
    assert aggregate["cell_count"] == 10
    assert aggregate["outcome_brier"] == pytest.approx(2.0)
    assert aggregate["outcome_nll"] == pytest.approx(3.0)
    assert aggregate["delta_mae"] == pytest.approx(4.0)


def test_leakage_scanner_clean_and_five_independent_positive_controls():
    clean = {
        "belief_summary": {
            "front_token": "v0",
            "known_cell_count": 1,
            "known_object_count": 0,
        },
        "organism": {key: 0.5 for key in predictive_control.STATE_KEYS},
    }
    report = target.run_leakage_controls(clean)
    assert report["clean_scan"]["clean"] is True
    assert report["all_positive_controls_detected"] is True
    assert set(report["positive_controls"]) == {
        "global_position",
        "cause",
        "token_mapping",
        "seed",
        "future_observation",
    }
    assert all(item["detected"] for item in report["positive_controls"].values())


def test_four_sqlite_tamper_controls_rehash_and_recovery_rejects_each(tmp_path):
    db_path = tmp_path / "source.sqlite3"
    run_id = "001c-tamper-positive-control"
    interventions = dict(
        engine.DEFAULT_INTERVENTIONS,
        predictive_control_mode="factored_mpc",
    )
    with SQLiteEventStore(db_path) as store:
        controller = PlaygroundController(
            store,
            run_id=run_id,
            seed=711,
            world_seed=52,
            layout_id="p0_cross_v1",
        )
        dispatched = controller.dispatch(interventions, trigger_source="ui_run_button")
        assert dispatched.receipt.committed

    report = target.run_tamper_controls(db_path, run_id, tmp_path / "tampered")
    assert set(report) == {
        "command",
        "predictive_model_hash",
        "plan_prediction",
        "update_receipt",
    }
    assert all(item["rehashed"] for item in report.values())
    assert all(item["rejected"] for item in report.values())


def test_update_trace_renderer_visibility_and_schema_pins_are_current():
    assert engine.STATE_SCHEMA_VERSION == "ego.life_playground.state.v8"
    assert engine.RUN_SCHEMA_VERSION == "ego.life_playground.run.v8"
    assert engine.TRACE_SCHEMA_VERSION == "ego.life_playground.trace.v13"
    assert engine.compute_code_path_manifest()["schema_version"] == "ego.life_playground.code_path.v9"

    source = (REPO_ROOT / "labs/ego_life_playground_v0/engine.py").read_text(
        encoding="utf-8"
    )
    assert '"update": _compact_predictive_update(predictive_update)' in source
    assert '"selected_action_update": _compact_predictive_update' not in source
    focused = (
        REPO_ROOT / "tests/test_ego_v2_factored_predictive_control_boundary_gate_001c.py"
    ).read_text(encoding="utf-8")
    assert 'ui_payload["predictive_control"]["update"]' in focused
