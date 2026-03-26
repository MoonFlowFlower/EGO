# P6 CLEANUP_INVENTORY

## 盘点范围

- 已读取任务与前置文档：`Tasks/task_pack_260325/*`、`artifacts/P5/*`
- 已扫描主范围：`docs/`、`scripts/`、`EgoCore/{docs,scripts,tests,tools}`、`OpenEmotion/{docs,scripts,tests,tools}`
- 已额外记录直接命中的兼容遗留：`OpenEmotion/legacy/openclaw/*`、`OpenEmotion/openclaw_skill/*`、`OpenEmotion/emotiond/*legacy*`、`OpenEmotion/emotiond/core.py.bak`

## 目录级 inventory

| path | files | path hack count | 当前判断 |
|---|---:|---:|---|
| `EgoCore/tools` | 27 | 18 | 历史验证脚本重，默认不算正式主链 |
| `EgoCore/scripts` | 21 | 9 | 历史运行/实验脚本，混有兼容入口 |
| `EgoCore/tests` | 90 | 15 | 既有正式守护测试，也有 legacy 标记测试 |
| `OpenEmotion/tools` | 46 | 30 | 历史实验/日报脚本重，兼容与过渡实现很多 |
| `OpenEmotion/scripts` | 88 | 59 | 历史实验/评估脚本密度高，非正式主链 |
| `OpenEmotion/tests` | 304 | 94 | 历史测试沉积最重，默认发现面容易误导 |
| `OpenEmotion/legacy/openclaw` | 21 | n/a | 明确历史宿主残留 |
| `OpenEmotion/openclaw_skill` | 4 | n/a | 明确兼容 skill 入口 |

## 决策矩阵

| item | decision | risk | 说明 | 本次状态 |
|---|---|---|---|---|
| `EgoCore/app/runtime_v2/*` | A keep as formal | high | Telegram 正式主链运行时 | 保留 |
| `EgoCore/app/telegram_bot.py` 中 `use_runtime_v2` 路径 | A keep as formal | high | 当前正式 Telegram 入口 | 保留 |
| `EgoCore/app/telegram_bot.py` 中 `_handle_with_new_runtime` | B keep as compatibility-only | medium | 旧 runtime 兼容桥 | 登记，未删 |
| `EgoCore/app/telegram_bot.py` 中 `_handle_with_legacy_router` | B keep as compatibility-only | high | 旧 Telegram 路由兜底，仍可被调用 | 登记，未删 |
| `EgoCore/app/runtime/agent_runner.py` | B keep as compatibility-only | medium | 旧 runtime core，仍被部分测试引用 | 登记，未删 |
| `EgoCore/app/runtime/request_classifier.py` | B keep as compatibility-only | medium | 旧 runtime 族组件 | 登记，未删 |
| `EgoCore/app/runtime/request_registry.py` | B keep as compatibility-only | medium | 旧 runtime 族组件 | 登记，未删 |
| `OpenEmotion/openemotion/*` | A keep as formal | high | 主体本体正式实现 | 保留 |
| `OpenEmotion/docs/00_MASTER_INDEX.md` / `03_BOUNDARY_AND_OWNERSHIP.md` / 边界宪章 | A keep as formal | high | 当前边界权威文档 | 保留 |
| `OpenEmotion/legacy/openclaw/*` | B keep as compatibility-only | high | 历史宿主链，易误导成正式入口 | 登记，未删 |
| `OpenEmotion/openclaw_skill/emotion_core/*` | B keep as compatibility-only | high | 兼容 skill 入口，已显式改成 compatibility-only 口径 | 已标记 |
| `OpenEmotion/compatibility-only/tests/*` | B keep as compatibility-only | medium | 手工兼容验证面，不再让 pytest 默认发现 | 本次新增承接路径 |
| `OpenEmotion/emotiond/memory/__init__.py` 的 legacy 导出 | C migrate then delete | high | 通过正式包表面继续暴露 `MemorySystem`，有第二真相源风险 | 仅登记 |
| `OpenEmotion/emotiond/self_model/__init__.py` 的 legacy 导出 | C migrate then delete | high | 通过正式包表面继续暴露 `SelfModelV0` 族 API | 仅登记 |
| `OpenEmotion/tools/e2e_memory_loop_check_v1.py` | C migrate then delete | medium | 直接 import `emotiond.memory_legacy` | 仅登记 |
| `OpenEmotion/tools/mvp13_daily_report.py` | C migrate then delete | medium | 继续依赖 `get_self_model_v0` | 仅登记 |
| `OpenEmotion/scripts/install_openclaw_integration.sh` | D delete now | high | 零活动引用、口径指向 `~/.openclaw` 旧宿主、误导默认接线 | 已删除 |
| `OpenEmotion/tests/test_final_integration.py.bak` | D delete now | low | 纯副本垃圾 | 已删除 |
| `OpenEmotion/tests/test_final_integration_daemon.py.bak` | D delete now | low | 纯副本垃圾 | 已删除 |
| `OpenEmotion/tests/test_openclaw_skill.py` | C migrate then delete | high | 位于主 `tests/`，会被默认收集，误导正式验证面 | 已迁到 `compatibility-only` |
| `OpenEmotion/tests/test_openclaw_integration2.py` | C migrate then delete | high | 位于主 `tests/`，仍验证旧 OpenClaw handler | 已迁到 `compatibility-only` |
| `OpenEmotion/tests/test_final_integration.py` | C migrate then delete | high | 位于主 `tests/`，依赖 `venv2` + `openclaw_skill` | 已迁到 `compatibility-only` |
| `OpenEmotion/emotiond/core.py.bak` | D delete now candidate | medium | 仓内代码副本，当前零文本引用 | 本次只登记，待单独删除 |
| `EgoCore/contracts/registry.json.bak` | D delete now candidate | low | 仓内备份副本 | 本次只登记，待单独删除 |

