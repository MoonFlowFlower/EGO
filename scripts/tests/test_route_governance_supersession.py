from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CODEX_DIR = ROOT / "scripts" / "codex"
if str(CODEX_DIR) not in sys.path:
    sys.path.insert(0, str(CODEX_DIR))

MODULE_PATH = CODEX_DIR / "verify_route_convergence.py"
spec = importlib.util.spec_from_file_location("verify_route_convergence_supersession", MODULE_PATH)
verify = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = verify
spec.loader.exec_module(verify)
guard = verify.route_sync_guard


def live_state() -> dict:
    return verify.load_program_state()


def historical_v4_state() -> dict:
    return verify._historical_visible_life_core_snapshot(live_state())  # noqa: SLF001


def error_text(state: dict) -> str:
    errors, _ = verify.validate_route_guard(state)
    return "\n".join(errors)


def route_state(state: dict) -> dict:
    return state["route_guard"]["transcribed_itl"]["route_state"]


def closure(state: dict) -> dict:
    return state["route_guard"]["transcribed_itl"]["closure"]


def product(state: dict) -> dict:
    return state["route_guard"].get("predecessor_product_authority", state["route_guard"]["product_authority"])


def v1_product(state: dict) -> dict:
    return state["route_guard"]["v1_ready_authority"]


def test_historical_v4_snapshot_preserves_closed_structural_boundary() -> None:
    state = historical_v4_state()
    route_guard = state["route_guard"]
    card2 = route_state(state)
    product_core = product(state)

    assert route_guard["schema_version"] == "ego.route_guard.v4"
    assert route_guard["route_revision_id"] == guard.VISIBLE_LIFE_CORE_ROUTE_REVISION
    assert route_guard["route_fingerprint"] == verify.compute_route_fingerprint(state)
    assert card2["allowed_next_actions"] == ["run_route_state_machine_validation"]
    assert card2["authorizations"]
    assert all(value is False for value in card2["authorizations"].values())
    assert card2["authorized_implementation_targets"] == []
    assert product_core["enabled"] is False
    assert product_core["default_enabled"] is False
    assert product_core["mainline_connected"] is False
    assert product_core["runtime_mainline_connected"] is False
    assert product_core["runtime_authority"] == "none"
    assert product_core["science_weight"] == 0
    assert product_core["authorized_implementation_targets"] == []
    assert product_core["allowed_next_actions"] == [
        guard.VISIBLE_LIFE_CORE_DRAFT_V1_ACTION_ID,
        "run_route_state_machine_validation",
    ]


def test_live_v6_route_is_exact_phase_c_v2_default_off_authority() -> None:
    state = live_state()
    errors, details = verify.validate_route_guard(state)

    assert errors == []
    assert details["route_fingerprint"] == state["route_guard"]["route_fingerprint"]
    assert details["phase_c_v2_authority"]["status"] == "pass"
    assert details["authorized_implementation_targets"] == guard.R1_VISUAL_IMPLEMENTATION_TARGETS


def test_itl_closure_blob_pin_mutation_is_rejected() -> None:
    state = copy.deepcopy(historical_v4_state())
    state["route_guard"]["authority_source"]["objects"]["closure"]["git_blob_oid"] = "0" * 40

    assert "itl_object_oid_mismatch:closure" in error_text(state)


def test_itl_product_axis_blob_pin_mutation_is_rejected() -> None:
    state = copy.deepcopy(historical_v4_state())
    state["route_guard"]["authority_source"]["objects"]["product_axis_state"]["git_blob_oid"] = "0" * 40

    errors = error_text(state)
    assert "itl_object_oid_mismatch:product_axis_state" in errors
    assert "visible_life_core_itl_pin_mismatch:product_axis_state" in errors


def test_transcribed_closed_route_mutation_is_rejected() -> None:
    state = copy.deepcopy(historical_v4_state())
    route_state(state)["implementation_authorized"] = True

    errors = error_text(state)
    assert "visible_life_route_state_transcription_mismatch" in errors
    assert "implementation_authorized must remain false" in errors


def test_transcribed_closure_authority_mutation_is_rejected() -> None:
    state = copy.deepcopy(historical_v4_state())
    closure(state)["authorizations"]["runtime"] = True

    errors = error_text(state)
    assert "visible_life_closure_transcription_mismatch" in errors
    assert "transcribed Card2 closure packet grants authority" in errors


def test_crosswalk_leaf_omission_is_rejected(monkeypatch) -> None:
    state = historical_v4_state()
    path = ROOT / state["route_guard"]["closure_crosswalk"]["path"]
    mutated = json.loads(path.read_text(encoding="utf-8"))
    mutated["entries"].pop()
    original_reader = guard._read_json_file

    def read_mutated(candidate: Path):
        if candidate == path:
            return mutated, None
        return original_reader(candidate)

    monkeypatch.setattr(guard, "_read_json_file", read_mutated)
    result = guard.validate_visible_life_closure_crosswalk(state)

    assert result["status"] == "fail"
    assert "visible_life_crosswalk_callable_recompute_mismatch" in result["errors"]
    assert "visible_life_crosswalk_leaf_omitted" in result["errors"]


