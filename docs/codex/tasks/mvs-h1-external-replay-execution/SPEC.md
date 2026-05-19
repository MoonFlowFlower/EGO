# MVS H1 External Replay Execution

## Goal

只消费 `artifacts/external_eval_replay_v1/cases/heldout_eval`，运行 baseline 与 current canonical shadow-H1 path 的 bounded replay execution，并产出 bucket-level 执行结果、失败表、机制相关总结。

## Non-goals

- 不新增 sources 或修改 frozen corpus
- 不改变 scorer ontology
- 不混 tuning 与 evaluation
- 不触碰 canonical mainline 行为
- 不做 repo-level state upgrade
- 不做 runtime efficacy claim

## Constraints

- 边界约束：只读取 frozen held-out case files
- 执行约束：所有 runtime / writeback 必须落到 task-local execution roots，不能污染 canonical stores
- 结果约束：每个失败都必须带 cause classification，不能静默丢 case
- 证明约束：最终结论只能停在 E2/E3 replay analysis 口径

## Problem framing

- 当前问题表述：外部 held-out cases 已提取完，下一步要看 current MVS/H1 在这批 cases 上能跑出什么 public/mechanism 信号
- 归一化后的问题表述：建立一个不改 mainline、不改 ontology 的 bounded replay runner，比较 baseline 与 canonical shadow-H1 execution traces
- 为什么这个 framing 更适合当前任务：这一步是分析与验证，不是新机制实现

## Unknowns to eliminate

- frozen held-out cases 是否都能被 current canonical replay runner 消费
- baseline 与 canonical shadow-H1 path 在 public outputs 上是否有可见差异
- 哪些 bucket 真正直接触发 H1 shadow path，哪些只是 broader MVS buckets

## Acceptance criteria

- [ ] 生成 execution report
- [ ] 生成 per-bucket score summary、failure table、mechanism relevance table
- [ ] 明确写出 under E2/E3 can prove / cannot prove

## Disallowed premature claims

- 不宣称 runtime efficacy
- 不宣称 live decision promotion
- 不宣称 external replay 结果等同于 E4

## Known risks / dependencies

- 风险：当前 canonical proto_self public outputs 可能对多数 external buckets 呈现 flat behavior
- 风险：H1 是 shadow-only telemetry，candidate 可能不产生 public delta
- 依赖：现有 frozen case files、canonical proto_self runtime、task-local temp stores

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `docs/codex/tasks/mvs-h1-external-raw-extraction-replay/SPEC.md`
- `docs/codex/tasks/mvs-h1-external-raw-extraction-replay/STATUS.md`
- `artifacts/external_eval_replay_v1/cases/heldout_eval/`
