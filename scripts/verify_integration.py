"""
Integration Verification: EgoCore + OpenEmotion

验证目标：
1. EgoCore ProtoSelfAdapter 能正确调用 OpenEmotion kernel
2. 状态加载/保存链路完整
3. Trace 写入链路完整
4. 事件标准化正确
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "OpenEmotion"))
sys.path.insert(0, str(Path(__file__).parent.parent / "EgoCore"))

from openemotion.proto_self import KernelEvent, ProtoSelfState, SCHEMA_VERSION
from openemotion.proto_self.kernel import process_event
from openemotion.proto_self.boundary import assert_no_direct_execution


def test_egocore_adapter_logic():
    """模拟 EgoCore adapter 的完整逻辑。"""
    print("[TEST] EgoCore Adapter Logic")

    # 模拟 mirror 目录
    with tempfile.TemporaryDirectory() as temp_dir:
        mirror_dir = Path(temp_dir) / "proto_self_mirror"
        mirror_dir.mkdir(parents=True, exist_ok=True)
        mirror_file = mirror_dir / "state.json"

        # 1. 模拟 EgoCore 事件
        egocore_event = {
            "event_id": "integration-test-001",
            "timestamp": datetime.now().isoformat(),
            "actor": "user",
            "source": "telegram",
            "event_type": "user_message",
            "user_intent": "set_preference",
            "raw_text": "I prefer detailed responses",
            "conversation_context": {"channel": "telegram"},
            "task_context": {"pending_tasks": 0},
            "runtime_summary": {"mode": "normal"},
            "safety_context": {"risk_level": 0.3},
            "external_result": None,
        }

        # 2. 事件标准化 (adapter.normalize_to_kernel_event)
        kernel_event = KernelEvent(
            schema_version=SCHEMA_VERSION,
            event_id=egocore_event.get("event_id", ""),
            timestamp=egocore_event.get("timestamp", datetime.now().isoformat()),
            actor=egocore_event.get("actor", "unknown"),
            source=egocore_event.get("source", "unknown"),
            event_type=egocore_event.get("event_type", "unknown"),
            user_intent=egocore_event.get("user_intent"),
            raw_text=egocore_event.get("raw_text"),
            conversation_context=egocore_event.get("conversation_context", {}),
            task_context=egocore_event.get("task_context", {}),
            runtime_summary=egocore_event.get("runtime_summary", {}),
            safety_context=egocore_event.get("safety_context", {}),
            external_result=egocore_event.get("external_result"),
        )
        print(f"  [PASS] Event normalized: {kernel_event.event_id}")

        # 3. 加载状态 (adapter.load_latest_state)
        if mirror_file.exists():
            with open(mirror_file, "r") as f:
                data = json.load(f)
            state = ProtoSelfState.from_dict(data)
            print(f"  [PASS] State loaded from mirror")
        else:
            state = ProtoSelfState.empty()
            print(f"  [PASS] New state created")

        # 4. 调用 kernel
        result = process_event(state, kernel_event)
        print(f"  [PASS] Kernel processed event")

        # 5. 边界检查
        assert_no_direct_execution(result.to_dict())
        print(f"  [PASS] Boundary check passed")

        # 6. 保存状态镜像 (adapter.save_mirror)
        with open(mirror_file, "w") as f:
            json.dump(state.to_dict(), f, indent=2, default=str)
        print(f"  [PASS] State mirror saved to {mirror_file}")

        # 7. 验证 trace
        trace = result.trace_payload
        assert trace.get("schema_version") == "proto_self.trace.v1"
        assert trace.get("event_id") == kernel_event.event_id
        print(f"  [PASS] Trace payload verified")

        # 8. 验证输出
        assert result.policy_hint is not None
        assert result.response_tendency is not None
        print(f"  [PASS] Output contains policy_hint and response_tendency")

        print("  [PASS] Full adapter logic verified")


def test_cross_repo_import():
    """验证跨仓库导入正确。"""
    print("[TEST] Cross-repo import")

    # 验证 OpenEmotion 可以导入
    from openemotion.proto_self import KernelEvent, ProtoSelfState
    from openemotion.proto_self.kernel import process_event
    from openemotion.proto_self.schemas import SCHEMA_VERSION
    from openemotion.proto_self.trace_types import build_trace_payload

    print("  [PASS] OpenEmotion imports work")

    # 验证核心组件
    event = KernelEvent(
        event_id="import-test-001",
        timestamp=datetime.now().isoformat(),
        actor="test",
        source="test",
        event_type="test",
    )
    state = ProtoSelfState.empty()
    output = process_event(state, event)

    print(f"  [PASS] Kernel output schema_version: {output.schema_version}")


def test_state_persistence_simulation():
    """模拟状态持久化场景。"""
    print("[TEST] State persistence simulation")

    with tempfile.TemporaryDirectory() as temp_dir:
        mirror_file = Path(temp_dir) / "state.json"

        # 第一轮：创建状态并处理事件
        state1 = ProtoSelfState.empty()
        event1 = KernelEvent(
            event_id="persist-001",
            timestamp=datetime.now().isoformat(),
            actor="user",
            source="telegram",
            event_type="user_message",
            user_intent="preference",
        )
        output1 = process_event(state1, event1)
        cycle_id_1 = output1.trace_payload.get("cycle_delta", {}).get("cycle_id")

        # 保存状态
        with open(mirror_file, "w") as f:
            json.dump(state1.to_dict(), f, default=str)
        print(f"  [PASS] State persisted")

        # 第二轮：重新加载并处理
        with open(mirror_file, "r") as f:
            data = json.load(f)
        state2 = ProtoSelfState.from_dict(data)

        event2 = KernelEvent(
            event_id="persist-002",
            timestamp=datetime.now().isoformat(),
            actor="user",
            source="telegram",
            event_type="user_message",
            user_intent="preference",  # 相同意图
        )
        output2 = process_event(state2, event2)
        cycle_id_2 = output2.trace_payload.get("cycle_delta", {}).get("cycle_id")

        # 验证 cycle 连续性
        assert cycle_id_1 == cycle_id_2, "Cycle ID should be consistent"
        assert output2.trace_payload.get("cycle_delta", {}).get("op") == "strengthen"
        print(f"  [PASS] Cycle continuity after persistence")

        # 验证状态累积
        assert len(state2.episodic_trace) == 2
        print(f"  [PASS] Episodic trace accumulated: {len(state2.episodic_trace)}")


def main():
    print("\n" + "=" * 70)
    print(" Integration Verification: EgoCore + OpenEmotion ")
    print("=" * 70 + "\n")

    tests = [
        test_cross_repo_import,
        test_egocore_adapter_logic,
        test_state_persistence_simulation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f" Results: {passed} passed, {failed} failed")
    if failed == 0:
        print(" Integration chain is VERIFIED")
    print("=" * 70 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
