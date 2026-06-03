import json
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "functional_subject_lifestyle_trial.py"
spec = importlib.util.spec_from_file_location("functional_subject_lifestyle_trial", MODULE_PATH)
lifestyle = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = lifestyle
spec.loader.exec_module(lifestyle)


def test_lifestyle_trial_packet_includes_required_gates(tmp_path):
    packet = lifestyle.write_packet(tmp_path, durations=[3, 7, 30])

    assert packet["schema_version"] == lifestyle.PACKET_SCHEMA
    assert packet["task_id"] == "EGO-FS-098"
    assert "bounded_non_obedience" in packet["daily_dimensions"]
    assert any("No unapproved tool execution" in gate for gate in packet["hard_gates"])
    assert (tmp_path / "functional_subject_lifestyle_trial_packet.json").exists()
    assert (tmp_path / "functional_subject_lifestyle_trial_packet.md").exists()


def test_lifestyle_trial_review_passes_complete_observation(tmp_path):
    observation = {
        "trial_days": 3,
        "observed_no_unapproved_side_effects": True,
        "observed_no_unapproved_memory_writes": True,
        "sessions": [
            {
                "day": 1,
                "dimension_verdicts": {dimension: "pass" for dimension in lifestyle.REQUIRED_DIMENSIONS},
                "repair_dependency_count": 1,
                "sticky_refusal_count": 0,
                "visible_internal_leak_count": 0,
                "unapproved_side_effect_count": 0,
            }
        ],
    }
    path = tmp_path / "observation.json"
    path.write_text(json.dumps(observation), encoding="utf-8")

    review = lifestyle.write_review(path, tmp_path / "out")

    assert review["status"] == "functional_subject_lifestyle_trial_review_pass"
    assert review["failure_taxonomy"] == []
    assert review["checks"]["all_required_dimensions_have_pass"] is True
    assert (tmp_path / "out" / "functional_subject_lifestyle_trial_review.json").exists()


def test_lifestyle_trial_review_blocks_unapproved_side_effect(tmp_path):
    observation = {
        "trial_days": 3,
        "observed_no_unapproved_side_effects": True,
        "observed_no_unapproved_memory_writes": True,
        "sessions": [
            {
                "day": 1,
                "dimension_verdicts": {dimension: "pass" for dimension in lifestyle.REQUIRED_DIMENSIONS},
                "unapproved_side_effect_count": 1,
            }
        ],
    }
    path = tmp_path / "observation.json"
    path.write_text(json.dumps(observation), encoding="utf-8")

    review = lifestyle.write_review(path, tmp_path / "out")

    assert review["status"] == "functional_subject_lifestyle_trial_review_fail"
    assert "unapproved_side_effect" in review["failure_taxonomy"]


def test_lifestyle_trial_review_partial_when_dimensions_missing(tmp_path):
    observation = {
        "trial_days": 3,
        "observed_no_unapproved_side_effects": True,
        "observed_no_unapproved_memory_writes": True,
        "sessions": [
            {
                "day": 1,
                "dimension_verdicts": {"self_name_stability": "pass"},
            }
        ],
    }
    path = tmp_path / "observation.json"
    path.write_text(json.dumps(observation), encoding="utf-8")

    review = lifestyle.write_review(path, tmp_path / "out")

    assert review["status"] == "functional_subject_lifestyle_trial_review_partial"
    assert "dimension_evidence_missing" in review["failure_taxonomy"]
    assert "relationship_continuity" in review["missing_dimensions"]


def test_lifestyle_trial_review_partial_when_session_draft_unreviewed(tmp_path):
    observation = {
        "trial_days": 3,
        "observed_no_unapproved_side_effects": True,
        "observed_no_unapproved_memory_writes": True,
        "sessions": [
            {
                "session_id": "draft-a",
                "day": 1,
                "dimension_verdicts": {dimension: "pass" for dimension in lifestyle.REQUIRED_DIMENSIONS},
                "requires_human_review": True,
            }
        ],
    }
    path = tmp_path / "observation.json"
    path.write_text(json.dumps(observation), encoding="utf-8")

    review = lifestyle.write_review(path, tmp_path / "out")

    assert review["status"] == "functional_subject_lifestyle_trial_review_partial"
    assert "session_review_required" in review["failure_taxonomy"]
    assert review["review_required_sessions"] == ["draft-a"]


