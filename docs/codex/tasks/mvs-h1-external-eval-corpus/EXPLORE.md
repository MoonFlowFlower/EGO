# MVS H1 External Eval Corpus - EXPLORE

> 仅在 research / verify / observation / proof / high-unknown 任务中强制使用。
> 每次实验后必须先更新本文件，再开始下一轮。

## Exploration mode

- enabled: yes
- why exploration mode is needed: source/license/split 需要 research，但输出仍是 deterministic manifest
- current framing: 先冻结 external held-out selection contract，再讨论 raw extraction
- success looks like: `6` buckets / `60` heldout rows / validator pass
- disallowed premature claims:
  - “外部泛化已证明”
  - “challenger 已被打败”

## Question reformulation

- original question: 去网上找能测 MVS/H1 的外部数据
- normalized question: 哪些公开 dataset card 能支持当前 ontology 下的 held-out selection contract
- why this framing is better: 它先解决 source authority 和 eval hygiene，再解决原始数据下载

## Hypotheses

### Hypothesis 1

- statement: 当前 6 个主 shortlist source 足以覆盖用户要求的 6 个 buckets
- why plausible: 这些 source 分别对应 ambiguity、conflict、memory/feedback、tool use 和 constraint-following
- kill criteria: 任一 bucket 需要引入第 7 类 source 才能成立
- smallest experiment: 逐个 bucket 冻结 `source_dataset_id + split + target_mechanism + expected_observable`

### Hypothesis 2

- statement: sample-level selection contract 可以先于 raw sample 下载独立成立
- why plausible: 用户当前要的是 corpus manifest，不是已执行的 eval run
- kill criteria: manifest 如果缺少 raw prompt 就无法表达 target mechanism / expected observable
- smallest experiment: 生成 60 条 row 并让 validator 检查完整性 / dedupe / overlap

## Experiment log

### Cycle 01

- question: 哪些 source 应进 main shortlist，哪些应进 reserve
- framing used: 只看公开 dataset card / benchmark 页面，不下 raw data
- experiment: 冻结 source matrix 与 bucket fit
- command / script / artifact: Hugging Face dataset cards; `MVS_H1_EXTERNAL_EVAL_SOURCE_SHORTLIST_CURRENT.md`
- observed result: 6 个 main shortlist source 足以覆盖 buckets，`Do-Not-Answer` 与 `SORRY-Bench` 进 reserve
- what it proves: source freeze 可在当前 ontology 下完成
- what it does not prove: 这些 source 上的真实 replay 成绩
- what path is ruled out: 把 refusal-heavy / custom-license source 混入主 held-out
- decision for next step: 进入 manifest/validator 实装

### Cycle 02

- question: selection contract 形式能否满足 held-out corpus manifest 的需求
- framing used: 每条 row 显式绑定 mechanism + observable + split + source
- experiment: 生成 60-row manifest + validator
- command / script / artifact:
  - `python3 scripts/codex/build_mvs_h1_external_eval_corpus.py`
  - `python3 scripts/codex/verify_mvs_h1_external_eval_corpus.py`
- observed result: `heldout_eval_count=60`，validator `ok=true`
- what it proves: repo 里已经有一份可被后续 slice 直接消费的外部 held-out manifest
- what it does not prove: raw extraction correctness 或 external replay efficacy
- what path is ruled out: 先下载数据再补 manifest
- decision for next step: close 当前任务，后续另开 raw extraction / replay slice

## Framing changes

- 2026-04-09: “找一些外部数据” -> “冻结外部 held-out selection contract” / 避免 scraping 与 tuning-eval 混写 / 使当前 slice 可闭环

## Candidate vs proof

- candidate_found: 6-source shortlist
- proof_pending: external raw extraction 与 replay execution
- proof_passed: source shortlist + manifest + validator
- remaining proof gap: 真实 external replay 尚未开始
