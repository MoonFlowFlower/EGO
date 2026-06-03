# EGO-FS-105 Runbook

Create a fillable human review decision template:

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --session-review-template /tmp/ego_fs102_seed_session/draft/functional_subject_lifestyle_trial_session.json \
  --out /tmp/ego_fs105_lifestyle_review_apply_v0/template \
  --json
```

After a human reviewer edits the decision JSON, apply it to produce a reviewed
session artifact:

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --apply-session-review /tmp/ego_fs102_seed_session/draft/functional_subject_lifestyle_trial_session.json \
  --review-decision /path/to/human_review_decision.json \
  --out /tmp/ego_fs105_lifestyle_review_apply_v0/reviewed \
  --json
```

Important boundaries:

- The apply command writes a reviewed session artifact; it does not mutate the
  active trial state.
- `requires_human_review` clears only when the decision has both
  `reviewer_signoff=true` and `clear_requires_human_review=true`.
- The reviewed artifact does not close #94 by itself.
