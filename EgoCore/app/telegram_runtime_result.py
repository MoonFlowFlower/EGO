from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TelegramTurnReply:
    reply_text: str
    delivery_kind: str
    status: str
    suppressible: bool = False
    request_id: Optional[str] = None
    generation_id: Optional[int] = None
    turn_id: Optional[str] = None


@dataclass
class TelegramTurnResult:
    status: str
    state: Any
    reply: Optional[TelegramTurnReply] = None

    @property
    def reply_text(self) -> str:
        return self.reply.reply_text if self.reply else ""

    @property
    def delivery_kind(self) -> Optional[str]:
        return self.reply.delivery_kind if self.reply else None
