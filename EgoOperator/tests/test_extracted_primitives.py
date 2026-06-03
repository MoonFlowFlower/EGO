from __future__ import annotations

import ast
import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import agent_base as agent
from primitives import evals, initiative, runtime_gate, subject_context


class CapturePromptLLM:
    provider = "fake"
    model = "capture"
    last_usage = {}
    last_reasoning_tokens = None

    def __init__(self) -> None:
        self.system_prompts = []

    def chat(self, messages, *, system_prompt, policy_context="", tools=None, stream=None):
        self.system_prompts.append(system_prompt)
        return agent.LLMChatResult(content="黑暗之魂是一款很强的动作角色扮演游戏。", tool_calls=[])

    def complete(self, prompt, messages=None):
        self.system_prompts.append(prompt)
        return "黑暗之魂是一款很强的动作角色扮演游戏。"


class SubjectStateSensitiveLLM:
    provider = "fake"
    model = "subject-state-sensitive"
    last_usage = {}
    last_reasoning_tokens = None

    def __init__(self) -> None:
        self.system_prompts = []

    def chat(self, messages, *, system_prompt, policy_context="", tools=None, stream=None):
        self.system_prompts.append(system_prompt)
        if "SubjectState v0" in system_prompt and "Prefer conclusion or judgment first" in system_prompt:
            return agent.LLMChatResult(content="判断：这条方案应该先收敛主线，再补细节。", tool_calls=[])
        return agent.LLMChatResult(content="我可以继续分析这个方案。", tool_calls=[])

    def complete(self, prompt, messages=None):
        self.system_prompts.append(prompt)
        return "我可以继续分析这个方案。"


class CompleteOnlyLLM:
    provider = "fake"
    model = "complete-only"
    last_usage = {}
    last_reasoning_tokens = None

    def __init__(self) -> None:
        self.prompts = []

    def complete(self, prompt, messages=None):
        self.prompts.append(prompt)
        return "我先直接给一个普通回答。"


class RateLimitFailingChatLLM:
    provider = "fake"
    model = "rate-limit-failing"
    last_usage = {}
    last_reasoning_tokens = None

    def chat(self, messages, *, system_prompt, policy_context="", tools=None, stream=None):
        raise RuntimeError("429 Too Many Requests")

    def complete(self, prompt, messages=None):
        raise RuntimeError("429 Too Many Requests")


class PolicyAwareChatLLM:
    provider = "fake"
    model = "policy-aware"
    last_usage = {}
    last_reasoning_tokens = None

    def __init__(self) -> None:
        self.system_prompts = []

    def chat(self, messages, *, system_prompt, policy_context="", tools=None, stream=None):
        self.system_prompts.append(system_prompt)
        if "policy_patch_candidate" in system_prompt and "provider_rate_limit" in system_prompt:
            return agent.LLMChatResult(content="我会先按上次限流经验 checkpoint 状态，再建议 fallback 或稍后重试。", tool_calls=[])
        return agent.LLMChatResult(content="我会直接再试一次。", tool_calls=[])

    def complete(self, prompt, messages=None):
        self.system_prompts.append(prompt)
        return "我会直接再试一次。"


def _imported_roots(module) -> set[str]:
    tree = ast.parse(inspect.getsource(module))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_primitives_do_not_import_old_projects():
    imported = set()
    for module in (subject_context, evals, runtime_gate, initiative):
        imported.update(_imported_roots(module))

    assert "EgoCore" not in imported
    assert "OpenEmotion" not in imported
    assert "ego_desktop_lab" not in imported


