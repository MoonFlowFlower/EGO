import json
import io

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
