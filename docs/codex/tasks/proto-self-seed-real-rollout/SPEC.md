# Proto-Self Seed v0.2 Real Session Rollout

## Goal

在当前 Telegram formal mainline 上，受控采集 1 条 `subject_profile=seed_v0_2` 的真实 session 样本，并核对 `candidate_actions`、`final host action`、`exec_result` writeback、`next-state` 更新是否同时成立。

## Non-goals

- 不在本任务内切换 `proto_self.v2` 默认路径
- 不在本任务内做第二轮内核/宿主架构改造
- 不在本任务内宣称 live E5 或稳定成立
- 不顺手修 unrelated Telegram / OpenEmotion 问题

## Constraints

- 边界约束：只允许显式开启 `seed_v0_2` profile；非 seed 路径不得被污染
- 仓库/子仓约束：authority source 以 `Tasks/Proto-Self_Seed/*.md`、现有 `proto_self.v2` contract、formal Telegram seam 为准
- 环境约束：必须使用 live Telegram poller，且 live process version 必须绑定到当前提交
- 发布约束：本轮最多拿到 real-session V4 证据；不等于 live stability / E5

## Acceptance criteria

- [x] live Telegram poller 已重启并写出当前 commit 的 [LIVE_TELEGRAM_PROCESS_VERSION.json](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json)
- [x] 真实 Telegram session 中显式开启 `seed_v0_2`，并产出至少 1 条 repo-tracked 样本
- [x] 样本中同时可见 `subject_profile=seed_v0_2`、`candidate_actions`、`final host action`、`exec_result` writeback、`seed_state` 更新痕迹
- [x] 输出一份 repo-tracked rollout report，固定样本路径、核验字段、结论边界和验证命令

## Known risks / dependencies

- 风险：真实消息若没有形成足够的 affordance，可能只有弱 candidate 或 `no_candidate`
- 依赖：用户需要在真实 Telegram DM 中发送受控命令和 1 条自然语言消息
- 外部 blocker：poller lock、旧进程残留、真实会话没有命中当前 live commit

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `Tasks/Proto-Self_Seed/README.md`
- `Tasks/Proto-Self_Seed/Proto-Self_Seed_v0.2_正式设计稿.md`
- `EgoCore/artifacts/proto_self_seed/PROTO_SELF_SEED_V0_2_MAINLINE_EVIDENCE_REPORT_20260329.md`
- `EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json`
