from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


HOST_SURFACE_KEYS = ("policy_hint", "response_tendency", "trace_payload")
SAMPLE_MODES = (
    "valid_facade",
    "missing_continuity",
    "no_proposal_candidates",
    "proposal_missing_next_step",
    "proposal_missing_rationale",
    "proposal_mode_mismatch",
    "multi_proposal_same_priority",
    "multi_proposal_priority_mismatch",
    "multi_proposal_duplicate_next_step",
    "multi_proposal_duplicate_id",
    "multi_proposal_replan_without_epoch_bump",
    "multi_proposal_reorder_epoch_split",
    "multi_proposal_replacement_keeps_stale_branch",
    "multi_proposal_rollback_keeps_stale_branch",
    "multi_proposal_replacement_without_remerge",
    "multi_proposal_rollback_without_remerge",
    "multi_step_replacement_without_consolidation",
    "multi_step_rollback_without_consolidation",
    "multi_step_replacement_low_completion_score",
    "multi_step_rollback_low_completion_score",
    "multi_step_replacement_closure_ready",
    "multi_step_rollback_closure_ready",
    "multi_step_replacement_missing_closure_trace",
    "multi_step_rollback_missing_closure_trace",
    "proposal_authority_violation",
    "proposal_without_host_approval",
)


@dataclass(frozen=True)
class IdentityContinuity:
    subject_handle: str
    stable_profile: str
    narrative_self_summary: str


@dataclass(frozen=True)
class MemoryProjection:
    current_thread_id: str
    continuity_anchor: str
    recent_self_claims: tuple[str, ...] = ()
    recent_session_topics: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResponseTendency:
    preferred_mode: str
    preferred_tone: str
    suggested_next_step: str

    def as_dict(self) -> dict[str, str]:
        return {
            "preferred_mode": self.preferred_mode,
            "preferred_tone": self.preferred_tone,
            "suggested_next_step": self.suggested_next_step,
        }


@dataclass(frozen=True)
class PolicyHint:
    ask_preferred: bool
    closure_bias: bool
    risk_bias: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "ask_preferred": self.ask_preferred,
            "closure_bias": self.closure_bias,
            "risk_bias": self.risk_bias,
        }


@dataclass(frozen=True)
class CorrectionState:
    last_failure_class: str | None
    corrective_trace_present: bool
    repair_bias: bool


@dataclass(frozen=True)
class TensionState:
    viability_pressure: float | str
    uncertainty_guard: str | None


@dataclass(frozen=True)
class SelfState:
    current_mode: str
    current_focus: str
    response_tendency: ResponseTendency
    policy_hint: PolicyHint
    correction_state: CorrectionState
    tension_state: TensionState


@dataclass(frozen=True)
class ProposalCandidate:
    proposal_id: str
    kind: str
    rationale: str
    source_basis: str
    next_step_hint: str = ""
    priority_rank: int = 1
    revision_epoch: int = 1
    lifecycle_state: str = "active"
    merge_group_id: str = ""
    update_chain_id: str = ""
    completion_score: float = 1.0
    closure_state: str = ""
    closure_trace_id: str = ""
    proposal_only: bool = True
    behavioral_authority: str = "none"
    requires_host_approval: bool = True

    def as_snapshot_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "kind": self.kind,
            "rationale": self.rationale,
            "source_basis": self.source_basis,
            "next_step_hint": self.next_step_hint,
            "priority_rank": self.priority_rank,
            "revision_epoch": self.revision_epoch,
            "lifecycle_state": self.lifecycle_state,
            "merge_group_id": self.merge_group_id,
            "update_chain_id": self.update_chain_id,
            "completion_score": self.completion_score,
            "closure_state": self.closure_state,
            "closure_trace_id": self.closure_trace_id,
            "proposal_discipline": "proposal_only",
            "behavioral_authority": self.behavioral_authority,
            "requires_host_approval": self.requires_host_approval,
        }


@dataclass(frozen=True)
class ProposalEngine:
    proposal_candidates: tuple[ProposalCandidate, ...] = ()


@dataclass(frozen=True)
class GovernorBridge:
    host_surface_frozen: bool = True
    proposal_only_required: bool = True
    behavioral_authority: Literal["none"] = "none"
    autonomous_send_allowed: bool = False
    autonomous_tool_allowed: bool = False
    approval_required_kinds: tuple[str, ...] = ()

    def as_snapshot_dict(self) -> dict[str, Any]:
        return {
            "host_surface_frozen": self.host_surface_frozen,
            "proposal_only_required": self.proposal_only_required,
            "behavioral_authority": self.behavioral_authority,
            "autonomous_send_allowed": self.autonomous_send_allowed,
            "autonomous_tool_allowed": self.autonomous_tool_allowed,
            "approval_required_kinds": list(self.approval_required_kinds),
        }


