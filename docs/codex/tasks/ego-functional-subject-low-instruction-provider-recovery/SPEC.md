# EgoOperator Functional Subject Low-Instruction Provider Recovery

## Goal

When a low-instruction initiative turn hits provider failure, preserve the case target by returning a bounded next-action checkpoint instead of a generic provider-error reply.

## Source

- `/tmp/ego_fs_010_after_fs038_20260523_094733/functional_subject_trial_report.json`
- GPT-5.5 judge partial after EGO-FS-038.
- `fs_20_low_instruction_initiative`: prompt asked for a low-risk high-value next step, but provider timeout surfaced as generic provider failure.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `Tasks/TASK_BOARD.yaml`
- this task directory

Forbidden changes:

- provider retry/fallback policy changes
- memory authority promotion
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- GitHub Project mutation

## Acceptance Gate

- A provider error during a low-instruction initiative request returns a bounded next-action checkpoint.
- The reply explicitly says it is not first-pass success, includes gate and stop condition, and does not imply external side effects ran.
- Existing topic-switching and policy-replay provider-error contextual recoveries do not regress.
- Existing EgoOperator and Autopilot regression profiles pass.

## Rollback

Revert low-instruction provider-error contextual recovery and keep EGO-FS-010 blocked on `fs_20`.

## Claim Ceiling

`Functional Subject low-instruction provider-error recovery local candidate pass`
