# Status

Last updated: 2026-05-31

## Current Milestone

Accepted as local/scripted comparison evidence. EGO-FS-087 ran the same-prompt
candidate/baseline comparison requested by the #94 Loop 112 GPT-5.5 partial
verdict.

## Source Evidence

- `/tmp/ego_fs010_functional_subject_total_gate_after_fs086_loop112/functional_subject_trial_report.json`
  -> GPT-5.5 `partial`.
- Missing evidence includes a baseline comparison against the same base
  LLM+RAG+tools path without Functional Subject gates.

## Boundary Contract

- Owner: `EgoOperator` evaluation harness.
- Canonical task state: `Tasks/TASK_BOARD.yaml`.
- Allowed mutation: baseline comparison runner timeout forwarding, task docs,
  task board.
- Forbidden mutation: runtime behavior changes, PROJECT_MEMORY, program state,
  evidence ledger, legacy runtime, GitHub Project as truth source.

## Initial Change

- Forwarded `--case-timeout-seconds` into
  `run_functional_subject_baseline_comparison` so the same timeout safety used
  by total-gate runs applies to candidate/baseline arms.

## Evidence

- `/tmp/ego_fs087_same_prompt_baseline_comparison_v1/functional_subject_baseline_comparison_report.json`
  -> `scripted_functional_subject_comparison_judge_partial`.
- Candidate and baseline both ran the same 20 Functional Subject prompts.
- Candidate arm: operator memory enabled, SubjectContext enabled, native memory
  gate enabled.
- Baseline arm: operator memory disabled, SubjectContext disabled, native memory
  gate disabled.
- Comparison summary: `reply_text_diff_count=16`,
  `candidate_mechanism_trace_count=20`, candidate clean first-pass `13/20`,
  baseline clean first-pass `13/20`, candidate repair cases `7/20`, baseline
  repair cases `7/20`.
- GPT-5.5 scores were strong on trace/gate/user-experience dimensions, but the
  verdict remained `partial` because clean first-pass and repair reliance did
  not clearly outperform baseline and durable delayed evidence is still missing.

## Next Step

Accept EGO-FS-087 as comparison evidence, sync #101 as Done, and route the next
#94 blocker into a delayed replay / fresh-session memory transition proof for
fs15/fs16/fs17.

## Claim Ceiling

`Functional Subject same-prompt baseline comparison local/scripted candidate pass`.