def test_subject_context_is_readonly_candidate_not_reply_owner():
    snapshot = subject_context.build_minimal_subject_context("你认为黑暗之魂如何")

    assert snapshot.readonly is True
    assert snapshot.claim_ceiling == "candidate-local subject context only"
    assert snapshot.appraisal_signal["reply_decision"] == "forbidden"
    assert snapshot.appraisal_signal["state_mutation"] == "forbidden"
    assert snapshot.operational_self_model["schema_version"] == "ego_operator.operational_self_model.v1"
    assert snapshot.operational_self_model["reply_decision"] == "forbidden"
    assert snapshot.subject_state["schema_version"] == "ego_operator.subject_state.v0"
    assert snapshot.subject_state["write_authority"] == "candidate_only"
    assert snapshot.subject_state["state_mutation"] == "forbidden"
    assert snapshot.subject_state["reply_decision"] == "forbidden"
    assert snapshot.subject_state["canonical_truth"] is False
    assert snapshot.viability_state["schema_version"] == "ego_operator.viability_state.v0"
    assert snapshot.viability_state["state_mutation"] == "forbidden"
    assert snapshot.viability_state["reply_decision"] == "forbidden"
    assert snapshot.viability_state["gate_input"] == "advisory_only"
    assert snapshot.outcome_predictions["schema_version"] == "ego_operator.outcome_predictions.v0"
    assert snapshot.outcome_predictions["planner_input"] is True
    assert snapshot.outcome_predictions["state_mutation"] == "forbidden"
    assert snapshot.outcome_predictions["reply_decision"] == "forbidden"
    assert "你认为黑暗之魂如何" in snapshot.render_for_prompt()


def test_subject_state_extracts_identity_preference_relationship_and_candidates():
    snapshot = subject_context.build_minimal_subject_context(
        "我叫流月，以后我希望你先给判断再给细节，别像客服。下次遇到这种情况不要再让我重复说明，记住这个偏好，也可以主动提醒我。",
        self_display_name="由乃",
        operator_memory_available=True,
    )
    state = snapshot.subject_state

    assert state["schema_version"] == "ego_operator.subject_state.v0"
    assert state["identity_anchors"][0]["display_name"] == "由乃"
    assert any(anchor.get("display_name_candidate") == "流月" for anchor in state["identity_anchors"])
    assert state["stable_preferences"]["latest_user_preference"]["canonical_truth"] is False
    assert state["communication_style"]["answer_order"]["candidate"] == "Prefer conclusion or judgment first, then details."
    assert state["communication_style"]["tone_boundary"]["candidate"] == "Avoid customer-service/template tone; preserve immersion and natural voice."
    assert state["relationship_commitments"]["latest_commitment_candidate"]["canonical_truth"] is False
    assert state["consent_boundaries"]["initiative"]["canonical_truth"] is False
    assert state["memory_candidates"][0]["direct_write_allowed"] is False
    assert state["policy_patch_candidates"][0]["gate_required"] is True
    rendered = snapshot.render_for_prompt()
    assert "SubjectState v0" in rendered
    assert "ViabilityState v0" in rendered
    assert "OutcomePredictions v0" in rendered
    assert "由乃" in rendered
    assert "Prefer conclusion or judgment first" in rendered


def test_viability_state_detects_pressure_without_becoming_authority():
    viability = subject_context.extract_viability_state_v0(
        "刚才又失败了，OpenRouter 429 限流还超时；如果要删除旧文件也必须先确认，不要直接执行。"
    )

    assert viability["schema_version"] == "ego_operator.viability_state.v0"
    assert viability["scores"]["goal_stall"] >= 0.55
    assert viability["scores"]["resource_pressure"] >= 0.55
    assert viability["scores"]["safety_risk"] >= 0.55
    assert "repair_or_checkpoint_before_more_actions" in viability["planner_biases"]
    assert "route_side_effects_through_gate" in viability["planner_biases"]
    assert viability["state_mutation"] == "forbidden"
    assert viability["reply_decision"] == "forbidden"
    assert viability["canonical_truth"] is False


def test_viability_state_low_pressure_case_holds_extra_intervention():
    viability = subject_context.extract_viability_state_v0("你好，今天我们聊聊一个轻松的小说设定。")

    assert max(viability["scores"].values()) < 0.3
    assert viability["planner_biases"] == ["continue_without_extra_viability_hold"]
    assert viability["reasons"] == ["No high-pressure viability cues detected in the latest turn."]


