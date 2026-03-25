from app.runtime_v2 import RuntimeV2TelegramBridge
from app.runtime_v2.state import RuntimeV2State


def test_telegram_bridge_plans_pre_runtime_no_busy_notice():
    """短探针不再触发 busy notice"""
    bridge = RuntimeV2TelegramBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")
    state.task_status = "running"
    state.current_goal = "修改 hello.html 配色"
    decision = bridge.inspect_ingress("还在吗", state)
    action = bridge.plan_pre_runtime(decision, state)
    # 短探针不再返回 busy notice
    assert decision.absorb_as_busy_notice is False
    assert action.busy_notice_text is None
    assert action.ack_text is None


def test_telegram_bridge_plans_no_ack_for_task():
    """任务不再发送 generic ACK"""
    bridge = RuntimeV2TelegramBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")
    decision = bridge.inspect_ingress("/home/moonlight/test.html 配色不太好看", state)
    action = bridge.plan_pre_runtime(decision, state)
    assert action.should_return_early is False
    assert action.ack_text is None  # 不再发送 generic ACK
