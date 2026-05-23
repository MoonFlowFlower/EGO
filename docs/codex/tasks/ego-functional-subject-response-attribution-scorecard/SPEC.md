# EgoOperator Functional Subject First-Pass Versus Repair Scorecard

## Goal

Make Functional Subject trial reports and GPT-5.5 judge packets explicitly separate first-pass LLM behavior from runtime repair, terminal guard, tool-result, outcome-prediction, and provider-recovery behavior.

## Source

- `/tmp/ego_fs_010_after_fs043_20260523_115238/functional_subject_trial_report.json`
- GPT-5.5 judge follow-up: reduce dependence on runtime repair and separate first-pass LLM behavior, runtime guard behavior, and end-to-end operator behavior.

## Scope

Allowed changes:

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- `Tasks/TASK_BOARD.yaml`
- this task directory

Forbidden changes:

- EgoOperator runtime behavior changes
- provider/model policy changes
- task board source-of-truth architecture changes
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- GitHub Project mutation

## Acceptance Gate

- Functional Subject report includes `response_attribution_summary` with origin counts, clean first-pass rate, repair case ids, repair type counts, and provider/tool/terminal counts.
- GPT-5.5 judge packet includes the same scorecard and tells judge not to merge runtime guard pass with first-pass capability.
- Markdown report surfaces the scorecard compactly.
- Existing Functional Subject trial and experiment-control tests do not regress.

## Rollback

Remove response-attribution scorecard fields and keep EGO-FS-010 judge partial reasons less structured.

## Claim Ceiling

`Functional Subject response-attribution scorecard local workflow pass`
