# OpenEmotion Live Integration Fixture Stabilization

## Goal

只修 `OpenEmotion/tests/test_live_integration_fixture.py` 的 live fixture 失败面，重点收口 Windows 下解释器路径解析错误、health timeout 预算失真、以及 port-conflict 测试契约与真实 host 绑定不一致的问题。

## Non-goals

- 不处理 `tests/test_outcome_capture_integration.py`
- 不处理 token、文档、self-report、shadow mode 等其他 OpenEmotion 失败面
- 不顺手重构 emotiond API、daemon 架构或 live fixture 总体测试策略

## Constraints

- 边界约束：只动 `test_live_integration_fixture.py` 及其直接契约；默认不改业务主逻辑
- 仓库/子仓约束：不引入新依赖，不创建新的测试框架
- 环境约束：以当前 Windows Python + `OpenEmotion/.venv/Scripts/python.exe` 为主验证口径
- 发布约束：先过目标测试，再过 `python3 scripts/codex/verify_repo.py --mode fast`，必要时用 `--mode full` 证明失败面已离开仓库级 summary

## Acceptance criteria

- [x] `OpenEmotion/tests/test_live_integration_fixture.py` 全量通过
- [x] live fixture 不再因 `venv/bin/python` 路径探测在 Windows 上抛 `WinError 1920`
- [x] `wait_for_health(timeout=1, interval=0.1)` 在 no-server case 下仍能产生多次尝试
- [x] port-conflict 测试使用与被测服务同 host 的真实冲突条件

## Known risks / dependencies

- 风险：如果把 timeout 压得过低，可能误报慢启动；因此只收缩 live fixture 内的 health probe 单次 timeout，不改服务主逻辑
- 依赖：`OpenEmotion/tests/test_live_integration_fixture.py`、`requests`、`uvicorn`、repo-local OpenEmotion runtime
- 外部 blocker：无

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `OpenEmotion/tests/test_live_integration_fixture.py`
- `OpenEmotion/emotiond/api.py`
- `scripts/codex/verify_repo.py`
