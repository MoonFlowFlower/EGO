# P6 TASK_REPORT

## 任务名称

P6：垃圾代码 / 历史 shim / 重复真相源清坟

## 任务类型

代码治理 / 历史清理 / 真相源收口

## 目标与成功判据

- 先盘点再清理，建立 `keep / compatibility-only / migrate then delete / delete now` 决策矩阵
- 找出仍在悄悄承担“第二真相源”或“默认入口”的高危遗留项
- 为每个保留 shim 明确 owner、寿命和退出计划
- 处理一批确定危险且不影响主链的遗留物
- 让仓库阅读路径更接近唯一主链，而不是默认踩进旧入口

## 当前层级

治理层 / 历史债清理层 / 真相源收口层

## 当前确定项

- P5 已把正式 packaging/import 权威源收回到工程配置
- 当前正式双核边界仍是 `EgoCore` 宿主 + `OpenEmotion` 主体本体
- `RuntimeV2` 是 Telegram 正式主线；旧 runtime 与旧 Telegram 路径只是 compatibility-only
- `OpenClaw` 不是正式宿主，但仓库内仍有 `legacy/openclaw` 与 `openclaw_skill` 遗留
- `OpenEmotion` 的 memory / self-model formal surface 已去掉 legacy 默认导出，但 legacy module 本体仍在

## 关键未知

- `openclaw_skill` 与 `legacy/openclaw` 是否还有仓外消费者
- `emotiond.memory` / `emotiond.self_model` 的 legacy export 迁移量到底多大
- `EgoCore/app/runtime/*` 旧 runtime 兼容族何时能完全清零

## 唯一主执行链

1. 先做 inventory 与 ownership / risk 分级。
2. 找出默认入口风险与第二真相源风险。
3. 先删零引用垃圾与错误入口。
4. 再把旧验证面迁出 formal 主路径。
5. 对不能删的 shim 统一登记寿命与退出计划。

## 不做项

- 不做 P7
- 不处理 Telegram 输出转义
- 不处理历史 ledger 回填
- 不处理 E5 聚合器
- 不顺手改 README 总口径
- 不删除当前仍被主链或验证链依赖的文件

## 前提检查

- 未发现 P5 前提失效
- 因此未触发《前提失效报告》

## 盘点结论

- path-hack 仍大量存在，但主要沉积在历史 `tools/`、`scripts/`、`tests/`
- 最危险的不是“代码旧”，而是“旧东西仍挂在默认入口或正式包表面”
- 当前最值得优先防回漂的遗留项有三类：
  - 主 `tests/` 下会被默认发现的旧 OpenClaw 测试
  - 正式包表面继续暴露 legacy API 的 `emotiond.memory` / `emotiond.self_model`
  - 仍留在正式 bot/runtime 文件中的旧 Telegram / old runtime compat 路径

## 本次实际改动

- 删除：
  - `OpenEmotion/scripts/install_openclaw_integration.sh`
  - `OpenEmotion/tests/test_final_integration.py.bak`
  - `OpenEmotion/tests/test_final_integration_daemon.py.bak`
- 迁移到 compatibility-only：
  - `OpenEmotion/tests/test_openclaw_skill.py`
  - `OpenEmotion/tests/test_openclaw_integration2.py`
  - `OpenEmotion/tests/test_final_integration.py`
- 新增：
  - `OpenEmotion/compatibility-only/tests/README.md`
- 口径纠偏：
  - `OpenEmotion/tests/test_project_structure.py`
  - `OpenEmotion/tests/test_documentation.py`
  - `OpenEmotion/tests/test_comprehensive_fixed.py`
  - `OpenEmotion/tests/test_comprehensive_suite.py`
  - `OpenEmotion/openclaw_skill/emotion_core/skill.py`
  - `OpenEmotion/openclaw_skill/emotion_core/SKILL.md`

## P6 第二轮：emotiond legacy re-export 收口

- `OpenEmotion/emotiond/memory/__init__.py`
  - 不再从 formal surface 暴露 `MemorySystem` / `memory_system` / `initialize_memory_system`
  - legacy memory 只留在 `emotiond.memory_legacy`
- `OpenEmotion/emotiond/self_model/__init__.py`
  - 不再从 formal surface 暴露 `SelfModelV0` / `get_self_model_v0` / `build_self_model_v0` / `render_self_report` 等
  - legacy self-model 只留在 `emotiond.self_model.legacy`
- 显式迁移调用点
  - `OpenEmotion/emotiond/core.py`
  - `OpenEmotion/emotiond/self_model_adapter.py`
  - 一批 legacy tests/tools
