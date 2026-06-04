#!/usr/bin/env python3
"""Run the default-off PSPC runtime-adjacent observer in artifact-only mode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from EgoOperator.adapters.pspc_runtime_adjacent_observer import PSPCRuntimeAdjacentObserver


CLAIM_CEILING = "lab_only_proto_self_mechanism_candidate / default_off_observer_only"
DEFAULT_OUT_DIR = Path("artifacts") / "pspc_runtime_adjacent_observer_v0"
FIXTURE_BOUNDARY_RESULT = (
    Path("artifacts") / "pspc_runtime_trace_fixture_boundary_v0" / "runtime_trace_fixture_boundary.json"
)


def load_json(repo_root: Path, relative_path: Path) -> dict[str, Any]:
    path = Path(repo_root) / relative_path
    if not path.exists():
        raise FileNotFoundError(f"missing artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"artifact must be an object: {path}")
    return payload


def run_observer(repo_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    observer = PSPCRuntimeAdjacentObserver()
    observer.assert_no_runtime_authority()
    boundary_result = load_json(repo_root, FIXTURE_BOUNDARY_RESULT)
    validation = observer.validate_fixture_boundary(boundary_result)
    if not validation["ok"]:
        raise ValueError(";".join(validation["errors"]))
    audit_observation = observer.to_audit_observation(boundary_result)
    result = {
        "status": "pass",
        "claim_ceiling": CLAIM_CEILING,
        "input_sources": {"fixture_boundary_source": str(FIXTURE_BOUNDARY_RESULT)},
        "observer": {
            "enabled": observer.enabled,
            "mainline_connected": observer.mainline_connected,
            "runtime_authority": observer.runtime_authority,
            "mode": observer.mode,
        },
        "validation": validation,
        "audit_observation": audit_observation,
        "runtime_behavior_unchanged": True,
        "next_allowed_step": "recorded_trace_replay_no_diff_only",
    }
    write_reports(result, out_dir)
    return result


def write_reports(result: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    json_path = out_dir / "runtime_adjacent_observer.json"
    report_path = out_dir / "RUNTIME_ADJACENT_OBSERVER_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    return json_path, report_path


def render_markdown_report(result: dict[str, Any]) -> str:
    observer = result["observer"]
    observation = result["audit_observation"]
    side_effects = "\n".join(
        f"- `{key}`: `{value}`" for key, value in sorted(observation["side_effects"].items())
    )
    return f"""# PSPC Runtime-Adjacent Observer v0

- status: `{result['status']}`
- claim_ceiling: `{result['claim_ceiling']}`
- observer_enabled: `{observer['enabled']}`
- observer_mainline_connected: `{observer['mainline_connected']}`
- runtime_authority: `{observer['runtime_authority']}`
- mode: `{observer['mode']}`
- non_executable: `{observation['non_executable']}`
- audit_only: `{observation['audit_only']}`
- runtime_behavior_unchanged: `{result['runtime_behavior_unchanged']}`
- next_allowed_step: `{result['next_allowed_step']}`

## Side Effects

{side_effects}

## What This Proves

This proves a default-off, unregistered PSPC runtime-adjacent observer can read the PSPC fixture-boundary artifact and convert it into audit-only non-executable data without changing runtime behavior or exposing direct action, user message, memory write, gate invocation, approval, transport, proactive trigger, planner call, training call, or model execution paths.

## What This Does Not Prove

It does not prove runtime registration safety, live runtime hook safety, real EgoOperator trace compatibility, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC must remain at runtime_trace_fixture_boundary_only until the observer contract, disabled defaults, or non-executable conversion boundary is repaired.

## Rollback

Delete `EgoOperator/adapters/pspc_runtime_adjacent_observer.py`, `scripts/run_pspc_runtime_adjacent_observer.py`, `tests/test_pspc_runtime_adjacent_observer.py`, `docs/codex/tasks/pspc-runtime-adjacent-observer-v0/`, `artifacts/pspc_runtime_adjacent_observer_v0/`, and matching governance/ledger/generated-view entries.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PSPC runtime-adjacent observer artifact review.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Output directory for observer artifacts.")
    args = parser.parse_args()
    result = run_observer(repo_root=ROOT, out_dir=Path(args.out))
    print(json.dumps({"status": result["status"], "out": str(Path(args.out))}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
