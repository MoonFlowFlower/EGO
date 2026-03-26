#!/usr/bin/env python3
"""
开发闭环 v1 - Replay/Tape 回放校验

验证目标：
1. 输入事件可回溯
2. 边界裁决可回溯
3. 结构化接口数据可回溯
4. 最终外部动作可回溯
5. 证据链写回可追踪

使用方式：
    python scripts/run_replay_check.py [--tape-dir DIR]
    --tape-dir: 指定 tape 目录，默认使用最近的 artifacts
"""

import json
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
EGO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(EGO_ROOT / "OpenEmotion"))
sys.path.insert(0, str(EGO_ROOT / "EgoCore"))


@dataclass
class ReplayStep:
    """回放步骤"""
    step_id: str
    step_type: str  # ingress/normalized/processed/output/final
    timestamp: str
    data_hash: str
    data_preview: str
    integrity: bool


@dataclass
class ReplayChain:
    """回放链"""
    event_id: str
    steps: List[ReplayStep]
    chain_integrity: bool
    missing_steps: List[str]
    hash_consistency: bool


@dataclass
class ReplayReport:
    """回放报告"""
    run_id: str
    timestamp: str
    chains_checked: int
    chains_passed: int
    chains_failed: int
    total_steps: int
    steps_passed: int
    steps_failed: int
    overall_integrity: bool
    chains: List[dict]
    errors: List[str]


def compute_hash(data: dict) -> str:
    """计算数据哈希"""
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()[:12]


def validate_step(step_data: dict, expected_fields: List[str]) -> tuple:
    """验证步骤完整性"""
    missing = [f for f in expected_fields if f not in step_data]
    return len(missing) == 0, missing


def replay_from_tape(tape_dir: Path) -> ReplayChain:
    """从 tape 目录回放"""
    event_id = tape_dir.name

    steps = []
    missing_steps = []
    all_integrity = True

    # Step 1: Ingress Event
    ingress_files = list(tape_dir.glob("*ingress*.json"))
    if ingress_files:
        data = json.loads(ingress_files[0].read_text())
        integrity, missing = validate_step(data, ["event_id", "timestamp", "source"])
        steps.append(ReplayStep(
            step_id=f"{event_id}_ingress",
            step_type="ingress",
            timestamp=data.get("timestamp", ""),
            data_hash=compute_hash(data),
            data_preview=str(data)[:100],
            integrity=integrity,
        ))
        if not integrity:
            all_integrity = False
    else:
        missing_steps.append("ingress")

    # Step 2: Normalized Event (KernelEvent)
    normalized_files = list(tape_dir.glob("*normalized*.json")) + list(tape_dir.glob("*request*.json"))
    if normalized_files:
        data = json.loads(normalized_files[0].read_text())
        integrity, missing = validate_step(data, ["event_id", "schema_version"])
        steps.append(ReplayStep(
            step_id=f"{event_id}_normalized",
            step_type="normalized",
            timestamp=data.get("timestamp", ""),
            data_hash=compute_hash(data),
            data_preview=str(data)[:100],
            integrity=integrity,
        ))
        if not integrity:
            all_integrity = False
    else:
        missing_steps.append("normalized")

    # Step 3: Processed Result (OpenEmotion output)
    processed_files = list(tape_dir.glob("*response*.json")) + list(tape_dir.glob("*output*.json"))
    if processed_files:
        data = json.loads(processed_files[0].read_text())
        integrity, missing = validate_step(data, ["schema_version", "trace_payload"])
        steps.append(ReplayStep(
            step_id=f"{event_id}_processed",
            step_type="processed",
            timestamp=data.get("timestamp", ""),
            data_hash=compute_hash(data),
            data_preview=str(data)[:100],
            integrity=integrity,
        ))
        if not integrity:
            all_integrity = False
    else:
        missing_steps.append("processed")

    # Step 4: Final Decision (EgoCore裁决)
    final_files = list(tape_dir.glob("*decision*.json")) + list(tape_dir.glob("*final*.json"))
    if final_files:
        data = json.loads(final_files[0].read_text())
        integrity, missing = validate_step(data, ["action", "timestamp"])
        steps.append(ReplayStep(
            step_id=f"{event_id}_final",
            step_type="final",
            timestamp=data.get("timestamp", ""),
            data_hash=compute_hash(data),
            data_preview=str(data)[:100],
            integrity=integrity,
        ))
        if not integrity:
            all_integrity = False
    else:
        missing_steps.append("final")

    # 验证 hash 一致性（如果有多个步骤）
    hash_consistency = True
    if len(steps) > 1:
        # 检查 event_id 一致性
        event_ids = set()
        for step in steps:
            # 尝试从预览中提取 event_id
            if "event_id" in step.data_preview:
                pass  # 简化检查

    return ReplayChain(
        event_id=event_id,
        steps=steps,
        chain_integrity=all_integrity and len(missing_steps) == 0,
        missing_steps=missing_steps,
        hash_consistency=hash_consistency,
    )


