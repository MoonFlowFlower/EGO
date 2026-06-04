"""Run one EgoOperator desktop chat turn and return JSON for EgoDesktop."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OPENROUTER_KEY_FILE = Path(r"D:\Project\AIProject\MyProject\Test\openrouterKey.txt")


def _read_key_file(path: Path) -> str:
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    for line in raw.splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if text.startswith("OPENROUTER_API_KEY="):
            text = text.split("=", 1)[1].strip()
        return text.strip().strip('"').strip("'")
    return ""


def _load_openrouter_key_before_agent_import() -> None:
    if os.getenv("OPENROUTER_API_KEY"):
        return
    configured = os.getenv("OPENROUTER_API_KEY_FILE", "").strip()
    candidates = [Path(configured)] if configured else []
    candidates.append(DEFAULT_OPENROUTER_KEY_FILE)
    for candidate in candidates:
        key = _read_key_file(candidate)
        if key:
            os.environ["OPENROUTER_API_KEY"] = key
            os.environ.setdefault("OPENROUTER_API_KEY_FILE", str(candidate))
            return


_load_openrouter_key_before_agent_import()

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from EgoOperator.agent_base import build_demo_runtime  # noqa: E402


def _llm_unavailable(runtime: object, reply_text: str) -> bool:
    planner = getattr(runtime, "planner", None)
    llm = getattr(planner, "llm", None)
    if llm is not None and llm.__class__.__name__ == "NoLLM":
        return True
    return str(reply_text or "").lstrip().startswith("LLM 不可用")


def _side_effects_from_result(result: object) -> dict:
    external_result = getattr(result, "external_result", None)
    if not isinstance(external_result, dict):
        return {
            "side_effects_executed": False,
            "memory_write": False,
            "tool_use": False,
            "message_send": False,
            "file_write": False,
            "network_call": False,
        }
    return {
        "side_effects_executed": bool(external_result.get("side_effects_executed")),
        "memory_write": bool(external_result.get("memory_write_executed")),
        "tool_use": bool(external_result.get("tool_use_executed")),
        "message_send": bool(external_result.get("message_send_executed")),
        "file_write": bool(external_result.get("file_write_executed")),
        "network_call": bool(external_result.get("network_call_executed")),
    }


def main() -> int:
    try:
        payload = json.loads((sys.stdin.read() or "{}").lstrip("\ufeff"))
        user_text = str(payload.get("user_text") or "").strip()
        if not user_text:
            print(json.dumps({"status": "input_error", "reason": "empty_user_text"}, ensure_ascii=False))
            return 2

        runtime = build_demo_runtime(enable_operator_memory=False)
        result = runtime.handle_user_message(user_text)
        pending = runtime.list_pending_approvals()
        reply_text = str(getattr(result, "reply_text", "") or "")
        unavailable = _llm_unavailable(runtime, reply_text)
        response = {
            "status": "llm_expression_unavailable" if unavailable else "ok",
            "reason": "provider_not_configured" if unavailable else "",
            "reply_text": reply_text,
            "event_id": str(getattr(result, "event_id", "") or ""),
            "pending_approvals": int(pending.get("pending_count") or 0) if isinstance(pending, dict) else 0,
            **_side_effects_from_result(result),
        }
        print(json.dumps(response, ensure_ascii=False))
        return 0
    except Exception as exc:  # pragma: no cover - exercised by Electron smoke/error paths.
        print(json.dumps({
            "status": "llm_expression_unavailable",
            "reason": exc.__class__.__name__,
            "error": str(exc),
            "side_effects_executed": False,
            "memory_write": False,
            "tool_use": False,
            "message_send": False,
        }, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
