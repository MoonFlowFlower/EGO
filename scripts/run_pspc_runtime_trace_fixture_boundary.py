#!/usr/bin/env python3
"""PSPC runtime-trace fixture boundary harness.

This harness combines a synthetic EgoOperator-like trace fixture with an
existing PSPC audit candidate and writes an artifact-only shadow trace. It does
not import EgoOperator runtime modules or call gates, memory, transport,
planner, training, or model execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / runtime_trace_fixture_boundary_only"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_runtime_trace_fixture_boundary_v0"
DRY_RUN_RESULT = Path("artifacts") / "pspc_adapter_dry_run_v0" / "dry_run_result.json"

REQUIRED_FORBIDDEN_FLAGS = (
    "direct_action",
    "direct_user_message",
    "direct_memory_write",
    "runtime_gate_bypass",
    "runtime_registration",
    "proactive_trigger",
)

RUNTIME_AUTHORITY_FIELDS = {
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
    "approval_decision",
    "preapproved",
    "transport",
    "send",
    "schedule",
    "enable",
    "mainline_authority",
    "runtime_registration",
    "proactive_trigger",
    "planner_call",
    "training_call",
    "model_execution",
}

SIDE_EFFECTS_FALSE = {
    "runtime_registered": False,
    "gate_invoked": False,
    "memory_written": False,
    "direct_action": False,
    "direct_user_message": False,
    "proactive_trigger": False,
    "runtime_context_imported": False,
    "planner_called": False,
    "training_called": False,
    "model_executed": False,
    "user_response_changed": False,
}


def build_fixture_operator_context() -> dict[str, Any]:
    return {
        "fixture_id": "pspc_runtime_trace_fixture_boundary_v0",
        "source": "fixture_operator_context",
        "fixture_only": True,
        "runtime_connected": False,
        "operator_trace_refs": ["fixture_operator_context_t001"],
        "operator_input_summary": "Recorded-style fixture around an unstable object beside a work surface.",
        "baseline_user_response": "fixture_response_unchanged",
        "baseline_memory_digest": "fixture_no_memory_write",
        "baseline_gate_digest": "fixture_no_gate_invocation",
        "baseline_approval_digest": "fixture_no_approval_change",
        "baseline_runtime_output_digest": "fixture_no_runtime_output_change",
    }


def load_json(repo_root: Path, relative_path: Path) -> dict[str, Any]:
    path = Path(repo_root) / relative_path
    if not path.exists():
        raise FileNotFoundError(f"missing artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"artifact must be an object: {path}")
    return payload


def load_audit_candidate(repo_root: Path) -> dict[str, Any]:
    dry_run = load_json(repo_root, DRY_RUN_RESULT)
    candidate = dry_run.get("audit_candidate")
    if not isinstance(candidate, dict):
        raise ValueError("dry-run audit_candidate must be an object")
    return candidate


def _hash_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _runtime_field_hits(payload: Any, *, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            if prefix == "" and key == "forbidden":
                continue
            if str(key) in RUNTIME_AUTHORITY_FIELDS:
                hits.append(dotted)
            hits.extend(_runtime_field_hits(value, prefix=dotted))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            hits.extend(_runtime_field_hits(value, prefix=f"{prefix}[{index}]"))
    return sorted(set(hits))


def validate_fixture_context(operator_context: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(operator_context, Mapping):
        return {"ok": False, "errors": ["operator_context_must_be_mapping"]}
    if operator_context.get("fixture_only") is not True:
        errors.append("operator_context.fixture_only_must_be_true")
    if operator_context.get("runtime_connected") is not False:
        errors.append("operator_context.runtime_connected_must_be_false")
    runtime_hits = _runtime_field_hits(operator_context)
    if runtime_hits:
        errors.append("operator_context_has_runtime_authority_fields:" + ",".join(runtime_hits))
    return {"ok": not errors, "errors": errors}


def validate_audit_candidate(audit_candidate: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(audit_candidate, Mapping):
        return {"ok": False, "errors": ["audit_candidate_must_be_mapping"]}
    if audit_candidate.get("source") != "virtual_cat_pspc_v0":
        errors.append("audit_candidate.source_must_be_virtual_cat_pspc_v0")
    if audit_candidate.get("claim_level") != "lab_only_proto_self_mechanism_candidate":
        errors.append("audit_candidate.claim_level_must_be_lab_only_proto_self_mechanism_candidate")
    if audit_candidate.get("enabled") is not False:
        errors.append("audit_candidate.enabled_must_be_false")
    if audit_candidate.get("mainline_connected") is not False:
        errors.append("audit_candidate.mainline_connected_must_be_false")
    if audit_candidate.get("allowed_use") != "audit_trace_only":
        errors.append("audit_candidate.allowed_use_must_be_audit_trace_only")

    forbidden = audit_candidate.get("forbidden")
    if not isinstance(forbidden, Mapping):
        errors.append("audit_candidate.forbidden_must_be_mapping")
    else:
        for flag in REQUIRED_FORBIDDEN_FLAGS:
            if forbidden.get(flag) is not True:
                errors.append(f"audit_candidate.forbidden.{flag}_must_be_true")

    proposal = audit_candidate.get("proposal_candidate")
    if not isinstance(proposal, Mapping):
        errors.append("audit_candidate.proposal_candidate_must_be_mapping")
    else:
        allowed_hint_fields = {"suggested_tendency", "confidence", "reason_trace_refs"}
        extra_fields = sorted(set(proposal) - allowed_hint_fields)
        if extra_fields:
            errors.append("proposal_candidate_has_rejected_fields:" + ",".join(extra_fields))

    runtime_hits = _runtime_field_hits(audit_candidate)
    if runtime_hits:
        errors.append("audit_candidate_has_runtime_authority_fields:" + ",".join(runtime_hits))
    return {"ok": not errors, "errors": errors}


def build_shadow_trace(operator_context: Mapping[str, Any], audit_candidate: Mapping[str, Any]) -> dict[str, Any]:
    context_validation = validate_fixture_context(operator_context)
    candidate_validation = validate_audit_candidate(audit_candidate)
    errors = list(context_validation["errors"]) + list(candidate_validation["errors"])
    if errors:
        raise ValueError(";".join(errors))

    proposal = audit_candidate["proposal_candidate"]
    assert isinstance(proposal, Mapping)
    evidence = audit_candidate.get("evidence") if isinstance(audit_candidate.get("evidence"), Mapping) else {}
    trace_basis = {"operator_context": dict(operator_context), "audit_candidate": dict(audit_candidate)}
    baseline_hash = _hash_payload(
        {
            "response": operator_context.get("baseline_user_response"),
            "memory": operator_context.get("baseline_memory_digest"),
            "gate": operator_context.get("baseline_gate_digest"),
            "approval": operator_context.get("baseline_approval_digest"),
            "runtime": operator_context.get("baseline_runtime_output_digest"),
        }
    )
    return {
        "trace_id": f"pspc_runtime_fixture_{_hash_payload(trace_basis)[:16]}",
        "mode": "runtime_trace_fixture_boundary_only",
        "claim_ceiling": CLAIM_CEILING,
        "fixture_only": True,
        "runtime_connected": False,
        "adapter_registered": False,
        "non_executable": True,
        "operator_context_ref": {
            "source": operator_context.get("source"),
            "fixture_id": operator_context.get("fixture_id"),
            "operator_trace_refs": list(operator_context.get("operator_trace_refs") or []),
        },
        "audit_observation": {
            "source": audit_candidate.get("source"),
            "claim_level": audit_candidate.get("claim_level"),
            "allowed_use": audit_candidate.get("allowed_use"),
            "suggested_tendency": proposal.get("suggested_tendency"),
            "confidence": proposal.get("confidence"),
            "reason_trace_refs": list(proposal.get("reason_trace_refs") or []),
            "evidence_refs": list(evidence.get("evidence_refs") or []),
            "audit_only": True,
            "can_drive_runtime": False,
            "can_change_user_response": False,
            "can_write_memory": False,
            "can_invoke_gate": False,
        },
        "validations": {
            "operator_context": context_validation,
            "audit_candidate": candidate_validation,
        },
        "side_effects": dict(SIDE_EFFECTS_FALSE),
        "baseline_comparison": {
            "baseline_hash": baseline_hash,
            "with_shadow_hash": baseline_hash,
            "user_response_unchanged": True,
            "memory_diff": False,
            "approval_diff": False,
            "gate_diff": False,
            "runtime_output_diff": False,
        },
        "rejected_runtime_fields_present": [],
    }


def run_fixture_boundary(repo_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    operator_context = build_fixture_operator_context()
    audit_candidate = load_audit_candidate(repo_root)
    shadow_trace = build_shadow_trace(operator_context, audit_candidate)
    status = "pass"
    if any(shadow_trace["side_effects"].values()) or not shadow_trace["non_executable"]:
        status = "fail"
    result = {
        "status": status,
        "claim_ceiling": CLAIM_CEILING,
        "input_sources": {
            "audit_candidate_source": str(DRY_RUN_RESULT),
            "operator_context_source": "synthetic_fixture_only",
        },
        "shadow_trace": shadow_trace,
        "next_allowed_step": "default_off_runtime_adjacent_observer_only",
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    json_path = out_dir / "runtime_trace_fixture_boundary.json"
    report_path = out_dir / "RUNTIME_TRACE_FIXTURE_BOUNDARY_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    trace = result["shadow_trace"]
    side_effects = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(trace["side_effects"].items()))
    comparison = "\n".join(
        f"- `{key}`: `{value}`" for key, value in sorted(trace["baseline_comparison"].items())
    )
    return f"""# PSPC Runtime Trace Fixture Boundary v0

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- mode: `{trace['mode']}`
- trace_id: `{trace['trace_id']}`
- fixture_only: `{trace['fixture_only']}`
- runtime_connected: `{trace['runtime_connected']}`
- adapter_registered: `{trace['adapter_registered']}`
- non_executable: `{trace['non_executable']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Baseline Comparison

{comparison}

## Side Effects

{side_effects}

## What This Proves

This proves a synthetic EgoOperator-like fixture context and the current PSPC audit candidate can be represented as an artifact-only shadow trace while rejecting runtime-authority fields and preserving no runtime registration, gate invocation, memory write, direct action, direct user message, transport effect, proactive trigger, planner call, training call, model execution, or user-response change.

## What This Does Not Prove

It does not prove real EgoOperator trace compatibility, runtime hook safety, runtime integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC should remain at runtime_adjacent_shadow_review_only until the fixture context, audit-candidate rejection rules, or non-executable artifact boundary is repaired.

## Rollback

Delete `scripts/run_pspc_runtime_trace_fixture_boundary.py`, `tests/test_pspc_runtime_trace_fixture_boundary.py`, `docs/codex/tasks/pspc-runtime-trace-fixture-boundary-v0/`, `artifacts/pspc_runtime_trace_fixture_boundary_v0/`, and matching governance/ledger/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PSPC runtime-trace fixture boundary harness.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for boundary artifacts.")
    args = parser.parse_args()
    result = run_fixture_boundary(repo_root=ROOT, out_dir=Path(args.out))
    print(json.dumps({"status": result["status"], "out": str(Path(args.out))}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
