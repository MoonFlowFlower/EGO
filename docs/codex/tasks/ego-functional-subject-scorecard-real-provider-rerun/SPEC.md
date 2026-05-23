# EgoOperator Functional Subject Scorecard Real-Provider Rerun

## Goal

Run the full 20-case Functional Subject real-provider trial after adding the response-attribution scorecard, then use the scorecard and GPT-5.5 judge packet to choose the next ready repair.

## Source

- EGO-FS-044 response-attribution scorecard.
- Latest GPT-5.5 judge request to separate first-pass LLM behavior, runtime guard behavior, and end-to-end operator behavior.

## Scope

Allowed actions:

- Run `scripts/run_ego_experience_trial.py --functional-subject-trial --judge-with-codex`.
- Record local evidence path in this task status and `Tasks/TASK_BOARD.yaml`.

Forbidden changes:

- EgoOperator runtime behavior changes
- provider/model policy changes
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- GitHub Project mutation

## Acceptance Gate

- Full 20-case real-provider trial completes or writes a timeout/partial report.
- Report includes `response_attribution_summary` and GPT-5.5 judge packet with the scorecard.
- Closeout records first-pass count, repair count, remaining blockers, and next ready task recommendation.
- No EGO runtime, program state, evidence ledger, or GitHub Project mutation is made by the smoke task itself.

## Rollback

Discard the run artifact and keep EGO-FS-010 blocked pending a later rerun.

## Claim Ceiling

`Functional Subject scorecard real-provider observation candidate pass`
