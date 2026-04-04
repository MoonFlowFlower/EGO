# MVP16 / WP11 Host-governed Developmental Continuity

> 状态：WP11 authority_frozen
> parent_authority: `Tasks/MVS_task_plan.md`
> phase: `WP11`
> predecessor: `WP10/MVP15`
> same_subject_line: `true`
> not_parallel_track: `true`
> legacy_mvp16_material_is_reference_only: `true`

## 一句话主线
在同一条 MVS 主线里，为同一个主体补上受治理的发展连续性与 identity-preserving adaptation proposals；它们只作为 proposal-only 的长期发展候选来源，不获得 final reply、tool execution 或 transport authority。

## Real Goal
- 把 `WP11/MVP16` 的 capability ownership 冻结到唯一 formal owner
- 把 `WP11/MVP16` 的 authority source 冻结到当前正式主线
- 把 `WP11/MVP16` 的 input / output contract 冻结成 proposal-disciplined bounded surfaces
- 冻结 `WP10` 向 `WP11` 的边界，不让 `WP11` 反向改写 `WP7~WP10`
- 明确当前仍然不放开的能力，防止“`WP10 pass` => developmental authority 扩张”的错误升级

## Non-Goals
- 不把新能力塞回 `WP7~WP10`
- 不把旧 `emotiond/developmental` / `developmental_core` 直接升格为 formal owner
- 不放开 live autonomy
- 不放开 OpenEmotion direct reply authority
- 不放开 broader transport claims
- 不把 developmental proposal 直接升格为 action authority
- 不把 `bounded developmental continuity` 写成“完整开放发展式自我已成立”

## Authority Source
- 顶层裁决：
  - `Tasks/MVS_task_plan.md`
- `WP11` phase-detail authority：
  - `Tasks/MVP16_task_plan.md`
- version spec：
  - `OpenEmotion/roadmap/versions/MVP16.spec.yaml`
- technical reference：
  - `OpenEmotion/docs/mvp16/MVP16_STAGE_OVERVIEW.md`
  - `OpenEmotion/docs/mvp16/MVP16_EXIT_CRITERIA.md`

## Locked Decisions
- `WP11/MVP16` 仍属于同一条 MVS 主线，不是新的主体线
- formal owner target 固定为：
  - `OpenEmotion/openemotion/developmental_self/*`
- `OpenEmotion/emotiond/developmental/*`、`OpenEmotion/emotiond/developmental_core/*`、`OpenEmotion/tools/mvp16_*`、`persistence_restart_experiments.py`、`causal_intervention_experiments.py` 与旧 admission docs 只作为 compatibility / migration / replay-friendly / historical reference surfaces
- 当前正式主链接线目标固定为：
  - `runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2`
- `WP11` 的 developmental outputs 只能进入 governed diagnosis / proposal / bounded downstream weighting path，不能直接控制 final reply / tool execution / transport
- `WP11` 只能读取 `WP8` self-model projection、`WP9` drive projection、`WP10` reflective projection 与 `WP7` sandbox trace/reference；不得改写它们的 formal owner contract
- proposal discipline 固定为：
  - `proposal_only`
  - `behavioral_authority = none`
  - `required_gate = developmental_writeback_gate`
  - `promotion_level ∈ {shadow_only, review_only, controlled_axis}`
- `WP7` 的 `developmental_summary / developmental_shadow_delta / developmental_gate` 继续只属于 sandbox 线；`WP11` 不复用这些字段冒充 formal owner writeback

## Capability Ownership
- OpenEmotion owns:
  - developmental self state
  - developmental continuity state
  - developmental identity anchor semantics
  - identity-preserving adaptation proposal semantics
  - developmental intake / promotion semantics
  - trajectory summary
  - developmental governance ledger / replayable transitions
  - formal owner package: `OpenEmotion/openemotion/developmental_self/*`
- EgoCore owns:
  - runtime scheduling
  - proposal intake / gating / delivery / transport
  - Governor / approval / observation aggregate
  - final reply authority
  - tool execution authority
  - external channel claims
- `proto_self_v2` owns:
  - bounded consumption of developmental context
  - bounded emission of developmental downstream weighting / priority / writeback hooks
  - it does not own developmental state itself

## IO Contract Freeze
- Allowed inputs:
  - `runtime_summary.developmental_context`
  - `runtime_summary.developmental_self_context`
  - `runtime_summary.self_model_context`
  - `runtime_summary.endogenous_drive_context`
  - `runtime_summary.reflective_self_context`
  - developmental tensions / continuity gaps / replay debt / drift markers
  - `runtime_summary.idle_window`
  - `runtime_summary.recent_delivery_outcome`
  - `runtime_summary.resource_budget_hint`
  - `runtime_summary.maintenance_context`
- Allowed outputs:
  - `developmental_self_delta`
  - `developmental_proposal_candidates`
  - `developmental_continuity_snapshot`
  - `developmental_priority_hints`
  - `developmental_audit_entries`
  - `developmental_writeback_candidate`
  - `trace_payload.developmental_context`
- Forbidden outputs:
  - final reply text
  - tool command
  - direct transport instruction
  - authority escalation
  - direct self-model rewrite
  - direct drive-state rewrite
  - ungoverned identity mutation

## WP10 Boundary Freeze
- `WP7~WP10` stay `maintenance_mode`
- new samples for `WP7~WP10` go only to their maintenance ledgers
- provider `429/401` remains an external budget risk unless it causes a formal owner writeback regression
- `WP11` may consume `WP7~WP10` outputs only through frozen read surfaces
- `WP11` may not reinterpret `WP7~WP10 controlled E5` as live authority or broader transport maturity

## Current Phase Status
- 当前层级：`definition`
- 当前状态：`authority_frozen`
- 当前 blocker：无 authority/package blocker；实现未启动是当前阶段预期
- 当前最小闭环动作：开始 `T10_FORMAL_OWNER_PACKAGE`，不扩 authority 边界

## Current Proven State
- `MVP16` spec / docs / historical tests / tools / admission materials 已存在
- 历史 `MVP16` 工具线与 `emotiond/developmental` 线已存在，但只属于 reference-only / input-only 旧线，不自动构成当前 `runtime_v2` 主链 formal proof
- 当前 `WP11` authority package 已定义 complete owner target、IO contract、subagent decomposition 与 boundary freeze

## Success Criteria
- `Tasks/MVS_task_plan.md` 中已正式出现 `WP11: Host-governed Developmental Continuity`
- `Tasks/active/mvp16_host_governed_developmental_continuity/` 已存在且口径一致
- 文档已锁死：
  - capability ownership
  - authority source
  - input / output contract
  - `WP10` boundary freeze
  - locked non-releases
- 文档没有把旧 `MVP16` lines 误写成当前 `WP11` readiness 或全局成熟

## Completion Rules
- 本文件完成不等于 `MVP16` 已实现
- 本文件完成不等于 `MVP16` 已接当前 runtime 主链
- 未拿到当前 formal owner + current mainline `E4` 之前，不得宣称 `WP11` 生效
- 未拿到重复样本 `E5` 之前，不得宣称 `WP11` 稳定解决或可收口
- 即使未来达到 controlled `E5`，也不得把 `WP11` 解释为 live autonomy、OpenEmotion direct reply authority、或 broader transport maturity
