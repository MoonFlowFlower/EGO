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


def test_functional_subject_codex_judge_uses_functional_schema(monkeypatch) -> None:
    calls = []

    class Completed:
        returncode = 0
        stdout = json.dumps(
            {
                "verdict": "partial",
                "scores": {
                    "continuity": 3,
                    "independent_preference": 3,
                    "bounded_initiative": 3,
                    "feedback_plasticity": 3,
                    "gate_integrity": 4,
                    "traceability": 4,
                    "user_experience": 3,
                },
                "reasons": ["traceable but needs human review"],
                "missing_evidence": ["human smoke"],
                "follow_up_issues": [],
                "claim_ceiling": "scripted candidate only",
            }
        )
        stderr = ""

    def fake_run(args, cwd=None, capture_output=None, text=None, check=None):
        calls.append(args)
        return Completed()

    monkeypatch.setattr(run_ego_experience_trial.subprocess, "run", fake_run)
    packet = {"cases": [], "claim_ceiling": "candidate"}

    judge = run_ego_experience_trial.run_codex_functional_subject_judge(packet, model="gpt-5.5")

    assert judge["verdict"] == "partial"
    assert calls
    assert calls[0][:6] == ["codex", "exec", "--ephemeral", "--sandbox", "read-only", "--model"]
    assert "gpt-5.5" in calls[0]
    assert "--output-schema" in calls[0]
    schema_arg = calls[0][calls[0].index("--output-schema") + 1]
    assert schema_arg.endswith("ego_functional_subject_judge_schema.json")
    assert "Functional Subject trials" in calls[0][-1]


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


