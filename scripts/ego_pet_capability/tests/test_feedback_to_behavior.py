from __future__ import annotations

from pathlib import Path

from scripts.ego_pet_capability.feedback_to_behavior import (
    PROBE_SEED,
    SCORED_SEEDS,
    _derived_designations,
    assert_seed_disjointness,
    load_world_config,
    rng_audit,
    run_pair_bundle_for_seed,
    run_phase,
)


def test_derived_designations_match_frozen_config() -> None:
    config = load_world_config()
    designations = _derived_designations(config)
    assert designations["R0_pre_shift"] == {"energy": "bowl", "comfort": "mat"}
    assert designations["R1_shift_a"] == {"energy": "sun_patch", "comfort": "perch"}
    assert designations["R2_shift_b"] == {"energy": "corner_bowl", "comfort": "blanket"}


def test_seed_disjointness_fail_closed() -> None:
    assert_seed_disjointness(SCORED_SEEDS)
    try:
        assert_seed_disjointness([PROBE_SEED])
    except ValueError as exc:
        assert "seed-disjointness assertion failed" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected seed-disjointness failure")


def test_probe_bundle_has_candidate_observe_events_and_control_zero_ga() -> None:
    config = load_world_config()
    bundle = run_pair_bundle_for_seed(config, seed=PROBE_SEED, run_id="unit_probe")
    observe_events = [event for event in bundle["events"] if event["event_kind"] == "observe"]
    assert [event["tick_index"] for event in observe_events] == [0, 201, 401]
    static_records = [
        record
        for record in bundle["metric_records"]
        if record["arm"] == "static" and record["event_kind"] == "observe" and record["gate_scope"] == "post_drift_observe"
    ]
    assert static_records
    assert sum(record["ab_divergence_count"] for record in static_records) == 0


def test_probe_phase_without_replay_is_deterministic_and_artifact_free(tmp_path: Path) -> None:
    first = run_phase(phase="probe", out_dir=tmp_path / "a", include_replay=False, write_artifacts=False)
    second = run_phase(phase="probe", out_dir=tmp_path / "b", include_replay=False, write_artifacts=False)
    assert first["gate_results"]["G-A/G-B"]["by_arm"] == second["gate_results"]["G-A/G-B"]["by_arm"]
    assert not (tmp_path / "a").exists()
    assert not (tmp_path / "b").exists()


def test_rng_audit_positive_control_detects_forbidden_random(tmp_path: Path) -> None:
    offender = tmp_path / "offender.py"
    offender.write_text("import random\nvalue = random.random()\n", encoding="utf-8")
    report = rng_audit(code_hash="unit", run_id="unit", scan_files=[offender])
    assert report["status"] == "fail"
    assert report["forbidden_hits"]

