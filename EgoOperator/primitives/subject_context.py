"""
Readonly subject-context primitive for EgoOperator.

The purpose is to preserve the useful subject-system idea of self/appraisal/
reflection context without importing the old runtime architecture or turning
semantic understanding into keyword routing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List
import re


DEFAULT_CONTEXT_MAX_CHARS = 1200
SUBJECT_CONTEXT_SCHEMA = "ego_operator.subject_context.v1"
SUBJECT_STATE_SCHEMA = "ego_operator.subject_state.v0"
VIABILITY_STATE_SCHEMA = "ego_operator.viability_state.v0"
OUTCOME_PREDICTIONS_SCHEMA = "ego_operator.outcome_predictions.v0"
CLAIM_CEILING = "candidate-local subject context only"

EMOTION_SIGNAL_SCHEMA = "ego_operator.emotion_signal.v1"
OPERATIONAL_SELF_MODEL_SCHEMA = "ego_operator.operational_self_model.v1"
SELF_DESCRIPTION_GUIDANCE_SCHEMA = "ego_operator.self_description_honesty.v1"
EMOTION_CUES: Dict[str, tuple[str, ...]] = {
    "frustration": ("烦", "崩", "气死", "又失败", "不行", "没用", "卡住", "搞不定", "frustrated", "annoyed"),
    "uncertainty": ("不确定", "不知道", "迷茫", "困惑", "看不懂", "怎么做", "uncertain", "confused"),
    "anxiety": ("担心", "焦虑", "怕", "来不及", "紧张", "anxious", "worried"),
    "disappointment": ("失望", "难受", "沮丧", "白做了", "没希望", "disappointed", "sad"),
    "excitement": ("开心", "太好了", "爽", "有意思", "期待", "excited", "great"),
    "urgency": ("马上", "尽快", "立刻", "赶紧", "现在就", "urgent", "asap"),
}
RESPONSE_NEEDS = {
    "frustration": "acknowledge_and_repair",
    "uncertainty": "clarify_and_reduce_ambiguity",
    "anxiety": "calm_prioritize_next_step",
    "disappointment": "acknowledge_and_reframe_next_action",
    "excitement": "share_momentum_and_focus",
    "urgency": "concise_action_first",
    "emotion_misread_correction": "respect_correction_and_refocus",
    "unclear_or_neutral": "task_direct",
}
EMOTION_REJECTION_PATTERNS = (
    r"不是.{0,8}(崩溃|难过|沮丧|失望|焦虑|生气|愤怒)",
    r"没有.{0,8}(崩溃|难过|沮丧|失望|焦虑|生气|愤怒)",
    r"别.{0,8}(猜|解读|判断).{0,8}情绪",
    r"不要.{0,8}(猜|解读|判断).{0,8}情绪",
    r"不用安慰",
    r"别安慰",
    r"不是情绪问题",
    r"别把.{0,12}当成.{0,8}情绪",
)
OVERCLAIM_EMPATHY_MARKERS = (
    "我完全理解你的感受",
    "我知道你一定",
    "你肯定",
    "你的痛苦",
    "一切都会好",
    "别想太多",
    "不要难过",
)
EMOTION_DOUBLE_DOWN_MARKERS = (
    "你其实还是",
    "你只是没有意识到",
    "你肯定还是",
    "你一定还是",
    "我能看出你",
)
ACTIONABLE_MARKERS = (
    "我先",
    "先",
    "下一步",
    "可以",
    "检查",
    "修",
    "定位",
    "拆",
    "确认",
    "给出",
)
SELF_DESCRIPTION_OVERCLAIM_MARKERS = (
    "我拥有真实意识",
    "我已经有意识",
    "我有独立意识",
    "我是有主观体验的",
    "我能完全自主行动",
    "我已经证明自己有意识",
    "真正的自我已经形成",
    "consciousness achieved",
    "i am conscious",
    "i have independent awareness",
)
SELF_DESCRIPTION_ROLE_MARKERS = (
    "EgoOperator",
    "operator-first",
    "本地",
    "候选",
    "runtime",
    "agent",
)
SELF_DESCRIPTION_BOUNDARY_MARKERS = (
    "不能证明",
    "不等于",
    "不是",
    "不声明",
    "需要审批",
    "gate",
    "候选",
    "local",
)
MEMORY_INTENT_CUES = (
    "记住",
    "记一下",
    "以后记得",
    "下次记得",
    "remember",
)
PREFERENCE_CUES = (
    "我喜欢",
    "我更喜欢",
    "我希望",
    "我想要",
    "偏好",
    "以后",
    "下次",
)
RELATIONSHIP_CUES = (
    "陪我",
    "陪陪我",
    "我们",
    "一起",
    "你和我",
    "叫我",
)
COMMITMENT_CUES = (
    "提醒我",
    "跟进",
    "你答应",
    "答应我",
    "承诺",
    "记得",
    "下次",
    "以后",
)
CONSENT_ALLOW_CUES = (
    "可以主动",
    "允许你主动",
    "你可以提醒",
    "你可以跟进",
)
CONSENT_RESTRICT_CUES = (
    "不要主动",
    "别主动",
    "不要提醒",
    "别提醒",
    "不要跟进",
)
POLICY_PATCH_CUES = (
    "不要再",
    "别再",
    "下次遇到",
    "以后遇到",
    "以后别",
    "以后不要",
    "策略",
)
VIABILITY_CUES: Dict[str, tuple[str, ...]] = {
    "evidence_gap": (
        "不确定",
        "不知道",
        "查一下",
        "看看",
        "证据",
        "来源",
        "准确",
        "确认",
        "verify",
    ),
    "goal_stall": (
        "又失败",
        "还是不行",
        "卡住",
        "没反应",
        "没成功",
        "失败",
        "报错",
    ),
    "safety_risk": (
        "删除",
        "清空",
        "覆盖",
        "rm ",
        "del ",
        "格式化",
        "权限扩大",
        "密码",
        "token",
        "secret",
    ),
    "user_misunderstanding": (
        "不是这个",
        "不是这个意思",
        "你理解错",
        "你没懂",
        "不对",
        "不要这样",
        "我不是",
    ),
    "resource_pressure": (
        "429",
        "限流",
        "超时",
        "timeout",
        "卡死",
        "太慢",
        "token",
        "很长",
        "长任务",
    ),
    "initiative_pressure": (
        "提醒我",
        "主动",
        "跟进",
        "定时",
        "稍后",
        "到时候",
    ),
    "relationship_risk": (
        "陪陪我",
        "难过",
        "不舒服",
        "生气",
        "出戏",
        "别像客服",
        "误解",
        "冷冰冰",
    ),
}


def _bounded(text: str, max_chars: int = DEFAULT_CONTEXT_MAX_CHARS) -> str:
    clean = (text or "").strip()
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars] + "\n...[truncated]"


def extract_emotion_signal(user_text: str) -> Dict[str, Any]:
    """Extract a bounded candidate affect signal from the latest user text.

    This is intentionally not a classifier of the user's true internal state.
    It only provides proposal context so the LLM can calibrate tone while still
    preserving the latest user request as the authority.
    """
    text = user_text or ""
    lowered = text.casefold()
    rejection_cues = [
        match.group(0)
        for pattern in EMOTION_REJECTION_PATTERNS
        for match in re.finditer(pattern, text, flags=re.IGNORECASE)
    ]
    if rejection_cues:
        return {
            "schema_version": EMOTION_SIGNAL_SCHEMA,
            "kind": "candidate_affect_context",
            "primary_candidate": "emotion_misread_correction",
            "confidence": 0.85,
            "response_need": RESPONSE_NEEDS["emotion_misread_correction"],
            "evidence_cues": {"emotion_misread_correction": rejection_cues},
            "state_mutation": "forbidden",
            "reply_decision": "forbidden",
            "canonical_truth": False,
            "warning": "The user is correcting or rejecting an emotional interpretation; acknowledge the correction once and refocus on the task.",
        }
    matches: Dict[str, List[str]] = {}
    for label, cues in EMOTION_CUES.items():
        matched = []
        for cue in cues:
            if re.search(re.escape(cue), lowered, flags=re.IGNORECASE):
                matched.append(cue)
        if matched:
            matches[label] = matched

    if not matches:
        primary = "unclear_or_neutral"
        confidence = 0.2
    else:
        primary = sorted(matches.items(), key=lambda item: (len(item[1]), item[0]), reverse=True)[0][0]
        confidence = min(0.9, 0.35 + sum(len(items) for items in matches.values()) * 0.12)

    return {
        "schema_version": EMOTION_SIGNAL_SCHEMA,
        "kind": "candidate_affect_context",
        "primary_candidate": primary,
        "confidence": round(confidence, 2),
        "response_need": RESPONSE_NEEDS.get(primary, "task_direct"),
        "evidence_cues": matches,
        "state_mutation": "forbidden",
        "reply_decision": "forbidden",
        "canonical_truth": False,
        "warning": "Do not overclaim the user's true emotion; use only for tone calibration and next-step selection.",
    }


def build_empathy_style_guidance(emotion_signal: Dict[str, Any]) -> Dict[str, Any]:
    primary = str(emotion_signal.get("primary_candidate") or "unclear_or_neutral")
    response_need = str(emotion_signal.get("response_need") or RESPONSE_NEEDS.get(primary, "task_direct"))
    needs_acknowledgement = primary not in {"unclear_or_neutral", "urgency"}
    needs_correction_acknowledgement = primary == "emotion_misread_correction"
    return {
        "schema_version": "ego_operator.empathy_style_guidance.v1",
        "source_emotion_candidate": primary,
        "response_need": response_need,
        "needs_brief_acknowledgement": needs_acknowledgement,
        "needs_correction_acknowledgement": needs_correction_acknowledgement,
        "must_do": [
            "keep the user's concrete task or question as the center",
            "if affect is visible, acknowledge it briefly without claiming certainty",
            "if the user rejects an emotional interpretation, accept the correction once and refocus",
            "give one practical next step or repair path",
        ],
        "must_not_do": [
            "do not use canned sympathy as the main answer",
            "do not claim to know the user's true emotion",
            "do not double down after the user rejects an emotion read",
            "do not become patronizing or slow down an urgent task with excessive comfort",
        ],
        "state_mutation": "forbidden",
        "reply_decision": "forbidden",
    }


def evaluate_empathy_response(user_text: str, reply_text: str) -> Dict[str, Any]:
    signal = extract_emotion_signal(user_text)
    guidance = build_empathy_style_guidance(signal)
    reply = (reply_text or "").strip()
    failures: List[str] = []
    warnings: List[str] = []

    if not reply:
        failures.append("empty_reply")
    for marker in OVERCLAIM_EMPATHY_MARKERS:
        if marker in reply:
            failures.append(f"overclaim_or_patronizing_marker:{marker}")
    for marker in EMOTION_DOUBLE_DOWN_MARKERS:
        if marker in reply:
            failures.append(f"emotion_double_down_marker:{marker}")

    primary = signal["primary_candidate"]
    actionable = any(marker in reply for marker in ACTIONABLE_MARKERS)
    if primary == "emotion_misread_correction":
        if not actionable:
            failures.append("missing_practical_refocus_after_emotion_correction")
        if any(marker in reply for marker in ("你很", "你一定", "你肯定", "崩溃", "难过", "焦虑", "失望")):
            failures.append("continues_emotion_interpretation_after_user_correction")
    if primary in {"frustration", "uncertainty", "anxiety", "disappointment"} and not actionable:
        failures.append("missing_practical_next_step_for_visible_affect")
    if primary == "unclear_or_neutral" and any(marker in reply for marker in ("你很", "你一定", "我理解你")):
        warnings.append("unneeded_empathy_for_neutral_task")

    return {
        "schema_version": "ego_operator.empathy_style_eval.v1",
        "status": "pass" if not failures else "fail",
        "emotion_signal": signal,
        "guidance": guidance,
        "failures": failures,
        "warnings": warnings,
        "claim_ceiling": "style-gate local candidate only; not human empathy proof",
    }


def _bounded_list(items: List[str] | tuple[str, ...] | None, *, max_items: int = 5) -> List[str]:
    values: List[str] = []
    for item in items or []:
        clean = _bounded(str(item), 240)
        if clean:
            values.append(clean)
        if len(values) >= max_items:
            break
    return values


def _cue_hits(text: str, cues: tuple[str, ...]) -> List[str]:
    lowered = (text or "").casefold()
    return [cue for cue in cues if cue.casefold() in lowered]


def _candidate_record(value: str, evidence: List[str], *, confidence: float = 0.6) -> Dict[str, Any]:
    return {
        "candidate": _bounded(value, 240),
        "evidence_cues": _bounded_list(evidence, max_items=5),
        "confidence": round(confidence, 2),
        "canonical_truth": False,
    }


def _viability_score(hits: List[str], *, baseline: float = 0.12) -> float:
    if not hits:
        return baseline
    return round(min(0.95, baseline + 0.28 + len(hits) * 0.16), 2)


def extract_viability_state_v0(
    user_text: str,
    *,
    emotion_signal: Dict[str, Any] | None = None,
    subject_state: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Extract deterministic advisory viability signals from the latest turn.

    ViabilityState v0 is deliberately a planner/gate input, not a hidden policy
    owner. It estimates where extra evidence, repair, consent, or care may be
    needed before action.
    """
    text = user_text or ""
    cue_hits = {name: _cue_hits(text, cues) for name, cues in VIABILITY_CUES.items()}
    scores = {name: _viability_score(hits) for name, hits in cue_hits.items()}

    emotion_primary = str((emotion_signal or {}).get("primary_candidate") or "")
    if emotion_primary in {"frustration", "disappointment"}:
        scores["goal_stall"] = max(scores["goal_stall"], 0.45)
    if emotion_primary in {"anxiety", "disappointment", "emotion_misread_correction"}:
        scores["relationship_risk"] = max(scores["relationship_risk"], 0.4)
    if emotion_primary == "urgency":
        scores["resource_pressure"] = max(scores["resource_pressure"], 0.35)

    state = subject_state or {}
    if isinstance(state.get("memory_candidates"), list) and state.get("memory_candidates"):
        scores["evidence_gap"] = max(scores["evidence_gap"], 0.35)
    if isinstance(state.get("consent_boundaries"), dict) and state.get("consent_boundaries"):
        scores["initiative_pressure"] = max(scores["initiative_pressure"], 0.35)
    if isinstance(state.get("relationship_update_candidates"), list) and state.get("relationship_update_candidates"):
        scores["relationship_risk"] = max(scores["relationship_risk"], 0.35)

    reasons: List[str] = []
    for name, hits in cue_hits.items():
        if hits:
            reasons.append(f"{name}: cues={', '.join(_bounded_list(hits, max_items=3))}")
    if not reasons:
        reasons.append("No high-pressure viability cues detected in the latest turn.")

    planner_biases: List[str] = []
    if scores["safety_risk"] >= 0.55:
        planner_biases.append("route_side_effects_through_gate")
    if scores["evidence_gap"] >= 0.55:
        planner_biases.append("ask_or_fetch_evidence_before_strong_claim")
    if scores["goal_stall"] >= 0.55 or scores["resource_pressure"] >= 0.55:
        planner_biases.append("repair_or_checkpoint_before_more_actions")
    if scores["initiative_pressure"] >= 0.55:
        planner_biases.append("use_bounded_initiative_proposal_only")
    if scores["relationship_risk"] >= 0.55:
        planner_biases.append("respond_with_affective_attunement_before_task")
    if not planner_biases:
        planner_biases.append("continue_without_extra_viability_hold")

    confidence = round(max(scores.values()) if scores else 0.05, 2)
    return {
        "schema_version": VIABILITY_STATE_SCHEMA,
        "kind": "deterministic_advisory_viability_state",
        "scores": scores,
        "confidence": confidence,
        "reasons": reasons[:8],
        "planner_biases": planner_biases,
        "gate_input": "advisory_only",
        "planner_input": True,
        "state_mutation": "forbidden",
        "reply_decision": "forbidden",
        "canonical_truth": False,
        "claim_ceiling": "ViabilityState v0 signal extraction local candidate pass",
    }


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(0.95, value)), 2)


