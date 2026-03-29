# Minimal Long-Run Task Example

## Goal

演示如何在不改业务代码的前提下，用 Codex Long-Run Harness 跑通一个最小长任务闭环。

## Non-goals

- 不修改 `EgoCore/` 或 `OpenEmotion/` 业务实现
- 不补新测试框架
- 不改变现有运行时边界

## Constraints

- 只允许修改文档与 `scripts/codex/`
- 必须复用当前仓库已存在的命令和规范
- 验证应优先使用 `scripts/codex/verify_repo.py`

## Acceptance criteria

- [ ] `SPEC.md / PLAN.md / IMPLEMENT.md / STATUS.md` 四件套齐全
- [ ] 能给出一个清晰的当前 milestone
- [ ] 能跑一次 `python3 scripts/codex/verify_repo.py --mode fast`
- [ ] 输出里记录 decisions / risks / next step / evidence

## Known risks / dependencies

- `full` 模式可能因环境或现有 suite 较重而不适合作为每步默认验证
- 当前仓库没有统一 lint 命令，验证会给出 skipped reason

## Authority refs

- `AGENTS.md`
- `docs/codex/README.md`
- `PROJECT_MEMORY.md`
- `Tasks/templates/README.md`
