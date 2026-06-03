"""Developmental shadow contracts for EgoOperator.

The shadow primitive is lab-only and advisory. It can create prediction and
candidate-bias records for later analysis, but it must not execute tools,
mutate identity, write memory, change boundaries, or own final actions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


DEVELOPMENTAL_SHADOW_PROPOSAL_SCHEMA = "ego_operator.developmental_shadow_proposal.v0"
PREDICTION_RECORD_SCHEMA = "ego_operator.prediction_record.v0"
PREDICTION_CALIBRATION_CANDIDATE_SCHEMA = "ego_operator.prediction_calibration_candidate.v0"
FEEDBACK_LINKED_OUTCOME_OBSERVATION_SCHEMA = "ego_operator.feedback_linked_outcome_observation.v0"
FEEDBACK_UPDATE_CANDIDATE_SCHEMA = "ego_operator.feedback_update_candidate.v0"
FEEDBACK_POLICY_PATCH_ADMISSION_RECORD_SCHEMA = "ego_operator.feedback_policy_patch_admission_record.v0"
CLAIM_CEILING = "Developmental Shadow + PredictionRecord local contract candidate pass"
CALIBRATION_CLAIM_CEILING = "Prediction-error replay/calibration local contract candidate pass"
FEEDBACK_UPDATE_CLAIM_CEILING = "Feedback-update candidate local/scripted candidate pass"
FEEDBACK_POLICY_PATCH_CLAIM_CEILING = "Feedback policy patch admission record local/scripted candidate pass"
FORBIDDEN_WRITE_TARGETS = (
    "canonical_memory",
    "core_memory",
    "identity",
    "boundary",
    "safety_policy",
    "tool_execution",
    "approval_state",
    "program_state",
    "evidence_ledger",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _bounded_list(value: Any, max_items: int = 5) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value[:max_items] if isinstance(item, dict)]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _canonical_action_type(action_type: Any) -> str:
    action = str(action_type or "").strip().lower()
    if action in {"respond", "response", "text_reply"}:
        return "reply"
    if action in {"clarify", "question"}:
        return "ask"
    return action


def _delivery_envelope_for_action(action_type: Any) -> str:
    action = _canonical_action_type(action_type)
    if action in {"reply", "suggest", "repair"}:
        return "reply"
    if action == "ask":
        return "ask"
    if action in {"tool_call", "tool"}:
        return "tool"
    if action in {"block", "refuse", "blocked"}:
        return "block"
    return action or "unknown"


def _delivery_envelope_for_option_kind(option_kind: Any) -> str:
    kind = _canonical_action_type(option_kind)
    if kind in {"reply", "suggest", "repair"}:
        return "reply"
    if kind == "ask":
        return "ask"
    if kind in {"tool_call", "tool"}:
        return "tool"
    if kind in {"block", "refuse", "blocked"}:
        return "block"
    return kind or "unknown"


def _prediction_record_outcome_label(
    *,
    selected_prediction: Dict[str, Any],
    chosen_option: Dict[str, Any],
    observed_outcome: Dict[str, Any],
    option_kind_match: bool,
    delivery_envelope_match: bool,
    mismatch_class: str,
) -> Dict[str, Any]:
    observed_status = str(observed_outcome.get("status") or "")
    comparison_scope = str(chosen_option.get("comparison_scope") or "option_kind")
    selection_owner = str(chosen_option.get("selection_owner") or "unknown")
    predicted_option_kind = _canonical_action_type(
        selected_prediction.get("option_kind")
        or selected_prediction.get("intent_kind")
        or selected_prediction.get("action_type")
    )
    chosen_option_kind = _canonical_action_type(
        chosen_option.get("option_kind")
        or chosen_option.get("intent_kind")
        or chosen_option.get("action_type")
    )
    rationale_refs = [
        str(item)
        for item in selected_prediction.get("rationale_refs") or []
        if isinstance(item, str)
    ]

    label = "prediction_matched"
    eligibility = "not_eligible"
    blocker = "prediction_matched"
    reasons: List[str] = []

    if observed_status in {"blocked", "llm_error", "empty_reply_recovered"}:
        label = "observed_status_error"
        blocker = observed_status
        reasons.append(f"observed_status:{observed_status}")
    elif comparison_scope == "external_owner_handoff":
        label = "runtime_owner_override"
        blocker = "external_owner_handoff"
        reasons.extend([f"selection_owner:{selection_owner}", f"comparison_scope:{comparison_scope}"])
    elif comparison_scope == "gate_envelope" or selection_owner == "runtime_gate":
        label = "runtime_gate_override"
        blocker = "runtime_gate"
        reasons.extend([f"selection_owner:{selection_owner}", f"comparison_scope:{comparison_scope}"])
    elif option_kind_match and delivery_envelope_match:
        label = "prediction_matched"
        blocker = "prediction_matched"
    elif option_kind_match and not delivery_envelope_match:
        label = "delivery_envelope_only"
        blocker = "delivery_envelope_only"
        reasons.append(f"mismatch_class:{mismatch_class}")
    elif not option_kind_match:
        if predicted_option_kind == "ask" and any(
            ref in {"evidence_gap", "user_misunderstanding", "context_gap"}
            for ref in rationale_refs
        ):
            label = "insufficient_context"
            eligibility = "review_only"
            blocker = "needs_context_outcome_review"
            reasons.extend(["predicted_option_kind:ask", "rationale_refs:" + ",".join(sorted(rationale_refs))])
        else:
            label = "comparable_option_kind_mismatch"
            eligibility = "candidate_option_kind_mismatch"
            blocker = ""
            reasons.extend([f"predicted_option_kind:{predicted_option_kind}", f"chosen_option_kind:{chosen_option_kind}"])
    else:
        label = "unknown"
        blocker = "unknown"

    if not reasons:
        reasons.append(label)

    return {
        "outcome_label": label,
        "calibration_eligibility": eligibility,
        "calibration_blocker": blocker,
        "outcome_label_reasons": reasons[:6],
    }


@dataclass(frozen=True)
class DevelopmentalShadowProposal:
    schema_version: str = DEVELOPMENTAL_SHADOW_PROPOSAL_SCHEMA
    mode: str = "shadow"
    advisory_only: bool = True
    side_effects_allowed: bool = False
    state_mutation: str = "forbidden"
    predicted_outcome: Dict[str, Any] = field(default_factory=dict)
    predicted_user_outcome: Dict[str, Any] = field(default_factory=dict)
    predicted_self_delta: Dict[str, Any] = field(default_factory=dict)
    candidate_memory_delta: Dict[str, Any] = field(default_factory=dict)
    candidate_option_bias: Dict[str, Any] = field(default_factory=dict)
    uncertainty: float = 0.5
    trace_payload: Dict[str, Any] = field(default_factory=dict)
    forbidden_write_targets: List[str] = field(default_factory=lambda: list(FORBIDDEN_WRITE_TARGETS))
    evidence_level: str = "E1_shadow_trace"
    rollback_condition: Dict[str, Any] = field(default_factory=dict)
    claim_ceiling: str = CLAIM_CEILING

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PredictionRecord:
    schema_version: str = PREDICTION_RECORD_SCHEMA
    record_id: str = ""
    event_id: str = ""
    created_at: str = ""
    ablation_group: str = "shadow_off"
    state_before: Dict[str, Any] = field(default_factory=dict)
    candidate_options: List[Dict[str, Any]] = field(default_factory=list)
    chosen_option: Dict[str, Any] = field(default_factory=dict)
    predicted_outcome: Dict[str, Any] = field(default_factory=dict)
    observed_outcome: Dict[str, Any] = field(default_factory=dict)
    prediction_error: Dict[str, Any] = field(default_factory=dict)
    candidate_update: Dict[str, Any] = field(default_factory=dict)
    allowed_write_targets: List[str] = field(default_factory=list)
    blocked_write_targets: List[str] = field(default_factory=lambda: list(FORBIDDEN_WRITE_TARGETS))
    evidence_level: str = "E1_local_trace"
    rollback_condition: Dict[str, Any] = field(default_factory=dict)
    claim_ceiling: str = CLAIM_CEILING

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PredictionCalibrationCandidate:
    schema_version: str = PREDICTION_CALIBRATION_CANDIDATE_SCHEMA
    created_at: str = ""
    mode: str = "candidate_only"
    advisory_only: bool = True
    side_effects_allowed: bool = False
    state_mutation: str = "forbidden"
    source_record_count: int = 0
    raw_mismatch_count: int = 0
    canonical_mismatch_count: int = 0
    alias_mismatch_count: int = 0
    option_kind_mismatch_count: int = 0
    delivery_envelope_mismatch_count: int = 0
    delivery_envelope_only_mismatch_count: int = 0
    non_comparable_owner_handoff_count: int = 0
    review_only_mismatch_count: int = 0
    outcome_label_counts: Dict[str, int] = field(default_factory=dict)
    calibration_eligibility_counts: Dict[str, int] = field(default_factory=dict)
    observed_patterns: List[Dict[str, Any]] = field(default_factory=list)
    proposed_adjustments: List[Dict[str, Any]] = field(default_factory=list)
    replay_plan: Dict[str, Any] = field(default_factory=dict)
    uncertainty: float = 0.5
    allowed_write_targets: List[str] = field(default_factory=list)
    blocked_write_targets: List[str] = field(default_factory=lambda: list(FORBIDDEN_WRITE_TARGETS))
    evidence_level: str = "E1_local_analysis"
    rollback_condition: Dict[str, Any] = field(default_factory=dict)
    claim_ceiling: str = CALIBRATION_CLAIM_CEILING

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FeedbackLinkedOutcomeObservation:
    schema_version: str = FEEDBACK_LINKED_OUTCOME_OBSERVATION_SCHEMA
    mode: str = "feedback_observation"
    advisory_only: bool = True
    side_effects_allowed: bool = False
    state_mutation: str = "forbidden"
    previous_record_id: str = ""
    previous_event_id: str = ""
    next_turn_id: str = ""
    previous_outcome_label: str = ""
    previous_calibration_eligibility: str = ""
    feedback_label: str = "unclear"
    feedback_strength: float = 0.0
    feedback_signal: Dict[str, Any] = field(default_factory=dict)
    calibration_implication: str = "not_enough_signal"
    trace_payload: Dict[str, Any] = field(default_factory=dict)
    allowed_write_targets: List[str] = field(default_factory=list)
    blocked_write_targets: List[str] = field(default_factory=lambda: list(FORBIDDEN_WRITE_TARGETS))
    evidence_level: str = "E1_local_trace"
    rollback_condition: Dict[str, Any] = field(default_factory=dict)
    claim_ceiling: str = CLAIM_CEILING

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FeedbackUpdateCandidate:
    schema_version: str = FEEDBACK_UPDATE_CANDIDATE_SCHEMA
    created_at: str = ""
    mode: str = "candidate_only"
    advisory_only: bool = True
    side_effects_allowed: bool = False
    state_mutation: str = "forbidden"
    source_observation_count: int = 0
    positive_feedback_count: int = 0
    negative_feedback_count: int = 0
    feedback_label_counts: Dict[str, int] = field(default_factory=dict)
    calibration_implication_counts: Dict[str, int] = field(default_factory=dict)
    candidate_updates: List[Dict[str, Any]] = field(default_factory=list)
    replay_plan: Dict[str, Any] = field(default_factory=dict)
    uncertainty: float = 0.5
    allowed_write_targets: List[str] = field(default_factory=list)
    blocked_write_targets: List[str] = field(default_factory=lambda: list(FORBIDDEN_WRITE_TARGETS))
    evidence_level: str = "E1_local_analysis"
    rollback_condition: Dict[str, Any] = field(default_factory=dict)
    claim_ceiling: str = FEEDBACK_UPDATE_CLAIM_CEILING

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FeedbackPolicyPatchAdmissionRecord:
    schema_version: str = FEEDBACK_POLICY_PATCH_ADMISSION_RECORD_SCHEMA
    admission_id: str = ""
    created_at: str = ""
    mode: str = "candidate_only"
    admission_status: str = "review_ready_disabled"
    enabled: bool = False
    advisory_only: bool = True
    side_effects_allowed: bool = False
    state_mutation: str = "forbidden"
    default_runtime_change: str = "forbidden"
    memory_write: str = "forbidden"
    training: str = "forbidden"
    patch_payload: Dict[str, Any] = field(default_factory=dict)
    source_evidence: Dict[str, Any] = field(default_factory=dict)
    admission_checks: Dict[str, bool] = field(default_factory=dict)
    reviewer_gate: Dict[str, Any] = field(default_factory=dict)
    allowed_write_targets: List[str] = field(default_factory=list)
    blocked_write_targets: List[str] = field(default_factory=lambda: list(FORBIDDEN_WRITE_TARGETS))
    evidence_level: str = "E2_local_scripted"
    rollback_condition: Dict[str, Any] = field(default_factory=dict)
    claim_ceiling: str = FEEDBACK_POLICY_PATCH_CLAIM_CEILING

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_developmental_shadow_proposal(context: Dict[str, Any]) -> DevelopmentalShadowProposal:
    """Create an advisory shadow proposal from already-built runtime context."""

    subject_context = _as_dict(context.get("subject_context"))
    viability_state = _as_dict(subject_context.get("viability_state"))
    outcome_predictions = _as_dict(subject_context.get("outcome_predictions"))
    selected_prediction = _as_dict(outcome_predictions.get("selected_prediction"))
    options = _bounded_list(outcome_predictions.get("options"), max_items=5)
    scores = _as_dict(viability_state.get("scores"))
    max_pressure = max((_safe_float(v) for v in scores.values()), default=0.0)
    uncertainty = round(max(0.05, min(0.95, 0.55 + max_pressure * 0.25)), 3)
    selected_action = str(selected_prediction.get("action_type") or "reply")
    selected_score = selected_prediction.get("selection_score")

    return DevelopmentalShadowProposal(
        predicted_outcome={
            "selected_action_type": selected_action,
            "selection_score": selected_score,
            "expected_external_status": "text_reply_only",
            "requires_gate": bool(selected_prediction.get("requires_gate", False)),
        },
        predicted_user_outcome={
            "expected_friction": "lower" if scores.get("relationship_risk", 0.0) else "unknown",
            "needs_clarification": selected_action == "ask",
        },
        predicted_self_delta={
            "viability_pressure_max": max_pressure,
            "expected_state_mutation": "none",
            "identity_change": "forbidden",
        },
        candidate_memory_delta={
            "status": "candidate_only",
            "core_memory_write": "forbidden",
            "promotion_required": "explicit_memory_gate",
        },
        candidate_option_bias={
            "bias_target_action_type": selected_action,
            "bias_strength": round(min(0.35, max_pressure * 0.2), 3),
            "source": "shadow_prediction_only",
        },
        uncertainty=uncertainty,
        trace_payload={
            "input_signal_keys": sorted(subject_context.keys()),
            "option_count": len(options),
            "top_option_action_type": str((options[0] or {}).get("action_type") if options else ""),
            "created_at": _utc_now(),
        },
        rollback_condition={
            "disable_flag": "developmental_shadow_enabled",
            "reason": "shadow proposal causes trace pollution or is mistaken for authority",
        },
    )


def validate_shadow_proposal_boundary(proposal: DevelopmentalShadowProposal | Dict[str, Any]) -> Dict[str, Any]:
    payload = proposal.as_dict() if isinstance(proposal, DevelopmentalShadowProposal) else _as_dict(proposal)
    failures: List[str] = []
    if payload.get("advisory_only") is not True:
        failures.append("not_advisory_only")
    if payload.get("side_effects_allowed") is not False:
        failures.append("side_effects_allowed")
    if payload.get("state_mutation") != "forbidden":
        failures.append("state_mutation_not_forbidden")
    forbidden_targets = set(payload.get("forbidden_write_targets") or [])
    missing = sorted(set(FORBIDDEN_WRITE_TARGETS) - forbidden_targets)
    if missing:
        failures.append("missing_forbidden_targets:" + ",".join(missing))
    return {
        "schema_version": "ego_operator.developmental_shadow_boundary_check.v0",
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "side_effects_executed": False,
        "canonical_state_mutation": False,
    }


def build_prediction_record(
    *,
    record_id: str,
    event_id: str,
    ablation_group: str,
    state_before: Dict[str, Any],
    outcome_predictions: Dict[str, Any],
    chosen_option: Dict[str, Any],
    observed_outcome: Dict[str, Any],
    shadow_proposal: DevelopmentalShadowProposal | None = None,
) -> PredictionRecord:
    options = _bounded_list(_as_dict(outcome_predictions).get("options"), max_items=8)
    selected_prediction = _as_dict(_as_dict(outcome_predictions).get("selected_prediction"))
    predicted_action = str(selected_prediction.get("action_type") or "")
    chosen_action = str(chosen_option.get("action_type") or "")
    predicted_option_kind = _canonical_action_type(
        selected_prediction.get("option_kind")
        or selected_prediction.get("intent_kind")
        or predicted_action
    )
    chosen_option_kind = _canonical_action_type(
        chosen_option.get("option_kind")
        or chosen_option.get("intent_kind")
        or chosen_action
    )
    predicted_delivery_envelope = str(
        selected_prediction.get("delivery_envelope")
        or _delivery_envelope_for_option_kind(predicted_option_kind)
    )
    chosen_delivery_envelope = str(
        chosen_option.get("delivery_envelope")
        or _delivery_envelope_for_action(chosen_action)
    )
    option_kind_match = bool(
        predicted_option_kind
        and chosen_option_kind
        and predicted_option_kind == chosen_option_kind
    )
    delivery_envelope_match = bool(
        predicted_delivery_envelope
        and chosen_delivery_envelope
        and predicted_delivery_envelope == chosen_delivery_envelope
    )
    if option_kind_match and delivery_envelope_match:
        mismatch_class = "none"
    elif option_kind_match:
        mismatch_class = "delivery_envelope_mismatch"
    elif delivery_envelope_match:
        mismatch_class = "option_kind_mismatch_same_delivery"
    else:
        mismatch_class = "option_kind_and_delivery_mismatch"
    observed_status = str(observed_outcome.get("status") or "")
    outcome_label_payload = _prediction_record_outcome_label(
        selected_prediction=selected_prediction,
        chosen_option=chosen_option,
        observed_outcome=observed_outcome,
        option_kind_match=option_kind_match,
        delivery_envelope_match=delivery_envelope_match,
        mismatch_class=mismatch_class,
    )
    prediction_error = {
        "schema_version": "ego_operator.prediction_error.v0",
        "action_type_match": bool(predicted_action and chosen_action and predicted_action == chosen_action),
        "canonical_action_type_match": bool(
            predicted_action
            and chosen_action
            and _canonical_action_type(predicted_action) == _canonical_action_type(chosen_action)
        ),
        "predicted_action_type": predicted_action,
        "chosen_action_type": chosen_action,
        "predicted_canonical_action_type": _canonical_action_type(predicted_action),
        "chosen_canonical_action_type": _canonical_action_type(chosen_action),
        "predicted_option_kind": predicted_option_kind,
        "chosen_option_kind": chosen_option_kind,
        "predicted_delivery_envelope": predicted_delivery_envelope,
        "chosen_delivery_envelope": chosen_delivery_envelope,
        "option_kind_match": option_kind_match,
        "delivery_envelope_match": delivery_envelope_match,
        "mismatch_class": mismatch_class,
        "comparison_scope": str(chosen_option.get("comparison_scope") or "option_kind"),
        "selection_owner": str(chosen_option.get("selection_owner") or "unknown"),
        **outcome_label_payload,
        "observed_status": observed_status,
        "side_effect_observed": bool(observed_outcome.get("side_effects_executed")),
        "error_class": "none" if observed_status not in {"blocked", "llm_error", "empty_reply_recovered"} else observed_status,
    }
    candidate_update = {
        "status": "candidate_only" if shadow_proposal is not None else "skipped",
        "source": "developmental_shadow" if shadow_proposal is not None else "prediction_record_only",
        "option_bias": shadow_proposal.candidate_option_bias if shadow_proposal is not None else {},
        "state_mutation": "forbidden",
        "gate_required_for_promotion": True,
    }
    return PredictionRecord(
        record_id=record_id,
        event_id=event_id,
        created_at=_utc_now(),
        ablation_group=ablation_group,
        state_before=state_before,
        candidate_options=options,
        chosen_option=chosen_option,
        predicted_outcome=selected_prediction,
        observed_outcome=observed_outcome,
        prediction_error=prediction_error,
        candidate_update=candidate_update,
        allowed_write_targets=[],
        blocked_write_targets=list(FORBIDDEN_WRITE_TARGETS),
        rollback_condition={
            "disable_flag": "developmental_shadow_enabled",
            "reason": "prediction records are decorative, misleading, or contaminate runtime behavior",
        },
    )


def build_prediction_calibration_candidate(records: List[Dict[str, Any]]) -> PredictionCalibrationCandidate:
    """Summarize PredictionRecord mismatches into replayable calibration candidates."""

    patterns: Dict[tuple[str, str], Dict[str, Any]] = {}
    raw_mismatch_count = 0
    alias_mismatch_count = 0
    canonical_mismatch_count = 0
    option_kind_mismatch_count = 0
    delivery_envelope_mismatch_count = 0
    delivery_envelope_only_mismatch_count = 0
    non_comparable_owner_handoff_count = 0
    review_only_mismatch_count = 0
    outcome_label_counts: Dict[str, int] = {}
    calibration_eligibility_counts: Dict[str, int] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        error = _as_dict(record.get("prediction_error"))
        outcome_label = str(error.get("outcome_label") or "")
        calibration_eligibility = str(error.get("calibration_eligibility") or "")
        if outcome_label:
            outcome_label_counts[outcome_label] = outcome_label_counts.get(outcome_label, 0) + 1
        if calibration_eligibility:
            calibration_eligibility_counts[calibration_eligibility] = calibration_eligibility_counts.get(calibration_eligibility, 0) + 1
        predicted = str(error.get("predicted_action_type") or "")
        chosen = str(error.get("chosen_action_type") or "")
        predicted_canonical = str(error.get("predicted_canonical_action_type") or _canonical_action_type(predicted))
        chosen_canonical = str(error.get("chosen_canonical_action_type") or _canonical_action_type(chosen))
        has_delivery_intent = any(
            key in error
            for key in (
                "predicted_option_kind",
                "chosen_option_kind",
                "predicted_delivery_envelope",
                "chosen_delivery_envelope",
            )
        )
        predicted_option_kind = str(error.get("predicted_option_kind") or predicted_canonical)
        chosen_option_kind = str(error.get("chosen_option_kind") or chosen_canonical)
        predicted_delivery = str(error.get("predicted_delivery_envelope") or _delivery_envelope_for_option_kind(predicted_option_kind))
        chosen_delivery = str(error.get("chosen_delivery_envelope") or _delivery_envelope_for_action(chosen))
        comparison_scope = str(error.get("comparison_scope") or "option_kind")
        if predicted and chosen and predicted != chosen:
            raw_mismatch_count += 1
        if predicted and chosen and predicted != chosen and predicted_canonical == chosen_canonical:
            alias_mismatch_count += 1
            continue
        if has_delivery_intent:
            if predicted_delivery and chosen_delivery and predicted_delivery != chosen_delivery:
                delivery_envelope_mismatch_count += 1
            if (
                predicted
                and chosen
                and predicted != chosen
                and predicted_option_kind == chosen_option_kind
                and predicted_delivery == chosen_delivery
            ):
                delivery_envelope_only_mismatch_count += 1
            if comparison_scope == "external_owner_handoff":
                non_comparable_owner_handoff_count += 1
                continue
            if not predicted_option_kind or not chosen_option_kind or predicted_option_kind == chosen_option_kind:
                continue
            if calibration_eligibility and calibration_eligibility != "candidate_option_kind_mismatch":
                if calibration_eligibility == "review_only":
                    review_only_mismatch_count += 1
                continue
            canonical_mismatch_count += 1
            option_kind_mismatch_count += 1
            key = (predicted_option_kind, chosen_option_kind)
            pattern_basis = "option_kind"
        else:
            if not predicted_canonical or not chosen_canonical or predicted_canonical == chosen_canonical:
                continue
            canonical_mismatch_count += 1
            option_kind_mismatch_count += 1
            key = (predicted_canonical, chosen_canonical)
            pattern_basis = "legacy_canonical_action_type"
        bucket = patterns.setdefault(
            key,
            {
                "predicted_action_type": key[0],
                "chosen_action_type": key[1],
                "predicted_option_kind": key[0],
                "chosen_option_kind": key[1],
                "pattern_basis": pattern_basis,
                "count": 0,
                "record_ids": [],
                "example_events": [],
                "rationale_refs": [],
                "outcome_labels": [],
                "calibration_eligibilities": [],
            },
        )
        bucket["count"] += 1
        if len(bucket["record_ids"]) < 5:
            bucket["record_ids"].append(record.get("record_id"))
        if len(bucket["example_events"]) < 3:
            bucket["example_events"].append({
                "record_id": record.get("record_id"),
                "event_id": record.get("event_id"),
                "predicted_outcome": record.get("predicted_outcome"),
                "chosen_option": record.get("chosen_option"),
                "observed_outcome": record.get("observed_outcome"),
                "prediction_error": {
                    "predicted_delivery_envelope": predicted_delivery,
                    "chosen_delivery_envelope": chosen_delivery,
                    "comparison_scope": comparison_scope,
                    "outcome_label": outcome_label,
                    "calibration_eligibility": calibration_eligibility,
                },
            })
        predicted_outcome = _as_dict(record.get("predicted_outcome"))
        for ref in predicted_outcome.get("rationale_refs") or []:
            if ref not in bucket["rationale_refs"]:
                bucket["rationale_refs"].append(ref)
        if outcome_label and outcome_label not in bucket["outcome_labels"]:
            bucket["outcome_labels"].append(outcome_label)
        if calibration_eligibility and calibration_eligibility not in bucket["calibration_eligibilities"]:
            bucket["calibration_eligibilities"].append(calibration_eligibility)

    observed_patterns = sorted(patterns.values(), key=lambda item: (-int(item.get("count") or 0), str(item.get("predicted_action_type") or "")))
    proposed_adjustments: List[Dict[str, Any]] = []
    for pattern in observed_patterns:
        count = int(pattern.get("count") or 0)
        proposed_adjustments.append({
            "status": "candidate_only",
            "predicted_action_type": pattern.get("predicted_action_type"),
            "observed_chosen_action_type": pattern.get("chosen_action_type"),
            "predicted_option_kind": pattern.get("predicted_option_kind"),
            "observed_chosen_option_kind": pattern.get("chosen_option_kind"),
            "pattern_basis": pattern.get("pattern_basis"),
            "source_outcome_labels": pattern.get("outcome_labels") or [],
            "source_calibration_eligibilities": pattern.get("calibration_eligibilities") or [],
            "support_count": count,
            "confidence": round(min(0.8, 0.35 + count * 0.1), 3),
            "proposal": (
                "Replay this pattern with calibration enabled in a lab-only arm; "
                "do not change runtime selection until a later baseline comparison proves improvement."
            ),
            "promotion_gate": "manual_replay_and_baseline_comparison_required",
            "state_mutation": "forbidden",
        })

    return PredictionCalibrationCandidate(
        created_at=_utc_now(),
        source_record_count=sum(1 for record in records if isinstance(record, dict)),
        raw_mismatch_count=raw_mismatch_count,
        canonical_mismatch_count=canonical_mismatch_count,
        alias_mismatch_count=alias_mismatch_count,
        option_kind_mismatch_count=option_kind_mismatch_count,
        delivery_envelope_mismatch_count=delivery_envelope_mismatch_count,
        delivery_envelope_only_mismatch_count=delivery_envelope_only_mismatch_count,
        non_comparable_owner_handoff_count=non_comparable_owner_handoff_count,
        review_only_mismatch_count=review_only_mismatch_count,
        outcome_label_counts=dict(sorted(outcome_label_counts.items())),
        calibration_eligibility_counts=dict(sorted(calibration_eligibility_counts.items())),
        observed_patterns=observed_patterns,
        proposed_adjustments=proposed_adjustments,
        replay_plan={
            "status": "candidate_only",
            "requires_replay": canonical_mismatch_count > 0,
            "recommended_next_experiment": "prediction_error_replay_calibration_ablation",
            "replay_inputs": "PredictionRecord JSONL + original sample pack",
            "promotion_condition": "later lab arm reduces canonical mismatches without tools, approvals, memory writes, or weaker user-visible behavior",
        },
        uncertainty=round(max(0.1, min(0.95, 0.7 - canonical_mismatch_count * 0.05)), 3),
        allowed_write_targets=[],
        blocked_write_targets=list(FORBIDDEN_WRITE_TARGETS),
        rollback_condition={
            "disable_flag": "prediction_error_calibration_enabled",
            "reason": "calibration candidate is mistaken for runtime authority or produces unverified behavior changes",
        },
    )


def validate_prediction_calibration_boundary(candidate: PredictionCalibrationCandidate | Dict[str, Any]) -> Dict[str, Any]:
    payload = candidate.as_dict() if isinstance(candidate, PredictionCalibrationCandidate) else _as_dict(candidate)
    failures: List[str] = []
    if payload.get("advisory_only") is not True:
        failures.append("not_advisory_only")
    if payload.get("side_effects_allowed") is not False:
        failures.append("side_effects_allowed")
    if payload.get("state_mutation") != "forbidden":
        failures.append("state_mutation_not_forbidden")
    if payload.get("allowed_write_targets") not in ([], None):
        failures.append("allowed_write_targets_not_empty")
    forbidden_targets = set(payload.get("blocked_write_targets") or [])
    missing = sorted(set(FORBIDDEN_WRITE_TARGETS) - forbidden_targets)
    if missing:
        failures.append("missing_blocked_targets:" + ",".join(missing))
    return {
        "schema_version": "ego_operator.prediction_calibration_boundary_check.v0",
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "side_effects_executed": False,
        "canonical_state_mutation": False,
        "runtime_selection_changed": False,
    }


def _feedback_signal_from_text(text: Any) -> Dict[str, Any]:
    raw = str(text or "").strip()
    normalized = raw.lower()
    matched_markers: List[str] = []
    label = "unclear"
    strength = 0.0
    implication = "not_enough_signal"

    correction_markers = ("不对", "不是", "误会", "偏了", "纠正", "答非所问", "没让你")
    rejection_markers = ("不要这样", "别这样", "停", "算了", "不需要", "不是这个")
    confirmation_markers = ("对", "没错", "可以", "很好", "就这样", "答对")
    continuation_markers = ("继续", "接着", "往下", "下一步")
    redirect_markers = ("换个方向", "先说", "改成", "换成", "回到")

    if any(marker in raw for marker in correction_markers):
        label = "explicit_correction"
        strength = 0.9
        implication = "negative_feedback_review"
        matched_markers = [marker for marker in correction_markers if marker in raw]
    elif any(marker in raw for marker in rejection_markers):
        label = "explicit_rejection"
        strength = 0.85
        implication = "negative_feedback_review"
        matched_markers = [marker for marker in rejection_markers if marker in raw]
    elif any(marker in raw for marker in redirect_markers):
        label = "redirect"
        strength = 0.55
        implication = "not_enough_signal"
        matched_markers = [marker for marker in redirect_markers if marker in raw]
    elif any(marker in raw for marker in continuation_markers) and any(marker in raw for marker in confirmation_markers):
        label = "positive_continuation"
        strength = 0.75
        implication = "positive_support_only"
        matched_markers = [
            marker
            for marker in continuation_markers + confirmation_markers
            if marker in raw
        ]
    elif any(marker in raw for marker in continuation_markers):
        label = "continuation_request"
        strength = 0.45
        implication = "not_enough_signal"
        matched_markers = [marker for marker in continuation_markers if marker in raw]
    elif any(marker in raw for marker in confirmation_markers):
        label = "confirmation"
        strength = 0.65
        implication = "positive_support_only"
        matched_markers = [marker for marker in confirmation_markers if marker in raw]

    return {
        "label": label,
        "strength": strength,
        "calibration_implication": implication,
        "matched_markers": matched_markers[:5],
        "text_excerpt": raw[:160],
        "text_length": len(raw),
        "normalized_contains_ascii": any("a" <= char <= "z" for char in normalized),
    }


def build_feedback_linked_outcome_observation(
    *,
    previous_record: Dict[str, Any],
    next_turn_id: str,
    next_user_text: str,
) -> FeedbackLinkedOutcomeObservation:
    """Link a PredictionRecord to the next user feedback signal.

    The observation is replay/advisory data only. It must not write memory,
    change identity, alter policy, or execute tools.
    """

    previous_error = _as_dict(previous_record.get("prediction_error"))
    signal = _feedback_signal_from_text(next_user_text)
    previous_eligibility = str(previous_error.get("calibration_eligibility") or "")
    implication = str(signal.get("calibration_implication") or "not_enough_signal")
    if implication == "negative_feedback_review" and previous_eligibility == "candidate_option_kind_mismatch":
        implication = "negative_feedback_candidate_review"
    elif implication == "positive_support_only" and previous_eligibility == "candidate_option_kind_mismatch":
        implication = "positive_support_candidate_only"

    return FeedbackLinkedOutcomeObservation(
        previous_record_id=str(previous_record.get("record_id") or ""),
        previous_event_id=str(previous_record.get("event_id") or ""),
        next_turn_id=str(next_turn_id or ""),
        previous_outcome_label=str(previous_error.get("outcome_label") or ""),
        previous_calibration_eligibility=previous_eligibility,
        feedback_label=str(signal.get("label") or "unclear"),
        feedback_strength=round(_safe_float(signal.get("strength")), 3),
        feedback_signal=signal,
        calibration_implication=implication,
        trace_payload={
            "previous_prediction_error": {
                "predicted_option_kind": previous_error.get("predicted_option_kind"),
                "chosen_option_kind": previous_error.get("chosen_option_kind"),
                "outcome_label": previous_error.get("outcome_label"),
                "calibration_eligibility": previous_error.get("calibration_eligibility"),
                "selection_owner": previous_error.get("selection_owner"),
            },
            "created_at": _utc_now(),
        },
        allowed_write_targets=[],
        blocked_write_targets=list(FORBIDDEN_WRITE_TARGETS),
        rollback_condition={
            "disable_flag": "feedback_linked_outcome_observation_enabled",
            "reason": "feedback observations are mistaken for runtime authority or memory writes",
        },
    )


def validate_feedback_linked_outcome_observation(
    observation: FeedbackLinkedOutcomeObservation | Dict[str, Any],
) -> Dict[str, Any]:
    payload = observation.as_dict() if isinstance(observation, FeedbackLinkedOutcomeObservation) else _as_dict(observation)
    failures: List[str] = []
    if payload.get("advisory_only") is not True:
        failures.append("not_advisory_only")
    if payload.get("side_effects_allowed") is not False:
        failures.append("side_effects_allowed")
    if payload.get("state_mutation") != "forbidden":
        failures.append("state_mutation_not_forbidden")
    if payload.get("allowed_write_targets") not in ([], None):
        failures.append("allowed_write_targets_not_empty")
    blocked_targets = set(payload.get("blocked_write_targets") or [])
    missing = sorted(set(FORBIDDEN_WRITE_TARGETS) - blocked_targets)
    if missing:
        failures.append("missing_blocked_targets:" + ",".join(missing))
    return {
        "schema_version": "ego_operator.feedback_linked_outcome_boundary_check.v0",
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "side_effects_executed": False,
        "canonical_state_mutation": False,
        "runtime_selection_changed": False,
    }


def build_feedback_update_candidate(observations: List[Dict[str, Any]]) -> FeedbackUpdateCandidate:
    """Summarize feedback observations into advisory replay/update candidates."""

    feedback_label_counts: Dict[str, int] = {}
    calibration_implication_counts: Dict[str, int] = {}
    candidate_updates: List[Dict[str, Any]] = []
    positive_feedback_count = 0
    negative_feedback_count = 0
    for item in observations:
        if not isinstance(item, dict):
            continue
        label = str(item.get("feedback_label") or "")
        implication = str(item.get("calibration_implication") or "")
        if label:
            feedback_label_counts[label] = feedback_label_counts.get(label, 0) + 1
        if implication:
            calibration_implication_counts[implication] = calibration_implication_counts.get(implication, 0) + 1
        if implication.startswith("positive_support"):
            positive_feedback_count += 1
        if implication.startswith("negative_feedback"):
            negative_feedback_count += 1
            candidate_updates.append({
                "update_kind": "review_previous_prediction",
                "previous_record_id": str(item.get("previous_record_id") or ""),
                "previous_event_id": str(item.get("previous_event_id") or ""),
                "previous_outcome_label": str(item.get("previous_outcome_label") or ""),
                "previous_calibration_eligibility": str(item.get("previous_calibration_eligibility") or ""),
                "feedback_label": label,
                "feedback_strength": _safe_float(item.get("feedback_strength")),
                "calibration_implication": implication,
                "proposal": "replay_before_any_policy_update",
                "state_mutation": "forbidden",
            })

    replay_required = bool(candidate_updates)
    uncertainty = 0.35 if positive_feedback_count and negative_feedback_count else 0.65
    return FeedbackUpdateCandidate(
        created_at=_utc_now(),
        source_observation_count=len([item for item in observations if isinstance(item, dict)]),
        positive_feedback_count=positive_feedback_count,
        negative_feedback_count=negative_feedback_count,
        feedback_label_counts=dict(sorted(feedback_label_counts.items())),
        calibration_implication_counts=dict(sorted(calibration_implication_counts.items())),
        candidate_updates=candidate_updates[:8],
        replay_plan={
            "required_before_runtime_change": replay_required,
            "minimum_replay_cases": max(1, len(candidate_updates)) if replay_required else 0,
            "requires_human_or_scripted_review": replay_required,
            "default_runtime_change": "forbidden",
            "memory_write": "forbidden",
        },
        uncertainty=uncertainty,
        allowed_write_targets=[],
        blocked_write_targets=list(FORBIDDEN_WRITE_TARGETS),
        rollback_condition={
            "disable_flag": "feedback_update_candidate_enabled",
            "reason": "feedback candidate is mistaken for memory, policy, or runtime authority",
        },
    )


def validate_feedback_update_candidate(
    candidate: FeedbackUpdateCandidate | Dict[str, Any],
) -> Dict[str, Any]:
    payload = candidate.as_dict() if isinstance(candidate, FeedbackUpdateCandidate) else _as_dict(candidate)
    failures: List[str] = []
    if payload.get("advisory_only") is not True:
        failures.append("not_advisory_only")
    if payload.get("side_effects_allowed") is not False:
        failures.append("side_effects_allowed")
    if payload.get("state_mutation") != "forbidden":
        failures.append("state_mutation_not_forbidden")
    if payload.get("allowed_write_targets") not in ([], None):
        failures.append("allowed_write_targets_not_empty")
    blocked_targets = set(payload.get("blocked_write_targets") or [])
    missing = sorted(set(FORBIDDEN_WRITE_TARGETS) - blocked_targets)
    if missing:
        failures.append("missing_blocked_targets:" + ",".join(missing))
    for update in payload.get("candidate_updates") or []:
        if not isinstance(update, dict):
            failures.append("candidate_update_not_object")
            continue
        if update.get("state_mutation") != "forbidden":
            failures.append("candidate_update_state_mutation_not_forbidden")
        if update.get("proposal") != "replay_before_any_policy_update":
            failures.append("candidate_update_missing_replay_guard")
    replay_plan = _as_dict(payload.get("replay_plan"))
    if payload.get("candidate_updates") and replay_plan.get("required_before_runtime_change") is not True:
        failures.append("replay_not_required_for_candidate_updates")
    if replay_plan.get("default_runtime_change") != "forbidden":
        failures.append("default_runtime_change_not_forbidden")
    if replay_plan.get("memory_write") != "forbidden":
        failures.append("memory_write_not_forbidden")
    return {
        "schema_version": "ego_operator.feedback_update_candidate_boundary_check.v0",
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "side_effects_executed": False,
        "canonical_state_mutation": False,
        "runtime_selection_changed": False,
    }


def build_feedback_policy_patch_admission_record(
    *,
    feedback_update_candidate: Dict[str, Any],
    runtime_ablation_report: Dict[str, Any],
    cross_pack_guard_report: Dict[str, Any],
) -> FeedbackPolicyPatchAdmissionRecord:
    """Package feedback-policy evidence into a disabled review artifact.

    This is an admission record, not an enabled policy. It exists so later work
    can review exactly which candidate was supported, which guards passed, and
    which rollback conditions must hold before any runtime change is considered.
    """

    candidate_updates = [
        item
        for item in feedback_update_candidate.get("candidate_updates") or []
        if isinstance(item, dict)
    ]
    target_results = [
        item
        for item in runtime_ablation_report.get("target_ablation_results") or []
        if isinstance(item, dict)
    ]
    target = target_results[0] if target_results else {}
    cross_summary = _as_dict(cross_pack_guard_report.get("cross_pack_guard_summary"))
    ablation_summary = _as_dict(runtime_ablation_report.get("ablation_summary"))
    source_evidence = {
        "feedback_update_candidate_schema": feedback_update_candidate.get("schema_version"),
        "feedback_update_candidate_mode": feedback_update_candidate.get("mode"),
        "candidate_update_count": len(candidate_updates),
        "runtime_ablation_status": runtime_ablation_report.get("status"),
        "runtime_ablation_decision": runtime_ablation_report.get("decision"),
        "target_case_count": ablation_summary.get("target_case_count"),
        "target_improved_count": ablation_summary.get("target_improved_count"),
        "unrelated_regression_count": ablation_summary.get("unrelated_regression_count"),
        "cross_pack_guard_status": cross_pack_guard_report.get("status"),
        "cross_pack_guard_decision": cross_pack_guard_report.get("decision"),
        "guard_record_count": cross_summary.get("guard_record_count"),
        "guard_scoped_application_count": cross_summary.get("guard_scoped_application_count"),
        "guard_unrelated_regression_count": cross_summary.get("guard_unrelated_regression_count"),
        "guard_pattern_collision_count": cross_summary.get("guard_pattern_collision_count"),
    }
    patch_payload = {
        "patch_kind": "feedback_option_bias_candidate",
        "activation_scope": "record_scoped_candidate_only",
        "enabled": False,
        "source_record_id": str(target.get("record_id") or ""),
        "source_case_id": str(target.get("case_id") or ""),
        "predicted_action_type": str(target.get("predicted_action") or ""),
        "preferred_action_type": str(target.get("chosen_action") or ""),
        "baseline_top_action": str(target.get("baseline_top_action") or ""),
        "ablation_top_action": str(target.get("ablation_top_action") or ""),
        "target_improved": target.get("target_improved") is True,
        "candidate_updates": candidate_updates[:3],
        "default_runtime_change": "forbidden",
        "memory_write": "forbidden",
        "training": "forbidden",
        "runtime_selection_changed": False,
    }
    checks = {
        "feedback_update_candidate_present": bool(candidate_updates),
        "feedback_update_candidate_mode_candidate_only": feedback_update_candidate.get("mode") == "candidate_only",
        "feedback_update_candidate_no_writes": feedback_update_candidate.get("allowed_write_targets") in ([], None),
        "runtime_ablation_pass": runtime_ablation_report.get("status") == "scripted_feedback_runtime_ablation_proof_pass",
        "runtime_ablation_target_improved": int(ablation_summary.get("target_improved_count") or 0) >= 1,
        "runtime_ablation_unrelated_no_regression": int(ablation_summary.get("unrelated_regression_count") or 0) == 0,
        "cross_pack_guard_pass": cross_pack_guard_report.get("status") == "scripted_cross_pack_feedback_ablation_guard_pass",
        "cross_pack_guard_scoped": int(cross_summary.get("guard_scoped_application_count") or 0) == 0,
        "cross_pack_guard_no_unrelated_regression": int(cross_summary.get("guard_unrelated_regression_count") or 0) == 0,
        "cross_pack_guard_no_pattern_collision": int(cross_summary.get("guard_pattern_collision_count") or 0) == 0,
        "broad_pattern_application_disallowed": (cross_pack_guard_report.get("checks") or {}).get("broad_pattern_application_disallowed") is True,
        "default_runtime_change_forbidden": True,
        "memory_write_forbidden": True,
        "training_forbidden": True,
        "no_allowed_writes": True,
        "reviewer_gate_required": True,
    }
    return FeedbackPolicyPatchAdmissionRecord(
        admission_id=f"admit_{str(target.get('record_id') or 'feedback_policy_patch')}",
        created_at=_utc_now(),
        admission_status="review_ready_disabled" if all(checks.values()) else "blocked",
        patch_payload=patch_payload,
        source_evidence=source_evidence,
        admission_checks=checks,
        reviewer_gate={
            "required_before_enablement": True,
            "minimum_next_gate": "human_or_scripted_policy_admission_review",
            "enablement_default": "disabled",
            "promotion_requires": [
                "reviewer_approval",
                "broader_replay_no_regression",
                "human_sanity_or_operator_comment",
            ],
        },
        allowed_write_targets=[],
        blocked_write_targets=list(FORBIDDEN_WRITE_TARGETS),
        rollback_condition={
            "remove_record": "feedback_policy_patch_admission_record",
            "disable_flag": "prediction_calibration_enabled",
            "reason": "candidate causes regression, broad pattern drift, or is mistaken for default runtime authority",
        },
    )


def validate_feedback_policy_patch_admission_record(
    record: FeedbackPolicyPatchAdmissionRecord | Dict[str, Any],
) -> Dict[str, Any]:
    payload = record.as_dict() if isinstance(record, FeedbackPolicyPatchAdmissionRecord) else _as_dict(record)
    failures: List[str] = []
    if payload.get("mode") != "candidate_only":
        failures.append("mode_not_candidate_only")
    if payload.get("admission_status") != "review_ready_disabled":
        failures.append("admission_not_review_ready_disabled")
    if payload.get("enabled") is not False:
        failures.append("enabled_not_false")
    if payload.get("advisory_only") is not True:
        failures.append("not_advisory_only")
    if payload.get("side_effects_allowed") is not False:
        failures.append("side_effects_allowed")
    if payload.get("state_mutation") != "forbidden":
        failures.append("state_mutation_not_forbidden")
    if payload.get("default_runtime_change") != "forbidden":
        failures.append("default_runtime_change_not_forbidden")
    if payload.get("memory_write") != "forbidden":
        failures.append("memory_write_not_forbidden")
    if payload.get("training") != "forbidden":
        failures.append("training_not_forbidden")
    if payload.get("allowed_write_targets") not in ([], None):
        failures.append("allowed_write_targets_not_empty")
    blocked_targets = set(payload.get("blocked_write_targets") or [])
    missing = sorted(set(FORBIDDEN_WRITE_TARGETS) - blocked_targets)
    if missing:
        failures.append("missing_blocked_targets:" + ",".join(missing))
    if not all((_as_dict(payload.get("admission_checks"))).values()):
        failures.append("admission_checks_not_all_true")
    patch_payload = _as_dict(payload.get("patch_payload"))
    if patch_payload.get("enabled") is not False:
        failures.append("patch_payload_enabled_not_false")
    if patch_payload.get("default_runtime_change") != "forbidden":
        failures.append("patch_payload_default_runtime_change_not_forbidden")
    if patch_payload.get("memory_write") != "forbidden":
        failures.append("patch_payload_memory_write_not_forbidden")
    if patch_payload.get("training") != "forbidden":
        failures.append("patch_payload_training_not_forbidden")
    reviewer_gate = _as_dict(payload.get("reviewer_gate"))
    if reviewer_gate.get("required_before_enablement") is not True:
        failures.append("reviewer_gate_not_required")
    return {
        "schema_version": "ego_operator.feedback_policy_patch_admission_boundary_check.v0",
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "side_effects_executed": False,
        "canonical_state_mutation": False,
        "runtime_selection_changed": False,
        "memory_write_executed": False,
        "training_executed": False,
    }
