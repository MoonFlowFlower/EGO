#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = ROOT / "docs" / "codex" / "tasks" / "runtime-proximal-post-stronger-selection-coherence-runner-implementation"
MANIFEST_PATH = TASK_ROOT / "RUNNER_MANIFEST.json"
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "RUNTIME_PROXIMAL_POST_STRONGER_SELECTION_COHERENCE_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "RUNTIME_PROXIMAL_POST_STRONGER_SELECTION_COHERENCE_CURRENT.md"
SCHEMA_VERSION = "runtime_proximal_post_stronger_selection_coherence_runner.v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the runtime-proximal post-stronger selection-coherence runner"
    )
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


def _write_md(path: Path, report: Dict[str, Any]) -> None:
    agg = dict(report.get("aggregate") or {})
    lines = [
        "# Runtime-Proximal Post-Stronger Selection-Coherence Runner",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- post_stronger_decision: `{agg.get('post_stronger_decision')}`",
        f"- stronger_admission_status: `{agg.get('stronger_admission_status')}`",
        f"- selection_coherence_status: `{agg.get('selection_coherence_status')}`",
        f"- ablation_retention_status: `{agg.get('ablation_retention_status')}`",
        f"- host_surface_integrity_status: `{agg.get('host_surface_integrity_status')}`",
        f"- claim_ceiling_status: `{agg.get('claim_ceiling_status')}`",
        f"- reviewer_gate_ready: `{agg.get('reviewer_gate_ready')}`",
        "",
        "## Input results",
    ]
    for name, payload in dict(report.get("input_results") or {}).items():
        lines.append(f"- `{name}`: `{payload.get('status')}`")
    blocked = list(agg.get("blocked_reasons") or [])
    lines.extend(["", "## Blocked reasons"])
    if blocked:
        for reason in blocked:
            lines.append(f"- `{reason}`")
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _surface_ok(surface: Any, allowed_surface: List[str]) -> bool:
    return list(surface or []) == allowed_surface


def _manifest_relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().replace("`", "").split())


def _contains_all(text: str, phrases: List[str]) -> bool:
    normalized = _normalize_text(text)
    return all(_normalize_text(phrase) in normalized for phrase in phrases)


def _extract_bullets_after_marker(text: str, marker: str) -> List[str]:
    lines = text.splitlines()
    normalized_marker = _normalize_text(marker)
    active = False
    bullets: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not active and _normalize_text(stripped) == normalized_marker:
            active = True
            continue
        if not active:
            continue
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip().replace("`", ""))
            continue
        if stripped == "":
            continue
        break
    return bullets


