#!/usr/bin/env python3
"""Review the disabled PSPC read-only shadow hook.

This runner is artifact-only. It reads the fixture shadow trace, renders a
disabled hook audit result, scans EgoOperator runtime sources for accidental
imports, and writes review artifacts.
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

from EgoOperator.adapters.pspc_read_only_shadow_hook import PSPCReadOnlyShadowHook


CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / disabled_shadow_hook_only"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_disabled_shadow_hook_v0"
FIXTURE_TRACE = Path("artifacts") / "pspc_fixture_shadow_trace_v0" / "shadow_trace.json"


def load_fixture_inputs(repo_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path = Path(repo_root) / FIXTURE_TRACE
    if not path.exists():
        raise FileNotFoundError(f"missing fixture shadow trace: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    trace = payload.get("shadow_trace")
    if not isinstance(trace, dict):
        raise ValueError("fixture shadow trace must contain shadow_trace object")
    operator_context = trace.get("operator_context")
    audit_candidate = trace.get("pspc_audit_candidate")
    if not isinstance(operator_context, dict):
        raise ValueError("fixture shadow trace operator_context must be object")
    if not isinstance(audit_candidate, dict):
        raise ValueError("fixture shadow trace pspc_audit_candidate must be object")
    return operator_context, audit_candidate


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
        if "pspc_read_only_shadow_hook" in text or "PSPCReadOnlyShadowHook" in text:
            offenders.append(str(path.relative_to(repo_root)))
    return {"runtime_source_count": len(runtime_sources), "offenders": offenders}


def run_review(repo_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    operator_context, audit_candidate = load_fixture_inputs(repo_root)
    hook = PSPCReadOnlyShadowHook()
    hook_result = hook.render_shadow_audit(operator_context, audit_candidate)
    runtime_scan = scan_runtime_sources(repo_root)
    side_effects = dict(hook_result["side_effects"])
    checks = {
        "hook_disabled": hook_result["enabled"] is False,
        "mainline_disconnected": hook_result["mainline_connected"] is False,
        "runtime_authority_none": hook_result["runtime_authority"] == "none",
        "non_executable": hook_result["non_executable"] is True,
        "runtime_import_or_registry_absent": runtime_scan["offenders"] == [],
        "side_effects_absent": all(value is False for value in side_effects.values()),
    }
    status = "pass" if all(checks.values()) else "fail"
    result = {
        "status": status,
        "claim_ceiling": CLAIM_CEILING,
        "input_source": str(FIXTURE_TRACE),
        "hook_result": hook_result,
        "checks": checks,
        "runtime_scan": runtime_scan,
        "side_effects": side_effects,
        "next_allowed_step": "recorded_run_shadow_observation_stage_card_or_task_only",
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    json_path = Path(out_dir) / "disabled_shadow_hook_result.json"
    report_path = Path(out_dir) / "DISABLED_SHADOW_HOOK_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["checks"].items()))
    side_effects = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["side_effects"].items()))
    hook_result = result["hook_result"]
    return f"""# PSPC Disabled Shadow Hook v0

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- input_source: `{result['input_source']}`
- hook_trace_id: `{hook_result['trace_id']}`
- hook_enabled: `{hook_result['enabled']}`
- mainline_connected: `{hook_result['mainline_connected']}`
- runtime_authority: `{hook_result['runtime_authority']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Checks

{checks}

## Side Effects

{side_effects}

## What This Proves

This proves a disabled PSPC read-only shadow hook can render an audit-only observation from fixture shadow trace data while remaining default-off, mainline-disconnected, non-executable, unregistered by runtime, and side-effect-free.

## What This Does Not Prove

It does not prove runtime registration safety, live runtime hook safety, real EgoOperator trace compatibility, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC must remain at shadow_hook_stage_card_only or fixture_shadow_trace_only until the hook contract, disabled defaults, or static runtime isolation are repaired.

## Rollback

Delete `EgoOperator/adapters/pspc_read_only_shadow_hook.py`, `scripts/run_pspc_disabled_shadow_hook_review.py`, `tests/test_pspc_disabled_shadow_hook.py`, `docs/codex/tasks/pspc-disabled-shadow-hook-v0/`, `artifacts/pspc_disabled_shadow_hook_v0/`, and matching governance/ledger/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PSPC disabled shadow hook review.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for review artifacts.")
    args = parser.parse_args()
    result = run_review(repo_root=ROOT, out_dir=Path(args.out))
    print(json.dumps({"status": result["status"], "out": str(Path(args.out))}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
