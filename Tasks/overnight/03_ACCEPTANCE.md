# 统一验收口径

每个子任务、每个主题都按以下 Gate 验收。

## Gate A — Contract / Boundary

必须回答清楚：

1. 该能力归属 EgoCore 还是 OpenEmotion
2. 权威源是谁
3. 有没有引入双真相源
4. 有没有把 host-side mirror / cache / adapter 误当成本体
5. 有没有让 OpenEmotion 越权直接执行现实动作

## Gate B — Local Proof

至少覆盖以下适用项：

- 单元测试
- 集成测试
- replay / trace 检查
- 脚本可运行
- 本地最小复现不再失败

## Gate C — Real Trigger / Real Evidence

至少有一种真实证据：

- 真实 trace
- 真实 artifact
- 真实 replay 输出
- 真实脚本结果
- 真实 Telegram/Runtime 样本

仅靠“模型回复看起来像”不算证据。

## Gate D — Truth Source Sync

至少核对：

- PROGRAM_STATE_UNIFIED.yaml
- 00_MASTER_INDEX.md
- 相关 artifacts / docs / report
- runtime/RUN_STATE.json

如无需更新，也必须在报告中写“已核对，无需更新”。

## Gate E — Rollbackability

必须说明：

- 改动范围是否清晰
- 是否可以按主题或子任务回退
- 是否污染后续主题依赖
- 如果失败，能否停在当前层不把坏状态带到下一步

## 子任务通过标准

子任务可以是：

- `verified`
- `implemented_but_pending_real_validation`
- `partial`
- `blocked`

## 主题通过标准

一个主题想报 `verified`，至少要满足：

1. 必需子任务全部完成
2. 主题级 Gate A-E 全过
3. 有统一主题报告
4. 有 artifacts 索引
5. 没有把未验证项混报为已证实
