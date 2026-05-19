# MVS H1 External Eval Corpus - PLAN

## Task summary

这是一个 bounded implementation + source-freeze slice。目标不是运行外部评测，而是把公开 source shortlist、60 条 held-out selection contract、reserve rows、license matrix 和 validator 一次性冻结下来，供后续 MVS/H1 replay/eval 直接消费。

## Execution mode

- mode: implementation / exploration
- why this mode: source 选择需要少量 research，但主要交付物是 repo-tracked manifest 与 validator
- proof required after discovery: 必须同时拿到 source shortlist、60-row manifest、license matrix、dedupe report、validator 通过

## Milestones

### Milestone 1: Public source freeze

- type: implementation / exploration
- question: 哪些公开 dataset card 最适合作为当前 6 个 buckets 的默认 held-out source
- current framing: 只用 dataset card / benchmark 页面冻结 shortlist，不下载 raw data
- hypotheses:
  - `SQuAD v2 + AmbigQA + ConflictQA + MemoryBench + API-Bank + IFEval` 足够覆盖 6 个 buckets
  - `Do-Not-Answer + SORRY-Bench` 更适合作 restricted reserve，而不是默认 held-out 主线
- scope:
  - `docs/codex/tasks/mvs-h1-external-eval-corpus/*`
  - `scripts/codex/build_mvs_h1_external_eval_corpus.py`
- experiments planned:
  - 浏览 Hugging Face dataset cards，确认 license / split / bucket fit
  - 冻结 source shortlist 与 reserve policy
- kill criteria:
  - 若 bucket 数必须扩到 6 之外才能覆盖需求，则停止
  - 若 source 许可或 split 不足以支持 held-out contract，则停止
- files / areas likely touched:
  - Task docs
  - shortlist / manifest builder
- acceptance:
  - source shortlist 冻结
  - reserve sources 明确且未混入主 held-out
- validation:
  - `python3 -m py_compile scripts/codex/build_mvs_h1_external_eval_corpus.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 若 shortlist 不能映射现有 ontology，就只保留 source matrix，不生成 sample rows

### Milestone 2: Manifest + validator freeze

- type: implementation / exploration
- question: 能否在不下载 raw data 的前提下，生成 60 条 sample-level selection contract，并由 validator 保证 bucket / dedupe / overlap 约束
- current framing: 每条 row 是 “selection contract” 而不是已下载原始样本
- hypotheses:
  - selection contract 形式足以支持后续外部 eval slice
  - Trial-1 hard set overlap 可以通过 deterministic validator 检出
- scope:
  - manifest / license matrix / dedupe report
  - validator
  - Task docs closeout
- experiments planned:
  - 生成 manifest
  - 运行 validator
- kill criteria:
  - 若 60-row manifest 需要依赖未验证的 raw scraping，则停止
  - 若 validator 无法保证 bucket balance / dedupe / overlap，则停止
- files / areas likely touched:
  - `scripts/codex/verify_mvs_h1_external_eval_corpus.py`
  - generated task artifacts
- acceptance:
  - `heldout_eval_count=60`
  - `restricted_reserve_count>=1`
  - validator `ok=true`
- validation:
  - `python3 -m py_compile scripts/codex/build_mvs_h1_external_eval_corpus.py scripts/codex/verify_mvs_h1_external_eval_corpus.py`
  - `python3 scripts/codex/build_mvs_h1_external_eval_corpus.py`
  - `python3 scripts/codex/verify_mvs_h1_external_eval_corpus.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 若 sample-level contract 不成立，退回 source shortlist + license matrix，不宣称 external eval manifest ready

## Progress

- current_status: Milestone 1 + Milestone 2 completed
- current_milestone: closeout
- milestone_state: completed
- candidate_vs_proof: proof_passed

## Decision log

- 2026-04-09: 外部 corpus 先做 source/selection contract，不拉 raw data；原因是当前任务只需要 bounded held-out manifest，不需要下载执行
- 2026-04-09: `Do-Not-Answer` 与 `SORRY-Bench` 放入 reserve，不进默认 held-out；原因是当前 ontology 更关注 public-driver 行为而不是 refusal-heavy safety评测

## Surprises / discoveries

- 新发现 1：`IFEval` 数据卡只有 `train` split，因此只能作为“source-only held-out reservation”使用，不能伪造 test split
- 新发现 2：`ConflictQA` viewer disabled，但 dataset card 仍足够支持 source-level eval contract
- 已排除路线 1：直接下载并抽取 60 个 raw prompts
- 已排除路线 2：把 tuning 和 held-out 在同一个 manifest 里混写

## Outcomes / retrospective

- 本轮已证明：当前 repo 已有一份 60-row 外部 held-out selection contract，覆盖 6 个指定 buckets，并通过 validator
- 还没证明：这些 source 上的真实 replay/runner 效果
- 本轮排除了什么：无约束 scraping、无 license 区分、无 dedupe 的外部样本收集方式
- 下一步最小闭环动作：单开 raw extraction / replay-on-external-corpus slice，只消费这份 manifest
