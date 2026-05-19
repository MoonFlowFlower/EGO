# MVS H1 External Eval Corpus - STATUS

## Current milestone

- name: Milestone 2 - Manifest + validator freeze
- owner: Codex
- state: completed
- type: implementation / exploration

## Current state

- current_layer: implementation / verification
- main_chain_status: external held-out source manifest frozen; no raw extraction yet
- completion_class: conditional_complete
- candidate_vs_proof: proof_passed

## Completed work

- 已生成 `MVS_H1_EXTERNAL_EVAL_SOURCE_SHORTLIST_CURRENT.{json,md}`
- 已生成 `MVS_H1_EXTERNAL_EVAL_CORPUS_MANIFEST_CURRENT.json`
- 已生成 `MVS_H1_EXTERNAL_EVAL_LICENSE_MATRIX_CURRENT.md`
- 已生成 `MVS_H1_EXTERNAL_EVAL_DEDUPE_REPORT_CURRENT.md`
- 已实现并跑通 `scripts/codex/verify_mvs_h1_external_eval_corpus.py`

## Last experiment

- question: 在不下载 raw data 的情况下，能否冻结一份对当前 MVS/H1 scorer 友好的 sample-level 外部 held-out selection contract
- framing: 用 selection contract 代替已下载样本，把 source/split/license/bucket/observable 固化下来
- result: `60` 条 held-out rows + `2` 条 restricted reserve rows 已落地，validator `ok=true`
- evidence_upgraded: yes

## What was learned

- `SQuAD v2 / AmbigQA / ConflictQA / MemoryBench / API-Bank / IFEval` 足够覆盖当前 6 个 buckets
- source-level held-out manifest 可以先独立于 raw download 落地，不必等外部 extraction slice

## What was ruled out

- 被排除路线 1：在本任务里直接抓取大规模 raw prompts
- 被排除路线 2：把 safety refusal-heavy dataset 默认并入当前主 held-out 清单

## Next framing

- 下一轮问题表述 / framing：仅当需要真正跑外部 replay 时，再基于这份 manifest 开 extraction + runner slice

## Last validation results

- mode: py_compile + builder + validator
- mode: py_compile + builder + validator + fast gate
- result: passed
- summary:
  - `python3 -m py_compile scripts/codex/build_mvs_h1_external_eval_corpus.py scripts/codex/verify_mvs_h1_external_eval_corpus.py`
  - `python3 scripts/codex/build_mvs_h1_external_eval_corpus.py`
  - `python3 scripts/codex/verify_mvs_h1_external_eval_corpus.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`

## Decisions made

- held-out main manifest 只保留 6 个 buckets，每 bucket 10 条
- `Do-Not-Answer` 与 `SORRY-Bench` 仅记录为 reserve，不进入默认主清单

## Open risks

- 风险 1：`API-Bank` / `ConflictQA` 的具体 raw extraction 仍需后续 slice 去把 source contract 落到实例级样本
- 风险 2：`IFEval` 只有 `train` split，需要在后续执行时继续严格保证它不被挪作 tuning
- proof gap: 还没有真实 external replay 结果

## Next step

- 唯一最高优先级动作：若继续，单开 external raw extraction + replay task，只消费这份 manifest

## Commands run / evidence

- `python3 -m py_compile scripts/codex/build_mvs_h1_external_eval_corpus.py scripts/codex/verify_mvs_h1_external_eval_corpus.py`
- `python3 scripts/codex/build_mvs_h1_external_eval_corpus.py`
- `python3 scripts/codex/verify_mvs_h1_external_eval_corpus.py`
- `docs/codex/tasks/mvs-h1-external-eval-corpus/MVS_H1_EXTERNAL_EVAL_SOURCE_SHORTLIST_CURRENT.md`
- `docs/codex/tasks/mvs-h1-external-eval-corpus/MVS_H1_EXTERNAL_EVAL_CORPUS_MANIFEST_CURRENT.json`
