# MVS H1 External Replay Execution - PLAN

## Task summary

在不扩 source、不改 ontology、不改 canonical 行为的前提下，对 60 个 frozen held-out external replay cases 跑 baseline 与 canonical shadow-H1 path，并收口 bucket-level 执行与机制结果。

## Execution mode

- mode: implementation
- why this mode: 输入、约束、case schema 已冻结，当前主要工作是 runner / scorer 落地
- proof required after discovery: execution completeness、failure accounting、bucket completeness、E2/E3 proof ceiling

## Milestones

### Milestone 1: Freeze Replay Contract And Runner

- type: implementation
- question: 如何在不改 canonical 行为的前提下跑 baseline/candidate replay
- current framing: case file -> replay plan -> isolated runtime execution -> public-output scoring
- hypotheses:
  - 所有 held-out cases 都能被 task-local isolated runtime 消费
  - 同一 scorer ontology 可用于 external replay bucket summaries
- scope:
  - 实现 execution runner
  - 实现 verifier
  - 锁定 task docs
- experiments planned:
  - 小样本 probe correction / continuity / uncertainty / tool buckets
  - 确认 H1 只在 synthetic exec-result buckets 出现
- kill criteria:
  - 必须更改 canonical mainline 才能执行
  - 必须更改 scorer ontology 才能评分
- files / areas likely touched:
  - `scripts/codex/run_mvs_h1_external_replay_execution.py`
  - `scripts/codex/verify_mvs_h1_external_replay_execution.py`
  - `docs/codex/tasks/mvs-h1-external-replay-execution/*`
- acceptance:
  - runner 能消费 frozen held-out cases
  - failures 会显式记账
- validation:
  - `python3 -m py_compile scripts/codex/run_mvs_h1_external_replay_execution.py scripts/codex/verify_mvs_h1_external_replay_execution.py`
- rollback note:
  - 如出现 canonical store 污染风险，停下并先改为 fully isolated temp stores

### Milestone 2: Execute, Score, And Close

- type: implementation
- question: baseline 与 canonical shadow-H1 在 external replay 上具体产生哪些 public/mechanism 信号
- current framing: bounded all-case execution with bucket summaries and proof ceiling
- hypotheses:
  - candidate 的 H1 telemetry 只会出现在 synthetic exec-result direct buckets
  - public outputs 对 baseline/candidate 可能 flat，但这仍是有效分析结果
- scope:
  - 全量执行 60 cases x 2 variants
  - 生成 execution/bucket/failure/mechanism reports
  - 写清 can prove / cannot prove
- experiments planned:
  - full replay execution
  - verifier + fast gate
- kill criteria:
  - failure accounting 不完整
  - restricted reserve 被混入 execution
- files / areas likely touched:
  - `artifacts/external_eval_replay_v1/reports/*EXECUTION*`
  - `artifacts/external_eval_replay_v1/reports/*BUCKET*`
  - `artifacts/external_eval_replay_v1/reports/*MECHANISM*`
- acceptance:
  - deliverables 1-5 全部生成
  - verifier 通过
- validation:
  - `python3 scripts/codex/verify_mvs_h1_external_replay_execution.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 如全量执行失败，保留 failure table 并降级为条件性完成

## Progress

- current_status: closed
- current_milestone: Milestone 2
- milestone_state: verified
- candidate_vs_proof: proof_passed

## Decision log

- 2026-04-10: execution 只消费 `heldout_eval` case files，不重读 source APIs
- 2026-04-10: runner 使用 task-local isolated stores，避免污染 canonical writeback paths
- 2026-04-10: external replay score 继续使用 Trial-1 的四维 public-output ontology 与权重
- 2026-04-10: full `RuntimeV2ProtoSelfRuntime` + mounted-drive execution roots 作为实现路线被排除，原因是 bounded replay 下 I/O 成本过高；最终 runner 收窄为 canonical event-builder + adapter surface，并将 execution roots 放到系统临时目录

## Surprises / discoveries

- external replay probe 表明 canonical shadow-H1 path 在 exec-result 后会稳定产生 `shadow_h1` telemetry
- 同 probe 下，baseline 与 candidate 的 public outputs 当前看起来大概率 flat
- full execution 证实 flat behavior 不是局部样本假象：`60` cases 下 `public_gap_cases_candidate_vs_baseline = 0`

## Outcomes / retrospective

- 本轮已证明：frozen held-out external corpus 可在 E2/E3 bounded replay 下被 baseline 与 canonical shadow-H1 path 全量消费，且 direct H1 buckets 会稳定产出 shadow-only telemetry
- 还没证明：runtime efficacy、E4 formal mainline behavior、live decision promotion、外部 corpus 上的真实 MVS public gain
- 本轮排除了什么：需要扩 source、改 scorer ontology、或改 canonical mainline 才能完成 external replay 的假设
- 下一步最小闭环动作：若继续，只能新开一个 external replay interpretation / scorer tightening task，或把这批结果与后续 challenger 对比任务分开推进
