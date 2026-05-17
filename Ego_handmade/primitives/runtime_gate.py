"""
Runtime-gate primitive contracts for Ego_handmade.

This module captures the reusable gate boundary from the old systems as a
small local contract. It does not execute tools and does not import old runtime
code; AgentRuntime/SafetyGate remain the admission path.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Tuple


CLAIM_CEILING = "Ego_handmade replacement candidate with extracted primitives"


@dataclass(frozen=True)
class RuntimeGateContract:
    tool_side_effects_default: str = "off"
    memory_write_gate: str = "/remember plus remember_note with explicit operator intent"
    network_default: str = "off"
    file_write_default: str = "off"
    command_default: str = "off"
    trace_scope: str = "Ego_handmade/artifacts/"
    claim_ceiling: str = CLAIM_CEILING
    forbidden_claims: Tuple[str, ...] = (
        "EGO mainline replacement",
        "EgoCore or OpenEmotion demotion",
        "formal long-term memory efficacy",
        "live autonomy",
        "runtime efficacy",
        "consciousness",
    )

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)


DEFAULT_RUNTIME_GATE_CONTRACT = RuntimeGateContract()


def describe_runtime_gate_contract() -> Dict[str, object]:
    return DEFAULT_RUNTIME_GATE_CONTRACT.as_dict()
