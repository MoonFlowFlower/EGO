# Status

Status: accepted

## Decisions

- Treat this as evidence generation, not runtime repair.
- Use the new response attribution scorecard to route the next repair task.
- Do not close EGO-FS-010 from this smoke alone unless its human-required gate is explicitly satisfied later.

## Verification

- Full real-provider rerun:
  `OPENROUTER_API_KEY=... python3 scripts/run_ego_experience_trial.py --functional-subject-trial --judge-with-codex --judge-model gpt-5.5 --case-timeout-seconds 60 --judge-timeout-seconds 600 --out /tmp/ego_fs_010_scorecard_rerun_20260523_121618`
- Result: `scripted_functional_subject_judge_partial`, 20 cases, provider=openrouter.
- Report: `/tmp/ego_fs_010_scorecard_rerun_20260523_121618/functional_subject_trial_report.json`
- Scorecard: clean first-pass 10/20, runtime repair 9/20, tool/result path 1/20.
- Experiment-control blocking classes: `planner_trace_not_transcript_visible` = 1.
- GPT-5.5 judge follow-up: strengthen applied OutcomePrediction so trace-selected actions actually drive more cases.

## Remaining Risk

This is real-provider scripted observation, not a Functional Subject pass. It does not close EGO-FS-010. It identifies the next mechanism gap: OutcomePrediction/ViabilityState should select or alter more actions, not only appear as context.
