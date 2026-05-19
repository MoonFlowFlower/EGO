#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = ROOT / "docs" / "codex" / "tasks" / "runtime-proximal-basic-standard-admission-runner-implementation"
MANIFEST_PATH = TASK_ROOT / "RUNNER_MANIFEST.json"
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "RUNTIME_PROXIMAL_BASIC_STANDARD_ADMISSION_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "RUNTIME_PROXIMAL_BASIC_STANDARD_ADMISSION_CURRENT.md"
SCHEMA_VERSION = "runtime_proximal_basic_standard_admission_runner.v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the runtime-proximal basic-standard admission runner")
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


def validate_manifest(manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if manifest.get("schema_version") != "runtime_proximal_basic_standard_admission_runner_manifest.v1":
        errors.append("schema_version must be runtime_proximal_basic_standard_admission_runner_manifest.v1")
    contract = dict(manifest.get("runner_contract") or {})
    if list(contract.get("allowed_host_surface") or []) != ["policy_hint", "response_tendency", "trace_payload"]:
        errors.append("allowed_host_surface must remain policy_hint/response_tendency/trace_payload")
    required_layers = list(contract.get("required_layers") or [])
    if required_layers != [
        "replay_gate",
        "controlled_replay_bridge",
        "controlled_observation",
        "unified_host_contract",
        "host_consumption_runner",
    ]:
        errors.append("required_layers drifted")
    artifacts = dict(manifest.get("artifacts") or {})
    for layer in required_layers:
        rel = str(artifacts.get(layer) or "").strip()
        if not rel:
            errors.append(f"artifacts.{layer} missing")
            continue
        if not (ROOT / rel).exists():
            errors.append(f"artifacts.{layer} does not exist: {rel}")
    return errors


def _load_inputs(manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    artifacts = dict(manifest.get("artifacts") or {})
    return {layer: _read_json(ROOT / rel_path) for layer, rel_path in artifacts.items()}


def _surface_ok(authority: Dict[str, Any], allowed_surface: List[str]) -> bool:
    return list(authority.get("host_consumable_surface") or []) == allowed_surface


def build_report(manifest: Dict[str, Any]) -> Dict[str, Any]:
    allowed_surface = list((manifest.get("runner_contract") or {}).get("allowed_host_surface") or [])
    inputs = _load_inputs(manifest)
    blocked_reasons: List[str] = []
    layer_results: Dict[str, Dict[str, Any]] = {}

    replay = dict(inputs["replay_gate"])
    replay_sel = dict(replay.get("selection") or {})
    replay_pass = replay_sel.get("decision") == "switch_to_active_inference" and bool(replay_sel.get("challenger_pass"))
    if not replay_pass:
        blocked_reasons.append("replay_gate_not_green_for_active_inference")
    layer_results["replay_gate"] = {"status": "pass" if replay_pass else "fail", "selection": replay_sel}

    controlled_replay = dict(inputs["controlled_replay_bridge"])
    cr_sel = dict(controlled_replay.get("selection") or {})
    cr_auth = dict(controlled_replay.get("authority_drift_audit") or {})
    cr_trace = dict(controlled_replay.get("trace_contract_check") or {})
    controlled_replay_pass = (
        cr_sel.get("decision") == "bridge_pass"
        and bool(cr_sel.get("candidate_pass"))
        and cr_auth.get("status") == "pass"
        and cr_trace.get("status") == "pass"
        and _surface_ok(cr_auth, allowed_surface)
    )
    if not controlled_replay_pass:
        blocked_reasons.append("controlled_replay_bridge_not_green")
    layer_results["controlled_replay_bridge"] = {
        "status": "pass" if controlled_replay_pass else "fail",
        "selection": cr_sel,
        "authority_drift_audit": cr_auth,
        "trace_contract_check": cr_trace,
    }

    controlled_observation = dict(inputs["controlled_observation"])
    co_sel = dict(controlled_observation.get("selection") or {})
    co_gate = dict(controlled_observation.get("aggregate_gate") or {})
    co_auth = dict(controlled_observation.get("authority_drift_audit") or {})
    co_trace = dict(controlled_observation.get("trace_contract_check") or {})
    co_surface = dict(controlled_observation.get("host_surface_bounded_audit") or {})
    controlled_observation_pass = (
        co_sel.get("decision") == "bridge_pass"
        and bool(co_sel.get("candidate_pass"))
        and co_gate.get("status") == "pass"
        and co_auth.get("status") == "pass"
        and co_trace.get("status") == "pass"
        and co_surface.get("status") == "pass"
        and list(co_surface.get("allowed_host_surface") or []) == allowed_surface
    )
    if not controlled_observation_pass:
        blocked_reasons.append("controlled_observation_not_green")
    layer_results["controlled_observation"] = {
        "status": "pass" if controlled_observation_pass else "fail",
        "selection": co_sel,
        "aggregate_gate": co_gate,
        "authority_drift_audit": co_auth,
        "trace_contract_check": co_trace,
        "host_surface_bounded_audit": co_surface,
    }

    parity = dict(inputs["unified_host_contract"])
    parity_agg = dict(parity.get("aggregate") or {})
    parity_pass = parity_agg.get("verdict") == "pass" and parity.get("claim_ceiling") == "host_contract_only"
    if not parity_pass:
        blocked_reasons.append("unified_host_contract_not_green")
    layer_results["unified_host_contract"] = {
        "status": "pass" if parity_pass else "fail",
        "aggregate": parity_agg,
        "claim_ceiling": parity.get("claim_ceiling"),
    }

    host_consumption = dict(inputs["host_consumption_runner"])
    hc_agg = dict(host_consumption.get("aggregate") or {})
    hc_auth = dict(host_consumption.get("authority_drift_audit") or {})
    hc_trace = dict(host_consumption.get("trace_contract_check") or {})
    hc_surface = dict(host_consumption.get("host_surface_bounded_audit") or {})
    host_consumption_pass = (
        hc_agg.get("execution_status") == "pass"
        and hc_agg.get("causal_signal_status") == "pass"
        and hc_auth.get("status") == "pass"
        and hc_trace.get("status") == "pass"
        and hc_surface.get("status") == "pass"
        and list(hc_surface.get("allowed_host_surface") or []) == allowed_surface
        and host_consumption.get("claim_ceiling") == "bounded_runner_only"
    )
    if not host_consumption_pass:
        blocked_reasons.append("host_consumption_runner_not_green")
    layer_results["host_consumption_runner"] = {
        "status": "pass" if host_consumption_pass else "fail",
        "aggregate": hc_agg,
        "authority_drift_audit": hc_auth,
        "trace_contract_check": hc_trace,
        "host_surface_bounded_audit": hc_surface,
        "claim_ceiling": host_consumption.get("claim_ceiling"),
    }

    layer_integrity_status = "pass" if all(item["status"] == "pass" for item in layer_results.values()) else "fail"
    host_surface_integrity_status = "pass" if (
        _surface_ok(cr_auth, allowed_surface)
        and list(co_surface.get("allowed_host_surface") or []) == allowed_surface
        and list(hc_surface.get("allowed_host_surface") or []) == allowed_surface
    ) else "fail"
    causal_transfer_status = "pass" if controlled_observation_pass and host_consumption_pass else "fail"
    claim_ceiling_status = "pass" if (
        parity.get("claim_ceiling") == "host_contract_only"
        and host_consumption.get("claim_ceiling") == "bounded_runner_only"
    ) else "fail"
    if host_surface_integrity_status != "pass":
        blocked_reasons.append("host_surface_integrity_failed")
    if causal_transfer_status != "pass":
        blocked_reasons.append("causal_transfer_not_green")
    if claim_ceiling_status != "pass":
        blocked_reasons.append("claim_ceiling_drift")

    admission_decision = "pass" if (
        layer_integrity_status == "pass"
        and host_surface_integrity_status == "pass"
        and causal_transfer_status == "pass"
        and claim_ceiling_status == "pass"
    ) else "hold"

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
        "source": "runtime_proximal_basic_standard_admission_runner",
        "claim_ceiling": "bounded_admission_only",
        "layer_results": layer_results,
        "aggregate": {
            "layer_integrity_status": layer_integrity_status,
            "host_surface_integrity_status": host_surface_integrity_status,
            "causal_transfer_status": causal_transfer_status,
            "claim_ceiling_status": claim_ceiling_status,
            "admission_decision": admission_decision,
            "reviewer_gate_ready": admission_decision == "pass",
            "blocked_reasons": sorted(set(blocked_reasons)),
        },
        "summary": {
            "required_layer_count": 5,
            "passed_layer_count": sum(1 for item in layer_results.values() if item["status"] == "pass"),
            "allowed_host_surface": allowed_surface,
        },
    }


def _write_md(path: Path, report: Dict[str, Any]) -> None:
    agg = dict(report.get("aggregate") or {})
    lines = [
        "# Runtime-Proximal Basic-Standard Admission Runner",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- admission_decision: `{agg.get('admission_decision')}`",
        f"- layer_integrity_status: `{agg.get('layer_integrity_status')}`",
        f"- host_surface_integrity_status: `{agg.get('host_surface_integrity_status')}`",
        f"- causal_transfer_status: `{agg.get('causal_transfer_status')}`",
        f"- claim_ceiling_status: `{agg.get('claim_ceiling_status')}`",
        f"- reviewer_gate_ready: `{agg.get('reviewer_gate_ready')}`",
        "",
        "## Layer results",
    ]
    for layer, payload in dict(report.get("layer_results") or {}).items():
        lines.append(f"- `{layer}`: `{payload.get('status')}`")
    blocked = list(agg.get("blocked_reasons") or [])
    lines.extend(["", "## Blocked reasons"])
    if blocked:
        lines.extend([f"- `{item}`" for item in blocked])
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_runner(*, manifest_path: Path) -> Dict[str, Any]:
    manifest = _read_json(manifest_path)
    errors = validate_manifest(manifest)
    if errors:
        raise SystemExit("manifest validation failed: " + "; ".join(errors))
    return build_report(manifest)


def main() -> int:
    args = parse_args()
    report = run_runner(manifest_path=args.manifest)
    _write_json(args.output_json, report)
    _write_md(args.output_md, report)
    print(json.dumps(report["aggregate"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