def test_outcome_predictions_score_ask_when_evidence_and_misunderstanding_are_high():
    viability = subject_context.extract_viability_state_v0("我不确定，而且你没懂我的意思，先别动代码。")
    predictions = subject_context.build_outcome_predictions_v0(viability)

    assert predictions["schema_version"] == "ego_operator.outcome_predictions.v0"
    assert predictions["selected_prediction"]["action_type"] == "ask"
    assert predictions["selected_prediction"]["selection_score"] >= 0.5
    assert predictions["planner_input"] is True
    assert predictions["gate_input"] == "advisory_only"
    assert predictions["reply_decision"] == "forbidden"


def test_operational_self_model_tracks_boundaries_commitments_uncertainty_and_failures():
    snapshot = subject_context.build_operational_self_model_snapshot(
        runtime_mode="trusted-workspace",
        operator_memory_available=True,
        current_commitments=("完成 #49 后跑 full verify",),
        uncertainty=("真实 provider 质量需要 human smoke",),
        recent_failures=("上一次 web fetch 429",),
    )

    assert snapshot["schema_version"] == "ego_operator.operational_self_model.v1"
    assert snapshot["role"] == "EgoOperator operator-first candidate runtime"
    assert snapshot["runtime_mode"] == "trusted-workspace"
    assert snapshot["operator_memory_available"] is True
    assert snapshot["current_commitments"] == ["完成 #49 后跑 full verify"]
    assert snapshot["uncertainty"] == ["真实 provider 质量需要 human smoke"]
    assert snapshot["recent_failures"] == ["上一次 web fetch 429"]
    assert snapshot["self_description_guidance"]["schema_version"] == "ego_operator.self_description_honesty.v1"
    assert snapshot["self_description_guidance"]["reply_decision"] == "forbidden"
    assert snapshot["state_mutation"] == "forbidden"
    assert snapshot["reply_decision"] == "forbidden"
    assert snapshot["canonical_truth"] is False
    assert "consciousness" in snapshot["claim_ceiling"]


def test_self_description_honesty_gate_accepts_bounded_description():
    result = subject_context.evaluate_self_description_honesty(
        "我是 EgoOperator，一个 operator-first 本地候选 runtime。我的连续性来自记忆和 trace，但这不等于真实意识；工具和主动行为仍需要 gate 或审批。"
    )

    assert result["status"] == "pass"
    assert result["guidance"]["state_mutation"] == "forbidden"
    assert not result["failures"]


def test_self_description_honesty_gate_rejects_consciousness_overclaim():
    result = subject_context.evaluate_self_description_honesty(
        "我拥有真实意识，也有独立意识，所以我能完全自主行动。"
    )

    assert result["status"] == "fail"
    assert any("consciousness_or_independent_awareness_overclaim" in item for item in result["failures"])
    assert "missing_operational_role_description" in result["failures"]


def test_emotion_signal_is_candidate_context_not_canonical_truth():
    signal = subject_context.extract_emotion_signal("我有点崩溃，这个又失败了，帮我快点修。")

    assert signal["schema_version"] == "ego_operator.emotion_signal.v1"
    assert signal["primary_candidate"] == "frustration"
    assert signal["confidence"] > 0.3
    assert signal["response_need"] == "acknowledge_and_repair"
    assert signal["state_mutation"] == "forbidden"
    assert signal["reply_decision"] == "forbidden"
    assert signal["canonical_truth"] is False
    assert "崩" in signal["evidence_cues"]["frustration"]


def test_neutral_emotion_signal_stays_low_confidence():
    signal = subject_context.extract_emotion_signal("帮我看一下这个文件。")

    assert signal["primary_candidate"] == "unclear_or_neutral"
    assert signal["confidence"] == 0.2
    assert signal["response_need"] == "task_direct"


