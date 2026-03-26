# P6 COMPAT_ONLY_REGISTER

## register rules

- 所有 shim 都必须写明 owner、边界、寿命、退出条件。
- 未登记 shim 视为问题。
- compatibility-only 不等于 formal，也不等于长期保留。

## register

| shim / path | owner | boundary statement | current consumers | expires when | target action |
|---|---|---|---|---|---|
| `EgoCore/app/telegram_bot.py:_handle_with_new_runtime` | EgoCore runtime | 旧 runtime 兼容桥，不是正式 Telegram 主线 | 旧兼容测试/旧脚本 | legacy runtime tests 清零 | delete |
| `EgoCore/app/telegram_bot.py:_handle_with_legacy_router` | EgoCore runtime | 更早 Telegram 路由兜底，不是正式主线 | 旧兼容场景 | 调用者清零 | delete |
| `EgoCore/app/runtime/agent_runner.py` | EgoCore runtime | legacy runtime core，不是 Telegram formal mainline | 历史 runtime tests | runtime_v2-only 收口完成 | delete |
| `EgoCore/app/runtime/request_classifier.py` | EgoCore runtime | old runtime helper，不是 formal contract | 历史 runtime tests | 同上 | delete |
| `EgoCore/app/runtime/request_registry.py` | EgoCore runtime | old runtime helper，不是 formal contract | 历史 runtime tests | 同上 | delete |
| `OpenEmotion/openclaw_skill/emotion_core/*` | OpenEmotion integration | legacy OpenClaw bridge shim，不是 formal mainline | 未完成消费者审计 | 外部 compat 使用者为 0 | delete |
| `OpenEmotion/legacy/openclaw/*` | OpenEmotion integration | 历史宿主残留，不是 formal host chain | 未完成消费者审计 | 外部 compat 使用者为 0 | delete |
| `OpenEmotion/compatibility-only/tests/*` | OpenEmotion testing | 手工 compat checks，不是 formal validation | 手工兼容验证 | compat 链整体删除时 | delete |
| `OpenEmotion/emotiond/memory/__init__.py` legacy exports | OpenEmotion memory | 兼容导出，不是 memory formal truth | 旧 tests / tools | `MemorySystem` 使用者迁零 | migrate then delete |
| `OpenEmotion/emotiond/self_model/__init__.py` legacy exports | OpenEmotion self-model | 兼容导出，不是 self-model formal truth | 旧 tests / tools / adapter | `SelfModelV0` 使用者迁零 | migrate then delete |
| `OpenEmotion/emotiond/memory_legacy.py` | OpenEmotion memory | legacy memory compat module，不是 formal memory API | `emotiond.core.py`、旧 tests/tools | `emotiond.core` 与旧 callers 全迁出 | delete |
| `OpenEmotion/emotiond/self_model/legacy.py` | OpenEmotion self-model | legacy self-model compat module，不是 formal self-model API | `emotiond.core.py`、adapter、旧 tests/tools | `emotiond.core` 与 adapter/旧 callers 全迁出 | delete |

## register gaps

| gap | why it is a problem |
|---|---|
| `OpenEmotion/emotiond/core.py.bak` 未有正式登记 | 典型未登记死副本 |
| `EgoCore/contracts/registry.json.bak` 未有正式登记 | 典型未登记备份副本 |
| `OpenEmotion/tools/*` 中多份 legacy/self_model_v0 工具未单独登记 | 仍会制造工具层第二真相源噪音 |
