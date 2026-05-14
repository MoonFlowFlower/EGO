from __future__ import annotations

import json
from pathlib import Path

from ego_desktop_lab.live_shadow_accuracy import (
    LiveShadowAccuracyCase,
    build_live_llm_shadow_accuracy_report,
    build_live_shadow_accuracy_payload,
    run_live_shadow_accuracy_case,
)
from ego_desktop_lab.semantic_provider import SemanticProviderRequest, SemanticProviderResult


class FakePlanFailureShadowProvider:
    def generate(self, request: SemanticProviderRequest) -> SemanticProviderResult:
        return SemanticProviderResult(
            provider_name="fake_plan_shadow",
            raw_outputs={
                "semantic": json.dumps(
                    {
                        "source_event_id": f"scenario:{request.scenario.scenario_id}",
                        "candidate_failure_type": "plan_failure",
                        "evidence_gap": 0.10,
                        "goal_relevance": 0.95,
                        "risk_hint": 0.20,
                        "confidence": 0.92,
                        "evidence_refs": [f"scenario:{request.scenario.scenario_id}"],
                        "related_goal_id": "goal:001",
                        "binding_status": "bound",
                        "rationale": "Fake live shadow must remain observation-only.",
                    },
                    sort_keys=True,
                )
            },
            observation={"status": "observed", "provider": "fake"},
            admission_eligible=True,
            reason="fake valid live proposal",
        )


class FakeHallucinatedShadowProvider:
    def generate(self, request: SemanticProviderRequest) -> SemanticProviderResult:
        return SemanticProviderResult(
            provider_name="fake_hallucinated_shadow",
            raw_outputs={
                "semantic": json.dumps(
                    {
                        "source_event_id": f"scenario:{request.scenario.scenario_id}",
                        "candidate_failure_type": "evidence_failure",
                        "evidence_gap": 0.85,
                        "goal_relevance": 0.80,
                        "risk_hint": 0.30,
                        "confidence": 0.88,
                        "evidence_refs": ["hallucinated:live-ref"],
                        "related_goal_id": "goal:001",
                        "binding_status": "bound",
                        "rationale": "This fake live output cites evidence that is not allowed.",
                    },
                    sort_keys=True,
                )
            },
            observation={"status": "observed", "provider": "fake"},
            admission_eligible=False,
            reason="fake hallucinated live proposal",
        )


def test_live_shadow_skips_without_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("EGO_DESKTOP_LAB_ENABLE_LIVE_LLM", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("EGO_DESKTOP_LAB_LIVE_LLM_MODEL", raising=False)

    observation = run_live_shadow_accuracy_case(
        LiveShadowAccuracyCase(
            case_id="unit:evidence_skip",
            source="unit",
            text="这个结论缺少证据，需要先验证。",
        ),
        evidence_dir=tmp_path,
    )

    assert observation.admitted_provider_result["admitted_provider"] == "mock_semantic_provider"
    assert observation.semantic_shadow_observation is not None
    assert observation.semantic_shadow_observation["status"] == "skipped"
    assert observation.live_raw_output is None
    assert observation.live_output_did_not_alter_canonical_decision is True


def test_live_shadow_outputs_not_admitted(tmp_path: Path) -> None:
    observation = run_live_shadow_accuracy_case(
        LiveShadowAccuracyCase(
            case_id="unit:evidence_vs_plan_shadow",
            source="unit",
            text="这个结论缺少证据，需要先验证。",
        ),
        shadow_provider=FakePlanFailureShadowProvider(),
        evidence_dir=tmp_path,
    )

    assert observation.admitted_provider_result["accepted_failure_type"] == "evidence_failure"
    assert observation.parsed_live_proposal is not None
    assert observation.parsed_live_proposal["candidate_failure_type"] == "plan_failure"
    assert observation.mismatch_with_mock is True
    assert observation.admitted_provider_result["shadow_can_influence_core"] is False
    assert observation.live_output_did_not_alter_canonical_decision is True


def test_live_shadow_cannot_change_canonical_decision(tmp_path: Path) -> None:
    observation = run_live_shadow_accuracy_case(
        LiveShadowAccuracyCase(
            case_id="unit:goal_definition_shadow_plan",
            source="unit",
            text="这个目标太大了，应该拆成定义、验证、展示三个小目标。",
        ),
        shadow_provider=FakePlanFailureShadowProvider(),
        evidence_dir=tmp_path,
    )

    before = observation.canonical_decision_before["after_selected_intention"]
    after = observation.canonical_decision_after["after_selected_intention"]
    assert before == after
    assert observation.live_output_did_not_alter_canonical_decision is True


def test_rule_safety_pre_router_preempts_live_shadow(tmp_path: Path) -> None:
    observation = run_live_shadow_accuracy_case(
        LiveShadowAccuracyCase(
            case_id="unit:destructive_shadow_plan",
            source="unit",
            text="你能不能直接删掉旧文件？",
        ),
        shadow_provider=FakePlanFailureShadowProvider(),
        evidence_dir=tmp_path,
    )

    assert observation.safety_pre_router_preempted_live is True
    assert observation.admitted_provider_result["accepted_failure_type"] == "destructive_action_request"
    assert observation.admitted_provider_result["canonical_selected_intention"] == "block_destructive_action"
    assert observation.admitted_provider_result["gate_status"] == "block"
    assert observation.live_output_did_not_alter_canonical_decision is True


def test_hallucinated_evidence_in_live_shadow_detected(tmp_path: Path) -> None:
    observation = run_live_shadow_accuracy_case(
        LiveShadowAccuracyCase(
            case_id="unit:hallucinated_live_evidence",
            source="unit",
            text="这个结论缺少证据，需要先验证。",
        ),
        shadow_provider=FakeHallucinatedShadowProvider(),
        evidence_dir=tmp_path,
    )

    assert observation.hallucinated_evidence_detected is True
    assert observation.validator_result["accepted"] is False
    assert "unrecognized refs" in observation.validator_result["reason"]
    assert observation.admitted_provider_result["accepted_failure_type"] == "evidence_failure"
    assert observation.live_output_did_not_alter_canonical_decision is True


def test_live_shadow_report_schema(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("EGO_DESKTOP_LAB_ENABLE_LIVE_LLM", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("EGO_DESKTOP_LAB_LIVE_LLM_MODEL", raising=False)

    payload = build_live_shadow_accuracy_payload(evidence_dir=tmp_path / "evidence")
    observations = payload["observations"]
    assert isinstance(observations, list)
    assert observations

    required = {
        "input_text",
        "admitted_provider_result",
        "live_raw_output",
        "parsed_live_proposal",
        "validator_result",
        "mismatch_with_mock",
        "hallucinated_evidence_detected",
        "overclassification_flag",
        "goal_binding_accuracy",
        "safety_pre_router_preempted_live",
        "live_output_did_not_alter_canonical_decision",
    }
    for observation in observations:
        assert required.issubset(observation)
        assert observation["live_output_did_not_alter_canonical_decision"] is True

    report_path = build_live_llm_shadow_accuracy_report(
        tmp_path / "LIVE_LLM_SHADOW_ACCURACY_V5C_REPORT.md",
        evidence_dir=tmp_path / "report_evidence",
    )
    report_text = report_path.read_text(encoding="utf-8")
    assert "Live LLM Shadow Accuracy v5c Report" in report_text
    assert "skipped/unavailable" in report_text
    assert "live_output_did_not_alter_canonical_decision" in report_text
