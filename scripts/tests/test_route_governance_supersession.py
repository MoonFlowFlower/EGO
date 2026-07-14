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


def test_live_route_guard_crosswalk_and_callable_lineage_pass() -> None:
    state = live_state()
    errors, details = verify.validate_route_guard(state)

    assert errors == []
    assert details["route_fingerprint"] == state["route_guard"]["route_fingerprint"]
    assert details["field_crosswalk"]["status"] == "pass"
    assert details["lineage_inventory"]["status"] == "pass"
    assert details["lineage_inventory"]["discovered_count"] == 9
    assert details["lineage_inventory"]["undisposed_count"] == 0


def test_itl_route_blob_pin_mutation_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["authority_source"]["objects"]["route_state"]["git_blob_oid"] = "0" * 40

    assert "itl_object_oid_mismatch:route_state" in error_text(state)


def test_transcribed_route_field_mutation_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    route_state(state)["implementation_authorized"] = True

    errors = error_text(state)
    assert "route_state_transcription_mismatch" in errors
    assert "implementation_authorized must remain false" in errors


def test_crosswalk_leaf_omission_positive_control_is_rejected(monkeypatch) -> None:
    state = live_state()
    path = ROOT / state["route_guard"]["field_crosswalk"]["path"]
    mutated = json.loads(path.read_text(encoding="utf-8"))
    mutated["entries"].pop()
    original_reader = guard._read_json_file

    def read_mutated(candidate: Path):
        if candidate == path:
            return mutated, None
        return original_reader(candidate)

    monkeypatch.setattr(guard, "_read_json_file", read_mutated)
    result = guard.validate_field_crosswalk(state)

    assert result["status"] == "fail"
    assert "field_crosswalk_callable_recompute_mismatch" in result["errors"]


def test_lineage_omission_positive_control_is_rejected(monkeypatch) -> None:
    state = live_state()
    path = ROOT / state["route_guard"]["lineage_universe"]["path"]
    mutated = json.loads(path.read_text(encoding="utf-8"))
    mutated["records"].pop()
    original_reader = guard._read_json_file

    def read_mutated(candidate: Path):
        if candidate == path:
            return mutated, None
        return original_reader(candidate)

    monkeypatch.setattr(guard, "_read_json_file", read_mutated)
    result = guard.validate_lineage_universe(state)

    assert result["status"] == "fail"
    assert "lineage_universe_callable_recompute_mismatch" in result["errors"]


def test_card2_action_policy_rejects_product_runtime_path() -> None:
    result = guard.validate_card2_action_paths(
        route_state=route_state(live_state()),
        changed_paths=["EgoOperator/agent_base.py"],
        scope_loaded=True,
        scope_allowed_paths=[guard.CARD2_TASK_PREFIX],
    )

    assert result["status"] == "fail"
    assert result["inferred_execution_paths"] == ["EgoOperator/agent_base.py"]
    assert "card2_execution_inferred_from_changed_paths" in result["errors"]


def test_card2_action_policy_rejects_missing_scope() -> None:
    result = guard.validate_card2_action_paths(
        route_state=route_state(live_state()),
        changed_paths=[f"{guard.CARD2_TASK_PREFIX}STAGE_CARD.md"],
        scope_loaded=False,
        scope_allowed_paths=[],
    )

    assert result["status"] == "fail"
    assert "missing_mutation_scope_for_card2_action" in result["errors"]


def test_nonempty_implementation_targets_are_rejected() -> None:
    state = copy.deepcopy(live_state())
    route_state(state)["authorized_implementation_targets"] = ["EgoDesktop/"]

    assert "authorized implementation targets must remain empty" in error_text(state)


def test_nonzero_science_weight_and_old_s0x_are_rejected() -> None:
    state = copy.deepcopy(live_state())
    route_state(state)["science_firewall"]["card2_science_weight"] = 1
    route_state(state)["science_firewall"]["satisfies_old_s0x"] = True

    assert "zero-science firewall drifted" in error_text(state)


def test_card2_execution_and_science_authorization_are_rejected() -> None:
    state = copy.deepcopy(live_state())
    route_state(state)["action_dependencies"][guard.CARD2_BANK_ACTION_ID]["execution_authorized"] = True
    route_state(state)["authorizations"]["science_successor"] = True

    errors = error_text(state)
    assert "Card 2 execution authorization must remain false" in errors
    assert "ITL authorizations transcription or fail-closed values drifted" in errors


def test_self_authored_second_control_plane_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["allowed_action_binding"] = {"allowed_next_action_ids": [guard.CARD2_BANK_ACTION_ID]}

    assert "self-authored route authority or lineage control plane remains present" in error_text(state)


def test_committed_itl_claim_ceiling_is_not_upgradeable() -> None:
    state = copy.deepcopy(live_state())
    route_state(state)["claim_ceiling"]["max"] = "mechanism validity"

    assert "ITL claim ceiling transcription drifted" in error_text(state)
