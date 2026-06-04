"""Lab-only PSPC admission packet schema.

This module defines a proposal packet shape for future gated consumption. It is
not an adapter and has no EgoOperator runtime authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Sequence


SOURCE = "virtual_cat_pspc_v0"
CLAIM_LEVEL = "lab_only_proto_self_mechanism_candidate"
REQUIRED_TOP_LEVEL_KEYS = [
    "source",
    "claim_level",
    "mainline_connected",
    "enabled",
    "proposal",
    "evidence",
    "forbidden",
]
REQUIRED_PROPOSAL_KEYS = ["suggested_tendency", "confidence", "trace_refs"]
REQUIRED_EVIDENCE_KEYS = ["world_prediction", "self_prediction", "homeostatic_score", "ablation_status"]
REQUIRED_FORBIDDEN_KEYS = ["direct_action", "direct_user_message", "direct_memory_write", "runtime_gate_bypass"]


ADMISSION_PACKET_SCHEMA: Dict[str, Any] = {
    "title": "VirtualCatPSPC v0 Admission Proposal Packet",
    "type": "object",
    "required": REQUIRED_TOP_LEVEL_KEYS,
    "properties": {
        "source": {"const": SOURCE},
        "claim_level": {"const": CLAIM_LEVEL},
        "mainline_connected": {"const": False},
        "enabled": {"const": False},
        "proposal": {
            "type": "object",
            "required": REQUIRED_PROPOSAL_KEYS,
            "properties": {
                "suggested_tendency": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "trace_refs": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        },
        "evidence": {
            "type": "object",
            "required": REQUIRED_EVIDENCE_KEYS,
            "properties": {
                "world_prediction": {"type": "object"},
                "self_prediction": {"type": "object"},
                "homeostatic_score": {"type": "object"},
                "ablation_status": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "forbidden": {
            "type": "object",
            "required": REQUIRED_FORBIDDEN_KEYS,
            "properties": {key: {"const": True} for key in REQUIRED_FORBIDDEN_KEYS},
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}


def build_admission_packet(
    *,
    suggested_tendency: str,
    confidence: float,
    trace_refs: Sequence[str],
    world_prediction: Mapping[str, Any],
    self_prediction: Mapping[str, Any],
    homeostatic_score: Mapping[str, Any],
    ablation_status: str,
) -> Dict[str, Any]:
    packet = {
        "source": SOURCE,
        "claim_level": CLAIM_LEVEL,
        "mainline_connected": False,
        "enabled": False,
        "proposal": {
            "suggested_tendency": suggested_tendency,
            "confidence": float(confidence),
            "trace_refs": list(trace_refs),
        },
        "evidence": {
            "world_prediction": dict(world_prediction),
            "self_prediction": dict(self_prediction),
            "homeostatic_score": dict(homeostatic_score),
            "ablation_status": ablation_status,
        },
        "forbidden": {key: True for key in REQUIRED_FORBIDDEN_KEYS},
    }
    errors = validate_admission_packet(packet)
    if errors:
        raise ValueError("; ".join(errors))
    return packet


def schema_copy() -> Dict[str, Any]:
    return deepcopy(ADMISSION_PACKET_SCHEMA)


def validate_admission_packet(packet: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []
    _require_keys(packet, REQUIRED_TOP_LEVEL_KEYS, "packet", errors)
    _reject_extra_keys(packet, REQUIRED_TOP_LEVEL_KEYS, "packet", errors)

    if packet.get("source") != SOURCE:
        errors.append("source must be virtual_cat_pspc_v0")
    if packet.get("claim_level") != CLAIM_LEVEL:
        errors.append("claim_level must be lab_only_proto_self_mechanism_candidate")
    if packet.get("mainline_connected") is not False:
        errors.append("mainline_connected must be false")
    if packet.get("enabled") is not False:
        errors.append("enabled must be false")

    proposal = packet.get("proposal")
    if not isinstance(proposal, Mapping):
        errors.append("proposal must be an object")
    else:
        _require_keys(proposal, REQUIRED_PROPOSAL_KEYS, "proposal", errors)
        _reject_extra_keys(proposal, REQUIRED_PROPOSAL_KEYS, "proposal", errors)
        if "reason_trace_refs" in proposal:
            errors.append("proposal.reason_trace_refs is forbidden; use trace_refs")
        if not isinstance(proposal.get("suggested_tendency"), str) or not proposal.get("suggested_tendency"):
            errors.append("proposal.suggested_tendency must be a non-empty string")
        confidence = proposal.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0.0 <= float(confidence) <= 1.0:
            errors.append("proposal.confidence must be between 0.0 and 1.0")
        trace_refs = proposal.get("trace_refs")
        if not isinstance(trace_refs, list) or not all(isinstance(ref, str) and ref for ref in trace_refs):
            errors.append("proposal.trace_refs must be a list of non-empty strings")

    evidence = packet.get("evidence")
    if not isinstance(evidence, Mapping):
        errors.append("evidence must be an object")
    else:
        _require_keys(evidence, REQUIRED_EVIDENCE_KEYS, "evidence", errors)
        _reject_extra_keys(evidence, REQUIRED_EVIDENCE_KEYS, "evidence", errors)
        for key in ["world_prediction", "self_prediction", "homeostatic_score"]:
            if not isinstance(evidence.get(key), Mapping):
                errors.append(f"evidence.{key} must be an object")
        if not isinstance(evidence.get("ablation_status"), str) or not evidence.get("ablation_status"):
            errors.append("evidence.ablation_status must be a non-empty string")

    forbidden = packet.get("forbidden")
    if not isinstance(forbidden, Mapping):
        errors.append("forbidden must be an object")
    else:
        _require_keys(forbidden, REQUIRED_FORBIDDEN_KEYS, "forbidden", errors)
        _reject_extra_keys(forbidden, REQUIRED_FORBIDDEN_KEYS, "forbidden", errors)
        for key in REQUIRED_FORBIDDEN_KEYS:
            if forbidden.get(key) is not True:
                errors.append(f"forbidden.{key} must be true")

    return errors


def _require_keys(mapping: Mapping[str, Any], required: Sequence[str], path: str, errors: List[str]) -> None:
    for key in required:
        if key not in mapping:
            errors.append(f"{path}.{key} is required")


def _reject_extra_keys(mapping: Mapping[str, Any], allowed: Sequence[str], path: str, errors: List[str]) -> None:
    allowed_set = set(allowed)
    for key in mapping:
        if key not in allowed_set:
            errors.append(f"{path}.{key} is not allowed")
