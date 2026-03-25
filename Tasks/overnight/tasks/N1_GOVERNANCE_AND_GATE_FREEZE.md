# N1 — 治理收尾与默认 Gate 固化

## 任务类型
治理收尾 / 回归固化 / 可验证性强化

## 目标
把“Proto-Self Kernel v1 已 verified_telegram_e2e”固化成默认可验主线，而不是一次性验收记忆。

## 当前层级
治理收尾层

## 当前确定项
- Proto-Self Kernel v1 的 Telegram 最小闭环已通过
- 已有 regression 脚本
- 已有 artifacts 与状态口径

## 关键未知
- preflight 是否已经被固化为默认前置检查
- regression 是否已经稳定纳入默认 Gate
- 正式索引与状态页是否完全一致
- 报告模板与运行态记录是否齐备

## 成功判据
1. 存在可执行的 preflight 检查入口，至少覆盖：
   - enabled
   - adapter loaded
   - trace writable
   - mirror writable
2. regression 能被明确纳入默认 Gate 或被清楚记录为待接入项
3. 真相源同步检查通过，或给出最小补齐改动
4. 生成 N1 报告，并更新 `runtime/RUN_STATE.json`

## 硬约束
- 不允许重新定义 Proto-Self 架构
- 不允许把治理收尾写成主体升级
- 不允许把一次性脚本当成永久制度，除非明确挂入主流程
- 不允许无证据声称“后续再也不会漂”

## 允许修改
- EgoCore 下的 Gate / preflight / regression 接线
- 文档索引与状态页
- 报告模板与脚本壳

## 禁止修改
- Proto-Self 本体语义
- OpenEmotion 的主体解释逻辑
- 无关运行时模块

## 必交付物
- preflight 方案或脚本
- Gate 接线说明或代码
- 真相源同步结果
- `reports/N1_REPORT.md`
- `runtime/RUN_STATE.json` 更新

## 必须记录的证据
- preflight 运行输出
- regression 运行输出
- 更新或核对过的真相源路径
- 若未全部通过，明确卡点

## Gate 重点
- Gate A：不越权
- Gate B：preflight / regression 本地可跑
- Gate C：至少给出真实脚本输出
- Gate D：真相源同步明确

## 失败出口
若发现 regression 或 preflight 还不具备可信接线条件：
- 停止继续做 N2
- 在报告中标记 `partial` 或 `blocked`
- 明确缺口与最小补齐动作
