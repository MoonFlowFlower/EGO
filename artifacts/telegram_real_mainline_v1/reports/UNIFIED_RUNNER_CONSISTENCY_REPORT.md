# 统一 runner 跨层一致性验证报告

## 任务名称
统一 runner 跨层一致性验证

## 当前层级
统一主链一致性验证层

## 证据层级
E3 主体结论，参考 E4 样本

## 主链接入状态
E2 / E3 已接入统一 `RuntimeV2Loop` 主链  
E4 参考样本已提供真实渠道对照证据

## 启用状态
E2 / E3 已在 unified runner 下实际执行  
E4 为已存在真实样本参考，不代表新增真实采集

## 结论口径
一致性成立：`simulated / integration / real_telegram` 共用同一条 `RuntimeV2Loop` 主链；差异仅存在于输入 source、输出 transport、evidence source。

## 当前确定项
- E2 通过 `cmd.exe /c py -3 scripts\run_telegram_simulated_smoke.py --quick` 实跑成功
- E3 通过 `cmd.exe /c py -3 scripts\run_telegram_integration_e2e.py --quick` 实跑成功
- E2/E3 样本均生成统一 evidence bundle：`raw_update / normalized_event / openemotion_result / response_plan / outbox_record / timeline / tape / replay`
- E2/E3 的 `normalized_event`、`response_plan`、`timeline` 阶段命名与 E4 参考样本一致
- 主链入口均落在 `RuntimeV2Loop.run_turn_typed(..., source=..., evidence_collector=...)`

## 关键未知
- 尚未新增本轮 E4 真实样本，因此不能证明真实渠道新增样本也完全遵循同一 metadata schema
- E4 参考样本生成于旧 collector 时期，`sample.json` 的 `source_type` 仍为 `real_telegram`，属于历史元数据差异
- 尚未覆盖高风险、多轮恢复、工具调用等更复杂场景

## 本次结论不能证明什么
- 不能证明真实 Telegram 已稳定运行
- 不能证明 E4 已新增完整成功样本
- 不能证明已进入观察期
- 不能证明关键未知为无
- 不能证明统一主链长期可靠

## E2 结果
- 运行命令：`cmd.exe /c py -3 scripts\run_telegram_simulated_smoke.py --quick`
- 结果：1/1 通过
- 样本：`sample_20260325_191135_e0bb2802`
- 报告：`artifacts/telegram_real_mainline_v1/simulated/smoke_simulated_20260325_191140.json`

## E3 结果
- 运行命令：`cmd.exe /c py -3 scripts\run_telegram_integration_e2e.py --quick`
- 结果：2/2 通过
- 样本：`sample_20260325_191135_c1c322e4`
- 报告：`artifacts/telegram_real_mainline_v1/integration/report_integration_20260325_191140.json`

## E4 参考结果
- 参考样本：`sample_20260325_180013_540e7b4e`
- 参考报告：`artifacts/telegram_real_mainline_v1/reports/VALIDATION_REPORT_E4_SAMPLE_001.md`
- 参考价值：提供真实渠道的 `raw_update / response_plan / outbox_record / timeline / replay` 对照证据

## 跨层一致性结论
- `runtime entry`：三层统一收敛到 `EgoCore/app/runtime_v2/loop.py` 的 `run_turn_typed`
- `source`：`normalized_event.source` 三层均为 `telegram`，差异只体现在样本 `source_type`
- `response plan 生成位置`：三层均在 `RuntimeV2Loop` 结束阶段捕获 `status / delivery_kind / reply_length`
- `openemotion_result 生成位置`：三层均在 `RuntimeV2Loop` 内通过 `ProtoSelfAdapter.handle_event` 产生
- `timeline / tape / replay`：E2/E3 结构完全一致；E4 文件级结构一致，但旧样本 `sample.json` 未内嵌 `replay` 字段，已通过独立 `replay.json` 补齐
- `输出 transport 差异`：E2/E3 使用 stubbed outbox 记录；E4 使用真实 Telegram 发送记录

## 证据清单
| evidence_id | evidence_level | source_type | artifact_path | what_it_proves | what_it_does_not_prove |
|---|---|---|---|---|---|
| E-URC-001 | E2 | simulated | `artifacts/telegram_real_mainline_v1/simulated/smoke_simulated_20260325_191140.json` | E2 unified runner 已真实执行 | 不证明真实渠道稳定 |
| E-URC-002 | E2 | simulated | `artifacts/telegram_real_mainline_v1/simulated/sample_20260325_191135_e0bb2802/sample.json` | E2 形成统一 evidence bundle | 不证明 E4 新样本成立 |
| E-URC-003 | E3 | integration | `artifacts/telegram_real_mainline_v1/integration/report_integration_20260325_191140.json` | E3 unified runner 已真实执行 | 不证明真实 Telegram 主链稳定 |
| E-URC-004 | E3 | integration | `artifacts/telegram_real_mainline_v1/integration/sample_20260325_191135_c1c322e4/sample.json` | E3 与 E2 共享相同主链产物结构 | 不证明没有复杂场景分叉 |
| E-URC-005 | E4 | real_channel | `artifacts/telegram_real_mainline_v1/reports/VALIDATION_REPORT_E4_SAMPLE_001.md` | E4 存在真实渠道参考证据 | 不证明本轮新增 E4 样本 |
| E-URC-006 | E4 | real_channel | `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260325_180013_540e7b4e/replay.json` | E4 文件级 replay artifact 可与 E2/E3 对照 | 不证明旧样本 metadata 全量升级 |
| E-URC-007 | E1 | integration | `EgoCore/app/runtime_v2/loop.py` | 三层入口确实指向同一 runtime 主链 | 不证明运行时效果，需结合 E2/E3 实跑 |
| E-URC-008 | E1 | integration | `scripts/telegram_mainline_common.py` | 三层 runner 共享同一 transport-neutral runner helper | 不证明真实 Telegram 发送稳定 |

## 下一步最小闭环动作
- 使用同一 unified runner 再新增 1 组真实 E4 样本，确认新样本 metadata 与 E2/E3 完全对齐
- 针对高风险输入和多轮输入各补 1 组 E2/E3/E4 对照样本
- 在新增真实样本前，不把本轮结论升级为稳定事实
