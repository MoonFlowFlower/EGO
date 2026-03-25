from __future__ import annotations

import asyncio

from .loop import RuntimeV2Loop
from .runtime_reply import RuntimeV2TurnResult


async def interactive_cli() -> int:
    loop = RuntimeV2Loop()
    session_id = "cli:runtime_v2"
    print("Runtime v2 CLI ready. Type 'exit' to quit.")
    while True:
        try:
            user_input = input("\n【你】")
        except EOFError:
            break
        if user_input.strip().lower() in {"exit", "quit"}:
            break
        result: RuntimeV2TurnResult = await loop.run_turn_typed(session_id=session_id, user_input=user_input)
        print(f"【AI】{result.reply_text}")
    return 0


def run_cli() -> int:
    return asyncio.run(interactive_cli())
