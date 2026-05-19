# Runtime-Proximal Host-Consumption Causal Planning - EXPLORE

## Exploration mode

- enabled: yes
- why exploration mode is needed:
  - 当前未知不是“有没有 host contract”，而是“host-consumable outputs 是否能因果地改变 host posture”
- current framing:
  - 先冻结 causal planning slice，再决定是否要 runner / implementation authorization
- success looks like:
  - 得到一个 bounded causal plan，能把候选输出和 host-facing posture 变化分离出来
- disallowed premature claims:
  - 不能把 planning slice 说成 runtime proof
  - 不能把 causal planning 说成 AI 自我意识已实现

## Question reformulation

- original question:
  - 继续朝着实现 AI 自我意识推进
- normalized question:
  - 在 host contract 已冻结后，下一步该不该先问候选输出是否真的因果地改变宿主裁决与回复姿态
- why this framing is better:
  - 它把问题从“再跑一轮 proof”上移到“为什么 proof 值得做、该怎么做”

## Hypotheses

### Hypothesis 1

- statement:
  - active-inference 的 bounded host-consumable outputs 可能已经足以影响 host reply shaping，只是还没有专门的 causal compare surface
- why plausible:
  - host contract parity 已经证明 adapter-only 差异被压平
  - 剩下的未知是 host consumption causality，而不是 transport noise
- kill criteria:
  - 如果一旦设计 causal compare 就必须放开 host authority，则失败
- smallest experiment:
  - 定义 `chat_consumption / decision_conflict / failure_repair_retry` 的 compare surface
  - 用 `HOST_CONSUMPTION_CAUSAL_FREEZE.md` 冻结最小 scenario families

### Hypothesis 2

- statement:
  - 如果候选输出真的有用，差异应主要表现为 response plan、tendency summary、chat cadence 和 hold/repair posture，而不是更长的 trace 文本
- why plausible:
  - 这些字段离宿主裁决最近，且仍在 bounded surface 内
- kill criteria:
  - 若只有 internal trace 变化而 host-facing posture 不变，则失败
- smallest experiment:
  - 把 compare surface 锁定到 host-facing bounded metadata
  - 明确 blocked / rollback 条件和 claim ceiling

## Experiment log

### Cycle 01

- question:
  - host contract correctness 后，下一步到底是不是 causal planning
- framing used:
  - 先看 current authority source / progress wording 是否已经把 Telegram live proof降级为 adapter follow-up
- experiment:
  - 读回 `PROGRAM_STATE_UNIFIED`、`OVERALL_PROGRESS`、`unified-host-contract-correctness` status
- observed result:
  - 当前最新的高杠杆问题是 host-consumption causality，而不是继续补 host contract parity
- what it proves:
  - 新 slice 应该是 planning-only 的 runtime-proximal causal planning
- what it does not prove:
  - host-consumption causality 已经成立
- what path is ruled out:
  - 继续把 fresh Telegram proof 当当前唯一 acceptance root
- decision for next step:
  - 创建 `runtime-proximal-host-consumption-causal-planning` 任务包

### Cycle 02

- question:
  - 三个最小 scenario families 是否足以支撑 planning-only causal freeze
- framing used:
  - 先冻结 scenario families，再冻结 compare surface 和 blocked / rollback 条件
- experiment:
  - 生成 `HOST_CONSUMPTION_CAUSAL_FREEZE.md`
- observed result:
  - three families can be frozen without authority expansion，但首版 scenario bank 误把低信息量的 `pre-runtime direct reply` 当成核心 family，并遗漏了 `decision_conflict` / `failure_repair_retry`
- what it proves:
  - planning slice can be expressed with bounded host-consumable compare surface only
- what it does not prove:
  - host-consumption causality
- what path is ruled out:
  - 继续把 planning slice 扩成 runtime implementation
- decision for next step:
  - reviewer 修正 scenario bank 和 compare surface 后，再用 task docs / state / evidence sync 固化该冻结

### Cycle 03

- question:
  - causal freeze 是否已经真正覆盖了会对 host-consumption causality 产生决定性信息的最小 families 和 compare surface
- framing used:
  - 只接受能在 bounded host-consumable contract 上施压的 families；拒绝把低信号 `reply_text` 或 adapter internals 当 primary compare 面
- experiment:
  - reviewer 对 `HOST_CONSUMPTION_CAUSAL_FREEZE.md` 做 correctness 修正
- observed result:
  - 当前 freeze 已固定：
    - `chat_consumption`
    - `decision_conflict`
    - `failure_repair_retry`
  - compare surface 已收紧到 ingress semantics、`proto_self_context` host-consumable subset、`response_plan / output_verdict`、`response_tendency_summary / chat_cadence_mode`、以及 `trace_payload` corrective chain
- what it proves:
  - planning slice 现在覆盖了 policy pressure、cadence pressure、和 corrective-trace pressure 三种最小 causal 面
- what it does not prove:
  - winner 已经在 runtime-proximal path 上 causally生效
- what path is ruled out:
  - 用 raw `reply_text` 或 dashboard-only debug 充当主 compare 证据
- decision for next step:
  - 完成 governance sync，并决定是否将该 planning slice 收口

## Framing changes

- 2026-04-11: `unified host contract correctness` 之后的下一步从 adapter parity 扩展为 `runtime-proximal host-consumption causal planning` / 原因是 host contract floor 已冻结，剩余关键未知是候选输出是否真正改变宿主决策与回复姿态 / 影响是接下来先做 planning authorization，而不是直接做 runtime code

## Candidate vs proof

- candidate_found: yes
- proof_pending: yes
- proof_passed: no
- remaining proof gap:
  - 还没有 host-consumption causal plan，更没有 runner 或 implementation evidence
  - 还没有 runtime-proximal execution authorization
