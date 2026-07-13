#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from typing import Any

from route_convergence_common import (
    HYGIENE_RULES,
    REPO_HYGIENE_POLICY_PATH,
    REPO_SURFACE_MAP_PATH,
    TASK_LANE_INDEX_PATH,
    build_route_entries,
    load_program_state,
    render_repo_hygiene_policy,
    render_repo_surface_map,
    render_task_lane_index,
)


EXPECTED_K0_STATUS = (
    "foundation_engineering_accepted_bounded__old_science_route_operator_closed_without_science_adjudication__"
    "verifier_family_closed_invalid__independent_acceptance_unavailable__product_science_decoupled__"
    "all_authorizations_false__runtime_disabled__non_mainline"
)

FUTURE_PRODUCT_TASK_KEY = "ego-learned-outcome-kernel-capability-001a"
FUTURE_PRODUCT_STAGE_CARD_PATH = (
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/STAGE_CARD.md"
)
P1_TASK_CARD_PATH = (
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1_INSTRUMENT_TASK_CARD.md"
)
P1_TASK_CARD_BLOB = "26c53396c88de3a0c35494665085a3b6c298e56c"
P1_TASK_CARD_SHA256 = "93608561afcd4ab35abae5bf6257f1ad5b8a35b779e0bee0a03a238012724a95"
P1_INSTRUMENT_TARGETS = [
    "scripts/ego_learned_outcome_kernel_capability_preflight_001a/__init__.py",
    "scripts/ego_learned_outcome_kernel_capability_preflight_001a/contract.py",
    "scripts/ego_learned_outcome_kernel_capability_preflight_001a/workload.py",
    "scripts/ego_learned_outcome_kernel_capability_preflight_001a/oracles.py",
    "scripts/ego_learned_outcome_kernel_capability_preflight_001a/baselines.py",
    "scripts/ego_learned_outcome_kernel_capability_preflight_001a/metrics.py",
    "scripts/ego_learned_outcome_kernel_capability_preflight_001a/leakage.py",
    "scripts/ego_learned_outcome_kernel_capability_preflight_001a/replay.py",
    "scripts/ego_learned_outcome_kernel_capability_preflight_001a/producer.py",
    "scripts/run_ego_learned_outcome_kernel_capability_preflight_001a.py",
    "tests/test_ego_learned_outcome_kernel_capability_preflight_001a.py",
]
FORMAL_ARTIFACT_PATH = "artifacts/ego_learned_outcome_kernel_capability_preflight_001a"
P1_AUTHORIZATION_COMMIT = "fdbc5dea725d635ee21ba7490d7b5b03b3ce11cc"
P0_PREREG_COMMIT = "ff1ab23e1db303a882cec17374b9ea3903fe03c6"
C1_AUDIT_COMMIT = "6f49f80d5877d5b0920d17222d5455ed1d3dd86b"
C1_AUDIT_PARENT = "8365911743aadf1ee508fb42336cfb0a9710aaed"
C1_LEDGER_BLOB = "7634cdccd69d25277bfeaab7e87865fd9e5bff0d"
P1R0_SOURCE_COMMIT = C1_AUDIT_PARENT
P1R0_BLUEPRINT_PATH = (
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/"
    "P1R0_EXECUTABLE_DESIGN_BLUEPRINT.json"
)
P1R0_BLUEPRINT_BLOB = "385808733e8f1c6bd17cc8733e1a9ff342d9c06d"
P1R0_BLUEPRINT_SHA256 = "f793d7b8580ab561a7c834f3dc365b4c771027434a03418042b3429fa8fadf42"
AUDIT_SCRIPT_PATH = (
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/"
    "P1R0_DESIGN_INVALID_SEMANTIC_AUDIT.py"
)
AUDIT_RESULT_PATH = (
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/"
    "P1R0_DESIGN_INVALID_AUDIT_RESULT.json"
)
AUDIT_INVALID_VERDICT = (
    "P1R0_EXECUTABLE_DESIGN_FEASIBILITY_FALSE_POSITIVE__"
    "P1R1_NOT_ADMISSIBLE__CURRENT_INSTRUMENT_FAMILY_CLOSEOUT_REQUIRED"
)
FAMILY_DISPOSITION = "CLOSED_INVALID_NO_P1R1_NO_P2"
FUTURE_PRODUCT_STATUS = (
    "P1R0_DESIGN_FEASIBILITY_FALSE_POSITIVE_BANKED__"
    "CURRENT_PREFLIGHT_INSTRUMENT_FAMILY_CLOSED_INVALID__P1R1_P2_FORBIDDEN"
)
CANONICAL_TASK_KEY = "ego-canonical-mechanism-integration-001a"
CANONICAL_WORKSTREAM_ID = "canonical_mechanism_integration_route_001a"
CANONICAL_WORKSTREAM_STATUS = (
    "route_frozen__m0_complete__m1_headless_bridge_ready_not_started__"
    "disabled__non_mainline"
)
CANONICAL_ROUTE_DOC_PATH = "docs/EGO_CANONICAL_MECHANISM_INTEGRATION_ROUTE_001A.md"
NEXT_MINIMAL_ACTION = (
    "Execute M1 of EGO-CANONICAL-MECHANISM-INTEGRATION-001A only: after fresh "
    "bootstrap and pin/clean-tree readback, build the headless default-off K0 + "
    "VirtualCat-derived canonical mechanism bridge and prove serialized "
    "model/update state plus prediction/error/update/proposal recomputation "
    "through one source/replay path. Do not touch EgoDesktop, EgoOperator, old "
    "PET/PSPC sources, historical artifacts, runtime/mainline flags, push, tag, "
    "or remote anchors in M1. Stop on second-state-authority, hidden adapter "
    "state, replay weakness, or equal-access baseline equivalence."
)
C1_PATH_PINS = {
    AUDIT_RESULT_PATH: (
        "b8fa7cf552efb41323a34d723653ff81cfa8c4db",
        "a2aed0bc994592b54f260d74923896eabc0982d3e47ea6c3b1a64879be7061ec",
    ),
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1R0_DESIGN_INVALID_C1_MUTATION_SCOPE.yaml": (
        "f5e7c456d0b928559193553d4a58f9e1fcbacea5",
        "ee1a353d6ddea3ee6106656dadd3a0c95487ef6b740d980c0b75adbaca17ab03",
    ),
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1R0_DESIGN_INVALID_C2_MUTATION_SCOPE.yaml": (
        "f8ba1b2a0a03013f153e5051ad57496687e7d119",
        "aa003759d276e337d7597bcb19eb3711e9ca47e1776dd1e9163609fd0d46d17c",
    ),
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1R0_DESIGN_INVALID_FAMILY_CLOSEOUT_TASK_CARD.md": (
        "811fc223c47879064a6582d63a6abd51c620db37",
        "eaa3c6af7f0bf29bd6cb84f49f78042acf1ac98a0b7a85c0c05580839efc18f9",
    ),
    AUDIT_SCRIPT_PATH: (
        "3b1561126228da15beffde90a5a6f8ac5bf4f83c",
        "eb3214cb792fadc8b27377ae20716c95cb9965357dc5884cf4de58075b77bc9b",
    ),
}
PROTECTED_HEAD_OBJECTS = {
    P1R0_BLUEPRINT_PATH: P1R0_BLUEPRINT_BLOB,
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1R0_EXECUTABLE_DESIGN_MUTATION_SCOPE.yaml": "ac53f72ba5ee441fa8e1473db892d32742ec5b80",
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1R0_EXECUTABLE_DESIGN_TASK_CARD.md": "8e3bd21529a62b9894c1105ac090396bcc90983c",
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1R0_PRIOR_BLOCKER_RECORD.json": "bb12ac725bcd208d5239aafe75008c5ce4c82f6e",
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/PREFLIGHT_CONTRACT.json": "d09235eff74ec68b5cc5004873af1b1186d7ee39",
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/PREFLIGHT_STAGE_CARD.md": "06e1484a61ed18a863f4ecdb8352aab951bbfb07",
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/PREFLIGHT_MUTATION_SCOPE.yaml": "883703d79dbdfbca3792df3efc815fefc9b851fe",
    P1_TASK_CARD_PATH: P1_TASK_CARD_BLOB,
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1A_AUTHORIZATION_MUTATION_SCOPE.yaml": "5b3e192fe06791533b9f2292d9372bc559d9a253",
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1B_INSTRUMENT_MUTATION_SCOPE.yaml": "c87bc1847d8e29e5e90e07e6c58c02ec9bbd3f87",
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1C_CLOSEOUT_MUTATION_SCOPE.yaml": "58a1687a278403fb82e0f4774e3a424bdb624a8d",
    "packages/ego_k0_kernel": "43380f76c37b05f36a4a4ef45354048787cafe68",
    "artifacts/ego_k0_foundation_001a": "907457e7d3028ba5437cf0e7730ec068a21cbf6b",
}
MANDATORY_AUDIT_FINDINGS = {
    "module_keys:contract.py",
    "module_keys:workload.py",
    "module_keys:oracles.py",
    "module_keys:baselines.py",
    "module_keys:metrics.py",
    "module_keys:leakage.py",
    "module_keys:replay.py",
    "module_keys:producer.py",
    "module_keys:template_collapse",
    "traceability:callable_mapping",
    "traceability:failure_mapping",
    "baseline:no_feedback_access",
    "baseline:observation_only_access",
    "baseline:matched_marginal_target",
    "baseline:legal_map_semantics",
    "baseline:specialist_target",
    "seed_firewall:fitted_history_meta_mlp",
    "seed_firewall:from_scratch_online_logistic",
    "formal:authorization_contract",
    "formal:transition_guards",
    "seed:formal_phase_mapping",
    "embedded_lint:blocked_branch",
    "embedded_lint:semantic_coverage",
}
EXPECTED_LEDGER_ENTRY = {
    "evidence_id": "ego_learned_outcome_kernel_p1r0_design_invalidity_001a",
    "status": "fail",
    "evidence_level": "E2",
    "source_type": "unit",
    "artifact_path": AUDIT_RESULT_PATH,
    "what_it_proves": (
        "bounded callable evidence that the stored P1R0 design-admission FEASIBLE "
        "result is a false positive and cannot admit P1R1 in the current "
        "P0/P1/P1R0 lineage"
    ),
    "what_it_does_not_prove": (
        "surface impossibility, theory or mechanism invalidity, learning, product "
        "readiness, runtime/mainline effect, agency, subjectivity or consciousness"
    ),
    "related_workstream": "k0_developmental_kernel_dual_track",
    "created_at": "2026-07-12T00:00:00Z",
    "created_from_commit": C1_AUDIT_COMMIT,
}
LEDGER_APPEND_BYTES = (
    '  - evidence_id: "ego_learned_outcome_kernel_p1r0_design_invalidity_001a"\n'
    '    status: "fail"\n'
    '    evidence_level: "E2"\n'
    '    source_type: "unit"\n'
    f'    artifact_path: "{AUDIT_RESULT_PATH}"\n'
    '    what_it_proves: "bounded callable evidence that the stored P1R0 design-admission FEASIBLE result is a false positive and cannot admit P1R1 in the current P0/P1/P1R0 lineage"\n'
    '    what_it_does_not_prove: "surface impossibility, theory or mechanism invalidity, learning, product readiness, runtime/mainline effect, agency, subjectivity or consciousness"\n'
    '    related_workstream: "k0_developmental_kernel_dual_track"\n'
    '    created_at: "2026-07-12T00:00:00Z"\n'
    f'    created_from_commit: "{C1_AUDIT_COMMIT}"\n'
).encode("utf-8")

