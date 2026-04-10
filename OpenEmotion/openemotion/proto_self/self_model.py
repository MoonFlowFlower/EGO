"""
Proto-Self Kernel v1 - Self-Model Update

自我模型更新：最小可测更新，不做"人格大杂烩"。

设计约束：
- 只做最小可测更新
- 不做复杂人格系统
- 更新必须可追溯、可回放
"""

from typing import Any, Dict

from openemotion.proto_self.h1_shadow import (
    H1_DEFAULT_SUCCESS,
    build_h1_shadow_key,
    resolve_h1_action_key,
)
from openemotion.proto_self.state import ProtoSelfState
from openemotion.proto_self.trial1_shadow import (
    trial1_variant_uses_mvs_core,
    trial1_variant_uses_counterfactual,
)


def update_self_model(
    state: ProtoSelfState,
    perceived: Dict[str, Any],
    appraisal_delta: Dict[str, Any],
) -> Dict[str, Any]:
    """
    更新 self_model：最小可测更新。
    
    只在明确信号下才改变 current_focus 和 current_mode。
    """
    delta = {
        "capabilities": {},
        "limitations": {},
        "current_focus": None,
        "current_mode": None,
        "self_confidence_by_domain": {},
        "counterfactual_success_by_action_patch": {},
        "recent_correction_tags_patch": {},
    }

    external_outcome_type = perceived.get("external_outcome_type")

    # 高风险 → 切换到 cautious 模式
    if perceived.get("risk_signal", 0.0) > 0.7:
        delta["current_mode"] = "cautious"

    # 高完成压力 → 聚焦于收尾
    if appraisal_delta.get("completion_pressure", 0.0) > 0.6:
        delta["current_focus"] = "closure"

    # 高好奇心 + 低风险 → 切换到探索模式
    if appraisal_delta.get("curiosity", 0.0) > 0.7 and perceived.get("risk_signal", 0.0) < 0.3:
        delta["current_mode"] = "exploration"

    # 外部失败/阻塞 → 切换到修复模式
    if external_outcome_type in {"failure", "blocked"}:
        delta["current_mode"] = "repair"
        delta["current_focus"] = "error_recovery"

    # 身份冲突 → 提升自我审查
    if perceived.get("identity_conflict", 0.0) > 0.5:
        delta["self_confidence_by_domain"] = {"self_monitoring": -0.1}

    if perceived.get("trial1_shadow_active"):
        variant_id = str(perceived.get("trial1_variant_id") or "")
        if not trial1_variant_uses_mvs_core(variant_id):
            return delta
        probe_key = str(perceived.get("trial1_probe_key") or "")
        outcome_type = perceived.get("external_outcome_type")
        correction_strength = state.self_model.recent_correction_tags.get(probe_key, 0.0)
        predicted_success = state.self_model.counterfactual_success_by_action.get(probe_key, 0.55)
        if outcome_type in {"failure", "blocked", "partial"}:
            delta["current_mode"] = "repair"
            delta["current_focus"] = "error_recovery"
            delta["recent_correction_tags_patch"][probe_key] = 1.0 if outcome_type != "partial" else 0.7
            delta["self_confidence_by_domain"][probe_key] = -0.15 if outcome_type != "partial" else -0.08
            if trial1_variant_uses_counterfactual(variant_id):
                target = 0.12 if outcome_type == "blocked" else 0.18 if outcome_type == "failure" else 0.35
                delta["counterfactual_success_by_action_patch"][probe_key] = target
        elif outcome_type == "success" and correction_strength > 0.0:
            delta["current_mode"] = "baseline"
            delta["current_focus"] = "stabilized_retry"
            delta["recent_correction_tags_patch"][probe_key] = max(0.0, correction_strength - 0.75)
            delta["self_confidence_by_domain"][probe_key] = 0.10
            if trial1_variant_uses_counterfactual(variant_id):
                delta["counterfactual_success_by_action_patch"][probe_key] = max(0.65, predicted_success)
        elif correction_strength >= 0.6:
            delta["current_mode"] = "repair"
            delta["current_focus"] = "guarded_retry"

    if perceived.get("h1_shadow_active"):
        action_key = resolve_h1_action_key(perceived)
        outcome_type = perceived.get("external_outcome_type")
        if action_key != "unknown" and outcome_type in {"failure", "blocked", "partial", "success"}:
            shadow_key = build_h1_shadow_key(action_key)
            correction_strength = state.self_model.recent_correction_tags.get(shadow_key, 0.0)
            predicted_success = state.self_model.counterfactual_success_by_action.get(shadow_key, H1_DEFAULT_SUCCESS)
            if outcome_type in {"failure", "blocked", "partial"}:
                delta["recent_correction_tags_patch"][shadow_key] = 1.0 if outcome_type != "partial" else 0.7
                if outcome_type == "blocked":
                    delta["counterfactual_success_by_action_patch"][shadow_key] = 0.12
                elif outcome_type == "failure":
                    delta["counterfactual_success_by_action_patch"][shadow_key] = 0.18
                else:
                    delta["counterfactual_success_by_action_patch"][shadow_key] = 0.35
            elif outcome_type == "success" and correction_strength > 0.0:
                delta["recent_correction_tags_patch"][shadow_key] = max(0.0, correction_strength - 0.75)
                delta["counterfactual_success_by_action_patch"][shadow_key] = max(0.65, predicted_success)

    return delta
