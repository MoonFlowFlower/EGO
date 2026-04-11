#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_active_inference_controlled_observation import (
    ARTIFACT_ROOT,
    MANIFEST_PATH,
    _authority_drift_audit,
    _case_verdict,
    _host_surface_bounded_audit,
    _load_json,
    _trace_contract_check,
    _validate_manifest,
    render_markdown as render_single_markdown,
    run_controlled_observation_scenario,
)
from score_mvs_replay_validator import (
    _baseline_b_scores,
    _bridge_selection_decision,
    _score_variant,
)


BATCH_JSON = ARTIFACT_ROOT / "ACTIVE_INFERENCE_CONTROLLED_OBSERVATION_BATCH_CURRENT.json"
BATCH_MD = ARTIFACT_ROOT / "ACTIVE_INFERENCE_CONTROLLED_OBSERVATION_BATCH_CURRENT.md"
SCORED_JSON = ARTIFACT_ROOT / "ACTIVE_INFERENCE_CONTROLLED_OBSERVATION_SCORED_CURRENT.json"
SCORED_MD = ARTIFACT_ROOT / "ACTIVE_INFERENCE_CONTROLLED_OBSERVATION_SCORED_CURRENT.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the active-inference controlled observation batch")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output-json", type=Path, default=BATCH_JSON)
    parser.add_argument("--output-md", type=Path, default=BATCH_MD)
    parser.add_argument("--scored-output-json", type=Path, default=SCORED_JSON)
    parser.add_argument("--scored-output-md", type=Path, default=SCORED_MD)
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _render_batch_markdown(report: Dict[str, Any]) -> str:
    authority_drift = dict(report.get("authority_drift_audit") or {})
    trace_contract = dict(report.get("trace_contract_check") or {})
    host_surface = dict(report.get("host_surface_bounded_audit") or {})
    aggregate_gate = dict(report.get("aggregate_gate") or {})
    lines = [
        "# Active-Inference Controlled Observation Batch",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- manifest: `{report.get('manifest_path')}`",
        f"- scenario_count: `{report.get('summary', {}).get('scenario_count')}`",
        f"- authority_drift_status: `{authority_drift.get('status', 'unknown')}`",
        f"- trace_contract_status: `{trace_contract.get('status', 'unknown')}`",
        f"- host_surface_bounded: `{host_surface.get('status', 'unknown')}`",
        f"- aggregate_gate_status: `{aggregate_gate.get('status', 'unknown')}`",
        "",
        "## Variant Coverage",
        "",
    ]
    for variant_id, summary in sorted((report.get("summary", {}).get("variants") or {}).items()):
        lines.append(
            f"- `{variant_id}`: scenarios=`{summary.get('scenario_count')}` "
            f"observation_records=`{summary.get('observation_record_count')}` "
            f"steps=`{summary.get('step_count')}`"
        )
    lines.extend(["", "## Winner Case Verdicts", ""])
    for verdict in report.get("winner_case_verdicts") or []:
        lines.append(
            f"- `{verdict.get('case_id')}` [{verdict.get('family')}] "
            f"pass=`{verdict.get('pass')}` target_scores=`{verdict.get('target_scores')}`"
        )
    return "\n".join(lines) + "\n"


def _render_scored_markdown(payload: Dict[str, Any]) -> str:
    selection = dict(payload.get("selection") or {})
    aggregate_gate = dict(payload.get("aggregate_gate") or {})
    authority_drift = dict(payload.get("authority_drift_audit") or {})
    trace_contract = dict(payload.get("trace_contract_check") or {})
    host_surface = dict(payload.get("host_surface_bounded_audit") or {})
    lines = [
        "# Active-Inference Controlled Observation Scored",
        "",
        f"- generated_at: `{payload.get('generated_at')}`",
        f"- selection_decision: `{selection.get('decision')}`",
        f"- candidate_pass: `{selection.get('candidate_pass')}`",
        f"- aggregate_gate_status: `{aggregate_gate.get('status')}`",
        f"- authority_drift_status: `{authority_drift.get('status', 'unknown')}`",
        f"- trace_contract_status: `{trace_contract.get('status', 'unknown')}`",
        f"- host_surface_bounded: `{host_surface.get('status', 'unknown')}`",
        "",
        "## Target Scores",
        "",
    ]
    for variant_id, scores in (payload.get("variant_scores") or {}).items():
        lines.append(
            f"- `{variant_id}`: composite=`{scores['composite']}` "
            f"T1=`{scores['target_scores']['T1']}` "
            f"T2=`{scores['target_scores']['T2']}` "
            f"T3=`{scores['target_scores']['T3']}` "
            f"T4=`{scores['target_scores']['T4']}` "
            f"T5=`{scores['target_scores']['T5']}`"
        )
    lines.extend(
        [
            "",
            "## Aggregate Gate",
            "",
            f"- scenario_count: `{aggregate_gate.get('scenario_count')}`",
            f"- winner_pass_count: `{aggregate_gate.get('winner_pass_count')}`",
            f"- external_result_scenario_count: `{aggregate_gate.get('external_result_scenario_count')}`",
            f"- replay_gate_pass: `{aggregate_gate.get('replay_gate_pass')}`",
        ]
    )
    return "\n".join(lines) + "\n"


