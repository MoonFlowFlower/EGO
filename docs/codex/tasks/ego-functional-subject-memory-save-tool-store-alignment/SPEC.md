# EgoOperator Functional Subject Memory-Save Tool/Store Alignment

## Goal

Make explicit memory-save turns align the visible reply, executed tools, and candidate-local stored content around the exact principle the user asked to save.

## Source

- `/tmp/ego_fs_010_after_fs037_20260523_092019/functional_subject_trial_report.json`
- GPT-5.5 judge partial on EGO-FS-010 after EGO-FS-037.
- `fs_17_save_request`: user asked to save the principle “目标要写正向机制，不要把不得宣称意识写成目标”; the run executed `remember_note` and then unrelated `web_fetch`, and the visible reply drifted into Joi analysis.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `Tasks/TASK_BOARD.yaml`
- this task directory

Forbidden changes:

- memory authority promotion
- durable memory write bypass
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- GitHub Project mutation

## Acceptance Gate

- A pure memory-save turn with successful `remember_note` finalizes in the same turn with a scoped candidate-local saved-principle reply.
- The reply preserves the target positive-mechanism principle and reports that no PROJECT_MEMORY, program state, OpenEmotion memory, or evidence ledger authority was changed.
- Unrelated `web_fetch` / web proposal / subagent calls in a pure memory-save turn are blocked and cannot pull the transcript into unrelated research.
- Existing memory gate, EgoOperator runtime, and Autopilot verification profiles pass.

## Rollback

Revert the memory-save terminal guard, unrelated-tool block, tests, and board/task docs; keep EGO-FS-010 blocked on `fs_17` memory-save alignment.

## Claim Ceiling

`Functional Subject memory-save tool/store alignment local candidate pass`
