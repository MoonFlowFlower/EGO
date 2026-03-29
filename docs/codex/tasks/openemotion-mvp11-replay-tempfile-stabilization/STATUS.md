# OpenEmotion MVP11 Replay Tempfile Stabilization - STATUS

## Current milestone

- name: Milestone 2 - Re-run verifier and reclassify remaining failures
- owner: Codex
- state: completed

## Current state

- current_layer: implementation / verification
- main_chain_status: 当前 slice 目标错误面已从 OpenEmotion full verify 摘要中清除；仓库仍有其他独立失败面
- completion_class: slice_complete_repo_still_failing

## Completed work

- 已建立独立 long-run task slice：`docs/codex/tasks/openemotion-mvp11-replay-tempfile-stabilization/`
- 已复现 `OpenEmotion/tests/mvp11/test_replay_backward_compat.py` 的 tempfile teardown `PermissionError`
- 已锁定根因：`emotiond.science.ledger` 在整个 run 生命周期内常驻 JSONL 文件句柄；部分测试路径不会显式 `end_run()`
- 已将 `Ledger` / `LedgerMVP11` 改为 append-per-call，无常驻句柄
- 已补回 `_file_handle` 兼容 sentinel，避免破坏旧测试契约
- 目标回归已通过：
  - `OpenEmotion/tests/mvp11/test_replay_backward_compat.py`
  - `OpenEmotion/tests/mvp10/test_logging_roundtrip.py::TestLedgerBasics::test_start_run`
  - `OpenEmotion/tests/mvp10/test_logging_roundtrip.py::TestLedgerBasics::test_end_run`
  - `OpenEmotion/tests/mvp10/test_science_mode_matrix.py`
- full verify 已复跑，并确认失败摘要中不再包含 `tests/mvp11/test_replay_backward_compat.py`

## Last validation results

- mode: targeted repro + targeted regression + verifier rerun
- result: slice acceptance reached; repo-level failures remain outside current slice
- summary:
  - `python3 -m py_compile OpenEmotion/emotiond/science/ledger.py`
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/mvp10/test_logging_roundtrip.py::TestLedgerBasics::test_start_run OpenEmotion/tests/mvp10/test_logging_roundtrip.py::TestLedgerBasics::test_end_run OpenEmotion/tests/mvp11/test_replay_backward_compat.py OpenEmotion/tests/mvp10/test_science_mode_matrix.py -q`
    - `59 passed, 2 warnings in 0.22s`
  - `python3 scripts/codex/verify_repo.py --mode fast`
    - success
  - `python3 scripts/codex/verify_repo.py --mode full`
    - `OpenEmotion test suite`: `57 failed, 4482 passed, 35 skipped, 20 errors`
    - current summary no longer contains `tests/mvp11/test_replay_backward_compat.py`
    - current summary no longer contains `tests/mvp10/test_logging_roundtrip.py`

## Decisions made

- 不修改 fixture 或测试来规避句柄问题
- 不依赖 `__del__` / GC / teardown 顺序；直接消掉 persistent file handle 设计
- 不删除 `_file_handle` 历史接口，而是降级为兼容 sentinel，避免无关测试回归

## Open risks

- full verify 仍有其他 replay / daemon / live fixture / outcome capture 失败，但它们不再归因为当前 ledger tempfile handle 泄漏
- `tests/mvp10/test_replay_determinism.py` 仍失败，但当前错误形态是 `LoopMVP10` / replay helper 的独立兼容问题，不属于这条 tempfile slice

## Next step

- 开下一条 OpenEmotion pytest stabilization slice，优先处理 `tests/test_daemon_lifecycle.py` 的 Windows sqlite/tempfile handle 错误

## Commands run / evidence

- `python3 scripts/codex/new_task.py openemotion-mvp11-replay-tempfile-stabilization --title "OpenEmotion MVP11 Replay Tempfile Stabilization"`
- `python3 -m py_compile OpenEmotion/emotiond/science/ledger.py`
- `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/mvp10/test_logging_roundtrip.py::TestLedgerBasics::test_start_run OpenEmotion/tests/mvp10/test_logging_roundtrip.py::TestLedgerBasics::test_end_run OpenEmotion/tests/mvp11/test_replay_backward_compat.py OpenEmotion/tests/mvp10/test_science_mode_matrix.py -q`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `python3 scripts/codex/verify_repo.py --mode full`
