# Blockers And Stop Reasons

## 本轮为什么必须停在“准入拒绝”

### 1. replay / audit insufficiency

- 观察窗口真实样本 `89`
- 完整样本 `60`
- 缺项样本 `29`

这不是小噪声，而是会直接削弱结论强度的正式 blocker。

### 2. identity continuity 覆盖不足

- 已拿到多个 `/new` 的直接真实样本，并且 session reset 审计记录 `command="/new"`
- 已拿到一条完整 `/new` 后显式规则 continuity 正样本链：`A1/A2/A3 -> /new -> B1`
- 已拿到 `猫娘流程` 在多次 `/new` 后持续命中同一 `profile_rule` 的真实链
- 已拿到 `restart continuity` 的跨证据链正证据：真实重启 shell 日志 + `sample_20260327_194005_25c165d3`
- 但 `restore` 仍没有直接真实样本，且 post-restart 命中样本仍不是完整单样本 E4 bundle
- 现有 `telegram_bot_api_e2e.py` 只能发送 `bot -> user` 消息，不能制造 `user -> bot` 的真实 ingress
- 当前仓库也明确不接入 `TDLib / Telethon`，因此缺少可自动生成真实入站样本的用户侧客户端

这已经把 O1 从“只有 `/new` 命令正证据”推进到“`/new continuity` 与 `restart continuity` 都已有强真实正证据”，但仍不足以支撑 O1 的完整通过。

### 3. plasticity / reflection 仍偏弱

- `response_tendency` 确实有变化，但主要集中在短期局部上下文
- `reflection_note` 在窗口内完全同型，尚不足以证明 reflection 本体稳定写回

## 当前停止条件

在以下任一条件未补齐前，不应进入 Developmental Self：

1. `restore` 真实样本补齐，且 post-restart continuity 命中样本若可能则补成更完整 bundle
2. 观察窗口 evidence gap 显著下降
3. plasticity / reflection 拿到更直接、可重复的真实因果证据

## 允许继续前的最小动作

- 用 `EgoCore/scripts/start_egocore_windows_python.sh` 从 canonical Windows root 起 bot
- 由真实 Telegram 用户侧消息优先完成 `restore` continuity 采样，并在需要时补一次更完整的 post-restart continuity 命中样本
- 先把观测窗口延长到 `3-7` 天
- 再做定向真实样本采集
- 最后重新跑一次准入评审，而不是直接开做下一阶段能力
