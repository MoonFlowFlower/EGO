# MVP17 Social Self / Other-Modeling 执行包

```yaml
task_id: L3-20260403-MVP17-SSOM
created_at: "2026-04-03T00:00:00Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: legacy_demotion_complete
parent_authority: "Tasks/MVS_task_plan.md"
phase_authority: "Tasks/MVP17_task_plan.md"
predecessor: "WP11/MVP16"
same_subject_line: true
not_parallel_track: true
scope: "WP12 / MVP17 Social Self / Other-Modeling"
```

---

## 真实目标

在不放开 authority 边界的前提下，把 `WP12/MVP17` 的 formal owner 落到 `OpenEmotion/openemotion/social_self/*`，并把 `trust / commitment / repair` 的 proposal-only contract 正式接到 `proto_self_v2`。

## 当前正式 owner target

- `OpenEmotion/openemotion/social_self/*`

## 当前正式主链 target

`social owner -> bounded social projection / proposals -> proto_self_runtime / proto_self_adapter / proto_self_v2 -> governed downstream weighting and social writeback candidate path`

## 当前锁定口径

- `MVP17` 是 `WP12`，接在 `WP11/MVP16` 后，不是新的主体线
- phase 1 只做 `trust / commitment / repair`
- `other-modeling` 当前只允许 bounded state / role continuity 语义，不做泛化心智解读
- `EgoCore/app/response/relationship_context.py`、`EgoCore/app/handlers/social_chat_handler.py`、`EgoCore/app/runtime/repair_context_manager.py`、`EgoCore/app/bridges/openemotion_bridge.py`、`OpenEmotion/emotiond/db.py`、`OpenEmotion/emotiond/state.py`、`OpenEmotion/emotiond/api.py` 只作为 reference-only / input-only 历史 surfaces
- `WP11` 保持 `maintenance_mode`
- `WP11` 新增样本只进对应 maintenance ledger，不回灌为 `WP11` scope reopen
- provider `429/401` 继续标注为外部预算层风险，不回灌为 `WP11` blocker

## 当前范围

- authority / contract freeze
- formal owner package target
- bounded proto-self social contract
- EgoCore runtime social bridge
- historical social / relation materials demotion
- subagent-ready task decomposition

## 当前状态

- formal owner：`T10 completed`
- proto_self_v2 contract：`T20 completed`
- EgoCore runtime bridge：`T30 completed`
- legacy demotion / compat map：`T40 completed`
- 主链接线：`current_runtime_mainline_connected`
- 启用状态：`bounded_runtime_bridge_connected`
- 当前 blocker：`causal proof / controlled observation not started`
- 当前最小动作：`T50_CAUSAL_VALIDATION`

## T10 已证实内容

- `OpenEmotion/openemotion/social_self/*` 已成为 phase 1 的唯一 formal owner 落点
- owner state 已覆盖 `relation_memory / other_model_state / trust_state / commitment_state / repair_state / social_boundary_state / governance_ledger`
- owner store、revision log、replay 与 proposal-only governance 已有最小测试通过
- 旧 social surfaces 仍只作为 reference-only / input-only，不构成 current formal owner

## T20 已证实内容

- `proto_self_v2` 已能消费 `runtime_summary.social_self_context` 与 `runtime_summary.social_context`
- `KernelOutputV2` 已发出锁定的 `social_self_delta / relation_update_candidates / trust_commitment_snapshot / social_policy_hints / repair_proposal_candidates / social_writeback_candidate`
- trace payload 已镜像 `social_context`
- social outputs 仍保持 `proposal_only + behavioral_authority = none`
- legacy `relationship_context` / `emotiond.state.bond_trust` 不会被误当成正式 social contract 输入

## T30 已证实内容

- `RuntimeV2ProtoSelfRuntime` 已把 `social_self_context` 与 `social_context` 注入当前 runtime 主链
- `social_self` proposal-only writeback 已能通过当前 `runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2` 主线回到 formal owner store
- `social_writeback_candidate` 在宿主侧仍被锁定为 `proposal_only + behavioral_authority = none + required_gate = social_writeback_gate`
- `state.proto_self_context` 已记录 `social_self_delta / relation_update_candidates / trust_commitment_snapshot / social_policy_hints / repair_proposal_candidates / social_writeback_candidate / social_writeback`
- EgoCore 定向 social bridge 测试已通过，且同文件全量 runtime bridge 回归通过

## T40 已证实内容

- historical social / relation surfaces 已在 `LEGACY_REFERENCE_REGISTER.md` 中完成逐项 demotion，当前只允许 `reference-only` 或 `input-only`
- 旧 `relationship_context / social_chat_handler / repair_context_manager / openemotion_bridge / emotiond.{api,db,state,models,other_minds,persistence,offline_rollouts,memory_legacy}` 现仅以 `LEGACY_REFERENCE_REGISTER.md` 中登记的 `reference-only / input-only` 身份存在，不再构成当前 `WP12` formal owner 或 current-runtime proof
- `OpenEmotion/tools/verify_mvp17_mainline_wiring.py` 已验证：formal owner 路径存在、当前 runtime 主链仍读取 `social_self` bounded contract、legacy register 完整且所列 historical surfaces 仍存在
- `OpenEmotion/tests/mvp17/test_mainline_reference_demotion.py` 已验证 no-second-truth 约束与 current-runtime social consumer 的唯一性

## 当前不做

- 放开 live autonomy
- 放开 OpenEmotion direct reply authority
- 放开 broader transport claims
- autonomous social outreach
- unbounded other-model mind-reading
- 把 `WP11` maintenance ledger 重新解释成 `WP12` readiness
- 把 historical roadmap / archive social materials 直接当成当前 `WP12` formal proof

## 执行入口

- authority：`Tasks/MVP17_task_plan.md`
- status：`STATUS.md`
- legacy register：`LEGACY_REFERENCE_REGISTER.md`
- contracts：`contracts/`
- task cards：`cards/`
