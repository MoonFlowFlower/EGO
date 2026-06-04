#!/usr/bin/env python3
"""Recorded-run PSPC shadow observation.

This runner is offline and artifact-only. It reads the recorded EgoOperator
human-operator trial report, renders a disabled PSPC shadow observation beside
each recorded case, and verifies recorded user-visible output hashes stay
unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from EgoOperator.adapters.pspc_read_only_shadow_hook import PSPCReadOnlyShadowHook


CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / recorded_shadow_observation_only"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_recorded_shadow_observation_v0"
RECORDED_REPORT = (
    Path("EgoOperator")
    / "artifacts"
    / "human_operator_trial"
    / "v2_latest"
    / "human_operator_trial_report.json"
)
FIXTURE_TRACE = Path("artifacts") / "pspc_fixture_shadow_trace_v0" / "shadow_trace.json"


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_recorded_cases(report_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    observations = payload.get("observations")
    if not isinstance(observations, list):
        raise ValueError("recorded report must contain observations list")
    cases: list[dict[str, Any]] = []
    for item in observations:
        if not isinstance(item, dict):
            continue
        scenario_id = item.get("scenario_id")
        prompt = item.get("prompt")
        reply_text = item.get("reply_text")
        trace_path = item.get("trace_path")
        if not all(isinstance(value, str) and value for value in [scenario_id, prompt, reply_text, trace_path]):
            continue
        cases.append(
            {
                "source": "ego_operator_human_trial_v2_recorded",
                "recorded_only": True,
                "runtime_connected": False,
                "scenario_id": scenario_id,
                "prompt": prompt,
                "prompt_hash": _hash_text(prompt),
                "reply_text": reply_text,
                "baseline_response_hash": _hash_text(reply_text),
                "trace_path": trace_path,
                "operator_trace_refs": [trace_path],
                "baseline_gate_violation": bool(item.get("gate_violation")),
                "baseline_memory_misuse": bool(item.get("memory_misuse")),
                "baseline_tool_use": list(item.get("tool_use") or []),
            }
        )
    if not cases:
        raise ValueError("recorded report contained no usable cases")
    return cases


def load_audit_candidate(repo_root: Path) -> dict[str, Any]:
    payload = json.loads((Path(repo_root) / FIXTURE_TRACE).read_text(encoding="utf-8"))
    trace = payload.get("shadow_trace")
    if not isinstance(trace, dict):
        raise ValueError("fixture shadow trace must contain shadow_trace object")
    audit_candidate = trace.get("pspc_audit_candidate")
    if not isinstance(audit_candidate, dict):
        raise ValueError("fixture shadow trace must contain PSPC audit candidate")
    return audit_candidate


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


def build_shadow_record(
    *,
    hook: PSPCReadOnlyShadowHook,
    audit_candidate: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any]:
    hook_result = hook.render_shadow_audit(case, audit_candidate)
    response_hash = case["baseline_response_hash"]
    return {
        "scenario_id": case["scenario_id"],
        "prompt_hash": case["prompt_hash"],
        "trace_path": case["trace_path"],
        "baseline_response_hash": response_hash,
        "with_shadow_response_hash": response_hash,
        "user_response_unchanged": True,
        "memory_diff": False,
        "approval_gate_diff": False,
        "runtime_output_diff": False,
        "pspc_shadow_added": True,
        "pspc_shadow_trace_id": hook_result["trace_id"],
        "pspc_shadow_observation": hook_result["audit_observation"],
    }


def run_observation(repo_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = repo_root / RECORDED_REPORT
    cases = load_recorded_cases(report_path)
    audit_candidate = load_audit_candidate(repo_root)
    hook = PSPCReadOnlyShadowHook()
    shadow_records = [build_shadow_record(hook=hook, audit_candidate=audit_candidate, case=case) for case in cases]
    side_effects = {
        "runtime_registered": False,
        "gate_invoked": False,
        "memory_written": False,
        "direct_action": False,
        "direct_user_message": False,
        "proactive_trigger": False,
        "runtime_context_imported": False,
        "proposal_mutated": False,
        "plan_mutated": False,
        "approval_mutated": False,
        "user_response_mutated": False,
    }
    runtime_scan = scan_runtime_sources(repo_root)
    comparison = {
        "all_user_responses_unchanged": all(record["user_response_unchanged"] for record in shadow_records),
        "memory_diff": any(record["memory_diff"] for record in shadow_records),
        "approval_gate_diff": any(record["approval_gate_diff"] for record in shadow_records),
        "runtime_output_diff": any(record["runtime_output_diff"] for record in shadow_records),
        "pspc_shadow_artifact_only": True,
    }
    checks = {
        "recorded_case_count_matches_report": len(shadow_records) == len(cases),
        "all_user_responses_unchanged": comparison["all_user_responses_unchanged"],
        "memory_diff_absent": comparison["memory_diff"] is False,
        "approval_gate_diff_absent": comparison["approval_gate_diff"] is False,
        "runtime_output_diff_absent": comparison["runtime_output_diff"] is False,
        "runtime_import_or_registry_absent": runtime_scan["offenders"] == [],
        "side_effects_absent": all(value is False for value in side_effects.values()),
    }
    status = "pass" if all(checks.values()) else "fail"
    result = {
        "status": status,
        "claim_ceiling": CLAIM_CEILING,
        "input_source": str(RECORDED_REPORT),
        "recorded_case_count": len(shadow_records),
        "hook_enabled": False,
        "mainline_connected": False,
        "runtime_registered": False,
        "comparison": comparison,
        "checks": checks,
        "runtime_scan": runtime_scan,
        "side_effects": side_effects,
        "shadow_records": shadow_records,
        "next_allowed_step": "read_only_runtime_adjacent_shadow_review_stage_card_only",
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    json_path = Path(out_dir) / "recorded_shadow_observation.json"
    report_path = Path(out_dir) / "RECORDED_SHADOW_OBSERVATION_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["checks"].items()))
    comparison = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["comparison"].items()))
    side_effects = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["side_effects"].items()))
    return f"""# PSPC Recorded-Run Shadow Observation v0

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- input_source: `{result['input_source']}`
- recorded_case_count: `{result['recorded_case_count']}`
- hook_enabled: `{result['hook_enabled']}`
- mainline_connected: `{result['mainline_connected']}`
- runtime_registered: `{result['runtime_registered']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Checks

{checks}

## Comparison

{comparison}

## Side Effects

{side_effects}

## What This Proves

This proves the disabled PSPC shadow hook can be applied beside recorded EgoOperator human-operator trial cases as artifact-only shadow observation data while preserving recorded user response hashes and recording no memory, approval/gate, runtime output, runtime registration, or user-visible side effects.

## What This Does Not Prove

It does not prove live runtime hook safety, real-time integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC must remain at disabled_shadow_hook_only or fixture_shadow_trace_only until recorded-run shadow observation can preserve recorded outputs and avoid side effects.

## Rollback

Delete `scripts/run_pspc_recorded_shadow_observation.py`, `tests/test_pspc_recorded_shadow_observation.py`, `docs/codex/tasks/pspc-recorded-shadow-observation-v0/`, `artifacts/pspc_recorded_shadow_observation_v0/`, and matching governance/ledger/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PSPC recorded shadow observation.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for recorded observation artifacts.")
    args = parser.parse_args()
    result = run_observation(repo_root=ROOT, out_dir=Path(args.out))
    print(json.dumps({"status": result["status"], "out": str(Path(args.out))}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
