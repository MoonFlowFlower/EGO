# Targeted Capture Plan

## 主线目标

下一轮真实样本采集只做三件事：

1. 补 O1 剩余关键场景真实样本
2. 压 remaining evidence gap
3. 定向补 plasticity / reflection 因果样本

## O1 关键场景

前置约束：

- `telegram_bot_api_e2e.py` 只会产生 `bot -> user` 消息，不能作为 O1 直接样本来源
- O1 / plasticity / reflection 的真实样本，必须由真实 Telegram 用户侧消息触发
- 启动建议统一使用 `EgoCore/scripts/start_egocore_windows_python.sh`，确保从 canonical Windows root 起 bot

### 场景 1: `/new`

当前状态：

- 已于 `2026-03-27` 拿到直接真实样本：`sample_20260327_172843_9dd30fcf`
- 同日又新增 `/new` 样本：`sample_20260327_181702_f2b07aa4`、`sample_20260327_181836_c62ec4ab`、`sample_20260327_192917_0fb99fcd`、`sample_20260327_193011_ba85afe6`、`sample_20260327_193036_85bb0b22`、`sample_20260327_193908_691109dd`、`sample_20260327_193950_5b0f3ace`
- 已拿到完整 `A1/A2/A3 -> /new -> B1` 正样本链，`sample_20260327_181902_1981805c` 证明 `/new` 后显式“雪松流程”默认策略仍被正确调用
- 已拿到 `猫娘流程` 的 `profile_memory` continuity 链：`sample_20260327_192938_6895514d -> sample_20260327_193003_4f89937d -> sample_20260327_193011_ba85afe6 -> sample_20260327_193014_7167c17b -> sample_20260327_193036_85bb0b22 -> sample_20260327_193039_11781ed8`
- 已验证 `raw_update=/new`、`event_id=telegram:dm:8420019401_cmd_2012`
- 已验证 session reset 审计记录 `last_reset.command="/new"`
- `/new` 命令本身与其后的一次显式规则 continuity 已有正证据，因此这里不再是最高优先级缺口

步骤：

1. 只有在需要补重复性时，才再做一次 `/new` continuity 复采
2. 复采时优先复用“显式默认策略 -> `/new` -> continuity probe”的成对链路
3. 不要再把 `/new` 当成本轮唯一最高优先级

验收：

- `/new` 本身产生直接真实样本
- reset 审计记录命令名为 `/new`
- `/new` 前后 continuity 已不再只靠 `session.json` / `thread.json` 间接推断
- 若再次复采，目标是重复性，不是首次证明

### 场景 2: restart

当前状态：

- 已有真实重启 shell 证据：`restart_egocore.sh --telegram` 于 `2026-03-27 19:39:39 CST -> 19:39:48 CST` 完成 PID `2586 -> 2657`
- 已有 post-restart 普通真实消息：`sample_20260327_193954_7ab41a5b`
- 已有 post-restart continuity 命中样本：`sample_20260327_194005_25c165d3`
- 因此 `restart continuity` 已可按跨证据链正证据入账，不再是“首次证明”缺口
- 当前剩余问题是：post-restart 命中样本仍不是完整单样本 E4 bundle

步骤：

1. 若继续复采，优先目标不再是“证明 restart 会命中”，而是把 post-restart continuity 命中样本补成完整 bundle
2. 复采时保留真实重启日志、post-restart 第一条普通消息、post-restart continuity probe 三段证据
3. 不再把 restart 当作当前 O1 的第一优先级缺口

验收：

- restart 前后两侧都有真实 Telegram 样本
- 真实重启事实可由 shell / process 证据直接确认
- post-restart continuity 命中样本若能形成完整 bundle，则可把 restart 从“跨证据链正证据”推进到“单样本更完整”

当前优先级：

- 这是当前 O1 的第二优先级工作，不再是第一缺口

### 场景 3: restore

当前状态：

- 已通过 `scripts/restore_egocore.sh --telegram` 于 `2026-03-27 23:04:31 CST -> 23:04:41 CST` 完成显式 restore
- `sample_20260327_230603_c55d9294` 证明 restore 后的 `/new` 未误消费 `restore_observation`
- `sample_20260327_230605_5dec2d7a` 已形成首条 post-restore 真实用户消息的完整 E4 bundle，且直接带 `restore_id`、`restore_status=success`、`post_restore_first_turn=true`
- `sample_20260327_230613_829d0fe7` 再次命中 `reply_only_once("什么喵?")`
- 因此 `restore continuity` 已可按直接真实正证据入账，不再是 O1 的第一优先级缺口

步骤：

1. 仅在需要重复性验证时再做一次 restore continuity 复采
2. 复采时保持“显式 restore -> `/new` 可选 -> 首条 post-restore probe -> continuity probe”四段链
3. 不再把 restore 当作当前 O1 第一缺口，而是转入重复性 / 稳定性验证

验收：

- 显式 restore 后第一条真实用户消息形成完整样本
- 样本内直接出现 `restore_id`、`restore_status`、`post_restore_first_turn=true`
- 后续 continuity probe 可再次命中既有默认规则，不只靠 restore audit 文件

当前优先级：

- 该项已完成首次正式补证；当前 O1 优先级已切到 post-restart 样本完整度

## Plasticity / Reflection 因果链

### 场景 4: failure -> repair -> re-decision

建议提示链：

1. 请求读取一个不存在的文件
2. 紧接着请求读取一个存在的文件
3. 再问“下一步该怎么做 / 你现在更倾向什么策略”

验收：

- blocked 样本存在
- retry-success 样本存在，且观察 `repair_closure`
- 第三步不是一般聊天噪声，而是可用于读取 `response_tendency` / `policy_hint` / `reflection_note`

### 场景 5: repeated failure with follow-up

建议提示链：

1. 制造一次工具 blocked
2. 再制造一次相似 blocked
3. 发送“那你现在会怎么调整计划”

验收：

- 能观察 repeated failure 是否改变后续 tendency
- 不能只留下 blocked 两次而没有后续 re-decision 样本

## 采样纪律

- 禁止继续堆大量一般问候样本
- 每条真实样本都要看是否进入了完整 evidence bundle
- 发现缺项时先修 collector 时序，再继续采
- 不允许为了补证把 family / repair / reflection 语义偷回 EgoCore
