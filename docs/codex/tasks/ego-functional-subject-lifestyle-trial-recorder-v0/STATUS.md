# Status

Last updated: 2026-06-01

## Result

`EGO-FS-099` is accepted as a local workflow candidate for recoverable
Functional Subject lifestyle-trial observation.

## What Changed

- `scripts/functional_subject_lifestyle_trial.py` now supports:
  - `--init-trial`
  - `--append-session`
  - `--export-observation`
- Trial state uses
  `ego_operator.functional_subject_lifestyle_trial_state.v0`.
- Exported observation uses
  `ego_operator.functional_subject_lifestyle_trial_observation.v0`.
- Existing review mode can review exported observations.

## Evidence

Commands:

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --init-trial \
  --planned-days 3 \
  --trial-id ego-fs099-demo \
  --out /tmp/ego_fs099_lifestyle_trial_state_demo \
  --json

python3 scripts/functional_subject_lifestyle_trial.py \
  --append-session /tmp/ego_fs099_lifestyle_trial_demo_session.json \
  --state-path /tmp/ego_fs099_lifestyle_trial_state_demo/functional_subject_lifestyle_trial_state.json \
  --out /tmp/ego_fs099_lifestyle_trial_state_demo \
  --json

python3 scripts/functional_subject_lifestyle_trial.py \
  --export-observation \
  --state-path /tmp/ego_fs099_lifestyle_trial_state_demo/functional_subject_lifestyle_trial_state.json \
  --out /tmp/ego_fs099_lifestyle_trial_state_demo_export \
  --json

python3 scripts/functional_subject_lifestyle_trial.py \
  --review-observation /tmp/ego_fs099_lifestyle_trial_state_demo_export/functional_subject_lifestyle_trial_observation.json \
  --out /tmp/ego_fs099_lifestyle_trial_state_demo_review \
  --json
```

Results:

- `/tmp/ego_fs099_lifestyle_trial_state_demo/functional_subject_lifestyle_trial_state.json`
  -> `ego_operator.functional_subject_lifestyle_trial_state.v0`.
- `/tmp/ego_fs099_lifestyle_trial_state_demo_export/functional_subject_lifestyle_trial_observation.json`
  -> `ego_operator.functional_subject_lifestyle_trial_observation.v0`.
- `/tmp/ego_fs099_lifestyle_trial_state_demo_review/functional_subject_lifestyle_trial_review.json`
  -> `functional_subject_lifestyle_trial_review_pass` for the synthetic
  append/export smoke sample.

## Decision

Accept EGO-FS-099 as local workflow infrastructure. The next real gate remains
a real 3-day lifestyle observation, not another synthetic pass.

## Next Smallest Safe Step

Start a real 3-day lifestyle trial state, append sessions as they happen, export
the observation JSON, then review it before #94 closeout or any default-policy
discussion.

## What This Does Not Prove

This does not prove a real lifestyle trial happened, #94 closeout, default
enablement, runtime efficacy, stable real user benefit, live autonomy, durable
memory efficacy, independent personhood, real subjective experience, or
consciousness.
