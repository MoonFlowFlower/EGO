# P1 FAILURE_SAMPLES

## 本轮新增失败样本

| failure_id | type | location | observed_issue | risk_if_ignored | current_disposition |
|---|---|---|---|---|---|
| P1-F-001 | regression_gap | `EgoCore/tests/test_runtime_v2_minimal.py::test_runtime_v2_loop_runs_plan_act_complete` | Windows `pytest` 下返回 `waiting_input`，未得到预期 `completed_verified` | 如果直接忽略，会把“多数回归通过”误报成“全部主链回归通过” | 已记录；本轮不扩展到 P2/Pverify 范围排查 |

## 历史失败样本（与 P1 直接相关的上下文）

| failure_id | evidence_level | source_type | artifact_path | what_it_proves | what_it_does_not_prove |
|---|---|---|---|---|---|
| fail_20260325_162332 | E3 | integration | `artifacts/telegram_real_mainline_v1/failure_cases/failure_fail_20260325_162332.json` | runtime / contract 接缝曾发生失败 | 不证明本轮瘦身已覆盖全部 contract 风险 |
| fail_20260325_162341 | E3 | integration | `artifacts/telegram_real_mainline_v1/failure_cases/failure_fail_20260325_162341.json` | runtime 配置链曾发生失败 | 不证明当前最小回归全部稳定 |

## 本次结论不能证明什么
- 不能证明 runtime 全量回归无破坏
- 不能证明 `test_runtime_v2_minimal` 的失败一定是 P1 引入，也不能证明它与 P1 无关
- 不能证明外部真实链路行为已重新验证
