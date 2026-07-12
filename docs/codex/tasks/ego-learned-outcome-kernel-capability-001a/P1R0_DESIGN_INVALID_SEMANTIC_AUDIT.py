#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SOURCE_COMMIT = "8365911743aadf1ee508fb42336cfb0a9710aaed"
BLUEPRINT_PATH = (
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/"
    "P1R0_EXECUTABLE_DESIGN_BLUEPRINT.json"
)
CONTRACT_PATH = (
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/"
    "PREFLIGHT_CONTRACT.json"
)
P1_CARD_PATH = (
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/"
    "P1_INSTRUMENT_TASK_CARD.md"
)
P1R0_CARD_PATH = (
    "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/"
    "P1R0_EXECUTABLE_DESIGN_TASK_CARD.md"
)
INVALID_VERDICT = (
    "P1R0_EXECUTABLE_DESIGN_FEASIBILITY_FALSE_POSITIVE__"
    "P1R1_NOT_ADMISSIBLE__CURRENT_INSTRUMENT_FAMILY_CLOSEOUT_REQUIRED"
)
CLAIM_CEILING = (
    "Independent semantic invalidation of the stored P1R0 design-admission "
    "verdict only. This does not prove that the frozen surface is impossible, "
    "that a mechanism is invalid, or that learning/product/runtime claims fail."
)

MODULE_REQUIRED_KEYS = {
    "contract.py": {
        "/surface_selection",
        "/surface",
        "/splits",
        "/seed_plan",
        "/computed_provenance",
    },
    "workload.py": {
        "/surface",
        "/collection_policy",
        "/information_boundary",
        "/splits",
        "/seed_plan",
        "/information_interventions",
    },
    "oracles.py": {
        "/surface",
        "/targets_and_oracles",
        "/information_boundary",
        "/instrument_controls",
    },
    "baselines.py": {
        "/baseline_role_registry",
        "/baseline_adequacy",
        "/accessibility_witness",
        "/information_boundary",
    },
    "metrics.py": {
        "/metrics",
        "/statistical_contract",
        "/positive_acceptance_rule",
        "/verdict_priority",
        "/computed_provenance",
    },
    "leakage.py": {
        "/leakage_scanner",
        "/information_boundary",
    },
    "replay.py": {
        "/replay",
        "/information_interventions",
        "/computed_provenance",
    },
    "producer.py": {
        "/authorization",
        "/future_artifacts",
        "/positive_acceptance_rule",
        "/verdict_priority",
        "/anti_zeno",
        "/stop_conditions",
    },
}

FORMAL_REQUIRED_DESIGN_FIELDS = {
    "authorization_object_path",
    "required_authorization_fields",
    "authorization_commit_ancestor_check",
    "p1r1_commit_pin_check",
    "p1r1_path_byte_identity_check",
    "clean_worktree_and_index_check",
    "formal_output_absence_check",
    "formal_run_limit_check",
    "current_head_self_assertion_forbidden",
}

P1R0_GENERIC_TRACE_CALLABLE = "production callable mapped by module_designs"
P1R0_GENERIC_TRACE_FAILURE = "frozen failure-priority status"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_bytes(repo: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{commit}:{path}"],
        cwd=repo,
    )


