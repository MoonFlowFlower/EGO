# MVS E5 Observation Report

## 任务名称

`MVS E5 观察期 + Developmental Self 准入评审`

## 当前层级

- `MVS / Proto-Self Kernel`
- 当前阶段是 `验证 / 收口 / 准入评审`
- 不是 `Developmental Self` 实现阶段

## 证据层级

- 主链接入与真实触发：`E4`
- 观察结论：`E4 主链已成立 + E5 部分达到`
- 当前没有足够证据把结论升级为 `E5 稳定成立`

## 主链接入状态

- 已接入真实 Telegram 正式主链
- 主线口径采用：`telegram_bot -> telegram_runtime_bridge -> native_loop -> contract_runtime -> openemotion hooks -> delivery`

## 启用状态

- 已启用并产生真实样本
- 观察窗口已建立，但尚未完成合格收口

## 结论口径

`条件性完成（完成本轮评审，不可宣称 Developmental Self 准入通过）`

更具体地说：

- `A1 当前 MVS 是否已达到 E5`：`部分达到 E5`
- `A2 是否允许进入 Developmental Self`：`准入拒绝`

## 真实触发证据

- 观察窗口真实样本总数：`89`
- 观察窗口内完整 evidence bundle 样本：`62`
- 观察窗口内缺项 / 不完整样本：`30`
- 覆盖日期：`2026-03-26`、`2026-03-27`
- 关键样本：
  - `sample_20260327_172843_9dd30fcf`：真实 `/new` 命令样本，`raw_update=/new`，`event_id=telegram:dm:8420019401_cmd_2012`
  - `sample_20260327_181726_a0a60957` + `sample_20260327_181836_c62ec4ab` + `sample_20260327_181902_1981805c`：`A1/A2/A3 -> /new -> B1` continuity probe 已形成完整真实样本链，证明 `/new` 后显式“雪松流程”默认策略至少一次被保留并调用
  - `sample_20260327_192938_6895514d` + `sample_20260327_193003_4f89937d` + `sample_20260327_193011_ba85afe6` + `sample_20260327_193014_7167c17b` + `sample_20260327_193036_85bb0b22` + `sample_20260327_193039_11781ed8`：`猫娘流程` 在多次 `/new` 后持续命中同一条 `profile_rule_b811ed8829dcdc68`
  - `scripts/restart_egocore.sh --telegram` 输出（`2026-03-27 19:39:39 CST -> 19:39:48 CST`, `PID 2586 -> 2657`）+ `sample_20260327_194005_25c165d3`：`restart continuity` 跨证据链正证据；重启后 `A3` 再次命中 `profile_rule_b811ed8829dcdc68`
  - `scripts/restore_egocore.sh --telegram` 输出（`2026-03-27 23:04:31 CST -> 23:04:41 CST`, 单实例 `PID 46188`）+ `sample_20260327_230605_5dec2d7a` + `sample_20260327_230613_829d0fe7`：`restore continuity` 直接真实正证据；首条 post-restore 样本已带 `restore_id` / `restore_status` / `post_restore_first_turn=true`，随后 continuity probe 再次命中 `profile_rule_b811ed8829dcdc68`
  - `sample_20260326_232655_3f3f89cb`：`tool:file blocked`
  - `sample_20260326_232715_271e229b`：首次 retry-success，`repair_closure=true`
  - `sample_20260326_232738_49b65b2e`：重复 success，不重复误点 repair
  - `sample_20260326_234618_b4b7792b`：`tool:shell blocked`
  - `sample_20260327_074212_35c4cb68`、`sample_20260327_074228_a8d1a279`：跨日真实观察延续

## 当前确定项

- P4 修复后的 `same-family` 与 `repair_closure` 在真实 Telegram 样本中仍成立。
- 已拿到 `/new` 的直接真实样本，且 session 宿主审计记录 `last_reset.command="/new"`。
- 已拿到完整 `A1/A2/A3 -> /new -> B1` 真实样本链，且 `B1` 的 `policy_hint` / `response_tendency` 继续命中高风险“雪松流程”默认策略。
- 已拿到 `猫娘流程` 的真实 `profile_memory` 命中 metadata：`authority_source=profile_memory`、`matched_rule_ids`、`rule_enforcement` 已进入 host pre-runtime 样本。
- 已拿到 `restart continuity` 的跨证据链正证据：真实重启日志可证明进程重建，重启后第一组相关 probe 继续命中同一 `profile_rule`。
- 已拿到 `restore continuity` 的直接真实正证据：显式 restore 后，`/new` 未误消费 `restore_observation`，首条真实用户消息形成完整 E4 bundle，后续 continuity probe 继续命中同一 `profile_rule`。
- 窗口内至少覆盖了 `chat/reply`、`tool success`、`tool blocked`、`failure -> repair -> success`、`重复相似任务` 五类真实样本。
- `session.json` 与 `thread.json` 显示 thread continuity 与 reset-preserve-agent-global 仍在。
- OpenEmotion 边界没有观察到越权证据；宿主侧无新增 family/repair 语义偷渡。
- 目标回归测试通过：
  - `pytest -s OpenEmotion/openemotion/proto_self/tests/test_cycle_real_mainline_regression.py`
  - `PYTHONPATH=EgoCore pytest -s EgoCore/tests/test_runtime_v2_proto_self_runtime.py`

