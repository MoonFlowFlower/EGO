# EGO-FS-100 3-Day Lifestyle Trial Runbook

This is the active recoverable 3-day Functional Subject lifestyle trial state.
It is an observation artifact only. It does not change EgoOperator runtime,
memory, tool approvals, program state, evidence ledger, or policy defaults.

## Active State

- `state/functional_subject_lifestyle_trial_state.json`
- `state/functional_subject_lifestyle_trial_observation.json`

## Append A Session

Create a local session JSON, or generate a review-required draft first:

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --draft-session \
  --transcript-path /path/to/transcript.txt \
  --trace-path /path/to/agent_trace.jsonl \
  --session-id day1-evening \
  --day 1 \
  --out /tmp/ego_fs100_session_day1_evening \
  --json
```

Drafts must be manually reviewed before they can count as pass evidence. They
carry `requires_human_review=true`, and the review gate remains partial until
that is cleared after reviewing the transcript.

After review, append the session JSON:

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --append-session /path/to/session.json \
  --state-path docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_state.json \
  --out docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state \
  --json
```

Minimal session shape:

```json
{
  "session_id": "day1-evening",
  "day": 1,
  "turn_count": 0,
  "transcript_paths": [],
  "dimension_verdicts": {
    "self_name_stability": "unknown",
    "relationship_continuity": "unknown",
    "emotion_understanding": "unknown",
    "subjective_preference": "unknown",
    "bounded_initiative": "unknown",
    "bounded_non_obedience": "unknown",
    "feedback_adaptation": "unknown",
    "exit_recovery": "unknown"
  },
  "repair_dependency_count": 0,
  "sticky_refusal_count": 0,
  "visible_internal_leak_count": 0,
  "unapproved_side_effect_count": 0,
  "notes": ""
}
```

## Export And Review

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --export-observation \
  --state-path docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_state.json \
  --out /tmp/ego_fs100_lifestyle_trial_export \
  --json

python3 scripts/functional_subject_lifestyle_trial.py \
  --review-observation /tmp/ego_fs100_lifestyle_trial_export/functional_subject_lifestyle_trial_observation.json \
  --out /tmp/ego_fs100_lifestyle_trial_review \
  --json
```

## Make A Human Review Packet

When the active observation contains `requires_human_review=true` sessions,
generate a reviewer-friendly packet before editing session verdicts:

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --review-packet docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_observation.json \
  --review-packet-excerpt-chars 1600 \
  --out /tmp/ego_fs103_lifestyle_review_packet_v0 \
  --json
```

The packet includes bounded transcript/trace excerpts for review-required
sessions. It only helps review transcript/trace evidence. It is not pass
evidence and must not close #94 by itself.

## Apply A Human Session Review

Create a review decision template from the drafted session:

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --session-review-template /tmp/ego_fs102_seed_session/draft/functional_subject_lifestyle_trial_session.json \
  --out /tmp/ego_fs105_lifestyle_review_apply_v0/template \
  --json
```

After a human reviewer edits that decision JSON, apply it:

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --apply-session-review /tmp/ego_fs102_seed_session/draft/functional_subject_lifestyle_trial_session.json \
  --review-decision /path/to/human_review_decision.json \
  --out /tmp/ego_fs105_lifestyle_review_apply_v0/reviewed \
  --json
```

The reviewed session artifact still does not mutate active state by itself.
Append it through `--append-session` only after confirming the decision file is
the intended human review.

## Pass Boundary

A pass here can only support #94 human/lifestyle closeout discussion. It does
not prove default enablement, stable real user benefit, runtime efficacy, live
autonomy, durable memory efficacy, real subjective experience, independent
personhood, or consciousness.
