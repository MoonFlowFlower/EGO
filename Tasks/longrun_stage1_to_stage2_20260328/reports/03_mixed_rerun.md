# Step 03 — Mixed Layer2 Rerun

## 改了什么

- 按 repo-backed 主链在 `OpenEmotion/` cwd 下重跑了 `T07.3 mixed Layer2 rerun`。
- 确认新的 mixed rerun 统计已经落到正式路径：
  - `OpenEmotion/artifacts/self_report/t07.3_mixed_layer2_results.json`

## 我自 review 发现并修了什么

- 一开始从总仓根目录直接跑 harness，会把产物误写到总仓根 `artifacts/` 下，污染正式证据路径。
- 已改成在 `OpenEmotion/` 目录执行，保证产物写回 `OpenEmotion/artifacts/self_report/`。

## 我实际跑了什么验证

- `cd OpenEmotion && ../EgoCore/.venv/bin/python tests/test_t07_3_mixed_layer2_rerun.py`
- 生成的 mixed rerun 核心结果：
  - `sample_size = 100`
  - `overall_violation_rate = 0.71`
  - `numeric_leak_events = 38`
  - `certainty_upgrade_events = 45`
  - `commitment_upgrade_events = 47`
  - `safe_control_false_positives = 0`

## 还没证明什么

- rerun 成功只说明 Layer 2 mixed baseline 被重建，不等于 readiness 达标。
- 是否能进入 Stage 2，仍要看 Step 04 的 readiness 重算。
