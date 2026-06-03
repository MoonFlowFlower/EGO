import argparse
import json
from pathlib import Path

import scripts.run_adult_fiction_candidate_suite as suite


def _args(**overrides):
    values = {
        "base_url": "http://localhost:1234/v1",
        "api_key": "lm-studio",
        "model": "",
        "exclude_model": ["cydonia"],
        "configure_timeout_seconds": 5.0,
        "scenario_file": Path("/tmp/private_scenario.json"),
        "settings_matrix": None,
        "out": None,
        "repeat_runs": 3,
        "suite_timeout_seconds": 1800,
        "wrapper_timeout_seconds": 0,
        "wait_for_candidate": False,
        "wait_timeout_seconds": 1800,
        "poll_seconds": 10,
        "expressiveness": "explicit",
        "prompt_profile": "direct_fiction",
        "adult_timeout_seconds": 180,
        "max_tokens": 120,
        "context_turns": 3,
        "message_char_limit": 420,
        "temperature": None,
        "top_p": None,
        "judge_with_codex": False,
        "judge_model": "gpt-5.5",
        "json": True,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_no_candidate_result_excludes_cydonia_and_ignores_embedding():
    result = suite.no_candidate_result(
        _args(judge_with_codex=True, judge_model="gpt-5.5"),
        ["thedrummer_cydonia-24b-v4.1", "text-embedding-nomic-embed-text-v1.5"],
    )

    assert result["status"] == "no_candidate_text_generation_models"
    assert result["text_generation_models"] == ["thedrummer_cydonia-24b-v4.1"]
    assert result["ignored_non_text_models"] == ["text-embedding-nomic-embed-text-v1.5"]
    assert result["excluded_text_generation_models"] == ["thedrummer_cydonia-24b-v4.1"]
    assert result["recommended_next_models"]
    assert "--judge-with-codex" in result["recommended_wait_command"]
    assert "--wait-for-candidate" in result["recommended_wait_command"]
    assert "--judge-with-codex" in result["recommended_direct_command"]
    json.dumps(result)


def test_no_candidate_result_filters_rejected_recommendations():
    result = suite.no_candidate_result(
        _args(exclude_model=["cydonia", "snowpiercer"]),
        ["thedrummer_cydonia-24b-v4.1", "snowpiercer-15b-v4", "text-embedding-nomic-embed-text-v1.5"],
    )

    assert result["recommended_next_models"][0]["candidate"] == "rocinante-xl-16b-q4_k_s"
    assert all("snowpiercer" not in item["candidate"] for item in result["recommended_next_models"])
    assert "non-excluded text-generation" in result["next_action"]


def test_build_trial_env_targets_selected_candidate():
    env = suite.build_trial_env(_args(temperature=0.45, top_p=0.85), "snowpiercer-q4")

    assert env["ADULT_FICTION_PROVIDER"] == "openai_compatible"
    assert env["ADULT_FICTION_MODEL"] == "snowpiercer-q4"
    assert env["ADULT_FICTION_MAX_TOKENS"] == "120"
    assert env["ADULT_FICTION_CONTEXT_TURNS"] == "3"
    assert env["ADULT_FICTION_MESSAGE_CHAR_LIMIT"] == "420"
    assert env["ADULT_FICTION_TEMPERATURE"] == "0.45"
    assert env["ADULT_FICTION_TOP_P"] == "0.85"


def test_build_trial_command_uses_real_acceptance_suite(tmp_path):
    scenario = tmp_path / "scenario.json"
    args = _args(scenario_file=scenario)
    command = suite.build_trial_command(args, tmp_path / "out")
    text = " ".join(command)

    assert "run_ego_experience_trial.py" in text
    assert "--adult-fiction-acceptance-suite" in command
    assert "--repeat-runs" in command
    assert "3" in command


def test_build_trial_command_can_request_gpt55_judge(tmp_path):
    scenario = tmp_path / "scenario.json"
    args = _args(scenario_file=scenario, judge_with_codex=True, judge_model="gpt-5.5")
    command = suite.build_trial_command(args, tmp_path / "out")

    assert "--judge-with-codex" in command
    assert "--judge-model" in command
    assert "gpt-5.5" in command


def test_build_trial_command_passes_settings_matrix(tmp_path):
    scenario = tmp_path / "scenario.json"
    settings = tmp_path / "settings.json"
    args = _args(scenario_file=scenario, settings_matrix=settings)
    command = suite.build_trial_command(args, tmp_path / "out")

    assert "--settings-matrix" in command
    assert str(settings) in command


def test_recommended_wrapper_command_includes_custom_scenario_and_out(tmp_path):
    scenario = tmp_path / "private scenario.json"
    settings = tmp_path / "quality settings.json"
    out = tmp_path / "candidate out"
    args = _args(
        scenario_file=scenario,
        settings_matrix=settings,
        out=out,
        wait_timeout_seconds=60,
        poll_seconds=2,
        exclude_model=["cydonia", "snowpiercer"],
        judge_with_codex=True,
        judge_model="gpt-5.5",
        temperature=0.45,
        top_p=0.85,
    )

    command = suite.recommended_wrapper_command(args, wait=True)

    assert "--wait-for-candidate" in command
    assert "--exclude-model cydonia" in command
    assert "--exclude-model snowpiercer" in command
    assert "--wait-timeout-seconds 60" in command
    assert "--poll-seconds 2" in command
    assert "--judge-with-codex" in command
    assert "--scenario-file" in command
    assert "--settings-matrix" in command
    assert "--temperature 0.45" in command
    assert "--top-p 0.85" in command
    assert "--out" in command


def test_recommended_wrapper_command_dedupes_exclusions(tmp_path):
    args = _args(exclude_model=["cydonia", "cydonia", "snowpiercer"])

    command = suite.recommended_wrapper_command(args, wait=False)

    assert command.count("--exclude-model cydonia") == 1
    assert command.count("--exclude-model snowpiercer") == 1


def test_unique_nonempty_dedupes_case_insensitive_exclusions():
    assert suite._unique_nonempty(("cydonia", "Cydonia", "", "snowpiercer")) == [
        "cydonia",
        "snowpiercer",
    ]


def test_classify_acceptance_report_ready_for_judge():
    report = {
        "status": "scripted_adult_fiction_acceptance_needs_judge",
        "settings_matrix_summary": {"status": "pass", "selected_setting_id": "tokens120"},
        "repeat_run_summary": {"status": "pass", "passed_run_count": 3, "required_runs": 3},
    }

    result = suite.classify_acceptance_report(report, 0)

    assert result["recommendation"] == "ready_for_gpt55_judge"
    assert result["reason"] == "mechanical_strict_suite_pass"


def test_classify_acceptance_report_judge_pass_ready_for_sanity():
    report = {
        "status": "scripted_adult_fiction_acceptance_judge_pass",
        "settings_matrix_summary": {"status": "pass", "selected_setting_id": "tokens120"},
        "repeat_run_summary": {"status": "pass", "passed_run_count": 3, "required_runs": 3},
        "gpt55_judge": {"verdict": "pass"},
        "strict_judge_score_gate": {"status": "pass"},
    }

    result = suite.classify_acceptance_report(report, 0)

    assert result["recommendation"] == "ready_for_human_sanity_and_closeout_packet"
    assert result["judge_verdict"] == "pass"
    assert result["strict_judge_score_gate"] == "pass"


def test_classify_acceptance_report_judge_partial_keeps_blocked():
    report = {
        "status": "scripted_adult_fiction_acceptance_judge_partial",
        "settings_matrix_summary": {"status": "pass", "selected_setting_id": "tokens120"},
        "repeat_run_summary": {"status": "pass", "passed_run_count": 3, "required_runs": 3},
        "gpt55_judge": {"verdict": "partial"},
    }

    result = suite.classify_acceptance_report(report, 1)

    assert result["recommendation"] == "keep_80_blocked_judge_partial"
    assert result["judge_verdict"] == "partial"


def test_classify_acceptance_report_repeat_instability():
    report = {
        "status": "scripted_adult_fiction_acceptance_failed",
        "settings_matrix_summary": {"status": "pass", "selected_setting_id": "tokens120"},
        "repeat_run_summary": {
            "status": "fail",
            "passed_run_count": 2,
            "required_runs": 3,
            "failure_counts": {"sticky_refusal_recovery_probe_failed": 1},
        },
        "suite_timeout": {"triggered": False},
    }

    result = suite.classify_acceptance_report(report, 1)

    assert result["recommendation"] == "keep_80_blocked_repeat_instability"
    assert result["failure_counts"] == {"sticky_refusal_recovery_probe_failed": 1}


def test_classify_acceptance_report_timeout():
    report = {
        "status": "scripted_adult_fiction_acceptance_timeout",
        "settings_matrix_summary": {"status": "pass"},
        "repeat_run_summary": {"status": "fail"},
        "suite_timeout": {"triggered": True, "stage": "repeat_runs"},
    }

    result = suite.classify_acceptance_report(report, 1)

    assert result["recommendation"] == "keep_80_blocked_timeout_or_capacity"
    assert result["reason"] == "timeout_at_repeat_runs"


def test_wait_for_candidate_returns_no_candidate_without_wait(monkeypatch):
    args = _args(wait_for_candidate=False)
    monkeypatch.setattr(
        suite.sidecar,
        "fetch_model_ids",
        lambda base_url, timeout: ["thedrummer_cydonia-24b-v4.1", "text-embedding-nomic-embed-text-v1.5"],
    )

    code, models, selected, result = suite.wait_for_candidate(args)

    assert code == 3
    assert models == ["thedrummer_cydonia-24b-v4.1", "text-embedding-nomic-embed-text-v1.5"]
    assert selected is None
    assert result["status"] == "no_candidate_text_generation_models"
    assert result["wait_status"] == "not_waiting"


def test_wait_for_candidate_finds_later_model(monkeypatch):
    args = _args(wait_for_candidate=True, wait_timeout_seconds=30, poll_seconds=1)
    calls = {"count": 0}

    def fake_fetch(base_url, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            return ["thedrummer_cydonia-24b-v4.1"]
        return ["thedrummer_cydonia-24b-v4.1", "snowpiercer-q4"]

    monkeypatch.setattr(suite.sidecar, "fetch_model_ids", fake_fetch)
    monkeypatch.setattr(suite.time, "sleep", lambda seconds: None)

    code, models, selected, result = suite.wait_for_candidate(args)

    assert code == 0
    assert selected == "snowpiercer-q4"
    assert models == ["thedrummer_cydonia-24b-v4.1", "snowpiercer-q4"]
    assert result["wait_status"] == "candidate_found"
    assert result["wait_attempts"] == 2
