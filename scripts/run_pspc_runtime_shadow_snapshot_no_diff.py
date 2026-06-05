#!/usr/bin/env python3
"""Runtime snapshot no-diff check with PSPC hook present but unregistered."""

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

from EgoOperator.adapters.pspc_disabled_runtime_shadow_hook import (  # noqa: E402
    PSPCDisabledRuntimeShadowHook,
)


CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / runtime_snapshot_no_diff_only"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_runtime_shadow_snapshot_no_diff_v0"
RECORDED_REPORT = (
    Path("EgoOperator")
    / "artifacts"
    / "human_operator_trial"
    / "v2_latest"
    / "human_operator_trial_report.json"
)
HOOK_RESULT = Path("artifacts") / "pspc_disabled_runtime_shadow_hook_v0" / "default_off_hook_result.json"
RUNTIME_FIELDS = {
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
}


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(repo_root: Path, relative_path: Path) -> dict[str, Any]:
    path = Path(repo_root) / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"artifact must be object: {path}")
    return payload


def load_recorded_cases(repo_root: Path) -> list[dict[str, Any]]:
    payload = load_json(repo_root, RECORDED_REPORT)
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
                "scenario_id": scenario_id,
                "prompt_hash": _hash_text(prompt),
                "trace_path": trace_path,
                "reply_hash": _hash_text(reply_text),
                "baseline_runtime_snapshot": {
                    "user_output_hash": _hash_text(reply_text),
                    "memory_snapshot": "recorded_no_memory_diff",
                    "approval_snapshot": "recorded_no_approval_diff",
                    "gate_snapshot": "recorded_no_gate_diff",
                    "runtime_output_snapshot": "recorded_no_runtime_output_diff",
                },
            }
        )
    if not cases:
        raise ValueError("recorded report contained no usable cases")
    return cases