- 新增边界守护测试：
  - `OpenEmotion/tests/test_emotiond_legacy_reexports_boundary.py`

## 本次关键判断

### A. keep as formal

- `EgoCore/app/runtime_v2/*`
- `EgoCore/app/telegram_bot.py` 的 `use_runtime_v2` 主链
- `OpenEmotion/openemotion/*`
- 当前边界/宪章主文档

### B. keep as compatibility-only

- `EgoCore/app/telegram_bot.py` 中 `_handle_with_new_runtime`
- `EgoCore/app/telegram_bot.py` 中 `_handle_with_legacy_router`
- `EgoCore/app/runtime/{agent_runner,request_classifier,request_registry}.py`
- `OpenEmotion/legacy/openclaw/*`
- `OpenEmotion/openclaw_skill/*`
- `OpenEmotion/compatibility-only/tests/*`

### C. migrate then delete

- `OpenEmotion/emotiond/memory_legacy.py`
- `OpenEmotion/emotiond/self_model/legacy.py`
- 依赖 `memory_legacy` / `SelfModelV0` 的旧 tools/tests
- `EgoCore` 旧 runtime 兼容族

### D. delete now

- `OpenEmotion/scripts/install_openclaw_integration.sh`
- 2 个 `tests/*.bak`

## 高危遗留项

| item | danger |
|---|---|
| `OpenEmotion/emotiond/memory_legacy.py` | legacy memory 本体仍在，formal callers 还未迁零 |
| `OpenEmotion/emotiond/self_model/legacy.py` | legacy self-model 本体仍在，formal callers 还未迁零 |
| `EgoCore/app/telegram_bot.py:_handle_with_legacy_router` | 仍在正式 bot 文件内，存在默认入口回漂风险 |
| `OpenEmotion/openclaw_skill/*` | 根路径存在，容易被误判成正式入口 |
| `OpenEmotion/legacy/openclaw/*` | 结构完整，容易被误判成仍可作为主链 |

第二轮后，`emotiond.memory` 与 `emotiond.self_model` 的 formal surface 已不再是高危点；残余风险转移到 legacy module 本体与其显式调用者。

## 验证

- `python3 -m py_compile ...`：通过
- `python3 -m pytest ...`：阻塞，当前 shell 无 `pytest`
- AST 校验 `__all__`：通过，formal surface 已不含 legacy symbols
- import smoke：阻塞，当前 shell 缺 `aiosqlite`
- 文本与引用关系回扫：已完成

## 本次结论能证明什么

- 能证明仓库内确实存在大量 compatibility-only / legacy / duplicate truth 风险，而不是“只是看起来旧”
- 能证明三份最误导的 OpenClaw 旧测试已不再处于主 `tests/` 默认发现面
- 能证明一条错误的旧安装入口和两份 `*.bak` 垃圾副本已经清除
- 能证明 `emotiond.memory` 与 `emotiond.self_model` 的 legacy API 已不再作为默认正式入口
- 能证明当前仍有两类高危项没法直接删：legacy module 本体，以及 `EgoCore` 旧 runtime compat 族

## 本次结论不能证明什么

- 不能证明 `openclaw_skill` 与 `legacy/openclaw` 已无任何仓外用户
- 不能证明所有 path-hack 文件都已退出
- 不能证明 `emotiond.memory_legacy.py` / `emotiond.self_model/legacy.py` 已可立即删除
- 不能证明全仓 pytest 回归通过，因为当前环境缺 `pytest`

## 还有哪些遗留项暂时不能删

- `EgoCore/app/telegram_bot.py` 中两个 compat handler
- `EgoCore/app/runtime/{agent_runner,request_classifier,request_registry}.py`
- `OpenEmotion/legacy/openclaw/*`
- `OpenEmotion/openclaw_skill/*`
- `OpenEmotion/emotiond/memory_legacy.py`
- `OpenEmotion/emotiond/self_model/legacy.py`
- 直接依赖 `MemorySystem` / `SelfModelV0` 的旧 tools/tests

## 离 P7 还差什么

- 先把 `emotiond.memory_legacy.py` / `emotiond.self_model/legacy.py` 的剩余调用者继续迁走
- 先补 `openclaw_skill` / `legacy/openclaw` 仓外消费者审计
- 先清掉 `EgoCore` 旧 runtime compat 族的最后调用者
- 先把未登记备份副本如 `OpenEmotion/emotiond/core.py.bak`、`EgoCore/contracts/registry.json.bak` 做完下一轮处理
- 然后才适合进入 P7 的风险信号单一化，而不是带着旧入口噪音继续往上叠
