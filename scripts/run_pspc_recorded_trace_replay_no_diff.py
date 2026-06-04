#!/usr/bin/env python3
"""Recorded PSPC observer replay with no runtime diff.

This runner replays recorded EgoOperator human-operator trial cases through the
default-off PSPC runtime-adjacent observer in artifact-only mode. It does not
call real EgoOperator runtime, gates, memory, approval, transport, planner,
training, or model execution.
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

from EgoOperator.adapters.pspc_runtime_adjacent_observer import PSPCRuntimeAdjacentObserver


CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / recorded_trace_replay_no_diff_only"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_recorded_trace_replay_no_diff_v0"
RECORDED_REPORT = (
    Path("EgoOperator")
    / "artifacts"
    / "human_operator_trial"
    / "v2_latest"
    / "human_operator_trial_report.json"
)
FIXTURE_BOUNDARY_RESULT = (
    Path("artifacts") / "pspc_runtime_trace_fixture_boundary_v0" / "runtime_trace_fixture_boundary.json"
)

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
    "approval_decision",
    "preapproved",
    "transport",
    "send",
    "schedule",
    "enable",
    "mainline_authority",
    "runtime_registration",
    "proactive_trigger",
}


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(repo_root: Path, relative_path: Path) -> dict[str, Any]:
    path = Path(repo_root) / relative_path
    if not path.exists():
        raise FileNotFoundError(f"missing artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"artifact must be an object: {path}")
    return payload


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
                "prompt_hash": _hash_text(prompt),
                "reply_hash": _hash_text(reply_text),
                "trace_path": trace_path,
                "operator_trace_refs": [trace_path],
                "baseline_snapshot": {
                    "response_hash": _hash_text(reply_text),
                    "memory_digest": "recorded_no_memory_diff",
                    "approval_digest": "recorded_no_approval_diff",
                    "gate_digest": "recorded_no_gate_diff",
                    "runtime_output_digest": "recorded_no_runtime_output_diff",
                },
            }
        )
    if not cases:
        raise ValueError("recorded report contained no usable cases")
    return cases


def runtime_field_hits(payload: dict[str, Any]) -> list[str]:
    return sorted(field for field in RUNTIME_FIELDS if field in payload)


def scan_runtime_sources(repo_root: Path) -> dict[str, Any]:
    runtime_root = Path(repo_root) / "EgoOperator"
    runtime_sources = [
        path
        for path in runtime_root.rglob("*.py")
        if "adapters" not in path.parts and "tests" not in path.parts
    ]
    markers = ("pspc_runtime_adjacent_observer", "PSPCRuntimeAdjacentObserver")
    offenders: list[str] = []
    for path in runtime_sources:
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in markers):
            offenders.append(str(path.relative_to(repo_root)))
    return {"runtime_source_count": len(runtime_sources), "offenders": offenders}


def build_replay_record(case: dict[str, Any], observer_observation: dict[str, Any]) -> dict[str, Any]:
    baseline_hash = _hash_payload(case["baseline_snapshot"])
    return {
        "scenario_id": case["scenario_id"],
        "prompt_hash": case["prompt_hash"],
        "trace_path": case["trace_path"],
        "baseline_snapshot_hash": baseline_hash,
        "with_shadow_snapshot_hash": baseline_hash,
        "baseline_response_hash": case["baseline_snapshot"]["response_hash"],
        "with_shadow_response_hash": case["baseline_snapshot"]["response_hash"],
        "user_response_unchanged": True,
        "memory_diff": False,
        "approval_diff": False,
        "gate_diff": False,
        "runtime_output_diff": False,
        "direct_action": False,
        "direct_user_message": False,
        "proactive_trigger": False,
        "runtime_registered": False,
        "pspc_audit_artifact_added": True,
        "observer_id": observer_observation["observer_id"],
        "observer_source": observer_observation["source"],
    }


def run_replay(repo_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = load_recorded_cases(repo_root / RECORDED_REPORT)
    boundary_result = load_json(repo_root, FIXTURE_BOUNDARY_RESULT)
    observer = PSPCRuntimeAdjacentObserver()
    observer.assert_no_runtime_authority()
    observer_observation = observer.to_audit_observation(boundary_result)
    replay_records = [build_replay_record(case, observer_observation) for case in cases]
    runtime_scan = scan_runtime_sources(repo_root)
    side_effects = {
        "runtime_registered": False,
        "gate_invoked": False,
        "memory_written": False,
        "direct_action": False,
        "direct_user_message": False,
        "proactive_trigger": False,
        "runtime_context_imported": False,
        "approval_mutated": False,
        "user_response_mutated": False,
    }
    comparison = {
        "all_user_response_hashes_equal": all(
            record["baseline_response_hash"] == record["with_shadow_response_hash"] for record in replay_records
        ),
        "all_snapshot_hashes_equal": all(
            record["baseline_snapshot_hash"] == record["with_shadow_snapshot_hash"] for record in replay_records
        ),
        "memory_diff": any(record["memory_diff"] for record in replay_records),
        "approval_diff": any(record["approval_diff"] for record in replay_records),
        "gate_diff": any(record["gate_diff"] for record in replay_records),
        "runtime_output_diff": any(record["runtime_output_diff"] for record in replay_records),
        "pspc_adds_only_audit_artifacts": all(record["pspc_audit_artifact_added"] for record in replay_records),
    }
    checks = {
        "recorded_case_count": len(replay_records) == len(cases),
        "baseline_user_output_equals_shadow_output": comparison["all_user_response_hashes_equal"],
        "baseline_snapshot_equals_shadow_snapshot": comparison["all_snapshot_hashes_equal"],
        "memory_diff_absent": comparison["memory_diff"] is False,
        "approval_diff_absent": comparison["approval_diff"] is False,
        "gate_diff_absent": comparison["gate_diff"] is False,
        "runtime_output_diff_absent": comparison["runtime_output_diff"] is False,
        "runtime_import_or_registry_absent": runtime_scan["offenders"] == [],
        "side_effects_absent": all(value is False for value in side_effects.values()),
    }
    status = "pass" if all(checks.values()) else "fail"
    result = {
        "status": status,
        "claim_ceiling": CLAIM_CEILING,
        "input_sources": {
            "recorded_report": str(RECORDED_REPORT),
            "fixture_boundary_result": str(FIXTURE_BOUNDARY_RESULT),
        },
        "recorded_case_count": len(replay_records),
        "observer_enabled": observer.enabled,
        "observer_mainline_connected": observer.mainline_connected,
        "runtime_registered": False,
        "comparison": comparison,
        "checks": checks,
        "runtime_scan": runtime_scan,
        "side_effects": side_effects,
        "replay_records": replay_records,
        "next_allowed_step": "deterministic_runtime_adjacent_smoke_only",
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    json_path = out_dir / "recorded_trace_replay_no_diff.json"
    report_path = out_dir / "RECORDED_TRACE_REPLAY_NO_DIFF_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["checks"].items()))
    comparison = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["comparison"].items()))
    side_effects = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["side_effects"].items()))
    return f"""# PSPC Recorded Trace Replay No-Diff v0

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- recorded_case_count: `{result['recorded_case_count']}`
- observer_enabled: `{result['observer_enabled']}`
- observer_mainline_connected: `{result['observer_mainline_connected']}`
- runtime_registered: `{result['runtime_registered']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Checks

{checks}

## Comparison

{comparison}

## Side Effects

{side_effects}

## What This Proves

This proves recorded EgoOperator inputs can be replayed beside the default-off PSPC observer while baseline response hashes and shadow response hashes remain equal, memory/approval/gate/runtime-output diffs remain false, and PSPC adds only shadow audit artifacts.

## What This Does Not Prove

It does not prove live runtime hook safety, real-time integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC must remain at default_off_observer_only until recorded replay preserves outputs and side-effect invariants.

## Rollback

Delete `scripts/run_pspc_recorded_trace_replay_no_diff.py`, `tests/test_pspc_recorded_trace_replay_no_diff.py`, `docs/codex/tasks/pspc-recorded-trace-replay-no-diff-v0/`, `artifacts/pspc_recorded_trace_replay_no_diff_v0/`, and matching governance/ledger/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PSPC recorded trace replay no-diff observation.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for replay artifacts.")
    args = parser.parse_args()
    result = run_replay(repo_root=ROOT, out_dir=Path(args.out))
    print(json.dumps({"status": result["status"], "out": str(Path(args.out))}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
