# MVS H1 External Raw Extraction Replay

## Goal

只消费已经冻结的外部 eval corpus manifest，把 held-out 样本转换成 replay-ready case files，并保留完整 source / license / split / bucket / provenance 字段。

## Non-goals

- 不新增任何 source、dataset、benchmark 或抓取范围
- 不改变 scorer ontology
- 不混入 tuning / training 样本
- 不触碰 canonical proto_self / EgoCore mainline 行为
- 不做 repo-level state upgrade

## Constraints

- 边界约束：只能读取 `mvs-h1-external-eval-corpus` 已冻结 manifest
- 仓库/子仓约束：输出只能落在 extraction artifact / 当前 task docs，不能改 canonical 行为
- 环境约束：优先用 stdlib + public dataset endpoints，不依赖本地 HF SDK
- 发布约束：restricted reserve 必须单独保留，不能混入 held-out replay cases

## Problem framing

- 当前问题表述：把外部 benchmark 清单变成可被当前 replay runner 消费的标准化 case
- 归一化后的问题表述：在不改变现有评测 ontology 的前提下，构建一层 source-preserving extraction adapter
- 为什么这个 framing 更适合当前任务：问题本质是 extraction/provenance 工程，不是新评测设计

## Unknowns to eliminate

- 冻结 manifest 中每一行是否都能从公开 source 稳定抽取
- 不同 source 的 raw schema 是否能归一成当前 replay-ready case family
- 去重、overlap、restricted reserve 分离是否能在 extraction 后继续成立

## Acceptance criteria

- [x] 生成 replay-ready held-out case files，并保留 source/provenance 字段
- [x] 生成 source-preserving extraction map、bucket report、failure report、dedupe/overlap re-check
- [x] restricted reserve 单独保留，不混入 held-out extraction

## Disallowed premature claims

- 不宣称外部 eval 已跑通 MVS/H1
- 不宣称任何 runtime efficacy 或 repo-level 生效

## Known risks / dependencies

- 风险：某些 dataset config 可用样本不足，导致 candidate pool exhausted
- 依赖：公开 dataset server / HF raw file endpoint 可访问
- 外部 blocker：无；本 slice 不依赖真实 Telegram / live runtime

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `docs/codex/tasks/mvs-h1-external-eval-corpus/SPEC.md`
- `docs/codex/tasks/mvs-h1-external-eval-corpus/PLAN.md`
- `docs/codex/tasks/mvs-h1-external-eval-corpus/STATUS.md`
- `docs/codex/tasks/mvs-h1-external-eval-corpus/MVS_H1_EXTERNAL_EVAL_CORPUS_MANIFEST_CURRENT.json`