EXPECTED_GOVERNANCE_SYNC: dict[str, Any] = {
    "record_type": "SOURCE_PINNED_DERIVED_READBACK",
    "ego_synced_to_itl_operator_close": True,
    "sync_claim": "LOCAL_EGO_GOVERNANCE_VIEW_ONLY",
    "runtime_trigger_evidence": "ABSENT",
    "source_itl": {
        "repo": "intelligence-theory-lab",
        "head": "b67c94fe1244ef6006ed3af8e924d4c670fe64bb",
        "tree": "2caa9a8ad5587d284ec0da01c4d07a5ed53e9ea7",
        "task_id": "K0-VERIFIER-FAMILY-DOWNGRADE-AND-PRODUCT-SCIENCE-DECOUPLING-001A",
        "card_path": (
            "docs/codex/tasks/"
            "K0-VERIFIER-FAMILY-DOWNGRADE-AND-PRODUCT-SCIENCE-DECOUPLING-001A.md"
        ),
        "card_blob": "add0d7823fb824e4ee1d74edbe9f88f8a726f36a",
        "card_raw_sha256": "4a765fee0e910018cef46a7b4734d08cf5014e012b874b1150543a179dcbc663",
    },
    "operator_route_decision": {
        "route_id": "K0-DUAL-TRACK-SUPERSESSION-001A",
        "artifact_current_state": "ADJUDICATED",
        "phase": "K0_SCIENCE_ROUTE_CLOSED_WITHOUT_SCIENCE_ADJUDICATION",
        "closure_type": "CLOSED_WITHOUT_SCIENCE_ADJUDICATION",
        "route_disposition": "CLOSED_WITHOUT_EXECUTION",
        "operator_decision": "CLOSE_CURRENT_K0_SCIENCE_ROUTE",
        "adjudication_scope": "ROUTE_GOVERNANCE_ONLY",
        "science_adjudication": "NOT_PERFORMED",
        "instrument_validity": "NOT_TESTED",
        "mechanism_evidence": "NOT_TESTED",
        "theory_falsification": "NO_THEORY_FALSIFICATION",
        "mechanism_verdict": "NO_MECHANISM_VERDICT",
        "active_mechanism_frontier": "none",
    },
    "verifier_family": {
        "original_execution_verdict": "NOT_ACCEPTED_PROCEDURAL_NONCONFORMANCE",
        "first_repair_review_verdict": "NOT_ACCEPTED__STRUCTURAL_TERMINAL_LATCH_FAIL_OPEN",
        "replacement_review_verdict": "REPLACEMENT_VERIFIER_INVALID",
        "family_disposition": "CLOSED_INVALID_NO_FURTHER_REPAIR",
        "independent_validator_acceptance": "UNAVAILABLE",
        "operator_closure_acceptance_from_this_family": "UNAVAILABLE",
        "stored_validation_report_treatment": "FROZEN_EXECUTOR_OUTPUT_NOT_ACCEPTANCE_EVIDENCE",
    },
    "foundation_evidence": {
        "engineering_evidence": "BANKED_ACCEPTED_BOUNDED",
        "preservation": "FOUNDATION_EVIDENCE_PRESERVED",
        "implementation_authorized": False,
        "enabled": False,
        "mainline_connected": False,
        "runtime_authority": "none",
        "artifact_commit": "8318bb33212f79e1e0a9cea15cad7b9cd176a0f5",
        "artifact_tree": "907457e7d3028ba5437cf0e7730ec068a21cbf6b",
        "result_blob": "a8b3237afc40a1f56df3906870ff94c5db9c10ff",
        "result_sha256": "834b4764514062f8937488fd4b89684b5ae684e9522d67f440ed3c077f077067",
        "mechanism_meaning_inherited": False,
    },
    "component_status": {
        "foundation_engineering_evidence": "BANKED_ACCEPTED_BOUNDED",
        "h0": "NOT_TESTED",
        "k0_reference": "BLOCKED_NOT_TESTED",
        "h1": "BLOCKED_NOT_TESTED",
        "freeze": "BLOCKED_NOT_TESTED",
        "formal": "BLOCKED_NOT_TESTED",
    },
    "root_authorizations": {
        "implementation_authorized": False,
        "authorized_implementation_targets": [],
        "runtime_authorized": False,
        "mainline_authorized": False,
        "science_execution_authorized": False,
        "mechanism_evidence_authorized": False,
        "theory_pressure_authorized": False,
        "science_successor_authorized": False,
        "capability_route_registered": False,
        "capability_implementation_authorized": False,
    },
    "route_authorizations": {
        "agency": False,
        "autonomy": False,
        "code_first_prebank_implementation": False,
        "consciousness": False,
        "ego_mainline_runtime": False,
        "experiment_execution": False,
        "formal_run": False,
        "foundation_implementation": False,
        "freeze": False,
        "h0_implementation": False,
        "h1_implementation": False,
        "k0_reference_implementation": False,
        "mechanism_validity": False,
        "remote_anchor": False,
        "scoring": False,
        "subjectivity": False,
        "theory_pressure": False,
        "ui_llm_deployment": False,
    },
    "child_authorizations": {
        "EGO-K0-FOUNDATION-001A": False,
        "EGO-K0-REFERENCE-KERNEL-001A": False,
        "ITL-K0-H0-H1-INSTRUMENT-001A:H0": False,
        "ITL-K0-H0-H1-INSTRUMENT-001A:H1": False,
        "K0-IMMUTABLE-FREEZE-001A": False,
        "ITL-K0-FORMAL-EVIDENCE-001A": False,
    },
    "future_product_route": {
        "task_id": "EGO-LEARNED-OUTCOME-KERNEL-CAPABILITY-001A",
        "current_status": FUTURE_PRODUCT_STATUS,
        "prior_governance_sync_created_card": False,
        "this_card_bank_creates_card": True,
        "stage_card_banked": True,
        "stage_card_lane": "reference_only",
        "stage_card_path": FUTURE_PRODUCT_STAGE_CARD_PATH,
        "stage_card_bank_commit": "a5b33745c785676f6c63cadf7946997ba8426b8c",
        "stage_card_bank_parent": "6f5a45545c78ab446ad77fed1f0c46bc70fbb07a",
        "stage_card_blob": "9675a6baeafed8eab6cbcc9b2da7a2be226aac3e",
        "stage_card_sha256": "ec41623c48eaf518a033d47b927fa4e9efc511d923c9091c30f80e0fccc0e3ad",
        "route_registered": False,
        "candidate_preflight_authorized": False,
        "implementation_authorized": False,
        "enabled": False,
        "default_off_required": True,
        "mainline_connected": False,
        "non_mainline_required": True,
        "runtime_authority": "none",
        "current_operator_authorization_scope": (
            "PREFLIGHT_INSTRUMENT_FAMILY_CLOSED_INVALID__NEW_SURFACE_REQUIRES_FRESH_TASK"
        ),
        "same_surface_successor_authorized": False,
        "new_surface_requires_fresh_task_id": True,
        "current_surface_reuse_authorized": False,
        "requires_separate_bounded_stage_card": False,
        "requires_fresh_operator_authorization": True,
        "requires_fresh_candidate_preflight_authorization": True,
        "requires_fresh_implementation_authorization": True,
        "old_science_acceptance_required_for_product_card": False,
        "decoupling_scope": "PRODUCT_CARD_BANKED_NO_EXECUTION_AUTHORITY",
        "inherits_old_k0r_authority": False,
        "inherits_old_science_attribution": False,
        "inherits_old_h0_h1_freeze_formal_contracts": False,
        "inherits_old_sealed_fixtures_or_heldout_data": False,
        "old_k0r_bypass": False,
        "may_satisfy_old_h1_freeze_formal": False,
        "may_reopen_old_science_route": False,
        "foundation_engineering_dependency_redeclared_for_card_only": True,
        "foundation_engineering_dependency_redeclaration_required_for_execution": True,
        "foundation_mechanism_meaning_inherited": False,
        "candidate_independent_preflight": {
            "task_id": "EGO-LEARNED-OUTCOME-KERNEL-CAPABILITY-PREFLIGHT-001A",
            "prereg_banked": True,
            "prereg_commit": "ff1ab23e1db303a882cec17374b9ea3903fe03c6",
            "prereg_contract_blob": "d09235eff74ec68b5cc5004873af1b1186d7ee39",
            "prereg_contract_sha256": "d9c2d8a12b41ab9b0482b270b63578631b88901ca78854da92853779e95858c3",
            "p1_authorization_commit": P1_AUTHORIZATION_COMMIT,
            "p1_instrument_banked": False,
            "p1_blocker_status": "P1_BLOCKED_BASELINE_PANEL_SMC_FORMAL_PIPELINE_AND_REPLAY_NONCONFORMANCE",
            "p1_authorization_consumed": True,
            "instrument_implementation_authorized": False,
            "dev_instrument_execution_authorized": False,
            "formal_preflight_authorized": False,
            "p1_authorization_single_transaction": True,
            "p1_authorization_consumption_required": False,
            "p1_task_card_path": P1_TASK_CARD_PATH,
            "p1_task_card_blob": P1_TASK_CARD_BLOB,
            "p1_task_card_sha256": P1_TASK_CARD_SHA256,
            "p1r0_design_banked": True,
            "p1r0_design_commit": P1R0_SOURCE_COMMIT,
            "p1r0_stored_feasibility_verdict": (
                "P1R0_EXECUTABLE_DESIGN_FEASIBLE_FOR_ONE_P1R1_ATTEMPT_ONLY"
            ),
            "p1r0_independent_audit_banked": True,
            "p1r0_independent_audit_commit": C1_AUDIT_COMMIT,
            "p1r0_independent_audit_script_path": AUDIT_SCRIPT_PATH,
            "p1r0_independent_audit_script_blob": C1_PATH_PINS[AUDIT_SCRIPT_PATH][0],
            "p1r0_independent_audit_script_sha256": C1_PATH_PINS[AUDIT_SCRIPT_PATH][1],
            "p1r0_independent_audit_result_path": AUDIT_RESULT_PATH,
            "p1r0_independent_audit_result_blob": C1_PATH_PINS[AUDIT_RESULT_PATH][0],
            "p1r0_independent_audit_result_sha256": C1_PATH_PINS[AUDIT_RESULT_PATH][1],
            "p1r0_independent_audit_verdict": AUDIT_INVALID_VERDICT,
            "p1r0_independent_audit_blocking_finding_count": 23,
            "p1r0_feasible_admission_valid": False,
            "p1r1_authorized": False,
            "p2_authorized": False,
            "preflight_instrument_family_disposition": FAMILY_DISPOSITION,
            "independent_validator_acceptance": "UNAVAILABLE",
            "local_callable_is_independent_validator": False,
            "surface_mathematical_status": "NOT_ADJUDICATED",
            "surface_impossibility_not_claimed": True,
            "authorized_preflight_instrument_targets": [],
        },
    },
    "science_route_firewall": {
        "science_successor_authorized": False,
        "product_results_have_science_weight": False,
        "product_results_can_supply_mechanism_attribution": False,
        "science_successor_requires_separate_candidate_independent_headroom_prototype": True,
        "product_route_cannot_satisfy_or_bypass_that_requirement": True,
    },
}