def test_product_authority_crosswalk_leaf_omission_is_rejected(monkeypatch) -> None:
    state = historical_v4_state()
    path = ROOT / state["route_guard"]["product_authority_crosswalk"]["path"]
    mutated = json.loads(path.read_text(encoding="utf-8"))
    mutated["entries"].pop()
    original_reader = guard._read_json_file

    def read_mutated(candidate: Path):
        if candidate == path:
            return mutated, None
        return original_reader(candidate)

    monkeypatch.setattr(guard, "_read_json_file", read_mutated)
    result = guard.validate_visible_life_core_authority_crosswalk(state)

    assert result["status"] == "fail"
    assert "visible_life_core_crosswalk_callable_recompute_mismatch" in result["errors"]
    assert "visible_life_core_crosswalk_leaf_omitted" in result["errors"]


def test_closed_card2_action_cannot_be_resurrected() -> None:
    state = copy.deepcopy(historical_v4_state())
    route_state(state)["allowed_next_actions"].append(guard.CARD2_BANK_ACTION_ID)

    assert "closed Card2 route exposes a non-validation action" in error_text(state)


def test_product_target_expansion_is_rejected() -> None:
    state = copy.deepcopy(historical_v4_state())
    product(state)["authorized_implementation_targets"].append("EgoDesktop/forbidden.py")

    assert "visible_life_core_targets_must_be_empty" in error_text(state)


def test_nonzero_product_science_weight_is_rejected() -> None:
    state = copy.deepcopy(historical_v4_state())
    product(state)["science_weight"] = 1
    product(state)["science_firewall"]["science_weight"] = 1

    errors = error_text(state)
    assert "visible_life_core_science_weight_mismatch" in errors
    assert "visible_life_core_science_firewall_mismatch" in errors


def test_product_runtime_or_mainline_authority_is_rejected() -> None:
    state = copy.deepcopy(historical_v4_state())
    product(state)["authorizations"]["runtime"] = True
    product(state)["mainline_connected"] = True

    errors = error_text(state)
    assert "visible_life_core_authorizations_mismatch" in errors
    assert "visible_life_core_mainline_connected_mismatch" in errors


def test_visible_life_exact_path_policy_rejects_egodesktop_and_extra_file() -> None:
    result = guard.validate_visible_life_action_paths(
        changed_paths=[*guard.VISIBLE_LIFE_TARGETS, "EgoDesktop/forbidden.py"],
        scope_allowed_paths=guard.VISIBLE_LIFE_TARGETS,
        require_complete_set=True,
    )

    assert result["status"] == "fail"
    assert "visible_life_changed_path_outside_exact_six" in result["errors"]
    assert "visible_life_forbidden_surface_path" in result["errors"]


def test_visible_life_exact_path_policy_rejects_incomplete_set() -> None:
    result = guard.validate_visible_life_action_paths(
        changed_paths=guard.VISIBLE_LIFE_TARGETS[:-1],
        scope_allowed_paths=guard.VISIBLE_LIFE_TARGETS,
        require_complete_set=True,
    )

    assert "visible_life_changed_path_set_incomplete" in result["errors"]


def test_visible_life_predecessor_must_remain_closed_evidence() -> None:
    state = copy.deepcopy(historical_v4_state())
    state["route_guard"]["route_views"]["task_routes"][
        "ego-visible-life-proxy-v0-route-replacement-001a"
    ]["lane"] = "active_default"

    assert "visible-life predecessor task must be closed evidence" in error_text(state)


def test_visible_life_core_is_the_sole_product_development_core() -> None:
    state = copy.deepcopy(historical_v4_state())
    assert product(state)["product_development_core_lineage"] == "SOLE_VISIBLE_LIFE_PRODUCT_DEVELOPMENT_LINEAGE"
    assert "product_development_mainline" not in product(state)
    product(state)["core_registry"]["parallel_visible_life"] = "other_core"

    assert "visible_life_core_registry_mismatch" in error_text(state)


def test_itl_and_ego_trigger_evidence_cannot_be_conflated() -> None:
    state = copy.deepcopy(historical_v4_state())
    product(state)["real_trigger_evidence"] = "BANKED_RECOMPUTING_PRODUCT_TRIGGER"

    assert "visible_life_core_real_trigger_evidence_mismatch" in error_text(state)


def test_shortened_v1_action_is_rejected() -> None:
    state = copy.deepcopy(historical_v4_state())
    product(state)["allowed_next_actions"][0] = "draft_EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A"

    assert "visible_life_core_allowed_actions_mismatch" in error_text(state)


