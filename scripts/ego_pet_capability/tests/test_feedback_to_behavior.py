from __future__ import annotations

from pathlib import Path

from scripts.ego_pet_capability.feedback_to_behavior import (
    DIRECTIONAL_INJECTION_MAP,
    InstrumentInvalidError,
    PROBE_SEED,
    SCORED_SEEDS,
    _derived_designations,
    assert_seed_disjointness,
    directional_delta_report,
    load_world_config,
    rng_audit,
    run_pair_bundle_for_seed,
    run_phase,
    validate_directional_injection_map,
)


def test_derived_designations_match_frozen_config() -> None:
    config = load_world_config()
    designations = _derived_designations(config)
    assert designations["R0_pre_shift"] == {"energy": "bowl", "comfort": "mat"}
    assert designations["R1_shift_a"] == {"energy": "sun_patch", "comfort": "perch"}
    assert designations["R2_shift_b"] == {"energy": "corner_bowl", "comfort": "blanket"}


def test_seed_disjointness_fail_closed() -> None:
    assert_seed_disjointness(SCORED_SEEDS)
    assert PROBE_SEED == 1106
    for reserved_seed in (1101, 2101, 3101):
        try:
            assert_seed_disjointness([reserved_seed])
        except InstrumentInvalidError as exc:
            assert "seed-disjointness assertion failed" in str(exc)
        else:  # pragma: no cover
            raise AssertionError(f"expected seed-disjointness failure for {reserved_seed}")


def test_directional_injection_map_rejects_old_r2_to_r0_and_accepts_repair() -> None:
    config = load_world_config()
    repaired = validate_directional_injection_map(config, DIRECTIONAL_INJECTION_MAP)
    assert repaired["status"] == "pass"
    assert repaired["injection_map"]["R1_shift_a"] == "R2_shift_b"
    assert repaired["injection_map"]["R2_shift_b"] == "R1_shift_a"
    old_map = {0: 1, 1: 2, 2: 0}
    try:
        validate_directional_injection_map(config, old_map)
    except InstrumentInvalidError as exc:
        assert "de-degeneracy assertion failed" in str(exc)
        assert exc.manifest["failing_gates"] == ["DE_DEGENERACY_ASSERTION"]
    else:  # pragma: no cover
        raise AssertionError("expected old R2<-R0 leg to fail de-degeneracy")


def test_synthetic_feedback_blind_arm_yields_zero_directional_delta() -> None:
    template = {
        "producer_function": "unit",
        "event_kind": "observe",
        "channel": "observe",
        "regime_id": "R1_shift_a",
        "regime_index": 1,
        "injected_regime_id": "R2_shift_b",
        "injected_regime_index": 2,
        "leg_id": "R1_shift_a<-R2_shift_b",
        "directional_scored_leg": True,
        "gate_scope": "post_drift_observe",
        "need": "energy",
        "intervention_tick": 201,
        "ab_window_ticks": [202],
        "ab_window_len": 1,
        "ab_divergence_count": 0,
        "ab_divergence_rate": 0.0,
        "ab_divergences": [],
        "c_window_ticks": [202],
        "c_window_len": 1,
        "c_target_site": "corner_bowl",
        "c_directional_match_count": 0,
        "c_directional_rate": 0.0,
        "c_raw_match_count": 0,
        "c_raw_rate": 0.0,
        "c_matches": [],
    }
    records = []
    for arm in ("candidate", "frozen_updates", "static", "candidate_ablated"):
        record = dict(template)
        record["arm"] = arm
        records.append(record)
    report = directional_delta_report(records, run_id="unit", code_hash="unit", seeds=[1])
    assert report["per_leg"]["R1_shift_a<-R2_shift_b"]["pooled"]["by_arm"]["candidate"]["delta_vs_frozen_updates"] == 0.0


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
