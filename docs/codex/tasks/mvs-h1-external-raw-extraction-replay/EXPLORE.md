# MVS H1 External Raw Extraction Replay - EXPLORE

> 本任务以 implementation 为主，但保留最小实验日志，用来记录 extraction gap 的归因与修复。

## Exploration mode

- enabled: yes
- why exploration mode is needed: source schema 和 candidate pool 是否足够，必须先做小规模可证伪检查
- current framing: frozen manifest rows should be resolvable into deterministic replay-ready cases without source expansion
- success looks like: 60/60 held-out rows extracted, reserve isolated, dedupe/overlap clean
- disallowed premature claims:
  - external replay 已通过
  - MVS/H1 已在外部 corpus 上验证有效

## Question reformulation

- original question: 如何从外部 benchmark 清单里拿到可用 case
- normalized question: 如何在现有 ontology 不变时建立 source-preserving extraction layer
- why this framing is better: 它把任务从“找更多数据”收紧为“把冻结数据接上当前 replay contract”

## Hypotheses

### Hypothesis 1

- statement: 每个 frozen source 都能被一个稳定的 raw-reader + normalizer 适配
- why plausible: source 都有公开 dataset card 或 raw endpoint
- kill criteria: 需要新增 source 或修改 scorer ontology
- smallest experiment: 逐个 source 探测 splits / raw file / row schema

### Hypothesis 2

- statement: continuity 缺口若出现，更可能是 candidate-pool 设计不足而不是来源不可用
- why plausible: `THUIR/MemoryBench` 有多个 continuity-like configs
- kill criteria: 同源多 config 也无法凑齐 10 条 continuity rows
- smallest experiment: 检查 `Locomo-*` 可用 rows 数量

## Experiment log

### Cycle 01

- question: 冻结 manifest 的各 source 是否可公开读取并映射到当前 case family
- framing used: source-specific raw read + deterministic normalizer
- experiment:
  - 探测 SQuAD v2 / AmbigQA / MemoryBench / IFEval dataset-server rows
  - 探测 ConflictQA / API-Bank raw HF files
- command / script / artifact:
  - `scripts/codex/build_mvs_h1_external_raw_extraction_replay.py`
- observed result:
  - extractor 初版成功 55/60，失败 5/60
  - 失败全部集中在 `continuity`
- what it proves:
  - 大多数 source 可被当前 extraction contract 覆盖
- what it does not prove:
  - continuity source 是否本质不足
- what path is ruled out:
  - “所有 source 都不稳定，必须改 ontology”
- decision for next step:
  - 聚焦 continuity failure root cause

### Cycle 02

- question: continuity failure 是来源不足还是单 config pool 过窄
- framing used: 保持同一 source，仅检查 `THUIR/MemoryBench` config 容量
- experiment:
  - 检查 `Locomo-0..3` 的 test rows
  - 把 continuity pool 改成同源 multi-config
- command / script / artifact:
  - `python3 scripts/codex/build_mvs_h1_external_raw_extraction_replay.py`
  - `artifacts/external_eval_replay_v1/reports/MVS_H1_EXTERNAL_REPLAY_BUCKET_REPORT_CURRENT.json`
- observed result:
  - `Locomo-0` 只有 5 条
  - `Locomo-1..3` 各有 5 条
  - multi-config 后达到 60/60 success
- what it proves:
  - 初始缺口来自 extractor pool 设计，而不是 frozen source 不足
- what it does not prove:
  - 下游 replay runner 的行为质量
- what path is ruled out:
  - 新增 source / 扩大 manifest 的路线
- decision for next step:
  - 跑 verifier、收口 task docs、关闭任务

## Framing changes

- 2026-04-10: `single-config continuity extraction` -> `same-source multi-config continuity extraction` / 初版出现 candidate_pool_exhausted / 在不扩 source 的前提下补齐 60/60

## Candidate vs proof

- candidate_found: source-preserving extraction layer can be built with stdlib-only readers
- proof_pending: replay execution on extracted cases
- proof_passed: frozen manifest -> replay-ready case extraction completeness, provenance completeness, reserve separation, dedupe/overlap cleanliness
- remaining proof gap: external replay execution / scoring 尚未运行
