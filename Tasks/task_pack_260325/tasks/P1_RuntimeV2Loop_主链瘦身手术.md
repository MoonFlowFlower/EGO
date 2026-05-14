# P1：RuntimeV2Loop 主链瘦身手术任务单

## 任务编号
P1

## 任务类型
架构重构 / 主链瘦身 / 责任切分

## 目标
把 RuntimeV2Loop 从‘功能垃圾桶’重构为真正的主链协调器，切出 Proto-Self ingress、risk signal、evidence sink、external result feedback 等职责，同时保持对外行为和回归不破。

## 成功判据
1. `RuntimeV2Loop` 文件显著瘦身，主流程清晰
2. Proto-Self 事件构造、risk 注入、evidence capture、external_result 回流不再混在同一方法
3. simulated / integration / real_telegram 现有主链行为保持不变或变更被明确解释
4. 新的职责边界可单测，可审计

## 当前层级
主链实现层 / 架构收口层

## 当前确定项
- `loop.py` 当前同时承担 feature flag、risk 评估、proto_self_event 构造、evidence capture、trace 写入、tool result 回流等职责
- README 已将 RuntimeV2Loop 视为 unified runner 主链

## 关键未知
- 是否还有更多跨层职责散落在 transition / decision / telegram bridge 等位置
- 当前 event dict / evidence collector / trace bridge 的耦合点是否还能进一步收口

## 为什么这个任务优先级高
这是当前最容易继续长出垃圾代码的主入口；越晚切越难。

## 强制范围
- EgoCore/app/runtime_v2/loop.py
- 与其直接耦合的 proto-self ingress / evidence / risk / feedback 代码
- 必要的 tests / replay / evidence 适配

## 明确不做
- 不在此任务里重做 Proto-Self 本体逻辑
- 不在此任务里重新设计长期状态存储
- 不顺手大改 unrelated module

## 开发前六问（必须先答）
### A. Capability Ownership
Runtime 编排归 EgoCore。

### B. Authority Source
主链 orchestration 真相源在 EgoCore runtime，不在 adapter 或 README。

### C. Mirror Need
允许保留 adapter / bridge，但必须退为薄层。

### D. Boundary Risk
若 loop.py 同时承担本体解释、状态语义和证据治理，等于跨层污染。

### E. Failure Owner
EgoCore runtime 负责人兜底。

### F. Exit Plan
loop.py 最终只保留 turn orchestration；临时 helper 若新增，必须登记并注明后续归属。

## 主执行链（只保留 1 条）
1. 画出 loop.py 当前职责图
2. 识别可抽离的纯宿主职责模块
3. 先抽函数，再抽组件，最后收主流程
4. 用现有回归验证行为未破
5. 追加最小 contract / unit / integration tests

## 备选链（仅当主链被证伪时启用）
若一步到位拆组件风险高，先做纯函数级收口与依赖注入，为下一轮再抽类做准备。

## 强制产出
- artifacts/archive/repo_cleanup_history/P1/TASK_REPORT.md
- artifacts/archive/repo_cleanup_history/P1/RESPONSIBILITY_MAP.md
- loop.py 重构提交
- 对应新增/更新测试
- CHANGE_PLAN.md（记录新旧职责对应关系）

## 强制证据
- 重构前后的责任图
- 文件长度 / 函数复杂度对比
- 关键回归结果
- 行为保持或变更说明

## 验收口径限制
只能报‘主链瘦身完成并通过对应层级回归’；不得顺带报‘整体系统更稳定’除非有观察期证据。

## 失败后回退动作
如回归破坏，优先回退结构变化而不是热补丁堆更多条件分支。

## 交给 Codex 的硬要求
- 先给责任图再动刀
- 主链入口只做协调，不做本体解释
- 不许把新垃圾模块从 loop.py 平移到另一个更难找的文件里
- 保留 1 条主执行链
