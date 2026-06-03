# Status

Last updated: 2026-06-01

## Result

`EGO-FS-098` is accepted as a local workflow candidate for Functional Subject
lifestyle-trial evidence collection.

## What Changed

- Added `scripts/functional_subject_lifestyle_trial.py`.
- Added deterministic tests for packet generation and review classification.
- Generated a 3/7/30 day lifestyle-trial packet.
- Verified a synthetic pass-shaped observation review path.

## Evidence

Commands:

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --out /tmp/ego_fs098_lifestyle_trial_protocol_v0 \
  --json

python3 scripts/functional_subject_lifestyle_trial.py \
  --review-observation /tmp/ego_fs098_lifestyle_trial_pass_observation.json \
  --out /tmp/ego_fs098_lifestyle_trial_review_pass_v0 \
  --json
```

Results:

- `/tmp/ego_fs098_lifestyle_trial_protocol_v0/functional_subject_lifestyle_trial_packet.json`
  -> `ego_operator.functional_subject_lifestyle_trial_packet.v0`.
- `/tmp/ego_fs098_lifestyle_trial_review_pass_v0/functional_subject_lifestyle_trial_review.json`
  -> `functional_subject_lifestyle_trial_review_pass` for the synthetic
  review-shape sample.

## Decision

Accept the protocol as local workflow infrastructure. It is the correct next
step after `EGO-FS-097` because current automatic tasks are exhausted and #94
still needs human/lifestyle evidence rather than another short micro-version or
default policy enablement.

## Next Smallest Safe Step

Use the packet for a real 3-day Functional Subject lifestyle observation, then
review the resulting observation JSON. If it passes, use it as #94 human
closeout discussion evidence or escalate to a stricter 7/30 day trial.

## What This Does Not Prove

This does not prove #94 closeout, default enablement, runtime efficacy, stable
real user benefit, live autonomy, durable memory efficacy, independent
personhood, real subjective experience, or consciousness.
