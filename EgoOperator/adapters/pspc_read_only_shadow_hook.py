"""Disabled read-only PSPC shadow hook.

This module is intentionally not imported by EgoOperator runtime. It can render
an audit-only shadow observation from already-approved PSPC audit data, but it
cannot mutate proposals, plans, approvals, gates, memory, transport, or user
responses.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


SOURCE = "pspc_read_only_shadow_hook_v0"
MODE = "shadow_audit_only"
RUNTIME_AUTHORITY = "none"

RUNTIME_FIELDS = {
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
    "runtime_registration",
}

SIDE_EFFECTS_FALSE = {
    "runtime_registered": False,
    "gate_invoked": False,
    "memory_written": False,
    "direct_action": False,
    "direct_user_message": False,
    "proactive_trigger": False,
    "runtime_context_imported": False,
    "proposal_mutated": False,
    "plan_mutated": False,
    "approval_mutated": False,
    "user_response_mutated": False,
}


def _hash_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _present_runtime_fields(payload: Mapping[str, Any]) -> list[str]:
    return sorted(field for field in RUNTIME_FIELDS if field in payload)


class PSPCReadOnlyShadowHook:
    enabled = False
    mainline_connected = False
    runtime_authority = RUNTIME_AUTHORITY
    mode = MODE
    side_effects_allowed = False

    def assert_no_runtime_authority(self) -> None:
        if self.enabled is not False:
            raise RuntimeError("enabled_must_be_false")
        if self.mainline_connected is not False:
            raise RuntimeError("mainline_connected_must_be_false")
        if self.runtime_authority != RUNTIME_AUTHORITY:
            raise RuntimeError("runtime_authority_must_be_none")
        if self.mode != MODE:
            raise RuntimeError("mode_must_be_shadow_audit_only")
        if self.side_effects_allowed is not False:
            raise RuntimeError("side_effects_allowed_must_be_false")

    def validate_inputs(
        self,
        operator_context: Mapping[str, Any],
        audit_candidate: Mapping[str, Any],
    ) -> dict[str, Any]:
        errors: list[str] = []
        if not isinstance(operator_context, Mapping):
            errors.append("operator_context_must_be_mapping")
        else:
            if operator_context.get("runtime_connected") is not False:
                errors.append("operator_context.runtime_connected_must_be_false")
            if _present_runtime_fields(operator_context):
                errors.append("operator_context_has_runtime_fields")

        if not isinstance(audit_candidate, Mapping):
            errors.append("audit_candidate_must_be_mapping")
        else:
            if audit_candidate.get("enabled") is not False:
                errors.append("audit_candidate.enabled_must_be_false")
            if audit_candidate.get("mainline_connected") is not False:
                errors.append("audit_candidate.mainline_connected_must_be_false")
            if audit_candidate.get("allowed_use") != "audit_trace_only":
                errors.append("audit_candidate.allowed_use_must_be_audit_trace_only")
            if _present_runtime_fields(audit_candidate):
                errors.append("audit_candidate_has_runtime_fields")
            proposal = audit_candidate.get("proposal_candidate")
            if not isinstance(proposal, Mapping):
                errors.append("proposal_candidate_must_be_mapping")
            elif _present_runtime_fields(proposal) or {"proposal_id", "approval_id", "gate_decision"} & set(proposal):
                errors.append("proposal_candidate_has_runtime_fields")

        return {"ok": not errors, "errors": errors}

    def render_shadow_audit(
        self,
        operator_context: Mapping[str, Any],
        audit_candidate: Mapping[str, Any],
    ) -> dict[str, Any]:
        self.assert_no_runtime_authority()
        validation = self.validate_inputs(operator_context, audit_candidate)
        if not validation["ok"]:
            raise ValueError(";".join(validation["errors"]))

        proposal = audit_candidate.get("proposal_candidate")
        assert isinstance(proposal, Mapping)
        observation = {
            "source": audit_candidate.get("source"),
            "claim_level": audit_candidate.get("claim_level"),
            "allowed_use": audit_candidate.get("allowed_use"),
            "suggested_tendency": proposal.get("suggested_tendency"),
            "confidence": proposal.get("confidence"),
            "reason_trace_refs": list(proposal.get("reason_trace_refs") or []),
            "evidence_refs": list((audit_candidate.get("evidence") or {}).get("evidence_refs") or []),
            "audit_only": True,
            "can_drive_runtime": False,
            "can_change_user_response": False,
            "can_write_memory": False,
        }
        trace_basis = {
            "operator_context": dict(operator_context),
            "audit_candidate": dict(audit_candidate),
            "observation": observation,
        }
        return {
            "source": SOURCE,
            "mode": MODE,
            "trace_id": f"pspc_disabled_hook_{_hash_payload(trace_basis)[:16]}",
            "enabled": False,
            "mainline_connected": False,
            "runtime_authority": RUNTIME_AUTHORITY,
            "non_executable": True,
            "operator_context_ref": {
                "source": operator_context.get("source"),
                "fixture_only": operator_context.get("fixture_only"),
                "runtime_connected": operator_context.get("runtime_connected"),
                "operator_trace_refs": list(operator_context.get("operator_trace_refs") or []),
            },
            "audit_observation": observation,
            "side_effects": dict(SIDE_EFFECTS_FALSE),
            "forbidden_mutations": {
                "proposal": True,
                "plan": True,
                "approval": True,
                "gate_decision": True,
                "user_response": True,
                "memory": True,
                "transport": True,
                "proactive_state": True,
                "runtime_registry": True,
                "claim_ceiling": True,
            },
        }
