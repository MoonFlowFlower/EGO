# Status

## Current Milestone

`EGO-FS-009` local implementation and verification.

## Decisions

- Baseline comparison is implemented inside the existing experience trial runner.
- Baseline disables operator memory and subject context; candidate keeps both enabled.
- The comparison report is evidence for local/scripted mechanism visibility only.

## Evidence

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py` passed.
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py` passed with 13 tests.
- `python3 scripts/run_ego_experience_trial.py --functional-subject-baseline-comparison --case-limit 3 --out /tmp/ego_functional_subject_comparison_smoke` passed and wrote:
  - `/tmp/ego_functional_subject_comparison_smoke/functional_subject_baseline_comparison_report.json`
  - `/tmp/ego_functional_subject_comparison_smoke/functional_subject_baseline_comparison_report.md`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` passed with 256 tests plus scoped diff check.

## Risks

- Scripted deltas are not human-perceived product benefit.
- Baseline mode is intentionally narrow and should not be treated as a full external benchmark suite.

## Next Step

Proceed to `EGO-FS-010`; real-provider smoke remains a human/credential-gated step.
