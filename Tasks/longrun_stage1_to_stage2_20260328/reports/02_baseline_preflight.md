# Step 02 — Baseline Preflight

## 改了什么

- 把 baseline 可执行环境从“默认 WSL pytest”收口到 `EgoCore/.venv`。
- 把 `pytest` 调用口径固定为 `-s`，避免当前环境里的 capture-layer `FileNotFoundError`。
- 把 `T07.3` harness 的运行口径改成“在 `OpenEmotion/` cwd 下直接用 Python 跑脚本”。

## 我自 review 发现并修了什么

- 一开始用默认 `pytest -q` 跑，发现当前环境会在 capture cleanup 时炸 `FileNotFoundError`。
- 继续自查后发现真正可用的环境是 `EgoCore/.venv`，但还缺 `pytest-asyncio`；已通过 `python -m pip install -e './OpenEmotion[dev]'` 把 OpenEmotion 的测试依赖接入现有 venv。
- 我还修正了执行契约里把 `test_t07_3_mixed_layer2_rerun.py` 当成普通 pytest file 的错误。

## 我实际跑了什么验证

- `./EgoCore/.venv/bin/python -m pytest -s -q OpenEmotion/tests/test_response_intent_checker.py`
  - `47 passed`
- `./EgoCore/.venv/bin/python -m pytest -s -q OpenEmotion/tests/testbot/test_intent_alignment_e2e.py`
  - `16 passed`
- `cd OpenEmotion && ../EgoCore/.venv/bin/python tests/test_t07_3_mixed_layer2_rerun.py`
  - 可执行，能生成 mixed rerun artifact

## 还没证明什么

- baseline 可运行不等于 readiness 已达标。
- `T07.3` rerun 的统计是否达到 Stage 2 readiness，还要在 Step 03-04 才能正式判。
