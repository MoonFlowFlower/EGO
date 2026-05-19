# MVS H1 External Eval Corpus

## Goal

基于公开 benchmark / dataset card，构建一个 bounded 的 MVS/H1 外部 held-out eval corpus manifest，使后续 replay / public-driver 验证可以在不 scraping、不过早下载原始数据、也不混入 tuning 的前提下，有一份可审计的外部样本真相源。

## Non-goals

- 不在本任务内下载或清洗完整原始数据集
- 不在本任务内构建 tuning set
- 不在本任务内变更 scorer ontology、挑战者评分、或 repo-level program state

## Constraints

- 边界约束：只使用公开 benchmark/task source 与 dataset card；不做随机大规模 scraping
- 仓库/子仓约束：manifest 必须映射现有 MVS/H1 机制与 observable，不能引入第二套 ontology
- 环境约束：当前 Linux env 未安装 `datasets` / `huggingface_hub`，因此本任务只做 curated manifest，不做 dataset 下载
- 发布约束：不升级 repo-level state，不宣称任何外部 eval 已经跑通

## Problem framing

- 当前问题表述：去网上找一些外部数据，做 MVS/H1 测试集
- 归一化后的问题表述：先冻结“外部 held-out eval 采样合同”，把来源、license、split、bucket、机制映射、期望 observable 和 dedupe/overlap 规则固化，再谈后续下载或执行
- 为什么这个 framing 更适合当前任务：当前缺的不是更多 raw data，而是一份不混淆 tuning/eval、不会漂移 ontology、并能被代码验证的外部评测清单

## Unknowns to eliminate

- 哪些公开数据源最适合 6 个指定 buckets
- 哪些 license / split 适合默认进入 held-out manifest，哪些只应进 reserve
- 如何在不下载原始数据的情况下仍保持 sample-level selection contract 可执行

## Acceptance criteria

- [ ] 只保留 6 个 buckets：`correction`、`ask_vs_answer_uncertainty`、`failure_revision_later_change`、`tool_risk_ambiguity`、`continuity`、`adversarial_constraints`
- [ ] 生成 60 条 `heldout_eval` rows，且每 bucket 正好 10 条
- [ ] 每条 row 都有 `license/source/split/bucket/target_mechanism/expected_observable`
- [ ] 额外记录 restricted reserve sources，但不混入默认 held-out 主清单
- [ ] validator 能验证 bucket 数、dedupe、partition、Trial-1 hard-set overlap

## Disallowed premature claims

- 不能宣称这些外部数据已经被当前 MVS/H1 runner 跑过
- 不能宣称这些 source 自动证明 challenger / candidate 的优劣
- 不能把 source shortlist 写成“已完成外部泛化证明”

## Known risks / dependencies

- 风险：部分 source 只有 `train` split 或 viewer disabled，需要在 manifest 中明确“source-only eval reservation”而不是伪造标准 split
- 依赖：Hugging Face dataset cards、公开 benchmark 页面
- 外部 blocker：若后续真的要拉取 raw samples，还需要额外的下载/selection slice

## Authority refs

- `docs/codex/tasks/ai-self-awareness-minimal-framework/REPLAY_VALIDATOR_SPEC.md`
- `docs/codex/tasks/ai-self-awareness-minimal-framework/TRIAL1_COUNTERFACTUAL_HARD_SET.json`
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- 相关 `Tasks/active/*.md` / review / report / spec