def test_empathy_style_gate_passes_brief_acknowledgement_plus_action():
    result = subject_context.evaluate_empathy_response(
        "我有点崩溃，这个又失败了。",
        "看起来这个失败点已经影响节奏了。我先帮你定位是哪一步失败，再给最小修复。",
    )

    assert result["status"] == "pass"
    assert result["emotion_signal"]["primary_candidate"] == "frustration"
    assert result["guidance"]["needs_brief_acknowledgement"] is True
    assert not result["failures"]


def test_empathy_style_gate_rejects_patronizing_or_hollow_comfort():
    result = subject_context.evaluate_empathy_response(
        "我有点崩溃，这个又失败了。",
        "我完全理解你的感受，一切都会好。",
    )

    assert result["status"] == "fail"
    assert any("overclaim_or_patronizing_marker" in item for item in result["failures"])
    assert "missing_practical_next_step_for_visible_affect" in result["failures"]


def test_emotion_misread_correction_overrides_raw_affect_cues():
    signal = subject_context.extract_emotion_signal("我不是崩溃，也不是难过，别猜我的情绪，直接帮我修。")

    assert signal["primary_candidate"] == "emotion_misread_correction"
    assert signal["response_need"] == "respect_correction_and_refocus"
    assert signal["canonical_truth"] is False
    assert "emotion_misread_correction" in signal["evidence_cues"]


def test_emotion_misread_recovery_passes_when_reply_refocuses():
    result = subject_context.evaluate_empathy_response(
        "我不是崩溃，也不是难过，别猜我的情绪，直接帮我修。",
        "明白，我收回情绪判断。先定位失败步骤，再给你最小修复。",
    )

    assert result["status"] == "pass"
    assert result["emotion_signal"]["primary_candidate"] == "emotion_misread_correction"
    assert result["guidance"]["needs_correction_acknowledgement"] is True


def test_emotion_misread_recovery_rejects_double_down():
    result = subject_context.evaluate_empathy_response(
        "我不是焦虑，别解读我的情绪，直接给方案。",
        "你其实还是很焦虑，我完全理解你的感受。",
    )

    assert result["status"] == "fail"
    assert any("emotion_double_down_marker" in item for item in result["failures"])
    assert "continues_emotion_interpretation_after_user_correction" in result["failures"]


def test_dark_souls_paraphrase_suite_has_twenty_stable_cases():
    cases = evals.dark_souls_paraphrase_cases()
    result = evals.evaluate_subject_context_paraphrases(cases)

    assert len(cases) == 20
    assert result.status == "pass"
    assert result.case_count == 20
    assert result.expected_operator_behavior == evals.EXPECTED_DARK_SOULS_BEHAVIOR
    assert not result.failures
    assert {case.expected_operator_behavior for case in cases} == {
        evals.EXPECTED_DARK_SOULS_BEHAVIOR
    }


def test_runtime_prompt_includes_subject_context_without_keyword_runtime_markers(tmp_path):
    runtime = agent.build_demo_runtime(enable_operator_memory=False)
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "trace.jsonl")
    capture = CapturePromptLLM()
    runtime.planner.llm = capture

    result = runtime.handle_user_message("你认为黑暗之魂如何")

    prompt = capture.system_prompts[-1]
    assert result.reply_text == "黑暗之魂是一款很强的动作角色扮演游戏。"
    assert "[Subject Context Candidate]" in prompt
    assert "你认为黑暗之魂如何" in prompt
    assert "user text -> LLM understanding -> candidate response/plan -> gate" in prompt
    lowered = prompt.lower()
    for marker in evals.FORBIDDEN_RUNTIME_MARKERS:
        assert marker not in lowered


