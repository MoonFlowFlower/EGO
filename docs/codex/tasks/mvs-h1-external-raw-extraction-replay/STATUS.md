# MVS H1 External Raw Extraction Replay - STATUS

## Current milestone

- name: Milestone 2 - Close Extraction Gaps And Verify
- owner: Codex
- state: completed
- type: implementation

## Current state

- current_layer: external eval extraction / replay-case preparation
- main_chain_status: canonical mainline untouched
- completion_class: conditional_complete
- candidate_vs_proof: proof_passed

## Completed work

- 实现了 frozen manifest -> replay-ready case extractor 与 verifier
- 生成了 extraction map、bucket report、failures report、dedupe/overlap re-check、restricted reserve report
- 修复了 continuity single-config candidate pool exhausted，最终达到 60/60 held-out extraction

## Last experiment

- question: `THUIR/MemoryBench` continuity 缺口是 source 不足还是 extractor pool 设计不足
- framing: 保持同一 frozen source，不新增 source，只在 config 组合上做最小修复
- result: `Locomo-0` 单 config 只有 5 条；切到 `Locomo-0..3` multi-config 后，continuity 达到 10/10
- evidence_upgraded: yes

## What was learned

- source-preserving replay extraction 可以完全建立在公开 dataset server / raw file endpoint 上
- 当前 frozen manifest 的 60 条 held-out rows 全部可被抽成 replay-ready cases
- restricted reserve 可以独立记录而不混入 held-out cases

## What was ruled out

- 被排除路线 1：需要新增 external source 才能补齐 continuity
- 被排除路线 2：需要改 scorer ontology 才能兼容外部 raw schema

## Next framing

- 下一轮不再做 extraction；只消费已生成 case files 做 replay execution / scoring

## Last validation results

- mode: fast + task-local
- result: passed
- summary:
  - `py_compile` passed
  - external replay verifier passed
  - `verify_repo --mode fast` passed
  - `git diff --check` scoped slice passed

## Decisions made

- 决策 1：restricted reserve 只输出 reserve report，不默认提取成 held-out case files
- 决策 2：continuity 使用同一 `THUIR/MemoryBench` source 下的多-config pool，而不是扩 source

## Open risks

- 风险 1：公开 dataset endpoint 的长期稳定性仍依赖外部服务
- 风险 2：当前 replay-ready case schema 已保 provenance，但尚未证明下游 runner 的行为覆盖率
- proof gap: external replay execution 尚未运行

## Next step

- 唯一最高优先级动作：创建 external replay execution task，只消费 `heldout_eval` cases 并保持 scorer ontology 不变

## Commands run / evidence

- `python3 -m py_compile scripts/codex/build_mvs_h1_external_raw_extraction_replay.py scripts/codex/verify_mvs_h1_external_raw_extraction_replay.py`
- `python3 scripts/codex/build_mvs_h1_external_raw_extraction_replay.py`
- `python3 scripts/codex/verify_mvs_h1_external_raw_extraction_replay.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `git diff --check -- docs/codex/tasks/mvs-h1-external-raw-extraction-replay scripts/codex/build_mvs_h1_external_raw_extraction_replay.py scripts/codex/verify_mvs_h1_external_raw_extraction_replay.py artifacts/external_eval_replay_v1/reports`
- `artifacts/external_eval_replay_v1/reports/MVS_H1_EXTERNAL_REPLAY_EXTRACTION_MAP_CURRENT.json`
- `artifacts/external_eval_replay_v1/reports/MVS_H1_EXTERNAL_REPLAY_BUCKET_REPORT_CURRENT.json`
- `artifacts/external_eval_replay_v1/reports/MVS_H1_EXTERNAL_REPLAY_FAILURES_CURRENT.json`
- `artifacts/external_eval_replay_v1/reports/MVS_H1_EXTERNAL_REPLAY_DEDUPE_RECHECK_CURRENT.json`
- `artifacts/external_eval_replay_v1/reports/MVS_H1_EXTERNAL_REPLAY_RESTRICTED_RESERVE_CURRENT.json`