def git_text(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def finding(
    check_id: str,
    json_pointer: str,
    expected: Any,
    observed: Any,
    reason: str,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "json_pointer": json_pointer,
        "expected": expected,
        "observed": observed,
        "reason": reason,
        "blocking": True,
    }


def module_key_findings(
    blueprint: dict[str, Any],
    contract: dict[str, Any] | None = None,
    p1_card: str | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    modules = {
        Path(item["path"]).name: item
        for item in blueprint.get("module_designs", [])
    }
    for module_name, required in MODULE_REQUIRED_KEYS.items():
        if contract is not None:
            absent_contract_keys = sorted(
                pointer
                for pointer in required
                if pointer.strip("/") not in contract
            )
            if absent_contract_keys:
                raise ValueError(
                    f"auditor expected missing P0 keys: {absent_contract_keys}"
                )
        if p1_card is not None and f"### {module_name}" not in p1_card:
            raise ValueError(
                f"pinned P1 card lacks module responsibility: {module_name}"
            )
        item = modules.get(module_name)
        observed = set((item or {}).get("frozen_contract_keys_consumed") or [])
        missing = sorted(required - observed)
        if missing:
            out.append(
                finding(
                    f"module_keys:{module_name}",
                    f"/module_designs/{module_name}/frozen_contract_keys_consumed",
                    sorted(required),
                    sorted(observed),
                    "Module-specific frozen inputs are not mapped; non-empty generic keys are insufficient.",
                )
            )
    unique_key_sets = {
        tuple(item.get("frozen_contract_keys_consumed") or [])
        for item in blueprint.get("module_designs", [])
    }
    if len(unique_key_sets) == 1:
        out.append(
            finding(
                "module_keys:template_collapse",
                "/module_designs",
                "module-specific key sets",
                [list(value) for value in sorted(unique_key_sets)],
                "All module designs reuse one generic frozen-key set.",
            )
        )
    return out


def traceability_findings(
    blueprint: dict[str, Any],
    p1_card: str | None = None,
) -> list[dict[str, Any]]:
    checks = [
        item
        for item in blueprint.get("traceability", [])
        if str(item.get("requirement_id", "")).startswith("P1-DEV-CHECK-")
    ]
    out: list[dict[str, Any]] = []
    if p1_card is not None:
        section = p1_card.split("## 10. Required DEV checks", 1)[1].split(
            "## 11.", 1
        )[0]
        frozen_checks = re.findall(r"(?m)^\d+\.\s+(.+?);?$", section)
        if len(frozen_checks) != 26:
            raise ValueError(
                f"pinned P1 card DEV-check count is {len(frozen_checks)}, not 26"
            )
    generic_callable = sum(
        item.get("owned_callable_or_state_transition")
        == P1R0_GENERIC_TRACE_CALLABLE
        for item in checks
    )
    generic_failure = sum(
        item.get("expected_failure_status") == P1R0_GENERIC_TRACE_FAILURE
        for item in checks
    )
    if len(checks) != 26 or generic_callable:
        out.append(
            finding(
                "traceability:callable_mapping",
                "/traceability/P1-DEV-CHECK-01..26",
                "26 exact callable or state-transition mappings",
                {
                    "check_count": len(checks),
                    "generic_callable_count": generic_callable,
                },
                "Requirement IDs exist, but callable ownership remains a generic placeholder.",
            )
        )
    if generic_failure:
        out.append(
            finding(
                "traceability:failure_mapping",
                "/traceability/P1-DEV-CHECK-01..26",
                "exact failure status per check",
                {"generic_failure_count": generic_failure},
                "Failure-path mapping is generic rather than executable.",
            )
        )
    return out


def baseline_by_id(blueprint: dict[str, Any], baseline_id: str) -> dict[str, Any]:
    return next(
        item
        for item in blueprint.get("baseline_designs", [])
        if item.get("id") == baseline_id
    )


def baseline_findings(
    blueprint: dict[str, Any],
    contract: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    frozen_by_id: dict[str, dict[str, Any]] = {}
    if contract is not None:
        registry = contract["baseline_role_registry"]
        for group in (
            "invalidating_controls",
            "feasible_reference",
            "capability_rivals",
        ):
            for item in registry[group]:
                frozen_by_id[item["id"]] = item

        required_fragments = {
            "no_feedback_public_prior": "constant public-prior probability 0.5",
            "observation_action_logistic": "current context and queried action only",
            "random_probability_matched_marginal": "matched to train marginal",
            "legal_map_estimator": "maximum-likelihood public latent state",
            "per_task_specialist_envelope": "evaluator-only specialist envelope",
        }
        for baseline_id, fragment in required_fragments.items():
            frozen = frozen_by_id[baseline_id]
            frozen_text = " ".join(
                str(value) for value in frozen.values()
            )
            if fragment not in frozen_text:
                raise ValueError(
                    f"pinned P0 semantics drifted for {baseline_id}"
                )

    no_feedback = baseline_by_id(blueprint, "no_feedback_public_prior")
    forbidden_history_fields = {
        "prior_legal_context_descriptors",
        "prior_chosen_action_descriptors",
        "prior_observed_binary_outcomes",
        "history_length",
    }
    observed_history = sorted(
        forbidden_history_fields
        & set(no_feedback.get("legal_input_fields") or [])
    )
    if observed_history:
        out.append(
            finding(
                "baseline:no_feedback_access",
                "/baseline_designs/no_feedback_public_prior/legal_input_fields",
                "no feedback/history fields",
                observed_history,
                "A no-feedback public-prior control must not read history.",
            )
        )

    observation_only = baseline_by_id(blueprint, "observation_action_logistic")
    observed_history = sorted(
        forbidden_history_fields
        & set(observation_only.get("legal_input_fields") or [])
    )
    if observed_history:
        out.append(
            finding(
                "baseline:observation_only_access",
                "/baseline_designs/observation_action_logistic/legal_input_fields",
                "current context and queried action only",
                observed_history,
                "The observation-only control is designed with history access.",
            )
        )

    matched = baseline_by_id(
        blueprint, "random_probability_matched_marginal"
    )
    matched_target = str(matched.get("fit_update_target") or "")
    matched_data = str(matched.get("fit_update_dataset_boundary") or "")
    if "observed" not in matched_target or "train" not in matched_data:
        out.append(
            finding(
                "baseline:matched_marginal_target",
                "/baseline_designs/random_probability_matched_marginal",
                "fit train observed-outcome marginal, then sample matched seeded probabilities",
                {
                    "target": matched_target,
                    "dataset": matched_data,
                },
                "The design uses current-packet/legal-q semantics instead of the frozen train marginal.",
            )
        )

    legal_map = baseline_by_id(blueprint, "legal_map_estimator")
    map_target = str(legal_map.get("fit_update_target") or "")
    map_data = str(legal_map.get("fit_update_dataset_boundary") or "")
    map_semantics = str(legal_map.get("prediction_update_semantics") or "")
    if (
        "public latent" not in map_semantics.lower()
        or "current legal" not in map_data.lower()
        or "train" in map_data.lower()
        or "observed chosen-action" in map_target.lower()
    ):
        out.append(
            finding(
                "baseline:legal_map_semantics",
                "/baseline_designs/legal_map_estimator",
                "episode legal-history maximum-likelihood public latent and public-family prediction",
                {
                    "target": map_target,
                    "dataset": map_data,
                    "semantics": map_semantics,
                },
                "The design turns the legal-history MAP rival into a train/validation label-fit route.",
            )
        )

    specialist = baseline_by_id(
        blueprint, "per_task_specialist_envelope"
    )
    specialist_target = str(specialist.get("fit_update_target") or "")
    if "instrument-control expected status" in specialist_target:
        out.append(
            finding(
                "baseline:specialist_target",
                "/baseline_designs/per_task_specialist_envelope/fit_update_target",
                "evaluator-only task-specialist prediction/decision envelope",
                specialist_target,
                "The capability rival is mapped to a control-status target rather than a specialist envelope.",
            )
        )

    for baseline_id in (
        "fitted_history_meta_mlp",
        "from_scratch_online_logistic",
    ):
        item = baseline_by_id(blueprint, baseline_id)
        exact = item.get("exact_configuration") or {}
        policy = str((item.get("seed_policy") or {}).get("p1r1_dev") or "")
        if "random_state" in exact and "retain frozen random_state" in policy:
            out.append(
                finding(
                    f"seed_firewall:{baseline_id}",
                    f"/baseline_designs/{baseline_id}/seed_policy/p1r1_dev",
                    (
                        "an explicit mapping from the fixed estimator RNG "
                        "to an allowed DEV domain without a second seed path"
                    ),
                    policy,
                    (
                        "The blueprint repeats both the fixed random_state "
                        "and DEV-only firewall without resolving their RNG "
                        "provenance."
                    ),
                )
            )
    return out


def formal_findings(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    formal = blueprint.get("formal_pipeline") or {}
    out: list[dict[str, Any]] = []
    missing = sorted(FORMAL_REQUIRED_DESIGN_FIELDS - set(formal))
    if missing:
        out.append(
            finding(
                "formal:authorization_contract",
                "/formal_pipeline",
                sorted(FORMAL_REQUIRED_DESIGN_FIELDS),
                sorted(formal),
                (
                    "The future success path lacks exact authorization, "
                    "ancestry, byte-pin, clean-repo, output-absence and "
                    "run-limit fields."
                ),
            )
        )
    guards = {
        str(item.get("guard") or "")
        for item in formal.get("transitions", [])
    }
    if len(guards) <= 1:
        out.append(
            finding(
                "formal:transition_guards",
                "/formal_pipeline/transitions/*/guard",
                "state-specific production guard contracts",
                sorted(guards),
                "All formal transitions reuse one generic guard sentence.",
            )
        )
    return out


def seed_phase_findings(
    blueprint: dict[str, Any],
    contract: dict[str, Any] | None = None,
    p1_card: str | None = None,
) -> list[dict[str, Any]]:
    reserved = [
        item
        for item in blueprint.get("seed_consumption_matrix", [])
        if item.get("classification")
        == "P2_FORMAL_RESERVED_NOT_CONSUMED_IN_P1R1"
    ]
    phases = {str(item.get("future_p2_phase") or "") for item in reserved}
    callables = {
        str(item.get("future_shared_pipeline_callable") or "")
        for item in reserved
    }
    if contract is not None:
        frozen_domains = set(contract["seed_plan"]["stream_domains"])
        observed_domains = {
            item.get("domain")
            for item in blueprint.get("seed_consumption_matrix", [])
        }
        if frozen_domains != observed_domains:
            raise ValueError("blueprint seed-domain set differs from pinned P0")
    if p1_card is not None:
        for domain in (
            "dev_history",
            "dev_outcome",
            "dev_action_order",
            "leakage_positive_control",
        ):
            if domain not in p1_card:
                raise ValueError(f"pinned P1 card lacks allowed domain {domain}")
    if len(phases) <= 1 or len(callables) <= 1:
        return [
            finding(
                "seed:formal_phase_mapping",
                "/seed_consumption_matrix",
                "domain-specific future phase and consumer callable mappings",
                {
                    "reserved_domain_count": len(reserved),
                    "unique_phase_count": len(phases),
                    "unique_callable_count": len(callables),
                    "phases": sorted(phases),
                    "callables": sorted(callables),
                },
                "Fourteen distinct formal/reference/replay domains collapse to one generic phase/callable mapping.",
            )
        ]
    return []


def embedded_lint_findings(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    source = str(
        (blueprint.get("structural_lint") or {}).get("producer_source") or ""
    )
    out: list[dict[str, Any]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [
            finding(
                "embedded_lint:syntax",
                "/structural_lint/producer_source",
                "valid Python AST",
                str(exc),
                "The embedded lint source is not executable Python.",
            )
        ]

    verdict_expression: ast.expr | None = None
    decision_buckets: dict[str, list[ast.expr]] = {
        "hard": [],
        "comp": [],
    }
    result_expressions: list[ast.expr] = []

    def subscript_name(node: ast.expr) -> tuple[str, str] | None:
        if not isinstance(node, ast.Subscript):
            return None
        if not isinstance(node.value, ast.Name):
            return None
        key_node = node.slice
        if not (
            isinstance(key_node, ast.Constant)
            and isinstance(key_node.value, str)
        ):
            return None
        return node.value.id, key_node.value

    def dictionary_values(node: ast.expr) -> list[ast.expr]:
        if not isinstance(node, ast.Dict):
            return []
        return [value for value in node.values if value is not None]

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id in decision_buckets:
                        decision_buckets[target.id].extend(
                            dictionary_values(node.value)
                        )
                    elif target.id == "result":
                        result_expressions.append(node.value)
                target_key = subscript_name(target)
                if target_key and target_key[0] in decision_buckets:
                    decision_buckets[target_key[0]].append(node.value)
                    if target_key == ("hard", "verdict"):
                        verdict_expression = node.value
        if not isinstance(node, ast.Call):
            continue
        if not (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in decision_buckets
            and node.func.attr == "update"
        ):
            continue
        bucket = node.func.value.id
        for argument in node.args:
            decision_buckets[bucket].extend(dictionary_values(argument))
        for keyword in node.keywords:
            decision_buckets[bucket].append(keyword.value)
            if bucket == "hard" and keyword.arg == "verdict":
                verdict_expression = keyword.value

    blocked_probe = copy.deepcopy(blueprint)
    blocked_probe["feasibility_verdict"] = (
        "P1R0_EXECUTABLE_DESIGN_BLOCKED__PROBE"
    )
    blocked_probe["blockers"] = [
        {"frozen_json_pointer": "/probe", "reason": "probe"}
    ]
    blocked_supported = False
    if verdict_expression is not None:
        try:
            expression = ast.Expression(body=verdict_expression)
            ast.fix_missing_locations(expression)
            blocked_supported = bool(
                eval(
                    compile(expression, "<embedded-verdict-probe>", "eval"),
                    {"__builtins__": {"all": all, "bool": bool}},
                    {"b": blocked_probe},
                )
            )
        except (KeyError, NameError, TypeError, ValueError):
            blocked_supported = False
    if not blocked_supported:
        out.append(
            finding(
                "embedded_lint:blocked_branch",
                "/structural_lint/producer_source",
                "hard-integrity support for both FEASIBLE and BLOCKED records",
                "task-card-valid BLOCKED probe evaluates false",
                "A task-card-valid BLOCKED blueprint cannot pass the embedded lint.",
            )
        )

    relevant_buckets: set[str] = set()
    for expression in result_expressions:
        relevant_buckets.update(
            node.id
            for node in ast.walk(expression)
            if isinstance(node, ast.Name) and node.id in decision_buckets
        )
    decision_expressions = list(result_expressions)
    for bucket in sorted(relevant_buckets):
        decision_expressions.extend(decision_buckets[bucket])

    decision_subscript_keys: set[str] = set()
    for expression in decision_expressions:
        for node in ast.walk(expression):
            key = subscript_name(node)
            if key and key[0] == "b":
                decision_subscript_keys.add(key[1])

    missing_semantic_checks = [
        token
        for token in (
            "frozen_contract_keys_consumed",
            "fit_update_target",
            "fit_update_dataset_boundary",
            "owned_callable_or_state_transition",
        )
        if token not in decision_subscript_keys
    ]
    if missing_semantic_checks:
        out.append(
            finding(
                "embedded_lint:semantic_coverage",
                "/structural_lint/producer_source",
                "semantic checks that directly feed comp/hard and the final result decision",
                missing_semantic_checks,
                "The lint omits admission-gating semantics or reads them decoratively without feeding the final decision.",
            )
        )
    return out


def audit_blueprint(
    blueprint: dict[str, Any],
    contract: dict[str, Any],
    p1_card: str,
    p1r0_card: str,
) -> list[dict[str, Any]]:
    if "same_task_repair_after_invalid_instrument=false" not in p1r0_card:
        raise ValueError("pinned P1R0 card lacks Anti-Zeno literal")
    findings: list[dict[str, Any]] = []
    findings.extend(module_key_findings(blueprint, contract, p1_card))
    findings.extend(traceability_findings(blueprint, p1_card))
    findings.extend(baseline_findings(blueprint, contract))
    findings.extend(formal_findings(blueprint))
    findings.extend(seed_phase_findings(blueprint, contract, p1_card))
    findings.extend(embedded_lint_findings(blueprint))
    return findings


def run_self_test() -> dict[str, Any]:
    checks: dict[str, bool] = {}

    module_good = {
        "module_designs": [
            {
                "path": f"x/{name}",
                "frozen_contract_keys_consumed": sorted(required),
            }
            for name, required in MODULE_REQUIRED_KEYS.items()
        ]
    }
    checks["module_negative_clean"] = not module_key_findings(module_good)
    module_bad = copy.deepcopy(module_good)
    module_bad["module_designs"][0]["frozen_contract_keys_consumed"] = []
    checks["module_positive_detected"] = bool(
        module_key_findings(module_bad)
    )

    trace_good = {
        "traceability": [
            {
                "requirement_id": f"P1-DEV-CHECK-{index:02d}",
                "owned_callable_or_state_transition": f"callable_{index}",
                "expected_failure_status": f"FAIL_{index}",
            }
            for index in range(1, 27)
        ]
    }
    checks["trace_negative_clean"] = not traceability_findings(trace_good)
    trace_bad = copy.deepcopy(trace_good)
    for item in trace_bad["traceability"]:
        item["owned_callable_or_state_transition"] = (
            P1R0_GENERIC_TRACE_CALLABLE
        )
        item["expected_failure_status"] = P1R0_GENERIC_TRACE_FAILURE
    checks["trace_positive_detected"] = bool(
        traceability_findings(trace_bad)
    )

    formal_good = {
        "formal_pipeline": {
            **{key: True for key in FORMAL_REQUIRED_DESIGN_FIELDS},
            "transitions": [
                {"guard": "guard authorization"},
                {"guard": "guard ancestry"},
            ],
        }
    }
    checks["formal_negative_clean"] = not formal_findings(formal_good)
    formal_bad = {"formal_pipeline": {"transitions": [{"guard": "same"}]}}
    checks["formal_positive_detected"] = bool(
        formal_findings(formal_bad)
    )

    baseline_good = {
        "baseline_designs": [
            {
                "id": "no_feedback_public_prior",
                "legal_input_fields": [],
            },
            {
                "id": "observation_action_logistic",
                "legal_input_fields": [
                    "current_context_descriptor",
                    "randomly_ordered_legal_action_descriptors",
                ],
            },
            {
                "id": "random_probability_matched_marginal",
                "fit_update_target": "observed binary outcome marginal",
                "fit_update_dataset_boundary": "legal train rows",
            },
            {
                "id": "legal_map_estimator",
                "fit_update_target": "public latent likelihood",
                "fit_update_dataset_boundary": "current legal history",
                "prediction_update_semantics": (
                    "maximum-likelihood public latent state and public-family "
                    "prediction"
                ),
            },
            {
                "id": "per_task_specialist_envelope",
                "fit_update_target": (
                    "evaluator-only task-specialist prediction envelope"
                ),
            },
            {
                "id": "fitted_history_meta_mlp",
                "exact_configuration": {"random_state": 65001},
                "seed_policy": {
                    "p1r1_dev": "explicit allowed DEV-domain mapping"
                },
            },
            {
                "id": "from_scratch_online_logistic",
                "exact_configuration": {"random_state": 65002},
                "seed_policy": {
                    "p1r1_dev": "explicit allowed DEV-domain mapping"
                },
            },
        ]
    }
    checks["baseline_negative_clean"] = not baseline_findings(
        baseline_good
    )
    baseline_bad = copy.deepcopy(baseline_good)
    matched = baseline_by_id(
        baseline_bad, "random_probability_matched_marginal"
    )
    matched["fit_update_target"] = "legal q"
    matched["fit_update_dataset_boundary"] = "current packet"
    checks["baseline_positive_detected"] = bool(
        baseline_findings(baseline_bad)
    )

    seed_good = {
        "seed_consumption_matrix": [
            {
                "classification": (
                    "P2_FORMAL_RESERVED_NOT_CONSUMED_IN_P1R1"
                ),
                "domain": f"reserved_{index}",
                "future_p2_phase": f"phase_{index}",
                "future_shared_pipeline_callable": f"callable_{index}",
            }
            for index in range(14)
        ]
    }
    checks["seed_phase_negative_clean"] = not seed_phase_findings(
        seed_good
    )
    seed_bad = copy.deepcopy(seed_good)
    for item in seed_bad["seed_consumption_matrix"]:
        item["future_p2_phase"] = "generic phase"
        item["future_shared_pipeline_callable"] = "generic callable"
    checks["seed_phase_positive_detected"] = bool(
        seed_phase_findings(seed_bad)
    )

    lint_good = {
        "frozen_contract_keys_consumed": ["/surface"],
        "fit_update_target": "observed outcome",
        "fit_update_dataset_boundary": "train split",
        "owned_callable_or_state_transition": "module.callable",
        "structural_lint": {
            "producer_source": (
                "hard={}\n"
                "hard.update(verdict=b['feasibility_verdict'] in "
                "['P1R0_EXECUTABLE_DESIGN_FEASIBLE',"
                "'P1R0_EXECUTABLE_DESIGN_BLOCKED__PROBE'])\n"
                "comp={}\n"
                "comp.update(module_keys=bool("
                "b['frozen_contract_keys_consumed']),"
                "target=bool(b['fit_update_target']),"
                "dataset=bool(b['fit_update_dataset_boundary']),"
                "trace=bool(b['owned_callable_or_state_transition']))\n"
                "result=all(hard.values()) and all(comp.values())\n"
            )
        }
    }
    checks["lint_negative_clean"] = not embedded_lint_findings(
        lint_good
    )

    lint_bad = {
        "frozen_contract_keys_consumed": ["/surface"],
        "fit_update_target": "observed outcome",
        "fit_update_dataset_boundary": "train split",
        "owned_callable_or_state_transition": "module.callable",
        "structural_lint": {
            "producer_source": (
                "semantic=(b['frozen_contract_keys_consumed'],"
                "b['fit_update_target'],b['fit_update_dataset_boundary'],"
                "b['owned_callable_or_state_transition'])\n"
                "hard={}\n"
                "hard.update(verdict=b['feasibility_verdict'] in "
                "['P1R0_EXECUTABLE_DESIGN_FEASIBLE',"
                "'P1R0_EXECUTABLE_DESIGN_BLOCKED__PROBE'])\n"
                "comp={}\n"
                "result=all(hard.values()) and all(comp.values())\n"
            )
        }
    }
    checks["lint_positive_detected"] = (
        "embedded_lint:semantic_coverage"
        in {
            item["check_id"]
            for item in embedded_lint_findings(lint_bad)
        }
    )

    return {
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def build_report(repo: Path, source_commit: str) -> dict[str, Any]:
    blueprint_bytes = git_bytes(
        repo, source_commit, BLUEPRINT_PATH
    )
    contract_bytes = git_bytes(repo, source_commit, CONTRACT_PATH)
    p1_card_bytes = git_bytes(repo, source_commit, P1_CARD_PATH)
    p1r0_card_bytes = git_bytes(
        repo, source_commit, P1R0_CARD_PATH
    )
    blueprint = json.loads(blueprint_bytes)
    contract = json.loads(contract_bytes)
    p1_card = p1_card_bytes.decode("utf-8")
    p1r0_card = p1r0_card_bytes.decode("utf-8")
    findings = audit_blueprint(
        blueprint,
        contract,
        p1_card,
        p1r0_card,
    )
    self_test = run_self_test()
    if not self_test["all_pass"]:
        raise RuntimeError("audit positive/negative control self-test failed")

    script_bytes = Path(__file__).read_bytes()
    input_hashes = {
        BLUEPRINT_PATH: sha256(blueprint_bytes),
        CONTRACT_PATH: sha256(contract_bytes),
        P1_CARD_PATH: sha256(p1_card_bytes),
        P1R0_CARD_PATH: sha256(p1r0_card_bytes),
    }
    input_blobs = {
        path: git_text(repo, "rev-parse", f"{source_commit}:{path}")
        for path in input_hashes
    }
    run_material = canonical_json_bytes(
        {
            "source_commit": source_commit,
            "input_hashes": input_hashes,
            "code_path_hash": sha256(script_bytes),
        }
    )
    computed_verdict = (
        INVALID_VERDICT
        if findings
        else "P1R0_EXECUTABLE_DESIGN_SEMANTIC_AUDIT_FOUND_NO_BLOCKER"
    )
    prior_boundary = blueprint.get("prior_p1_boundary") or {}
    p1r1_admissible = not findings
    p2_admissible = bool(
        p1r1_admissible
        and prior_boundary.get("p1b_commit")
        and not prior_boundary.get("formal_artifact_present")
        and not prior_boundary.get("p2_authorization_present")
    )
    return {
        "schema_version": "ego.p1r0.design_invalid_audit.v1",
        "producer_function": "audit_blueprint",
        "producer_script": (
            "docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/"
            "P1R0_DESIGN_INVALID_SEMANTIC_AUDIT.py"
        ),
        "code_path_hash": sha256(script_bytes),
        "run_id": "p1r0-semantic-audit-" + sha256(run_material)[:16],
        "source_commit": source_commit,
        "input_artifact_paths": list(input_hashes),
        "input_artifact_hashes": input_hashes,
        "input_artifact_blobs": input_blobs,
        "stored_feasibility_verdict": blueprint.get(
            "feasibility_verdict"
        ),
        "stored_blockers": blueprint.get("blockers"),
        "embedded_lint_recorded_result": (
            blueprint.get("structural_lint") or {}
        ).get("recorded_result"),
        "semantic_input_consumption": {
            CONTRACT_PATH: [
                "/baseline_role_registry",
                "/seed_plan/stream_domains",
            ],
            P1_CARD_PATH: [
                "section 7 module responsibilities",
                "section 9 seed firewall",
                "section 10 required DEV checks",
            ],
            P1R0_CARD_PATH: [
                "section 24 Anti-Zeno route",
            ],
        },
        "self_test": self_test,
        "aggregation_rule": (
            "INVALID iff one or more independently computed semantic "
            "blocking findings exist; no score or compensation"
        ),
        "blocking_finding_count": len(findings),
        "blocking_findings": findings,
        "computed_verdict": computed_verdict,
        "p1r1_admissible": p1r1_admissible,
        "p2_admissible": p2_admissible,
        "admissibility_computation": {
            "p1r1": "no independent semantic findings",
            "p2": (
                "p1r1 admissible AND banked P1B/P1R1 commit present AND "
                "formal artifact absent AND P2 authorization absent"
            ),
        },
        "policy_boundaries": {
            "independent_validator_acceptance": "UNAVAILABLE",
            "local_callable_is_independent_validator": False,
            "formal_authorization": False,
            "surface_mathematical_status": "NOT_ADJUDICATED",
            "surface_impossibility_not_claimed": True,
        },
        "claim_ceiling": CLAIM_CEILING,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source-commit", default=SOURCE_COMMIT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--require-invalid", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        report = run_self_test()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["all_pass"] else 2

    report = build_report(args.repo.resolve(), args.source_commit)
    data = canonical_json_bytes(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
    else:
        sys.stdout.buffer.write(data)

    if args.require_invalid and report["computed_verdict"] != INVALID_VERDICT:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
