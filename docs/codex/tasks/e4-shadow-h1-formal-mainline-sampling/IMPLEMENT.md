# E4 Shadow H1 Formal Mainline Sampling - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `FROZEN_SAMPLE_MATRIX.json`
- `docs/codex/tasks/h1-canonical-shadow-patch/STATUS.md`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 每次只推进 `STATUS.md` 中的 `Current milestone`
- 现有 `Tasks/active/*.md` 只作为 authority refs，不复制成第二真相源
- Trial-1 / Trial-2 只作为 evidence refs，不复制成第二真相源
- 真实采样 authority 固定为 `artifacts/telegram_real_mainline_v1/real_telegram/*/ledger.json`

## Scope control

- 只改当前 milestone 需要的文件
- 不顺手推进 live decision promotion、scorer ontology、challenger 评分
- 保持 diff scoped

## Validation strategy

- 每个 milestone 完成后运行：
  - `python3 scripts/codex/verify_repo.py --mode fast`
- 当前任务的最小验证还包括：
  - `python3 -m py_compile <touched files>`
  - scoped `pytest`
  - `python3 scripts/codex/run_h1_e4_sampling_preflight.py`
  - `python3 scripts/codex/build_h1_e4_sample_reports.py`
  - `git diff --check -- <scoped files>`
- full gate 只作为 monitored residual context，不是当前 milestone 的 acceptance gate

## Failure handling

- 验证失败先修复
- 修不动就记录 blocker、降级完成口径、停止推进
- 不跳过失败验证直接进入下一 milestone
- 若 `run_h1_e4_sampling_preflight.py` 结论为 `close`，本任务停在 preflight closeout；不要伪装成 live sampling completed

## Stopping rule

- 当前 milestone 未验证通过，不进入下一 milestone
- 缺少外部 Telegram operator、live clean-bind 不成立、authority source 冲突、或 same-surface contamination 未排除时停止
- 若 sampling path 仍被 `native_loop` / runtime observation residual 污染，立即停止并只产 `causality exclusion`

## Final handoff checklist

- [ ] `PLAN.md` 已更新进度与决策
- [ ] `STATUS.md` 已更新验证结果与 next step
- [ ] commands run / evidence 已记录
- [ ] risks / rollback notes 已记录
