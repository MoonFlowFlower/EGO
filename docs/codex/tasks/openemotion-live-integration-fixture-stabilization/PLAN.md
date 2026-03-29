# OpenEmotion Live Integration Fixture Stabilization - PLAN

## Task summary

这是一个实现 / 验证层的 pytest stabilization slice。范围只覆盖 `test_live_integration_fixture.py` 的 live 启动契约，不扩到其他 OpenEmotion 失败面。

## Milestones

### Milestone 1: Reproduce and repair fixture contract failures

- scope: 复现 live fixture 失败，修复解释器路径选择、health timeout 预算、port-conflict 测试契约
- files / areas likely touched:
  - `OpenEmotion/tests/test_live_integration_fixture.py`
- acceptance:
  - `OpenEmotion/tests/test_live_integration_fixture.py` 全量通过
  - `WinError 1920` 不再出现
  - no-server 与 port-conflict case 都按预期返回失败信号
- validation:
  - `/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/.venv/Scripts/python.exe -m pytest OpenEmotion/tests/test_live_integration_fixture.py -q`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note: 如果 health probe 收缩导致 live 启动误报，回退 timeout 调整，仅保留解释器路径与 host binding 契约修复

### Milestone 2: Re-run repo verifier and classify remaining failures

- scope: 用 full verifier 确认当前失败面已离开仓库级 summary，并把剩余失败明确归到其他 slice
- files / areas likely touched:
  - `docs/codex/tasks/openemotion-live-integration-fixture-stabilization/*.md`
- acceptance:
  - `python3 scripts/codex/verify_repo.py --mode full` 已复跑
  - `tests/test_live_integration_fixture.py` 不再出现在 failed/error summary
- validation:
  - `python3 scripts/codex/verify_repo.py --mode full`
- rollback note: 如果 full verify 暴露当前 patch 引入的新回归，停在当前 slice 内修复，不跳到其他失败面

## Progress

- current_status: completed
- current_milestone: Milestone 2
- milestone_state: 目标测试、fast verify、full verify 已完成；当前 slice 已与其余 OpenEmotion 失败面分离

## Decision log

- 2026-03-29: 这条 failure surface 先按测试契约错误处理，不先动 emotiond 主逻辑；因为首轮失败全部收敛在 fixture 路径解析与 probe 预算
- 2026-03-29: live fixture 的解释器解析需要先尝试 Windows `Scripts/python.exe`，并对坏 venv 路径的 `Path.exists()` 异常做兼容
- 2026-03-29: port-conflict 在当前 Windows 环境必须占用 `127.0.0.1` 才能稳定和 `uvicorn --host 127.0.0.1` 形成真实冲突

## Surprises / discoveries

- `('', 0)` 在当前 Windows 环境里不能稳定阻止 `uvicorn --host 127.0.0.1` 绑定同端口，导致旧测试假阳性
- `wait_for_health()` 原先固定单次 `requests` timeout=2，会把 `timeout=1` 的总预算压成单次尝试

## Outcomes / retrospective

- 本轮已证明：
  - `test_live_integration_fixture.py` 的首要问题是测试契约和跨平台路径处理，而不是 daemon 业务主逻辑损坏
  - 目标文件已恢复全绿
  - `fast verify` 已通过
-  - `full verify` 中该失败面已完全离开仓库级 summary
- 还没证明：
  - OpenEmotion 全仓 full verify 已全绿
- 下一步最小闭环动作：
  - 单开下一条 OpenEmotion pytest stabilization slice，优先处理 `tests/test_outcome_capture_integration.py`