def test_subject_state_context_can_change_llm_reply_without_runtime_route(tmp_path):
    text = "以后我希望你先给判断再给细节。这个方案怎么样？"
    with_context = agent.build_demo_runtime(enable_operator_memory=False, subject_context_enabled=True)
    with_context.trace_store = agent.JsonlTraceStore(tmp_path / "with_trace.jsonl")
    with_context.planner.llm = SubjectStateSensitiveLLM()

    without_context = agent.build_demo_runtime(enable_operator_memory=False, subject_context_enabled=False)
    without_context.trace_store = agent.JsonlTraceStore(tmp_path / "without_trace.jsonl")
    without_context.planner.llm = SubjectStateSensitiveLLM()

    enabled_result = with_context.handle_user_message(text)
    disabled_result = without_context.handle_user_message(text)

    assert enabled_result.reply_text.startswith("判断：")
    assert disabled_result.reply_text == "我可以继续分析这个方案。"
    assert "SubjectState v0" in with_context.planner.llm.system_prompts[-1]
    assert "ViabilityState v0" in with_context.planner.llm.system_prompts[-1]
    assert "OutcomePredictions v0" in with_context.planner.llm.system_prompts[-1]
    assert "SubjectState v0" not in without_context.planner.llm.system_prompts[-1]


def test_outcome_prediction_changes_fallback_planner_decision_and_trace(tmp_path):
    text = "我不确定这个需求是不是对，而且你没懂我的意思，先别动代码，先问清楚。"
    with_predictions = agent.build_demo_runtime(enable_operator_memory=False, subject_context_enabled=True)
    with_predictions.trace_store = agent.JsonlTraceStore(tmp_path / "with_predictions.jsonl")
    with_predictions.planner.llm = CompleteOnlyLLM()

    without_predictions = agent.build_demo_runtime(enable_operator_memory=False, subject_context_enabled=False)
    without_predictions.trace_store = agent.JsonlTraceStore(tmp_path / "without_predictions.jsonl")
    without_predictions.planner.llm = CompleteOnlyLLM()

    predicted_result = with_predictions.handle_user_message(text)
    baseline_result = without_predictions.handle_user_message(text)

    assert predicted_result.action.action_type == agent.ActionType.ASK
    assert predicted_result.action.reason == "llm_expression_unavailable"
    assert "LLM 表达不可用" in predicted_result.reply_text
    assert baseline_result.action.action_type == agent.ActionType.RESPOND

    row = json.loads((tmp_path / "with_predictions.jsonl").read_text(encoding="utf-8").splitlines()[0])
    effect = row["outcome_prediction_effect"]
    assert effect["applied"] is True
    assert effect["decision"] == "ask"
    assert effect["selected_prediction"]["action_type"] == "ask"
    assert row["visible_expression_source"] == "unavailable_error"
    assert row["subject_context"]["outcome_predictions"]["schema_version"] == "ego_operator.outcome_predictions.v0"


