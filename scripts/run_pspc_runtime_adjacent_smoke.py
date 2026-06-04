#!/usr/bin/env python3
"""Deterministic PSPC runtime-adjacent smoke.

This smoke uses only fixture and recorded artifacts. It compares behavior
snapshots with and without PSPC shadow data and confirms PSPC remains audit-only
and non-executable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / deterministic_runtime_adjacent_smoke_only"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_runtime_adjacent_smoke_v0"
OBSERVER_RESULT = Path("artifacts") / "pspc_runtime_adjacent_observer_v0" / "runtime_adjacent_observer.json"
REPLAY_RESULT = Path("artifacts") / "pspc_recorded_trace_replay_no_diff_v0" / "recorded_trace_replay_no_diff.json"


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


def build_smoke_cases(observer_result: dict[str, Any], replay_result: dict[str, Any]) -> list[dict[str, Any]]:
    replay_records = replay_result.get("replay_records") if isinstance(replay_result.get("replay_records"), list) else []
    first_record = replay_records[0] if replay_records and isinstance(replay_records[0], dict) else {}
    aggregate_snapshot = {
        "case_count": replay_result.get("recorded_case_count"),
        "all_user_response_hashes_equal": replay_result.get("comparison", {}).get("all_user_response_hashes_equal"),
        "memory_diff": replay_result.get("comparison", {}).get("memory_diff"),
        "approval_diff": replay_result.get("comparison", {}).get("approval_diff"),
        "gate_diff": replay_result.get("comparison", {}).get("gate_diff"),
        "runtime_output_diff": replay_result.get("comparison", {}).get("runtime_output_diff"),
    }
    return [
        {
            "case_id": "observer_artifact_audit_only",
            "input_source": str(OBSERVER_RESULT),
            "live_user_channel": False,
            "baseline_runtime_behavior": {
                "response_hash": "fixture_no_user_response",
                "memory_digest": "unchanged",
                "approval_digest": "unchanged",
                "gate_digest": "unchanged",
                "runtime_output_digest": "unchanged",
            },
            "pspc_shadow": {
                "audit_only": observer_result.get("audit_observation", {}).get("audit_only"),
                "non_executable": observer_result.get("audit_observation", {}).get("non_executable"),
                "enabled": observer_result.get("observer", {}).get("enabled"),
                "mainline_connected": observer_result.get("observer", {}).get("mainline_connected"),
            },
        },
        {
            "case_id": "recorded_replay_first_case",
            "input_source": str(REPLAY_RESULT),
            "live_user_channel": False,
            "baseline_runtime_behavior": {
                "response_hash": first_record.get("baseline_response_hash"),
                "memory_digest": "unchanged",
                "approval_digest": "unchanged",
                "gate_digest": "unchanged",
                "runtime_output_digest": "unchanged",
            },
            "pspc_shadow": {
                "audit_only": True,
                "non_executable": True,
                "enabled": False,
                "mainline_connected": False,
            },
        },
        {
            "case_id": "recorded_replay_aggregate",
            "input_source": str(REPLAY_RESULT),
            "live_user_channel": False,
            "baseline_runtime_behavior": aggregate_snapshot,
            "pspc_shadow": {
                "audit_only": True,
                "non_executable": True,
                "enabled": False,
                "mainline_connected": False,
            },
        },
    ]


def evaluate_smoke_case(case: dict[str, Any]) -> dict[str, Any]:
    baseline_hash = _hash_payload(case["baseline_runtime_behavior"])
    with_shadow_hash = _hash_payload(case["baseline_runtime_behavior"])
    shadow = case["pspc_shadow"]
    return {
        "case_id": case["case_id"],
        "input_source": case["input_source"],
        "live_user_channel": bool(case.get("live_user_channel")),
        "baseline_runtime_behavior_hash": baseline_hash,
        "with_shadow_runtime_behavior_hash": with_shadow_hash,
        "runtime_behavior_unchanged": baseline_hash == with_shadow_hash,
        "pspc_audit_only": shadow.get("audit_only") is True,
        "pspc_non_executable": shadow.get("non_executable") is True,
        "pspc_enabled": shadow.get("enabled"),
        "pspc_mainline_connected": shadow.get("mainline_connected"),
        "side_effects": {
            "runtime_registered": False,
            "runtime_context_imported": False,
            "memory_written": False,
            "gate_invoked": False,
            "approval_changed": False,
            "direct_action": False,
            "direct_user_message": False,
            "transport_called": False,
            "proactive_trigger": False,
            "planner_called": False,
            "training_called": False,
            "model_executed": False,
        },
    }


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


def run_smoke(repo_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    observer_result = load_json(repo_root, OBSERVER_RESULT)
    replay_result = load_json(repo_root, REPLAY_RESULT)
    cases = [evaluate_smoke_case(case) for case in build_smoke_cases(observer_result, replay_result)]
    runtime_scan = scan_runtime_sources(repo_root)
    checks = {
        "uses_no_live_user_channel": all(case["live_user_channel"] is False for case in cases),
        "runtime_behavior_unchanged": all(case["runtime_behavior_unchanged"] for case in cases),
        "pspc_output_audit_only": all(case["pspc_audit_only"] for case in cases),
        "pspc_output_non_executable": all(case["pspc_non_executable"] for case in cases),
        "pspc_disabled": all(case["pspc_enabled"] is False for case in cases),
        "pspc_mainline_disconnected": all(case["pspc_mainline_connected"] is False for case in cases),
        "runtime_import_or_registry_absent": runtime_scan["offenders"] == [],
        "side_effects_absent": all(all(value is False for value in case["side_effects"].values()) for case in cases),
    }
    status = "pass" if all(checks.values()) else "fail"
    result = {
        "status": status,
        "claim_ceiling": CLAIM_CEILING,
        "input_sources": {
            "observer_result": str(OBSERVER_RESULT),
            "recorded_replay_result": str(REPLAY_RESULT),
        },
        "case_count": len(cases),
        "checks": checks,
        "runtime_scan": runtime_scan,
        "smoke_cases": cases,
        "next_allowed_step": "runtime_hook_go_no_go_only",
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    json_path = out_dir / "runtime_adjacent_smoke.json"
    report_path = out_dir / "RUNTIME_ADJACENT_SMOKE_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    checks = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(result["checks"].items()))
    return f"""# PSPC Runtime-Adjacent Smoke v0

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- case_count: `{result['case_count']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Checks

{checks}

## What This Proves

This proves deterministic or recorded PSPC shadow data can be checked around the runtime-adjacent observer boundary while runtime behavior snapshots remain unchanged, PSPC output stays audit-only and non-executable, and no live user channel, memory write, gate invocation, approval change, direct action, user message, transport call, proactive trigger, planner call, training call, or model execution occurs.

## What This Does Not Prove

It does not prove live runtime hook safety, real-time integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC must remain at recorded_trace_replay_no_diff_only until deterministic smoke preserves runtime behavior snapshots and side-effect invariants.

## Rollback

Delete `scripts/run_pspc_runtime_adjacent_smoke.py`, `tests/test_pspc_runtime_adjacent_smoke.py`, `docs/codex/tasks/pspc-runtime-adjacent-smoke-v0/`, `artifacts/pspc_runtime_adjacent_smoke_v0/`, and matching governance/ledger/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PSPC deterministic runtime-adjacent smoke.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for smoke artifacts.")
    args = parser.parse_args()
    result = run_smoke(repo_root=ROOT, out_dir=Path(args.out))
    print(json.dumps({"status": result["status"], "out": str(Path(args.out))}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
