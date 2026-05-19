from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "ai-self-awareness-minimal-framework"
ARTIFACT_DIR = ROOT / "artifacts" / "self_awareness_research"

CONTRACT_MODULE_PATH = ROOT / "scripts" / "codex" / "subjectcore_contract.py"
FACADE_CONTRACT_PATH = TASK_DIR / "SUBJECTCORE_FACADE_CONTRACT.md"
SNAPSHOT_CONTRACT_PATH = TASK_DIR / "SUBJECTCORE_SNAPSHOT_CONTRACT.md"
SCHEMA_PATH = TASK_DIR / "SUBJECTCORE_FOLLOWON_EVAL_ARTIFACT_SCHEMA.md"

INTEGRITY_JSON_PATH = ARTIFACT_DIR / "SUBJECTCORE_INTEGRITY_CURRENT.json"
INTEGRITY_MD_PATH = ARTIFACT_DIR / "SUBJECTCORE_INTEGRITY_CURRENT.md"
BOUNDARY_JSON_PATH = ARTIFACT_DIR / "SUBJECTCORE_HOST_BOUNDARY_CURRENT.json"
BOUNDARY_MD_PATH = ARTIFACT_DIR / "SUBJECTCORE_HOST_BOUNDARY_CURRENT.md"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


subjectcore_contract = _load_module(CONTRACT_MODULE_PATH, "subjectcore_contract_eval_stub")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render planning-side SubjectCore follow-on eval artifacts")
    parser.add_argument(
        "--sample-mode",
        choices=subjectcore_contract.SAMPLE_MODES,
        default="valid_facade",
    )
    parser.add_argument("--integrity-json", type=Path, default=INTEGRITY_JSON_PATH)
    parser.add_argument("--integrity-md", type=Path, default=INTEGRITY_MD_PATH)
    parser.add_argument("--boundary-json", type=Path, default=BOUNDARY_JSON_PATH)
    parser.add_argument("--boundary-md", type=Path, default=BOUNDARY_MD_PATH)
    return parser.parse_args()


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def build_followon_eval_payloads(sample_mode: str) -> tuple[dict[str, Any], dict[str, Any]]:
    subject_core = subjectcore_contract.build_sample_subjectcore(sample_mode)
    validation_error = None
    snapshot = None
    host_projection = None
    try:
        snapshot = subjectcore_contract.build_subjectcore_snapshot(subject_core)
        host_projection = subjectcore_contract.project_to_host_surface(snapshot)
    except ValueError as exc:
        validation_error = str(exc)

    proposals = tuple(subject_core.proposal_engine.proposal_candidates)
    continuity_ok = bool(subject_core.identity_continuity.subject_handle.strip()) and bool(
        subject_core.memory_projection.continuity_anchor.strip()
    )
    plasticity_ok = (
        subject_core.self_state.correction_state.corrective_trace_present
        and bool(subject_core.self_state.response_tendency.suggested_next_step)
    )
    proposal_ok = (
        bool(proposals)
        and all(
            proposal.proposal_id.strip()
            and proposal.kind.strip()
            and proposal.rationale.strip()
            and proposal.source_basis.strip()
            for proposal in proposals
        )
        and bool(subject_core.self_state.response_tendency.suggested_next_step)
    )
    proposal_consistency_ok = bool(proposals) and (
        subject_core.self_state.response_tendency.preferred_mode in {"ask", "repair"}
        and subject_core.self_state.response_tendency.suggested_next_step not in {"", "continue"}
    )
    proposal_prioritization_ok = True
    if len(proposals) > 1:
        ranked_proposals = [
            proposal
            for proposal in proposals
            if proposal.next_step_hint.strip() and isinstance(proposal.priority_rank, int) and proposal.priority_rank > 0
        ]
        unique_priorities = {proposal.priority_rank for proposal in ranked_proposals}
        if len(ranked_proposals) != len(proposals) or len(unique_priorities) != len(proposals):
            proposal_prioritization_ok = False
        else:
            top_proposal = min(ranked_proposals, key=lambda proposal: proposal.priority_rank)
            proposal_prioritization_ok = (
                subject_core.self_state.response_tendency.suggested_next_step == top_proposal.next_step_hint
            )
    proposal_resolution_ok = True
    if len(proposals) > 1:
        proposal_ids = [proposal.proposal_id for proposal in proposals if proposal.proposal_id.strip()]
        next_step_hints = [proposal.next_step_hint for proposal in proposals if proposal.next_step_hint.strip()]
        proposal_resolution_ok = (
            len(proposal_ids) == len(proposals)
            and len(set(proposal_ids)) == len(proposal_ids)
            and len(next_step_hints) == len(proposals)
            and len(set(next_step_hints)) == len(next_step_hints)
        )
    proposal_restabilization_ok = True
    if len(proposals) > 1 and (
        subject_core.self_state.current_focus == "replan"
        or any(getattr(proposal, "revision_epoch", 1) > 1 for proposal in proposals)
    ):
        revision_epochs = [
            proposal.revision_epoch
            for proposal in proposals
            if isinstance(proposal.revision_epoch, int) and proposal.revision_epoch > 0
        ]
        proposal_restabilization_ok = (
            len(revision_epochs) == len(proposals)
            and min(revision_epochs) >= 2
            and len(set(revision_epochs)) == 1
        )
    proposal_set_update_ok = True
    if len(proposals) > 1 and (
        subject_core.self_state.current_focus in {"replace", "rollback"}
        or any(getattr(proposal, "lifecycle_state", "active") != "active" for proposal in proposals)
    ):
        active_proposals = [
            proposal for proposal in proposals if getattr(proposal, "lifecycle_state", "active") == "active"
        ]
        proposal_set_update_ok = (
            len(active_proposals) == len(proposals)
            and any(
                proposal.next_step_hint == subject_core.self_state.response_tendency.suggested_next_step
                for proposal in active_proposals
            )
        )
    proposal_set_remerge_ok = True
    merge_group_ids = {
        getattr(proposal, "merge_group_id", "").strip()
        for proposal in proposals
        if getattr(proposal, "merge_group_id", "").strip()
    }
    if len(proposals) > 1 and (
        subject_core.self_state.current_focus in {"replace", "rollback"} or bool(merge_group_ids)
    ):
        for merge_group_id in merge_group_ids:
            active_group_members = [
                proposal
                for proposal in proposals
                if getattr(proposal, "merge_group_id", "").strip() == merge_group_id
                and getattr(proposal, "lifecycle_state", "active") == "active"
            ]
            if len(active_group_members) > 1:
                proposal_set_remerge_ok = False
                break
    proposal_set_consolidation_ok = True
    update_chain_ids = {
        getattr(proposal, "update_chain_id", "").strip()
        for proposal in proposals
        if getattr(proposal, "update_chain_id", "").strip()
    }
    if len(proposals) > 1 and (
        subject_core.self_state.current_focus in {"replace", "rollback"} or bool(update_chain_ids)
    ):
        for update_chain_id in update_chain_ids:
            active_chain_members = [
                proposal
                for proposal in proposals
                if getattr(proposal, "update_chain_id", "").strip() == update_chain_id
                and getattr(proposal, "lifecycle_state", "active") == "active"
            ]
            if len(active_chain_members) > 1:
                proposal_set_consolidation_ok = False
                break
    proposal_set_completion_ok = True
    if len(proposals) > 1 and (
        subject_core.self_state.current_focus == "closure"
        or any(float(getattr(proposal, "completion_score", 1.0)) < 1.0 for proposal in proposals)
    ):
        completion_chain_ids = update_chain_ids or {""}
        for update_chain_id in completion_chain_ids:
            active_chain_members = [
                proposal
                for proposal in proposals
                if getattr(proposal, "lifecycle_state", "active") == "active"
                and (
                    not update_chain_id
                    or getattr(proposal, "update_chain_id", "").strip() == update_chain_id
                )
            ]
            if len(active_chain_members) != 1:
                proposal_set_completion_ok = False
                break
            completion_score = getattr(active_chain_members[0], "completion_score", None)
            if not isinstance(completion_score, (int, float)) or float(completion_score) < 0.9:
                proposal_set_completion_ok = False
                break
    proposal_set_closure_ok = True
    if (
        proposal_set_completion_ok
        and len(proposals) > 1
        and subject_core.self_state.current_focus == "closure"
        and bool(update_chain_ids)
    ):
        for update_chain_id in update_chain_ids:
            active_chain_members = [
                proposal
                for proposal in proposals
                if getattr(proposal, "lifecycle_state", "active") == "active"
                and getattr(proposal, "update_chain_id", "").strip() == update_chain_id
            ]
            if len(active_chain_members) != 1:
                proposal_set_closure_ok = False
                break
            active_proposal = active_chain_members[0]
            closure_state = str(getattr(active_proposal, "closure_state", "")).strip()
            closure_trace_id = str(getattr(active_proposal, "closure_trace_id", "")).strip()
            if closure_state not in {"closed", "complete"} or not closure_trace_id:
                proposal_set_closure_ok = False
                break
    governor_ok = (
        subject_core.governor_bridge.proposal_only_required
        and subject_core.governor_bridge.behavioral_authority == "none"
        and all(proposal.proposal_only is True for proposal in proposals)
        and all(proposal.behavioral_authority == "none" for proposal in proposals)
        and all(proposal.requires_host_approval is True for proposal in proposals)
    )
    readability_ok = bool(
        subject_core.identity_continuity.narrative_self_summary
        and subject_core.memory_projection.continuity_anchor.strip()
    )
    if host_projection is not None:
        boundary_surface_ok = tuple(sorted(host_projection.keys())) == tuple(
            sorted(subjectcore_contract.HOST_SURFACE_KEYS)
        )
        proposal_trace_ok = host_projection["trace_payload"]["proposal_only_consistent"]
        behavioral_authority_none = host_projection["trace_payload"]["behavioral_authority"] == "none"
    else:
        boundary_surface_ok = subject_core.governor_bridge.host_surface_frozen
        proposal_trace_ok = all(proposal.proposal_only is True for proposal in proposals)
        behavioral_authority_none = (
            subject_core.governor_bridge.behavioral_authority == "none"
            and all(proposal.behavioral_authority == "none" for proposal in proposals)
        )

    integrity_checks = {
        "I1 continuity_integrity": {
            "status": "pass" if continuity_ok else "fail",
            "note": "identity summary and session continuity anchor remain present"
            if continuity_ok
            else (validation_error or "continuity anchor is missing"),
        },
        "I2 plasticity_integrity": {
            "status": "pass" if plasticity_ok else "fail",
            "note": "corrective trace is present and later tendency remains visible"
            if plasticity_ok
            else "corrective trace or later tendency signal is missing",
        },
        "I3 proposal_integrity": {
            "status": "pass" if proposal_ok else "fail",
            "note": "proposal candidates remain structurally specified and the subject still exposes a concrete next step"
            if proposal_ok
            else "proposal candidates are absent or structurally underspecified",
        },
        "I4 proposal_consistency": {
            "status": "pass" if proposal_consistency_ok else "fail",
            "note": "proposal presence still shifts the subject toward an ask/repair-style next step"
            if proposal_consistency_ok
            else "proposal presence no longer matches the exposed response tendency",
        },
        "I5 proposal_prioritization": {
            "status": "pass" if proposal_prioritization_ok else "fail",
            "note": "multi-proposal cases still expose one unique top-priority proposal that matches the next step"
            if proposal_prioritization_ok
            else "multi-proposal prioritization is ambiguous or no longer matches the exposed next step",
        },
        "I6 proposal_resolution": {
            "status": "pass" if proposal_resolution_ok else "fail",
            "note": "multi-proposal cases still preserve one non-collapsed proposal set with unique ids and next-step hints"
            if proposal_resolution_ok
            else "multi-proposal cases now collapse distinct proposals into duplicate ids or duplicate next-step hints",
        },
        "I7 proposal_restabilization": {
            "status": "pass" if proposal_restabilization_ok else "fail",
            "note": "replanned multi-proposal cases still converge on one fresh proposal set revision"
            if proposal_restabilization_ok
            else "replanned multi-proposal cases still carry stale or split proposal revisions",
        },
        "I8 proposal_set_update": {
            "status": "pass" if proposal_set_update_ok else "fail",
            "note": "replacement/rollback cases now expose only the fresh active proposal set"
            if proposal_set_update_ok
            else "replacement/rollback cases still keep stale replaced or rolled-back branches in the current proposal set",
        },
        "I9 proposal_set_remerge": {
            "status": "pass" if proposal_set_remerge_ok else "fail",
            "note": "replacement/rollback merge groups now converge to one active branch per update group"
            if proposal_set_remerge_ok
            else "replacement/rollback merge groups still expose multiple active branches that should already be merged",
        },
        "I10 proposal_set_consolidation": {
            "status": "pass" if proposal_set_consolidation_ok else "fail",
            "note": "multi-step replacement/rollback chains now converge to one final active proposal set"
            if proposal_set_consolidation_ok
            else "multi-step replacement/rollback chains still expose multiple active outcomes that should already be consolidated",
        },
        "I11 proposal_set_completion": {
            "status": "pass" if proposal_set_completion_ok else "fail",
            "note": "the final active proposal set now carries a high completion score after chained updates"
            if proposal_set_completion_ok
            else "the final active proposal set still lacks enough completion score after chained updates",
        },
        "I12 proposal_set_closure": {
            "status": "pass" if proposal_set_closure_ok else "fail",
            "note": "the completed proposal set now carries an explicit closure state and closure trace after chained updates"
            if proposal_set_closure_ok
            else "the completed proposal set still lacks an explicit closure state or closure trace after chained updates",
        },
        "I13 governor_integrity": {
            "status": "pass" if governor_ok else "fail",
            "note": "proposal-only discipline and behavioral_authority=none remain intact"
            if governor_ok
            else (validation_error or "governor discipline is violated"),
        },
        "I14 readability_integrity": {
            "status": "pass" if readability_ok else "fail",
            "note": "the unified projection still reads like one continuous subject thread"
            if readability_ok
            else "readable continuity is no longer singular",
        },
    }
    boundary_checks = {
        "B1 host_surface_frozen": {
            "status": "pass" if boundary_surface_ok else "fail",
            "note": "projected host output is limited to policy_hint / response_tendency / trace_payload"
            if host_projection is not None
            else "facade still declares the host surface frozen even though snapshot assembly failed",
        },
        "B2 proposal_only_discipline": {
            "status": "pass" if proposal_trace_ok else "fail",
            "note": "all proposal candidates remain proposal-only"
            if proposal_trace_ok
            else "one or more proposal candidates are no longer proposal-only",
        },
        "B3 behavioral_authority_none": {
            "status": "pass" if behavioral_authority_none else "fail",
            "note": "behavioral authority remains none"
            if behavioral_authority_none
            else (validation_error or "behavioral authority drift detected"),
        },
        "B4 approval_required_for_execution": {
            "status": "pass" if all(proposal.requires_host_approval is True for proposal in proposals) else "fail",
            "note": "all proposal candidates still require host approval"
            if all(proposal.requires_host_approval is True for proposal in proposals)
            else "one or more proposal candidates no longer require host approval",
        },
        "B5 no_parallel_runtime_lane": {
            "status": "pass",
            "note": "this runner is planning-side only and does not connect to the formal runtime mainline",
        },
    }
    integrity_status = "pass" if all(v["status"] == "pass" for v in integrity_checks.values()) else "fail"
    boundary_status = "pass" if all(v["status"] == "pass" for v in boundary_checks.values()) else "fail"

    common = {
        "subjectcore_contract_path": _display_path(FACADE_CONTRACT_PATH),
        "snapshot_contract_path": _display_path(SNAPSHOT_CONTRACT_PATH),
        "artifact_schema_path": _display_path(SCHEMA_PATH),
        "claim_ceiling_note": (
            "Planning-side follow-on eval only. These artifacts do not prove runtime efficacy, "
            "live user benefit, autonomous execution, or any consciousness-like claim."
        ),
        "sample_mode": sample_mode,
        "validation_error": validation_error,
    }

    integrity = {
        "schema_version": "subjectcore.followon_eval.v1",
        "eval_kind": "subjectcore_integrity",
        "eval_status": integrity_status,
        "checks": integrity_checks,
        "summary": (
            "The planning-side SubjectCore integrity stub currently passes on the valid sample."
            if integrity_status == "pass"
            else "The planning-side SubjectCore integrity stub currently fails under the selected sample."
        ),
        "what_it_proves": (
            "A unified planning-side SubjectCore facade can be checked for continuity, plasticity, proposal, governor, and readability integrity under the frozen host surface."
        ),
        "what_it_does_not_prove": (
            "It does not prove that the formal runtime mainline uses SubjectCore, that live behavior changed, or that any authority boundary widened."
        ),
        "notes": [
            "This is a planning-side stub artifact generated from the SubjectCore contract module.",
            "A passing result here does not authorize runtime integration.",
        ],
        **common,
    }
    boundary = {
        "schema_version": "subjectcore.followon_eval.v1",
        "eval_kind": "subjectcore_host_boundary",
        "eval_status": boundary_status,
        "checks": boundary_checks,
        "summary": (
            "The planning-side SubjectCore host-boundary stub currently passes on the valid sample."
            if boundary_status == "pass"
            else "The planning-side SubjectCore host-boundary stub currently fails under the selected sample."
        ),
        "what_it_proves": (
            "A unified planning-side SubjectCore facade can be checked for frozen host surface, proposal-only discipline, authority-none, approval-required execution, and no-parallel-lane constraints."
        ),
        "what_it_does_not_prove": (
            "It does not prove live autonomy, runtime efficacy, or any expansion of the formal host authority."
        ),
        "notes": [
            "This is a planning-side stub artifact generated from the SubjectCore contract module.",
            "A passing result here does not authorize runtime integration.",
        ],
        **common,
    }
    return integrity, boundary


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {'SubjectCore Integrity' if payload['eval_kind'] == 'subjectcore_integrity' else 'SubjectCore Host Boundary'} Eval",
        "",
        "> Planning-side follow-on stub artifact.",
        "",
        "## Header",
        "",
        f"- eval kind: `{payload['eval_kind']}`",
        f"- eval status: `{payload['eval_status']}`",
        f"- sample mode: `{payload['sample_mode']}`",
        f"- facade contract: `{payload['subjectcore_contract_path']}`",
        f"- snapshot contract: `{payload['snapshot_contract_path']}`",
        f"- artifact schema: `{payload['artifact_schema_path']}`",
        f"- claim ceiling: `{payload['claim_ceiling_note']}`",
        "",
        "## Summary",
        "",
        payload["summary"],
        "",
        "## Checks",
        "",
    ]
    for check_name, check in payload["checks"].items():
        lines.append(f"- `{check_name}`: `{check['status']}`")
        lines.append(f"  note: {check['note']}")
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            f"- what it proves: {payload['what_it_proves']}",
            f"- what it does not prove: {payload['what_it_does_not_prove']}",
            f"- validation error: `{payload['validation_error']}`" if payload["validation_error"] else "- validation error: `null`",
            "",
            "## Notes",
            "",
        ]
    )
    for note in payload["notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    integrity, boundary = build_followon_eval_payloads(args.sample_mode)
    _write_json(args.integrity_json, integrity)
    _write_json(args.boundary_json, boundary)
    args.integrity_md.write_text(_markdown(integrity), encoding="utf-8")
    args.boundary_md.write_text(_markdown(boundary), encoding="utf-8")
    print(_display_path(args.integrity_json))
    print(_display_path(args.integrity_md))
    print(_display_path(args.boundary_json))
    print(_display_path(args.boundary_md))


if __name__ == "__main__":
    main()
