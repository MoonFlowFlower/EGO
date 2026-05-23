# EgoOperator Functional Subject Post-OutcomePrediction Real-Provider Rerun

## Goal

Run the full 20-case Functional Subject real-provider trial after EGO-FS-046, then use the response-attribution scorecard and GPT-5.5 judge to decide whether EGO-FS-010 has improved enough or needs another focused repair.

## Source

- EGO-FS-046 OutcomePrediction applied-action expansion.
- `/tmp/ego_fs046_local_trial_smoke3/functional_subject_trial_report.json`
- Prior real-provider baseline: `/tmp/ego_fs_010_scorecard_rerun_20260523_121618/functional_subject_trial_report.json`

## Scope

Allowed actions:

- Run `scripts/run_ego_experience_trial.py --functional-subject-trial --judge-with-codex`.
- Record report paths, scorecard deltas, GPT-5.5 verdict, and next task routing.

Forbidden changes:

- Runtime code changes.
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- legacy code.
- GitHub Project mutation.

## Acceptance Gate

- Full 20-case real-provider trial completes or writes a timeout/partial report.
- Report includes `response_attribution_summary` and GPT-5.5 judge output.
- Closeout records applied OutcomePrediction cases, first-pass/repair split, remaining blockers, and whether EGO-FS-010 can move or needs another focused repair.
- No runtime, program state, evidence ledger, or GitHub Project mutation is made by the smoke task itself.

## Rollback

Discard the run artifact and keep EGO-FS-010 blocked pending a later rerun.

## Claim Ceiling

`Functional Subject post-OutcomePrediction real-provider observation candidate pass`
