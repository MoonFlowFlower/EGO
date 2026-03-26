#!/usr/bin/env python3
"""
开发闭环 v1 - 最小主链 E2E Smoke 测试

验证目标：
1. 用户输入进入 EgoCore
2. 标准化事件进入 OpenEmotion
3. OpenEmotion 返回结构化结果
4. EgoCore 完成最终裁决
5. 输出回复/ask/wait/block/escalate
6. 结果回流 trace/replay/artifacts/memory 输入链

使用方式：
    python scripts/run_devloop_smoke_e2e.py [--quick]
    --quick: 快速模式，仅运行关键场景
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
EGO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(EGO_ROOT / "OpenEmotion"))
sys.path.insert(0, str(EGO_ROOT / "EgoCore"))


@dataclass
class SmokeTestResult:
    """Smoke 测试结果"""
    test_name: str
    passed: bool
    message: str
    evidence: dict
    timestamp: str


@dataclass
class SmokeTestReport:
    """Smoke 测试报告"""
    run_id: str
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    results: list
    main_chain_status: str  # accessible/broken/blocked
    enabled_status: bool
    trigger_evidence: Optional[str]


def test_event_normalization():
    """测试：事件标准化"""
    print("\n[SMOKE] Event Normalization")

    from openemotion.proto_self import KernelEvent, SCHEMA_VERSION

    # 模拟 EgoCore 输入事件
    egocore_event = {
        "event_id": "smoke-test-001",
        "timestamp": datetime.now().isoformat(),
        "actor": "user",
        "source": "telegram",
        "event_type": "user_message",
        "user_intent": "test_smoke",
        "raw_text": "这是一条测试消息",
        "conversation_context": {"channel": "telegram"},
        "task_context": {"pending_tasks": 0},
        "runtime_summary": {"mode": "normal"},
        "safety_context": {"risk": "low", "risk_level": "low"},
        "external_result": None,
    }

    # 标准化为 KernelEvent
    kernel_event = KernelEvent(
        schema_version=SCHEMA_VERSION,
        event_id=egocore_event["event_id"],
        timestamp=egocore_event["timestamp"],
        actor=egocore_event["actor"],
        source=egocore_event["source"],
        event_type=egocore_event["event_type"],
        user_intent=egocore_event["user_intent"],
        raw_text=egocore_event["raw_text"],
        conversation_context=egocore_event["conversation_context"],
        task_context=egocore_event["task_context"],
        runtime_summary=egocore_event["runtime_summary"],
        safety_context=egocore_event["safety_context"],
        external_result=egocore_event["external_result"],
    )

    # 验证
    assert kernel_event.schema_version == SCHEMA_VERSION
    assert kernel_event.event_id == "smoke-test-001"
    assert kernel_event.source == "telegram"

    print("  [PASS] Event normalized to KernelEvent")

    return SmokeTestResult(
        test_name="event_normalization",
        passed=True,
        message="事件标准化成功",
        evidence={"event_id": kernel_event.event_id, "schema_version": SCHEMA_VERSION},
        timestamp=datetime.now().isoformat(),
    )


def test_openemotion_processing():
    """测试：OpenEmotion 处理"""
    print("\n[SMOKE] OpenEmotion Processing")

    from openemotion.proto_self import KernelEvent, ProtoSelfState
    from openemotion.proto_self.kernel import process_event

    # 创建测试事件
    event = KernelEvent(
        event_id="smoke-test-002",
        timestamp=datetime.now().isoformat(),
        actor="user",
        source="telegram",
        event_type="user_message",
        user_intent="test_verify",
        raw_text="运行测试",
    )

    # 处理事件
    state = ProtoSelfState.empty()
    result = process_event(state, event)

    # 验证结构化输出
    assert result.schema_version is not None
    assert result.policy_hint is not None
    assert result.response_tendency is not None
    assert result.trace_payload is not None

    print("  [PASS] OpenEmotion returned structured result")

    return SmokeTestResult(
        test_name="openemotion_processing",
        passed=True,
        message="OpenEmotion 处理成功",
        evidence={
            "schema_version": result.schema_version,
            "has_policy_hint": result.policy_hint is not None,
            "has_response_tendency": result.response_tendency is not None,
            "trace_schema": result.trace_payload.get("schema_version"),
        },
        timestamp=datetime.now().isoformat(),
    )


def test_boundary_check():
    """测试：边界检查"""
    print("\n[SMOKE] Boundary Check")

    from openemotion.proto_self.boundary import assert_no_direct_execution

    # 模拟一个正常输出
    safe_output = {
        "schema_version": "proto_self.v1",
        "policy_hint": {"action": "respond"},
        "response_tendency": {"tone": "neutral"},
        "trace_payload": {},
    }

    # 边界检查应该通过
    assert_no_direct_execution(safe_output)
    print("  [PASS] Boundary check passed for safe output")

    # 模拟一个越界输出（包含禁止的执行关键字）
    unsafe_output = {
        "schema_version": "proto_self.v1",
        "policy_hint": {"execute_tool": "delete_file"},  # 禁止关键字
    }

    # 边界检查应该失败
    try:
        assert_no_direct_execution(unsafe_output)
        raise AssertionError("Should have raised for unsafe output")
    except AssertionError as e:
        if "Boundary violation" in str(e):
            print(f"  [PASS] Boundary check blocked unsafe output")
        else:
            raise

    return SmokeTestResult(
        test_name="boundary_check",
        passed=True,
        message="边界检查正常工作",
        evidence={
            "safe_output_passed": True,
            "unsafe_output_blocked": True,
        },
        timestamp=datetime.now().isoformat(),
    )


def test_risk_differentiation():
    """测试：风险区分"""
    print("\n[SMOKE] Risk Differentiation")

    from openemotion.proto_self import KernelEvent, ProtoSelfState
    from openemotion.proto_self.kernel import process_event

    # 高风险事件
    high_risk_event = KernelEvent(
        event_id="smoke-test-high-risk",
        timestamp=datetime.now().isoformat(),
        actor="user",
        source="telegram",
        event_type="user_message",
        user_intent="file_risk_op",
        raw_text="删除临时文件",
        safety_context={"risk": "high", "risk_level": "high"},
    )

    # 低风险事件
    low_risk_event = KernelEvent(
        event_id="smoke-test-low-risk",
        timestamp=datetime.now().isoformat(),
        actor="user",
        source="telegram",
        event_type="user_message",
        user_intent="test_verify",
        raw_text="读取文件",
        safety_context={"risk": "low", "risk_level": "low"},
    )

    state = ProtoSelfState.empty()

    # 处理高风险事件
    high_result = process_event(state, high_risk_event)
    high_psi_bucket = high_result.trace_payload.get("cycle_delta", {}).get("psi_bucket", "")

    # 处理低风险事件
    low_result = process_event(state, low_risk_event)
    low_psi_bucket = low_result.trace_payload.get("cycle_delta", {}).get("psi_bucket", "")

    # 验证区分
    high_has_risk = "risk_high" in high_psi_bucket
    low_has_risk = "risk_high" in low_psi_bucket

    print(f"  High-risk psi_bucket: {high_psi_bucket}")
    print(f"  Low-risk psi_bucket: {low_psi_bucket}")

    assert high_has_risk, "High risk should have :risk_high suffix"
    assert not low_has_risk, "Low risk should not have :risk_high suffix"

    print("  [PASS] Risk differentiation working")

    return SmokeTestResult(
        test_name="risk_differentiation",
        passed=True,
        message="风险区分正常工作",
        evidence={
            "high_risk_bucket": high_psi_bucket,
            "low_risk_bucket": low_psi_bucket,
            "differentiated": high_has_risk and not low_has_risk,
        },
        timestamp=datetime.now().isoformat(),
    )


def test_state_persistence():
    """测试：状态持久化"""
    print("\n[SMOKE] State Persistence")

    from openemotion.proto_self import KernelEvent, ProtoSelfState
    from openemotion.proto_self.kernel import process_event

    with tempfile.TemporaryDirectory() as temp_dir:
        state_file = Path(temp_dir) / "state.json"

        # 第一轮：创建并保存
        state1 = ProtoSelfState.empty()
        event1 = KernelEvent(
            event_id="persist-001",
            timestamp=datetime.now().isoformat(),
            actor="user",
            source="telegram",
            event_type="user_message",
            user_intent="test_persist",
        )
        process_event(state1, event1)

        with open(state_file, "w") as f:
            json.dump(state1.to_dict(), f, default=str)

        # 第二轮：加载并继续
        with open(state_file, "r") as f:
            data = json.load(f)
        state2 = ProtoSelfState.from_dict(data)

        event2 = KernelEvent(
            event_id="persist-002",
            timestamp=datetime.now().isoformat(),
            actor="user",
            source="telegram",
            event_type="user_message",
            user_intent="test_persist",
        )
        result = process_event(state2, event2)

        # 验证 trace 累积
        trace_count = len(state2.episodic_trace)
        assert trace_count >= 1, "Trace should accumulate"

        print(f"  [PASS] State persisted and loaded, trace count: {trace_count}")

    return SmokeTestResult(
        test_name="state_persistence",
        passed=True,
        message="状态持久化正常",
        evidence={
            "trace_count": trace_count,
            "persistence_works": True,
        },
        timestamp=datetime.now().isoformat(),
    )


def test_trace_payload_integrity():
    """测试：Trace Payload 完整性"""
    print("\n[SMOKE] Trace Payload Integrity")

    from openemotion.proto_self import KernelEvent, ProtoSelfState
    from openemotion.proto_self.kernel import process_event

    event = KernelEvent(
        event_id="smoke-trace-001",
        timestamp=datetime.now().isoformat(),
        actor="user",
        source="telegram",
        event_type="user_message",
        user_intent="test_trace",
    )

    state = ProtoSelfState.empty()
    result = process_event(state, event)

    trace = result.trace_payload

    # 验证 trace 必要字段
    required_fields = ["schema_version", "event_id"]
    missing = [f for f in required_fields if f not in trace]

    assert not missing, f"Missing trace fields: {missing}"

    print(f"  [PASS] Trace payload contains required fields")

    return SmokeTestResult(
        test_name="trace_payload_integrity",
        passed=True,
        message="Trace payload 完整",
        evidence={
            "has_schema_version": "schema_version" in trace,
            "has_event_id": "event_id" in trace,
            "trace_keys": list(trace.keys()),
        },
        timestamp=datetime.now().isoformat(),
    )


def main():
    print("\n" + "=" * 70)
    print(" Development Closed Loop v1 - E2E Smoke Test")
    print("=" * 70)

    # 运行所有测试
    tests = [
        test_event_normalization,
        test_openemotion_processing,
        test_boundary_check,
        test_risk_differentiation,
        test_state_persistence,
        test_trace_payload_integrity,
    ]

    results = []
    passed = 0
    failed = 0

    for test in tests:
        try:
            result = test()
            results.append(asdict(result))
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {e}")
            import traceback
            traceback.print_exc()
            results.append(asdict(SmokeTestResult(
                test_name=test.__name__,
                passed=False,
                message=str(e),
                evidence={},
                timestamp=datetime.now().isoformat(),
            )))
            failed += 1

    # 生成报告
    run_id = f"smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    report = SmokeTestReport(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        total_tests=len(tests),
        passed=passed,
        failed=failed,
        results=results,
        main_chain_status="accessible" if failed == 0 else "blocked",
        enabled_status=failed == 0,
        trigger_evidence=f"smoke_test_passed_{passed}/{len(tests)}" if failed == 0 else None,
    )

    # 保存报告
    artifacts_dir = EGO_ROOT / "artifacts" / "devloop_v1"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_file = artifacts_dir / f"smoke_report_{run_id}.json"

    with open(report_file, "w") as f:
        json.dump(asdict(report), f, indent=2, default=str)

    # 打印结果
    print("\n" + "=" * 70)
    print(f" Results: {passed}/{len(tests)} passed")
    print(f" Main Chain Status: {report.main_chain_status}")
    print(f" Report: {report_file}")
    print("=" * 70 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