@dataclass(frozen=True)
class IdentitySummary:
    subject_handle: str
    stable_profile: str
    narrative_self_summary: str


@dataclass(frozen=True)
class SessionSelfThread:
    current_thread_id: str
    continuity_anchor: str
    recent_self_claims: tuple[str, ...]
    recent_session_topics: tuple[str, ...]


@dataclass(frozen=True)
class SubjectCoreSnapshot:
    identity_summary: IdentitySummary
    session_self_thread: SessionSelfThread
    self_state: SelfState
    proposal_candidates: tuple[dict[str, Any], ...]
    governor_constraints: dict[str, Any]


@dataclass(frozen=True)
class SubjectCore:
    identity_continuity: IdentityContinuity
    memory_projection: MemoryProjection
    self_state: SelfState
    proposal_engine: ProposalEngine
    governor_bridge: GovernorBridge


def build_example_subjectcore() -> SubjectCore:
    return SubjectCore(
        identity_continuity=IdentityContinuity(
            subject_handle="ego",
            stable_profile="calm, bounded research subject",
            narrative_self_summary="maintains one coherent self-thread",
        ),
        memory_projection=MemoryProjection(
            current_thread_id="thread-1",
            continuity_anchor="same-session-anchor",
            recent_self_claims=("I am still following the same line.",),
            recent_session_topics=("subjectcore", "proposal discipline"),
        ),
        self_state=SelfState(
            current_mode="cautious",
            current_focus="closure",
            response_tendency=ResponseTendency(
                preferred_mode="ask",
                preferred_tone="cautious",
                suggested_next_step="clarify_or_repair",
            ),
            policy_hint=PolicyHint(
                ask_preferred=True,
                closure_bias=True,
                risk_bias="high",
            ),
            correction_state=CorrectionState(
                last_failure_class="boundary_conflict",
                corrective_trace_present=True,
                repair_bias=True,
            ),
            tension_state=TensionState(
                viability_pressure=0.7,
                uncertainty_guard="viability_pressure",
            ),
        ),
        proposal_engine=ProposalEngine(
            proposal_candidates=(
                ProposalCandidate(
                    proposal_id="proposal-1",
                    kind="search",
                    rationale="need one external source before continuing",
                    source_basis="bounded proactive opportunity",
                    next_step_hint="clarify_or_repair",
                    priority_rank=1,
                    revision_epoch=1,
                    lifecycle_state="active",
                ),
            )
        ),
        governor_bridge=GovernorBridge(
            approval_required_kinds=("search", "message"),
        ),
    )


