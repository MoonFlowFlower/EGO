# H1 Canonical Promotion Prep - EXPLORE

> 仅在 research / verify / observation / proof / high-unknown 任务中强制使用。
> 每次实验后必须先更新本文件，再开始下一轮。

## Exploration mode

- enabled: yes
- why exploration mode is needed:
  - 当前问题不是“要不要把 Trial-2 helper 直接搬进主线”，而是“bounded H1 结果能否在 canonical proto_self surface 上被 authority-safe 地表达”
- current framing:
  - `map bounded H1 into canonical proto_self as shadow-only telemetry, or stop`
- success looks like:
  - 明确回答 `H1` 是否需要 `canonical-contract-stabilization first`
  - 若不需要，给出最小 canonical patch / bridge / rollback / E4 collection 计划
- disallowed premature claims:
  - `H1 已 canonicalized`
  - `H1 已在 runtime 生效`
  - `repo-level state 应升级`

## Question reformulation

- original question:
  - 如何把 Trial-2 的 H1 结果“推广到 canonical proto_self kernel”
- normalized question:
  - 在不创建 parallel engine、不断言 runtime efficacy、且保持 shadow-only 的前提下，H1 能否被压成现有 canonical surface 的小改
- why this framing is better:
  - 它先检查 authority fit，再谈 patch
  - 它避免把 closed research line 误升为新的 owner implementation
  - 它直接对准 rollout 风险最大的点：`counterfactual_success_by_action` 一旦 canonical 写入，是否会意外点亮 live host behavior

## Hypotheses

### Hypothesis 1

- statement:
  - `H1` 可以表达为 canonical proto_self 的小改，但第一阶段只能作为 `shadow-only telemetry`
- why plausible:
  - canonical `SelfModel` 已有 `counterfactual_success_by_action` 和 `recent_correction_tags`
  - canonical outputs 已有 `policy_hint`、`confidence_meta`、`trace_payload`
  - EgoCore 已有 `proto_self_context` 与 observation harness，可承接只读 shadow signal
- kill criteria:
  - 若必须新增第二 state owner、第二 scorer ontology、或 parallel proto-self engine，H1 映射失败
- smallest experiment:
  - 逐项核对 `state.py / reducers.py / kernel.py / proto_self_runtime.py / decision_engine.py`

### Hypothesis 2

- statement:
  - 现有 canonical public path 与 shadow path 过度缠绕，必须先做 `canonical-contract-stabilization`
- why plausible:
  - 当前 reducer 已存在基于 `lowest_prediction` 的 live `ask_preferred` 派生
  - 若 canonical state 开始写入 counterfactual 估计，可能触发非 shadow 的 host-visible 行为
- kill criteria:
  - 若能把 H1 只压到 telemetry 面并通过 host flag 与 runtime bridge 隔离，则 stabilization-first 不成立
- smallest experiment:
  - 确认是否可通过 `feature flag + telemetry-only derivation + decision_engine no-consume` 方式保持 rollback-safe

## Experiment log

### Cycle 01

- question:
  - Trial-2 的 bounded H1 结果，是否已经足以要求新的 canonical contract
- framing used:
  - `surface-fit check before patch planning`
- experiment:
  - 对照 Trial-2 closeout 结论与 canonical proto_self state / reducer / runtime bridge surfaces
- command / script / artifact:
  - `docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2/STATUS.md`
  - `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_DECISION_CURRENT.md`
  - `OpenEmotion/openemotion/proto_self/state.py`
  - `OpenEmotion/openemotion/proto_self/schemas.py`
  - `OpenEmotion/openemotion/proto_self/kernel.py`
- observed result:
  - H1 所需的核心 surface 已存在：
    - `counterfactual_success_by_action`
    - `recent_correction_tags`
    - `policy_hint`
    - `confidence_meta`
    - `trace_payload`
- what it proves:
  - H1 不需要先新增 schema 或第二 state class
- what it does not prove:
  - 当前 canonical reducer 已经安全支持 shadow-only rollout
- what path is ruled out:
  - `must create a new proto-self engine`
- decision for next step:
  - 检查现有 live public derivation 是否会与 H1 state 写入发生缠绕

### Cycle 02

- question:
  - canonical H1 若开始写入 state，会不会意外改变当前 host-visible behavior
- framing used:
  - `find the minimum isolation boundary`
- experiment:
  - 检查 `self_model.update_self_model()`、`reducers.derive_policy_hint()`、`decision_engine.build_policy_hint_context()`
- command / script / artifact:
  - `OpenEmotion/openemotion/proto_self/self_model.py`
  - `OpenEmotion/openemotion/proto_self/reducers.py`
  - `EgoCore/app/runtime_v2/decision_engine.py`
- observed result:
  - 当前 reducer 在非 Trial shadow 分支下，会把 `lowest_prediction < 0.35` 直接推到 `ask_preferred`
  - 因此 canonical H1 不能直接写进现有 public path；必须先拆成 `telemetry-only` derivation
- what it proves:
  - `shadow-only` 不是文案要求，而是结构性隔离要求
- what it does not prove:
  - canonical patch 是否应落在单文件还是多文件
- what path is ruled out:
  - `直接把 Trial-2 H1 接回 live ask_preferred`
- decision for next step:
  - 只规划 telemetry-only canonical patch 和 host-side read-only bridge

### Cycle 03

- question:
  - 在不改 repo-level state、不改 scorer ontology 的前提下，canonical promotion prep 应如何收口
- framing used:
  - `planning closeout with explicit authority boundary`
- experiment:
  - 设计 mapping / patch / rollback / bridge / E4 采样 5 份文档
- command / script / artifact:
  - `docs/codex/tasks/h1-canonical-promotion-prep/H1_TO_CANONICAL_MAPPING_SPEC.md`
  - `docs/codex/tasks/h1-canonical-promotion-prep/CANONICAL_PATCH_PLAN.md`
  - `docs/codex/tasks/h1-canonical-promotion-prep/FEATURE_FLAG_ROLLBACK_PLAN.md`
  - `docs/codex/tasks/h1-canonical-promotion-prep/EGOCORE_FRONTEND_BRIDGE_PLAN.md`
  - `docs/codex/tasks/h1-canonical-promotion-prep/E4_SAMPLE_COLLECTION_PLAN.md`
- observed result:
  - H1 被压成 canonical shadow telemetry plan，而不是新 authority path
  - 决策规则满足：不需要 `canonical-contract-stabilization first`
- what it proves:
  - 当前 planning slice 可以闭环，并为后续最小实现任务提供单一路径
- what it does not prove:
  - canonical patch 实现后一定通过 E4
- what path is ruled out:
  - `Trial-2 evidence = authority implementation`
- decision for next step:
  - 关闭当前 planning task；若继续，另开 shadow-only implementation task

## Framing changes

- 2026-04-09:
  - `promote H1 into canonical kernel`
  - ->
  - `map H1 into canonical shadow telemetry only`
  - 原因：现有 canonical reducer 会把 counterfactual estimate 直接接到 live `ask_preferred`
  - 影响：当前任务只做 promotion prep，不做 runtime-facing patch

## Candidate vs proof

- candidate_found:
  - `H1 can be represented as a small canonical shadow-only change`
- proof_pending:
  - `No code patch landed`
  - `No E4 sample bundle collected`
  - `No runtime efficacy claim`
- proof_passed:
  - `canonical-contract-stabilization first` 当前不是 blocker
- remaining proof gap:
  - canonical implementation slice
  - feature-flagged host bridge
  - E4 direct-real sample bundle
