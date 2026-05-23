# EgoOperator Functional Subject Judge Timeout + Pre-Judge Report Guard

## Goal

Make Functional Subject judged trial runs audit-safe even when the GPT-5.5/Codex judge subprocess hangs: write a complete pre-judge report before invoking the judge, and bound the judge subprocess with an optional timeout.

## Scope

Allowed changes:

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- `Tasks/TASK_BOARD.yaml`
- this task directory

Forbidden changes:

- `EgoOperator/**` runtime behavior
- tracked secrets or API keys
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- GitHub Project mutation

## Acceptance Gate

- `functional_subject_trial_report.json` and markdown are written before GPT-5.5 judging starts.
- `--judge-timeout-seconds` bounds the Functional Subject judge subprocess and returns structured `codex_judge_timeout` evidence.
- Timeout or unavailable judge results remain `partial` and cannot close `EGO-FS-010`.
- Existing judge pass path remains compatible.

## Claim Ceiling

`Functional Subject judge timeout/pre-judge report local workflow candidate pass`