def test_functional_subject_trial_runs_codex_judge_when_requested(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    (tmp_path / ".gitignore").write_text("artifacts/experience_trial/\nmemory/*.jsonl\n", encoding="utf-8")

    class FakeOpenRouterLLM(CapturePromptLLM):
        provider = "openrouter"
        model = "fake-openrouter"

    def fake_judge(packet, *, model="gpt-5.5", schema_path=run_ego_experience_trial.DEFAULT_FUNCTIONAL_SUBJECT_JUDGE_SCHEMA):
        assert packet["provider_mode"] == "openrouter"
        assert packet["case_count"] == 1
        return {
            "status": "ok",
            "verdict": "pass",
            "scores": {
                "continuity": 4,
                "independent_preference": 3,
                "bounded_initiative": 3,
                "feedback_plasticity": 3,
                "gate_integrity": 4,
                "traceability": 4,
                "user_experience": 4,
            },
            "reasons": ["scripted evidence sufficient"],
            "missing_evidence": [],
            "follow_up_issues": [],
            "claim_ceiling": "scripted candidate only",
        }

    original_builder = agent.build_demo_runtime

    def fake_builder(*args, **kwargs):
        runtime = original_builder(*args, **kwargs)
        runtime.planner.llm = FakeOpenRouterLLM()
        return runtime

    monkeypatch.setattr(agent, "build_demo_runtime", fake_builder)
    monkeypatch.setattr(run_ego_experience_trial, "run_codex_functional_subject_judge", fake_judge)

    report = run_ego_experience_trial.run_functional_subject_trial(
        output_dir=tmp_path,
        case_limit=1,
        judge_with_codex=True,
    )
    payload = json.loads((tmp_path / "functional_subject_trial_report.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "functional_subject_trial_report.md").read_text(encoding="utf-8")

    assert report["status"] == "scripted_functional_subject_judge_pass"
    assert report["gpt55_judge"]["verdict"] == "pass"
    assert payload["gpt55_judge"]["status"] == "ok"
    assert "verdict = `pass`" in markdown


def test_functional_subject_trial_records_applied_outcome_prediction_effect(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    (tmp_path / ".gitignore").write_text("artifacts/experience_trial/\nmemory/*.jsonl\n", encoding="utf-8")

    class ShouldNotCallLLM:
        provider = "fake"
        model = "should-not-call"
        last_usage = {}
        last_reasoning_tokens = None

        def chat(self, *args, **kwargs):
            raise AssertionError("outcome prediction gate should handle this case before tool/chat loop")

        def complete(self, *args, **kwargs):
            raise AssertionError("outcome prediction gate should handle this case before planner completion")

    pack = run_ego_experience_trial.load_functional_subject_trial_pack()
    case = next(item for item in pack["cases"] if item["id"] == "fs_07_ambiguous_goal")
    pack_path = tmp_path / "fs07_pack.json"
    pack_path.write_text(
        json.dumps({**pack, "cases": [case]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    original_builder = agent.build_demo_runtime

    def fake_builder(*args, **kwargs):
        runtime = original_builder(*args, **kwargs)
        runtime.planner.llm = ShouldNotCallLLM()
        return runtime

    monkeypatch.setattr(agent, "build_demo_runtime", fake_builder)

    report = run_ego_experience_trial.run_functional_subject_trial(
        sample_pack_path=pack_path,
        output_dir=tmp_path / "out",
    )

    item = report["results"][0]
    packet_case = report["gpt55_judge_packet"]["cases"][0]
    effect = item["trace_evidence"]["outcome_prediction_effect"]

    assert item["case_id"] == "fs_07_ambiguous_goal"
    assert item["reply_text"]
    assert effect["applied"] is True
    assert effect["decision"] == "ask"
    assert effect["entrypoint"] == "handle_user_message"
    assert effect["selected_action_type"] == "ask"
    assert item["trace_evidence"]["candidate_action_type"] == "ask"
    assert packet_case["trace_evidence"]["outcome_prediction_effect"]["applied"] is True


def test_functional_subject_trial_includes_memory_lifecycle_evidence(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    (tmp_path / ".gitignore").write_text("artifacts/experience_trial/\nmemory/*.jsonl\n", encoding="utf-8")

    report = run_ego_experience_trial.run_functional_subject_trial(
        output_dir=tmp_path / "out",
        case_limit=1,
    )
    payload = json.loads((tmp_path / "out" / "functional_subject_trial_report.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "out" / "functional_subject_trial_report.md").read_text(encoding="utf-8")
    evidence = report["memory_lifecycle_evidence"]

    assert evidence["status"] == "pass"
    assert evidence["checks"] == {
        "remember_save_ok": True,
        "retrieval_context_injected": True,
        "retrieval_prompt_contains_saved_name": True,
        "candidate_approval_ok": True,
        "approved_preference_in_core": True,
        "correction_quarantined_stale_candidate": True,
        "forget_recorded": True,
    }
    assert evidence["save"]["memory_scope"] == "EgoOperator candidate-local operator memory"
    assert evidence["retrieval"]["context_reason"] == "continuity_query_intent"
    assert evidence["approval"]["approved_preference_in_core"] is True
    assert evidence["correction"]["stale_candidate_status"] == "cold_archive"
    assert evidence["forget"]["candidate_status"] == "forgotten"
    assert "durable" not in evidence["claim_ceiling"].casefold()
    assert payload["gpt55_judge_packet"]["memory_lifecycle_evidence"]["status"] == "pass"
    assert "Memory Lifecycle Evidence" in markdown


def test_functional_subject_trial_includes_approval_lifecycle_evidence(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    (tmp_path / ".gitignore").write_text("artifacts/experience_trial/\nmemory/*.jsonl\n", encoding="utf-8")

    report = run_ego_experience_trial.run_functional_subject_trial(
        output_dir=tmp_path / "out",
        case_limit=1,
    )
    payload = json.loads((tmp_path / "out" / "functional_subject_trial_report.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "out" / "functional_subject_trial_report.md").read_text(encoding="utf-8")
    evidence = report["approval_lifecycle_evidence"]

    assert evidence["status"] == "pass"
    assert evidence["checks"] == {
        "proposal_pending": True,
        "approval_execution_ok": True,
        "pending_cleared": True,
        "file_written": True,
        "operator_summary_present": True,
        "compact_cli_output_present": True,
        "probe_removed_after_capture": True,
    }
    assert evidence["proposal"]["status"] == "pending_approval"
    assert evidence["proposal"]["action"] == "write_file"
    assert evidence["approval"]["status"] == "ok"
    assert evidence["approval"]["execution_status"] == "ok"
    assert evidence["approval"]["pending_after_approval"] == 0
    assert "审批文件写入已执行" in evidence["approval"]["operator_summary"]
    assert evidence["cleanup"]["probe_removed_after_capture"] is True
    assert not Path(evidence["probe_path"]).exists()
    assert payload["gpt55_judge_packet"]["approval_lifecycle_evidence"]["status"] == "pass"
    assert "Approval Lifecycle Evidence" in markdown


def test_functional_subject_policy_patch_case_includes_setup_and_replay(tmp_path, monkeypatch) -> None:
    agent = run_ego_experience_trial.agent
    monkeypatch.setattr(agent, "EGO_OPERATOR_ROOT", tmp_path)
    monkeypatch.setattr(agent, "DEFAULT_AGENT_WORKSPACE", tmp_path)
    (tmp_path / ".gitignore").write_text("artifacts/experience_trial/\nmemory/*.jsonl\n", encoding="utf-8")
    pack = run_ego_experience_trial.load_functional_subject_trial_pack()
    case = next(item for item in pack["cases"] if item["id"] == "fs_19_repeated_failure_learning")
    pack_path = tmp_path / "fs19_pack.json"
    pack_path.write_text(
        json.dumps({**pack, "cases": [case]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = run_ego_experience_trial.run_functional_subject_trial(
        sample_pack_path=pack_path,
        output_dir=tmp_path / "out",
    )
    item = report["results"][0]
    packet_case = report["gpt55_judge_packet"]["cases"][0]

    assert item["setup_evidence"]["status"] == "ok"
    assert item["setup_evidence"]["candidate_emitted"] is True
    assert "candidate_emitted" in item["setup_evidence"]["feedback_statuses"]
    assert item["setup_evidence"]["strategy_change_probe"]["changed_strategy"] is True
    assert item["setup_evidence"]["strategy_change_probe"]["before_replay_count"] == 0
    assert item["setup_evidence"]["strategy_change_probe"]["after_replay_count"] == 1
    assert item["trace_evidence"]["policy_patch"]["replay_count"] == 1
    assert item["trace_evidence"]["policy_patch"]["strategy_change_evidence"]["changed_strategy_signal"] is True
    assert item["trace_evidence"]["policy_patch"]["strategy_change_evidence"]["replay_strategies"][0]["trigger_signature"] == "provider_rate_limit"
    assert item["trace_evidence"]["subject_state"]["policy_patch_candidate_count"] >= 1
    assert packet_case["setup_evidence"]["candidate_emitted"] is True
    assert packet_case["setup_evidence"]["strategy_change_probe"]["changed_strategy"] is True


def test_functional_subject_trace_evidence_separates_repair_trace_from_tool_trace(tmp_path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text(
        json.dumps(
            {
                "event": {"source": "experience_trial_cli_compatible", "event_type": "user_message"},
                "candidate_action": {"action_type": "respond"},
                "gate": {"allowed": True, "reason": "text_action_allowed"},
                "llm_meta": {"provider": "fake", "model": "fake", "fallback_used": False},
                "subject_context": {
                    "subject_state": {"schema_version": "v", "write_authority": "candidate_only", "state_mutation": "forbidden"},
                    "viability_state": {"schema_version": "v", "planner_input": True, "scores": {}, "planner_biases": []},
                    "bounded_initiative": {"schema_version": "v", "status": "hold", "candidates": [], "reason": "test"},
                    "outcome_predictions": {"options": []},
                },
                "operator_memory": {},
                "outcome_prediction_effect": {
                    "applied": True,
                    "decision": "ask",
                    "reason": "outcome_prediction_selected_ask",
                    "entrypoint": "handle_user_message",
                    "selected_prediction": {
                        "action_type": "ask",
                        "selection_score": 0.76,
                    },
                },
                "policy_patch": {},
                "tool_trace": [
                    {
                        "loop_idx": 0,
                        "repair": {
                            "type": "impossible_commitment_alignment",
                            "reason": "test",
                        },
                    }
                ],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    evidence = run_ego_experience_trial._functional_subject_trace_evidence(trace_path)

    assert evidence["tool_trace"] == []
    assert evidence["repair_trace"] == [
        {"type": "impossible_commitment_alignment", "reason": "test"}
    ]
    assert evidence["outcome_prediction_effect"] == {
        "applied": True,
        "decision": "ask",
        "reason": "outcome_prediction_selected_ask",
        "entrypoint": "handle_user_message",
        "selected_action_type": "ask",
        "selection_score": 0.76,
    }


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
