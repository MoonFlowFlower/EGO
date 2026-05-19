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
    TRIAL1_ABLATION_ALTERNATIVE_EXPLANATION_ISOLATION_ID,
    TRIAL1_ABLATION_COUNTERFACTUAL_PUBLIC_PATH_SEVER_ID,
    TRIAL1_BASELINE_ID,
    TRIAL1_CANDIDATE_ID,
    TRIAL1_CHALLENGER_ID,
    TRIAL1_FEATURE_FLAG_ENV,
    build_trial1_contract,
)


TASK_ROOT = ROOT / "docs" / "codex" / "tasks" / "ai-self-awareness-minimal-framework"
HARD_SET_PATH = TASK_ROOT / "TRIAL1_COUNTERFACTUAL_HARD_SET.json"
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "TRIAL1_HARD_SET_RERUN_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "TRIAL1_HARD_SET_RERUN_CURRENT.md"
RUN_ROOT = ARTIFACT_ROOT / "trial1_hard_set_rerun"

DEFAULT_VARIANTS = [
    TRIAL1_BASELINE_ID,
    TRIAL1_CANDIDATE_ID,
    TRIAL1_ABLATION_COUNTERFACTUAL_PUBLIC_PATH_SEVER_ID,
    TRIAL1_ABLATION_ALTERNATIVE_EXPLANATION_ISOLATION_ID,
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Trial-1 hard-set rerun for redesigned ablations")
    parser.add_argument("--hard-set", type=Path, default=HARD_SET_PATH)
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


def _build_adapter(base_dir: Path) -> ProtoSelfAdapter:
    mirror_dir = base_dir / "mirror"
    state_store = ProtoSelfStateStore(
        root_dir=base_dir / "proto_self_store",
        legacy_mirror_dir=mirror_dir,
    )
    return ProtoSelfAdapter(mirror_dir=mirror_dir, state_store=state_store)


def _case_variant_experiment_id(case_id: str, variant_id: str) -> str:
    return f"trial1.hardset.{variant_id}.{case_id}"


def _summarize_state(adapter: ProtoSelfAdapter, *, experiment_id: str) -> Dict[str, Any]:
    state = adapter.state_store.load_experiment_state_v2(experiment_id).to_v1()
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


def _normalize_step(step: Dict[str, Any], *, case_id: str, index: int) -> Dict[str, Any]:
    normalized = dict(step)
    normalized.setdefault("session_id", f"trial1-hard-set:{case_id}")
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
    runtime_summary["trial1_shadow"] = {
        "enabled": True,
        "shadow_only": True,
        "variant_id": variant_id,
        "action_family": step.get("action_family"),
        "bucket_id": case.get("bucket_id"),
        "case_id": case.get("case_id"),
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
    case: Dict[str, Any],
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
        case=case,
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


def _run_case(variant_id: str, case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = str(case["case_id"])
    experiment_id = _case_variant_experiment_id(case_id, variant_id)
    case_root = RUN_ROOT / variant_id / case_id
    adapter = _build_adapter(case_root)
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
        "bucket_id": case.get("bucket_id"),
        "diagnostic_role": case.get("diagnostic_role"),
        "why_hard": case.get("why_hard"),
        "expected_representation_neutral_gap": dict(case.get("expected_representation_neutral_gap") or {}),
        "experiment_id": experiment_id,
        "source_type": "diagnostic_hard_set",
        "source_ref": str(HARD_SET_PATH),
        "steps": step_logs,
    }


def _case_signal_summary(case_result: Dict[str, Any]) -> Dict[str, Any]:
    steps = list(case_result.get("steps") or [])
    return {
        "has_corrective_trace": any(bool((step["memory_update"] or {}).get("corrective_trace")) for step in steps),
        "followup_modes": [step["response_tendency"].get("preferred_mode") for step in steps if step["kind"] == "ingress"],
        "followup_guarded": any(
            bool(step["policy_hint"].get("shadow_repair_bias") or step["policy_hint"].get("shadow_counterfactual_guard"))
            for step in steps
        ),
        "ask_preferred": any(bool(step["policy_hint"].get("ask_preferred")) for step in steps),
        "final_viability_pressure": steps[-1]["state_snapshot"]["viability_pressure"] if steps else 0.0,
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
            "cases_with_ask_preferred": sum(1 for item in signals if item["ask_preferred"]),
            "max_final_viability_pressure": max((item["final_viability_pressure"] for item in signals), default=0.0),
        }
    summary["candidate_over_baseline"] = {
        case_id: {
            "candidate_followup_modes": candidate_signal.get("followup_modes", []),
            "baseline_followup_modes": baseline_cases.get(case_id, {}).get("followup_modes", []),
            "guard_shift": bool(candidate_signal.get("followup_guarded"))
            and not bool(baseline_cases.get(case_id, {}).get("followup_guarded")),
            "ask_shift": bool(candidate_signal.get("ask_preferred"))
            and not bool(baseline_cases.get(case_id, {}).get("ask_preferred")),
        }
        for case_id, candidate_signal in candidate_cases.items()
    }
    summary["challenger_status"] = "live_not_scored"
    return summary


def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# Trial-1 Hard-Set Rerun",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- hard_set: `{report['hard_set_path']}`",
        f"- variants_run: `{', '.join(report['variants_run'])}`",
        f"- preregistration_refs: `{', '.join(report['preregistration_refs'])}`",
        "",
        "## Variant Summary",
        "",
    ]
    for variant_id, variant_summary in report["summary"]["variants"].items():
        lines.append(
            f"- `{variant_id}`: cases={variant_summary['case_count']}, "
            f"ask_preferred_cases={variant_summary['cases_with_ask_preferred']}, "
            f"guarded_cases={variant_summary['cases_with_followup_guard']}, "
            f"trace_cases={variant_summary['cases_with_corrective_trace']}, "
            f"max_viability={variant_summary['max_final_viability_pressure']:.3f}"
        )
    lines.extend(["", "## Candidate Over Baseline", ""])
    for case_id, case_summary in report["summary"]["candidate_over_baseline"].items():
        lines.append(
            f"- `{case_id}`: baseline_followup={case_summary['baseline_followup_modes']}, "
            f"candidate_followup={case_summary['candidate_followup_modes']}, "
            f"guard_shift={case_summary['guard_shift']}, "
            f"ask_shift={case_summary['ask_shift']}"
        )
    lines.extend(
        [
            "",
            "## Claim Ceiling",
            "",
            "- This artifact is diagnostic-only and limited to the existing hard set.",
            "- It does not expand the official replay suite or upgrade repo-level state.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    hard_set = load_json(args.hard_set)
    cases = list(hard_set.get("cases") or [])
    contract = build_trial1_contract(
        ablation_ids=(
            TRIAL1_ABLATION_COUNTERFACTUAL_PUBLIC_PATH_SEVER_ID,
            TRIAL1_ABLATION_ALTERNATIVE_EXPLANATION_ISOLATION_ID,
        )
    )
    variants = [variant_id for variant_id in args.variants if variant_id in contract["supported_variant_ids"]]
    os.environ[TRIAL1_FEATURE_FLAG_ENV] = "true"

    results_by_variant: Dict[str, Any] = {}
    for variant_id in variants:
        results_by_variant[variant_id] = [_run_case(variant_id=variant_id, case=dict(case)) for case in cases]

    report = {
        "generated_at": now_iso(),
        "hard_set_path": str(args.hard_set),
        "hard_set_case_ids": [str(case.get("case_id") or "") for case in cases],
        "contract": contract,
        "variants_run": variants,
        "challenger_id": TRIAL1_CHALLENGER_ID,
        "challenger_status": "live_not_scored",
        "runner_mode": "diagnostic_hard_set_only",
        "preregistration_refs": [
            str(TASK_ROOT / "TRIAL1_ABLATION_FIDELITY_CHECKS.md"),
            str(TASK_ROOT / "TRIAL1_OUTCOME_INTERPRETATION_MATRIX.md"),
            str(TASK_ROOT / "TRIAL1_GAP_THRESHOLDS.md"),
        ],
        "results_by_variant": results_by_variant,
        "summary": _build_summary(results_by_variant),
    }
    write_json(args.output_json, report)
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
