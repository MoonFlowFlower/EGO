#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
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
from openemotion.proto_self.mvs_replay import (
    MVS_BASELINE_A_ID,
    MVS_CANDIDATE_ID,
    MVS_CHALLENGER_ID,
    MVS_REPLAY_FEATURE_FLAG_ENV,
    MVS_ABLATION_MINUS_BOUNDARY_ID,
    MVS_ABLATION_MINUS_CORRECTIVE_TRACE_ID,
    MVS_ABLATION_MINUS_COUNTERFACTUAL_ID,
    MVS_ABLATION_MINUS_VIABILITY_ID,
    build_mvs_contract,
    iter_mvs_cases,
    validate_mvs_manifest,
)


TASK_ROOT = ROOT / "docs" / "codex" / "tasks" / "ai-self-awareness-minimal-framework"
MANIFEST_PATH = TASK_ROOT / "MVS_REPLAY_CORPUS_MANIFEST.json"
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "MVS_REPLAY_VALIDATOR_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "MVS_REPLAY_VALIDATOR_CURRENT.md"

DEFAULT_VARIANTS = [
    MVS_BASELINE_A_ID,
    MVS_CANDIDATE_ID,
    MVS_ABLATION_MINUS_COUNTERFACTUAL_ID,
    MVS_ABLATION_MINUS_VIABILITY_ID,
    MVS_ABLATION_MINUS_CORRECTIVE_TRACE_ID,
    MVS_ABLATION_MINUS_BOUNDARY_ID,
    MVS_CHALLENGER_ID,
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the held-out MVS replay validator")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output-json", type=Path, default=REPORT_JSON)
    parser.add_argument("--output-md", type=Path, default=REPORT_MD)
    parser.add_argument("--variants", nargs="*", default=DEFAULT_VARIANTS)
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


class _NullTraceBridge:
    def write(self, trace_payload: Dict[str, Any]) -> None:
        return None


def _build_adapter(base_dir: Path) -> ProtoSelfAdapter:
    mirror_dir = base_dir / "mirror"
    return ProtoSelfAdapter(
        mirror_dir=mirror_dir,
        state_store=ProtoSelfStateStore(
            root_dir=base_dir / "proto_self_store",
            legacy_mirror_dir=mirror_dir,
        ),
        trace_bridge=_NullTraceBridge(),
    )


def _case_variant_experiment_id(case_id: str, variant_id: str) -> str:
    return f"mvs.replay.{variant_id}.{case_id}"


def _summarize_state(adapter: ProtoSelfAdapter, *, experiment_id: str) -> Dict[str, Any]:
    state = adapter.state_store.load_experiment_state_v2(experiment_id).to_v1()
    last_episode = state.episodic_trace[-1].to_dict() if state.episodic_trace else {}
    return {
        "current_mode": state.self_model.current_mode,
        "current_focus": state.self_model.current_focus,
        "viability_pressure": round(float(state.drives.viability_pressure), 4),
        "counterfactual_success_by_action": dict(state.self_model.counterfactual_success_by_action),
        "boundary_confidence_by_action": dict(state.self_model.boundary_confidence_by_action),
        "world_assumption_confidence": dict(state.self_model.world_assumption_confidence),
        "recent_correction_tags": dict(state.self_model.recent_correction_tags),
        "source_confidence_by_action": dict(state.self_model.source_confidence_by_action),
        "agency_confidence_by_action": dict(state.self_model.agency_confidence_by_action),
        "uncertainty_by_action": dict(state.self_model.uncertainty_by_action),
        "calibration_memory_by_action": dict(state.self_model.calibration_memory_by_action),
        "temporal_repair_weight_by_action": dict(state.self_model.temporal_repair_weight_by_action),
        "episodic_count": len(state.episodic_trace),
        "revision_counter": state.revision_counter,
        "last_corrective_trace": dict(last_episode.get("corrective_trace") or {}),
    }


def _normalize_step(step: Dict[str, Any], *, case_id: str, index: int) -> Dict[str, Any]:
    normalized = dict(step)
    normalized.setdefault("session_id", f"mvs-replay:{case_id}")
    normalized.setdefault("turn_id", f"turn_{index + 1:03d}")
    normalized.setdefault("step", index)
    return normalized


def _preload_experiment_state(
    adapter: ProtoSelfAdapter,
    *,
    experiment_id: str,
    preloaded_state: Dict[str, Any],
) -> None:
    state = adapter.state_store.load_experiment_state(experiment_id)
    state.self_model.counterfactual_success_by_action = {
        str(key): float(value)
        for key, value in dict(preloaded_state.get("counterfactual_success_by_action") or {}).items()
    }
    state.self_model.boundary_confidence_by_action = {
        str(key): float(value)
        for key, value in dict(preloaded_state.get("boundary_confidence_by_action") or {}).items()
    }
    state.self_model.world_assumption_confidence = {
        str(key): float(value)
        for key, value in dict(preloaded_state.get("world_assumption_confidence") or {}).items()
    }
    state.self_model.recent_correction_tags = {
        str(key): float(value)
        for key, value in dict(preloaded_state.get("recent_correction_tags") or {}).items()
    }
    state.drives.viability_pressure = float(preloaded_state.get("viability_pressure", 0.0))
    adapter.state_store.save_experiment_state(experiment_id, state)


