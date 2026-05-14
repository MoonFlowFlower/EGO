# P3：Proto-Self 契约单一化任务单

## 任务编号
P3

## 任务类型
契约治理 / schema 收口 / 边界清理

## 目标
把 EgoCore → OpenEmotion 输入事件与 OpenEmotion → EgoCore 输出结果真正收口成唯一结构化契约，禁止宿主侧继续手拼漂移字段，消除双字段、别名字段和隐式兼容污染。

## 成功判据
1. 存在明确唯一的输入/输出 schema 权威源
2. 宿主侧不再自由拼接临时字段
3. 兼容层只保留在 adapter 一处
4. contract tests 能防止未来接口漂移

## 当前层级
边界契约层

## 当前确定项
- 目前 runtime 主链手工构造 event dict，再由 adapter normalize
- 已出现同时写 `risk` 与 `risk_level` 的兼容痕迹

## 关键未知
- 还有哪些字段在不同模块中名称不一致
- 现有 tests 是否足以阻止未来漂移

## 为什么这个任务优先级高
契约不稳，所有 replay / trace / evidence / state 都会继续漂。

## 强制范围
- KernelEvent / KernelOutput 相关 schema
- normalize_to_kernel_event
- runtime / adapter / trace / evidence 的字段映射
- contract / compatibility tests

## 明确不做
- 不借机重写 kernel 内部算法
- 不扩大到所有业务对象的 schema 革命

## 开发前六问（必须先答）
### A. Capability Ownership
结构化输入输出边界由双核共同遵守；本体字段解释权在 OpenEmotion，宿主映射权在 EgoCore adapter。

### B. Authority Source
最终字段语义权威源在 OpenEmotion schema；宿主只负责对齐。

### C. Mirror Need
兼容映射允许存在，但只能有一个入口，不得多点复制。

### D. Boundary Risk
多处字段别名并存会形成事实上的多重契约。

### E. Failure Owner
接口漂移由边界治理负责，不能甩锅给调用方。

### F. Exit Plan
保留一版兼容映射期后删除旧字段；必须注明废弃计划。

## 主执行链（只保留 1 条）
1. 列出现有输入输出字段全集
2. 标记别名 / 漂移 / 冗余字段
3. 指定唯一 canonical schema
4. 收口所有映射到 adapter / schema 层
5. 建 contract tests

## 备选链（仅当主链被证伪时启用）
若全量收口风险高，先从高风险字段（如 risk）开始做分阶段废弃。

## 强制产出
- artifacts/archive/repo_cleanup_history/P3/TASK_REPORT.md
- artifacts/archive/repo_cleanup_history/P3/SCHEMA_DIFF.md
- canonical schema 文档/代码
- contract tests
- 废弃字段迁移计划

## 强制证据
- 字段清单与冲突表
- contract test 结果
- 迁移说明
- does_not_prove 字段

## 验收口径限制
只能报‘契约已收口到某层级’，不得报‘边界彻底稳定’除非后续观察期已跑过。

## 失败后回退动作
兼容问题出现时优先回到 adapter 单点兼容，而不是把兼容散回多个模块。

## 交给 Codex 的硬要求
- 先列字段全集
- 一个字段只能有一个 canonical name
- 兼容只允许单点存在
- 必须附废弃计划
