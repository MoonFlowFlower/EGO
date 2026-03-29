# Minimal Long-Run Task Example - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `docs/codex/README.md`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 每次只推进 `STATUS.md` 中的 `Current milestone`
- 不把本示例扩展成真实业务任务

## Scope control

- 只演示流程
- 不改业务代码
- 不引入新依赖

## Validation strategy

- 每步默认：
  - `python3 scripts/codex/verify_repo.py --mode fast`
- 只需要看探测与 summary 是否可读，不要求业务 suite 全跑一遍

## Failure handling

- 若 fast verifier 输出不清晰，先修脚本
- 若命令不可用，明确记录 skipped reason

## Stopping rule

- 当前 milestone 未验证，不切换下一 milestone
- 若要改业务代码，停止本示例并新建真实任务

## Final handoff checklist

- [ ] `PLAN.md` 已更新
- [ ] `STATUS.md` 已更新
- [ ] commands run / evidence 已记录
- [ ] next step 已明确
