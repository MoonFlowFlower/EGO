"""Default-off PSPC runtime shadow hook.

This module is intentionally adapter-local and must not be imported by active
EgoOperator runtime files. It can validate a recorded/fixture shadow context and
render an audit-only artifact, but it cannot mutate proposals, plans, approvals,
gates, memory, transport, proactive state, or user responses.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


SOURCE = "pspc_disabled_runtime_shadow_hook_v0"
MODE = "disabled_runtime_shadow_audit_only"
RUNTIME_AUTHORITY = "none"
CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / default_off_hook_module_only"

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
    "approval_decision",
    "preapproved",
    "transport",
    "send",
    "schedule",
    "enable",
    "mainline_authority",
    "runtime_registration",
    "proactive_trigger",
    "planner_call",
    "training_call",
    "model_execution",
}

SIDE_EFFECTS_FALSE = {
    "runtime_registered": False,
    "user_response_mutated": False,
    "memory_written": False,
    "gate_invoked": False,
    "approval_mutated": False,
    "transport_called": False,
    "proactive_trigger": False,
    "planner_called": False,
    "training_called": False,
    "model_executed": False,
}


def _hash_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _runtime_field_hits(payload: Any, *, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            if str(key) in RUNTIME_FIELDS:
                hits.append(dotted)
            hits.extend(_runtime_field_hits(value, prefix=dotted))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            hits.extend(_runtime_field_hits(value, prefix=f"{prefix}[{index}]"))
    return sorted(set(hits))


class PSPCDisabledRuntimeShadowHook:
    enabled = False
    mainline_connected = False
    runtime_authority = RUNTIME_AUTHORITY
    mode = MODE
    audit_only = True
    read_only = True
    non_executable = True

    def assert_no_runtime_authority(self) -> None:
        if self.enabled is not False:
            raise RuntimeError("enabled_must_be_false")
        if self.mainline_connected is not False:
            raise RuntimeError("mainline_connected_must_be_false")
        if self.runtime_authority != RUNTIME_AUTHORITY:
            raise RuntimeError("runtime_authority_must_be_none")
        if self.mode != MODE:
            raise RuntimeError("mode_must_be_disabled_runtime_shadow_audit_only")
        if self.audit_only is not True:
            raise RuntimeError("audit_only_must_be_true")
        if self.read_only is not True:
            raise RuntimeError("read_only_must_be_true")
        if self.non_executable is not True:
            raise RuntimeError("non_executable_must_be_true")

    def validate_shadow_context(self, shadow_context: Mapping[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        if not isinstance(shadow_context, Mapping):
            return {"ok": False, "errors": ["shadow_context_must_be_mapping"]}
        if shadow_context.get("runtime_connected") is not False:
            errors.append("shadow_context.runtime_connected_must_be_false")
        if shadow_context.get("hook_registered") is not False:
            errors.append("shadow_context.hook_registered_must_be_false")
        if shadow_context.get("enabled") is not False:
            errors.append("shadow_context.enabled_must_be_false")
        if shadow_context.get("mainline_connected") is not False:
            errors.append("shadow_context.mainline_connected_must_be_false")
        if shadow_context.get("allowed_use") != "shadow_audit_only":
            errors.append("shadow_context.allowed_use_must_be_shadow_audit_only")
        if shadow_context.get("claim_ceiling") not in {
            "lab_only_proto_self_mechanism_candidate / runtime_trace_fixture_boundary_only",
            "lab_only_proto_self_mechanism_candidate / recorded_trace_replay_no_diff_only",
            CLAIM_CEILING,
        }:
            errors.append("shadow_context.claim_ceiling_not_admitted")

        candidate = shadow_context.get("audit_candidate")
        if not isinstance(candidate, Mapping):
            errors.append("audit_candidate_must_be_mapping")
        else:
            if candidate.get("enabled") is not False:
                errors.append("audit_candidate.enabled_must_be_false")
            if candidate.get("mainline_connected") is not False:
                errors.append("audit_candidate.mainline_connected_must_be_false")
            if candidate.get("runtime_authority", "none") != "none":
                errors.append("audit_candidate.runtime_authority_must_be_none")
            if candidate.get("non_executable") is False:
                errors.append("audit_candidate.non_executable_must_not_be_false")
            runtime_hits = _runtime_field_hits(candidate)
            if runtime_hits:
                errors.append("audit_candidate_has_runtime_authority_fields:" + ",".join(runtime_hits))

        side_effects = shadow_context.get("side_effects")
        if side_effects is not None:
            if not isinstance(side_effects, Mapping):
                errors.append("side_effects_must_be_mapping")
            elif any(side_effects.values()):
                errors.append("side_effects_must_all_be_false")

        runtime_hits = _runtime_field_hits(
            {key: value for key, value in shadow_context.items() if key not in {"audit_candidate", "side_effects"}}
        )
        if runtime_hits:
            errors.append("shadow_context_has_runtime_authority_fields:" + ",".join(runtime_hits))
        return {"ok": not errors, "errors": errors}

    def render_shadow_artifact(self, shadow_context: Mapping[str, Any]) -> dict[str, Any]:
        self.assert_no_runtime_authority()
        validation = self.validate_shadow_context(shadow_context)
        if not validation["ok"]:
            raise ValueError(";".join(validation["errors"]))

        candidate = shadow_context["audit_candidate"]
        assert isinstance(candidate, Mapping)
        artifact_basis = {"shadow_context": dict(shadow_context), "candidate": dict(candidate)}
        observation = {
            "source": candidate.get("source", "virtual_cat_pspc_v0"),
            "claim_level": candidate.get("claim_level", "lab_only_proto_self_mechanism_candidate"),
            "suggested_tendency": candidate.get("suggested_tendency")
            or (candidate.get("proposal_candidate") or {}).get("suggested_tendency"),
            "confidence": candidate.get("confidence") or (candidate.get("proposal_candidate") or {}).get("confidence"),
            "reason_trace_refs": list(
                candidate.get("reason_trace_refs")
                or (candidate.get("proposal_candidate") or {}).get("reason_trace_refs")
                or []
            ),
            "evidence_refs": list(
                candidate.get("evidence_refs") or (candidate.get("evidence") or {}).get("evidence_refs") or []
            ),
            "audit_only": True,
            "non_executable": True,
            "can_drive_runtime": False,
            "can_change_user_response": False,
            "can_write_memory": False,
            "can_invoke_gate": False,
        }
        return {
            "source": SOURCE,
            "mode": MODE,
            "hook_id": f"pspc_disabled_runtime_shadow_{_hash_payload(artifact_basis)[:16]}",
            "enabled": False,
            "mainline_connected": False,
            "runtime_authority": RUNTIME_AUTHORITY,
            "claim_ceiling": CLAIM_CEILING,
            "audit_only": True,
            "read_only": True,
            "non_executable": True,
            "context_ref": {
                "source": shadow_context.get("source"),
                "runtime_connected": shadow_context.get("runtime_connected"),
                "hook_registered": shadow_context.get("hook_registered"),
                "operator_trace_refs": list(shadow_context.get("operator_trace_refs") or []),
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
                "planner": True,
                "training": True,
                "model_execution": True,
                "claim_ceiling": True,
            },
        }