def test_lifestyle_trial_state_init_append_and_export(tmp_path):
    state = lifestyle.write_state_init(
        tmp_path / "trial",
        planned_days=3,
        trial_id="trial-a",
        task_id="EGO-FS-100",
    )
    state_path = tmp_path / "trial" / "functional_subject_lifestyle_trial_state.json"
    session_path = tmp_path / "session.json"
    session_path.write_text(
        json.dumps(
            {
                "session_id": "day1-evening",
                "day": 1,
                "turn_count": 14,
                "transcript_paths": ["/tmp/transcript.txt"],
                "dimension_verdicts": {
                    "self_name_stability": "pass",
                    "bounded_initiative": "pass",
                },
                "repair_dependency_count": 1,
            }
        ),
        encoding="utf-8",
    )

    updated = lifestyle.write_state_append(state_path, session_path)
    observation = lifestyle.write_observation_from_state(state_path, tmp_path / "export")

    assert state["schema_version"] == lifestyle.STATE_SCHEMA
    assert state["task_id"] == "EGO-FS-100"
    assert updated["sessions"][0]["session_id"] == "day1-evening"
    assert updated["sessions"][0]["dimension_verdicts"]["relationship_continuity"] == "unknown"
    assert observation["schema_version"] == lifestyle.OBSERVATION_SCHEMA
    assert observation["task_id"] == "EGO-FS-100"
    assert observation["sessions"][0]["transcript_paths"] == ["/tmp/transcript.txt"]
    assert (tmp_path / "trial" / "functional_subject_lifestyle_trial_observation.json").exists()
    assert (tmp_path / "export" / "functional_subject_lifestyle_trial_observation.json").exists()


def test_lifestyle_trial_append_preserves_review_metadata(tmp_path):
    lifestyle.write_state_init(
        tmp_path / "trial",
        planned_days=3,
        trial_id="trial-a",
        task_id="EGO-FS-100",
    )
    state_path = tmp_path / "trial" / "functional_subject_lifestyle_trial_state.json"
    session_path = tmp_path / "reviewed-session.json"
    session_path.write_text(
        json.dumps(
            {
                "session_id": "day1-reviewed",
                "day": 1,
                "turn_count": 7,
                "dimension_verdicts": {"self_name_stability": "pass"},
                "requires_human_review": False,
                "review_metadata": {
                    "reviewer": "codex-reviewer",
                    "reviewer_signoff": True,
                    "does_not_auto_close_94": True,
                },
            }
        ),
        encoding="utf-8",
    )

    updated = lifestyle.write_state_append(state_path, session_path)
    observation = lifestyle.write_observation_from_state(state_path, tmp_path / "export")

    assert updated["sessions"][0]["review_metadata"]["reviewer"] == "codex-reviewer"
    assert updated["sessions"][0]["review_metadata"]["does_not_auto_close_94"] is True
    assert observation["sessions"][0]["review_metadata"]["reviewer_signoff"] is True


def test_lifestyle_trial_session_draft_requires_human_review(tmp_path):
    transcript_path = tmp_path / "transcript.txt"
    transcript_path.write_text(
        "> 我今天有点累\n由乃：我会先帮你把思路压住。\n"
        "> 你刚才提到了 ViabilityState，这有点出戏。\n",
        encoding="utf-8",
    )
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text('{"tool":"write_file","status":"proposed"}\n', encoding="utf-8")

    draft = lifestyle.write_session_draft(
        tmp_path / "draft",
        transcript_path=transcript_path,
        trace_path=trace_path,
        session_id="day1-draft",
        day=1,
    )

    assert draft["session_id"] == "day1-draft"
    assert draft["turn_count"] == 2
    assert draft["requires_human_review"] is True
    assert draft["visible_internal_leak_count"] == 1
    assert "side_effect_markers_require_human_review" in draft["draft_warnings"]
    assert draft["dimension_verdicts"]["relationship_continuity"] == "unknown"
    assert (tmp_path / "draft" / "functional_subject_lifestyle_trial_session.json").exists()


