#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List

from runtime_mainline_observation_common import EGO_ROOT, run_runtime_observation_session


ARTIFACTS_ROOT = EGO_ROOT / "OpenEmotion" / "artifacts" / "mvp12"


def _load_messages(args: argparse.Namespace) -> List[str]:
    messages: List[str] = list(args.message or [])
    if args.messages_file:
        content = Path(args.messages_file).read_text(encoding="utf-8")
        if args.messages_file.endswith(".json"):
            payload = json.loads(content)
            if not isinstance(payload, list):
                raise ValueError("messages-file JSON must be a list of strings")
            messages.extend(str(item) for item in payload if str(item).strip())
        else:
            messages.extend(line.strip() for line in content.splitlines() if line.strip())
    if messages:
        return messages
    return [
        "我在想，意识的门槛其实可能比人类自以为的低很多。你怎么看？",
        "继续说",
        "还记得我吗",
        "如果意识是光谱，那边界是不是更多是伦理上的，而不是事实上的？",
    ]


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run scripted user messages through the formal runtime mainline and emit observation_record_v1."
    )
    parser.add_argument("--message", action="append", default=[], help="Add one scripted user message")
    parser.add_argument("--messages-file", default=None, help="JSON list or newline-delimited text file")
    parser.add_argument(
        "--session-id",
        default=f"session:mvp12:runtime_harness:{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    )
    parser.add_argument(
        "--observation-log",
        default=str(ARTIFACTS_ROOT / "runtime_harness_observation_current.jsonl"),
    )
    args = parser.parse_args()

    result = await run_runtime_observation_session(
        messages=_load_messages(args),
        session_id=args.session_id,
        observation_log=Path(args.observation_log),
    )
    summary_path = Path(args.observation_log).with_suffix(".json")
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
