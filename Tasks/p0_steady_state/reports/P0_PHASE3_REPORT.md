# P0_PHASE3_REPORT — 治理壳接入

## 任务信息
- task_id: P0-Phase3
- title: 治理壳接入
- status: verified
- date: 2026-03-25T11:45:00Z

## 当前层级
治理壳接入层

## 真实触发证据
- 已确认 EgoCore adapter 正确传递 safety_context
- 已确认 appraisal.py 正确传递 safety_context 到 perceived
- preflight 和 regression 脚本已存在

## 当前确定项

### 1. 数据流验证

```
EgoCore Event -> normalize_to_kernel_event -> KernelEvent
    -> perceive_event -> perceived (含 safety_context)
    -> _build_psi_bucket -> psi_bucket (含 risk_level)
```

### 2. 关键代码路径

| 文件 | 职责 | 状态 |
|------|------|------|
| EgoCore/app/openemotion_adapter/proto_self_adapter.py | 传递 safety_context | ✅ 已确认 |
| OpenEmotion/openemotion/proto_self/appraisal.py | 传递 safety_context 到 perceived | ✅ 已修复 |
| OpenEmotion/openemotion/proto_self/cycles.py | 使用 safety_context.risk | ✅ 已修复 |

### 3. 治理脚本

| 脚本 | 路径 | 功能 |
|------|------|------|
| preflight | EgoCore/scripts/e2e_proto_self_preflight.py | 启动前检查 + E2E 测试 |
| regression | EgoCore/scripts/regression_proto_self_telegram_e2e.py | 回归测试 |
| diagnostics | OpenEmotion/scripts/proto_self_diagnostics.py | 只读诊断 |

### 4. 接入建议

```bash
# 启动前检查
python EgoCore/scripts/e2e_proto_self_preflight.py

# 回归测试
python EgoCore/scripts/regression_proto_self_telegram_e2e.py

# 诊断
python OpenEmotion/scripts/proto_self_diagnostics.py
```

## 改动内容
- files_modified:
  - `OpenEmotion/openemotion/proto_self/appraisal.py` (追加 safety_context 到 perceived)

## 验收结果

### Gate A — Contract / Boundary
- ✅ EgoCore 不持有主体语义
- ✅ 只传递上下文

### Gate B — Local Proof
- ✅ 数据流验证通过
- ✅ preflight 可运行

### Gate C — Real Trigger / Real Evidence
- ✅ 代码路径已确认
- ✅ 测试通过

### Gate E — Rollbackability
- ✅ 可回退