## 仍承担“第二真相源”或“默认入口”风险的项

| item | 风险类型 | 为什么危险 |
|---|---|---|
| `OpenEmotion/emotiond/memory/__init__.py` | 第二真相源 | 正式包入口继续把 `MemorySystem` 暴露为默认 import 面 |
| `OpenEmotion/emotiond/self_model/__init__.py` | 第二真相源 | 正式包入口继续把 legacy `SelfModelV0` 族 API 暴露为默认 import 面 |
| `EgoCore/app/telegram_bot.py` 中 `_handle_with_legacy_router` | 默认入口回漂 | 仍在正式 bot 文件里，可被 flags/兼容逻辑命中 |
| `OpenEmotion/openclaw_skill/emotion_core/*` | 默认入口误判 | 根路径直观、易被误认为正式集成面 |
| `OpenEmotion/legacy/openclaw/*` | 默认入口误判 | 名字虽带 legacy，但仍保留完整 hooks/skills/tests 结构 |

## 本次已实际处置

| change | result |
|---|---|
| 删除 `OpenEmotion/scripts/install_openclaw_integration.sh` | 去掉零引用且错误指向旧宿主的安装入口 |
| 删除 2 个 `tests/*.bak` | 去掉纯副本垃圾 |
| 将 3 个 OpenClaw 旧测试迁到 `OpenEmotion/compatibility-only/tests/` 并改名 | 不再作为默认 pytest 主验证面被发现 |
| 更新 `OpenEmotion/tests/test_project_structure.py` | 不再把 `openclaw_skill` 视为正式必备结构 |
| 更新 `OpenEmotion/tests/test_documentation.py` | 不再把 “OpenClaw skill usage” 视为正式文档必备项 |
| 更新 `OpenEmotion/tests/test_comprehensive_fixed.py` / `test_comprehensive_suite.py` | 不再把 OpenClaw 旧测试写进综合主测试面 |
| 更新 `OpenEmotion/openclaw_skill/emotion_core/{skill.py,SKILL.md}` | 显式标明 compatibility-only |

## P6 第二轮：emotiond legacy re-export 收口

| item | old state | new state | decision | status |
|---|---|---|---|---|
| `OpenEmotion/emotiond/memory/__init__.py` | 正式包表面暴露 `MemorySystem` / `memory_system` / `initialize_memory_system` | 只导出 MVP-10 formal memory API；legacy 仅在 `emotiond.memory_legacy` | C migrate then delete | 本轮已完成“去默认导出”，未删 legacy 模块本体 |
| `OpenEmotion/emotiond/self_model/__init__.py` | 正式包表面暴露 `SelfModelV0`、`get_self_model_v0`、`render_self_report` 等 legacy API | 只导出 MVP13 formal self-model API；legacy 仅在 `emotiond.self_model.legacy` | C migrate then delete | 本轮已完成“去默认导出”，未删 legacy 模块本体 |
| `OpenEmotion/emotiond/core.py` | 从正式包表面取 legacy memory/self-model 符号 | 改为显式 import `memory_legacy` 与 `self_model.legacy` | B keep as compatibility-aware formal caller | 已迁移 |
| `OpenEmotion/emotiond/self_model_adapter.py` | 从正式包表面取 `get_self_model_v0` | 改为显式 import `emotiond.self_model.legacy` | B keep as compatibility-aware formal caller | 已迁移 |
| `OpenEmotion/tools/*` 与 `OpenEmotion/tests/*` 中 legacy 调用点 | 从正式包表面取 legacy 符号 | 改为显式 legacy import | B keep as compatibility-only callers | 已迁移一批高频调用点 |
