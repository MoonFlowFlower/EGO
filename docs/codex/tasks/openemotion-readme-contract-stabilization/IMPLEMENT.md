# OpenEmotion README Contract Stabilization - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `OpenEmotion/tests/test_documentation.py`
- `OpenEmotion/tests/test_comprehensive_fixed.py`
- `OpenEmotion/Makefile`
- `OpenEmotion/pyproject.toml`
- `OpenEmotion/deploy/systemd/user/emotiond.service`
- `OpenEmotion/README.md`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 每次只推进 `STATUS.md` 中的 `Current milestone`
- 现有 `Tasks/active/*.md` 只作为 authority refs，不复制成第二真相源
- README examples must stay grounded in repo-tracked commands; do not invent new
  operations just to satisfy the test contract

## Scope control

- Only change `OpenEmotion/README.md` and this task directory unless validation
  proves another file is required for contract accuracy.
- Do not widen into runtime, daemon, or API implementation changes.
- Keep the diff scoped to documentation contract restoration.

## Validation strategy

- Milestone 1:
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/test_documentation.py -q`
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/test_comprehensive_fixed.py::TestDocumentationComprehensive::test_readme_content -q`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- Closeout:
  - `git diff --check`
  - `python3 scripts/codex/verify_repo.py --mode full`

## Failure handling

- If a required README string is wrong, fix the contract block before widening scope.
- If validation shows a command/example is not repo-tracked, remove or correct the
  claim rather than preserving inaccurate docs.
- Do not move to full verify until the targeted README gates pass.

## Stopping rule

- 当前 milestone 未验证通过，不进入下一 milestone
- 缺少外部凭据/审批、authority source 冲突、或 slice 无法闭环时停止

## Final handoff checklist

- [ ] `PLAN.md` 已更新进度与决策
- [ ] `STATUS.md` 已更新验证结果与 next step
- [ ] commands run / evidence 已记录
- [ ] risks / rollback notes 已记录
