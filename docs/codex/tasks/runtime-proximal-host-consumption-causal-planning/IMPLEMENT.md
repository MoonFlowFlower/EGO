# Runtime-Proximal Host-Consumption Causal Planning - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `docs/PROGRAM_STATE_UNIFIED.yaml`

## Execution rules

- 当前 tranche 只做 planning authorization，不做 runtime code
- 只定义 causal question、scenario bank、compare surface、rollback 条件
- 不升级 live Telegram proof，不新增 runtime public API

## Scope control

- 允许改：
  - task package 文档
  - repo state / progress wording
  - evidence ledger 的 planning artifact 记录
- 不允许改：
  - `EgoCore/` runtime behavior
  - `OpenEmotion/` subject semantics
  - new runner implementation
  - live Telegram acceptance logic
  - canonical host contract 冻结面

## Validation strategy

- docs / state:
  - `python3 scripts/codex/generate_program_state_views.py`
  - `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check`
  - `git diff --check -- <scoped files>`

## Failure handling

- 如果 state wording 仍把 fresh Telegram proof 写成当前 acceptance root：
  - 先回写 authority source
  - 再回写派生视图
- 如果 planning 需要 new scorer / new API：
  - 直接停在 planning phase，不升级实现范围

## Artifact contract

- planning artifact:
  - `docs/codex/tasks/runtime-proximal-host-consumption-causal-planning/SPEC.md`
  - `docs/codex/tasks/runtime-proximal-host-consumption-causal-planning/PLAN.md`
  - `docs/codex/tasks/runtime-proximal-host-consumption-causal-planning/STATUS.md`
- artifact meaning:
  - `source = planning_authorization_only`
  - `claim_ceiling = planning_only`
- artifact must not be consumed by:
  - fresh real Telegram acceptance
  - runtime efficacy claims

## Final handoff checklist

- [ ] causal question 已写清
- [ ] scenario bank compare surface 已写清
- [ ] authority / progress wording 已同步
- [ ] evidence ledger 已同步
- [ ] derived views 已重生成
