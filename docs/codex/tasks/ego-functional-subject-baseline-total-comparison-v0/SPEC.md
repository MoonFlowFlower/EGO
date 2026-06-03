# EGO-FS-087: Same-Prompt Baseline Comparison For #94 v0

## Problem Reframe

EGO-FS-010/#94 Loop 112 remains GPT-5.5 `partial`. The focused `fs_14` and
`fs_17` blockers are resolved; the current missing proof is whether the same
base model/tool stack without Functional Subject gates fails or weakens on the
same 20-case sample pack.

## Positive Mechanism Goal

Prove a same-prompt baseline comparison:

- candidate arm: SubjectState / ViabilityState / OutcomePrediction / native
  memory gates enabled;
- baseline arm: operator memory disabled, SubjectContext disabled, native memory
  gate disabled;
- same 20 Functional Subject prompts;
- judge packet compares reply deltas, clean first-pass counts, repair reliance,
  and trace mechanism evidence.

## Scope

Allowed:

- `scripts/run_ego_experience_trial.py`
- this task directory and `Tasks/TASK_BOARD.yaml`

Not allowed:

- runtime mechanism changes beyond passing existing timeout args into the
  baseline runner;
- PROJECT_MEMORY, program state, evidence ledger, legacy runtime;
- GitHub Project as task truth source.

## Acceptance Gate

- Baseline comparison runs over the same Functional Subject pack with candidate
  and baseline arms.
- GPT-5.5 judge returns structured verdict.
- Report includes candidate/baseline response attribution summaries and delta
  records.
- No claim stronger than local/scripted candidate pass.

## Rollback

Remove the CLI timeout forwarding change and ignore the comparison report.

## Claim Ceiling

`Functional Subject same-prompt baseline comparison local/scripted candidate pass`.
