# EgoCore Pytest Suite Stabilization - PLAN

## Task summary

这是一个 `bugfix + long-run` slice。目标层级是实现/验证层：修复当前 full verify 中 `EgoCore pytest suite` 的失败簇，并回到统一验证入口确认主链更接近全绿。

## Milestones

### Milestone 1: Portability and compatibility baseline

- scope: 修复硬编码路径、旧接口兼容别名、async test 标记等会直接导致测试失效的基础问题
- files / areas likely touched:
  - `EgoCore/tests/test_doc_system_inventory_builder.py`
  - `EgoCore/tests/test_legacy_runtime_module_markers.py`
  - `EgoCore/tests/test_proto_self_wiring.py`
  - `EgoCore/app/agent_core/native_loop.py`
  - `EgoCore/app/runtime/session_manager.py`
  - `EgoCore/app/runtime/event_bus.py`
- acceptance:
  - 上述测试文件不再依赖 `/home/moonlight/...` 绝对路径
  - `test_native_loop.py`、`test_runtime_architecture.py`、`test_proto_self_wiring.py` 的已知接口失配消失
- validation:
  - `cd EgoCore && PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest tests/test_doc_system_inventory_builder.py tests/test_legacy_runtime_module_markers.py tests/test_native_loop.py tests/test_proto_self_wiring.py tests/test_runtime_architecture.py -v -s`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note: 若兼容 shim 破坏主运行时，优先回退到仅测试侧路径修复，再单独隔离 runtime 兼容层

### Milestone 2: Runtime v2 / Telegram regression cluster

- scope: 修复 runtime_v2、Telegram bot、prompt loading、semantic routing 的剩余失败簇
- files / areas likely touched:
  - `EgoCore/tests/test_runtime_v2_*.py`
  - `EgoCore/tests/test_semantic_router.py`
  - `EgoCore/tests/test_telegram_*.py`
  - `EgoCore/app/telegram_bot.py`
  - `EgoCore/app/runtime_v2/*`
  - `EgoCore/app/runtime/semantic_router.py`
- acceptance:
  - `.pytest_cache/lastfailed` 中当前 25 个失败项清零
  - 相关 runtime_v2 / Telegram 子集测试通过
- validation:
  - `cd EgoCore && PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest tests/test_runtime_v2_cli_and_telegram.py tests/test_runtime_v2_delivery_unification.py tests/test_runtime_v2_e2e_chain_regression.py tests/test_runtime_v2_e2e_regression.py tests/test_runtime_v2_failure_notice_dedupe.py tests/test_runtime_v2_prompt_files.py tests/test_runtime_v2_typed_delivery.py tests/test_semantic_router.py tests/test_telegram_bot_single_start.py tests/test_telegram_prompt_command.py tests/test_telegram_run_without_manual_setup.py tests/test_runtime_v2_proto_self_runtime.py tests/test_telegram_artifact_confirmation_flow.py -v -s`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note: 若某个失败簇需要跨模块重构，则在本 milestone 内降级为 blocker 记录，不顺手扩大到新设计任务

## Progress

- current_status: completed
- current_milestone: closed
- milestone_state: both milestones implemented and full verify rerun completed

## Decision log

- 2026-03-29: 先做 portability/compatibility 基线修复，再处理 runtime_v2/Telegram 失败簇；原因是这批失败改动面最小，且能直接减少误报
- 2026-03-29: 不在本 slice 内处理 OpenEmotion 缺依赖导致的 skipped；原因是当前用户目标只针对 EgoCore pytest suite failures
- 2026-03-29: `build_doc_system_inventory.py` 改为 `git ls-files` 优先扫描并缩短 hotspot timeout；原因是 full verify 在 doc inventory builder 测试上出现不可判定挂起
- 2026-03-29: `MetricsHook` 的 `enabled=false` 收紧为零开销 dropped 路径，并允许 `initialize()` 重读环境；原因是 full verify 暴露了 disabled-path overhead 与全局 hook 配置残留
- 2026-03-29: 移除 `native_loop.run_turn()` 对 `contract_runtime.execute_tool` 的强制覆盖；原因是这会破坏 contract-runtime 测试中的 monkeypatch，并把验证错误地拉回真实工具环境

## Surprises / discoveries

- `verify_repo.py --mode full` 已经能到达真实 failure surface，当前 25 个失败主要来自测试可移植性、兼容 API 漂移和 runtime_v2/Telegram 行为回归
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion` 是当前 EgoCore pytest suite 可收集运行的必要前提
- `TelegramBot` 的 runtime_v2 lazy-loop 契约本身是对的，剩余回归主要是路径同步与测试夹具假设问题，不需要再扩大到 native/runtime_v2 设计改写
- `Path.rglob('*')` 即使后置过滤，也会把大目录遍历成本带进 full verify；这类 inventory tool 需要前置剪枝或走 tracked-file 列表

## Outcomes / retrospective

- 本轮已证明：`EgoCore pytest suite` 的 25 个现有失败已收敛到 0，且 `python3 scripts/codex/verify_repo.py --mode full` 下的 `EgoCore pytest suite` 现在是 `745 passed, 1 warning`
- 本轮也已证明：`EgoCore Telegram mainline regression` 继续通过，说明这批修复没有把 Telegram 主链打坏
- 仍未证明：全仓 full verify 完全无 skipped；当前剩余 `OpenEmotion` skipped 来自解释器依赖与 health endpoint 缺失，超出本 slice 目标
- 下一步最小闭环动作：若继续推进，应单开环境/依赖 slice，专门清理 OpenEmotion current-interpreter `fastapi` 缺依赖与 testbot health endpoint 缺失
