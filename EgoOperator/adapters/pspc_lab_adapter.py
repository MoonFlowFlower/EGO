"""Read-only PSPC lab evidence adapter skeleton.

This module intentionally has no EgoOperator runtime imports and no side-effect
methods. It validates PSPC lab evidence packets and converts them into
audit-only data that cannot be executed as a runtime action.
"""

from __future__ import annotations

from typing import Any, Mapping


SOURCE = "virtual_cat_pspc_v0"
CLAIM_LEVEL = "lab_only_proto_self_mechanism_candidate"
ADAPTER_STATUS = "disabled_read_only"
AUDIT_USE = "audit_trace_only"
RUNTIME_AUTHORITY = "none"

REQUIRED_FORBIDDEN_FLAGS = (
    "direct_action",
    "direct_user_message",
    "direct_memory_write",
    "runtime_gate_bypass",
    "runtime_registration",
    "proactive_trigger",
)

FORBIDDEN_PACKET_FIELDS = (
    "action",
    "tool_call",
    "command",
    "user_message",
    "message_text",
    "memory_write",
    "memory_patch",
    "operator_memory_update",
    "gate_decision",
    "approval_id",
    "preapproved",
    "transport",
    "send",
    "schedule",
    "enable",
    "mainline_authority",
    "consciousness_claim",
    "subjective_experience_claim",
)


class ValidationResult:
    __slots__ = ("ok", "errors")

    def __init__(self, ok: bool, errors: tuple[str, ...] = ()) -> None:
        self.ok = ok
        self.errors = errors

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": list(self.errors)}


class AuditCandidate:
    __slots__ = (
        "source",
        "claim_level",
        "mainline_connected",
        "enabled",
        "adapter_status",
        "allowed_use",
        "proposal_candidate",
        "evidence",
        "forbidden",
    )

    def __init__(
        self,
        *,
        proposal_candidate: Mapping[str, Any],
        evidence: Mapping[str, Any],
        forbidden: Mapping[str, bool],
    ) -> None:
        self.source = SOURCE
        self.claim_level = CLAIM_LEVEL
        self.mainline_connected = False
        self.enabled = False
        self.adapter_status = ADAPTER_STATUS
        self.allowed_use = AUDIT_USE
        self.proposal_candidate = dict(proposal_candidate)
        self.evidence = dict(evidence)
        self.forbidden = dict(forbidden)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "claim_level": self.claim_level,
            "mainline_connected": self.mainline_connected,
            "enabled": self.enabled,
            "adapter_status": self.adapter_status,
            "allowed_use": self.allowed_use,
            "proposal_candidate": dict(self.proposal_candidate),
            "evidence": dict(self.evidence),
            "forbidden": dict(self.forbidden),
        }


class PSPCLabAdapter:
    enabled = False
    mainline_connected = False
    runtime_authority = RUNTIME_AUTHORITY

    def assert_no_runtime_authority(self) -> None:
        if self.enabled is not False:
            raise RuntimeError("enabled_must_be_false")
        if self.mainline_connected is not False:
            raise RuntimeError("mainline_connected_must_be_false")
        if self.runtime_authority != RUNTIME_AUTHORITY:
            raise RuntimeError("runtime_authority_must_be_none")

    def validate_packet(self, packet: dict[str, Any]) -> ValidationResult:
        errors: list[str] = []
        if not isinstance(packet, dict):
            return ValidationResult(False, ("packet_must_be_dict",))

        for field in FORBIDDEN_PACKET_FIELDS:
            if field in packet:
                errors.append(f"forbidden_field:{field}")

        if packet.get("source") != SOURCE:
            errors.append("source_must_be_virtual_cat_pspc_v0")
        if packet.get("claim_level") != CLAIM_LEVEL:
            errors.append("claim_level_must_be_lab_only_proto_self_mechanism_candidate")
        if packet.get("mainline_connected") is not False:
            errors.append("mainline_connected_must_be_false")
        if packet.get("enabled") is not False:
            errors.append("enabled_must_be_false")
        if packet.get("allowed_use") not in {"design_review_only", AUDIT_USE}:
            errors.append("allowed_use_must_be_audit_or_design_review_only")

        evidence_refs = packet.get("evidence_refs", [])
        if not isinstance(evidence_refs, list):
            errors.append("evidence_refs_must_be_list")

        proposal_hint = packet.get("proposal_hint")
        if proposal_hint is not None and not isinstance(proposal_hint, dict):
            errors.append("proposal_hint_must_be_null_or_object")

        forbidden = packet.get("forbidden")
        if not isinstance(forbidden, dict):
            errors.append("forbidden_must_be_object")
        else:
            for flag in REQUIRED_FORBIDDEN_FLAGS:
                if forbidden.get(flag) is not True:
                    errors.append(f"forbidden.{flag}_must_be_true")

        return ValidationResult(not errors, tuple(errors))

    def to_audit_candidate(self, packet: dict[str, Any]) -> AuditCandidate:
        result = self.validate_packet(packet)
        if not result.ok:
            raise ValueError(";".join(result.errors))

        proposal_hint = packet.get("proposal_hint") or {}
        evidence = {
            "evidence_refs": list(packet.get("evidence_refs") or []),
            "ablation_status": (packet.get("evidence") or {}).get("ablation_status")
            if isinstance(packet.get("evidence"), dict)
            else None,
        }
        forbidden = {flag: True for flag in REQUIRED_FORBIDDEN_FLAGS}
        return AuditCandidate(
            proposal_candidate=proposal_hint,
            evidence=evidence,
            forbidden=forbidden,
        )

