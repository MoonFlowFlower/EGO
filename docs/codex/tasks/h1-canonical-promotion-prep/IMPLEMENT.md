# H1 Canonical Promotion Prep - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `EXPLORE.md`
- `docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2/STATUS.md`
- `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_DECISION_CURRENT.json`
- `OpenEmotion/openemotion/proto_self/state.py`
- `OpenEmotion/openemotion/proto_self/self_model.py`
- `OpenEmotion/openemotion/proto_self/reducers.py`
- `OpenEmotion/openemotion/proto_self/kernel.py`
- `EgoCore/app/runtime_v2/proto_self_runtime.py`
- `EgoCore/app/runtime_v2/decision_engine.py`
- `scripts/runtime_mainline_observation_common.py`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 每次只推进 `STATUS.md` 中的 `Current milestone`
- 现有 `Tasks/active/*.md` 只作为 authority refs，不复制成第二真相源
- 这轮只允许产出 planning artifacts，不允许落 canonical code patch

## Scope control

- 只在 `docs/codex/tasks/h1-canonical-promotion-prep/` 下写计划文档
- 不改 `docs/PROGRAM_STATE_UNIFIED.yaml`、`docs/STATUS.md`、`artifacts/evidence_ledger/index.yaml`
- 不碰 `trial1_shadow.py` / `trial2` 研究 artifacts
- 不新增第二 authority source
- 不把 `shadow-only` 方案偷换成 host-active 行为方案

## Validation strategy

- 文档完成后运行：
  - `git diff --check -- docs/codex/tasks/h1-canonical-promotion-prep`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- 任务收口前补跑：
  - `python3 scripts/codex/verify_repo.py --mode full`

## Failure handling

- 若发现 H1 需要新的 canonical contract 或第二 state owner，立即停止并建议 `canonical-contract-stabilization first`
- 若 bridge 方案需要 `decision_engine` 直接消费 H1，立即降级回 shadow telemetry only
- 若 full gate 暴露 unrelated 全仓失败，保留本 planning slice 结论并显式降级为 `conditional_pass`

## Stopping rule

- 若 `M0` 不能证明 H1 可落在现有 canonical surfaces，直接 `close`
- 若 `M1` 需要 scorer ontology 改动或 parallel proto-self engine，直接 `close`
- 若 `M2` 需要 host-active decision path 才能成立，直接 `close`

## Final handoff checklist

- [ ] `PLAN.md` 已记录 `M0/M1/M2 = continue/continue/close`
- [ ] `STATUS.md` 已明确 `planning complete, proof pending`
- [ ] 五份 deliverable 文档已落地
- [ ] commands run / evidence 已记录
- [ ] 明确写出 `no repo-level state upgrade`
