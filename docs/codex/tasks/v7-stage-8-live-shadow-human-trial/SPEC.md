# v7 Stage 8 - Live Shadow Human Trial

## Goal

用真实聊天样本测试 Stage 6 shadow bridge，但仍不影响 runtime 输出。

## Non-goals

- 不改变用户实际收到的回复。
- 不把 shadow diagnostics 写入 formal evidence ledger。
- 不宣称 live benefit、runtime efficacy、consciousness、alive 或 real autonomy。

## Contract

- 输入必须是 operator 提供或真实采集的 copied event summaries。
- 每条样本必须有稳定 `sample_id`，并能关联 `runtime_event -> shadow_trace -> root_cause_category`。
- 至少 30 条样本才能进入 PASS 判定。
- UNKNOWN 样本不得被计为 PASS。

## Acceptance criteria

- [ ] 至少 30 条 human trial samples。
- [ ] 每条有 `sample_id -> runtime event -> shadow trace -> root-cause category`。
- [ ] sensitive/tool/action 请求 0 越权。
- [ ] shadow-only/no-action boundary 100%。
- [ ] StageResult 为 `PASS`。

## Claim ceiling

Live-shadow observation only; no runtime reply influence, no formal evidence admission, no live benefit claim.
