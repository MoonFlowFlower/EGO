# Runtime-Proximal Host-Consumption Runner Implementation - PLAN

## Task summary

把已经冻结的 host-consumption causal planning 落成一个最小 runnable slice：在 runtime-proximal 但仍 bounded 的条件下，对三类 frozen families 跑 `Baseline A` 与 `active-inference`，并产出 host-consumable compare report。

## Execution mode

- mode: implementation
- why this mode:
  - causal question、scenario families、compare surface、rollback 已冻结完成
  - 再加一层纯授权不会降低不确定性

## Milestones

### Milestone 1: Runner + Focused Tests

- type: implementation
- scope:
  - `scripts/codex/run_runtime_proximal_host_consumption_runner.py`
  - `EgoCore/tests/test_runtime_proximal_host_consumption_runner.py`
  - task-local manifest
- acceptance:
  - runner 可跑三类 frozen families
  - 报告里只保留 host-consumable compare surface
  - focused tests 通过
- rollback note:
  - 若实现必须扩大到 runtime public API、candidate-private host API、或第二 scorer ontology，则在当前 milestone 内判 `blocked`，不继续扩实现面

### Milestone 2: Governance Sync

- type: implementation
- scope:
  - `docs/PROGRAM_STATE_UNIFIED.yaml`
  - `docs/OVERALL_PROGRESS.md`
  - `docs/codex/tasks/ai-self-awareness-minimal-framework/STATUS.md`
  - `docs/codex/tasks/ai-self-awareness-minimal-framework/PLAN.md`
  - `artifacts/evidence_ledger/index.yaml`
- acceptance:
  - 当前 execution slice 切到 runner implementation
  - causal planning freeze 改成已完成
  - 不把 runner 结果写成 runtime efficacy / self-awareness achieved

## Progress

- current_status: `complete`
- current_milestone: `Milestone 1: Runner + Focused Tests`
- milestone_state: `closeout_complete`
- candidate_vs_proof: `proof_passed_for_slice`

## Current reviewer conclusion

- verdict: `success_reached`
- why:
  - runner wiring, trace contract, and host-surface boundedness are green
  - `decision_conflict` and `failure_repair_retry` provide the required primary candidate-vs-baseline host pressure
  - `chat_consumption` is now explicitly treated as a supporting-family saturation detector on the bounded host surface, so policy / initiative / corrective pressure is sufficient evidence even when cadence saturates to the same hold posture
  - this closes the current bounded runner slice without widening authority, public API, or scorer ontology
