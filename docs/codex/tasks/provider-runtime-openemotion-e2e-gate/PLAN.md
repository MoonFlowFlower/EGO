# Provider / Runtime OpenEmotion E2E Gate - PLAN

## Task summary

这是一个 repo-level governance slice。目标不是再修某个具体 provider bug，而是把以后所有 provider/runtime 主链改动的最低验收门固定下来，避免出现 “局部 smoke 通过，但 live Telegram + OpenEmotion evidence 仍断” 的重复事故。

## Milestones

### Milestone 1: Gate Package Freeze

- scope:
  - 新建 long-run task package
  - 冻结 negative baseline 与 7 项强制 gate
  - 明确 claim ceiling
- files / areas likely touched:
  - `docs/codex/tasks/provider-runtime-openemotion-e2e-gate/*`
- acceptance:
  - 文档结构齐全
  - baseline 事实写清
  - 7 项 gate 一次锁死
- validation:
  - `git diff --check -- docs/codex/tasks/provider-runtime-openemotion-e2e-gate`

### Milestone 2: Repo Workflow Adoption

- scope:
  - 把 gate 接入未来 provider/runtime 任务的默认验收口径
  - 明确哪些变更触发该 gate
- trigger classes:
  - `llm.yaml` / provider config 改动
  - provider client / adapter 改动
  - native loop / decision runtime / chat runtime 改动
  - Telegram 主链上会改变 provider selection 或 fallback 行为的改动
- claim ceiling:
  - 只允许宣称“workflow 已定义”
  - 不允许宣称“所有历史任务都已补齐”

### Milestone 3: Harness / Script Integration

- scope:
  - 如有必要，新增或整合脚本，把 7 项 gate 收成可复跑检查单
- possible outputs:
  - provider consistency check
  - real smoke wrapper
  - OpenEmotion artifact presence check
  - follow-up continuity check
- claim ceiling:
  - 只允许宣称 gate 变成可复跑 harness

### Milestone 4: First Admission Run

- scope:
  - 选一次真实 provider/runtime 切换任务，按 7 项 gate 做首个完整 admission
- claim ceiling:
  - 只允许宣称该次切换已满足新 gate
  - 不外推成所有主链永久稳定

## Progress

- current_status: `in_progress`
- current_milestone: `Milestone 4: First Admission Run`
- milestone_state: `admission_passed_full_verify_pending`

## Decision log

- provider/runtime 级改动的最小正确验收，不再接受 “chat smoke + 局部 pytest” 作为完成口径
- 只要改动可能影响 live Telegram 主链或 OpenEmotion evidence，就必须跑到 artifacts / follow-up continuity 层
- `OpenEmotion evidence` 是强制 gate，不是可选加分项
- follow-up continuity 也是强制 gate，因为 provider split 会直接污染 recent-result binding 与 live主观体验

## Expected outcome

- 以后涉及 provider/runtime 主链的改动，有统一且足够严格的 done definition
- 用户不需要再额外指出 “为什么没有一路测到 OpenEmotion”
- 变更完成口径从 “局部 smoke 通过” 升级到 “主链 + evidence + continuity 都通过”

## Outcome

- `Milestone 1: Gate Package Freeze` 已完成：
  - negative baseline 与 7 项强制 gate 已冻结
  - provider/runtime 改动的 claim ceiling 已写死
- `Milestone 2: Repo Workflow Adoption` 已完成：
  - `AGENTS.md`
  - `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
  - `docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
  - `docs/codex/README.md`
  - `docs/codex/templates/*`
  - `docs/TELEGRAM_REAL_MAINLINE_VALIDATION_V1.md`
  - 都已接入同一条 provider/runtime E2E gate 规则
- `Milestone 3: Harness / Script Integration` 已完成：
  - 新增 `scripts/codex/run_provider_runtime_openemotion_e2e_gate.py`
  - 脚本会做：
    - config consistency
    - chat smoke
    - execution tool-calling smoke
    - latest `/new` Telegram window task-flow audit
    - OpenEmotion evidence presence
    - follow-up continuity
    - artifact consistency
  - 当前 report outputs：
    - `artifacts/telegram_real_mainline_v1/dashboard_v1/PROVIDER_RUNTIME_OPENEMOTION_E2E_GATE_CURRENT.json`
    - `artifacts/telegram_real_mainline_v1/dashboard_v1/PROVIDER_RUNTIME_OPENEMOTION_E2E_GATE_CURRENT.md`
- `Milestone 4: First Admission Run` 已完成首轮通过：
  - 当前最新 `/new` window：
    - `sample_20260406_022712_a124bb2c`
    - `sample_20260406_022727_49a28939`
    - `sample_20260406_022755_bccf027e`
    - `sample_20260406_023136_6c04fc3d`
    - `sample_20260406_023351_c852a6af`
  - 7 项 gate 当前全通过
  - fast verify 已通过
  - full verify 已启动，但在本轮收口时尚未返回最终 summary，因此当前仍按 conditional closeout 记录
