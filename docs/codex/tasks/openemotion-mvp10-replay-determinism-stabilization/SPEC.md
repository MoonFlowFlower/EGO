# OpenEmotion MVP10 Replay Determinism Stabilization

## Goal

- 修复 `tests/mvp10/test_replay_determinism.py` 的两处回归，使 MVP10 replay 脚本与 `LoopMVP10` 的现行接口重新对齐，并恢复 deterministic replay 的最小验证链。

## Non-goals

- 不处理其他 OpenEmotion pytest 失败面。
- 不重构 MVP10/MVP11 命名历史或 replay 架构。
- 不扩到新的 determinism 指标或更深层 replay 语义变更。

## Constraints

- 边界约束：只修接口漂移和 backward-compat 断点，不改随机性算法。
- 仓库/子仓约束：改动保持在 `OpenEmotion` 和当前 codex task 文档。
- 环境约束：验证使用现有 `OpenEmotion/.venv/Scripts/python.exe` 与 repo verifier。
- 发布约束：必须先过目标测试和 `python3 scripts/codex/verify_repo.py --mode fast`，再给完成口径。

## Acceptance criteria

- [ ] `tests/mvp10/test_replay_determinism.py` 通过
- [ ] `scripts/replay_mvp10.py` 不再访问不存在的 `loop.state` / `loop.ledger.events`
- [ ] `LoopMVP10._select_action()` 保持 deterministic，并兼容测试期望的 `action` key
- [ ] `python3 scripts/codex/verify_repo.py --mode fast` 通过

## Known risks / dependencies

- 风险：若 replay 比较字段选错，可能把时间戳漂移误判为非 deterministic。
- 依赖：`LoopMVP10` 当前 JSONL 事件格式、`summary_<run_id>.json`、`Ledger.load_run()`
- 外部 blocker：无

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `OpenEmotion/tests/mvp10/test_replay_determinism.py`
- `OpenEmotion/scripts/replay_mvp10.py`
- `OpenEmotion/emotiond/loop_mvp10.py`
