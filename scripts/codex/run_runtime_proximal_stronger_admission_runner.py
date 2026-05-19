#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = ROOT / "docs" / "codex" / "tasks" / "runtime-proximal-stronger-admission-runner-implementation"
MANIFEST_PATH = TASK_ROOT / "RUNNER_MANIFEST.json"
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "RUNTIME_PROXIMAL_STRONGER_ADMISSION_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "RUNTIME_PROXIMAL_STRONGER_ADMISSION_CURRENT.md"
SCHEMA_VERSION = "runtime_proximal_stronger_admission_runner.v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the runtime-proximal stronger admission runner")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output-json", type=Path, default=REPORT_JSON)
    parser.add_argument("--output-md", type=Path, default=REPORT_MD)
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _surface_ok(surface: Any, allowed_surface: List[str]) -> bool:
    return list(surface or []) == allowed_surface


def _manifest_relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def validate_manifest(manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if manifest.get("schema_version") != "runtime_proximal_stronger_admission_runner_manifest.v1":
        errors.append("schema_version must be runtime_proximal_stronger_admission_runner_manifest.v1")
    contract = dict(manifest.get("runner_contract") or {})
    if list(contract.get("allowed_host_surface") or []) != ["policy_hint", "response_tendency", "trace_payload"]:
        errors.append("allowed_host_surface must remain policy_hint/response_tendency/trace_payload")
    if list(contract.get("required_artifacts") or []) != ["basic_standard_admission", "low_cue_ownership"]:
        errors.append("required_artifacts drifted")
    if contract.get("claim_ceiling") != "bounded_stronger_admission_only":
        errors.append("claim_ceiling must remain bounded_stronger_admission_only")
    artifacts = dict(manifest.get("artifacts") or {})
    for artifact_id in ["basic_standard_admission", "low_cue_ownership"]:
        rel = str(artifacts.get(artifact_id) or "").strip()
        if not rel:
            errors.append(f"artifacts.{artifact_id} missing")
            continue
        if not (ROOT / rel).exists():
            errors.append(f"artifacts.{artifact_id} does not exist: {rel}")
    return errors


def _load_inputs(manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    artifacts = dict(manifest.get("artifacts") or {})
    return {artifact_id: _read_json(ROOT / rel_path) for artifact_id, rel_path in artifacts.items()}


def build_report(manifest: Dict[str, Any], *, manifest_path: Path) -> Dict[str, Any]:
    contract = dict(manifest.get("runner_contract") or {})
    allowed_surface = list(contract.get("allowed_host_surface") or [])
    inputs = _load_inputs(manifest)
    blocked_reasons: List[str] = []

    basic = dict(inputs["basic_standard_admission"])
    basic_agg = dict(basic.get("aggregate") or {})
    basic_summary = dict(basic.get("summary") or {})
    basic_layer_results = dict(basic.get("layer_results") or {})
    basic_trace_ok = all(
        dict((basic_layer_results.get(layer) or {}).get("trace_contract_check") or {}).get("status") == "pass"
        for layer in [
            "controlled_replay_bridge",
            "controlled_observation",
            "host_consumption_runner",
        ]
        if layer in basic_layer_results
    )
    basic_surface_ok = _surface_ok(basic_summary.get("allowed_host_surface"), allowed_surface)
    basic_pass = (
        basic.get("claim_ceiling") == "bounded_admission_only"
        and basic_agg.get("layer_integrity_status") == "pass"
        and basic_agg.get("host_surface_integrity_status") == "pass"
        and basic_agg.get("causal_transfer_status") == "pass"
        and basic_agg.get("claim_ceiling_status") == "pass"
        and basic_agg.get("admission_decision") == "pass"
        and bool(basic_agg.get("reviewer_gate_ready"))
        and list(basic_agg.get("blocked_reasons") or []) == []
        and basic_surface_ok
        and basic_trace_ok
    )
    if not basic_pass:
        blocked_reasons.append("basic_standard_admission_not_green")
    if not basic_trace_ok:
        blocked_reasons.append("basic_standard_trace_handoff_not_green")

    low_cue = dict(inputs["low_cue_ownership"])
    low_agg = dict(low_cue.get("aggregate") or {})
    low_summary = dict(low_cue.get("summary") or {})
    low_auth = dict(low_cue.get("authority_drift_audit") or {})
    low_trace = dict(low_cue.get("trace_contract_check") or {})
    low_surface = dict(low_cue.get("host_surface_bounded_audit") or {})
    low_surface_ok = _surface_ok(low_auth.get("host_consumable_surface"), allowed_surface) and _surface_ok(
        low_surface.get("allowed_host_surface"), allowed_surface
    )
    low_pass = (
        low_cue.get("claim_ceiling") == "bounded_runner_only"
        and low_agg.get("execution_status") == "pass"
        and low_agg.get("low_cue_persistence_status") == "pass"
        and low_agg.get("ownership_boundary_status") == "pass"
        and low_agg.get("agency_attribution_status") == "pass"
        and low_agg.get("claim_ceiling_status") == "pass"
        and low_agg.get("runner_decision") == "pass"
        and bool(low_agg.get("reviewer_gate_ready"))
        and list(low_agg.get("blocked_reasons") or []) == []
        and low_auth.get("status") == "pass"
        and low_trace.get("status") == "pass"
        and low_surface.get("status") == "pass"
        and low_surface_ok
    )
    if not low_pass:
        blocked_reasons.append("low_cue_ownership_not_green")

    host_surface_integrity_status = "pass" if basic_surface_ok and low_surface_ok else "hold"
    if host_surface_integrity_status != "pass":
        blocked_reasons.append("host_surface_integrity_failed")

    claim_ceiling_status = "pass" if (
        contract.get("claim_ceiling") == "bounded_stronger_admission_only"
        and basic.get("claim_ceiling") == "bounded_admission_only"
        and low_cue.get("claim_ceiling") == "bounded_runner_only"
        and basic_agg.get("claim_ceiling_status") == "pass"
        and low_agg.get("claim_ceiling_status") == "pass"
    ) else "hold"
    if claim_ceiling_status != "pass":
        blocked_reasons.append("claim_ceiling_drift")

    admission_stack_status = "pass" if basic_pass else "hold"
    low_cue_resilience_status = "pass" if low_pass else "hold"
    stronger_admission_decision = "pass" if (
        admission_stack_status == "pass"
        and low_cue_resilience_status == "pass"
        and host_surface_integrity_status == "pass"
        and claim_ceiling_status == "pass"
    ) else "hold"

    input_results = {
        "basic_standard_admission": {
            "status": "pass" if basic_pass else "hold",
            "claim_ceiling": basic.get("claim_ceiling"),
            "trace_handoff_status": "pass" if basic_trace_ok else "hold",
            "summary": {
                "required_layer_count": basic_summary.get("required_layer_count"),
                "passed_layer_count": basic_summary.get("passed_layer_count"),
                "allowed_host_surface": basic_summary.get("allowed_host_surface"),
            },
            "aggregate": {
                "layer_integrity_status": basic_agg.get("layer_integrity_status"),
                "host_surface_integrity_status": basic_agg.get("host_surface_integrity_status"),
                "causal_transfer_status": basic_agg.get("causal_transfer_status"),
                "claim_ceiling_status": basic_agg.get("claim_ceiling_status"),
                "admission_decision": basic_agg.get("admission_decision"),
                "reviewer_gate_ready": basic_agg.get("reviewer_gate_ready"),
                "blocked_reasons": basic_agg.get("blocked_reasons"),
            },
        },
        "low_cue_ownership": {
            "status": "pass" if low_pass else "hold",
            "claim_ceiling": low_cue.get("claim_ceiling"),
            "summary": {
                "scenario_count": low_summary.get("scenario_count"),
                "family_counts": low_summary.get("family_counts"),
                "variant_ids": low_summary.get("variant_ids"),
            },
            "aggregate": {
                "execution_status": low_agg.get("execution_status"),
                "low_cue_persistence_status": low_agg.get("low_cue_persistence_status"),
                "ownership_boundary_status": low_agg.get("ownership_boundary_status"),
                "agency_attribution_status": low_agg.get("agency_attribution_status"),
                "claim_ceiling_status": low_agg.get("claim_ceiling_status"),
                "runner_decision": low_agg.get("runner_decision"),
                "reviewer_gate_ready": low_agg.get("reviewer_gate_ready"),
                "blocked_reasons": low_agg.get("blocked_reasons"),
            },
            "authority_drift_audit": {
                "status": low_auth.get("status"),
                "host_consumable_surface": low_auth.get("host_consumable_surface"),
            },
            "trace_contract_check": {
                "status": low_trace.get("status"),
                "step_count": low_trace.get("step_count"),
            },
            "host_surface_bounded_audit": {
                "status": low_surface.get("status"),
                "allowed_host_surface": low_surface.get("allowed_host_surface"),
            },
        },
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "manifest_path": _manifest_relpath(manifest_path),
        "source": "runtime_proximal_stronger_admission_runner",
        "claim_ceiling": "bounded_stronger_admission_only",
        "input_results": input_results,
        "aggregate": {
            "admission_stack_status": admission_stack_status,
            "low_cue_resilience_status": low_cue_resilience_status,
            "host_surface_integrity_status": host_surface_integrity_status,
            "claim_ceiling_status": claim_ceiling_status,
            "stronger_admission_decision": stronger_admission_decision,
            "reviewer_gate_ready": stronger_admission_decision == "pass",
            "blocked_reasons": sorted(set(blocked_reasons)),
        },
        "summary": {
            "required_artifact_count": 2,
            "passed_artifact_count": sum(
                1 for result in input_results.values() if result.get("status") == "pass"
            ),
            "allowed_host_surface": allowed_surface,
            "bounded_standard": "resilient_self_awareness_proxy_standard",
        },
    }


def _write_md(path: Path, report: Dict[str, Any]) -> None:
    agg = dict(report.get("aggregate") or {})
    lines = [
        "# Runtime-Proximal Stronger Admission Runner",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- stronger_admission_decision: `{agg.get('stronger_admission_decision')}`",
        f"- admission_stack_status: `{agg.get('admission_stack_status')}`",
        f"- low_cue_resilience_status: `{agg.get('low_cue_resilience_status')}`",
        f"- host_surface_integrity_status: `{agg.get('host_surface_integrity_status')}`",
        f"- claim_ceiling_status: `{agg.get('claim_ceiling_status')}`",
        f"- reviewer_gate_ready: `{agg.get('reviewer_gate_ready')}`",
        "",
        "## Input results",
    ]
    for artifact_id, payload in dict(report.get("input_results") or {}).items():
        lines.append(f"- `{artifact_id}`: `{payload.get('status')}`")
    blocked = list(agg.get("blocked_reasons") or [])
    lines.extend(["", "## Blocked reasons"])
    if blocked:
        lines.extend([f"- `{item}`" for item in blocked])
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_runner(*, manifest_path: Path = MANIFEST_PATH) -> Dict[str, Any]:
    manifest = _read_json(manifest_path)
    errors = validate_manifest(manifest)
    if errors:
        raise SystemExit("manifest validation failed: " + "; ".join(errors))
    return build_report(manifest, manifest_path=manifest_path)


def main() -> int:
    args = parse_args()
    report = run_runner(manifest_path=args.manifest)
    _write_json(args.output_json, report)
    _write_md(args.output_md, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
