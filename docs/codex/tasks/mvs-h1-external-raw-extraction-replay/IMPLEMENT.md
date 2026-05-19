# MVS H1 External Raw Extraction Replay - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `docs/codex/tasks/mvs-h1-external-eval-corpus/MVS_H1_EXTERNAL_EVAL_CORPUS_MANIFEST_CURRENT.json`

## Execution rules

- 只消费 frozen manifest，不追加 source
- 只生成 extraction artifacts，不改 canonical mainline 行为
- restricted reserve 只做独立记录，不参与 held-out extraction

## Scope control

- 允许修改：
  - `scripts/codex/build_mvs_h1_external_raw_extraction_replay.py`
  - `scripts/codex/verify_mvs_h1_external_raw_extraction_replay.py`
  - 当前 task docs
  - `artifacts/external_eval_replay_v1/` outputs
- 不允许修改：
  - scorer ontology
  - replay runner contract
  - canonical proto_self / EgoCore runtime mainline

## Validation strategy

- 语法：
  - `python3 -m py_compile scripts/codex/build_mvs_h1_external_raw_extraction_replay.py scripts/codex/verify_mvs_h1_external_raw_extraction_replay.py`
- extraction contract：
  - `python3 scripts/codex/build_mvs_h1_external_raw_extraction_replay.py`
  - `python3 scripts/codex/verify_mvs_h1_external_raw_extraction_replay.py`
- repo fast gate：
  - `python3 scripts/codex/verify_repo.py --mode fast`
- pre-closeout hygiene：
  - `git diff --check -- docs/codex/tasks/mvs-h1-external-raw-extraction-replay scripts/codex/build_mvs_h1_external_raw_extraction_replay.py scripts/codex/verify_mvs_h1_external_raw_extraction_replay.py artifacts/external_eval_replay_v1`

## Failure handling

- source row 不可抽取时，必须进入 failure report，不得静默丢弃
- 若单一 config 不足但同一 source 还有可用 config，优先做 same-source multi-config 修复
- 若必须改 frozen manifest 或 scorer ontology，停止并降级为 underdefined

## Stopping rule

- extraction verifier 未通过，不进入 closeout
- 如需新增 source、扩 manifest、或改 scorer ontology，则立即停止并回写 blocker

## Final handoff checklist

- [x] `PLAN.md` 已更新进度与决策
- [x] `STATUS.md` 已更新验证结果与 next step
- [x] commands run / evidence 已记录
- [x] risks / rollback notes 已记录
