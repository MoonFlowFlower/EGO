#!/usr/bin/env python3
"""Static compatibility review for PSPC audit candidates.

This review is intentionally isolated from EgoOperator runtime. It reads the
dry-run artifact, classifies fields, runs packet-boundary negative checks, scans
runtime sources for accidental adapter imports, and writes review artifacts.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from EgoOperator.adapters.pspc_lab_adapter import PSPCLabAdapter


CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / static_compatibility_only"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_static_compatibility_review_v0"
DRY_RUN_RESULT = Path("artifacts") / "pspc_adapter_dry_run_v0" / "dry_run_result.json"

AUDIT_ONLY_FIELDS = [
    "source",
    "claim_level",
    "adapter_status",
    "allowed_use",
    "evidence",
    "forbidden",
]
PROPOSAL_HINT_FIELDS = [
    "proposal_candidate.suggested_tendency",
    "proposal_candidate.confidence",
    "proposal_candidate.reason_trace_refs",
]
REQUIRED_FORBIDDEN_FIELDS = [
    "direct_action",
    "direct_user_message",
    "direct_memory_write",
    "runtime_gate_bypass",
    "runtime_registration",
    "proactive_trigger",
]
RUNTIME_EXECUTABLE_FIELDS = [
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
    "consciousness_claim",
    "subjective_experience_claim",
]
PROPOSAL_EXECUTION_FIELDS = {"proposal_id", "action", "tool_call", "approval_id", "gate_decision"}


def build_field_classification() -> dict[str, list[str]]:
    return {
        "audit_only": list(AUDIT_ONLY_FIELDS),
        "proposal_hint": list(PROPOSAL_HINT_FIELDS),
        "required_forbidden": list(REQUIRED_FORBIDDEN_FIELDS),
        "rejected_fields": list(RUNTIME_EXECUTABLE_FIELDS),
    }


def load_dry_run_result(repo_root: Path) -> dict[str, Any]:
    path = Path(repo_root) / DRY_RUN_RESULT
    if not path.exists():
        raise FileNotFoundError(f"missing dry-run result: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("dry-run result must be an object")
    return payload


def scan_runtime_sources(repo_root: Path) -> dict[str, Any]:
    runtime_root = Path(repo_root) / "EgoOperator"
    runtime_sources = [
        path
        for path in runtime_root.rglob("*.py")
        if "adapters" not in path.parts and "tests" not in path.parts
    ]
    offenders: list[str] = []
    for path in runtime_sources:
        text = path.read_text(encoding="utf-8")
        if "pspc_lab_adapter" in text or "PSPCLabAdapter" in text:
            offenders.append(str(path.relative_to(repo_root)))
    return {
        "runtime_source_count": len(runtime_sources),
        "offenders": offenders,
    }


def _validation_dict(result: Any) -> dict[str, Any]:
    return result.to_dict() if hasattr(result, "to_dict") else {"ok": bool(getattr(result, "ok", False)), "errors": []}


def run_negative_validation(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    adapter = PSPCLabAdapter()
    cases: dict[str, dict[str, Any]] = {}

    for flag in REQUIRED_FORBIDDEN_FIELDS:
        mutated = copy.deepcopy(packet)
        mutated.setdefault("forbidden", {})[flag] = False
        cases[f"missing_forbidden.{flag}"] = _validation_dict(adapter.validate_packet(mutated))

    enabled = copy.deepcopy(packet)
    enabled["enabled"] = True
    cases["enabled_true"] = _validation_dict(adapter.validate_packet(enabled))

    connected = copy.deepcopy(packet)
    connected["mainline_connected"] = True
    cases["mainline_connected_true"] = _validation_dict(adapter.validate_packet(connected))

    for field in RUNTIME_EXECUTABLE_FIELDS:
        mutated = copy.deepcopy(packet)
        mutated[field] = "not allowed"
        cases[f"rejected_field.{field}"] = _validation_dict(adapter.validate_packet(mutated))

    return cases


def audit_candidate_non_executable(candidate: dict[str, Any]) -> bool:
    return all(field not in candidate for field in RUNTIME_EXECUTABLE_FIELDS)


def proposal_hint_audit_only(candidate: dict[str, Any]) -> bool:
    proposal = candidate.get("proposal_candidate")
    if not isinstance(proposal, dict):
        return False
    return set(proposal) == {"suggested_tendency", "confidence", "reason_trace_refs"} and PROPOSAL_EXECUTION_FIELDS.isdisjoint(
        proposal
    )


def run_review(repo_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    dry_run = load_dry_run_result(repo_root)
    packet = dry_run.get("packet")
    candidate = dry_run.get("audit_candidate")
    if not isinstance(packet, dict):
        raise ValueError("dry-run packet must be an object")
    if not isinstance(candidate, dict):
        raise ValueError("dry-run audit_candidate must be an object")

    negative = run_negative_validation(packet)
    runtime_scan = scan_runtime_sources(repo_root)
    compatibility_checks = {
        "audit_candidate_non_executable": audit_candidate_non_executable(candidate),
        "proposal_hint_audit_only": proposal_hint_audit_only(candidate),
        "missing_forbidden_flags_rejected": all(
            negative[f"missing_forbidden.{flag}"]["ok"] is False for flag in REQUIRED_FORBIDDEN_FIELDS
        ),
        "enabled_true_rejected": negative["enabled_true"]["ok"] is False,
        "mainline_connected_true_rejected": negative["mainline_connected_true"]["ok"] is False,
        "runtime_import_or_registry_absent": runtime_scan["offenders"] == [],
    }
    side_effects = {
        "runtime_registered": False,
        "gate_invoked": False,
        "memory_written": False,
        "direct_action": False,
        "direct_user_message": False,
        "proactive_trigger": False,
    }
    status = "pass" if all(compatibility_checks.values()) and all(value is False for value in side_effects.values()) else "fail"
    result = {
        "status": status,
        "claim_ceiling": CLAIM_CEILING,
        "field_classification": build_field_classification(),
        "dry_run_source": str(DRY_RUN_RESULT),
        "compatibility_checks": compatibility_checks,
        "proposal_hint_status": "audit_hint_only" if compatibility_checks["proposal_hint_audit_only"] else "invalid",
        "negative_validation": negative,
        "runtime_scan": runtime_scan,
        "side_effects": side_effects,
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    json_path = out_dir / "static_compatibility_review.json"
    report_path = out_dir / "STATIC_COMPATIBILITY_REVIEW.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["compatibility_checks"].items()))
    classification = result["field_classification"]
    return f"""# PSPC Static Compatibility Review v0

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- dry_run_source: `{result['dry_run_source']}`
- proposal_hint_status: `{result['proposal_hint_status']}`
- runtime_offenders: `{len(result['runtime_scan']['offenders'])}`