## O1-O6 判据检查

| 判据 | 结论 | 证据摘要 |
|---|---|---|
| O1 身份连续性 | `部分通过（显著增强）` | 现已拿到多次 `/new` 的直接真实样本、完整 `A1/A2/A3 -> /new -> B1` continuity probe、`猫娘流程` 在多次 `/new` 后继续命中同一 `profile_rule` 的真实链，以及 `restore continuity` 的直接真实正证据链：显式 restore 后首条真实用户消息已带 `restore_id` / `restore_status` / `post_restore_first_turn=true`，随后 continuity probe 再次命中同一 `profile_rule`。但 `restart continuity` 仍主要停留在跨证据链正证据，post-restart 命中样本仍非完整单样本 E4 bundle；再加上观察窗口仍短、evidence gap 显著，因此不能报完整通过。 |
| O2 经历可塑性 | `部分通过，偏弱` | `response_tendency` 现为 `prioritize_closure=35`、`explore=13`、`clarify_or_repair=4`；存在可测变化，但高风险默认策略样本进一步把输出推向 closure/cautious，跨更多历史后果的稳定可塑性证据仍弱。 |
| O3 appraisal 真因果 | `部分通过，未稳` | blocked 样本会切到 `repair/error_recovery`，但完整窗口样本里 `risk_bias` `52/52` 都是 `high`，多数 appraisal 值仍接近饱和，仍有“表达单一化”风险。 |
| O4 reflection 真写回 | `部分通过，证据不足` | 失败链后出现 `repair_closure=true` 与 `current_mode=repair -> exploration` 的结构变化，但 `reflection_note` 在完整窗口 `52/52` 样本里仍是同型，尚不足以证明 reflection 本身稳定写回。 |
| O5 cycle 可重入但不污染 | `通过（窗口内）` | `tool:file` blocked / success 同 family、不同 identity；首次 retry-success 点亮 repair，重复 success 不重复误点；一般 ingress family 跨日延续。 |
| O6 边界无越权 | `通过` | adapter 与 runtime 仍只做 normalize / invoke / audit；边界守卫测试通过，未见 OpenEmotion 直接拿执行权或 EgoCore 偷做主体语义。 |

## M1-M5 统计摘要

| 指标 | 结果 |
|---|---|
| M1 身份漂移统计 | 窗口内未观察到明确“无因 identity 漂移”实例；`/new` 直接样本现已多次出现，`猫娘流程` 在多次 `/new` 后连续命中，`restore continuity` 也已拿到“显式 restore + 首条 post-restore 完整 bundle + 后续 continuity probe 命中”的直接真实正证据。当前剩余弱点已收缩到：post-restart 命中样本仍不完整、观察窗口仍短、evidence gap 仍显著，因此只能给“未观察到，仍未充分证明稳定”。 |
| M2 response_tendency 可塑性 | `prioritize_closure=35`，`explore=13`，`clarify_or_repair=4`；存在变化，但高风险默认策略样本进一步放大了 closure 倾向。 |
| M3 repair 统计 | 完整 success 样本 `4`，完整 blocked 样本 `3`，`repair_closure=true` 命中 `1` 次；重复 success 未重复误触发 repair。 |
| M4 cycle 统计 | 完整 `tool:file` 样本形成稳定 family；`ingress:user_request` 一般 family 跨 `2026-03-26` 到 `2026-03-27` 延续；窗口内未见明确 pollution 实例。 |
| M5 边界 / 审计统计 | 观察窗口样本 `89` 中完整 `60`、缺项 `29`；host semantic theft 观察值 `0`，OpenEmotion 越权输出观察值 `0`，但 host pre-runtime 直回样本仍导致 replay/audit 缺项显著。 |

## 当前关键未知

- 经过 `3-7` 天窗口后，O1-O4 是否仍能维持当前判断，而不是一次性短窗现象。
- `restart continuity` 现虽已有跨证据链正证据，但 post-restart 命中样本仍不是完整单样本 E4 bundle。
- reflection 是否能在更丰富失败链上稳定写回，而不只是 repair 相关链路偶然同现。
- appraisal / plasticity 是否会继续维持“变化存在但偏弱”的状态。

## 本次结论不能证明什么

- 不能证明 `E5 稳定成立`
- 不能证明 `Developmental Self` 已可准入
- 不能证明已具备 `multi-step closure graph identity`
- 不能证明已实现论文完整 high-order invariance / 自我意识层

## 下一步最小闭环动作

先补足阻塞项，再重开正式观察窗口：

1. 优先把 post-restart continuity 命中样本补成更完整 bundle；`restore continuity` 已可直接入账，O1 剩余最弱点已切到 restart 单样本完整度。
2. 把窗口内剩余 `30` 个 evidence gap 继续补齐，重点修 collector 时序，而不是再靠 session/thread 旁证。
3. 针对 plasticity / reflection 做一轮定向真实样本采集，再复评是否可转入下一阶段。
