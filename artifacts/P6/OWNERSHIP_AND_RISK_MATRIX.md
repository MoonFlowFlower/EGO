# P6 OWNERSHIP_AND_RISK_MATRIX

| item | owner | current role | decision | risk | second-source risk | default-entry risk | exit plan |
|---|---|---|---|---|---|---|---|
| `EgoCore/app/runtime_v2/*` | EgoCore runtime | formal mainline | A | high | no | no | n/a |
| `EgoCore/app/telegram_bot.py:_handle_with_new_runtime` | EgoCore runtime | legacy compat path | B | medium | no | medium | 等对应兼容测试清零后删 |
| `EgoCore/app/telegram_bot.py:_handle_with_legacy_router` | EgoCore runtime | older compat path | B | high | no | high | 先确认无人通过 flags/旧脚本调用，再删 |
| `EgoCore/app/runtime/agent_runner.py` | EgoCore runtime | old runtime compat core | B | medium | no | medium | 迁走引用它的 legacy tests 后删 |
| `EgoCore/app/runtime/request_classifier.py` | EgoCore runtime | old runtime compat piece | B | medium | no | low | 同 `agent_runner.py` |
| `EgoCore/app/runtime/request_registry.py` | EgoCore runtime | old runtime compat piece | B | medium | no | low | 同 `agent_runner.py` |
| `OpenEmotion/legacy/openclaw/*` | OpenEmotion integration | historical host chain | B | high | no | high | 外部消费者确认清零后整体删除 |
| `OpenEmotion/openclaw_skill/emotion_core/*` | OpenEmotion integration | legacy bridge shim | B | high | no | high | 先补消费者审计，再从仓根迁出或删除 |
| `OpenEmotion/compatibility-only/tests/*` | OpenEmotion testing | manual compat checks | B | medium | no | no | 当 `legacy/openclaw` / `openclaw_skill` 删除时一起删 |
| `OpenEmotion/emotiond/memory/__init__.py` legacy exports | OpenEmotion memory | shim on formal surface | C | high | high | medium | 先迁走 `MemorySystem` 使用者，再移除 re-export |
| `OpenEmotion/emotiond/self_model/__init__.py` legacy exports | OpenEmotion self-model | shim on formal surface | C | high | high | medium | 先迁走 `SelfModelV0` 使用者与 adapter，再移除 re-export |
| `OpenEmotion/tools/e2e_memory_loop_check_v1.py` | OpenEmotion tooling | old verification tool | C | medium | medium | low | 改用新 memory API 后删除 |
| `OpenEmotion/tools/mvp13_daily_report.py` | OpenEmotion tooling | old report tool | C | medium | medium | low | 改用新 self-model manager 后删除 legacy import |
| `OpenEmotion/scripts/install_openclaw_integration.sh` | OpenEmotion integration | obsolete installer | D | high | no | high | 本次已删 |
| `OpenEmotion/tests/test_openclaw_skill.py` old path | OpenEmotion testing | misleading default test | C | high | no | high | 已迁出主 `tests/`；后续随 compat 链删除 |
| `OpenEmotion/tests/test_openclaw_integration2.py` old path | OpenEmotion testing | misleading default test | C | high | no | high | 已迁出主 `tests/`；后续随 compat 链删除 |
| `OpenEmotion/tests/test_final_integration.py` old path | OpenEmotion testing | misleading default test | C | high | no | high | 已迁出主 `tests/`；后续随 compat 链删除 |
| `OpenEmotion/emotiond/core.py.bak` | OpenEmotion core | dead backup candidate | D | medium | no | low | 下一轮确认后直接删 |
| `EgoCore/contracts/registry.json.bak` | EgoCore contracts | dead backup candidate | D | low | no | low | 下一轮确认后直接删 |

## P6 第二轮状态更新

| item | update |
|---|---|
| `OpenEmotion/emotiond/memory/__init__.py` legacy exports | 已从 formal surface 移除；second-source risk 从 `high` 降到 `medium`，残余风险转为 legacy module 本体仍在 |
| `OpenEmotion/emotiond/self_model/__init__.py` legacy exports | 已从 formal surface 移除；second-source risk 从 `high` 降到 `medium`，残余风险转为 legacy module 本体仍在 |
| `OpenEmotion/emotiond/core.py` | 已显式声明 legacy dependency，不再通过 formal surface 偷拿旧符号 |
| `OpenEmotion/emotiond/self_model_adapter.py` | 已显式声明 legacy dependency，不再通过 formal surface 偷拿旧符号 |

## 风险分层说明

- `high`
  - 仍在正式包表面暴露 legacy API
  - 仍在默认 `tests/`/主入口附近出现旧宿主链
  - 仍可能让 agent 误读当前正式主线
- `medium`
  - 主要影响局部工具/脚本/旧验证链
  - 不直接是正式入口，但仍制造引用噪音
- `low`
  - 明确副本或纯备份文件

## ownership 结论

- EgoCore runtime 负责：旧 Telegram / old runtime compat 退出
- OpenEmotion integration 负责：`legacy/openclaw`、`openclaw_skill` 生命周期管理
- OpenEmotion memory / self-model 负责：legacy export 从正式包表面退出
- OpenEmotion testing 负责：把 compatibility checks 与 formal validation 彻底分层