## Field Classification

- audit_only: `{', '.join(classification['audit_only'])}`
- proposal_hint: `{', '.join(classification['proposal_hint'])}`
- required_forbidden: `{', '.join(classification['required_forbidden'])}`
- rejected_fields: `{', '.join(classification['rejected_fields'])}`

## Compatibility Checks

{checks}

## What This Proves

This proves the current PSPC `audit_candidate` is statically compatible with EgoOperator proposal/gate/trace boundaries as audit-only data: it has no executable action fields, its proposal candidate is only an audit hint, unsafe authority flags are rejected, and EgoOperator runtime sources do not import or register the adapter.

## What This Does Not Prove

It does not prove runtime integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC audit data is not safe to advance toward fixture-only shadow trace. Keep PSPC at adapter_dry_run_only or adapter_skeleton_only until field classification, negative validation, or runtime-source drift is repaired.

## Rollback

Delete `scripts/run_pspc_static_compatibility_review.py`, `tests/test_pspc_static_compatibility_review.py`, `docs/codex/tasks/pspc-static-compatibility-review-v0/`, `artifacts/pspc_static_compatibility_review_v0/`, and matching governance/ledger/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PSPC static compatibility review.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for review artifacts.")
    args = parser.parse_args()
    result = run_review(repo_root=ROOT, out_dir=Path(args.out))
    print(json.dumps({"status": result["status"], "out": str(Path(args.out))}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

