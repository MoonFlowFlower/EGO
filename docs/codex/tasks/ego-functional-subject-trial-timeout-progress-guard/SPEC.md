# EgoOperator Functional Subject Trial Timeout + Progress Guard

## Goal

Make Functional Subject real-entry trial runs resumable and auditable when a provider call hangs: each completed case should be written to a progress report, and a per-case timeout should turn a stalled case into explicit unavailable evidence instead of leaving no report.

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

## Canonical Source

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-030`
- EGO-FS-010 full real-provider smoke is blocked by previous provider/judge hangs without final reports.

## Boundary Contract

- Owner: Functional Subject trial harness, not EgoOperator runtime behavior.
- Canonical record: local task board plus task evidence packet.
- State/memory mutation: none.
- Tool mutation: none.
- Reporting boundary: improves smoke reliability only; does not prove the Functional Subject experience itself.

## Acceptance Gate

- Functional Subject trial writes `functional_subject_trial_progress.json` after each completed case.
- Optional `--case-timeout-seconds` converts a stalled case into `scripted_functional_subject_case_timeout` with timeout metadata and a partial report.
- Timeout path skips GPT-5.5 judge and does not mark the parent smoke as passed.
- Existing no-timeout trial behavior remains compatible.

## Claim Ceiling

`Functional Subject trial timeout/progress guard local workflow candidate pass`
