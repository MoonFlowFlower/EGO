from __future__ import annotations

from typing import Any

from .constants import FORBIDDEN_VISIBLE_KEYS


def _walk(payload: Any, path: str = "$") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_str = str(key)
            child_path = f"{path}.{key_str}"
            if key_str in FORBIDDEN_VISIBLE_KEYS:
                hits.append({"path": child_path, "key": key_str})
            hits.extend(_walk(value, child_path))
    elif isinstance(payload, list):
        for idx, value in enumerate(payload):
            hits.extend(_walk(value, f"{path}[{idx}]"))
    return hits


def scan_visible_payload(payload: Any) -> dict:
    hits = _walk(payload)
    return {
        "producer_function": "scan_visible_payload",
        "positive_control_key": "s_t",
        "leak_found": bool(hits),
        "hits": hits,
    }


def positive_control_report() -> dict:
    planted = {"candidate_visible": {"t": 1, "x1": 0.5, "s_t": 0.85}}
    result = scan_visible_payload(planted)
    return {"status": "pass" if result["leak_found"] else "fail", "scan": result}
