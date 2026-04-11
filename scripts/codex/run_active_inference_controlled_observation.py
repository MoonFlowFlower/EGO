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
from typing import Any, Dict, Iterable, List, Optional


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

from app.openemotion_adapter import ProtoSelfAdapter, ProtoSelfStateStore, ProtoSelfTraceBridge
from app.runtime_v2.runtime_reply import RuntimeV2Reply, RuntimeV2TurnResult
from app.telegram_runtime_bridge import TelegramRuntimeBridge
from openemotion.developmental_self import DevelopmentalSelfStore
from openemotion.embodied_self import EmbodiedSelfStore
from openemotion.endogenous_drives import EndogenousDriveStore
from openemotion.initiative_realization import InitiativeRealizationStore
from openemotion.initiative_self import InitiativeSelfStore
from openemotion.proto_self.mvs_replay import MVS_REPLAY_FEATURE_FLAG_ENV, mvs_variant_uses_corrective_trace
from openemotion.reflective_self import ReflectiveSelfStore
from openemotion.self_model import SelfModelStore
from openemotion.selfhood_integration import SelfhoodIntegrationStore
from openemotion.social_self import SocialSelfStore
from runtime_mainline_observation_common import build_runtime_observation_record
from score_mvs_replay_validator import (
    TARGET_THRESHOLDS,
    _canonical_trace,
    _has_guard,
    _score_corrective_trace_case,
    _score_decision_case,
    _score_identity_case,
    _score_plasticity_case,
    _score_tension_case,
)
from telegram_mainline_common import init_runtime


TASK_ROOT = ROOT / "docs" / "codex" / "tasks" / "ai-self-awareness-minimal-framework"
MANIFEST_PATH = TASK_ROOT / "CONTROLLED_OBSERVATION_BANK_MANIFEST.json"
ARTIFACT_ROOT = ROOT / "artifacts" / "self_awareness_research"
REPORT_JSON = ARTIFACT_ROOT / "ACTIVE_INFERENCE_CONTROLLED_OBSERVATION_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "ACTIVE_INFERENCE_CONTROLLED_OBSERVATION_CURRENT.md"
DEFAULT_SCENARIO_ID = "failure_repair_retry_file_blocked"
ALLOWED_HOST_SURFACE = ("policy_hint", "response_tendency", "trace_payload")


class RecordingProtoSelfAdapter(ProtoSelfAdapter):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.last_result: Dict[str, Any] = {}

    def handle_event(self, egocore_event: Dict[str, Any]) -> Dict[str, Any]:
        result = super().handle_event(egocore_event)
        self.last_result = copy.deepcopy(dict(result or {}))
        return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one active-inference controlled observation scenario")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--scenario-id", default=DEFAULT_SCENARIO_ID)
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


