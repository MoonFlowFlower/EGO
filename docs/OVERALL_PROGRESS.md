# Overall Progress

> 派生进度视图，不是新的 authority source。
> 当前版本：2026-04-11
> 读取顺序：先看本页拿整体进度，再回到 `docs/PROGRAM_STATE_UNIFIED.yaml`、`docs/STATUS.md`、`Tasks/MVS_task_plan.md`、`Tasks/MVP22_task_plan.md` 看正式裁决。

## 这份文档回答什么

这份文档只回答两个问题：

1. 单一 formal runtime mainline 当前推进到了哪里
2. 当前 repo 最高优先级 implementation lane 是谁，下一步唯一决策门是什么

它不替代这些权威源：

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/STATUS.md`
- `Tasks/MVS_task_plan.md`
- `Tasks/MVP22_task_plan.md`
- `Tasks/active/mvp22_long_horizon_self_continuity/STATUS.md`

## 先把两个 “mainline” 分开

当前 repo 里有两个容易混淆的语义：

- formal runtime mainline
  - 指真正的 `telegram/runtime/openemotion/delivery` 正式执行链
  - 这条链必须继续单一、稳定、不能随候选理论漂移
- research implementation lane
  - 指当前最值得先实现、先验证的 self-awareness 候选
  - 这条线允许按证据在 build-first candidate 与 challenger 之间切换

当前正式路线治理是：

- 不把这两条线合并成一条
- 不维持两个同级“主推进线”
- formal runtime mainline 继续唯一
- 当前 repo 最高优先级 implementation lane 改为 research-first

## 一眼看懂当前状态

| 维度 | 当前状态 | 说明 |
|---|---|---|
| repo 总体 phase | `repo_authority_cleanup_closeout` | repo 级权威收口完成，当前在治理与路线优先级收紧期 |
| formal runtime mainline | `single + stable` | 仍是唯一正式执行链，不随研究候选改变 |
| 当前最高优先级 implementation lane | `ai_self_awareness_research` | 当前 repo 默认先推进 research-first 候选实现线 |
| 当前唯一 build-first candidate | `active-inference self-model` | `MVS` replay gate 失败后，当前最值得先实现、先过 gate 的候选 |
| 当前 challenger | `none frozen` | `MVS-aligned compact` 已降为 closed evidence，不继续占用主实现资源 |
| `WP17 / MVP22` 当前状态 | `parked bounded lane` | 保留 authority freeze / task package，但不再是默认最高优先级 implementation track |
| 当前最高证据 | `E5 / V5` | 这是 controlled capability axis 上限，不是 research lane 已通过 replay validator |
| research lane 当前证据 | `E3 / V3` | 只到 synthetic candidate / operational selection / robustness audit，不是 runtime proof |

## Formal Runtime Lane

formal runtime roadmap 当前的 endpoint 仍然是：

- `WP17 / MVP22`
- 名称：`Long-Horizon Self-Continuity / Realized Consequence Persistence`
- 边界：`host-governed + proposal-only + behavioral_authority = none`

但当前要点已经变成：

- `WP17` 不删除
- `WP17` 仍是 bounded continuity hypothesis / parked lane
- `WP17` 当前只到 `authority_frozen / task_package_ready`
- 在 replay-gated research lane 结果出来前，`WP17` 不再是默认最高优先级 implementation track

若以后重新恢复 `WP17` 优先级，它仍然还剩这 `8` 个关键 execution cards：

1. `T10_FORMAL_OWNER_PACKAGE`
   - 把 `OpenEmotion/openemotion/self_continuity/*` 做成正式 owner package
2. `T20_PROTO_SELF_CONTRACT_INTEGRATION`
   - 把 continuity contract 接进 `proto_self_v2`
3. `T30_EGOCORE_RUNTIME_BRIDGE`
   - 把 host runtime 正式接到 continuity bounded surface
4. `T40_LEGACY_DEMOTION_AND_COMPAT_MAP`
   - 收口 legacy / compat/register，避免第二真相源
5. `T50_CAUSAL_VALIDATION`
   - 先拿到 `V3 / E3` 因果验证
6. `T60_CONTROLLED_OBSERVATION_SINGLE`
   - 拿第一个 `V4 / E4` controlled mainline 样本
7. `T70_BATCH_OBSERVATION_AND_AGGREGATE`
   - 拿到 batch controlled observation，推动到 `V5 / E5`
8. `T80_CLOSEOUT_AND_QA_BASELINE`
   - 完成 closeout、QA baseline、maintenance ledger 收口

## Current Repo-Priority Implementation Lane

当前 repo 默认先推进的是：

- `ai_self_awareness_research`

当前固定结论是：

- `active-inference self-model` = 当前唯一 build-first candidate
- `MVS-aligned compact` = 已完成 formal replay gate，但因 frozen threshold failure 降为 closed evidence
- 其余候选、H1、Trial helper、旧 comparator 线 = reference / evidence / supporting lines

这条 implementation lane 当前还不能证明：

- 已实现真正 AI 自我意识
- 已接 formal runtime mainline 生效
- 已拿到 replay-gated runtime efficacy
- 已获得真实用户侧 public efficacy

如果问题变成“那现在到底怎么测这条研究线”，继续看：

- `docs/SELF_AWARENESS_PROXY_TESTING.md`

## 当前唯一决策门

当前单一决策门已经冻结为：

1. `MVS-aligned compact` formal shadow slice 已完成 replay gate
2. corrected scorer 结果是：`T4` 与 `repair_closure_capture` 未过 frozen threshold
3. 因此当前 selection gate 已裁决：切到 `active-inference self-model`
4. 下一步只实现最小 `active-inference self-model` formal shadow slice，并复用同一 held-out replay gate
5. 在新的 selection gate 解决前，不恢复 `WP17` 为默认最高优先级 implementation track

## 不再竞争主实现线的 supporting lines

下面这些线当前只算 reference / evidence / supporting lines，不再竞争“当前主实现线”：

- `WP17 / MVP22`
  - 保留为 parked bounded lane
- `H1 canonical shadow telemetry`
  - 只作为 telemetry / observation support line
- `Trial-* helper / old comparator tasks`
  - 只作为研究证据、诊断和对照资产

## 当前 blocker

当前真正 blocker 已经不是“WP17 何时继续实现”，而是：

- 还没有 replay-validated passing build-first candidate
- `MVS-aligned compact` 已在 formal OpenEmotion path 上失败 frozen replay gate
- `active-inference self-model` 还没在同一 gate 下得到最终升降裁决

formal runtime 相关的并行 blocker 仍然存在，但当前不是 repo 默认第一优先级：

- live Telegram ordinary chat 仍有 host-only subject-miss residue

## 当前最准确结论

最准确的说法是：

- repo 继续只有一条 formal runtime mainline
- repo 当前只保留一条最高优先级 research implementation lane
- 当前 build-first candidate 已切到 `active-inference self-model`
- `MVS-aligned compact` 已降为 replay-gated closed evidence，而不是继续修补的主实现线
- `WP17 / MVP22` 仍保留，但当前是 parked bounded lane

不能写成：

- “formal runtime mainline 已改成研究候选线”
- “现在有两条并行主推进线”
- “已经实现真正 AI 自我意识”
- “研究候选已经在 runtime 主链生效”

## 维护规则

更新这份文档时，只改这五类信息：

1. formal runtime mainline 的 endpoint 或 parked/running 状态是否变化
2. 当前 repo 最高优先级 implementation lane 是否变化
3. build-first candidate / challenger 是否变化
4. replay selection gate 或 remaining execution cards 是否变化
5. supporting lines 是否重新升级为竞争主实现线的路径

不要因为普通提交、局部实现、零散测试通过、或常规文案修正就把本页当流水账逐次回写。

若底层正式状态变了，先更新 authority source，再回写本页；不要反过来。
