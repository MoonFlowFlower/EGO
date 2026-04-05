# MVP22 / WP17 Long-Horizon Self-Continuity / Realized Consequence Persistence

> 状态：T00 complete / authority_frozen / task_package_ready
> parent_authority: `Tasks/MVS_task_plan.md`
> phase: `WP17`
> predecessor: `WP16/MVP21`
> same_subject_line: `true`
> not_parallel_track: `true`
> legacy_mvp22_material_is_reference_only: `true`

## 一句话主线
在同一条 MVS 主线里，为同一个主体补上 host-governed、proposal-only 的 long-horizon self-continuity / realized consequence persistence；第一刀只冻结 formal owner、continuity intake / output contract、`WP8~WP16` boundary freeze 与 task package，不放开任何 direct reply / tool / transport authority，也不进入 open-world free-form autonomy。

## Real Goal
- 把 `WP17/MVP22` 的 capability ownership 冻结到唯一 formal owner
- 把 `WP17/MVP22` 的 authority source 冻结到当前正式主线
- 把 `WP17/MVP22` 的 input / output contract 冻结成 proposal-disciplined bounded surfaces
- 冻结 `WP8~WP16` upstream maintenance 边界，不让 `WP17` 反向改写既有 owner
- 明确当前仍然不放开的 continuity / persistence / restart-restore authority，防止“已有 realized loop => 已有开放自主演化”的错误升级

## Non-Goals
- 不宣称 owner/runtime 已实现
- 不宣称已接当前 runtime 主链
- 不宣称 `E4/E5`
- 不宣称 observation started
- 不宣称 maintenance mode
- 不 reopen `WP8~WP16`
- 不放开 live autonomy
- 不放开 OpenEmotion direct reply authority
- 不放开 tool execution authority
- 不放开 broader transport claims
- 不做 open-world free-form autonomy
- 不允许 direct mutation of upstream owner state
- 不创建 `WP18` docs

## Authority Source
- 顶层裁决：
  - `Tasks/MVS_task_plan.md`
- `WP17` phase-detail authority：
  - `Tasks/MVP22_task_plan.md`
- technical reference：
  - `Tasks/MVP15_task_plan.md`
  - `Tasks/MVP16_task_plan.md`
  - `Tasks/MVP17_task_plan.md`
  - `Tasks/MVP18_task_plan.md`
  - `Tasks/MVP19_task_plan.md`
  - `Tasks/MVP20_task_plan.md`
  - `Tasks/MVP21_task_plan.md`
  - `OpenEmotion/roadmap/SELF_AWARE_AI_ROADMAP.md`
  - `OpenEmotion/roadmap/VersionRoadmap.md`
- 说明：
  - 当前没有 repo-tracked `MVP22` version spec
  - 若后续新增 `MVP22` version spec，它在 authority 显式更新前只能作为 technical reference

## Locked Decisions
- `WP17/MVP22` 仍属于同一条 MVS 主线，不是新的主体线
- formal owner target 固定为：
  - `OpenEmotion/openemotion/self_continuity/*`
- 当前正式主链接线目标固定为：
  - `runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2`
- `WP17` 只拥有 long-horizon continuity / consequence persistence semantics，不拥有 `WP8~WP16` 的 upstream owner state
- phase 1 formal intake 固定为：
  - `runtime_summary.initiative_realization_context`
  - `runtime_summary.selfhood_integration_context`
  - `runtime_summary.self_model_context`
  - `runtime_summary.reflective_self_context`
  - `runtime_summary.developmental_self_context`
  - `runtime_summary.social_self_context`
  - `runtime_summary.embodied_self_context`
  - `runtime_summary.maintenance_context`
  - `runtime_summary.recent_delivery_outcome`
  - `runtime_summary.restart_restore_observation_context`
- phase 1 formal outputs 固定为：
  - `self_continuity_delta`
  - `realized_commitment_snapshot`
  - `consequence_consolidation_candidates`
  - `identity_continuity_hints`
  - `continuity_break_alerts`
  - `self_persistence_tendency`
  - `self_continuity_writeback_candidate`
  - `trace_payload.self_continuity_context`
- proposal discipline 固定为：
  - `proposal_only = true`
  - `behavioral_authority = none`
  - `required_gate = self_continuity_writeback_gate`
- phase 1 scope 固定为：
  - realized outcome consolidation
  - cross-session / cross-restart continuity
  - continuity-break detection
  - identity-preserving tendency after realized success/failure
