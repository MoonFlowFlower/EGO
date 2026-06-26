from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "egodesktop-joi-real-loop-g-ablation-backend-trace-snapshot-v0"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_006_claim_hygiene_uses_collect_only_snapshot_not_replay_conformance():
    surfaces = [
        TASK_DIR / "SPEC.md",
        TASK_DIR / "STATUS.md",
        TASK_DIR / "CLAUDE_REVIEW_PACKET_006_TO_007.md",
        ROOT / "Tasks" / "TASK_BOARD.yaml",
    ]
    joined = "\n".join(_read(path) for path in surfaces)
    lowered = joined.lower()

    assert "collect conformant" not in lowered
    assert "conformant real desktop backend trace snapshot rows" not in lowered
    assert "schema_valid_collect_only_snapshot" in joined
    assert "does not satisfy 001C section 12" in joined


def test_006_review_repair_freezes_d_field_precondition_before_007_scoring():
    precondition = _read(TASK_DIR / "D_FIELD_REPLAY_PRECONDITION_007.md")

    assert "D_FIELD_FREEZE_STATUS: not_satisfied_for_scoring" in precondition
    assert "non_llm_d_fields" in precondition
    assert "complete_state_serialized: false" in precondition
    assert "complete_observation_serialized: false" in precondition
    assert "No >=007 scoring run may execute" in precondition


def test_006_minimal_surface_and_closeout_scope_are_attached_for_re_review():
    minimal_surface = _read(TASK_DIR / "MINIMAL_SURFACE_006.md")
    closeout = _read(TASK_DIR / "CLOSEOUT_SCOPE_READBACK_006A.md")

    assert "Instrument, do not fork" in minimal_surface
    assert "reuse 003/004 trace_rows.jsonl" in minimal_surface
    assert "No baseline, attribution, route-B, readiness" in minimal_surface
    assert "python scripts\\codex_session_guard.py --mutation-scope" in closeout
    assert "mutation_scope: loaded" in closeout
