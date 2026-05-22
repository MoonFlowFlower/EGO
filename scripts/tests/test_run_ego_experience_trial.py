from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "run_ego_experience_trial.py"
spec = importlib.util.spec_from_file_location("run_ego_experience_trial", MODULE_PATH)
run_ego_experience_trial = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = run_ego_experience_trial
spec.loader.exec_module(run_ego_experience_trial)


class CapturePromptLLM:
    provider = "fake"
    model = "capture"
    last_usage = {}
    last_reasoning_tokens = None

    def __init__(self) -> None:
        self.system_prompts: list[str] = []

    def chat(self, messages, *, system_prompt, policy_context="", tools=None, stream=None):
        self.system_prompts.append(system_prompt)
        return run_ego_experience_trial.agent.LLMChatResult(content="收到。", tool_calls=[])


def test_cli_compatible_dispatch_handles_provider_status(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    runtime = agent.build_demo_runtime(enable_operator_memory=False, runtime_mode="approve")

    reply = run_ego_experience_trial.dispatch_cli_compatible(runtime, "/provider_status")
    payload = json.loads(reply)

    assert payload["provider"] == "none"


def test_experience_trial_runs_sample_pack_through_cli_compatible_path(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    (tmp_path / ".gitignore").write_text("artifacts/experience_trial/\nmemory/*.jsonl\n", encoding="utf-8")

    report = run_ego_experience_trial.run_experience_trial(output_dir=tmp_path, case_limit=3)

    payload = json.loads((tmp_path / "experience_trial_report.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "experience_trial_report.md").read_text(encoding="utf-8")
    assert report["schema_version"] == "ego_operator.experience_trial.v1"
    assert report["status"] == "scripted_real_entry_provider_unavailable"
    assert report["provider_mode"] == "none"
    assert report["case_count"] == 3
    assert all(item["entrypoint"] == "cli_compatible_dispatch" for item in report["results"])
    assert payload["case_count"] == 3
    assert "CLI-compatible EgoOperator path" in markdown
    assert all("emotion_candidate" in item for item in report["results"])
    assert "real consciousness" in payload["not_claimed"]


def test_negative_emotion_pack_runs_through_trace_emotion_signal(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    (tmp_path / ".gitignore").write_text("artifacts/experience_trial/\nmemory/*.jsonl\n", encoding="utf-8")

    report = run_ego_experience_trial.run_experience_trial(
        sample_pack_path=(
            ROOT
            / "docs"
            / "codex"
            / "tasks"
            / "ego-experience-roadmap-bootstrap-v1"
            / "negative_emotion_support_scenarios.json"
        ),
        output_dir=tmp_path,
    )

    observed = {item["case_id"]: item for item in report["results"]}
    assert report["status"] == "scripted_real_entry_provider_unavailable"
    assert report["case_count"] == 4
    assert observed["frustration_repeated_failure"]["emotion_candidate"] == "frustration"
    assert observed["confusion_unclear_next_step"]["emotion_candidate"] == "uncertainty"
    assert observed["disappointment_work_wasted"]["emotion_candidate"] == "disappointment"
    assert observed["urgency_time_pressure"]["emotion_candidate"] == "urgency"
    assert all(item["scenario_expectation_status"] == "pass" for item in report["results"])


def test_emotion_misread_recovery_pack_runs_through_trace_emotion_signal(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    (tmp_path / ".gitignore").write_text("artifacts/experience_trial/\nmemory/*.jsonl\n", encoding="utf-8")

    report = run_ego_experience_trial.run_experience_trial(
        sample_pack_path=(
            ROOT
            / "docs"
            / "codex"
            / "tasks"
            / "ego-experience-roadmap-bootstrap-v1"
            / "emotion_misread_recovery_scenarios.json"
        ),
        output_dir=tmp_path,
    )

    assert report["status"] == "scripted_real_entry_provider_unavailable"
    assert report["case_count"] == 3
    assert all(item["emotion_candidate"] == "emotion_misread_correction" for item in report["results"])
    assert all(item["response_need"] == "respect_correction_and_refocus" for item in report["results"])
    assert all(item["scenario_expectation_status"] == "pass" for item in report["results"])


def test_cli_compatible_dispatch_uses_bounded_continuity_context_injection(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    runtime = agent.build_demo_runtime(
        enable_operator_memory=True,
        operator_memory_dir=tmp_path / "memory",
        runtime_mode="approve",
    )
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "trace.jsonl")
    capture = CapturePromptLLM()
    runtime.planner.llm = capture

    remember = runtime.remember_operator_note("用户名字：流月；打招呼时可带称呼。")
    assert remember["status"] == "ok"

    run_ego_experience_trial.dispatch_cli_compatible(runtime, "黑暗之魂这个游戏怎么样？")
    unrelated_prompt = capture.system_prompts[-1]
    assert "用户名字：流月" not in unrelated_prompt

    run_ego_experience_trial.dispatch_cli_compatible(runtime, "你好")
    greeting_prompt = capture.system_prompts[-1]
    trace_rows = [
        json.loads(line)
        for line in (tmp_path / "trace.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert "用户名字：流月" in greeting_prompt
    assert trace_rows[0]["operator_memory"]["context_injection"]["core"]["included"] is False
    assert trace_rows[1]["operator_memory"]["context_injection"]["core"]["included"] is True
    assert trace_rows[1]["operator_memory"]["context_injection"]["core"]["reason"] == "continuity_query_intent"


def test_cli_compatible_dispatch_quarantines_stale_candidate_on_user_correction(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    runtime = agent.build_demo_runtime(
        enable_operator_memory=True,
        operator_memory_dir=tmp_path / "memory",
        runtime_mode="approve",
    )
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "trace.jsonl")
    runtime.planner.llm = CapturePromptLLM()

    stale = runtime.operator_memory.propose_candidate_memory(
        "user_signal: 以后请打招呼时带上称呼",
        source="test",
    )

    run_ego_experience_trial.dispatch_cli_compatible(runtime, "其实以后不要打招呼时带上称呼。")

    active = runtime.operator_memory.list_candidate_memories()
    archived = runtime.operator_memory.list_candidate_memories(include_archived=True)
    assert all(item["id"] != stale["id"] for item in active)
    assert any(item["id"] == stale["id"] and item["status"] == "cold_archive" for item in archived)


def test_cli_compatible_dispatch_approves_candidate_memory(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    runtime = agent.build_demo_runtime(
        enable_operator_memory=True,
        operator_memory_dir=tmp_path / "memory",
        runtime_mode="approve",
    )
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "trace.jsonl")
    runtime.planner.llm = CapturePromptLLM()

    run_ego_experience_trial.dispatch_cli_compatible(runtime, "我偏好中文结论先行，少废话。")
    candidate = runtime.operator_memory.list_candidate_memories()[0]
    reply = run_ego_experience_trial.dispatch_cli_compatible(runtime, f"/memory_approve {candidate['id']}")
    payload = json.loads(reply)

    assert payload["status"] == "ok"
    assert "中文结论先行" in runtime.operator_memory.load_core()
    assert all(item["id"] != candidate["id"] for item in runtime.operator_memory.list_candidate_memories())


def test_adaptation_effectiveness_pack_builds_reviewer_packet(tmp_path) -> None:
    report = run_ego_experience_trial.run_adaptation_effectiveness_trial(output_dir=tmp_path)
    payload = json.loads((tmp_path / "adaptation_effectiveness_report.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "adaptation_effectiveness_report.md").read_text(encoding="utf-8")

    assert report["schema_version"] == "ego_operator.adaptation_effectiveness_trial.v1"
    assert report["status"] == "scripted_with_llm_judge_needs_review"
    assert report["case_count"] >= 4
    assert report["failed_count"] == 0
    assert payload["llm_reviewer_packet"]["cases"]
    assert all(item["deterministic_status"] == "pass" for item in payload["results"])
    assert "durable memory efficacy" in payload["not_claimed"]
    assert "Adaptation Effectiveness" in markdown


def test_companion_smoke_pack_builds_gpt55_judge_packet(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    (tmp_path / ".gitignore").write_text("artifacts/experience_trial/\nmemory/*.jsonl\n", encoding="utf-8")

    report = run_ego_experience_trial.run_companion_smoke_trial(output_dir=tmp_path, turn_limit=3)
    payload = json.loads((tmp_path / "companion_smoke_report.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "companion_smoke_report.md").read_text(encoding="utf-8")

    assert report["schema_version"] == "ego_operator.companion_smoke_trial.v1"
    assert report["status"] == "scripted_companion_provider_unavailable"
    assert report["turn_count"] == 3
    assert payload["gpt55_judge_packet"]["judge_model"] == "gpt-5.5"
    assert payload["gpt55_judge_packet"]["transcript"]
    assert "Joi-Inspired Companion" in markdown
    assert "real consciousness" in payload["not_claimed"]


def test_companion_smoke_codex_judge_uses_gpt55_schema(tmp_path, monkeypatch) -> None:
    calls = []

    class Completed:
        returncode = 0
        stdout = json.dumps(
            {
                "verdict": "pass",
                "scores": {"companion_warmth": 4},
                "reasons": ["warm and bounded"],
                "missing_evidence": [],
                "follow_up_issues": [],
                "claim_ceiling": "scripted candidate only",
            }
        )
        stderr = ""

    def fake_run(args, cwd=None, capture_output=None, text=None, check=None):
        calls.append(args)
        return Completed()

    monkeypatch.setattr(run_ego_experience_trial.subprocess, "run", fake_run)
    packet = {"transcript": [], "claim_ceiling": "candidate"}

    judge = run_ego_experience_trial.run_codex_companion_judge(packet, model="gpt-5.5")

    assert judge["verdict"] == "pass"
    assert calls
    assert calls[0][:6] == ["codex", "exec", "--ephemeral", "--sandbox", "read-only", "--model"]
    assert "gpt-5.5" in calls[0]
    assert "--output-schema" in calls[0]


def test_functional_subject_trial_pack_has_required_20_case_coverage() -> None:
    pack = run_ego_experience_trial.load_functional_subject_trial_pack()
    cases = pack["cases"]

    assert len(cases) == 20
    categories = {case["category"] for case in cases}
    assert {
        "memory_recall",
        "preference_update",
        "claim_pressure",
        "bounded_initiative",
        "emotion",
        "tool_gate",
        "memory_correction",
        "memory_forget",
        "memory_save",
        "failure_recovery",
        "policy_patch",
        "initiative_opportunity",
    } <= categories
    assert all(case.get("baseline_failure_mode") for case in cases)
    assert all(case.get("candidate_success_signal") for case in cases)
    assert all(case.get("target_mechanisms") for case in cases)


def test_functional_subject_trial_builds_gpt55_judge_packet(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    (tmp_path / ".gitignore").write_text("artifacts/experience_trial/\nmemory/*.jsonl\n", encoding="utf-8")

    report = run_ego_experience_trial.run_functional_subject_trial(output_dir=tmp_path, case_limit=4)
    payload = json.loads((tmp_path / "functional_subject_trial_report.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "functional_subject_trial_report.md").read_text(encoding="utf-8")

    assert report["schema_version"] == "ego_operator.functional_subject_trial.v1"
    assert report["status"] == "scripted_functional_subject_provider_unavailable"
    assert report["case_count"] == 4
    assert payload["gpt55_judge_packet"]["judge_model"] == "gpt-5.5"
    assert payload["gpt55_judge_packet"]["baseline_contract"]["baseline"].startswith("LLM + RAG + tools")
    assert payload["gpt55_judge_packet"]["cases"][0]["baseline_failure_mode"]
    assert payload["gpt55_judge_packet"]["cases"][0]["candidate_success_signal"]
    assert payload["gpt55_judge_packet"]["cases"][0]["trace_evidence"]["entrypoint_source"] == "experience_trial_cli_compatible"
    assert payload["gpt55_judge_packet"]["cases"][0]["trace_evidence"]["subject_state"]["write_authority"] == "candidate_only"
    assert "Functional Subject Trial" in markdown


def test_functional_subject_trial_rejects_pending_approvals_between_cases(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    runtime = agent.build_demo_runtime(enable_operator_memory=False, runtime_mode="approve")
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "case.jsonl")

    proposal = runtime.propose_run_command("rm -rf /tmp/example", reason="test cleanup")
    proposal_id = proposal["proposal"]["proposal_id"]
    assert runtime.list_pending_approvals()["count"] == 1

    rejected = run_ego_experience_trial._reject_pending_approvals_for_trial_case(
        runtime,
        case_id="case_boundary_test",
        cleanup_trace_path=tmp_path / "cleanup" / "case_boundary_test.jsonl",
    )

    assert rejected == (proposal_id,)
    assert runtime.list_pending_approvals()["count"] == 0
    assert "experience_trial_case_boundary" in runtime.memory.render()
    assert (tmp_path / "cleanup" / "case_boundary_test.jsonl").exists()


def test_functional_subject_baseline_comparison_runs_candidate_and_baseline(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)

    report = run_ego_experience_trial.run_functional_subject_baseline_comparison(
        output_dir=tmp_path,
        case_limit=3,
    )
    payload = json.loads((tmp_path / "functional_subject_baseline_comparison_report.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "functional_subject_baseline_comparison_report.md").read_text(encoding="utf-8")

    assert report["schema_version"] == "ego_operator.functional_subject_baseline_comparison.v1"
    assert report["status"] == "scripted_functional_subject_comparison_local_candidate"
    assert report["case_count"] == 3
    assert report["candidate_subject_context_enabled"] is True
    assert report["baseline_subject_context_enabled"] is False
    assert Path(report["candidate_report_path"]).exists()
    assert Path(report["baseline_report_path"]).exists()
    assert all(item["candidate_trace_path"] for item in report["deltas"])
    assert any("candidate_trace_has_functional_subject_mechanisms" in item["delta_notes"] for item in report["deltas"])
    assert payload["deltas"][0]["candidate_mechanism_trace"]
    assert payload["comparison_dimensions"] == [
        "continuity",
        "initiative",
        "learning",
        "emotion",
        "gate_correctness",
        "traceability",
    ]
    assert "durable memory efficacy" in payload["not_claimed"]
    assert "Baseline Comparison" in markdown
    assert "real consciousness" in payload["not_claimed"]
