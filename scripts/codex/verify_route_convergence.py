#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
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
EVIDENCE_LEDGER_BLOB = "7634cdccd69d25277bfeaab7e87865fd9e5bff0d"

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
        "current_status": "P1_INSTRUMENT_BLOCKED__AUTHORIZATION_CONSUMED__FORMAL_EXECUTION_NOT_AUTHORIZED",
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
        "current_operator_authorization_scope": "P1_INSTRUMENT_AUTHORIZATION_CONSUMED__P2_REQUIRES_FRESH_AUTHORIZATION",
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

    governance_sync = foundation_ws.get("governance_sync")
    if governance_sync != EXPECTED_GOVERNANCE_SYNC:
        errors.append("K0 governance_sync mapping does not match the pinned closed-invalid contract")

    future_product_route = (governance_sync or {}).get("future_product_route") or {}
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
    ledger_blob = _git_lines(["rev-parse", "HEAD:artifacts/evidence_ledger/index.yaml"])
    if ledger_blob != [EVIDENCE_LEDGER_BLOB]:
        errors.append("evidence ledger changed during the P1 instrument transaction")

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
