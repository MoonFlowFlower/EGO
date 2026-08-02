from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "codex" / "audit_ego_v2_reference_to_product_admissibility_001p.py"


def _load_subject():
    spec = importlib.util.spec_from_file_location("admissibility_001p", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_001o_bytes_and_packet_consumption_are_read_only_inputs() -> None:
    subject = _load_subject()
    result = subject.verify_frozen_predecessor(ROOT)
    assert result["pass"] is True
    assert result["verdict"] == "PUBLIC_FEATURED_EXACT_HIERARCHICAL_TRANSFER_CAPACITY_ESTABLISHED"
    assert result["qualification_consumed_once"] is True
    assert result["replication_consumed_once"] is True
    assert result["frozen_file_mismatches"] == []


def test_slow_information_provenance_separates_public_history_grammar_and_private() -> None:
    subject = _load_subject()
    provenance = subject.audit_slow_information_provenance(ROOT)
    by_field = {row["field"]: row for row in provenance["fields"]}
    assert by_field["shared_mechanism_posterior"]["formed_from_public_history"] is True
    assert by_field["shared_mechanism_posterior"]["persistence_scope"] == "slow_cross_world"
    assert by_field["current_world_nuisance_posterior"]["persistence_scope"] == "fast_current_world"
    assert by_field["public_history_hash"]["persistence_scope"] == "fast_current_world_metadata"
    assert by_field["shared_prior_initialization"]["source_class"] == "fixed_generic_prior"
    assert by_field["shared_mechanism_hypothesis_family"]["source_class"] == "benchmark_grammar_hardcoded"
    assert by_field["realized_shared_mechanism_index"]["source_class"] == "evaluator_private_assignment"
    assert by_field["realized_shared_mechanism_index"]["candidate_access"] is False
    assert provenance["candidate_state_contains_private_assignment"] is False
    assert provenance["all_serialized_state_fields_classified"] is True
    assert set(provenance["serialized_reference_state_fields"]) == {
        "joint",
        "update_count",
        "world_update_count",
        "public_history_hash",
    }


def test_reference_starts_generic_updates_online_and_ablations_break_slow_knowledge() -> None:
    subject = _load_subject()
    online = subject.audit_online_learning(ROOT)
    assert online["initial_shared_truth_probability"] == 0.025
    assert online["trained_shared_truth_probability"] > 0.999
    assert online["public_feedback_update_count"] == 768
    assert online["world_reset_preserves_shared_marginal"] is True
    assert online["slow_reset_breaks_transfer"] is True
    assert online["history_shuffle_blocks_slow_knowledge"] is True
    assert online["pass"] is True


def test_realized_function_is_not_prefilled_but_correct_family_is_hardcoded() -> None:
    subject = _load_subject()
    knowledge = subject.audit_function_knowledge(ROOT)
    assert knowledge["realized_function_prefilled"] is False
    assert knowledge["correct_finite_hypothesis_family_hardcoded"] is True
    assert knowledge["exact_likelihood_hardcoded"] is True
    assert knowledge["classification"] == "LEGAL_PUBLIC_MODEL_BASED_LEARNER_AND_STRUCTURED_CAPACITY_UPPER_BOUND"
    assert knowledge["route"] == "A"


def test_current_product_chain_cannot_express_frozen_featured_contract_without_semantic_change() -> None:
    subject = _load_subject()
    runtime = subject.audit_runtime_admissibility(ROOT)
    assert runtime["controller_store_replay_pattern_compatible"] is True
    assert all(runtime["current_main_chain"].values()) is True
    assert runtime["public_featured_module_in_engine_code_path"] is False
    assert runtime["observation_contract_match"] is False
    assert runtime["action_contract_match"] is False
    assert runtime["metabolism_terminal_contract_match"] is False
    assert runtime["evaluator_wrapper_currently_required"] is True
    assert runtime["currently_product_admissible"] is False
    assert runtime["blocker"] == "EXPLICIT_PRODUCT_OBSERVATION_ACTION_SEMANTICS_AUTHORIZATION_REQUIRED"


def test_automatic_decision_is_route_a_then_stop_at_authorization_boundary() -> None:
    subject = _load_subject()
    report = subject.build_audit(ROOT)
    assert report["reference_route"] == "A"
    assert report["reference_is_learner"] is True
    assert report["reference_is_structured_upper_bound"] is True
    assert report["product_implementation_started"] is False
    assert report["decision"] == "ROUTE_A_LEARNER_PRODUCT_SEMANTICS_AUTHORIZATION_REQUIRED"
