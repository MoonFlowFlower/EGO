# OpenEmotion MVP10 Replay Determinism Stabilization - PLAN

## Task summary

- 问题层级是实现/验证层接口漂移。当前范围只收敛 MVP10 replay 脚本和 `LoopMVP10` 的 backward-compat 契约，不扩到其他 OpenEmotion 失败面。

## Milestones

### Milestone 1: Align replay script with current LoopMVP10 contract

- scope: 修复 replay 脚本中的旧字段访问，恢复从 summary/events 回放同一 run 的能力。
- files / areas likely touched:
  - `OpenEmotion/scripts/replay_mvp10.py`
- acceptance:
  - `replay_run()` 能在当前 `LoopMVP10` 接口下完成 replay
  - 不再访问 `loop.state` 或 `loop.ledger.events`
  - `test_replay_script_produces_matching_run` 通过
- validation:
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/mvp10/test_replay_determinism.py -q`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note: 若 replay 字段比较选错，回退为只比较测试明确要求的 deterministic fields。

### Milestone 2: Restore deterministic action backward compatibility

- scope: 让 `_select_action()` 兼容旧测试期望的 `action` key，同时保持当前 `type` key。
- files / areas likely touched:
  - `OpenEmotion/emotiond/loop_mvp10.py`
- acceptance:
  - `test_action_selection_deterministic` 通过
  - 新返回 shape 不破坏现有 `type` 读取方
- validation:
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/mvp10/test_replay_determinism.py -q`
  - `python3 scripts/codex/verify_repo.py --mode fast`
  - `python3 scripts/codex/verify_repo.py --mode full`
- rollback note: 若 shape 变更引起额外回归，仅保留 additive key，不改已有 key 语义。

## Progress

- current_status: completed
- current_milestone: Milestone 1 + 2
- milestone_state: patched and verified

## Decision log

- 2026-03-29: 先按现行 `LoopMVP10` 契约修 replay 脚本，而不是改测试。原因：失败来自旧 API 调用残留，属于实现层回归。
- 2026-03-29: `_select_action()` 采用 additive backward-compat。原因：测试期望 `action`，当前代码已输出 `type`，最小修复是双写同值。

## Surprises / discoveries

- `replay_mvp10.py` 依赖了三个已失效假设：`loop.state`、`start()` 返回值、`loop.ledger.events`
- `summary_<run_id>.json` 已含 `goals`，可作为 replay goal 的更强 authority source

## Outcomes / retrospective

- 本轮已证明：`tests/mvp10/test_replay_determinism.py` 已恢复通过，且失败根因确实是 replay script / action shape 的旧接口残留。
- 还没证明：OpenEmotion 全仓已全绿；当前仍有其他独立失败面。
- 下一步最小闭环动作：切到下一条独立失败面，不再在本 slice 内继续扩 scope。
