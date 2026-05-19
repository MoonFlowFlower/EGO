# H1 Canonical Shadow Patch

## Goal

把 Trial-2 的 `H1 counterfactual low-success guard` 翻译成 canonical `proto_self` 的最小 shadow-only telemetry patch，并通过 EgoCore 做只读桥接与 E4 样本采集挂钩。

## Non-goals

- 不把 H1 直接接到 live `ask_preferred` / `ask_needed`
- 不改 scorer ontology
- 不升级 repo-level program state
- 不宣称 runtime efficacy
- 不继续推进 Trial-1 / Trial-2 研究线实现，它们只保留为证据源

## Constraints

- 边界约束：不能新建 parallel proto-self engine；canonical patch 必须落在 `OpenEmotion/openemotion/proto_self/*`
- 仓库/子仓约束：EgoCore 只能做 host-owned flag、telemetry forwarding、observation capture；不能消费 H1 作为 live decision input
- 环境约束：当前任务只做 shadow-only、flag-guarded、rollback-safe slice；如果 shadow isolation 失败，立即降级为 mirror-only trace integration
- 发布约束：本任务不修改 repo-level truth source；交付口径最多是 `conditional complete / shadow telemetry wired`

## Problem framing

- 当前问题表述：把 Trial-2 的 bounded H1 结果“接进 canonical proto-self”
- 归一化后的问题表述：在不扰动 canonical live replay/public behavior 的前提下，把 H1 变成 canonical shadow telemetry，并让 formal runtime mainline 可采样、可回滚、可验证
- 为什么这个 framing 更适合当前任务：它直接对准当前最小闭环需求，避免把研究证据错误升级成主链 efficacy claim

## Unknowns to eliminate

- shadow H1 是否能写进 canonical state surface 而不被 live public derivation误消费
- EgoCore 是否能把 H1 telemetry forward 到 `proto_self_context` 与 observation artifact，而不进入 prompt / delivery path
- feature flag off/on 是否能保持 rollback-safe 与 replay-safe

## Acceptance criteria

- [ ] canonical `proto_self` 能在 flag on 时产出 `shadow_h1` telemetry，并在 flag off 时完全不产出
- [ ] `shadow_h1` 不直接改变 live `policy_hint.ask_preferred` / `response_tendency.ask_needed`
- [ ] EgoCore 能只读桥接 `shadow_h1` 到 `state.proto_self_context`
- [ ] observation hook 能记录 `proto_self_shadow_h1`，且不改 observation scorer ontology
- [ ] slice-local tests、replay checks、`git diff --check`、`python3 scripts/codex/verify_repo.py --mode fast` 通过

## Disallowed premature claims

- 不能宣称 `H1 promoted to live canonical decision path`
- 不能宣称 `runtime efficacy passed`
- 不能宣称 `repo-level state should upgrade`

## Known risks / dependencies

- 风险：canonical reducer 当前直接读取 `counterfactual_success_by_action` / `recent_correction_tags`，必须先隔离 shadow keys
- 依赖：`OpenEmotion/openemotion/proto_self_v2/kernel.py` 默认经由 v1 canonical kernel；`EgoCore/app/runtime_v2/proto_self_runtime.py` 是 host rollout authority
- 外部 blocker：无外部审批依赖；若 shadow isolation 证明不可行，按 stop rule 退回 mirror-only trace integration

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `docs/codex/tasks/h1-canonical-promotion-prep/H1_TO_CANONICAL_MAPPING_SPEC.md`
- `docs/codex/tasks/h1-canonical-promotion-prep/CANONICAL_PATCH_PLAN.md`
- `docs/codex/tasks/h1-canonical-promotion-prep/FEATURE_FLAG_ROLLBACK_PLAN.md`
- `docs/codex/tasks/h1-canonical-promotion-prep/EGOCORE_FRONTEND_BRIDGE_PLAN.md`
- `docs/codex/tasks/h1-canonical-promotion-prep/E4_SAMPLE_COLLECTION_PLAN.md`
