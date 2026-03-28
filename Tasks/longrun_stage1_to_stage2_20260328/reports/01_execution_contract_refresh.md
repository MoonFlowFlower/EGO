# Step 01 — Execution Contract Refresh

## 改了什么

- 把 `OpenEmotion/tasks/MVP11_5/T07_shadow_rerun_readiness.yaml` 中的过期执行命令降级为历史信息。
- 为本批次锁定了新的 repo-backed 执行契约：
  - `./EgoCore/.venv/bin/python -m pytest -s -q OpenEmotion/tests/test_response_intent_checker.py`
  - `cd OpenEmotion && ../EgoCore/.venv/bin/python tests/test_t07_3_mixed_layer2_rerun.py`
  - `./EgoCore/.venv/bin/python -m pytest -s -q OpenEmotion/tests/testbot/test_intent_alignment_e2e.py`
- 写入了机器可读契约：
  - `steps/STAGE2_01_mvp11_5_execution_contract.json`

## 我自 review 发现并修了什么

- 明确把“旧 T07 命令过期”写成显式 deprecation，而不是隐式忽略。
- 把 readiness 输入文件和允许修复的 blocker 范围一起锁死，避免后面 repair loop 越界到 Stage 3+。
- 独立 reviewer 指出我最初残留了一条已证伪的 `pytest -q tests/test_t07_3_mixed_layer2_rerun.py` 口径；已经回收为脚本直跑版本。

## 我实际跑了什么验证

- 复核以下真实路径存在：
  - `OpenEmotion/tests/test_response_intent_checker.py`
  - `OpenEmotion/tests/test_t07_3_mixed_layer2_rerun.py`
  - `OpenEmotion/tests/testbot/test_intent_alignment_e2e.py`
  - `OpenEmotion/artifacts/self_report/t07.3_mixed_layer2_results.json`
  - `OpenEmotion/artifacts/self_report/MVP11_5_shadow_readiness.md`
  - `OpenEmotion/artifacts/roadmap/evidence/MVP11_5_T07.3.md`

## 还没证明什么

- 还没证明这些测试在当前环境里都能成功执行。
- 还没证明 mixed rerun 的最新结果已经满足 readiness criteria；这要在 Step 02-04 才能判断。
