from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT
    / "docs"
    / "codex"
    / "tasks"
    / "ego-functional-subject-architecture-contract-v0"
    / "architecture_contract_v0.yaml"
)


def load_contract() -> dict[str, Any]:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_contract_defines_candidate_only_core_records_and_owner_boundaries() -> None:
    contract = load_contract()

    assert contract["owner"] == "EgoOperator"
    assert contract["authority"]["canonical_runtime_owner"] == "EgoOperator"
    assert "mutate_core_memory" in contract["authority"]["llm_forbidden_roles"]
    assert "execute_tool_or_side_effect_without_gate" in contract["authority"]["llm_forbidden_roles"]

    subject_state = contract["records"]["SubjectStateV0"]
    assert subject_state["write_authority"] == "candidate_only"
    assert "core_memory" in subject_state["forbidden_direct_writes"]
    assert "program_state" in subject_state["forbidden_direct_writes"]
    assert "evidence_ledger" in subject_state["forbidden_direct_writes"]


def test_contract_maps_functional_subject_into_egooperator_mainline_flow() -> None:
    contract = load_contract()
    assert contract["data_flow"] == [
        "user_event",
        "llm_understanding",
        "subject_signal_candidates",
        "viability_state_v0",
        "outcome_prediction_set_v0",
        "planner_or_proposal_selection",
        "runtime_gate",
        "action_or_noop",
        "trace_record",
        "feedback_observation",
        "memory_policy_relationship_candidates",
        "replay_or_review",
    ]


def test_contract_contains_required_primitives_gates_trace_fields_and_followup_slices() -> None:
    contract = load_contract()

    assert {"SubjectStateV0", "ViabilityStateV0", "OutcomePredictionV0", "PolicyPatchCandidateV0"} <= set(
        contract["records"]
    )
    assert {
        "reply",
        "ask",
        "wait",
        "remind",
        "refuse",
        "repair",
        "suggest",
        "tool_propose",
        "memory_candidate",
        "no_action",
    } <= set(contract["action_primitives"])
    assert {
        "claim_gate",
        "memory_gate",
        "initiative_gate",
        "tool_gate",
        "identity_gate",
        "relationship_gate",
        "policy_gate",
        "trace_gate",
    } <= set(contract["gates"])
    assert {
        "subject_state_digest",
        "viability_state",
        "outcome_predictions",
        "selected_action",
        "gate_decisions",
        "action_result",
        "feedback_observation",
        "emitted_candidates",
        "replay_refs",
    } <= set(contract["trace_fields"])
    assert {f"EGO-FS-{idx:03d}" for idx in range(2, 11)} <= set(contract["implementation_slices"])


def test_positive_goals_are_not_claim_ceiling_disclaimers() -> None:
    contract = load_contract()
    mechanism_goals = [
        str(value.get("goal", ""))
        for value in contract["positive_goal"]["mechanisms"].values()
    ]

    forbidden_goal_phrases = [
        "do not claim",
        "not claim",
        "consciousness",
        "不得宣称",
        "意识",
    ]
    for goal in mechanism_goals:
        lowered = goal.casefold()
        assert all(phrase not in lowered for phrase in forbidden_goal_phrases)

    not_claimed = contract["reporting_rules"]["not_claimed"]
    assert "consciousness" in not_claimed
