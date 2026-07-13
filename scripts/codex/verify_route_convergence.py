#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
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

# Historical pinned replay fixture for the already-closed K0 science lineage.
# It is not a source for current product route, lane, next-action, or authority facts.
HISTORICAL_K0_GOVERNANCE_SYNC_PIN: dict[str, Any] = {
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


def _git_in_repo(repo: Path, args: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=text,
        check=False,
    )


def compute_route_fingerprint(program_state: dict[str, Any]) -> str:
    program = program_state.get("program") or {}
    route_guard = dict(program_state.get("route_guard") or {})
    route_guard.pop("route_fingerprint", None)
    canonical_subset = {
        "program": {
            "current_phase": program.get("current_phase"),
            "next_minimal_action": program.get("next_minimal_action"),
        },
        "route_guard": route_guard,
    }
    encoded = json.dumps(
        canonical_subset,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_field(payload: Any, field: str) -> Any:
    current = payload
    for part in field.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _check_inventory_source(source: dict[str, Any], repo_root: Path, itl_root: Path) -> tuple[bool, str]:
    source_type = str(source.get("type") or "")
    if source_type == "repo_path":
        relative = str(source.get("value") or "")
        return (repo_root / relative).exists(), relative
    if source_type == "repo_json_value":
        relative = str(source.get("value") or "")
        path = repo_root / relative
        if not path.is_file():
            return False, relative
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False, relative
        actual = _json_field(payload, str(source.get("field") or ""))
        return actual == source.get("expected"), f"{relative}:{source.get('field')}"
    if source_type == "git_commit":
        commit = str(source.get("value") or "")
        proc = _git_in_repo(repo_root, ["cat-file", "-e", f"{commit}^{{commit}}"])
        return proc.returncode == 0, commit
    if source_type == "git_ancestry_chain":
        commits = [str(item) for item in source.get("values") or []]
        if len(commits) < 2:
            return False, "git_ancestry_chain"
        for commit in commits:
            if _git_in_repo(repo_root, ["cat-file", "-e", f"{commit}^{{commit}}"] ).returncode != 0:
                return False, commit
        for parent, child in zip(commits, commits[1:]):
            proc = _git_in_repo(repo_root, ["rev-parse", f"{child}^"])
            if proc.returncode != 0 or proc.stdout.strip() != parent:
                return False, f"{parent}->{child}"
        return True, "->".join(commits)
    if source_type == "itl_git_object":
        relative = str(source.get("path") or "")
        expected = str(source.get("git_blob_oid") or "")
        proc = _git_in_repo(itl_root, ["rev-parse", f"HEAD:{relative}"])
        return proc.returncode == 0 and proc.stdout.strip() == expected, relative
    return False, source_type or "missing_source_type"


def compute_prior_lineage_inventory(
    program_state: dict[str, Any],
    *,
    repo_root: Path | None = None,
    itl_root: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or REPO_HYGIENE_POLICY_PATH.parents[1]
    itl_root = itl_root or repo_root.parent / "intelligence-theory-lab"
    route_guard = program_state.get("route_guard") or {}
    inventory = route_guard.get("lineage_inventory") or {}
    records = inventory.get("records") if isinstance(inventory, dict) else []
    results: list[dict[str, Any]] = []
    for record in records or []:
        if not isinstance(record, dict):
            results.append({"lineage_id": None, "discovered": False, "disposed": False, "source_results": []})
            continue
        source_results = []
        for source in record.get("source_refs") or []:
            if not isinstance(source, dict):
                source_results.append({"ok": False, "ref": "invalid_source"})
                continue
            ok, ref = _check_inventory_source(source, repo_root, itl_root)
            source_results.append({"ok": ok, "ref": ref, "type": source.get("type")})
        discovered = bool(source_results) and all(item["ok"] for item in source_results)
        disposition = str(record.get("disposition") or "").strip()
        disposed = discovered and bool(disposition) and "UNDISPOSED" not in disposition
        results.append(
            {
                "lineage_id": record.get("lineage_id"),
                "discovered": discovered,
                "disposed": disposed,
                "disposition": disposition,
                "source_results": source_results,
            }
        )
    discovered_count = sum(1 for result in results if result["discovered"])
    disposed_count = sum(1 for result in results if result["disposed"])
    return {
        "producer_function": "scripts.codex.verify_route_convergence.compute_prior_lineage_inventory",
        "discovered_count": discovered_count,
        "disposed_count": disposed_count,
        "undisposed_count": len(results) - disposed_count,
        "records": results,
    }


def _validate_git_object_pin(repo: Path, pin: dict[str, Any], errors: list[str], label: str) -> bytes | None:
    path = str(pin.get("path") or "")
    expected_oid = str(pin.get("git_blob_oid") or "")
    expected_sha = str(pin.get("git_blob_payload_sha256") or "")
    oid = _git_in_repo(repo, ["rev-parse", f"HEAD:{path}"])
    if oid.returncode != 0 or oid.stdout.strip() != expected_oid:
        errors.append(f"{label} git blob OID mismatch: {path}")
        return None
    payload = _git_in_repo(repo, ["cat-file", "blob", f"HEAD:{path}"], text=False)
    if payload.returncode != 0 or hashlib.sha256(payload.stdout).hexdigest() != expected_sha:
        errors.append(f"{label} committed payload SHA-256 mismatch: {path}")
        return None
    return payload.stdout


def validate_route_guard(program_state: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    repo_root = REPO_HYGIENE_POLICY_PATH.parents[1]
    itl_root = repo_root.parent / "intelligence-theory-lab"
    route_guard = program_state.get("route_guard")
    if not isinstance(route_guard, dict):
        return ["route_guard is missing"], {}
    if route_guard.get("schema_version") != "ego.route_guard.v1":
        errors.append("route_guard schema_version must be ego.route_guard.v1")
    if route_guard.get("route_revision_id") != "EGO_ROUTE_8692_SUPERSESSION_001A":
        errors.append("route_guard revision does not record the additive 8692 supersession")
    computed_fingerprint = compute_route_fingerprint(program_state)
    if route_guard.get("route_fingerprint") != computed_fingerprint:
        errors.append("route_guard fingerprint does not match the canonical semantic subset")

    axes = route_guard.get("authority_axes") or {}
    product_axis = axes.get("product_capability") or {}
    science_axis = axes.get("science_attribution") or {}
    if product_axis != {"repo": "Ego", "source": "docs/PROGRAM_STATE_UNIFIED.yaml"}:
        errors.append("product/capability authority axis must resolve only to Ego PROGRAM_STATE_UNIFIED")
    pinned_head = str(science_axis.get("pinned_head") or "")
    if science_axis.get("repo") != "intelligence-theory-lab" or science_axis.get("source") != (
        "artifacts/ROUTE-STATE-MACHINE-001A"
    ):
        errors.append("science/attribution authority axis must resolve only to the ITL route-state machine")
    itl_head = _git_in_repo(itl_root, ["rev-parse", "HEAD"])
    if itl_head.returncode != 0 or itl_head.stdout.strip() != pinned_head:
        errors.append("science authority pinned HEAD does not match the live ITL committed object source")

    science_pins = route_guard.get("science_source_pins") or {}
    for key in ("state", "closure", "validation_report"):
        pin = science_pins.get(key) or {}
        payload = _validate_git_object_pin(itl_root, pin, errors, f"science_source_pins.{key}")
        if key == "validation_report" and payload is not None:
            path = str(pin.get("path") or "")
            filtered = _git_in_repo(itl_root, ["hash-object", "--path", path, path])
            if filtered.returncode != 0 or filtered.stdout.strip() != pin.get("required_filtered_blob_oid"):
                errors.append("validation_report filtered blob OID does not match the committed object")
            checkout = itl_root / path
            if not checkout.is_file() or hashlib.sha256(checkout.read_bytes()).hexdigest() != pin.get(
                "checkout_raw_sha256"
            ):
                errors.append("validation_report checkout raw SHA-256 does not match the disclosed materialization")
            elif checkout.read_bytes().replace(b"\r\n", b"\n") != payload:
                errors.append("validation_report checkout differs from committed bytes by more than CRLF/LF")

    binding = route_guard.get("allowed_action_binding") or {}
    if binding.get("allowed_next_action_ids") != ["bank_EGO-PET-WORLD-V1-CAPABILITY-HEADROOM-001A"]:
        errors.append("allowed action binding must contain only the Card 2 banking action")
    if binding.get("only_next_task") != "EGO-PET-WORLD-V1-CAPABILITY-HEADROOM-001A":
        errors.append("only_next_task must bind Card 2")
    if binding.get("permission") != "DRAFT_AND_BANK_CARD_ONLY" or binding.get("execution_authorized") is not False:
        errors.append("Card 2 binding must authorize drafting/banking only and reject execution")
    if binding.get("authorized_implementation_targets") != []:
        errors.append("allowed action binding must have no implementation targets")

    authorizations = route_guard.get("authorizations") or {}
    if authorizations.get("authorized_implementation_targets") != []:
        errors.append("route_guard authorized implementation targets must be empty")
    if any(value is not False for key, value in authorizations.items() if key != "authorized_implementation_targets"):
        errors.append("all route_guard authorizations must remain false")

    authority_state = route_guard.get("authority_state") or {}
    old_route = authority_state.get("old_route_8692") or {}
    if old_route.get("disposition") != "SUPERSEDED_BEFORE_M1":
        errors.append("old route 8692 supersession disposition is absent")
    for milestone in ("m1", "m2", "m3"):
        if old_route.get(milestone) != "NOT_STARTED_CANCELLED_BY_SUPERSESSION":
            errors.append(f"old route milestone {milestone} is not cancelled by supersession")
    egodesktop = authority_state.get("egodesktop") or {}
    if egodesktop != {
        "archive_state": "ARCHIVED_LEGACY_LLM_UI_ROUTE",
        "active_route_dependency": False,
        "successor_dependency": False,
        "runtime_authority": "none",
    }:
        errors.append("EgoDesktop archive authority state is not fail-closed")
    successor = authority_state.get("k0_successor") or {}
    if successor != {
        "enabled": False,
        "mainline_connected": False,
        "runtime_authority": "none",
        "real_trigger_evidence": "absent",
    }:
        errors.append("K0 successor state must remain disabled, non-mainline, authority-free, and untriggered")
    foundation = authority_state.get("foundation") or {}
    if foundation != {"evidence_state": "BANKED_ACCEPTED_BOUNDED", "runtime_enabled": False}:
        errors.append("Foundation bounded engineering evidence was not preserved at its recorded ceiling")
    if (authority_state.get("ego_operator") or {}).get("active_default") is not True:
        errors.append("EgoOperator must remain the sole active default")
    task_routes = ((route_guard.get("route_views") or {}).get("task_routes") or {})
    former_route = task_routes.get("ego-canonical-mechanism-integration-001a") or {}
    if egodesktop.get("archive_state") == "ARCHIVED_LEGACY_LLM_UI_ROUTE" and former_route.get("lane") != (
        "closed_evidence"
    ):
        errors.append("PROGRAM_STATE archives EgoDesktop but the former 8692 task sink is not closed_evidence")
    current_surfaces = ((route_guard.get("route_views") or {}).get("current_surfaces") or [])
    if any(
        isinstance(row, dict)
        and (
            row.get("surface") == "canonical_mechanism_successor"
            or "selected default-off successor" in str(row.get("role") or "").lower()
            or "supporting_active" in str(row.get("authority") or "").lower()
        )
        for row in current_surfaces
    ):
        errors.append("renderer source still promotes VirtualCat/EgoDesktop as an active successor route")
    egodesktop_surfaces = [
        row for row in current_surfaces if isinstance(row, dict) and "EgoDesktop/" in (row.get("paths") or [])
    ]
    if len(egodesktop_surfaces) != 1 or "archived legacy reference only" not in str(
        egodesktop_surfaces[0].get("authority") if egodesktop_surfaces else ""
    ).lower():
        errors.append("EgoDesktop surface sink does not preserve archived-reference-only semantics")

    next_contract = binding.get("next_task_contract") or {}
    if next_contract.get("task_kind") != "executable_candidate_independent_headroom":
        errors.append("Card 2 task kind does not require executable candidate-independent headroom")
    if next_contract.get("execution_authorized") is not False:
        errors.append("Card 2 execution must remain unauthorized")
    if next_contract.get("pilot_1_positive_control_allowed") is not False or next_contract.get(
        "pilot_1_regression_baseline_allowed"
    ) is not False:
        errors.append("Card 2 must not reuse pilot #1 as positive control or regression baseline")
    contract_pins = next_contract.get("frozen_contract_pins") or {}
    for key, pin in contract_pins.items():
        _validate_git_object_pin(itl_root, pin or {}, errors, f"frozen_contract_pins.{key}")
    registry_pin = contract_pins.get("baseline_immunity_registry") or {}
    registry_payload = _validate_git_object_pin(itl_root, registry_pin, [], "failure_family_registry")
    if registry_payload is None:
        errors.append("failure-family registry could not be read from its committed ITL object")
    else:
        try:
            failure_families = json.loads(registry_payload).get("failure_families")
        except (json.JSONDecodeError, AttributeError):
            failure_families = None
        declared_registry = next_contract.get("failure_family_registry") or {}
        if not isinstance(failure_families, list) or len(failure_families) != declared_registry.get("required_count"):
            errors.append("Card 2 failure-family count or registry semantics drifted from the pinned source")

    inventory_result = compute_prior_lineage_inventory(program_state, repo_root=repo_root, itl_root=itl_root)
    inventory = route_guard.get("lineage_inventory") or {}
    for key in ("discovered_count", "disposed_count", "undisposed_count"):
        if inventory.get(key) != inventory_result.get(key):
            errors.append(f"lineage inventory declared {key} does not match callable repo inventory")
    if inventory_result.get("undisposed_count") != 0:
        errors.append("prior lineage inventory contains an undisposed lineage")
    pilot_repair = next(
        (record for record in inventory.get("records") or [] if record.get("lineage_id") == "pilot_1_repair"),
        {},
    )
    successor_use = pilot_repair.get("successor_use") or {}
    if pilot_repair.get("audit_ref") is None and any(
        successor_use.get(key) != "BLOCKED_PENDING_RETRO_YELLOW"
        for key in ("positive_control", "regression_baseline")
    ):
        errors.append("pilot #1 repair cannot be enabled for successor use while audit_ref is null")
    ceiling = str(pilot_repair.get("evidence_ceiling") or "").lower()
    if "capability" not in ceiling or "learning" in ceiling or "mechanism" in ceiling:
        errors.append("pilot #1 repair capability verdict was upgraded beyond its recorded evidence ceiling")

    anti_zeno = route_guard.get("anti_zeno") or {}
    if anti_zeno.get("governance_only_successor_allowed") is not False or anti_zeno.get(
        "next_required_output_class"
    ) != "callable_candidate_independent_headroom":
        errors.append("anti-Zeno next-output enforcement is missing")

    return errors, {
        "route_fingerprint": computed_fingerprint,
        "science_authority_pin_status": "pass" if not any("science" in error for error in errors) else "fail",
        "lineage_inventory": inventory_result,
    }


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
    route_guard_errors, _ = validate_route_guard(program_state)
    errors.extend(route_guard_errors)
    audit_report = _validate_committed_audit(errors)
    _validate_additive_ledger(errors)
    if check_generated_files:
        expected_lane_index = render_task_lane_index(program_state)
        expected_hygiene_policy = render_repo_hygiene_policy()
        expected_surface_map = render_repo_surface_map(program_state)

        _check_generated_file(TASK_LANE_INDEX_PATH, expected_lane_index, errors)
        _check_generated_file(REPO_HYGIENE_POLICY_PATH, expected_hygiene_policy, errors)
        _check_generated_file(REPO_SURFACE_MAP_PATH, expected_surface_map, errors)

    route_guard = program_state.get("route_guard") or {}
    route_views = route_guard.get("route_views") or {}
    task_routes = route_views.get("task_routes") or {}
    expected_active_keys = sorted(
        str(key) for key, value in task_routes.items() if isinstance(value, dict) and value.get("lane") == "active_default"
    )
    active_default_entries = [entry for entry in entries if entry.lane == "active_default"]
    if sorted(entry.key for entry in active_default_entries) != expected_active_keys or len(expected_active_keys) != 1:
        errors.append("active_default task lane does not match the single structured route_guard owner")

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

    superseded_keys = sorted(
        str(key)
        for key, value in task_routes.items()
        if isinstance(value, dict) and value.get("workstream_id") == "canonical_mechanism_integration_route_001a"
    )
    canonical_entries = [entry for entry in entries if entry.key in superseded_keys]
    if len(canonical_entries) != 1:
        errors.append(f"expected exactly one structured superseded 8692 route entry, found {len(canonical_entries)}")
    else:
        canonical_entry = canonical_entries[0]
        expected_route = task_routes.get(canonical_entry.key) or {}
        if canonical_entry.lane != expected_route.get("lane") or canonical_entry.why.split(" Current workstream status:", 1)[0] != expected_route.get("why"):
            errors.append("superseded 8692 route entry diverges from structured route_guard")

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
    if foundation_ws.get("evidence_level") != "E3" or foundation_ws.get("verification_level") != "V3":
        errors.append("K0 Foundation workstream must retain the bounded Ego E3/V3 governance classification")
    if foundation_ws.get("enabled") is not False or foundation_ws.get("mainline_connected") is not False:
        errors.append("K0 Foundation workstream must remain disabled and non-mainline")

    canonical_ws = workstreams.get("canonical_mechanism_integration_route_001a") or {}
    if "superseded_before_m1" not in str(canonical_ws.get("status") or ""):
        errors.append("former 8692 workstream does not record supersession before M1")
    if canonical_ws.get("evidence_level") != "E1" or canonical_ws.get("verification_level") != "V1":
        errors.append("superseded 8692 workstream must remain docs/governance E1/V1")
    if canonical_ws.get("enabled") is not False or canonical_ws.get("mainline_connected") is not False:
        errors.append("superseded 8692 workstream must remain disabled and non-mainline")

    governance_sync = foundation_ws.get("governance_sync")

    future_product_route = (governance_sync or {}).get("future_product_route") or {}
    preflight = future_product_route.get("candidate_independent_preflight") or {}
    binding = route_guard.get("allowed_action_binding") or {}
    if str(binding.get("only_next_task") or "") not in str(program_state.get("program", {}).get("next_minimal_action") or ""):
        errors.append("program.next_minimal_action does not reflect the structured allowed-action binding")
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
    _, route_details = validate_route_guard(program_state)
    route_guard = program_state.get("route_guard") or {}
    lineage = route_details.get("lineage_inventory") or {}
    print(
        json.dumps(
            {
                "status": "pass",
                "active_default": active_default_entries[0].key if active_default_entries else None,
                "supporting_active_count": sum(1 for entry in entries if entry.lane == "supporting_active"),
                "route_revision_id": route_guard.get("route_revision_id"),
                "route_fingerprint": route_details.get("route_fingerprint"),
                "old_route_8692_disposition": (
                    (route_guard.get("authority_state") or {}).get("old_route_8692") or {}
                ).get("disposition"),
                "egodesktop_archive_state": (
                    (route_guard.get("authority_state") or {}).get("egodesktop") or {}
                ).get("archive_state"),
                "allowed_next_action_ids": (
                    (route_guard.get("allowed_action_binding") or {}).get("allowed_next_action_ids") or []
                ),
                "lineage_counts": {
                    "discovered": lineage.get("discovered_count"),
                    "disposed": lineage.get("disposed_count"),
                    "undisposed": lineage.get("undisposed_count"),
                },
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
