# E4 证据样本: sample_20260325_191135_c1c322e4

## 基本信息

- **样本ID**: sample_20260325_191135_c1c322e4
- **时间戳**: 2026-03-25T19:11:35.100323
- **证据层级**: E3
- **来源类型**: integration
- **渠道**: telegram

## 证据完整性

| 证据项 | 状态 |
|--------|------|
| raw_update | ✅ |
| normalized_event | ✅ |
| openemotion_result | ✅ |
| response_plan | ✅ |
| outbox_record | ✅ |
| timeline | ✅ |
| tape | ✅ |
| replay | ✅ |

## 时间线

- 2026-03-25T19:11:35.100358: update_received
- 2026-03-25T19:11:35.108618: event_normalized
- 2026-03-25T19:11:35.108629: openemotion_processed
- 2026-03-25T19:11:40.435045: response_planned
- 2026-03-25T19:11:40.435072: message_sent

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
*此样本由 TelegramEvidenceCollector 自动生成*
