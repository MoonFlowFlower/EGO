# 2026-03-26 Session Archive

- topic: EgoCore / OpenEmotion 服务启动恢复与 E5 观察期继续执行
- date: 2026-03-26
- repo: `EGO`

## 本次完成

- 确认 OpenEmotion 正式入口仍为：
  - `python -m emotiond.main`
- 确认 EgoCore 正式入口仍为：
  - `python -m app.main --telegram`
  - `EgoCore/scripts/start_egocore.sh --telegram`
- 启动 OpenEmotion：
  - `emotiond` 已在 `127.0.0.1:18080` 提供 `/health`
- 修复 EgoCore 正式入口的两个非业务阻塞：
  - `EgoCore/app/main.py` 缺失 `import sys`
  - `EgoCore/scripts/*.sh` 含 CRLF，导致 WSL 下脚本不可执行
- 在 Windows 规范路径下补齐 editable install：
  - `py -3 -m pip install -e OpenEmotion -e EgoCore`
- 在 Windows 正式路径下确认 EgoCore `--status` 可运行，且 `Proto-Self Kernel: READY`
- 启动 EgoCore Telegram 主链，日志已进入：
  - `Telegram bot is running!`

## 为什么没有更新文档口径

- 启动方式本身没有变化
- 变化的是：
  - 一个入口文件漏导入
  - 一组 shell 脚本的 CRLF 兼容性问题
- 因此不需要改“正式启动方式”文档口径

## 当前运行状态

- OpenEmotion:
  - health: `ok=true`
  - bind: `127.0.0.1:18080`
- EgoCore:
  - `py -3 -m app.main --status` 通过
  - Telegram bot 日志显示已进入运行态

## E5 状态

- E5 仍然只是“已启动观察期”
- 本次没有新增 2026-03-26 起的新真实样本
- 因此不能报：
  - `E5 已完成`
  - `稳定运行`
  - `稳态收口`

## 下一步

- 只继续采集 2026-03-26 起的新真实 Telegram 主链样本
- 成功样本与失败样本继续入 `artifacts/E5/*`
- 不改架构，不改业务逻辑
