# Provider / Runtime OpenEmotion E2E Gate

## Goal

把 “provider / runtime 主链改动必须一路通测到 OpenEmotion artifacts 与 follow-up continuity” 固定成 repo-level 强制验收门，避免再出现“局部 smoke 通过，但 Telegram 主链、native loop、OpenEmotion evidence、后续追问 continuity 仍断裂”的伪完成。

## Non-goals

- 不在本轮修改 `EgoCore/`、`OpenEmotion/`、`scripts/` 或任何运行时代码
- 不在本轮重构现有 `verify_repo.py`
- 不把这条 gate 升成新的 `WP`
- 不回写历史 live 样本或 dashboard 结论

## Problem baseline to freeze

当前任务要冻结的事实来自 2026-04-06 之前的 live provider/runtime 切换事故：

- 当时只证明了 `chat` 路径可用，没有把 `execution / decision / native_loop / OpenEmotion evidence` 一起验完
- 结果是 live Telegram 出现：
  - `chat` 正常
  - task / decision 仍落到旧 provider
  - 后续 `429` 与 continuity 断层污染了 live evidence
- 已确认的根因包括：
  - `chat` 与 `execution` use-case provider split
  - `native_loop` 存在旧 provider/model 硬编码默认值
- 这说明 provider/runtime 级改动的最低正确验收不是 “LLM pong smoke 通过”，而是：
  - Telegram fresh entry
  - runtime_v2 chat / decision
  - native tool-calling
  - OpenEmotion ingress / result / trace
  - follow-up continuity
  - artifacts / dashboard consistency

## Required invariant

任何会影响 live mainline 的 provider/runtime 改动，在对外宣称“已切换 / 已完成 / 已生效”之前，必须同时满足：

1. `config_consistent`
   - `default` 与各 use-case provider/model 不再无意 split
   - 不存在旧 provider/model 硬编码绕过配置
2. `chat_smoke_pass`
   - 当前正式聊天 use-case 能真实返回
3. `execution_tool_call_pass`
   - 当前正式 execution / native loop 能真实产出工具调用
4. `telegram_task_flow_pass`
   - fresh Telegram 会话里最小任务链路可跑通
5. `openemotion_evidence_pass`
   - fresh 样本存在 `openemotion_result.json`、`openemotion_trace.json`、`response_plan.json`
6. `followup_continuity_pass`
   - 同 session 后续追问能绑定最近任务/结果，不从零开始
7. `artifact_consistency_pass`
   - evidence / dashboard / current report 不出现 provider split 造成的伪象

缺任何一项，都只能报：

- `局部接线完成`
- `条件性完成`
- `blocked`

不得报：

- `切换完成`
- `live 已恢复`
- `主链已稳定`

## Acceptance criteria

- [ ] `docs/codex/tasks/provider-runtime-openemotion-e2e-gate/` 已完整落地
- [ ] `SPEC.md / PLAN.md / IMPLEMENT.md / STATUS.md` 明确把 provider/runtime 改动定义为 **必须通测到 OpenEmotion evidence** 的强制 gate
- [ ] 文档已冻结 7 个强制验收条件：
  - `config_consistent`
  - `chat_smoke_pass`
  - `execution_tool_call_pass`
  - `telegram_task_flow_pass`
  - `openemotion_evidence_pass`
  - `followup_continuity_pass`
  - `artifact_consistency_pass`
- [ ] 文档已明确写出 current negative baseline：
  - 只测 chat 不够
  - provider split 会污染 live evidence
  - old hardcoded provider defaults 属于 blocker
- [ ] 文档已锁定 claim ceiling：
  - 没通过 7 项 gate 前，只能报局部完成/条件性完成

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `README.md`
- `EgoCore/README.md`
- `docs/codex/tasks/live-chat-subjective-variability/STATUS.md`
- `docs/codex/tasks/mandatory-subject-ingress-all-turns/STATUS.md`
