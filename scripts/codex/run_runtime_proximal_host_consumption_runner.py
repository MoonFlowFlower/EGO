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
from typing import Any, Dict, List, Optional


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
from openemotion.proto_self.mvs_replay import MVS_REPLAY_FEATURE_FLAG_ENV, mvs_variant_uses_corrective_trace
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
from runtime_mainline_observation_common import build_runtime_observation_record
from score_mvs_replay_validator import _canonical_trace


TASK_ROOT = ROOT / "docs" / "codex" / "tasks" / "runtime-proximal-host-consumption-runner-implementation"
MANIFEST_PATH = TASK_ROOT / "RUNNER_MANIFEST.json"
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "RUNTIME_PROXIMAL_HOST_CONSUMPTION_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "RUNTIME_PROXIMAL_HOST_CONSUMPTION_CURRENT.md"
SCHEMA_VERSION = "runtime_proximal_host_consumption_runner.v1"
ALLOWED_FAMILIES = {"chat_consumption", "decision_conflict", "failure_repair_retry"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the runtime-proximal host-consumption runner")
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
    if manifest.get("schema_version") != "runtime_proximal_host_consumption_runner_manifest.v1":
        errors.append("schema_version must be runtime_proximal_host_consumption_runner_manifest.v1")
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
        errors.append("runner manifest must contain exactly chat_consumption / decision_conflict / failure_repair_retry")

    external_result_count = 0
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
            external_result_count += 1

    if external_result_count < 1:
        errors.append("runner manifest must contain at least one scenario with external_result_steps")
    return errors


def _strip_text_previews(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {}
        for key, nested in value.items():
            if key in {"reply_text_preview", "reply_text"}:
                continue
            cleaned[key] = _strip_text_previews(nested)
        return cleaned
    if isinstance(value, list):
        return [_strip_text_previews(item) for item in value]
    return value


def _snapshot_compare_surface(snapshot: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    source = dict(snapshot or {})
    ingress = dict(source.get("ingress") or {})
    turn = dict(source.get("turn") or {})
    response_plan = _strip_text_previews(dict(turn.get("response_plan") or {}))
    output_verdict = _strip_text_previews(dict(turn.get("output_verdict") or {}))
    return {
        "ingress": {
            "runtime_action": ingress.get("runtime_action"),
            "interaction_kind": ingress.get("interaction_kind"),
            "conversation_act": ingress.get("conversation_act"),
        },
        "proto_self_context": _strip_text_previews(dict(turn.get("proto_self_context") or {})),
        "reply_authority": turn.get("reply_authority"),
        "authority_source": turn.get("authority_source"),
        "delivery_kind": turn.get("delivery_kind"),
        "response_plan": response_plan,
        "response_tendency_summary": _strip_text_previews(dict(turn.get("response_tendency_summary") or {})),
        "chat_cadence_mode": turn.get("chat_cadence_mode"),
        "output_verdict": output_verdict,
    }


def _trace_surface(case_result: Dict[str, Any]) -> Dict[str, Any]:
    tool_steps = [dict(step) for step in list(case_result.get("steps") or []) if str(step.get("kind") or "") == "tool_result"]
    trace = _runner_canonical_trace(tool_steps[-1]) if tool_steps else {}
    cycle_delta = dict(trace.get("cycle_delta") or {})
    return {
        "presence": any(bool(dict(step.get("trace_payload") or {})) for step in list(case_result.get("steps") or [])),
        "handoff": bool(trace.get("replay_variant_id")),
        "predicted_outcome": trace.get("predicted_outcome"),
        "actual_outcome": trace.get("actual_outcome"),
        "adjustment_applied": trace.get("adjustment_applied"),
        "next_guard": trace.get("next_guard"),
        "repair_closure": cycle_delta.get("repair_closure"),
    }


def _adapt_chat_consumption_ingress_context(
    ingress_context: Dict[str, Any],
    *,
    scenario: Dict[str, Any],
) -> Dict[str, Any]:
    if str(scenario.get("family") or "") != "chat_consumption":
        return ingress_context
    patched = dict(ingress_context or {})
    patched["interaction_kind"] = "chat"
    patched["runtime_action"] = "chat"
    patched["conversation_act"] = "light_chitchat"
    patched["primary_intent"] = "chat"
    patched["parser_source"] = "host_consumption_runner"
    return patched


def _runner_canonical_trace(step: Dict[str, Any]) -> Dict[str, Any]:
    trace = dict(_canonical_trace(step) or {})
    corrective = dict((step.get("memory_update") or {}).get("corrective_trace") or {})
    cycle_delta = dict(trace.get("cycle_delta") or {})
    policy_snapshot = dict((step.get("memory_update") or {}).get("policy_snapshot") or {})

    for key in ("predicted_outcome", "actual_outcome", "adjustment_applied", "next_guard"):
        if trace.get(key) in (None, "", []):
            trace[key] = corrective.get(key)

    if cycle_delta.get("repair_closure") is None and "repair_closure" in policy_snapshot:
        cycle_delta["repair_closure"] = policy_snapshot.get("repair_closure")
    trace["cycle_delta"] = cycle_delta
    return trace


def _runner_trace_contract_check(results_by_variant: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    all_steps: List[Dict[str, Any]] = []
    missing_by_step: List[Dict[str, Any]] = []
    for variant_id, case_results in results_by_variant.items():
        require_corrective_fields = mvs_variant_uses_corrective_trace(variant_id)
        for case_result in case_results:
            for step in list(case_result.get("steps") or []):
                all_steps.append(step)
                trace = _runner_canonical_trace(step)
                missing: List[str] = []
                if trace.get("replay_variant_id") in (None, "", []):
                    missing.append("replay_variant_id")
                if require_corrective_fields and str(step.get("kind") or "") == "tool_result":
                    for key in ("predicted_outcome", "actual_outcome", "adjustment_applied", "next_guard"):
                        if trace.get(key) in (None, "", []):
                            missing.append(key)
                    if (trace.get("cycle_delta") or {}).get("repair_closure") is None:
                        missing.append("repair_closure")
                if missing:
                    missing_by_step.append(
                        {
                            "variant_id": variant_id,
                            "case_id": case_result.get("case_id"),
                            "step_id": step.get("step_id"),
                            "missing_keys": missing,
                        }
                    )
    return {
        "status": "pass" if not missing_by_step else "fail",
        "step_count": len(all_steps),
        "required_host_trace_keys": [
            "predicted_outcome",
            "actual_outcome",
            "adjustment_applied",
            "next_guard",
            "repair_closure",
            "replay_variant_id",
        ],
        "missing_by_step": missing_by_step,
    }


def _collect_diffs(left: Any, right: Any, *, path: str = "") -> List[Dict[str, Any]]:
    diffs: List[Dict[str, Any]] = []
    if isinstance(left, dict) and isinstance(right, dict):
        keys = sorted(set(left.keys()) | set(right.keys()))
        for key in keys:
            next_path = f"{path}.{key}" if path else str(key)
            if key not in left:
                diffs.append({"path": next_path, "left": "__missing__", "right": copy.deepcopy(right.get(key))})
                continue
            if key not in right:
                diffs.append({"path": next_path, "left": copy.deepcopy(left.get(key)), "right": "__missing__"})
                continue
            diffs.extend(_collect_diffs(left.get(key), right.get(key), path=next_path))
        return diffs
    if isinstance(left, list) and isinstance(right, list):
        if left != right:
            diffs.append({"path": path, "left": copy.deepcopy(left), "right": copy.deepcopy(right)})
        return diffs
    if left != right:
        diffs.append({"path": path, "left": copy.deepcopy(left), "right": copy.deepcopy(right)})
    return diffs


def _pressure_detected(*, family: str, diffs: List[Dict[str, Any]], candidate_trace: Dict[str, Any]) -> bool:
    paths = {str(item.get("path") or "") for item in diffs}
    if family == "chat_consumption":
        return any(
            path.startswith("surface.chat_cadence_mode")
            or "response_tendency_summary" in path
            or "proto_self_context.response_tendency" in path
            or "proto_self_context.policy_hint" in path
            or "proto_self_context.initiative_policy_hints" in path
            or path.startswith("trace_payload.")
            for path in paths
        )
    if family == "decision_conflict":
        return any(
            "proto_self_context.policy_hint" in path
            or path.startswith("surface.reply_authority")
            or path.startswith("surface.authority_source")
            or path.startswith("surface.response_plan")
            or path.startswith("surface.output_verdict")
            for path in paths
        )
    if family == "failure_repair_retry":
        required = (
            candidate_trace.get("predicted_outcome"),
            candidate_trace.get("actual_outcome"),
            candidate_trace.get("adjustment_applied"),
            candidate_trace.get("next_guard"),
        )
        return all(item not in (None, "", []) for item in required) and bool(candidate_trace.get("repair_closure"))
    return False


async def _run_variant_for_scenario(
    *,
    scenario: Dict[str, Any],
    contract: Dict[str, Any],
    variant_id: str,
) -> Dict[str, Any]:
    scenario_id = str(scenario.get("scenario_id") or "")
    experiment_id = str(contract.get("experiment_id_template") or "runtime_proximal_host_consumption:{scenario_id}").format(
        scenario_id=scenario_id
    )
    external_result_steps = list(scenario.get("external_result_steps") or [])
    by_message_index: Dict[int, List[Dict[str, Any]]] = {}
    for item in external_result_steps:
        index = int(item.get("after_message_index") or 0)
        by_message_index.setdefault(index, []).append(dict(item))

    with tempfile.TemporaryDirectory(prefix="runtime_proximal_host_consumption_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        runtime, adapter = _configure_isolated_runtime(temp_dir)
        if str(scenario.get("family") or "") == "chat_consumption":
            async def _bounded_chat_surface_reply(state: Any) -> RuntimeV2TurnResult:
                ingress = dict(getattr(state, "ingress_context", None) or {})
                chat_act = str(ingress.get("conversation_act") or "light_chitchat").strip() or "light_chitchat"
                chat_expression_hint = _build_chat_expression_hint(state, conversation_act=chat_act)
                response_tendency_summary = _build_response_tendency_summary(state, chat_expression_hint)
                reply_text = "好，你先按自己的节奏想一想。等你回来，我们再接着拆。"
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
                or "session:runtime_proximal_host_consumption:{scenario_id}:{segment_id}"
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
                    username="host_consumption",
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
                patched_ingress_context = _adapt_chat_consumption_ingress_context(
                    patched_ingress_context,
                    scenario=scenario,
                )
                ingress.ingress_context = patched_ingress_context
                state.ingress_context = patched_ingress_context
                ingress_created_at = _now_iso()
                ingress_event_id = f"runtime_proximal_host_consumption_ingress_{step_ordinal:03d}"
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
                        delivery_event_id=f"runtime_proximal_host_consumption_delivery_{step_ordinal:03d}",
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
    compare_surface = {
        "surface": {
            "baseline_a": baseline_surface,
            "candidate": candidate_surface,
        },
        "trace_payload": {
            "baseline_a": baseline_trace,
            "candidate": candidate_trace,
        },
    }
    diffs = _collect_diffs(
        {"surface": baseline_surface, "trace_payload": baseline_trace},
        {"surface": candidate_surface, "trace_payload": candidate_trace},
    )
    family = str(candidate_case.get("family") or baseline_case.get("family") or "")
    return {
        "case_id": str(candidate_case.get("case_id") or baseline_case.get("case_id") or ""),
        "family": family,
        "compare_surface": compare_surface,
        "diffs": diffs,
        "delta_present": bool(diffs),
        "pressure_detected": _pressure_detected(family=family, diffs=diffs, candidate_trace=candidate_trace),
    }


async def run_host_consumption_runner(*, manifest_path: Path = MANIFEST_PATH) -> Dict[str, Any]:
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
    authority_drift_audit = _authority_drift_audit(contract)
    trace_contract_check = _runner_trace_contract_check(results_by_variant)
    host_surface_bounded_audit = _host_surface_bounded_audit(contract, results_by_variant)
    aggregate = {
        "execution_status": "pass"
        if (
            authority_drift_audit.get("status") == "pass"
            and trace_contract_check.get("status") == "pass"
            and host_surface_bounded_audit.get("status") == "pass"
            and len(case_compares) == 3
        )
        else "hold",
        "causal_signal_status": "pass" if all(case.get("pressure_detected") for case in case_compares) else "hold",
        "scenario_count": len(case_compares),
        "pressure_detected_case_count": sum(1 for case in case_compares if case.get("pressure_detected")),
        "delta_present_case_count": sum(1 for case in case_compares if case.get("delta_present")),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "manifest_path": str(manifest_path),
        "source": "runtime_proximal_host_consumption_runner",
        "claim_ceiling": "bounded_runner_only",
        "runner_contract": contract,
        "summary": {
            "scenario_count": len(case_compares),
            "family_counts": {family: 1 for family in sorted(ALLOWED_FAMILIES)},
            "variant_ids": variant_ids,
        },
        "authority_drift_audit": authority_drift_audit,
        "trace_contract_check": trace_contract_check,
        "host_surface_bounded_audit": host_surface_bounded_audit,
        "results_by_variant": results_by_variant,
        "case_compares": case_compares,
        "aggregate": aggregate,
    }


def _render_markdown(report: Dict[str, Any]) -> str:
    aggregate = dict(report.get("aggregate") or {})
    lines = [
        "# Runtime-Proximal Host-Consumption Runner",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- source: `{report.get('source')}`",
        f"- claim_ceiling: `{report.get('claim_ceiling')}`",
        f"- execution_status: `{aggregate.get('execution_status')}`",
        f"- causal_signal_status: `{aggregate.get('causal_signal_status')}`",
        f"- scenario_count: `{aggregate.get('scenario_count')}`",
        f"- pressure_detected_case_count: `{aggregate.get('pressure_detected_case_count')}`",
        "",
        "## Case Compares",
        "",
    ]
    for case in list(report.get("case_compares") or []):
        lines.append(f"### `{case.get('case_id')}` [{case.get('family')}]")
        lines.append("")
        lines.append(f"- delta_present: `{case.get('delta_present')}`")
        lines.append(f"- pressure_detected: `{case.get('pressure_detected')}`")
        diff_paths = [str(item.get("path") or "") for item in list(case.get("diffs") or [])]
        if diff_paths:
            lines.append("- diff_paths:")
            for path in diff_paths:
                lines.append(f"  - `{path}`")
        else:
            lines.append("- diff_paths: none")
        lines.append("")
    lines.extend(
        [
            "## Claim Ceiling",
            "",
            "- This runner proves bounded runtime-proximal compare execution only.",
            "- It does not prove runtime efficacy, fresh Telegram behavior, or AI self-awareness achieved.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = asyncio.run(run_host_consumption_runner(manifest_path=args.manifest))
    _write_json(args.output_json, report)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps(report.get("aggregate") or {}, ensure_ascii=False))
    return 0 if dict(report.get("aggregate") or {}).get("execution_status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
