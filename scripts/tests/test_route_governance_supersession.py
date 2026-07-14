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


def error_text(state: dict) -> str:
    errors, _ = verify.validate_route_guard(state)
    return "\n".join(errors)


def route_state(state: dict) -> dict:
    return state["route_guard"]["transcribed_itl"]["route_state"]


def closure(state: dict) -> dict:
    return state["route_guard"]["transcribed_itl"]["closure"]


def product(state: dict) -> dict:
    return state["route_guard"]["product_authority"]


def test_live_v3_route_has_only_the_expected_pre_receipt_blocker() -> None:
    state = live_state()
    errors, details = verify.validate_route_guard(state)

    assert errors in ([], ["Phase-A Red review: candidate_red_review_record_unavailable"])
    assert details["route_fingerprint"] == state["route_guard"]["route_fingerprint"]
    assert details["closure_crosswalk"]["status"] == "pass"
    assert details["product_authority"]["status"] == "pass"


def test_itl_closure_blob_pin_mutation_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["authority_source"]["objects"]["closure"]["git_blob_oid"] = "0" * 40

    assert "itl_object_oid_mismatch:closure" in error_text(state)


def test_transcribed_closed_route_mutation_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    route_state(state)["implementation_authorized"] = True

    errors = error_text(state)
    assert "visible_life_route_state_transcription_mismatch" in errors
    assert "implementation_authorized must remain false" in errors


def test_transcribed_closure_authority_mutation_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    closure(state)["authorizations"]["runtime"] = True

    errors = error_text(state)
    assert "visible_life_closure_transcription_mismatch" in errors
    assert "transcribed Card2 closure packet grants authority" in errors


def test_crosswalk_leaf_omission_is_rejected(monkeypatch) -> None:
    state = live_state()
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


def test_closed_card2_action_cannot_be_resurrected() -> None:
    state = copy.deepcopy(live_state())
    route_state(state)["allowed_next_actions"].append(guard.CARD2_BANK_ACTION_ID)

    assert "closed Card2 route exposes a non-validation action" in error_text(state)


def test_product_target_expansion_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    product(state)["authorized_implementation_targets"].append("EgoDesktop/forbidden.py")

    assert "visible_life_product_targets_mismatch" in error_text(state)


def test_nonzero_product_science_weight_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    product(state)["science_weight"] = 1
    product(state)["science_firewall"]["science_weight"] = 1

    errors = error_text(state)
    assert "visible_life_product_science_weight_mismatch" in errors
    assert "visible_life_product_science_firewall_mismatch" in errors


def test_product_runtime_or_mainline_authority_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    product(state)["authorizations"]["runtime"] = True
    product(state)["mainline_connected"] = True

    errors = error_text(state)
    assert "visible_life_product_authorizations_mismatch" in errors
    assert "visible_life_product_mainline_connected_mismatch" in errors


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


def test_visible_life_task_must_remain_parked() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["route_views"]["task_routes"][
        "ego-visible-life-proxy-v0-route-replacement-001a"
    ]["lane"] = "active_default"

    assert "visible-life task must remain parked and non-default" in error_text(state)
