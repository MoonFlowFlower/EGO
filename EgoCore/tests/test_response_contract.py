from app.response_contract import build_status_response_plan, evaluate_memory_claim
from app.restore_runtime import PendingRestoreObservation
from app.runtime_v2.state import RuntimeV2State


def test_memory_claim_gate_blocks_without_restore_authority() -> None:
    verdict = evaluate_memory_claim("我已经恢复成功，还记得你。")
    assert verdict.claim_detected is True
    assert verdict.allowed is False
    assert verdict.reason == "missing_restore_authority"


def test_memory_claim_gate_allows_with_restore_authority() -> None:
    observation = PendingRestoreObservation(
        restore_id="r1",
        restore_status="success",
        loaded_layers=["identity"],
        degraded_mode=False,
        degradation_reason=None,
        restore_timestamp="2026-03-31T08:00:00Z",
    )
    verdict = evaluate_memory_claim("我已经恢复成功，还记得你。", restore_observation=observation)
    assert verdict.claim_detected is True
    assert verdict.allowed is True
    assert verdict.authority_source == "restore_audit"


def test_build_status_response_plan_wraps_runtime_reply_and_verdict() -> None:
    state = RuntimeV2State(session_id="s", current_goal="整理任务", current_step="检查状态")
    observation = PendingRestoreObservation(
        restore_id="r1",
        restore_status="success",
        loaded_layers=["identity"],
        degraded_mode=False,
        degradation_reason=None,
        restore_timestamp="2026-03-31T08:00:00Z",
    )
    plan = build_status_response_plan(
        "status",
        state,
        assume_active=True,
        restore_observation=observation,
    )
    assert plan.kind == "status_probe"
    assert plan.delivery_kind == "final"
    assert "当前步骤" in plan.reply_text
    assert plan.memory_claim_verdict is not None
    assert plan.memory_claim_verdict.allowed is True
