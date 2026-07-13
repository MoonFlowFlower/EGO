from __future__ import annotations

import copy
import importlib.util
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


def live_state() -> dict:
    return verify.load_program_state()


def error_text(state: dict) -> str:
    errors, _ = verify.validate_route_guard(state)
    return "\n".join(errors)


def lineage_record(state: dict, lineage_id: str) -> dict:
    return next(
        record
        for record in state["route_guard"]["lineage_inventory"]["records"]
        if record["lineage_id"] == lineage_id
    )


def test_live_route_guard_and_callable_lineage_inventory_pass() -> None:
    state = live_state()
    errors, details = verify.validate_route_guard(state)

    assert errors == []
    assert details["route_fingerprint"] == state["route_guard"]["route_fingerprint"]
    assert details["lineage_inventory"]["discovered_count"] == 9
    assert details["lineage_inventory"]["disposed_count"] == 9
    assert details["lineage_inventory"]["undisposed_count"] == 0


def test_removing_supersession_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["authority_state"]["old_route_8692"]["disposition"] = "ACTIVE"

    assert "supersession disposition is absent" in error_text(state)


def test_restoring_m1_authorization_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["authority_state"]["old_route_8692"]["m1"] = "AUTHORIZED"

    assert "milestone m1 is not cancelled" in error_text(state)


def test_egodesktop_successor_dependency_activation_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["authority_state"]["egodesktop"]["successor_dependency"] = True

    assert "EgoDesktop archive authority state is not fail-closed" in error_text(state)


def test_science_successor_registration_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["authorizations"]["science_successor_registration"] = True

    assert "all route_guard authorizations must remain false" in error_text(state)


def test_undisposed_lineage_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    record = lineage_record(state, "outcome_utility_closure")
    record["disposition"] = "UNDISPOSED"
    state["route_guard"]["lineage_inventory"]["disposed_count"] = 8
    state["route_guard"]["lineage_inventory"]["undisposed_count"] = 1

    assert "prior lineage inventory contains an undisposed lineage" in error_text(state)


def test_null_audit_ref_cannot_enable_pilot1_successor_use() -> None:
    state = copy.deepcopy(live_state())
    record = lineage_record(state, "pilot_1_repair")
    assert record["audit_ref"] is None
    record["successor_use"]["positive_control"] = "ENABLED"

    assert "cannot be enabled for successor use while audit_ref is null" in error_text(state)


def test_unbound_allowed_action_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["allowed_action_binding"]["allowed_next_action_ids"].append("bank_UNBOUND_CARD")

    assert "must contain only the Card 2 banking action" in error_text(state)


def test_itl_pin_mutation_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["science_source_pins"]["closure"]["git_blob_oid"] = "0" * 40

    assert "science_source_pins.closure git blob OID mismatch" in error_text(state)


def test_nonempty_authorized_implementation_target_is_rejected() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["authorizations"]["authorized_implementation_targets"] = ["EgoDesktop/"]

    assert "route_guard authorized implementation targets must be empty" in error_text(state)


def test_renderer_source_cannot_promote_virtualcat_egodesktop_active_route() -> None:
    state = copy.deepcopy(live_state())
    surface = next(
        row
        for row in state["route_guard"]["route_views"]["current_surfaces"]
        if row["surface"] == "superseded_8692_route"
    )
    surface["surface"] = "canonical_mechanism_successor"
    surface["role"] = "Selected default-off successor route: K0, VirtualCat, EgoDesktop."

    assert "still promotes VirtualCat/EgoDesktop as an active successor route" in error_text(state)


def test_archived_program_state_cannot_render_supporting_active_sink() -> None:
    state = copy.deepcopy(live_state())
    state["route_guard"]["route_views"]["task_routes"][
        "ego-canonical-mechanism-integration-001a"
    ]["lane"] = "supporting_active"

    assert "former 8692 task sink is not closed_evidence" in error_text(state)


def test_capability_verdict_cannot_be_upgraded_to_learning_or_mechanism_evidence() -> None:
    state = copy.deepcopy(live_state())
    lineage_record(state, "pilot_1_repair")["evidence_ceiling"] = "learning_mechanism_evidence"

    assert "capability verdict was upgraded" in error_text(state)
