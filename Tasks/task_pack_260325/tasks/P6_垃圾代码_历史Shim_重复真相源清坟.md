# P6：垃圾代码 / 历史 Shim / 重复真相源清坟任务单

## 任务编号
P6

## 任务类型
代码治理 / 历史清理 / 真相源收口

## 目标
系统性识别并处理历史 compatibility-only 路径、死代码、重复实现、临时 shim、已经被主链替代却仍残留的文档与代码，给每一项一个明确归宿。

## 成功判据
1. 产出 keep / merge / migrate / compatibility-only / delete-now / delete-later 清单
2. 每个 shim / mirror / legacy path 都有归属、原因、退出计划
3. 删除或隔离真正的垃圾代码
4. 不再让总仓或 EgoCore 偷偷承载 OpenEmotion 本体逻辑

## 当前层级
代码治理层 / 历史债清理层

## 当前确定项
- 项目长期强调禁止双真相源、禁止把过渡实现伪装成正式边界
- 历史上存在 compatibility-only、mirror、shim 等路径

## 关键未知
- 当前仓库里到底还有多少真正没用但仍影响判断的遗留物
- 哪些代码虽然丑但目前仍是主链依赖

## 为什么这个任务优先级高
如果不清坟，后续每次强模型进来都会被历史噪音拖偏。

## 强制范围
- legacy / compatibility / deprecated / shim / mirror / duplicate docs / duplicate state logic
- 只清理与双核边界和主链质量直接相关的遗留物

## 明确不做
- 不为了‘好看’大面积删除未知依赖
- 不在未识别主链引用前删代码

## 开发前六问（必须先答）
### A. Capability Ownership
总仓集成与各子仓边界治理共同负责。

### B. Authority Source
主链依赖关系与功能归属清单才是判断标准，不是文件名里的 legacy/deprecated 字样。

### C. Mirror Need
所有保留的 mirror / shim 都必须登记。

### D. Boundary Risk
如果垃圾代码仍在冒充正式路径，会持续制造双主与误判。

### E. Failure Owner
对应模块归属方兜底；总仓负责集成层清理。

### F. Exit Plan
每个保留 shim 必须标删除条件与时间点。

## 主执行链（只保留 1 条）
1. 盘点疑似垃圾/重复/legacy 项
2. 建依赖与引用关系
3. 分成 keep / merge / migrate / compat / delete
4. 先删无引用真垃圾，再隔离兼容路径
5. 更新文档与索引

## 备选链（仅当主链被证伪时启用）
若自动判断风险高，先输出‘待人工确认候选清单’，只删零引用确定垃圾。

## 强制产出
- artifacts/P6/TASK_REPORT.md
- artifacts/P6/CLEANUP_MATRIX.md
- artifacts/P6/SHIM_REGISTER.md
- 删除/隔离提交
- 文档更新

## 强制证据
- 引用关系
- 删除前后回归
- shim register
- does_not_prove 字段

## 验收口径限制
只能报‘清理到某层级’，不得说‘仓库已完全整洁’。

## 失败后回退动作
任何清理引发主链异常，优先恢复并将该项降级为 compat candidate。

## 交给 Codex 的硬要求
- 先建清理矩阵
- 不允许凭感觉删
- 保留项必须有理由与退出计划
- 真正零引用垃圾优先处理
