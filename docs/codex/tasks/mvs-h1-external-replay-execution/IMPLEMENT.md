# MVS H1 External Replay Execution - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `artifacts/external_eval_replay_v1/cases/heldout_eval/`

## Execution rules

- 只消费 held-out case files，不重拉 source 数据
- baseline 与 candidate 都只能通过 isolated temp stores 运行
- 不触碰 canonical mainline behavior，不改 scorer ontology

## Scope control

- 允许修改：
  - `scripts/codex/run_mvs_h1_external_replay_execution.py`
  - `scripts/codex/verify_mvs_h1_external_replay_execution.py`
  - 当前 task docs
  - `artifacts/external_eval_replay_v1/reports/*EXTERNAL_REPLAY*`
- 不允许修改：
  - canonical proto_self / EgoCore runtime 行为
  - frozen external corpus
  - repo-level program state

## Validation strategy

- `python3 -m py_compile scripts/codex/run_mvs_h1_external_replay_execution.py scripts/codex/verify_mvs_h1_external_replay_execution.py`
- `python3 scripts/codex/run_mvs_h1_external_replay_execution.py`
- `python3 scripts/codex/verify_mvs_h1_external_replay_execution.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `git diff --check -- docs/codex/tasks/mvs-h1-external-replay-execution scripts/codex/run_mvs_h1_external_replay_execution.py scripts/codex/verify_mvs_h1_external_replay_execution.py artifacts/external_eval_replay_v1/reports`

## Failure handling

- case 加载失败必须进入 failure table
- unsupported family / execution exception 必须进入 failure table
- 如 execution 需要改 canonical 行为才可闭环，则停止并降级为 blocker

## Stopping rule

- verifier 未通过，不进入 closeout
- 如果 runner 需要扩 source、改 ontology、或写 canonical stores，立即停止

## Final handoff checklist

- [ ] `PLAN.md` 已更新进度与决策
- [ ] `STATUS.md` 已更新验证结果与 next step
- [ ] commands run / evidence 已记录
- [ ] can prove / cannot prove 已写清
