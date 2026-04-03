#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).parent
EGO_ROOT = SCRIPT_DIR.parent
EGOCORE_ROOT = EGO_ROOT / "EgoCore"
OPENEMOTION_ROOT = EGO_ROOT / "OpenEmotion"

if str(EGOCORE_ROOT) not in sys.path:
    sys.path.insert(0, str(EGOCORE_ROOT))
if str(OPENEMOTION_ROOT) not in sys.path:
    sys.path.insert(0, str(OPENEMOTION_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from telegram_mainline_common import init_runtime

from app.response_contract.output_check import apply_output_check
from app.response_contract.response_plan import build_runtime_result_response_plan
from app.telegram_runtime_bridge import TelegramRuntimeBridge


OBSERVATION_RECORD_SCHEMA_VERSION = "observation_record.v1"
DIRECT_REAL_OBSERVATION_SOURCE = "direct_real"
DELIVERY_AUTHORITY_SOURCE = "response_contract.output_check"
ALLOWED_TRANSPORT_SOURCES = {"runtime_harness", "telegram"}


def _is_iso8601(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return True


def _build_event_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:8]}"


def validate_observation_record(record: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    if str(record.get("schema_version") or "") != OBSERVATION_RECORD_SCHEMA_VERSION:
        missing.append("schema_version")
    if str(record.get("observation_source") or "") != DIRECT_REAL_OBSERVATION_SOURCE:
        missing.append("observation_source")
    if str(record.get("transport_source") or "") not in ALLOWED_TRANSPORT_SOURCES:
        missing.append("transport_source")
    if str(record.get("delivery_authority_source") or "") != DELIVERY_AUTHORITY_SOURCE:
        missing.append("delivery_authority_source")

    required_text_fields = (
        "session_id",
        "turn_id",
        "ingress_event_id",
        "ingress_text",
        "runtime_status",
        "runtime_reply_text",
        "delivery_event_id",
        "delivery_text",
        "reply_authority",
        "reply_origin",
        "delivery_kind",
        "output_check_reason",
    )
    for field_name in required_text_fields:
        if not str(record.get(field_name) or "").strip():
            missing.append(field_name)

    if not _is_iso8601(record.get("ingress_created_at")):
        missing.append("ingress_created_at")
    if not _is_iso8601(record.get("delivery_created_at")):
        missing.append("delivery_created_at")
    return missing


def build_runtime_observation_record(
    *,
    session_id: str,
    turn_id: str,
    user_input: str,
    result: Any,
    state: Any,
    transport_source: str,
    source: str,
    ingress_event_id: Optional[str] = None,
    ingress_created_at: Optional[str] = None,
    delivery_event_id: Optional[str] = None,
    delivery_created_at: Optional[str] = None,
) -> Dict[str, Any]:
    if transport_source not in ALLOWED_TRANSPORT_SOURCES:
        raise ValueError(f"Unsupported transport_source={transport_source}")

    response_plan = build_runtime_result_response_plan(result, state)
    verdict = apply_output_check(response_plan, state)

    record = {
        "schema_version": OBSERVATION_RECORD_SCHEMA_VERSION,
        "observation_source": DIRECT_REAL_OBSERVATION_SOURCE,
        "transport_source": transport_source,
        "source": source,
        "session_id": session_id,
        "turn_id": turn_id,
        "ingress_event_id": ingress_event_id or _build_event_id("ingress"),
        "ingress_created_at": ingress_created_at or datetime.now().isoformat(),
        "ingress_text": str(user_input or ""),
        "runtime_status": str(getattr(result, "status", "") or ""),
        "runtime_reply_text": str(getattr(result, "reply_text", "") or ""),
        "delivery_event_id": delivery_event_id or _build_event_id("delivery"),
        "delivery_created_at": delivery_created_at or datetime.now().isoformat(),
        "delivery_text": str(verdict.reply_text or ""),
        "reply_authority": str(verdict.applied_authority or ""),
        "reply_origin": str(verdict.reply_origin or ""),
        "delivery_kind": str(verdict.delivery_kind or ""),
        "delivery_authority_source": DELIVERY_AUTHORITY_SOURCE,
        "output_check_reason": str(verdict.reason or ""),
        "intent_gate_status": str(verdict.intent_gate_status or ""),
        "intent_gate_reason": str(verdict.intent_gate_reason or ""),
    }
    missing = validate_observation_record(record)
    if missing:
        raise ValueError(f"Invalid observation_record_v1 fields: {', '.join(missing)}")
    return record


def append_observation_records(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_observation_records(path: Path, *, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            entry = json.loads(line)
            if validate_observation_record(entry):
                continue
            records.append(entry)
    if limit is not None and limit > 0:
        return records[-limit:]
    return records


def extract_telegram_observation_records(session_log: Path, *, limit: int) -> List[Dict[str, Any]]:
    if limit <= 0 or not session_log.exists():
        return []
    observations: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None
    session_id = session_log.stem
    with session_log.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            entry = json.loads(line)
            kind = entry.get("kind")
            payload = entry.get("payload") or {}
            if kind == "telegram_ingress":
                current = {
                    "schema_version": OBSERVATION_RECORD_SCHEMA_VERSION,
                    "observation_source": DIRECT_REAL_OBSERVATION_SOURCE,
                    "transport_source": "telegram",
                    "source": "telegram",
                    "session_id": str(payload.get("session_key") or session_id),
                    "turn_id": str(payload.get("turn_id") or entry.get("event_id") or ""),
                    "ingress_event_id": entry.get("event_id"),
                    "ingress_created_at": entry.get("created_at"),
                    "ingress_text": payload.get("text_preview") or "",
                }
                continue
            if current is None:
                continue
            if kind == "runtime_v2_result":
                current["runtime_status"] = payload.get("status") or ""
                current["runtime_reply_text"] = payload.get("reply_text") or ""
                continue
            if kind == "telegram_delivery":
                current["delivery_event_id"] = entry.get("event_id")
                current["delivery_created_at"] = entry.get("created_at")
                current["delivery_text"] = payload.get("text") or ""
                current["reply_authority"] = payload.get("reply_authority") or ""
                current["reply_origin"] = payload.get("reply_origin") or ""
                current["delivery_kind"] = payload.get("delivery_kind") or ""
                current["delivery_authority_source"] = DELIVERY_AUTHORITY_SOURCE
                current["output_check_reason"] = payload.get("output_check_reason") or "telegram_delivery"
                current["intent_gate_status"] = payload.get("intent_gate_status") or ""
                current["intent_gate_reason"] = payload.get("intent_gate_reason") or ""
                if not validate_observation_record(current):
                    observations.append(dict(current))
                current = None
    return observations[-limit:]


async def run_runtime_mainline_session(
    *,
    messages: List[str],
    session_id: str,
    transport_source: str = "runtime_harness",
    source: str = "runtime_harness",
    runtime: Any | None = None,
) -> Tuple[Any, Any, List[Dict[str, Any]]]:
    runtime = runtime or init_runtime()
    ingress_bridge = TelegramRuntimeBridge()
    records: List[Dict[str, Any]] = []

    for index, text in enumerate(messages, start=1):
        state = runtime.get_state(session_id)
        decision = await ingress_bridge.inspect_ingress_semantic(text, state, llm_client=None)
        state.ingress_context = ingress_bridge.build_ingress_context(decision, state)
        state.ingress_context["observation_source"] = DIRECT_REAL_OBSERVATION_SOURCE
        state.ingress_context["traffic_source"] = "real"

        ingress_created_at = datetime.now().isoformat()
        ingress_event_id = _build_event_id(f"runtime_ingress_{index:03d}")
        result = await runtime.run_turn_typed(
            session_id=session_id,
            user_input=text,
            source=source,
        )
        delivery_created_at = datetime.now().isoformat()
        turn_id = (
            str(getattr(getattr(result, "reply", None), "turn_id", "") or "")
            or str(getattr(state, "active_turn_id", "") or "")
            or f"turn_{index:03d}"
        )
        records.append(
            build_runtime_observation_record(
                session_id=session_id,
                turn_id=turn_id,
                user_input=text,
                result=result,
                state=state,
                transport_source=transport_source,
                source=source,
                ingress_event_id=ingress_event_id,
                ingress_created_at=ingress_created_at,
                delivery_event_id=_build_event_id(f"runtime_delivery_{index:03d}"),
                delivery_created_at=delivery_created_at,
            )
        )

    return runtime, runtime.get_state(session_id), records


async def run_runtime_observation_session(
    *,
    messages: List[str],
    session_id: str,
    observation_log: Path,
    transport_source: str = "runtime_harness",
    source: str = "runtime_harness",
) -> Dict[str, Any]:
    _, _, records = await run_runtime_mainline_session(
        messages=messages,
        session_id=session_id,
        transport_source=transport_source,
        source=source,
    )
    append_observation_records(observation_log, records)
    return {
        "schema_version": "runtime_mainline_observation.run.v1",
        "session_id": session_id,
        "transport_source": transport_source,
        "observation_log": str(observation_log),
        "observation_count": len(records),
        "records": records,
    }