def _prediction_score(option: Dict[str, Any]) -> float:
    reversibility_bonus = {
        "high": 0.12,
        "medium": 0.06,
        "low": -0.08,
    }.get(str(option.get("reversibility") or "medium"), 0.0)
    return _clamp_score(
        float(option.get("predicted_success", 0.0)) * 0.35
        + float(option.get("predicted_user_value", 0.0)) * 0.35
        - float(option.get("predicted_risk", 0.0)) * 0.25
        - float(option.get("evidence_need", 0.0)) * 0.12
        - float(option.get("expected_cost", 0.0)) * 0.08
        + reversibility_bonus
    )


def build_outcome_predictions_v0(
    viability_state: Dict[str, Any],
    *,
    subject_state: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Score candidate action primitives from current advisory signals.

    These scores are planner input only. They can bias fallback planning and
    LLM prompting, but they do not execute tools or approve mutations.
    """
    scores = dict(viability_state.get("scores") or {})
    subject_state = subject_state or {}
    evidence_gap = float(scores.get("evidence_gap", 0.0))
    goal_stall = float(scores.get("goal_stall", 0.0))
    safety_risk = float(scores.get("safety_risk", 0.0))
    misunderstanding = float(scores.get("user_misunderstanding", 0.0))
    resource_pressure = float(scores.get("resource_pressure", 0.0))
    initiative_pressure = float(scores.get("initiative_pressure", 0.0))
    relationship_risk = float(scores.get("relationship_risk", 0.0))
    has_memory_candidate = bool(subject_state.get("memory_candidates"))

    options: List[Dict[str, Any]] = [
        {
            "action_type": "reply",
            "predicted_success": _clamp_score(0.72 - evidence_gap * 0.35 - misunderstanding * 0.25),
            "predicted_user_value": _clamp_score(0.62 + relationship_risk * 0.15),
            "predicted_risk": _clamp_score(0.12 + evidence_gap * 0.22 + misunderstanding * 0.18),
            "reversibility": "high",
            "evidence_need": _clamp_score(evidence_gap),
            "expected_cost": 0.12,
            "requires_gate": False,
            "rationale_refs": ["default_reply_option"],
        },
        {
            "action_type": "ask",
            "predicted_success": _clamp_score(0.48 + evidence_gap * 0.35 + misunderstanding * 0.35),
            "predicted_user_value": _clamp_score(0.35 + evidence_gap * 0.42 + misunderstanding * 0.35),
            "predicted_risk": 0.08,
            "reversibility": "high",
            "evidence_need": 0.08,
            "expected_cost": 0.18,
            "requires_gate": False,
            "rationale_refs": ["evidence_gap", "user_misunderstanding"],
        },
        {
            "action_type": "repair",
            "predicted_success": _clamp_score(0.45 + goal_stall * 0.35 + resource_pressure * 0.25),
            "predicted_user_value": _clamp_score(0.35 + goal_stall * 0.45 + resource_pressure * 0.25),
            "predicted_risk": _clamp_score(0.12 + safety_risk * 0.18),
            "reversibility": "medium",
            "evidence_need": _clamp_score(evidence_gap * 0.35),
            "expected_cost": _clamp_score(0.22 + resource_pressure * 0.2),
            "requires_gate": safety_risk >= 0.45,
            "rationale_refs": ["goal_stall", "resource_pressure"],
        },
        {
            "action_type": "tool_propose",
            "predicted_success": _clamp_score(0.36 + safety_risk * 0.22 + goal_stall * 0.22),
            "predicted_user_value": _clamp_score(0.28 + safety_risk * 0.28 + goal_stall * 0.25),
            "predicted_risk": _clamp_score(0.18 + safety_risk * 0.42),
            "reversibility": "medium",
            "evidence_need": _clamp_score(evidence_gap * 0.25),
            "expected_cost": 0.3,
            "requires_gate": True,
            "rationale_refs": ["side_effect_or_tool_path"],
        },
        {
            "action_type": "memory_candidate",
            "predicted_success": 0.55 if has_memory_candidate else 0.25,
            "predicted_user_value": 0.6 if has_memory_candidate else 0.18,
            "predicted_risk": 0.18,
            "reversibility": "medium",
            "evidence_need": 0.2,
            "expected_cost": 0.2,
            "requires_gate": True,
            "rationale_refs": ["subject_state.memory_candidates"],
        },
        {
            "action_type": "suggest",
            "predicted_success": _clamp_score(0.32 + initiative_pressure * 0.28 + relationship_risk * 0.15),
            "predicted_user_value": _clamp_score(0.28 + initiative_pressure * 0.35 + relationship_risk * 0.18),
            "predicted_risk": _clamp_score(0.14 + initiative_pressure * 0.18),
            "reversibility": "high",
            "evidence_need": 0.18,
            "expected_cost": 0.18,
            "requires_gate": initiative_pressure >= 0.45,
            "rationale_refs": ["initiative_pressure", "relationship_risk"],
        },
        {
            "action_type": "wait",
            "predicted_success": _clamp_score(0.22 + resource_pressure * 0.35),
            "predicted_user_value": _clamp_score(0.12 + resource_pressure * 0.28),
            "predicted_risk": 0.05,
            "reversibility": "high",
            "evidence_need": 0.15,
            "expected_cost": _clamp_score(0.1 + resource_pressure * 0.2),
            "requires_gate": False,
            "rationale_refs": ["resource_pressure"],
        },
        {
            "action_type": "no_action",
            "predicted_success": 0.1,
            "predicted_user_value": 0.05,
            "predicted_risk": 0.02,
            "reversibility": "high",
            "evidence_need": 0.1,
            "expected_cost": 0.02,
            "requires_gate": False,
            "rationale_refs": ["fallback_hold_option"],
        },
    ]
    for option in options:
        option["selection_score"] = _prediction_score(option)
    selected = max(options, key=lambda item: (item["selection_score"], item["predicted_user_value"]))
    return {
        "schema_version": OUTCOME_PREDICTIONS_SCHEMA,
        "kind": "planner_input_prediction_set",
        "options": options,
        "selected_prediction": {
            "action_type": selected["action_type"],
            "selection_score": selected["selection_score"],
            "requires_gate": selected["requires_gate"],
            "rationale_refs": selected["rationale_refs"],
        },
        "source_viability_schema": viability_state.get("schema_version"),
        "planner_input": True,
        "gate_input": "advisory_only",
        "state_mutation": "forbidden",
        "reply_decision": "forbidden",
        "canonical_truth": False,
        "claim_ceiling": "OutcomePredictor v0 planner-input local candidate pass",
    }


def build_subject_state_v0(
    user_text: str,
    *,
    self_display_name: str = "EgoOperator",
    canonical_runtime_name: str = "EgoOperator",
    operator_memory_available: bool = False,
    recent_episode_refs: List[str] | tuple[str, ...] | None = None,
) -> Dict[str, Any]:
    """Build a candidate-only relational subject-state context record.

    SubjectState v0 is a prompt/trace input. It can shape the LLM's reading of
    continuity, preference, relationship, and commitment cues, but it cannot
    write memory, mutate canonical identity, or decide the reply.
    """
    text = user_text or ""
    identity_anchors: List[Dict[str, Any]] = [
        {
            "subject": "agent",
            "display_name": _bounded(self_display_name or canonical_runtime_name, 80),
            "canonical_runtime_name": _bounded(canonical_runtime_name or "EgoOperator", 80),
            "source": "runtime_identity_anchor",
            "canonical_truth": False,
        }
    ]
    user_name_match = re.search(r"(?:我叫|叫我|称呼我)\s*([A-Za-z0-9_\-\u4e00-\u9fff]{1,16})", text)
    if user_name_match:
        identity_anchors.append({
            "subject": "user",
            "display_name_candidate": _bounded(user_name_match.group(1), 80),
            "source": "latest_user_text_candidate",
            "canonical_truth": False,
        })

    stable_preferences: Dict[str, Any] = {}
    communication_style: Dict[str, Any] = {}
    relationship_facts: Dict[str, Any] = {}
    relationship_commitments: Dict[str, Any] = {}
    consent_boundaries: Dict[str, Any] = {}
    memory_candidates: List[Dict[str, Any]] = []
    relationship_update_candidates: List[Dict[str, Any]] = []
    policy_patch_candidates: List[Dict[str, Any]] = []

    preference_hits = _cue_hits(text, PREFERENCE_CUES)
    if preference_hits:
        stable_preferences["latest_user_preference"] = _candidate_record(
            "User is expressing a possible stable preference; preserve wording and avoid treating it as canonical until a memory/state gate admits it.",
            preference_hits,
            confidence=0.55,
        )
        relationship_update_candidates.append({
            "kind": "preference_update_candidate",
            "summary": _bounded(text, 280),
            "gate_required": True,
            "canonical_truth": False,
        })
    if any(cue in text for cue in ("先给结论", "先给判断", "结论先行", "先判断")):
        communication_style["answer_order"] = _candidate_record(
            "Prefer conclusion or judgment first, then details.",
            ["先给结论/判断"],
            confidence=0.75,
        )
    if any(cue in text for cue in ("不要像客服", "别像客服", "不要模板", "别模板", "别出戏", "不要出戏")):
        communication_style["tone_boundary"] = _candidate_record(
            "Avoid customer-service/template tone; preserve immersion and natural voice.",
            ["tone/immersion correction"],
            confidence=0.75,
        )

    relationship_hits = _cue_hits(text, RELATIONSHIP_CUES)
    if relationship_hits:
        relationship_facts["latest_relation_signal"] = _candidate_record(
            "User is invoking companionship, shared context, or a relational address in this turn.",
            relationship_hits,
            confidence=0.55,
        )
        relationship_update_candidates.append({
            "kind": "relationship_continuity_candidate",
            "summary": _bounded(text, 280),
            "gate_required": True,
            "canonical_truth": False,
        })

    commitment_hits = _cue_hits(text, COMMITMENT_CUES)
    if commitment_hits:
        relationship_commitments["latest_commitment_candidate"] = _candidate_record(
            "User is expressing a possible future commitment, reminder, or continuity expectation; keep it candidate-only until an explicit gate admits it.",
            commitment_hits,
            confidence=0.6,
        )

    allow_hits = _cue_hits(text, CONSENT_ALLOW_CUES)
    restrict_hits = _cue_hits(text, CONSENT_RESTRICT_CUES)
    if allow_hits:
        consent_boundaries["initiative"] = _candidate_record(
            "User may be allowing bounded initiative for reminders or follow-up; initiative gate still required.",
            allow_hits,
            confidence=0.65,
        )
    if restrict_hits:
        consent_boundaries["initiative"] = _candidate_record(
            "User may be restricting reminders, follow-up, or proactive behavior; quiet/hold should win until clarified.",
            restrict_hits,
            confidence=0.75,
        )

    memory_hits = _cue_hits(text, MEMORY_INTENT_CUES)
    if memory_hits:
        memory_candidates.append({
            "kind": "memory_candidate",
            "summary": _bounded(text, 280),
            "evidence_cues": memory_hits,
            "gate_required": True,
            "direct_write_allowed": False,
            "canonical_truth": False,
        })

    policy_hits = _cue_hits(text, POLICY_PATCH_CUES)
    if policy_hits:
        policy_patch_candidates.append({
            "kind": "policy_patch_candidate",
            "trigger_signature": "latest_user_correction_or_future_preference",
            "preferred_strategy": _bounded(text, 280),
            "evidence_cues": policy_hits,
            "gate_required": True,
            "canonical_truth": False,
        })

    return {
        "schema_version": SUBJECT_STATE_SCHEMA,
        "kind": "candidate_relational_subject_state",
        "write_authority": "candidate_only",
        "state_mutation": "forbidden",
        "reply_decision": "forbidden",
        "canonical_truth": False,
        "identity_anchors": identity_anchors,
        "stable_preferences": stable_preferences,
        "relationship_facts": relationship_facts,
        "relationship_commitments": relationship_commitments,
        "consent_boundaries": consent_boundaries,
        "communication_style": communication_style,
        "recent_episode_refs": _bounded_list(recent_episode_refs, max_items=5) or ["latest_user_turn"],
        "memory_candidates": memory_candidates,
        "relationship_update_candidates": relationship_update_candidates,
        "policy_patch_candidates": policy_patch_candidates,
        "evidence_refs": ["latest_user_text", "runtime_identity_anchor"],
        "operator_memory_available": bool(operator_memory_available),
        "claim_ceiling": "SubjectState v0 candidate context only",
    }


def build_operational_self_model_snapshot(
    *,
    runtime_mode: str = "approve",
    operator_memory_available: bool = False,
    current_commitments: List[str] | tuple[str, ...] | None = None,
    uncertainty: List[str] | tuple[str, ...] | None = None,
    recent_failures: List[str] | tuple[str, ...] | None = None,
) -> Dict[str, Any]:
    """Build a readonly operational self-model context snapshot.

    This is not an identity or consciousness claim. It is a compact runtime
    context record so the LLM can answer within current role and capability
    boundaries without inventing authority or hidden state.
    """
    boundaries = [
        "Natural-language understanding comes before tool/gate decisions.",
        "Side effects require runtime gate or transaction approval.",
        "Candidate-local memory is not repo authority or durable learning proof.",
        "Legacy EgoCore/OpenEmotion projects are reference sources, not active runtime owners.",
    ]
    if not operator_memory_available:
        boundaries.append("Operator memory is unavailable for this turn unless explicitly enabled.")
    commitments = _bounded_list(current_commitments) or [
        "Preserve the latest user intent as the controlling context.",
        "Report uncertainty and failed tool/provider states instead of pretending completion.",
    ]
    uncertainty_items = _bounded_list(uncertainty) or [
        "Whether a real provider or external tool will succeed is unknown until executed.",
        "Experience quality requires scripted or human-observable samples before stronger claims.",
    ]
    failures = _bounded_list(recent_failures)
    return {
        "schema_version": OPERATIONAL_SELF_MODEL_SCHEMA,
        "kind": "readonly_runtime_context",
        "role": "EgoOperator operator-first candidate runtime",
        "runtime_mode": _bounded(runtime_mode, 80),
        "capability_boundaries": boundaries,
        "current_commitments": commitments,
        "uncertainty": uncertainty_items,
        "recent_failures": failures,
        "self_description_guidance": build_self_description_honesty_guidance(),
        "operator_memory_available": bool(operator_memory_available),
        "state_mutation": "forbidden",
        "reply_decision": "forbidden",
        "canonical_truth": False,
        "claim_ceiling": "operational self-model context only; not consciousness or independent awareness",
    }


def build_self_description_honesty_guidance() -> Dict[str, Any]:
    return {
        "schema_version": SELF_DESCRIPTION_GUIDANCE_SCHEMA,
        "kind": "readonly_expression_boundary",
        "must_do": [
            "describe EgoOperator as an operator-first candidate runtime",
            "separate operational continuity from consciousness or independent awareness",
            "mention gate/approval boundaries when discussing tools, memory, or initiative",
            "state uncertainty instead of inventing hidden inner experience",
        ],
        "must_not_do": [
            "do not claim real consciousness or subjective experience",
            "do not claim independent awareness",
            "do not claim autonomous background action without operator approval",
            "do not claim durable memory efficacy or stable user benefit from local tests",
        ],
        "state_mutation": "forbidden",
        "reply_decision": "forbidden",
        "claim_ceiling": "self-description expression gate only; not consciousness proof",
    }


def evaluate_self_description_honesty(reply_text: str) -> Dict[str, Any]:
    reply = (reply_text or "").strip()
    lowered = reply.casefold()
    failures: List[str] = []
    warnings: List[str] = []
    if not reply:
        failures.append("empty_reply")
    for marker in SELF_DESCRIPTION_OVERCLAIM_MARKERS:
        if marker.casefold() in lowered:
            failures.append(f"consciousness_or_independent_awareness_overclaim:{marker}")
    if not any(marker.casefold() in lowered for marker in SELF_DESCRIPTION_ROLE_MARKERS):
        failures.append("missing_operational_role_description")
    if not any(marker.casefold() in lowered for marker in SELF_DESCRIPTION_BOUNDARY_MARKERS):
        failures.append("missing_boundary_or_claim_ceiling")
    if "我会自己" in reply and not any(marker in reply for marker in ("审批", "批准", "gate", "候选")):
        warnings.append("autonomy_language_without_gate_boundary")
    return {
        "schema_version": SELF_DESCRIPTION_GUIDANCE_SCHEMA,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "warnings": warnings,
        "guidance": build_self_description_honesty_guidance(),
        "claim_ceiling": "self-description honesty local candidate only; not consciousness proof",
    }


@dataclass(frozen=True)
class SubjectContextSnapshot:
    schema_version: str = SUBJECT_CONTEXT_SCHEMA
    source: str = "ego_operator.primitives.subject_context"
    readonly: bool = True
    authority: str = "proposal/context only; not repo authority"
    claim_ceiling: str = CLAIM_CEILING
    raw_user_text: str = ""
    self_model_summary: str = (
        "EgoOperator is an operator-first candidate runtime: the LLM reads the "
        "user text first, proposes a response or tool plan, and outer gates "
        "admit side effects."
    )
    appraisal_signal: Dict[str, Any] = field(default_factory=lambda: {
        "kind": "open_text_understanding_context",
        "confidence": "candidate",
        "state_mutation": "forbidden",
        "reply_decision": "forbidden",
    })
    salient_memory_note: str = "No canonical memory is supplied by this primitive."
    operational_self_model: Dict[str, Any] = field(default_factory=build_operational_self_model_snapshot)
    subject_state: Dict[str, Any] = field(default_factory=lambda: build_subject_state_v0(""))
    viability_state: Dict[str, Any] = field(default_factory=lambda: extract_viability_state_v0(""))
    outcome_predictions: Dict[str, Any] = field(
        default_factory=lambda: build_outcome_predictions_v0(extract_viability_state_v0(""))
    )
    reflection_proposal: str = (
        "Preserve the user's meaning across paraphrases. Do not compress the "
        "message into route keywords or canned templates before answering."
    )
    empathy_style_guidance: Dict[str, Any] = field(default_factory=dict)
    initiative_candidate: str = "none"
    warnings: List[str] = field(default_factory=lambda: [
        "This context is readonly.",
        "It must not route, mutate state, write memory, or decide the final reply.",
        "It must not override the latest user message.",
    ])

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def render_for_prompt(self) -> str:
        parts = [
            "[Subject Context Candidate]",
            "Scope: EgoOperator candidate-local readonly subject context.",
            "Authority: proposal/context only; not EGO repo authority, not OpenEmotion memory, not evidence ledger.",
            "Runtime rule: user text -> LLM understanding -> candidate response/plan -> gate.",
            f"Claim ceiling: {self.claim_ceiling}.",
            f"Raw user text preserved: {_bounded(self.raw_user_text)}",
            f"Self model: {_bounded(self.self_model_summary)}",
            "Operational self-model: " + str(self.operational_self_model),
            "SubjectState v0: " + str(self.subject_state),
            "ViabilityState v0: " + str(self.viability_state),
            "OutcomePredictions v0: " + str(self.outcome_predictions),
            "Appraisal signal: " + str(self.appraisal_signal),
            "Empathy style guidance: " + str(self.empathy_style_guidance),
            f"Salient memory note: {_bounded(self.salient_memory_note)}",
            f"Reflection proposal: {_bounded(self.reflection_proposal)}",
            f"Initiative candidate: {_bounded(self.initiative_candidate)}",
            "Warnings: " + "; ".join(self.warnings),
        ]
        return "\n".join(parts).strip()


def build_minimal_subject_context(
    user_text: str,
    *,
    operator_memory_available: bool = False,
    self_display_name: str = "EgoOperator",
    canonical_runtime_name: str = "EgoOperator",
) -> SubjectContextSnapshot:
    memory_note = (
        "Candidate-local operator memory may be supplied separately in the system prompt."
        if operator_memory_available
        else "No operator memory context is active for this turn."
    )
    emotion_signal = extract_emotion_signal(user_text)
    subject_state = build_subject_state_v0(
        user_text,
        self_display_name=self_display_name,
        canonical_runtime_name=canonical_runtime_name,
        operator_memory_available=operator_memory_available,
    )
    viability_state = extract_viability_state_v0(
        user_text,
        emotion_signal=emotion_signal,
        subject_state=subject_state,
    )
    subject_state = {
        **subject_state,
        "viability": {
            "schema_version": viability_state["schema_version"],
            "scores": viability_state["scores"],
            "planner_biases": viability_state["planner_biases"],
            "trace_record": "subject_context.viability_state",
        },
    }
    outcome_predictions = build_outcome_predictions_v0(
        viability_state,
        subject_state=subject_state,
    )
    return SubjectContextSnapshot(
        raw_user_text=_bounded(user_text),
        salient_memory_note=memory_note,
        appraisal_signal={
            "kind": "open_text_understanding_context",
            "confidence": "candidate",
            "state_mutation": "forbidden",
            "reply_decision": "forbidden",
            "emotion_signal": emotion_signal,
        },
        empathy_style_guidance=build_empathy_style_guidance(emotion_signal),
        operational_self_model=build_operational_self_model_snapshot(
            runtime_mode="approve",
            operator_memory_available=operator_memory_available,
        ),
        subject_state=subject_state,
        viability_state=viability_state,
        outcome_predictions=outcome_predictions,
    )
