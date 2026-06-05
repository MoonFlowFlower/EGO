import json
import io
from typing import Any

import pytest

from scripts import ego_desktop_pspc_signal_extract as extractor


def test_parse_semantic_response_accepts_strict_event_packet() -> None:
    packet = extractor.parse_semantic_response(
        json.dumps(
            {
                "events": [
                    {
                        "event_kind": "gift_or_care_offer",
                        "category": "gentle",
                        "confidence": 0.82,
                        "salience": 0.7,
                        "state_delta": {
                            "trust_proxy": 0.18,
                            "approach_tendency": 0.16,
                        },
                        "evidence_excerpt": "给你喝奶茶",
                        "reason": "user offers a small care gesture",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        user_text="给你喝奶茶",
    )

    assert packet["schema_version"] == extractor.SEMANTIC_EVENTS_SCHEMA_VERSION
    assert packet["claim_ceiling"] == extractor.SEMANTIC_EXTRACTOR_CLAIM_CEILING
    assert packet["runtime_authority"] == "none"
    assert packet["enabled"] is False
    assert packet["mainline_connected"] is False
    assert packet["extractor_status"] == "ok"
    assert packet["events"][0]["event_kind"] == "gift_or_care_offer"
    assert packet["events"][0]["category"] == "gentle"
    assert packet["side_effects_absent"]["real_memory_written"] is False


def test_parse_semantic_response_rejects_forbidden_fields() -> None:
    with pytest.raises(ValueError, match="forbidden executable field"):
        extractor.parse_semantic_response(
            json.dumps(
                {
                    "events": [
                        {
                            "event_kind": "gift_or_care_offer",
                            "category": "gentle",
                            "confidence": 0.82,
                            "salience": 0.7,
                            "state_delta": {},
                            "evidence_excerpt": "给你喝奶茶",
                            "reason": "bad packet",
                            "user_message": "do this",
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            user_text="给你喝奶茶",
        )


def test_parse_semantic_response_derives_category_from_event_kind() -> None:
    packet = extractor.parse_semantic_response(
        json.dumps(
            {
                "events": [
                    {
                        "event_kind": "gentle_touch",
                        "category": "neutral",
                        "confidence": 0.8,
                        "salience": 0.8,
                        "state_delta": {"trust_proxy": 0.1},
                        "evidence_excerpt": "摸摸你",
                        "reason": "provider supplied inconsistent category",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        user_text="摸摸你",
    )

    assert packet["events"][0]["event_kind"] == "gentle_touch"
    assert packet["events"][0]["category"] == "gentle"


def test_unavailable_packet_has_no_events_or_authority() -> None:
    packet = extractor.build_unavailable_packet(
        user_text="给你喝奶茶",
        reason="timeout",
    )

    assert packet["extractor_status"] == "extractor_unavailable"
    assert packet["events"] == []
    assert packet["runtime_authority"] == "none"
    assert packet["enabled"] is False
    assert packet["mainline_connected"] is False
    assert packet["side_effects_absent"]["transport_called"] is False


def test_stdin_payload_accepts_utf8_bom(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        extractor.sys,
        "stdin",
        io.StringIO('\ufeff{"user_text":"给你喝奶茶","recent_messages":[]}'),
    )

    payload = extractor.read_stdin_payload()

    assert payload["user_text"] == "给你喝奶茶"


def test_stdin_payload_reads_utf8_bytes_without_chinese_corruption() -> None:
    class BinaryInput:
        buffer = io.BytesIO('{"user_text":"摸摸你","recent_messages":[]}'.encode("utf-8"))

    payload = extractor.read_stdin_payload(BinaryInput())

    assert payload["user_text"] == "摸摸你"


def test_openrouter_falls_back_after_empty_primary_response(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __init__(self, payload: dict[str, Any]) -> None:
            self.payload = payload

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(self.payload).encode("utf-8")

    calls: list[str] = []

    def fake_urlopen(request: Any, timeout: float) -> FakeResponse:
        body = json.loads(request.data.decode("utf-8"))
        calls.append(body["model"])
        if len(calls) == 1:
            return FakeResponse({"choices": [{"message": {"content": ""}}]})
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "events": [
                                        {
                                            "event_kind": "gentle_touch",
                                            "category": "gentle",
                                            "confidence": 0.84,
                                            "salience": 0.7,
                                            "state_delta": {"trust_proxy": 0.08},
                                            "evidence_excerpt": "摸摸你",
                                            "reason": "gentle touch cue",
                                        }
                                    ]
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            }
        )

    monkeypatch.setenv("OPENROUTER_PSPC_SIGNAL_MODEL", "primary-empty")
    monkeypatch.setattr(extractor, "DEFAULT_FALLBACK_MODELS_TEXT", "fallback-ok")
    monkeypatch.setattr(extractor, "_openrouter_key", lambda: "test-key")
    monkeypatch.setattr(extractor.urllib.request, "urlopen", fake_urlopen)

    raw = extractor.call_openrouter({"user_text": "摸摸你", "recent_messages": []}, timeout_ms=6000)
    packet = extractor.parse_semantic_response(raw, user_text="摸摸你")

    assert calls == ["primary-empty", "fallback-ok"]
    assert packet["extractor_status"] == "ok"
    assert packet["events"][0]["event_kind"] == "gentle_touch"