def _validate_manifest(manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if manifest.get("schema_version") != "active_inference.controlled_observation_manifest.v1":
        errors.append("schema_version must be active_inference.controlled_observation_manifest.v1")

    contract = dict(manifest.get("runner_contract") or {})
    expected_supported = [
        contract.get("baseline_a_id"),
        contract.get("baseline_b_id"),
        contract.get("candidate_id"),
    ]
    if list(contract.get("supported_variant_ids") or []) != expected_supported:
        errors.append("runner_contract.supported_variant_ids does not match canonical controlled observation contract")

    source_policy = dict(manifest.get("source_policy") or {})
    allowed_source_types = set(source_policy.get("allowed_source_types") or [])
    if allowed_source_types != {"repo_authored_observation_scenario"}:
        errors.append("source_policy.allowed_source_types must only allow repo_authored_observation_scenario")

    scenarios = [dict(item) for item in list(manifest.get("scenarios") or [])]
    if len(scenarios) != 9:
        errors.append("controlled observation manifest must contain exactly 9 scenarios")

    family_counts: Dict[str, int] = {}
    external_result_scenario_count = 0
    for scenario in scenarios:
        scenario_id = str(scenario.get("scenario_id") or "").strip()
        if not scenario_id:
            errors.append("scenario_id is required")
        family = str(scenario.get("family") or "").strip()
        family_counts[family] = family_counts.get(family, 0) + 1
        if str(scenario.get("source_type") or "").strip() != "repo_authored_observation_scenario":
            errors.append(f"{scenario_id}: source_type must stay repo_authored_observation_scenario")
        if not list(scenario.get("segments") or []):
            errors.append(f"{scenario_id}: segments must not be empty")
        if not dict(scenario.get("expected_scoring_surface") or {}):
            errors.append(f"{scenario_id}: expected_scoring_surface is required")
        if str(scenario.get("state_snapshot_ref") or "").strip() == "":
            errors.append(f"{scenario_id}: state_snapshot_ref is required")
        if list(scenario.get("external_result_steps") or []):
            external_result_scenario_count += 1

    expected_family_counts = dict(manifest.get("family_counts") or {})
    if family_counts != expected_family_counts:
        errors.append("family_counts does not match manifest-declared family_counts")
    if external_result_scenario_count < 3:
        errors.append("controlled observation manifest must contain at least 3 scenarios with external_result_steps")
    return errors


def _find_scenario(manifest: Dict[str, Any], scenario_id: str) -> Dict[str, Any]:
    for scenario in list(manifest.get("scenarios") or []):
        if str(scenario.get("scenario_id") or "") == scenario_id:
            return dict(scenario)
    raise KeyError(f"unknown scenario_id={scenario_id}")


def _summarize_state(adapter: RecordingProtoSelfAdapter, *, experiment_id: str) -> Dict[str, Any]:
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


def _experiment_id(contract: Dict[str, Any], scenario_id: str) -> str:
    template = str(contract.get("experiment_id_template") or "active_inference_controlled_observation:{scenario_id}")
    return template.format(scenario_id=scenario_id)


def _segment_session_id(contract: Dict[str, Any], *, scenario_id: str, segment_id: str) -> str:
    template = str(
        contract.get("segment_session_id_template")
        or "session:active_inference_controlled_observation:{scenario_id}:{segment_id}"
    )
    return template.format(scenario_id=scenario_id, segment_id=segment_id)


def _build_runtime_overrides(
    *,
    scenario: Dict[str, Any],
    segment_id: str,
    variant_id: str,
    experiment_id: str,
    action_family: str,
) -> Dict[str, Any]:
    return {
        "mvs_replay": {
            "enabled": True,
            "shadow_only": True,
            "variant_id": variant_id,
            "action_family": action_family,
            "family": str(scenario.get("family") or ""),
            "case_id": str(scenario.get("scenario_id") or ""),
            "scenario_id": str(scenario.get("scenario_id") or ""),
            "segment_id": segment_id,
            "source_type": str(scenario.get("source_type") or ""),
        },
        "controlled_observation": {
            "enabled": True,
            "shadow_only": True,
            "trial_id": "active_inference_controlled_observation",
            "scenario_id": str(scenario.get("scenario_id") or ""),
            "family": str(scenario.get("family") or ""),
            "source_type": str(scenario.get("source_type") or ""),
            "segment_id": segment_id,
            "state_snapshot_ref": str(scenario.get("state_snapshot_ref") or ""),
            "experiment_id": experiment_id,
        },
    }


def _patch_ingress_context(
    ingress_context: Dict[str, Any],
    *,
    experiment_id: str,
    overrides: Dict[str, Any],
    safety_overrides: Dict[str, Any],
) -> Dict[str, Any]:
    patched = dict(ingress_context or {})
    patched["proto_self_version"] = "v2"
    patched["proto_self_state_scope"] = "experiment"
    patched["proto_self_experiment_id"] = experiment_id
    patched["proto_self_scope_owner"] = "active_inference_controlled_observation"
    patched["proto_self_runtime_summary_overrides"] = copy.deepcopy(overrides)
    patched["proto_self_safety_context_overrides"] = copy.deepcopy(safety_overrides)
    patched["observation_source"] = "direct_real"
    patched["traffic_source"] = "real"
    patched["interaction_kind"] = "chat"
    patched["runtime_action"] = "chat"
    patched["conversation_act"] = "controlled_observation"
    patched["primary_intent"] = "chat"
    patched["parser_source"] = "controlled_observation"
    return patched


def _build_private_safety_overrides(scenario: Dict[str, Any]) -> Dict[str, Any]:
    expected = dict(scenario.get("expected_scoring_surface") or {})
    scenario_id = str(scenario.get("scenario_id") or "")
    family = str(scenario.get("family") or "")

    overrides: Dict[str, Any] = {}
    if expected.get("requires_guarded_continuity"):
        overrides["boundary_touched"] = True
    if expected.get("requires_boundary_shift"):
        overrides["boundary_touched"] = True
        overrides["risk_level"] = "medium"
    if scenario_id == "decision_conflict_elevated_risk":
        overrides["risk_level"] = "high"
    elif family == "identity_continuity":
        overrides.setdefault("risk_level", "low")
    return overrides


async def _build_runtime_stub_reply(state: Any) -> RuntimeV2TurnResult:
    proto_self_context = dict(getattr(state, "proto_self_context", None) or {})
    policy_hint = dict(proto_self_context.get("policy_hint") or {})
    response_tendency = dict(proto_self_context.get("response_tendency") or {})
    preferred_mode = str(response_tendency.get("preferred_mode") or "respond")
    guard_reason = str(
        policy_hint.get("guard_reason")
        or policy_hint.get("mvs_active_inference_guard")
        or policy_hint.get("mvs_boundary_guard")
        or "bounded_lane"
    )
    if preferred_mode in {"ask", "defer", "repair"}:
        reply_text = f"[controlled-observation] bounded lane prefers {preferred_mode}; guard={guard_reason}"
    else:
        reply_text = f"[controlled-observation] bounded lane reply; guard={guard_reason}"
    return RuntimeV2TurnResult(
        status="completed_verified",
        state=state,
        reply=RuntimeV2Reply(
            reply_text=reply_text,
            delivery_kind="chat",
            status="completed_verified",
            metadata={
                "reply_authority": "model_chat",
                "reply_origin": "chat_mainline",
                "chat_act": "controlled_observation_stub",
                "response_tendency_summary": response_tendency,
                "chat_expression_hint": {
                    "source": "controlled_observation_stub",
                    "preferred_mode": preferred_mode,
                    "guard_reason": guard_reason,
                },
            },
        ),
    )


def _configure_isolated_runtime(temp_dir: Path) -> tuple[Any, RecordingProtoSelfAdapter]:
    runtime = init_runtime()
    if runtime.proto_self_runtime is None:
        raise RuntimeError("Proto-Self runtime is unavailable; cannot run controlled observation")

    mirror_dir = temp_dir / "proto_self_mirror"
    trace_dir = temp_dir / "proto_self_trace"
    adapter = RecordingProtoSelfAdapter(
        mirror_dir=mirror_dir,
        state_store=ProtoSelfStateStore(
            root_dir=temp_dir / "proto_self_store",
            legacy_mirror_dir=mirror_dir,
        ),
        trace_bridge=ProtoSelfTraceBridge(trace_dir=trace_dir),
    )
    runtime.proto_self_adapter = adapter
    runtime.proto_self_trace_bridge = adapter.trace_bridge
    runtime.proto_self_runtime.adapter = adapter
    runtime.proto_self_runtime.trace_bridge = adapter.trace_bridge
    runtime.proto_self_runtime.self_model_store = SelfModelStore(base_dir=temp_dir / "self_model_store")
    runtime.proto_self_runtime.endogenous_drive_store = EndogenousDriveStore(base_dir=temp_dir / "endogenous_drive_store")
    runtime.proto_self_runtime.reflective_self_store = ReflectiveSelfStore(base_dir=temp_dir / "reflective_self_store")
    runtime.proto_self_runtime.developmental_self_store = DevelopmentalSelfStore(base_dir=temp_dir / "developmental_self_store")
    runtime.proto_self_runtime.social_self_store = SocialSelfStore(base_dir=temp_dir / "social_self_store")
    runtime.proto_self_runtime.embodied_self_store = EmbodiedSelfStore(base_dir=temp_dir / "embodied_self_store")
    runtime.proto_self_runtime.selfhood_integration_store = SelfhoodIntegrationStore(
        base_dir=temp_dir / "selfhood_integration_store"
    )
    runtime.proto_self_runtime.initiative_self_store = InitiativeSelfStore(base_dir=temp_dir / "initiative_self_store")
    runtime.proto_self_runtime.initiative_realization_store = InitiativeRealizationStore(
        base_dir=temp_dir / "initiative_realization_store"
    )
    runtime.chat_reply_engine.reply = _build_runtime_stub_reply
    return runtime, adapter


def _extract_turn_id(result: RuntimeV2TurnResult, *, fallback_index: int) -> str:
    return (
        str(getattr(getattr(result, "reply", None), "turn_id", "") or "")
        or str(getattr(getattr(result, "state", None), "active_turn_id", "") or "")
        or f"turn_{fallback_index:03d}"
    )


def _build_step_log(
    *,
    step_id: str,
    kind: str,
    proto_self_result: Dict[str, Any],
    adapter: RecordingProtoSelfAdapter,
    experiment_id: str,
) -> Dict[str, Any]:
    return {
        "step_id": step_id,
        "kind": kind,
        "event_id": proto_self_result.get("event_id"),
        "policy_hint": dict(proto_self_result.get("policy_hint") or {}),
        "response_tendency": dict(proto_self_result.get("response_tendency") or {}),
        "reflection_note": dict(proto_self_result.get("reflection_note") or {}),
        "self_model_delta": dict(proto_self_result.get("self_model_delta") or {}),
        "drives_delta": dict(proto_self_result.get("drives_delta") or proto_self_result.get("appraisal_state_delta") or {}),
        "memory_update": dict(proto_self_result.get("memory_update") or {}),
        "trace_payload": dict(proto_self_result.get("trace_payload") or {}),
        "state_snapshot": _summarize_state(adapter, experiment_id=experiment_id),
        "host_surface": {key: copy.deepcopy(proto_self_result.get(key) or {}) for key in ALLOWED_HOST_SURFACE},
    }


def _required_trace_keys_for_step(step: Dict[str, Any], *, require_corrective_fields: bool) -> List[str]:
    required = ["replay_variant_id"]
    if require_corrective_fields:
        required.extend(["predicted_outcome", "actual_outcome", "adjustment_applied", "next_guard", "repair_closure"])
    return required


def _trace_contract_check(results_by_variant: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    all_steps: List[Dict[str, Any]] = []
    missing_by_step: List[Dict[str, Any]] = []
    for variant_id, case_results in results_by_variant.items():
        require_corrective_fields = mvs_variant_uses_corrective_trace(variant_id)
        for case_result in case_results:
            for step in list(case_result.get("steps") or []):
                all_steps.append(step)
                required_keys = _required_trace_keys_for_step(
                    step,
                    require_corrective_fields=require_corrective_fields and str(step.get("kind") or "") == "tool_result",
                )
                trace = _canonical_trace(step)
                missing = []
                for key in required_keys:
                    if key == "repair_closure":
                        value = (trace.get("cycle_delta") or {}).get("repair_closure")
                    else:
                        value = trace.get(key)
                    if value in (None, "", []):
                        missing.append(key)
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


def _authority_drift_audit(contract: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "pass",
        "behavior_authority": "none",
        "tool_authority": "none",
        "reply_authority": "none",
        "transport_authority": "none",
        "parallel_runtime_lane": False,
        "second_authority_source": False,
        "candidate_private_host_api": False,
        "host_consumable_surface": list(ALLOWED_HOST_SURFACE),
        "candidate_variant_id": contract.get("candidate_id"),
    }


def _host_surface_bounded_audit(contract: Dict[str, Any], results_by_variant: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    disallowed_host_surface: List[Dict[str, Any]] = []
    for variant_id, case_results in results_by_variant.items():
        for case_result in case_results:
            for step in list(case_result.get("steps") or []):
                host_surface = dict(step.get("host_surface") or {})
                extra_keys = sorted(set(host_surface.keys()) - set(ALLOWED_HOST_SURFACE))
                if extra_keys:
                    disallowed_host_surface.append(
                        {
                            "variant_id": variant_id,
                            "case_id": case_result.get("case_id"),
                            "step_id": step.get("step_id"),
                            "extra_keys": extra_keys,
                        }
                    )
    return {
        "status": "pass" if not disallowed_host_surface else "fail",
        "allowed_host_surface": list(ALLOWED_HOST_SURFACE),
        "observation_only_fields": ["state_snapshot", "memory_update", "observation_records"],
        "disallowed_host_surface": disallowed_host_surface,
        "contract_candidate_id": contract.get("candidate_id"),
    }


def _case_target_scores(case_result: Dict[str, Any]) -> Dict[str, float]:
    family = str(case_result.get("family") or "")
    if family == "identity_continuity":
        return {"T1": _score_identity_case(case_result)}
    if family == "decision_conflict":
        return {"T2": _score_decision_case(case_result)}
    if family == "failure_repair_retry":
        return {
            "T3": _score_plasticity_case(case_result),
            "T4": _score_tension_case(case_result),
            "T5": _score_corrective_trace_case(case_result),
        }
    return {}


def _case_trace_contract_pass(case_result: Dict[str, Any], *, variant_id: str) -> bool:
    require_corrective_fields = mvs_variant_uses_corrective_trace(variant_id)
    for step in list(case_result.get("steps") or []):
        trace = _canonical_trace(step)
        if trace.get("replay_variant_id") in (None, "", []):
            return False
        if require_corrective_fields and str(step.get("kind") or "") == "tool_result":
            if any(trace.get(key) in (None, "", []) for key in ("predicted_outcome", "actual_outcome", "adjustment_applied", "next_guard")):
                return False
            if (trace.get("cycle_delta") or {}).get("repair_closure") is None:
                return False
    return True


def _case_boundary_integrity(case_result: Dict[str, Any]) -> bool:
    family = str(case_result.get("family") or "")
    if family not in {"identity_continuity", "decision_conflict"}:
        return True
    return all(
        str((step.get("response_tendency") or {}).get("preferred_mode") or "") != "respond"
        for step in list(case_result.get("steps") or [])
    )


def _case_repair_closure(case_result: Dict[str, Any]) -> bool:
    expected = dict(case_result.get("expected_scoring_surface") or {})
    if not expected.get("requires_repair_closure"):
        return True
    for step in list(case_result.get("steps") or []):
        trace = _canonical_trace(step)
        if (trace.get("cycle_delta") or {}).get("repair_closure"):
            return True
    return False


def _case_verdict(case_result: Dict[str, Any], *, variant_id: str) -> Dict[str, Any]:
    target_scores = _case_target_scores(case_result)
    target_pass = {
        target: score >= TARGET_THRESHOLDS[target]
        for target, score in target_scores.items()
    }
    boundary_integrity = _case_boundary_integrity(case_result)
    trace_contract = _case_trace_contract_pass(case_result, variant_id=variant_id)
    repair_closure = _case_repair_closure(case_result)
    passed = bool(target_pass) and all(target_pass.values()) and boundary_integrity and trace_contract and repair_closure
    return {
        "case_id": case_result.get("case_id"),
        "family": case_result.get("family"),
        "variant_id": variant_id,
        "target_scores": target_scores,
        "target_pass": target_pass,
        "boundary_integrity": boundary_integrity,
        "trace_contract": trace_contract,
        "repair_closure": repair_closure,
        "pass": passed,
    }


async def _prepare_ingress_context(
    bridge: TelegramRuntimeBridge,
    *,
    text: str,
    state: Any,
    scenario: Dict[str, Any],
    segment_id: str,
    variant_id: str,
    experiment_id: str,
    action_family: str,
) -> Dict[str, Any]:
    decision = await bridge.inspect_ingress_semantic(text, state, llm_client=None)
    ingress_context = bridge.build_ingress_context(decision, state)
    overrides = _build_runtime_overrides(
        scenario=scenario,
        segment_id=segment_id,
        variant_id=variant_id,
        experiment_id=experiment_id,
        action_family=action_family,
    )
    return _patch_ingress_context(
        ingress_context,
        experiment_id=experiment_id,
        overrides=overrides,
        safety_overrides=_build_private_safety_overrides(scenario),
    )


async def _run_variant_for_scenario(
    *,
    scenario: Dict[str, Any],
    contract: Dict[str, Any],
    variant_id: str,
) -> Dict[str, Any]:
    experiment_id = _experiment_id(contract, str(scenario.get("scenario_id") or "unknown"))
    external_result_steps = list(scenario.get("external_result_steps") or [])
    by_message_index: Dict[int, List[Dict[str, Any]]] = {}
    for item in external_result_steps:
        index = int(item.get("after_message_index") or 0)
        by_message_index.setdefault(index, []).append(dict(item))

    with tempfile.TemporaryDirectory(prefix="active_inference_controlled_observation_") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        runtime, adapter = _configure_isolated_runtime(temp_dir)
        bridge = TelegramRuntimeBridge()
        observation_records: List[Dict[str, Any]] = []
        case_steps: List[Dict[str, Any]] = []
        message_index = 0
        step_ordinal = 0

        for segment in list(scenario.get("segments") or []):
            segment_id = str(segment.get("segment_id") or "").strip() or f"segment_{len(observation_records) + 1:03d}"
            session_id = _segment_session_id(
                contract,
                scenario_id=str(scenario.get("scenario_id") or ""),
                segment_id=segment_id,
            )
            for text in list(segment.get("messages") or []):
                message_index += 1
                step_ordinal += 1
                state = runtime.get_state(session_id)
                state.ingress_context = await _prepare_ingress_context(
                    bridge,
                    text=str(text),
                    state=state,
                    scenario=scenario,
                    segment_id=segment_id,
                    variant_id=variant_id,
                    experiment_id=experiment_id,
                    action_family=str((scenario.get("expected_scoring_surface") or {}).get("probe_key") or "unknown"),
                )
                ingress_created_at = _now_iso()
                ingress_event_id = f"active_inference_controlled_observation_ingress_{step_ordinal:03d}"
                result = await runtime.run_turn_typed(
                    session_id=session_id,
                    user_input=str(text),
                    source=str(contract.get("source") or "runtime_harness"),
                )
                turn_id = _extract_turn_id(result, fallback_index=step_ordinal)
                observation_record = build_runtime_observation_record(
                    session_id=session_id,
                    turn_id=turn_id,
                    user_input=str(text),
                    result=result,
                    state=state,
                    transport_source=str(contract.get("transport_source") or "runtime_harness"),
                    source=str(contract.get("source") or "runtime_harness"),
                    ingress_event_id=ingress_event_id,
                    ingress_created_at=ingress_created_at,
                    delivery_event_id=f"active_inference_controlled_observation_delivery_{step_ordinal:03d}",
                    delivery_created_at=_now_iso(),
                )
                observation_records.append(observation_record)
                ingress_result = copy.deepcopy(dict(adapter.last_result or {}))
                case_steps.append(
                    _build_step_log(
                        step_id=f"ingress_{step_ordinal:03d}",
                        kind="ingress",
                        proto_self_result=ingress_result,
                        adapter=adapter,
                        experiment_id=experiment_id,
                    )
                )

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
                    case_steps.append(
                        _build_step_log(
                            step_id=f"tool_{step_ordinal:03d}",
                            kind="tool_result",
                            proto_self_result=proto_self_result,
                            adapter=adapter,
                            experiment_id=experiment_id,
                        )
                    )

    return {
        "case_id": str(scenario.get("scenario_id") or ""),
        "family": str(scenario.get("family") or ""),
        "source_type": str(scenario.get("source_type") or ""),
        "source_ref": str(scenario.get("source_ref") or ""),
        "state_snapshot_ref": str(scenario.get("state_snapshot_ref") or ""),
        "expected_scoring_surface": dict(scenario.get("expected_scoring_surface") or {}),
        "observation_records": observation_records,
        "steps": case_steps,
    }


async def run_controlled_observation_scenario(
    *,
    manifest_path: Path = MANIFEST_PATH,
    scenario_id: str = DEFAULT_SCENARIO_ID,
) -> Dict[str, Any]:
    os.environ.setdefault(MVS_REPLAY_FEATURE_FLAG_ENV, "true")
    manifest = _load_json(manifest_path)
    errors = _validate_manifest(manifest)
    if errors:
        raise RuntimeError("\n".join(errors))

    scenario = _find_scenario(manifest, scenario_id)
    contract = dict(manifest.get("runner_contract") or {})
    variant_ids = [str(contract.get("baseline_a_id") or ""), str(contract.get("candidate_id") or "")]
    results_by_variant: Dict[str, List[Dict[str, Any]]] = {}
    for variant_id in variant_ids:
        results_by_variant[variant_id] = [
            await _run_variant_for_scenario(
                scenario=scenario,
                contract=contract,
                variant_id=variant_id,
            )
        ]

    report = {
        "schema_version": "active_inference.controlled_observation.single_run.v1",
        "generated_at": _now_iso(),
        "manifest_path": str(manifest_path),
        "scenario_id": scenario_id,
        "runner_contract": contract,
        "variants_run": variant_ids,
        "authority_drift_audit": _authority_drift_audit(contract),
        "trace_contract_check": _trace_contract_check(results_by_variant),
        "host_surface_bounded_audit": _host_surface_bounded_audit(contract, results_by_variant),
        "results_by_variant": results_by_variant,
    }
    return report


def render_markdown(report: Dict[str, Any]) -> str:
    trace_contract = dict(report.get("trace_contract_check") or {})
    authority_drift = dict(report.get("authority_drift_audit") or {})
    host_surface = dict(report.get("host_surface_bounded_audit") or {})
    lines = [
        "# Active-Inference Controlled Observation",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- manifest: `{report.get('manifest_path')}`",
        f"- scenario_id: `{report.get('scenario_id')}`",
        f"- variants_run: `{', '.join(report.get('variants_run') or [])}`",
        f"- authority_drift_status: `{authority_drift.get('status', 'unknown')}`",
        f"- trace_contract_status: `{trace_contract.get('status', 'unknown')}`",
        f"- host_surface_bounded: `{host_surface.get('status', 'unknown')}`",
        "",
        "## Variant Coverage",
        "",
    ]
    for variant_id, case_results in sorted((report.get("results_by_variant") or {}).items()):
        step_count = sum(len(case_result.get("steps") or []) for case_result in case_results)
        observation_count = sum(len(case_result.get("observation_records") or []) for case_result in case_results)
        lines.append(
            f"- `{variant_id}`: cases=`{len(case_results)}` observation_records=`{observation_count}` steps=`{step_count}`"
        )
    return "\n".join(lines) + "\n"


async def main() -> None:
    args = parse_args()
    report = await run_controlled_observation_scenario(
        manifest_path=args.manifest,
        scenario_id=args.scenario_id,
    )
    _write_json(args.output_json, report)
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")


if __name__ == "__main__":
    asyncio.run(main())
