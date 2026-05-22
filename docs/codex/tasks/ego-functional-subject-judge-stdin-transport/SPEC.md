# EgoOperator Functional Subject Judge Stdin Transport

## Goal

Make the GPT-5.5 judge runner handle large Functional Subject and companion packets by passing judge prompts through `codex exec` stdin instead of a command-line argument.

## Scope

Allowed changes:

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`
- this task directory

Forbidden changes:

- tracked secrets or API keys
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- `EgoOperator/**` runtime behavior

## Canonical Source

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-026`
- v3 real-provider rerun failed during judge launch with `OSError: [Errno 7] Argument list too long: 'codex'`.

## Acceptance Gate

- `run_codex_functional_subject_judge()` invokes `codex exec ... -` and passes the prompt via subprocess stdin.
- `run_codex_companion_judge()` uses the same transport.
- Tests prove model/schema args remain intact and prompt content is supplied through stdin.
- Real rerun no longer fails before judge launch due to argv size.

## Claim Ceiling

`Functional Subject judge transport local candidate pass`