async def run_controlled_observation_batch(*, manifest_path: Path = MANIFEST_PATH) -> tuple[Dict[str, Any], Dict[str, Any]]:
    manifest = _load_json(manifest_path)
    errors = _validate_manifest(manifest)
    if errors:
        raise RuntimeError("\n".join(errors))

    contract = dict(manifest.get("runner_contract") or {})
    scenarios = [dict(item) for item in list(manifest.get("scenarios") or [])]
    results_by_variant: Dict[str, List[Dict[str, Any]]] = {
        str(contract.get("baseline_a_id") or ""): [],
        str(contract.get("candidate_id") or ""): [],
    }
    for scenario in scenarios:
        single_report = await run_controlled_observation_scenario(
            manifest_path=manifest_path,
            scenario_id=str(scenario.get("scenario_id") or ""),
        )
        for variant_id, case_results in dict(single_report.get("results_by_variant") or {}).items():
            results_by_variant.setdefault(variant_id, []).extend(list(case_results or []))

    authority_drift_audit = _authority_drift_audit(contract)
    trace_contract_check = _trace_contract_check(results_by_variant)
    host_surface_bounded_audit = _host_surface_bounded_audit(contract, results_by_variant)
    summary = {
        "scenario_count": len(scenarios),
        "family_counts": dict(manifest.get("family_counts") or {}),
        "external_result_scenario_count": sum(1 for item in scenarios if list(item.get("external_result_steps") or [])),
        "variants": {
            variant_id: {
                "scenario_count": len(case_results),
                "observation_record_count": sum(
                    len(case_result.get("observation_records") or []) for case_result in case_results
                ),
                "step_count": sum(len(case_result.get("steps") or []) for case_result in case_results),
            }
            for variant_id, case_results in results_by_variant.items()
        },
    }

    winner_id = str(contract.get("candidate_id") or "")
    baseline_a_id = str(contract.get("baseline_a_id") or "")
    winner_case_verdicts = [
        _case_verdict(case_result, variant_id=winner_id)
        for case_result in list(results_by_variant.get(winner_id) or [])
    ]
    baseline_case_verdicts = [
        _case_verdict(case_result, variant_id=baseline_a_id)
        for case_result in list(results_by_variant.get(baseline_a_id) or [])
    ]

    batch_report = {
        "schema_version": "active_inference.controlled_observation.batch_run.v1",
        "generated_at": _now_iso(),
        "manifest_path": str(manifest_path),
        "runner_contract": contract,
        "summary": summary,
        "authority_drift_audit": authority_drift_audit,
        "trace_contract_check": trace_contract_check,
        "host_surface_bounded_audit": host_surface_bounded_audit,
        "results_by_variant": results_by_variant,
        "winner_case_verdicts": winner_case_verdicts,
        "baseline_case_verdicts": baseline_case_verdicts,
    }

    variant_scores = {
        variant_id: _score_variant(case_results).to_dict()
        for variant_id, case_results in results_by_variant.items()
    }
    variant_scores[str(contract.get("baseline_b_id") or "")] = _baseline_b_scores().to_dict()
    selection = _bridge_selection_decision(
        candidate=_score_variant(results_by_variant[winner_id]),
        baseline_a=_score_variant(results_by_variant[baseline_a_id]),
    )
    aggregate_gate = {
        "status": "pass"
        if (
            selection.get("candidate_pass")
            and authority_drift_audit.get("status") == "pass"
            and trace_contract_check.get("status") == "pass"
            and host_surface_bounded_audit.get("status") == "pass"
            and summary["scenario_count"] == 9
            and sum(1 for verdict in winner_case_verdicts if verdict.get("pass")) == 9
            and summary["external_result_scenario_count"] >= 3
        )
        else "hold",
        "replay_gate_pass": bool(selection.get("candidate_pass")),
        "scenario_count": summary["scenario_count"],
        "winner_pass_count": sum(1 for verdict in winner_case_verdicts if verdict.get("pass")),
        "external_result_scenario_count": summary["external_result_scenario_count"],
    }
    batch_report["aggregate_gate"] = aggregate_gate

    scored_payload = {
        "schema_version": "active_inference.controlled_observation.scored.v1",
        "generated_at": _now_iso(),
        "input_report_path": str(BATCH_JSON),
        "runner_contract": contract,
        "variant_scores": variant_scores,
        "selection": selection,
        "authority_drift_audit": authority_drift_audit,
        "trace_contract_check": trace_contract_check,
        "host_surface_bounded_audit": host_surface_bounded_audit,
        "aggregate_gate": aggregate_gate,
        "winner_case_verdicts": winner_case_verdicts,
        "baseline_case_verdicts": baseline_case_verdicts,
    }
    return batch_report, scored_payload


async def main() -> None:
    args = parse_args()
    batch_report, scored_payload = await run_controlled_observation_batch(manifest_path=args.manifest)
    _write_json(args.output_json, batch_report)
    args.output_md.write_text(_render_batch_markdown(batch_report), encoding="utf-8")
    _write_json(args.scored_output_json, scored_payload)
    args.scored_output_md.write_text(_render_scored_markdown(scored_payload), encoding="utf-8")
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(f"wrote {args.scored_output_json}")
    print(f"wrote {args.scored_output_md}")


if __name__ == "__main__":
    asyncio.run(main())