- `WP17` 当前不放开：
  - direct reply / tool / transport authority
  - open-world free-form autonomy
  - upstream owner mutation

## Capability Ownership
- OpenEmotion owns:
  - `realized_history_state`
  - `commitment_persistence_state`
  - `identity_continuity_state`
  - `restart_restore_continuity_state`
  - `consequence_consolidation_state`
  - `continuity_break_risk_state`
  - `self_persistence_tendency`
  - `continuity_ledger`
  - formal owner target: `OpenEmotion/openemotion/self_continuity/*`
- Upstream owners remain authoritative and read-only to `WP17`:
  - `OpenEmotion/openemotion/initiative_realization/*`
  - `OpenEmotion/openemotion/selfhood_integration/*`
  - `OpenEmotion/openemotion/self_model/*`
  - `OpenEmotion/openemotion/reflective_self/*`
  - `OpenEmotion/openemotion/developmental_self/*`
  - `OpenEmotion/openemotion/social_self/*`
  - `OpenEmotion/openemotion/embodied_self/*`
- EgoCore owns:
  - runtime / session / task / tool / transport
  - outward response contract
  - ask / wait / block / escalate
  - final reply authority
  - trace / replay / gate / audit / maintenance ledger
  - real-world execution and risk adjudication
- `proto_self_v2` owns:
  - bounded consumption of continuity context
  - bounded emission of continuity candidates, snapshots, hints, and writeback candidates
  - it does not own self-continuity owner state itself

## IO Contract Freeze
- Allowed inputs:
  - `runtime_summary.initiative_realization_context`
  - `runtime_summary.selfhood_integration_context`
  - `runtime_summary.self_model_context`
  - `runtime_summary.reflective_self_context`
  - `runtime_summary.developmental_self_context`
  - `runtime_summary.social_self_context`
  - `runtime_summary.embodied_self_context`
  - `runtime_summary.maintenance_context`
  - `runtime_summary.recent_delivery_outcome`
  - `runtime_summary.restart_restore_observation_context`
- Allowed outputs:
  - `self_continuity_delta`
  - `realized_commitment_snapshot`
  - `consequence_consolidation_candidates`
  - `identity_continuity_hints`
  - `continuity_break_alerts`
  - `self_persistence_tendency`
  - `self_continuity_writeback_candidate`
  - `trace_payload.self_continuity_context`
- Forbidden outputs:
  - final reply text
  - tool command
  - transport directive
  - direct Governor bypass
  - direct authority escalation
  - direct mutation of `WP8~WP16` owner state
  - live autonomy release

## WP8~WP16 Boundary Freeze
- `WP8~WP16` 当前都继续是 maintenance / frozen upstreams
- 新样本只进各自 maintenance ledger
- `WP17` 只能读取 `WP8~WP16` 的 frozen read surfaces
- `WP17` 不得改写 `initiative_realization/*`、`selfhood_integration/*`、`self_model/*`、`reflective_self/*`、`developmental_self/*`、`social_self/*`、`embodied_self/*`
- `WP17` 不得因 continuation / persistence 语义而扩大 host authority 或 transport claims

## Current Phase Status
- 当前层级：`authority_freeze`
- 当前状态：`authority_frozen`
- 当前 blocker：`none`
- 当前最小闭环动作：`T10_FORMAL_OWNER_PACKAGE`
- 当前 claim ceiling：`T00 complete only`

## Success Criteria
- `Tasks/MVS_task_plan.md` 中已正式出现 `WP17: Long-Horizon Self-Continuity / Realized Consequence Persistence`
- `Tasks/active/mvp22_long_horizon_self_continuity/` 已存在且口径一致
- 文档已锁死：
  - capability ownership
  - authority source
  - input / output contract
  - `WP8~WP16` boundary freeze
  - locked non-releases
  - subagent assignment
  - task-card write scopes
- 文档没有把 self-continuity 漂成当前 implementation、mainline wiring、`E4/E5`、observation、或 maintenance mode

## Completion Rules
- 本文件完成只证明 `WP17/MVP22` authority 已冻结并具备 task-package readiness
- 本文件完成不等于 `MVP22` 已实现
- 本文件完成不等于 `MVP22` 已接当前 runtime 主链
- 本文件完成不等于 `MVP22` 已拿到 `E4/E5`
- 本文件完成不等于 `MVP22` 已开始 observation
- 本文件完成不等于 `MVP22` 已进入 maintenance mode
