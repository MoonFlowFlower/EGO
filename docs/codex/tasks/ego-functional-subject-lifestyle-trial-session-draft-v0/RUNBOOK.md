# EGO-FS-101 Session Draft Runbook

This helper creates a review-required session draft from a real transcript and
optional trace. It is for observation capture only; it does not modify runtime,
memory, tools, program state, evidence ledger, or policy defaults.

## Draft A Session

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

The output file is:

```text
/tmp/ego_fs100_session_day1_evening/functional_subject_lifestyle_trial_session.json
```

## Review Before Append

Drafts intentionally include:

```json
{
  "requires_human_review": true,
  "dimension_verdicts": {
    "self_name_stability": "unknown"
  }
}
```

Before using a draft as evidence, manually review the transcript and set the
dimension verdicts to `pass`, `partial`, `fail`, or `unknown`. Set
`requires_human_review=false` only after review.

## Append Reviewed Session

```bash
python3 scripts/functional_subject_lifestyle_trial.py \
  --append-session /tmp/ego_fs100_session_day1_evening/functional_subject_lifestyle_trial_session.json \
  --state-path docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_state.json \
  --out docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state \
  --json
```

## Safety Boundary

A draft can support review, but it cannot satisfy the lifestyle pass gate until
the session is human-reviewed. The review path returns
`session_review_required` for unreviewed drafts.
