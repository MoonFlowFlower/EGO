from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ego_pet.creature import _best_site, zero_creature_state
from scripts.ego_pet_capability.forage_prediction_error import (
    ARMS,
    ForageEvent,
    PROBE_SEED,
    SCORED_SEEDS,
    VARIANTS,
    InstrumentInvalidError,
    ablation_report,
    assert_seed_disjointness,
    baseline_comparison_report,
    code_path_hash,
    flatten_pair_trace,
    gate_scoped_pair_trace,
    gate_trace_keep_predicate,
    load_world_config,
    metric_records_for_event,
    pair_c_yield,
    pe_fidelity_report,
    rng_audit,
    run_pair_bundle_for_seed,
    run_phase,
)
from scripts.ego_pet_capability.trace import (
    CapabilityTraceTooLargeError,
    MAX_CAPABILITY_TRACE_BYTES,
    write_gate_scoped_jsonl,
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


def test_forage_gate_scoped_trace_preserves_gate_records(tmp_path: Path) -> None:
    config = load_world_config()
    bundle = run_pair_bundle_for_seed(config, seed=PROBE_SEED, run_id="unit_pe_probe_gate_trace")
    full_rows = flatten_pair_trace(bundle["pair_runs"])
    scoped_rows = gate_scoped_pair_trace(bundle["pair_runs"], bundle["metric_records"])
    report = write_gate_scoped_jsonl(
        tmp_path / "probe_trace.jsonl",
        full_rows,
        gate_trace_keep_predicate(bundle["metric_records"]),
    )
    assert 0 < len(scoped_rows) < len(full_rows)
    assert report["rows_written"] == len(scoped_rows)
    assert report["size_guard"]["bytes"] < MAX_CAPABILITY_TRACE_BYTES

    rows_by_pair: dict[str, list[dict[str, object]]] = {}
    for row in scoped_rows:
        rows_by_pair.setdefault(str(row["pair_id"]), []).append(row)

    recomputed_records = []
    for event_payload in bundle["events"]:
        event = ForageEvent.from_dict(event_payload)
        for arm in ARMS:
            recomputed_records.extend(
                metric_records_for_event(
                    arm=arm,
                    event=event,
                    variant_runs={
                        variant: {"trace_rows": rows_by_pair.get(f"{event.event_id}:{arm}:{variant}", [])}
                        for variant in VARIANTS
                    },
                )
            )
    assert recomputed_records == bundle["metric_records"]


def test_capability_trace_size_guard_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(CapabilityTraceTooLargeError, match="gate-scope"):
        write_gate_scoped_jsonl(
            tmp_path / "too_large_trace.jsonl",
            [{"payload": "x" * 1024}],
            lambda _row: True,
            max_bytes=64,
        )


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
