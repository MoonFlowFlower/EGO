"""
Proto-Self Kernel Adapter for EgoCore

宿主侧最薄接线层：只做 normalize / load state / invoke kernel / save mirror / write trace。

设计约束：
- 只做事件标准化、状态加载、kernel 调用、状态镜像、trace 写入
- 不允许在 adapter 里发明主体语义
- 不允许在 EgoCore 里追加长期 self-model 更新逻辑
- 所有主体本体语义必须留在 OpenEmotion
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# OpenEmotion imports
from openemotion.proto_self import (
    KernelEvent,
    KernelOutput,
    ProtoSelfState,
    SCHEMA_VERSION,
)
from openemotion.proto_self.kernel import process_event
from openemotion.proto_self.boundary import assert_no_direct_execution


class ProtoSelfAdapter:
    """
    Proto-Self Kernel 适配器。
    
    职责：
    - 事件标准化：把 EgoCore 事件转换为 KernelEvent
    - 状态加载：从 mirror 文件加载 ProtoSelfState
    - kernel 调用：调用 process_event
    - 状态镜像：保存状态镜像
    - trace 写入：桥接到 EgoCore trace 系统
    """

    def __init__(
        self,
        mirror_dir: Optional[Path] = None,
        trace_bridge: Optional[Any] = None,
    ):
        self.mirror_dir = mirror_dir or Path("artifacts/proto_self_mirror")
        self.mirror_dir.mkdir(parents=True, exist_ok=True)
        self.trace_bridge = trace_bridge

    def handle_event(self, egocore_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 EgoCore 事件的主入口。

        流程：
        1. 标准化事件
        2. 加载状态
        3. 调用 kernel
        4. 保存镜像
        5. 写 trace
        6. 返回结果
        """
        event_id = egocore_event.get("event_id", "unknown")
        logger.info(f"[PSK-ADAPTER-01] handle_event called event_id={event_id}")

        # 1. 标准化事件
        logger.info(f"[PSK-ADAPTER-02] Normalizing event...")
        kernel_event = normalize_to_kernel_event(egocore_event)

        # 2. 加载状态
        logger.info(f"[PSK-ADAPTER-03] Loading state from {self.mirror_dir}")
        state = self.load_latest_state()
        logger.info(f"[PSK-ADAPTER-04] State loaded, cycles={len(state.cycle_store.signatures) if hasattr(state, 'cycle_store') else 'N/A'}")

        # 3. 调用 kernel
        logger.info(f"[PSK-ADAPTER-05] Calling kernel process_event...")
        result = process_event(state, kernel_event)
        logger.info(f"[PSK-ADAPTER-06] Kernel returned, has_policy_hint={result.policy_hint is not None}")

        # 4. 边界检查
        assert_no_direct_execution(result.to_dict())

        # 5. 保存镜像
        mirror_path = self.mirror_dir / "state.json"
        logger.info(f"[PSK-ADAPTER-07] Saving mirror to {mirror_path}")
        self.save_mirror(state)
        logger.info(f"[PSK-ADAPTER-08] Mirror saved, exists={mirror_path.exists()}")

        # 6. 写 trace
        if self.trace_bridge:
            logger.info(f"[PSK-ADAPTER-09] Writing trace via bridge...")
            self.trace_bridge.write(result.trace_payload)
            logger.info(f"[PSK-ADAPTER-10] Trace written")
        else:
            logger.warning(f"[PSK-ADAPTER-09] No trace_bridge available!")

        # 7. 返回结果
        logger.info(f"[PSK-ADAPTER-11] Returning result")
        return {
            "policy_hint": result.policy_hint,
            "response_tendency": result.response_tendency.to_dict() if result.response_tendency else None,
            "identity_state_delta": result.identity_state_delta,
            "self_model_delta": result.self_model_delta,
            "appraisal_state_delta": result.appraisal_state_delta,
            "reflection_note": result.reflection_note.to_dict() if result.reflection_note else None,
        }

    def load_latest_state(self) -> ProtoSelfState:
        """加载最新状态镜像。"""
        mirror_file = self.mirror_dir / "state.json"
        if mirror_file.exists():
            try:
                with open(mirror_file, "r") as f:
                    data = json.load(f)
                return ProtoSelfState.from_dict(data)
            except Exception:
                pass
        return ProtoSelfState.empty()

    def save_mirror(self, state: ProtoSelfState) -> None:
        """保存状态镜像。"""
        mirror_file = self.mirror_dir / "state.json"
        with open(mirror_file, "w") as f:
            json.dump(state.to_dict(), f, indent=2, default=str)


def normalize_to_kernel_event(egocore_event: Dict[str, Any]) -> KernelEvent:
    """
    把 EgoCore 事件标准化为 KernelEvent。
    
    这是 adapter 的核心职责：确保事件格式一致。
    """
    return KernelEvent(
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
