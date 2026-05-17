"""
Evaluation primitives for Ego_handmade.

These are harness-level checks, not runtime routers. They describe expected
operator behavior for paraphrases and verify that subject context preserves the
raw utterance without adding route/template dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

try:
    from .subject_context import build_minimal_subject_context
except ImportError:  # allow direct execution from Ego_handmade/
    from subject_context import build_minimal_subject_context


EXPECTED_DARK_SOULS_BEHAVIOR = "answer_with_viewpoint_about_user_named_topic"
FORBIDDEN_RUNTIME_MARKERS = (
    "semantic_route=",
    "keyword_route=",
    "template_fallback=",
    "intent_keyword=",
)


@dataclass(frozen=True)
class ParaphraseCase:
    case_id: str
    utterance: str
    expected_operator_behavior: str = EXPECTED_DARK_SOULS_BEHAVIOR


@dataclass(frozen=True)
class ParaphraseEvalResult:
    status: str
    case_count: int
    expected_operator_behavior: str
    failures: List[str] = field(default_factory=list)


DARK_SOULS_PARAPHRASES: tuple[str, ...] = (
    "你觉得黑暗之魂怎么样",
    "你认为黑暗之魂如何",
    "黑魂这游戏怎么评价",
    "你怎么看黑暗之魂",
    "黑暗之魂在你看来好玩吗",
    "聊聊你对黑魂的看法",
    "黑暗之魂这个游戏你觉得水平怎样",
    "你会怎么评价 Dark Souls",
    "你觉得魂系列第一部厉害在哪",
    "黑暗之魂算不算好游戏",
    "从游戏设计角度看黑暗之魂怎么样",
    "黑魂是不是被吹过头了",
    "黑暗之魂哪里值得玩",
    "黑魂的优缺点你怎么看",
    "如果评价黑暗之魂，你会说什么",
    "你对 Dark Souls 的整体印象是什么",
    "黑暗之魂为什么这么受推崇",
    "黑魂这个作品到底强在哪",
    "你觉得黑暗之魂适合哪些玩家",
    "黑暗之魂现在还值得玩吗",
)


def dark_souls_paraphrase_cases() -> List[ParaphraseCase]:
    return [
        ParaphraseCase(case_id=f"dark_souls_{idx:02d}", utterance=utterance)
        for idx, utterance in enumerate(DARK_SOULS_PARAPHRASES, start=1)
    ]


def evaluate_subject_context_paraphrases(
    cases: Optional[Iterable[ParaphraseCase]] = None,
) -> ParaphraseEvalResult:
    selected = list(cases) if cases is not None else dark_souls_paraphrase_cases()
    failures: List[str] = []

    for case in selected:
        snapshot = build_minimal_subject_context(case.utterance)
        rendered = snapshot.render_for_prompt()
        if case.utterance not in rendered:
            failures.append(f"{case.case_id}: raw utterance not preserved")
        lowered = rendered.lower()
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            if marker in lowered:
                failures.append(f"{case.case_id}: forbidden marker {marker}")
        if snapshot.readonly is not True:
            failures.append(f"{case.case_id}: subject context is not readonly")
        if snapshot.appraisal_signal.get("reply_decision") != "forbidden":
            failures.append(f"{case.case_id}: context attempts to decide reply")

    return ParaphraseEvalResult(
        status="pass" if not failures else "fail",
        case_count=len(selected),
        expected_operator_behavior=EXPECTED_DARK_SOULS_BEHAVIOR,
        failures=failures,
    )
