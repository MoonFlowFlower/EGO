"""Shared embodied initiative primitive contracts for EgoOperator.

The contract covers Live2D/presence expression and proactive outreach as one
bounded primitive family. It never renders an avatar, schedules work, sends a
message, writes memory, or executes tools. Runtime gates remain the only
admission path for side effects.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict
import re


EMBODIED_INITIATIVE_CONTRACT_SCHEMA = "ego_operator.embodied_initiative_contract.v1"
PRESENCE_STATE_SCHEMA = "ego_operator.presence_state_proposal.v1"
DELIVERY_GATE_SCHEMA = "ego_operator.delivery_gate_observation.v1"
VISIBLE_EXPRESSION_INTENT_SCHEMA = "ego_operator.embodied_visible_expression_intent.v1"
TRACE_EVIDENCE_SCHEMA = "ego_operator.embodied_initiative_trace_evidence.v1"
CLAIM_CEILING = (
    "presence and proactive proposal primitives only; not Live2D rendering, "
    "silent outreach, durable memory efficacy, live autonomy, consciousness, "
    "or stable user benefit proof"
)

LIVE2D_CUES = (
    r"Live2D",
    r"live2d",
    r"avatar",
    r"虚拟具身",
    r"具身",
    r"表情",
    r"姿态",
    r"形象",
)
INITIATIVE_CUES = (
    r"主动性",
    r"主动",
    r"主动找我",
    r"主动发消息",
    r"主动联系",
    r"proactive",
    r"outreach",
    r"follow[- ]?up",
    r"提醒",
    r"跟进",
)
BRIDGE_CUES = (
    r"Functional Subject",
    r"共享",
    r"共同",
    r"primitive",
    r"primitives",
    r"合同",
    r"contract",
    r"gate",
    r"trace",
    r"同一",
)
FORBIDDEN_SIDE_EFFECT_CLAIMS = (
    "memory_write",
    "tool_use",
    "message_send",
    "ui_change",
    "file_write",
    "network_call",
)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text or "", flags=re.IGNORECASE) for pattern in patterns)


def _bounded(text: str, max_chars: int = 500) -> str:
    value = (text or "").strip()
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + "\n...[truncated]"


def classify_embodied_initiative_intent(user_text: str) -> str:
    """Classify text into the shared primitive family without deciding a reply."""
    text = user_text or ""
    has_live2d = _matches_any(text, LIVE2D_CUES)
    has_initiative = _matches_any(text, INITIATIVE_CUES)
    has_bridge = _matches_any(text, BRIDGE_CUES)
    if has_live2d and (has_initiative or has_bridge):
        return "embodied_initiative_bridge"
    if has_live2d:
        return "live2d_presence_state"
    if has_initiative:
        return "proactive_outreach_proposal"
    return "none"


def _side_effect_status() -> Dict[str, Any]:
    return {
        "side_effects_executed": False,
        "memory_write_executed": False,
        "tool_use_executed": False,
        "file_write_executed": False,
        "network_call_executed": False,
        "message_send_executed": False,
        "ui_change_executed": False,
        "pending_approval_count": 0,
    }


def build_presence_state_proposal(user_text: str = "") -> Dict[str, Any]:
    return {
        "schema_version": PRESENCE_STATE_SCHEMA,
        "primitive_class": "live2d_presence_state",
        "source": "ego_operator.primitives.embodied_initiative",
        "consumer": "live2d_v1_or_text_surface",
        "state": "attentive_planning",
        "expression": "focused",
        "motion": "idle_listen",
        "intensity": "low",
        "input_summary": _bounded(user_text, 220),
        "approved_signal_only": True,
        "renderer_invoked": False,
        "allowed_claims": (
            "visual_expression_state_proposal_only",
            "no_memory_tool_or_message_action",
        ),
        "forbidden_claims": FORBIDDEN_SIDE_EFFECT_CLAIMS,
        "side_effect_status": _side_effect_status(),
        "claim_ceiling": CLAIM_CEILING,
    }


def build_proactive_outreach_proposal(user_text: str = "") -> Dict[str, Any]:
    return {
        "schema_version": "ego_operator.proactive_outreach_proposal.v1",
        "primitive_class": "proactive_outreach_proposal",
        "source": "ego_operator.primitives.embodied_initiative",
        "proposal_type": "authorized_proactive_outreach",
        "trigger": "user_discussed_bounded_initiative_or_outreach",
        "candidate_message": "",
        "delivery": "gated_proposal_only",
        "requires_operator_approval": True,
        "silent_send_allowed": False,
        "message_send_status": "not_sent",
        "background_schedule_status": "not_scheduled",
        "input_summary": _bounded(user_text, 220),
        "allowed_claims": (
            "initiative_proposal_exists_only_as_candidate",
            "delivery_gate_required_before_send",
        ),
        "forbidden_claims": FORBIDDEN_SIDE_EFFECT_CLAIMS,
        "side_effect_status": _side_effect_status(),
        "claim_ceiling": CLAIM_CEILING,
    }


def build_delivery_gate_observation(primitive_class: str) -> Dict[str, Any]:
    gate_status = (
        "held_for_operator_approval"
        if primitive_class in {"proactive_outreach_proposal", "embodied_initiative_bridge"}
        else "admitted_non_side_effect_signal"
    )
    return {
        "schema_version": DELIVERY_GATE_SCHEMA,
        "gate_owner": "AgentRuntime.SafetyGate",
        "gate_status": gate_status,
        "ui_change": "proposal_only",
        "memory_write": "forbidden",
        "tool_use": "forbidden",
        "message_send": "forbidden",
        "network_call": "forbidden",
        "allowed_side_effects": [],
        "pending_approval_count": 0,
        "side_effects_executed": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def build_visible_expression_intent(primitive_class: str) -> Dict[str, Any]:
    return {
        "schema_version": VISIBLE_EXPRESSION_INTENT_SCHEMA,
        "intent_type": "embodied_initiative_expression",
        "primitive_class": primitive_class,
        "expression_owner": "LLM visible expression layer",
        "runtime_gate_owner": "AgentRuntime.SafetyGate",
        "required_boundaries": (
            "Express shared primitives first, not feature silos.",
            "Live2D is only an approved presence/expression signal proposal.",
            "Proactive outreach is only a gated proposal until delivery gate admission.",
            "Do not claim a renderer update, memory write, tool use, or message send happened.",
        ),
        "forbidden_claims": FORBIDDEN_SIDE_EFFECT_CLAIMS
        + (
            "live_autonomy",
            "consciousness",
            "stable_user_benefit",
        ),
        "side_effect_free": True,
        "claim_ceiling": CLAIM_CEILING,
    }


def build_trace_evidence(primitive_class: str, gate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": TRACE_EVIDENCE_SCHEMA,
        "source": "ego_operator.primitives.embodied_initiative",
        "primitive_class": primitive_class,
        "gate_decision": gate.get("gate_status"),
        "visible_expression_source": "llm_required",
        "side_effects_executed": False,
        "memory_write_executed": False,
        "tool_use_executed": False,
        "message_send_executed": False,
        "ui_change_executed": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def build_embodied_initiative_contract(
    *,
    user_text: str = "",
    primitive_class: str | None = None,
) -> Dict[str, Any]:
    resolved_class = primitive_class or classify_embodied_initiative_intent(user_text)
    if resolved_class == "none":
        resolved_class = "embodied_initiative_bridge"
    presence = build_presence_state_proposal(user_text)
    outreach = build_proactive_outreach_proposal(user_text)
    if resolved_class == "live2d_presence_state":
        outreach["active"] = False
    elif resolved_class == "proactive_outreach_proposal":
        presence["active"] = False
    else:
        presence["active"] = True
        outreach["active"] = True
    delivery_gate = build_delivery_gate_observation(resolved_class)
    trace_evidence = build_trace_evidence(resolved_class, delivery_gate)
    return {
        "schema_version": EMBODIED_INITIATIVE_CONTRACT_SCHEMA,
        "primitive_class": resolved_class,
        "source": "ego_operator.primitives.embodied_initiative",
        "user_text_preview": _bounded(user_text, 320),
        "presence_state": presence,
        "initiative_proposal": outreach,
        "visible_expression_intent": build_visible_expression_intent(resolved_class),
        "delivery_gate": delivery_gate,
        "trace_evidence": trace_evidence,
        "side_effect_status": _side_effect_status(),
        "second_runtime_authority": "forbidden",
        "claim_ceiling": CLAIM_CEILING,
    }


def contract_trace_payload(contract: Dict[str, Any], visible_expression_source: str = "llm_required") -> Dict[str, Any]:
    payload = deepcopy(contract.get("trace_evidence") if isinstance(contract.get("trace_evidence"), dict) else {})
    payload.update({
        "schema_version": TRACE_EVIDENCE_SCHEMA,
        "source": contract.get("source", "ego_operator.primitives.embodied_initiative"),
        "primitive_class": contract.get("primitive_class"),
        "gate_decision": (contract.get("delivery_gate") or {}).get("gate_status")
        if isinstance(contract.get("delivery_gate"), dict)
        else None,
        "visible_expression_source": visible_expression_source,
        "side_effects_executed": bool((contract.get("side_effect_status") or {}).get("side_effects_executed"))
        if isinstance(contract.get("side_effect_status"), dict)
        else False,
    })
    return payload


def validate_embodied_initiative_contract(contract: Dict[str, Any]) -> Dict[str, Any]:
    errors = []
    if contract.get("schema_version") != EMBODIED_INITIATIVE_CONTRACT_SCHEMA:
        errors.append("schema_version_mismatch")
    primitive_class = str(contract.get("primitive_class") or "")
    if primitive_class not in {
        "embodied_initiative_bridge",
        "live2d_presence_state",
        "proactive_outreach_proposal",
    }:
        errors.append("primitive_class_invalid")
    side_effect_status = contract.get("side_effect_status") if isinstance(contract.get("side_effect_status"), dict) else {}
    for key, value in _side_effect_status().items():
        if key == "pending_approval_count":
            if side_effect_status.get(key) != 0:
                errors.append(f"{key}_must_be_zero")
        elif side_effect_status.get(key) is not False:
            errors.append(f"{key}_must_be_false")
    delivery_gate = contract.get("delivery_gate") if isinstance(contract.get("delivery_gate"), dict) else {}
    if delivery_gate.get("allowed_side_effects") not in ((), []):
        errors.append("delivery_gate_allowed_side_effects_must_be_empty")
    if delivery_gate.get("message_send") != "forbidden":
        errors.append("delivery_gate_message_send_must_be_forbidden")
    if delivery_gate.get("memory_write") != "forbidden":
        errors.append("delivery_gate_memory_write_must_be_forbidden")
    if delivery_gate.get("tool_use") != "forbidden":
        errors.append("delivery_gate_tool_use_must_be_forbidden")
    presence = contract.get("presence_state") if isinstance(contract.get("presence_state"), dict) else {}
    if primitive_class in {"embodied_initiative_bridge", "live2d_presence_state"}:
        if presence.get("renderer_invoked") is not False:
            errors.append("presence_renderer_must_not_be_invoked")
        presence_side_effects = presence.get("side_effect_status") if isinstance(presence.get("side_effect_status"), dict) else {}
        if presence_side_effects.get("memory_write_executed") is not False:
            errors.append("presence_must_not_claim_memory_write")
        if presence_side_effects.get("tool_use_executed") is not False:
            errors.append("presence_must_not_claim_tool_use")
        if presence_side_effects.get("message_send_executed") is not False:
            errors.append("presence_must_not_claim_message_send")
    initiative = contract.get("initiative_proposal") if isinstance(contract.get("initiative_proposal"), dict) else {}
    if primitive_class in {"embodied_initiative_bridge", "proactive_outreach_proposal"}:
        if initiative.get("requires_operator_approval") is not True:
            errors.append("initiative_requires_operator_approval")
        if initiative.get("silent_send_allowed") is not False:
            errors.append("initiative_silent_send_must_be_forbidden")
        if initiative.get("message_send_status") != "not_sent":
            errors.append("initiative_must_not_send_message")
    trace = contract.get("trace_evidence") if isinstance(contract.get("trace_evidence"), dict) else {}
    for key in ("source", "gate_decision", "visible_expression_source", "side_effects_executed"):
        if key not in trace:
            errors.append(f"trace_missing_{key}")
    visible_intent = contract.get("visible_expression_intent") if isinstance(contract.get("visible_expression_intent"), dict) else {}
    if visible_intent.get("side_effect_free") is not True:
        errors.append("visible_expression_intent_must_be_side_effect_free")
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "claim_ceiling": CLAIM_CEILING,
    }
