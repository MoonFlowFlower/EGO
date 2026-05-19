# MVS H1 External Replay Execution - STATUS

## Current milestone

- name: Milestone 2 - Execute, Score, And Close
- owner: Codex
- state: completed
- type: implementation

## Current state

- current_layer: external replay execution / bounded analysis
- main_chain_status: canonical mainline untouched; isolated temp stores only
- completion_class: conditional_complete
- candidate_vs_proof: proof_passed

## Completed work

- 创建了 execution task 目录
- 冻结了 runner 边界：只读 held-out cases、baseline vs canonical shadow-H1、不改 ontology
- 完成了 correction / continuity / uncertainty / tool bucket 的小样本 probe
- 完成了 `60` held-out cases x `2` variants 的 full replay execution
- 生成了 execution / bucket / failure / mechanism 四类报告

## Last experiment

- question: baseline 与 canonical shadow-H1 在 frozen external replay 上是否产生 public gap，还是只产生 shadow-only telemetry
- framing: full held-out execution with canonical event-builder + adapter surface, same public-output ontology
- result: `executed_case_variants=120`, `execution_failures=0`, `public_gap_cases_candidate_vs_baseline=0`, `shadow_only_cases_candidate_vs_baseline=30`
- evidence_upgraded: yes

## What was learned

- task-local isolated stores 足以避免 canonical writeback 污染
- current canonical shadow-H1 path 在 external replay 下仍是 shadow-only：candidate 只在 3 个 direct buckets 上出现 `shadow_h1`
- `correction` / `failure_revision_later_change` buckets 当前没有形成 public revision gap，也没有形成 complete corrective trace
- `ask_vs_answer_uncertainty` / `continuity` / `adversarial_constraints` buckets 在 baseline 和 candidate 上都呈现相同 public signatures

## What was ruled out

- 被排除路线 1：直接读写 canonical stores 来跑 external replay
- 被排除路线 2：需要扩 source 或改 scorer ontology 才能开始执行
- 被排除路线 3：full runtime + mounted-drive execution roots 作为当前 bounded replay 默认路径

## Next framing

- external replay execution 已完成；下一轮若存在，应进入 interpretation / challenger-comparison 之前的独立任务

## Last validation results

- mode: full task-local + fast
- result: passed
- summary:
  - external replay execution verifier passed
  - `candidate_shadow_present_on_direct_buckets` passed
  - fast gate pending final rerun

## Decisions made

- 决策 1：runner 最终使用 canonical event-builder + adapter surface，而不是 full runtime writeback loop
- 决策 2：工具歧义 / correction / failure buckets 使用 synthetic exec-result 来触发 bounded shadow telemetry path
- 决策 3：execution roots 改到系统临时目录，只保最终 reports，避免 mounted-drive I/O 拖垮 bounded replay

## Open risks

- 风险 1：当前 bucket scores 对多个 buckets 呈现 `1.0` flat profile，说明 ontology 在这批 replay 上的区分度有限
- 风险 2：correction-oriented buckets 没有 complete corrective trace，不应把 shadow telemetry 误当作 revision efficacy
- proof gap: external replay interpretation 尚未与 challenger 或更强 ablation 对齐

## Next step

- 唯一最高优先级动作：如果继续，单开 interpretation task，先决定这组 flat replay 结果是否足以支撑后续 challenger comparison

## Commands run / evidence

- `python3 scripts/codex/new_task.py mvs-h1-external-replay-execution --title "MVS H1 External Replay Execution"`
- correction / continuity / uncertainty / tool bucket probe commands
- `python3 -m py_compile scripts/codex/run_mvs_h1_external_replay_execution.py scripts/codex/verify_mvs_h1_external_replay_execution.py`
- `python3 scripts/codex/run_mvs_h1_external_replay_execution.py`
- `python3 scripts/codex/verify_mvs_h1_external_replay_execution.py`
- `artifacts/external_eval_replay_v1/reports/MVS_H1_EXTERNAL_REPLAY_EXECUTION_CURRENT.json`
- `artifacts/external_eval_replay_v1/reports/MVS_H1_EXTERNAL_REPLAY_BUCKET_SCORE_SUMMARY_CURRENT.json`
- `artifacts/external_eval_replay_v1/reports/MVS_H1_EXTERNAL_REPLAY_EXECUTION_FAILURES_CURRENT.json`
- `artifacts/external_eval_replay_v1/reports/MVS_H1_EXTERNAL_REPLAY_MECHANISM_RELEVANCE_CURRENT.json`
