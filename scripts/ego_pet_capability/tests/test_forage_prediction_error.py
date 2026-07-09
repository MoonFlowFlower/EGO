from __future__ import annotations

from pathlib import Path

from scripts.ego_pet.creature import _best_site, zero_creature_state
from scripts.ego_pet_capability.forage_prediction_error import (
    ARMS,
    PROBE_SEED,
    SCORED_SEEDS,
    InstrumentInvalidError,
    ablation_report,
    assert_seed_disjointness,
    baseline_comparison_report,
    code_path_hash,
    load_world_config,
    pair_c_yield,
    pe_fidelity_report,
    rng_audit,
    run_pair_bundle_for_seed,
    run_phase,
)


def test_seed_disjointness_four_way_fail_closed() -> None:
    assert_seed_disjointness(SCORED_SEEDS)
    assert PROBE_SEED == 1107
    for reserved_seed in (1101, 2101, 3101, 4101):
        try:
            assert_seed_disjointness([reserved_seed])
        except InstrumentInvalidError as exc:
            assert "seed-disjointness assertion failed" in str(exc)
        else:  # pragma: no cover
            raise AssertionError(f"expected seed-disjointness failure for {reserved_seed}")


def test_pair_c_target_degeneracy_rejects_same_as_current_and_accepts_moved_target() -> None:
    config = load_world_config()
    creature = zero_creature_state(config, arm="candidate")
    need = "energy"
    site = _best_site(creature["model"], need)
    actual, meta = pair_c_yield(config, creature, {"action_type": "forage_energy", "site": site}, need)
    assert actual
    assert meta["pair_c_target_site"] != meta["pre_intervention_best_site"]

    degenerate = zero_creature_state(config, arm="candidate")
    for values in degenerate["model"].values():
        values["energy"] = 0.0
        values["comfort"] = 0.0
    degenerate_site = _best_site(degenerate["model"], need)
    try:
        pair_c_yield(config, degenerate, {"action_type": "forage_energy", "site": degenerate_site}, need)
    except InstrumentInvalidError as exc:
        assert "Pair-C target-degeneracy" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected Pair-C target degeneracy failure")


def test_probe_bundle_decomposition_signatures() -> None:
    config = load_world_config()
    bundle = run_pair_bundle_for_seed(config, seed=PROBE_SEED, run_id="unit_pe_probe")
    code_hash = code_path_hash()
    records = bundle["metric_records"]
    pe = pe_fidelity_report(records, run_id="unit", code_hash=code_hash, seeds=[PROBE_SEED])
    baseline = baseline_comparison_report(records, run_id="unit", code_hash=code_hash, seeds=[PROBE_SEED])
    ablation = ablation_report(records, run_id="unit", code_hash=code_hash, seeds=[PROBE_SEED])
    assert pe["status"] == "pass"
    assert baseline["by_arm"]["schedule_reobserve"]["C_delta"] == 0.0
    assert baseline["by_arm"]["static"]["C_delta"] == 0.0
    assert baseline["by_arm"]["frozen_updates"]["C_delta"] >= 0.60
    assert baseline["by_arm"]["candidate_ablated"]["C_delta"] >= 0.60
    assert ablation["by_arm"]["frozen_updates"]["W_rate"] == 0.0
    assert ablation["by_arm"]["candidate_ablated"]["W_rate"] == 0.0


def test_probe_phase_without_replay_is_deterministic_and_artifact_free(tmp_path: Path) -> None:
    first = run_phase(phase="probe", out_dir=tmp_path / "a", include_replay=False, write_artifacts=False)
    second = run_phase(phase="probe", out_dir=tmp_path / "b", include_replay=False, write_artifacts=False)
    assert first["per_arm_C_table"] == second["per_arm_C_table"]
    assert first["per_arm_W_table"] == second["per_arm_W_table"]
    assert not (tmp_path / "a").exists()
    assert not (tmp_path / "b").exists()


def test_rng_audit_positive_control_detects_forbidden_random(tmp_path: Path) -> None:
    offender = tmp_path / "offender.py"
    offender.write_text("import random\nvalue = random.random()\n", encoding="utf-8")
    report = rng_audit(code_hash="unit", run_id="unit", scan_files=[offender])
    assert report["status"] == "fail"
    assert report["forbidden_hits"]


def test_arm_set_includes_rate_matched_schedule_control() -> None:
    assert ARMS == ("candidate", "frozen_updates", "static", "candidate_ablated", "schedule_reobserve")