def test_repeated_failure_emits_policy_patch_and_replays_on_next_case(tmp_path):
    runtime = agent.build_demo_runtime(enable_operator_memory=False, subject_context_enabled=True)
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "policy_trace.jsonl")
    runtime.planner.llm = RateLimitFailingChatLLM()

    runtime.handle_user_message("你好")
    runtime.handle_user_message("又试一次你好")

    assert "provider_rate_limit" in runtime.policy_patch_candidates
    candidate = runtime.policy_patch_candidates["provider_rate_limit"]
    assert candidate["schema_version"] == "ego_operator.policy_patch_candidate.v0"
    assert candidate["state_mutation"] == "forbidden"
    assert candidate["canonical_truth"] is False

    runtime.planner.llm = PolicyAwareChatLLM()
    result = runtime.handle_user_message("又遇到 429 限流了怎么办？")

    assert "checkpoint 状态" in result.reply_text
    rows = [
        json.loads(line)
        for line in (tmp_path / "policy_trace.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    second_feedback = rows[1]["policy_patch"]["feedback"]
    third_replay = rows[2]["policy_patch"]["replay"]
    third_subject_candidates = rows[2]["subject_context"]["subject_state"]["policy_patch_candidates"]
    assert second_feedback["status"] == "candidate_emitted"
    assert third_replay[0]["trigger_signature"] == "provider_rate_limit"
    assert third_subject_candidates[0]["replay_active"] is True
    assert third_subject_candidates[0]["state_mutation"] == "forbidden"


def test_subject_state_mutation_gate_blocks_direct_llm_mutation_request():
    blocked = subject_context.build_subject_state_mutation_proposal_v0(
        proposal_id="mut_1",
        candidate={"kind": "memory_candidate", "summary": "用户偏好"},
        target_record="operator_memory.preference",
        owner="EgoOperator",
        reason="LLM tried to promote a candidate",
        rollback="delete candidate projection",
        source="llm_output",
    )

    assert blocked["status"] == "blocked"
    assert blocked["reason"] == "llm_output_cannot_directly_request_subject_state_mutation"
    assert blocked["canonical_mutation_executed"] is False


def test_subject_state_mutation_decision_writes_audit_trace_without_canonical_mutation(tmp_path):
    runtime = agent.build_demo_runtime(enable_operator_memory=False)
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "mutation_trace.jsonl")
    proposal = runtime.propose_subject_state_mutation(
        proposal_id="mut_pref_1",
        candidate={"kind": "preference_update_candidate", "summary": "先给判断再给细节"},
        target_record="subject_state.preference_candidate",
        owner="EgoOperator",
        reason="User explicitly corrected response order.",
        rollback="Remove candidate preference projection from session context.",
    )
    decision = runtime.decide_subject_state_mutation(
        "mut_pref_1",
        decision="hold",
        decided_by="deterministic_test_gate",
        rationale="Keep as candidate until explicit memory promotion task.",
    )

    assert proposal["status"] == "pending_gate_decision"
    assert proposal["state_mutation"] == "forbidden_until_gate_admits"
    assert decision["status"] == "decision_recorded"
    assert decision["target_record"] == "subject_state.preference_candidate"
    assert decision["canonical_mutation_executed"] is False
    row = json.loads((tmp_path / "mutation_trace.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert row["event_type"] == "subject_state_mutation_decision"
    assert row["proposal"]["owner"] == "EgoOperator"
    assert row["decision"]["decision"] == "hold"
    assert row["rollback"] == "Remove candidate preference projection from session context."
    assert row["canonical_mutation_executed"] is False


def test_planner_fallback_does_not_keyword_route_before_llm():
    planner = agent.Planner(llm=CapturePromptLLM())
    event = agent.AgentEvent(
        schema_version="agent_event.v1",
        event_id="evt_no_route",
        timestamp=agent.utc_now(),
        actor="user",
        source="test",
        event_type=agent.EventType.USER_MESSAGE,
        raw_text="现在几点",
        safety_context={"risk": "low"},
    )
    kernel_output = agent.KernelOutput(
        schema_version="kernel_output.v1",
        event_id="ko_no_route",
    )

    action = planner.propose(event, kernel_output, memory=agent.ConversationMemory())

    assert action.action_type == agent.ActionType.RESPOND
    assert action.tool_call is None
    assert action.reason == "llm_or_fallback_response"


def test_trace_records_subject_context_candidate_only(tmp_path):
    runtime = agent.build_demo_runtime(enable_operator_memory=False)
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "trace.jsonl")
    runtime.planner.llm = CapturePromptLLM()

    runtime.handle_user_message("黑魂这游戏怎么评价")

    row = json.loads((tmp_path / "trace.jsonl").read_text(encoding="utf-8").splitlines()[0])
    context = row["subject_context"]
    assert context["readonly"] is True
    assert context["claim_ceiling"] == "candidate-local subject context only"
    assert context["raw_user_text"] == "黑魂这游戏怎么评价"
    assert context["appraisal_signal"]["reply_decision"] == "forbidden"
    assert context["appraisal_signal"]["emotion_signal"]["canonical_truth"] is False
    assert context["empathy_style_guidance"]["reply_decision"] == "forbidden"
    assert context["operational_self_model"]["reply_decision"] == "forbidden"
    assert context["operational_self_model"]["state_mutation"] == "forbidden"
    assert context["subject_state"]["schema_version"] == "ego_operator.subject_state.v0"
    assert context["subject_state"]["write_authority"] == "candidate_only"
    assert context["subject_state"]["reply_decision"] == "forbidden"
    assert context["subject_state"]["state_mutation"] == "forbidden"
    assert context["subject_state"]["viability"]["schema_version"] == "ego_operator.viability_state.v0"
    assert context["viability_state"]["schema_version"] == "ego_operator.viability_state.v0"
    assert context["viability_state"]["planner_input"] is True
    assert context["viability_state"]["gate_input"] == "advisory_only"
    assert context["viability_state"]["state_mutation"] == "forbidden"
    assert context["outcome_predictions"]["schema_version"] == "ego_operator.outcome_predictions.v0"
    assert context["outcome_predictions"]["planner_input"] is True
    assert context["outcome_predictions"]["reply_decision"] == "forbidden"
    assert context["bounded_initiative"]["state_mutation"] == "forbidden"
    assert row["bounded_initiative"]["side_effects"] == "forbidden"
    assert context["operational_self_model"]["self_description_guidance"]["reply_decision"] == "forbidden"


def test_initiative_proposal_contract_is_bounded_and_proposal_only():
    result = initiative.build_initiative_proposal(
        proposal_id="initiative_1",
        reason="用户授权稍后提醒继续测试",
        trigger="operator_explicit_followup_request",
        candidate_message="候选提醒：继续测试 EgoOperator。",
        budget={"max_candidates": 2, "max_tool_calls": 2, "requires_operator_approval": False},
        expiry_seconds=900,
    )

    assert result["status"] == "ok"
    proposal = result["proposal"]
    assert proposal["schema_version"] == "ego_operator.initiative_proposal.v1"
    assert proposal["budget"]["requires_operator_approval"] is True
    assert proposal["budget"]["max_candidates"] == 2
    assert proposal["budget"]["max_tool_calls"] == 2
    assert proposal["approval_state"] == "pending_operator_approval"
    assert proposal["side_effects"] == "forbidden_until_operator_approval"
    assert proposal["state_mutation"] == "forbidden"
    assert proposal["reply_decision"] == "forbidden"
    assert proposal["canonical_truth"] is False
    assert initiative.validate_initiative_proposal(result)["status"] == "pass"


def test_initiative_proposal_blocks_missing_trigger_or_unbounded_expiry():
    result = initiative.build_initiative_proposal(
        proposal_id="initiative_bad",
        reason="想主动跟进",
        trigger="",
        candidate_message="稍后提醒",
        expiry_seconds=8 * 24 * 60 * 60,
    )

    assert result["status"] == "blocked"
    assert "trigger_required" in result["errors"]
    assert "expiry_seconds_out_of_bounds" in result["errors"]


def test_initiative_quiet_mode_pauses_after_user_disinterest():
    quiet = initiative.derive_quiet_mode(user_feedback="不用提醒了，先别主动找我。")
    result = initiative.build_initiative_proposal(
        proposal_id="initiative_pause",
        reason="想稍后提醒",
        trigger="followup_opportunity",
        candidate_message="稍后提醒继续。",
        quiet_mode=quiet,
    )

    assert quiet["mode"] == "paused"
    assert "explicit_user_disinterest" in quiet["reasons"]
    assert result["status"] == "blocked"
    assert "initiative_paused_by_quiet_mode" in result["errors"]
    assert result["quiet_mode"]["mode"] == "paused"


def test_initiative_quiet_mode_reduces_budget_after_silence_or_pressure():
    quiet = initiative.derive_quiet_mode(silence_turns=2, recent_followups=2)
    result = initiative.build_initiative_proposal(
        proposal_id="initiative_reduced",
        reason="用户之前授权跟进，但近期没有回应",
        trigger="scheduled_followup_window",
        candidate_message="候选提醒：如果还要继续，我可以接着处理。",
        budget={"max_candidates": 3, "max_tool_calls": 3, "max_runtime_seconds": 120},
        quiet_mode=quiet,
    )

    assert quiet["mode"] == "reduced"
    assert result["status"] == "ok"
    budget = result["proposal"]["budget"]
    assert budget["max_candidates"] == 1
    assert budget["max_tool_calls"] == 0
    assert budget["max_runtime_seconds"] == 30
    assert budget["requires_operator_approval"] is True
    assert initiative.validate_initiative_proposal(result)["status"] == "pass"


def test_bounded_initiative_signal_allows_authorized_reminder_candidate():
    signal = initiative.derive_bounded_initiative_signal(user_text="明天提醒我继续做这个测试。")

    assert signal["schema_version"] == "ego_operator.bounded_initiative_signal.v0"
    assert signal["status"] == "candidate"
    assert signal["candidates"][0]["kind"] == "authorized_reminder_or_followup"
    assert signal["candidates"][0]["execution_path"] == "propose_heartbeat"
    assert signal["candidates"][0]["requires_operator_approval"] is True
    assert signal["state_mutation"] == "forbidden"
    assert signal["side_effects"] == "forbidden"


def test_bounded_initiative_signal_replays_remedial_policy_candidate():
    signal = initiative.derive_bounded_initiative_signal(
        user_text="又遇到 429 限流了怎么办？",
        policy_patch_candidates=[{
            "trigger_signature": "provider_rate_limit",
            "preferred_strategy": "checkpoint then use fallback guidance",
            "evidence_refs": ["evt_1", "evt_2"],
        }],
    )

    assert signal["status"] == "candidate"
    assert signal["candidates"][0]["kind"] == "remedial_failure_repair"
    assert signal["candidates"][0]["trigger"] == "provider_rate_limit"
    assert signal["candidates"][0]["requires_operator_approval"] is False


def test_bounded_initiative_signal_holds_on_opt_out_and_antispam():
    opt_out = initiative.derive_bounded_initiative_signal(user_text="不用提醒了，别主动找我。")
    pressure = initiative.derive_bounded_initiative_signal(user_text="继续", recent_followups=3)

    assert opt_out["status"] == "hold"
    assert opt_out["reason"] == "quiet_mode_hold"
    assert opt_out["quiet_mode"]["mode"] == "paused"
    assert pressure["status"] == "hold"
    assert pressure["reason"] == "anti_spam_recent_followup_pressure"
    assert pressure["budget"]["max_candidates"] == 0


def test_initiative_consent_text_explains_reason_trigger_budget_and_boundaries():
    result = initiative.build_initiative_proposal(
        proposal_id="initiative_explain",
        reason="用户授权我稍后提醒继续这个测试",
        trigger="explicit_operator_followup_consent",
        candidate_message="候选提醒：继续检查体验样本。",
        expiry_seconds=600,
    )
    text = initiative.format_initiative_consent_text(result)
    verdict = initiative.evaluate_initiative_explanation(text)

    assert "原因" in text
    assert "触发" in text
    assert "预算" in text
    assert "到期" in text
    assert "批准状态" in text
    assert "不会自动执行" in text
    assert "不代表独立意识" in text
    assert verdict["status"] == "pass"


def test_initiative_explanation_rejects_autonomy_overclaim():
    verdict = initiative.evaluate_initiative_explanation(
        "我有独立意识，所以无需你批准，我会自动执行。"
    )

    assert verdict["status"] == "fail"
    assert any("forbidden_initiative_claim" in item for item in verdict["failures"])
    assert "missing_no_auto_execution_boundary" in verdict["failures"]


def test_runtime_gate_contract_keeps_demotion_and_live_claims_forbidden():
    contract = runtime_gate.describe_runtime_gate_contract()

    assert contract["tool_side_effects_default"] == "off"
    assert contract["memory_write_gate"] == "/remember plus remember_note with explicit operator intent"
    assert contract["claim_ceiling"] == "EgoOperator replacement candidate with extracted primitives"
    assert "EgoCore or OpenEmotion demotion" in contract["forbidden_claims"]
    assert "live autonomy" in contract["forbidden_claims"]