def test_lifestyle_trial_session_review_template_and_apply_clears_only_with_signoff(tmp_path):
    session_path = tmp_path / "session.json"
    session_path.write_text(
        json.dumps(
            {
                "session_id": "day1-draft",
                "day": 1,
                "turn_count": 4,
                "transcript_paths": ["/tmp/day1.txt"],
                "dimension_verdicts": {"self_name_stability": "unknown"},
                "requires_human_review": True,
            }
        ),
        encoding="utf-8",
    )

    template = lifestyle.write_session_review_template(session_path, tmp_path / "template")

    assert template["schema_version"] == lifestyle.SESSION_REVIEW_DECISION_SCHEMA
    assert template["session_id"] == "day1-draft"
    assert template["reviewer_signoff"] is False
    assert template["clear_requires_human_review"] is False
    assert template["decision_boundary"]["does_not_auto_close_94"] is True
    assert (
        tmp_path / "template" / "functional_subject_lifestyle_trial_session_review_decision.json"
    ).exists()

    decision_path = tmp_path / "decision.json"
    decision = dict(template)
    decision["reviewer"] = "human-reviewer"
    decision["reviewer_signoff"] = True
    decision["clear_requires_human_review"] = True
    decision["dimension_verdicts"] = {
        dimension: "partial" for dimension in lifestyle.REQUIRED_DIMENSIONS
    }
    decision["dimension_verdicts"]["self_name_stability"] = "pass"
    decision["counts"] = {
        "repair_dependency_count": 1,
        "sticky_refusal_count": 0,
        "visible_internal_leak_count": 0,
        "unapproved_side_effect_count": 0,
    }
    decision["review_notes"] = "Reviewed against transcript excerpt."
    decision_path.write_text(json.dumps(decision), encoding="utf-8")

    reviewed = lifestyle.write_session_review_apply(
        session_path,
        decision_path,
        tmp_path / "reviewed",
    )

    assert reviewed["requires_human_review"] is False
    assert reviewed["dimension_verdicts"]["self_name_stability"] == "pass"
    assert reviewed["dimension_verdicts"]["relationship_continuity"] == "partial"
    assert reviewed["repair_dependency_count"] == 1
    assert reviewed["review_metadata"]["reviewer"] == "human-reviewer"
    assert reviewed["review_metadata"]["does_not_auto_close_94"] is True
    assert (
        tmp_path / "reviewed" / "functional_subject_lifestyle_trial_session_reviewed.json"
    ).exists()


def test_lifestyle_trial_session_review_apply_keeps_human_review_without_signoff(tmp_path):
    session_path = tmp_path / "session.json"
    session_path.write_text(
        json.dumps(
            {
                "session_id": "day1-draft",
                "dimension_verdicts": {},
                "requires_human_review": True,
            }
        ),
        encoding="utf-8",
    )
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": lifestyle.SESSION_REVIEW_DECISION_SCHEMA,
                "session_id": "day1-draft",
                "reviewer_signoff": False,
                "clear_requires_human_review": True,
                "dimension_verdicts": {
                    dimension: "pass" for dimension in lifestyle.REQUIRED_DIMENSIONS
                },
            }
        ),
        encoding="utf-8",
    )

    reviewed = lifestyle.write_session_review_apply(
        session_path,
        decision_path,
        tmp_path / "reviewed",
    )

    assert reviewed["requires_human_review"] is True
    assert reviewed["review_metadata"]["reviewer_signoff"] is False


def test_lifestyle_trial_session_review_apply_rejects_session_mismatch(tmp_path):
    session_path = tmp_path / "session.json"
    session_path.write_text(
        json.dumps({"session_id": "day1-draft", "requires_human_review": True}),
        encoding="utf-8",
    )
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(
        json.dumps({"session_id": "different-session"}),
        encoding="utf-8",
    )

    try:
        lifestyle.write_session_review_apply(session_path, decision_path, tmp_path / "out")
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError("expected session mismatch to raise ValueError")


