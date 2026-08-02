#!/usr/bin/env python3
"""Read-only provenance and product-admissibility audit for frozen 001O."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "EGO-V2-REFERENCE-TO-PRODUCT-ADMISSIBILITY-001P"
PREDECESSOR_TASK_ID = "EGO-V2-PUBLIC-FEATURED-COMPOSITIONAL-CAUSAL-TRANSFER-001O"
PREDECESSOR_VERDICT = "PUBLIC_FEATURED_EXACT_HIERARCHICAL_TRANSFER_CAPACITY_ESTABLISHED"
ARTIFACT_RELATIVE = Path("artifacts") / TASK_ID
PREDECESSOR_ARTIFACT_RELATIVE = Path("artifacts") / PREDECESSOR_TASK_ID
REFERENCE_RELATIVE = Path("labs/ego_life_playground_v0/public_featured_transfer.py")
RUNNER_RELATIVE = Path(
    "scripts/codex/run_ego_v2_public_featured_compositional_transfer_001o.py"
)
ENGINE_RELATIVE = Path("labs/ego_life_playground_v0/engine.py")
MICROWORLD_RELATIVE = Path("labs/ego_life_playground_v0/microworld.py")
CONTROLLER_RELATIVE = Path("labs/ego_life_playground_v0/controller.py")
STORE_RELATIVE = Path("labs/ego_life_playground_v0/store.py")


SERIALIZED_REFERENCE_STATE_FIELDS = {
    "joint",
    "update_count",
    "world_update_count",
    "public_history_hash",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def artifact_root(root: Path = ROOT) -> Path:
    return root / ARTIFACT_RELATIVE


def predecessor_root(root: Path = ROOT) -> Path:
    return root / PREDECESSOR_ARTIFACT_RELATIVE


def _source(root: Path, relative: Path) -> str:
    return (root / relative).read_text(encoding="utf-8")


def _parse(root: Path, relative: Path) -> ast.Module:
    return ast.parse(_source(root, relative), filename=str(relative))


def _function_evidence(root: Path, relative: Path, names: Iterable[str]) -> dict[str, Any]:
    source = _source(root, relative)
    lines = source.splitlines()
    tree = ast.parse(source)
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            segment = "\n".join(lines[node.lineno - 1 : node.end_lineno]) + "\n"
            result[node.name] = {
                "path": str(relative).replace("\\", "/"),
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "source_sha256": hashlib.sha256(segment.encode("utf-8")).hexdigest(),
                "parameters": [argument.arg for argument in node.args.args],
            }
    missing = set(names) - set(result)
    if missing:
        raise ValueError(f"missing expected functions in {relative}: {sorted(missing)}")
    return result


def _literal_assignment(root: Path, relative: Path, name: str) -> Any:
    for node in _parse(root, relative).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                return ast.literal_eval(node.value)
    raise ValueError(f"literal assignment {name} missing in {relative}")


def _reachable_symbols(root: Path, relative: Path, roots: Iterable[str]) -> dict[str, list[str]]:
    tree = _parse(root, relative)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    pending = list(roots)
    visited: set[str] = set()
    loaded: set[str] = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        node = functions.get(name)
        if node is None:
            continue
        visited.add(name)
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                loaded.add(child.id)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if child.func.id in functions and child.func.id not in visited:
                    pending.append(child.func.id)
    return {"functions": sorted(visited), "loaded_symbols": sorted(loaded)}


def verify_frozen_predecessor(root: Path = ROOT) -> dict[str, Any]:
    artifacts = predecessor_root(root)
    result = load_json(artifacts / "result.json")
    freeze = load_json(artifacts / "candidate_freeze.json")
    qualification = load_json(artifacts / "qualification_consumption.json")
    replication = load_json(artifacts / "replication_consumption.json")
    mismatches = []
    for relative, expected in freeze["files"].items():
        path = root / relative
        actual = sha256(path)
        if actual != expected:
            mismatches.append({"path": relative, "expected": expected, "actual": actual})
    tree_query = subprocess.run(
        ["git", "rev-parse", f"HEAD:{PREDECESSOR_ARTIFACT_RELATIVE.as_posix()}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    status_query = subprocess.run(
        ["git", "status", "--porcelain=v1", "--", str(PREDECESSOR_ARTIFACT_RELATIVE)],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    checks = {
        "verdict_frozen": result.get("verdict") == PREDECESSOR_VERDICT,
        "qualification_consumed_once": qualification.get("consumed_once") is True,
        "replication_consumed_once": replication.get("consumed_once") is True,
        "candidate_freeze_files_match": not mismatches,
        "predecessor_artifact_tracked": tree_query.returncode == 0,
        "predecessor_artifact_worktree_clean": not status_query.stdout.strip(),
    }
    return {
        "task_id": TASK_ID,
        "predecessor_task_id": PREDECESSOR_TASK_ID,
        "verdict": result.get("verdict"),
        "qualification_consumed_once": qualification.get("consumed_once") is True,
        "replication_consumed_once": replication.get("consumed_once") is True,
        "candidate_freeze_hash": freeze["combined_hash"],
        "frozen_file_mismatches": mismatches,
        "predecessor_artifact_tree_oid": tree_query.stdout.strip(),
        "checks": checks,
        "pass": all(checks.values()),
    }


def audit_slow_information_provenance(root: Path = ROOT) -> dict[str, Any]:
    artifacts = predecessor_root(root)
    training = load_json(artifacts / "training_public_history_receipt.json")
    grammar = load_json(artifacts / "grammar_preregistration.json")
    functions = _function_evidence(
        root,
        REFERENCE_RELATIVE,
        ("new_reference_state", "update_after_transition", "shared_marginal", "reset_for_world", "plan_action"),
    )
    fields = [
        {
            "field": "shared_mechanism_posterior",
            "serialized_state_field": "joint",
            "candidate_representation": "marginal over the 40 rows of joint[g][current_nuisance]",
            "source_class": "public_cross_world_training_history",
            "formed_from_public_history": True,
            "persistence_scope": "slow_cross_world",
            "decision_role": "posterior predictive action effects",
            "initial_value": "uniform 1/40",
            "trained_evaluator_diagnostic_probability": training[
                "shared_probability_at_evaluator_truth"
            ],
            "candidate_access": True,
            "evidence": [functions["new_reference_state"], functions["update_after_transition"], functions["shared_marginal"]],
        },
        {
            "field": "current_world_nuisance_posterior",
            "serialized_state_field": "joint",
            "candidate_representation": "conditional mass across the two columns of joint",
            "source_class": "current_world_public_feedback_plus_benchmark_local_prior",
            "formed_from_public_history": True,
            "persistence_scope": "fast_current_world",
            "decision_role": "posterior predictive action effects",
            "initial_value": grammar["local_nuisance"]["public_prior"],
            "candidate_access": True,
            "evidence": [functions["new_reference_state"], functions["reset_for_world"], functions["update_after_transition"]],
        },
        {
            "field": "update_count",
            "serialized_state_field": "update_count",
            "candidate_representation": "integer in JSON state",
            "source_class": "public_feedback_event_count",
            "formed_from_public_history": True,
            "persistence_scope": "slow_cross_world_metadata",
            "decision_role": "receipt_only_not_planner_input",
            "initial_value": 0,
            "trained_value": training["candidate_state_receipt"]["update_count"],
            "candidate_access": True,
            "evidence": [functions["new_reference_state"], functions["update_after_transition"]],
        },
        {
            "field": "world_update_count",
            "serialized_state_field": "world_update_count",
            "candidate_representation": "integer in JSON state",
            "source_class": "current_world_public_feedback_event_count",
            "formed_from_public_history": True,
            "persistence_scope": "fast_current_world_metadata",
            "decision_role": "receipt_only_not_planner_input",
            "initial_value": 0,
            "reset_value": 0,
            "candidate_access": True,
            "evidence": [functions["new_reference_state"], functions["reset_for_world"], functions["update_after_transition"]],
        },
        {
            "field": "public_history_hash",
            "serialized_state_field": "public_history_hash",
            "candidate_representation": "hash chain over public action/features/feedback",
            "source_class": "current_world_public_history_receipt",
            "formed_from_public_history": True,
            "persistence_scope": "fast_current_world_metadata",
            "decision_role": "receipt_only_not_planner_input",
            "reset_value": "canonical hash of empty history",
            "candidate_access": True,
            "evidence": [functions["new_reference_state"], functions["reset_for_world"], functions["update_after_transition"]],
        },
        {
            "field": "shared_prior_initialization",
            "candidate_representation": "uniform probability over all 40 public-family hypotheses",
            "source_class": "fixed_generic_prior",
            "formed_from_public_history": False,
            "persistence_scope": "initialization_only",
            "decision_role": "uninformative starting mass",
            "contains_realized_answer": False,
            "candidate_access": True,
            "evidence": functions["new_reference_state"],
        },
        {
            "field": "shared_mechanism_hypothesis_family",
            "candidate_representation": "40 fixed weight-pair hypotheses",
            "source_class": "benchmark_grammar_hardcoded",
            "formed_from_public_history": False,
            "persistence_scope": "fixed_model_class",
            "decision_role": "defines exact posterior support",
            "contains_realized_answer": False,
            "guarantees_realized_answer_is_in_support": True,
            "candidate_access": True,
            "evidence": {
                "path": str(REFERENCE_RELATIVE).replace("\\", "/"),
                "file_sha256": sha256(root / REFERENCE_RELATIVE),
                "hypothesis_count": grammar["shared_mechanism_family"]["hypothesis_count"],
            },
        },
        {
            "field": "likelihood_noise_effect_scales_and_planner_constants",
            "candidate_representation": "fixed exact model and homeostatic planning constants",
            "source_class": "benchmark_grammar_hardcoded",
            "formed_from_public_history": False,
            "persistence_scope": "fixed_model_and_planner",
            "decision_role": "exact likelihood and fixed homeostatic action ranking",
            "contains_realized_answer": False,
            "candidate_access": True,
            "evidence": {
                "effect_model": grammar["effect_model"],
                "organism": grammar["organism"],
                "planner": grammar["planner"],
            },
        },
        {
            "field": "realized_shared_mechanism_index",
            "candidate_representation": None,
            "source_class": "evaluator_private_assignment",
            "formed_from_public_history": False,
            "persistence_scope": "evaluator_only",
            "decision_role": "diagnostic_scoring_only",
            "candidate_access": False,
            "evaluator_value": grammar["shared_mechanism_family"]["evaluator_actual_index"],
            "evidence": {
                "path": str(RUNNER_RELATIVE).replace("\\", "/"),
                "runner_file_sha256": sha256(root / RUNNER_RELATIVE),
            },
        },
        {
            "field": "world_seed_local_mode_packet_split_and_opaque_world",
            "candidate_representation": None,
            "source_class": "evaluator_private_assignment",
            "formed_from_public_history": False,
            "persistence_scope": "evaluator_only",
            "decision_role": "packet_execution_and_scoring_only",
            "candidate_access": False,
            "evidence": {
                "private_field_positive_controls_rejected": training[
                    "candidate_private_field_rejections"
                ],
                "packet_assignment_sha256": sha256(artifacts / "packet_assignments.json"),
            },
        },
    ]
    candidate_private = any(
        row["source_class"] == "evaluator_private_assignment" and row["candidate_access"]
        for row in fields
    )
    serialized_coverage = {
        str(row["serialized_state_field"])
        for row in fields
        if row.get("serialized_state_field") is not None
    }
    return {
        "task_id": TASK_ID,
        "fields": fields,
        "candidate_state_contains_private_assignment": candidate_private,
        "serialized_reference_state_fields": sorted(SERIALIZED_REFERENCE_STATE_FIELDS),
        "serialized_state_field_coverage": sorted(serialized_coverage),
        "all_serialized_state_fields_classified": serialized_coverage
        == SERIALIZED_REFERENCE_STATE_FIELDS,
        "slow_information_summary": (
            "Only the shared marginal of joint is transferable decision information, and it is learned "
            "from public cross-world histories. The nuisance conditional and its counters/receipt are "
            "current-world state. The exact finite family, likelihood, local-mode prior, effect scales, "
            "and planner are fixed benchmark grammar. The uniform shared prior is generic. The realized "
            "mechanism and packet/world assignments remain evaluator-only."
        ),
        "pass": not candidate_private and serialized_coverage == SERIALIZED_REFERENCE_STATE_FIELDS,
    }


def audit_online_learning(root: Path = ROOT) -> dict[str, Any]:
    artifacts = predecessor_root(root)
    training = load_json(artifacts / "training_public_history_receipt.json")
    qualification = load_json(artifacts / "qualification_result.json")["summary"]
    replication = load_json(artifacts / "replication_result.json")["summary"]
    initial_probability = 1.0 / 40.0
    trained_probability = float(training["shared_probability_at_evaluator_truth"])
    shuffled_probability = float(training["history_shuffle_shared_probability_at_evaluator_truth"])
    reset_source = _source(root, REFERENCE_RELATIVE)
    reset_segment = _function_evidence(root, REFERENCE_RELATIVE, ("reset_for_world",))[
        "reset_for_world"
    ]
    slow_reset_damage = all(
        float(packet["transfer_gain"]) > 0.0
        and int(packet["positive_worlds"]) >= 12
        for packet in (qualification, replication)
    )
    shuffle_damage = all(
        float(packet["controls"]["HISTORY_SHUFFLE"]["gain_removal_fraction"])
        >= 0.5
        for packet in (qualification, replication)
    )
    checks = {
        "generic_initialization": math.isclose(initial_probability, 0.025),
        "public_feedback_updates_applied": training["candidate_state_receipt"]["update_count"]
        == training["public_events"]
        == 768,
        "shared_truth_probability_moved_from_generic": trained_probability > 0.999,
        "shared_entropy_reduced": float(training["shared_entropy_bits"]) < 0.01,
        "world_reset_preserves_shared_marginal": "shared_marginal(state) if preserve_shared else None"
        in reset_source,
        "slow_reset_breaks_transfer": slow_reset_damage,
        "history_shuffle_blocks_slow_knowledge": shuffled_probability < initial_probability
        and shuffle_damage,
    }
    return {
        "task_id": TASK_ID,
        "initial_shared_truth_probability": initial_probability,
        "trained_shared_truth_probability": trained_probability,
        "trained_shared_entropy_bits": training["shared_entropy_bits"],
        "public_feedback_update_count": training["candidate_state_receipt"]["update_count"],
        "public_training_events": training["public_events"],
        "history_shuffle_shared_truth_probability": shuffled_probability,
        "feedback_attribution_shuffle_operationalization": (
            "Frozen HISTORY_SHUFFLE feeds the previous public observation/features with the current action and "
            "feedback, breaking feature-to-feedback attribution. It is not a separate arbitrary permutation of "
            "feedback rows."
        ),
        "literal_feedback_row_permutation_run_by_001p": False,
        "world_reset_preserves_shared_marginal": checks[
            "world_reset_preserves_shared_marginal"
        ],
        "world_reset_evidence": reset_segment,
        "slow_reset_operationalization": "SCRATCH_EXACT_BAYES starts the same exact architecture at uniform shared mass",
        "slow_reset_breaks_transfer": slow_reset_damage,
        "slow_reset_packet_effects": {
            "qualification": {
                "transfer_early_deficit_auc": qualification["metrics"]["TRANSFER_EXACT_HIERARCHICAL_BAYES"]["mean_early_deficit_auc"],
                "slow_reset_early_deficit_auc": qualification["metrics"]["SCRATCH_EXACT_BAYES"]["mean_early_deficit_auc"],
                "damage": qualification["transfer_gain"],
                "recovery_fraction_lost": qualification["recovery_fraction"],
            },
            "replication": {
                "transfer_early_deficit_auc": replication["metrics"]["TRANSFER_EXACT_HIERARCHICAL_BAYES"]["mean_early_deficit_auc"],
                "slow_reset_early_deficit_auc": replication["metrics"]["SCRATCH_EXACT_BAYES"]["mean_early_deficit_auc"],
                "damage": replication["transfer_gain"],
                "recovery_fraction_lost": replication["recovery_fraction"],
            },
        },
        "history_shuffle_blocks_slow_knowledge": checks[
            "history_shuffle_blocks_slow_knowledge"
        ],
        "qualification_transfer_gain": qualification["transfer_gain"],
        "replication_transfer_gain": replication["transfer_gain"],
        "qualification_history_shuffle_gain_removal_fraction": qualification["controls"][
            "HISTORY_SHUFFLE"
        ]["gain_removal_fraction"],
        "replication_history_shuffle_gain_removal_fraction": replication["controls"][
            "HISTORY_SHUFFLE"
        ]["gain_removal_fraction"],
        "checks": checks,
        "pass": all(checks.values()),
    }


def audit_function_knowledge(root: Path = ROOT) -> dict[str, Any]:
    reference_source = _source(root, REFERENCE_RELATIVE)
    runner_source = _source(root, RUNNER_RELATIVE)
    reachable = _reachable_symbols(
        root,
        REFERENCE_RELATIVE,
        ("new_reference_state", "plan_action", "update_after_transition", "reset_for_world"),
    )
    private_symbols = {
        "ACTUAL_MECHANISM_INDEX",
        "evaluator_seed",
        "opaque_world",
        "packet_name",
        "private_aligned_reference_state",
        "symbolic_capacity_audit",
    }
    reachable_private = sorted(private_symbols & set(reachable["loaded_symbols"]))
    task_local_diagnostic_truth = "mechanism = MECHANISMS[17]" in reference_source
    transfer_branch_uses_trained_state = (
        'else:\n        state = copy.deepcopy(trained_state)' in runner_source
    )
    private_alignment_is_arm_guarded = (
        'if arm in ("PRIVATE_ORACLE", "PRIVATE_ALIGNED_REFERENCE")' in runner_source
        and "reference.private_aligned_reference_state" in runner_source
    )
    generic_prior = "global_prior = [1.0 / len(MECHANISMS)] * len(MECHANISMS)" in reference_source
    realized_prefilled = bool(reachable_private or not generic_prior or not transfer_branch_uses_trained_state)
    route = "B" if realized_prefilled else "A"
    classification = (
        "STRUCTURED_CAPACITY_UPPER_BOUND_WITH_PREFILLED_REALIZED_FUNCTION"
        if realized_prefilled
        else "LEGAL_PUBLIC_MODEL_BASED_LEARNER_AND_STRUCTURED_CAPACITY_UPPER_BOUND"
    )
    return {
        "task_id": TASK_ID,
        "realized_function_prefilled": realized_prefilled,
        "correct_finite_hypothesis_family_hardcoded": True,
        "exact_likelihood_hardcoded": True,
        "generic_shared_prior": generic_prior,
        "transfer_arm_uses_publicly_trained_state": transfer_branch_uses_trained_state,
        "private_aligned_constructor_is_diagnostic_arm_only": private_alignment_is_arm_guarded,
        "candidate_plan_update_reachable_private_symbols": reachable_private,
        "candidate_reachable_call_graph": reachable,
        "task_local_file_contains_evaluator_diagnostic_truth": task_local_diagnostic_truth,
        "direct_product_import_allowed": False,
        "direct_product_import_reason": (
            "The task-local file also contains split constants, private diagnostic constructors, and a "
            "symbolic audit fixed to mechanism 17 even though none is reachable from the transfer plan/update path."
        ),
        "classification": classification,
        "route": route,
        "classification_reason": (
            "It learns which shared hypothesis and current nuisance explain public feedback, while also "
            "remaining an upper bound for the strong assumption that the correct finite family and exact likelihood "
            "are known."
            if not realized_prefilled
            else "A realized shared function or equivalent private assignment is reachable from candidate behavior."
        ),
    }


def audit_runtime_admissibility(root: Path = ROOT) -> dict[str, Any]:
    reference_actions = tuple(_literal_assignment(root, REFERENCE_RELATIVE, "ACTIONS"))
    product_actions = tuple(_literal_assignment(root, MICROWORLD_RELATIVE, "ACTIONS"))
    reference_source = _source(root, REFERENCE_RELATIVE)
    product_world_source = _source(root, MICROWORLD_RELATIVE)
    engine_source = _source(root, ENGINE_RELATIVE)
    controller_source = _source(root, CONTROLLER_RELATIVE)
    store_source = _source(root, STORE_RELATIVE)
    product_observation = {
        "schema": _literal_assignment(root, MICROWORLD_RELATIVE, "PUBLIC_OBSERVATION_SCHEMA_VERSION"),
        "fields": ["schema_version", "visual"],
        "visual_shape": "3x5 token grid",
    }
    reference_observation = {
        "fields": ["organism", "slots", "previous"],
        "slot_count": _literal_assignment(root, REFERENCE_RELATIVE, "SLOT_COUNT"),
        "slot_fields": ["features"],
        "feature_count": _literal_assignment(root, REFERENCE_RELATIVE, "FEATURE_COUNT"),
    }
    module_in_engine = "public_featured_transfer" in engine_source
    observation_match = product_observation["fields"] == reference_observation["fields"]
    action_match = product_actions == reference_actions
    replay_pattern = all(
        text in store_source
        for text in (
            "recompute before reading the stored trace row",
            "stored trace differs from independent recomputation",
            "state = recomputed.next_state",
        )
    ) and "compute_step(self.state, command, self.run_meta)" in controller_source
    controller_dispatches_engine_then_store = all(
        token in controller_source
        for token in (
            "compute_step(self.state, command, self.run_meta)",
            "self.store.append_step(command, computed.trace)",
        )
    )
    engine_runs_metabolism_then_terminal = all(
        token in engine_source
        for token in (
            "metabolism = compute_metabolism_ledger(",
            'if next_state["organism"]["energy"] == 0.0:',
            '"trial_status": "terminal"',
        )
    )
    store_recomputes_before_trace_read = all(
        token in store_source
        for token in (
            "recomputed = self._compute_step(state, command, run_meta)",
            "Build the candidate frame from recomputation before consulting",
            'stored_trace = _decode_json(trace_row["trace_json"], "trace")',
        )
    )
    evaluator_required = (
        not module_in_engine
        and "make_public_observation" in _source(root, RUNNER_RELATIVE)
        and "_execute_evaluator_transition" in _source(root, RUNNER_RELATIVE)
    )
    current_admissible = bool(
        replay_pattern
        and controller_dispatches_engine_then_store
        and engine_runs_metabolism_then_terminal
        and store_recomputes_before_trace_read
        and module_in_engine
        and observation_match
        and action_match
        and not evaluator_required
    )
    return {
        "task_id": TASK_ID,
        "controller_store_replay_pattern_compatible": replay_pattern,
        "stored_trace_is_behavior_input": False,
        "current_main_chain": {
            "controller_dispatches_engine_then_store": controller_dispatches_engine_then_store,
            "engine_runs_metabolism_then_terminal": engine_runs_metabolism_then_terminal,
            "store_recomputes_before_trace_read": store_recomputes_before_trace_read,
            "path": "controller.dispatch -> engine.compute_step -> compute_metabolism_ledger -> inline terminal check -> store.append_step/recover_run",
        },
        "public_featured_module_in_engine_code_path": module_in_engine,
        "current_product_observation_contract": product_observation,
        "frozen_reference_observation_contract": reference_observation,
        "observation_contract_match": observation_match,
        "current_product_actions": list(product_actions),
        "frozen_reference_actions": list(reference_actions),
        "action_contract_match": action_match,
        "metabolism_terminal_contract_match": False,
        "metabolism_terminal_mismatch": (
            "Frozen 001O applies featured stochastic energy/safety deltas and terminates when either reaches zero; "
            "the current product reducer uses its visual-grid metabolism and terminates a life on energy zero."
        ),
        "evaluator_wrapper_currently_required": evaluator_required,
        "current_product_feature_source": "anonymous visual token identity only; no legal five-bit public factor vector",
        "unsafe_adapter_rejected": (
            "Deriving featured factors from token identity or packet/private assignment would violate the "
            "frozen candidate-input contract and manufacture a second truth source."
        ),
        "currently_product_admissible": current_admissible,
        "blocker": "EXPLICIT_PRODUCT_OBSERVATION_ACTION_SEMANTICS_AUTHORIZATION_REQUIRED",
        "minimum_authorized_successor": (
            "A new default-off product mode that reuses the frozen 001O feature-slot and positional-interaction "
            "contract, extracts a clean runtime-only learner without diagnostic truth, and wires it into the "
            "sole reducer/metabolism/terminal/store replay path."
        ),
        "product_files_modified_by_audit": False,
    }


def build_audit(root: Path = ROOT) -> dict[str, Any]:
    frozen = verify_frozen_predecessor(root)
    provenance = audit_slow_information_provenance(root)
    online = audit_online_learning(root)
    knowledge = audit_function_knowledge(root)
    runtime = audit_runtime_admissibility(root)
    route_a = bool(
        frozen["pass"]
        and provenance["pass"]
        and online["pass"]
        and knowledge["route"] == "A"
        and not knowledge["realized_function_prefilled"]
    )
    decision = (
        "ROUTE_A_LEARNER_PRODUCT_SEMANTICS_AUTHORIZATION_REQUIRED"
        if route_a and not runtime["currently_product_admissible"]
        else "ROUTE_A_PRODUCT_IMPLEMENTATION_ADMISSIBLE"
        if route_a
        else "ROUTE_B_MINIMAL_LEARNED_HIERARCHICAL_CANDIDATE_REQUIRED"
    )
    return {
        "task_id": TASK_ID,
        "frozen_predecessor": frozen,
        "reference_route": "A" if route_a else "B",
        "reference_is_learner": route_a,
        "reference_is_structured_upper_bound": knowledge[
            "correct_finite_hypothesis_family_hardcoded"
        ]
        and knowledge["exact_likelihood_hardcoded"],
        "reference_classification": knowledge["classification"],
        "product_admissible_current_chain": runtime["currently_product_admissible"],
        "product_implementation_started": False,
        "decision": decision,
        "why": [
            "The shared posterior starts uniform and public feedback moves evaluator-diagnostic truth mass from 0.025 to above 0.999.",
            "World reset preserves only the learned shared marginal and restores the fixed benchmark current-world nuisance prior.",
            "Scratch exact Bayes and shuffled history remove the transfer benefit; the realized assignment is not reachable from candidate plan/update.",
            "The correct finite family and exact likelihood are hardcoded, so the learner remains a structured capacity upper bound outside that modeling assumption.",
            "The existing product observation/action/metabolism/terminal contract does not match frozen 001O feature slots, positional interactions, and energy-safety transition contract.",
        ],
        "next_action": runtime["minimum_authorized_successor"],
        "claim_ceiling": (
            "Frozen 001O is a legal public model-based learner within a known exact finite family, while also "
            "serving as a structured capacity upper bound. It is not currently a product-main-chain capability."
        ),
        "what_this_does_not_prove": [
            "product runtime transfer",
            "learning outside the frozen hypothesis family",
            "general compositional transfer",
            "neural learning",
            "consciousness",
            "agency",
            "real-world survival ability",
        ],
    }


def run_audit(root: Path = ROOT) -> dict[str, Any]:
    output = artifact_root(root)
    frozen = verify_frozen_predecessor(root)
    provenance = audit_slow_information_provenance(root)
    online = audit_online_learning(root)
    knowledge = audit_function_knowledge(root)
    runtime = audit_runtime_admissibility(root)
    report = build_audit(root)
    write_json(output / "protected_predecessor_receipt.json", frozen)
    write_json(output / "slow_information_provenance.json", provenance)
    write_json(output / "online_learning_audit.json", online)
    write_json(output / "function_knowledge_audit.json", knowledge)
    write_json(output / "runtime_admissibility_audit.json", runtime)
    write_json(output / "audit_report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    report = run_audit(args.root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