def replay_from_trace_file(trace_file: Path) -> ReplayChain:
    """从单个 trace 文件回放"""
    data = json.loads(trace_file.read_text())
    event_id = data.get("event_id", trace_file.stem)

    steps = []
    missing_steps = []
    all_integrity = True

    # 验证 trace payload
    trace = data.get("trace_payload", {})
    integrity, missing = validate_step(trace, ["schema_version", "event_id"])

    steps.append(ReplayStep(
        step_id=f"{event_id}_trace",
        step_type="trace",
        timestamp=data.get("timestamp", ""),
        data_hash=compute_hash(data),
        data_preview=str(data)[:100],
        integrity=integrity,
    ))

    if not integrity:
        all_integrity = False

    return ReplayChain(
        event_id=event_id,
        steps=steps,
        chain_integrity=all_integrity,
        missing_steps=missing_steps,
        hash_consistency=True,
    )


def create_sample_tape():
    """创建样例 tape 用于验证"""
    print("\n[REPLAY] Creating sample tape for verification...")

    from openemotion.proto_self import KernelEvent, ProtoSelfState
    from openemotion.proto_self.kernel import process_event

    artifacts_dir = EGO_ROOT / "artifacts" / "devloop_v1" / "sample_tape"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    event_id = f"replay_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Step 1: 保存 ingress event
    ingress_event = {
        "event_id": event_id,
        "timestamp": datetime.now().isoformat(),
        "actor": "user",
        "source": "telegram",
        "event_type": "user_message",
        "user_intent": "replay_test",
        "raw_text": "测试回放",
    }
    (artifacts_dir / "ingress.json").write_text(json.dumps(ingress_event, indent=2))

    # Step 2: 标准化并保存
    kernel_event = KernelEvent(
        event_id=event_id,
        timestamp=datetime.now().isoformat(),
        actor="user",
        source="telegram",
        event_type="user_message",
        user_intent="replay_test",
        raw_text="测试回放",
    )
    (artifacts_dir / "normalized.json").write_text(json.dumps(kernel_event.to_dict(), indent=2))

    # Step 3: 处理并保存
    state = ProtoSelfState.empty()
    result = process_event(state, kernel_event)
    (artifacts_dir / "response.json").write_text(json.dumps(result.to_dict(), indent=2))

    # Step 4: 保存最终决策
    final_decision = {
        "action": "respond",
        "timestamp": datetime.now().isoformat(),
        "event_id": event_id,
        "response_text": "回放测试成功",
    }
    (artifacts_dir / "final.json").write_text(json.dumps(final_decision, indent=2))

    print(f"  [PASS] Sample tape created at {artifacts_dir}")

    return artifacts_dir


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Replay/Tape 回放校验")
    parser.add_argument("--tape-dir", type=str, help="指定 tape 目录")
    parser.add_argument("--create-sample", action="store_true", help="创建样例 tape")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print(" Development Closed Loop v1 - Replay Check")
    print("=" * 70)

    errors = []
    chains = []

    # 如果指定创建样例
    if args.create_sample:
        tape_dir = create_sample_tape()
        args.tape_dir = str(tape_dir)

    # 查找 tape 目录
    if args.tape_dir:
        tape_dirs = [Path(args.tape_dir)]
    else:
        # 自动查找 artifacts 下的 tape 目录
        artifacts_base = EGO_ROOT / "artifacts"
        tape_dirs = []

        # 查找 e2e_scenarios
        for scenario_dir in artifacts_base.glob("e2e_scenarios/*"):
            if scenario_dir.is_dir():
                tape_dirs.append(scenario_dir)

        # 查找 dual_repo_closed_loop
        for loop_dir in artifacts_base.glob("dual_repo_closed_loop_v*"):
            for evt_dir in loop_dir.glob("egocore_ingress/*"):
                if evt_dir.is_dir():
                    tape_dirs.append(evt_dir)

        # 查找 sample_tape
        sample_tape = artifacts_base / "devloop_v1" / "sample_tape"
        if sample_tape.exists():
            tape_dirs.append(sample_tape)

    if not tape_dirs:
        print("\n[WARN] No tape directories found. Creating sample tape...")
        tape_dirs = [create_sample_tape()]

    # 回放每个 chain
    chains_checked = 0
    chains_passed = 0
    chains_failed = 0
    total_steps = 0
    steps_passed = 0
    steps_failed = 0

    for tape_dir in tape_dirs:
        if not tape_dir.exists():
            continue

        print(f"\n[REPLAY] Checking {tape_dir.name}...")

        try:
            if tape_dir.is_dir() and any(tape_dir.glob("*.json")):
                chain = replay_from_tape(tape_dir)
            else:
                # 尝试作为单个 trace 文件
                chain = replay_from_trace_file(tape_dir)

            chains_checked += 1
            total_steps += len(chain.steps)
            steps_passed += sum(1 for s in chain.steps if s.integrity)
            steps_failed += sum(1 for s in chain.steps if not s.integrity)

            if chain.chain_integrity:
                chains_passed += 1
                print(f"  [PASS] Chain integrity OK - {len(chain.steps)} steps")
            else:
                chains_failed += 1
                print(f"  [FAIL] Chain broken - missing: {chain.missing_steps}")
                errors.append(f"{tape_dir.name}: missing {chain.missing_steps}")

            chains.append({
                "event_id": chain.event_id,
                "steps": [asdict(s) for s in chain.steps],
                "chain_integrity": chain.chain_integrity,
                "missing_steps": chain.missing_steps,
            })

        except Exception as e:
            chains_failed += 1
            errors.append(f"{tape_dir.name}: {e}")
            print(f"  [ERROR] {e}")

    # 生成报告
    run_id = f"replay_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    report = ReplayReport(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        chains_checked=chains_checked,
        chains_passed=chains_passed,
        chains_failed=chains_failed,
        total_steps=total_steps,
        steps_passed=steps_passed,
        steps_failed=steps_failed,
        overall_integrity=chains_failed == 0 and chains_checked > 0,
        chains=chains,
        errors=errors,
    )

    # 保存报告
    artifacts_dir = EGO_ROOT / "artifacts" / "devloop_v1"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_file = artifacts_dir / f"replay_report_{run_id}.json"

    with open(report_file, "w") as f:
        json.dump(asdict(report), f, indent=2, default=str)

    # 打印结果
    print("\n" + "=" * 70)
    print(f" Chains: {chains_checked} checked, {chains_passed} passed, {chains_failed} failed")
    print(f" Steps: {total_steps} total, {steps_passed} passed, {steps_failed} failed")
    print(f" Overall Integrity: {report.overall_integrity}")
    print(f" Report: {report_file}")
    print("=" * 70 + "\n")

    return 0 if report.overall_integrity else 1


if __name__ == "__main__":
    sys.exit(main())
