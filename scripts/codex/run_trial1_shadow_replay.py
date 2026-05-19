#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "EgoCore") not in sys.path:
    sys.path.insert(0, str(ROOT / "EgoCore"))
if str(ROOT / "OpenEmotion") not in sys.path:
    sys.path.insert(0, str(ROOT / "OpenEmotion"))

from app.openemotion_adapter.proto_self_adapter import ProtoSelfAdapter
from app.openemotion_adapter.proto_self_state_store import ProtoSelfStateStore
from app.runtime_v2.proto_self_runtime import build_external_result_event, build_proto_self_ingress_event
from app.runtime_v2.state import RuntimeV2State
from openemotion.proto_self.trial1_shadow import (
    TRIAL1_ABLATION_IDS,
    TRIAL1_BASELINE_ID,
    TRIAL1_CANDIDATE_ID,
    TRIAL1_CHALLENGER_ID,
    TRIAL1_FEATURE_FLAG_ENV,
    TRIAL1_REQUIRED_BUCKET_IDS,
    TRIAL1_SUPPORTED_VARIANT_IDS,
    build_trial1_contract,
    find_trial1_manifest_leakage,
    validate_trial1_manifest,
)


MANIFEST_PATH = (
    ROOT
    / "docs"
    / "codex"
    / "tasks"
    / "ai-self-awareness-minimal-framework"
    / "TRIAL1_REPLAY_CORPUS_MANIFEST.json"
)
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "TRIAL1_SHADOW_REPLAY_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "TRIAL1_SHADOW_REPLAY_CURRENT.md"
RUN_ROOT = ARTIFACT_ROOT / "trial1_shadow_replay"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Trial-1 shadow-only replay admission slice")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument(
        "--variants",
        nargs="*",
        default=[TRIAL1_BASELINE_ID, TRIAL1_CANDIDATE_ID, *TRIAL1_ABLATION_IDS],
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def load_manifest(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _case_variant_experiment_id(case_id: str, variant_id: str) -> str:
    return f"trial1.{variant_id}.{case_id}"


def _build_adapter(base_dir: Path) -> ProtoSelfAdapter:
    mirror_dir = base_dir / "mirror"
    state_store = ProtoSelfStateStore(
        root_dir=base_dir / "proto_self_store",
        legacy_mirror_dir=mirror_dir,
    )
    return ProtoSelfAdapter(mirror_dir=mirror_dir, state_store=state_store)


def _summarize_state(adapter: ProtoSelfAdapter, *, experiment_id: str) -> Dict[str, Any]:
    state_v2 = adapter.state_store.load_experiment_state_v2(experiment_id)
    state = state_v2.to_v1()
    last_episode = state.episodic_trace[-1].to_dict() if state.episodic_trace else {}
    return {
        "current_mode": state.self_model.current_mode,
        "current_focus": state.self_model.current_focus,
        "viability_pressure": round(float(state.drives.viability_pressure), 4),
        "counterfactual_success_by_action": dict(state.self_model.counterfactual_success_by_action),
        "recent_correction_tags": dict(state.self_model.recent_correction_tags),
        "episodic_count": len(state.episodic_trace),
        "revision_counter": state.revision_counter,
        "last_corrective_trace": dict(last_episode.get("corrective_trace") or {}),
    }


def _patch_payload(
    payload: Dict[str, Any],
    *,
    step: Dict[str, Any],
    bucket_id: str,
    case_id: str,
    experiment_id: str,
    variant_id: str,
) -> Dict[str, Any]:
    patched = dict(payload)
    runtime_summary = dict(patched.get("runtime_summary") or {})
    runtime_summary["state_scope"] = "experiment"
    runtime_summary["experiment_id"] = experiment_id
    runtime_summary["trial1_shadow"] = {
        "enabled": True,
        "shadow_only": True,
        "variant_id": variant_id,
        "action_family": step.get("action_family"),
        "bucket_id": bucket_id,
        "case_id": case_id,
        "step_id": step.get("step_id"),
    }
    if step.get("restore_observation") is not None:
        runtime_summary["restore_observation"] = dict(step["restore_observation"])
    patched["runtime_summary"] = runtime_summary

    if patched.get("schema_version") == "proto_self.v2":
        if step.get("task_summary_patch"):
            task_summary = dict(patched.get("task_summary") or {})
            task_summary.update(dict(step.get("task_summary_patch") or {}))
            patched["task_summary"] = task_summary
        if step.get("safety_context_patch"):
            safety_context = dict(patched.get("safety_context") or {})
            safety_context.update(dict(step.get("safety_context_patch") or {}))
            patched["safety_context"] = safety_context
        if step.get("executed_action_prev"):
            patched["executed_action_prev"] = dict(step["executed_action_prev"])
    return patched


def _run_step(
    *,
    adapter: ProtoSelfAdapter,
    state: RuntimeV2State,
    step: Dict[str, Any],
    bucket_id: str,
    case_id: str,
    experiment_id: str,
    variant_id: str,
) -> Dict[str, Any]:
    state.session_id = str(step["session_id"])
    state.current_goal = step.get("current_goal") or state.current_goal
    state.ingress_context = {
        "proto_self_version": "v2",
        "restore_observation": step.get("restore_observation"),
        "executed_action_prev": step.get("executed_action_prev"),
        "prediction_snapshot_prev": step.get("prediction_snapshot_prev", {}),
    }

    if step["kind"] == "ingress":
        payload = build_proto_self_ingress_event(
            session_id=str(step["session_id"]),
            turn_id=str(step["turn_id"]),
            source="replay",
            user_input=str(step["user_input"]),
            state=state,
        )
    elif step["kind"] == "tool_result":
        tool_result = dict(step["tool_result"])
        state.last_tool_result = tool_result
        payload = build_external_result_event(
            session_id=str(step["session_id"]),
            turn_id=str(step["turn_id"]),
            step=int(step.get("step", 0)),
            tool_result=tool_result,
            state=state,
        )
    else:
        raise ValueError(f"unsupported step kind: {step['kind']}")

    payload = _patch_payload(
        payload,
        step=step,
        bucket_id=bucket_id,
        case_id=case_id,
        experiment_id=experiment_id,
        variant_id=variant_id,
    )
    result = adapter.handle_event(payload)
    state_snapshot = _summarize_state(adapter, experiment_id=experiment_id)
    return {
        "step_id": step["step_id"],
        "kind": step["kind"],
        "event_id": result.get("event_id"),
        "policy_hint": dict(result.get("policy_hint") or {}),
        "response_tendency": dict(result.get("response_tendency") or {}),
        "reflection_note": dict(result.get("reflection_note") or {}),
        "self_model_delta": dict(result.get("self_model_delta") or {}),
        "drives_delta": dict(result.get("drives_delta") or result.get("appraisal_state_delta") or {}),
        "memory_update": dict(result.get("memory_update") or {}),
        "trace_payload": dict(result.get("trace_payload") or {}),
        "state_snapshot": state_snapshot,
    }


def _run_case(variant_id: str, bucket_id: str, case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = str(case["case_id"])
    experiment_id = _case_variant_experiment_id(case_id, variant_id)
    case_root = RUN_ROOT / variant_id / case_id
    adapter = _build_adapter(case_root)
    state = RuntimeV2State(session_id=str(case["steps"][0]["session_id"]))
    step_logs = [
        _run_step(
            adapter=adapter,
            state=state,
            step=dict(step),
            bucket_id=bucket_id,
            case_id=case_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
        )
        for step in list(case.get("steps") or [])
    ]
    return {
        "case_id": case_id,
        "bucket_id": bucket_id,
        "experiment_id": experiment_id,
        "source_type": case.get("source_type"),
        "source_ref": case.get("source_ref"),
        "steps": step_logs,
    }


def _cases_from_manifest(manifest: Dict[str, Any]) -> list[tuple[str, Dict[str, Any]]]:
    items: list[tuple[str, Dict[str, Any]]] = []
    for bucket in list(manifest.get("buckets") or []):
        bucket_id = str(bucket.get("bucket_id") or "")
        for case in list(bucket.get("cases") or []):
            items.append((bucket_id, dict(case)))
    return items


def _case_signal_summary(case_result: Dict[str, Any]) -> Dict[str, Any]:
    steps = list(case_result.get("steps") or [])
    followup_ingress = [step for step in steps if step["kind"] == "ingress"][1:]
    return {
        "has_failure_reflection": any(step["reflection_note"] for step in steps if step["kind"] == "tool_result"),
        "has_corrective_trace": any(
            bool((step["memory_update"] or {}).get("corrective_trace")) for step in steps
        ),
        "followup_modes": [step["response_tendency"].get("preferred_mode") for step in followup_ingress],
        "followup_guarded": any(
            bool(step["policy_hint"].get("shadow_repair_bias") or step["policy_hint"].get("shadow_counterfactual_guard"))
            for step in followup_ingress
        ),
        "final_viability_pressure": steps[-1]["state_snapshot"]["viability_pressure"] if steps else 0.0,
        "final_correction_tags": dict(steps[-1]["state_snapshot"]["recent_correction_tags"]) if steps else {},
    }


def _build_summary(results_by_variant: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"variants": {}}
    baseline_cases = {
        item["case_id"]: _case_signal_summary(item) for item in results_by_variant.get(TRIAL1_BASELINE_ID, [])
    }
    candidate_cases = {
        item["case_id"]: _case_signal_summary(item) for item in results_by_variant.get(TRIAL1_CANDIDATE_ID, [])
    }

    for variant_id, case_results in results_by_variant.items():
        signals = [_case_signal_summary(case_result) for case_result in case_results]
        summary["variants"][variant_id] = {
            "case_count": len(case_results),
            "cases_with_corrective_trace": sum(1 for item in signals if item["has_corrective_trace"]),
            "cases_with_followup_guard": sum(1 for item in signals if item["followup_guarded"]),
            "max_final_viability_pressure": max((item["final_viability_pressure"] for item in signals), default=0.0),
        }

    candidate_over_baseline = {}
    for case_id, candidate_signal in candidate_cases.items():
        baseline_signal = baseline_cases.get(case_id, {})
        candidate_over_baseline[case_id] = {
            "candidate_followup_modes": candidate_signal.get("followup_modes", []),
            "baseline_followup_modes": baseline_signal.get("followup_modes", []),
            "guard_shift": bool(candidate_signal.get("followup_guarded"))
            and not bool(baseline_signal.get("followup_guarded")),
            "corrective_trace_shift": bool(candidate_signal.get("has_corrective_trace"))
            and not bool(baseline_signal.get("has_corrective_trace")),
        }
    summary["candidate_over_baseline"] = candidate_over_baseline
    summary["challenger_status"] = "live_not_implemented"
    return summary


def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# Trial-1 Shadow Replay",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- manifest: `{report['manifest_path']}`",
        f"- variants_run: `{', '.join(report['variants_run'])}`",
        f"- challenger_status: `{report['summary']['challenger_status']}`",
        "",
        "## Variant Summary",
        "",
    ]
    for variant_id, variant_summary in report["summary"]["variants"].items():
        lines.append(
            f"- `{variant_id}`: cases={variant_summary['case_count']}, "
            f"corrective_trace_cases={variant_summary['cases_with_corrective_trace']}, "
            f"followup_guard_cases={variant_summary['cases_with_followup_guard']}, "
            f"max_viability={variant_summary['max_final_viability_pressure']:.3f}"
        )
    lines.extend(["", "## Candidate Over Baseline", ""])
    for case_id, case_summary in report["summary"]["candidate_over_baseline"].items():
        lines.append(
            f"- `{case_id}`: baseline_followup={case_summary['baseline_followup_modes']}, "
            f"candidate_followup={case_summary['candidate_followup_modes']}, "
            f"guard_shift={case_summary['guard_shift']}, "
            f"corrective_trace_shift={case_summary['corrective_trace_shift']}"
        )
    lines.extend(
        [
            "",
            "## Claim Ceiling",
            "",
            "- This artifact only shows shadow-only Trial-1 admission signals.",
            "- It does not claim replay threshold pass, runtime efficacy, or any consciousness-like property.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    manifest_errors = validate_trial1_manifest(manifest)
    leakage_errors = find_trial1_manifest_leakage(manifest)
    if manifest_errors:
        raise SystemExit("invalid Trial-1 manifest:\n- " + "\n- ".join(manifest_errors))
    if leakage_errors:
        raise SystemExit("leakage detected:\n- " + "\n- ".join(leakage_errors))

    contract = build_trial1_contract()
    variants = [variant_id for variant_id in args.variants if variant_id in TRIAL1_SUPPORTED_VARIANT_IDS]
    os.environ[TRIAL1_FEATURE_FLAG_ENV] = "true"

    results_by_variant: Dict[str, Any] = {}
    for variant_id in variants:
        case_results = []
        for bucket_id, case in _cases_from_manifest(manifest):
            case_results.append(_run_case(variant_id=variant_id, bucket_id=bucket_id, case=case))
        results_by_variant[variant_id] = case_results

    report = {
        "generated_at": now_iso(),
        "manifest_path": str(args.manifest),
        "contract": contract,
        "required_bucket_ids": list(TRIAL1_REQUIRED_BUCKET_IDS),
        "variants_run": variants,
        "challenger_id": TRIAL1_CHALLENGER_ID,
        "challenger_status": "live_not_implemented",
        "results_by_variant": results_by_variant,
        "summary": _build_summary(results_by_variant),
    }
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {REPORT_JSON}")
    print(f"Wrote {REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
