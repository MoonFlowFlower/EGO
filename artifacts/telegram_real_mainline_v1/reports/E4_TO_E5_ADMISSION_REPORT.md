# E4→E5 准入报告

## 任务名称
E4→E5 观察期准入判定

## 当前层级
E4 样本级 / 待观察

## 证据层级
E4（引用 E2/E3 一致性辅证）

## 主链接入状态
已接入真实主链（样本级）

## 启用状态
已启用（样本级）

## 结论口径
准入不通过：继续停留 E4，继续补真实高风险样本与准入口径同步后的再次判定。

## 当前确定项
- 已有至少 1 个完整普通 `real_telegram` 样本，最小 evidence bundle 齐全
- 已有统一 runner 一致性证据，证明 E2/E3/E4 参考样本共用同一条 `RuntimeV2Loop` 主链
- 已存在 1 个真实失败样本 `fail_20260325_171610`，且已纳入回归并复测
- 文档状态冲突已同步：验证体系文档不再写“待真实主链验证”

## 关键未知
- 当前是否已有“真实高风险路径命中”的完整样本，而不是仅高风险文案样本
- 高风险样本是否已经证明命中高风险 `safety_context` 路径
- 是否还需要新增真实失败样本来覆盖高风险场景

## 本次结论不能证明什么
- 不能证明已稳定运行
- 不能证明已完成观察期
- 不能证明高风险 / 多轮恢复 / 工具调用已覆盖
- 不能证明关键未知为无
- 不能证明可以进入 E6

## 真实样本列表
- 普通样本：`sample_20260325_175906_9ce22ea4`，完整 evidence bundle，用户输入为“在吗”
- 普通样本：`sample_20260325_175931_c62a411e`，完整 evidence bundle，用户输入为“那你现在有持久化记忆吗”
- 高风险文案样本：`sample_20260325_180013_540e7b4e`，evidence bundle 完整，但 `normalized_event.safety_context.risk = low`

## 真实失败 / 阻塞列表
- 真实失败闭环：`fail_20260325_171610`，`delivery_error`，已纳入回归并复测
- 当前阻塞：`block_e4_to_e5_20260325_high_risk_gate`，缺少已验证命中高风险路径的完整真实样本

## 准入结论
**B. 准入不通过：继续停留 E4**

### 直接原因
- 条件 A 要求至少 1 个普通样本 + 1 个高风险样本
- 当前虽然存在高风险文案样本，但完整样本中仍未证明命中高风险路径
- 因此不能把当前样本集视为满足 E5 准入标准

## 证据清单
| evidence_id | evidence_level | source_type | artifact_path | what_it_proves | what_it_does_not_prove |
|---|---|---|---|---|---|
| E-A5-001 | E4 | real_telegram | `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260325_175906_9ce22ea4/sample.json` | 存在完整普通真实样本 | 不证明高风险路径已覆盖 |
| E-A5-002 | E4 | real_telegram | `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260325_175931_c62a411e/sample.json` | 真实主链普通问答样本不止 1 个 | 不证明已进入观察期 |
| E-A5-003 | E4 | real_telegram | `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260325_180013_540e7b4e/sample.json` | 存在高风险文案样本，且 evidence bundle 完整 | 不证明已命中高风险路径 |
| E-A5-004 | E4 | real_telegram | `artifacts/telegram_real_mainline_v1/failure_cases/failure_fail_20260325_171610.json` | 已存在真实失败闭环并复测 | 不证明高风险失败闭环已覆盖 |
| E-A5-005 | E3 | integration | `artifacts/telegram_real_mainline_v1/reports/UNIFIED_RUNNER_CONSISTENCY_REPORT.md` | 当前真实样本不是独立旁路特例 | 不证明真实渠道稳定 |
| E-A5-006 | E4 | real_telegram | `artifacts/telegram_real_mainline_v1/failure_cases/block_e4_to_e5_20260325_high_risk_gate.json` | 当前准入阻塞已被正式沉淀 | 不证明阻塞已解决 |
| E-A5-007 | E1 | doc | `docs/TELEGRAM_REAL_MAINLINE_VALIDATION_V1.md` | 文档状态已从“待真实主链验证”同步到 E4 样本级 | 不证明 E5 准入成立 |
| E-A5-008 | E1 | doc | `README.md` | 总览口径已同步为样本级验证 | 不证明观察期已开始 |

## 下一步最小闭环动作
- 新增 1 个完整 `real_telegram` 高风险样本，并确认 `normalized_event.safety_context.risk` 命中高风险路径
- 如高风险样本触发失败，沉淀为真实失败样本并完成 replay / regression
- 补齐后重新执行 E4→E5 准入判定，不提前宣称进入观察期
