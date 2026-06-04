"""Go / no-go review for PSPC v0 admission-roadmap evidence."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping


GO_CRITERIA = [
    {
        "id": "anti_hardcoding_passed",
        "summary_key": "anti_hardcoding_status",
        "expected": "pass",
        "no_go_trigger": "behavior_depends_on_object_name_or_audit_not_passed",
    },
    {
        "id": "multi_seed_generalization_passed",
        "summary_key": "multi_seed_layout_generalization_status",
        "expected": "pass",
        "gate_key": "danger_generalization",
        "no_go_trigger": "multi_seed_generalization_not_passed",
    },
    {
        "id": "world_model_ablation_passed",
        "summary_key": "world_model_causal_strength_status",
        "expected": "pass",
        "gate_key": "frozen_world_model",
        "no_go_trigger": "world_model_ablation_not_passed",
    },
    {
        "id": "self_model_ablation_passed",
        "summary_key": "self_model_causal_strength_status",
        "expected": "pass",
        "gate_key": "frozen_self_model",
        "no_go_trigger": "self_model_ablation_not_passed",
    },
    {
        "id": "memory_deletion_corruption_passed",
        "summary_key": "memory_consolidation_admission_status",
        "expected": "pass",
        "gate_key": "memory_deletion",
        "no_go_trigger": "memory_deletion_or_corruption_not_passed",
    },
    {
        "id": "homeostatic_anti_hacking_passed",
        "summary_key": "homeostatic_value_anti_hacking_status",
        "expected": "pass",
        "no_go_trigger": "homeostatic_anti_hacking_not_passed",
    },
    {
        "id": "admission_packet_contract_passed",
        "summary_key": "admission_packet_contract_status",
        "expected": "pass",
        "no_go_trigger": "admission_packet_contract_not_passed",
    },
]


def run_go_no_go_review(*, summary: Mapping[str, Any], adapter_exists: bool) -> Dict[str, Any]:
    go_conditions = [_evaluate_criterion(summary, criterion) for criterion in GO_CRITERIA]
    no_go_triggers = [
        condition["no_go_trigger"] for condition in go_conditions if condition["status"] != "pass"
    ]

    if adapter_exists:
        no_go_triggers.append("adapter_already_created_in_wrong_phase")
    if summary.get("mainline_connected") is not False:
        no_go_triggers.append("mainline_connected_unexpectedly_true")
    if summary.get("enabled") is not False:
        no_go_triggers.append("enabled_unexpectedly_true")
    if summary.get("repo_wide_evidence_remains") != "E3":
        no_go_triggers.append("repo_wide_claim_ceiling_changed")

    status = "go" if not no_go_triggers else "no_go"
    verdict = (
        "go_for_separate_read_only_adapter_design_review_only"
        if status == "go"
        else "no_go_for_adapter_design"
    )
    return {
        "status": status,
        "verdict": verdict,
        "go_conditions": go_conditions,
        "no_go_triggers": no_go_triggers,
        "scope_limits": {
            "adapter_created": adapter_exists,
            "mainline_connected": bool(summary.get("mainline_connected")),
            "enabled": bool(summary.get("enabled")),
            "repo_wide_evidence_remains": summary.get("repo_wide_evidence_remains"),
            "ego_operator_runtime_change_allowed": False,
            "repo_wide_claim_ceiling_change_allowed": False,
            "user_facing_route_creation_allowed": False,
        },
        "what_it_proves": (
            "The current PSPC-local evidence is strong enough to justify a future read-only adapter design "
            "review under a separate task and gate, while keeping PSPC disabled and disconnected from mainline."
        ),
        "what_it_does_not_prove": (
            "This does not prove adapter readiness, EgoOperator runtime efficacy, stable real user benefit, "
            "live autonomy, production integration safety, consciousness, or subjective experience."
        ),
    }


def _evaluate_criterion(summary: Mapping[str, Any], criterion: Mapping[str, Any]) -> Dict[str, Any]:
    actual = summary.get(str(criterion["summary_key"]))
    expected = criterion["expected"]
    gate_key = criterion.get("gate_key")
    gates = summary.get("gates") if isinstance(summary.get("gates"), Mapping) else {}
    gate_passed = True if gate_key is None else gates.get(str(gate_key)) is True
    passed = actual == expected and gate_passed
    return {
        "id": criterion["id"],
        "status": "pass" if passed else "fail",
        "expected": expected,
        "actual": actual,
        "gate_key": gate_key,
        "gate_passed": gate_passed,
        "no_go_trigger": criterion["no_go_trigger"],
    }
