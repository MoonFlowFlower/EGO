# Proto-Self Seed Host Evidence Stabilization - PLAN

## Task summary

- task type: bugfix
- current layer: host bridge / evidence / delivery
- change classification: root-cause fix

## Milestones

### Milestone 1

- scope:
  - collector 保留 OpenEmotion event payload
  - step progress 对工具名改成非机械文案
  - follow-up 文件阅读意图绑定到 `last_explicit_target`
- files / areas likely touched:
  - `EgoCore/app/telegram_evidence_collector.py`
  - `EgoCore/app/runtime_v2/progress_events.py`
  - `EgoCore/app/runtime_v2/semantic_parser.py`
  - `EgoCore/app/telegram_runtime_bridge.py`
  - 相关 EgoCore tests
- acceptance:
  - 3 个目标行为都能被 repo-local 测试证明
- validation:
  - targeted pytest
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 关闭本次 patch 即回到当前显式 seed rollout 前的 host 行为

## Progress

- completed

## Decision log

- follow-up 绑定优先复用 `last_explicit_target`，不引入第二套会话记忆
- 机械 progress 只消掉工具名占位，不移除全部 progress 机制

## Surprises / discoveries

- `openemotion.events` 之前只存 metadata，不存 payload，本身就是证据丢失点

## Outcomes / retrospective

- collector 现在会把 OpenEmotion event payload 一并入账，finalized sample 可回看 ingress candidate
- 文件工具 progress 不再暴露 `开始执行第 1 步：file。`
- follow-up 文件阅读会复用 `last_explicit_target` 并走 `analyze` 路径
