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
CLAIM_CEILING = "candidate-local subject context only"

EMOTION_SIGNAL_SCHEMA = "ego_operator.emotion_signal.v1"
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
    "unclear_or_neutral": "task_direct",
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
    reflection_proposal: str = (
        "Preserve the user's meaning across paraphrases. Do not compress the "
        "message into route keywords or canned templates before answering."
    )
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
            "Appraisal signal: " + str(self.appraisal_signal),
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
) -> SubjectContextSnapshot:
    memory_note = (
        "Candidate-local operator memory may be supplied separately in the system prompt."
        if operator_memory_available
        else "No operator memory context is active for this turn."
    )
    return SubjectContextSnapshot(
        raw_user_text=_bounded(user_text),
        salient_memory_note=memory_note,
        appraisal_signal={
            "kind": "open_text_understanding_context",
            "confidence": "candidate",
            "state_mutation": "forbidden",
            "reply_decision": "forbidden",
            "emotion_signal": extract_emotion_signal(user_text),
        },
    )
