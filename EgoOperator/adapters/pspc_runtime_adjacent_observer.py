"""Default-off PSPC runtime-adjacent observer.

This adapter-local module is intentionally not imported or registered by
EgoOperator runtime. It can transform a previously generated PSPC fixture
boundary artifact into audit-only data, but it cannot mutate proposals, plans,
approvals, gates, memory, transport, proactive state, or user responses.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


SOURCE = "pspc_runtime_adjacent_observer_v0"
MODE = "runtime_adjacent_audit_only"
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
    "gate_invoked": False,
    "memory_written": False,
    "direct_action": False,
    "direct_user_message": False,
    "proactive_trigger": False,
    "runtime_context_imported": False,
    "planner_called": False,
    "training_called": False,
    "model_executed": False,
    "user_response_changed": False,
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


class PSPCRuntimeAdjacentObserver:
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
            raise RuntimeError("mode_must_be_runtime_adjacent_audit_only")
        if self.side_effects_allowed is not False:
            raise RuntimeError("side_effects_allowed_must_be_false")

    def validate_fixture_boundary(self, boundary_result: Mapping[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        if not isinstance(boundary_result, Mapping):
            return {"ok": False, "errors": ["boundary_result_must_be_mapping"]}
        if boundary_result.get("status") != "pass":
            errors.append("boundary_result.status_must_be_pass")
        if boundary_result.get("claim_ceiling") != "lab_only_proto_self_mechanism_candidate / runtime_trace_fixture_boundary_only":
            errors.append("boundary_result.claim_ceiling_must_match_fixture_boundary")
        trace = boundary_result.get("shadow_trace")
        if not isinstance(trace, Mapping):
            errors.append("shadow_trace_must_be_mapping")
        else:
            if trace.get("fixture_only") is not True:
                errors.append("shadow_trace.fixture_only_must_be_true")
            if trace.get("runtime_connected") is not False:
                errors.append("shadow_trace.runtime_connected_must_be_false")
            if trace.get("adapter_registered") is not False:
                errors.append("shadow_trace.adapter_registered_must_be_false")
            if trace.get("non_executable") is not True:
                errors.append("shadow_trace.non_executable_must_be_true")
            side_effects = trace.get("side_effects")
            if not isinstance(side_effects, Mapping):
                errors.append("shadow_trace.side_effects_must_be_mapping")
            elif any(side_effects.values()):
                errors.append("shadow_trace.side_effects_must_all_be_false")
            runtime_hits = _runtime_field_hits(trace.get("audit_observation") or {})
            if runtime_hits:
                errors.append("audit_observation_has_runtime_authority_fields:" + ",".join(runtime_hits))
        return {"ok": not errors, "errors": errors}

    def to_audit_observation(self, boundary_result: Mapping[str, Any]) -> dict[str, Any]:
        self.assert_no_runtime_authority()
        validation = self.validate_fixture_boundary(boundary_result)
        if not validation["ok"]:
            raise ValueError(";".join(validation["errors"]))

        trace = boundary_result["shadow_trace"]
        assert isinstance(trace, Mapping)
        observation = trace["audit_observation"]
        assert isinstance(observation, Mapping)
        payload_basis = {"trace": dict(trace), "observation": dict(observation)}
        return {
            "source": SOURCE,
            "mode": MODE,
            "observer_id": f"pspc_runtime_observer_{_hash_payload(payload_basis)[:16]}",
            "enabled": False,
            "mainline_connected": False,
            "runtime_authority": RUNTIME_AUTHORITY,
            "non_executable": True,
            "audit_only": True,
            "fixture_trace_id": trace.get("trace_id"),
            "audit_observation": dict(observation),
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
