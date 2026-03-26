# P4：Trace / Evidence / Replay 统一账本任务单

## 任务编号
P4

## 任务类型
治理 / 可观测性 / 证据链收口

## 目标
把 proto-self trace、runtime evidence、response plan、replay artifacts 从散落副本收口成统一账本体系，避免出现‘回放真相源’和‘验收真相源’分别存在的双账本问题。

## 成功判据
1. trace / evidence / replay 三者关系有统一模型
2. 每类 artifact 都知道谁是权威源、谁是派生视图
3. 至少一条真实或集成样本可以从统一账本完整追到输入、处理、输出
4. 不再需要在多个文件里手工拼证据包

## 当前层级
治理与科学仪器层

## 当前确定项
- 当前既有 evidence collector，又有 proto_self_trace_bridge 默认写单独 jsonl
- README 和验收协议都强调 replay / trace / audit / artifact discipline

## 关键未知
- 当前哪些文件是权威账本，哪些只是导出副本
- 是否已有 replay 依赖某个散落文件格式

## 为什么这个任务优先级高
没有统一账本，你后面做 E5/E6 观察期和长期固化会非常痛苦。

## 强制范围
- evidence collector
- proto_self_trace_bridge
- replay 相关 artifacts
- response plan / normalized_event / real channel evidence bundle

## 明确不做
- 不顺手重做所有日志系统
- 不把统一账本做成复杂大平台

## 开发前六问（必须先答）
### A. Capability Ownership
治理证据链归 EgoCore。

### B. Authority Source
正式证据账本权威源在 EgoCore；OpenEmotion trace 只是其中一部分输入/派生记录。

### C. Mirror Need
允许导出视图，不允许多份都自称正式账本。

### D. Boundary Risk
若 replay 依赖一套文件、验收依赖另一套文件，就是双账本。

### E. Failure Owner
EgoCore 治理层兜底。

### F. Exit Plan
旧 trace/evidence 输出若保留，只能作为兼容视图，并登记删除时点。

## 主执行链（只保留 1 条）
1. 画现有 artifact 流图
2. 标出权威账本与派生视图
3. 统一 event_id / turn_id / session_id / evidence_id 关联键
4. 收口最小证据包生成
5. 用一条样本验证可追踪性

## 备选链（仅当主链被证伪时启用）
若一次性统一不了，先统一索引与 ID 关联，再逐步合并文件形态。

## 强制产出
- artifacts/P4/TASK_REPORT.md
- artifacts/P4/LEDGER_MODEL.md
- artifacts/P4/ARTIFACT_FLOW_MAP.md
- 至少一条端到端样本证据包
- 对应代码与测试

## 强制证据
- artifact 流图
- 样本追踪链
- 权威源/派生视图清单
- replay 可用性说明

## 验收口径限制
只能报‘统一账本模型已建立/接线’，不得报‘长期治理已完成’。

## 失败后回退动作
如统一账本方案影响现有回放，先保留索引层兼容。

## 交给 Codex 的硬要求
- 先画 artifact 流图
- 每类 artifact 必须标权威源
- 不许让多个文件都自称正式证据
- 样本追踪链必须可读