def test_runtime_mainline_cannot_be_smuggled_through_product_core() -> None:
    state = copy.deepcopy(historical_v4_state())
    product(state)["runtime_mainline_connected"] = True

    assert "visible_life_core_runtime_mainline_connected_mismatch" in error_text(state)


def test_ambiguous_product_development_mainline_field_is_rejected() -> None:
    state = copy.deepcopy(historical_v4_state())
    product(state)["product_development_mainline"] = True

    assert "visible_life_core_ambiguous_mainline_field_forbidden" in error_text(state)


def test_consumed_v0_implementation_action_cannot_be_reopened() -> None:
    state = copy.deepcopy(historical_v4_state())
    product(state)["predecessor_action"]["state"] = "AUTHORIZED_NOT_STARTED"

    assert "visible_life_core_predecessor_action_not_consumed" in error_text(state)


def test_v1_implementation_is_not_authorized() -> None:
    state = copy.deepcopy(historical_v4_state())
    product(state)["authorizations"]["implementation"] = True
    product(state)["authorized_implementation_targets"] = ["labs/ego_life_playground_v1/engine.py"]

    errors = error_text(state)
    assert "visible_life_core_authorizations_mismatch" in errors
    assert "visible_life_core_targets_must_be_empty" in errors


def test_v4_route_rejects_failed_callable_core_evidence(monkeypatch) -> None:
    state = historical_v4_state()
    monkeypatch.setattr(
        guard,
        "validate_visible_life_core_evidence",
        lambda *_args, **_kwargs: {
            "status": "fail",
            "errors": ["positive_control_corruption_detected"],
        },
    )

    assert "visible_life_core_evidence:positive_control_corruption_detected" in error_text(state)


def test_v4_main_readback_uses_product_authority_actions() -> None:
    state = historical_v4_state()
    route_guard = state["route_guard"]

    assert verify.route_allowed_next_action_ids(route_guard) == product(state)["allowed_next_actions"]
    assert verify.route_allowed_next_action_ids(route_guard) != route_state(state)["allowed_next_actions"]


def test_phase_c_v2_live_authority_is_exact_and_default_off() -> None:
    state = live_state()
    authority = state["route_guard"]["v2_authority"]

    assert state["route_guard"]["route_revision_id"] == guard.PHASE_C_V2_ROUTE_REVISION
    assert authority["implementation_authorized"] is True
    assert authority["authorized_implementation_targets"] == guard.R1_VISUAL_IMPLEMENTATION_TARGETS
    assert authority["allowed_next_actions"] == [guard.PHASE_C_V2_VALIDATION_ACTION_ID]
    for key, expected in guard.PHASE_C_V2_CLOSED_SWITCHES.items():
        assert authority[key] == expected
    assert authority["worktree_authority"] == guard._r1_visual_worktree_authority_projection()  # noqa: SLF001
    assert authority["worktree_authority"]["linked_v2_rollback_reference"]["frozen"] is True


def test_phase_c_v2_source_pin_mutation_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["authority_source"]["objects"]["v2_state"]["git_blob_oid"] = "0" * 40

    errors, _ = verify.validate_route_guard(state)

    assert "Phase-C V2 authority state object pin mismatch" in errors


def test_phase_c_v2_exact_ordered_target_drift_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    targets = state["route_guard"]["v2_authority"]["authorized_implementation_targets"]
    targets[0], targets[1] = targets[1], targets[0]

    errors, _ = verify.validate_route_guard(state)

    assert "Phase-C V2 program projection canonical bytes mismatch" in errors


def test_phase_c_v2_closed_switch_drift_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    authority = state["route_guard"]["v2_authority"]
    authority["enabled"] = True
    authority["runtime_authority"] = "candidate"
    authority["science_weight"] = 1
    authority["remote_anchor"] = True

    errors, _ = verify.validate_route_guard(state)

    assert "Phase-C V2 program projection canonical bytes mismatch" in errors


def test_phase_c_v2_dirty_main_cannot_be_promoted_to_live_authority() -> None:
    state = copy.deepcopy(live_state())
    worktrees = state["route_guard"]["v2_authority"]["worktree_authority"]
    worktrees["negative_checkpoint"]["live_authority"] = True

    errors, _ = verify.validate_route_guard(state)

    assert "Phase-C V2 program projection canonical bytes mismatch" in errors


def test_phase_c_v2_successor_branch_cannot_lose_sole_authority_binding() -> None:
    state = copy.deepcopy(live_state())
    successor = state["route_guard"]["v2_authority"]["worktree_authority"][
        "active_v2_development_authority"
    ]
    successor["branch"] = "main"
    successor["sole"] = False

    errors, _ = verify.validate_route_guard(state)

    assert "Phase-C V2 program projection canonical bytes mismatch" in errors


def test_phase_c_v2_main_readback_uses_exact_implementation_actions() -> None:
    state = live_state()
    route_guard = state["route_guard"]

    assert verify.route_allowed_next_action_ids(route_guard) == [guard.PHASE_C_V2_VALIDATION_ACTION_ID]
