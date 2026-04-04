# MVP18 Embodied Loop / Environment Coupling 执行包

```yaml
task_id: L3-20260404-MVP18-ELEC
created_at: "2026-04-04T00:00:00Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: observation_started
parent_authority: "Tasks/MVS_task_plan.md"
phase_authority: "Tasks/MVP18_task_plan.md"
predecessor: "WP12/MVP17"
same_subject_line: true
not_parallel_track: true
scope: "WP13 / MVP18 Embodied Loop / Environment Coupling"
```

---

## 真实目标

在不放开 authority 边界的前提下，把 `WP13/MVP18` 的 formal owner 已落到 `OpenEmotion/openemotion/embodied_self/*`，并继续把 `resource/slack pressure`、`action -> consequence` bounded writeback、`self/world boundary pressure` 的 proposal-only contract 正式接到当前主链规划里。

## 当前正式 owner target

- `OpenEmotion/openemotion/embodied_self/*`

## 当前正式主链 target

`embodied owner -> bounded embodied projection / proposals -> proto_self_runtime / proto_self_adapter / proto_self_v2 -> governed downstream weighting and embodied writeback candidate path`

## 当前锁定口径

- `MVP18` 是 `WP13`，接在 `WP12/MVP17` 后，不是新的主体线
- phase 1 只做 `resource/slack pressure`、`action -> consequence` bounded writeback、`self/world boundary pressure`
- `EgoCore` 继续保留 runtime / response / tool / transport / environment risk adjudication 的最终权威
- `OpenEmotion/emotiond/consequence.py`、`OpenEmotion/emotiond/science/interventions.py`、`OpenEmotion/roadmap/VersionRoadmap.md` 只作为 reference-only / input-only / technical reference 历史 surfaces
- `WP12` 保持 `maintenance_mode`
- `WP12` 新增样本只进对应 maintenance ledger，不回灌为 `WP12` scope reopen
- provider `429/401` 继续标注为外部预算层风险，不回灌为 `WP12` blocker

## 当前范围

- authority / contract freeze
- formal embodied owner package target
- bounded proto-self embodied contract
- EgoCore runtime embodied bridge target
- historical consequence / intervention materials demotion
- subagent-ready task decomposition

## 当前状态

- 执行包状态：`observation_started`
- authority freeze：`completed`
- formal owner：`T10 completed`
- proto_self_v2 contract：`T20 completed`
- EgoCore runtime bridge：`T30 completed`
- legacy demotion / compat map：`T40 completed`
- causal validation：`T50 completed`
- single controlled observation：`T60 completed`
- batch controlled observation / aggregate：`T70 pending`
- 主链接线：`current runtime embodied bridge present`
- 启用状态：`controlled_mainline_observation`
- 当前 blocker：`T70 batch controlled observation / aggregate pending`
- 当前最小动作：`start T70_BATCH_OBSERVATION_AND_AGGREGATE; do not implement closeout before T70`

## T10 已证实内容

- `OpenEmotion/openemotion/embodied_self/*` 已成为 phase 1 的唯一 formal owner 落点
- owner state 已覆盖 `embodied_state / environment_coupling_state / resource_pressure_state / boundary_pressure_state / action_consequence_memory / self_world_boundary_semantics / proposal_history / governance_ledger`
- owner store、revision log、replay 与 proposal-only governance 已有最小测试通过
- bounded runtime projection 已形成，但不泄漏 owner 全量状态
- 旧 consequence / intervention surfaces 仍只作为 reference-only / input-only，不构成 current formal owner

## T20 已证实内容

- `proto_self_v2` 已能消费 `runtime_summary.embodied_self_context` 与 `runtime_summary.environment_context`
- `KernelOutputV2` 已发出锁定的 `embodied_self_delta / consequence_update_candidates / resource_boundary_snapshot / embodied_policy_hints / repair_or_stabilize_proposal_candidates / embodied_writeback_candidate`
- trace payload 已镜像 `environment_context`
- embodied outputs 仍保持 `proposal_only + behavioral_authority = none`
- legacy consequence / intervention fields 不会被误当成正式 embodied contract 输入

## T30 已证实内容

