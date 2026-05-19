# H1 Canonical Shadow Patch - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `docs/codex/tasks/h1-canonical-promotion-prep/*.md`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 每次只推进 `STATUS.md` 中的 `Current milestone`
- Trial-1 / Trial-2 只作为 evidence refs，不复制成第二真相源

## Scope control

- 只改当前 milestone 需要的文件
- 不顺手推进 live decision promotion
- 保持 diff scoped

## Validation strategy

- 每个 milestone 完成后运行：
  - `python3 scripts/codex/verify_repo.py --mode fast`
- 当前任务的最小验证还包括：
  - `python3 -m py_compile <touched files>`
  - scoped `pytest`
  - `git diff --check -- <scoped files>`
- 如 fast gate 通过且 scoped proof 已收口，再视情况补 `python3 scripts/codex/verify_repo.py --mode full`

## Failure handling

- 验证失败先修复
- 修不动就记录 blocker、降级完成口径、停止推进
- 不跳过失败验证直接进入下一 milestone

## Stopping rule

- 当前 milestone 未验证通过，不进入下一 milestone
- 缺少外部凭据/审批、authority source 冲突、或 slice 无法闭环时停止
- 如果 canonical patch 无法保持 shadow-only 而不扰动 replay/public behavior，立即停止并回退到 mirror-only trace integration recommendation

## Final handoff checklist

- [ ] `PLAN.md` 已更新进度与决策
- [ ] `STATUS.md` 已更新验证结果与 next step
- [ ] commands run / evidence 已记录
- [ ] risks / rollback notes 已记录