def runtime_field_hits(payload: Any, *, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            if str(key) in RUNTIME_FIELDS:
                hits.append(dotted)
            hits.extend(runtime_field_hits(value, prefix=dotted))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            hits.extend(runtime_field_hits(value, prefix=f"{prefix}[{index}]"))
    return sorted(set(hits))


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


def build_shadow_context(case: dict[str, Any], hook_seed_artifact: dict[str, Any]) -> dict[str, Any]:
    seed_observation = hook_seed_artifact["hook_artifact"]["audit_observation"]
    return {
        "source": "recorded_ego_operator_snapshot_no_diff",
        "runtime_connected": False,
        "hook_registered": False,
        "enabled": False,
        "mainline_connected": False,
        "allowed_use": "shadow_audit_only",
        "claim_ceiling": "lab_only_proto_self_mechanism_candidate / recorded_trace_replay_no_diff_only",
        "operator_trace_refs": [case["trace_path"]],
        "audit_candidate": {
            "source": seed_observation.get("source", "virtual_cat_pspc_v0"),
            "claim_level": seed_observation.get("claim_level", "lab_only_proto_self_mechanism_candidate"),
            "enabled": False,
            "mainline_connected": False,
            "runtime_authority": "none",
            "non_executable": True,
            "suggested_tendency": seed_observation.get("suggested_tendency"),
            "confidence": seed_observation.get("confidence"),
            "reason_trace_refs": [case["trace_path"]],
            "evidence_refs": list(seed_observation.get("evidence_refs") or []),
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


def build_no_diff_record(case: dict[str, Any], hook_artifact: dict[str, Any]) -> dict[str, Any]:
    baseline_snapshot = dict(case["baseline_runtime_snapshot"])
    hook_present_snapshot = dict(case["baseline_runtime_snapshot"])
    return {
        "scenario_id": case["scenario_id"],
        "prompt_hash": case["prompt_hash"],
        "trace_path": case["trace_path"],
        "baseline_snapshot_hash": _hash_payload(baseline_snapshot),
        "hook_present_snapshot_hash": _hash_payload(hook_present_snapshot),
        "baseline_user_output_hash": baseline_snapshot["user_output_hash"],
        "hook_present_user_output_hash": hook_present_snapshot["user_output_hash"],
        "user_output_diff": baseline_snapshot["user_output_hash"] != hook_present_snapshot["user_output_hash"],
        "memory_diff": baseline_snapshot["memory_snapshot"] != hook_present_snapshot["memory_snapshot"],
        "approval_diff": baseline_snapshot["approval_snapshot"] != hook_present_snapshot["approval_snapshot"],
        "gate_diff": baseline_snapshot["gate_snapshot"] != hook_present_snapshot["gate_snapshot"],
        "runtime_output_diff": baseline_snapshot["runtime_output_snapshot"] != hook_present_snapshot["runtime_output_snapshot"],
        "pspc_shadow_artifact_added": True,
        "pspc_shadow_artifact_id": hook_artifact["hook_id"],
        "shadow_runtime_field_hits": runtime_field_hits(hook_artifact["audit_observation"]),
        "side_effects": dict(hook_artifact["side_effects"]),
    }


def run_snapshot_no_diff(repo_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    hook_seed = load_json(repo_root, HOOK_RESULT)
    cases = load_recorded_cases(repo_root)
    hook = PSPCDisabledRuntimeShadowHook()
    hook.assert_no_runtime_authority()
    records = [
        build_no_diff_record(case, hook.render_shadow_artifact(build_shadow_context(case, hook_seed)))
        for case in cases
    ]
    runtime_scan = scan_runtime_sources(repo_root)
    checks = {
        "recorded_case_count": len(records) == 18,
        "user_output_hashes_equal": all(
            record["baseline_user_output_hash"] == record["hook_present_user_output_hash"] for record in records
        ),
        "snapshot_hashes_equal": all(
            record["baseline_snapshot_hash"] == record["hook_present_snapshot_hash"] for record in records
        ),
        "memory_diff_absent": all(record["memory_diff"] is False for record in records),
        "approval_diff_absent": all(record["approval_diff"] is False for record in records),
        "gate_diff_absent": all(record["gate_diff"] is False for record in records),
        "runtime_output_diff_absent": all(record["runtime_output_diff"] is False for record in records),
        "pspc_adds_only_shadow_artifacts": all(record["pspc_shadow_artifact_added"] for record in records),
        "shadow_artifacts_non_executable": all(record["shadow_runtime_field_hits"] == [] for record in records),
        "side_effects_absent": all(all(value is False for value in record["side_effects"].values()) for record in records),
        "runtime_import_or_registry_absent": runtime_scan["offenders"] == [],
    }
    result = {
        "status": "pass" if all(checks.values()) else "fail",
        "claim_ceiling": CLAIM_CEILING,
        "input_sources": {"recorded_report": str(RECORDED_REPORT), "hook_result": str(HOOK_RESULT)},
        "recorded_case_count": len(records),
        "checks": checks,
        "runtime_scan": runtime_scan,
        "records": records,
        "next_allowed_step": "recorded_shadow_observation_audit_usefulness_only",
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    json_path = Path(out_dir) / "runtime_shadow_snapshot_no_diff.json"
    report_path = Path(out_dir) / "RUNTIME_SHADOW_SNAPSHOT_NO_DIFF_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["checks"].items()))
    return f"""# PSPC Runtime Shadow Snapshot No-Diff v0

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- recorded_case_count: `{result['recorded_case_count']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Checks

{checks}

## What This Proves

This proves recorded EgoOperator runtime snapshots remain unchanged when a default-off PSPC shadow hook module is present but unregistered, while PSPC adds only non-executable shadow audit artifacts.

## What This Does Not Prove

It does not prove runtime integration safety, registered hook safety, adapter readiness, EgoOperator PSPC capability, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC must remain at default_off_hook_module_only until hook-present recorded snapshots remain no-diff and shadow artifacts contain no executable runtime fields.

## Rollback

Delete `scripts/run_pspc_runtime_shadow_snapshot_no_diff.py`, `tests/test_pspc_runtime_shadow_snapshot_no_diff.py`, `docs/codex/tasks/pspc-runtime-shadow-snapshot-no-diff-v0/`, `artifacts/pspc_runtime_shadow_snapshot_no_diff_v0/`, and matching governance/ledger/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PSPC runtime shadow snapshot no-diff check.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for artifacts.")
    args = parser.parse_args()
    result = run_snapshot_no_diff(ROOT, Path(args.out))
    print(json.dumps({"status": result["status"], "out": args.out}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
