# P6 DELETE_PLAN

## 已完成 delete-now

| item | why delete now | evidence |
|---|---|---|
| `OpenEmotion/scripts/install_openclaw_integration.sh` | 指向 `~/.openclaw` 旧宿主安装流程，零活动引用，误导默认入口 | 文本引用扫描仅剩 generated/archive；脚本本身仍输出 `openclaw hooks enable` |
| `OpenEmotion/tests/test_final_integration.py.bak` | 纯副本垃圾 | 仓内无引用 |
| `OpenEmotion/tests/test_final_integration_daemon.py.bak` | 纯副本垃圾 | 仓内无引用 |

## 已完成 migrate-then-keep-compat

| old path | new path | reason |
|---|---|---|
| `OpenEmotion/tests/test_openclaw_skill.py` | `OpenEmotion/compatibility-only/tests/openclaw_skill_compat.py` | 从默认 pytest 主验证面迁出 |
| `OpenEmotion/tests/test_openclaw_integration2.py` | `OpenEmotion/compatibility-only/tests/openclaw_integration2_compat.py` | 从默认 pytest 主验证面迁出 |
| `OpenEmotion/tests/test_final_integration.py` | `OpenEmotion/compatibility-only/tests/final_integration_openclaw_compat.py` | 从默认 pytest 主验证面迁出 |

## 下一轮 delete-now 候选

| item | blocking check | owner | note |
|---|---|---|---|
| `OpenEmotion/emotiond/core.py.bak` | 再确认无运行/文档引用 | OpenEmotion core | 当前文本扫描未发现引用 |
| `EgoCore/contracts/registry.json.bak` | 再确认无人工流程依赖 | EgoCore contracts | 典型备份副本 |

## migrate-then-delete backlog

| item | migrate target | delete condition |
|---|---|---|
| `OpenEmotion/emotiond/memory/__init__.py` legacy exports | `openemotion.memory/*` 或新的 `emotiond.memory.*` 正式 API | `MemorySystem` 使用者迁零 |
| `OpenEmotion/emotiond/self_model/__init__.py` legacy exports | `SelfModelManager` / `schema` / `updates` | `SelfModelV0` 直接依赖迁零 |
| `OpenEmotion/tools/e2e_memory_loop_check_v1.py` | 新 memory API 版本工具 | 不再 import `memory_legacy` |
| `OpenEmotion/tools/mvp13_daily_report.py` | 新 self-model manager 路径 | 不再 import `get_self_model_v0` |
| `EgoCore/app/telegram_bot.py:_handle_with_legacy_router` | Runtime v2 only | 兼容 flags 与旧测试清零 |
| `EgoCore/app/runtime/agent_runner.py` 及相关旧 runtime 族 | Runtime v2 / formal runtime APIs | legacy tests 清零 |
| `OpenEmotion/openclaw_skill/*` | none | 外部 compat 消费者为 0 |
| `OpenEmotion/legacy/openclaw/*` | none | 同上 |

## delete sequencing

1. 先删零引用副本和错误安装入口。
2. 再把旧测试/旧脚本从默认发现面迁出。
3. 再迁掉正式包表面的 legacy re-export。
4. 最后整体删除 compat 链目录。

## P6 第二轮已完成的迁移步骤

1. `emotiond.memory.__all__` 已去掉 legacy symbols。
2. `emotiond.self_model.__all__` 已去掉 legacy symbols。
3. formal / compat callers 改为显式 import `emotiond.memory_legacy` 与 `emotiond.self_model.legacy`。
4. 新增边界守护测试 `OpenEmotion/tests/test_emotiond_legacy_reexports_boundary.py`。
