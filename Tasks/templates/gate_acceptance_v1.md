# Gate A/B/C 统一验收模板

> 来源：`POLICIES/EgoCore_OpenEmotion_Boundary_Constitution_v1.md` §13
> 适用：所有功能模块接入主链前的强制验收
> 规则：没有 Gate A/B/C 证据，不允许报闭环

---

## 模块信息

| 字段 | 值 |
|------|-----|
| module_name | |
| version | |
| check_date | |
| owner | |

---

## Gate A：Boundary Contract

> 证明模块归属明确、schema 明确、权威源明确、无明显双主

### A.1 能力归属

| 能力 | 归属 | 证据 |
|------|------|------|
| | `[EgoCore/OpenEmotion]` | |

### A.2 Schema 定义

| 检查项 | 状态 | 文件路径 |
|-------|------|----------|
| input schema 已定义 | ☐ | |
| output schema 已定义 | ☐ | |
| error schema 已定义 | ☐ | |
| 版本化 | ☐ | |

### A.3 权威源明确

| 数据 | 权威源位置 | 是否唯一 |
|------|-----------|----------|
| | | ☐ |

### A.4 双主检查

| 检查项 | 状态 |
|-------|------|
| 同一数据无两边各维护 | ☐ |
| 同一字段无两边各定义语义 | ☐ |
| 临时实现未变永久方案 | ☐ |

### Gate A 结论

**状态**：`[PASS / FAIL / CONDITIONAL]`

**证据链接**：

---

## Gate B：Boundary E2E

> 证明 EgoCore 与 OpenEmotion 通过结构化接口联动，不靠 prompt 补丁联动，越界时有明确失败出口

### B.1 结构化接口检查

| 检查项 | 状态 | 证据 |
|-------|------|------|
| EgoCore → OpenEmotion 走结构化事件 | ☐ | |
| OpenEmotion → EgoCore 走结构化结果 | ☐ | |
| 无 prompt 文本传递关键字段 | ☐ | |

### B.2 E2E 场景验证

| 场景 | 状态 | 说明 |
|------|------|------|
| 正常输入返回预期输出 | ☐ | |
| 边界条件处理正确 | ☐ | |
| 越界时有明确失败出口 | ☐ | |
| 依赖异常触发 fallback | ☐ | |

### B.3 最小 E2E 样本

```yaml
# 样本 1：正常场景
input:
output:
status:

# 样本 2：边界场景
input:
output:
status:
```

### Gate B 结论

**状态**：`[PASS / FAIL / CONDITIONAL]`

**E2E 报告路径**：

---

## Gate C：Boundary Integrity

> 证明 cache/mirror/shim 已登记，replay/audit 可追踪，没有把过渡实现伪装成正式边界

### C.1 Shim/Mirror/Cache 登记

| 名称 | 类型 | 状态 | 到期版本 |
|------|------|------|----------|
| | `[shim/mirror/cache]` | ☐ 已登记 | |

### C.2 Replay 可追踪

| 检查项 | 状态 |
|-------|------|
| 输入事件可回溯 | ☐ |
| 边界裁决可回溯 | ☐ |
| 结构化接口数据可回溯 | ☐ |
| 最终外部动作可回溯 | ☐ |
| 证据链写回可追踪 | ☐ |

### C.3 口径检查

| 禁止口径 | 是否出现 |
|----------|----------|
| "已完成"但未接主链 | ☐ 无 |
| "已修复"但无验证证据 | ☐ 无 |
| "已生效"但无触发证据 | ☐ 无 |
| "已闭环"但未启用 | ☐ 无 |

### C.4 失败分类验证

至少 1 个失败样例被正确归因：

```yaml
failure_type: [boundary_error/authority_error/schema_error/runtime_error/e2e_broken/test_gap/wording_error]
actual_evidence:
classification_correct: [yes/no]
```

### Gate C 结论

**状态**：`[PASS / FAIL / CONDITIONAL]`

**证据链接**：

---

## 综合评估

### Gate 汇总

| Gate | 状态 | 日期 |
|------|------|------|
| A - Boundary Contract | `[PASS/FAIL/CONDITIONAL]` | |
| B - Boundary E2E | `[PASS/FAIL/CONDITIONAL]` | |
| C - Boundary Integrity | `[PASS/FAIL/CONDITIONAL]` | |

### 接主链建议

- [ ] 可以接入
- [ ] 有条件接入（需满足 XXX）
- [ ] 暂不建议接入

### 阻塞项

<!-- 列出未通过的项 -->

### 风险说明

<!-- 即使通过，也要说明已知风险 -->

---

## 验收签字

| 角色 | 日期 | 意见 |
|------|------|------|
| 模块负责人 | | |
| 边界审核 | | |
| 最终批准 | | |

---

## 附录：失败分类定义

| 类型 | 定义 |
|------|------|
| boundary_error | 边界归属错误，能力错位写入 |
| authority_error | 权威源错误，数据定义不一致 |
| schema_error | schema/contract 错误，字段定义缺失 |
| runtime_error | runtime/orchestration 错误，执行链异常 |
| e2e_broken | E2E 断链，主链验证失败 |
| test_gap | 测试缺口，覆盖不足 |
| wording_error | 仅口径错误，实际未生效 |

---

*此模板基于边界宪章 v1 强制执行*
