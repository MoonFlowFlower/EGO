---
name: ai-architecture-boundary
description: Use only for AIProject architecture-boundary tasks involving legacy EgoCore/OpenEmotion, OpenClaw, or cross-system owner boundaries, authority source, receipt/main-chain semantics, enablement, trigger evidence, or architectural drift from local fixes. Do not use for ordinary EgoOperator runtime repairs, single-file fixes, or general coding unless the task explicitly compares or changes legacy boundary ownership.
---

# AI Architecture Boundary

该 skill 只服务 AIProject 的正式边界治理，不是跨项目通用规则，也不是普通 EgoOperator runtime 修复的默认入口。

## Boundary Model

- EgoCore 负责 legacy 外部交互、runtime、工具执行与现实裁决
- OpenEmotion 负责 legacy self-model、memory evolution、appraisal、reflection、developmental self
- OpenClaw 是受约束的施工执行体，不是长期正式宿主
- EgoOperator-first 迁移后，普通 operator-first runtime 工作以 `EgoOperator` contract / gate / trace 为准；只有触及 legacy owner 边界或跨系统 authority 时才启用本 skill。

当局部修复与边界完整性冲突时，优先守住正式边界，不为短期方便制造长期漂移。

## Workflow

1. 先确认当前问题是否真是边界问题，而不是普通实现缺陷或 EgoOperator 局部体验修复。
2. 明确：
   - chosen owner
   - authority source
   - current layer
   - main-chain stage
   - proof required to call it effective
3. 如果方案引入 shim / cache / mirror / compatibility logic，必须同时给 exit plan。
4. 若问题仍处于想法 / 构件 / 接入阶段，不要把观察期话术拿来冒充已生效。
5. 回复必须区分：
   - 已接主链但未启用
   - 已启用但未触发
   - 已触发但仍缺长期观测

## Archival Purge Checklist

When the task archives or purges legacy `EgoCore`, `OpenEmotion`, `ego_desktop_lab`, OpenClaw, or other old authority-looking surfaces, run this sequence before closeout:

1. Dependency proof: classify references as `active_dependency`, `historical_reference`, `archive_pointer`, or `forbidden_active_authority`.
2. Archive pointer: create or document the tag/branch/commit before deleting current-tree code.
3. Manifest: record removed paths, reason, archive pointer, claim boundary, and rollback instructions.
4. Inventory: preserve reusable ideas as reference only, with no runtime authority or default path.
5. Tombstone: leave a thin pointer in the old location.
6. Anti-regression: add a deterministic verifier that rejects active imports, default routes, registry references, or active-doc authority claims.
7. Closeout scope: declare an `Expected Mutation Surface` and, for large deletion/migration, a task-local `MUTATION_SCOPE.yaml`; do not permanently broaden global allowed paths for one-off deletion surfaces.
8. Publish: run closeout, commit the scoped diff, push `origin main`, and push the archive tag when the pointer is a tag.

## Guardrails

- 不让 EgoCore 偷做 OpenEmotion 本体。
- 不让 OpenEmotion 偷做现实执行与运行时治理。
- receipt / trigger evidence / enablement 缺失时，不宣称闭环完成。
- 对 `~/.openclaw/**` 的保护路径，不建议自由手写改动；优先安全写入路径和可回退变更。
