# EGO-FS-104 Runbook

Generate a review packet with bounded transcript and trace excerpts:

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --review-packet docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_observation.json \
  --review-packet-excerpt-chars 1600 \
  --out /tmp/ego_fs104_lifestyle_review_excerpts_v0 \
  --json
```

Outputs:

- `/tmp/ego_fs104_lifestyle_review_excerpts_v0/functional_subject_lifestyle_trial_review_packet.json`
- `/tmp/ego_fs104_lifestyle_review_excerpts_v0/functional_subject_lifestyle_trial_review_packet.md`

The excerpts are review aids only. They do not automatically change dimension
verdicts, clear `requires_human_review`, or close #94.
