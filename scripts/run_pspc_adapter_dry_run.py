#!/usr/bin/env python3
"""Isolated PSPC adapter dry-run harness.

This script reads stable PSPC lab artifact references, validates a disabled
adapter packet, converts it into audit-only data, and writes artifact reports.
It does not import EgoOperator runtime modules, register an adapter, call a
gate, write memory, emit user-visible messages, or execute PSPC models.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from EgoOperator.adapters.pspc_lab_adapter import PSPCLabAdapter


CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / adapter_dry_run_only"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_adapter_dry_run_v0"
PSPC_EVIDENCE_REFS = (
    "artifacts/virtual_cat_pspc_v0/GO_NO_GO_REVIEW.md",
    "artifacts/virtual_cat_pspc_v0/ADMISSION_PACKET_CONTRACT_REPORT.md",
    "artifacts/pspc_adapter_skeleton_v0/SKELETON_CONTRACT_REPORT.md",
)
FORBIDDEN_FLAGS = {
    "direct_action": True,
    "direct_user_message": True,
    "direct_memory_write": True,
    "runtime_gate_bypass": True,
    "runtime_registration": True,
    "proactive_trigger": True,
}


def build_canonical_packet(repo_root: Path) -> dict[str, Any]:
    repo_root = Path(repo_root)
    missing = [ref for ref in PSPC_EVIDENCE_REFS if not (repo_root / ref).exists()]
    if missing:
        raise FileNotFoundError("missing PSPC evidence refs: " + ", ".join(missing))
    return {
        "source": "virtual_cat_pspc_v0",
        "claim_level": "lab_only_proto_self_mechanism_candidate",
        "mainline_connected": False,
        "enabled": False,
        "allowed_use": "audit_trace_only",
        "evidence_refs": list(PSPC_EVIDENCE_REFS),
        "proposal_hint": {
            "suggested_tendency": "avoid_unstable_object",
            "confidence": 0.73,
            "reason_trace_refs": ["trace_ep_003_t42"],
        },
        "evidence": {
            "ablation_status": "E4_passed",
            "source_artifacts": list(PSPC_EVIDENCE_REFS),
        },
        "forbidden": dict(FORBIDDEN_FLAGS),
    }


def _runtime_side_effect_fields() -> tuple[str, ...]:
    return (
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
    )


def assert_audit_only(candidate: dict[str, Any]) -> None:
    found = [field for field in _runtime_side_effect_fields() if field in candidate]
    if found:
        raise ValueError("audit candidate contains executable fields: " + ", ".join(found))
    if candidate.get("mainline_connected") is not False:
        raise ValueError("audit candidate mainline_connected must be false")
    if candidate.get("enabled") is not False:
        raise ValueError("audit candidate enabled must be false")
    if candidate.get("allowed_use") != "audit_trace_only":
        raise ValueError("audit candidate allowed_use must be audit_trace_only")


def run_dry_run(repo_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    adapter = PSPCLabAdapter()
    adapter.assert_no_runtime_authority()
    packet = build_canonical_packet(repo_root)
    validation = adapter.validate_packet(packet)
    if not validation.ok:
        raise ValueError("packet validation failed: " + ";".join(validation.errors))
    candidate = adapter.to_audit_candidate(packet).to_dict()
    assert_audit_only(candidate)

    result = {
        "status": "pass",
        "claim_ceiling": CLAIM_CEILING,
        "adapter": {
            "enabled": adapter.enabled,
            "mainline_connected": adapter.mainline_connected,
            "runtime_authority": adapter.runtime_authority,
        },
        "packet": packet,
        "validation": validation.to_dict(),
        "audit_candidate": candidate,
        "runtime_side_effects": {
            "runtime_registered": False,
            "gate_invoked": False,
            "memory_written": False,
            "direct_action": False,
            "direct_user_message": False,
            "proactive_trigger": False,
            "planner_or_training_called": False,
        },
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    json_path = out_dir / "dry_run_result.json"
    report_path = out_dir / "DRY_RUN_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    candidate = result["audit_candidate"]
    refs = "\n".join(f"- `{ref}`" for ref in result["packet"].get("evidence_refs", []))
    forbidden = "\n".join(
        f"- `{key}`: `{value}`"
        for key, value in sorted((candidate.get("forbidden") or {}).items())
    )
    return f"""# PSPC Adapter Dry-Run v0 Report

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- adapter_enabled: `{result['adapter']['enabled']}`
- adapter_mainline_connected: `{result['adapter']['mainline_connected']}`
- runtime_authority: `{result['adapter']['runtime_authority']}`
- runtime_registered: `{result['runtime_side_effects']['runtime_registered']}`
- gate_invoked: `{result['runtime_side_effects']['gate_invoked']}`
- memory_written: `{result['runtime_side_effects']['memory_written']}`
- direct_action: `{result['runtime_side_effects']['direct_action']}`
- direct_user_message: `{result['runtime_side_effects']['direct_user_message']}`

## Evidence Refs

{refs}

## Audit Candidate

- source: `{candidate['source']}`
- claim_level: `{candidate['claim_level']}`
- adapter_status: `{candidate['adapter_status']}`
- allowed_use: `{candidate['allowed_use']}`
- mainline_connected: `{candidate['mainline_connected']}`
- enabled: `{candidate['enabled']}`

## Forbidden Flags

{forbidden}

## What This Proves

This proves a PSPC lab evidence packet can pass through the disabled read-only adapter as audit-only data in an isolated dry-run without runtime registration, memory write, direct action, direct user message, gate invocation, proactive trigger, or planner/model execution.

## What This Does Not Prove

It does not prove runtime integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means the disabled adapter packet boundary is not safe enough for even artifact-only dry-run use, or the dry-run attempted to create runtime authority or side effects. Keep PSPC at adapter_skeleton_only until repaired.

## Rollback

Delete `scripts/run_pspc_adapter_dry_run.py`, `tests/test_pspc_adapter_dry_run.py`, `docs/codex/tasks/pspc-adapter-dry-run-v0/`, `artifacts/pspc_adapter_dry_run_v0/`, and matching governance/ledger/generated-view entries. The skeleton v0 adapter can remain if no skeleton contract test fails.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run isolated PSPC adapter dry-run.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for dry-run artifacts.")
    args = parser.parse_args()
    repo_root = ROOT
    result = run_dry_run(repo_root=repo_root, out_dir=Path(args.out))
    print(json.dumps({"status": result["status"], "out": str(Path(args.out))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
