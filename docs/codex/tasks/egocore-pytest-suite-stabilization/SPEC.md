# EgoCore Pytest Suite Stabilization

## Goal

在不扩业务 scope 的前提下，清理 `python3 scripts/codex/verify_repo.py --mode full` 中 `EgoCore pytest suite` 的现有失败，使 full verify 至少不再被这组已知回归阻塞。

## Non-goals

- 不改 `OpenEmotion` 缺依赖导致的 skipped 行为
- 不新增业务功能或改动任务框架以外的产品策略
- 不顺手清理与当前失败无关的历史测试或架构问题

## Constraints

- 边界约束：只处理当前 full verify 中 `EgoCore pytest suite` 的失败簇
- 仓库/子仓约束：保持 `EgoCore` 与 `OpenEmotion` 双仓边界，不把测试问题转化为跨仓大重构
- 环境约束：当前 Linux 解释器缺 `fastapi`，`OpenEmotion` runtime-backed checks 允许保持 skipped
- 发布约束：每个 milestone 完成后必须至少跑针对性 pytest；收口时回到 `python3 scripts/codex/verify_repo.py --mode full`

## Acceptance criteria

- [ ] `docs/codex/tasks/egocore-pytest-suite-stabilization/` 四份任务文档完整，记录真实失败簇、决策、风险与 next step
- [ ] 当前 `EgoCore pytest suite` 的 25 个失败被缩减到 0，或剩余失败被证明是新的独立 blocker 且有明确收口记录
- [ ] `python3 scripts/codex/verify_repo.py --mode full` 复跑完成，`EgoCore pytest suite` 不再是 failed 项

## Known risks / dependencies

- 风险：部分失败可能来自测试预期与运行时 contract 的兼容漂移，需要加最小 shim 而不是重写主逻辑
- 依赖：repo-local `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion` 仍是 `EgoCore pytest suite` 的必要运行前提
- 外部 blocker：若某簇失败证明依赖外部服务、凭据或真实 Telegram 运行态，则该簇需要单独降级并记录

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `AGENTS.md`
- `docs/codex/README.md`
- `docs/codex/tasks/codex-harness-hardening/SPEC.md`
- `docs/codex/tasks/codex-harness-hardening/STATUS.md`
- `scripts/codex/verify_repo.py`
