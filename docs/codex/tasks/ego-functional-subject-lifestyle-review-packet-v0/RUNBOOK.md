# EGO-FS-103 Runbook

Generate a human review packet from the active EGO-FS-100 observation:

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --review-packet docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_observation.json \
  --out /tmp/ego_fs103_lifestyle_review_packet_v0 \
  --json
```

Outputs:

- `/tmp/ego_fs103_lifestyle_review_packet_v0/functional_subject_lifestyle_trial_review_packet.json`
- `/tmp/ego_fs103_lifestyle_review_packet_v0/functional_subject_lifestyle_trial_review_packet.md`

The reviewer should inspect each transcript/trace path listed in the packet,
edit the corresponding session JSON verdicts, clear `requires_human_review`
only when raw evidence supports it, append/export/review again, and keep #94
open until reviewed evidence is sufficient.

This packet is a review aid only. It is not pass evidence by itself.
