import json
from pathlib import Path

from scripts.ego_kernel.probe_substate import (
    build_probe_state,
    generate_observation_log,
    run_probe_episode,
)
from scripts.ego_kernel.replay import (
    compare_action_hash_sequences,
    replay_fresh_subprocess,
    replay_in_process,
)
from scripts.ego_kernel.state import KernelState
from scripts.ego_kernel.validation_gates import classify_kernel_references, hygiene_status
from scripts.run_ego_kernel_substrate_validation import run_validation


ROOT = Path(__file__).resolve().parents[1]


def test_kernel_state_canonical_hash_and_seed_registry_are_state_owned():
    left = KernelState(
        task_id="unit",
        run_id="run-a",
        episode_id="ep-a",
        step_id=0,
        substates={
            "counter": {"tick": 0},
            "pref_ema": {"values": [1.0, 0.0, 0.0, 0.0]},
        },
        seed_registry={"noise_user": {"seed": 11, "draws": 0}},
    )
    right = KernelState(
        task_id="unit",
        run_id="run-a",
        episode_id="ep-a",
        step_id=0,
        substates={
            "pref_ema": {"values": [1.0, 0.0, 0.0, 0.0]},
            "counter": {"tick": 0},
        },
        seed_registry={"noise_user": {"draws": 0, "seed": 11}},
    )

    assert left.canonical_json() == right.canonical_json()
    assert left.state_hash() == right.state_hash()
    assert left.seed_registry["noise_user"]["seed"] == 11

    changed = left.with_updates(substates={"counter": {"tick": 1}})
    assert changed.state_hash() != left.state_hash()


def test_probe_episode_replays_in_fresh_subprocess_and_from_midpoint():
    observations = generate_observation_log(seed=11, episode_index=0, ticks=24)
    initial = build_probe_state(seed=11, run_id="unit-run", episode_id="ep-0")
    uninterrupted = run_probe_episode(
        initial,
        observations,
        checkpoint_ticks={0, 12, 24},
    )

    fresh = replay_fresh_subprocess(
        initial_state=initial.to_dict(),
        observations=observations,
        repo_root=ROOT,
    )
    assert compare_action_hash_sequences(uninterrupted["trace_rows"], fresh["trace_rows"]) == []

    resumed = replay_in_process(
        initial_state=uninterrupted["checkpoints"]["12"],
        observations=observations[12:],
    )
    assert compare_action_hash_sequences(uninterrupted["trace_rows"][12:], resumed["trace_rows"]) == []


def test_validation_runner_writes_contract_artifacts_and_passes(tmp_path):
    result = run_validation(repo_root=ROOT, out_dir=tmp_path)

    assert result["verdict"] == "r0_substrate_pass"
    assert result["claim_ceiling"] == "kernel_substrate_engineering_only"
    assert result["gate_results"]["G-R0-REPLAY"]["mismatches_total"] == 0
    assert result["gate_results"]["G-R0-REPLAY"]["fresh_subprocess_runs_per_episode"] == 2
    assert result["gate_results"]["G-R0-CAUSALITY"]["min_direction_agreement"] >= 0.90
    assert result["gate_results"]["G-R0-CAUSALITY"]["pairwise_difference_rate"] >= 0.50
    assert result["gate_results"]["G-R0-CAUSALITY"]["zeroed_agreement_with_original"] <= 0.40
    assert result["gate_results"]["G-R0-SEED-NEGCTRL"]["perturbed_seed_detected"] is True
    assert result["gate_results"]["G-R0-SEED-NEGCTRL"]["missing_registry_nondeterminism_detected"] is True
    assert result["gate_results"]["G-R0-LLMSWAP-HARNESS"]["state_action_deltas_identical"] is True
    hygiene = result["gate_results"]["HYGIENE"]
    assert hygiene["ego_operator_imports_in_kernel"] == []
    assert hygiene["undeclared_references"] == []
    assert hygiene["declared_adopter_count"] == 2

    expected_artifacts = [
        "result.json",
        "config_frozen.json",
        "replay_report.json",
        "state_causality_report.json",
        "seed_negctrl_report.json",
        "llm_swap_harness_report.json",
    ]
    for name in expected_artifacts:
        assert (tmp_path / name).exists(), name

    result_payload = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert result_payload["verdict"] == "r0_substrate_pass"


def test_hygiene_negative_control_rejects_undeclared_kernel_reference():
    allowlist = [
        {
            "path": "EgoDesktop/scripts/run-joi-g-ablation-kernel-adoption.js",
            "authorizing_card": "ego-r3-adoption-slice-001a",
            "rationale": "sanctioned adopter",
        }
    ]
    references = [
        "EgoDesktop/scripts/run-joi-g-ablation-kernel-adoption.js",
        "EgoDesktop/src/unregistered_kernel_consumer.js",
    ]

    undeclared = classify_kernel_references(references, allowlist)

    assert undeclared == ["EgoDesktop/src/unregistered_kernel_consumer.js"]
    assert hygiene_status([], undeclared) == "fail"


def test_hygiene_allowlist_ablation_is_load_bearing():
    references = [
        "EgoDesktop/scripts/run-joi-g-ablation-kernel-adoption.js",
        "EgoDesktop/tests/pet_suite_baseline_gate.test.js",
    ]
    allowlist = [
        {
            "path": "EgoDesktop/scripts/run-joi-g-ablation-kernel-adoption.js",
            "authorizing_card": "ego-r3-adoption-slice-001a",
            "rationale": "sanctioned R3 adopter",
        },
        {
            "path": "EgoDesktop/tests/pet_suite_baseline_gate.test.js",
            "authorizing_card": "egodesktop-pet-world-integration-001a",
            "rationale": "sanctioned PET P1 baseline adopter",
        },
    ]

    ablated = [entry for entry in allowlist if entry["path"] != references[0]]
    undeclared = classify_kernel_references(references, ablated)

    assert references[0] in undeclared
    assert hygiene_status([], undeclared) == "fail"
    assert hygiene_status([], classify_kernel_references(references, allowlist)) == "pass"
