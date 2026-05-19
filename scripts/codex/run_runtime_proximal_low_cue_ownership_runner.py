#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(ROOT / "EgoCore") not in sys.path:
    sys.path.insert(0, str(ROOT / "EgoCore"))
if str(ROOT / "OpenEmotion") not in sys.path:
    sys.path.insert(0, str(ROOT / "OpenEmotion"))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from app.response_contract.output_check import apply_output_check
from app.response_contract.response_plan import build_runtime_result_response_plan
from app.runtime_v2.chat_reply_engine import (
    _build_chat_cadence_mode,
    _build_chat_expression_hint,
    _build_response_tendency_summary,
)
from app.runtime_v2.runtime_reply import RuntimeV2Reply, RuntimeV2TurnResult
from app.runtime_v2.unified_channel_contract import (
    build_host_contract_snapshot,
    build_telegram_unified_request,
    build_unified_egress,
    build_unified_ingress,
    build_unified_turn_result,
)
from app.telegram_runtime_bridge import TelegramRuntimeBridge
from openemotion.proto_self.mvs_replay import MVS_REPLAY_FEATURE_FLAG_ENV
from run_active_inference_controlled_observation import (
    _authority_drift_audit,
    _build_private_safety_overrides,
    _build_runtime_overrides,
    _build_step_log,
    _configure_isolated_runtime,
    _extract_turn_id,
    _host_surface_bounded_audit,
    _patch_ingress_context,
    _prepare_ingress_context,
)
from run_runtime_proximal_host_consumption_runner import (
    _collect_diffs,
    _runner_canonical_trace,
    _runner_trace_contract_check,
    _snapshot_compare_surface,
    _trace_surface,
)
from runtime_mainline_observation_common import build_runtime_observation_record


