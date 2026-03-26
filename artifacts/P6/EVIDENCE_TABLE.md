# P6 EVIDENCE_TABLE

| claim | evidence | result |
|---|---|---|
| P5 前提仍成立：主链 runtime path hack 已从正式入口移除 | `artifacts/P5/TASK_REPORT.md`、`artifacts/P5/IMPORT_HACK_INVENTORY.md` | 成立 |
| 当前正式边界仍是 EgoCore 宿主 + OpenEmotion 本体 | `EgoCore/docs/03_BOUNDARY_AND_OWNERSHIP.md`、`OpenEmotion/docs/03_BOUNDARY_AND_OWNERSHIP.md`、边界宪章 | 成立 |
| OpenClaw 不是正式宿主 | `EgoCore/docs/00_MASTER_INDEX.md`、`OpenEmotion/docs/00_MASTER_INDEX.md` | 成立 |
| 旧 Telegram 路径仍在代码里作为 compatibility-only 保留 | `EgoCore/app/telegram_bot.py` 参数注释与 warning 文案；`EgoCore/docs/05_DEPRECATED_AND_SHIMS.md` | 成立 |
| 旧 runtime core 仍保留 | `EgoCore/app/runtime/agent_runner.py` 顶部注释 | 成立 |
| `emotiond.memory` 仍通过正式包入口暴露 legacy `MemorySystem` | `OpenEmotion/emotiond/memory/__init__.py` “For backward compatibility” + import `emotiond.memory_legacy` | 成立 |
| `emotiond.self_model` 仍通过正式包入口暴露 legacy API | `OpenEmotion/emotiond/self_model/__init__.py` “Legacy imports (for backward compatibility)” | 成立 |
| `OpenEmotion/tests/` 曾把 OpenClaw 旧链当默认发现面 | 迁移前 `tests/test_openclaw_skill.py`、`tests/test_openclaw_integration2.py`、`tests/test_final_integration.py` 均位于主 `tests/` | 成立 |
| 本次已将 3 个旧测试迁出默认发现面 | 现路径为 `OpenEmotion/compatibility-only/tests/*_compat.py`；`find OpenEmotion/tests -maxdepth 1 ...` 返回空 | 成立 |
| 本次已删除 2 个 `*.bak` 与 1 个旧安装脚本 | 文件已不存在；仓内文本扫描只剩 archive/quarantine 历史记录 | 成立 |
| 主验证面不再把 `openclaw_skill` 视为正式必备结构 | `OpenEmotion/tests/test_project_structure.py` 与 `test_documentation.py` 已去除强制要求 | 成立 |
| `emotiond.memory` formal surface 已去除 legacy 导出 | AST 检查 `OpenEmotion/emotiond/memory/__init__.py` 的 `__all__` 不含 `MemorySystem` 等符号 | 成立 |
| `emotiond.self_model` formal surface 已去除 legacy 导出 | AST 检查 `OpenEmotion/emotiond/self_model/__init__.py` 的 `__all__` 不含 `SelfModelV0` 等符号 | 成立 |
| remaining callers 已改为显式 legacy import | `rg -n` 回扫后仅剩 `OpenEmotion/emotiond/core.py.bak` 命中旧 import 模式 | 成立 |
| 语法未被本次编辑破坏 | `python3 -m py_compile ...` 对本次修改文件通过 | 成立 |
| 无法做 pytest 回归 | 当前 shell 环境 `python3 -m pytest ...` 返回 `No module named pytest` | 阻塞 |
| 无法做完整 import smoke | 直接 import `emotiond.memory` 触发 `ModuleNotFoundError: aiosqlite` | 阻塞 |

## 关键命令摘录

| command | output summary |
|---|---|
| `rg -l 'sys.path|PYTHONPATH|site.addsitedir' ...` | 统计出 `EgoCore` 仍有 `18/9/15`，`OpenEmotion` 仍有 `30/59/94` 个 path-hack 文件 |
| `find OpenEmotion/tests -maxdepth 1 -type f ...` | 现在不再有 `test_*openclaw*`、`test_final_integration.py`、`*.bak` |
| `python3 -m py_compile ...` | PASS |
| `python3 -m pytest ...` | BLOCKED: `No module named pytest` |
| `python3 - <<'PY' ... ast ...` | PASS，证明 `__all__` 已不含 legacy symbols |
| `cd OpenEmotion && python3 - <<'PY' import emotiond.memory ...` | BLOCKED: `aiosqlite` 缺失 |
