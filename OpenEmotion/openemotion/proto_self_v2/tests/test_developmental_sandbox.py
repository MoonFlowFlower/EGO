from __future__ import annotations

from openemotion.proto_self_v2.kernel import process_update_packet
from openemotion.proto_self_v2.schemas import UpdateEventV2, UpdatePacketV2
from openemotion.proto_self_v2.state import ProtoSelfStateV2


def _developmental_packet(*, event_type: str = "developmental_tick", replay_seed: int | None = None) -> UpdatePacketV2:
    runtime_summary = {
        "runtime": "runtime_v2",
        "state_scope": "agent_global",
        "developmental_mode": "shadow_observe",
        "observation_source": "synthetic" if event_type == "developmental_tick" else "replay",
        "developmental_trigger": "idle",
        "idle_seconds": 90.0,
        "max_candidates": 4,
    }
    if replay_seed is not None:
        runtime_summary["replay_seed"] = replay_seed
    return UpdatePacketV2(
        event_id=f"evt_{event_type}",
        timestamp="2026-04-01T21:00:00",
        event=UpdateEventV2(
            actor="system",
            source="runtime",
            event_type=event_type,
            user_intent=None,
            raw_text=None,
        ),
        conversation_summary={"session_id": "session:test", "turn_id": "turn_dev"},
        task_summary={"pending_tasks": 0, "blocked_tasks": 0},
        runtime_summary=runtime_summary,
        safety_context={"risk_level": "low"},
        intervention_context={
            "developmental_input": {
                "state_snapshot": {"identity_confidence": 0.5, "current_mode": "chat"},
                "unresolved_tensions": [{"kind": "identity", "intensity": 0.8}],
                "long_term_goals": [{"name": "cohere", "pressure": 0.4}],
            }
        },
    )


def test_developmental_tick_writes_shadow_and_trace(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENEMOTION_MVP12_ARTIFACTS_DIR", str(tmp_path))
    state = ProtoSelfStateV2.empty()

    output = process_update_packet(state, _developmental_packet())

    assert output.schema_version == "proto_self.output.v2"
    assert output.candidate_actions == []
    assert output.developmental_summary["cycle_id"]
    assert output.developmental_gate["status"] == "allow"
    assert output.developmental_shadow_delta["shadow_revision_after"] == 1
    assert output.trace_payload["developmental"]["cycle_id"] == output.developmental_summary["cycle_id"]
    assert state.developmental_shadow.shadow_revision == 1
    assert (tmp_path / "developmental_cycles.json").exists()
    assert (tmp_path / "developmental_cycles.jsonl").exists()
    assert (tmp_path / "candidate_pool.json").exists()
    assert (tmp_path / "shadow_state.json").exists()
    assert (tmp_path / "replay_consistency_report.json").exists()
    assert (tmp_path / "gate_checklist.md").exists()


def test_same_replay_seed_produces_same_candidate_hashes(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENEMOTION_MVP12_ARTIFACTS_DIR", str(tmp_path))
    state_one = ProtoSelfStateV2.empty()
    state_two = ProtoSelfStateV2.empty()

    output_one = process_update_packet(state_one, _developmental_packet(replay_seed=123456))
    output_two = process_update_packet(state_two, _developmental_packet(replay_seed=123456))

    assert output_one.trace_payload["developmental"]["candidate_hashes"] == output_two.trace_payload["developmental"]["candidate_hashes"]


def test_developmental_replay_does_not_mutate_formal_proto_state(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENEMOTION_MVP12_ARTIFACTS_DIR", str(tmp_path))
    state = ProtoSelfStateV2.empty()
    formal_before = {
        "identity": state.identity.to_dict(),
        "self_model": state.self_model.to_dict(),
        "drives": state.drives.to_dict(),
        "cycles": state.cycles.to_dict(),
        "revision_counter": state.revision_counter,
    }

    output = process_update_packet(state, _developmental_packet(event_type="developmental_replay", replay_seed=42))

    formal_after = {
        "identity": state.identity.to_dict(),
        "self_model": state.self_model.to_dict(),
        "drives": state.drives.to_dict(),
        "cycles": state.cycles.to_dict(),
        "revision_counter": state.revision_counter,
    }

    assert output.developmental_summary["observation_source"] == "replay"
    assert formal_after == formal_before
    assert state.developmental_shadow.shadow_revision == 1
