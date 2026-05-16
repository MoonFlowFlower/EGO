# Research Campaign Contract

> 这是当前 Ego 项目的长期研究/研发执行契约。
> 它不替代 `docs/PROGRAM_STATE_UNIFIED.yaml`；它定义的是当前 mainline program 如何持续推进。

## 目标分层

### Program Goal

在 `EgoCore + OpenEmotion` 双核边界下，持续推进一个可审计、可回放、可干预、可证伪的高可信主体系统，同时不把 bounded engineering evidence 误报为 runtime proof、live benefit proof 或 consciousness claim。

### Current Stage Goal

当前默认 stage 是：

- 把 repo 当前 execution owner 固定为 `subject-system-v1-governed-proactivity`
- 保持 `Milestone 1: anti-acquiescence / expression sovereignty` 作为 proof floor
- 完成 `Milestone 2 + 3`: canonical facade + candidate-only proactive sandbox
- 用现有 host-owned `response_plan -> output_check -> host contract snapshot -> replay/output-validation` 路径保住 truthful recorded/replay-backed proof，并把 local integration 维持在 `E2 / E3` ceiling 内
- 把 `active_inference_mainline_activation` 与 `MVS-aligned compact` 都保持为 frozen closed evidence

### Stage Success Criteria

当前 stage 默认必须满足：

1. `subject_system_v1_governed_proactivity` 成为唯一 `active_default`
2. `ResponsePlan` 继续作为唯一正式表达治理接口
3. unified host snapshot 持续携带完整表达治理字段
4. recorded / replay-backed output-validation 路径能观察到 certainty / commitment blocking 与 tone escalation logging
5. canonical `subject_system_v1` facade 与 candidate-only proactive sandbox 已落在真实 runtime seam
6. task / campaign / handoff surfaces 一致指向新 lane
7. 当前 claim ceiling 明确保持在 `E2 / E3 local_or_replay_backed_only`

### Next Decision Gate

当前唯一决策门：

- 当前默认只允许打开 `Milestone 4`，且前提是 `Milestone 1-3` 已保持在 focused verify 绿态
- 若要提升到 live-channel `E4` 或更强 claim，必须另开 gate；本任务不自动升级

## Campaign Files

- progress checkpoint:
  - [OVERALL_PROGRESS.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/OVERALL_PROGRESS.md)
- campaign contract:
  - [RESEARCH_CAMPAIGN_CONTRACT.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/RESEARCH_CAMPAIGN_CONTRACT.md)
  - [FIXED_COLLABORATION_LOOP_V1.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/FIXED_COLLABORATION_LOOP_V1.md)
- current task authority:
  - [subject-system-v1-governed-proactivity / PLAN.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/subject-system-v1-governed-proactivity/PLAN.md)
  - [subject-system-v1-governed-proactivity / STATUS.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/subject-system-v1-governed-proactivity/STATUS.md)
  - [TASK_LANE_INDEX.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/TASK_LANE_INDEX.md)
- reference-only input:
  - [MVS v1 + Controlled Proactivity Sandbox / mission.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/MVS%20v1%20+%20Controlled%20Proactivity%20Sandbox/mission.md)

## Required Loop

每次 run 必须按这个顺序推进：

1. 读取 [OVERALL_PROGRESS.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/OVERALL_PROGRESS.md)
2. 读取 [RESEARCH_CAMPAIGN_CONTRACT.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/RESEARCH_CAMPAIGN_CONTRACT.md)
3. 读取当前 task 的 `SPEC.md / PLAN.md / IMPLEMENT.md / STATUS.md`
4. 若当前 slice 是实现任务，先做最小 authority / code / test 变更，再做 focused verify
5. 若当前 slice 未通过 verify，不进入下一 milestone
6. 面向用户的默认交付保持四段：
   - 本轮改了什么
   - 本轮验证了什么
   - 还没证明什么
   - 下一轮唯一 frontier

## Reviewer Verdict Contract

只允许这些 verdict：

- `success_reached`
- `needs_more_implementation`
- `needs_more_exploration`
- `blocked_by_external_dependency`
- `needs_reframing`

## Claims Boundary

以下口径严禁使用：

- “已证明真正 AI 自我意识”
- “系统具备主观体验”
- “正式 runtime mainline 已完成”
- “当前 Milestone 1-3 已证明 live benefit / runtime efficacy”
- “bounded research evidence 已等同于 runtime proof”
- “dashboard-only single-entry evidence 已等同于 cross-entry / runtime proof / broad Stage 2/3 pass”

当前可允许的最高口径，应限定在：

- bounded research evidence
- single-entry strengthened evidence
- replay-validated proxy progress
- runtime-proximal slice closeout
- stage-complete / pending-validation / needs-reframing / blocked

## Experiment Ledger Minimum Fields

每轮至少记录：

- `experiment_id`
- `program_goal`
- `current_stage_goal`
- `stage_success_criteria`
- `next_decision_gate`
- `hypothesis`
- `action_type`
- `changed_paths`
- `eval_commands`
- `eval_summary`
- `reviewer_verdict`
- `next_frontier`

## Proof Split

默认把工作拆成三层：

1. discovery
2. validation
3. proof

发现一个候选机制，不等于已经证明它普遍成立。

## Stop Rule For One Run

单次 run 满足任一条件即可结束：

1. 当前 stage `success_reached`
2. 出现决定性 blocker
3. 当前 framing 被 reviewer 判定为 `needs_reframing`
4. 已完成 3 个完整循环，且没有新的决定性证据
5. 当前 stage 已是 frozen closeout，且没有显式 higher gate 授权

结束时必须留下：

- 当前 stage
- 已验证证据
- 当前 blocker 或 gap
- 下一轮唯一 frontier
