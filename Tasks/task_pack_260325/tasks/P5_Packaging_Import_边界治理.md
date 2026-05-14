# P5：Packaging / Import 边界治理任务单

## 任务编号
P5

## 任务类型
工程化 / 环境一致性 / 导入治理

## 目标
去掉运行时 `sys.path` 注入等临时 import hack，建立适用于 monorepo + subtree + CI + Windows/Linux 的正式包导入方式，减少环境偶发差异。

## 成功判据
1. 删除或显著减少 runtime path hack
2. 本地 / CI / Windows / Linux 导入方式一致
3. subtree 场景下仍可工作
4. 有清晰的开发态与发布态说明

## 当前层级
工程化层

## 当前确定项
- 当前 `RuntimeV2Loop` 在模块开头手动把 OpenEmotion 路径插入 `sys.path`
- 这类 hack 容易在不同环境下产生隐式差异

## 关键未知
- 仓库当前安装方式、CI 方式、Windows 路径差异是否已被其他脚本硬编码
- subtree 与正式包方式如何最小兼容

## 为什么这个任务优先级高
这是典型‘现在能跑，后面越改越脆’的问题；很适合强模型做全局工程化收口。

## 强制范围
- 包导入路径
- pyproject/setup/workspace 组织方式
- CI / 本地运行方式
- 开发说明文档

## 明确不做
- 不重写业务代码
- 不因为做工程化就强行拆仓/并仓

## 开发前六问（必须先答）
### A. Capability Ownership
工程打包与运行方式归 EgoCore 宿主集成层。

### B. Authority Source
正式导入方式的权威源在仓库工程配置，不在 runtime 代码临时 hack。

### C. Mirror Need
允许兼容脚本，但必须登记并逐步退出。

### D. Boundary Risk
运行时 import hack 会把工程边界问题伪装成业务逻辑问题。

### E. Failure Owner
工程配置兜底。

### F. Exit Plan
保留短期兼容入口时，必须写明删除条件。

## 主执行链（只保留 1 条）
1. 盘点当前 import hack 与启动脚本
2. 设计正式包/工作区方案
3. 实现最小工程改造
4. 验证多环境导入一致
5. 更新开发文档

## 备选链（仅当主链被证伪时启用）
若一次性删 hack 风险大，先将 hack 限缩到单一入口并补工程迁移计划。

## 强制产出
- artifacts/archive/repo_cleanup_history/P5/TASK_REPORT.md
- artifacts/archive/repo_cleanup_history/P5/IMPORT_HACK_INVENTORY.md
- 工程配置改动
- 多环境验证记录
- 文档更新

## 强制证据
- hack 清单
- 新旧启动方式对照
- Windows/Linux/CI 验证结果
- does_not_prove 字段

## 验收口径限制
只能报‘工程导入边界已收口到某层级’，不得顺带报‘跨环境长期稳定’。

## 失败后回退动作
如删除 hack 导致环境崩溃，优先恢复单入口兼容而非到处加新 hack。

## 交给 Codex 的硬要求
- 先盘点 hack
- 正式方案优先于临时补丁
- 兼容只允许单入口
- 必须给多环境验证表
