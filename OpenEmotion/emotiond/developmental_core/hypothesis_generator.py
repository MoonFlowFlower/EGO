"""
MVP12 Hypothesis Generator

Generates candidate hypotheses from cycle context.
All outputs are sandboxed candidates that must go through evaluation.
"""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any, Dict, List, Optional

from .models import (
    Candidate,
    InterpretationCandidate,
    ActionCandidate,
    ExplanationCandidate,
    SelfModelHypothesis,
    CycleContext,
    CycleTrigger,
)


class HypothesisGenerator:
    """
    Generates candidate hypotheses from developmental cycle context.

    This is a sandboxed operation - outputs are proposals only and
    must go through Governor v2 for approval.
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def _recent_dialogue(self, snapshot: Dict[str, Any]) -> tuple[str, str]:
        recent_user_turns = list(snapshot.get("recent_user_turns") or [])
        recent_assistant_replies = list(snapshot.get("recent_assistant_replies") or [])
        latest_user_turn = str(
            recent_user_turns[-1] if recent_user_turns else snapshot.get("ingress_text") or ""
        ).strip()
        latest_assistant_reply = str(
            recent_assistant_replies[-1] if recent_assistant_replies else snapshot.get("delivery_text") or ""
        ).strip()
        return latest_user_turn, latest_assistant_reply

    def _primary_clause(self, text: str, *, limit: int = 48) -> str:
        raw = str(text or "").strip()
        if not raw:
            return ""
        for separator in ("。", "，", "？", "！", ":", "：", ".", ",", "?", "!"):
            raw = raw.split(separator, 1)[0].strip()
            if raw:
                break
        if len(raw) <= limit:
            return raw
        return raw[: limit - 1].rstrip() + "…"

    def _tension_label(self, snapshot: Dict[str, Any]) -> str:
        tensions = list(snapshot.get("unresolved_tensions") or [])
        if not tensions:
            return ""
        strongest = max(
            tensions,
            key=lambda item: float(item.get("intensity") or item.get("pressure") or 0.0),
        )
        return self._primary_clause(str(strongest.get("label") or strongest.get("kind") or ""), limit=32)

    def _idle_hypothesis_text(self, anchor: str) -> str:
        if "操作员" in anchor:
            return "那个像“操作员”的感觉，本身也许就是系统里生成出来的一层解释。"
        if "意识" in anchor:
            return "如果意识更像光谱，那“我在选择”的感觉也许也是渐变出来的，不是突然出现的。"
        if anchor:
            return f"围绕“{anchor}”的讨论可能还没有真正收束，它后面也许还有一层没被说出来。"
        return "当前状态虽然安静，但未必是真的收束，可能只是把一个问题暂时压到了后台。"

    def _idle_interpretation_text(self, anchor: str, latest_reply: str) -> str:
        if "操作员" in anchor:
            return "这个话题没有停在比喻上，它已经开始逼近“谁在做选择”这个更深的边界。"
        if "意识" in anchor:
            return "这个问题已经不只是定义意识，而是在逼近主体边界和伦理责任怎么划线。"
        if anchor:
            return f"空档期里还会回到“{anchor}”，说明这条线对当前状态仍有残余拉力。"
        if latest_reply:
            return f"刚才那句“{self._primary_clause(latest_reply, limit=40)}”没有把话题真正关掉。"
        return "空档期可能不是结束，而是在为下一次重组留空间。"

    def generate(
        self,
        context: CycleContext,
        state_snapshot: Optional[Dict[str, Any]] = None,
        max_candidates: int = 5,
    ) -> List[Candidate]:
        """Generate candidates based on cycle context and state."""
        candidates = []
        snapshot = state_snapshot or context.state_snapshot

        # Generate based on trigger type
        if context.trigger == CycleTrigger.IDLE:
            candidates.extend(self._generate_idle_candidates(context, snapshot))
        elif context.trigger == CycleTrigger.UNRESOLVED_TENSION:
            candidates.extend(self._generate_tension_candidates(context, snapshot))
        elif context.trigger == CycleTrigger.LONG_TERM_GOAL:
            candidates.extend(self._generate_goal_candidates(context, snapshot))
        elif context.trigger == CycleTrigger.REPLAY_EVENT:
            candidates.extend(self._generate_replay_candidates(context, snapshot))

        # Sort by confidence and limit
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        return candidates[:max_candidates]

    def _generate_idle_candidates(
        self,
        context: CycleContext,
        snapshot: Dict[str, Any],
    ) -> List[Candidate]:
        """Generate candidates during idle cycles."""
        candidates = []
        latest_user_turn, latest_assistant_reply = self._recent_dialogue(snapshot)
        anchor = self._primary_clause(latest_user_turn or latest_assistant_reply, limit=40)

        # Self-reflection hypothesis
        candidates.append(SelfModelHypothesis(
            origin_cycle=context.cycle_id,
            confidence=0.3 + self.rng.random() * 0.2,
            trace_reference=context.trace_hash,
            hypothesis=self._idle_hypothesis_text(anchor),
            test_predictions=[
                f"如果再沿着“{anchor or '这个点'}”追问，系统还会继续回到同一条线。"
            ],
            disconfirmation_criteria=["话题迅速失去连续性", "下一轮完全不再指向当前主题"],
        ))

        # Exploration interpretation
        candidates.append(InterpretationCandidate(
            origin_cycle=context.cycle_id,
            confidence=0.4 + self.rng.random() * 0.2,
            trace_reference=context.trace_hash,
            interpretation=self._idle_interpretation_text(anchor, latest_assistant_reply),
            evidence_refs=[anchor] if anchor else [],
            alternatives=["系统只是暂时安静了", "当前只是没有新输入，不代表内部已经收束"],
        ))

        return candidates

    def _generate_tension_candidates(
        self,
        context: CycleContext,
        snapshot: Dict[str, Any],
    ) -> List[Candidate]:
        """Generate candidates for unresolved tensions."""
        candidates = []
        latest_user_turn, _ = self._recent_dialogue(snapshot)
        anchor = self._primary_clause(latest_user_turn, limit=40)
        tension_label = self._tension_label(snapshot)

        # Tension explanation
        candidates.append(ExplanationCandidate(
            origin_cycle=context.cycle_id,
            confidence=0.5 + self.rng.random() * 0.3,
            trace_reference=context.trace_hash,
            explanation=(
                f"“{anchor}”这条线还没收住，当前张力更像是 {tension_label or '一个未闭合的问题'} 在持续回拉。"
                if anchor
                else f"当前张力没有自然消退，更像是 {tension_label or '一个未闭合的问题'} 仍在内部占位。"
            ),
            supporting_facts=[f"{tension_label or 'tension'} exceeds threshold"],
            counter_evidence=[],
        ))

        # Resolution action
        candidates.append(ActionCandidate(
            origin_cycle=context.cycle_id,
            confidence=0.4 + self.rng.random() * 0.2,
            trace_reference=context.trace_hash,
            action_type="observe",
            target="internal_state",
            expected_outcome="Gather more information about tension source",
            risk_assessment={"disruption": 0.1},
        ))

        return candidates

    def _generate_goal_candidates(
        self,
        context: CycleContext,
        snapshot: Dict[str, Any],
    ) -> List[Candidate]:
        """Generate candidates for long-term goal pressure."""
        candidates = []
        goals = list(snapshot.get("long_term_goals") or [])
        goal_label = self._primary_clause(str((goals[0] if goals else {}).get("label") or ""), limit=40)

        # Goal pursuit action
        candidates.append(ActionCandidate(
            origin_cycle=context.cycle_id,
            confidence=0.6 + self.rng.random() * 0.2,
            trace_reference=context.trace_hash,
            action_type="approach",
            target=goal_label or "long_term_goal",
            expected_outcome=(
                f"沿着“{goal_label}”继续推进，确认这条线是否值得保留"
                if goal_label
                else "继续确认当前长期目标是否仍值得追踪"
            ),
            risk_assessment={"resource_cost": 0.2, "disruption": 0.1},
        ))

        return candidates

    def _generate_replay_candidates(
        self,
        context: CycleContext,
        snapshot: Dict[str, Any],
    ) -> List[Candidate]:
        """Generate candidates from replay events."""
        candidates = []

        # Replay interpretation
        candidates.append(InterpretationCandidate(
            origin_cycle=context.cycle_id,
            confidence=0.5,
            trace_reference=context.trace_hash,
            interpretation="Replaying past cycle for verification",
            evidence_refs=[],
            alternatives=[],
        ))

        return candidates