- `EgoCore/app/runtime_v2/proto_self_runtime.py` 当前会在正式 runtime 主线里注入 `runtime_summary.embodied_self_context` 与 `runtime_summary.environment_context`
- 当前 `runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2` 已记录 `embodied_self_delta / consequence_update_candidates / resource_boundary_snapshot / embodied_policy_hints / repair_or_stabilize_proposal_candidates / embodied_writeback_candidate`
- 当前 `state.proto_self_context` 已镜像 `environment_context` 与 `embodied_writeback`
- embodied writeback 仍保持 `proposal_only + behavioral_authority = none + required_gate = embodied_writeback_gate`
- 定向 runtime bridge tests 已在 `EgoCore/tests/test_runtime_v2_proto_self_runtime.py` 通过

## T40 已证实内容

- `Tasks/active/mvp18_embodied_loop_environment_coupling/LEGACY_REFERENCE_REGISTER.md` 现已显式登记当前 embodied / consequence / intervention 历史 surfaces 的 `technical reference / reference-only / input-only` 分类
- `OpenEmotion/tools/verify_mvp18_mainline_wiring.py` 现在会同时验证：
  - `OpenEmotion/openemotion/embodied_self/*` formal owner package 存在
  - `proto_self_v2` 当前仍读取 bounded embodied / environment context
  - `EgoCore` current runtime embodied consumer 仍是唯一 formal path
  - 旧 `consequence / interventions / science_mode` surfaces 没有被重新抬成 second truth
- `OpenEmotion/tests/mvp18/test_mainline_reference_demotion.py` 已把 no-second-truth / demotion 断言固定成定向回归测试

## T50 已证实内容

- `OpenEmotion/tests/mvp18/test_embodied_causal_formal_proof.py` 已通过 4 组 paired intervention/control proof
- 当前已证明：
  - high resource/slack pressure 会改变 conservative embodied weighting
  - consequence memory present 会改变 bounded consequence weighting
  - self/world boundary pressure guarded 会改变 bounded boundary weighting
  - 仅 outcome wording 改写而无结构化指标变化时，不会制造假的 downstream behavioral proof
- `OpenEmotion/tools/run_mvp18_causal_validation.py` 已生成当前 causal proof artifacts：
  - `OpenEmotion/artifacts/mvp18/mvp18_causal_validation_current.json`
  - `OpenEmotion/artifacts/mvp18/mvp18_causal_validation_current.md`
- 当前 causal report 为 `status = pass`、`verification_level = V3`、`evidence_level = E3`、`pair_count = 4`、`passed_count = 4`

## T60 已证实内容

- `OpenEmotion/tools/run_mvp18_controlled_observation.py` 已生成首个 controlled runtime-mainline embodied observation artifacts：
  - `OpenEmotion/artifacts/mvp18/mvp18_controlled_observation_current.json`
  - `OpenEmotion/artifacts/mvp18/mvp18_controlled_observation_current.md`
- `OpenEmotion/tests/mvp18/test_controlled_observation.py` 已把 single controlled observation 的最小 contract 固定成回归测试
- 当前 single controlled observation 结果为：
  - `status = pass`
  - `verification_level = V4`
  - `evidence_level = E4`
  - `embodied_writeback_gate = allow_writeback`
  - `embodied_proposal_present = true`
  - `proposal_only_discipline_consistent = true`
  - `behavioral_authority_none = true`
  - `bounded_influence_present = true`
  - `replay_valid = true`
- 这只证明当前 formal owner + current runtime mainline 已拿到首个 embodied proposal-only writeback 样本，不证明 repeated stability、`E5`、closeout、或 maintenance mode

## 当前不做

- 放开 live autonomy
- 放开 OpenEmotion direct reply authority
- 放开 broader transport claims
- embodied takeover
- 持续主动外发
- autonomous tool expansion
- 把 `WP12` maintenance institutionalization 重新解释成 `WP13` readiness
- 把 historical consequence / intervention materials 直接当成当前 `WP13` formal proof

## 执行入口

- authority：`Tasks/MVP18_task_plan.md`
- status：`STATUS.md`
- legacy register：`LEGACY_REFERENCE_REGISTER.md`
- contracts：`contracts/`
- task cards：`cards/`
- subagent assignment：`SUBAGENT_ASSIGNMENT.md`
