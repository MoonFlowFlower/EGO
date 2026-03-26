# P0_R3_REPORT — runtime 主链接线修复

## 任务信息
- task_id: P0-R3
- title: runtime 主链接线修复
- status: verified
- date: 2026-03-25T14:12:00Z

---

## 一、问题描述

### 1.1 问题发现（P0-FINAL）

在 P0-FINAL 真实 Telegram 双样本验证中发现：

- `safety_context` 在 `runtime_v2/loop.py:135` 被硬编码为空字典 `{}`
- 导致 R2 修复的 `event_builder.py` 字段映射无法在运行时生效
- 高风险操作的 psi_bucket 不包含 `:risk_high` 后缀

### 1.2 数据流断裂

```
修复前:
  context_assembler.py: safety_context.risk_level = "high"  ✅
          ↓
  runtime_v2/loop.py: safety_context: {}  ❌ 覆盖为空
          ↓
  event_builder.py: 收到空字典
          ↓
  OpenEmotion: risk_signal = 0.0  ❌
```

---

## 二、修复内容

### 2.1 修改文件

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `EgoCore/app/runtime_v2/loop.py` | 新增函数 | `_assess_risk_level()` 风险评估 |
| `EgoCore/app/runtime_v2/loop.py` | 修复 | `proto_self_event.safety_context` 不再硬编码 |
| `EgoCore/scripts/p0_r3_unit_test.py` | 新增 | 单元测试 |
| `EgoCore/scripts/p0_r3_e2e_test.py` | 新增 | E2E 测试 |

### 2.2 核心修复

**修复前**：
```python
proto_self_event = {
    # ...
    "safety_context": {},  # ❌ 硬编码为空
    # ...
}
```

**修复后**：
```python
# P0-R3: 评估用户输入的风险等级
risk_level = _assess_risk_level(truncated_input)

proto_self_event = {
    # ...
    "safety_context": {
        "risk": risk_level,  # OpenEmotion 期望的字段名
        "risk_level": risk_level,  # 保留原字段名
    },
    # ...
}
```

### 2.3 修复后数据流

```
修复后:
  runtime_v2/loop.py: _assess_risk_level("删除临时文件") = "high"
          ↓
  proto_self_event.safety_context = {"risk": "high", "risk_level": "high"}
          ↓
  event_builder.py: 正确映射
          ↓
  OpenEmotion: risk_signal = 0.5  ✅
          ↓
  psi_bucket: "telegram:user_message:file_risk_op:risk_high"  ✅
```

---

## 三、测试结果

### 3.1 单元测试

- 文件：`EgoCore/scripts/p0_r3_unit_test.py`
- 结果：**13/13 通过**

| 测试类 | 测试数 | 状态 |
|--------|--------|------|
| TestRiskAssessment | 11 | ✅ 全部通过 |
| TestSafetyContextNotOverwritten | 2 | ✅ 全部通过 |

### 3.2 E2E 测试

- 文件：`EgoCore/scripts/p0_r3_e2e_test.py`
- 结果：**全部通过**

| 测试项 | 结果 |
|--------|------|
| 风险评估正确 | ✅ |
| 字段映射正确 | ✅ |
| psi_bucket 正确 | ✅ |
| cycle_id 不同 | ✅ |

### 3.3 真实 Telegram 验证

| 消息 | psi_bucket | cycle_id | risk_signal |
|------|------------|----------|-------------|
| 删除临时文件 | `telegram:user_message:file_risk_op:risk_high` | `f7c8318dccc2d7c0` | 0.5 |
| 读取文件 test.txt | `telegram:user_message:test_verify` | `34c1264506f1d7fe` | 0.1 |

---

## 四、成功判据验收

| 判据 | 状态 | 证据 |
|------|------|------|
| 高风险 bucket 含 `:risk_high` | ✅ 通过 | psi_bucket 包含后缀 |
| 低风险 bucket 不含 `:risk_high` | ✅ 通过 | 无后缀 |
| 两者 cycle_id 不同 | ✅ 通过 | 不同 cycle_id |
| diagnostics / trace / 现场现象一致 | ✅ 通过 | 数据流完整 |
| safety_context 不再被覆盖为空 | ✅ 通过 | 包含 risk 字段 |

---

## 五、结论

### 5.1 核心结论

**P0-R3 修复成功，runtime 主链接线完成。**

- `runtime_v2/loop.py` 正确评估风险并传递到 `safety_context`
- 高风险操作的 psi_bucket 包含 `:risk_high` 后缀
- 高低风险操作被分配到不同的 cycle

### 5.2 可宣称

- ✅ **runtime_v2/loop.py 不再将 safety_context 覆盖为空**
- ✅ **高风险操作的 psi_bucket 包含 `:risk_high` 后缀**
- ✅ **高低风险操作被正确区分到不同 cycle**
- ✅ **真实 Telegram 环境验证通过**

### 5.3 后续行动

- P1: 将 target/environment 纳入 psi_bucket
- P1: 自动化回归测试接入 CI

---

## 六、Artifacts

```
EgoCore/app/runtime_v2/loop.py              # 修复文件
EgoCore/scripts/p0_r3_unit_test.py          # 单元测试
EgoCore/scripts/p0_r3_e2e_test.py           # E2E 测试
EgoCore/artifacts/proto_self_mirror/state.json  # 验证状态
Tasks/p0_steady_state/reports_r3/P0_R3_REPORT.md  # 本报告
```

---

*验证日期: 2026-03-25*
*验证人: Claude Code*
