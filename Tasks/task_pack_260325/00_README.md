# EGO 强模型重构任务包（2026-03-25）

## 任务目标

把 GPT-5.4 / Codex 这类强模型优先投入到 **最核心、最困难、最能改变主链质量** 的部分，而不是继续堆新功能。

本任务包只围绕以下三类高杠杆问题展开：

1. **真实状态是否被准确汇报**
2. **主链边界是否干净**
3. **主体状态 / trace / evidence 是否收口**

---

## 当前层级

- 层级：治理 + 架构 + 主链重构层
- 主链接入状态：`RuntimeV2Loop` 已被当作 simulated / integration / real_telegram 统一主链候选
- 启用状态：Proto-Self 已在 runtime 主链中接线
- 真实触发证据：README 口径与当前代码显示已存在真实 Telegram 样本与 unified runner 表述
- 关键未知：文档口径是否高于证据；主体状态、trace、evidence 是否仍存在双账本 / 双主 / 过渡实现伪装问题

---

## 执行顺序（强制）

只允许按下面顺序推进，不允许跳做后面的“好看优化”：

1. `P0_真实状态审计与过度报喜清理.md`
2. `P1_RuntimeV2Loop_主链瘦身手术.md`
3. `P2_主体状态持久化重构.md`
4. `P3_ProtoSelf_契约单一化.md`
5. `P4_Trace_Evidence_Replay_统一账本.md`
6. `P5_Packaging_Import_边界治理.md`
7. `P6_垃圾代码_历史Shim_重复真相源清坟.md`
8. `P7_风险信号单一化.md`

---

## 强制共用规则

所有任务都必须遵守：

1. **先审计再改造**：不得在未确认权威源、现状与证据层级前直接大改
2. **只保留一个主方案**：除非主方案被证伪，否则不要同时铺两条重构线
3. **改主链必须保行为**：除非任务明确要求改行为，否则先保现有对外行为与回归结果
4. **结论强度不得高于证据强度**
5. **不得把 shim / mirror / cache 写成正式本体**
6. **每个任务结束必须给出“本次结论不能证明什么”**
7. **连续两次同层修补仍复现时，必须升层重定义问题**

---

## 每个任务的标准交付物

每个任务必须至少产出：

- `artifacts/<task_id>/TASK_REPORT.md`
- `artifacts/<task_id>/CHANGE_PLAN.md`
- `artifacts/<task_id>/EVIDENCE_TABLE.md`
- `artifacts/<task_id>/FAILURE_SAMPLES.md`（如无失败样本，必须说明为什么当前阶段还拿不到）
- 对应代码改动 / 文档改动 / 测试改动

---

## 建议工作方式

每次只让 Codex 做 **一个任务**。做完后你开一个新会话，重新喂给它：

- 上一个任务的 `TASK_REPORT.md`
- 本任务任务单
- 仓库当前最新状态

不要在同一会话里串做多个重构任务，否则上下文会越来越脏，Codex 会开始偷懒、泛化、报喜或忽略前提。

---

## 你对 Codex 的统一总执行令

见：`templates/00_CODEX_总执行令.md`

## 你每轮发给 Codex 的逐任务启动词

见：`templates/01_CODEX_逐任务启动模板.md`

## 你每轮结束后让 Codex 产出的收口模板

见：`templates/02_CODEX_任务结束收口模板.md`

## 如何避免上下文过长

见：`templates/03_CODEX_防上下文过长协议.md`
