# P6 FAILURE_SAMPLES

## sample 1: pytest 环境阻塞

- command: `python3 -m pytest OpenEmotion/tests/test_openclaw_skill.py OpenEmotion/tests/test_openclaw_integration2.py OpenEmotion/tests/test_final_integration.py -q`
- result: `No module named pytest`
- meaning: 本次无法在当前 shell 完成 pytest 回归，只能做静态语法校验与引用证据收口

## sample 2: 旧安装入口仍指向 OpenClaw

- file: `OpenEmotion/scripts/install_openclaw_integration.sh`（已删除）
- failure pattern:
  - 输出 `openclaw hooks enable ...`
  - 写入 `~/.openclaw/openclaw.json`
  - 将 `OpenClaw` 安装流程包装成继续可用的默认接线
- why dangerous: 它会把历史宿主链伪装成当前可用入口

## sample 3: 旧测试曾冒充默认验证面

- old files:
  - `OpenEmotion/tests/test_openclaw_skill.py`
  - `OpenEmotion/tests/test_openclaw_integration2.py`
  - `OpenEmotion/tests/test_final_integration.py`
- failure pattern:
  - 位于主 `tests/` 根下
  - 默认 pytest 会发现
  - 内容直接依赖 `openclaw_skill`、旧 handler、`venv2`
- handling: 本次已迁到 `OpenEmotion/compatibility-only/tests/`

## sample 4: 第二真相源仍挂在正式包表面

- file: `OpenEmotion/emotiond/memory/__init__.py`
- failure pattern: `MemorySystem` 仍从正式 `emotiond.memory` 暴露

- file: `OpenEmotion/emotiond/self_model/__init__.py`
- failure pattern: `SelfModelV0` 及相关 legacy API 仍从正式 `emotiond.self_model` 暴露

- why dangerous: 调用方无需显式写 `legacy` 就能走到旧实现，容易形成“正式 API 仍默认支持旧真相源”的误判

## sample 5: 第二轮验证环境阻塞

- command: `cd OpenEmotion && python3 - <<'PY' import emotiond.memory ... PY`
- result: `ModuleNotFoundError: aiosqlite`
- meaning: 当前环境不足以完成完整 import smoke；因此本轮以 AST + py_compile + 引用关系回扫作为最小证据包
