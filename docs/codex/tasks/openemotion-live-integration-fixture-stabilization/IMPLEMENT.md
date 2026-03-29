# OpenEmotion Live Integration Fixture Stabilization - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `OpenEmotion/tests/test_live_integration_fixture.py`
- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 每次只推进 `STATUS.md` 中的 `Current milestone`
- 当前 slice 只修 live fixture 契约，不扩到其他 OpenEmotion 失败面

## Scope control

- 只改 live fixture 及其状态文档
- 不顺手推进下一个 milestone
- 保持 diff scoped，不把 `test_outcome_capture_integration.py` 等其他失败面并入本 slice

## Validation strategy

- 当前 slice 的决定性验证：
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/test_live_integration_fixture.py -q`
- 每个 milestone 完成后运行：
  - `python3 scripts/codex/verify_repo.py --mode fast`
- 收口时运行：
  - `python3 scripts/codex/verify_repo.py --mode full`

## Failure handling

- 如果目标测试仍失败，优先继续收缩到 fixture 解释器解析、health probe 预算、port-conflict host binding 三个直接点
- 如果 verifier 暴露新回归，先修当前 slice 引入的回归
- 不因仓库里其他现存失败面而误报本 slice 未完成

## Stopping rule

- `test_live_integration_fixture.py` 未全绿，不进入下一失败面
- 当前 slice targeted 验证通过且 verifier 已补最小收口后停止

## Final handoff checklist

- [x] `PLAN.md` 已更新进度与决策
- [x] `STATUS.md` 已更新验证结果与 next step
- [x] commands run / evidence 已记录
- [x] risks / rollback notes 已记录
