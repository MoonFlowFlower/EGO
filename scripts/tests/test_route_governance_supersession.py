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


def test_historical_v4_route_remains_callable_and_closed() -> None:
    state = historical_v4_state()
    errors, details = verify.validate_route_guard(state)

    assert errors == []
    assert details["route_fingerprint"] == state["route_guard"]["route_fingerprint"]
    assert details["closure_crosswalk"]["status"] == "pass"
    assert details["product_core_authority"]["status"] in {"pass", "fail"}


def test_live_v5_route_has_only_phase_c_receipt_pending_before_review() -> None:
    state = live_state()
    errors, details = verify.validate_route_guard(state)

    assert set(errors).issubset(
        {
            "V1 READY product authority: "
            "v1_ready_red_review:v1_ready_candidate_red_receipt_unavailable"
        }
    )
    assert details["route_fingerprint"] == state["route_guard"]["route_fingerprint"]
    assert details["v1_ready_product_authority"]["source"]["status"] == "pass"
    assert details["authorized_implementation_targets"] == guard.V1_READY_IMPLEMENTATION_TARGETS


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


def test_v1_ready_live_authority_is_exact_and_default_off() -> None:
    state = live_state()
    result = guard.validate_v1_ready_product_authority(state, require_review=False)

    assert result["status"] == "pass", result["errors"]
    assert state["route_guard"]["route_revision_id"] == guard.V1_READY_ROUTE_REVISION
    assert v1_product(state)["implementation_authorized"] is True
    assert v1_product(state)["authorized_implementation_targets"] == guard.V1_READY_IMPLEMENTATION_TARGETS
    assert v1_product(state)["allowed_next_actions"] == [
        guard.V1_READY_IMPLEMENT_ACTION_ID,
        "run_route_state_machine_validation",
    ]
    assert v1_product(state)["enabled"] is False
    assert v1_product(state)["default_enabled"] is False
    assert v1_product(state)["mainline_connected"] is False
    assert v1_product(state)["runtime_mainline_connected"] is False
    assert v1_product(state)["runtime_authority"] == "none"
    assert v1_product(state)["science_weight"] == 0
    assert v1_product(state)["remote_anchor"] is False


def test_v1_ready_source_pin_mutation_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["authority_source"]["objects"]["v1_state"]["git_blob_oid"] = "0" * 40

    result = guard.validate_v1_ready_product_authority(state, require_review=False)

    assert result["status"] == "fail"
    assert "v1_ready_itl_pin_mismatch:v1_state" in result["errors"]
    assert "v1_ready_source:itl_object_oid_mismatch:v1_state" in result["errors"]


def test_v1_ready_crosswalk_leaf_omission_is_rejected(monkeypatch) -> None:
    state = live_state()
    path = ROOT / state["route_guard"]["v1_ready_authority_crosswalk"]["path"]
    mutated = json.loads(path.read_text(encoding="utf-8"))
    mutated["entries"].pop()
    original_reader = guard._read_json_file

    def read_mutated(candidate: Path):
        if candidate == path:
            return mutated, None
        return original_reader(candidate)

    monkeypatch.setattr(guard, "_read_json_file", read_mutated)
    result = guard.validate_v1_ready_authority_crosswalk(state)

    assert result["status"] == "fail"
    assert "v1_ready_crosswalk_callable_recompute_mismatch" in result["errors"]
    assert "v1_ready_crosswalk_leaf_omitted" in result["errors"]


def test_v1_ready_exact_ordered_target_drift_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    targets = v1_product(state)["authorized_implementation_targets"]
    targets[0], targets[1] = targets[1], targets[0]

    result = guard.validate_v1_ready_product_authority(state, require_review=False)

    assert "v1_ready_authorized_implementation_targets_mismatch" in result["errors"]


def test_v1_ready_runtime_science_or_remote_drift_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    authority = v1_product(state)
    authority["enabled"] = True
    authority["runtime_authority"] = "candidate"
    authority["science_weight"] = 1
    authority["remote_anchor"] = True

    errors = guard.validate_v1_ready_product_authority(state, require_review=False)["errors"]

    assert "v1_ready_enabled_mismatch" in errors
    assert "v1_ready_runtime_authority_mismatch" in errors
    assert "v1_ready_science_weight_mismatch" in errors
    assert "v1_ready_remote_anchor_mismatch" in errors


def test_v1_ready_three_trigger_fields_cannot_be_conflated() -> None:
    state = copy.deepcopy(live_state())
    triggers = state["route_guard"]["product_trigger_evidence"]
    triggers["v1_local_product"] = triggers["ego_v0_local_product"]

    errors = guard.validate_v1_ready_product_authority(state, require_review=False)["errors"]

    assert "v1_ready_trigger_evidence_mismatch" in errors


def test_v1_ready_pointer_stale_current_successor_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["authority_state"]["old_route_8692"]["current_reader_disposition"] = (
        "CURRENT_SELECTED_SUCCESSOR"
    )

    errors = guard.validate_v1_ready_product_authority(state, require_review=False)["errors"]

    assert "v1_ready_old_route_8692_pointer_mismatch" in errors


def test_v1_ready_egodesktop_stays_archive_and_egooperator_stays_default() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["authority_state"]["egodesktop"]["archive_state"] = "ACTIVE_SUCCESSOR"
    state["route_guard"]["authority_state"]["ego_operator"]["active_default"] = False

    errors = guard.validate_v1_ready_product_authority(state, require_review=False)["errors"]

    assert "v1_ready_egodesktop_archive_pointer_mismatch" in errors
    assert "v1_ready_ego_operator_default_mismatch" in errors


def test_v1_ready_main_readback_uses_implementation_actions() -> None:
    state = live_state()
    route_guard = state["route_guard"]

    assert verify.route_allowed_next_action_ids(route_guard) == [
        guard.V1_READY_IMPLEMENT_ACTION_ID,
        "run_route_state_machine_validation",
    ]


def test_v1_ready_pointer_scanner_positive_control_rejects_stale_current_claim() -> None:
    contents = {
        path: (
            f"{guard.V1_READY_POINTER_AUTHORITY_MARKER}\n"
            f"{guard.V1_READY_POINTER_ARCHIVE_MARKER}\n"
        )
        for path in guard.V1_READY_STALE_POINTER_PATHS
    }
    target = guard.V1_READY_STALE_POINTER_PATHS[0]
    contents[target] = "Current selected successor is K0 -> VirtualCat -> EgoDesktop.\n" + contents[target]

    errors = guard.validate_v1_ready_pointer_texts(contents)

    assert f"v1_ready_pointer_stale_current_claim_before_authority:{target}" in errors