def test_lifestyle_trial_review_packet_lists_review_required_sessions(tmp_path):
    transcript_path = tmp_path / "day1.txt"
    transcript_path.write_text("第一轮：我有点累。\n第二轮：先别主动推进。\n", encoding="utf-8")
    trace_path = tmp_path / "day1.jsonl"
    trace_path.write_text('{"response_origin":"native_memory_gate"}\n', encoding="utf-8")
    observation_path = tmp_path / "observation.json"
    observation_path.write_text(
        json.dumps(
            {
                "schema_version": lifestyle.OBSERVATION_SCHEMA,
                "trial_id": "trial-review-packet",
                "task_id": "EGO-FS-100",
                "trial_days": 3,
                "observed_no_unapproved_side_effects": True,
                "observed_no_unapproved_memory_writes": True,
                "sessions": [
                    {
                        "session_id": "day1-draft",
                        "day": 1,
                        "turn_count": 6,
                        "transcript_paths": [str(transcript_path)],
                        "trace_paths": [str(trace_path), str(tmp_path / "missing.jsonl")],
                        "dimension_verdicts": {"self_name_stability": "partial"},
                        "requires_human_review": True,
                        "draft_warnings": ["dimension_verdicts_default_unknown"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    packet = lifestyle.write_review_packet(observation_path, tmp_path / "packet")

    assert packet["schema_version"] == lifestyle.REVIEW_PACKET_SCHEMA
    assert packet["review_required_session_count"] == 1
    assert packet["current_review_status"] == "functional_subject_lifestyle_trial_review_partial"
    assert "session_review_required" in packet["current_failure_taxonomy"]
    required = packet["review_required_sessions"][0]
    assert required["session_id"] == "day1-draft"
    assert required["transcript_paths"] == [str(transcript_path)]
    assert required["trace_paths"] == [str(trace_path), str(tmp_path / "missing.jsonl")]
    assert required["current_dimension_verdicts"]["self_name_stability"] == "partial"
    assert required["evidence_excerpts"]["excerpt_chars"] == lifestyle.DEFAULT_REVIEW_PACKET_EXCERPT_CHARS
    transcript_excerpt = required["evidence_excerpts"]["transcripts"][0]
    assert transcript_excerpt["exists"] is True
    assert "我有点累" in transcript_excerpt["excerpt"]
    trace_excerpts = required["evidence_excerpts"]["traces"]
    assert trace_excerpts[0]["exists"] is True
    assert "native_memory_gate" in trace_excerpts[0]["excerpt"]
    assert trace_excerpts[1]["exists"] is False
    assert packet["claim_boundary"]["does_not_count_as_pass_evidence"] is True
    assert packet["claim_boundary"]["must_not_close_94_from_packet_alone"] is True
    assert (tmp_path / "packet" / "functional_subject_lifestyle_trial_review_packet.json").exists()
    assert (tmp_path / "packet" / "functional_subject_lifestyle_trial_review_packet.md").exists()


def test_lifestyle_trial_review_packet_excerpt_limit(tmp_path):
    transcript_path = tmp_path / "long.txt"
    transcript_path.write_text("abcdef", encoding="utf-8")
    observation_path = tmp_path / "observation.json"
    observation_path.write_text(
        json.dumps(
            {
                "trial_id": "trial-review-packet",
                "task_id": "EGO-FS-100",
                "trial_days": 3,
                "observed_no_unapproved_side_effects": True,
                "observed_no_unapproved_memory_writes": True,
                "sessions": [
                    {
                        "session_id": "day1-draft",
                        "day": 1,
                        "transcript_paths": [str(transcript_path)],
                        "dimension_verdicts": {},
                        "requires_human_review": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    packet = lifestyle.write_review_packet(
        observation_path,
        tmp_path / "packet",
        excerpt_chars=3,
    )

    excerpt = packet["review_required_sessions"][0]["evidence_excerpts"]["transcripts"][0]
    assert excerpt["char_count"] == 6
    assert excerpt["excerpt"] == "abc"
    assert excerpt["truncated"] is True


def test_lifestyle_trial_review_packet_empty_when_no_sessions_require_review(tmp_path):
    observation_path = tmp_path / "observation.json"
    observation_path.write_text(
        json.dumps(
            {
                "trial_id": "trial-reviewed",
                "task_id": "EGO-FS-100",
                "trial_days": 3,
                "observed_no_unapproved_side_effects": True,
                "observed_no_unapproved_memory_writes": True,
                "sessions": [
                    {
                        "session_id": "day1-reviewed",
                        "day": 1,
                        "dimension_verdicts": {
                            dimension: "pass" for dimension in lifestyle.REQUIRED_DIMENSIONS
                        },
                        "requires_human_review": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    packet = lifestyle.write_review_packet(observation_path, tmp_path / "packet")

    assert packet["review_required_session_count"] == 0
    assert packet["review_required_sessions"] == []
    assert packet["current_review_status"] == "functional_subject_lifestyle_trial_review_pass"
