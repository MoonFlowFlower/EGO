from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CODEX_DIR = ROOT / "scripts" / "codex"
if str(CODEX_DIR) not in sys.path:
    sys.path.insert(0, str(CODEX_DIR))

MODULE_PATH = CODEX_DIR / "verify_route_convergence.py"
spec = importlib.util.spec_from_file_location("verify_route_convergence_r1_visual", MODULE_PATH)
verify = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = verify
spec.loader.exec_module(verify)
guard = verify.route_sync_guard


def live_state() -> dict:
    return verify.load_program_state()


def test_live_v7_route_exposes_only_action_repair_and_exact_targets() -> None:
    state = live_state()
    errors, details = verify.validate_route_guard(state)

    assert errors == []
    route_guard = state["route_guard"]
    assert route_guard["schema_version"] == "ego.route_guard.v7"
    assert route_guard["route_revision_id"] == guard.R1_VISUAL_ROUTE_REVISION
    assert details["route_fingerprint"] == route_guard["route_fingerprint"]
    assert details["authorized_implementation_targets"] == guard.R1_VISUAL_IMPLEMENTATION_TARGETS
    assert verify.route_allowed_next_action_ids(route_guard) == [
        guard.R1_VISUAL_IMPLEMENT_ACTION_ID,
        guard.R1_VISUAL_VALIDATION_ACTION_ID,
    ]


def test_live_v7_route_rejects_target_switch_source_and_old_action_drift() -> None:
    state = live_state()

    target_drift = copy.deepcopy(state)
    target_drift["route_guard"]["v2_authority"]["authorized_implementation_targets"].reverse()
    assert "Phase-C V2 program projection canonical bytes mismatch" in verify.validate_route_guard(target_drift)[0]

    switch_drift = copy.deepcopy(state)
    switch_drift["route_guard"]["v2_authority"]["background_dispatch"] = True
    assert "Phase-C V2 program projection canonical bytes mismatch" in verify.validate_route_guard(switch_drift)[0]

    source_drift = copy.deepcopy(state)
    source_drift["route_guard"]["authority_source"]["objects"]["v2_state"]["git_blob_oid"] = "0" * 40
    assert "Phase-C V2 authority state object pin mismatch" in verify.validate_route_guard(source_drift)[0]

    action_drift = copy.deepcopy(state)
    action_drift["route_guard"]["v2_authority"]["allowed_next_actions"].insert(
        0, guard.PHASE_C_V2_LEGACY_IMPLEMENT_ACTION_ID
    )
    assert "Phase-C V2 program projection canonical bytes mismatch" in verify.validate_route_guard(action_drift)[0]


def test_live_v7_phase_a_scope_positive_controls_are_fail_closed() -> None:
    scope = guard.build_r1_visual_phase_a_scope()
    assert guard.validate_r1_visual_phase_a_scope_payload(scope) == []

    for forbidden in (
        "labs/ego_life_playground_v0/app.py",
        "labs/ego_life_playground_v0/store.py",
        "scripts/run_ego_life_playground_v0.py",
        "docs/PROGRAM_STATE_UNIFIED.yaml",
    ):
        hostile = copy.deepcopy(scope)
        hostile["authorized_implementation_targets"] = [
            *guard.R1_VISUAL_IMPLEMENTATION_TARGETS,
            forbidden,
        ]
        assert "r1_visual_phase_a_targets_mismatch" in guard.validate_r1_visual_phase_a_scope_payload(hostile)
