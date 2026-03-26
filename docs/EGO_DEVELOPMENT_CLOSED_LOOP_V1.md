# EGO 开发闭环 v1

> 正式开发闭环说明文档
> 版本：v1.0
> 状态：E2 (模拟验证通过)
> 证据层级：E2
> 结论口径：已实现，脚本级模拟验证通过

**注意**: 本文档描述的能力已完成实现和模拟验证，但尚未接入真实 Telegram 主链。
需要 E4 级证据才能宣称"已接主链/已启用/已生效"。

---

## 一、定位与目标

### 定位

开发闭环 v1 是 EGO 项目的基础设施，用于把开发过程标准化为可验证、可回放、可阻断的正式主链。

### 目标

把"方案生成 → 施工 → 验证 → 收口"的开发过程收成一条：
- **可重复**：每次任务遵循相同流程
- **可审计**：所有步骤有证据留存
- **可回放**：失败可定位、可复现
- **可阻断**：边界违规自动阻断

### 成功判据

- 新任务不再主要依赖人工慢速聊天排错
- 在进入主链前，被 Gate、E2E、Replay、证据链自动发现大部分问题
- 不破坏 EgoCore / OpenEmotion 的正式双核边界

---

## 二、核心组件

### 2.1 任务六问门禁

每个新任务开始前，必须强制填写：

| 问题 | 目的 |
|------|------|
| Capability Ownership | 确定能力归属（EgoCore/OpenEmotion） |
| Authority Source | 确定权威数据源 |
| Mirror Need | 确定是否需要 shim/mirror/cache |
| Boundary Risk | 评估双主风险 |
| Failure Owner | 确定失败兜底负责人 |
| Exit Plan | 确定临时实现的退出计划 |

**模板位置**：`Tasks/templates/task_boundary_checklist.md`

### 2.2 Gate A/B/C 验收

| Gate | 目的 | 检查项 |
|------|------|--------|
| Gate A | Boundary Contract | 模块归属、schema、权威源、双主检查 |
| Gate B | Boundary E2E | 结构化接口、E2E 验证、越界阻断 |
| Gate C | Boundary Integrity | shim 登记、replay 可追踪、口径检查 |

**模板位置**：`Tasks/templates/gate_acceptance_v1.md`

### 2.3 E2E Smoke 测试

最小主链验证切片：

1. 用户输入进入 EgoCore
2. 标准化事件进入 OpenEmotion
3. OpenEmotion 返回结构化结果
4. EgoCore 完成最终裁决
5. 输出回复/ask/wait/block/escalate
6. 结果回流 trace/replay/artifacts/memory

**脚本位置**：`scripts/run_devloop_smoke_e2e.py`

### 2.4 Replay 校验

验证：

1. 输入事件可回溯
2. 边界裁决可回溯
3. 结构化接口数据可回溯
4. 最终外部动作可回溯
5. 证据链写回可追踪

**脚本位置**：`scripts/run_replay_check.py`

### 2.5 失败分类器

**失败类型**：

| 类型 | 定义 | 严重性 |
|------|------|--------|
| boundary_error | 边界归属错误，能力错位写入 | high |
| authority_error | 权威源错误，数据定义不一致 | high |
| schema_error | schema/contract 错误 | medium |
| runtime_error | runtime/orchestration 错误 | medium |
| e2e_broken | E2E 断链，主链验证失败 | high |
| test_gap | 测试缺口，覆盖不足 | low |
| wording_error | 仅口径错误，实际未生效 | low |

**假完成口径检查**：
- "已完成"但未接主链
- "已修复"但无验证证据
- "已生效"但无触发证据
- "已闭环"但未启用

**脚本位置**：`scripts/classify_failure.py`

---

## 三、使用流程

### 3.1 任务开始

```bash
# 1. 复制六问门禁模板
cp Tasks/templates/task_boundary_checklist.md Tasks/active/YYYYMMDD-L{X}-{type}-{brief}.md

# 2. 填写六问
# 3. 确认门禁状态为 PASS 后开始开发
```

### 3.2 开发过程

```bash
# 边开发边验证
python scripts/run_devloop_smoke_e2e.py --quick
```

### 3.3 任务收口

```bash
# 1. 填写 Gate A/B/C 模板
cp Tasks/templates/gate_acceptance_v1.md artifacts/devloop_v1/gate_{module}.md

# 2. 运行完整 E2E
python scripts/run_devloop_smoke_e2e.py

# 3. 运行 replay 检查
python scripts/run_replay_check.py --tape-dir artifacts/devloop_v1/sample_tape

# 4. 运行失败分类
python scripts/classify_failure.py --analyze-report artifacts/devloop_v1/smoke_report.json
```

### 3.4 验收标准

只有同时满足以下条件，才允许报"开发闭环 v1 已实现"：

1. ☐ 六问门禁已可复用
2. ☐ Gate A/B/C 模板已落地
3. ☐ 至少 1 条最小 Telegram 主链 E2E 跑通
4. ☐ 至少 1 次 replay/tape 校验成功
5. ☐ 至少 1 个失败样本被正确分类
6. ☐ 有 artifacts 证据目录
7. ☐ 输出口径未再误报"已生效/已闭环"

---

## 四、边界规则

### EgoCore 允许承载

- 用户交互前端
- session/task runtime
- 工具调度与权限控制
- 安全边界
- trace/replay/audit/gate/preflight/tool_doctor
- 边界适配层：adapter/normalization/compatibility guard

### OpenEmotion 允许承载

- identity invariants
- self-model
- long-term self summary
- memory evolution
- appraisal/internal state
- reflection/diagnosis/policy update candidate

### 明确禁止

1. **把过渡实现伪装成正式能力** - shim/mirror/cache 必须登记
2. **继续在 EgoCore 扩写主体本体** - memory/appraisal/reflection 归 OpenEmotion
3. **没有 Gate 就报完成** - 必须有 Gate A/B/C 证据
4. **靠 prompt 临时约定关键字段** - 必须走结构化事件和结果
5. **扩大题目** - 本任务只做开发闭环壳

---

## 五、Artifacts 结构

```
artifacts/devloop_v1/
├── smoke_report_YYYYMMDD_HHMMSS.json    # E2E smoke 报告
├── replay_report_YYYYMMDD_HHMMSS.json   # Replay 校验报告
├── classification_report_YYYYMMDD.json  # 失败分类报告
├── gate_{module}.md                     # Gate 验收模板
└── sample_tape/                        # 回放样例
    ├── ingress.json
    ├── normalized.json
    ├── response.json
    └── final.json
```

---

## 六、参考文档

- 边界宪章：`POLICIES/EgoCore_OpenEmotion_Boundary_Constitution_v1.md`
- 任务模板：`Tasks/templates/`
- 现有 E2E：`EgoCore/scripts/e2e_*.py`

---

## 七、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-25 | 初始版本，包含 5 个建设项 |

---

*此文档为开发闭环 v1 的正式说明*
