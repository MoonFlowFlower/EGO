# OpenEmotion MVP11 Replay Tempfile Stabilization - PLAN

## Task summary

这是一个实现 / 验证层的 bugfix slice。目标是只修 `mvp11 replay backward compat` 在 Windows tempfile teardown 下的 JSONL 句柄泄漏问题，不扩到其他 OpenEmotion 失败面。

## Milestones

### Milestone 1: Reproduce and repair ledger handle lifecycle

- scope: 复现 `tests/mvp11/test_replay_backward_compat.py` 的 teardown `PermissionError`，定位到 ledger 句柄生命周期，并用最小 patch 修复
- files / areas likely touched:
  - `OpenEmotion/emotiond/science/ledger.py`
- acceptance:
  - `OpenEmotion/tests/mvp11/test_replay_backward_compat.py` 全量通过
  - 不再出现 Windows tempdir teardown `PermissionError`
- validation:
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/mvp11/test_replay_backward_compat.py -q`
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/mvp10/test_science_mode_matrix.py -q`
- rollback note: 若 append-per-call 写法破坏 replay 语义，回退到 persistent handle 方案并改成显式 close/finalizer 收口

### Milestone 2: Re-run verifier and reclassify remaining failures

- scope: 用 full verify 证明这条错误面已离开 OpenEmotion 摘要，并把剩余失败面重新分组
- files / areas likely touched:
  - `docs/codex/tasks/openemotion-mvp11-replay-tempfile-stabilization/*.md`
- acceptance:
  - `python3 scripts/codex/verify_repo.py --mode full` 已复跑
  - OpenEmotion 错误摘要中不再包含 `tests/mvp11/test_replay_backward_compat.py` tempfile teardown 错误
- validation:
  - `python3 scripts/codex/verify_repo.py --mode fast`
  - `python3 scripts/codex/verify_repo.py --mode full`
- rollback note: 若 full verify 证明问题未离开摘要，停在当前 slice 继续修复，不跳到下一失败面

## Progress

- current_status: completed_for_slice
- current_milestone: Milestone 2
- milestone_state: 目标错误面已离开 full verify 摘要；当前切片已完成，仓库仍有其他独立失败面

## Decision log

- 2026-03-29: 不改 fixture，不在测试里强行 `end_run()`；根因在生产实现，应该在 ledger 生命周期上收口
- 2026-03-29: 优先改成 append-per-call，无常驻文件句柄；这样比依赖 `__del__` / GC / fixture teardown 顺序更稳
- 2026-03-29: 保留 `_file_handle` 兼容属性作为 sentinel，不再持有真实 OS 文件句柄；这样既保留旧测试契约，又不把 Windows teardown 问题带回来

## Surprises / discoveries

- `mvp11 replay backward compat` 的错误不是逻辑断言失败，而是 Windows 下 tempdir 删除时句柄仍占用
- 依赖同一 ledger 主链的 `mvp10 science mode matrix` 是一个便宜且有代表性的回归守门

## Outcomes / retrospective

- 本轮已证明：
  - 问题根因是 `emotiond.science.ledger` 常驻 JSONL 句柄，而不是 tempdir fixture 自身
  - `tests/mvp11/test_replay_backward_compat.py` 已恢复通过
  - `tests/mvp10/test_science_mode_matrix.py` 仍保持通过
  - `mvp11 replay backward compat` tempfile teardown 错误已离开 `python3 scripts/codex/verify_repo.py --mode full` 的失败摘要
  - 这次修复没有把 `mvp10 test_logging_roundtrip` 一起打坏
- 仍未解决：
  - OpenEmotion 仓库层仍有其他独立失败面，例如 `test_daemon_lifecycle`、`test_live_integration_fixture`、`test_outcome_capture_integration`
- 下一步最小闭环动作：
  - 开下一条 OpenEmotion pytest stabilization slice，优先处理 `test_daemon_lifecycle` 的 Windows sqlite/tempfile 句柄错误
