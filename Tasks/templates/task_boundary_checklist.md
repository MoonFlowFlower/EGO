# 任务六问门禁模板

> 来源：`POLICIES/EgoCore_OpenEmotion_Boundary_Constitution_v1.md` §12
> 适用：所有新任务开始前，必须强制填写
> 规则：没有这六节，不允许进入开发

---

## 任务信息

| 字段 | 值 |
|------|-----|
| task_id | |
| task_name | |
| created_at | |
| owner | |

---

## 六问门禁

### 1. Capability Ownership（能力归属）

**问题**：这个能力属于 EgoCore 还是 OpenEmotion？

**判定规则**：
- 回答"系统如何与外界交互/执行/审批/阻断/编排？"→ **归 EgoCore**
- 回答"系统是谁/如何变化/如何被经历塑造/如何理解和修正自己？"→ **归 OpenEmotion**

**回答**：
- 归属：`[EgoCore / OpenEmotion / Dual]`
- 理由：

---

### 2. Authority Source（权威数据源）

**问题**：这个能力的权威数据在哪？

**判定规则**：
- EgoCore 权威数据：session/task/tool/safety/response/replay/audit
- OpenEmotion 权威数据：identity/self-model/memory/appraisal/reflection/policy

**回答**：
- 权威源位置：
- 数据类型：
- 是否需要 mirror/cache：

---

### 3. Mirror Need（镜像需求）

**问题**：是否需要 cache/mirror/shim？

**如果需要，必须登记**：
| 字段 | 值 |
|------|-----|
| 名称 | |
| 所在仓库与路径 | |
| 为什么存在 | |
| 替代正式归属在哪 | |
| 到哪个版本前必须迁移 | |
| 若不迁移会造成什么风险 | |
| 迁移完成后删除谁 | |

**回答**：
- 需要镜像：`[是/否]`
- 镜像类型：
- 生命周期计划：

---

### 4. Boundary Risk（边界风险）

**问题**：是否会引入双重真相源？

**检查项**：
- [ ] 同一数据不会有两边各维护一套
- [ ] 同一字段不会两边各定义语义
- [ ] 临时实现不会变成永久方案

**回答**：
- 双主风险：`[无/低/中/高]`
- 风险说明：
- 缓解措施：

---

### 5. Failure Owner（失败兜底）

**问题**：失败时谁负责兜底？

**判定规则**：
- EgoCore 负责：现实动作裁决、工具执行失败、安全边界违规
- OpenEmotion 负责：主体状态异常、一致性损坏、反思失败

**回答**：
- 失败类型：
- 兜底负责人：
- 回退策略：

---

### 6. Exit Plan（退出计划）

**问题**：如果有临时 shim，何时删除？

**必须有**：
- 到期版本号
- 删除条件
- 回滚方案

**回答**：
- 是否有 shim：
- 到期版本：
- 删除计划：

---

## 门禁结论

| 检查项 | 状态 |
|-------|------|
| 能力归属明确 | ☐ |
| 权威源明确 | ☐ |
| 镜像已登记/不需要 | ☐ |
| 双主风险可控 | ☐ |
| 失败兜底明确 | ☐ |
| 退出计划明确 | ☐ |

**门禁状态**：`[PASS / BLOCKED]`

**阻塞原因**（如有）：

---

## 附录：参考规则

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

### 一票否决条件

- 开始承载最终解释权（shim 变本体）
- 没有到期版本
- 没有删除计划
- 被多个新功能继续复用扩张
- 变成默认长期实现

---

*此模板基于边界宪章 v1 强制执行*
