# OpenEmotion MVP11 Replay Tempfile Stabilization

## Goal

清掉 `python3 scripts/codex/verify_repo.py --mode full` 中 `tests/mvp11/test_replay_backward_compat.py` 的 Windows tempfile/handle teardown 错误，让 OpenEmotion 失败面从“replay ledger 文件句柄未释放”收敛到更真实的业务/fixture 问题。

## Non-goals

- 不在本任务内清理 `tests/test_daemon_lifecycle.py`、`tests/test_live_integration_fixture.py`、`tests/test_outcome_capture_integration.py` 等其他失败面
- 不在本任务内重构 replay schema、event model、snapshot 格式
- 不顺手把整个 OpenEmotion pytest suite 打到全绿

## Constraints

- 边界约束：只修 `emotiond.science.ledger` 的文件句柄生命周期，不靠 fixture 修改或跳过测试收口
- 仓库/子仓约束：保持 MVP10/MVP11 ledger API 与产物格式兼容；不破坏现有 replay/summary 文件路径
- 环境约束：以 `OpenEmotion/.venv/Scripts/python.exe` 作为当前验证 runtime
- 发布约束：只提交本 slice touched files；使用 `cmd.exe /c git commit` 与 `cmd.exe /c git push origin main`

## Acceptance criteria

- [ ] `OpenEmotion/tests/mvp11/test_replay_backward_compat.py` 全量通过，且不再出现 tempfile teardown 的 `PermissionError`
- [ ] 依赖同一 ledger 主链的 `OpenEmotion/tests/mvp10/test_science_mode_matrix.py` 回归通过
- [ ] `python3 scripts/codex/verify_repo.py --mode full` 已复跑，且 `mvp11 replay backward compat` 不再出现在 OpenEmotion 错误摘要里

## Known risks / dependencies

- 风险：若把 ledger 改成按次 append 写入，必须确保不破坏 MVP10/MVP11 的持久化与 summary 语义
- 依赖：上一条 slice 已清掉 OpenEmotion collection/import blockers，本条 slice 依赖当前 full verify 能进入真实执行面
- 外部 blocker：无外部服务 blocker；若 full verify 仍失败，应视为新的仓内真实失败面

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `docs/codex/tasks/openemotion-test-collection-stabilization/STATUS.md`
- `scripts/codex/verify_repo.py`
- `OpenEmotion/tests/mvp11/test_replay_backward_compat.py`
- `OpenEmotion/tests/mvp10/test_science_mode_matrix.py`
- `OpenEmotion/emotiond/science/ledger.py`
