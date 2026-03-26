from __future__ import annotations

from app.runtime_v2.telegram_bridge import (
    RuntimeV2TelegramBridge,
    TelegramDeliveryAction,
    TelegramIngressDecision,
    TelegramPreRuntimeAction,
)


class TelegramRuntimeBridge(RuntimeV2TelegramBridge):
    """Telegram host-side ingress/delivery planner.

    This is the canonical import point for Telegram mainline code.
    The implementation currently reuses the proven runtime_v2 bridge logic
    while we continue shrinking legacy ownership behind Telegram-specific
    boundaries.
    """


__all__ = [
    "TelegramRuntimeBridge",
    "TelegramDeliveryAction",
    "TelegramIngressDecision",
    "TelegramPreRuntimeAction",
]
