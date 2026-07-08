from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.ego_r2_controlled_initiative.runner as runner
from scripts.ego_r2_controlled_initiative.env import R2Config, simulate_episode
from scripts.ego_r2_controlled_initiative.leak import scan_visible_payload
from scripts.ego_r2_controlled_initiative.policies import (
    A1NoLearnedTablesCandidate,
    GatedInitiativeLearner,
)
from scripts.ego_r2_controlled_initiative.replay import fresh_process_smoke_replay
from scripts.ego_r2_controlled_initiative.runner import classify_process_result, compute_p0
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


def test_addendum001_degen_gate_uses_corrected_harmful_spam_rule() -> None:
    gate = compute_p0(n_ep=40, include_replay=False)["gate_results"]["G-P0-DEGEN"]

    assert gate["always_act_mean"] <= -0.06
    assert gate["always_act_ci_high"] < 0
    assert gate["pass"] is True


def test_p2_refuses_when_certificate_argument_missing() -> None:
    with pytest.raises(SystemExit) as exc:
        runner.load_valid_part0_certificate(None)

    assert "instrument_invalid_certificate" in str(exc.value)
    assert "--certificate" in str(exc.value)


def test_p2_refuses_banked_v1_failing_certificate_read_only() -> None:
    cert_path = Path("artifacts/ego-r2-controlled-initiative-001a/p0/part0_certificate.json")

    with pytest.raises(SystemExit) as exc:
        runner.load_valid_part0_certificate(cert_path)

    assert "instrument_invalid_certificate" in str(exc.value)
    assert str(cert_path) in str(exc.value)


def test_p2_accepts_addendum001_p0r_certificate_without_scoring() -> None:
    cert_path = Path("artifacts/ego-r2-controlled-initiative-001a/p0_rerun_addendum001/part0_certificate.json")

    validated = runner.load_valid_part0_certificate(cert_path)

    assert validated["certificate_path"] == str(cert_path)
    assert validated["certificate_sha256"]
    assert validated["certificate"]["status"] == "valid"
    assert all(gate.get("pass") is True for gate in validated["certificate"]["gate_results"].values())
