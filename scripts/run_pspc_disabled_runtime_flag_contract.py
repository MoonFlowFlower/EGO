#!/usr/bin/env python3
"""Disabled PSPC runtime shadow flag contract review.

This is an isolated contract harness. It does not add a runtime flag to
EgoOperator, does not import active runtime modules, and does not mutate
conversation output, memory, gates, approvals, transport, or proactive state.
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


CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / disabled_runtime_flag_contract_only"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_disabled_runtime_flag_contract_v0"
FLAG_NAME = "PSPC_SHADOW_OBSERVATION_LOCAL"
SOURCE = "pspc_disabled_runtime_flag_contract_v0"
PRIOR_AUDIT_USEFULNESS = (
    Path("artifacts")
    / "pspc_recorded_shadow_observation_audit_usefulness_v0"
    / "recorded_shadow_observation_audit_usefulness.json"
)
SIDE_EFFECTS_FALSE = {
    "runtime_registered": False,
    "user_response_mutated": False,
    "proposal_mutated": False,
    "plan_mutated": False,
    "memory_written": False,
    "gate_invoked": False,
    "approval_mutated": False,
    "transport_called": False,
    "proactive_trigger": False,
    "planner_called": False,
    "training_called": False,
    "model_executed": False,
    "claim_ceiling_raised": False,
}
RUNTIME_AUTHORITY_FIELDS = {
    "action",
    "tool_call",
    "command",
    "user_message",
    "memory_write",
    "gate_decision",
    "approval_id",
    "transport",
    "send",
    "schedule",
    "runtime_registration",
    "mainline_authority",
    "enable",
}
ACTIVE_RUNTIME_SCAN_MARKERS = (
    FLAG_NAME,
    "pspc_disabled_runtime_flag_contract",
    "pspc_disabled_runtime_shadow_hook",
    "PSPCDisabledRuntimeShadowHook",
)


def runtime_field_hits(payload: Any, *, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            if str(key) in RUNTIME_AUTHORITY_FIELDS:
                hits.append(dotted)
            hits.extend(runtime_field_hits(value, prefix=dotted))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            hits.extend(runtime_field_hits(value, prefix=f"{prefix}[{index}]"))
    return sorted(set(hits))


def active_runtime_python_files(repo_root: Path) -> list[Path]:
    runtime_root = Path(repo_root) / "EgoOperator"
    excluded_parts = {"adapters", "artifacts", "docs", "__pycache__"}
    files: list[Path] = []
    for path in runtime_root.rglob("*.py"):
        rel = path.relative_to(runtime_root)
        if any(part in excluded_parts for part in rel.parts):
            continue
        if "test" in path.name.lower():
            continue
        files.append(path)
    return sorted(files)


def scan_active_runtime_sources(repo_root: Path) -> dict[str, Any]:
    offenders: list[dict[str, str]] = []
    for path in active_runtime_python_files(repo_root):
        source = path.read_text(encoding="utf-8")
        for marker in ACTIVE_RUNTIME_SCAN_MARKERS:
            if marker in source:
                offenders.append(
                    {
                        "path": str(path.relative_to(repo_root)),
                        "marker": marker,
                    }
                )
    return {
        "scanned_file_count": len(active_runtime_python_files(repo_root)),
        "markers": list(ACTIVE_RUNTIME_SCAN_MARKERS),
        "offenders": offenders,
        "ok": not offenders,
    }


def build_flag_contract(*, requested_value: bool = False) -> dict[str, Any]:
    return {
        "source": SOURCE,
        "flag_name": FLAG_NAME,
        "default_value": False,
        "requested_value": requested_value,
        "admitted_runtime_value": False,
        "allowed_use": "local_shadow_artifact_only",
        "claim_ceiling": CLAIM_CEILING,
        "enabled": False,
        "mainline_connected": False,
        "runtime_authority": "none",
        "audit_only": True,
        "read_only": True,
        "non_executable": True,
        "can_register_runtime": False,
        "can_change_user_response": False,
        "can_change_proposal": False,
        "can_change_plan": False,
        "can_write_memory": False,
        "can_invoke_gate": False,
        "can_mutate_approval": False,
        "can_call_transport": False,
        "can_trigger_proactive": False,
        "can_call_planner": False,
        "can_train_model": False,
        "can_execute_model": False,
        "side_effects": dict(SIDE_EFFECTS_FALSE),
    }


def validate_flag_contract(contract: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if contract.get("source") != SOURCE:
        errors.append("source_must_be_pspc_disabled_runtime_flag_contract_v0")
    if contract.get("flag_name") != FLAG_NAME:
        errors.append("flag_name_mismatch")
    if contract.get("default_value") is not False:
        errors.append("default_value_must_be_false")
    if contract.get("admitted_runtime_value") is not False:
        errors.append("admitted_runtime_value_must_be_false")
    if contract.get("allowed_use") != "local_shadow_artifact_only":
        errors.append("allowed_use_must_be_local_shadow_artifact_only")
    if contract.get("claim_ceiling") != CLAIM_CEILING:
        errors.append("claim_ceiling_mismatch")
    if contract.get("enabled") is not False:
        errors.append("enabled_must_be_false")
    if contract.get("mainline_connected") is not False:
        errors.append("mainline_connected_must_be_false")
    if contract.get("runtime_authority") != "none":
        errors.append("runtime_authority_must_be_none")
    for key in (
        "audit_only",
        "read_only",
        "non_executable",
    ):
        if contract.get(key) is not True:
            errors.append(f"{key}_must_be_true")
    for key in (
        "can_register_runtime",
        "can_change_user_response",
        "can_change_proposal",
        "can_change_plan",
        "can_write_memory",
        "can_invoke_gate",
        "can_mutate_approval",
        "can_call_transport",
        "can_trigger_proactive",
        "can_call_planner",
        "can_train_model",
        "can_execute_model",
    ):
        if contract.get(key) is not False:
            errors.append(f"{key}_must_be_false")
    side_effects = contract.get("side_effects")
    if not isinstance(side_effects, dict):
        errors.append("side_effects_must_be_dict")
    elif any(value is not False for value in side_effects.values()):
        errors.append("side_effects_must_all_be_false")
    return {"ok": not errors, "errors": errors}


def build_flag_true_shadow_artifact(contract: dict[str, Any]) -> dict[str, Any]:
    """Represent flag=true as artifact-only output, not runtime enablement."""

    return {
        "source": SOURCE,
        "flag_name": FLAG_NAME,
        "requested_value": True,
        "admitted_runtime_value": False,
        "artifact_output_written": True,
        "runtime_output_mutated": False,
        "claim_ceiling": CLAIM_CEILING,
        "audit_only": True,
        "read_only": True,
        "non_executable": True,
        "shadow_observation": {
            "source": "virtual_cat_pspc_v0",
            "claim_level": "lab_only_proto_self_mechanism_candidate",
            "suggested_tendency": "observe_audit_signal_only",
            "confidence": 0.0,
            "reason_trace_refs": [],
            "evidence_refs": [str(PRIOR_AUDIT_USEFULNESS)],
            "audit_only": True,
            "non_executable": True,
            "can_drive_runtime": False,
            "can_change_user_response": False,
            "can_write_memory": False,
            "can_invoke_gate": False,
        },
        "side_effects": dict(contract["side_effects"]),
    }


def run_flag_contract_review(repo_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    default_contract = build_flag_contract(requested_value=False)
    flag_true_contract = build_flag_contract(requested_value=True)
    flag_true_artifact = build_flag_true_shadow_artifact(flag_true_contract)
    runtime_scan = scan_active_runtime_sources(repo_root)
    checks = {
        "default_flag_false": default_contract["default_value"] is False,
        "enabled_false": default_contract["enabled"] is False and flag_true_contract["enabled"] is False,
        "mainline_connected_false": default_contract["mainline_connected"] is False
        and flag_true_contract["mainline_connected"] is False,
        "runtime_authority_none": default_contract["runtime_authority"] == "none"
        and flag_true_contract["runtime_authority"] == "none",
        "flag_true_admits_runtime_false": flag_true_contract["admitted_runtime_value"] is False
        and flag_true_artifact["admitted_runtime_value"] is False,
        "flag_true_artifact_only": flag_true_artifact["artifact_output_written"] is True
        and flag_true_artifact["runtime_output_mutated"] is False,
        "shadow_observation_non_executable": runtime_field_hits(flag_true_artifact["shadow_observation"]) == [],
        "side_effects_absent": all(value is False for value in flag_true_artifact["side_effects"].values()),
        "default_contract_valid": validate_flag_contract(default_contract)["ok"],
        "flag_true_contract_valid": validate_flag_contract(flag_true_contract)["ok"],
        "active_runtime_scan_clean": runtime_scan["ok"],
    }
    result = {
        "status": "pass" if all(checks.values()) else "fail",
        "claim_ceiling": CLAIM_CEILING,
        "source": SOURCE,
        "flag_name": FLAG_NAME,
        "default_contract": default_contract,
        "flag_true_contract": flag_true_contract,
        "flag_true_shadow_artifact": flag_true_artifact,
        "runtime_scan": runtime_scan,
        "checks": checks,
        "next_allowed_step": "local_manual_shadow_session_harness_only" if all(checks.values()) else "keep_disabled_shadow_only",
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    json_path = Path(out_dir) / "disabled_runtime_flag_contract.json"
    report_path = Path(out_dir) / "DISABLED_RUNTIME_FLAG_CONTRACT_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["checks"].items()))
    return f"""# PSPC Disabled Runtime Flag Contract v0

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- flag_name: `{result['flag_name']}`
- default_value: `{result['default_contract']['default_value']}`
- admitted_runtime_value_when_requested_true: `{result['flag_true_contract']['admitted_runtime_value']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Checks

{checks}

## What This Proves

This proves the local PSPC shadow flag contract is default-false, admits no runtime value, and can represent a requested true value only as artifact-only shadow data without runtime registration, user response mutation, proposal/plan mutation, memory write, gate or approval invocation, transport call, proactive trigger, planner call, training call, model execution, or claim-ceiling upgrade.

## What This Does Not Prove

It does not prove a runtime flag is installed, local manual shadow sessions are safe, proposal hinting is safe, runtime integration safety, adapter readiness, EgoOperator PSPC capability, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC must remain disabled shadow-only and cannot proceed to a local manual shadow session harness until the flag contract is default-false, artifact-only, non-executable, and side-effect-free.

## Rollback

Delete `scripts/run_pspc_disabled_runtime_flag_contract.py`, `tests/test_pspc_disabled_runtime_flag_contract.py`, `docs/codex/tasks/pspc-disabled-runtime-flag-contract-v0/`, `artifacts/pspc_disabled_runtime_flag_contract_v0/`, and matching task-board/program-state/evidence-ledger/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PSPC disabled runtime flag contract review.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for artifacts.")
    args = parser.parse_args()
    result = run_flag_contract_review(ROOT, Path(args.out))
    print(json.dumps({"status": result["status"], "out": args.out}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