def _patch_payload(
    payload: Dict[str, Any],
    *,
    step: Dict[str, Any],
    case: Dict[str, Any],
    experiment_id: str,
    variant_id: str,
) -> Dict[str, Any]:
    patched = dict(payload)
    runtime_summary = dict(patched.get("runtime_summary") or {})
    runtime_summary["state_scope"] = "experiment"
    runtime_summary["experiment_id"] = experiment_id
    runtime_summary["mvs_replay"] = {
        "enabled": True,
        "shadow_only": True,
        "variant_id": variant_id,
        "action_family": step.get("action_family"),
        "family": case.get("family"),
        "case_id": case.get("case_id"),
        "step_id": step.get("step_id"),
    }
    patched["runtime_summary"] = runtime_summary

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
    case: Dict[str, Any],
    experiment_id: str,
    variant_id: str,
) -> Dict[str, Any]:
    state.session_id = str(step["session_id"])
    state.current_goal = step.get("current_goal") or state.current_goal
    state.ingress_context = {
        "proto_self_version": "v2",
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
        case=case,
        experiment_id=experiment_id,
        variant_id=variant_id,
    )
    result = adapter.handle_event(payload)
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
        "state_snapshot": _summarize_state(adapter, experiment_id=experiment_id),
    }


def _run_case(variant_id: str, case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = str(case["case_id"])
    experiment_id = _case_variant_experiment_id(case_id, variant_id)
    with tempfile.TemporaryDirectory(prefix="mvs_replay_") as temp_dir:
        adapter = _build_adapter(Path(temp_dir))
        _preload_experiment_state(
            adapter,
            experiment_id=experiment_id,
            preloaded_state=dict(case.get("preloaded_state") or {}),
        )
        steps = [
            _normalize_step(dict(step), case_id=case_id, index=index)
            for index, step in enumerate(list(case.get("steps") or []))
        ]
        state = RuntimeV2State(session_id=str(steps[0]["session_id"]))
        step_logs = [
            _run_step(
                adapter=adapter,
                state=state,
                step=step,
                case=case,
                experiment_id=experiment_id,
                variant_id=variant_id,
            )
            for step in steps
        ]
    return {
        "case_id": case_id,
        "family": case.get("family"),
        "source_type": case.get("source_type"),
        "source_ref": case.get("source_ref"),
        "preloaded_state": dict(case.get("preloaded_state") or {}),
        "expected_scoring_surface": dict(case.get("expected_scoring_surface") or {}),
        "steps": step_logs,
    }


def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# MVS Replay Validator",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- manifest: `{report['manifest_path']}`",
        f"- variants_run: `{', '.join(report['variants_run'])}`",
        f"- case_count: `{report['summary']['case_count']}`",
        "",
        "## Variant Coverage",
        "",
    ]
    for variant_id, summary in sorted(report["summary"]["variants"].items()):
        lines.append(f"- `{variant_id}`: cases=`{summary['case_count']}` steps=`{summary['step_count']}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    os.environ.setdefault(MVS_REPLAY_FEATURE_FLAG_ENV, "true")

    manifest = load_json(args.manifest)
    errors = validate_mvs_manifest(manifest)
    if errors:
        raise SystemExit("\n".join(errors))

    contract = build_mvs_contract()
    variant_ids = [variant for variant in args.variants if variant != contract["baseline_b_id"]]
    case_list = iter_mvs_cases(manifest)

    results_by_variant = {}
    for variant_id in variant_ids:
        case_results = []
        for index, case in enumerate(case_list, start=1):
            if index == 1 or index % 10 == 0 or index == len(case_list):
                print(f"[mvs-replay] variant={variant_id} case={index}/{len(case_list)}", flush=True)
            case_results.append(_run_case(variant_id, case))
        results_by_variant[variant_id] = case_results
    summary = {
        "case_count": len(case_list),
        "variants": {
            variant_id: {
                "case_count": len(case_results),
                "step_count": sum(len(case_result.get("steps") or []) for case_result in case_results),
            }
            for variant_id, case_results in results_by_variant.items()
        },
    }
    report = {
        "schema_version": "mvs.replay_validator_run.v1",
        "generated_at": now_iso(),
        "manifest_path": str(args.manifest),
        "runner_contract": contract,
        "variants_run": variant_ids,
        "summary": summary,
        "results_by_variant": results_by_variant,
    }
    write_json(args.output_json, report)
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")


if __name__ == "__main__":
    main()