def validate_manifest(manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if manifest.get("schema_version") != "runtime_proximal_post_stronger_selection_coherence_runner_manifest.v1":
        errors.append(
            "schema_version must be runtime_proximal_post_stronger_selection_coherence_runner_manifest.v1"
        )
    contract = dict(manifest.get("runner_contract") or {})
    allowed_surface = list(contract.get("allowed_host_surface") or [])
    if allowed_surface != ["policy_hint", "response_tendency", "trace_payload"]:
        errors.append("allowed_host_surface must remain policy_hint/response_tendency/trace_payload")
    required_artifacts = list(contract.get("required_artifacts") or [])
    if required_artifacts != ["stronger_admission", "replay_gate", "selection_closeout"]:
        errors.append("required_artifacts drifted")
    if contract.get("expected_selection_decision") != "switch_to_active_inference":
        errors.append("expected_selection_decision must remain switch_to_active_inference")
    if list(contract.get("required_ablation_keys") or []) != [
        "counterfactual",
        "viability",
        "corrective_trace",
        "boundary_confidence",
    ]:
        errors.append("required_ablation_keys drifted")
    if dict(contract.get("target_delta_rules") or {}) != {
        "T1": "non_regression>=-0.02",
        "T2": "delta>=0.05",
        "T3": "delta>=0.05",
        "T4": "delta>=0.05",
        "T5": "delta>=0.05",
    }:
        errors.append("target_delta_rules drifted")
    selection_closeout = dict(contract.get("selection_closeout") or {})
    if not list(selection_closeout.get("required_routing_phrases") or []):
        errors.append("selection_closeout.required_routing_phrases missing")
    if not list(selection_closeout.get("required_host_surface_terms") or []):
        errors.append("selection_closeout.required_host_surface_terms missing")
    if not list(selection_closeout.get("required_claim_guard_terms") or []):
        errors.append("selection_closeout.required_claim_guard_terms missing")
    if contract.get("claim_ceiling") != "bounded_post_stronger_selection_coherence_only":
        errors.append("claim_ceiling must remain bounded_post_stronger_selection_coherence_only")
    artifacts = dict(manifest.get("artifacts") or {})
    for artifact_id in ["stronger_admission", "replay_gate", "selection_closeout"]:
        rel = str(artifacts.get(artifact_id) or "").strip()
        if not rel:
            errors.append(f"artifacts.{artifact_id} missing")
            continue
        if not (ROOT / rel).exists():
            errors.append(f"artifacts.{artifact_id} does not exist: {rel}")
    return errors


def _load_inputs(manifest: Dict[str, Any]) -> Dict[str, Any]:
    artifacts = dict(manifest.get("artifacts") or {})
    return {
        "stronger_admission": _read_json(ROOT / str(artifacts["stronger_admission"])),
        "replay_gate": _read_json(ROOT / str(artifacts["replay_gate"])),
        "selection_closeout_text": (ROOT / str(artifacts["selection_closeout"])).read_text(encoding="utf-8"),
    }


def build_report(manifest: Dict[str, Any], *, manifest_path: Path) -> Dict[str, Any]:
    contract = dict(manifest.get("runner_contract") or {})
    allowed_surface = list(contract.get("allowed_host_surface") or [])
    expected_rules = dict(contract.get("target_delta_rules") or {})
    required_ablation_keys = list(contract.get("required_ablation_keys") or [])
    selection_closeout_contract = dict(contract.get("selection_closeout") or {})
    inputs = _load_inputs(manifest)
    blocked_reasons: List[str] = []

    stronger = dict(inputs["stronger_admission"])
    stronger_agg = dict(stronger.get("aggregate") or {})
    stronger_summary = dict(stronger.get("summary") or {})
    stronger_surface_ok = _surface_ok(stronger_summary.get("allowed_host_surface"), allowed_surface)
    stronger_pass = (
        stronger.get("claim_ceiling") == "bounded_stronger_admission_only"
        and stronger_agg.get("admission_stack_status") == "pass"
        and stronger_agg.get("low_cue_resilience_status") == "pass"
        and stronger_agg.get("host_surface_integrity_status") == "pass"
        and stronger_agg.get("claim_ceiling_status") == "pass"
        and stronger_agg.get("stronger_admission_decision") == "pass"
        and bool(stronger_agg.get("reviewer_gate_ready"))
        and list(stronger_agg.get("blocked_reasons") or []) == []
        and stronger_summary.get("required_artifact_count") == 2
        and stronger_summary.get("passed_artifact_count") == 2
        and stronger_surface_ok
    )
    if not stronger_pass:
        blocked_reasons.append("stronger_admission_not_green")

    replay = dict(inputs["replay_gate"])
    replay_selection = dict(replay.get("selection") or {})
    replay_gate_status = (
        "pass"
        if (
            replay_selection.get("decision") == contract.get("expected_selection_decision")
            and replay_selection.get("challenger_status") == "pass"
            and bool(replay_selection.get("challenger_pass"))
            and bool(replay_selection.get("challenger_switch_advantage"))
            and dict(replay_selection.get("challenger_target_delta_rules") or {}) == expected_rules
        )
        else "hold"
    )
    if replay_gate_status != "pass":
        blocked_reasons.append("replay_selection_not_green")

    ablation_drops = dict(replay_selection.get("ablation_drops") or {})
    ablation_retention_status = (
        "pass"
        if (
            replay_gate_status == "pass"
            and list(replay_selection.get("weak_ablations") or []) == []
            and all(float(ablation_drops.get(key, 0.0)) > 0.0 for key in required_ablation_keys)
        )
        else "hold"
    )
    if ablation_retention_status != "pass":
        blocked_reasons.append("replay_ablation_retention_not_green")

    selection_closeout_text = str(inputs["selection_closeout_text"])
    selection_verdict_bullets = _extract_bullets_after_marker(selection_closeout_text, "当前正式裁决固定为：")
    routing_reset_bullets = _extract_bullets_after_marker(selection_closeout_text, "repo 顶层 routing 继续固定为：")
    host_surface_bullets = _extract_bullets_after_marker(
        selection_closeout_text,
        "当前唯一允许进入宿主消费面的 surface 继续固定为：",
    )
    forbidden_claim_bullets = _extract_bullets_after_marker(selection_closeout_text, "当前禁止口径：")
    routing_ok = _contains_all(
        "\n".join(selection_verdict_bullets + routing_reset_bullets),
        list(selection_closeout_contract.get("required_routing_phrases") or []),
    )
    closeout_surface_ok = _contains_all(
        "\n".join(host_surface_bullets),
        list(selection_closeout_contract.get("required_host_surface_terms") or []),
    )
    closeout_claim_guard_ok = _contains_all(
        "\n".join(forbidden_claim_bullets),
        list(selection_closeout_contract.get("required_claim_guard_terms") or []),
    )
    selection_closeout_status = (
        "pass" if routing_ok and closeout_surface_ok and closeout_claim_guard_ok else "hold"
    )
    if selection_closeout_status != "pass":
        blocked_reasons.append("selection_closeout_summary_not_green")

    selection_coherence_status = (
        "pass"
        if stronger_pass and replay_gate_status == "pass" and selection_closeout_status == "pass"
        else "hold"
    )
    if selection_coherence_status != "pass":
        blocked_reasons.append("selection_coherence_not_green")

    host_surface_integrity_status = "pass" if stronger_surface_ok and closeout_surface_ok else "hold"
    if host_surface_integrity_status != "pass":
        blocked_reasons.append("host_surface_integrity_failed")

    claim_ceiling_status = (
        "pass"
        if (
            contract.get("claim_ceiling") == "bounded_post_stronger_selection_coherence_only"
            and stronger_agg.get("claim_ceiling_status") == "pass"
            and closeout_claim_guard_ok
        )
        else "hold"
    )
    if claim_ceiling_status != "pass":
        blocked_reasons.append("claim_ceiling_drift")

    post_stronger_decision = (
        "pass"
        if (
            stronger_pass
            and selection_coherence_status == "pass"
            and ablation_retention_status == "pass"
            and host_surface_integrity_status == "pass"
            and claim_ceiling_status == "pass"
        )
        else "hold"
    )

    input_results = {
        "stronger_admission": {
            "status": "pass" if stronger_pass else "hold",
            "claim_ceiling": stronger.get("claim_ceiling"),
            "summary": {
                "required_artifact_count": stronger_summary.get("required_artifact_count"),
                "passed_artifact_count": stronger_summary.get("passed_artifact_count"),
                "allowed_host_surface": stronger_summary.get("allowed_host_surface"),
                "bounded_standard": stronger_summary.get("bounded_standard"),
            },
            "aggregate": {
                "admission_stack_status": stronger_agg.get("admission_stack_status"),
                "low_cue_resilience_status": stronger_agg.get("low_cue_resilience_status"),
                "host_surface_integrity_status": stronger_agg.get("host_surface_integrity_status"),
                "claim_ceiling_status": stronger_agg.get("claim_ceiling_status"),
                "stronger_admission_decision": stronger_agg.get("stronger_admission_decision"),
                "reviewer_gate_ready": stronger_agg.get("reviewer_gate_ready"),
                "blocked_reasons": stronger_agg.get("blocked_reasons"),
            },
        },
        "replay_gate": {
            "status": replay_gate_status,
            "selection": {
                "decision": replay_selection.get("decision"),
                "challenger_status": replay_selection.get("challenger_status"),
                "challenger_pass": replay_selection.get("challenger_pass"),
                "challenger_switch_advantage": replay_selection.get("challenger_switch_advantage"),
                "challenger_target_delta_rules": replay_selection.get("challenger_target_delta_rules"),
                "weak_ablations": replay_selection.get("weak_ablations"),
                "ablation_drops": replay_selection.get("ablation_drops"),
            },
        },
        "selection_closeout": {
            "status": selection_closeout_status,
            "routing_assertions": {
                "routing_ok": routing_ok,
                "host_surface_ok": closeout_surface_ok,
                "claim_guard_ok": closeout_claim_guard_ok,
                "selection_verdict_bullets": selection_verdict_bullets,
                "routing_reset_bullets": routing_reset_bullets,
                "host_surface_bullets": host_surface_bullets,
                "forbidden_claim_bullets": forbidden_claim_bullets,
            },
        },
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "manifest_path": _manifest_relpath(manifest_path),
        "source": "runtime_proximal_post_stronger_selection_coherence_runner",
        "claim_ceiling": "bounded_post_stronger_selection_coherence_only",
        "input_results": input_results,
        "aggregate": {
            "stronger_admission_status": "pass" if stronger_pass else "hold",
            "selection_coherence_status": selection_coherence_status,
            "ablation_retention_status": ablation_retention_status,
            "host_surface_integrity_status": host_surface_integrity_status,
            "claim_ceiling_status": claim_ceiling_status,
            "post_stronger_decision": post_stronger_decision,
            "reviewer_gate_ready": post_stronger_decision == "pass",
            "blocked_reasons": sorted(set(blocked_reasons)),
        },
        "summary": {
            "required_artifact_count": 3,
            "passed_artifact_count": sum(
                1 for result in input_results.values() if result.get("status") == "pass"
            ),
            "allowed_host_surface": allowed_surface,
            "bounded_standard": "selection_coherent_resilient_self_awareness_proxy_standard",
        },
    }


def run_runner(
    *,
    manifest_path: Path = MANIFEST_PATH,
    output_json: Path = REPORT_JSON,
    output_md: Path = REPORT_MD,
) -> Dict[str, Any]:
    manifest = _read_json(manifest_path)
    errors = validate_manifest(manifest)
    if errors:
        raise SystemExit("Manifest validation failed:\n- " + "\n- ".join(errors))
    report = build_report(manifest, manifest_path=manifest_path)
    _write_json(output_json, report)
    _write_md(output_md, report)
    return report


def main() -> int:
    args = parse_args()
    run_runner(manifest_path=args.manifest, output_json=args.output_json, output_md=args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
