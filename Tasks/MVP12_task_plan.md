# MVP12 / WP7 Developmental Sandbox

> 状态：WP7 maintenance_mode
> parent_authority: `Tasks/MVS_task_plan.md`
> phase: `WP7`
> predecessor: `WP6`
> same_subject_line: `true`
> not_parallel_track: `true`

## 一句话主线
在同一条 MVS 主线里，为同一个主体补上受治理的 developmental sandbox；它能在正式 runtime 主链中产生 shadow-only developmental activity 和 host-governed proactive draft / send chain，但不获得 final reply、tool execution 或默认 live autonomy。

## Real Goal
- 把 `WP7/MVP12` 的 formal runtime owner 固定到当前主链
- 让 developmental activity 以 sandbox 方式进入正式 runtime ingress/egress 主链
- 让 proactive draft / idle scheduler / delivery / outbox / transport 只以 host-governed 方式出现
- 让 `WP7` 的主证据建立在 controlled observation，而不是 transport log 口头解释

## Non-Goals
- 不让 developmental sandbox 直接控制 final reply
- 不让 developmental sandbox 直接控制 tool execution
- 不把 `emotiond.daemon` 重新升格为 runtime owner
- 不把 host-governed proactive chain 误写成默认 live autonomy
- 不把单条 Telegram transport 样本误写成稳定 transport maturity

## Authority Source
- 顶层裁决：
  - `Tasks/MVS_task_plan.md`
- version spec：
  - `OpenEmotion/roadmap/versions/MVP12.spec.yaml`
- formal runtime owner：
  - `EgoCore/app/runtime_v2`
  - `EgoCore/app/runtime_v2/proto_self_runtime.py`
  - `EgoCore/app/openemotion_adapter/proto_self_adapter.py`
  - `OpenEmotion/openemotion/proto_self_v2/*`
- implementation library：
  - `OpenEmotion/emotiond/developmental_core/*`
- reference-only / historical execution surfaces：
  - `OpenEmotion/emotiond/daemon.py`
  - `EgoCore/app/openemotion_adapter/developmental_writeback.py`
  - `Tasks/active/krd_mvs_mainline/*`
  - `OpenEmotion/artifacts/mvp12/TASK.md`
  - `OpenEmotion/artifacts/mvp12/t02_task.md`
  - `OpenEmotion/artifacts/mvp12/t03_task.md`

## Locked Decisions
- formal runtime path 固定为：
  - `runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2`
- primary evidence source 固定为：
  - formal runtime ingress/egress mainline
  - `direct_real` = 穿过正式主链并留下完整 `observation_record_v1` 的真实样本
- supplemental transport evidence：
  - `telegram`
- `OpenEmotion/emotiond/developmental_core/*` 只作为实现库复用
- `emotiond.daemon` 不再是 formal runtime owner
- developmental writeback 只允许：
  - `developmental_shadow`
  - `shadow_self`
  - shadow-only writeback
- proactive chain 只允许：
  - `developmental_tick`
  - `background_thought_candidates`
  - `initiative_arbiter`
  - `controlled_idle_scheduler`
  - `pending_proactive_followup`
  - `controlled_proactive_delivery_lane`
  - `host_proactive_outbox_lane`
  - `controlled_outbox_drain`
  - `controlled_telegram_transport_bridge`
  - `feature_flagged_host_governed_proactive_telegram_auto_cycle`
  - `host_governed_proactive_telegram_enable_policy`
- live 默认：
  - `off`
- `WP7` 仍不得：
  - 直接注入 `response_plan`
  - 直接改正式 proto-self owner state
  - 声称默认 live autonomy
  - 声称 OpenEmotion direct reply authority

## Current Phase Status
- 当前层级：`closure`
- 当前状态：`maintenance_mode`
- 当前 blocker：controlled observation 范围内无主 blocker；supplemental Telegram transport evidence 仍是 single-sample `E4`，但这不阻断 `WP7` controlled-axis 收口
- 当前最小闭环动作：保持 `WP7` 维护态，新样本只追加到 `Tasks/active/mvp12_developmental_sandbox/MAINTENANCE_LEDGER.md`；若继续推进主线，下一步应进入 `WP8/MVP13` 之后的阶段，而不是回头扩 `WP7`

## Current Proven State
- `runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2` 已接入 `developmental_tick / developmental_replay`
- `developmental_shadow / shadow_self` 已作为 shadow-only writeback 子状态进入正式主链
- scripted runtime mainline observation harness 已落地：
  - `scripts/run_runtime_mainline_observation.py`
- controlled evidence verifier 已落地：
  - `OpenEmotion/tools/run_mvp12_controlled_evidence.py`
- aggregate verifier 已落地：
  - `OpenEmotion/tools/aggregate_mvp12_observations.py`
- current controlled aggregate 已 `pass`：
  - `report_count = 7`
  - `direct_real_report_count = 6`
  - `direct_real_window_count_total = 12`
  - `governance_violation_total = 0`
  - `replay_consistent_all = true`
  - `span_hours = 14.098`
- host-governed proactive chain 的 controlled runners 已全部存在并生成 current artifacts：
  - proactive followup draft
  - idle scheduler
  - controlled proactive delivery
  - proactive outbox
  - proactive outbox drain
  - Telegram proactive transport
  - host-governed proactive Telegram auto cycle
- supplemental Telegram evidence 当前为 single `E4`：
  - allowlisted host-governed proactive follow-up 样本已存在
  - 但仍不是 transport-specific `E5`

## Completion Rules
- `WP7` 可在 formal runtime sandbox + controlled observation 轴上收口进入维护态
- `WP7` 的 controlled observation `pass` 不等于 live authority handoff
- `WP7` 的 host-governed Telegram proactive 样本当前只到 single `E4`
- 即使 `WP7` 收口，也不得解释为：
  - 默认 live autonomy
  - OpenEmotion direct reply authority
  - stable transport maturity
- 进入维护态后，新增样本只进入 `Tasks/active/mvp12_developmental_sandbox/MAINTENANCE_LEDGER.md`，除非触发明确 reopen 条件
