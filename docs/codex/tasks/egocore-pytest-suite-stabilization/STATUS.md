# EgoCore Pytest Suite Stabilization - STATUS

## Current milestone

- name: closed
- owner: Codex
- state: completed

## Current state

- current_layer: implementation + verification
- main_chain_status: `python3 scripts/codex/verify_repo.py --mode full` now clears `EgoCore pytest suite` and `EgoCore Telegram mainline regression`
- completion_class: conditional_complete

## Completed work

- 创建 bugfix slice：`docs/codex/tasks/egocore-pytest-suite-stabilization/`
- 完成 failure clustering，确认 portability/compatibility 与 runtime_v2/Telegram 是主失败簇
- 修复 repo portability 与 compatibility 问题：
  - doc inventory builder 的 repo root / tracked-file scan / hotspot timeout
  - runtime session/event bus sync compatibility
  - legacy marker / proto-self wiring 测试的路径与 async 约束
- 修复 runtime_v2 / Telegram 行为回归：
  - prompt fallback root
  - semantic short-question classification
  - tool broker / native loop config loading
  - Telegram setup/document filter 兼容
- 修复 full-surface 后续 blocker：
  - `MetricsHook` disabled-path 零开销与环境重读
  - `NativeToolCallingLoop` 不再覆盖 `contract_runtime.execute_tool` monkeypatch

## Last validation results

- mode: `full`
- result: passed_for_slice
- summary: `EgoCore pytest suite` => `745 passed, 1 warning`; `EgoCore Telegram mainline regression` => `69 passed, 1 warning`; `Codex repo lint` => success; `OpenEmotion` 仍有环境性 skipped

## Decisions made

- 先修 portability/hardcoded-path/compatibility 基线，再修 runtime_v2/Telegram 簇
- 统一以 `python3 scripts/codex/verify_repo.py --mode full` 为最终验收入口，不单独发明新收口标准
- 不为修复 `test_native_loop_contract_runtime` 去改测试口径，而是撤回 `native_loop` 对 `contract_runtime.execute_tool` 的强制覆盖，恢复可测试的 contract 边界

## Open risks

- 当前 `OpenEmotion` checks 仍依赖解释器环境：
  - current interpreter 缺 `fastapi`
  - testbot PR subset 缺可用 health endpoint `127.0.0.1:18080`
- 这些不是本 slice 的 EgoCore pytest failures，但会继续影响“全仓 full verify 全绿”的口径

## Next step

- 若继续推进，单开一个环境/依赖 slice，清理 OpenEmotion current-interpreter 依赖与 health endpoint 可用性

## Commands run / evidence

- `python3 scripts/codex/new_task.py egocore-pytest-suite-stabilization --title "EgoCore Pytest Suite Stabilization"`
- `python3 scripts/codex/verify_repo.py --mode full`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_cli_and_telegram.py EgoCore/tests/test_runtime_v2_delivery_unification.py EgoCore/tests/test_runtime_v2_e2e_chain_regression.py EgoCore/tests/test_runtime_v2_e2e_regression.py EgoCore/tests/test_runtime_v2_failure_notice_dedupe.py EgoCore/tests/test_runtime_v2_prompt_files.py EgoCore/tests/test_runtime_v2_typed_delivery.py EgoCore/tests/test_semantic_router.py EgoCore/tests/test_telegram_bot_single_start.py EgoCore/tests/test_telegram_prompt_command.py EgoCore/tests/test_telegram_run_without_manual_setup.py -q -s`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_doc_system_inventory_builder.py::test_doc_system_inventory_builder_generates_key_outputs -q -s`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/integration/test_metrics_production_integration.py::TestFlagOffConsistency::test_flag_off_zero_overhead -q -s`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_native_loop.py EgoCore/tests/test_native_loop_contract_runtime.py -q -s`
- `/tmp/egocore_full_verify.log`
