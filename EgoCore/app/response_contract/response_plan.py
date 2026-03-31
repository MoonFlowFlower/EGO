from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.restore_runtime import PendingRestoreObservation
from app.runtime_v2.semantic_parser import build_runtime_status_reply

from .memory_claim_gate import MemoryClaimVerdict, evaluate_memory_claim


@dataclass(frozen=True)
class ResponsePlan:
    kind: str
    reply_text: str
    delivery_kind: str
    authority_source: str
    memory_claim_verdict: Optional[MemoryClaimVerdict] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def build_status_response_plan(
    text: str,
    state: Any,
    *,
    assume_active: bool = False,
    restore_observation: Optional[PendingRestoreObservation] = None,
) -> ResponsePlan:
    verdict = evaluate_memory_claim(text, restore_observation=restore_observation)
    reply_text = build_runtime_status_reply(state, assume_active=assume_active)
    return ResponsePlan(
        kind="status_probe",
        reply_text=reply_text,
        delivery_kind="final",
        authority_source="response_contract.response_plan",
        memory_claim_verdict=verdict,
        metadata={
            "assume_active": assume_active,
            "memory_claim_reason": verdict.reason,
            "memory_claim_allowed": verdict.allowed,
        },
    )
