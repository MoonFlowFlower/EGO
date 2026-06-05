"""Extract PSPC reply-preview semantic interaction events for EgoDesktop.

This helper is local preview infrastructure only. It emits audit/debug signal
packets and never writes memory, invokes gates, sends messages, or executes
tools.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any
import urllib.error
import urllib.request


SEMANTIC_EVENTS_SCHEMA_VERSION = "ego_desktop.pspc_semantic_interaction_events.v0"
SEMANTIC_EXTRACTOR_CLAIM_CEILING = "local_reply_preview_semantic_signal_extractor_only"
DEFAULT_OPENROUTER_KEY_FILE = Path(r"D:\Project\AIProject\MyProject\Test\openrouterKey.txt")
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "tencent/hy3-preview")
DEFAULT_FALLBACK_MODELS_TEXT = os.getenv(
    "OPENROUTER_PSPC_SIGNAL_FALLBACK_MODELS",
    os.getenv(
        "OPENROUTER_FALLBACK_MODELS",
        "google/gemini-2.5-flash-lite,google/gemini-3.1-flash-lite,openai/gpt-4.1-mini",
    ),
)
FORBIDDEN_FIELDS = {
    "action",
    "tool_call",
    "command",
    "user_message",
    "memory_write",
    "gate_decision",
    "approval_id",
    "transport",
    "send",
    "schedule",
    "enable",
    "enabled",
    "mainline_connected",
    "mainline_authority",
    "runtime_authority",
    "proposal_id",
}
EVENT_KINDS = {
    "gift_or_care_offer",
    "gentle_touch",
    "affinity_statement",
    "trust_probe",
    "comfort_presence",
    "boundary_pressure",
    "fatigue_or_late_night",
    "neutral",
}
CATEGORIES = {"gentle", "interruption", "late_night", "neutral"}
EVENT_KIND_CATEGORY = {
    "gift_or_care_offer": "gentle",
    "gentle_touch": "gentle",
    "affinity_statement": "gentle",
    "trust_probe": "gentle",
    "comfort_presence": "gentle",
    "boundary_pressure": "interruption",
    "fatigue_or_late_night": "late_night",
    "neutral": "neutral",
}
STATE_DELTA_FIELDS = {
    "trust_proxy",
    "stress_proxy",
    "approach_tendency",
    "avoidance_tendency",
    "care_tendency",
    "boundary_tendency",
    "low_interrupt_tendency",
}


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


def _openrouter_key() -> str:
    if os.getenv("OPENROUTER_API_KEY"):
        return os.getenv("OPENROUTER_API_KEY", "")
    configured = os.getenv("OPENROUTER_API_KEY_FILE", "").strip()
    candidates = [Path(configured)] if configured else []
    candidates.append(DEFAULT_OPENROUTER_KEY_FILE)
    for candidate in candidates:
        key = _read_key_file(candidate)
        if key:
            return key
    return ""


def _contains_forbidden_field(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in FORBIDDEN_FIELDS:
                return True
            if _contains_forbidden_field(child):
                return True
    if isinstance(value, list):
        return any(_contains_forbidden_field(item) for item in value)
    return False


def _number(value: Any, *, default: float = 0.0, minimum: float = 0.0, maximum: float = 1.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return round(max(minimum, min(maximum, parsed)), 4)


def _packet_base(user_text: str, *, status: str) -> dict[str, Any]:
    return {
        "schema_version": SEMANTIC_EVENTS_SCHEMA_VERSION,
        "source": "ego_desktop_pspc_semantic_signal_extractor",
        "claim_ceiling": SEMANTIC_EXTRACTOR_CLAIM_CEILING,
        "runtime_authority": "none",
        "enabled": False,
        "mainline_connected": False,
        "extractor_status": status,
        "input_text_hash_basis": str(user_text or "")[:24],
        "events": [],
        "forbidden": {
            "direct_action": True,
            "direct_user_message": True,
            "direct_memory_write": True,
            "runtime_gate_bypass": True,
            "runtime_registration": True,
            "proactive_trigger": True,
            "planner_execution": True,
            "model_execution": True,
            "training": True,
        },
        "no_authority": {
            "direct_action_allowed": False,
            "direct_user_message_allowed": False,
            "direct_memory_write_allowed": False,
            "runtime_gate_bypass_allowed": False,
            "runtime_registration_allowed": False,
            "proactive_trigger_allowed": False,
            "planner_execution_allowed": False,
            "model_execution_allowed": False,
            "training_allowed": False,
        },
        "side_effects_absent": {
            "real_memory_written": False,
            "gate_invoked": False,
            "approval_invoked": False,
            "transport_called": False,
            "proactive_triggered": False,
            "runtime_registered": False,
            "message_sent": False,
        },
    }


def build_unavailable_packet(*, user_text: str, reason: str) -> dict[str, Any]:
    packet = _packet_base(user_text, status="extractor_unavailable")
    packet["reason"] = str(reason or "unavailable")[:240]
    return packet


def _normalize_state_delta(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, float] = {}
    for key, raw in value.items():
        if str(key) not in STATE_DELTA_FIELDS:
            raise ValueError(f"invalid state_delta field: {key}")
        normalized[str(key)] = _number(raw, minimum=-0.25, maximum=0.25)
    return normalized


def _normalize_event(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("event must be an object")
    if _contains_forbidden_field(value):
        raise ValueError("forbidden executable field in semantic event")
    event_kind = str(value.get("event_kind") or "neutral")
    category = str(value.get("category") or "neutral")
    if event_kind not in EVENT_KINDS:
        raise ValueError(f"invalid event_kind: {event_kind}")
    if category not in CATEGORIES:
        raise ValueError(f"invalid category: {category}")
    category = EVENT_KIND_CATEGORY[event_kind]
    return {
        "event_kind": event_kind,
        "category": category,
        "confidence": _number(value.get("confidence"), default=0.0),
        "salience": _number(value.get("salience"), default=0.0),
        "state_delta": _normalize_state_delta(value.get("state_delta")),
        "evidence_excerpt": str(value.get("evidence_excerpt") or "")[:120],
        "reason": str(value.get("reason") or "")[:240],
    }


def parse_semantic_response(raw_response: str, *, user_text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(str(raw_response or "").strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid semantic extractor JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("semantic extractor response must be an object")
    if _contains_forbidden_field(parsed):
        raise ValueError("forbidden executable field in semantic extractor response")
    events = parsed.get("events")
    if events is None:
        events = []
    if not isinstance(events, list):
        raise ValueError("events must be an array")
    if len(events) > 4:
        raise ValueError("events must contain at most 4 items")
    packet = _packet_base(user_text, status="ok")
    packet["events"] = [_normalize_event(event) for event in events]
    if not packet["events"]:
        packet["events"] = [
            {
                "event_kind": "neutral",
                "category": "neutral",
                "confidence": 1.0,
                "salience": 0.0,
                "state_delta": {},
                "evidence_excerpt": str(user_text or "")[:80],
                "reason": "No relationship-relevant interaction signal detected.",
            }
        ]
    return packet


def build_prompt(payload: dict[str, Any]) -> list[dict[str, str]]:
    user_text = str(payload.get("user_text") or "")
    recent_messages = payload.get("recent_messages")
    if not isinstance(recent_messages, list):
        recent_messages = []
    recent_lines = []
    for item in recent_messages[-8:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "")
        content = str(item.get("content") or "")[:300]
        if role in {"user", "assistant"} and content:
            recent_lines.append(f"{role}: {content}")
    schema = (
        '{"events":[{"event_kind":"gift_or_care_offer|gentle_touch|affinity_statement|'
        'trust_probe|comfort_presence|boundary_pressure|fatigue_or_late_night|neutral",'
        '"category":"gentle|interruption|late_night|neutral","confidence":0.0,'
        '"salience":0.0,"state_delta":{"trust_proxy":0.0},"evidence_excerpt":"",'
        '"reason":""}]}'
    )
    return [
        {
            "role": "system",
            "content": (
                "You extract local PSPC reply-preview interaction signals. "
                "Return strict JSON only. Do not output actions, user messages, tool calls, "
                "memory writes, gate decisions, transport, schedule, enabled, or mainline fields. "
                "The output is audit/debug data only, not a command. "
                "State deltas must be small proxy updates between -0.25 and 0.25."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Recent transcript:\n{chr(10).join(recent_lines) or '(none)'}\n\n"
                f"Current user text:\n{user_text}\n\n"
                "Classify semantic interaction events. Use neutral if there is no relationship, "
                "boundary, or late-night care signal. Required JSON shape:\n"
                f"{schema}"
            ),
        },
    ]


def _candidate_models() -> list[str]:
    primary = os.getenv("OPENROUTER_PSPC_SIGNAL_MODEL", DEFAULT_MODEL).strip()
    fallbacks = [
        item.strip()
        for item in DEFAULT_FALLBACK_MODELS_TEXT.split(",")
        if item.strip()
    ]
    return list(dict.fromkeys([primary, *fallbacks] if primary else fallbacks))


def _call_openrouter_model(payload: dict[str, Any], *, timeout_ms: int, model: str) -> str:
    key = _openrouter_key()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is empty")
    body = {
        "model": model,
        "messages": build_prompt(payload),
        "temperature": 0,
        "max_tokens": 500,
    }
    if os.getenv("OPENROUTER_PSPC_SIGNAL_RESPONSE_FORMAT", "json_object").strip().lower() != "off":
        body["response_format"] = {"type": "json_object"}
    request = urllib.request.Request(
        os.getenv("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_BASE_URL),
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", ""),
            "X-Title": os.getenv("OPENROUTER_APP_NAME", "EgoDesktop"),
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=max(1, timeout_ms / 1000.0)) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    choices = parsed.get("choices") if isinstance(parsed, dict) else None
    if not choices:
        raise RuntimeError("OpenRouter response has no choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not content:
        raise RuntimeError("OpenRouter response has empty content")
    return str(content)


def call_openrouter(payload: dict[str, Any], *, timeout_ms: int) -> str:
    errors: list[str] = []
    for model in _candidate_models():
        try:
            return _call_openrouter_model(payload, timeout_ms=timeout_ms, model=model)
        except (RuntimeError, urllib.error.URLError, TimeoutError) as exc:
            errors.append(f"{model}: {exc}")
    raise RuntimeError("OpenRouter PSPC extractor failed for all models: " + " | ".join(errors))


def read_stdin_payload(stream: Any = None) -> dict[str, Any]:
    try:
        source = stream if stream is not None else sys.stdin
        source_buffer = getattr(source, "buffer", None)
        if source_buffer is not None:
            raw = source_buffer.read().decode("utf-8-sig")
        else:
            raw = source.read().lstrip("\ufeff")
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid input JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("input payload must be an object")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract EgoDesktop PSPC semantic interaction signals.")
    parser.add_argument("--timeout-ms", type=int, default=6000)
    parser.add_argument("--fixture-response", default="")
    args = parser.parse_args(argv)
    try:
        payload = read_stdin_payload()
        user_text = str(payload.get("user_text") or "")
        if args.fixture_response:
            raw_response = args.fixture_response
        else:
            raw_response = call_openrouter(payload, timeout_ms=args.timeout_ms)
        packet = parse_semantic_response(raw_response, user_text=user_text)
    except (ValueError, RuntimeError, urllib.error.URLError, TimeoutError) as exc:
        try:
            user_text = str(locals().get("payload", {}).get("user_text") or "")
        except Exception:
            user_text = ""
        packet = build_unavailable_packet(user_text=user_text, reason=str(exc))
    print(json.dumps(packet, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
