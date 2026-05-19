# H1 Canonical Shadow Patch - PLAN

## Task summary

在 canonical `proto_self` surface 内实现 H1 shadow telemetry，并通过 EgoCore 做只读桥接与 observation hook 接线，不推广到 live public path。

## Execution mode

- mode: implementation
- why this mode: H1 mapping、flag topology、bridge plan 已在前置 planning task 冻结，这一轮只实现最小 shadow slice
- proof required after discovery: 需要用 slice-local tests 和 replay checks 证明 `flag off = no telemetry`、`flag on = telemetry only`、`live public behavior unchanged`

## Milestones

### Milestone 1: Task Freeze And Canonical Shadow Shape

- type: implementation
- question: H1 能否在 canonical state/output surface 内表达成 shadow-only telemetry，而不变成第二引擎或 live decision path
- current framing: 用 namespaced shadow keys 写入 canonical self_model surface，并在 reducer / confidence_meta 层过滤 live derivation
- hypotheses:
  - namespaced shadow keys 可以保留 canonical owner surface，同时不污染 live replay/public path
  - trace/confidence_meta 足以表达 H1 telemetry，无需 schema migration
- scope:
  - 冻结本任务的 spec / milestone / stop rule
  - 确认 canonical patch shape、flag topology、rollback boundary
- experiments planned:
  - 代码前先锁定 task docs 和 stop condition
- kill criteria:
  - 必须改 live decision surface 才能表达 H1
  - 必须新建 parallel engine 或 second authority source
- files / areas likely touched:
  - `docs/codex/tasks/h1-canonical-shadow-patch/*`
- acceptance:
  - task docs 明确 shadow-only 边界、stop rule、validation slice
- validation:
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - docs-only，无需 code rollback

### Milestone 2: Canonical Patch And Thin Bridge

- type: implementation
- question: canonical H1 telemetry 能否只作为 trace/confidence/context 被观察，而不进入 live decision input
- current framing: OpenEmotion 负责 shadow telemetry derivation；EgoCore 只做 host-owned flag 注入、read-only context bridge、observation capture
- hypotheses:
  - canonical reducer 过滤 shadow keys 后，flag on 不会改变 live `ask_preferred/ask_needed`
  - EgoCore 可保留 `shadow_h1` 到 turn 结束，供 observation hook 采样
- scope:
  - 新增 canonical H1 helper
  - 只改 canonical proto_self v1/v2 trace surfaces、runtime flag injection、context bridge、observation hook
  - 不改 decision_engine、不改 scorer、不改 repo state
- experiments planned:
  - 双路径比较：flag off vs flag on
  - replay/trace roundtrip
  - runtime bridge + observation capture
- kill criteria:
  - shadow keys 仍会进入 live public derivation
  - final turn state 无法保留 `shadow_h1` 供 observation hook 采样
- files / areas likely touched:
  - `OpenEmotion/openemotion/proto_self/*`
  - `OpenEmotion/openemotion/proto_self_v2/*`
  - `EgoCore/app/runtime_v2/proto_self_runtime.py`
  - `scripts/runtime_mainline_observation_common.py`
  - scoped tests
- acceptance:
  - `shadow_h1` 只在 flag on 且 allowlisted 时出现
  - live `policy_hint` / `response_tendency` 不被 H1 shadow path 改写
  - EgoCore 只读桥接和 observation hook 可见 `shadow_h1`
- validation:
  - `python3 -m py_compile <touched files>`
  - scoped `pytest`
  - `git diff --check -- <scoped files>`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 关闭 host flag 即回到 baseline；必要时删掉 context bridge / observation hook，不需要 schema migration

## Progress

- current_status: implemented_and_scoped_validated
- current_milestone: Milestone 2: Canonical Patch And Thin Bridge
- milestone_state: completed
- candidate_vs_proof: proof_pending

## Decision log

- 2026-04-09: 采用 namespaced shadow keys，而不是 live key 直写；原因是必须隔离 canonical live derivation；影响是需要 reducer / confidence_meta 过滤 shadow entries
- 2026-04-09: Trial-1 / Trial-2 保持只读证据源，不复用 `trial1_shadow.py` 做 owner implementation；原因是避免 parallel engine；影响是新建 canonical helper 模块

## Surprises / discoveries

- 新发现 1：`proto_self_v2` 默认经由 canonical v1 kernel，因此 v1 patch 就会进入 formal v2 主线
- 新发现 2：当前 live reducer 直接读取 `counterfactual_success_by_action` / `recent_correction_tags`，不做隔离会污染 live public path
- 已排除路线 1：直接把 H1 写进 live `ask_preferred/ask_needed`
- 已排除路线 2：继续依赖 `trial1_shadow.py` 作为 runtime owner implementation

## Outcomes / retrospective

- 本轮已证明：canonical H1 可以作为 shadow-only telemetry patch 落进 formal proto_self surface，并经由 EgoCore 只读桥接到 `proto_self_context` 与 observation hook
- 还没证明：runtime efficacy、E4 real-mainline sample quality、repo-level promotion
- 本轮排除了什么：parallel engine、live public promotion、repo-level state update
- 下一步最小闭环动作：运行专门的 E4 shadow sample collection task，在 formal runtime mainline 上采样 `shadow_h1`
