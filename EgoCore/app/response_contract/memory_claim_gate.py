from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.restore_runtime import PendingRestoreObservation


RESTORE_CLAIM_MARKERS = (
    "已恢复",
    "恢复成功",
    "恢复了",
    "我记得",
    "还记得",
    "记得你",
    "remember",
    "restored",
    "restore succeeded",
)


@dataclass(frozen=True)
class MemoryClaimVerdict:
    allowed: bool
    reason: str
    authority_source: str
    claim_detected: bool


def evaluate_memory_claim(
    text: str,
    *,
    restore_observation: Optional[PendingRestoreObservation] = None,
) -> MemoryClaimVerdict:
    normalized = (text or "").strip().lower()
    claim_detected = any(marker.lower() in normalized for marker in RESTORE_CLAIM_MARKERS)
    if not claim_detected:
        return MemoryClaimVerdict(
            allowed=True,
            reason="no_memory_claim_detected",
            authority_source="memory_claim_gate",
            claim_detected=False,
        )

    if restore_observation is None:
        return MemoryClaimVerdict(
            allowed=False,
            reason="missing_restore_authority",
            authority_source="memory_claim_gate",
            claim_detected=True,
        )

    if restore_observation.restore_status in {"success", "partial"}:
        return MemoryClaimVerdict(
            allowed=True,
            reason=f"restore_{restore_observation.restore_status}",
            authority_source=restore_observation.authority_source,
            claim_detected=True,
        )

    return MemoryClaimVerdict(
        allowed=False,
        reason=f"restore_{restore_observation.restore_status}",
        authority_source=restore_observation.authority_source,
        claim_detected=True,
    )
