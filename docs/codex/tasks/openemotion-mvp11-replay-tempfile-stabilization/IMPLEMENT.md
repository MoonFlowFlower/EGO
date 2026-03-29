# OpenEmotion MVP11 Replay Tempfile Stabilization - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `OpenEmotion/tests/mvp11/test_replay_backward_compat.py`
- `OpenEmotion/emotiond/science/ledger.py`
- `scripts/codex/verify_repo.py`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 每次只推进 `STATUS.md` 中的 `Current milestone`
- 现有 `Tasks/active/*.md` 只作为 authority refs，不复制成第二真相源

## Scope control

- 只改当前 milestone 需要的文件
- 不顺手推进下一个 milestone
- 保持 diff scoped
- 不把这条 slice 扩大成 daemon/live fixture 或 outcome capture 清理任务

## Validation strategy

- 每个 milestone 完成后运行：
  - `python3 scripts/codex/verify_repo.py --mode fast`
- 收口或高风险改动时运行：
  - `python3 scripts/codex/verify_repo.py --mode full`

## Failure handling

- 验证失败先修复
- 修不动就记录 blocker、降级完成口径、停止推进
- 不跳过失败验证直接进入下一 milestone
- 若 append-per-call 破坏现有 ledger 语义，先回退实现策略，不通过测试改 fixture 兜底

## Stopping rule

- 当前 milestone 未验证通过，不进入下一 milestone
- 缺少外部凭据/审批、authority source 冲突、或 slice 无法闭环时停止

## Final handoff checklist

- [ ] `PLAN.md` 已更新进度与决策
- [ ] `STATUS.md` 已更新验证结果与 next step
- [ ] commands run / evidence 已记录
- [ ] risks / rollback notes 已记录
