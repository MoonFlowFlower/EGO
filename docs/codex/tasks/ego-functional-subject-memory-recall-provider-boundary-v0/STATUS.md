# Status

Last updated: 2026-05-31

## Current Milestone

Accepted locally/scripted.

## What Changed

- Added a narrow Functional Subject continuity-recall native gate.
- The gate only targets explicit questions about why Functional Subject is the
  project goal; it does not capture ordinary memory-restart prompts such as
  `EGO-FS-083` preference recall.
- The response admits uncertainty, summarizes the current project mechanism
  framing, and stays read-only.

## Evidence

- Targeted contract tests:
  `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py -k 'functional_subject_recall or memory_save_provider_error or memory_forget_provider_error'`
  -> `4 passed, 260 deselected`.
- #94 rerun:
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs090_loop117/functional_subject_trial_report.json`
  -> `scripted_functional_subject_judge_partial`.
- Loop 117 fs01 evidence:
  `fs_01_shared_memory_recall` is clean first-pass with origin
  `native_memory_gate` and reason `native_functional_subject_recall_gate`.
- Loop 117 summary:
  clean first-pass `16/20`, blocking case count `0`, GPT-5.5 still `partial`.

## Remaining Risk

#94 remains open. The remaining judge concerns are broader than fs01:
multi-session non-scripted operator evidence, baseline comparison, durable memory
scope, and OutcomePrediction action-selection evidence outside repair-heavy
paths.

## Not Claimed

No durable memory efficacy, stable user benefit, runtime efficacy, live
autonomy, independent personhood, real subjective experience, or consciousness.
