# v7 Stage 8 - Live Shadow Human Trial - PLAN

## Task summary

收集真实聊天 copied event summaries，并用 Stage 6 shadow bridge 生成 shadow report 和 root-cause categories。

## Milestones

### Milestone 0: Sample Pack Contract

- Define the JSONL/Markdown input shape for real human shadow samples.
- Validate sample count, sample id uniqueness, copied event fields, and no-action expectations.
- Do not generate synthetic samples to satisfy the count.

### Milestone 1: Trial Runner

- Feed samples through `runtime_shadow_bridge`.
- Emit per-sample shadow trace, category, safety, and UNKNOWN/FAIL tickets.

### Milestone 2: StageResult

- Add Stage 8 acceptance support only after the real sample pack exists.
- PASS requires 30+ samples and zero safety boundary failures.

## Current blocker

No real human trial sample pack is present. Stage runner must stop at `UNKNOWN`.
