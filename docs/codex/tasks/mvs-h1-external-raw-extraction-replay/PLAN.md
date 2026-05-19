# MVS H1 External Raw Extraction Replay - PLAN

## Task summary

把冻结的外部 eval manifest 转成 replay-ready cases，保持 source-preserving provenance，不扩 source、不改 scorer ontology、不混 tuning。

## Execution mode

- mode: implementation
- why this mode: 任务边界已由冻结 manifest 和既有 scorer ontology 锁定
- proof required after discovery: extraction completeness、provenance completeness、dedupe/overlap cleanliness

## Milestones

### Milestone 1: Freeze Inputs And Extraction Contract

- type: implementation
- question: 哪些 source endpoint 和 schema 足够支撑 frozen manifest
- current framing: manifest row -> deterministic extractor -> replay-ready case
- hypotheses:
  - 每个 bucket 都能映射到当前 replay ontology 的一个已知 case family
  - 公开 dataset endpoints 足以读取 raw rows
- scope:
  - 创建 extraction task
  - 实现 source-specific raw readers
  - 实现 normalized case builders
- experiments planned:
  - 对每个 dataset source 做结构探测
  - 先构建 extractor，再用 failure report 暴露缺口
- kill criteria:
  - 必须新增新 source 才能闭环
  - 需要改 scorer ontology 才能落地
- files / areas likely touched:
  - `scripts/codex/build_mvs_h1_external_raw_extraction_replay.py`
  - `scripts/codex/verify_mvs_h1_external_raw_extraction_replay.py`
  - `docs/codex/tasks/mvs-h1-external-raw-extraction-replay/*`
- acceptance:
  - extractor 能消费 frozen manifest
  - reserve 独立保留
- validation:
  - `python3 -m py_compile scripts/codex/build_mvs_h1_external_raw_extraction_replay.py scripts/codex/verify_mvs_h1_external_raw_extraction_replay.py`
- rollback note:
  - 若 source schema 太不稳定，则保留失败报告而不碰 manifest

### Milestone 2: Close Extraction Gaps And Verify

- type: implementation
- question: extraction failures 是真实外部不可得，还是 extractor candidate-pool 设计不足
- current framing: 最小修复 extraction logic，不改 frozen sources
- hypotheses:
  - continuity 缺口可通过同一来源内的多-config pool 补齐
  - 无需新增 source 即可达到 60/60 held-out extraction
- scope:
  - 修复 continuity candidate pool
  - 重跑 extractor + verifier
  - 收口 task docs
- experiments planned:
  - 对 `THUIR/MemoryBench` continuity config 做小规模可用性检查
  - 重跑 full extraction
- kill criteria:
  - 必须改 manifest 才能补齐
  - 必须增加新 source 才能补齐
- files / areas likely touched:
  - `scripts/codex/build_mvs_h1_external_raw_extraction_replay.py`
  - `docs/codex/tasks/mvs-h1-external-raw-extraction-replay/*`
- acceptance:
  - 60 held-out rows 全部转成 replay-ready case
  - `restricted_reserve` 单独保留
  - dedupe / overlap re-check 通过
- validation:
  - `python3 scripts/codex/verify_mvs_h1_external_raw_extraction_replay.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 如果 multi-config 仍不足，降级为带 failure report 的条件性完成

## Progress

- current_status: closed
- current_milestone: Milestone 2
- milestone_state: verified
- candidate_vs_proof: proof_passed

## Decision log

- 2026-04-10: 只使用 frozen manifest，不重新搜索或扩大 source 集合
- 2026-04-10: `continuity` 初版失败归因为 single-config candidate pool exhausted，而不是 source/license 问题
- 2026-04-10: 在同一 `THUIR/MemoryBench` source 内改为 multi-config continuity pool，补齐 60/60 extracted cases

## Surprises / discoveries

- `osunlp/ConflictQA` dataset-server split endpoint 不可用，但 raw HF file 可稳定读取
- `THUIR/MemoryBench:Locomo-0` 只有 5 条可用 continuity rows，单 config 不足以支撑 frozen 10-row bucket
- 已排除路线 1：新增 source 或改 frozen manifest
- 已排除路线 2：修改 scorer ontology 以适配 source schema

## Outcomes / retrospective

- 本轮已证明：冻结 manifest 可以在不扩 source 的前提下转成 60 个 held-out replay-ready cases
- 还没证明：这些 external cases 在 replay runner 上的行为区分度
- 本轮排除了什么：single-config continuity pool 足够的假设
- 下一步最小闭环动作：新开只消费 `artifacts/external_eval_replay_v1/cases/heldout_eval/` 的 replay execution task
