"""
Readonly subject-context primitive for EgoOperator.

The purpose is to preserve the useful subject-system idea of self/appraisal/
reflection context without importing the old runtime architecture or turning
semantic understanding into keyword routing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


DEFAULT_CONTEXT_MAX_CHARS = 1200
SUBJECT_CONTEXT_SCHEMA = "ego_operator.subject_context.v1"
CLAIM_CEILING = "candidate-local subject context only"


def _bounded(text: str, max_chars: int = DEFAULT_CONTEXT_MAX_CHARS) -> str:
    clean = (text or "").strip()
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars] + "\n...[truncated]"


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
    )
