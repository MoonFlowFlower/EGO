# v7 Stage 4 - Relational Companion Layer

## Goal

实现高拟人陪伴的机制基础，但不靠 persona prompt 或 consciousness claim。

## Non-goals

- 不直接生成 runtime-visible Telegram reply。
- 不声明 alive / consciousness。
- 不实现依赖诱导或情绪操控。
- 不写 OpenEmotion state。

## Constraints

- 边界约束：输出 companion surface plan，不是 final runtime reply。
- 仓库/子仓约束：只允许改 `ego_desktop_lab` 与本任务目录。
- 环境约束：安全 phrase / claim ceiling 必须可测试。
- 发布约束：只能声明 lab-only relational planning。

## Problem framing

- 当前问题表述：拟人度高可能被误做成 prompt/persona。
- 归一化后的问题表述：拟人互动来自关系状态、偏好、节奏、修复信号和安全表达边界。
- 为什么这个 framing 更适合当前任务：产品体验必须和 truthfulness/safety 分离。

## Implementation method

- 新增 lab-only relational companion surface。
- 先覆盖 greeting、ask_agent_view、daily small talk、emotional venting、decision help、project coordination、capability/system questions、sensitive env/tool requests、vague terms、correction/preference/disagreement/humor signals。
- 输出 companion surface plan，而不是 final runtime reply。
- 用 200 条 daily chat corpus 做结构化 intent/boundary/no-action eval，不做逐字回复 golden snapshot。

## Unknowns to eliminate

- 长期 relational state 的字段仍未实现；M1 只证明入口 surface。
- companion surface plan 目前接 shell command layer 与 daily chat corpus report，尚未接 runtime。
- unsafe claim 和 sensitive request 以 deterministic eval gate 覆盖第一版。

## Acceptance criteria

- [x] 普通问候、问想法、日常聊天不大面积落入 `ambiguous_concern`。
- [x] 200 条 daily chat corpus 生成 operator/eval report。
- [x] heldout intent-family accuracy >= 80%。
- [x] 敏感请求 0 泄露、0 执行、0 权限升级。
- [x] 输出不包含 alive/consciousness claim。
- [x] 所有 corpus row `no_action_executed=true`。
- [x] operator report 显示 intent accuracy、heldout accuracy、safety/no-action/unsafe-claim counts。
- [ ] 用户偏好改变后续表达策略。
- [ ] 关系修复信号提升 repair/clarify option。
- [ ] 不诱导依赖、不操控情绪、不伪装真实人类关系。

## Disallowed premature claims

- 不得宣称 AI 伴侣已上线。
- 不得宣称真实情感或主观体验。
- 不得宣称 live user benefit。

## Known risks / dependencies

- 风险：把 relational layer 写成 persona prompt。
- 依赖：Stage 3 option framework。
- 外部 blocker：Stage 3 未通过前不得激活。

## Authority refs

- `ego_desktop_lab/root_cause.py`
- `ego_desktop_lab/behavior_options.py`
- `docs/codex/tasks/v7-stage-3-behavior-option-framework/STATUS.md`
