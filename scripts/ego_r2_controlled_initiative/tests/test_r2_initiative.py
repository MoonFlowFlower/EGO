from __future__ import annotations

import json
from pathlib import Path

from scripts.ego_r2_controlled_initiative.env import R2Config, simulate_episode
from scripts.ego_r2_controlled_initiative.leak import scan_visible_payload
from scripts.ego_r2_controlled_initiative.policies import (
    A1NoLearnedTablesCandidate,
    GatedInitiativeLearner,
)
from scripts.ego_r2_controlled_initiative.replay import fresh_process_smoke_replay
from scripts.ego_r2_controlled_initiative.runner import classify_process_result
from scripts.ego_r2_controlled_initiative.validation import package_forbidden_imports


def test_planted_leak_positive_control_fires() -> None:
    clean = {"candidate_visible": {"t": 1, "x1": 0.2, "history": [{"feedback": "ignore"}]}}
    planted = {"candidate_visible": {"t": 1, "x1": 0.2, "s_t": 0.85}}

    clean_result = scan_visible_payload(clean)
    planted_result = scan_visible_payload(planted)

    assert clean_result["leak_found"] is False
    assert planted_result["leak_found"] is True
    assert any(hit["key"] == "s_t" for hit in planted_result["hits"])


def test_a1_ablation_changes_decision_on_synthetic_fixture() -> None:
    full = GatedInitiativeLearner.synthetic_with_tables(phase_bin=10)
    ablated = A1NoLearnedTablesCandidate.synthetic_with_uninformative_priors()
    observations = [
        {"t": 100, "x1": 0.72, "x2": 0.86, "x3": 1.0, "x4": 0.1},
        {"t": 106, "x1": 0.68, "x2": 0.82, "x3": 1.0, "x4": 0.2},
        {"t": 112, "x1": 0.22, "x2": 0.20, "x3": 1.0, "x4": 0.3},
    ]

    full_actions = [full.decide(obs)["action"] for obs in observations]
    ablated_actions = [ablated.decide(obs)["action"] for obs in observations]

    assert sum(a != b for a, b in zip(full_actions, ablated_actions)) >= 1


def test_fresh_process_replay_bit_exact_on_two_episode_smoke(tmp_path: Path) -> None:
    report = fresh_process_smoke_replay(tmp_path, master_seed=31, n_episodes=2)

    assert report["status"] == "pass"
    assert report["digest_1"] == report["digest_2"]
    assert report["episodes"] == 2


def test_executor_classifies_spawn_error_distinct_from_timeout() -> None:
    spawn = classify_process_result(returncode=None, timed_out=False, stdout="", stderr="missing executable")
    timeout = classify_process_result(returncode=None, timed_out=True, stdout="line1\nline2", stderr="")

    assert spawn["status"] == "spawn_error"
    assert timeout["status"] == "timeout"
    assert timeout["stdout_tail"] == ["line1", "line2"]


def test_package_has_no_forbidden_framework_imports() -> None:
    result = package_forbidden_imports()

    assert result["status"] == "pass"
    assert result["hits"] == []


def test_crn_identical_episode_seed_produces_identical_env_stream() -> None:
    config = R2Config()
    silent_policy = lambda obs: False

    episode_a = simulate_episode(config=config, master_seed=31, episode_index=0, policy_fn=silent_policy)
    episode_b = simulate_episode(config=config, master_seed=31, episode_index=0, policy_fn=silent_policy)

    stream_a = [(row["t"], row["x1"], row["x2"], row["x3"], row["x4"]) for row in episode_a.candidate_trace]
    stream_b = [(row["t"], row["x1"], row["x2"], row["x3"], row["x4"]) for row in episode_b.candidate_trace]
    assert json.dumps(stream_a, sort_keys=True) == json.dumps(stream_b, sort_keys=True)
