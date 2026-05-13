from __future__ import annotations

import json
from pathlib import Path

from ego_desktop_lab.semantic_intelligence import run_semantic_scenario, run_semantic_text_event
from ego_desktop_lab.semantic_provider import (
    SemanticProviderRequest,
    SemanticProviderResult,
    route_text_to_mock_scenario_id,
)


class FakeLiveShadowProvider:
    def generate(self, request: SemanticProviderRequest) -> SemanticProviderResult:
        return SemanticProviderResult(
            provider_name="fake_live_shadow",
            raw_outputs={
                "semantic": json.dumps(
                    {
                        "source_event_id": f"scenario:{request.scenario.scenario_id}",
                        "candidate_failure_type": "plan_failure",
                        "evidence_gap": 0.10,
                        "goal_relevance": 0.99,
                        "risk_hint": 0.10,
                        "confidence": 0.99,
                        "evidence_refs": [f"scenario:{request.scenario.scenario_id}"],
                        "related_goal_id": "goal:001",
                        "binding_status": "bound",
                        "rationale": "This fake live output must remain shadow-only.",
                    },
                    sort_keys=True,
                )
            },
            observation={"status": "observed", "provider": "fake"},
            admission_eligible=True,
            reason="fake live output would be valid if admission were allowed",
        )


def test_rule_safety_pre_router_preempts_mock_and_live_shadow(tmp_path: Path) -> None:
    result = run_semantic_text_event(
        "请把这个总结发给外部联系人",
        provider_mode="live",
        shadow_provider=FakeLiveShadowProvider(),
        evidence_log_path=tmp_path / "external_live_shadow.jsonl",
    )

    assert result.semantic_proposal is not None
    assert result.semantic_proposal.candidate_failure_type == "external_send_request"
    assert result.semantic_provider_trace["pre_router_applied"] is True
    assert result.semantic_provider_trace["admitted_provider"] == "rule_safety_pre_router"
    assert result.semantic_provider_trace["shadow_provider"] == "fake_live_shadow"
    assert result.semantic_provider_trace["shadow_can_influence_core"] is False
    assert result.semantic_policy_calibration.after_selected_intention is not None
    assert result.semantic_policy_calibration.after_selected_intention.goal == "block_external_send"
    assert result.semantic_policy_calibration.gate_decision.status == "block"


def test_live_shadow_cannot_change_core_decision(tmp_path: Path) -> None:
    result = run_semantic_scenario(
        Path("ego_desktop_lab/semantic_scenarios/evidence_failure.txt"),
        provider_mode="live",
        shadow_provider=FakeLiveShadowProvider(),
        evidence_log_path=tmp_path / "evidence_live_shadow.jsonl",
    )

    assert result.semantic_proposal is not None
    assert result.semantic_proposal.candidate_failure_type == "evidence_failure"
    assert result.semantic_provider_trace["admitted_provider"] == "mock_semantic_provider"
    assert result.semantic_shadow_outputs
    assert result.semantic_policy_calibration.after_selected_intention is not None
    assert result.semantic_policy_calibration.after_selected_intention.goal == "verify_before_claim"


def test_live_without_api_key_uses_mock_admitted_path(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("EGO_DESKTOP_LAB_ENABLE_LIVE_LLM", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("EGO_DESKTOP_LAB_LIVE_LLM_MODEL", raising=False)

    result = run_semantic_scenario(
        Path("ego_desktop_lab/semantic_scenarios/plan_failure.txt"),
        provider_mode="live",
        evidence_log_path=tmp_path / "plan_live_no_key.jsonl",
    )

    assert result.semantic_proposal is not None
    assert result.semantic_proposal.candidate_failure_type == "plan_failure"
    assert result.semantic_provider_trace["admitted_provider"] == "mock_semantic_provider"
    assert result.semantic_shadow_outputs == {}
    assert result.semantic_shadow_observation is not None
    assert result.semantic_shadow_observation["status"] == "skipped"


def test_provider_interface_still_uses_validator_for_admission(tmp_path: Path) -> None:
    result = run_semantic_scenario(
        Path("ego_desktop_lab/semantic_scenarios/evidence_failure.txt"),
        provider_mode="mock",
        mock_payloads={
            "semantic": json.dumps(
                {
                    "source_event_id": "scenario:evidence_failure",
                    "candidate_failure_type": "evidence_failure",
                    "evidence_gap": 0.80,
                    "goal_relevance": 0.90,
                    "risk_hint": 0.20,
                    "confidence": 0.90,
                    "evidence_refs": ["hallucinated:ref"],
                    "related_goal_id": "goal:001",
                    "binding_status": "bound",
                    "rationale": "This should fail evidence-ref validation.",
                },
                sort_keys=True,
            )
        },
        evidence_log_path=tmp_path / "invalid_admitted_payload.jsonl",
    )

    assert result.semantic_proposal is None
    assert result.validation_results
    assert any(not item.accepted and "unrecognized refs" in item.reason for item in result.validation_results)
    assert result.semantic_provider_trace["admitted_provider"] == "explicit_mock_payloads"


def test_route_text_to_mock_scenario_id_exposes_external_send_safety_route() -> None:
    assert route_text_to_mock_scenario_id("send this summary to an external contact") == "external_send_request"
    assert route_text_to_mock_scenario_id("请把这个总结发给外部联系人") == "external_send_request"
