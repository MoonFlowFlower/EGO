#!/usr/bin/env python3
"""Review the default-off PSPC runtime shadow hook module."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from EgoOperator.adapters.pspc_disabled_runtime_shadow_hook import (  # noqa: E402
    CLAIM_CEILING,
    PSPCDisabledRuntimeShadowHook,
)


DEFAULT_OUT_DIR = Path("artifacts") / "pspc_disabled_runtime_shadow_hook_v0"


def build_fixture_shadow_context() -> dict[str, Any]:
    return {
        "source": "pspc_disabled_runtime_shadow_hook_fixture",
        "runtime_connected": False,
        "hook_registered": False,
        "enabled": False,
        "mainline_connected": False,
        "allowed_use": "shadow_audit_only",
        "claim_ceiling": CLAIM_CEILING,
        "operator_trace_refs": ["trace_ep_003_t42"],
        "audit_candidate": {
            "source": "virtual_cat_pspc_v0",
            "claim_level": "lab_only_proto_self_mechanism_candidate",
            "enabled": False,
            "mainline_connected": False,
            "runtime_authority": "none",
            "non_executable": True,
            "suggested_tendency": "avoid_unstable_object",
            "confidence": 0.73,
            "reason_trace_refs": ["trace_ep_003_t42"],
            "evidence_refs": ["artifacts/virtual_cat_pspc_v0/summary.json"],
        },
        "side_effects": {
            "runtime_registered": False,
            "user_response_mutated": False,
            "memory_written": False,
            "gate_invoked": False,
            "approval_mutated": False,
            "transport_called": False,
            "proactive_trigger": False,
            "planner_called": False,
            "training_called": False,
            "model_executed": False,
        },
    }


def scan_runtime_sources(repo_root: Path) -> dict[str, Any]:
    runtime_sources = [
        path
        for path in (Path(repo_root) / "EgoOperator").rglob("*.py")
        if "adapters" not in path.parts and "tests" not in path.parts
    ]
    markers = ("pspc_disabled_runtime_shadow_hook", "PSPCDisabledRuntimeShadowHook")
    offenders: list[str] = []
    for path in runtime_sources:
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in markers):
            offenders.append(str(path.relative_to(repo_root)))
    return {"runtime_source_count": len(runtime_sources), "offenders": offenders}


def run_review(repo_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    hook = PSPCDisabledRuntimeShadowHook()
    hook.assert_no_runtime_authority()
    shadow_context = build_fixture_shadow_context()
    validation = hook.validate_shadow_context(shadow_context)
    if not validation["ok"]:
        raise ValueError(";".join(validation["errors"]))
    artifact = hook.render_shadow_artifact(shadow_context)
    runtime_scan = scan_runtime_sources(repo_root)
    checks = {
        "hook_disabled": artifact["enabled"] is False,
        "hook_mainline_disconnected": artifact["mainline_connected"] is False,
        "hook_runtime_authority_none": artifact["runtime_authority"] == "none",
        "audit_only": artifact["audit_only"] is True,
        "read_only": artifact["read_only"] is True,
        "non_executable": artifact["non_executable"] is True,
        "side_effects_absent": all(value is False for value in artifact["side_effects"].values()),
        "runtime_import_or_registry_absent": runtime_scan["offenders"] == [],
    }
    result = {
        "status": "pass" if all(checks.values()) else "fail",
        "claim_ceiling": CLAIM_CEILING,
        "checks": checks,
        "validation": validation,
        "runtime_scan": runtime_scan,
        "hook_artifact": artifact,
        "next_allowed_step": "runtime_snapshot_no_diff_with_hook_present_only",
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    json_path = Path(out_dir) / "default_off_hook_result.json"
    report_path = Path(out_dir) / "DEFAULT_OFF_HOOK_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["checks"].items()))
    return f"""# PSPC Default-Off Runtime Shadow Hook v0

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Checks

{checks}

## What This Proves

This proves a default-off PSPC runtime shadow hook module can validate a shadow context and render audit-only, read-only, non-executable artifact data while remaining unregistered, disabled, mainline-disconnected, and free of runtime authority.

## What This Does Not Prove

It does not prove hook registration safety, runtime integration safety, adapter readiness, EgoOperator PSPC capability, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC must remain at Stage Card-only hook evidence until disabled defaults, validation, non-executable output, or runtime import isolation is repaired.

## Rollback

Delete `EgoOperator/adapters/pspc_disabled_runtime_shadow_hook.py`, `scripts/run_pspc_disabled_runtime_shadow_hook.py`, `tests/test_pspc_disabled_runtime_shadow_hook.py`, `docs/codex/tasks/pspc-disabled-runtime-shadow-hook-v0/`, `artifacts/pspc_disabled_runtime_shadow_hook_v0/`, and matching governance/ledger/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PSPC default-off runtime shadow hook review.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for review artifacts.")
    args = parser.parse_args()
    result = run_review(ROOT, Path(args.out))
    print(json.dumps({"status": result["status"], "out": args.out}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
