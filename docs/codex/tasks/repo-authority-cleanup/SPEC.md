# Repo Authority Cleanup

## Goal

在不改变 formal mainline、不新增功能、不重写双核架构的前提下，对 `EgoCore + OpenEmotion` 做一次全仓强制收口：建立真相地图，压平 authority/caller/path 分类，逐波消除 dual-authority 与“冒充主实现”的残留路径，并为后续 archive/delete 提供可证明、可回退的 admission 基线。

## Non-goals

- 不新建第二套 `proto_self / kernel / developmental_core / self_model / drives / reflection`
- 不改变 formal mainline：`native_hooks -> proto_self_runtime -> proto_self_adapter -> proto_self_v2/kernel`
- 不把主体本体逻辑迁回 `EgoCore`
- 不把 `emotiond.developmental_core` 在身份未澄清前当 dead code 删除
- 不在本任务里顺手扩功能、改 runtime 核心语义、或大规模物理搬迁 `docs/` / `artifacts/`

## Constraints

- 边界约束：
  - `EgoCore` 只负责宿主、runtime、任务、工具、安全、治理、adapter、mirror、最终裁决
  - `OpenEmotion` 只负责 identity、self-model、memory、appraisal、reflection、developmental self 本体
  - 任何能力只能有一个 authority；允许 mirror，不允许双主
- 仓库/子仓约束：
  - 当前正式主链与 `proto_self_v2` formal surface 不变
  - 现行 trace / replay / audit / gate 依赖链不可打断
  - 当前单一权威决策基线以 `docs/PROTO_SELF_SINGLE_AUTHORITY_DECISION.md` 为准
- 环境约束：
  - 当前 worktree 很脏，必须保持 diff scoped，只改本任务文件
  - 现有 artifacts/logs 不能按“看起来旧”直接删，必须先完成 caller/evidence 分类
- 发布约束：
  - 每波必须可单独回退
  - 每波都要留下验证结果、决策、风险、next step、rollback notes

## Acceptance criteria

- [ ] `docs/codex/tasks/repo-authority-cleanup/` 已建立，并存在 `SPEC/PLAN/IMPLEMENT/STATUS + 6 个 ledger`
- [ ] Phase 0 已产出首版真相地图：formal mainline、authority/substrate、compat/shim/mirror/reference/archive/delete-candidate、current evidence、canonical docs 均有 ledger
- [ ] `identity` 已按代码事实落为单一 runtime authority baseline，并在 ledger / docs / gate 中对齐
- [ ] `self-model` 若进入本轮，必须完成代码级 authority demotion：formal owner 明确、legacy adapter/mirror 不再冒充 live authority、formal mainline 无 legacy import
- [ ] `drives / reflection / developmental` 本轮至少进入 ledger 与 conflict register，不再隐性漂移
- [ ] 本轮不改坏 formal mainline、replay/trace/adapter 边界、repo gate 与现行 evidence chain

## Known risks / dependencies

- 风险：全仓存在大量既有脏文件与历史 artifacts；若不严格 scoped，很容易把无关噪声混进提交
- 风险：`proto_self_restore`、`self_model_adapter`、`self_model_mirror` 仍有 tools/docs/generated caller；本轮只能做 delete-admission，不保证直接删除
- 风险：`drives / reflection / developmental` 的 dual-layer 结构仍活跃；第一轮不能同时动四块语义
- 依赖：已有 authority refs、path register、single-authority verifier、identity baseline code wave
- 外部 blocker：若 caller 关系无法在本轮清楚证明，删除波次必须延后

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `README.md`
- `EgoCore/README.md`
- `OpenEmotion/README.md`
- `docs/CURRENT_PROJECT_LOGIC_FLOW.md`
- `docs/PROTO_SELF_MVP_AUTHORITY_AUDIT.md`
- `docs/PROTO_SELF_SINGLE_AUTHORITY_DECISION.md`
- `EgoCore/docs/05_DEPRECATED_AND_SHIMS.md`
- `scripts/codex/verify_path_classification.py`
- `scripts/codex/verify_proto_self_single_authority.py`