TASK_ROOT = ROOT / "docs" / "codex" / "tasks" / "runtime-proximal-low-cue-ownership-runner-implementation"
MANIFEST_PATH = TASK_ROOT / "RUNNER_MANIFEST.json"
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "RUNTIME_PROXIMAL_LOW_CUE_OWNERSHIP_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "RUNTIME_PROXIMAL_LOW_CUE_OWNERSHIP_CURRENT.md"
SCHEMA_VERSION = "runtime_proximal_low_cue_ownership_runner.v1"
ALLOWED_FAMILIES = {
    "low_cue_persistence",
    "ownership_ambiguity",
    "agency_attribution_after_correction",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the runtime-proximal low-cue ownership runner")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output-json", type=Path, default=REPORT_JSON)
    parser.add_argument("--output-md", type=Path, default=REPORT_MD)
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def validate_manifest(manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if manifest.get("schema_version") != "runtime_proximal_low_cue_ownership_runner_manifest.v1":
        errors.append("schema_version must be runtime_proximal_low_cue_ownership_runner_manifest.v1")
    contract = dict(manifest.get("runner_contract") or {})
    expected_supported = [
        contract.get("baseline_a_id"),
        contract.get("candidate_id"),
    ]
    if list(contract.get("supported_variant_ids") or []) != expected_supported:
        errors.append("runner_contract.supported_variant_ids must match baseline_a_id + candidate_id")

    scenarios = [dict(item) for item in list(manifest.get("scenarios") or [])]
    if len(scenarios) != 3:
        errors.append("runner manifest must contain exactly 3 scenarios")
    families = {str(item.get("family") or "") for item in scenarios}
    if families != ALLOWED_FAMILIES:
        errors.append("runner manifest must contain exactly low_cue_persistence / ownership_ambiguity / agency_attribution_after_correction")

    external_result_scenario_count = 0
    for scenario in scenarios:
        scenario_id = str(scenario.get("scenario_id") or "").strip()
        if not scenario_id:
            errors.append("scenario_id is required")
        if str(scenario.get("source_type") or "").strip() != "repo_authored_observation_scenario":
            errors.append(f"{scenario_id}: source_type must stay repo_authored_observation_scenario")
        if not list(scenario.get("segments") or []):
            errors.append(f"{scenario_id}: segments must not be empty")
        if str(scenario.get("state_snapshot_ref") or "").strip() == "":
            errors.append(f"{scenario_id}: state_snapshot_ref is required")
        if not dict(scenario.get("expected_scoring_surface") or {}):
            errors.append(f"{scenario_id}: expected_scoring_surface is required")
        if list(scenario.get("external_result_steps") or []):
            external_result_scenario_count += 1
    if external_result_scenario_count < 2:
        errors.append("runner manifest must contain at least two scenarios with external_result_steps")
    return errors


def _adapt_ingress_context_for_family(
    ingress_context: Dict[str, Any],
    *,
    scenario: Dict[str, Any],
) -> Dict[str, Any]:
    family = str(scenario.get("family") or "")
    patched = dict(ingress_context or {})
    patched["interaction_kind"] = "chat"
    patched["runtime_action"] = "chat"
    patched["primary_intent"] = "chat"
    patched["parser_source"] = "runtime_proximal_low_cue_ownership_runner"
    if family in {"low_cue_persistence", "ownership_ambiguity"}:
        patched["conversation_act"] = "light_chitchat"
    elif family == "agency_attribution_after_correction":
        patched["conversation_act"] = "thread_continue"
    return patched


async def _run_variant_for_scenario(
    *,
    scenario: Dict[str, Any],
    contract: Dict[str, Any],
    variant_id: str,
) -> Dict[str, Any]:
    scenario_id = str(scenario.get("scenario_id") or "")
    experiment_id = str(contract.get("experiment_id_template") or "runtime_proximal_low_cue_ownership:{scenario_id}").format(
        scenario_id=scenario_id
    )
    external_result_steps = list(scenario.get("external_result_steps") or [])
    by_message_index: Dict[int, List[Dict[str, Any]]] = {}
    for item in external_result_steps:
        index = int(item.get("after_message_index") or 0)
        by_message_index.setdefault(index, []).append(dict(item))

    with tempfile.TemporaryDirectory(prefix="runtime_proximal_low_cue_ownership_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        runtime, adapter = _configure_isolated_runtime(temp_dir)

        async def _bounded_chat_surface_reply(state: Any) -> RuntimeV2TurnResult:
            ingress = dict(getattr(state, "ingress_context", None) or {})
            chat_act = str(ingress.get("conversation_act") or "light_chitchat").strip() or "light_chitchat"
            chat_expression_hint = _build_chat_expression_hint(state, conversation_act=chat_act)
            response_tendency_summary = _build_response_tendency_summary(state, chat_expression_hint)
            preferred_mode = str(response_tendency_summary.get("preferred_mode") or "").strip().lower()
            if preferred_mode == "ask":
                reply_text = "先别跳结论。你先说当前最稳的下一步是什么。"
            elif preferred_mode == "repair":
                reply_text = "先记住刚才的失败，再沿着同一条边界继续。"
            elif preferred_mode == "defer":
                reply_text = "先保留这条边界，不急着把来源和成功状态说死。"
            else:
                reply_text = "先沿着当前边界继续。"
            state.finalize_chat_turn(assistant_reply=reply_text, chat_act=chat_act)
            state.last_model_action = {
                "type": "chat",
                "message": reply_text,
                "chat_act": chat_act,
                "reply_authority": "model_chat",
                "chat_expression_hint": chat_expression_hint,
                "chat_cadence_mode": _build_chat_cadence_mode(chat_expression_hint),
                "response_tendency_summary": response_tendency_summary,
            }
            state.record(
                "assistant",
                {
                    "type": "chat_reply",
                    "text": reply_text,
                    "chat_act": chat_act,
                    "reply_authority": "model_chat",
                    "reply_origin": "chat_mainline",
                    "chat_expression_hint": chat_expression_hint,
                    "chat_cadence_mode": _build_chat_cadence_mode(chat_expression_hint),
                    "response_tendency_summary": response_tendency_summary,
                    "degraded": False,
                    "chat_degradation": None,
                },
            )
            state.last_delivery_type = "chat"
            return RuntimeV2TurnResult(
                status="chat",
                state=state,
                reply=RuntimeV2Reply(
                    reply_text=reply_text,
                    delivery_kind="chat",
                    status="chat",
                    metadata={
                        "chat_act": chat_act,
                        "reply_origin": "chat_mainline",
                        "reply_authority": "model_chat",
                        "chat_expression_hint": chat_expression_hint,
                        "chat_cadence_mode": _build_chat_cadence_mode(chat_expression_hint),
                        "response_tendency_summary": response_tendency_summary,
                        "degraded": False,
                    },
                ),
                finish_reason="chat_mainline",
            )

        runtime.chat_reply_engine.reply = _bounded_chat_surface_reply
        bridge = TelegramRuntimeBridge()
        observation_records: List[Dict[str, Any]] = []
        case_steps: List[Dict[str, Any]] = []
        message_index = 0
        step_ordinal = 0

        for segment in list(scenario.get("segments") or []):
            segment_id = str(segment.get("segment_id") or "").strip() or f"segment_{message_index+1:03d}"
            session_id = str(
                contract.get("segment_session_id_template")
                or "session:runtime_proximal_low_cue_ownership:{scenario_id}:{segment_id}"
            ).format(scenario_id=scenario_id, segment_id=segment_id)
            for text in list(segment.get("messages") or []):
                message_index += 1
                step_ordinal += 1
                state = runtime.get_state(session_id)
                request = build_telegram_unified_request(
                    session_key=session_id,
                    text=str(text),
                    chat_id=8420019401,
                    user_id=456,
                    username="low_cue_ownership",
                    message_id=step_ordinal,
                    source_kind="telegram_prepared",
                )
                ingress = await build_unified_ingress(request, state, bridge=bridge, llm_client=None)
                patched_ingress_context = await _prepare_ingress_context(
                    bridge,
                    text=str(text),
                    state=state,
                    scenario=scenario,
                    segment_id=segment_id,
                    variant_id=variant_id,
                    experiment_id=experiment_id,
                    action_family=str((scenario.get("expected_scoring_surface") or {}).get("probe_key") or "unknown"),
                )
                patched_ingress_context = _adapt_ingress_context_for_family(
                    patched_ingress_context,
                    scenario=scenario,
                )
                ingress.ingress_context = patched_ingress_context
                state.ingress_context = patched_ingress_context
                ingress_created_at = _now_iso()
                ingress_event_id = f"runtime_proximal_low_cue_ownership_ingress_{step_ordinal:03d}"
                runtime_result = await runtime.run_turn_typed(
                    session_id=session_id,
                    user_input=str(text),
                    source=str(contract.get("source") or "runtime_harness"),
                )
                response_plan = build_runtime_result_response_plan(runtime_result, state)
                output_verdict = apply_output_check(response_plan, state)
                turn_id = _extract_turn_id(runtime_result, fallback_index=step_ordinal)
                turn_result = build_unified_turn_result(
                    state=state,
                    runtime_result=runtime_result,
                    request=request,
                    ingress=ingress,
                    response_plan=response_plan,
                    output_verdict=output_verdict,
                )
                egress = build_unified_egress(turn_result, state, bridge=bridge)
                snapshot = build_host_contract_snapshot(
                    request=request,
                    ingress=ingress,
                    turn_result=turn_result,
                    egress=egress,
                )
                observation_records.append(
                    build_runtime_observation_record(
                        session_id=session_id,
                        turn_id=turn_id,
                        user_input=str(text),
                        result=runtime_result,
                        state=state,
                        transport_source=str(contract.get("transport_source") or "runtime_harness"),
                        source=str(contract.get("source") or "runtime_harness"),
                        ingress_event_id=ingress_event_id,
                        ingress_created_at=ingress_created_at,
                        delivery_event_id=f"runtime_proximal_low_cue_ownership_delivery_{step_ordinal:03d}",
                        delivery_created_at=_now_iso(),
                    )
                )
                ingress_result = copy.deepcopy(dict(adapter.last_result or {}))
                step_log = _build_step_log(
                    step_id=f"ingress_{step_ordinal:03d}",
                    kind="ingress",
                    proto_self_result=ingress_result,
                    adapter=adapter,
                    experiment_id=experiment_id,
                )
                step_log["canonical_trace"] = _runner_canonical_trace(step_log)
                step_log["host_contract_snapshot"] = snapshot
                case_steps.append(step_log)

                for external_result_step in by_message_index.get(message_index, []):
                    step_ordinal += 1
                    state.ingress_context = _patch_ingress_context(
                        dict(state.ingress_context or {}),
                        experiment_id=experiment_id,
                        overrides=_build_runtime_overrides(
                            scenario=scenario,
                            segment_id=segment_id,
                            variant_id=variant_id,
                            experiment_id=experiment_id,
                            action_family=str(
                                (scenario.get("expected_scoring_surface") or {}).get("probe_key") or "unknown"
                            ),
                        ),
                        safety_overrides=_build_private_safety_overrides(scenario),
                    )
                    state.last_tool_result = dict(external_result_step.get("tool_result") or {})
                    runtime.proto_self_runtime.process_external_result(
                        session_id=session_id,
                        turn_id=turn_id,
                        step=step_ordinal,
                        state=state,
                    )
                    proto_self_result = copy.deepcopy(
                        dict(state.proto_self_context.get("external_result") or adapter.last_result or {})
                    )
                    step_log = _build_step_log(
                        step_id=f"tool_{step_ordinal:03d}",
                        kind="tool_result",
                        proto_self_result=proto_self_result,
                        adapter=adapter,
                        experiment_id=experiment_id,
                    )
                    step_log["canonical_trace"] = _runner_canonical_trace(step_log)
                    case_steps.append(step_log)

    return {
        "case_id": scenario_id,
        "family": str(scenario.get("family") or ""),
        "expected_scoring_surface": dict(scenario.get("expected_scoring_surface") or {}),
        "observation_records": observation_records,
        "steps": case_steps,
    }


def _build_case_compare(
    *,
    baseline_case: Dict[str, Any],
    candidate_case: Dict[str, Any],
) -> Dict[str, Any]:
    baseline_steps = [dict(step) for step in list(baseline_case.get("steps") or []) if step.get("host_contract_snapshot")]
    candidate_steps = [dict(step) for step in list(candidate_case.get("steps") or []) if step.get("host_contract_snapshot")]
    baseline_surface = _snapshot_compare_surface(
        dict((baseline_steps[-1] if baseline_steps else {}).get("host_contract_snapshot") or {})
    )
    candidate_surface = _snapshot_compare_surface(
        dict((candidate_steps[-1] if candidate_steps else {}).get("host_contract_snapshot") or {})
    )
    baseline_trace = _trace_surface(baseline_case)
    candidate_trace = _trace_surface(candidate_case)
    diffs = _collect_diffs(
        {"surface": baseline_surface, "trace_payload": baseline_trace},
        {"surface": candidate_surface, "trace_payload": candidate_trace},
    )
    return {
        "case_id": str(candidate_case.get("case_id") or baseline_case.get("case_id") or ""),
        "family": str(candidate_case.get("family") or baseline_case.get("family") or ""),
        "compare_surface": {
            "surface": {
                "baseline_a": baseline_surface,
                "candidate": candidate_surface,
            },
            "trace_payload": {
                "baseline_a": baseline_trace,
                "candidate": candidate_trace,
            },
        },
        "diffs": diffs,
        "delta_present": bool(diffs),
    }


def _has_host_pressure(surface: Dict[str, Any]) -> bool:
    proto = dict(surface.get("proto_self_context") or {})
    policy = dict(proto.get("policy_hint") or {})
    tendency = dict(surface.get("response_tendency_summary") or {})
    initiative = dict(proto.get("initiative_policy_hints") or {})
    if tendency.get("preferred_mode") in {"ask", "defer", "repair"}:
        return True
    if policy.get("ask_preferred") is True:
        return True
    if policy.get("guard_reason"):
        return True
    if initiative.get("initiative_priority"):
        return True
    return False


def _case_verdict(compare: Dict[str, Any]) -> Dict[str, Any]:
    family = str(compare.get("family") or "")
    surface = dict((compare.get("compare_surface") or {}).get("surface") or {})
    trace_payload = dict((compare.get("compare_surface") or {}).get("trace_payload") or {})
    candidate_surface = dict(surface.get("candidate") or {})
    candidate_proto = dict(candidate_surface.get("proto_self_context") or {})
    candidate_policy = dict(candidate_proto.get("policy_hint") or {})
    candidate_tendency = dict(candidate_surface.get("response_tendency_summary") or {})
    candidate_trace = dict(trace_payload.get("candidate") or {})
    diff_paths = [str(item.get("path") or "") for item in list(compare.get("diffs") or [])]
    pressure_visible = _has_host_pressure(candidate_surface)
    trace_handoff = bool(candidate_trace.get("handoff"))

    if family == "low_cue_persistence":
        status = "pass" if pressure_visible and trace_handoff else "hold"
        reason = (
            "low_cue_followup_preserves_bounded_pressure"
            if status == "pass"
            else "low_cue_followup_lost_bounded_pressure"
        )
    elif family == "ownership_ambiguity":
        source_or_agency_guard = any(
            candidate_policy.get(key)
            for key in ("mvs_source_guard", "mvs_agency_guard", "mvs_active_inference_guard")
        )
        status = "pass" if source_or_agency_guard else "hold"
        reason = (
            "ownership_or_source_guard_visible_on_host_surface"
            if status == "pass"
            else "bounded_pressure_visible_but_no_explicit_ownership_guard"
            if pressure_visible
            else "ownership_ambiguity_collapsed_without_host_pressure"
        )
    elif family == "agency_attribution_after_correction":
        corrective_keys_present = all(
            candidate_trace.get(key) not in (None, "", [])
            for key in ("predicted_outcome", "actual_outcome", "adjustment_applied", "next_guard")
        )
        repair_closure = candidate_trace.get("repair_closure") is True
        status = "pass" if corrective_keys_present and repair_closure else "hold"
        reason = (
            "corrective_trace_and_repair_closure_visible"
            if status == "pass"
            else "correction_visible_but_agency_attribution_not_closed"
        )
    else:
        status = "hold"
        reason = "unknown_family"

    return {
        "case_id": compare.get("case_id"),
        "family": family,
        "status": status,
        "reason": reason,
        "pressure_visible": pressure_visible,
        "trace_handoff": trace_handoff,
        "delta_present": bool(compare.get("delta_present")),
        "diff_paths": diff_paths,
        "candidate_surface_summary": {
            "reply_authority": candidate_surface.get("reply_authority"),
            "authority_source": candidate_surface.get("authority_source"),
            "delivery_kind": candidate_surface.get("delivery_kind"),
            "chat_cadence_mode": candidate_surface.get("chat_cadence_mode"),
            "response_tendency_summary": candidate_tendency,
            "initiative_policy_hints": candidate_proto.get("initiative_policy_hints") or {},
            "policy_hint": candidate_policy,
        },
        "candidate_trace_summary": {
            "presence": candidate_trace.get("presence"),
            "handoff": candidate_trace.get("handoff"),
            "predicted_outcome": candidate_trace.get("predicted_outcome"),
            "actual_outcome": candidate_trace.get("actual_outcome"),
            "adjustment_applied": candidate_trace.get("adjustment_applied"),
            "next_guard": candidate_trace.get("next_guard"),
            "repair_closure": candidate_trace.get("repair_closure"),
        },
    }


async def run_low_cue_ownership_runner(*, manifest_path: Path = MANIFEST_PATH) -> Dict[str, Any]:
    os.environ.setdefault(MVS_REPLAY_FEATURE_FLAG_ENV, "true")
    manifest = _load_json(manifest_path)
    errors = validate_manifest(manifest)
    if errors:
        raise RuntimeError("\n".join(errors))

    contract = dict(manifest.get("runner_contract") or {})
    scenarios = [dict(item) for item in list(manifest.get("scenarios") or [])]
    variant_ids = [str(contract.get("baseline_a_id") or ""), str(contract.get("candidate_id") or "")]
    results_by_variant: Dict[str, List[Dict[str, Any]]] = {variant_id: [] for variant_id in variant_ids}
    for scenario in scenarios:
        for variant_id in variant_ids:
            results_by_variant[variant_id].append(
                await _run_variant_for_scenario(
                    scenario=scenario,
                    contract=contract,
                    variant_id=variant_id,
                )
            )

    baseline_cases = {str(item.get("case_id") or ""): item for item in results_by_variant[variant_ids[0]]}
    candidate_cases = {str(item.get("case_id") or ""): item for item in results_by_variant[variant_ids[1]]}
    case_compares = [
        _build_case_compare(
            baseline_case=baseline_cases[scenario_id],
            candidate_case=candidate_cases[scenario_id],
        )
        for scenario_id in sorted(candidate_cases)
    ]
    case_verdicts = [_case_verdict(case) for case in case_compares]
    authority_drift_audit = _authority_drift_audit(contract)
    trace_contract_check = _runner_trace_contract_check(results_by_variant)
    host_surface_bounded_audit = _host_surface_bounded_audit(contract, results_by_variant)
    claim_ceiling_status = "pass"
    blocked_reasons: List[str] = []
    if authority_drift_audit.get("status") != "pass":
        blocked_reasons.append("authority_drift_failed")
    if trace_contract_check.get("status") != "pass":
        blocked_reasons.append("trace_contract_failed")
    if host_surface_bounded_audit.get("status") != "pass":
        blocked_reasons.append("host_surface_bounded_failed")
    if claim_ceiling_status != "pass":
        blocked_reasons.append("claim_ceiling_failed")
    invalid_case_statuses = [
        verdict["case_id"]
        for verdict in case_verdicts
        if verdict.get("status") not in {"pass", "hold"}
    ]
    if invalid_case_statuses:
        blocked_reasons.append("non_judgeable_family_status")

    aggregate = {
        "execution_status": "pass"
        if (
            authority_drift_audit.get("status") == "pass"
            and trace_contract_check.get("status") == "pass"
            and host_surface_bounded_audit.get("status") == "pass"
            and len(case_verdicts) == 3
            and not invalid_case_statuses
        )
        else "hold",
        "low_cue_persistence_status": next(
            verdict["status"] for verdict in case_verdicts if verdict["family"] == "low_cue_persistence"
        ),
        "ownership_boundary_status": next(
            verdict["status"] for verdict in case_verdicts if verdict["family"] == "ownership_ambiguity"
        ),
        "agency_attribution_status": next(
            verdict["status"] for verdict in case_verdicts if verdict["family"] == "agency_attribution_after_correction"
        ),
        "claim_ceiling_status": claim_ceiling_status,
        "runner_decision": "pass"
        if (
            authority_drift_audit.get("status") == "pass"
            and trace_contract_check.get("status") == "pass"
            and host_surface_bounded_audit.get("status") == "pass"
            and claim_ceiling_status == "pass"
            and not invalid_case_statuses
        )
        else "hold",
        "reviewer_gate_ready": (
            authority_drift_audit.get("status") == "pass"
            and trace_contract_check.get("status") == "pass"
            and host_surface_bounded_audit.get("status") == "pass"
            and claim_ceiling_status == "pass"
            and not invalid_case_statuses
        ),
        "blocked_reasons": sorted(set(blocked_reasons)),
        "family_pass_count": sum(1 for verdict in case_verdicts if verdict.get("status") == "pass"),
        "family_hold_count": sum(1 for verdict in case_verdicts if verdict.get("status") == "hold"),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "manifest_path": str(manifest_path),
        "source": "runtime_proximal_low_cue_ownership_runner",
        "claim_ceiling": "bounded_runner_only",
        "runner_contract": contract,
        "summary": {
            "scenario_count": len(case_verdicts),
            "family_counts": {family: 1 for family in sorted(ALLOWED_FAMILIES)},
            "variant_ids": variant_ids,
        },
        "authority_drift_audit": authority_drift_audit,
        "trace_contract_check": trace_contract_check,
        "host_surface_bounded_audit": host_surface_bounded_audit,
        "results_by_variant": results_by_variant,
        "case_compares": case_compares,
        "case_verdicts": case_verdicts,
        "aggregate": aggregate,
    }


def _render_markdown(report: Dict[str, Any]) -> str:
    aggregate = dict(report.get("aggregate") or {})
    lines = [
        "# Runtime-Proximal Low-Cue Ownership Runner",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- source: `{report.get('source')}`",
        f"- claim_ceiling: `{report.get('claim_ceiling')}`",
        f"- execution_status: `{aggregate.get('execution_status')}`",
        f"- runner_decision: `{aggregate.get('runner_decision')}`",
        f"- low_cue_persistence_status: `{aggregate.get('low_cue_persistence_status')}`",
        f"- ownership_boundary_status: `{aggregate.get('ownership_boundary_status')}`",
        f"- agency_attribution_status: `{aggregate.get('agency_attribution_status')}`",
        f"- claim_ceiling_status: `{aggregate.get('claim_ceiling_status')}`",
        f"- reviewer_gate_ready: `{aggregate.get('reviewer_gate_ready')}`",
        "",
        "## Case verdicts",
        "",
    ]
    for case in list(report.get("case_verdicts") or []):
        lines.append(f"### `{case.get('case_id')}` [{case.get('family')}]")
        lines.append("")
        lines.append(f"- status: `{case.get('status')}`")
        lines.append(f"- reason: `{case.get('reason')}`")
        lines.append(f"- pressure_visible: `{case.get('pressure_visible')}`")
        lines.append(f"- trace_handoff: `{case.get('trace_handoff')}`")
        diff_paths = list(case.get("diff_paths") or [])
        if diff_paths:
            lines.append("- diff_paths:")
            for path in diff_paths:
                lines.append(f"  - `{path}`")
        else:
            lines.append("- diff_paths: none")
        lines.append("")
    blocked = list(aggregate.get("blocked_reasons") or [])
    lines.extend(["## Blocked reasons", ""])
    if blocked:
        lines.extend([f"- `{item}`" for item in blocked])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Claim Ceiling",
            "",
            "- This runner proves bounded runtime-proximal family verdicts only.",
            "- It does not prove runtime efficacy, live benefit, or AI self-awareness achieved.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = asyncio.run(run_low_cue_ownership_runner(manifest_path=args.manifest))
    _write_json(args.output_json, report)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps(report.get("aggregate") or {}, ensure_ascii=False))
    return 0 if dict(report.get("aggregate") or {}).get("execution_status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
