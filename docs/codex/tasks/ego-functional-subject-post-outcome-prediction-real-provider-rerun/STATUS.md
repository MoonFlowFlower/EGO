# Status

Status: accepted

## Decisions

- Treat this as evidence generation, not runtime repair.
- Compare against the EGO-FS-045 scorecard, especially applied OutcomePrediction count and runtime repair dependence.
- Do not close EGO-FS-010 unless GPT-5.5/human evidence satisfies its human-required gate later.

## Verification

- Full real-provider rerun:
  `OPENROUTER_API_KEY=... python3 scripts/run_ego_experience_trial.py --functional-subject-trial --judge-with-codex --judge-model gpt-5.5 --case-timeout-seconds 60 --judge-timeout-seconds 600 --out /tmp/ego_fs_010_after_fs046_20260523_131112`
- Result: `scripted_functional_subject_judge_partial`, 20 cases, provider=openrouter.
- Report: `/tmp/ego_fs_010_after_fs046_20260523_131112/functional_subject_trial_report.json`
- Scorecard: clean first-pass 14/20, outcome_prediction_gate 6/20, runtime repair 6/20.
- Applied OutcomePrediction cases: `fs_07`, `fs_08`, `fs_12`, `fs_13`, `fs_18`, `fs_20`.
- Experiment-control blocking classes: none.
- GPT-5.5 judge remains partial; strongest next blockers are native memory correction/save/forget strength and longitudinal/restart evidence.

## Remaining Risk

Provider behavior may still be partial even if local OutcomePrediction coverage improved. This task can only record scripted real-provider observation.

EGO-FS-010 remains blocked/human-gated; this smoke does not prove full Functional Subject pass.
