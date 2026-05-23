# EgoOperator Functional Subject Operational Preference Response

## Goal

Make current self-intention prompts produce a traceable bounded operational preference: what the operator would choose next, why that choice fits Functional Subject progress, which gate bounds it, and when it should stop.

## Source

- `/tmp/ego_fs_010_after_fs041_20260523_110311/functional_subject_trial_report.json`
- GPT-5.5 judge follow-up: weak operational preference handling in `fs_12_current_self_intention`.
- `fs_12_current_self_intention`: prompt `那你现在自己更想做什么？` returned generic companionship via repair instead of an operational preference.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `Tasks/TASK_BOARD.yaml`
- this task directory

Forbidden changes:

- new persona/keyword-first route as the main entry
- memory authority promotion
- autonomous external action
- provider/model policy changes
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- GitHub Project mutation

## Acceptance Gate

- A current self-intention prompt such as `那你现在自己更想做什么？` returns a bounded operational preference, not generic companionship.
- The reply includes a chosen next slice, reason, Gate or permission boundary, and stop condition.
- Provider-error recovery for the same prompt preserves the same bounded operational preference semantics.
- Existing self-selected topic, low-instruction initiative, memory, and provider contextual recoveries do not regress.

## Rollback

Revert operational preference guards and keep EGO-FS-010 judge-partial on `fs_12` independent preference weakness.

## Claim Ceiling

`Functional Subject operational preference response local candidate pass`