STALE_K0_SEMANTICS = (
    "closure_review_required",
    "governance_stop",
    "operator replace-versus-close decision pending",
    "operator_decision_required",
)


def _git_lines(args: list[str]) -> list[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_HYGIENE_POLICY_PATH.parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _git_bytes(args: list[str]) -> bytes | None:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_HYGIENE_POLICY_PATH.parents[1],
        capture_output=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def _mapping_contains_key(node: Any, key: str) -> bool:
    if isinstance(node, dict):
        return key in node or any(_mapping_contains_key(value, key) for value in node.values())
    if isinstance(node, list):
        return any(_mapping_contains_key(value, key) for value in node)
    return False


def _validate_committed_audit(errors: list[str]) -> dict[str, Any] | None:
    repo_root = REPO_HYGIENE_POLICY_PATH.parents[1]
    if _git_lines(["rev-parse", f"{C1_AUDIT_COMMIT}^"]) != [C1_AUDIT_PARENT]:
        errors.append("C1 audit commit parent does not match the pinned P1R0 source commit")

    c1_diff = set(
        _git_lines(["diff-tree", "--no-commit-id", "--name-status", "-r", C1_AUDIT_COMMIT])
    )
    expected_c1_diff = {f"A\t{path}" for path in C1_PATH_PINS}
    if c1_diff != expected_c1_diff:
        errors.append("C1 audit commit does not contain the exact five additions")

    committed_bytes: dict[str, bytes] = {}
    for path, (expected_blob, expected_sha256) in C1_PATH_PINS.items():
        if _git_lines(["rev-parse", f"{C1_AUDIT_COMMIT}:{path}"]) != [expected_blob]:
            errors.append(f"C1 blob pin mismatch: {path}")
            continue
        data = _git_bytes(["cat-file", "blob", f"{C1_AUDIT_COMMIT}:{path}"])
        if data is None or hashlib.sha256(data).hexdigest() != expected_sha256:
            errors.append(f"C1 raw SHA-256 pin mismatch: {path}")
            continue
        committed_bytes[path] = data

    if _git_lines(["rev-parse", f"{P1R0_SOURCE_COMMIT}:{P1R0_BLUEPRINT_PATH}"]) != [
        P1R0_BLUEPRINT_BLOB
    ]:
        errors.append("P1R0 blueprint blob pin does not match the source commit")
    blueprint_bytes = _git_bytes(
        ["cat-file", "blob", f"{P1R0_SOURCE_COMMIT}:{P1R0_BLUEPRINT_PATH}"]
    )
    if blueprint_bytes is None or hashlib.sha256(blueprint_bytes).hexdigest() != P1R0_BLUEPRINT_SHA256:
        errors.append("P1R0 blueprint SHA-256 pin does not match the source commit")

    script_bytes = committed_bytes.get(AUDIT_SCRIPT_PATH)
    result_bytes = committed_bytes.get(AUDIT_RESULT_PATH)
    if script_bytes is None or result_bytes is None:
        return None
    if len(result_bytes) != 16589:
        errors.append("committed audit result length is not the canonical 16589 bytes")

    fd, temporary_script = tempfile.mkstemp(prefix="p1r0_committed_audit_", suffix=".py")
    os.close(fd)
    try:
        with open(temporary_script, "wb") as stream:
            stream.write(script_bytes)
        proc = subprocess.run(
            [
                sys.executable,
                temporary_script,
                "--repo",
                str(repo_root),
                "--source-commit",
                P1R0_SOURCE_COMMIT,
                "--require-invalid",
            ],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
    finally:
        try:
            os.unlink(temporary_script)
        except FileNotFoundError:
            pass
    if proc.returncode != 0:
        errors.append(
            "committed independent audit execution failed: "
            + proc.stderr.decode("utf-8", errors="replace").strip()
        )
        return None
    if proc.stdout != result_bytes:
        errors.append("committed independent audit stdout does not byte-match the committed result")
        return None

    try:
        report = json.loads(result_bytes)
    except json.JSONDecodeError as exc:
        errors.append(f"committed independent audit result is not valid JSON: {exc}")
        return None

    if report.get("producer_function") != "audit_blueprint":
        errors.append("audit producer_function is not the callable audit_blueprint path")
    if report.get("code_path_hash") != C1_PATH_PINS[AUDIT_SCRIPT_PATH][1]:
        errors.append("audit code_path_hash does not match the committed auditor")
    if report.get("run_id") != "p1r0-semantic-audit-5e7a43afa2eb1344":
        errors.append("audit deterministic run_id differs from the pinned computation")
    if report.get("source_commit") != P1R0_SOURCE_COMMIT:
        errors.append("audit source commit differs from the pinned P1R0 commit")
    if (report.get("self_test") or {}).get("all_pass") is not True:
        errors.append("audit positive/negative control self-test did not pass")
    findings = report.get("blocking_findings") or []
    finding_ids = [item.get("check_id") for item in findings if isinstance(item, dict)]
    if report.get("blocking_finding_count") != 23 or len(finding_ids) != 23:
        errors.append("audit must contain exactly 23 computed blocking findings")
    if set(finding_ids) != MANDATORY_AUDIT_FINDINGS or len(set(finding_ids)) != 23:
        errors.append("audit mandatory finding IDs do not match the frozen 23-ID set")
    if report.get("computed_verdict") != AUDIT_INVALID_VERDICT:
        errors.append("audit did not compute the required INVALID verdict")
    if report.get("stored_feasibility_verdict") != (
        "P1R0_EXECUTABLE_DESIGN_FEASIBLE_FOR_ONE_P1R1_ATTEMPT_ONLY"
    ):
        errors.append("audit did not preserve the stored P1R0 FEASIBLE verdict separately")
    if report.get("p1r1_admissible") is not False or report.get("p2_admissible") is not False:
        errors.append("audit must deny P1R1 and P2 admissibility")
    boundaries = report.get("policy_boundaries") or {}
    if boundaries.get("independent_validator_acceptance") != "UNAVAILABLE":
        errors.append("audit must retain independent validator acceptance as UNAVAILABLE")
    if boundaries.get("local_callable_is_independent_validator") is not False:
        errors.append("local callable audit must not be represented as an independent validator")
    if boundaries.get("surface_mathematical_status") != "NOT_ADJUDICATED":
        errors.append("surface mathematical status must remain NOT_ADJUDICATED")
    if boundaries.get("surface_impossibility_not_claimed") is not True:
        errors.append("surface impossibility must remain explicitly unclaimed")

    input_hashes = report.get("input_artifact_hashes") or {}
    input_blobs = report.get("input_artifact_blobs") or {}
    for path, expected_sha256 in input_hashes.items():
        source_bytes = _git_bytes(["cat-file", "blob", f"{P1R0_SOURCE_COMMIT}:{path}"])
        if source_bytes is None or hashlib.sha256(source_bytes).hexdigest() != expected_sha256:
            errors.append(f"audit input SHA-256 does not match pinned Git bytes: {path}")
        if _git_lines(["rev-parse", f"{P1R0_SOURCE_COMMIT}:{path}"]) != [input_blobs.get(path)]:
            errors.append(f"audit input blob does not match pinned Git object: {path}")
    return report


def _validate_additive_ledger(errors: list[str]) -> None:
    repo_root = REPO_HYGIENE_POLICY_PATH.parents[1]
    if _git_lines(["rev-parse", f"{C1_AUDIT_COMMIT}:artifacts/evidence_ledger/index.yaml"]) != [
        C1_LEDGER_BLOB
    ]:
        errors.append("C1 pre-append evidence-ledger blob pin does not match")
        return
    prior_bytes = _git_bytes(
        ["cat-file", "blob", f"{C1_AUDIT_COMMIT}:artifacts/evidence_ledger/index.yaml"]
    )
    current_bytes = (repo_root / "artifacts/evidence_ledger/index.yaml").read_bytes()
    canonical_current_bytes = current_bytes.replace(b"\r\n", b"\n")
    expected_bytes = None if prior_bytes is None else prior_bytes + LEDGER_APPEND_BYTES
    if expected_bytes is None or canonical_current_bytes != expected_bytes:
        errors.append("evidence ledger is not the exact byte-preserving single-entry append")
    head_bytes = _git_bytes(["cat-file", "blob", "HEAD:artifacts/evidence_ledger/index.yaml"])
    if head_bytes not in {prior_bytes, expected_bytes}:
        errors.append("HEAD evidence-ledger blob is neither the pinned parent nor exact additive result")
    if current_bytes.count(EXPECTED_LEDGER_ENTRY["evidence_id"].encode("utf-8")) != 1:
        errors.append("bounded P1R0 invalidity ledger entry must occur exactly once")


def _check_generated_file(path, expected: str, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing generated file: {path}")
        return
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        errors.append(f"generated file drift detected: {path}")


def validate_route_convergence(
    program_state: dict[str, Any],
    entries: list[Any],
    *,
    check_generated_files: bool = True,
) -> list[str]:
    errors: list[str] = []
    repo_root = REPO_HYGIENE_POLICY_PATH.parents[1]
    audit_report = _validate_committed_audit(errors)
    _validate_additive_ledger(errors)
    if check_generated_files:
        expected_lane_index = render_task_lane_index(program_state)
        expected_hygiene_policy = render_repo_hygiene_policy()
        expected_surface_map = render_repo_surface_map()

        _check_generated_file(TASK_LANE_INDEX_PATH, expected_lane_index, errors)
        _check_generated_file(REPO_HYGIENE_POLICY_PATH, expected_hygiene_policy, errors)
        _check_generated_file(REPO_SURFACE_MAP_PATH, expected_surface_map, errors)

    active_default_entries = [entry for entry in entries if entry.lane == "active_default"]
    if len(active_default_entries) != 1:
        errors.append(f"expected exactly one active_default entry, found {len(active_default_entries)}")
    elif active_default_entries[0].key != "ego-operator-human-operator-trial-v2":
        errors.append("active_default entry must be `ego-operator-human-operator-trial-v2` during EgoOperator human-observation gate")

    foundation_entries = [entry for entry in entries if entry.key == "ego-k0-foundation-001a"]
    if len(foundation_entries) != 1:
        errors.append(f"expected exactly one Foundation route entry, found {len(foundation_entries)}")
    else:
        foundation_entry = foundation_entries[0]
        if foundation_entry.lane != "closed_evidence":
            errors.append("Foundation must appear only in `closed_evidence`")
        foundation_why = foundation_entry.why.lower()
        required_foundation_semantics = (
            "bounded engineering evidence",
            "banked/accepted",
            "authorization consumed",
            "disabled",
            "non-mainline",
            "no runtime authority",
        )
        for phrase in required_foundation_semantics:
            if phrase not in foundation_why:
                errors.append(f"Foundation route explanation missing `{phrase}`")

    supporting_foundation_entries = [
        entry for entry in entries if entry.key == "ego-k0-foundation-001a" and entry.lane == "supporting_active"
    ]
    if supporting_foundation_entries:
        errors.append("Foundation must not appear in `supporting_active`")

    reference_kernel_entries = [entry for entry in entries if entry.key == "ego-k0-reference-kernel-001a"]
    if len(reference_kernel_entries) != 1:
        errors.append(f"expected exactly one Reference Kernel route entry, found {len(reference_kernel_entries)}")
    else:
        reference_kernel_entry = reference_kernel_entries[0]
        if reference_kernel_entry.lane != "reference_only":
            errors.append("Reference Kernel must appear only in `reference_only`")
        reference_why = reference_kernel_entry.why.lower()
        required_reference_semantics = (
            "old science-attribution plan",
            "not executed",
            "blocked_not_tested",
            "operator closed the old route without science adjudication",
            "independent validator acceptance unavailable",
            "no implementation authority",
            "not the future product route",
        )
        for phrase in required_reference_semantics:
            if phrase not in reference_why:
                errors.append(f"Reference Kernel route explanation missing `{phrase}`")

    disallowed_reference_lanes = {
        entry.lane
        for entry in reference_kernel_entries
        if entry.lane in {"parked", "active_default", "supporting_active", "closed_evidence"}
    }
    if disallowed_reference_lanes:
        errors.append(
            "Reference Kernel appears in disallowed lane(s): "
            + ", ".join(sorted(disallowed_reference_lanes))
        )

    future_product_entries = [entry for entry in entries if entry.key == FUTURE_PRODUCT_TASK_KEY]
    if len(future_product_entries) != 1:
        errors.append(f"expected exactly one learned-outcome capability card entry, found {len(future_product_entries)}")
    else:
        future_product_entry = future_product_entries[0]
        if future_product_entry.lane != "reference_only":
            errors.append("learned-outcome capability card must appear only in `reference_only`")
        if future_product_entry.lane in {"parked", "supporting_active", "active_default"}:
            errors.append("learned-outcome capability card appears in a disallowed actionable lane")

    canonical_entries = [entry for entry in entries if entry.key == CANONICAL_TASK_KEY]
    if len(canonical_entries) != 1:
        errors.append(
            f"expected exactly one canonical mechanism integration entry, found {len(canonical_entries)}"
        )
    else:
        canonical_entry = canonical_entries[0]
        if canonical_entry.lane != "supporting_active":
            errors.append("canonical mechanism integration must be `supporting_active` before M1")
        canonical_why = canonical_entry.why.lower()
        for phrase in (
            "sole selected successor route",
            "m1 headless",
            "enablement/mainline/runtime authority remain absent",
        ):
            if phrase not in canonical_why:
                errors.append(f"canonical route explanation missing `{phrase}`")

    route_doc = repo_root / CANONICAL_ROUTE_DOC_PATH
    if not route_doc.is_file():
        errors.append(f"canonical route document missing: {CANONICAL_ROUTE_DOC_PATH}")
    else:
        route_text = route_doc.read_text(encoding="utf-8")
        for phrase in (
            "### K0 Foundation — sole substrate authority",
            "VirtualCatPSPC-derived world/self-model adapter",
            "EgoDesktop observer/input surface",
            "Historical `go_for_*` text is not current authority",
            "M1 — next action",
        ):
            if phrase not in route_text:
                errors.append(f"canonical route document missing `{phrase}`")

    workstreams = {item.get("id"): item for item in program_state.get("workstreams") or []}
    active_ws = workstreams.get("ego_operator_first_transition") or {}
    if not active_ws:
        errors.append("ego_operator_first_transition workstream missing from docs/PROGRAM_STATE_UNIFIED.yaml")
    elif not str(active_ws.get("status") or "").strip():
        errors.append("ego_operator_first_transition workstream must carry a non-empty current status")
    supporting_ws = workstreams.get("repo_cleanup_route_convergence") or {}
    if supporting_ws.get("status") != "supporting_active":
        errors.append("repo_cleanup_route_convergence workstream must exist and stay `supporting_active`")

    foundation_ws = workstreams.get("k0_developmental_kernel_dual_track") or {}
    if foundation_ws.get("status") != EXPECTED_K0_STATUS:
        errors.append("K0 workstream must record the exact closed-invalid governance-sync status")
    if foundation_ws.get("evidence_level") != "E3" or foundation_ws.get("verification_level") != "V3":
        errors.append("K0 Foundation workstream must retain the bounded Ego E3/V3 governance classification")
    if foundation_ws.get("enabled") is not False or foundation_ws.get("mainline_connected") is not False:
        errors.append("K0 Foundation workstream must remain disabled and non-mainline")

    canonical_ws = workstreams.get(CANONICAL_WORKSTREAM_ID) or {}
    if canonical_ws.get("status") != CANONICAL_WORKSTREAM_STATUS:
        errors.append("canonical mechanism workstream status does not match the frozen M0 boundary")
    if canonical_ws.get("evidence_level") != "E1" or canonical_ws.get("verification_level") != "V1":
        errors.append("canonical M0 workstream must remain docs/governance E1/V1")
    if canonical_ws.get("enabled") is not False or canonical_ws.get("mainline_connected") is not False:
        errors.append("canonical mechanism successor must remain disabled and non-mainline in M0")

    governance_sync = foundation_ws.get("governance_sync")
    if governance_sync != EXPECTED_GOVERNANCE_SYNC:
        errors.append("K0 governance_sync mapping does not match the pinned closed-invalid contract")

    future_product_route = (governance_sync or {}).get("future_product_route") or {}
    preflight = future_product_route.get("candidate_independent_preflight") or {}
    if program_state.get("program", {}).get("next_minimal_action") != NEXT_MINIMAL_ACTION:
        errors.append("program.next_minimal_action does not match the canonical M1 boundary")
    if future_product_route.get("current_status") != FUTURE_PRODUCT_STATUS:
        errors.append("future product route status does not record the exact P1R0 invalid family closeout")
    if future_product_route.get("current_operator_authorization_scope") != (
        "PREFLIGHT_INSTRUMENT_FAMILY_CLOSED_INVALID__NEW_SURFACE_REQUIRES_FRESH_TASK"
    ):
        errors.append("current operator authorization scope does not require a fresh new-surface task")
    expected_surface_boundaries = {
        "same_surface_successor_authorized": False,
        "new_surface_requires_fresh_task_id": True,
        "current_surface_reuse_authorized": False,
    }
    for key, expected in expected_surface_boundaries.items():
        if future_product_route.get(key) is not expected:
            errors.append(f"future product route boundary mismatch: {key}")
    if preflight.get("preflight_instrument_family_disposition") != FAMILY_DISPOSITION:
        errors.append("current P0/P1/P1R0 instrument lineage is not closed invalid")
    if audit_report is not None and preflight.get("p1r0_independent_audit_verdict") != audit_report.get(
        "computed_verdict"
    ):
        errors.append("Program State audit verdict does not equal the recomputed callable verdict")
    if preflight.get("p1r0_stored_feasibility_verdict") != (
        "P1R0_EXECUTABLE_DESIGN_FEASIBLE_FOR_ONE_P1R1_ATTEMPT_ONLY"
    ):
        errors.append("Program State did not preserve the stored P1R0 FEASIBLE verdict")
    if _mapping_contains_key(program_state, "product_results_have_mechanism_attribution"):
        errors.append("wrong near-key product_results_have_mechanism_attribution is forbidden")

    root_authorizations = (governance_sync or {}).get("root_authorizations") or {}
    route_authorizations = (governance_sync or {}).get("route_authorizations") or {}
    child_authorizations = (governance_sync or {}).get("child_authorizations") or {}
    if root_authorizations.get("authorized_implementation_targets") != []:
        errors.append("authorized implementation targets must remain empty")
    if any(value is not False for key, value in root_authorizations.items() if key != "authorized_implementation_targets"):
        errors.append("all root authorization values must remain false")
    if any(value is not False for value in route_authorizations.values()):
        errors.append("all route authorization values must remain false")
    if len(child_authorizations) != 6 or any(value is not False for value in child_authorizations.values()):
        errors.append("all six historical child authorization values must remain false")
    for key in (
        "route_registered",
        "candidate_preflight_authorized",
        "implementation_authorized",
        "enabled",
        "mainline_connected",
    ):
        if future_product_route.get(key) is not False:
            errors.append(f"future product route execution boundary must remain false: {key}")
    if future_product_route.get("runtime_authority") != "none":
        errors.append("future product route runtime authority must remain none")
    for key in (
        "instrument_implementation_authorized",
        "dev_instrument_execution_authorized",
        "formal_preflight_authorized",
        "p1r1_authorized",
        "p2_authorized",
    ):
        if preflight.get(key) is not False:
            errors.append(f"preflight authorization must remain false: {key}")
    if preflight.get("authorized_preflight_instrument_targets") != []:
        errors.append("authorized preflight instrument targets must remain empty")
    firewall = (governance_sync or {}).get("science_route_firewall") or {}
    if firewall.get("product_results_have_science_weight") is not False:
        errors.append("product results must retain no science weight")
    if firewall.get("product_results_can_supply_mechanism_attribution") is not False:
        errors.append("product results must not supply mechanism attribution")
    bank_commit = str(future_product_route.get("stage_card_bank_commit") or "")
    bank_parent = str(future_product_route.get("stage_card_bank_parent") or "")
    card_path = str(future_product_route.get("stage_card_path") or "")
    card_blob = str(future_product_route.get("stage_card_blob") or "")
    card_sha256 = str(future_product_route.get("stage_card_sha256") or "")
    actual_parent = _git_lines(["rev-parse", f"{bank_commit}^"])
    if actual_parent != [bank_parent]:
        errors.append("learned-outcome capability card bank parent pin does not match git object readback")
    actual_blob = _git_lines(["rev-parse", f"{bank_commit}:{card_path}"])
    if actual_blob != [card_blob]:
        errors.append("learned-outcome capability Stage Card blob pin does not match git object readback")
    card_bytes = _git_bytes(["cat-file", "blob", f"{bank_commit}:{card_path}"])
    if card_bytes is None or hashlib.sha256(card_bytes).hexdigest() != card_sha256:
        errors.append("learned-outcome capability Stage Card SHA-256 pin does not match committed bytes")

    repo_root = REPO_HYGIENE_POLICY_PATH.parents[1]
    p1_task_card = repo_root / P1_TASK_CARD_PATH
    if not p1_task_card.is_file():
        errors.append("P1 instrument task card is missing from the working tree")
    else:
        p1_bytes = p1_task_card.read_bytes()
        git_blob = hashlib.sha1(
            f"blob {len(p1_bytes)}\0".encode("ascii") + p1_bytes,
            usedforsecurity=False,
        ).hexdigest()
        if git_blob != P1_TASK_CARD_BLOB:
            errors.append("P1 instrument task-card working blob does not match the temporary authorization pin")
        if hashlib.sha256(p1_bytes).hexdigest() != P1_TASK_CARD_SHA256:
            errors.append("P1 instrument task-card working SHA-256 does not match the temporary authorization pin")
    if (repo_root / FORMAL_ARTIFACT_PATH).exists():
        errors.append("formal learned-outcome preflight artifact path must remain absent during P1")
    authorization_parent = _git_lines(["rev-parse", f"{P1_AUTHORIZATION_COMMIT}^"])
    if authorization_parent != [P0_PREREG_COMMIT]:
        errors.append("P1 authorization commit is not the direct child of the frozen prereg commit")
    authorization_paths = set(
        _git_lines(["diff-tree", "--no-commit-id", "--name-only", "-r", P1_AUTHORIZATION_COMMIT])
    )
    expected_authorization_paths = {
        "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1_INSTRUMENT_TASK_CARD.md",
        "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1A_AUTHORIZATION_MUTATION_SCOPE.yaml",
        "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1B_INSTRUMENT_MUTATION_SCOPE.yaml",
        "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1C_CLOSEOUT_MUTATION_SCOPE.yaml",
        "docs/PROGRAM_STATE_UNIFIED.yaml",
        "scripts/codex/verify_route_convergence.py",
        "docs/STATUS.md",
        "artifacts/reports/program_state_summary.md",
    }
    if authorization_paths != expected_authorization_paths:
        errors.append("P1 authorization commit does not contain the exact eight-path set")
    instrument_paths_present = [
        relative for relative in P1_INSTRUMENT_TARGETS if (repo_root / relative).exists()
    ]
    if instrument_paths_present:
        errors.append("blocked P1 instrument paths must be absent after authorization consumption")
    forbidden_execution_paths = (
        "packages/ego_learned_outcome_kernel",
        "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P2_FORMAL_AUTHORIZATION.json",
    )
    for relative in forbidden_execution_paths:
        if (repo_root / relative).exists():
            errors.append(f"forbidden formal/product path must remain absent: {relative}")

    for path, expected_object in PROTECTED_HEAD_OBJECTS.items():
        if _git_lines(["rev-parse", f"HEAD:{path}"]) != [expected_object]:
            errors.append(f"protected P0/P1/P1R0/Foundation object drift: {path}")

    foundation_sink_text = " ".join(
        (
            str(foundation_ws.get("status") or ""),
            str(foundation_ws.get("summary") or ""),
            foundation_entries[0].why if len(foundation_entries) == 1 else "",
            reference_kernel_entries[0].why if len(reference_kernel_entries) == 1 else "",
        )
    ).lower()
    for stale_phrase in (*STALE_K0_SEMANTICS, "authorized_ready_to_implement", "authorized only"):
        if stale_phrase in foundation_sink_text:
            errors.append(f"stale K0 pending/actionable semantics remain: `{stale_phrase}`")

    gitignore_text = (REPO_HYGIENE_POLICY_PATH.parents[1] / ".gitignore").read_text(encoding="utf-8")

    for rule in HYGIENE_RULES:
        for snippet in rule.ignore_snippets:
            if snippet not in gitignore_text:
                errors.append(f".gitignore missing route-hygiene snippet `{snippet}`")

        untracked = _git_lines(["ls-files", "--others", "--exclude-standard", "--", rule.path_prefix])
        if untracked:
            errors.append(
                f"unignored operational exhaust present under {rule.path_prefix}: {', '.join(untracked[:5])}"
            )

        added = set(_git_lines(["diff", "--name-only", "--diff-filter=A", "HEAD", "--", rule.path_prefix]))
        added.update(_git_lines(["diff", "--cached", "--name-only", "--diff-filter=A", "--", rule.path_prefix]))
        if added:
            errors.append(
                f"new tracked operational exhaust detected under {rule.path_prefix}: {', '.join(sorted(added)[:5])}"
            )

    return errors


def main() -> int:
    program_state = load_program_state()
    entries = build_route_entries(program_state)
    errors = validate_route_convergence(program_state, entries)
    if errors:
        print(json.dumps({"status": "fail", "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    workstreams = {item.get("id"): item for item in program_state.get("workstreams") or []}
    k0_workstream = workstreams.get("k0_developmental_kernel_dual_track") or {}
    governance_sync = k0_workstream.get("governance_sync") or {}
    verifier_family = governance_sync.get("verifier_family") or {}
    future_product_route = governance_sync.get("future_product_route") or {}
    preflight = future_product_route.get("candidate_independent_preflight") or {}
    reference_kernel_entries = [entry for entry in entries if entry.key == "ego-k0-reference-kernel-001a"]
    future_product_entries = [entry for entry in entries if entry.key == FUTURE_PRODUCT_TASK_KEY]
    active_default_entries = [entry for entry in entries if entry.lane == "active_default"]
    print(
        json.dumps(
            {
                "status": "pass",
                "active_default": active_default_entries[0].key if active_default_entries else None,
                "supporting_active_count": sum(1 for entry in entries if entry.lane == "supporting_active"),
                "k0_workstream_status": k0_workstream.get("status"),
                "old_reference_kernel_lane": (
                    reference_kernel_entries[0].lane if len(reference_kernel_entries) == 1 else None
                ),
                "verifier_family_disposition": verifier_family.get("family_disposition"),
                "independent_validator_acceptance": verifier_family.get("independent_validator_acceptance"),
                "local_callable_is_independent_validator": preflight.get(
                    "local_callable_is_independent_validator"
                ),
                "surface_mathematical_status": preflight.get("surface_mathematical_status"),
                "surface_impossibility_not_claimed": preflight.get(
                    "surface_impossibility_not_claimed"
                ),
                "preflight_instrument_family_disposition": preflight.get(
                    "preflight_instrument_family_disposition"
                ),
                "future_product_route_status": future_product_route.get("current_status"),
                "future_product_route_lane": (
                    future_product_entries[0].lane if len(future_product_entries) == 1 else None
                ),
                "route_index": str(TASK_LANE_INDEX_PATH.relative_to(REPO_HYGIENE_POLICY_PATH.parents[1])),
                "hygiene_policy": str(REPO_HYGIENE_POLICY_PATH.relative_to(REPO_HYGIENE_POLICY_PATH.parents[1])),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
