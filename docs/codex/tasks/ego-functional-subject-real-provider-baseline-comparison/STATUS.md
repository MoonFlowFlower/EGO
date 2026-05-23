# Status

Status: accepted

## Decisions

- Reuse the existing baseline comparison runner after EGO-FS-051 cleaned the baseline control.
- Do not add a new judge step here; this task only records real-provider comparison evidence.
- Keep EGO-FS-010 blocked unless a later judge/human gate explicitly admits closure.

## Verification

- Real-provider comparison:
  - `python3 scripts/run_ego_experience_trial.py --functional-subject-baseline-comparison --case-limit 20 --out /tmp/ego_fs052_real_provider_baseline_comparison_20260523_143604`
  - candidate provider mode: `openrouter`
  - baseline provider mode: `openrouter`
  - candidate native memory gate enabled: `true`
  - baseline native memory gate enabled: `false`
- Scorecard:
  - candidate clean first-pass `15/20`, baseline clean first-pass `12/20`
  - candidate repair cases `5`, baseline repair cases `7`
  - candidate mechanism trace count `20`
  - reply text diff count `19`
  - no empty replies or timeouts

## Evidence

- `EVIDENCE.real_provider_baseline_comparison.json`
- `/tmp/ego_fs052_real_provider_baseline_comparison_20260523_143604/functional_subject_baseline_comparison_report.json`
- `/tmp/ego_fs052_real_provider_baseline_comparison_20260523_143604/functional_subject_baseline_comparison_report.md`

## Remaining Risk

Real-provider comparison evidence can quantify candidate-vs-baseline differences, but it does not by itself prove stable user benefit, restart durability, or human-observable improvement.
