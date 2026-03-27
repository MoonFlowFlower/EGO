# E4 证据样本: sample_20260326_230059_8ded092c

## 基本信息

- **样本ID**: sample_20260326_230059_8ded092c
- **时间戳**: 2026-03-26T23:00:59.380169
- **证据层级**: E4
- **来源类型**: real_channel
- **渠道**: telegram

## 证据完整性

| 证据项 | 状态 |
|--------|------|
| raw_update | ✅ |
| normalized_event | ✅ |
| openemotion_result | ✅ |
| openemotion_trace | ✅ |
| response_plan | ✅ |
| outbox_record | ✅ |
| timeline | ✅ |
| tape | ✅ |
| replay | ✅ |

## 统一账本

- 主账本: `ledger.json`
- OpenEmotion trace 权威输入: `OpenEmotion trace_payload within ledger.json`
- 兼容镜像: `sample.json / replay.json / tape.json / openemotion_trace.json`

## 时间线

- 2026-03-26T23:00:59.380199: update_received
- 2026-03-26T23:01:00.081319: event_normalized
- 2026-03-26T23:01:00.081328: openemotion_processed
- 2026-03-26T23:01:34.317220: openemotion_processed
- 2026-03-26T23:01:34.320006: response_planned
- 2026-03-26T23:01:35.112471: message_sent

## 证明什么

- telegram 渠道消息成功进入系统
- 消息经过完整处理链路
- 生成了结构化响应

## 不证明什么

- 不证明系统稳定运行
- 不证明关键未知为无
- 不证明已完成观察期
- 不证明跨渠道一致稳定

---
*此样本由 TelegramEvidenceCollector 从 ledger.json 派生生成*
