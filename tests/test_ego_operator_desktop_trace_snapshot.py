from pathlib import Path

from scripts.ego_operator_desktop_turn import (
    JOI_REAL_LOOP_TRACE_SNAPSHOT_SCHEMA_VERSION,
    build_joi_real_loop_trace_snapshot,
    extract_joi_real_loop_llm_replay_id,
    joi_real_loop_backend_trace_path,
)


AUTHORITY_FIELD_NAMES = {
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
    "mainline_authority",
    "runtime_registration",
    "proposal_id",
}


def contains_authority_field(value):
    if isinstance(value, dict):
        return any(key in AUTHORITY_FIELD_NAMES or contains_authority_field(child) for key, child in value.items())
    if isinstance(value, list):
        return any(contains_authority_field(item) for item in value)
    return False


def sample_trace_record():
    return {
        "event": {
            "event_id": "evt-001",
            "raw_text": "hello",
        },
        "state_digest": {
            "mode": "attend",
            "focus": "desktop_chat",
            "drives": {"stability": 0.75},
            "revision_counter": 3,
            "cycle_count": 4,
        },
        "subject_context": {
            "viability_state": {"energy": 0.6, "stress": 0.2},
            "private_prompt_surface": "must be hashed, not copied",
        },
        "llm_meta": {
            "provider": "openrouter",
            "model": "provider-model",
            "usage": {"total_tokens": 12},
        },
        "external_result": {
            "status": "completed",
            "side_effects_executed": False,
            "memory_write_executed": False,
        },
    }


def test_backend_trace_path_is_default_off(monkeypatch, tmp_path):
    monkeypatch.delenv("JOI_REAL_LOOP_G_ABLATION", raising=False)
    monkeypatch.setenv("JOI_REAL_LOOP_TRACE_DIR", str(tmp_path))

    assert joi_real_loop_backend_trace_path() is None

    monkeypatch.setenv("JOI_REAL_LOOP_G_ABLATION", "1")
    monkeypatch.setenv("JOI_REAL_LOOP_RUN_ID", "run with spaces")

    trace_path = joi_real_loop_backend_trace_path()

    assert trace_path is not None
    assert trace_path.parent == tmp_path / "backend_traces"
    assert trace_path.name.startswith("run_with_spaces_")
    assert trace_path.suffix == ".jsonl"


def test_trace_snapshot_is_sanitized_and_hashes_runtime_record(tmp_path):
    trace_path = tmp_path / "backend_traces" / "turn.jsonl"
    snapshot = build_joi_real_loop_trace_snapshot(sample_trace_record(), trace_path)

    assert snapshot["schema_version"] == JOI_REAL_LOOP_TRACE_SNAPSHOT_SCHEMA_VERSION
    assert snapshot["source"] == "ego_operator_desktop_turn_trace_store"
    assert snapshot["state_source"] == "ego_operator_runtime_trace_store"
    assert snapshot["event_id"] == "evt-001"
    assert len(snapshot["trace_record_hash"]) == 64
    assert len(snapshot["trace_path_hash"]) == 64
    assert snapshot["state_digest"]["mode"] == "attend"
    assert snapshot["state_digest"]["focus"] == "desktop_chat"
    assert snapshot["viability_state"] == {"energy": 0.6, "stress": 0.2}
    assert snapshot["llm_replay_contract"] == "absent"
    assert "raw_text" not in snapshot
    assert "private_prompt_surface" not in snapshot
    assert contains_authority_field(snapshot) is False


def test_llm_replay_id_is_extracted_only_from_explicit_replay_contract():
    assert extract_joi_real_loop_llm_replay_id(sample_trace_record()) == ""
    assert extract_joi_real_loop_llm_replay_id({
        "llm_meta": {
            "trace_record_hash": "a" * 64,
            "llm_replay_id": "llm-replay-001",
        },
    }) == "llm-replay-001"
