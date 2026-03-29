# Proto-Self Seed Host Evidence Stabilization - SPEC

## Goal

- 修掉 `seed_v0_2` 真实 rollout 中 3 个 host/evidence 层问题：
  - finalized real sample 要保留 ingress candidate
  - 去掉机械化 `开始执行第 1 步：file。` 进度文案
  - “读取完整内容/不要截断”这类 follow-up 不再落到 `powershell` shell path

## Non-goals

- 不改 Seed kernel 设计
- 不改 Telegram 正式主链 owner
- 不扩大到其他 runtime_v2 planner/执行器重构

## Constraints

- authority source:
  - `Tasks/Proto-Self_Seed/Proto-Self_Seed_v0.2_正式设计稿.md`
  - `docs/codex/tasks/proto-self-seed-real-rollout/*`
  - 当前 Telegram formal mainline / proto_self.v2 seam
- 只做最小 host/evidence patch
- 非 seed 路径行为不能被偷改

## Acceptance criteria

- collector 持久化 `openemotion.events[*].payload`，足以在 finalized sample 中回看 ingress candidate
- 文件工具执行时不再出现 `开始执行第 1 步：file。`
- 对已有显式文件目标发送“继续读取完整内容/不要截断”时，ingress 走 `task_request + analyze + explicit_target`，不是 shell/powershell
- 聚焦测试通过

## Known risks / dependencies

- real rollout 仍需要用户再发一轮 Telegram 消息做最终 E4 采样
- profile memory standing rules 仍可能污染特定路径，不在本 slice 处理
