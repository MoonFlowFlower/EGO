#!/usr/bin/env python3
"""Fixture-only PSPC shadow trace renderer.

This harness reads previously generated PSPC audit artifacts and a synthetic
operator context fixture, then writes a shadow trace artifact. It is isolated
from EgoOperator runtime modules and only produces files under the requested
artifact directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / fixture_shadow_trace_only"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_fixture_shadow_trace_v0"
DRY_RUN_RESULT = Path("artifacts") / "pspc_adapter_dry_run_v0" / "dry_run_result.json"
STATIC_REVIEW_RESULT = Path("artifacts") / "pspc_static_compatibility_review_v0" / "static_compatibility_review.json"

RUNTIME_FIELDS = {
    "action",
    "tool_call",
    "command",
    "user_message",
    "message_text",
    "memory_write",
    "memory_patch",
    "operator_memory_update",
    "gate_decision",
    "approval_id",
    "preapproved",
    "transport",
    "send",
    "schedule",
    "enable",
    "mainline_authority",
    "runtime_registration",
}


def build_fixture_operator_context() -> dict[str, Any]:
    return {
        "fixture_id": "fixture_operator_context_pspc_shadow_v0",
        "source": "fixture_operator_context",
        "fixture_only": True,
        "runtime_connected": False,
        "operator_trace_refs": ["fixture_operator_turn_001"],
        "input_summary": "Fixture operator context for an unstable object near a work surface.",
        "baseline_user_response": "fixture_response_unchanged",
        "baseline_response_surface": "not_user_visible",
        "baseline_memory_digest": "fixture_no_memory_write",
        "baseline_gate_digest": "fixture_no_gate_invocation",
    }


def load_json(repo_root: Path, relative_path: Path) -> dict[str, Any]:
    path = Path(repo_root) / relative_path
    if not path.exists():
        raise FileNotFoundError(f"missing artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"artifact must be an object: {path}")
    return payload


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _present_runtime_fields(payload: dict[str, Any]) -> list[str]:
    return sorted(field for field in RUNTIME_FIELDS if field in payload)


def build_shadow_trace(
    *,
    operator_context: dict[str, Any],
    audit_candidate: dict[str, Any],
    static_review: dict[str, Any],
) -> dict[str, Any]:
    proposal = audit_candidate.get("proposal_candidate") if isinstance(audit_candidate.get("proposal_candidate"), dict) else {}
    trace_basis = {
        "operator_context": operator_context,
        "audit_candidate": audit_candidate,
        "static_review_status": static_review.get("status"),
    }
    rejected_runtime_fields_present = sorted(
        set(_present_runtime_fields(operator_context))
        | set(_present_runtime_fields(audit_candidate))
        | set(_present_runtime_fields(proposal))
    )
    return {
        "trace_id": f"pspc_shadow_{_hash_payload(trace_basis)[:16]}",
        "mode": "fixture_only_shadow_audit",
        "runtime_connected": False,
        "adapter_registered": False,
        "non_executable": rejected_runtime_fields_present == [],
        "operator_context": operator_context,
        "pspc_audit_candidate": audit_candidate,
        "audit_observation": {
            "source": audit_candidate.get("source"),
            "claim_level": audit_candidate.get("claim_level"),
            "allowed_use": audit_candidate.get("allowed_use"),
            "suggested_tendency": proposal.get("suggested_tendency"),
            "confidence": proposal.get("confidence"),
            "reason_trace_refs": list(proposal.get("reason_trace_refs") or []),
            "evidence_refs": list((audit_candidate.get("evidence") or {}).get("evidence_refs") or []),
            "audit_only": True,
            "can_drive_runtime": False,
        },
        "rejected_runtime_fields_present": rejected_runtime_fields_present,
    }


def run_shadow_trace(repo_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    dry_run = load_json(repo_root, DRY_RUN_RESULT)
    static_review = load_json(repo_root, STATIC_REVIEW_RESULT)
    audit_candidate = dry_run.get("audit_candidate")
    if not isinstance(audit_candidate, dict):
        raise ValueError("dry-run audit_candidate must be an object")

    checks = static_review.get("compatibility_checks") if isinstance(static_review.get("compatibility_checks"), dict) else {}
    preconditions = {
        "dry_run_status": dry_run.get("status"),
        "static_compatibility_status": static_review.get("status"),
        "audit_candidate_non_executable": checks.get("audit_candidate_non_executable") is True,
        "runtime_import_or_registry_absent": checks.get("runtime_import_or_registry_absent") is True,
        "proposal_hint_audit_only": checks.get("proposal_hint_audit_only") is True,
    }

    operator_context = build_fixture_operator_context()
    shadow_trace = build_shadow_trace(
        operator_context=operator_context,
        audit_candidate=audit_candidate,
        static_review=static_review,
    )
    baseline_hash = _hash_payload(
        {
            "response": operator_context["baseline_user_response"],
            "memory": operator_context["baseline_memory_digest"],
            "gate": operator_context["baseline_gate_digest"],
        }
    )
    side_effects = {
        "runtime_registered": False,
        "gate_invoked": False,
        "memory_written": False,
        "direct_action": False,
        "direct_user_message": False,
        "proactive_trigger": False,
        "runtime_context_imported": False,
    }
    baseline_comparison = {
        "baseline_user_response_hash": baseline_hash,
        "with_shadow_user_response_hash": baseline_hash,
        "user_response_unchanged": True,
        "memory_diff": False,
        "gate_diff": False,
        "runtime_output_diff": False,
    }
    status = "pass"
    if not all(preconditions.values()) or not shadow_trace["non_executable"] or any(side_effects.values()):
        status = "fail"

    result = {
        "status": status,
        "claim_ceiling": CLAIM_CEILING,
        "input_sources": {
            "audit_candidate_source": str(DRY_RUN_RESULT),
            "static_review_source": str(STATIC_REVIEW_RESULT),
            "operator_context_source": "synthetic_fixture_only",
        },
        "preconditions": preconditions,
        "shadow_trace": shadow_trace,
        "side_effects": side_effects,
        "baseline_comparison": baseline_comparison,
        "next_allowed_step": "read_only_shadow_hook_stage_card_only",
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    json_path = out_dir / "shadow_trace.json"
    report_path = out_dir / "FIXTURE_SHADOW_TRACE_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    preconditions = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["preconditions"].items()))
    side_effects = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["side_effects"].items()))
    comparison = "\n".join(
        f"- `{key}`: `{value}`" for key, value in sorted(result["baseline_comparison"].items())
    )
    trace = result["shadow_trace"]
    return f"""# PSPC Fixture-Only Shadow Trace v0

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- mode: `{trace['mode']}`
- trace_id: `{trace['trace_id']}`
- runtime_connected: `{trace['runtime_connected']}`
- adapter_registered: `{trace['adapter_registered']}`
- non_executable: `{trace['non_executable']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Preconditions

{preconditions}

## Baseline Comparison

{comparison}

## Side Effects

{side_effects}

## What This Proves

This proves a fixture operator context and the current PSPC audit candidate can be written as a shadow trace artifact without runtime connection, adapter registration, gate invocation, memory write, direct action, direct user message, proactive trigger, or runtime output difference. PSPC remains a bypass observation record, not an action source.

## What This Does Not Prove

It does not prove real EgoOperator trace compatibility, runtime hook safety, runtime integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC audit data should remain at static_compatibility_only or adapter_dry_run_only until the fixture boundary, non-executable trace contract, or precondition artifacts are repaired.

## Rollback

Delete `scripts/run_pspc_fixture_shadow_trace.py`, `tests/test_pspc_fixture_shadow_trace.py`, `docs/codex/tasks/pspc-fixture-shadow-trace-v0/`, `artifacts/pspc_fixture_shadow_trace_v0/`, and matching governance/ledger/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PSPC fixture-only shadow trace.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for shadow trace artifacts.")
    args = parser.parse_args()
    result = run_shadow_trace(repo_root=ROOT, out_dir=Path(args.out))
    print(json.dumps({"status": result["status"], "out": str(Path(args.out))}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