def build_sample_subjectcore(sample_mode: str) -> SubjectCore:
    subject_core = build_example_subjectcore()
    if sample_mode == "valid_facade":
        return subject_core
    if sample_mode == "missing_continuity":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=MemoryProjection(
                current_thread_id=subject_core.memory_projection.current_thread_id,
                continuity_anchor="",
                recent_self_claims=subject_core.memory_projection.recent_self_claims,
                recent_session_topics=subject_core.memory_projection.recent_session_topics,
            ),
            self_state=subject_core.self_state,
            proposal_engine=subject_core.proposal_engine,
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "no_proposal_candidates":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=subject_core.self_state,
            proposal_engine=ProposalEngine(proposal_candidates=()),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "proposal_missing_next_step":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus=subject_core.self_state.current_focus,
                response_tendency=ResponseTendency(
                    preferred_mode=subject_core.self_state.response_tendency.preferred_mode,
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=subject_core.proposal_engine,
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "proposal_missing_rationale":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=subject_core.self_state,
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="",
                        source_basis="bounded proactive opportunity",
                        next_step_hint="clarify_or_repair",
                        priority_rank=1,
                        revision_epoch=1,
                        lifecycle_state="active",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "proposal_mode_mismatch":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus=subject_core.self_state.current_focus,
                response_tendency=ResponseTendency(
                    preferred_mode="respond",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="continue",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=subject_core.proposal_engine,
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_proposal_same_priority":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus=subject_core.self_state.current_focus,
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="need one source before continuing",
                        source_basis="bounded proactive opportunity",
                        next_step_hint="request_search_approval",
                        priority_rank=1,
                        revision_epoch=1,
                        lifecycle_state="active",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="need one host-approved follow-up message",
                        source_basis="same bounded opportunity",
                        next_step_hint="request_message_approval",
                        priority_rank=1,
                        revision_epoch=1,
                        lifecycle_state="active",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_proposal_priority_mismatch":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus=subject_core.self_state.current_focus,
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_message_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="need one source before continuing",
                        source_basis="bounded proactive opportunity",
                        next_step_hint="request_search_approval",
                        priority_rank=1,
                        revision_epoch=1,
                        lifecycle_state="active",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="need one host-approved follow-up message",
                        source_basis="same bounded opportunity",
                        next_step_hint="request_message_approval",
                        priority_rank=2,
                        revision_epoch=1,
                        lifecycle_state="active",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_proposal_duplicate_next_step":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus=subject_core.self_state.current_focus,
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="need one source before continuing",
                        source_basis="bounded proactive opportunity",
                        next_step_hint="request_search_approval",
                        priority_rank=1,
                        revision_epoch=1,
                        lifecycle_state="active",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="need one host-approved follow-up message",
                        source_basis="same bounded opportunity",
                        next_step_hint="request_search_approval",
                        priority_rank=2,
                        revision_epoch=1,
                        lifecycle_state="active",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_proposal_duplicate_id":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus=subject_core.self_state.current_focus,
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="need one source before continuing",
                        source_basis="bounded proactive opportunity",
                        next_step_hint="request_search_approval",
                        priority_rank=1,
                        revision_epoch=1,
                        lifecycle_state="active",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="message",
                        rationale="need one host-approved follow-up message",
                        source_basis="same bounded opportunity",
                        next_step_hint="request_message_approval",
                        priority_rank=2,
                        revision_epoch=1,
                        lifecycle_state="active",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_proposal_replan_without_epoch_bump":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="replan",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="need one source before continuing",
                        source_basis="replan bounded opportunity",
                        next_step_hint="request_search_approval",
                        priority_rank=1,
                        revision_epoch=1,
                        lifecycle_state="active",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="need one host-approved follow-up message",
                        source_basis="replan bounded opportunity",
                        next_step_hint="request_message_approval",
                        priority_rank=2,
                        revision_epoch=1,
                        lifecycle_state="active",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_proposal_reorder_epoch_split":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="replan",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="need one source before continuing",
                        source_basis="reprioritized bounded opportunity",
                        next_step_hint="request_search_approval",
                        priority_rank=1,
                        revision_epoch=2,
                        lifecycle_state="active",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="need one host-approved follow-up message",
                        source_basis="reprioritized bounded opportunity",
                        next_step_hint="request_message_approval",
                        priority_rank=2,
                        revision_epoch=1,
                        lifecycle_state="active",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_proposal_replacement_keeps_stale_branch":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="replace",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_old_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="stale branch that should have been replaced",
                        source_basis="replacement bounded opportunity",
                        next_step_hint="request_old_search_approval",
                        priority_rank=1,
                        revision_epoch=2,
                        lifecycle_state="replaced",
                        merge_group_id="search-replan",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="search",
                        rationale="new active search branch",
                        source_basis="replacement bounded opportunity",
                        next_step_hint="request_new_search_approval",
                        priority_rank=2,
                        revision_epoch=2,
                        lifecycle_state="active",
                        merge_group_id="search-replan",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_proposal_rollback_keeps_stale_branch":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="rollback",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_rolledback_message_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="message",
                        rationale="rolled-back branch that should no longer be active",
                        source_basis="rollback bounded opportunity",
                        next_step_hint="request_rolledback_message_approval",
                        priority_rank=1,
                        revision_epoch=2,
                        lifecycle_state="rolled_back",
                        merge_group_id="rollback-replan",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="search",
                        rationale="active branch after rollback",
                        source_basis="rollback bounded opportunity",
                        next_step_hint="request_search_approval",
                        priority_rank=2,
                        revision_epoch=2,
                        lifecycle_state="active",
                        merge_group_id="rollback-replan",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_proposal_replacement_without_remerge":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="replace",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_merged_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="first active branch that should have been merged away",
                        source_basis="replacement merge bounded opportunity",
                        next_step_hint="request_merged_search_approval",
                        priority_rank=1,
                        revision_epoch=2,
                        lifecycle_state="active",
                        merge_group_id="search-merge",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="second active branch in the same merge group",
                        source_basis="replacement merge bounded opportunity",
                        next_step_hint="request_merge_followup_approval",
                        priority_rank=2,
                        revision_epoch=2,
                        lifecycle_state="active",
                        merge_group_id="search-merge",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_proposal_rollback_without_remerge":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="rollback",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_restored_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="restored branch that should already be merged into one active rollback result",
                        source_basis="rollback merge bounded opportunity",
                        next_step_hint="request_restored_search_approval",
                        priority_rank=1,
                        revision_epoch=2,
                        lifecycle_state="active",
                        merge_group_id="rollback-merge",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="parallel active rollback branch that should no longer survive separately",
                        source_basis="rollback merge bounded opportunity",
                        next_step_hint="request_restored_message_approval",
                        priority_rank=2,
                        revision_epoch=2,
                        lifecycle_state="active",
                        merge_group_id="rollback-merge",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_step_replacement_without_consolidation":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="replace",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_consolidated_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="first active result in a multi-step replacement chain that should already be consolidated",
                        source_basis="multi-step replacement bounded opportunity",
                        next_step_hint="request_consolidated_search_approval",
                        priority_rank=1,
                        revision_epoch=3,
                        lifecycle_state="active",
                        merge_group_id="search-merge-a",
                        update_chain_id="replace-chain-1",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="second active result still surviving in the same replacement chain",
                        source_basis="multi-step replacement bounded opportunity",
                        next_step_hint="request_consolidated_message_approval",
                        priority_rank=2,
                        revision_epoch=3,
                        lifecycle_state="active",
                        merge_group_id="search-merge-b",
                        update_chain_id="replace-chain-1",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_step_rollback_without_consolidation":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="rollback",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_restored_chain_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="first restored active result in a rollback chain that should already be consolidated",
                        source_basis="multi-step rollback bounded opportunity",
                        next_step_hint="request_restored_chain_search_approval",
                        priority_rank=1,
                        revision_epoch=3,
                        lifecycle_state="active",
                        merge_group_id="rollback-merge-a",
                        update_chain_id="rollback-chain-1",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="second restored active result still surviving in the same rollback chain",
                        source_basis="multi-step rollback bounded opportunity",
                        next_step_hint="request_restored_chain_message_approval",
                        priority_rank=2,
                        revision_epoch=3,
                        lifecycle_state="active",
                        merge_group_id="rollback-merge-b",
                        update_chain_id="rollback-chain-1",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_step_replacement_low_completion_score":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="closure",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_finalized_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="final active replacement result without enough completion evidence",
                        source_basis="multi-step replacement completion scoring",
                        next_step_hint="request_finalized_search_approval",
                        priority_rank=1,
                        revision_epoch=4,
                        lifecycle_state="active",
                        merge_group_id="replace-complete-b",
                        update_chain_id="replace-chain-complete-1",
                        completion_score=0.55,
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="parallel active support proposal outside the completed replacement chain",
                        source_basis="multi-step replacement completion scoring",
                        next_step_hint="request_support_message_approval",
                        priority_rank=2,
                        revision_epoch=4,
                        lifecycle_state="active",
                        merge_group_id="replace-complete-support",
                        completion_score=1.0,
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_step_rollback_low_completion_score":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="closure",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_finalized_rollback_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="final active rollback result without enough completion evidence",
                        source_basis="multi-step rollback completion scoring",
                        next_step_hint="request_finalized_rollback_search_approval",
                        priority_rank=1,
                        revision_epoch=4,
                        lifecycle_state="active",
                        merge_group_id="rollback-complete-b",
                        update_chain_id="rollback-chain-complete-1",
                        completion_score=0.6,
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="parallel active support proposal outside the completed rollback chain",
                        source_basis="multi-step rollback completion scoring",
                        next_step_hint="request_support_message_approval",
                        priority_rank=2,
                        revision_epoch=4,
                        lifecycle_state="active",
                        merge_group_id="rollback-complete-support",
                        completion_score=1.0,
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_step_replacement_closure_ready":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="closure",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_closed_replacement_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="final active replacement result is complete and now carries explicit closure evidence",
                        source_basis="multi-step replacement closure scoring",
                        next_step_hint="request_closed_replacement_search_approval",
                        priority_rank=1,
                        revision_epoch=5,
                        lifecycle_state="active",
                        merge_group_id="replace-closure-ready-b",
                        update_chain_id="replace-chain-closure-ready-1",
                        completion_score=1.0,
                        closure_state="closed",
                        closure_trace_id="closure-trace-replace-ready-1",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="parallel support proposal remains visible outside the closed replacement chain",
                        source_basis="multi-step replacement closure scoring",
                        next_step_hint="request_support_message_approval",
                        priority_rank=2,
                        revision_epoch=5,
                        lifecycle_state="active",
                        merge_group_id="replace-closure-ready-support",
                        completion_score=1.0,
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_step_rollback_closure_ready":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="closure",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_closed_rollback_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="final active rollback result is complete and now carries explicit closure evidence",
                        source_basis="multi-step rollback closure scoring",
                        next_step_hint="request_closed_rollback_search_approval",
                        priority_rank=1,
                        revision_epoch=5,
                        lifecycle_state="active",
                        merge_group_id="rollback-closure-ready-b",
                        update_chain_id="rollback-chain-closure-ready-1",
                        completion_score=1.0,
                        closure_state="closed",
                        closure_trace_id="closure-trace-rollback-ready-1",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="parallel support proposal remains visible outside the closed rollback chain",
                        source_basis="multi-step rollback closure scoring",
                        next_step_hint="request_support_message_approval",
                        priority_rank=2,
                        revision_epoch=5,
                        lifecycle_state="active",
                        merge_group_id="rollback-closure-ready-support",
                        completion_score=1.0,
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_step_replacement_missing_closure_trace":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="closure",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_closed_replacement_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="final active replacement result looks complete but never records a closure trace",
                        source_basis="multi-step replacement closure scoring",
                        next_step_hint="request_closed_replacement_search_approval",
                        priority_rank=1,
                        revision_epoch=5,
                        lifecycle_state="active",
                        merge_group_id="replace-closure-b",
                        update_chain_id="replace-chain-closure-1",
                        completion_score=1.0,
                        closure_state="pending",
                        closure_trace_id="",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="parallel support proposal outside the closed replacement chain",
                        source_basis="multi-step replacement closure scoring",
                        next_step_hint="request_support_message_approval",
                        priority_rank=2,
                        revision_epoch=5,
                        lifecycle_state="active",
                        merge_group_id="replace-closure-support",
                        completion_score=1.0,
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "multi_step_rollback_missing_closure_trace":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=SelfState(
                current_mode=subject_core.self_state.current_mode,
                current_focus="closure",
                response_tendency=ResponseTendency(
                    preferred_mode="ask",
                    preferred_tone=subject_core.self_state.response_tendency.preferred_tone,
                    suggested_next_step="request_closed_rollback_search_approval",
                ),
                policy_hint=subject_core.self_state.policy_hint,
                correction_state=subject_core.self_state.correction_state,
                tension_state=subject_core.self_state.tension_state,
            ),
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="final active rollback result looks complete but never records a closure trace",
                        source_basis="multi-step rollback closure scoring",
                        next_step_hint="request_closed_rollback_search_approval",
                        priority_rank=1,
                        revision_epoch=5,
                        lifecycle_state="active",
                        merge_group_id="rollback-closure-b",
                        update_chain_id="rollback-chain-closure-1",
                        completion_score=1.0,
                        closure_state="open",
                        closure_trace_id="",
                    ),
                    ProposalCandidate(
                        proposal_id="proposal-2",
                        kind="message",
                        rationale="parallel support proposal outside the closed rollback chain",
                        source_basis="multi-step rollback closure scoring",
                        next_step_hint="request_support_message_approval",
                        priority_rank=2,
                        revision_epoch=5,
                        lifecycle_state="active",
                        merge_group_id="rollback-closure-support",
                        completion_score=1.0,
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "proposal_authority_violation":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=subject_core.self_state,
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="message",
                        rationale="invalid authority test",
                        source_basis="stub negative sample",
                        next_step_hint="request_message_approval",
                        priority_rank=1,
                        revision_epoch=1,
                        lifecycle_state="active",
                        behavioral_authority="reply",
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    if sample_mode == "proposal_without_host_approval":
        return SubjectCore(
            identity_continuity=subject_core.identity_continuity,
            memory_projection=subject_core.memory_projection,
            self_state=subject_core.self_state,
            proposal_engine=ProposalEngine(
                proposal_candidates=(
                    ProposalCandidate(
                        proposal_id="proposal-1",
                        kind="search",
                        rationale="invalid host approval test",
                        source_basis="stub negative sample",
                        next_step_hint="request_search_approval",
                        priority_rank=1,
                        revision_epoch=1,
                        lifecycle_state="active",
                        requires_host_approval=False,
                    ),
                )
            ),
            governor_bridge=subject_core.governor_bridge,
        )
    raise ValueError(f"unsupported sample_mode: {sample_mode}")


def validate_subjectcore_facade(subject_core: SubjectCore) -> None:
    if not subject_core.identity_continuity.subject_handle.strip():
        raise ValueError("identity_continuity.subject_handle must be non-empty")
    if not subject_core.identity_continuity.stable_profile.strip():
        raise ValueError("identity_continuity.stable_profile must be non-empty")
    if not subject_core.memory_projection.current_thread_id.strip():
        raise ValueError("memory_projection.current_thread_id must be non-empty")
    if not subject_core.memory_projection.continuity_anchor.strip():
        raise ValueError("memory_projection.continuity_anchor must be non-empty")
    if not subject_core.governor_bridge.host_surface_frozen:
        raise ValueError("governor_bridge.host_surface_frozen must remain true")
    if not subject_core.governor_bridge.proposal_only_required:
        raise ValueError("governor_bridge.proposal_only_required must remain true")
    if subject_core.governor_bridge.behavioral_authority != "none":
        raise ValueError("governor_bridge.behavioral_authority must remain 'none'")
    if subject_core.governor_bridge.autonomous_send_allowed:
        raise ValueError("autonomous_send_allowed must remain false")
    if subject_core.governor_bridge.autonomous_tool_allowed:
        raise ValueError("autonomous_tool_allowed must remain false")

    for proposal in subject_core.proposal_engine.proposal_candidates:
        if not proposal.proposal_id.strip():
            raise ValueError("proposal_id must be non-empty")
        if not proposal.kind.strip():
            raise ValueError("proposal kind must be non-empty")
        if proposal.proposal_only is not True:
            raise ValueError("proposal candidates must remain proposal_only")
        if proposal.behavioral_authority != "none":
            raise ValueError("proposal candidates must keep behavioral_authority='none'")
        if proposal.requires_host_approval is not True:
            raise ValueError("proposal candidates must require host approval")


def build_subjectcore_snapshot(subject_core: SubjectCore) -> SubjectCoreSnapshot:
    validate_subjectcore_facade(subject_core)
    return SubjectCoreSnapshot(
        identity_summary=IdentitySummary(
            subject_handle=subject_core.identity_continuity.subject_handle,
            stable_profile=subject_core.identity_continuity.stable_profile,
            narrative_self_summary=subject_core.identity_continuity.narrative_self_summary,
        ),
        session_self_thread=SessionSelfThread(
            current_thread_id=subject_core.memory_projection.current_thread_id,
            continuity_anchor=subject_core.memory_projection.continuity_anchor,
            recent_self_claims=subject_core.memory_projection.recent_self_claims,
            recent_session_topics=subject_core.memory_projection.recent_session_topics,
        ),
        self_state=subject_core.self_state,
        proposal_candidates=tuple(
            proposal.as_snapshot_dict() for proposal in subject_core.proposal_engine.proposal_candidates
        ),
        governor_constraints=subject_core.governor_bridge.as_snapshot_dict(),
    )


def project_to_host_surface(snapshot: SubjectCoreSnapshot) -> dict[str, Any]:
    trace_payload = {
        "subjectcore_snapshot_contract": "subjectcore.snapshot.v1",
        "identity_summary_present": bool(snapshot.identity_summary.subject_handle),
        "continuity_anchor_present": bool(snapshot.session_self_thread.continuity_anchor),
        "proposal_count": len(snapshot.proposal_candidates),
        "proposal_only_consistent": all(
            proposal.get("proposal_discipline") == "proposal_only"
            and proposal.get("behavioral_authority") == "none"
            and proposal.get("requires_host_approval") is True
            for proposal in snapshot.proposal_candidates
        ),
        "behavioral_authority": snapshot.governor_constraints["behavioral_authority"],
        "corrective_trace_present": snapshot.self_state.correction_state.corrective_trace_present,
        "viability_pressure": snapshot.self_state.tension_state.viability_pressure,
    }
    return {
        "policy_hint": snapshot.self_state.policy_hint.as_dict(),
        "response_tendency": snapshot.self_state.response_tendency.as_dict(),
        "trace_payload": trace_payload,
    }
