# OpenEmotion V6K2 Whitelist Alert Stabilization - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `OpenEmotion/tests/embedding/test_v6k2_whitelist_operations.py`
- `OpenEmotion/emotiond/memory/embedding/whitelist_alert_engine.py`
- `OpenEmotion/emotiond/memory/embedding/whitelist_governance.py`
- `OpenEmotion/emotiond/memory/embedding/production_whitelist.py`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 每次只推进 `STATUS.md` 中的 `Current milestone`
- 现有 `Tasks/active/*.md` 只作为 authority refs，不复制成第二真相源

## Scope control

- Only change the alert-engine contract surface and this task directory unless
  validation proves another file is required.
- Do not redesign governance thresholds or scheduler behavior in this slice.
- Keep the patch minimal and directly tied to the failing BOOTSTRAP alert case.

## Validation strategy

- Milestone 1:
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/embedding/test_v6k2_whitelist_operations.py -q`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- Closeout:
  - `git diff --check`
  - `python3 scripts/codex/verify_repo.py --mode full`

## Failure handling

- If the BOOTSTRAP alert type breaks downstream tests, keep the fix local and
  adjust the alert semantics rather than widening into unrelated modules.
- If validation exposes a broader governance contract mismatch, stop and record
  the blocker instead of refactoring the whole whitelist stack.
- Do not move to full verify until the targeted v6k.2 suite passes.

## Stopping rule

- 当前 milestone 未验证通过，不进入下一 milestone
- 缺少外部凭据/审批、authority source 冲突、或 slice 无法闭环时停止

## Final handoff checklist

- [ ] `PLAN.md` 已更新进度与决策
- [ ] `STATUS.md` 已更新验证结果与 next step
- [ ] commands run / evidence 已记录
- [ ] risks / rollback notes 已记录
