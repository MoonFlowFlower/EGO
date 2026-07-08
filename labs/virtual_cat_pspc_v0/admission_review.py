"""Go / no-go review for PSPC v0 admission-roadmap evidence."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
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

REQUIRED_ADAPTER_FORBIDDEN_FLAGS = frozenset(
    {
        "direct_action",
        "direct_user_message",
        "direct_memory_write",
        "runtime_gate_bypass",
        "runtime_registration",
        "proactive_trigger",
    }
)

REQUIRED_FORBIDDEN_PACKET_FIELDS = frozenset(
    {
        "action",
        "tool_call",
        "command",
        "user_message",
        "message_text",
        "memory_write",
        "memory_patch",
        "operator_memory_update",
        "gate_decision",
        "approval_id",
        "preapproved",
        "transport",
        "send",
        "schedule",
        "enable",
        "mainline_authority",
        "consciousness_claim",
        "subjective_experience_claim",
    }
)


def run_go_no_go_review(
    *,
    summary: Mapping[str, Any],
    adapter_exists: bool,
    adapter_contract: Mapping[str, Any] | None = None,
    lab_egooperator_import_refs: List[str] | None = None,
) -> Dict[str, Any]:
    """Compute the PSPC report-level go/no-go result.

    A sanctioned adapter file is not by itself a no-go condition after the
    2026-07-08 contract supersession. If present, it must be justified by
    independent inert-adapter facts from a static scanner.
    """

    go_conditions = [_evaluate_criterion(summary, criterion) for criterion in GO_CRITERIA]
    no_go_triggers = [
        condition["no_go_trigger"] for condition in go_conditions if condition["status"] != "pass"
    ]
    adapter_contract_facts = dict(adapter_contract or {})
    adapter_contract_violations: List[str] = []

    if adapter_exists:
        if not adapter_contract_facts:
            adapter_contract_violations.append("adapter_contract_missing_for_existing_adapter")
        else:
            adapter_contract_violations.extend(inert_adapter_contract_violations(adapter_contract_facts))
    for violation in adapter_contract_violations:
        if violation == "adapter_contract_missing_for_existing_adapter":
            no_go_triggers.append(violation)
        else:
            no_go_triggers.append(f"adapter_contract_violation:{violation}")

    lab_import_refs = list(lab_egooperator_import_refs or [])
    if lab_import_refs:
        no_go_triggers.append("lab_imports_egooperator")

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
    adapter_contract_status = (
        "not_applicable"
        if not adapter_exists
        else "pass"
        if not adapter_contract_violations
        else "fail"
    )
    scope_limits = {
        "adapter_created": adapter_exists,
        "adapter_contract_status": adapter_contract_status,
        "adapter_contract_violations": adapter_contract_violations,
        "lab_egooperator_import_refs": lab_import_refs,
        "mainline_connected": bool(summary.get("mainline_connected")),
        "enabled": bool(summary.get("enabled")),
        "repo_wide_evidence_remains": summary.get("repo_wide_evidence_remains"),
        "ego_operator_runtime_change_allowed": False,
        "repo_wide_claim_ceiling_change_allowed": False,
        "user_facing_route_creation_allowed": False,
    }
    what_it_proves = (
        "The current PSPC-local evidence is strong enough to justify a future read-only adapter design "
        "review under a separate task and gate, while any present adapter is independently checked as inert, "
        "disabled, and disconnected from mainline."
        if status == "go"
        else "The current PSPC go/no-go review computation found blocking evidence or scope triggers; "
        "adapter design or runtime-integration claims must not advance until the triggers are repaired and rerun."
    )
    return {
        "status": status,
        "verdict": verdict,
        "go_conditions": go_conditions,
        "no_go_triggers": no_go_triggers,
        "scope_limits": scope_limits,
        "provenance": _review_provenance(
            summary=summary,
            adapter_exists=adapter_exists,
            adapter_contract=adapter_contract_facts,
            lab_egooperator_import_refs=lab_import_refs,
            go_conditions=go_conditions,
            no_go_triggers=no_go_triggers,
        ),
        "what_it_proves": what_it_proves,
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


def adapter_contract_facts_from_source(
    source: str,
    *,
    runtime_registration_refs: List[str] | None = None,
) -> Dict[str, Any]:
    """Extract inert-adapter contract facts from source without importing it."""

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {
            "source_parse_error": f"{exc.__class__.__name__}:{exc.msg}",
            "runtime_registration_refs": runtime_registration_refs or [],
            "adapter_egooperator_imports": [],
        }

    constants = _module_assignment_map(tree)
    class_assignments = _class_assignment_map(tree, "PSPCLabAdapter", constants)
    return {
        "adapter_status": constants.get("ADAPTER_STATUS"),
        "enabled": class_assignments.get("enabled"),
        "mainline_connected": class_assignments.get("mainline_connected"),
        "runtime_authority": class_assignments.get("runtime_authority"),
        "required_forbidden_flags": constants.get("REQUIRED_FORBIDDEN_FLAGS") or (),
        "forbidden_packet_fields": constants.get("FORBIDDEN_PACKET_FIELDS") or (),
        "runtime_registration_refs": runtime_registration_refs or [],
        "adapter_egooperator_imports": egooperator_imports_in_source(source),
    }


def inert_adapter_contract_violations(facts: Mapping[str, Any]) -> List[str]:
    violations: List[str] = []
    if facts.get("source_parse_error"):
        violations.append(f"source_parse_error:{facts['source_parse_error']}")
    if facts.get("adapter_status") != "disabled_read_only":
        violations.append("adapter_status_must_be_disabled_read_only")
    if facts.get("enabled") is not False:
        violations.append("enabled_must_be_false")
    if facts.get("mainline_connected") is not False:
        violations.append("mainline_connected_must_be_false")
    if facts.get("runtime_authority") != "none":
        violations.append("runtime_authority_must_be_none")

    forbidden_flags = set(facts.get("required_forbidden_flags") or ())
    missing_flags = REQUIRED_ADAPTER_FORBIDDEN_FLAGS - forbidden_flags
    if missing_flags:
        violations.append(f"missing_required_forbidden_flags:{','.join(sorted(missing_flags))}")

    forbidden_fields = set(facts.get("forbidden_packet_fields") or ())
    missing_fields = REQUIRED_FORBIDDEN_PACKET_FIELDS - forbidden_fields
    if missing_fields:
        violations.append(f"missing_forbidden_packet_fields:{','.join(sorted(missing_fields))}")

    runtime_registration_refs = list(facts.get("runtime_registration_refs") or ())
    if runtime_registration_refs:
        violations.append(f"runtime_registration_refs:{','.join(runtime_registration_refs)}")

    adapter_imports = list(facts.get("adapter_egooperator_imports") or ())
    if adapter_imports:
        violations.append(f"adapter_egooperator_imports:{','.join(adapter_imports)}")

    return violations


def egooperator_imports_in_source(source: str) -> List[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"syntax_error:{exc.msg}"]

    imports: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "EgoOperator" or alias.name.startswith("EgoOperator."):
                    imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "EgoOperator" or module.startswith("EgoOperator."):
                imports.append(module)
    return imports


def _module_assignment_map(tree: ast.Module) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            values[node.targets[0].id] = _literal_or_constant(node.value, values)
    return values


def _class_assignment_map(tree: ast.Module, class_name: str, constants: Mapping[str, Any]) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                    values[item.targets[0].id] = _literal_or_constant(item.value, constants)
    return values


def _literal_or_constant(node: ast.AST, constants: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return tuple(_literal_or_constant(item, constants) for item in node.elts)
    return None


def _review_provenance(
    *,
    summary: Mapping[str, Any],
    adapter_exists: bool,
    adapter_contract: Mapping[str, Any],
    lab_egooperator_import_refs: List[str],
    go_conditions: List[Mapping[str, Any]],
    no_go_triggers: List[str],
) -> Dict[str, Any]:
    input_artifacts = _summary_input_artifacts(summary)
    if adapter_exists:
        input_artifacts.append("EgoOperator/adapters/pspc_lab_adapter.py")
    payload = {
        "summary": _jsonable(summary),
        "adapter_exists": adapter_exists,
        "adapter_contract": _jsonable(adapter_contract),
        "lab_egooperator_import_refs": lab_egooperator_import_refs,
        "go_conditions": _jsonable(go_conditions),
        "no_go_triggers": no_go_triggers,
    }
    run_id = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return {
        "producer_function": "labs.virtual_cat_pspc_v0.admission_review.run_go_no_go_review",
        "input_artifacts": sorted(set(input_artifacts)),
        "run_id": f"go_no_go_review_{run_id}",
        "seed_ids": list(summary.get("seeds") or []),
        "context_ids": ["virtual_cat_pspc_v0_report_generation"],
        "episode_ids": list(summary.get("episode_ids") or []),
        "aggregation_rule": "all_go_conditions_pass_and_no_no_go_triggers",
        "code_path_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def _summary_input_artifacts(summary: Mapping[str, Any]) -> List[str]:
    artifacts: List[str] = []
    for value in summary.values():
        if isinstance(value, str) and value.startswith("artifacts/"):
            artifacts.append(value)
    return artifacts


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)
