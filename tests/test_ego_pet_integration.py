import json
from pathlib import Path

from scripts.ego_kernel.trace import validate_trace_row
from scripts.ego_pet.battery import (
    baseline_comparison,
    code_path_hash,
    replay_episode,
    run_arm_set,
    run_battery,
    run_episode,
)
from scripts.ego_pet.memory_wiring import run_poison_quarantine_probe
from scripts.ego_pet.static_gate import load_static_gate_config, maybe_emit_bubble, zero_static_gate_state
from scripts.ego_pet.world import load_world_config


ROOT = Path(__file__).resolve().parents[1]


def test_seed_registry_determinism_two_in_process_runs_bit_equal():
    config = load_world_config()
    left = run_episode(config=config, seed=1101, arm="candidate", run_id="unit", episode_id="left")
    right = run_episode(config=config, seed=1101, arm="candidate", run_id="unit", episode_id="left")

    assert [row["state_after_hash"] for row in left["trace_rows"]] == [row["state_after_hash"] for row in right["trace_rows"]]
    assert [row["action"] for row in left["trace_rows"]] == [row["action"] for row in right["trace_rows"]]


def test_trace_rows_validate_kernel_trace_v0_and_replay_recomputes_actions():
    config = load_world_config()
    result = run_episode(config=config, seed=1102, arm="candidate", run_id="unit", episode_id="candidate")

    validate_trace_row(result["trace_rows"][0])
    replayed = replay_episode({"initial_state": result["initial_state"], "observations": result["observations"]})

    assert [row["action"] for row in result["trace_rows"]] == [row["action"] for row in replayed["trace_rows"]]
    assert [row["state_after_hash"] for row in result["trace_rows"]] == [row["state_after_hash"] for row in replayed["trace_rows"]]


def test_mem_path_poison_fixture_quarantines_without_promotion():
    report = run_poison_quarantine_probe()

    assert report["status"] == "pass"
    assert report["direct_external_owned_writes"] == 0
    assert report["unauthorized_promotions"] == 0
    assert report["quarantine_entries"] == 1


def test_static_gate_rate_limits_and_enforces_non_learner_origin():
    config = load_static_gate_config()
    state = zero_static_gate_state()

    state, first = maybe_emit_bubble(
        state,
        tick_index=1,
        world_needs={"energy": 0.10, "comfort": 0.80},
        config=config,
        config_sha256="unit-sha",
    )
    state, second = maybe_emit_bubble(
        state,
        tick_index=2,
        world_needs={"energy": 0.10, "comfort": 0.80},
        config=config,
        config_sha256="unit-sha",
    )

    assert first is not None
    assert first["learner_originated"] is False
    assert second is None


def test_ablation_tripwire_fires_on_constructed_identity_case_and_not_evaluable_branch(tmp_path):
    config = load_world_config()
    code_hash = code_path_hash()
    runs = run_arm_set(config, [1103], run_id="unit", arms=["candidate", "standin", "random", "static", "frozen_updates", "schedule_aware_reference"])
    hard = baseline_comparison(runs, config, run_id="unit", code_hash=code_hash)

    forced = {**hard, "status": "fail"}
    from scripts.ego_pet.battery import ablation_report

    report = ablation_report(runs, config, hard_report=forced, run_id="unit", code_hash=code_hash)
    assert report["status"] == "not_evaluable_no_win"

    identity = json.loads(json.dumps(runs))
    identity["frozen_updates"] = identity["candidate"]
    passed_hard = {**hard, "status": "pass", "seed_ids": [1103]}
    identity_report = ablation_report(identity, config, hard_report=passed_hard, run_id="unit", code_hash=code_hash)
    assert identity_report["identity_tripwire"]["status"] == "fail"


def test_probe_path_uses_dev_seed_and_writes_probe_report(tmp_path):
    result = run_battery(phase="probe", out_dir=tmp_path, seed=1104)

    assert result["phase"] == "probe"
    assert result["seed_ids"] == [1104]
    assert (tmp_path / "probe_report.json").exists()
    assert result["cpu"]["projected_full_p0_cpu_hours"] is not None

